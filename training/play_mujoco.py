#!/usr/bin/env python3
"""单环境 MuJoCo/mjlab 策略回放；默认本地 Viser 界面。"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import importlib.metadata
import json
from pathlib import Path
import sys


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, help="显式选择兼容的 mjlab .pt 策略")
    parser.add_argument("--viewer", choices=("viser", "native"), default="viser",
                        help="默认 viser；native 为实验入口，本机 WSLg 软件渲染低速")
    parser.add_argument("--simple", action="store_true", help="使用原始碰撞简模")
    parser.add_argument("--port", type=int, default=8080, help="本地 Viser 端口，默认 8080")
    parser.add_argument("--device", default="cuda:0", help="默认 cuda:0，与现有策略环境一致")
    parser.add_argument("--velocity", type=float, default=0.0, help="前后速度，-0.2 至 0.2 m/s")
    parser.add_argument("--duration", type=float, help="初始化完成后运行指定墙钟秒数并退出")
    parser.add_argument("--metrics", type=Path, help="退出时保存后端计时 JSON")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port 必须在 1–65535")
    if not -0.2 <= args.velocity <= 0.2:
        parser.error("--velocity 必须在 -0.2 至 0.2 m/s")
    if args.duration is not None and not 0 < args.duration < float("inf"):
        parser.error("--duration 必须是有限正数")
    return args


def main():
    args = arguments()
    try:
        import torch
        import viser
        from mjlab.envs import ManagerBasedRlEnv
        from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
        from mjlab.utils.torch import configure_torch_backends
        from mjlab_duck.playback import DEFAULT_CHECKPOINT, make_playback_config
        from mjlab_duck.train_duck import duck_rl_cfg
        from mjlab_duck.viewer import DuckNativeViewer, DuckViserViewer, PlaybackMetrics
    except ImportError as exc:
        raise RuntimeError(
            "请使用现有 WSL 环境启动：在仓库运行 "
            "powershell.exe -File training/play-mujoco.ps1。"
            f" 缺少依赖：{exc}"
        ) from exc
    versions = {name: importlib.metadata.version(name)
                for name in ("mjlab", "mujoco", "viser", "rsl-rl-lib", "torch")}
    if versions["mjlab"] != "1.3.0":
        raise RuntimeError(f"此入口适配 mjlab 1.3.0；当前 {versions['mjlab']}，请使用 training/.venv-wsl。")
    checkpoint = (args.checkpoint or DEFAULT_CHECKPOINT).resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(f"找不到策略：{checkpoint}；请用 --checkpoint 指定兼容的 .pt 文件。")
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("WSL CUDA 不可用；请在已有 RTX 4080 的 WSL 环境运行 training/play-mujoco.ps1。")
    configure_torch_backends()
    cfg, model_path = make_playback_config(simple=args.simple, velocity=args.velocity)
    metadata = {
        "viewer": args.viewer, "checkpoint": str(checkpoint), "model": str(model_path),
        "versions": versions, "device": args.device, "num_envs": 1,
        "observation_dimensions": 49, "action_dimensions": 14,
        "requested_duration_seconds": args.duration,
    }
    metrics = PlaybackMetrics(metadata)
    env = viewer = server = None
    try:
        env = ManagerBasedRlEnv(cfg=cfg, device=args.device)
        agent_cfg = duck_rl_cfg()
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
        runner = MjlabOnPolicyRunner(wrapped, asdict(agent_cfg), device=args.device)
        runner.load(str(checkpoint), load_cfg={"actor": True}, strict=True, map_location=args.device)
        policy = runner.get_inference_policy(device=args.device)
        # 在计时/展示前完成首次推理和物理内核初始化，然后重置回起始状态。
        with torch.no_grad():
            wrapped.step(policy(wrapped.get_observations()))
        wrapped.reset()
        if args.device.startswith("cuda"):
            torch.cuda.synchronize(args.device)
        if args.viewer == "viser":
            server = viser.ViserServer(host="127.0.0.1", port=args.port, label="Duck · MuJoCo 仿真")
            viewer = DuckViserViewer(wrapped, policy, metrics=metrics, duration=args.duration,
                                    simple=args.simple, viser_server=server, frame_rate=60.0)
            metadata["url"] = f"http://127.0.0.1:{server.get_port()}"
            print(f"\n打开浏览器：{metadata['url']}\n仅仿真；Ctrl+C 或页面“退出”结束。", flush=True)
        else:
            print("native 为实验入口：本机 WSLg 当前使用 llvmpipe 软件渲染，"
                  "实时性未通过；日常观察建议使用默认 Viser。", flush=True)
            viewer = DuckNativeViewer(wrapped, policy, metrics=metrics, duration=args.duration,
                                     frame_rate=60.0)
        print(f"策略：{checkpoint.name} | 单环境 | 控制 50 Hz | 模型：{model_path.name}", flush=True)
        viewer.run()
    except BaseException as exc:
        metrics.error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        try:
            if viewer is not None and not viewer._playback_closed:
                viewer.close()
        finally:
            if env is not None:
                env.close()
            if server is not None:
                server.stop()
            metrics.finish(getattr(viewer, "_is_paused", False))
            report = metrics.report(0.02)
            if args.metrics is not None:
                args.metrics.parent.mkdir(parents=True, exist_ok=True)
                args.metrics.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"后端计时已保存：{args.metrics.resolve()}", flush=True)
            print(f"完成控制步：{report['counts'].get('running_control_steps', 0)}；"
                  f"场景完成：{report['counts'].get('scene_completed', 0)}；"
                  "浏览器 FPS 未测量。", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"回放失败：{error}", file=sys.stderr, flush=True)
        sys.exit(1)
