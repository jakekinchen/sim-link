"""Load T20.36h's canonical batch without constructing a policy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.t20_36d_exact_act_gate_b_control_design import (
    verify_spec_file as verify_act_spec_file,
)
from scenesmith.robot_lab.t20_36e_act_batch import load_exact_batch


def load_smolvla_batch(
    *, repo_root: Path, spec: dict[str, Any]
) -> dict[str, Any]:
    act_spec = verify_act_spec_file(repo_root=repo_root)
    batch = load_exact_batch(repo_root=repo_root, spec=act_spec)
    required = spec["canonical_batch"]["batch_evidence_required"]
    evidence = batch["evidence"]
    if (
        evidence["physical_action_chunk_sha256"]
        != required["physical_action_chunk_sha256"]
        or evidence["physical_state_sha256"]
        != required["physical_state_sha256"]
        or evidence["image_tensor_sha256"][
            "observation.images.base_0_rgb"
        ]
        != required["base_image_tensor_sha256"]
        or evidence["image_tensor_sha256"][
            "observation.images.left_wrist_0_rgb"
        ]
        != required["wrist_image_tensor_sha256"]
        or evidence["task"] != spec["canonical_batch"]["task"]
    ):
        raise ValueError("T20.36h canonical SmolVLA batch drifted")
    return batch
