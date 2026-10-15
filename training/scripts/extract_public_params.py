#!/usr/bin/env python3
"""只读提取上游公开物理参数 → training/params/*.json。

数据来源（只读，不修改参考库）：
- references/microduck-replica/software/training/src/mjlab_microduck/robot/microduck/robot_walk.xml
  （Pollen Microduck 官方 CAD 经 onshape-to-robot 导出；质量/惯量/运动学/限位）
- references/microduck-replica/software/training/src/mjlab_microduck/robot/hd1910/1910_m6.json
  （LuwuDynamics/xgoduck_rl 公开的 HD-1910 BAM M6 辨识参数，Apache-2.0）

本脚本只解析数值并做运动学级联（自写四元数运算），输出本项目自己的参数表；
不复制、不加载上游模型文件到仿真。
"""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC_XML = REPO / "references/microduck-replica/software/training/src/mjlab_microduck/robot/microduck/robot_walk.xml"
SRC_1910 = REPO / "references/microduck-replica/software/training/src/mjlab_microduck/robot/hd1910/1910_m6.json"
OUT_DIR = REPO / "training/params"

# HOME 站姿（STAND2），逐值抄录自 microduck_constants.py HOME_FRAME.joint_pos（73-97 行）。
# 与上游关节名一一对应；左右符号相反的成对关节按上游原值保留。
HOME_POSE = {
    "left_hip_yaw": 0.0,
    "right_hip_yaw": 0.0,
    "left_hip_roll": -0.0873,
    "right_hip_roll": 0.0873,
    "left_hip_pitch": -0.4579,
    "right_hip_pitch": 0.4579,
    "left_knee": -0.0049,
    "right_knee": 0.0049,
    "left_ankle": 0.4530,
    "right_ankle": -0.4530,
    "neck_pitch": 0.3491,
    "head_pitch": 0.3491,
    "head_yaw": 0.0,
    "head_roll": 0.0,
}


# ---------- 四元数（wxyz，MuJoCo 约定） ----------

def quat_mul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def quat_conj(q):
    return (q[0], -q[1], -q[2], -q[3])


def quat_to_mat(q):
    w, x, y, z = q
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ]


def mat_vec(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_norm(a):
    return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)


def axis_angle_quat(axis, angle):
    n = vec_norm(axis)
    if n == 0:
        return (1.0, 0.0, 0.0, 0.0)
    s = math.sin(angle / 2.0) / n
    return (math.cos(angle / 2.0), axis[0] * s, axis[1] * s, axis[2] * s)


def parse_floats(text):
    return tuple(float(x) for x in text.split())


# ---------- 解析 XML ----------

def parse_body(elem, parent_name):
    """递归解析一个 <body>，返回 dict 树（不含世界位形）。"""
    body = {
        "name": elem.get("name"),
        "parent": parent_name,
        "pos": parse_floats(elem.get("pos", "0 0 0")),
        "quat": parse_floats(elem.get("quat", "1 0 0 0")),
        "joints": [],
        "children": [],
        "sites": [],
        "collision_geoms": [],
    }
    for child in elem:
        if child.tag == "joint":
            j = {
                "name": child.get("name"),
                "type": child.get("type", "hinge"),
                "axis": parse_floats(child.get("axis", "0 0 1")),
                "range": parse_floats(child.get("range")) if child.get("range") else None,
                "class": child.get("class"),
            }
            body["joints"].append(j)
        elif child.tag == "inertial":
            body["inertial"] = {
                "pos": parse_floats(child.get("pos")),
                "mass": float(child.get("mass")),
                "fullinertia": parse_floats(child.get("fullinertia")),
            }
        elif child.tag == "site":
            body["sites"].append({
                "name": child.get("name"),
                "pos": parse_floats(child.get("pos", "0 0 0")),
            })
        elif child.tag == "geom":
            if child.get("class") == "collision":
                body["collision_geoms"].append(child.get("name"))
        elif child.tag == "body":
            body["children"].append(parse_body(child, body["name"]))
    return body


def flatten(bodies, body, out):
    out.append(body)
    for c in body["children"]:
        flatten(bodies, c, out)


def world_pose(body, parent_pos, parent_quat, qmap):
    """X_body(q) = X_parent ⊕ X_static(pos,quat) ⊕ X_joint(q)。

    MuJoCo 铰链：绕 body 局部系中 joint pos（本模型均为 0,0,0）的 axis 旋转。
    """
    p = vec_add(parent_pos, mat_vec(quat_to_mat(parent_quat), body["pos"]))
    q = quat_mul(parent_quat, body["quat"])
    joint_origins_world = []
    joint_axes_world = []
    for j in body["joints"]:
        qj = q
        if j["type"] == "hinge" and qmap is not None and j["name"] in qmap:
            qj = quat_mul(q, axis_angle_quat(j["axis"], qmap[j["name"]]))
        joint_origins_world.append(p)
        joint_axes_world.append(mat_vec(quat_to_mat(q), j["axis"]))
        q = qj
    return p, q, joint_origins_world, joint_axes_world


def compute_world(flat, root_pos, root_quat, qmap):
    """按树级联，返回每个 body 的世界原点/姿态与各关节世界原点/轴向。"""
    result = {}
    root = flat[0]  # trunk_base

    def rec(body, p, q, is_root=False):
        if is_root:
            # 根 body 的 p/q 已是其在 worldbody 中的静态位形，不再叠加 pos/quat
            wp, wq = p, q
            jos = [wp] * len(body["joints"])
            jax = [mat_vec(quat_to_mat(wq), j["axis"]) for j in body["joints"]]
        else:
            wp, wq, jos, jax = world_pose(body, p, q, qmap)
        result[body["name"]] = {
            "world_pos": [round(x, 6) for x in wp],
            "world_quat": [round(x, 6) for x in wq],
            "joint_world": [
                {
                    "name": j["name"],
                    "origin": [round(x, 6) for x in o],
                    "axis_world": [round(x, 6) for x in a],
                }
                for j, o, a in zip(body["joints"], jos, jax)
            ],
        }
        for c in body["children"]:
            rec(c, wp, wq)

    rec(root, root_pos, root_quat, is_root=True)
    return result


def main():
    tree = ET.parse(SRC_XML)
    mujoco = tree.getroot()
    worldbody = mujoco.find("worldbody")
    trunk = worldbody.find("body")  # trunk_base（含 freejoint）
    trunk_pos = parse_floats(trunk.get("pos", "0 0 0"))
    trunk_quat = parse_floats(trunk.get("quat", "1 0 0 0"))

    root_body = parse_body(trunk, None)
    flat: list[dict] = []
    flatten({}, root_body, flat)

    actuators = [a.get("name") for a in mujoco.find("actuator").findall("position")]

    geometry = {
        "meta": {
            "description": "Pollen Microduck 官方 CAD（onshape-to-robot 导出）公开物理参数，"
                           "本项目只读提取；XL330 版质量/惯量，非 HD-1910 C 线实测。",
            "source_file": str(SRC_XML.relative_to(REPO)).replace("\\", "/"),
            "extracted": "2026-10-15",
            "units": {"length": "m", "mass": "kg", "inertia": "kg·m^2", "angle": "rad"},
            "conventions": {
                "body_pos_quat": "body 原点/姿态相对父 body；quat 为 wxyz",
                "joint_axis": "铰链轴向在该 body 局部坐标系（全部为 0 0 1）",
                "joint_rotation": "X_body(q)=X_parent·X_static(pos,quat)·X_joint(q)",
                "inertial": "质心与 fullinertia=(Ixx,Iyy,Izz,Ixy,Ixz,Iyz) 在 body 局部系、绕质心",
                "trunk_base": "自由浮动基座，worldbody 内 pos/quat 为初始位形",
            },
        },
        "trunk_base_init": {"pos": list(trunk_pos), "quat": list(trunk_quat)},
        "actuator_order": actuators,
        "bodies": {},
        "world_pose_at_zero": compute_world(flat, trunk_pos, trunk_quat, {}),
        "world_pose_at_home": compute_world(flat, trunk_pos, trunk_quat, HOME_POSE),
    }
    for b in flat:
        geometry["bodies"][b["name"]] = {
            "parent": b["parent"],
            "pos": list(b["pos"]),
            "quat": list(b["quat"]),
            "inertial": b.get("inertial"),
            "joints": b["joints"],
            "sites": b["sites"],
            "collision_geoms": b["collision_geoms"],
        }

    bam = json.loads(SRC_1910.read_text(encoding="utf-8"))
    bam_doc = {
        "meta": {
            "description": "HD-1910（HLS1910）BAM M6 辨识参数，LuwuDynamics 公开，原值抄录。",
            "source_file": str(SRC_1910.relative_to(REPO)).replace("\\", "/"),
            "upstream": "LuwuDynamics/xgoduck_rl @ 326d77a1（Apache-2.0）",
            "upstream_sha256": "ef2d51adfb1cc0831b9b02ca19aa9176fceecdf725148d084378d7d9a64afceb",
            "caveats": "非本项目辨识；q_offset 不等于装配零位；max_velocity=100 为放开斜率限速的近似，"
                       "非空载转速；command_delay 与队列 lag 不可相加宣称为实机总延迟。",
            "extracted": "2026-10-15",
        },
        "params": bam,
    }

    home_doc = {
        "meta": {
            "description": "STAND2 站姿 HOME 关节角，抄录自上游 microduck_constants.py HOME_FRAME（73-97 行）。",
            "source_file": "references/microduck-replica/software/training/src/mjlab_microduck/robot/microduck_constants.py",
            "units": {"angle": "rad"},
            "note": "躯干相对踝轴前移约 5mm，注释称用于让质心落在踝轴上方。",
            "extracted": "2026-10-15",
        },
        "joint_pos": HOME_POSE,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "microduck_geometry.json").write_text(
        json.dumps(geometry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT_DIR / "hd1910_bam_m6.json").write_text(
        json.dumps(bam_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT_DIR / "home_pose.json").write_text(
        json.dumps(home_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    total_mass = sum(b.get("inertial", {}).get("mass", 0.0) for b in flat)
    print(f"bodies={len(flat)} joints14={len(actuators)} total_mass={total_mass:.4f} kg")
    for name in ("trunk_base", "jaw_soft", "ankle_left"):
        w = geometry["world_pose_at_home"][name]
        print(f"  HOME world {name}: pos={w['world_pos']}")


if __name__ == "__main__":
    main()
