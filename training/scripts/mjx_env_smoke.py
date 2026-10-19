#!/usr/bin/env python3
"""mjlab 最小环境 smoke：自建 duck_v0.xml + 自写奖励在 GPU 上闭环。

验证里程碑：我们的模型/物理参数/环境逻辑（观测-动作-奖励-终止）在 mjlab
GPU 管线中端到端运行，并测批量吞吐。全部配置为本项目自设计。
"""

import json
import time

import mujoco
import torch

from mjlab.actuator import IdealPdActuatorCfg
from mjlab.entity import Entity, EntityArticulationInfoCfg, EntityCfg
from mjlab.envs import ManagerBasedRlEnv, ManagerBasedRlEnvCfg
from mjlab.envs.mdp import joint_pos_rel, joint_vel_rel, time_out
from mjlab.envs.mdp.actions import JointPositionActionCfg
from mjlab.managers.observation_manager import ObservationGroupCfg, ObservationTermCfg
from mjlab.managers.reward_manager import RewardTermCfg
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.managers.termination_manager import TerminationTermCfg
from mjlab.scene import SceneCfg
from mjlab.sim import MujocoCfg, SimulationCfg
from mjlab.terrains import TerrainEntityCfg

XML = "models/duck_v0.xml"
HOME = json.load(open("params/home_pose.json", encoding="utf-8"))["joint_pos"]
NUM_ENVS = 4096
DEVICE = "cuda:0"


def _duck_spec():
    spec = mujoco.MjSpec.from_file(XML)
    for act in list(spec.actuators):
        spec.delete(act)
    return spec


def duck_home_reward(env, asset_cfg, home: torch.Tensor):
    """自写奖励：关节角接近 HOME（smoke 用最小可训练信号）。"""
    asset: Entity = env.scene[asset_cfg.name]
    q = asset.data.joint_pos[:, asset_cfg.joint_ids]
    return torch.exp(-torch.mean((q - home) ** 2, dim=-1) / 0.25)


def main():
    joints = SceneEntityCfg("robot", joint_names=(r".*",))
    home_t = torch.tensor([HOME[n] for n in [
        "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
        "neck_pitch", "head_pitch", "head_yaw", "head_roll",
        "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
    ]], device=DEVICE)

    robot = EntityCfg(
        spec_fn=_duck_spec,
        articulation=EntityArticulationInfoCfg(
            actuators=(IdealPdActuatorCfg(
                target_names_expr=(r".*",),
                stiffness=25.0, damping=2.0, effort_limit=0.94,
                armature=0.00178, frictionloss=0.0158,
            ),),
        ),
    )

    obs_terms = {
        "joint_pos": ObservationTermCfg(func=joint_pos_rel, params={"asset_cfg": joints}),
        "joint_vel": ObservationTermCfg(func=joint_vel_rel, params={"asset_cfg": joints}),
    }
    cfg = ManagerBasedRlEnvCfg(
        scene=SceneCfg(terrain=TerrainEntityCfg(terrain_type="plane"),
                       entities={"robot": robot}, num_envs=NUM_ENVS, env_spacing=2.0),
        observations={"actor": ObservationGroupCfg(obs_terms),
                      "critic": ObservationGroupCfg(dict(obs_terms))},
        actions={"joints": JointPositionActionCfg(
            entity_name="robot", actuator_names=(r".*",), scale=0.5)},
        events={},
        rewards={"home": RewardTermCfg(
            func=duck_home_reward, weight=1.0,
            params={"asset_cfg": joints, "home": home_t})},
        terminations={"time_out": TerminationTermCfg(func=time_out, time_out=True)},
        sim=SimulationCfg(mujoco=MujocoCfg(timestep=0.002)),
        decimation=10,
        episode_length_s=10.0,
    )

    t0 = time.time()
    env = ManagerBasedRlEnv(cfg, device=DEVICE)
    obs, _ = env.reset()
    actor_obs = obs["actor"] if isinstance(obs["actor"], dict) else {"flat": obs["actor"]}
    print(f"环境构建+重置完成 ({time.time()-t0:.1f}s)，actor 观测形状 "
          f"{next(iter(actor_obs.values())).shape}")

    act_dim = env.action_manager.total_action_dim
    action = torch.zeros(NUM_ENVS, act_dim, device=DEVICE)
    STEPS = 200
    t0 = time.time()
    for _ in range(STEPS):
        obs, rew, term, trunc, info = env.step(action)
    elapsed = time.time() - t0
    print(f"闭环吞吐: {STEPS*NUM_ENVS/elapsed:,.0f} env-steps/s"
          f"（{NUM_ENVS} env × {STEPS} 控制步 / {elapsed:.2f}s，含观测+奖励）")
    print(f"奖励样例: {rew[:4].tolist()}")


if __name__ == "__main__":
    main()
