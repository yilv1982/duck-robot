"""duck v0 站立任务：本项目自编的最小 gymnasium 训练环境。

学习目标（real2sim2real 第 3 步）：从 HOME 站姿出发，抵抗初始扰动保持站立。
观测 45 维：机体坐标系重力方向(3) + 相对 HOME 关节角(14) + 关节速度(14) + 上次动作(14)。
动作 14 维：目标角 = HOME + ACTION_SCALE × action，position actuator 直控。

不使用上游观测/奖励配置；接口定义见 training/README.md。
"""

from __future__ import annotations

import json
from pathlib import Path

import gymnasium as gym
import mujoco
import numpy as np

TRAIN = Path(__file__).resolve().parents[1]
MODEL_XML = TRAIN / "models" / "duck_v0.xml"
HOME_JSON = TRAIN / "params" / "home_pose.json"

CONTROL_HZ = 50.0
DECIMATION = 10  # × timestep 0.002s
ACTION_SCALE = 0.5
EPISODE_SECONDS = 10.0

# 奖励权重（自选初始值；迭代时一次只改一项）
W_UPRIGHT = 1.0
W_HEIGHT = 1.0
W_JOINT_HOME = 0.5
W_ACTION_RATE = -0.05
W_ACTION_MAG = -0.01   # 动作幅度惩罚：帮助先收敛到"安静站住"再学调整
W_ALIVE = 0.5

Z_HOME_TOL = 0.05     # 高度奖励宽度（m）
TILT_TERMINATE = 0.9  # |重力水平分量| 超过此值判摔（cos 倾角 < ~0.44）


class DuckStandEnv(gym.Env):
    """MuJoCo 后端；qpos 布局 = freejoint(7) + 14 关节（XML 声明序）。"""

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": int(CONTROL_HZ)}

    def __init__(self, render_mode: str | None = None):
        self.render_mode = render_mode
        self.model = mujoco.MjModel.from_xml_path(str(MODEL_XML))
        self.data = mujoco.MjData(self.model)

        self.nq = self.model.nq
        self.nu = self.model.nu
        assert self.nu == 14 and self.nq == 21, f"模型维度异常: nq={self.nq} nu={self.nu}"

        home = json.loads(HOME_JSON.read_text(encoding="utf-8"))["joint_pos"]
        self.act_names = [
            mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
            for i in range(self.nu)
        ]
        self.home_q = np.array([home[n] for n in self.act_names], dtype=np.float64)
        self.qpos_addr = np.array([self.model.jnt_qposadr[i] for i in range(1, self.model.njnt)])
        self.ctrlrange = self.model.actuator_ctrlrange.copy()
        self.z_home = self.model.key_qpos[0][2]

        self.obs_dim = 3 + 14 + 14 + 14
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (self.obs_dim,), np.float64)
        self.action_space = gym.spaces.Box(-1.0, 1.0, (self.nu,), np.float64)

        self._last_action = np.zeros(self.nu)
        self._renderer = None
        self._viewer = None

    # ---------- 观测 ----------

    def _gravity_body(self) -> np.ndarray:
        """重力方向在机体坐标系的单位向量（直立时 ≈ (0,0,-1)）。"""
        q = self.data.qpos[3:7]
        rot = np.zeros(9)
        mujoco.mju_quat2Mat(rot, q)
        rot = rot.reshape(3, 3)
        g_world = np.array([0.0, 0.0, -1.0])
        return rot.T @ g_world

    def _get_obs(self) -> np.ndarray:
        q_rel = self.data.qpos[self.qpos_addr] - self.home_q
        dq = self.data.qvel[6:]
        return np.concatenate([self._gravity_body(), q_rel, dq, self._last_action]).astype(np.float64)

    # ---------- 回合流程 ----------

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:] = self.model.key_qpos[0]
        self.data.qvel[:] = 0.0

        rng = self.np_random
        self.data.qpos[self.qpos_addr] += rng.uniform(-0.015, 0.015, self.nu)
        self.data.qpos[2] += rng.uniform(-0.005, 0.005)
        self.data.qpos[3:7] = self._tilt_quat(rng.uniform(0.0, 0.04))
        self.data.qvel[2] = rng.uniform(-0.03, 0.03)

        self._last_action = np.zeros(self.nu)
        self.data.ctrl[:] = self.home_q
        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    def _tilt_quat(self, angle: float) -> np.ndarray:
        """绕随机水平轴倾斜 angle 的四元数（wxyz）。"""
        rng = self.np_random
        axis = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0])
        axis /= np.linalg.norm(axis) + 1e-9
        quat = np.zeros(4)
        mujoco.mju_axisAngle2Quat(quat, axis, angle)
        return quat

    def step(self, action):
        action = np.clip(action, -1.0, 1.0)
        target = np.clip(self.home_q + ACTION_SCALE * action,
                         self.ctrlrange[:, 0], self.ctrlrange[:, 1])
        prev_action = self._last_action.copy()

        self.data.ctrl[:] = target
        for _ in range(DECIMATION):
            mujoco.mj_step(self.model, self.data)

        obs = self._get_obs()
        g = self._gravity_body()
        z = self.data.qpos[2]

        upright = -g[2]                        # 直立=1
        height = float(np.exp(-((z - self.z_home) / Z_HOME_TOL) ** 2))
        joint_home = float(np.exp(-np.mean((self.data.qpos[self.qpos_addr] - self.home_q) ** 2) / 0.25))
        action_rate = float(np.mean((action - prev_action) ** 2))
        action_mag = float(np.mean(action ** 2))

        reward = (W_UPRIGHT * upright + W_HEIGHT * height
                  + W_JOINT_HOME * joint_home + W_ACTION_RATE * action_rate
                  + W_ACTION_MAG * action_mag + W_ALIVE)

        terminated = bool(np.linalg.norm(g[:2]) > TILT_TERMINATE or z < self.z_home * 0.6)
        self._last_action = action.copy()

        if self.render_mode == "human":
            self.render()
        return obs, float(reward), terminated, False, {
            "upright": upright, "height": height, "z": z}

    # ---------- 渲染 ----------

    def render(self):
        if self.render_mode == "rgb_array":
            if self._renderer is None:
                self._renderer = mujoco.Renderer(self.model, 480, 640)
            self._renderer.update_scene(self.data)
            return self._renderer.render()
        if self._viewer is None:
            import mujoco.viewer
            self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
        if self._viewer.is_running():
            self._viewer.sync()
        return None

    def close(self):
        if self._renderer is not None:
            self._renderer.close()
        if self._viewer is not None:
            self._viewer.close()
