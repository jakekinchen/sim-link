#!/usr/bin/env python3
"""Run a bounded local-MPS PI0.5 LoRA overfit on the T20.1 grasp view."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.pi05_preprocessing_contract import (
    CHECKPOINT_REPOSITORY_ID,
    CHECKPOINT_REVISION,
    TOKENIZER_REVISION,
)
from scenesmith.robot_lab.simulation_training_authority import require_active_simulation_training_authority
from scenesmith.robot_lab.simulation_training_spec import SPEC_PATH
from scenesmith.robot_lab.so101_coordinates import mujoco_to_lerobot


TASK = "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."
CHUNK_SIZE = 50
TRAIN_EPISODE_FRAMES = 244
VALID_TRAIN_STARTS = tuple(range(0, 195)) + tuple(range(244, 439))
VALID_EVALUATION_STARTS = tuple(range(0, 195))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--updates", type=int, default=5)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--task-id", choices=("T20.3", "T20.4"), default="T20.3")
    parser.add_argument("--seed", type=int, default=203)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    args = parser.parse_args()
    if (
        args.updates <= 0
        or args.gradient_accumulation_steps <= 0
        or not np.isfinite(args.learning_rate)
        or args.learning_rate <= 0
    ):
        parser.error("updates, accumulation steps, and learning rate must be finite and positive")
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    output = _resolve(args.output)
    if output.exists():
        raise ValueError("T20.3 output already exists; runs are immutable")

    spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    tensor_path = REPO_ROOT / spec["materialized_tensor_view"]["path"]
    if _sha(tensor_path) != spec["materialized_tensor_view"]["file_sha256"]:
        raise ValueError("T20.3 tensor-view hash drifted")
    snapshot = _snapshot_root(CHECKPOINT_REPOSITORY_ID, CHECKPOINT_REVISION)
    tokenizer = _snapshot_root("google/paligemma-3b-pt-224", TOKENIZER_REVISION)
    required = (
        snapshot / "config.json",
        snapshot / "model.safetensors",
        snapshot / "policy_preprocessor.json",
        snapshot / "policy_preprocessor_step_2_normalizer_processor.safetensors",
        tokenizer / "tokenizer.json",
    )
    if any(not path.is_file() for path in required):
        raise FileNotFoundError("Pinned PI0.5 checkpoint or tokenizer snapshot is incomplete")
    source_hashes = {str(path.relative_to(snapshot)) if snapshot in path.parents else f"tokenizer/{path.name}": _sha(path) for path in required}

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class
    from lerobot.processor.pipeline import DataProcessorPipeline
    from safetensors import safe_open

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.3 requires the authorized local MPS runtime")
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)
    arrays = np.load(tensor_path)
    _validate_arrays(arrays)

    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.gradient_checkpointing = True
    config.compile_model = False
    config.pretrained_path = str(snapshot)
    policy_class = get_policy_class(config.type)
    base_policy = policy_class.from_pretrained(
        snapshot,
        config=config,
        local_files_only=True,
        strict=True,
    )
    weight_check = _verify_loaded_weight(base_policy, snapshot / "model.safetensors", safe_open)
    policy = base_policy.wrap_with_peft(
        peft_cli_overrides={
            "method_type": "LORA",
            "r": 4,
            "lora_alpha": 4,
        }
    ).to("mps")
    trainable = [(name, value) for name, value in policy.named_parameters() if value.requires_grad]
    if not trainable:
        raise ValueError("T20.3 LoRA configuration produced no trainable parameters")
    optimizer = torch.optim.AdamW(
        [value for _, value in trainable],
        lr=args.learning_rate,
        weight_decay=0.0,
    )
    preprocessor = DataProcessorPipeline.from_pretrained(
        snapshot,
        config_filename="policy_preprocessor.json",
        local_files_only=True,
        overrides={"device_processor": {"device": "cpu"}},
    )

    baseline_train = _mean_loss(policy, preprocessor, arrays, "train", (0, 244), torch, args.seed + 1000)
    baseline_evaluation = _mean_loss(policy, preprocessor, arrays, "evaluation", (0, 96), torch, args.seed + 2000)
    losses: list[float] = []
    microbatch_losses: list[float] = []
    gradient_norms: list[float] = []
    realized_starts: list[int] = []
    policy.train()
    training_plan = _training_plan(args.updates, args.gradient_accumulation_steps)
    microbatch_index = 0
    for starts in training_plan:
        optimizer.zero_grad(set_to_none=True)
        update_losses: list[float] = []
        for start in starts:
            realized_starts.append(start)
            batch = _batch(preprocessor, arrays, split="train", start=start, torch=torch, device="mps")
            torch.manual_seed(args.seed + microbatch_index)
            loss, _metrics = policy(batch)
            if not torch.isfinite(loss):
                raise ValueError(f"{args.task_id} observed a non-finite training loss")
            (loss / args.gradient_accumulation_steps).backward()
            if not all(torch.isfinite(value.grad).all().item() for _, value in trainable if value.grad is not None):
                raise ValueError(f"{args.task_id} observed a non-finite gradient")
            observed_loss = float(loss.detach().cpu())
            microbatch_losses.append(observed_loss)
            update_losses.append(observed_loss)
            microbatch_index += 1
        norm = torch.nn.utils.clip_grad_norm_([value for _, value in trainable], max_norm=1.0)
        if not torch.isfinite(norm):
            raise ValueError(f"{args.task_id} observed a non-finite gradient norm")
        optimizer.step()
        torch.mps.synchronize()
        losses.append(float(sum(update_losses) / len(update_losses)))
        gradient_norms.append(float(norm.detach().cpu()))

    final_train = _mean_loss(policy, preprocessor, arrays, "train", (0, 244), torch, args.seed + 1000)
    final_evaluation = _mean_loss(policy, preprocessor, arrays, "evaluation", (0, 96), torch, args.seed + 2000)
    output.mkdir(parents=True)
    checkpoint = output / "adapter"
    policy.save_pretrained(checkpoint, safe_serialization=True)
    checkpoint_files = {
        str(path.relative_to(output)): {"sha256": _sha(path), "size_bytes": path.stat().st_size}
        for path in sorted(checkpoint.rglob("*"))
        if path.is_file()
    }
    summary = {
        "schema_version": (
            "scenesmith.t20_3_pi05_overfit.v1"
            if args.task_id == "T20.3"
            else "scenesmith.t20_4_pi05_update_ladder.v1"
        ),
        "task_id": args.task_id,
        "source_training_spec_identity_sha256": spec["identity_sha256"],
        "source_tensor_view_sha256": _sha(tensor_path),
        "checkpoint_repository_id": CHECKPOINT_REPOSITORY_ID,
        "checkpoint_revision": CHECKPOINT_REVISION,
        "tokenizer_revision": TOKENIZER_REVISION,
        "source_file_hashes": source_hashes,
        "loaded_weight_check": weight_check,
        "runtime": {"torch": torch.__version__, "device": "mps", "dtype": "float32", "offline": True},
        "adapter": {
            "kind": "lora",
            "rank": 4,
            "alpha": 4,
            "trainable_parameter_count": sum(value.numel() for _, value in trainable),
            "trainable_parameter_tensor_count": len(trainable),
            "checkpoint_files": checkpoint_files,
        },
        "updates": args.updates,
        "optimizer_update_count": args.updates,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "microbatch_count": len(realized_starts),
        "seed": args.seed,
        "learning_rate": args.learning_rate,
        "chunk_size": CHUNK_SIZE,
        "realized_train_starts": realized_starts,
        "coordinate_conversion": "canonical_mujoco_radians_to_lerobot_degrees_and_gripper_percent",
        "loss": {
            "baseline_train": baseline_train,
            "baseline_held_out": baseline_evaluation,
            "per_update": losses,
            "per_microbatch": microbatch_losses,
            "gradient_norms_before_clip": gradient_norms,
            "final_train": final_train,
            "final_held_out": final_evaluation,
            "all_finite": True,
        },
        "source_bytes_rewritten": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "simulation_semantic_strict_success": False,
        "simulation_policy_accepted": False,
        "disposition": "supervised_pi05_lora_training_only; closed-loop semantic evaluation pending",
    }
    (output / "run_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _validate_arrays(arrays) -> None:
    expected = {
        "train_state": (488, 12),
        "train_action": (488, 6),
        "evaluation_state": (244, 12),
        "evaluation_action": (244, 6),
    }
    for name, shape in expected.items():
        if arrays[name].shape != shape or not np.isfinite(arrays[name]).all():
            raise ValueError(f"T20.3 tensor {name} is invalid")


def _training_plan(updates: int, accumulation_steps: int) -> list[list[int]]:
    if updates <= 0 or accumulation_steps <= 0:
        raise ValueError("Training plan dimensions must be positive")
    return [
        [
            VALID_TRAIN_STARTS[((update * accumulation_steps + microbatch) * 73) % len(VALID_TRAIN_STARTS)]
            for microbatch in range(accumulation_steps)
        ]
        for update in range(updates)
    ]


def _batch(preprocessor, arrays, *, split: str, start: int, torch, device: str):
    valid = VALID_TRAIN_STARTS if split == "train" else VALID_EVALUATION_STARTS
    if start not in valid:
        raise ValueError("T20.3 sample start crosses an episode boundary")
    raw = {
        "observation.images.top": torch.as_tensor(arrays[f"{split}_top_rgb"][start]).permute(2, 0, 1).float().div(255),
        "observation.images.wrist": torch.as_tensor(arrays[f"{split}_wrist_rgb"][start]).permute(2, 0, 1).float().div(255),
        "observation.state": torch.tensor(mujoco_to_lerobot(arrays[f"{split}_state"][start, :6]), dtype=torch.float32),
        "action": torch.tensor([mujoco_to_lerobot(value) for value in arrays[f"{split}_action"][start : start + CHUNK_SIZE]], dtype=torch.float32),
        "task": TASK,
    }
    batch = preprocessor(raw)
    batch["action"] = batch["action"].unsqueeze(0)
    return {key: value.to(device) if isinstance(value, torch.Tensor) else value for key, value in batch.items()}


def _mean_loss(policy, preprocessor, arrays, split: str, starts: tuple[int, ...], torch, seed: int) -> float:
    values = []
    policy.eval()
    with torch.no_grad():
        for index, start in enumerate(starts):
            torch.manual_seed(seed + index)
            loss, _ = policy(_batch(preprocessor, arrays, split=split, start=start, torch=torch, device="mps"))
            if not torch.isfinite(loss):
                raise ValueError("T20.3 evaluation observed a non-finite loss")
            values.append(float(loss.detach().cpu()))
    policy.train()
    return float(sum(values) / len(values))


def _verify_loaded_weight(policy, weights_path: Path, safe_open) -> dict:
    state = policy.state_dict()
    with safe_open(weights_path, framework="pt", device="cpu") as source:
        for source_name in source.keys():
            candidates = (source_name, f"model.{source_name}")
            target_name = next((name for name in candidates if name in state), None)
            if target_name is None:
                continue
            expected = source.get_tensor(source_name)
            observed = state[target_name].detach().cpu()
            if expected.shape != observed.shape:
                continue
            maximum_error = float((expected.float() - observed.float()).abs().max())
            if maximum_error != 0.0:
                raise ValueError("PI0.5 loaded weight differs from its pinned checkpoint")
            return {"source_tensor": source_name, "model_tensor": target_name, "maximum_absolute_error": maximum_error}
    raise ValueError("Could not bind any loaded PI0.5 tensor to the pinned checkpoint")


def _snapshot_root(repository_id: str, revision: str) -> Path:
    directory = "models--" + repository_id.replace("/", "--")
    return Path.home() / ".cache/huggingface/hub" / directory / "snapshots" / revision


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
