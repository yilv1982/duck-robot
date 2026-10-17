#!/usr/bin/env python3
"""行走任务验收：速度跟踪 + 推扰（3N）统一测试。

用法（在 training/ 下）：
    .venv/Scripts/python.exe scripts/eval_walk.py [checkpoint.zip]

指标：
1. 速度跟踪：各命令档（-0.2~+0.2 m/s 五档）平均速度误差与存活；
2. 3N 推扰满额率（原验收门槛 ≥80%）：vx_cmd ∈ {-0.2, 0, +0.2} 三档 × 20 场景。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

TRAIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRAIN))

from duckstand.env import DuckStandEnv  # noqa: E402


def run_episode(env, policy, vx_cmd, push=None):
    """一回合：固定命令；push=(t_push, angle, force) 可选脉冲。返回 (存活步, 末半段均 vx)。"""
    obs, _ = env.reset(seed=0)
    env.push_enabled = False
    env._vx_cmd = vx_cmd
    trunk = env._trunk_bid
    start = int(push[0] * 50) if push else -1
    done, L, vxs = False, 0, []
    while not done:
        a, _ = policy.predict(obs, deterministic=True)
        if push and start <= L < start + 15:
            env.data.xfrc_applied[trunk, 0] = push[2] * np.cos(push[1])
            env.data.xfrc_applied[trunk, 1] = push[2] * np.sin(push[1])
        elif push:
            env.data.xfrc_applied[trunk, :3] = 0.0
        obs, r, term, trunc, info = env.step(a)
        if L >= 100:  # 跳过起步 2s
            vxs.append(info["vx"])
        L += 1
        done = term or trunc
    return L, (float(np.mean(vxs)) if vxs else 0.0)


def main():
    ckpt = sys.argv[1] if len(sys.argv) > 1 else str(TRAIN / "checkpoints" / "duck_walk_v06" / "final.zip")
    from stable_baselines3 import PPO

    env = DuckStandEnv()
    policy = PPO.load(ckpt)

    print("== 速度跟踪（每档 5 回合）==")
    for cmd in (-0.2, -0.1, 0.0, 0.1, 0.2):
        errs, full = [], []
        for ep in range(5):
            L, vx = run_episode(env, policy, cmd)
            errs.append(abs(vx - cmd))
            full.append(L >= 500)
        print(f"  cmd={cmd:+.1f}: 存活 {np.mean(full):.0%}, 平均速度误差 {np.mean(errs):.3f} m/s")

    print("== 3N×0.3s 推扰满额率（20 场景 × 三命令档，门槛≥80%）==")
    for cmd in (-0.2, 0.0, 0.2):
        full = []
        for tt in (2.0, 3.5, 5.0, 6.5, 8.0):
            for ang in (0.0, 1.6, 3.1, 4.7):
                L, _ = run_episode(env, policy, cmd, push=(tt, ang, 3.0))
                full.append(L >= 500)
        print(f"  vx_cmd={cmd:+.1f}: {np.mean(full):.0%}")


if __name__ == "__main__":
    main()
