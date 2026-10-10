#!/usr/bin/env bash
# A-only WSL entry point. Never installs dependencies or resumes a checkpoint.
set -euo pipefail
readonly ROOT=/mnt/c/Projects/duck-robot
readonly PROJECT="$ROOT/references/microduck-build-tutorial/mjlab_microduck"
readonly VENV=/home/yilv/.venvs/duck-robot-a-training
readonly PYTHON="$VENV/bin/python"
readonly TASK=Mjlab-Velocity-Microduck

usage() {
  cat <<'HELP'
Usage: bash scripts/a-training.sh COMMAND [OPTIONS]
  check       Verify A-only interpreter/source, locked core versions and task.
  list        List registered mjlab tasks (no simulation).
  smoke       Fresh CUDA run: 64 envs / 5 iterations, expected model_4.pt.
  train       --num-envs N --max-iterations N (both explicit; fresh CUDA run).
  export      --checkpoint FILE --output NEW.onnx [--device cuda:0]
No implicit installs, automatic long training, checkpoint discovery or overwrite.
Relative export paths are interpreted relative to the caller's working directory.
HELP
}
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 2; }
[[ $# -gt 0 ]] || { usage; exit 2; }
command_name=$1; shift
case "$command_name" in
  -h|--help|help) usage; exit 0 ;;
  check|list|smoke|train|export) ;;
  *) fail "Unknown command: $command_name" ;;
esac
if [[ "$command_name" == check || "$command_name" == list || "$command_name" == smoke ]]; then
  [[ $# -eq 0 ]] || fail "$command_name accepts no options"
fi
num_envs= iterations=
if [[ "$command_name" == train ]]; then
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --num-envs)
        [[ $# -ge 2 && -z "$num_envs" ]] || fail 'Specify --num-envs once with a value'
        num_envs=$2; shift 2 ;;
      --max-iterations)
        [[ $# -ge 2 && -z "$iterations" ]] || fail 'Specify --max-iterations once with a value'
        iterations=$2; shift 2 ;;
      *) fail "Unknown train option: $1" ;;
    esac
  done
  [[ "$num_envs" =~ ^[1-9][0-9]*$ && "$iterations" =~ ^[1-9][0-9]*$ ]] ||
    fail 'train requires explicit positive --num-envs N and --max-iterations N'
fi
[[ -x "$PYTHON" ]] || fail "A venv missing: $VENV (install explicitly with README instructions)"
[[ "$(realpath -- "${BASH_SOURCE[0]}")" == "$ROOT/scripts/a-training.sh" ]] ||
  fail 'Run the fixed A entry point, not a relocated copy'
unset PYTHONHOME PYTHONPATH VIRTUAL_ENV
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export MUJOCO_GL=egl
# -I also ignores user site and CWD imports. -B avoids modifying robot/tasks.
"$PYTHON" -I -B - <<'PY'
import importlib.metadata as md
import json
from pathlib import Path
import sys
import mjlab_microduck
expected_prefix = Path('/home/yilv/.venvs/duck-robot-a-training')
expected_source = Path('/mnt/c/Projects/duck-robot/references/microduck-build-tutorial/mjlab_microduck/src/mjlab_microduck/__init__.py')
if Path(sys.prefix) != expected_prefix or Path(sys.prefix).resolve() != expected_prefix:
    raise SystemExit(f'Wrong sys.prefix: {sys.prefix}')
if Path(mjlab_microduck.__file__) != expected_source or expected_source.resolve() != expected_source:
    raise SystemExit(f'Wrong A source: {mjlab_microduck.__file__}')
for name, expected in {'mjlab': '1.3.0', 'torch': '2.9.1', 'warp-lang': '1.12.0', 'mujoco': '3.10.0', 'better-actuator-models': '1.0.0'}.items():
    actual = md.version(name)
    if actual != expected:
        raise SystemExit(f'{name}: expected {expected}, got {actual}')
bam = json.loads(md.distribution('better-actuator-models').read_text('direct_url.json') or '{}')
if bam.get('vcs_info', {}).get('commit_id') != '0007411bd82c48f1bc12ae8382f98e4d8b879c95':
    raise SystemExit(f'Unexpected BAM provenance: {bam}')
print(f'[A] prefix={sys.prefix}\n[A] source={mjlab_microduck.__file__}', flush=True)
PY

case "$command_name" in
  check|list)
    "$PYTHON" -I -B - "$command_name" <<'PY'
import importlib.metadata as md
import sys
# Explicit import turns failed plugin discovery into a hard failure.
import mjlab
import mjlab_microduck.tasks
from mjlab.tasks.registry import list_tasks, load_env_cfg, load_rl_cfg
names = list_tasks()
if 'Mjlab-Velocity-Microduck' not in names:
    raise SystemExit('A task is not registered')
if sys.argv[1] == 'list':
    print('\n'.join(names))
else:
    for name in ('mjlab', 'torch', 'warp-lang', 'mujoco', 'better-actuator-models', 'onnx', 'onnxruntime', 'tensorboard'):
        print(f'{name}=={md.version(name)}')
    cfg = load_env_cfg('Mjlab-Velocity-Microduck')
    rl = load_rl_cfg('Mjlab-Velocity-Microduck')
    if not rl.actor.obs_normalization:
        raise SystemExit('A actor normalizer must be enabled')
    print('Task: Mjlab-Velocity-Microduck; actor normalizer: enabled')
    print('Static check only: GPU training and ONNX parity are NOT tested here.')
PY
    ;;
  export)
    exec "$PYTHON" -I -B -m mjlab_microduck.scripts.export_onnx "$@"
    ;;
  smoke|train)
    "$PYTHON" -I -B - <<'PY'
import torch
if not torch.cuda.is_available():
    raise SystemExit('CUDA is required; mjwarp CPU simulation is not a supported fallback')
PY
    if [[ "$command_name" == smoke ]]; then num_envs=64; iterations=5; fi
    run_name="a-${command_name}-$(date -u +%Y%m%dT%H%M%S%N)-$$"
    printf '[A] Fresh run: %s; envs=%s; iterations=%s\n' "$run_name" "$num_envs" "$iterations"
    printf '[A] Expected final checkpoint: model_%s.pt\n' "$((iterations - 1))"
    cd -- "$PROJECT"
    exec "$PYTHON" -I -B -m mjlab.scripts.train "$TASK" \
      --env.scene.num-envs "$num_envs" \
      --agent.max-iterations "$iterations" \
      --agent.resume False \
      --agent.logger tensorboard \
      --agent.upload-model False \
      --agent.run-name "$run_name"
    ;;
esac
