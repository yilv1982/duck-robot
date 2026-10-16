#!/usr/bin/env python3
"""duck v0 站立策略训练入口（SB3 PPO）。

用法（在 training/ 下）：
    .venv/Scripts/python.exe train.py --steps 200000
checkpoint 与日志写入 training/checkpoints/。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CallbackList, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from duckstand.env import DuckStandEnv


class LogStdCap(BaseCallback):
    def __init__(self, cap: float):
        super().__init__()
        self.cap = cap

    def _on_step(self) -> bool:
        return True

    def on_rollout_start(self):
        self.model.policy.log_std.data.clamp_(max=self.cap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=200_000)
    ap.add_argument("--envs", type=int, default=8)
    ap.add_argument("--continue-from", type=str, default=None, help="续训的 checkpoint 路径")
    ap.add_argument("--run-name", type=str, default="duck_stand_v0")
    ap.add_argument("--log-std", type=float, default=None,
                    help="续训时覆盖策略初始 log_std（如 -3.0），压低探索噪声")
    ap.add_argument("--log-std-cap", type=float, default=None,
                    help="每次更新后钳制 log_std 上限（如 -2.66≈std 0.07），"
                         "防 PPO 自适应调大噪声（v0.3b/d 学崩根因）")
    args = ap.parse_args()

    out_dir = Path(__file__).parent / "checkpoints" / args.run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    venv = DummyVecEnv([lambda: Monitor(DuckStandEnv()) for _ in range(args.envs)])

    if args.continue_from:
        model = PPO.load(args.continue_from, env=venv)
        if args.log_std is not None:
            model.policy.log_std.data.fill_(args.log_std)
            print(f"续训: {args.continue_from} (log_std 覆盖为 {args.log_std})")
        else:
            print(f"续训: {args.continue_from}")
    else:
        model = PPO(
            "MlpPolicy", venv,
            # std≈0.15：与 ACTION_SCALE=0.1 组合后目标抖动 ±0.015 rad，
            # 随机基线存活 ~3s，保证初始梯度信号（大幅 std 下全部 0.5s 内摔死）。
            policy_kwargs=dict(net_arch=[128, 128], log_std_init=-1.0),
            n_steps=512, batch_size=512, n_epochs=5,
            learning_rate=3e-4, gamma=0.99, gae_lambda=0.95,
            ent_coef=0.0, verbose=1,
        )

    ckpt_cb = CheckpointCallback(save_freq=20_000, save_path=str(out_dir), name_prefix="ckpt")
    callbacks = [ckpt_cb]
    if args.log_std_cap is not None:
        callbacks.append(LogStdCap(args.log_std_cap))
    model.learn(total_timesteps=args.steps, callback=CallbackList(callbacks))
    model.save(out_dir / "final")
    print(f"已保存: {out_dir / 'final'}.zip")


if __name__ == "__main__":
    main()
