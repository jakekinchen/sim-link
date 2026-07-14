"""Compose the T20.14 bounded retrain and closed-loop falsification gate."""

from __future__ import annotations

import math

from typing import Any

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes
from scenesmith.robot_lab.learned_action_localization import (
    verify_model_action_localization,
)


SCHEMA_VERSION = "scenesmith.t20_14_dataset_normalized_pi05_gate.v1"
EXPECTED_KEYFRAME_PHASES = [
    "pregrasp",
    "close",
    "grasp_hold",
    "unsupported_lift_hold",
    "retreat",
]
EXPECTED_TRAIN_STARTS = [
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
]


def build_dataset_normalized_pi05_gate(
    training_path: str,
    training: dict[str, Any],
    training_file_sha256: str,
    closed_loop_path: str,
    closed_loop: dict[str, Any],
    closed_loop_file_sha256: str,
    baseline_path: str,
    baseline: dict[str, Any],
    baseline_file_sha256: str,
) -> dict[str, Any]:
    _verify_training(training)
    _verify_closed_loop(closed_loop, training, training_file_sha256)
    verify_model_action_localization(baseline)
    if baseline.get("model_id") != "pi05":
        raise ValueError("T20.14 baseline must be the T20.11 PI0.5 result")
    for value in (
        training_file_sha256,
        closed_loop_file_sha256,
        baseline_file_sha256,
    ):
        if not _is_sha256(value):
            raise ValueError("T20.14 source file hash is invalid")

    training_effect = _training_effect(training["loss"])
    action_effect = derive_action_error_effect(
        baseline["action_error_diagnostics"],
        closed_loop["action_error_diagnostics"],
    )
    rollout = closed_loop["closed_loop"]
    keyframes = rollout["rendered_keyframes"]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.14",
            "sources": {
                "training": _source(training_path, training, training_file_sha256),
                "closed_loop": _source(
                    closed_loop_path, closed_loop, closed_loop_file_sha256
                ),
                "t20_11_pi05_baseline": _source(
                    baseline_path, baseline, baseline_file_sha256
                ),
            },
            "training_effect": training_effect,
            "initial_action_error_effect": action_effect,
            "strict_closed_loop": {
                "seed": rollout["seed"],
                "frame_count": rollout["frame_count"],
                "projected_action_frame_count": rollout[
                    "projected_action_frame_count"
                ],
                "active_assist_frame_count": rollout["active_assist_frame_count"],
                "maximum_anchor_lift_m": rollout["maximum_anchor_lift_m"],
                "terminal_outcome": rollout["terminal_outcome"],
                "strict_v2_valid_frame_counts": rollout[
                    "strict_v2_valid_frame_counts"
                ],
                "failed_gate_margins": rollout["failed_gate_margins"],
                "simulation_semantic_strict_success": rollout[
                    "simulation_semantic_strict_success"
                ],
            },
            "rendered_grasp_evidence": {
                "keyframe_count": len(keyframes),
                "phases": [row["phase"] for row in keyframes],
                "frame_indices": [row["frame_index"] for row in keyframes],
                "image_count": sum(len(row["images"]) for row in keyframes),
                "reviewed_views": ["top", "wrist"],
                "visual_finding": (
                    "gripper_remains_visibly_displaced_from_cube_through_"
                    "pregrasp_close_hold_lift_and_retreat"
                ),
                "visible_contact_or_lift": False,
            },
            "finding": {
                "dataset_normalization_improved_initial_gripper_error": action_effect[
                    "gripper_improved"
                ],
                "dataset_normalization_regressed_initial_arm_error": action_effect[
                    "non_gripper_regressed"
                ],
                "capability_gain_demonstrated": False,
                "selected_next_hypothesis": (
                    "state_vs_action_normalizer_ablation_before_more_optimizer_updates"
                ),
                "reason": (
                    "the joint normalizer replacement reduced gripper error but "
                    "introduced a broad frame-zero arm regression; separate the "
                    "state-token and action-postprocessor effects before training more"
                ),
            },
            "simulation_policy_accepted": False,
            "optimizer_training": True,
            "model_inference_executed": True,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_dataset_normalized_pi05_gate(
    payload: dict[str, Any],
    training_path: str,
    training: dict[str, Any],
    training_file_sha256: str,
    closed_loop_path: str,
    closed_loop: dict[str, Any],
    closed_loop_file_sha256: str,
    baseline_path: str,
    baseline: dict[str, Any],
    baseline_file_sha256: str,
) -> None:
    verify_signed_payload(payload, label="T20.14 dataset-normalized PI0.5 gate")
    expected = build_dataset_normalized_pi05_gate(
        training_path,
        training,
        training_file_sha256,
        closed_loop_path,
        closed_loop,
        closed_loop_file_sha256,
        baseline_path,
        baseline,
        baseline_file_sha256,
    )
    if payload != expected:
        raise ValueError("T20.14 gate drifted from source evidence")


def derive_action_error_effect(
    baseline: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    baseline_arm = _non_gripper_mae(baseline)
    candidate_arm = _non_gripper_mae(candidate)
    baseline_gripper = _finite_number(
        baseline.get("initial_gripper_absolute_error_rad"), "baseline gripper error"
    )
    candidate_gripper = _finite_number(
        candidate.get("initial_gripper_absolute_error_rad"), "candidate gripper error"
    )
    gripper_improvement = baseline_gripper - candidate_gripper
    arm_regression = candidate_arm - baseline_arm
    return {
        "baseline_initial_gripper_absolute_error_rad": baseline_gripper,
        "candidate_initial_gripper_absolute_error_rad": candidate_gripper,
        "gripper_error_improvement_rad": gripper_improvement,
        "gripper_improved": gripper_improvement > 0.0,
        "baseline_initial_non_gripper_mae_rad": baseline_arm,
        "candidate_initial_non_gripper_mae_rad": candidate_arm,
        "non_gripper_error_regression_rad": arm_regression,
        "non_gripper_error_ratio": candidate_arm / baseline_arm,
        "non_gripper_regressed": arm_regression > 0.0,
        "candidate_dominant_initial_error_joint": candidate.get(
            "dominant_initial_error_joint"
        ),
    }


def _training_effect(loss: dict[str, Any]) -> dict[str, Any]:
    baseline_train = _finite_number(loss["baseline_train"]["mean"], "baseline train")
    final_train = _finite_number(loss["final_train"]["mean"], "final train")
    baseline_eval = _finite_number(
        loss["baseline_held_out"]["mean"], "baseline held-out"
    )
    final_eval = _finite_number(loss["final_held_out"]["mean"], "final held-out")
    return {
        "baseline_train_mean": baseline_train,
        "final_train_mean": final_train,
        "train_mean_change": final_train - baseline_train,
        "baseline_held_out_mean": baseline_eval,
        "final_held_out_mean": final_eval,
        "held_out_mean_change": final_eval - baseline_eval,
        "all_finite": True,
    }


def _verify_training(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.14 training result")
    required = {
        "schema_version": "scenesmith.t20_14_dataset_normalized_pi05_training.v1",
        "task_id": "T20.14",
        "model_id": "pi05",
        "optimizer_update_count": 20,
        "microbatch_count": 20,
        "optimizer_training": True,
        "model_inference_executed": False,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    if any(payload.get(name) != value for name, value in required.items()):
        raise ValueError("T20.14 training contract drifted")
    if (
        payload.get("normalization", {}).get("loss_dimension_weights") != [1.0] * 6
        or payload.get("normalization", {}).get(
            "held_out_values_contributed_to_fit"
        )
        is not False
        or payload.get("realized_train_starts") != EXPECTED_TRAIN_STARTS
        or payload.get("runtime", {}).get("device") != "mps"
        or payload.get("runtime", {}).get("offline") is not True
    ):
        raise ValueError("T20.14 training intervention drifted")
    loss = payload.get("loss", {})
    if (
        loss.get("all_finite") is not True
        or len(loss.get("per_update", [])) != 20
        or len(loss.get("per_update_per_dimension", [])) != 20
        or any(len(row) != 6 for row in loss.get("per_update_per_dimension", []))
        or not _all_finite(loss.get("per_update", []))
        or not _all_finite(loss.get("gradient_norms_before_clip", []))
        or not _all_finite(
            value
            for row in loss.get("per_update_per_dimension", [])
            for value in row
        )
    ):
        raise ValueError("T20.14 training loss accounting drifted")


def _verify_closed_loop(
    payload: dict[str, Any],
    training: dict[str, Any],
    training_file_sha256: str,
) -> None:
    verify_signed_payload(payload, label="T20.14 closed-loop result")
    rollout = payload.get("closed_loop", {})
    verify_signed_payload(rollout, label="T20.14 nested rollout")
    diagnostics = payload.get("action_error_diagnostics", {})
    if (
        payload.get("schema_version")
        != "scenesmith.t20_14_dataset_normalized_pi05_closed_loop.v1"
        or payload.get("task_id") != "T20.14"
        or payload.get("model_id") != "pi05"
        or payload.get("source_training_identity_sha256")
        != training.get("identity_sha256")
        or payload.get("source_training_file_sha256") != training_file_sha256
        or payload.get("source_normalizer_identity_sha256")
        != training.get("source_normalizer_identity_sha256")
        or payload.get("model_inference_executed") is not True
        or payload.get("optimizer_training") is not False
        or payload.get("simulation_policy_accepted") is not False
        or payload.get("physical_actuation") is not False
        or payload.get("external_compute_started") is not False
        or payload.get("brev_compute_started") is not False
        or diagnostics.get("frame_count") != 244
        or diagnostics.get("initial_observation_comparison", {}).get(
            "identical_within_tolerance"
        )
        is not True
        or rollout.get("seed") != 2
        or rollout.get("frame_count") != 244
        or rollout.get("projected_action_frame_count") != 0
        or rollout.get("active_assist_frame_count") != 0
        or rollout.get("checkpoint_sha256")
        != training.get("checkpoint_files", {})
        .get("checkpoint/adapter_model.safetensors", {})
        .get("sha256")
        or rollout.get("simulation_semantic_strict_success") is not False
    ):
        raise ValueError("T20.14 closed-loop evidence drifted")
    validate_rendered_keyframes(rollout.get("rendered_keyframes"))
    phases = [row["phase"] for row in rollout["rendered_keyframes"]]
    if phases != EXPECTED_KEYFRAME_PHASES:
        raise ValueError("T20.14 rendered grasp phases drifted")


def _non_gripper_mae(diagnostics: dict[str, Any]) -> float:
    values = diagnostics.get("initial_action_absolute_error_rad", {})
    if set(values) != set(JOINT_NAMES):
        raise ValueError("T20.14 per-joint initial errors are incomplete")
    arm = [_finite_number(values[name], name) for name in JOINT_NAMES[:-1]]
    result = sum(arm) / len(arm)
    if result <= 0.0:
        raise ValueError("T20.14 baseline arm error must be positive")
    return result


def _source(path: str, payload: dict[str, Any], file_sha256: str) -> dict[str, Any]:
    return {
        "path": path,
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": file_sha256,
    }


def _finite_number(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"T20.14 {label} is non-finite")
    return result


def _all_finite(values) -> bool:
    try:
        return all(math.isfinite(float(value)) for value in values)
    except (TypeError, ValueError):
        return False


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
