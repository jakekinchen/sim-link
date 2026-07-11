#!/usr/bin/env bash
set -euo pipefail

LEROBOT_COMMIT="e40b58a8dfa9e7b86918c374791599d070518d11"
SCENESMITH_PATCH="${SCENESMITH_LEROBOT_PATCH:-$HOME/pi05_gripper_loss_weight.patch}"
SCENESMITH_PATCH_SHA256="efe912e3cf75c76a3b0a01d2baec8f0856ce2e2a981f4845978f0e9e34155284"
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

uv python install 3.12
if [[ ! -d "$HOME/pi05-venv" ]]; then
  uv venv --python 3.12 "$HOME/pi05-venv"
fi

if [[ ! -d "$HOME/lerobot/.git" ]]; then
  mkdir -p "$HOME/lerobot"
  git -C "$HOME/lerobot" init
  git -C "$HOME/lerobot" remote add origin https://github.com/huggingface/lerobot.git
fi
git -C "$HOME/lerobot" fetch --depth 1 origin "$LEROBOT_COMMIT"
git -C "$HOME/lerobot" checkout --detach FETCH_HEAD

if [[ ! -f "$SCENESMITH_PATCH" ]]; then
  echo "Missing required SceneSmith LeRobot patch: $SCENESMITH_PATCH" >&2
  exit 1
fi
actual_patch_sha256="$(shasum -a 256 "$SCENESMITH_PATCH" | awk '{print $1}')"
if [[ "$actual_patch_sha256" != "$SCENESMITH_PATCH_SHA256" ]]; then
  echo "SceneSmith LeRobot patch identity mismatch" >&2
  exit 1
fi
if git -C "$HOME/lerobot" apply --reverse --check "$SCENESMITH_PATCH" 2>/dev/null; then
  echo "SceneSmith PI0.5 patch is already applied"
else
  git -C "$HOME/lerobot" apply --check "$SCENESMITH_PATCH"
  git -C "$HOME/lerobot" apply "$SCENESMITH_PATCH"
fi

uv pip install --python "$HOME/pi05-venv/bin/python" \
  -e "$HOME/lerobot[training,pi,peft]"

"$HOME/pi05-venv/bin/python" - <<'PY'
import torch
import lerobot
import peft

print(
    {
        "torch": torch.__version__,
        "lerobot": lerobot.__version__,
        "peft": peft.__version__,
        "cuda": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
)
if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available after environment setup")
PY
