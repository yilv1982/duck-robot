#!/usr/bin/env python3
"""回放入口：加载 checkpoint 在 MuJoCo viewer 中观看策略。

用法（在 training/ 下）：
    .venv/Scripts/python.exe play.py checkpoints/duck_stand_v0/final.zip
"""

from __future__ import annotations

import sys
import time

from stable_baselines3 import PPO

from duckstand.env import DuckStandEnv


def main():
    ckpt = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/duck_stand_v0/final.zip"
    env = DuckStandEnv(render_mode="human")
    model = PPO.load(ckpt)
    obs, _ = env.reset(seed=0)

    episodes = 0
    ep_return, ep_len = 0.0, 0
    while episodes < 10 and env._viewer is not None and env._viewer.is_running():
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        ep_return += reward
        ep_len += 1
        time.sleep(1.0 / env.CONTROL_HZ)
        if terminated or truncated:
            print(f"episode {episodes}: return={ep_return:.1f} len={ep_len} "
                  f"z={info.get('z', float('nan')):.3f}")
            obs, _ = env.reset()
            ep_return, ep_len = 0.0, 0
            episodes += 1
    env.close()


if __name__ == "__main__":
    main()
