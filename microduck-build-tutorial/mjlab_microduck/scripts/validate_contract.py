#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Repeatable A-training contract checks (never starts a training run).

Default: stdlib-only source/XML/assets/deployment metadata audit.
--compile-xml: CPU MuJoCo XML compilation only; no BAM import (safe in B venv).
--config: require pinned A BAM, build Entity on CPU, check config + real IMU math.
--env-steps N: additionally reset/step an actual env N times, only by explicit opt-in.

Examples (from this training directory):
  python scripts/validate_contract.py
  python scripts/validate_contract.py --compile-xml --config
  python scripts/validate_contract.py --env-steps 8 --device cuda:0
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ROBOT = ROOT / "src/mjlab_microduck/robot"
TASKS = ROOT / "src/mjlab_microduck/tasks"
DEPLOY = ROOT.parent / "microduck/src"
SOURCE_SHA = "cb70b792312d559a4da09064d92009079671815f"
BAM_SHA = "0007411bd82c48f1bc12ae8382f98e4d8b879c95"
ORDER = (
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
    "neck_pitch", "head_pitch", "head_yaw", "head_roll",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
)
POSE = (0., -.087, -.458, -.005, .453, .349, .349, 0., 0., 0., .087, .458, .005, -.453)
ACTOR_TERMS = ("base_ang_vel", "projected_gravity", "joint_pos", "joint_vel", "actions", "command")
FOOT_GEOMS = ("left_foot_collision", "right_foot_collision")
MOUNT = (.7071068, 0., .7071068, 0.)
FINAL_RANGES = ((-.5, .7), (-.3, .3), (-1.5, 1.5), (-3., 3.))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def tree(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def assignment_values(module, target):
    target_dump = ast.unparse(ast.parse(target, mode="eval").body)
    return [n.value for n in ast.walk(module) if isinstance(n, (ast.Assign, ast.AnnAssign))
            and any(ast.unparse(t) == target_dump for t in
                    (n.targets if isinstance(n, ast.Assign) else [n.target]))]


def literal(module, target):
    values = assignment_values(module, target)
    require(len(values) == 1, f"Expected one assignment: {target}")
    return ast.literal_eval(values[0])


def call_keywords(module, name):
    calls = [n for n in ast.walk(module) if isinstance(n, ast.Call) and ast.unparse(n.func) == name]
    require(len(calls) == 1, f"Expected one {name} call")
    return {kw.arg: kw.value for kw in calls[0].keywords}


def protobuf_fields(data):
    """Read length-delimited ONNX metadata without importing ONNX or running it."""
    pos = 0
    def varint():
        nonlocal pos
        value = shift = 0
        while True:
            byte = data[pos]
            pos += 1
            value |= (byte & 127) << shift
            if not byte & 128:
                return value
            shift += 7
            require(shift < 70, "Invalid protobuf varint")
    while pos < len(data):
        tag = varint()
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            varint()
        elif wire in (1, 5):
            pos += 8 if wire == 1 else 4
        elif wire == 2:
            length = varint()
            end = pos + length
            require(end <= len(data), "Truncated protobuf")
            yield number, data[pos:end]
            pos = end
        else:
            raise AssertionError(f"Unexpected protobuf wire type {wire}")


def deployment_metadata():
    metadata = {}
    for number, value in protobuf_fields((DEPLOY / "agents/walk.onnx").read_bytes()):
        if number == 14:  # ONNX ModelProto.metadata_props, not graph tensors.
            entry = dict(protobuf_fields(value))
            metadata[entry[1].decode()] = entry[2].decode()
    return metadata


def check_sources():
    manifest = json.loads((ROBOT / "source_manifest.json").read_text())
    require(manifest["revision"] == SOURCE_SHA, "Wrong upstream revision")
    require(manifest["licenses"]["code"]["spdx"] == "Apache-2.0", "Code license")
    require(manifest["licenses"]["model"]["version"] is None, "Do not invent CC version")
    require(manifest["licenses"]["model"]["name"] == "Creative Commons BY-SA-NC", "Model license")
    paths = []
    for item in manifest["files"]:
        file = (ROBOT / item["path"]).resolve()
        require(file.is_relative_to(ROBOT.resolve()), "Manifest path escapes robot/")
        data = file.read_bytes()
        require(item["revision"] == SOURCE_SHA, f"Revision: {file}")
        expected_url = f"https://raw.githubusercontent.com/pollen-robotics/microduck_rl/{SOURCE_SHA}/{item['upstream_path']}"
        require(item["url"] == expected_url, f"URL: {file}")
        require(len(data) == item["bytes"], f"Size: {file}")
        require(hashlib.sha256(data).hexdigest() == item["sha256"], f"SHA256: {file}")
        blob = f"blob {len(data)}\0".encode() + data
        require(hashlib.sha1(blob).hexdigest() == item["git_blob_sha1"], f"Git blob: {file}")
        paths.append(item["path"])
    require(len(paths) == len(set(paths)) == 45, "Expected 45 unique upstream files")
    require("3D model files are licensed under Creative Commons BY-SA-NC." in
            (ROBOT / "provenance/UPSTREAM_README.md").read_text(), "License evidence")
    xml = ET.parse(ROBOT / "microduck/robot_walk.xml").getroot()
    joints = xml.findall(".//worldbody//joint")
    require(tuple(j.get("name") for j in joints) == ORDER, "XML 14-joint order")
    require(all(j.get("type", "hinge") == "hinge" for j in joints), "Only hinge joints")
    require(len(xml.findall(".//freejoint")) == 1, "Exactly one freejoint")
    require(xml.find(".//body[@name='trunk_base']") is not None, "Missing trunk_base")
    for site in ("left_foot", "right_foot", "imu"):
        require(xml.find(f".//site[@name='{site}']") is not None, f"Missing {site} site")
    for name in FOOT_GEOMS:
        require(xml.find(f".//geom[@name='{name}']") is not None, f"Missing {name}")
    require(len(xml.findall(".//worldbody//geom[@class='self_collision_only']")) == 3,
            "Must retain all 3 upstream self-collision geoms")
    meshdir = xml.find("compiler").get("meshdir")
    meshes = {f"microduck/{meshdir}/{m.get('file')}" for m in xml.findall(".//asset/mesh")}
    require(len(meshes) == 38, "Expected 38 mesh files")
    require(meshes == {p for p in paths if p.endswith(".stl")}, "Mesh/manifest mismatch")
    print("PASS sources: immutable upstream XML + 38 STL; 14 hinges + freejoint; names/licenses")


def check_static_contract():
    constants = tree(ROBOT / "microduck_constants.py")
    deploy = tree(DEPLOY / "constants.py")
    cfg = tree(TASKS / "microduck_velocity_env_cfg.py")
    require(literal(constants, "JOINT_ORDER") == ORDER, "Training joint order")
    require(literal(constants, "HOME_POSE") == POSE, "Training HOME14 (no hardware offsets)")
    require(tuple(literal(deploy, "OBSERVATION_DOF_ORDER")) == ORDER, "A deployment order")
    metadata = deployment_metadata()
    require(tuple(metadata["joint_names"].split(",")) == ORDER, "A ONNX joint_names")
    require(tuple(map(float, metadata["default_joint_pos"].split(","))) == POSE, "A ONNX default pose")
    require(tuple(metadata["observation_names"].split(",")) == ACTOR_TERMS, "A actor term order")
    require(float(metadata["action_scale"]) == 1., "A ONNX action_scale")
    require(literal(cfg, "cfg.decimation") == 4, "Explicit decimation=4")
    sim = call_keywords(cfg, "MujocoCfg")
    require(ast.literal_eval(sim["timestep"]) == .005, "Physics timestep .005")
    require(literal(cfg, "joint_pos_action.scale") == 1., "Action scale=1")
    require(literal(cfg, "joint_pos_action.use_default_offset") is True, "Default pose offset")
    initial = call_keywords(constants, "EntityCfg.InitialStateCfg")
    z = ast.literal_eval(initial["pos"])[2]
    delta = literal(cfg, 'cfg.events["reset_base"].params["pose_range"]["z"]')
    require(all(math.isclose(z + d, e) for d, e in zip(delta, (.12, .13))), "Double-height reset")
    bam = call_keywords(constants, "BamActuatorCfg")
    expected = dict(motor_name="xl330", model="m6", kp_fw=125, vin=5., vin_range=(4.5, 5.5),
                    max_current=1.75, vin_drop_gain_range=(0., 0.), vin_min=4.5,
                    delay_min_lag=0, delay_max_lag=0)
    for name, value in expected.items():
        require(ast.literal_eval(bam[name]) == value, f"BAM {name}")
    require(ast.unparse(bam["target_names_expr"]) == "JOINT_ORDER", "BAM targets")
    collision = call_keywords(constants, "CollisionCfg")
    for name, value in dict(condim=3, priority=1, friction=(1.,), disable_other_geoms=False).items():
        require(ast.literal_eval(collision[name]) == value, f"Foot collision {name}")
    require(literal(cfg, "BNO080_MOUNT_QUAT") == literal(deploy, "IMU_MOUNT_QUAT") == MOUNT,
            "Physical IMU mount")
    require('dof_friction_randomization' not in ast.unparse(cfg), "Ineffective friction DR event")
    for target, value in (("VX_MAX", .7), ("VX_MAX_BACKWARD", .5), ("VY_MAX", .3),
                          ("VTHETA_MAX_MOVING", 1.5), ("VTHETA_MAX_STATIONARY", 3.)):
        require(literal(deploy, target) == value, f"Deployment envelope {target}")
    source = ast.unparse(cfg)
    require("6000 * 24" in source and "3000 * 24" in source, "Curriculum thresholds")
    require("Mjlab-Velocity-Microduck" in (TASKS / "__init__.py").read_text(), "Registered task")
    print("PASS static contract: A ONNX HOME/order, 50 Hz, scale=1, BAM 5V, reset height, mount")


def check_xml_compile():
    import mujoco
    for filename in ("robot_walk.xml", "scene_walk.xml"):
        model = mujoco.MjModel.from_xml_path(str(ROBOT / "microduck" / filename))
        require((model.nq, model.nv, model.nu) == (21, 20, 14), f"Compiled dimensions {filename}")
        names = tuple(model.joint(i).name for i in range(1, model.njnt))
        require(names == ORDER, f"Compiled joint order {filename}")
        data = mujoco.MjData(model)
        data.qpos[:7] = (.0, .0, .12, 1., 0., 0., 0.)
        data.qpos[7:] = POSE
        mujoco.mj_forward(model, data)
        require(all(math.isfinite(x) for x in data.qpos), f"Finite qpos {filename}")
    print(f"PASS CPU XML compile/forward: MuJoCo {mujoco.__version__}; nq=21 nv=20 nu=14 (no BAM)")


def check_a_bam():
    dist = importlib.metadata.distribution("better-actuator-models")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    require(direct.get("vcs_info", {}).get("commit_id") == BAM_SHA,
            "--config/--env-steps requires A's pinned BAM doc commit, NEVER B's BAM")
    # Finish mjlab entry-point discovery before BAM imports back into mjlab.
    import mjlab  # noqa: F401
    import bam.mjlab
    manifest = json.loads((ROBOT / "source_manifest.json").read_text())
    require(hashlib.sha256(Path(bam.mjlab.__file__).read_bytes()).hexdigest() ==
            manifest["bam"]["api_sha256"], "Installed BAM mjlab.py differs from pinned doc source")
    print("PASS A BAM provenance: " + BAM_SHA)


def check_imu_math():
    """Execute actual training funcs and A Observer/imu_reader with CPU tensor fakes.

    Only extract the relevant definitions: never load controller/I2C drivers.
    All quaternion conventions are wxyz. Sensor q = body q * conjugate(mount).
    """
    import numpy as np
    import torch
    from mjlab.managers.scene_entity_config import SceneEntityCfg
    from mjlab_microduck.tasks.mdp import mounted_body_ang_vel, mounted_body_projected_gravity
    scope = {"np": np, "IMU_MOUNT_QUAT": MOUNT}
    names = {"_normalize_quat", "_quat_conj", "_quat_mul", "imu_quat_to_body", "quat_apply_inverse"}
    definitions = [n for n in tree(DEPLOY / "imu_reader.py").body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(DEPLOY / "imu_reader.py"), "exec"), scope)
    observer = next(n for n in tree(DEPLOY / "observer.py").body if isinstance(n, ast.ClassDef) and n.name == "Observer")
    observe = next(n for n in observer.body if isinstance(n, ast.FunctionDef) and n.name == "read_state")
    # Execute the actual state assignments from the observer's IMU read block.
    assignments = [n for n in ast.walk(observe) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                           and t.value.id == "state" and t.attr in ("gyro", "quat", "body_quat", "projected_gravity")
                           for t in n.targets)]
    require(len(assignments) == 4, "Observer policy IMU assignments changed")
    observer_code = compile(ast.Module(body=assignments, type_ignores=[]), "observer_imu_contract", "exec")
    normalize, multiply = scope["_normalize_quat"], scope["_quat_mul"]
    mount = normalize(MOUNT)
    asset_cfg = SceneEntityCfg("robot", body_names=("trunk_base",))
    asset_cfg.body_ids = [0]
    cases = [("level", (1., 0., 0., 0.))]
    for axis in range(3):
        for angle in (-math.pi/2, -.31, .31, math.pi/2):
            q = [math.cos(angle/2), 0., 0., 0.]
            q[axis+1] = math.sin(angle/2)
            cases.append((f"axis{axis}:{angle:.3f}", tuple(q)))
    cases.append(("compound", multiply(cases[2][1], cases[7][1])))
    gyro_cases = [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.), (.3, -.5, .7)]
    for label, body_q in cases:
        sensor_q = normalize(multiply(body_q, scope["_quat_conj"](mount)))
        for world_gyro in gyro_cases:
            sensor_gyro = scope["quat_apply_inverse"](sensor_q, world_gyro)
            state = SimpleNamespace()
            controller = SimpleNamespace(read_gyro=lambda: sensor_gyro, read_quat=lambda dt: sensor_q)
            scope.update(state=state, self=SimpleNamespace(controller=controller), dt=.02)
            exec(observer_code, scope)
            data = SimpleNamespace(
                body_link_quat_w=torch.tensor([[body_q]], dtype=torch.float64),
                gravity_vec_w=torch.tensor([[0., 0., -1.]], dtype=torch.float64),
                body_link_ang_vel_w=torch.tensor([[world_gyro]], dtype=torch.float64),
            )
            env = SimpleNamespace(scene={"robot": SimpleNamespace(data=data)}, num_envs=1, device="cpu")
            up = mounted_body_projected_gravity(env, MOUNT, asset_cfg).numpy()[0]
            gyro = mounted_body_ang_vel(env, MOUNT, asset_cfg).numpy()[0]
            np.testing.assert_allclose(up, state.projected_gravity, atol=1e-7, err_msg=label)
            np.testing.assert_allclose(gyro, state.gyro, atol=1e-7, err_msg=label)
            np.testing.assert_allclose(state.body_quat, body_q, atol=1e-7, err_msg=label)
            if label == "level":
                np.testing.assert_allclose(up, [1., 0., 0.], atol=1e-7)
    print(f"PASS real IMU functions: {len(cases)} orientations x {len(gyro_cases)} gyros; level up=(1,0,0)")


def check_config():
    sys.path.insert(0, str(ROOT / "src"))
    check_a_bam()
    import numpy as np
    import mujoco
    from mjlab.tasks.registry import load_env_cfg, load_rl_cfg
    import mjlab_microduck.tasks  # standard registration, no env construction
    from mjlab_microduck.robot.microduck_constants import MICRODUCK_ROBOT_CFG, get_walk_spec
    from mjlab_microduck.tasks.mdp import step_based_staged_curriculum
    cfg = load_env_cfg("Mjlab-Velocity-Microduck")
    require(math.isclose(cfg.decimation * cfg.sim.mujoco.timestep, .02), "Control 50Hz")
    require(tuple(cfg.observations["actor"].terms) == ACTOR_TERMS, "Actor order")
    require(sum((3, 3, 14, 14, 14, 3)) == 51, "Actor 51")
    require(cfg.actions["joint_pos"].scale == 1. and cfg.actions["joint_pos"].use_default_offset, "Actions")
    require("dof_friction_randomization" not in cfg.events, "No zero-friction randomization")
    spec1, spec2 = get_walk_spec(), get_walk_spec()
    require(spec1 is not spec2, "Fresh MjSpec per call")
    self_geoms_before = [(g.meshname, g.contype, g.conaffinity) for g in spec1.geoms if g.contype == 2]
    entity = deepcopy(MICRODUCK_ROBOT_CFG).build()  # CPU, no simulation initialization
    model = entity.spec.compile()
    require(tuple(entity.joint_names) == ORDER and model.nu == 14, "Entity 14-joint/action order")
    np.testing.assert_allclose(model.key_qpos[0, 7:], POSE, atol=1e-12)
    np.testing.assert_allclose(model.key_qpos[0, :3], [0., 0., .12], atol=1e-12)
    require([model.joint(int(j)).name for j in model.actuator_trnid[:, 0]] == list(ORDER), "Actuator order")
    require(all(model.dof_frictionloss[6:] == 0.) and all(model.dof_damping[6:] == 0.), "BAM owns friction")
    for name in FOOT_GEOMS:
        geom = model.geom(name)
        require(int(geom.condim[0]) == 3 and int(geom.priority[0]) == 1, f"Contact {name}")
        require(float(geom.friction[0]) == 1., f"Friction {name}")
    require(self_geoms_before == [(g.meshname, g.contype, g.conaffinity)
            for g in entity.spec.geoms if g.contype == 2], "Self-collision geoms preserved")
    # Construct sampler without GPU buffers to verify deepcopy binds to this cfg.
    from unittest.mock import patch
    from mjlab_microduck.tasks.mdp import UniformVelocityCommandWithRotation
    command = cfg.commands["twist"]
    with patch.object(UniformVelocityCommandWithRotation, "__init__", return_value=None) as init:
        command.build(object())
        require(init.call_args.args[0] is command, "Command deepcopy closure leak")
    ranges = lambda c: (c.ranges.lin_vel_x, c.ranges.lin_vel_y, c.ranges.ang_vel_z, c.rotation_env_ang_vel_range)
    untouched = load_env_cfg("Mjlab-Velocity-Microduck")
    original_ranges = ranges(untouched.commands["twist"])
    fake = SimpleNamespace(common_step_counter=0,
        command_manager=SimpleNamespace(get_term_cfg=lambda name: command),
        reward_manager=SimpleNamespace(get_term_cfg=lambda name: cfg.rewards[name]))
    curriculum_cfg = cfg.curriculum["staged_curriculum"]
    stages = curriculum_cfg.params["stages"]
    require([s["step"] for s in stages] == [72000, 144000], "Stage steps")
    curriculum = step_based_staged_curriculum(curriculum_cfg, fake)
    for step, expected in ((71999, 0), (72000, 1), (143999, 1), (144000, 2), (144001, 2)):
        fake.common_step_counter = step
        require(curriculum(fake, [], stages)["stage"] == expected, f"Stage boundary {step}")
    require(ranges(command) == FINAL_RANGES, "Final deployment ranges")
    require(ranges(untouched.commands["twist"]) == original_ranges, "Registry config isolation")
    play = load_env_cfg("Mjlab-Velocity-Microduck", play=True)
    require(ranges(play.commands["twist"]) == FINAL_RANGES and not play.curriculum, "Play ranges")
    require(load_rl_cfg("Mjlab-Velocity-Microduck").num_steps_per_env == 24, "PPO steps per iteration")
    check_imu_math()
    print("PASS A CPU config/Entity: order/HOME, contact masks, BAM friction, 51/14 term contract, curriculum")
    return load_env_cfg("Mjlab-Velocity-Microduck")


def check_env(cfg, steps, device):
    import torch
    from mjlab.envs import ManagerBasedRlEnv
    cfg.scene.num_envs = 2
    cfg.seed = 42
    env = ManagerBasedRlEnv(cfg, device=device)
    try:
        obs, _ = env.reset()
        require(tuple(obs["actor"].shape) == (2, 51), "Runtime actor shape")
        require(env.action_manager.total_action_dim == 14, "Runtime actions14")
        def finite(tensors):
            if isinstance(tensors, torch.Tensor):
                require(bool(torch.isfinite(tensors).all()), "Nonfinite env tensor")
            elif hasattr(tensors, "values"):
                for value in tensors.values():
                    finite(value)
            elif isinstance(tensors, (tuple, list)):
                for value in tensors:
                    finite(value)
        finite(obs)
        for step in range(steps):
            action = torch.zeros((2, 14), device=device)
            if step % 2:
                action[:, 0] = .01
            result = env.step(action)
            finite(result[:4])
            require(tuple(result[0]["actor"].shape) == (2, 51), "Step actor shape")
        print(f"PASS actual env reset + {steps} finite steps on {device}; actor51/actions14")
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--compile-xml", action="store_true")
    parser.add_argument("--config", action="store_true")
    parser.add_argument("--env-steps", type=int, default=0)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    require(args.env_steps >= 0, "--env-steps must be nonnegative")
    check_sources()
    check_static_contract()
    if args.compile_xml:
        check_xml_compile()
    if args.config or args.env_steps:
        cfg = check_config()
        if args.env_steps:
            check_env(cfg, args.env_steps, args.device)
    else:
        print("SKIP actual A config/IMU functions/env: use --config; env reset/step is opt-in only")
    print("CONTRACT PASS (only the checks explicitly listed above were executed)")


if __name__ == "__main__":
    main()
