#!/usr/bin/env python3
"""Run the exact 20-sample T20.14 PI0.5 dataset-normalized LoRA rung."""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.model_bakeoff import (
    HELD_OUT_DIAGNOSTIC_STARTS,
    TRAIN_DIAGNOSTIC_STARTS,
    TRAINING_SEED,
)
from scenesmith.robot_lab.simulation_training_authority import (
    require_active_simulation_training_authority,
)
from scenesmith.robot_lab.so101_coordinates import mujoco_to_lerobot
from scripts.robot_lab.run_t20_7_model_training import (
    TASK,
    _model_contract,
    _set_offline_runtime,
    _snapshot,
    _verify_model_sources,
)


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
NORMALIZER_PATH = REPO_ROOT / "outputs/robot_lab/t20_13_dataset_bound_pi05_normalizer.json"
SCHEMA_VERSION = "scenesmith.t20_14_dataset_normalized_pi05_training.v1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    if output.exists():
        raise ValueError("T20.14 training output already exists")
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    plan = load_strict_json(PLAN_PATH)
    verify_signed_payload(plan, label="T20.14 source T20.7 plan")
    normalizer = load_strict_json(NORMALIZER_PATH)
    verify_signed_payload(normalizer, label="T20.14 source T20.13 normalizer")
    if (
        normalizer.get("finding", {}).get("selected_next_hypothesis")
        != "bounded_pi05_retrain_with_dataset_normalizer_and_equal_loss_weights"
    ):
        raise ValueError("T20.14 source normalizer does not authorize this hypothesis")
    tensor_path = REPO_ROOT / plan["source_tensor_view"]["path"]
    if _sha(tensor_path) != plan["source_tensor_view"]["file_sha256"]:
        raise ValueError("T20.14 tensor-view hash drifted")
    arrays = np.load(tensor_path)
    _validate_arrays(arrays)
    _set_offline_runtime()
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")

    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class
    from lerobot.policies.pi05.processor_pi05 import make_pi05_pre_post_processors

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.14 requires the authorized local MPS runtime")
    if (
        os.environ.get("SCENESMITH_GRIPPER_LOSS_WEIGHT", "1") != "1"
        or os.environ.get("SCENESMITH_GRIPPER_ONLY_LOSS", "0") != "0"
    ):
        raise ValueError("T20.14 requires equal six-way loss weights")
    _seed_all(torch, TRAINING_SEED)
    contract = _model_contract(plan, "pi05")
    _verify_model_sources(contract)
    snapshot = _snapshot(contract["initialization"])
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.gradient_checkpointing = True
    config.compile_model = False
    config.pretrained_path = str(snapshot)
    policy_class = get_policy_class(config.type)
    base = policy_class.from_pretrained(
        snapshot, config=config, local_files_only=True, strict=True
    )
    policy = base.wrap_with_peft(
        peft_cli_overrides={"method_type": "LORA", "r": 4, "lora_alpha": 4}
    ).to("mps")
    dataset_stats = _dataset_stats(normalizer, torch)
    preprocessor, _postprocessor = make_pi05_pre_post_processors(
        config, dataset_stats=dataset_stats
    )
    trainable = [parameter for parameter in policy.parameters() if parameter.requires_grad]
    if not trainable:
        raise ValueError("T20.14 LoRA has no trainable parameters")
    optimizer = torch.optim.AdamW(trainable, lr=5e-5, weight_decay=0.0)

    baseline_train = _mean_diagnostics(
        policy, preprocessor, arrays, "train", TRAIN_DIAGNOSTIC_STARTS, torch, 3037
    )
    baseline_held_out = _mean_diagnostics(
        policy,
        preprocessor,
        arrays,
        "evaluation",
        HELD_OUT_DIAGNOSTIC_STARTS,
        torch,
        4037,
    )
    losses = []
    per_dimension_losses = []
    gradient_norms = []
    starts = list(plan["common_sample_plan"]["ordered_train_starts"])
    policy.train()
    for update_index, start in enumerate(starts):
        optimizer.zero_grad(set_to_none=True)
        _seed_all(torch, TRAINING_SEED + update_index)
        loss, metrics = policy(_batch(preprocessor, arrays, "train", start, torch))
        if not torch.isfinite(loss):
            raise ValueError("T20.14 observed a non-finite training loss")
        loss.backward()
        gradients = [value.grad for value in trainable if value.grad is not None]
        if not gradients or not all(torch.isfinite(value).all().item() for value in gradients):
            raise ValueError("T20.14 observed a missing or non-finite gradient")
        norm = torch.nn.utils.clip_grad_norm_(trainable, max_norm=1.0)
        if not torch.isfinite(norm):
            raise ValueError("T20.14 observed a non-finite gradient norm")
        require_active_simulation_training_authority(repo_root=REPO_ROOT)
        optimizer.step()
        torch.mps.synchronize()
        losses.append(float(loss.detach().cpu()))
        per_dimension_losses.append(_loss_per_dimension(metrics))
        gradient_norms.append(float(norm.detach().cpu()))
    final_train = _mean_diagnostics(
        policy, preprocessor, arrays, "train", TRAIN_DIAGNOSTIC_STARTS, torch, 3037
    )
    final_held_out = _mean_diagnostics(
        policy,
        preprocessor,
        arrays,
        "evaluation",
        HELD_OUT_DIAGNOSTIC_STARTS,
        torch,
        4037,
    )

    output.mkdir(parents=True)
    checkpoint = output / "checkpoint"
    policy.save_pretrained(checkpoint, safe_serialization=True)
    checkpoint_files = {
        str(path.relative_to(output)): {
            "sha256": _sha(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(checkpoint.rglob("*"))
        if path.is_file()
    }
    payload = sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.14",
            "model_id": "pi05",
            "source_plan_identity_sha256": plan["identity_sha256"],
            "source_tensor_view_sha256": _sha(tensor_path),
            "source_normalizer_identity_sha256": normalizer["identity_sha256"],
            "source_normalizer_file_sha256": _sha(NORMALIZER_PATH),
            "source_model_sha256": contract["initialization"]["model_sha256"],
            "sample_plan_sha256": contract["sample_plan_sha256"],
            "realized_train_starts": starts,
            "optimizer_update_count": len(starts),
            "microbatch_count": len(starts),
            "action_chunk_size": 50,
            "seed": TRAINING_SEED,
            "optimizer": {
                "name": "AdamW",
                "learning_rate": 5e-5,
                "weight_decay": 0.0,
                "gradient_clip_norm": 1.0,
            },
            "normalization": {
                "mode": "MEAN_STD",
                "fit_split": "train_only",
                "held_out_values_contributed_to_fit": False,
                "statistics": normalizer["fitted_statistics"],
                "loss_dimension_weights": [1.0] * 6,
            },
            "loss": {
                "baseline_train": baseline_train,
                "baseline_held_out": baseline_held_out,
                "per_update": losses,
                "per_update_per_dimension": per_dimension_losses,
                "gradient_norms_before_clip": gradient_norms,
                "final_train": final_train,
                "final_held_out": final_held_out,
                "all_finite": True,
            },
            "trainable_parameter_count": sum(value.numel() for value in trainable),
            "total_parameter_count": sum(value.numel() for value in policy.parameters()),
            "checkpoint_files": checkpoint_files,
            "runtime": {
                "python": sys.version.split()[0],
                "torch": torch.__version__,
                "device": "mps",
                "dtype": "float32",
                "offline": True,
                "lerobot_stack_identity_sha256": stack["identity_sha256"],
            },
            "optimizer_training": True,
            "model_inference_executed": False,
            "closed_loop_evaluation_executed": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    dump_canonical_json(output / "run_summary.json", payload)
    print("pi05", payload["identity_sha256"], baseline_train["mean"], final_train["mean"])
    return 0


def _batch(preprocessor, arrays, split: str, start: int, torch):
    raw = {
        "observation.images.base_0_rgb": torch.as_tensor(
            arrays[f"{split}_top_rgb"][start]
        ).permute(2, 0, 1).float().div(255),
        "observation.images.left_wrist_0_rgb": torch.as_tensor(
            arrays[f"{split}_wrist_rgb"][start]
        ).permute(2, 0, 1).float().div(255),
        "observation.state": torch.tensor(
            mujoco_to_lerobot(arrays[f"{split}_state"][start, :6]),
            dtype=torch.float32,
        ),
        "action": torch.tensor(
            [
                mujoco_to_lerobot(value)
                for value in arrays[f"{split}_action"][start : start + 50]
            ],
            dtype=torch.float32,
        ),
        "task": TASK,
    }
    batch = preprocessor(raw)
    if batch["action"].ndim == 2:
        batch["action"] = batch["action"].unsqueeze(0)
    return {
        key: value.to("mps") if isinstance(value, torch.Tensor) else value
        for key, value in batch.items()
    }


def _mean_diagnostics(policy, preprocessor, arrays, split, starts, torch, seed):
    values = []
    per_dimension = []
    policy.eval()
    with torch.no_grad():
        for index, start in enumerate(starts):
            _seed_all(torch, seed + index)
            loss, metrics = policy(_batch(preprocessor, arrays, split, start, torch))
            if not torch.isfinite(loss):
                raise ValueError("T20.14 diagnostic loss is non-finite")
            values.append(float(loss.detach().cpu()))
            per_dimension.append(_loss_per_dimension(metrics))
    policy.train()
    return {
        "mean": float(sum(values) / len(values)),
        "per_sample": values,
        "per_dimension_mean": [
            float(sum(row[index] for row in per_dimension) / len(per_dimension))
            for index in range(6)
        ],
    }


def _loss_per_dimension(metrics) -> list[float]:
    values = metrics.get("loss_per_dim")
    if not isinstance(values, list) or len(values) != 6:
        raise ValueError("T20.14 PI0.5 per-dimension loss accounting is missing")
    output = [float(value) for value in values]
    if not all(np.isfinite(output)):
        raise ValueError("T20.14 PI0.5 per-dimension loss is non-finite")
    if metrics.get("gripper_loss_weight") != 1.0 or metrics.get("gripper_only_loss") is not False:
        raise ValueError("T20.14 PI0.5 loss weighting drifted")
    return output


def _dataset_stats(normalizer, torch):
    return {
        key: {
            name: torch.tensor(values[name], dtype=torch.float32)
            for name in ("mean", "std")
        }
        for key, values in {
            "observation.state": normalizer["fitted_statistics"]["state"],
            "action": normalizer["fitted_statistics"]["action"],
        }.items()
    }


def _validate_arrays(arrays) -> None:
    expected = {
        "train_state": (488, 12),
        "train_action": (488, 6),
        "evaluation_state": (244, 12),
        "evaluation_action": (244, 6),
        "train_top_rgb": (488, 64, 64, 3),
        "train_wrist_rgb": (488, 64, 64, 3),
        "evaluation_top_rgb": (244, 64, 64, 3),
        "evaluation_wrist_rgb": (244, 64, 64, 3),
    }
    for name, shape in expected.items():
        if arrays[name].shape != shape or not np.isfinite(arrays[name]).all():
            raise ValueError(f"T20.14 tensor array is invalid: {name}")


def _seed_all(torch, seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
