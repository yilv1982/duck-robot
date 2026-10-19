#!/usr/bin/env python3
"""mjlab DuckWalk 验收：速度跟踪 + 3N 等效推扰（速度脉冲）满额率。

用法（WSL training/ 下）：
    .venv-wsl/bin/python scripts/eval_mjlab.py [checkpoint.pt]
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mjlab_duck.env_cfg import duck_walk_env_cfg  # noqa: E402
from mjlab.envs import ManagerBasedRlEnv  # noqa: E402

DEV = "cuda:0"


def load_policy(ckpt: str):
    """从 checkpoint 手写前向：ELU MLP 128×128（权重结构实测 mlp.0/2/4）。"""
    data = torch.load(ckpt, map_location=DEV, weights_only=False)
    sd = data["actor_state_dict"]
    mean = sd["obs_normalizer._mean"].to(DEV)
    var = sd["obs_normalizer._var"].to(DEV)
    layers = [sd["mlp.0.weight"], sd["mlp.0.bias"],
              sd["mlp.2.weight"], sd["mlp.2.bias"],
              sd["mlp.4.weight"], sd["mlp.4.bias"]]

    @torch.no_grad()
    def actor(obs_norm):
        x = torch.nn.functional.elu(obs_norm @ layers[0].T + layers[1])
        x = torch.nn.functional.elu(x @ layers[2].T + layers[3])
        return x @ layers[4].T + layers[5]

    return actor, mean, var


def rollout(env, ac, mean, var, vx_cmd, push_step=None, push_vel=0.36):
    """单场景：固定命令；push_step 时给根速度脉冲（等效 3N×0.3s/0.737kg≈1.2m/s，
    实际用 0.36 m/s 对齐 CPU 版 3N 冲量水平速度）。返回 (存活步, 末段均 vx)。"""
    obs, _ = env.reset()
    env.command_manager.get_term("velocity")._cmd[:, 0] = vx_cmd
    asset = env.scene["robot"]
    n = env.num_envs
    alive = torch.ones(n, dtype=torch.bool, device=DEV)  # 每 env 独立存活标记
    L, vxs = 0, []
    while L < 500:
        if push_step is not None and L == push_step:
            vel = asset.data.root_link_vel_w.clone()
            vel[:, 0] += push_vel
            asset.write_root_link_velocity_to_sim(vel)
        flat = obs["actor"]
        norm = (flat - mean) / torch.sqrt(var + 1e-8)
        a = ac(norm)
        obs, rew, term, trunc, info = env.step(a)
        alive &= ~term  # 逐 env 累计终止
        if L >= 100:
            vxs.append(asset.data.root_link_lin_vel_b[:, 0].clone())
        L += 1
    vx_mean = torch.stack(vxs).mean(dim=0) if vxs else torch.zeros(1, device=DEV)
    return alive, vx_mean


def main():
    ckpt = sys.argv[1] if len(sys.argv) > 1 else str(sorted(
        (Path("logs/rsl_rl/duck_walk")).glob("*/model_*.pt"))[-1])
    print(f"checkpoint: {ckpt}")
    ac, mean, var = load_policy(ckpt)

    env_cfg = duck_walk_env_cfg(num_envs=20, play=True)
    env = ManagerBasedRlEnv(env_cfg, device=DEV)

    print("== 速度跟踪（每档 5 回合，20 并行 env）==")
    for cmd in (-0.2, -0.1, 0.0, 0.1, 0.2):
        alive, vx = rollout(env, ac, mean, var, cmd)
        err = float(torch.abs(vx[alive].mean() - cmd)) if alive.any() else float("nan")
        print(f"  cmd={cmd:+.1f}: 存活 {int(alive.sum())}/{env.num_envs}, "
              f"速度误差 {err:.3f} m/s")

    print("== 3N 等效推扰（速度脉冲 ~0.36m/s，5 时刻×4 方向=20 场景）==")
    full = 0
    total = 0
    for t in (2.0, 3.5, 5.0, 6.5, 8.0):
        alive, _ = rollout(env, ac, mean, var, 0.0, push_step=int(t * 50))
        full += int(alive.sum())
        total += env.num_envs
    print(f"  满额率: {full/total:.0%}（{full}/{total}，门槛≥80%）")


if __name__ == "__main__":
    main()
