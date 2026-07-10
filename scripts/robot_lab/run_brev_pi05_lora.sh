#!/usr/bin/env bash
set -euo pipefail

STEPS="${STEPS:-800}"
BATCH_SIZE="${BATCH_SIZE:-8}"
NUM_WORKERS="${NUM_WORKERS:-4}"
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/outputs/pi05-scenesmith-so101-sort-lora-v1}"
MODEL_REPO="${MODEL_REPO:-jakekinchen/pi05-scenesmith-so101-sort-lora-v1}"
BASE_POLICY="${BASE_POLICY:-Cache-SCA/pi05_teleop_sort_block}"
DATASET_REPO="${DATASET_REPO:-jakekinchen/scenesmith-so101-sort-causal-envelope-smoke}"
PUSH_TO_HUB="${PUSH_TO_HUB:-true}"
LOG_FREQ="${LOG_FREQ:-10}"
SAVE_FREQ="${SAVE_FREQ:-$STEPS}"
PEFT_R="${PEFT_R:-16}"
PEFT_ALPHA="${PEFT_ALPHA:-16}"
PEFT_TARGET_MODULES="${PEFT_TARGET_MODULES:-}"
USE_EXISTING_ADAPTER="${USE_EXISTING_ADAPTER:-false}"
LEARNING_RATE="${LEARNING_RATE:-5e-5}"
WEIGHT_DECAY="${WEIGHT_DECAY:-0.01}"
WARMUP_STEPS="${WARMUP_STEPS:-50}"
export SCENESMITH_GRIPPER_LOSS_WEIGHT="${SCENESMITH_GRIPPER_LOSS_WEIGHT:-1}"
export SCENESMITH_GRIPPER_ONLY_LOSS="${SCENESMITH_GRIPPER_ONLY_LOSS:-0}"
export SCENESMITH_TRAINABLE_PARAMETER_SUBSTRING="${SCENESMITH_TRAINABLE_PARAMETER_SUBSTRING:-}"
export SCENESMITH_TRAINABLE_OUTPUT_ROWS="${SCENESMITH_TRAINABLE_OUTPUT_ROWS:-}"

peft_args=()
if [[ "$USE_EXISTING_ADAPTER" != "true" ]]; then
  peft_args+=(
    "--peft.method_type=LORA"
    "--peft.r=$PEFT_R"
    "--peft.lora_alpha=$PEFT_ALPHA"
  )
  if [[ -n "$PEFT_TARGET_MODULES" ]]; then
    peft_args+=("--peft.target_modules=$PEFT_TARGET_MODULES")
  fi
fi

export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
export TOKENIZERS_PARALLELISM="false"
mkdir -p "$HOME/training-logs"

"$HOME/pi05-venv/bin/lerobot-train" \
  --policy.path="$BASE_POLICY" \
  --policy.repo_id="$MODEL_REPO" \
  --policy.push_to_hub="$PUSH_TO_HUB" \
  --policy.dtype=bfloat16 \
  --policy.gradient_checkpointing=true \
  --policy.compile_model=false \
  --policy.optimizer_lr="$LEARNING_RATE" \
  --policy.optimizer_weight_decay="$WEIGHT_DECAY" \
  --policy.scheduler_warmup_steps="$WARMUP_STEPS" \
  --policy.scheduler_decay_steps="$STEPS" \
  --dataset.repo_id="$DATASET_REPO" \
  --dataset.return_uint8=true \
  --rename_map='{"observation.images.top":"observation.images.base_0_rgb","observation.images.wrist":"observation.images.left_wrist_0_rgb"}' \
  "${peft_args[@]}" \
  --batch_size="$BATCH_SIZE" \
  --num_workers="$NUM_WORKERS" \
  --steps="$STEPS" \
  --save_freq="$SAVE_FREQ" \
  --log_freq="$LOG_FREQ" \
  --wandb.enable=false \
  --job_name=pi05-scenesmith-so101-sort-lora-v1 \
  --output_dir="$OUTPUT_DIR" \
  2>&1 | tee "$HOME/training-logs/$(basename "$OUTPUT_DIR").log"
