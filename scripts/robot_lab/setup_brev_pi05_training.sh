#!/usr/bin/env bash
set -euo pipefail

LEROBOT_COMMIT="e40b58a8dfa9e7b86918c374791599d070518d11"
SCENESMITH_PATCH="${SCENESMITH_LEROBOT_PATCH:-$HOME/pi05_gripper_loss_weight.patch}"
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

# This LeRobot revision imports its data-only templates directory as a package.
# Editable installs need the package marker for post-training Hub model cards.
touch "$HOME/lerobot/src/lerobot/templates/__init__.py"
if [[ -f "$SCENESMITH_PATCH" ]]; then
  if git -C "$HOME/lerobot" apply --reverse --check "$SCENESMITH_PATCH" 2>/dev/null; then
    echo "SceneSmith PI0.5 gripper-loss patch is already applied"
  else
    git -C "$HOME/lerobot" apply --check "$SCENESMITH_PATCH"
    git -C "$HOME/lerobot" apply "$SCENESMITH_PATCH"
  fi
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
