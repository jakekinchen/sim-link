#!/usr/bin/env python3
"""Evaluate one saved T20.2 ACT checkpoint in held-out MuJoCo closed loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.act_grasp_closed_loop import run_act_grasp_closed_loop
from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.simulation_training_authority import require_active_simulation_training_authority
from scenesmith.robot_lab.simulation_training_spec import SPEC_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    training_run = _resolve(args.training_run)
    output = _resolve(args.output)
    if output.exists():
        raise ValueError("T20.2 closed-loop outputs are immutable")
    summary_path = training_run / "run_summary.json"
    checkpoint_path = training_run / "act_t20_2_state.pt"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if _sha(checkpoint_path) != summary["checkpoint"]["sha256"]:
        raise ValueError("T20.2 checkpoint hash drifted from its run summary")
    spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    if summary["source_training_spec_identity_sha256"] != spec["identity_sha256"]:
        raise ValueError("T20.2 checkpoint training-spec binding drifted")

    runtime = REPO_ROOT / "external/lerobot/src"
    sys.path.insert(0, str(runtime))
    import torch
    from lerobot.configs.types import FeatureType, NormalizationMode, PolicyFeature
    from lerobot.policies.act.configuration_act import ACTConfig
    from lerobot.policies.act.modeling_act import ACTPolicy

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.2 closed-loop evaluation requires authorized local MPS")
    config = ACTConfig(
        input_features={
            "observation.images.top_rgb": PolicyFeature(FeatureType.VISUAL, (3, 64, 64)),
            "observation.images.wrist_rgb": PolicyFeature(FeatureType.VISUAL, (3, 64, 64)),
            "observation.state": PolicyFeature(FeatureType.STATE, (12,)),
        },
        output_features={"action": PolicyFeature(FeatureType.ACTION, (6,))},
        device="mps",
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
    model = ACTPolicy(config).to("mps")
    with torch.serialization.safe_globals(
        [PolicyFeature, FeatureType, NormalizationMode]
    ):
        saved = torch.load(checkpoint_path, map_location="mps", weights_only=True)
    model.load_state_dict(saved["model"], strict=True)
    model.eval()
    model.reset()

    def policy(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        from PIL import Image

        batch = {
            "observation.images.top_rgb": _image_tensor(images["top"], Image, torch),
            "observation.images.wrist_rgb": _image_tensor(images["wrist"], Image, torch),
            "observation.state": torch.as_tensor(state).unsqueeze(0).to("mps"),
        }
        with torch.no_grad():
            action = model.select_action(batch)
        return action.detach().cpu().numpy()[0]

    payload = run_act_grasp_closed_loop(
        policy,
        checkpoint_sha256=summary["checkpoint"]["sha256"],
        training_run_summary_sha256=_sha(summary_path),
        seed=2,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print(json.dumps({key: payload[key] for key in ("identity_sha256", "terminal_outcome", "simulation_semantic_strict_success", "maximum_anchor_lift_m", "projected_action_frame_count", "failed_gate_margins")}, indent=2))
    return 0


def _image_tensor(image: np.ndarray, image_module, torch):
    resized = np.asarray(image_module.fromarray(image).resize((64, 64), image_module.Resampling.BILINEAR), dtype=np.uint8).copy()
    return torch.as_tensor(resized).permute(2, 0, 1).unsqueeze(0).float().div(255).to("mps")


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
