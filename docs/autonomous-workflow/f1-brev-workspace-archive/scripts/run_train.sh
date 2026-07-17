#!/usr/bin/env bash
set -euo pipefail

F1_ROOT="${F1_ROOT:-$HOME/sim-link-f1}"
PYTHON="$F1_ROOT/deps/lerobot/.venv/bin/python"
OUTPUT="$F1_ROOT/outputs/training"
DATASET="$F1_ROOT/inputs/r0_dataset"
MODEL="$F1_ROOT/inputs/pi05_base"
LOG="$F1_ROOT/receipts/TRAINING.log"
PID_FILE="$F1_ROOT/receipts/TRAINING.pid"

[[ -f "$F1_ROOT/receipts/REMOTE_PREFLIGHT.json" ]] || { echo "remote preflight receipt missing" >&2; exit 1; }
[[ ! -e "$OUTPUT" ]] || { echo "training output already exists" >&2; exit 1; }
[[ ! -e "$PID_FILE" ]] || { echo "training PID marker already exists" >&2; exit 1; }

export CUDA_VISIBLE_DEVICES=0
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$F1_ROOT/deps/lerobot/src:$F1_ROOT/sim-link"
export HF_HOME="$F1_ROOT/huggingface"
export WANDB_DISABLED=true

nohup "$PYTHON" -m lerobot.scripts.lerobot_train \
  --dataset.repo_id=scenesmith/t20-42-r0-anchor-grasp-train \
  --dataset.root="$DATASET" \
  --dataset.image_transforms.enable=false \
  --dataset.return_uint8=true \
  --dataset.video_backend=pyav \
  --policy.path="$MODEL" \
  --policy.device=cuda \
  --policy.dtype=bfloat16 \
  --policy.compile_model=true \
  --policy.gradient_checkpointing=true \
  --policy.freeze_vision_encoder=false \
  --policy.train_expert_only=false \
  --policy.scheduler_decay_steps=5000 \
  --policy.normalization_mapping='{"ACTION":"MEAN_STD","STATE":"MEAN_STD","VISUAL":"IDENTITY"}' \
  --policy.push_to_hub=false \
  --batch_size=8 \
  --num_workers=2 \
  --steps=5000 \
  --seed=20260717 \
  --env_eval_freq=0 \
  --eval_steps=0 \
  --log_freq=10 \
  --save_checkpoint=true \
  --save_freq=1000 \
  --output_dir="$OUTPUT" \
  --job_name=f1_pi05_r0_full_5k \
  --wandb.enable=false \
  --job.target=local \
  >"$LOG" 2>&1 &

pid=$!
printf '%s\n' "$pid" > "$PID_FILE"
printf 'launched pid=%s log=%s\n' "$pid" "$LOG"
