#!/usr/bin/env python3
"""Run the bounded, local T20.2 ACT overfit from the signed T20.1 tensor view."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.simulation_training_authority import require_active_simulation_training_authority
from scenesmith.robot_lab.simulation_training_spec import SPEC_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--updates", type=int, default=20)
    parser.add_argument("--seed", type=int, default=201)
    args = parser.parse_args()
    if args.updates <= 0:
        parser.error("--updates must be positive")
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    output = _resolve(args.output)
    if output.exists():
        raise ValueError("T20.2 output already exists; runs are immutable")
    spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    view = REPO_ROOT / spec["materialized_tensor_view"]["path"]
    if _sha(view) != spec["materialized_tensor_view"]["file_sha256"]:
        raise ValueError("T20.2 tensor-view hash drifted")
    runtime = REPO_ROOT / "external/lerobot/src"
    if not runtime.is_dir():
        raise FileNotFoundError("Pinned local LeRobot source is unavailable")
    sys.path.insert(0, str(runtime))
    import torch
    from lerobot.configs.types import FeatureType, PolicyFeature
    from lerobot.policies.act.configuration_act import ACTConfig
    from lerobot.policies.act.modeling_act import ACTPolicy

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.2 requires the authorized local MPS runtime")
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)
    device = "mps"
    arrays = np.load(view)
    config = ACTConfig(
        input_features={
            "observation.images.top_rgb": PolicyFeature(FeatureType.VISUAL, (3, 64, 64)),
            "observation.images.wrist_rgb": PolicyFeature(FeatureType.VISUAL, (3, 64, 64)),
            "observation.state": PolicyFeature(FeatureType.STATE, (12,)),
        },
        output_features={"action": PolicyFeature(FeatureType.ACTION, (6,))},
        device=device,
        chunk_size=8,
        n_action_steps=1,
        pretrained_backbone_weights=None,
        dim_model=64,
        n_heads=4,
        dim_feedforward=128,
        n_encoder_layers=1,
        n_decoder_layers=1,
        use_vae=False,
        optimizer_lr=1e-4,
        optimizer_lr_backbone=1e-4,
    )
    model = ACTPolicy(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    baseline = _loss(model, arrays, split="train", device=device)
    losses = []
    for update in range(args.updates):
        batch = _batch(arrays, split="train", starts=[(update * 7 + offset * 53) % 480 for offset in range(4)], device=device)
        optimizer.zero_grad(set_to_none=True)
        loss, _metrics = model(batch)
        if not torch.isfinite(loss):
            raise ValueError("T20.2 observed a non-finite training loss")
        loss.backward()
        gradient_finite = all(torch.isfinite(parameter.grad).all().item() for parameter in model.parameters() if parameter.grad is not None)
        if not gradient_finite:
            raise ValueError("T20.2 observed a non-finite gradient")
        optimizer.step()
        torch.mps.synchronize()
        losses.append(float(loss.detach().cpu()))
    train_loss = _loss(model, arrays, split="train", device=device)
    evaluation_loss = _loss(model, arrays, split="evaluation", device=device)
    model.reset()
    diagnostic = _policy_action_diagnostic(model, arrays, device=device)
    output.mkdir(parents=True)
    checkpoint = output / "act_t20_2_state.pt"
    torch.save({"model": model.state_dict(), "config": dict(config.__dict__)}, checkpoint)
    summary = {
        "schema_version": "scenesmith.t20_2_act_overfit.v1",
        "task_id": "T20.2",
        "source_training_spec_identity_sha256": spec["identity_sha256"],
        "source_tensor_view_sha256": _sha(view),
        "runtime": {"torch": torch.__version__, "device": device, "mps_available": True},
        "model": {"kind": "lerobot_act", "chunk_size": 8, "trainable_parameter_count": sum(item.numel() for item in model.parameters())},
        "updates": args.updates,
        "seed": args.seed,
        "loss": {"baseline_train_l1": baseline, "per_update_l1": losses, "final_train_l1": train_loss, "held_out_l1": evaluation_loss, "all_finite": True},
        "policy_action_diagnostic": diagnostic,
        "checkpoint": {"path": checkpoint.name, "sha256": _sha(checkpoint)},
        "source_bytes_rewritten": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "simulation_semantic_strict_success": False,
        "simulation_policy_accepted": False,
        "disposition": "supervised_overfit_only; no closed-loop semantic evaluation claimed",
    }
    (output / "run_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _loss(model, arrays, *, split: str, device: str) -> float:
    values = []
    model.eval()
    import torch
    with torch.no_grad():
        for start in range(0, len(arrays[f"{split}_state"]) - 8, 32):
            loss, _ = model(_batch(arrays, split=split, starts=list(range(start, min(start + 4, len(arrays[f"{split}_state"]) - 8))), device=device))
            values.append(float(loss.detach().cpu()))
    model.train()
    return float(sum(values) / len(values))


def _batch(arrays, *, split: str, starts: list[int], device: str):
    import torch
    top = arrays[f"{split}_top_rgb"]
    wrist = arrays[f"{split}_wrist_rgb"]
    state = arrays[f"{split}_state"]
    action = arrays[f"{split}_action"]
    chunk = 8
    return {
        "observation.images.top_rgb": torch.as_tensor(np.stack([top[index] for index in starts])).permute(0, 3, 1, 2).float().div(255).to(device),
        "observation.images.wrist_rgb": torch.as_tensor(np.stack([wrist[index] for index in starts])).permute(0, 3, 1, 2).float().div(255).to(device),
        "observation.state": torch.as_tensor(np.stack([state[index] for index in starts])).float().to(device),
        "action": torch.as_tensor(np.stack([action[index : index + chunk] for index in starts])).float().to(device),
        "action_is_pad": torch.zeros((len(starts), chunk), dtype=torch.bool, device=device),
    }


def _policy_action_diagnostic(model, arrays, *, device: str) -> dict:
    batch = _batch(arrays, split="evaluation", starts=[0], device=device)
    for key in ("action", "action_is_pad"):
        batch.pop(key)
    prediction = model.select_action(batch).detach().cpu().numpy()[0].tolist()
    return {"split": "held_out", "frame_index": 0, "action": prediction, "finite": bool(np.isfinite(prediction).all())}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
