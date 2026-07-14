#!/usr/bin/env python3
"""Run one exact-common-sample T20.7 optimizer rung on local MPS."""

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

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.model_bakeoff import (
    HELD_OUT_DIAGNOSTIC_STARTS,
    MODEL_ORDER,
    TRAIN_DIAGNOSTIC_STARTS,
    TRAINING_SEED,
    build_model_training_result,
    verify_model_training_result,
)
from scenesmith.robot_lab.simulation_training_authority import (
    require_active_simulation_training_authority,
)
from scenesmith.robot_lab.so101_coordinates import mujoco_to_lerobot


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
TASK = "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODEL_ORDER, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    if output.exists():
        raise ValueError("T20.7 model training outputs are immutable")

    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    plan = load_strict_json(PLAN_PATH)
    tensor_path = REPO_ROOT / plan["source_tensor_view"]["path"]
    if _sha(tensor_path) != plan["source_tensor_view"]["file_sha256"]:
        raise ValueError("T20.7 source tensor view hash drifted")
    arrays = np.load(tensor_path)
    _validate_arrays(arrays)
    _set_offline_runtime()
    observation, policy = _train_model(args.model, arrays, plan)

    output.mkdir(parents=True)
    checkpoint = output / "checkpoint"
    _save_checkpoint(policy, args.model, checkpoint)
    observation["checkpoint_files"] = _checkpoint_manifest(output, checkpoint)
    payload = build_model_training_result(plan, args.model, observation)
    verify_model_training_result(payload, plan)
    dump_canonical_json(output / "run_summary.json", payload)
    print(f"{args.model}: {payload['identity_sha256']}")
    return 0


def _train_model(model_id: str, arrays, plan: dict):
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    import torch

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.7 requires the authorized local MPS runtime")
    _seed_all(torch, TRAINING_SEED)
    policy, preprocessor, source_weight_check = _load_model(
        model_id, plan, torch
    )
    trainable = [parameter for parameter in policy.parameters() if parameter.requires_grad]
    if not trainable:
        raise ValueError("T20.7 model training found no trainable parameters")
    learning_rate = 5e-5 if model_id in ("pi05", "smolvla") else 1e-4
    optimizer = torch.optim.AdamW(trainable, lr=learning_rate, weight_decay=0.0)
    batch_builder = lambda split, start: _batch(  # noqa: E731
        model_id, preprocessor, arrays, split, start, torch
    )

    baseline_train = _mean_loss(
        policy,
        batch_builder,
        TRAIN_DIAGNOSTIC_STARTS,
        torch,
        TRAINING_SEED + 1000,
    )
    baseline_held_out = _mean_loss(
        policy,
        batch_builder,
        HELD_OUT_DIAGNOSTIC_STARTS,
        torch,
        TRAINING_SEED + 2000,
        split="evaluation",
    )
    realized_starts: list[int] = []
    losses: list[float] = []
    gradient_norms: list[float] = []
    policy.train()
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    for update_index, start in enumerate(
        plan["common_sample_plan"]["ordered_train_starts"]
    ):
        optimizer.zero_grad(set_to_none=True)
        _seed_all(torch, TRAINING_SEED + update_index)
        loss, _metrics = policy(batch_builder("train", start))
        if not torch.isfinite(loss):
            raise ValueError("T20.7 model training observed a non-finite loss")
        loss.backward()
        gradients = [
            parameter.grad for parameter in trainable if parameter.grad is not None
        ]
        if not gradients or not all(
            torch.isfinite(gradient).all().item() for gradient in gradients
        ):
            raise ValueError("T20.7 model training observed a missing or non-finite gradient")
        norm = torch.nn.utils.clip_grad_norm_(trainable, max_norm=1.0)
        if not torch.isfinite(norm):
            raise ValueError("T20.7 model training observed a non-finite gradient norm")
        require_active_simulation_training_authority(repo_root=REPO_ROOT)
        optimizer.step()
        torch.mps.synchronize()
        realized_starts.append(start)
        losses.append(float(loss.detach().cpu()))
        gradient_norms.append(float(norm.detach().cpu()))

    final_train = _mean_loss(
        policy,
        batch_builder,
        TRAIN_DIAGNOSTIC_STARTS,
        torch,
        TRAINING_SEED + 1000,
    )
    final_held_out = _mean_loss(
        policy,
        batch_builder,
        HELD_OUT_DIAGNOSTIC_STARTS,
        torch,
        TRAINING_SEED + 2000,
        split="evaluation",
    )
    observation = {
        "realized_train_starts": realized_starts,
        "optimizer": {
            "name": "AdamW",
            "learning_rate": learning_rate,
            "weight_decay": 0.0,
            "gradient_clip_norm": 1.0,
        },
        "loss": {
            "baseline_train": baseline_train,
            "baseline_held_out": baseline_held_out,
            "per_update": losses,
            "gradient_norms_before_clip": gradient_norms,
            "final_train": final_train,
            "final_held_out": final_held_out,
        },
        "trainable_parameter_count": sum(
            parameter.numel() for parameter in trainable
        ),
        "total_parameter_count": sum(
            parameter.numel() for parameter in policy.parameters()
        ),
        "runtime": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "device": "mps",
            "dtype": "float32",
            "offline": True,
            "lerobot_stack_identity_sha256": stack["identity_sha256"],
        },
        "source_weight_check": source_weight_check,
    }
    if model_id == "diffusion_policy":
        import diffusers

        observation["runtime"]["diffusers"] = diffusers.__version__
    return observation, policy


def _load_model(model_id: str, plan: dict, torch):
    if model_id == "pi05":
        return _load_pi05(plan, torch)
    if model_id == "smolvla":
        return _load_smolvla(plan, torch)
    if model_id == "act":
        return _load_act(torch)
    return _load_diffusion(torch)


def _load_pi05(plan: dict, torch):
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class
    from lerobot.processor.pipeline import DataProcessorPipeline

    model_contract = _model_contract(plan, "pi05")
    _verify_model_sources(model_contract)
    snapshot = _snapshot(model_contract["initialization"])
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
    preprocessor = DataProcessorPipeline.from_pretrained(
        snapshot,
        config_filename="policy_preprocessor.json",
        local_files_only=True,
        overrides={"device_processor": {"device": "cpu"}},
    )
    source = {
        "kind": "sha256",
        "value": model_contract["initialization"]["model_sha256"],
    }
    return policy, preprocessor, source


def _load_smolvla(plan: dict, torch):
    import lerobot.policies.smolvla.processor_smolvla  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class
    from lerobot.processor.pipeline import DataProcessorPipeline

    model_contract = _model_contract(plan, "smolvla")
    _verify_model_sources(model_contract)
    snapshot = _snapshot(model_contract["initialization"])
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.compile_model = False
    config.pretrained_path = str(snapshot)
    policy_class = get_policy_class(config.type)
    base = policy_class.from_pretrained(
        snapshot, config=config, local_files_only=True, strict=True
    )
    policy = base.wrap_with_peft(
        peft_cli_overrides={"method_type": "LORA", "r": 4, "lora_alpha": 4}
    ).to("mps")
    preprocessor = DataProcessorPipeline.from_pretrained(
        snapshot,
        config_filename="policy_preprocessor.json",
        local_files_only=True,
        overrides={"device_processor": {"device": "cpu"}},
    )
    source = {
        "kind": "sha256",
        "value": model_contract["initialization"]["model_sha256"],
    }
    return policy, preprocessor, source


def _load_act(torch):
    from lerobot.configs.types import FeatureType, PolicyFeature
    from lerobot.policies.act.configuration_act import ACTConfig
    from lerobot.policies.act.modeling_act import ACTPolicy

    config = ACTConfig(
        input_features=_features(FeatureType, PolicyFeature),
        output_features={"action": PolicyFeature(FeatureType.ACTION, (6,))},
        device="mps",
        chunk_size=50,
        n_action_steps=5,
        pretrained_backbone_weights=None,
        dim_model=64,
        n_heads=4,
        dim_feedforward=128,
        n_encoder_layers=1,
        n_decoder_layers=1,
        use_vae=False,
    )
    return (
        ACTPolicy(config).to("mps"),
        None,
        {"kind": "deterministic_random_init", "seed": TRAINING_SEED},
    )


def _load_diffusion(torch):
    from lerobot.configs.types import FeatureType, PolicyFeature
    from lerobot.policies.diffusion.configuration_diffusion import DiffusionConfig
    from lerobot.policies.diffusion.modeling_diffusion import DiffusionPolicy

    config = DiffusionConfig(
        input_features=_features(FeatureType, PolicyFeature),
        output_features={"action": PolicyFeature(FeatureType.ACTION, (6,))},
        device="mps",
        n_obs_steps=1,
        horizon=50,
        n_action_steps=5,
        drop_n_last_frames=0,
        pretrained_backbone_weights=None,
        use_separate_rgb_encoder_per_camera=False,
        spatial_softmax_num_keypoints=8,
        down_dims=(64,),
        diffusion_step_embed_dim=64,
        num_train_timesteps=100,
        num_inference_steps=10,
    )
    return (
        DiffusionPolicy(config).to("mps"),
        None,
        {"kind": "deterministic_random_init", "seed": TRAINING_SEED},
    )


def _batch(model_id: str, preprocessor, arrays, split: str, start: int, torch):
    if model_id in ("pi05", "smolvla"):
        return _vla_batch(model_id, preprocessor, arrays, split, start, torch)
    batch = {
        "observation.images.top_rgb": torch.as_tensor(
            arrays[f"{split}_top_rgb"][start]
        ).permute(2, 0, 1).unsqueeze(0).float().div(255).to("mps"),
        "observation.images.wrist_rgb": torch.as_tensor(
            arrays[f"{split}_wrist_rgb"][start]
        ).permute(2, 0, 1).unsqueeze(0).float().div(255).to("mps"),
        "observation.state": torch.as_tensor(
            arrays[f"{split}_state"][start]
        ).unsqueeze(0).float().to("mps"),
        "action": torch.as_tensor(
            arrays[f"{split}_action"][start : start + 50]
        ).unsqueeze(0).float().to("mps"),
        "action_is_pad": torch.zeros((1, 50), dtype=torch.bool, device="mps"),
    }
    if model_id == "diffusion_policy":
        batch["observation.state"] = batch["observation.state"].unsqueeze(1)
    return batch


def _vla_batch(model_id, preprocessor, arrays, split, start, torch):
    top_key, wrist_key = (
        ("top", "wrist") if model_id == "pi05" else ("camera1", "camera2")
    )
    raw = {
        f"observation.images.{top_key}": torch.as_tensor(
            arrays[f"{split}_top_rgb"][start]
        ).permute(2, 0, 1).float().div(255),
        f"observation.images.{wrist_key}": torch.as_tensor(
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
    if model_id == "smolvla":
        raw["observation.images.camera3"] = torch.zeros_like(
            raw["observation.images.camera1"]
        )
    batch = preprocessor(raw)
    batch["action"] = batch["action"].unsqueeze(0)
    return {
        key: value.to("mps") if isinstance(value, torch.Tensor) else value
        for key, value in batch.items()
    }


def _mean_loss(policy, batch_builder, starts, torch, seed, *, split="train"):
    values = []
    policy.eval()
    with torch.no_grad():
        for index, start in enumerate(starts):
            _seed_all(torch, seed + index)
            loss, _metrics = policy(batch_builder(split, start))
            if not torch.isfinite(loss):
                raise ValueError("T20.7 diagnostic observed a non-finite loss")
            values.append(float(loss.detach().cpu()))
    policy.train()
    return float(sum(values) / len(values))


def _save_checkpoint(policy, model_id: str, checkpoint: Path) -> None:
    import torch

    if model_id in ("pi05", "smolvla"):
        policy.save_pretrained(checkpoint, safe_serialization=True)
        return
    checkpoint.mkdir(parents=True)
    torch.save(
        {
            "model_id": model_id,
            "seed": TRAINING_SEED,
            "model": policy.state_dict(),
        },
        checkpoint / "model_state.pt",
    )


def _checkpoint_manifest(output: Path, checkpoint: Path) -> dict:
    return {
        str(path.relative_to(output)): {
            "sha256": _sha(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(checkpoint.rglob("*"))
        if path.is_file()
    }


def _features(FeatureType, PolicyFeature):
    return {
        "observation.images.top_rgb": PolicyFeature(
            FeatureType.VISUAL, (3, 64, 64)
        ),
        "observation.images.wrist_rgb": PolicyFeature(
            FeatureType.VISUAL, (3, 64, 64)
        ),
        "observation.state": PolicyFeature(FeatureType.STATE, (12,)),
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
    for key, shape in expected.items():
        if arrays[key].shape != shape or not np.isfinite(arrays[key]).all():
            raise ValueError(f"T20.7 tensor array is invalid: {key}")


def _model_contract(plan: dict, model_id: str) -> dict:
    return next(model for model in plan["models"] if model["model_id"] == model_id)


def _snapshot(initialization: dict) -> Path:
    directory = "models--" + initialization["repository_id"].replace("/", "--")
    return (
        Path.home()
        / ".cache/huggingface/hub"
        / directory
        / "snapshots"
        / initialization["revision"]
    )


def _verify_model_sources(model_contract: dict) -> None:
    for dependency in model_contract["initialization"]["source_dependencies"]:
        root = _snapshot(dependency)
        for relative_path, expected_sha256 in dependency["files"].items():
            if _sha(root / relative_path) != expected_sha256:
                raise ValueError("T20.7 pinned model or processor source hash drifted")


def _seed_all(torch, seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


def _set_offline_runtime() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")


def _sha(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"T20.7 required local file is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
