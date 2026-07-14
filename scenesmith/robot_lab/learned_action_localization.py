"""Per-frame learned-action error localization against a source oracle."""

from __future__ import annotations

import math

from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes
from scenesmith.robot_lab.model_bakeoff import MODEL_ORDER


SCHEMA_VERSION = "scenesmith.t20_11_model_action_localization.v1"
ACTION_DIVERGENCE_THRESHOLD_RAD = 1e-6
INITIAL_STATE_TOLERANCE = 1e-6


def analyze_model_actions(
    source_frames: list[dict[str, Any]],
    model_frames: list[dict[str, Any]],
    *,
    source_anchor_start_position_m: list[float],
) -> dict[str, Any]:
    if len(source_frames) != 244 or len(model_frames) != 244:
        raise ValueError("T20.11 action comparison requires 244 source/model frames")
    by_phase: dict[str, list[np.ndarray]] = {}
    first_divergence: dict[str, Any] | None = None
    all_errors: list[np.ndarray] = []
    phase_sequence_exact = True
    for index, (source, model) in enumerate(zip(source_frames, model_frames, strict=True)):
        source_action = _vector(source["actions"]["requested"]["values"], 6, "source action")
        model_action = _vector(model["policy_requested_action"], 6, "model action")
        error = np.abs(model_action - source_action)
        phase = source.get("source_phase")
        phase_match = isinstance(phase, str) and phase == model.get("phase")
        phase_sequence_exact = phase_sequence_exact and phase_match
        if not phase_match:
            raise ValueError("T20.11 source/model phase sequence drifted")
        by_phase.setdefault(phase, []).append(error)
        all_errors.append(error)
        if first_divergence is None and float(np.max(error)) > ACTION_DIVERGENCE_THRESHOLD_RAD:
            joint_index = int(np.argmax(error))
            first_divergence = {
                "frame_index": index,
                "phase": phase,
                "joint_name": JOINT_NAMES[joint_index],
                "absolute_error_rad": float(error[joint_index]),
                "threshold_rad": ACTION_DIVERGENCE_THRESHOLD_RAD,
                "source_action_rad": float(source_action[joint_index]),
                "model_action_rad": float(model_action[joint_index]),
            }
    matrix = np.stack(all_errors)
    initial_source_qpos = _vector(
        source_frames[0]["observations"]["joint_position_mujoco_rad"],
        6,
        "source initial qpos",
    )
    initial_model_qpos = _vector(model_frames[0]["mujoco_qpos"], 6, "model initial qpos")
    initial_source_qvel = _vector(
        source_frames[0]["observations"]["joint_velocity_mujoco_rad_s"],
        6,
        "source initial qvel",
    )
    initial_model_qvel = _vector(model_frames[0]["mujoco_qvel"], 6, "model initial qvel")
    object_positions = model_frames[0].get("cube_positions_m", {})
    if len(object_positions) != 1:
        raise ValueError("T20.11 initial model object identity is ambiguous")
    initial_model_object = _vector(next(iter(object_positions.values())), 3, "model object position")
    initial_source_object = _vector(source_anchor_start_position_m, 3, "source object position")
    initial_state_errors = {
        "joint_position_max_abs_error_rad": float(
            np.max(np.abs(initial_model_qpos - initial_source_qpos))
        ),
        "joint_velocity_max_abs_error_rad_s": float(
            np.max(np.abs(initial_model_qvel - initial_source_qvel))
        ),
        "object_position_max_abs_error_m": float(
            np.max(np.abs(initial_model_object - initial_source_object))
        ),
    }
    initial_identical = all(
        value <= INITIAL_STATE_TOLERANCE for value in initial_state_errors.values()
    )
    phase_results = {}
    for phase, errors in by_phase.items():
        values = np.stack(errors)
        phase_results[phase] = {
            "frame_count": len(errors),
            "mean_absolute_error_rad": float(np.mean(values)),
            "maximum_absolute_error_rad": float(np.max(values)),
            "per_joint_mean_absolute_error_rad": {
                name: float(value) for name, value in zip(JOINT_NAMES, np.mean(values, axis=0), strict=True)
            },
            "per_joint_maximum_absolute_error_rad": {
                name: float(value) for name, value in zip(JOINT_NAMES, np.max(values, axis=0), strict=True)
            },
        }
    initial_error = matrix[0]
    dominant_initial = int(np.argmax(initial_error))
    return {
        "frame_count": 244,
        "compared_joint_names": list(JOINT_NAMES),
        "phase_sequence_exact": phase_sequence_exact,
        "all_action_errors_finite": bool(np.isfinite(matrix).all()),
        "action_divergence_threshold_rad": ACTION_DIVERGENCE_THRESHOLD_RAD,
        "first_action_divergence": first_divergence,
        "initial_observation_comparison": {
            **initial_state_errors,
            "tolerance": INITIAL_STATE_TOLERANCE,
            "identical_within_tolerance": initial_identical,
        },
        "initial_action_absolute_error_rad": {
            name: float(value) for name, value in zip(JOINT_NAMES, initial_error, strict=True)
        },
        "initial_action_mean_absolute_error_rad": float(np.mean(initial_error)),
        "initial_action_maximum_absolute_error_rad": float(np.max(initial_error)),
        "initial_gripper_absolute_error_rad": float(initial_error[-1]),
        "dominant_initial_error_joint": JOINT_NAMES[dominant_initial],
        "trajectory_mean_absolute_error_rad": float(np.mean(matrix)),
        "trajectory_maximum_absolute_error_rad": float(np.max(matrix)),
        "per_phase": phase_results,
        "causal_interpretation": {
            "frame_zero": "identical_reset_prediction_error",
            "later_frames": "closed_loop_prediction_plus_compounding_state_distribution_drift",
            "teacher_forced_loss_claimed": False,
        },
    }


def verify_model_action_localization(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.11 model action localization")
    model_id = payload.get("model_id")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != "T20.11"
        or model_id not in MODEL_ORDER
    ):
        raise ValueError("T20.11 model localization identity drifted")
    diagnostics = payload.get("action_error_diagnostics", {})
    if (
        diagnostics.get("frame_count") != 244
        or diagnostics.get("phase_sequence_exact") is not True
        or diagnostics.get("all_action_errors_finite") is not True
        or diagnostics.get("initial_observation_comparison", {}).get(
            "identical_within_tolerance"
        )
        is not True
        or diagnostics.get("first_action_divergence", {}).get("frame_index") != 0
        or set(diagnostics.get("initial_action_absolute_error_rad", {}))
        != set(JOINT_NAMES)
    ):
        raise ValueError("T20.11 action-error diagnostics drifted")
    rollout = payload.get("corrected_closed_loop", {})
    verify_signed_payload(rollout, label="T20.11 corrected model rollout")
    if (
        rollout.get("task_id") != "T20.11"
        or rollout.get("policy_label") != model_id
        or rollout.get("frame_count") != 244
        or rollout.get("release_clearance_basis")
        != "force_bearing_pad_or_nonpad_contact"
    ):
        raise ValueError("T20.11 corrected model rollout linkage drifted")
    validate_rendered_keyframes(rollout.get("rendered_keyframes"))
    required_true = ("model_inference_executed",)
    required_false = (
        "optimizer_training",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if any(payload.get(name) is not True for name in required_true) or any(
        payload.get(name) is not False for name in required_false
    ):
        raise ValueError("T20.11 model execution or authority fields drifted")


def _vector(value: Any, size: int, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (size,) or not np.isfinite(result).all():
        raise ValueError(f"T20.11 {label} is malformed or non-finite")
    return result
