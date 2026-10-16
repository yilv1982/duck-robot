#!/usr/bin/env python3
"""交互测试：加载站立策略，在 MuJoCo viewer 里手工施加干扰。

用法（在 training/ 下）：
    .venv/Scripts/python.exe interact.py [checkpoint.zip]
    默认 checkpoints/duck_stand_v022/final.zip

操作（MuJoCo viewer 内置扰动功能）：
    双击机器人任意身体       选中该部位（高亮）
    按住 Ctrl + 左键拖动     对选中部位施加外力（弹簧式，拖得越远力越大）
    松开 Ctrl/鼠标           力消失，机器人自行恢复
    拖动旋转视角 / 滚轮缩放   观察姿态

机器人摔倒后 1 秒自动重置回 HOME 重新站好。终端实时打印状态。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np
from stable_baselines3 import PPO

sys.path.insert(0, str(Path(__file__).parent))
from duckstand.env import DuckStandEnv  # noqa: E402


def main():
    ckpt = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/duck_stand_v022/final.zip"
    env = DuckStandEnv()
    env.push_enabled = False  # 交互模式关闭自动推扰，保留用户手推的力
    policy = PPO.load(ckpt)
    obs, _ = env.reset(seed=0)

    print(__doc__)
    print(f"策略: {ckpt} | 关闭 viewer 窗口退出\n")

    steps_alive = 0
    with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
        while viewer.is_running():
            t0 = time.perf_counter()
            action, _ = policy.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            steps_alive += 1

            if terminated:
                print(f"摔倒了（存活 {steps_alive / 50:.1f}s，upright={info['upright']:.2f}），"
                      f"1s 后重置…")
                time.sleep(1.0)
                obs, _ = env.reset()
                steps_alive = 0
            elif truncated:
                # 交互模式不因 10s 截断重置——用户可能正要推它
                env._step_count = 0

            # 外力状态（viewer 的 Ctrl+拖拽扰动写入 xfrc_applied）
            force = env.data.xfrc_applied[:, :3]
            fmag = float(np.linalg.norm(force, axis=1).max())
            if fmag > 0.05 and steps_alive % 25 == 0:
                print(f"  正在受力 {fmag:.2f} N，upright={info['upright']:.3f}，"
                      f"z={info['z']:.3f}")

            viewer.sync()
            # 实速回放：每控制步 0.02s
            dt = 0.02 - (time.perf_counter() - t0)
            if dt > 0:
                time.sleep(dt)

    print("viewer 已关闭，退出。")


if __name__ == "__main__":
    main()
