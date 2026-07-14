"""Frame-zero frozen-inference variability contracts for T20.26."""

from __future__ import annotations

from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.t20_25_frozen_candidate_localization import CANDIDATE_IDS


BATCH_SCHEMA_VERSION = "scenesmith.t20_26_frame_zero_inference_batch.v1"
GATE_SCHEMA_VERSION = "scenesmith.t20_26_frame_zero_variability_gate.v1"
BATCH_IDS = (1, 2)
SAMPLE_SCHEDULE = (
    ("same_01", "same_seed_repeat", 20260714),
    ("same_02", "same_seed_repeat", 20260714),
    ("same_03", "same_seed_repeat", 20260714),
    ("distinct_01", "distinct_seed_sample", 20260720),
    ("distinct_02", "distinct_seed_sample", 20260721),
    ("distinct_03", "distinct_seed_sample", 20260722),
    ("distinct_04", "distinct_seed_sample", 20260723),
)


def build_batch(
    *,
    candidate_id: str,
    batch_id: int,
    source_episode_file_sha256: str,
    source_episode_identity_sha256: str,
    training_identity_sha256: str,
    checkpoint_sha256: str,
    lerobot_stack_identity_sha256: str,
    observation: dict[str, Any],
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    _validate_observation(observation)
    _validate_samples(samples)
    same = _actions(samples, "same_seed_repeat")
    distinct = _actions(samples, "distinct_seed_sample")
    diagnostics = {
        "sample_count": len(samples),
        "same_seed_repeat_count": len(same),
        "distinct_seed_sample_count": len(distinct),
        "same_seed_within_process_max_abs_difference_rad": _max_pairwise(same),
        "distinct_seed_max_pairwise_difference_rad": _max_pairwise(distinct),
        "distinct_seed_per_joint_standard_deviation_rad": {
            name: float(value)
            for name, value in zip(JOINT_NAMES, np.std(distinct, axis=0), strict=True)
        },
        "all_actions_finite": True,
    }
    batch = sign_payload(
        {
            "schema_version": BATCH_SCHEMA_VERSION,
            "task_id": "T20.26",
            "candidate_id": candidate_id,
            "batch_id": batch_id,
            "source_episode_file_sha256": source_episode_file_sha256,
            "source_episode_identity_sha256": source_episode_identity_sha256,
            "training_identity_sha256": training_identity_sha256,
            "checkpoint_sha256": checkpoint_sha256,
            "lerobot_stack_identity_sha256": lerobot_stack_identity_sha256,
            "observation": observation,
            "samples": samples,
            "diagnostics": diagnostics,
            "model_inference_executed": True,
            "action_applied": False,
            "closed_loop_rollout_executed": False,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    verify_batch(batch)
    return batch


def verify_batch(batch: dict[str, Any]) -> None:
    verify_signed_payload(batch, label="T20.26 frame-zero batch")
    if (
        batch.get("schema_version") != BATCH_SCHEMA_VERSION
        or batch.get("task_id") != "T20.26"
        or batch.get("candidate_id") not in CANDIDATE_IDS
        or batch.get("batch_id") not in BATCH_IDS
    ):
        raise ValueError("T20.26 batch identity or coverage drifted")
    for field in (
        "source_episode_file_sha256",
        "source_episode_identity_sha256",
        "training_identity_sha256",
        "checkpoint_sha256",
        "lerobot_stack_identity_sha256",
    ):
        _sha(batch.get(field), field)
    _validate_observation(batch.get("observation"))
    samples = batch.get("samples")
    _validate_samples(samples)
    same = _actions(samples, "same_seed_repeat")
    distinct = _actions(samples, "distinct_seed_sample")
    expected_diagnostics = {
        "sample_count": len(samples),
        "same_seed_repeat_count": len(same),
        "distinct_seed_sample_count": len(distinct),
        "same_seed_within_process_max_abs_difference_rad": _max_pairwise(same),
        "distinct_seed_max_pairwise_difference_rad": _max_pairwise(distinct),
        "distinct_seed_per_joint_standard_deviation_rad": {
            name: float(value)
            for name, value in zip(JOINT_NAMES, np.std(distinct, axis=0), strict=True)
        },
        "all_actions_finite": True,
    }
    if batch.get("diagnostics") != expected_diagnostics:
        raise ValueError("T20.26 batch diagnostics drifted")
    required_false = (
        "action_applied",
        "closed_loop_rollout_executed",
        "optimizer_training",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if batch.get("model_inference_executed") is not True or any(
        batch.get(field) is not False for field in required_false
    ):
        raise ValueError("T20.26 execution or authority fields drifted")


def build_gate(batches: list[dict[str, Any]]) -> dict[str, Any]:
    _validate_batch_set(batches)
    gate = _compose_gate(batches)
    verify_gate(gate, batches)
    return gate


def verify_gate(gate: dict[str, Any], batches: list[dict[str, Any]]) -> None:
    verify_signed_payload(gate, label="T20.26 variability gate")
    _validate_batch_set(batches)
    if gate != _compose_gate(batches):
        raise ValueError("T20.26 variability gate drifted from batch evidence")


def _validate_batch_set(batches: list[dict[str, Any]]) -> None:
    if len(batches) != 4:
        raise ValueError("T20.26 gate requires four candidate/batch artifacts")
    for batch in batches:
        verify_batch(batch)
    actual = [(batch["candidate_id"], batch["batch_id"]) for batch in batches]
    expected = [(candidate, batch) for candidate in CANDIDATE_IDS for batch in BATCH_IDS]
    if actual != expected:
        raise ValueError("T20.26 candidate/batch coverage is missing or reordered")
    keyed = {(batch["candidate_id"], batch["batch_id"]): batch for batch in batches}
    reference = batches[0]
    for batch in batches[1:]:
        if any(
            batch[field] != reference[field]
            for field in (
                "source_episode_file_sha256",
                "source_episode_identity_sha256",
                "lerobot_stack_identity_sha256",
                "observation",
            )
        ):
            raise ValueError("T20.26 batches do not bind the identical observation/runtime")
    for candidate in CANDIDATE_IDS:
        if (
            keyed[(candidate, 1)]["checkpoint_sha256"]
            != keyed[(candidate, 2)]["checkpoint_sha256"]
        ):
            raise ValueError("T20.26 candidate checkpoint changed across processes")


def _compose_gate(batches: list[dict[str, Any]]) -> dict[str, Any]:
    keyed = {(batch["candidate_id"], batch["batch_id"]): batch for batch in batches}
    summaries = {}
    for candidate in CANDIDATE_IDS:
        first = keyed[(candidate, 1)]
        second = keyed[(candidate, 2)]
        a = _actions(first["samples"], "same_seed_repeat")[0]
        b = _actions(second["samples"], "same_seed_repeat")[0]
        summaries[candidate] = {
            "batch_identity_sha256": {
                "1": first["identity_sha256"],
                "2": second["identity_sha256"],
            },
            "within_process_same_seed_max_abs_difference_rad": max(
                first["diagnostics"]["same_seed_within_process_max_abs_difference_rad"],
                second["diagnostics"]["same_seed_within_process_max_abs_difference_rad"],
            ),
            "cross_process_same_seed_max_abs_difference_rad": float(np.max(np.abs(a - b))),
            "maximum_distinct_seed_pairwise_difference_rad": max(
                first["diagnostics"]["distinct_seed_max_pairwise_difference_rad"],
                second["diagnostics"]["distinct_seed_max_pairwise_difference_rad"],
            ),
        }
    cross_process_gap = any(
        row["cross_process_same_seed_max_abs_difference_rad"] > 1e-8
        for row in summaries.values()
    )
    return sign_payload(
        {
            "schema_version": GATE_SCHEMA_VERSION,
            "task_id": "T20.26",
            "candidate_summaries": summaries,
            "cross_process_same_seed_gap_reproduced": cross_process_gap,
            "selected_next_hypothesis": (
                "audit_unbound_runtime_or_random_generator_state"
                if cross_process_gap
                else (
                    "treat_prior_clean_hash_as_historical_runtime_specific_and_"
                    "repeat_training_comparison_with_multi_seed_inference"
                )
            ),
            "action_applied": False,
            "closed_loop_rollout_executed": False,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def _validate_observation(observation: Any) -> None:
    if not isinstance(observation, dict) or observation.get("seed") != 6:
        raise ValueError("T20.26 observation must be held-out seed 6 frame zero")
    if observation.get("frame_index") != 0 or observation.get("phase") != "approach":
        raise ValueError("T20.26 observation frame or phase drifted")
    for field in ("top_raw_sha256", "wrist_raw_sha256"):
        _sha(observation.get(field), field)
    for field in ("qpos_rad", "qvel_rad_s"):
        _vector(observation.get(field), field)
    value = observation.get("source_state_max_abs_error")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
        or value > 1e-6
        or value < 0.0
    ):
        raise ValueError("T20.26 observation does not match the source reset")


def _validate_samples(samples: Any) -> None:
    if not isinstance(samples, list) or len(samples) != len(SAMPLE_SCHEDULE):
        raise ValueError("T20.26 sample schedule is incomplete")
    for sample, (sample_id, mode, seed) in zip(samples, SAMPLE_SCHEDULE, strict=True):
        if (
            sample.get("sample_id") != sample_id
            or sample.get("mode") != mode
            or sample.get("inference_seed") != seed
        ):
            raise ValueError("T20.26 sample schedule is missing or reordered")
        _vector(sample.get("requested_action_rad"), "requested action")


def _actions(samples: list[dict[str, Any]], mode: str) -> np.ndarray:
    return np.asarray(
        [sample["requested_action_rad"] for sample in samples if sample["mode"] == mode],
        dtype=np.float64,
    )


def _max_pairwise(values: np.ndarray) -> float:
    return float(max(np.max(np.abs(a - b)) for a in values for b in values))


def _vector(value: Any, label: str) -> list[float]:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (len(JOINT_NAMES),) or not np.isfinite(result).all():
        raise ValueError(f"T20.26 {label} must be a finite six-joint vector")
    return result.astype(float).tolist()


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError(f"T20.26 {label} must be lowercase SHA-256")
    return value
