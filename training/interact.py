#!/usr/bin/env python3
"""旧 CPU/SB3 交互：加载匹配当前环境的策略，手工施加干扰。

用法（在 training/ 下）：
    .venv/Scripts/python.exe interact.py path/to/current_sb3_checkpoint.zip
    必须显式指定兼容 checkpoint；当前 mjlab 策略使用 play_mujoco.py。

操作（MuJoCo viewer 内置扰动功能）：
    双击机器人任意身体       选中该部位（高亮）
    按住 Ctrl + 左键拖动     对选中部位施加外力（弹簧式，拖得越远力越大）
    松开 Ctrl/鼠标           力消失，机器人自行恢复
    拖动旋转视角 / 滚轮缩放   观察姿态

机器人摔倒后 1 秒自动重置，等待期间窗口保持响应。终端打印状态。
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from duckstand.env import CONTROL_HZ, DuckStandEnv  # noqa: E402
from play import load_compatible_policy, wait_for_control_deadline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", help="与当前环境匹配的 SB3 .zip；mjlab 使用 play_mujoco.py")
    args = parser.parse_args()
    env = DuckStandEnv()
    env.push_enabled = False  # 交互模式关闭自动推扰，保留用户手推的力
    try:
        try:
            policy = load_compatible_policy(args.checkpoint, env)
        except ValueError as exc:
            parser.error(str(exc))
        obs, _ = env.reset(seed=0)

        print(__doc__)
        print(f"策略: {args.checkpoint} | 关闭 viewer 窗口退出\n")

        steps_alive = 0
        reset_at = None
        period = 1.0 / CONTROL_HZ
        with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
            deadline = time.perf_counter()
            while viewer.is_running():
                if reset_at is not None:
                    if time.perf_counter() < reset_at:
                        viewer.sync()
                        deadline = wait_for_control_deadline(deadline, period)
                        continue
                    obs, _ = env.reset()
                    steps_alive = 0
                    reset_at = None
                    deadline = time.perf_counter()

                action, _ = policy.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                steps_alive += 1

                if terminated:
                    print(f"摔倒了（存活 {steps_alive / CONTROL_HZ:.1f}s，upright={info['upright']:.2f}），"
                          "1s 后重置…")
                    reset_at = time.perf_counter() + 1.0
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
                deadline = wait_for_control_deadline(deadline, period)
    finally:
        env.close()

    print("viewer 已关闭，退出。")


if __name__ == "__main__":
    main()
