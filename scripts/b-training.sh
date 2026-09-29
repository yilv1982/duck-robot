#!/usr/bin/env bash
# Linux/WSL entry point for the XL330 flat-ground training task.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: bash scripts/b-training.sh MODE [ARGS]
  check                              Check CUDA, dependencies and package origin
  list                               List registered training tasks
  smoke                              Train ONLY 64 environments / 5 iterations
  play CHECKPOINT [native|viser]      Play one environment (default: native)
  export CHECKPOINT [OUTPUT.onnx]     Export (default: caller's ./output.onnx)
  tensorboard [PORT]                  Serve 127.0.0.1 only (default: 6007)
  -h, --help                         Show this help

Task: Mjlab-Velocity-Flat-MicroDuck (XL330, NOT HD1910)
Paths are Linux paths, relative to the caller's working directory.
Export requires an existing parent directory and refuses existing outputs.
No implicit long training, hardware control, or system package installation.
USAGE
}

die() { printf 'Error: %s\n' "$*" >&2; exit 2; }

[[ $# -gt 0 ]] || { usage >&2; exit 2; }
mode=$1
shift
case "$mode" in
    -h|--help) [[ $# -eq 0 ]] || die 'Help takes no arguments.'; usage; exit 0 ;;
    check|list|smoke) [[ $# -eq 0 ]] || die "$mode takes no arguments." ;;
    play|export) [[ $# -ge 1 && $# -le 2 ]] || die "$mode requires CHECKPOINT and at most one optional argument." ;;
    tensorboard) [[ $# -le 1 ]] || die 'tensorboard accepts at most one port.' ;;
    *) usage >&2; die "Unknown mode: $mode" ;;
esac

[[ $(uname -s) == Linux ]] || die 'Run this script in Linux or WSL Ubuntu, not Windows Bash.'
command -v realpath >/dev/null || die 'GNU realpath is required.'
[[ -n ${HOME:-} && $HOME == /* ]] || die 'HOME must be an absolute Linux path.'

# Resolve all user paths BEFORE changing directory to the training project.
checkpoint=''
output=''
viewer=''
port=''
case "$mode" in
    play|export)
        [[ -n $1 && -f $1 && -r $1 ]] || die "Checkpoint is not a readable file: $1"
        checkpoint=$(realpath -e -- "$1")
        if [[ $mode == play ]]; then
            viewer=${2-native}
            [[ $viewer == native || $viewer == viser ]] || die 'Viewer must be native or viser.'
        else
            output=${2-output.onnx}
            [[ -n $output && $output == *.onnx ]] || die 'Output must be a nonempty .onnx path.'
            [[ ! -e $output && ! -L $output ]] || die "Refusing existing output; choose a new path: $output"
            output=$(realpath -m -- "$output")
            [[ -d $(dirname -- "$output") && -w $(dirname -- "$output") ]] || die 'Output parent directory must exist and be writable.'
        fi
        ;;
    tensorboard)
        port=${1-6007}
        [[ $port =~ ^[0-9]{1,5}$ ]] || die 'Port must be an integer from 1 to 65535.'
        port=$((10#$port))
        (( port >= 1 && port <= 65535 )) || die 'Port must be an integer from 1 to 65535.'
        ;;
esac

script_path=$(realpath -e -- "${BASH_SOURCE[0]}")
project_root=$(cd -- "$(dirname -- "$script_path")/.." && pwd -P)
training_dir="$project_root/microduck-replica/software/training"
[[ -f $training_dir/pyproject.toml && -f $training_dir/uv.lock ]] || die "Training project or lockfile missing: $training_dir"

# Every mode uses the same Linux environment and the existing lockfile.
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/duck-robot-training"
export UV_HTTP_TIMEOUT=600
export UV_LINK_MODE=copy
if command -v uv >/dev/null 2>&1; then
    uv_bin=$(command -v uv)
elif [[ -x $HOME/.local/bin/uv ]]; then
    uv_bin="$HOME/.local/bin/uv"
else
    die 'Linux uv is missing. Install it separately into ~/.local/bin or PATH.'
fi
readonly task='Mjlab-Velocity-Flat-MicroDuck'
cd -- "$training_dir"
printf 'Task: %s\nTraining directory: %s\nEnvironment: %s\n' "$task" "$training_dir" "$UV_PROJECT_ENVIRONMENT"

case "$mode" in
    check)
        "$uv_bin" run --frozen python - <<'PY'
import importlib
import importlib.metadata as metadata
import os
from pathlib import Path
import sys

print(f"Python: {sys.version.split()[0]} ({sys.executable})", flush=True)
expected_env = Path(os.environ["UV_PROJECT_ENVIRONMENT"]).resolve()
if Path(sys.prefix).resolve() != expected_env:
    raise SystemExit(f"Wrong environment: {sys.prefix}; expected {expected_env}")
for distribution, module in (
    ("mjlab-microduck", "mjlab_microduck"),
    ("mjlab", "mjlab"),
    ("torch", "torch"),
    ("warp-lang", "warp"),
    ("mujoco", "mujoco"),
    ("mujoco-warp", "mujoco_warp"),
    ("rsl-rl-lib", "rsl_rl"),
    ("better-actuator-models", "bam"),
    ("onnx", "onnx"),
    ("onnxruntime", "onnxruntime"),
    ("tensorboard", "tensorboard"),
):
    print(f"{distribution}: {metadata.version(distribution)}", flush=True)
    importlib.import_module(module)

import mjlab_microduck
origin = Path(mjlab_microduck.__file__).resolve()
expected_origin = (Path.cwd() / "src/mjlab_microduck/__init__.py").resolve()
print(f"Training package: {origin}", flush=True)
if origin != expected_origin:
    raise SystemExit(f"Wrong training package; expected {expected_origin}")

import mjlab.tasks
from mjlab.tasks.registry import list_tasks
if "Mjlab-Velocity-Flat-MicroDuck" not in list_tasks():
    raise SystemExit("XL330 flat task is not registered")

import torch
print(f"PyTorch CUDA runtime: {torch.version.cuda}", flush=True)
if not torch.cuda.is_available():
    raise SystemExit("CUDA is unavailable to PyTorch")
print(f"CUDA device count: {torch.cuda.device_count()}", flush=True)
print(f"CUDA device 0: {torch.cuda.get_device_name(0)}", flush=True)
torch.ones(1, device="cuda:0").sum().item()
torch.cuda.synchronize()

import warp as wp
wp.init()
if not wp.get_cuda_devices():
    raise SystemExit("CUDA is unavailable to Warp")
print("Check passed: dependency imports, local task and CUDA are available.")
PY
        ;;
    list)
        "$uv_bin" run --frozen python -m mjlab.scripts.list_envs
        ;;
    smoke)
        run_name="b-xl330-smoke-$(date -u +%Y%m%dT%H%M%S%N)-$$-$RANDOM"
        printf 'Smoke run name: %s\nLogs: %s/logs/rsl_rl/velocity\n' "$run_name" "$training_dir"
        "$uv_bin" run --frozen train "$task" \
            --env.scene.num-envs 64 --agent.max-iterations 5 \
            --agent.logger tensorboard --agent.run-name "$run_name"
        ;;
    play)
        "$uv_bin" run --frozen play "$task" \
            --checkpoint-file "$checkpoint" --num-envs 1 --viewer "$viewer"
        ;;
    export)
        # Recheck after uv discovery and directory switching; never knowingly overwrite.
        [[ ! -e $output && ! -L $output ]] || die "Refusing existing output: $output"
        printf 'Export destination: %s\n' "$output"
        "$uv_bin" run --frozen python scripts/export.py "$task" \
            --checkpoint-file "$checkpoint" --num-envs 1 --onnx-file "$output"
        ;;
    tensorboard)
        printf 'TensorBoard: http://127.0.0.1:%s (Ctrl+C to stop)\n' "$port"
        "$uv_bin" run --frozen tensorboard \
            --logdir "$training_dir/logs/rsl_rl/velocity" --host 127.0.0.1 --port "$port"
        ;;
esac
