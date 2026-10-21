#!/usr/bin/env python3
"""旧 CPU/SB3 回放入口：加载匹配当前环境的 checkpoint。

用法（在 training/ 下）：
    .venv/Scripts/python.exe play.py path/to/current_sb3_checkpoint.zip

必须显式指定 checkpoint；历史 45/47 维策略不能用于当前 49 维环境。
当前 mjlab 策略请使用 play_mujoco.py，不要传给此 SB3 入口。
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from stable_baselines3 import PPO

from duckstand.env import CONTROL_HZ, DuckStandEnv


def load_compatible_policy(checkpoint: str, env: DuckStandEnv):
    """在打开窗口之前检查 SB3 策略的基础输入/输出契约。"""
    if Path(checkpoint).suffix.lower() in {".pt", ".pth"}:
        raise ValueError("此入口只支持 SB3 checkpoint；mjlab 策略请使用 play_mujoco.py。")
    try:
        policy = PPO.load(checkpoint)
    except (FileNotFoundError, OSError, KeyError, ValueError) as exc:
        raise ValueError(
            f"无法加载 SB3 checkpoint {checkpoint!r}: {exc}。"
            "请显式选择与当前环境匹配的 SB3 策略；mjlab 策略请使用 play_mujoco.py。"
        ) from exc
    actual = (policy.observation_space.shape, policy.action_space.shape)
    expected = (env.observation_space.shape, env.action_space.shape)
    if actual != expected:
        raise ValueError(
            f"checkpoint 维数不兼容：观测/动作 {actual}，当前环境需要 {expected}。"
            "历史 45/47 维策略需要原环境；mjlab 策略请使用 play_mujoco.py。"
        )
    return policy


def wait_for_control_deadline(deadline: float, period: float) -> float:
    """按绝对时刻等待；明显落后时重设时钟，不积压追帧或跳过物理步。"""
    deadline += period
    now = time.perf_counter()
    delay = deadline - now
    if delay > 0:
        time.sleep(delay)
    elif delay < -period:
        deadline = now
    return deadline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", help="与当前环境匹配的 SB3 .zip；mjlab 使用 play_mujoco.py")
    args = parser.parse_args()
    env = DuckStandEnv(render_mode="human")
    try:
        try:
            policy = load_compatible_policy(args.checkpoint, env)
        except ValueError as exc:
            parser.error(str(exc))
        obs, _ = env.reset(seed=0)
        env.render()  # reset 不创建窗口，必须先创建再检查 is_running。

        episodes = 0
        ep_return, ep_len = 0.0, 0
        period = 1.0 / CONTROL_HZ
        deadline = time.perf_counter()
        while episodes < 10 and env._viewer.is_running():
            action, _ = policy.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            ep_return += reward
            ep_len += 1
            if terminated or truncated:
                print(f"episode {episodes}: return={ep_return:.1f} len={ep_len} "
                      f"z={info.get('z', float('nan')):.3f}")
                obs, _ = env.reset()
                ep_return, ep_len = 0.0, 0
                episodes += 1
                deadline = time.perf_counter()
            deadline = wait_for_control_deadline(deadline, period)
    finally:
        env.close()


if __name__ == "__main__":
    main()
