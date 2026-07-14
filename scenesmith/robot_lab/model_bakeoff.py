"""Deterministic common-sample plan for the T20.7 four-model bake-off."""

from __future__ import annotations

import hashlib

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.phase_outcome_evaluation import verify_phase_outcome_fixture
from scenesmith.robot_lab.simulation_training_spec import verify_training_spec
from scenesmith.robot_lab.strict_grasp import verify_strict_grasp_v2_fixture


SCHEMA_VERSION = "scenesmith.t20_7_model_bakeoff_plan.v1"
MODEL_ORDER = ("pi05", "smolvla", "act", "diffusion_policy")
ORDERED_TRAIN_STARTS = (
    0,
    73,
    146,
    268,
    341,
    414,
    48,
    121,
    194,
    316,
    389,
    23,
    96,
    169,
    291,
    364,
    437,
    71,
    144,
    266,
)
ACTION_CHUNK_SIZE = 50


def build_model_bakeoff_plan(
    training_spec: dict[str, Any],
    semantic_fixture: dict[str, Any],
    strict_v2_fixture: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Build a source-bound plan without loading or training any model."""

    root = Path(repo_root)
    tensor_ref = training_spec["materialized_tensor_view"]
    tensor_path = root / tensor_ref["path"]
    verify_training_spec(
        training_spec,
        repo_root=root,
        tensor_view_path=tensor_path,
    )
    verify_strict_grasp_v2_fixture(strict_v2_fixture)
    verify_phase_outcome_fixture(semantic_fixture, strict_v2_fixture)
    if _sha(tensor_path) != tensor_ref["file_sha256"]:
        raise ValueError("T20.7 tensor-view hash drifted")
    _validate_starts(training_spec)
    starts_hash = hashlib.sha256(canonical_json_bytes(list(ORDERED_TRAIN_STARTS))).hexdigest()
    models = _model_contracts(starts_hash)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.7",
            "scope": "local_mps_equal_sample_four_model_bakeoff",
            "source_training_spec_identity_sha256": training_spec["identity_sha256"],
            "source_tensor_view": dict(tensor_ref),
            "source_semantic_fixture_identity_sha256": semantic_fixture[
                "identity_sha256"
            ],
            "source_strict_v2_identity_sha256": strict_v2_fixture["identity_sha256"],
            "common_sample_plan": {
                "train_episode_frame_ranges": [[0, 244], [244, 488]],
                "ordered_train_starts": list(ORDERED_TRAIN_STARTS),
                "ordered_train_starts_sha256": starts_hash,
                "action_chunk_size": ACTION_CHUNK_SIZE,
                "batch_size": 1,
                "optimizer_update_count": len(ORDERED_TRAIN_STARTS),
                "microbatch_count": len(ORDERED_TRAIN_STARTS),
                "canary_start": ORDERED_TRAIN_STARTS[0],
                "same_samples_required_for_every_model": True,
            },
            "evaluation_contract": {
                "held_out_episode_seed": 2,
                "inference_seed": 1703,
                "executed_action_horizon": 5,
                "denoising_steps_where_applicable": 10,
                "frame_count": 244,
                "rendered_keyframe_count": 5,
                "rendered_keyframe_size_px": 256,
                "policy_owned_actions_only": True,
                "action_projection_allowed": False,
                "controller_assistance_allowed": False,
                "terminal_outcome_separate_from_strict_success": True,
            },
            "models": models,
            "losses_cross_model_comparable": False,
            "ranking_surface": "fixed_seed_policy_owned_closed_loop_strict_behavior",
            "canary_executed": False,
            "optimizer_training": False,
            "model_inference_executed": False,
            "simulation_policy_accepted": False,
            "physical_transfer_eligible": False,
            "hardware_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "authority_not_granted": [
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
        }
    )


def verify_model_bakeoff_plan(
    payload: dict[str, Any],
    training_spec: dict[str, Any],
    semantic_fixture: dict[str, Any],
    strict_v2_fixture: dict[str, Any],
    *,
    repo_root: Path,
) -> None:
    verify_signed_payload(payload, label="T20.7 model bake-off plan")
    expected = build_model_bakeoff_plan(
        training_spec,
        semantic_fixture,
        strict_v2_fixture,
        repo_root=repo_root,
    )
    if payload != expected:
        raise ValueError("T20.7 model bake-off plan drifted from deterministic sources")


def _validate_starts(training_spec: dict[str, Any]) -> None:
    if training_spec.get("split_frame_counts") != {"train": 488, "evaluation": 244}:
        raise ValueError("T20.7 training split frame counts drifted")
    if len(set(ORDERED_TRAIN_STARTS)) != len(ORDERED_TRAIN_STARTS):
        raise ValueError("T20.7 common sample starts are not unique")
    for start in ORDERED_TRAIN_STARTS:
        in_first = 0 <= start and start + ACTION_CHUNK_SIZE <= 244
        in_second = 244 <= start and start + ACTION_CHUNK_SIZE <= 488
        if not (in_first or in_second):
            raise ValueError(f"T20.7 sample start crosses an episode boundary: {start}")


def _model_contracts(starts_hash: str) -> list[dict[str, Any]]:
    common = {
        "sample_plan_sha256": starts_hash,
        "action_chunk_size": ACTION_CHUNK_SIZE,
        "device": "mps",
        "dtype": "float32",
    }
    return [
        {
            **common,
            "model_id": "pi05",
            "family": "PI0.5",
            "initialization": {
                "kind": "pinned_pretrained_plus_rank4_lora",
                "repository_id": "Cache-SCA/pi05_teleop_sort_block",
                "revision": "84b551af1303e92d97d6752d43cc3c9f1a090778",
                "model_sha256": "471adf9abf281d7e3b5750b126cdd9a6efbdc7a230a9dd6fa8570e6b86cc62cf",
            },
        },
        {
            **common,
            "model_id": "smolvla",
            "family": "SmolVLA",
            "initialization": {
                "kind": "pinned_pretrained_plus_rank4_lora",
                "repository_id": "lerobot/smolvla_base",
                "revision": "c83c3163b8ca9b7e67c509fffd9121e66cb96205",
                "model_sha256": "7cd549ac2351fb069c0ddb3c34ad2d09cfc92b56a15dccdfc2e41467aaca01eb",
            },
        },
        {
            **common,
            "model_id": "act",
            "family": "ACT",
            "initialization": {
                "kind": "deterministic_compact_random_init",
                "architecture_source": "T20.2 reviewed compact ACT with chunk enlarged to 50",
                "seed": 207,
                "pretrained_backbone_weights": None,
            },
        },
        {
            **common,
            "model_id": "diffusion_policy",
            "family": "Diffusion Policy",
            "initialization": {
                "kind": "deterministic_compact_random_init",
                "architecture": "resnet18 plus one-stage temporal unet",
                "seed": 207,
                "pretrained_backbone_weights": None,
                "diffusion_train_steps": 100,
            },
        },
    ]


def _sha(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"T20.7 source file is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()
