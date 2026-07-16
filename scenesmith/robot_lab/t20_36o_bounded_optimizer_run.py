"""Deterministic probe and result contracts for T20.36o bounded correction."""

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
from scenesmith.robot_lab.t20_36o_baseline_capture import score_action_tensor
from scenesmith.robot_lab.t20_36o_bounded_optimizer_authority import (
    TRACKED_ATTEMPT_PATH,
    verify_attempt_marker,
)


PROBE_TENSOR_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_probe_tensors.json"
)
PROBE_SCHEMA_VERSION = "scenesmith.t20_36o_optimizer_probe_tensors.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36o_optimizer_result.v1"
FAILURE_RESULT_SCHEMA_VERSION = "scenesmith.t20_36o_optimizer_failure_result.v1"
CHUNK_START_FRAMES = (0, 50, 100, 150, 200)
EXECUTED_LENGTHS = (50, 50, 50, 50, 44)
INFERENCE_SEEDS = (20260721, 20260722, 20260723, 20260724, 20260725)
REPEATS = 2
TARGET_HORIZON = 50
ACTION_DIMENSIONS = 6


def build_probe_artifact(
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    optimizer_spec: dict[str, Any],
    bridge_spec: dict[str, Any],
    source_gate_baseline_objective_mean: float,
    probes: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_attempt_marker(attempt, permit=permit)
    verify_signed_payload(optimizer_spec, label="T20.36o probe optimizer spec")
    verify_signed_payload(bridge_spec, label="T20.36o probe bridge spec")
    _verify_lineage(
        attempt=attempt,
        permit=permit,
        optimizer_spec=optimizer_spec,
        bridge_spec=bridge_spec,
    )
    baseline = _finite_positive(
        source_gate_baseline_objective_mean,
        label="source gate baseline objective",
    )
    allowed_updates = permit["probe_update_counts"]
    if (
        allowed_updates != [500, 1000, 1500, 2000, 2500]
        or permit.get("probe_starts") != list(CHUNK_START_FRAMES)
        or permit.get("probe_inference_seeds") != list(INFERENCE_SEEDS)
        or permit.get("probe_repeats") != REPEATS
    ):
        raise ValueError("T20.36o optimizer probe permit drifted")
    observed_updates = [row.get("update_count") for row in probes]
    if (
        not probes
        or observed_updates != allowed_updates[: len(observed_updates)]
        or len(probes) > len(allowed_updates)
    ):
        raise ValueError("T20.36o optimizer probe schedule drifted")
    source_windows = bridge_spec.get("source_windows")
    if (
        not isinstance(source_windows, list)
        or [row.get("start_frame") for row in source_windows]
        != list(CHUNK_START_FRAMES)
        or [row.get("executed_length") for row in source_windows]
        != list(EXECUTED_LENGTHS)
    ):
        raise ValueError("T20.36o probe bridge window drifted")
    windows = {row["start_frame"]: row for row in source_windows}
    thresholds = bridge_spec["acceptance"]["phase_joint_maximum_error_rad"]
    objective_threshold = bridge_spec["acceptance"][
        "maximum_source_batch_objective_ratio"
    ]
    expected_keys = _probe_keys()
    normalized_probes = []
    first_passing_update = None
    for probe_index, probe in enumerate(probes):
        update_count = observed_updates[probe_index]
        source_mean = _finite_nonnegative(
            probe.get("source_objective_mean"),
            label="probe source objective mean",
        )
        source_ratio = source_mean / baseline
        supplied_ratio = _finite_nonnegative(
            probe.get("source_objective_ratio"),
            label="probe source objective ratio",
        )
        if abs(source_ratio - supplied_ratio) > 1e-12:
            raise ValueError("T20.36o probe source objective ratio drifted")
        rows = probe.get("rows")
        if not isinstance(rows, list) or len(rows) != len(expected_keys):
            raise ValueError("T20.36o probe tensor coverage drifted")
        normalized_rows = []
        pair_values: dict[tuple[int, int], list[list[float]]] = {}
        score_rows = []
        for expected_key, row in zip(expected_keys, rows, strict=True):
            if any(row.get(key) != value for key, value in expected_key.items()):
                raise ValueError("T20.36o probe tensor order drifted")
            tensor = _matrix(row.get("decoded_action_chunk"))
            digest = hashlib.sha256(canonical_json_bytes(tensor)).hexdigest()
            pair_key = (expected_key["start_index"], expected_key["seed_index"])
            if expected_key["repeat_index"] == 0:
                pair_values[pair_key] = tensor
                window = windows[expected_key["start_frame"]]
                score = score_action_tensor(
                    tensor=tensor,
                    target=window["padded_target_action_mujoco_rad"],
                    executed_mask=window["executed_mask"],
                    thresholds=thresholds,
                )
                score_rows.append(
                    {
                        "start_frame": expected_key["start_frame"],
                        "executed_length": expected_key["executed_length"],
                        "inference_seed": expected_key["inference_seed"],
                        "action_chunk_sha256": digest,
                        **score,
                    }
                )
            elif pair_values.get(pair_key) != tensor:
                raise ValueError("T20.36o probe repeat drifted")
            normalized_rows.append(
                {
                    **expected_key,
                    "decoded_action_chunk_sha256": digest,
                    "decoded_action_chunk": tensor,
                }
            )
        action_passed = all(row["passed"] for row in score_rows)
        objective_passed = source_ratio <= objective_threshold
        passed = action_passed and objective_passed
        if passed and first_passing_update is None:
            first_passing_update = update_count
        elif first_passing_update is not None:
            raise ValueError("T20.36o probes continued after first pass")
        normalized_probes.append(
            {
                "probe_index": probe_index,
                "update_count": update_count,
                "source_objective_mean": source_mean,
                "source_objective_ratio": source_ratio,
                "source_objective_ratio_threshold": objective_threshold,
                "source_objective_passed": objective_passed,
                "action_gate_passed": action_passed,
                "passed": passed,
                "score_rows": score_rows,
                "rows": normalized_rows,
            }
        )
    if first_passing_update is None and observed_updates[-1] != allowed_updates[-1]:
        raise ValueError("T20.36o negative probe sequence stopped before ceiling")
    return sign_payload(
        {
            "schema_version": PROBE_SCHEMA_VERSION,
            "task_id": "T20.36o",
            "attempt_identity_sha256": attempt["identity_sha256"],
            "training_permit_identity_sha256": permit["identity_sha256"],
            "optimizer_spec_identity_sha256": optimizer_spec["identity_sha256"],
            "bridge_spec_identity_sha256": bridge_spec["identity_sha256"],
            "source_checkpoint_identity_sha256": permit[
                "source_checkpoint_identity_sha256"
            ],
            "source_gate_baseline_objective_mean": baseline,
            "probe_count": len(normalized_probes),
            "decoded_tensor_count": len(normalized_probes) * len(expected_keys),
            "first_passing_update": first_passing_update,
            "probes": normalized_probes,
            "all_repeats_bit_identical": True,
            "optimizer_training": True,
            "threshold_changed": False,
            "retry_authorized": False,
            "gate_c_authorized": False,
            "gate_c_executed": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_probe_artifact(
    payload: dict[str, Any],
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    optimizer_spec: dict[str, Any],
    bridge_spec: dict[str, Any],
    source_gate_baseline_objective_mean: float,
) -> None:
    verify_signed_payload(payload, label="T20.36o optimizer probe artifact")
    expected = build_probe_artifact(
        attempt=attempt,
        permit=permit,
        optimizer_spec=optimizer_spec,
        bridge_spec=bridge_spec,
        source_gate_baseline_objective_mean=source_gate_baseline_objective_mean,
        probes=payload.get("probes"),
    )
    if payload != expected:
        raise ValueError("T20.36o optimizer probe artifact drifted")


def build_result(
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    optimizer_spec: dict[str, Any],
    probe_artifact: dict[str, Any],
    training_metrics: dict[str, Any],
    checkpoint_tree: list[dict[str, Any]],
    source_checkpoint_tree_unchanged: bool,
) -> dict[str, Any]:
    verify_attempt_marker(attempt, permit=permit)
    verify_signed_payload(optimizer_spec, label="T20.36o result optimizer spec")
    verify_signed_payload(probe_artifact, label="T20.36o result probes")
    if (
        attempt.get("training_permit_identity_sha256")
        != permit.get("identity_sha256")
        or permit.get("optimizer_spec_identity_sha256")
        != optimizer_spec.get("identity_sha256")
        or probe_artifact.get("attempt_identity_sha256")
        != attempt.get("identity_sha256")
        or probe_artifact.get("training_permit_identity_sha256")
        != permit.get("identity_sha256")
        or probe_artifact.get("optimizer_spec_identity_sha256")
        != optimizer_spec.get("identity_sha256")
        or probe_artifact.get("source_checkpoint_identity_sha256")
        != permit.get("source_checkpoint_identity_sha256")
    ):
        raise ValueError("T20.36o optimizer result lineage drifted")
    update_count = training_metrics.get("optimizer_update_count")
    if isinstance(update_count, bool) or not isinstance(update_count, int):
        raise ValueError("T20.36o optimizer update count drifted")
    first_pass = probe_artifact["first_passing_update"]
    expected_update = first_pass if first_pass is not None else 2500
    metric_names = (
        "per_update_objective",
        "per_update_correction_objective",
        "per_update_standard_replay_objective",
        "gradient_norms_before_clip",
    )
    if (
        update_count != expected_update
        or any(
            not isinstance(training_metrics.get(name), list)
            or len(training_metrics[name]) != update_count
            or any(not _is_finite_number(value) for value in training_metrics[name])
            for name in metric_names
        )
        or source_checkpoint_tree_unchanged is not True
        or not _valid_file_tree(checkpoint_tree)
    ):
        raise ValueError("T20.36o optimizer result evidence drifted")
    checkpoint_identity = hashlib.sha256(
        canonical_json_bytes(checkpoint_tree)
    ).hexdigest()
    passed = first_pass is not None
    probe_summary = [
        {
            "update_count": row["update_count"],
            "source_objective_ratio": row["source_objective_ratio"],
            "source_objective_passed": row["source_objective_passed"],
            "action_gate_passed": row["action_gate_passed"],
            "passed": row["passed"],
            "total_violation_count": sum(
                score["violation_count"] for score in row["score_rows"]
            ),
            "passing_probe_count": sum(
                score["passed"] for score in row["score_rows"]
            ),
        }
        for row in probe_artifact["probes"]
    ]
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.36o",
            "attempt_identity_sha256": attempt["identity_sha256"],
            "tracked_attempt_path": TRACKED_ATTEMPT_PATH.as_posix(),
            "training_permit_identity_sha256": permit["identity_sha256"],
            "optimizer_spec_identity_sha256": optimizer_spec["identity_sha256"],
            "probe_artifact_identity_sha256": probe_artifact["identity_sha256"],
            "tracked_probe_artifact_path": PROBE_TENSOR_PATH.as_posix(),
            "source_checkpoint_identity_sha256": permit[
                "source_checkpoint_identity_sha256"
            ],
            "source_checkpoint_tree_unchanged": True,
            "optimizer_update_count": update_count,
            "first_passing_update": first_pass,
            "probe_summary": probe_summary,
            "bridge_gate_passed": passed,
            "checkpoint_tree": checkpoint_tree,
            "checkpoint_identity_sha256": checkpoint_identity,
            **{name: training_metrics[name] for name in metric_names},
            "decision": (
                "route_separate_gate_c_episode_0_authority_request"
                if passed
                else "close_x_bridge_after_bounded_negative_no_retry"
            ),
            "optimizer_created": True,
            "optimizer_training": True,
            "checkpoint_written": True,
            "retry_authorized": False,
            "threshold_changed": False,
            "gate_c_request_eligible": passed,
            "gate_c_authorized": False,
            "gate_c_executed": False,
            "policy_track_selected": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_result(
    payload: dict[str, Any],
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    optimizer_spec: dict[str, Any],
    probe_artifact: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36o optimizer result")
    expected = build_result(
        attempt=attempt,
        permit=permit,
        optimizer_spec=optimizer_spec,
        probe_artifact=probe_artifact,
        training_metrics={
            key: payload[key]
            for key in (
                "optimizer_update_count",
                "per_update_objective",
                "per_update_correction_objective",
                "per_update_standard_replay_objective",
                "gradient_norms_before_clip",
            )
        },
        checkpoint_tree=payload.get("checkpoint_tree"),
        source_checkpoint_tree_unchanged=payload.get(
            "source_checkpoint_tree_unchanged"
        ),
    )
    if payload != expected:
        raise ValueError("T20.36o optimizer result drifted")


def build_failure_result(
    *,
    permit: dict[str, Any],
    attempt: dict[str, Any],
    failure_stage: str,
    error_type: str,
    error_message: str,
    checkpoint_tensor_read: bool,
    model_constructed: bool,
    model_loaded: bool,
    optimizer_created: bool,
    optimizer_update_count: int,
) -> dict[str, Any]:
    verify_attempt_marker(attempt, permit=permit)
    if not all(
        isinstance(value, bool)
        for value in (
            checkpoint_tensor_read,
            model_constructed,
            model_loaded,
            optimizer_created,
        )
    ) or not all(
        isinstance(value, str) and value.strip()
        for value in (failure_stage, error_type, error_message)
    ):
        raise ValueError("T20.36o optimizer failure evidence drifted")
    if (
        isinstance(optimizer_update_count, bool)
        or not isinstance(optimizer_update_count, int)
        or not 0 <= optimizer_update_count <= 2500
    ):
        raise ValueError("T20.36o optimizer failure update count drifted")
    return sign_payload(
        {
            "schema_version": FAILURE_RESULT_SCHEMA_VERSION,
            "task_id": "T20.36o",
            "decision": "bounded_optimizer_runtime_failure_no_retry",
            "training_permit_identity_sha256": permit["identity_sha256"],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "failure_stage": failure_stage,
            "error_type": error_type,
            "error_message": error_message,
            "checkpoint_tensor_read": checkpoint_tensor_read,
            "model_constructed": model_constructed,
            "model_loaded": model_loaded,
            "optimizer_created": optimizer_created,
            "optimizer_update_count": optimizer_update_count,
            "retry_authorized": False,
            "gate_c_authorized": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def _probe_keys() -> list[dict[str, int]]:
    return [
        {
            "start_index": start_index,
            "start_frame": start_frame,
            "executed_length": EXECUTED_LENGTHS[start_index],
            "seed_index": seed_index,
            "inference_seed": inference_seed,
            "repeat_index": repeat_index,
        }
        for start_index, start_frame in enumerate(CHUNK_START_FRAMES)
        for seed_index, inference_seed in enumerate(INFERENCE_SEEDS)
        for repeat_index in range(REPEATS)
    ]


def _matrix(value: Any) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != TARGET_HORIZON:
        raise ValueError("T20.36o probe tensor must be 50x6")
    output = []
    for row in value:
        if not isinstance(row, list) or len(row) != ACTION_DIMENSIONS:
            raise ValueError("T20.36o probe tensor must be 50x6")
        normalized = []
        for item in row:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError("T20.36o probe tensor must be finite")
            number = float(item)
            if not math.isfinite(number):
                raise ValueError("T20.36o probe tensor must be finite")
            normalized.append(number)
        output.append(normalized)
    return output


def _finite_nonnegative(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.36o {label} must be finite")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"T20.36o {label} must be finite and nonnegative")
    return number


def _finite_positive(value: Any, *, label: str) -> float:
    number = _finite_nonnegative(value, label=label)
    if number <= 0.0:
        raise ValueError(f"T20.36o {label} must be positive")
    return number


def _verify_lineage(
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    optimizer_spec: dict[str, Any],
    bridge_spec: dict[str, Any],
) -> None:
    if (
        attempt.get("optimizer_spec_identity_sha256")
        != optimizer_spec.get("identity_sha256")
        or permit.get("optimizer_spec_identity_sha256")
        != optimizer_spec.get("identity_sha256")
        or optimizer_spec.get("bridge_spec_identity_sha256")
        != bridge_spec.get("identity_sha256")
        or permit.get("source_checkpoint_identity_sha256")
        != optimizer_spec.get("source_checkpoint_identity_sha256")
        or bridge_spec.get("source_checkpoint_identity_sha256")
        != permit.get("source_checkpoint_identity_sha256")
    ):
        raise ValueError("T20.36o optimizer probe lineage drifted")


def _is_finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _valid_file_tree(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    paths = []
    for row in value:
        if not isinstance(row, dict):
            return False
        path = row.get("path")
        digest = row.get("sha256")
        size = row.get("size_bytes")
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or ".." in Path(path).parts
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
        ):
            return False
        paths.append(path)
    return len(paths) == len(set(paths)) and paths == sorted(paths)
