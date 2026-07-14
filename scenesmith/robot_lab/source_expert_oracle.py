"""Deterministic source-versus-policy-adapter diagnostics for T20.9."""

from __future__ import annotations

import math

from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes


SCHEMA_VERSION = "scenesmith.t20_9_source_expert_oracle.v1"
DIVERGENCE_THRESHOLDS = {
    "action_abs_error_rad": 0.0,
    "joint_position_abs_error_rad": 1e-12,
    "joint_velocity_abs_error_rad_s": 1e-9,
    "object_position_abs_error_m": 5e-7,
}


def analyze_source_oracle(
    stored_frames: list[dict[str, Any]],
    regenerated_frames: list[dict[str, Any]],
    oracle_frames: list[dict[str, Any]],
    *,
    source_outcome: dict[str, Any],
    oracle_rollout: dict[str, Any],
) -> dict[str, Any]:
    """Measure the first execution divergence and semantic gate mismatch."""

    frame_count = len(stored_frames)
    if frame_count <= 0 or len(regenerated_frames) != frame_count or len(oracle_frames) != frame_count:
        raise ValueError("T20.9 source and oracle frame counts differ")
    per_phase: dict[str, dict[str, Any]] = {}
    first_divergence: dict[str, Any] | None = None
    action_sequence_exact = True
    phase_sequence_exact = True
    contact_geometry_sequence_exact = True
    all_finite = True
    object_names: set[str] = set()

    for index, (stored, regenerated, oracle) in enumerate(
        zip(stored_frames, regenerated_frames, oracle_frames, strict=True)
    ):
        phase = regenerated.get("phase")
        if not isinstance(phase, str) or not phase:
            raise ValueError("T20.9 regenerated phase is invalid")
        phase_row = per_phase.setdefault(
            phase,
            {
                "frame_count": 0,
                "max_action_abs_error_rad": 0.0,
                "max_joint_position_abs_error_rad": 0.0,
                "max_joint_velocity_abs_error_rad_s": 0.0,
                "max_object_position_abs_error_m": 0.0,
                "phase_mismatch_count": 0,
                "contact_geometry_mismatch_count": 0,
            },
        )
        phase_row["frame_count"] += 1
        stored_action = _vector(stored["actions"]["requested"]["values"], "stored action", 6)
        regenerated_action = _vector(regenerated["mujoco_requested_action"], "regenerated action", 6)
        oracle_action = _vector(oracle["policy_requested_action"], "oracle action", 6)
        stored_qpos = _vector(stored["observations"]["joint_position_mujoco_rad"], "stored qpos", 6)
        regenerated_qpos = _vector(regenerated["mujoco_qpos"], "regenerated qpos", 6)
        oracle_qpos = _vector(oracle["mujoco_qpos"], "oracle qpos", 6)
        stored_qvel = _vector(stored["observations"]["joint_velocity_mujoco_rad_s"], "stored qvel", 6)
        regenerated_qvel = _vector(regenerated["mujoco_qvel"], "regenerated qvel", 6)
        oracle_qvel = _vector(oracle["mujoco_qvel"], "oracle qvel", 6)
        action_error = _max_error(stored_action, regenerated_action, oracle_action)
        qpos_error = _max_error(stored_qpos, regenerated_qpos, oracle_qpos)
        qvel_error = _max_error(stored_qvel, regenerated_qvel, oracle_qvel)

        regenerated_objects = regenerated.get("cube_positions_m")
        oracle_objects = oracle.get("cube_positions_m")
        if not isinstance(regenerated_objects, dict) or set(regenerated_objects) != set(oracle_objects or {}):
            raise ValueError("T20.9 object-position identities differ")
        object_names.update(regenerated_objects)
        object_error = max(
            (
                float(
                    np.max(
                        np.abs(
                            _vector(regenerated_objects[name], "regenerated object position", 3)
                            - _vector(oracle_objects[name], "oracle object position", 3)
                        )
                    )
                )
                for name in regenerated_objects
            ),
            default=0.0,
        )
        phase_match = stored.get("source_phase") == phase == oracle.get("phase")
        contact_match = regenerated.get("all_robot_object_contact_geoms") == oracle.get(
            "all_robot_object_contact_geoms"
        )
        action_sequence_exact = action_sequence_exact and action_error == 0.0
        phase_sequence_exact = phase_sequence_exact and phase_match
        contact_geometry_sequence_exact = contact_geometry_sequence_exact and contact_match
        all_finite = all_finite and all(
            math.isfinite(value) for value in (action_error, qpos_error, qvel_error, object_error)
        )
        phase_row["max_action_abs_error_rad"] = max(
            phase_row["max_action_abs_error_rad"], action_error
        )
        phase_row["max_joint_position_abs_error_rad"] = max(
            phase_row["max_joint_position_abs_error_rad"], qpos_error
        )
        phase_row["max_joint_velocity_abs_error_rad_s"] = max(
            phase_row["max_joint_velocity_abs_error_rad_s"], qvel_error
        )
        phase_row["max_object_position_abs_error_m"] = max(
            phase_row["max_object_position_abs_error_m"], object_error
        )
        phase_row["phase_mismatch_count"] += int(not phase_match)
        phase_row["contact_geometry_mismatch_count"] += int(not contact_match)
        failures = {
            "action_abs_error_rad": action_error > DIVERGENCE_THRESHOLDS["action_abs_error_rad"],
            "joint_position_abs_error_rad": qpos_error
            > DIVERGENCE_THRESHOLDS["joint_position_abs_error_rad"],
            "joint_velocity_abs_error_rad_s": qvel_error
            > DIVERGENCE_THRESHOLDS["joint_velocity_abs_error_rad_s"],
            "object_position_abs_error_m": object_error
            > DIVERGENCE_THRESHOLDS["object_position_abs_error_m"],
            "phase": not phase_match,
            "contact_geometry": not contact_match,
        }
        if first_divergence is None and any(failures.values()):
            first_divergence = {
                "frame_index": index,
                "phase": phase,
                "failed_dimensions": sorted(name for name, failed in failures.items() if failed),
                "measurements": {
                    "action_abs_error_rad": action_error,
                    "joint_position_abs_error_rad": qpos_error,
                    "joint_velocity_abs_error_rad_s": qvel_error,
                    "object_position_abs_error_m": object_error,
                },
            }

    source_gate_names = sorted(source_outcome.get("gate_margins", {}))
    oracle_failed = oracle_rollout.get("failed_gate_margins", [])
    failed_names = [row.get("gate") for row in oracle_failed]
    release_rows = [row for row in regenerated_frames if row.get("phase") == "release_settle"]
    retreat_rows = [row for row in regenerated_frames if row.get("phase") == "retreat"]
    release_final_clear = bool(release_rows) and not release_rows[-1].get(
        "all_robot_object_contact_geoms", []
    )
    retreat_final_clear = bool(retreat_rows) and not retreat_rows[-1].get(
        "all_robot_object_contact_geoms", []
    )
    adapter_reproduced = bool(
        first_divergence is None
        and action_sequence_exact
        and phase_sequence_exact
        and contact_geometry_sequence_exact
        and all_finite
        and oracle_rollout.get("projected_action_frame_count") == 0
        and oracle_rollout.get("active_assist_frame_count") == 0
    )
    semantic_mismatch = bool(
        adapter_reproduced
        and source_outcome.get("strict_success") is True
        and oracle_rollout.get("simulation_semantic_strict_success") is False
        and failed_names == ["release_final_contact_clear"]
        and "release_final_contact_clear" not in source_gate_names
        and not release_final_clear
        and retreat_final_clear
    )
    return {
        "frame_count": frame_count,
        "object_names": sorted(object_names),
        "divergence_thresholds": dict(DIVERGENCE_THRESHOLDS),
        "per_phase": per_phase,
        "first_execution_divergence": first_divergence,
        "all_numeric_diagnostics_finite": all_finite,
        "source_regeneration_matches_stored_actions": action_sequence_exact,
        "phase_sequence_exact": phase_sequence_exact,
        "contact_geometry_sequence_exact": contact_geometry_sequence_exact,
        "execution_adapter_reproduced_source_trajectory": adapter_reproduced,
        "source_declared_strict_success": source_outcome.get("strict_success"),
        "source_declared_gate_names": source_gate_names,
        "oracle_strict_success": oracle_rollout.get("simulation_semantic_strict_success"),
        "oracle_failed_gate_names": failed_names,
        "release_settle_final_contact_clear": release_final_clear,
        "retreat_final_contact_clear": retreat_final_clear,
        "source_vs_acceptance_semantic_mismatch": semantic_mismatch,
        "mismatch_kind": (
            "release_clear_gate_absent_from_source_training_success_contract"
            if semantic_mismatch
            else None
        ),
    }


def build_source_oracle_artifact(
    *,
    source_refs: dict[str, Any],
    t20_7_evaluation_ref: dict[str, Any],
    oracle_rollout: dict[str, Any],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    if diagnostics.get("execution_adapter_reproduced_source_trajectory") is not True:
        outcome = "execution_divergence_requires_correction"
    elif diagnostics.get("source_vs_acceptance_semantic_mismatch") is True:
        outcome = "adapter_valid_source_acceptance_contract_mismatch"
    else:
        outcome = "adapter_valid_no_contract_mismatch"
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.9",
            "evidence_mode": "source_expert_action_oracle_through_policy_closed_loop_adapter",
            "source_refs": source_refs,
            "t20_7_evaluation_ref": t20_7_evaluation_ref,
            "diagnostics": diagnostics,
            "oracle_rollout": oracle_rollout,
            "terminal_diagnostic_outcome": outcome,
            "model_loaded": False,
            "model_inference_executed": False,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_source_oracle_artifact(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.9 source-expert oracle")
    if payload.get("schema_version") != SCHEMA_VERSION or payload.get("task_id") != "T20.9":
        raise ValueError("T20.9 oracle schema or task identity drifted")
    diagnostics = payload.get("diagnostics", {})
    rollout = payload.get("oracle_rollout", {})
    verify_signed_payload(rollout, label="T20.9 nested oracle rollout")
    expected_rollout = {
        "schema_version": SCHEMA_VERSION,
        "task_id": "T20.9",
        "evidence_mode": "source_expert_action_oracle_through_policy_closed_loop_adapter",
        "policy_label": "source_expert_oracle",
        "seed": 2,
        "policy_controls_owned_all_frames": True,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "physical_transfer_ready": False,
        "promotion_eligible": False,
    }
    if any(rollout.get(name) != value for name, value in expected_rollout.items()):
        raise ValueError("T20.9 nested oracle rollout contract drifted")
    if diagnostics.get("frame_count") != 244 or rollout.get("frame_count") != 244:
        raise ValueError("T20.9 oracle frame count drifted")
    validate_rendered_keyframes(rollout.get("rendered_keyframes"))
    required_false = (
        "model_loaded",
        "model_inference_executed",
        "optimizer_training",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if any(payload.get(name) is not False for name in required_false):
        raise ValueError("T20.9 oracle authority or execution field drifted")
    if rollout.get("projected_action_frame_count") != 0 or rollout.get(
        "active_assist_frame_count"
    ) != 0:
        raise ValueError("T20.9 oracle projection or assistance is forbidden")
    source_refs = payload.get("source_refs", {})
    episode_ref = source_refs.get("episode", {})
    evaluation_ref = payload.get("t20_7_evaluation_ref", {})
    if (
        source_refs.get("source_episode_regenerated_byte_identically") is not True
        or episode_ref.get("seed") != 2
        or episode_ref.get("frame_count") != 244
        or episode_ref.get("source_action_sequence_sha256")
        != rollout.get("policy_action_sequence_sha256")
        or not _is_sha256(episode_ref.get("file_sha256"))
        or evaluation_ref.get("strict_success_count") != 0
        or evaluation_ref.get("winner_model_id") is not None
    ):
        raise ValueError("T20.9 source or T20.7 evidence linkage drifted")
    adapter_reproduced = diagnostics.get(
        "execution_adapter_reproduced_source_trajectory"
    )
    if adapter_reproduced != (
        diagnostics.get("first_execution_divergence") is None
        and diagnostics.get("source_regeneration_matches_stored_actions") is True
        and diagnostics.get("phase_sequence_exact") is True
        and diagnostics.get("contact_geometry_sequence_exact") is True
        and diagnostics.get("all_numeric_diagnostics_finite") is True
    ):
        raise ValueError("T20.9 adapter-reproduction decision drifted")
    failed_names = [
        row.get("gate") for row in rollout.get("failed_gate_margins", [])
    ]
    semantic_mismatch = bool(
        adapter_reproduced
        and diagnostics.get("source_declared_strict_success") is True
        and diagnostics.get("oracle_strict_success") is False
        and failed_names == ["release_final_contact_clear"]
        and diagnostics.get("oracle_failed_gate_names") == failed_names
        and "release_final_contact_clear"
        not in diagnostics.get("source_declared_gate_names", [])
        and diagnostics.get("release_settle_final_contact_clear") is False
        and diagnostics.get("retreat_final_contact_clear") is True
    )
    if diagnostics.get("source_vs_acceptance_semantic_mismatch") is not semantic_mismatch:
        raise ValueError("T20.9 source-versus-acceptance semantic decision drifted")
    expected_kind = (
        "release_clear_gate_absent_from_source_training_success_contract"
        if semantic_mismatch
        else None
    )
    if diagnostics.get("mismatch_kind") != expected_kind:
        raise ValueError("T20.9 semantic mismatch kind drifted")
    expected_terminal = (
        "execution_divergence_requires_correction"
        if not adapter_reproduced
        else "adapter_valid_source_acceptance_contract_mismatch"
        if semantic_mismatch
        else "adapter_valid_no_contract_mismatch"
    )
    if payload.get("terminal_diagnostic_outcome") != expected_terminal:
        raise ValueError("T20.9 terminal diagnostic outcome drifted")


def _vector(value: Any, label: str, size: int) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (size,):
        raise ValueError(f"T20.9 {label} has an invalid shape")
    if not np.isfinite(result).all():
        raise ValueError(f"T20.9 {label} is non-finite")
    return result


def _max_error(first: np.ndarray, second: np.ndarray, third: np.ndarray) -> float:
    if first.shape != second.shape or first.shape != third.shape:
        raise ValueError("T20.9 compared vector shapes differ")
    return float(max(np.max(np.abs(first - second)), np.max(np.abs(first - third))))


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
