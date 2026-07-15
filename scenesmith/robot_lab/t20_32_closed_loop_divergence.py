"""Signed complete-trace localization for T20.32."""

from __future__ import annotations

import hashlib
import json

from typing import Any

import numpy as np

from scenesmith.robot_lab.act_grasp_closed_loop import PHASE_PLAN, ROLLOUT_FRAMES
from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID


THRESHOLD_SCHEMA_VERSION = "scenesmith.t20_32_divergence_thresholds.v1"
TRACE_SCHEMA_VERSION = "scenesmith.t20_32_closed_loop_trace.v1"
REPORT_SCHEMA_VERSION = "scenesmith.t20_32_divergence_localization_report.v1"
ADAPTER_IDS = (
    "t20_24_recovery_augmented",
    "t20_31_nominal_action_quantile",
)
ALL_SEEDS = (0, 6, 7)
HELD_OUT_SEEDS = (6, 7)
TRAINING_SEED = 0
ACTION_HORIZON = 5
ACTION_DIVERGENCE_THRESHOLD_RAD = 0.05
STATE_DIVERGENCE_THRESHOLD_RAD = 0.01
RESET_TOLERANCE_RAD = 1e-6
PRECONTACT_PHASES = ("approach", "pregrasp")


def build_threshold_contract() -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": THRESHOLD_SCHEMA_VERSION,
            "task_id": "T20.32",
            "joint_names": list(JOINT_NAMES),
            "action_horizon": ACTION_HORIZON,
            "action_divergence_threshold_rad": ACTION_DIVERGENCE_THRESHOLD_RAD,
            "state_divergence_threshold_rad": STATE_DIVERGENCE_THRESHOLD_RAD,
            "initial_reset_tolerance_rad": RESET_TOLERANCE_RAD,
            "classification_order": [
                "frame_zero_prediction",
                "action_chunk_boundary",
                "pre_contact_drift",
                "observation_feedback_compounding",
            ],
            "threshold_basis": {
                "action": "absolute per-joint requested-action error",
                "state": "absolute per-joint qpos error",
                "chunk_boundary": "frame_index modulo action_horizon equals zero",
            },
            "optimizer_training": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_threshold_contract(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.32 divergence threshold contract")
    if payload != build_threshold_contract():
        raise ValueError("T20.32 threshold contract drifted")


def build_comparison_rows(
    source_frames: list[dict[str, Any]], candidate_frames: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if len(source_frames) != ROLLOUT_FRAMES or len(candidate_frames) != ROLLOUT_FRAMES:
        raise ValueError("T20.32 requires complete 244-frame source and candidate traces")
    rows: list[dict[str, Any]] = []
    for index, (source, candidate) in enumerate(
        zip(source_frames, candidate_frames, strict=True)
    ):
        phase = source.get("source_phase")
        if phase != candidate.get("phase"):
            raise ValueError("T20.32 source/candidate phase order drifted")
        rows.append(
            {
                "frame_index": index,
                "phase": phase,
                "chunk_index": index // ACTION_HORIZON,
                "chunk_offset": index % ACTION_HORIZON,
                "source_requested_action_rad": _source_action(source, "requested"),
                "source_applied_action_rad": _source_action(source, "sent"),
                "candidate_requested_action_rad": _vector(
                    candidate.get("policy_requested_action"),
                    "candidate requested action",
                ),
                "candidate_applied_action_rad": _vector(
                    candidate.get("policy_applied_action"),
                    "candidate applied action",
                ),
                "source_qpos_rad": _vector(
                    source.get("observations", {}).get(
                        "joint_position_mujoco_rad"
                    ),
                    "source qpos",
                ),
                "candidate_qpos_rad": _vector(
                    candidate.get("mujoco_qpos"), "candidate qpos"
                ),
                "source_qvel_rad_s": _vector(
                    source.get("observations", {}).get(
                        "joint_velocity_mujoco_rad_s"
                    ),
                    "source qvel",
                ),
                "candidate_qvel_rad_s": _vector(
                    candidate.get("mujoco_qvel"), "candidate qvel"
                ),
                "candidate_anchor_position_m": _position(
                    candidate.get("cube_positions_m", {}).get(OBJECT_ID)
                ),
                "candidate_strict_contact": bool(
                    candidate.get("t20_32_strict_contact", False)
                ),
            }
        )
    _validate_rows(rows)
    return rows


def summarize_rows(rows: list[dict[str, Any]], threshold: dict[str, Any]) -> dict[str, Any]:
    verify_threshold_contract(threshold)
    _validate_rows(rows)
    source_action = _matrix(rows, "source_requested_action_rad")
    requested = _matrix(rows, "candidate_requested_action_rad")
    applied = _matrix(rows, "candidate_applied_action_rad")
    source_qpos = _matrix(rows, "source_qpos_rad")
    qpos = _matrix(rows, "candidate_qpos_rad")
    source_qvel = _matrix(rows, "source_qvel_rad_s")
    qvel = _matrix(rows, "candidate_qvel_rad_s")
    action_error = np.abs(requested - source_action)
    qpos_error = np.abs(qpos - source_qpos)
    qvel_error = np.abs(qvel - source_qvel)
    requested_applied_error = np.abs(requested - applied)
    action_threshold = float(threshold["action_divergence_threshold_rad"])
    state_threshold = float(threshold["state_divergence_threshold_rad"])
    reset_tolerance = float(threshold["initial_reset_tolerance_rad"])
    first_action = _first_divergence(rows, action_error, action_threshold)
    first_state = _first_divergence(rows, qpos_error, state_threshold)
    first_event = _earliest(first_action, first_state)
    classification = _classify(first_event)
    arm_error = action_error[:, :-1]
    gripper_error = action_error[:, -1]
    return {
        "frame_count": ROLLOUT_FRAMES,
        "joint_names": list(JOINT_NAMES),
        "phase_frame_counts": {
            phase: sum(row["phase"] == phase for row in rows)
            for phase, _ in PHASE_PLAN
        },
        "all_values_finite": True,
        "initial_reset_identical_within_tolerance": bool(
            np.max(qpos_error[0]) <= reset_tolerance
            and np.max(qvel_error[0]) <= reset_tolerance
        ),
        "requested_applied_maximum_error_rad": float(
            np.max(requested_applied_error)
        ),
        "frame_zero_action_mean_absolute_error_rad": float(
            np.mean(action_error[0])
        ),
        "frame_zero_arm_mean_absolute_error_rad": float(
            np.mean(action_error[0, :-1])
        ),
        "frame_zero_gripper_absolute_error_rad": float(action_error[0, -1]),
        "trajectory_action_mean_absolute_error_rad": float(np.mean(action_error)),
        "trajectory_qpos_mean_absolute_error_rad": float(np.mean(qpos_error)),
        "trajectory_qvel_mean_absolute_error_rad_s": float(np.mean(qvel_error)),
        "first_action_divergence": first_action,
        "first_state_divergence": first_state,
        "earliest_divergence": first_event,
        "divergence_class": classification,
        "per_joint_action_divergence_onset": _per_joint_onset(
            rows, action_error, action_threshold
        ),
        "per_joint_state_divergence_onset": _per_joint_onset(
            rows, qpos_error, state_threshold
        ),
        "gripper_versus_arm_attribution": {
            "arm_trajectory_mean_absolute_error_rad": float(np.mean(arm_error)),
            "gripper_trajectory_mean_absolute_error_rad": float(
                np.mean(gripper_error)
            ),
            "dominant": (
                "arm"
                if float(np.mean(arm_error)) > float(np.mean(gripper_error))
                else "gripper"
            ),
        },
        "strict_contact_frame_count": sum(
            bool(row["candidate_strict_contact"]) for row in rows
        ),
        "candidate_anchor_start_position_m": rows[0][
            "candidate_anchor_position_m"
        ],
        "candidate_anchor_final_position_m": rows[-1][
            "candidate_anchor_position_m"
        ],
        "causal_scope": (
            "source-relative closed-loop association; no teacher-forced or "
            "single-cause training attribution"
        ),
    }


def build_trace_payload(
    *,
    threshold: dict[str, Any],
    adapter_id: str,
    seed: int,
    inference_seed: int,
    source_episode_file_sha256: str,
    source_episode_identity_sha256: str,
    training_identity_sha256: str,
    checkpoint_sha256: str,
    rows: list[dict[str, Any]],
    closed_loop: dict[str, Any],
    prior_evaluation_identity_sha256: str | None,
    prior_action_sequence_sha256: str | None,
) -> dict[str, Any]:
    verify_threshold_contract(threshold)
    diagnostics = summarize_rows(rows, threshold)
    requested_sha = _sequence_sha(rows, "candidate_requested_action_rad")
    applied_sha = _sequence_sha(rows, "candidate_applied_action_rad")
    prior_reproduced = (
        None
        if prior_action_sequence_sha256 is None
        else prior_action_sequence_sha256 == requested_sha
    )
    payload = sign_payload(
        {
            "schema_version": TRACE_SCHEMA_VERSION,
            "task_id": "T20.32",
            "adapter_id": adapter_id,
            "seed": seed,
            "seed_role": "training" if seed == TRAINING_SEED else "held_out",
            "inference_seed": inference_seed,
            "threshold_contract_identity_sha256": threshold["identity_sha256"],
            "source_episode_file_sha256": source_episode_file_sha256,
            "source_episode_identity_sha256": source_episode_identity_sha256,
            "training_identity_sha256": training_identity_sha256,
            "checkpoint_sha256": checkpoint_sha256,
            "comparisons": rows,
            "diagnostics": diagnostics,
            "closed_loop": closed_loop,
            "requested_action_sequence_sha256": requested_sha,
            "applied_action_sequence_sha256": applied_sha,
            "prior_evaluation_identity_sha256": prior_evaluation_identity_sha256,
            "prior_action_sequence_sha256": prior_action_sequence_sha256,
            "prior_action_sequence_reproduced_exactly": prior_reproduced,
            "training_seed_reproduction_strict_success": (
                closed_loop.get("simulation_semantic_strict_success")
                if seed == TRAINING_SEED
                else None
            ),
            "model_inference_executed": True,
            "optimizer_training": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "twin_updated": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    verify_trace_payload(payload, threshold=threshold)
    return payload


def verify_trace_payload(
    payload: dict[str, Any], *, threshold: dict[str, Any]
) -> None:
    verify_threshold_contract(threshold)
    verify_signed_payload(payload, label="T20.32 closed-loop trace")
    if (
        payload.get("schema_version") != TRACE_SCHEMA_VERSION
        or payload.get("task_id") != "T20.32"
        or payload.get("adapter_id") not in ADAPTER_IDS
        or payload.get("seed") not in ALL_SEEDS
        or payload.get("seed_role")
        != ("training" if payload.get("seed") == TRAINING_SEED else "held_out")
    ):
        raise ValueError("T20.32 trace coverage or identity drifted")
    if payload.get("threshold_contract_identity_sha256") != threshold.get(
        "identity_sha256"
    ):
        raise ValueError("T20.32 trace threshold binding drifted")
    if isinstance(payload.get("inference_seed"), bool) or not isinstance(
        payload.get("inference_seed"), int
    ):
        raise ValueError("T20.32 inference seed drifted")
    for field in (
        "source_episode_file_sha256",
        "source_episode_identity_sha256",
        "training_identity_sha256",
        "checkpoint_sha256",
        "requested_action_sequence_sha256",
        "applied_action_sequence_sha256",
    ):
        _sha(payload.get(field), field)
    rows = payload.get("comparisons")
    if payload.get("diagnostics") != summarize_rows(rows, threshold):
        raise ValueError("T20.32 trace diagnostics drifted")
    if payload["diagnostics"]["initial_reset_identical_within_tolerance"] is not True:
        raise ValueError("T20.32 trace did not share the source reset")
    rollout = payload.get("closed_loop", {})
    verify_signed_payload(rollout, label="T20.32 embedded closed-loop rollout")
    if (
        rollout.get("seed") != payload["seed"]
        or rollout.get("frame_count") != ROLLOUT_FRAMES
        or rollout.get("policy_action_sequence_sha256")
        != payload["requested_action_sequence_sha256"]
        or payload["requested_action_sequence_sha256"]
        != _sequence_sha(rows, "candidate_requested_action_rad")
        or payload["applied_action_sequence_sha256"]
        != _sequence_sha(rows, "candidate_applied_action_rad")
        or rollout.get("projected_action_frame_count") != 0
        or rollout.get("active_assist_frame_count") != 0
    ):
        raise ValueError(
            "T20.32 rollout linkage, trace shape, projection, or assistance drifted"
        )
    prior_identity = payload.get("prior_evaluation_identity_sha256")
    prior_sha = payload.get("prior_action_sequence_sha256")
    prior_reproduced = payload.get("prior_action_sequence_reproduced_exactly")
    if payload["seed"] in HELD_OUT_SEEDS:
        _sha(prior_identity, "prior evaluation identity")
        _sha(prior_sha, "prior action sequence")
        if prior_reproduced is not True or prior_sha != payload[
            "requested_action_sequence_sha256"
        ]:
            raise ValueError("T20.32 held-out frozen replay did not reproduce exactly")
    elif any(value is not None for value in (prior_identity, prior_sha, prior_reproduced)):
        raise ValueError("T20.32 training seed fabricated a prior evaluation")
    expected_training = (
        rollout.get("simulation_semantic_strict_success")
        if payload["seed"] == TRAINING_SEED
        else None
    )
    if payload.get("training_seed_reproduction_strict_success") is not expected_training:
        raise ValueError("T20.32 training-seed reproduction outcome drifted")
    required_false = (
        "optimizer_training",
        "dataset_mutated",
        "statistics_changed",
        "twin_updated",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if payload.get("model_inference_executed") is not True or any(
        payload.get(field) is not False for field in required_false
    ):
        raise ValueError("T20.32 trace execution or authority fields drifted")


def build_localization_report(
    *, threshold: dict[str, Any], traces: list[dict[str, Any]]
) -> dict[str, Any]:
    _validate_trace_set(threshold, traces)
    report = _compose_report(threshold, traces)
    verify_localization_report(report, threshold=threshold, traces=traces)
    return report


def verify_localization_report(
    report: dict[str, Any], *, threshold: dict[str, Any], traces: list[dict[str, Any]]
) -> None:
    verify_signed_payload(report, label="T20.32 divergence localization report")
    _validate_trace_set(threshold, traces)
    if report != _compose_report(threshold, traces):
        raise ValueError("T20.32 localization report drifted from trace evidence")


def _validate_trace_set(
    threshold: dict[str, Any], traces: list[dict[str, Any]]
) -> None:
    verify_threshold_contract(threshold)
    if not isinstance(traces, list) or len(traces) != 6:
        raise ValueError("T20.32 report requires exactly six adapter/seed traces")
    for trace in traces:
        verify_trace_payload(trace, threshold=threshold)
    actual = [(trace["adapter_id"], trace["seed"]) for trace in traces]
    expected = [
        (adapter, seed) for adapter in ADAPTER_IDS for seed in ALL_SEEDS
    ]
    if actual != expected:
        raise ValueError("T20.32 trace coverage order is missing, duplicated, or reordered")
    keyed = {(trace["adapter_id"], trace["seed"]): trace for trace in traces}
    for seed in ALL_SEEDS:
        left = keyed[(ADAPTER_IDS[0], seed)]
        right = keyed[(ADAPTER_IDS[1], seed)]
        for field in (
            "source_episode_file_sha256",
            "source_episode_identity_sha256",
        ):
            if left[field] != right[field]:
                raise ValueError("T20.32 adapters substituted source evidence")
        for left_row, right_row in zip(
            left["comparisons"], right["comparisons"], strict=True
        ):
            for field in (
                "source_requested_action_rad",
                "source_applied_action_rad",
                "source_qpos_rad",
                "source_qvel_rad_s",
            ):
                if left_row[field] != right_row[field]:
                    raise ValueError("T20.32 adapters substituted source trace values")


def _compose_report(
    threshold: dict[str, Any], traces: list[dict[str, Any]]
) -> dict[str, Any]:
    keyed = {(trace["adapter_id"], trace["seed"]): trace for trace in traces}
    training = [keyed[(adapter, TRAINING_SEED)] for adapter in ADAPTER_IDS]
    all_training_success = all(
        trace["training_seed_reproduction_strict_success"] is True
        for trace in training
    )
    frame_zero_training_failure = any(
        (trace["diagnostics"]["first_action_divergence"] or {}).get(
            "frame_index"
        )
        == 0
        for trace in training
    )
    training_classes = {
        trace["diagnostics"]["divergence_class"] for trace in training
    }
    if all_training_success:
        lowest_gate = "D"
        selected = "gate_d_dataset_coverage"
    elif frame_zero_training_failure:
        lowest_gate = "B"
        selected = "gate_b_memorization_or_model_plumbing"
    elif "action_chunk_boundary" in training_classes:
        lowest_gate = "C"
        selected = "gate_c_action_chunk_execution_semantics"
    else:
        lowest_gate = "C"
        selected = "gate_c_observation_feedback_or_cadence"
    localizations = {
        adapter: {
            str(seed): {
                "trace_identity_sha256": keyed[(adapter, seed)][
                    "identity_sha256"
                ],
                "seed_role": keyed[(adapter, seed)]["seed_role"],
                "first_action_divergence": keyed[(adapter, seed)][
                    "diagnostics"
                ]["first_action_divergence"],
                "first_state_divergence": keyed[(adapter, seed)][
                    "diagnostics"
                ]["first_state_divergence"],
                "earliest_divergence": keyed[(adapter, seed)]["diagnostics"][
                    "earliest_divergence"
                ],
                "divergence_class": keyed[(adapter, seed)]["diagnostics"][
                    "divergence_class"
                ],
                "per_joint_action_divergence_onset": keyed[(adapter, seed)][
                    "diagnostics"
                ]["per_joint_action_divergence_onset"],
                "per_joint_state_divergence_onset": keyed[(adapter, seed)][
                    "diagnostics"
                ]["per_joint_state_divergence_onset"],
                "gripper_versus_arm_attribution": keyed[(adapter, seed)][
                    "diagnostics"
                ]["gripper_versus_arm_attribution"],
                "strict_success": keyed[(adapter, seed)]["closed_loop"][
                    "simulation_semantic_strict_success"
                ],
                "terminal_outcome": keyed[(adapter, seed)]["closed_loop"][
                    "terminal_outcome"
                ],
                "prior_action_sequence_reproduced_exactly": keyed[
                    (adapter, seed)
                ]["prior_action_sequence_reproduced_exactly"],
            }
            for seed in ALL_SEEDS
        }
        for adapter in ADAPTER_IDS
    }
    return sign_payload(
        {
            "schema_version": REPORT_SCHEMA_VERSION,
            "task_id": "T20.32",
            "threshold_contract_identity_sha256": threshold[
                "identity_sha256"
            ],
            "trace_count": len(traces),
            "frame_count_per_trace": ROLLOUT_FRAMES,
            "total_compared_frames": len(traces) * ROLLOUT_FRAMES,
            "localizations": localizations,
            "training_seed_strict_success_count": sum(
                trace["training_seed_reproduction_strict_success"] is True
                for trace in training
            ),
            "lowest_unmet_capability_gate": lowest_gate,
            "selected_next_gate_hypothesis": selected,
            "routing_basis": (
                "training-seed reproduction precedes held-out generalization; "
                "frame-zero failure routes Gate B, aligned onset at or after "
                "execution routes Gate C, and training-seed success routes Gate D"
            ),
            "authority_granted": [
                "t20_32_offline_closed_loop_divergence_localization_verified"
            ],
            "authority_not_granted": [
                "optimizer_training",
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
            "optimizer_training": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "twin_updated": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def _validate_rows(rows: Any) -> None:
    if not isinstance(rows, list) or len(rows) != ROLLOUT_FRAMES:
        raise ValueError("T20.32 comparison rows must contain exactly 244 frames")
    expected_phases = [phase for phase, count in PHASE_PLAN for _ in range(count)]
    for index, (row, phase) in enumerate(zip(rows, expected_phases, strict=True)):
        if (
            row.get("frame_index") != index
            or row.get("phase") != phase
            or row.get("chunk_index") != index // ACTION_HORIZON
            or row.get("chunk_offset") != index % ACTION_HORIZON
        ):
            raise ValueError("T20.32 comparison frame, phase, or chunk order drifted")
        for field in (
            "source_requested_action_rad",
            "source_applied_action_rad",
            "candidate_requested_action_rad",
            "candidate_applied_action_rad",
            "source_qpos_rad",
            "candidate_qpos_rad",
            "source_qvel_rad_s",
            "candidate_qvel_rad_s",
        ):
            _vector(row.get(field), field)
        _position(row.get("candidate_anchor_position_m"))
        if not isinstance(row.get("candidate_strict_contact"), bool):
            raise ValueError("T20.32 strict-contact trace value must be boolean")


def _source_action(source: dict[str, Any], stage: str) -> list[float]:
    return _vector(
        source.get("actions", {}).get(stage, {}).get("values"),
        f"source {stage} action",
    )


def _vector(value: Any, label: str) -> list[float]:
    vector = np.asarray(value, dtype=np.float64)
    if vector.shape != (len(JOINT_NAMES),) or not np.isfinite(vector).all():
        raise ValueError(f"T20.32 {label} must be a finite six-joint vector")
    return vector.astype(float).tolist()


def _position(value: Any) -> list[float]:
    position = np.asarray(value, dtype=np.float64)
    if position.shape != (3,) or not np.isfinite(position).all():
        raise ValueError("T20.32 anchor position must be a finite xyz vector")
    return position.astype(float).tolist()


def _matrix(rows: list[dict[str, Any]], field: str) -> np.ndarray:
    return np.asarray([row[field] for row in rows], dtype=np.float64)


def _sequence_sha(rows: list[dict[str, Any]], field: str) -> str:
    encoded = json.dumps(
        [row[field] for row in rows], separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _first_divergence(
    rows: list[dict[str, Any]], errors: np.ndarray, threshold: float
) -> dict[str, Any] | None:
    for index, row in enumerate(rows):
        joint = int(np.argmax(errors[index]))
        value = float(errors[index, joint])
        if value > threshold:
            return {
                "frame_index": index,
                "phase": row["phase"],
                "chunk_index": row["chunk_index"],
                "chunk_offset": row["chunk_offset"],
                "joint_name": JOINT_NAMES[joint],
                "absolute_error": value,
                "threshold": threshold,
            }
    return None


def _per_joint_onset(
    rows: list[dict[str, Any]], errors: np.ndarray, threshold: float
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for joint, name in enumerate(JOINT_NAMES):
        indices = np.flatnonzero(errors[:, joint] > threshold)
        if not len(indices):
            result[name] = None
            continue
        index = int(indices[0])
        result[name] = {
            "frame_index": index,
            "phase": rows[index]["phase"],
            "chunk_index": rows[index]["chunk_index"],
            "chunk_offset": rows[index]["chunk_offset"],
            "absolute_error": float(errors[index, joint]),
            "threshold": threshold,
        }
    return result


def _earliest(*events: dict[str, Any] | None) -> dict[str, Any] | None:
    present = [event for event in events if event is not None]
    return min(present, key=lambda event: event["frame_index"]) if present else None


def _classify(event: dict[str, Any] | None) -> str:
    if event is None:
        return "no_declared_divergence"
    if event["frame_index"] == 0:
        return "frame_zero_prediction"
    if event["chunk_offset"] == 0:
        return "action_chunk_boundary"
    if event["phase"] in PRECONTACT_PHASES:
        return "pre_contact_drift"
    return "observation_feedback_compounding"


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.32 {label} must be lowercase SHA-256")
    return value
