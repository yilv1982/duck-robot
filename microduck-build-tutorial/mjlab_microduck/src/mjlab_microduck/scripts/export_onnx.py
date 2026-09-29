# Copyright 2026 Marc Duclusaud
# Licensed under the Apache License, Version 2.0.
"""Safely export a new A checkpoint, preserving normalization and validating parity.

No checkpoint discovery, legacy pickle loading, deployment writes or overwrites.
Use a-training.sh export --checkpoint FILE --output NEW.onnx (default cuda:0).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as importlib_metadata
import json
import os
from pathlib import Path
import sys
import tempfile

TASK = "Mjlab-Velocity-Microduck"
ROOT = Path("/mnt/e/Projects/duck-robot")
PROJECT = ROOT / "microduck-build-tutorial/mjlab_microduck"
VENV = Path("/home/yilv/.venvs/duck-robot-a-training")
SOURCE = PROJECT / "src/mjlab_microduck/__init__.py"
NUM_OBS, NUM_ACTIONS = 51, 14
# Original deployment's OBSERVATION_DOF_ORDER, not motor-ID order.
JOINT_ORDER = [
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
    "neck_pitch", "head_pitch", "head_yaw", "head_roll",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
]


def verify_source() -> None:
    import mjlab_microduck

    if Path(sys.prefix) != VENV or VENV.resolve() != VENV:
        raise RuntimeError(f"Wrong A interpreter prefix: {sys.prefix}")
    if Path(mjlab_microduck.__file__) != SOURCE or SOURCE.resolve() != SOURCE:
        raise RuntimeError(f"Wrong A source: {mjlab_microduck.__file__}")
    expected_versions = {
        "mjlab": "1.3.0", "torch": "2.9.1", "warp-lang": "1.12.0",
        "mujoco": "3.10.0", "better-actuator-models": "1.0.0",
    }
    for name, version in expected_versions.items():
        if importlib_metadata.version(name) != version:
            raise RuntimeError(f"Unexpected {name} version; reinstall using uv sync --locked")
    bam = json.loads(importlib_metadata.distribution("better-actuator-models").read_text("direct_url.json") or "{}")
    if bam.get("vcs_info", {}).get("commit_id") != "0007411bd82c48f1bc12ae8382f98e4d8b879c95":
        raise RuntimeError("BAM is not the fixed A doc commit")


def validate_paths(checkpoint: Path, output: Path) -> tuple[Path, Path]:
    # lexists also rejects broken symlinks. Check before resolving the target.
    output = output.expanduser().absolute()
    if os.path.lexists(output):
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    if output.name.lower() in {"walk.onnx", "velocity.pt", "constants.py"}:
        raise ValueError("Original deployment filenames are protected")
    output = output.resolve()
    protected = (
        ROOT / "microduck-replica",
        ROOT / "microduck-build-tutorial/microduck",
        PROJECT / "src",
        Path("/home/yilv/.venvs"),
    )
    # /mnt/e is Windows-backed: protect case variants as well as symlink aliases.
    output_key = str(output).casefold()
    if any(
        output_key == str(path.resolve()).casefold()
        or output_key.startswith(str(path.resolve()).casefold() + "/")
        for path in protected
    ):
        raise ValueError(f"Refusing export into deployment, sources or a venv: {output}")
    if output.suffix.lower() != ".onnx":
        raise ValueError("--output must name a new .onnx file")
    checkpoint = checkpoint.expanduser().resolve(strict=True)
    if not checkpoint.is_file() or checkpoint.suffix != ".pt":
        raise ValueError(f"--checkpoint must be an existing .pt file: {checkpoint}")
    if checkpoint.name.lower() == "velocity.pt":
        raise ValueError("Use the new training checkpoint, not original velocity.pt")
    return checkpoint, output


def load_actor(runner, checkpoint: Path):
    import torch

    # Do NOT call runner.load: mjlab 1.3.0 hardcodes weights_only=False there.
    loaded = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(loaded, dict) or "actor_state_dict" not in loaded:
        raise ValueError("Expected a fresh rsl-rl checkpoint with actor_state_dict; no legacy migration")
    state = loaded["actor_state_dict"]
    if not isinstance(state, dict):
        raise ValueError("actor_state_dict must be a tensor mapping")
    required = {"obs_normalizer._mean", "obs_normalizer._var", "obs_normalizer._std", "obs_normalizer.count"}
    if not required.issubset(state):
        raise ValueError("Checkpoint is missing actor normalizer state")
    for name, value in state.items():
        if not isinstance(value, torch.Tensor) or not torch.isfinite(value).all():
            raise ValueError(f"Invalid or non-finite actor state: {name}")
    runner.alg.load(loaded, load_cfg={"actor": True}, strict=True)
    actor = runner.alg.get_policy()
    actor.eval()
    if isinstance(actor.obs_normalizer, torch.nn.Identity):
        raise ValueError("Actor normalizer was disabled")
    for name in required:
        torch.testing.assert_close(actor.state_dict()[name].cpu(), state[name], rtol=0, atol=0)
    if actor.obs_dim != NUM_OBS:
        raise ValueError(f"Expected {NUM_OBS} actor observations, got {actor.obs_dim}")
    return actor


def build_metadata(env, checkpoint: Path) -> dict:
    import torch
    from mjlab.rl.exporter_utils import get_base_metadata

    metadata = get_base_metadata(env, run_path=checkpoint.parent.name)
    action_names = list(env.action_manager.get_term("joint_pos").target_names)
    if metadata["joint_names"] != JOINT_ORDER or action_names != JOINT_ORDER:
        raise ValueError(f"Joint order mismatch: robot={metadata['joint_names']}, action={action_names}")
    # Validate the actual resolved observation joint selection, not just names in a config.
    robot_names = list(env.scene["robot"].joint_names)
    for term in ("joint_pos", "joint_vel"):
        entity_cfg = env.observation_manager.get_term_cfg("actor", term).params["asset_cfg"]
        ids = entity_cfg.joint_ids
        if isinstance(ids, slice):
            names = robot_names[ids]
        else:
            names = [robot_names[int(i)] for i in ids]
        if names != JOINT_ORDER:
            raise ValueError(f"{term} observation joint order mismatch: {names}")
    for key in ("default_joint_pos", "joint_stiffness", "joint_damping"):
        values = metadata[key]
        if len(values) != NUM_ACTIONS or not torch.isfinite(torch.tensor(values)).all():
            raise ValueError(f"Invalid {key} metadata")
    with checkpoint.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    metadata.update({
        "task": TASK,
        "num_observations": NUM_OBS,
        "num_actions": NUM_ACTIONS,
        "action_joint_names": action_names,
        "observation_joint_names": JOINT_ORDER,
        "normalizer_included": "true",
        "checkpoint_sha256": digest,
        "validation": "ONNX checker + ORT CPU + deterministic actor parity; 3 samples",
    })
    return metadata


def validate_onnx(path: Path, actor, observations) -> float:
    import numpy as np
    import onnx
    import onnxruntime as ort
    import torch

    model = onnx.load(str(path))
    onnx.checker.check_model(model, full_check=True)
    metadata = {item.key: item.value for item in model.metadata_props}
    for key in ("joint_names", "action_joint_names", "observation_joint_names"):
        if metadata.get(key, "").split(",") != JOINT_ORDER:
            raise ValueError(f"Export metadata lost joint ordering: {key}")
    if metadata.get("normalizer_included") != "true":
        raise ValueError("Missing normalizer metadata")
    session_options = ort.SessionOptions()
    session_options.intra_op_num_threads = 1
    session_options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(path), sess_options=session_options, providers=["CPUExecutionProvider"])
    inputs, outputs = session.get_inputs(), session.get_outputs()
    if len(inputs) != 1 or inputs[0].shape != [1, NUM_OBS] or inputs[0].type != "tensor(float)":
        raise ValueError(f"Expected one float32 [1, {NUM_OBS}] ONNX input")
    if len(outputs) != 1 or outputs[0].shape != [1, NUM_ACTIONS] or outputs[0].type != "tensor(float)":
        raise ValueError(f"Expected one float32 [1, {NUM_ACTIONS}] ONNX output")
    groups = list(actor.obs_groups)
    sample = torch.cat([observations[key] for key in groups], dim=-1).detach().cpu().numpy()
    if sample.shape != (1, NUM_OBS):
        raise ValueError(f"Invalid environment observation shape: {sample.shape}")
    samples = [sample, np.zeros_like(sample), np.random.default_rng(0).normal(0, 0.2, sample.shape).astype(np.float32)]
    max_error = 0.0
    with torch.inference_mode():
        for index, sample in enumerate(samples):
            if not np.isfinite(sample).all():
                raise ValueError(f"Non-finite sample {index}")
            actor_obs = observations.clone()
            offset = 0
            for key in groups:
                width = observations[key].shape[-1]
                actor_obs[key] = torch.as_tensor(sample[:, offset:offset + width], device=observations[key].device)
                offset += width
            # This is the regular actor forward path, NOT its ONNX/export wrapper.
            expected = actor(actor_obs, stochastic_output=False).detach().cpu().numpy()
            actual = session.run([outputs[0].name], {inputs[0].name: sample})[0]
            if actual.shape != (1, NUM_ACTIONS) or not np.isfinite(actual).all() or not np.isfinite(expected).all():
                raise ValueError(f"Invalid actor/ORT actions for sample {index}")
            np.testing.assert_allclose(actual, expected, rtol=1e-4, atol=1e-5, err_msg=f"actor/ORT sample {index}")
            max_error = max(max_error, float(np.max(np.abs(actual - expected))))
    print(f"[OK] ONNX checker, ORT 51/14 finite, joint metadata, 3 actor comparisons; max_abs_error={max_error:.8g}")
    return max_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cuda:0", help="CUDA simulation device (default: cuda:0; no CPU fallback)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify_source()
    checkpoint, output = validate_paths(args.checkpoint, args.output)
    import torch
    if not args.device.startswith("cuda:") or not torch.cuda.is_available():
        raise RuntimeError("Export requires CUDA for the single mjwarp env; CPU simulation is unsupported")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.set_float32_matmul_precision("highest")
    import mjlab
    import mjlab_microduck.tasks  # Explicit failure if A plugin registration failed.
    from dataclasses import asdict
    from mjlab.envs import ManagerBasedRlEnv
    from mjlab.rl import RslRlVecEnvWrapper
    from mjlab.rl.exporter_utils import attach_metadata_to_onnx
    from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

    cfg = load_env_cfg(TASK, play=True)
    cfg.scene.num_envs = 1
    agent_cfg = load_rl_cfg(TASK)
    agent_cfg.resume = False
    agent_cfg.logger = "tensorboard"
    agent_cfg.upload_model = False
    env = None
    try:
        env = ManagerBasedRlEnv(cfg=cfg, device=args.device)
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
        if wrapped.num_envs != 1 or wrapped.num_actions != NUM_ACTIONS:
            raise ValueError("Export requires exactly one environment with 14 actions")
        runner_cls = load_runner_cls(TASK)
        if runner_cls is None:
            raise RuntimeError("A task must register its mjlab runner")
        runner = runner_cls(wrapped, asdict(agent_cfg), device=args.device)
        actor = load_actor(runner, checkpoint)
        observations = wrapped.get_observations()
        metadata = build_metadata(env, checkpoint)
        # Work in the target filesystem, then atomically publish WITHOUT replacing.
        # Do not use os.replace/rename: those can silently overwrite a racing writer.
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".a-export-", dir=output.parent) as staging:
            staged = Path(staging) / "policy.onnx"
            runner.export_policy_to_onnx(staging, staged.name)
            attach_metadata_to_onnx(str(staged), metadata)
            validate_onnx(staged, actor, observations)
            os.link(staged, output, follow_symlinks=False)
        print(f"[OK] Exported new policy: {output}")
    finally:
        if env is not None:
            env.close()


if __name__ == "__main__":
    main()
