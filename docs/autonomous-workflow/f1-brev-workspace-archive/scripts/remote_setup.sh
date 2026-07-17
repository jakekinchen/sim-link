#!/usr/bin/env bash
set -euo pipefail

F1_ROOT="${F1_ROOT:-$HOME/sim-link-f1}"
LEROBOT_COMMIT="e40b58a8dfa9e7b86918c374791599d070518d11"
SO_ARM100_COMMIT="fda892cba81032c46c40976a48c9ceadbf40a9ca"
PATCH="$F1_ROOT/sim-link/scripts/robot_lab/patches/pi05_gripper_loss_weight.patch"
PATCH_SHA="efe912e3cf75c76a3b0a01d2baec8f0856ce2e2a981f4845978f0e9e34155284"

mkdir -p "$F1_ROOT/deps" "$F1_ROOT/inputs" "$F1_ROOT/outputs" "$F1_ROOT/receipts"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.12

if [[ ! -d "$F1_ROOT/deps/lerobot/.git" ]]; then
  git init "$F1_ROOT/deps/lerobot"
  git -C "$F1_ROOT/deps/lerobot" remote add origin https://github.com/huggingface/lerobot.git
fi
git -C "$F1_ROOT/deps/lerobot" fetch --depth 1 origin "$LEROBOT_COMMIT"
git -C "$F1_ROOT/deps/lerobot" checkout --detach FETCH_HEAD

actual_patch_sha="$(sha256sum "$PATCH" | awk '{print $1}')"
[[ "$actual_patch_sha" == "$PATCH_SHA" ]] || { echo "LeRobot patch hash mismatch" >&2; exit 1; }
git -C "$F1_ROOT/deps/lerobot" apply --check "$PATCH"
git -C "$F1_ROOT/deps/lerobot" apply "$PATCH"

if [[ ! -d "$F1_ROOT/deps/SO-ARM100/.git" ]]; then
  git init "$F1_ROOT/deps/SO-ARM100"
  git -C "$F1_ROOT/deps/SO-ARM100" remote add origin https://github.com/TheRobotStudio/SO-ARM100.git
fi
git -C "$F1_ROOT/deps/SO-ARM100" fetch --depth 1 origin "$SO_ARM100_COMMIT"
git -C "$F1_ROOT/deps/SO-ARM100" checkout --detach FETCH_HEAD

mkdir -p "$F1_ROOT/sim-link/external"
ln -s "$F1_ROOT/deps/SO-ARM100" "$F1_ROOT/sim-link/external/SO-ARM100"

uv sync \
  --project "$F1_ROOT/deps/lerobot" \
  --python 3.12 \
  --frozen \
  --no-dev \
  --extra training \
  --extra pi \
  --extra peft

uv pip install \
  --python "$F1_ROOT/deps/lerobot/.venv/bin/python" \
  "mujoco==3.3.5" \
  "pyarrow==25.0.0"

"$F1_ROOT/deps/lerobot/.venv/bin/python" - <<'PY'
import importlib.metadata as m
import torch
names = ["lerobot", "torch", "torchvision", "transformers", "datasets", "numpy", "Pillow", "pyarrow", "mujoco", "peft"]
print({name: m.version(name) for name in names})
print({"cuda": torch.cuda.is_available(), "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None})
if not torch.cuda.is_available():
    raise SystemExit("CUDA unavailable")
PY
