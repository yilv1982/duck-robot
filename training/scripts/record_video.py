#!/usr/bin/env python3
"""离屏渲染仿真录像（MP4）。

用法（在 training/ 下）：
    .venv/Scripts/python.exe scripts/record_video.py passive              # HOME 静置站立
    .venv/Scripts/python.exe scripts/record_video.py policy <ckpt.zip>   # 加载策略回放
输出 training/videos/*.mp4（不入版本库）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import imageio.v2 as imageio
import mujoco
import numpy as np

TRAIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRAIN))
OUT_DIR = TRAIN / "videos"
FPS = 50  # 控制周期 50 Hz，每控制步 1 帧实速


def make_renderer(model):
    renderer = mujoco.Renderer(model, height=600, width=800)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.005, 0.0, 0.10]
    cam.distance = 0.55
    cam.azimuth = 90.0   # 侧视
    cam.elevation = -8.0
    return renderer, cam


def record(data, frames_getter, seconds: float, out_path: Path, renderer, cam):
    writer = imageio.get_writer(out_path, fps=FPS, macro_block_size=None)
    n = int(seconds * FPS)
    for _ in range(n):
        frames_getter()
        renderer.update_scene(data, camera=cam)
        writer.append_data(renderer.render())
    writer.close()
    print(f"已写 {out_path} ({n} 帧 / {seconds:.0f}s)")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "passive"
    OUT_DIR.mkdir(exist_ok=True)

    if mode == "passive":
        sys.path.insert(0, str(TRAIN))
        from duckstand.env import DuckStandEnv

        env = DuckStandEnv()
        renderer, cam = make_renderer(env.model)
        env.reset(seed=0)

        writer = imageio.get_writer(OUT_DIR / "stand_passive.mp4", fps=FPS, macro_block_size=None)
        n = int(6.0 * FPS)
        for _ in range(n):
            env.step(np.zeros(14))  # action=0 → 目标恒为 HOME，固件力矩环闭环
            renderer.update_scene(env.data, camera=cam)
            writer.append_data(renderer.render())
        writer.close()
        print(f"已写 {OUT_DIR / 'stand_passive.mp4'} ({n} 帧 / 6s)")
        renderer.close()

    elif mode == "policy":
        ckpt = sys.argv[2] if len(sys.argv) > 2 else str(
            TRAIN / "checkpoints" / "duck_stand_v02" / "final.zip")
        from stable_baselines3 import PPO
        from duckstand.env import DuckStandEnv

        env = DuckStandEnv()
        policy = PPO.load(ckpt)
        renderer, cam = make_renderer(env.model)

        obs, _ = env.reset(seed=7)
        writer = imageio.get_writer(OUT_DIR / "policy_1m.mp4", fps=FPS, macro_block_size=None)
        n = 0
        ep_step = 0
        while n < 6 * FPS:  # 最多 6 s
            a, _ = policy.predict(obs, deterministic=True)
            obs, r, term, trunc, info = env.step(a)
            renderer.update_scene(env.data, camera=cam)
            writer.append_data(renderer.render())
            n += 1
            ep_step += 1
            if term or trunc:
                print(f"回合存活 {ep_step / FPS:.2f}s ({ep_step} 步, 末态 z={info['z']:.3f})")
                ep_step = 0
                obs, _ = env.reset()
        writer.close()
        print(f"已写 {OUT_DIR / 'policy_1m.mp4'} ({n} 帧 / {n / FPS:.1f}s)")
        renderer.close()
    else:
        raise SystemExit(f"未知模式: {mode}（passive | policy）")


if __name__ == "__main__":
    main()
