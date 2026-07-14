"""Frozen-candidate action/state localization for T20.25."""

from __future__ import annotations

import hashlib
import json

from typing import Any

import numpy as np

from scenesmith.robot_lab.act_grasp_closed_loop import PHASE_PLAN, ROLLOUT_FRAMES
from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES


TRACE_SCHEMA_VERSION = "scenesmith.t20_25_frozen_candidate_trace.v1"
GATE_SCHEMA_VERSION = "scenesmith.t20_25_frozen_candidate_localization_gate.v1"
CANDIDATE_IDS = ("clean_base", "recovery_augmented")
HELD_OUT_SEEDS = (6, 7)
PRECONTACT_PHASES = ("approach", "pregrasp")
DIVERGENCE_THRESHOLD = 1e-6


def build_comparison_rows(
    source_frames: list[dict[str, Any]], candidate_frames: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if len(source_frames) != ROLLOUT_FRAMES or len(candidate_frames) != ROLLOUT_FRAMES:
        raise ValueError("T20.25 requires complete 244-frame source and candidate traces")
    rows = []
    for index, (source, candidate) in enumerate(zip(source_frames, candidate_frames, strict=True)):
        phase = source.get("source_phase")
        if phase != candidate.get("phase"):
            raise ValueError("T20.25 source/candidate phase order drifted")
        rows.append(
            {
                "frame_index": index,
                "phase": phase,
                "source_action_rad": _vector(
                    source.get("actions", {}).get("requested", {}).get("values"),
                    "source action",
                ),
                "candidate_action_rad": _vector(
                    candidate.get("policy_requested_action"), "candidate action"
                ),
                "source_qpos_rad": _vector(
                    source.get("observations", {}).get("joint_position_mujoco_rad"),
                    "source qpos",
                ),
                "candidate_qpos_rad": _vector(candidate.get("mujoco_qpos"), "candidate qpos"),
                "source_qvel_rad_s": _vector(
                    source.get("observations", {}).get("joint_velocity_mujoco_rad_s"),
                    "source qvel",
                ),
                "candidate_qvel_rad_s": _vector(candidate.get("mujoco_qvel"), "candidate qvel"),
            }
        )
    return rows


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    _validate_rows(rows)
    source_action = _matrix(rows, "source_action_rad")
    candidate_action = _matrix(rows, "candidate_action_rad")
    source_qpos = _matrix(rows, "source_qpos_rad")
    candidate_qpos = _matrix(rows, "candidate_qpos_rad")
    source_qvel = _matrix(rows, "source_qvel_rad_s")
    candidate_qvel = _matrix(rows, "candidate_qvel_rad_s")
    action_error = np.abs(candidate_action - source_action)
    qpos_error = np.abs(candidate_qpos - source_qpos)
    qvel_error = np.abs(candidate_qvel - source_qvel)
    precontact = np.asarray([row["phase"] in PRECONTACT_PHASES for row in rows])
    return {
        "frame_count": ROLLOUT_FRAMES,
        "joint_names": list(JOINT_NAMES),
        "phase_frame_counts": {
            phase: sum(row["phase"] == phase for row in rows) for phase, _ in PHASE_PLAN
        },
        "all_values_finite": True,
        "initial_reset_identical_within_tolerance": bool(
            np.max(qpos_error[0]) <= DIVERGENCE_THRESHOLD
            and np.max(qvel_error[0]) <= DIVERGENCE_THRESHOLD
        ),
        "frame_zero_action_mean_absolute_error_rad": float(np.mean(action_error[0])),
        "frame_zero_non_gripper_mean_absolute_error_rad": float(
            np.mean(action_error[0, :-1])
        ),
        "frame_zero_gripper_absolute_error_rad": float(action_error[0, -1]),
        "frame_zero_action_per_joint_absolute_error_rad": {
            name: float(value)
            for name, value in zip(JOINT_NAMES, action_error[0], strict=True)
        },
        "precontact_action_mean_absolute_error_rad": float(np.mean(action_error[precontact])),
        "trajectory_action_mean_absolute_error_rad": float(np.mean(action_error)),
        "trajectory_action_maximum_absolute_error_rad": float(np.max(action_error)),
        "precontact_qpos_mean_absolute_error_rad": float(np.mean(qpos_error[precontact])),
        "trajectory_qpos_mean_absolute_error_rad": float(np.mean(qpos_error)),
        "trajectory_qvel_mean_absolute_error_rad_s": float(np.mean(qvel_error)),
        "first_action_divergence": _first_divergence(rows, action_error),
        "first_qpos_divergence": _first_divergence(rows, qpos_error),
        "per_phase": {
            phase: {
                "frame_count": int(
                    np.sum(mask := np.asarray([row["phase"] == phase for row in rows]))
                ),
                "action_mean_absolute_error_rad": float(np.mean(action_error[mask])),
                "qpos_mean_absolute_error_rad": float(np.mean(qpos_error[mask])),
            }
            for phase, _ in PHASE_PLAN
        },
        "causal_interpretation": {
            "frame_zero": "identical_reset_prediction_error",
            "later_frames": "closed_loop_prediction_plus_compounding_state_distribution_drift",
            "teacher_forced_loss_claimed": False,
        },
    }


def build_trace_payload(
    *,
    candidate_id: str,
    seed: int,
    source_episode_file_sha256: str,
    source_episode_identity_sha256: str,
    training_identity_sha256: str,
    checkpoint_sha256: str,
    rows: list[dict[str, Any]],
    closed_loop: dict[str, Any],
) -> dict[str, Any]:
    diagnostics = summarize_rows(rows)
    payload = sign_payload(
        {
            "schema_version": TRACE_SCHEMA_VERSION,
            "task_id": "T20.25",
            "candidate_id": candidate_id,
            "seed": seed,
            "source_episode_file_sha256": source_episode_file_sha256,
            "source_episode_identity_sha256": source_episode_identity_sha256,
            "training_identity_sha256": training_identity_sha256,
            "checkpoint_sha256": checkpoint_sha256,
            "comparisons": rows,
            "diagnostics": diagnostics,
            "closed_loop": closed_loop,
            "model_inference_executed": True,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    verify_trace_payload(payload)
    return payload


def verify_trace_payload(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.25 frozen-candidate trace")
    if (
        payload.get("schema_version") != TRACE_SCHEMA_VERSION
        or payload.get("task_id") != "T20.25"
        or payload.get("candidate_id") not in CANDIDATE_IDS
        or payload.get("seed") not in HELD_OUT_SEEDS
    ):
        raise ValueError("T20.25 trace identity or coverage drifted")
    for name in (
        "source_episode_file_sha256",
        "source_episode_identity_sha256",
        "training_identity_sha256",
        "checkpoint_sha256",
    ):
        _sha(payload.get(name), name)
    rows = payload.get("comparisons")
    if payload.get("diagnostics") != summarize_rows(rows):
        raise ValueError("T20.25 trace diagnostics drifted")
    if payload["diagnostics"]["initial_reset_identical_within_tolerance"] is not True:
        raise ValueError("T20.25 candidate did not begin from the identical source reset")
    rollout = payload.get("closed_loop", {})
    action_bytes = json.dumps(
        [row["candidate_action_rad"] for row in rows], separators=(",", ":"), allow_nan=False
    ).encode()
    if (
        rollout.get("seed") != payload["seed"]
        or rollout.get("frame_count") != ROLLOUT_FRAMES
        or rollout.get("policy_action_sequence_sha256")
        != hashlib.sha256(action_bytes).hexdigest()
        or rollout.get("projected_action_frame_count") != 0
        or rollout.get("active_assist_frame_count") != 0
    ):
        raise ValueError("T20.25 trace rollout linkage, projection, or assistance drifted")
    required_false = (
        "optimizer_training",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if payload.get("model_inference_executed") is not True or any(
        payload.get(name) is not False for name in required_false
    ):
        raise ValueError("T20.25 trace execution or authority fields drifted")


def build_localization_gate(traces: list[dict[str, Any]]) -> dict[str, Any]:
    _validate_trace_set(traces)
    gate = _recompose_gate_without_verify(traces)
    verify_localization_gate(gate, traces)
    return gate


def verify_localization_gate(gate: dict[str, Any], traces: list[dict[str, Any]]) -> None:
    verify_signed_payload(gate, label="T20.25 localization gate")
    _validate_trace_set(traces)
    expected = _recompose_gate_without_verify(traces)
    if gate != expected:
        raise ValueError("T20.25 localization gate drifted from trace evidence")


def _validate_trace_set(traces: list[dict[str, Any]]) -> None:
    if len(traces) != 4:
        raise ValueError("T20.25 gate requires four candidate/seed traces")
    for trace in traces:
        verify_trace_payload(trace)
    actual_order = [(trace["candidate_id"], trace["seed"]) for trace in traces]
    expected_order = [
        (candidate, seed) for candidate in CANDIDATE_IDS for seed in HELD_OUT_SEEDS
    ]
    if actual_order != expected_order:
        raise ValueError("T20.25 candidate/seed coverage is missing, duplicated, or reordered")
    keyed = {(trace["candidate_id"], trace["seed"]): trace for trace in traces}
    expected = {(candidate, seed) for candidate in CANDIDATE_IDS for seed in HELD_OUT_SEEDS}
    if set(keyed) != expected:
        raise ValueError("T20.25 candidate/seed coverage is missing, duplicated, or reordered")
    for seed in HELD_OUT_SEEDS:
        clean = keyed[("clean_base", seed)]
        recovery = keyed[("recovery_augmented", seed)]
        if any(
            clean[field] != recovery[field]
            for field in (
                "source_episode_file_sha256",
                "source_episode_identity_sha256",
            )
        ):
            raise ValueError("T20.25 candidates do not share the same source episode")
        for clean_row, recovery_row in zip(
            clean["comparisons"], recovery["comparisons"], strict=True
        ):
            for field in (
                "source_action_rad",
                "source_qpos_rad",
                "source_qvel_rad_s",
            ):
                if clean_row[field] != recovery_row[field]:
                    raise ValueError("T20.25 candidate traces substituted source values")


def _recompose_gate_without_verify(traces: list[dict[str, Any]]) -> dict[str, Any]:
    # The public builder validates traces. This helper mirrors its deterministic
    # composition while avoiding a verifier recursion.
    keyed = {(trace["candidate_id"], trace["seed"]): trace for trace in traces}
    candidate_summaries = {}
    for candidate in CANDIDATE_IDS:
        diagnostics = [keyed[(candidate, seed)]["diagnostics"] for seed in HELD_OUT_SEEDS]
        candidate_summaries[candidate] = {
            "trace_identity_sha256_by_seed": {
                str(seed): keyed[(candidate, seed)]["identity_sha256"] for seed in HELD_OUT_SEEDS
            },
            "frame_zero_action_mean_absolute_error_rad": _mean(
                diagnostics, "frame_zero_action_mean_absolute_error_rad"
            ),
            "frame_zero_non_gripper_mean_absolute_error_rad": _mean(
                diagnostics, "frame_zero_non_gripper_mean_absolute_error_rad"
            ),
            "frame_zero_gripper_absolute_error_rad": _mean(
                diagnostics, "frame_zero_gripper_absolute_error_rad"
            ),
            "precontact_action_mean_absolute_error_rad": _mean(
                diagnostics, "precontact_action_mean_absolute_error_rad"
            ),
            "trajectory_action_mean_absolute_error_rad": _mean(
                diagnostics, "trajectory_action_mean_absolute_error_rad"
            ),
            "trajectory_qpos_mean_absolute_error_rad": _mean(
                diagnostics, "trajectory_qpos_mean_absolute_error_rad"
            ),
        }
    clean = candidate_summaries["clean_base"]
    recovery = candidate_summaries["recovery_augmented"]
    fz = (
        recovery["frame_zero_action_mean_absolute_error_rad"]
        - clean["frame_zero_action_mean_absolute_error_rad"]
    )
    pre = (
        recovery["precontact_action_mean_absolute_error_rad"]
        - clean["precontact_action_mean_absolute_error_rad"]
    )
    direct = {
        str(seed): _candidate_pair_summary(
            keyed[("clean_base", seed)], keyed[("recovery_augmented", seed)]
        )
        for seed in HELD_OUT_SEEDS
    }
    shared_frame_zero = all(
        (
            keyed[(candidate, seed)]["diagnostics"]["first_action_divergence"]
            or {}
        ).get("frame_index")
        == 0
        for candidate in CANDIDATE_IDS
        for seed in HELD_OUT_SEEDS
    )
    return sign_payload({
        "schema_version": GATE_SCHEMA_VERSION,
        "task_id": "T20.25",
        "candidate_summaries": candidate_summaries,
        "recovery_relative_effect": {
            "frame_zero": _effect(fz),
            "precontact": _effect(pre),
            "frame_zero_delta_rad": fz,
            "precontact_delta_rad": pre,
        },
        "candidate_to_candidate_by_seed": direct,
        "earliest_shared_failure_surface": (
            "identical_reset_prediction_error"
            if shared_frame_zero
            else "later_closed_loop_prediction_and_state_drift"
        ),
        "selected_next_hypothesis": (
            "localize_post_precontact_closed_loop_state_drift_before_more_optimizer"
            if pre < -DIVERGENCE_THRESHOLD
            else "audit_recovery_sample_exposure_and_phase_weighting_before_more_optimizer"
        ),
        "optimizer_training": False,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "physical_transfer_ready": False,
        "promotion_eligible": False,
    })


def _validate_rows(rows: Any) -> None:
    if not isinstance(rows, list) or len(rows) != ROLLOUT_FRAMES:
        raise ValueError("T20.25 comparison rows must contain exactly 244 frames")
    expected_phases = [phase for phase, count in PHASE_PLAN for _ in range(count)]
    for index, (row, phase) in enumerate(zip(rows, expected_phases, strict=True)):
        if row.get("frame_index") != index or row.get("phase") != phase:
            raise ValueError("T20.25 comparison frame or phase order drifted")
        for field in (
            "source_action_rad", "candidate_action_rad", "source_qpos_rad",
            "candidate_qpos_rad", "source_qvel_rad_s", "candidate_qvel_rad_s",
        ):
            _vector(row.get(field), field)


def _matrix(rows: list[dict[str, Any]], field: str) -> np.ndarray:
    return np.asarray([row[field] for row in rows], dtype=np.float64)


def _vector(value: Any, label: str) -> list[float]:
    vector = np.asarray(value, dtype=np.float64)
    if vector.shape != (len(JOINT_NAMES),) or not np.isfinite(vector).all():
        raise ValueError(f"T20.25 {label} must be a finite six-joint vector")
    return vector.astype(float).tolist()


def _first_divergence(rows: list[dict[str, Any]], errors: np.ndarray) -> dict[str, Any] | None:
    for index in range(len(rows)):
        maximum = float(np.max(errors[index]))
        if maximum > DIVERGENCE_THRESHOLD:
            joint = int(np.argmax(errors[index]))
            return {
                "frame_index": index,
                "phase": rows[index]["phase"],
                "joint_name": JOINT_NAMES[joint],
                "absolute_error": float(errors[index, joint]),
                "threshold": DIVERGENCE_THRESHOLD,
            }
    return None


def _candidate_pair_summary(
    clean: dict[str, Any], recovery: dict[str, Any]
) -> dict[str, Any]:
    clean_rows = clean["comparisons"]
    recovery_rows = recovery["comparisons"]
    clean_action = _matrix(clean_rows, "candidate_action_rad")
    recovery_action = _matrix(recovery_rows, "candidate_action_rad")
    clean_qpos = _matrix(clean_rows, "candidate_qpos_rad")
    recovery_qpos = _matrix(recovery_rows, "candidate_qpos_rad")
    action_error = np.abs(recovery_action - clean_action)
    qpos_error = np.abs(recovery_qpos - clean_qpos)
    precontact = np.asarray(
        [row["phase"] in PRECONTACT_PHASES for row in clean_rows]
    )
    return {
        "frame_zero_action_mean_absolute_difference_rad": float(
            np.mean(action_error[0])
        ),
        "precontact_action_mean_absolute_difference_rad": float(
            np.mean(action_error[precontact])
        ),
        "trajectory_action_mean_absolute_difference_rad": float(
            np.mean(action_error)
        ),
        "trajectory_qpos_mean_absolute_difference_rad": float(np.mean(qpos_error)),
        "first_action_divergence": _first_divergence(clean_rows, action_error),
        "first_qpos_divergence": _first_divergence(clean_rows, qpos_error),
    }


def _mean(rows: list[dict[str, Any]], field: str) -> float:
    return float(np.mean([row[field] for row in rows]))


def _effect(delta: float) -> str:
    if delta < -DIVERGENCE_THRESHOLD:
        return "improved"
    if delta > DIVERGENCE_THRESHOLD:
        return "regressed"
    return "unchanged"


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError(f"T20.25 {label} must be lowercase SHA-256")
    return value
