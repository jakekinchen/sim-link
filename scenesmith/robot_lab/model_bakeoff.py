"""Deterministic common-sample plan for the T20.7 four-model bake-off."""

from __future__ import annotations

import hashlib
import math

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
CANARY_SCHEMA_VERSION = "scenesmith.t20_7_model_canary.v1"
CANARY_GATE_SCHEMA_VERSION = "scenesmith.t20_7_model_canary_gate.v1"


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


def build_model_canary_result(
    plan: dict[str, Any], model_id: str, observation: dict[str, Any]
) -> dict[str, Any]:
    """Sign one immutable same-sample forward/backward canary observation."""

    verify_signed_payload(plan, label="T20.7 model bake-off plan")
    model = next((item for item in plan["models"] if item["model_id"] == model_id), None)
    if model is None:
        raise ValueError(f"T20.7 model is absent from the plan: {model_id}")
    required = (
        "loss",
        "gradient_norm",
        "trainable_parameter_count",
        "total_parameter_count",
        "runtime",
        "source_weight_check",
    )
    if any(key not in observation for key in required):
        raise ValueError("T20.7 canary observation is incomplete")
    for key in ("loss", "gradient_norm"):
        value = observation[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"T20.7 canary {key} must be finite")
    for key in ("trainable_parameter_count", "total_parameter_count"):
        value = observation[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"T20.7 canary {key} must be positive")
    payload = {
        "schema_version": CANARY_SCHEMA_VERSION,
        "task_id": "T20.7",
        "model_id": model_id,
        "source_plan_identity_sha256": plan["identity_sha256"],
        "source_tensor_view_sha256": plan["source_tensor_view"]["file_sha256"],
        "source_semantic_fixture_identity_sha256": plan[
            "source_semantic_fixture_identity_sha256"
        ],
        "sample_start": plan["common_sample_plan"]["canary_start"],
        "sample_plan_sha256": model["sample_plan_sha256"],
        "action_chunk_size": model["action_chunk_size"],
        "initialization": model["initialization"],
        "input_adapter": model["input_adapter"],
        "loss": float(observation["loss"]),
        "gradient_norm": float(observation["gradient_norm"]),
        "loss_finite": True,
        "gradients_finite": True,
        "trainable_parameter_count": observation["trainable_parameter_count"],
        "total_parameter_count": observation["total_parameter_count"],
        "runtime": observation["runtime"],
        "source_weight_check": observation["source_weight_check"],
        "forward_pass_completed": True,
        "backward_pass_completed": True,
        "optimizer_step_completed": False,
        "optimizer_training": False,
        "model_inference_executed": False,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    return sign_payload(payload)


def verify_model_canary_result(payload: dict[str, Any], plan: dict[str, Any]) -> None:
    """Validate one observed canary without pretending its numeric loss is deterministic."""

    verify_signed_payload(payload, label="T20.7 model canary result")
    model = next(
        (item for item in plan["models"] if item["model_id"] == payload.get("model_id")),
        None,
    )
    expected = {
        "schema_version": CANARY_SCHEMA_VERSION,
        "task_id": "T20.7",
        "source_plan_identity_sha256": plan["identity_sha256"],
        "source_tensor_view_sha256": plan["source_tensor_view"]["file_sha256"],
        "source_semantic_fixture_identity_sha256": plan[
            "source_semantic_fixture_identity_sha256"
        ],
        "sample_start": plan["common_sample_plan"]["canary_start"],
        "action_chunk_size": ACTION_CHUNK_SIZE,
    }
    if model is None or any(payload.get(key) != value for key, value in expected.items()):
        raise ValueError("T20.7 model canary linkage drifted")
    if payload.get("sample_plan_sha256") != model["sample_plan_sha256"]:
        raise ValueError("T20.7 model canary sample plan drifted")
    if payload.get("initialization") != model["initialization"]:
        raise ValueError("T20.7 model canary initialization drifted")
    if payload.get("input_adapter") != model["input_adapter"]:
        raise ValueError("T20.7 model canary input adapter drifted")
    for key in ("loss", "gradient_norm"):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"T20.7 model canary {key} is non-finite")
    required_true = ("loss_finite", "gradients_finite", "forward_pass_completed", "backward_pass_completed")
    required_false = (
        "optimizer_step_completed",
        "optimizer_training",
        "model_inference_executed",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
    )
    if any(payload.get(key) is not True for key in required_true) or any(
        payload.get(key) is not False for key in required_false
    ):
        raise ValueError("T20.7 model canary authority or completion fields drifted")


def build_model_canary_gate(
    plan: dict[str, Any], results: list[tuple[str, dict[str, Any], str]]
) -> dict[str, Any]:
    """Compose four immutable per-model canaries into one continuation gate."""

    if [payload.get("model_id") for _, payload, _ in results] != list(MODEL_ORDER):
        raise ValueError("T20.7 model canary results are incomplete or out of order")
    entries = []
    for path, payload, file_sha256 in results:
        verify_model_canary_result(payload, plan)
        if len(file_sha256) != 64:
            raise ValueError("T20.7 model canary file hash is invalid")
        entries.append(
            {
                "model_id": payload["model_id"],
                "path": path,
                "identity_sha256": payload["identity_sha256"],
                "file_sha256": file_sha256,
                "loss": payload["loss"],
                "gradient_norm": payload["gradient_norm"],
                "trainable_parameter_count": payload["trainable_parameter_count"],
                "total_parameter_count": payload["total_parameter_count"],
            }
        )
    return sign_payload(
        {
            "schema_version": CANARY_GATE_SCHEMA_VERSION,
            "task_id": "T20.7",
            "source_plan_identity_sha256": plan["identity_sha256"],
            "sample_start": plan["common_sample_plan"]["canary_start"],
            "sample_plan_sha256": plan["common_sample_plan"][
                "ordered_train_starts_sha256"
            ],
            "model_results": entries,
            "all_four_models_present": True,
            "all_losses_finite": True,
            "all_gradients_finite": True,
            "same_sample_verified": True,
            "continuation_rung_authorized": True,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_model_canary_gate(
    payload: dict[str, Any],
    plan: dict[str, Any],
    results: list[tuple[str, dict[str, Any], str]],
) -> None:
    verify_signed_payload(payload, label="T20.7 model canary gate")
    if payload != build_model_canary_gate(plan, results):
        raise ValueError("T20.7 model canary gate drifted from observed results")


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
                "source_dependencies": [
                    {
                        "repository_id": "Cache-SCA/pi05_teleop_sort_block",
                        "revision": "84b551af1303e92d97d6752d43cc3c9f1a090778",
                        "files": {
                            "config.json": "e6a32a933c9d4ffceea65677b1bba6281b233cf5307ee8abef12b18eb9935eb3",
                            "model.safetensors": "471adf9abf281d7e3b5750b126cdd9a6efbdc7a230a9dd6fa8570e6b86cc62cf",
                            "policy_preprocessor.json": "50ecdd21c5f4e02c65da336605cbe0137207cb82f5ea904823d7dc285112b54b",
                            "policy_preprocessor_step_2_normalizer_processor.safetensors": "8dc4c304b136dc66eca1b3156059b3d2bbd296864fff99e8453ed5fc128d070f",
                        },
                    },
                    {
                        "repository_id": "google/paligemma-3b-pt-224",
                        "revision": "35e4f46485b4d07967e7e9935bc3786aad50687c",
                        "files": {"tokenizer.json": "ef6773c135b77b834de1d13c75a4c98ab7a3684ffd602d1831e1f1bf5467c563"},
                    },
                ],
            },
            "input_adapter": {
                "top_rgb": "observation.images.top",
                "wrist_rgb": "observation.images.wrist",
                "empty_camera_count": 0,
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
                "source_dependencies": [
                    {
                        "repository_id": "lerobot/smolvla_base",
                        "revision": "c83c3163b8ca9b7e67c509fffd9121e66cb96205",
                        "files": {
                            "config.json": "650584b56c104720f7a3c91d1ec6bec9e8de8ac11e60c92ba2fa82d93eda147d",
                            "model.safetensors": "7cd549ac2351fb069c0ddb3c34ad2d09cfc92b56a15dccdfc2e41467aaca01eb",
                            "policy_preprocessor.json": "7683d648280a72f0d51e869fb8dd1596beed90b7f84849330cf1bc26634a4bd6",
                            "policy_preprocessor_step_5_normalizer_processor.safetensors": "490ab239d96e263687c0b2e386a0afbc235a2eceb9857c36ed32f2f162a3e7c8",
                        },
                    },
                    {
                        "repository_id": "HuggingFaceTB/SmolVLM2-500M-Video-Instruct",
                        "revision": "7b375e1b73b11138ff12fe22c8f2822d8fe03467",
                        "files": {
                            "config.json": "ea6bc1237e96247f6258de3e202e2e62b93d6f386dc47e7b36b5588bf3a15e17",
                            "model.safetensors": "b9bfd456c9472c0acd5719d6e514c4b859891af205ee1a736552fd3497b8b0c3",
                            "preprocessor_config.json": "149e315d9410368e5491455bb06e0f763426e9e56cca731c13b24404a29b6374",
                            "processor_config.json": "f3ad45028447b3562b4752be0d5916d6806c1ef589091a469608dcf0faa1737c",
                            "tokenizer.json": "5ece781dc8d2b2f3e2f289ca0ae50b17cfc27dd27bfe7971bb8241e0b964331a",
                        },
                    },
                ],
            },
            "input_adapter": {
                "top_rgb": "observation.images.camera1",
                "wrist_rgb": "observation.images.camera2",
                "empty_camera_count": 1,
                "empty_camera_key": "observation.images.camera3",
                "empty_camera_value": 0.0,
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
            "input_adapter": {
                "top_rgb": "observation.images.top_rgb",
                "wrist_rgb": "observation.images.wrist_rgb",
                "empty_camera_count": 0,
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
            "input_adapter": {
                "top_rgb": "observation.images.top_rgb",
                "wrist_rgb": "observation.images.wrist_rgb",
                "empty_camera_count": 0,
            },
        },
    ]


def _sha(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"T20.7 source file is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()
