#!/usr/bin/env python3
"""推扰验收：固定测试集上对比策略与恒零基线。

用法（在 training/ 下）：
    .venv/Scripts/python.exe scripts/eval_push.py [checkpoint.zip]

三类指标：
1. 固定推扰测试集（20 场景：时刻×方向×力幅 2–4N×0.3s）满额率；
2. 主动响应：受力窗口(+0.5s) 内策略输出变化 |Δa| 对平稳段的倍数（>3 判主动）；
3. 无扰回归：不推时 10 回合满额率与 |Δa|（不得因学推扰变得乱动/站不稳）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np

TRAIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRAIN))

from duckstand.env import DuckStandEnv  # noqa: E402


def run_scene(env, policy, t_push, angle, force, dur=15):
    """单场景：t_push 秒时施加 force N、dur 控制步的水平脉冲，返回 (存活步数, 响应指标)。"""
    trunk = env._trunk_bid
    obs, _ = env.reset(seed=0)
    env.push_enabled = False  # 关随机调度，用固定场景
    env.data.xfrc_applied[:] = 0.0
    start = int(t_push * 50)
    calm_da, resp_da, done, L = [], [], False, 0
    prev_a = None
    while not done:
        if policy is None:
            a = np.zeros(14)
        else:
            a, _ = policy.predict(obs, deterministic=True)
        if start <= L < start + dur:
            env.data.xfrc_applied[trunk, 0] = force * np.cos(angle)
            env.data.xfrc_applied[trunk, 1] = force * np.sin(angle)
        else:
            env.data.xfrc_applied[trunk, :3] = 0.0
        obs, r, term, trunc, info = env.step(a)
        if prev_a is not None:
            da = float(np.abs(a - prev_a).mean())
            (resp_da if start - 5 <= L < start + dur + 25 else
             calm_da if 10 <= L < start - 10 else []).append(da)
        prev_a = np.asarray(a).copy()
        L += 1
        done = term or trunc
    calm = float(np.mean(calm_da)) if calm_da else 0.0
    resp = float(np.mean(resp_da)) if resp_da else 0.0
    return L, (resp / calm if calm > 1e-6 else float("inf"))


def main():
    ckpt = sys.argv[1] if len(sys.argv) > 1 else str(TRAIN / "checkpoints" / "duck_stand_v03" / "final.zip")
    from stable_baselines3 import PPO
    env = DuckStandEnv()
    policy = PPO.load(ckpt)

    # 固定测试集：5 个时刻 × 4 个方向 × 力幅 {2, 3, 4} 中取 20 组合
    scenes = []
    for t in (2.0, 3.5, 5.0, 6.5, 8.0):
        for ang in (0.0, 1.6, 3.1, 4.7):
            scenes.append((t, ang, 3.0))          # 3N × 20
    assert len(scenes) == 20

    for label, pol in (("恒零基线", None), ("策略", policy)):
        full, ratios = [], []
        for t, ang, f in scenes:
            L, ratio = run_scene(env, pol, t, ang, f)
            full.append(L >= 500)
            if pol is not None:
                ratios.append(ratio)
        line = f"{label}: 3N×0.3s 满额率 {np.mean(full):.0%} (20 场景)"
        if ratios:
            line += f"；受力窗口 |Δa|/平稳段 = {np.median(ratios):.1f}×"
        print(line)

    # 无扰回归
    env.push_enabled = False
    lens, das = [], []
    for i in range(10):
        obs, _ = env.reset(seed=1000 + i)
        done, L, prev, am = False, 0, None, []
        while not done:
            a, _ = policy.predict(obs, deterministic=True)
            obs, r, term, trunc, info = env.step(a)
            if prev is not None:
                am.append(float(np.abs(a - prev).mean()))
            prev = np.asarray(a).copy()
            L += 1
            done = term or trunc
        lens.append(L >= 500)
        das.append(np.mean(am) if am else 0.0)
    print(f"无扰回归: 满额率 {np.mean(lens):.0%}, 平稳段每步|Δa|={np.mean(das):.4f}")


if __name__ == "__main__":
    main()
