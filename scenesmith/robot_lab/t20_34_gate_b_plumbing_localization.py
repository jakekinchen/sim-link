"""Signed optimizer-free Gate B plumbing localization for T20.34."""

from __future__ import annotations

import hashlib
import math

from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    ACTION_HORIZON,
    INFERENCE_SEEDS,
    verify_run,
    verify_training_spec,
)


SCHEMA_VERSION = "scenesmith.t20_34_gate_b_plumbing_localization.v1"
OUTPUT_PATH = "configurations/robot_lab/t20_34_gate_b_plumbing_localization.json"


def build_report(
    *, spec: dict[str, Any], prior_run: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    verify_training_spec(spec)
    verify_run(
        prior_run,
        spec=spec,
        authority_identity=prior_run["authority_decision_identity_sha256"],
    )
    payload = _compose(spec=spec, prior_run=prior_run, evidence=evidence)
    verify_report(payload, spec=spec, prior_run=prior_run)
    return payload


def verify_report(
    payload: dict[str, Any], *, spec: dict[str, Any], prior_run: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.34 Gate B plumbing localization")
    expected = _compose(
        spec=spec, prior_run=prior_run, evidence=payload.get("evidence")
    )
    if payload != expected:
        raise ValueError("T20.34 report drifted from bound evidence")


def _compose(
    *, spec: dict[str, Any], prior_run: dict[str, Any], evidence: Any
) -> dict[str, Any]:
    verify_training_spec(spec)
    verify_run(
        prior_run,
        spec=spec,
        authority_identity=prior_run["authority_decision_identity_sha256"],
    )
    if not isinstance(evidence, dict):
        raise ValueError("T20.34 evidence must be an object")
    target = _matrix(evidence.get("source_target_action_rad"), "source target")
    source_hash = hashlib.sha256(
        canonical_json_bytes(target.astype(float).tolist())
    ).hexdigest()
    if source_hash != spec["source_batch"]["measured_action_chunk_sha256"]:
        raise ValueError("T20.34 source target drifted from T20.33")
    base_chunks = _chunks(evidence.get("base_decoded_chunks_rad"), "base")
    adapter_chunks = _chunks(evidence.get("adapter_decoded_chunks_rad"), "adapter")
    prior_hashes = {
        row["inference_seed"]: row["decoded_action_chunk_sha256"]
        for row in prior_run["decoded_action_chunks"]
    }
    rows = []
    unchanged = []
    for seed in INFERENCE_SEEDS:
        base = base_chunks[seed]
        adapter = adapter_chunks[seed]
        adapter_hash = _chunk_sha(adapter)
        if adapter_hash != prior_hashes[seed]:
            raise ValueError("T20.34 adapter replay hash drifted from T20.33")
        base_error = np.abs(base - target)
        adapter_error = np.abs(adapter - target)
        movement = adapter - base
        direction = target - base
        denominator = float(np.linalg.norm(movement) * np.linalg.norm(direction))
        cosine = 0.0 if denominator == 0 else float(np.sum(movement * direction) / denominator)
        is_unchanged = bool(np.array_equal(base, adapter))
        unchanged.append(is_unchanged)
        rows.append(
            {
                "inference_seed": seed,
                "base_chunk_sha256": _chunk_sha(base),
                "adapter_chunk_sha256": adapter_hash,
                "adapter_reproduced_t20_33_exactly": True,
                "outputs_unchanged": is_unchanged,
                "base_mean_absolute_error_rad": float(np.mean(base_error)),
                "adapter_mean_absolute_error_rad": float(np.mean(adapter_error)),
                "mean_error_improvement_rad": float(np.mean(base_error) - np.mean(adapter_error)),
                "base_maximum_absolute_error_rad": float(np.max(base_error)),
                "adapter_maximum_absolute_error_rad": float(np.max(adapter_error)),
                "per_joint_base_mean_absolute_error_rad": np.mean(base_error, axis=0).astype(float).tolist(),
                "per_joint_adapter_mean_absolute_error_rad": np.mean(adapter_error, axis=0).astype(float).tolist(),
                "adapter_movement_l2_rad": float(np.linalg.norm(movement)),
                "target_direction_l2_rad": float(np.linalg.norm(direction)),
                "movement_target_cosine_alignment": cosine,
            }
        )
    tensors = evidence.get("adapter_tensors")
    if not isinstance(tensors, list) or not tensors:
        raise ValueError("T20.34 adapter tensor evidence is missing")
    total_values = total_nonzero = 0
    for row in tensors:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise ValueError("T20.34 adapter tensor evidence is malformed")
        count = row.get("value_count")
        nonzero = row.get("nonzero_count")
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ValueError("T20.34 adapter tensor count is invalid")
        if isinstance(nonzero, bool) or not isinstance(nonzero, int) or not 0 <= nonzero <= count:
            raise ValueError("T20.34 adapter nonzero count is invalid")
        _finite(row.get("l2_norm"), "tensor l2 norm")
        _finite(row.get("maximum_absolute_value"), "tensor maximum")
        total_values += count
        total_nonzero += nonzero
    base_objective = _finite(evidence.get("base_objective_mean"), "base objective")
    adapter_objective = _finite(evidence.get("adapter_objective_mean"), "adapter objective")
    prior_base = float(prior_run["baseline_objective_mean"])
    prior_adapter = float(prior_run["final_objective_mean"])
    if abs(base_objective - prior_base) > 1e-6 or abs(adapter_objective - prior_adapter) > 1e-6:
        raise ValueError("T20.34 objective replay drifted from T20.33")
    active = total_nonzero > 0 and not all(unchanged)
    consistent_improvement = all(
        row["mean_error_improvement_rad"] > 0
        and row["movement_target_cosine_alignment"] > 0
        for row in rows
    )
    if not active:
        selected = "adapter_checkpoint_plumbing"
    elif not consistent_improvement:
        selected = "objective_to_inference_alignment"
    else:
        selected = "insufficient_gate_b_optimization_or_capacity"
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.34",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "t20_33_run_identity_sha256": prior_run["identity_sha256"],
            "evidence": evidence,
            "adapter_tensor_value_count": total_values,
            "adapter_tensor_nonzero_count": total_nonzero,
            "adapter_active": active,
            "base_objective_mean": base_objective,
            "adapter_objective_mean": adapter_objective,
            "objective_improvement": base_objective - adapter_objective,
            "seed_results": rows,
            "every_seed_decoded_error_improved_and_aligned": consistent_improvement,
            "selected_next_hypothesis": selected,
            "optimizer_training": False,
            "closed_loop_rollout": False,
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


def _chunks(value: Any, label: str) -> dict[int, np.ndarray]:
    if not isinstance(value, list) or len(value) != len(INFERENCE_SEEDS):
        raise ValueError(f"T20.34 {label} chunk coverage drifted")
    if [row.get("inference_seed") for row in value] != list(INFERENCE_SEEDS):
        raise ValueError(f"T20.34 {label} seed order drifted")
    return {row["inference_seed"]: _matrix(row.get("actions"), f"{label} actions") for row in value}


def _matrix(value: Any, label: str) -> np.ndarray:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != (ACTION_HORIZON, 6) or not np.isfinite(matrix).all():
        raise ValueError(f"T20.34 {label} must be a finite 50x6 matrix")
    return matrix


def _chunk_sha(matrix: np.ndarray) -> str:
    return hashlib.sha256(canonical_json_bytes(matrix.astype(float).tolist())).hexdigest()


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"T20.34 {label} must be finite")
    return float(value)
