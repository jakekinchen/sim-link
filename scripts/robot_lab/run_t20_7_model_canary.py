#!/usr/bin/env python3
"""Run one offline local-MPS T20.7 forward/backward canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
    MODEL_ORDER,
    build_model_canary_result,
    verify_model_canary_result,
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
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    if output.exists():
        raise ValueError("T20.7 canary outputs are immutable")
    plan = load_strict_json(PLAN_PATH)
    arrays = np.load(REPO_ROOT / plan["source_tensor_view"]["path"])
    start = plan["common_sample_plan"]["canary_start"]
    _set_offline_runtime()
    observation = _run_model(args.model, arrays, start, plan)
    payload = build_model_canary_result(plan, args.model, observation)
    verify_model_canary_result(payload, plan)
    dump_canonical_json(output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _run_model(model_id: str, arrays, start: int, plan: dict):
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    import torch

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.7 requires the authorized local MPS runtime")
    seed = 207
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    if model_id == "pi05":
        result = _run_pi05(torch, arrays, start, plan)
    elif model_id == "smolvla":
        result = _run_smolvla(torch, arrays, start, plan)
    elif model_id == "act":
        result = _run_act(torch, arrays, start)
    else:
        result = _run_diffusion(torch, arrays, start)
    result["runtime"].update(
        {
            "python": sys.version.split()[0],
            "lerobot_stack_identity_sha256": stack["identity_sha256"],
        }
    )
    if model_id == "diffusion_policy":
        import diffusers

        result["runtime"]["diffusers"] = diffusers.__version__
    return result


def _run_pi05(torch, arrays, start: int, plan: dict):
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class
    from lerobot.processor.pipeline import DataProcessorPipeline

    model_contract = _model_contract(plan, "pi05")
    snapshot = _snapshot(model_contract["initialization"])
    _verify_model_sources(model_contract)
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.gradient_checkpointing = True
    config.compile_model = False
    policy_class = get_policy_class(config.type)
    base = policy_class.from_pretrained(snapshot, config=config, local_files_only=True, strict=True)
    policy = base.wrap_with_peft(
        peft_cli_overrides={"method_type": "LORA", "r": 4, "lora_alpha": 4}
    ).to("mps")
    preprocessor = DataProcessorPipeline.from_pretrained(
        snapshot,
        config_filename="policy_preprocessor.json",
        local_files_only=True,
        overrides={"device_processor": {"device": "cpu"}},
    )
    batch = _vla_batch(preprocessor, arrays, start, torch, "top", "wrist")
    return _forward_backward(policy, batch, torch, {"kind": "sha256", "value": model_contract["initialization"]["model_sha256"]})


def _run_smolvla(torch, arrays, start: int, plan: dict):
    import lerobot.policies.smolvla.processor_smolvla  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class
    from lerobot.processor.pipeline import DataProcessorPipeline

    model_contract = _model_contract(plan, "smolvla")
    snapshot = _snapshot(model_contract["initialization"])
    _verify_model_sources(model_contract)
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.compile_model = False
    config.pretrained_path = str(snapshot)
    policy_class = get_policy_class(config.type)
    base = policy_class.from_pretrained(snapshot, config=config, local_files_only=True, strict=True)
    policy = base.wrap_with_peft(
        peft_cli_overrides={"method_type": "LORA", "r": 4, "lora_alpha": 4}
    ).to("mps")
    preprocessor = DataProcessorPipeline.from_pretrained(
        snapshot,
        config_filename="policy_preprocessor.json",
        local_files_only=True,
        overrides={"device_processor": {"device": "cpu"}},
    )
    batch = _vla_batch(preprocessor, arrays, start, torch, "camera1", "camera2", add_empty=True)
    return _forward_backward(policy, batch, torch, {"kind": "sha256", "value": model_contract["initialization"]["model_sha256"]})


def _run_act(torch, arrays, start: int):
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
    policy = ACTPolicy(config).to("mps")
    batch = _tensor_batch(arrays, start, torch)
    return _forward_backward(policy, batch, torch, {"kind": "deterministic_random_init", "seed": 207})


def _run_diffusion(torch, arrays, start: int):
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
    policy = DiffusionPolicy(config).to("mps")
    batch = _tensor_batch(arrays, start, torch)
    batch["observation.state"] = batch["observation.state"].unsqueeze(1)
    return _forward_backward(policy, batch, torch, {"kind": "deterministic_random_init", "seed": 207})


def _features(FeatureType, PolicyFeature):
    return {
        "observation.images.top_rgb": PolicyFeature(FeatureType.VISUAL, (3, 64, 64)),
        "observation.images.wrist_rgb": PolicyFeature(FeatureType.VISUAL, (3, 64, 64)),
        "observation.state": PolicyFeature(FeatureType.STATE, (12,)),
    }


def _tensor_batch(arrays, start: int, torch):
    return {
        "observation.images.top_rgb": torch.as_tensor(arrays["train_top_rgb"][start]).permute(2, 0, 1).unsqueeze(0).float().div(255).to("mps"),
        "observation.images.wrist_rgb": torch.as_tensor(arrays["train_wrist_rgb"][start]).permute(2, 0, 1).unsqueeze(0).float().div(255).to("mps"),
        "observation.state": torch.as_tensor(arrays["train_state"][start]).unsqueeze(0).float().to("mps"),
        "action": torch.as_tensor(arrays["train_action"][start : start + 50]).unsqueeze(0).float().to("mps"),
        "action_is_pad": torch.zeros((1, 50), dtype=torch.bool, device="mps"),
    }


def _vla_batch(preprocessor, arrays, start: int, torch, top_key: str, wrist_key: str, *, add_empty: bool = False):
    raw = {
        f"observation.images.{top_key}": torch.as_tensor(arrays["train_top_rgb"][start]).permute(2, 0, 1).float().div(255),
        f"observation.images.{wrist_key}": torch.as_tensor(arrays["train_wrist_rgb"][start]).permute(2, 0, 1).float().div(255),
        "observation.state": torch.tensor(mujoco_to_lerobot(arrays["train_state"][start, :6]), dtype=torch.float32),
        "action": torch.tensor([mujoco_to_lerobot(value) for value in arrays["train_action"][start : start + 50]], dtype=torch.float32),
        "task": TASK,
    }
    if add_empty:
        raw["observation.images.camera3"] = torch.zeros_like(raw[f"observation.images.{top_key}"])
    batch = preprocessor(raw)
    batch["action"] = batch["action"].unsqueeze(0)
    return {key: value.to("mps") if isinstance(value, torch.Tensor) else value for key, value in batch.items()}


def _forward_backward(policy, batch: dict, torch, source_weight_check: dict):
    policy.train()
    policy.zero_grad(set_to_none=True)
    loss, _metrics = policy(batch)
    if not torch.isfinite(loss):
        raise ValueError("T20.7 canary loss is non-finite")
    loss.backward()
    trainable = [parameter for parameter in policy.parameters() if parameter.requires_grad]
    gradients = [parameter.grad for parameter in trainable if parameter.grad is not None]
    if not gradients or not all(torch.isfinite(gradient).all().item() for gradient in gradients):
        raise ValueError("T20.7 canary gradient is missing or non-finite")
    squared = sum(float(gradient.detach().float().pow(2).sum().cpu()) for gradient in gradients)
    gradient_norm = math.sqrt(squared)
    result = {
        "loss": float(loss.detach().cpu()),
        "gradient_norm": gradient_norm,
        "trainable_parameter_count": sum(parameter.numel() for parameter in trainable),
        "total_parameter_count": sum(parameter.numel() for parameter in policy.parameters()),
        "runtime": {"torch": torch.__version__, "device": "mps", "dtype": "float32", "offline": True},
        "source_weight_check": source_weight_check,
    }
    policy.zero_grad(set_to_none=True)
    return result


def _model_contract(plan: dict, model_id: str) -> dict:
    return next(model for model in plan["models"] if model["model_id"] == model_id)


def _snapshot(initialization: dict) -> Path:
    directory = "models--" + initialization["repository_id"].replace("/", "--")
    return Path.home() / ".cache/huggingface/hub" / directory / "snapshots" / initialization["revision"]


def _verify_model_sources(model_contract: dict) -> None:
    for dependency in model_contract["initialization"]["source_dependencies"]:
        root = _snapshot(dependency)
        for relative_path, expected_sha256 in dependency["files"].items():
            if _sha(root / relative_path) != expected_sha256:
                raise ValueError("T20.7 pinned model or processor source hash drifted")


def _sha(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"T20.7 required local file is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _set_offline_runtime() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")


if __name__ == "__main__":
    raise SystemExit(main())
