"""Fail-closed contracts for T20.36m SmolVLA tensor reproduction."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36j_exact_smolvla_gate_b import (
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
    INSTALLED_CLOSURE_PATH,
    PROCESSOR_SMOKE_PATH,
)
from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (
    CORRECTED_PREFLIGHT_PATH,
)
from scenesmith.robot_lab.t20_36l_frozen_consequence_gate import (
    JOINT_NAMES,
    RESULT_PATH as FROZEN_SCORE_PATH,
    SPEC_PATH as FROZEN_GATE_PATH,
)
from scenesmith.robot_lab.t20_36m_tensor_reproduction_authority import (
    EXPECTED_CHECKPOINT_IDENTITY,
    EXPECTED_FROZEN_GATE_IDENTITY,
    EXPECTED_FROZEN_SCORE_IDENTITY,
    EXPECTED_SMOLVLA_RESULT_IDENTITY,
    EXPECTED_SMOLVLA_RUN_IDENTITY,
    REPO_ROOT,
    load_verified_sources as load_authority_sources,
)


TASK_ID = "T20.36m"
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36m_tensor_reproduction_preflight.json"
)
INFERENCE_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36m_tensor_reproduction_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_36m_tensor_reproduction_result.json"
)
RUN_ROOT = Path("outputs/robot_lab/t20_36m_tensor_reproduction_run_001")
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
TENSOR_PATH = RUN_ROOT / "decoded_action_tensors.json"
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
FAILURE_PATH = RUN_ROOT / "failure.json"
FAILURE_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36m_tensor_reproduction_failure_result.json"
)
RUNTIME_SCHEMA_VERSION = "scenesmith.t20_36m_tensor_reproduction_preflight.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_36m_tensor_reproduction_permit.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_36m_tensor_reproduction_attempt.v1"
TENSOR_SCHEMA_VERSION = "scenesmith.t20_36m_decoded_action_tensors.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_36m_tensor_reproduction_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36m_tensor_reproduction_result.v1"
FAILURE_SCHEMA_VERSION = "scenesmith.t20_36m_tensor_reproduction_failure.v1"
FAILURE_RESULT_SCHEMA_VERSION = (
    "scenesmith.t20_36m_tensor_reproduction_failure_result.v1"
)
INFERENCE_SEEDS = (20260811, 20260812, 20260813, 20260814, 20260815)
EXPECTED_ACTION_HASHES = (
    "4e347f1aca45c75302b0cc4be6e6134ee9c4fefddde752e91da280ae7e9bac61",
    "b0bfdec2be39340042a99d6ff5f8ce25440f121518c75a29dc5117ffee7455a4",
    "b8e1154dc233ae49d56877caeb95bc51d5f1fb2ed77e40f2120d66fab85232ee",
    "b578627eb74d8e86277118ef141d869da885efc287140576cdb25a700b984eb6",
    "64e925f9a8f4c8e43a703bfab2bfaba0355202a0849c8b9256f57c55b1f29b4d",
)
MINIMUM_FREE_DISK_BYTES = 2 * 1024 * 1024 * 1024
TARGET_HORIZON = 50
REACH_STOP_EXCLUSIVE = 32


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    authority_sources = load_authority_sources(repo_root=root)
    closure = load_strict_json(root / INSTALLED_CLOSURE_PATH)
    smoke = load_strict_json(root / PROCESSOR_SMOKE_PATH)
    corrected_preflight = load_strict_json(root / CORRECTED_PREFLIGHT_PATH)
    for label, payload in (
        ("installed closure", closure),
        ("processor smoke", smoke),
        ("corrected preflight", corrected_preflight),
    ):
        verify_signed_payload(payload, label=f"T20.36m {label}")
    run = authority_sources["smolvla_run"]
    frozen_gate = authority_sources["frozen_gate"]
    frozen_score = authority_sources["frozen_score"]
    if (
        corrected_preflight.get("installed_closure", {}).get("identity_sha256")
        != closure["identity_sha256"]
        or corrected_preflight.get("processor_smoke", {}).get("identity_sha256")
        != smoke["identity_sha256"]
        or corrected_preflight.get("lerobot_stack_identity_sha256") is None
        or corrected_preflight.get("batch_evidence_identity_sha256") is None
    ):
        raise ValueError("T20.36m corrected preflight linkage drifted")
    final = run.get("evaluations", [])[-1]
    hashes = tuple(row.get("first_action_chunk_sha256") for row in final["inference_rows"])
    if hashes != EXPECTED_ACTION_HASHES:
        raise ValueError("T20.36m source action hashes drifted")
    return {
        "checkpoint_identity_sha256": EXPECTED_CHECKPOINT_IDENTITY,
        "source_run_identity_sha256": EXPECTED_SMOLVLA_RUN_IDENTITY,
        "source_result_identity_sha256": EXPECTED_SMOLVLA_RESULT_IDENTITY,
        "frozen_gate_identity_sha256": EXPECTED_FROZEN_GATE_IDENTITY,
        "frozen_score_identity_sha256": EXPECTED_FROZEN_SCORE_IDENTITY,
        "checkpoint_tree": run["checkpoint_tree"],
        "installed_closure_identity_sha256": closure["identity_sha256"],
        "processor_smoke_identity_sha256": smoke["identity_sha256"],
        "lerobot_stack_identity_sha256": corrected_preflight[
            "lerobot_stack_identity_sha256"
        ],
        "batch_evidence_identity_sha256": corrected_preflight[
            "batch_evidence_identity_sha256"
        ],
        "source_run": run,
        "source_result": authority_sources["smolvla_result"],
        "smolvla_spec": authority_sources["smolvla_spec"],
        "frozen_gate": frozen_gate,
        "frozen_score": frozen_score,
        "installed_closure": closure,
        "processor_smoke": smoke,
        "corrected_preflight": corrected_preflight,
    }


def build_runtime_preflight(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    python_major_minor: list[int],
    mps_available: bool,
    checkpoint_tree: list[dict[str, Any]],
    free_disk_bytes: int,
    source_commit: str,
    remote_source_commit: str,
    attempt_exists: bool,
    result_exists: bool,
) -> dict[str, Any]:
    _sha(authority_identity, "authority identity")
    for name in (
        "checkpoint_identity_sha256",
        "source_run_identity_sha256",
        "source_result_identity_sha256",
        "frozen_gate_identity_sha256",
        "frozen_score_identity_sha256",
        "installed_closure_identity_sha256",
        "processor_smoke_identity_sha256",
        "lerobot_stack_identity_sha256",
        "batch_evidence_identity_sha256",
    ):
        _sha(sources.get(name), name)
    _commit(source_commit, "source commit")
    _commit(remote_source_commit, "remote source commit")
    if (
        python_major_minor != [3, 12]
        or mps_available is not True
        or checkpoint_tree != sources.get("checkpoint_tree")
        or isinstance(free_disk_bytes, bool)
        or not isinstance(free_disk_bytes, int)
        or free_disk_bytes < MINIMUM_FREE_DISK_BYTES
        or source_commit != remote_source_commit
        or attempt_exists is not False
        or result_exists is not False
    ):
        raise ValueError("T20.36m runtime preflight failed closed")
    return sign_payload(
        {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "authority_decision_identity_sha256": authority_identity,
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
            "frozen_score_identity_sha256": sources[
                "frozen_score_identity_sha256"
            ],
            "installed_closure_identity_sha256": sources[
                "installed_closure_identity_sha256"
            ],
            "processor_smoke_identity_sha256": sources[
                "processor_smoke_identity_sha256"
            ],
            "lerobot_stack_identity_sha256": sources[
                "lerobot_stack_identity_sha256"
            ],
            "batch_evidence_identity_sha256": sources[
                "batch_evidence_identity_sha256"
            ],
            "python_major_minor": python_major_minor,
            "mps_available": True,
            "checkpoint_tree": checkpoint_tree,
            "checkpoint_bytes_hashed": True,
            "checkpoint_tensor_deserialized": False,
            "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
            "free_disk_bytes": free_disk_bytes,
            "source_commit": source_commit,
            "remote_source_commit": remote_source_commit,
            "remote_source_commit_matches": True,
            "attempt_exists": False,
            "result_exists": False,
            "network_accessed": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "new_seed": False,
            "extra_repeat": False,
            "threshold_changed": False,
            "gate_c_authorized": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
) -> None:
    verify_signed_payload(payload, label="T20.36m runtime preflight")
    expected = build_runtime_preflight(
        sources=sources,
        authority_identity=authority_identity,
        python_major_minor=payload.get("python_major_minor"),
        mps_available=payload.get("mps_available"),
        checkpoint_tree=payload.get("checkpoint_tree"),
        free_disk_bytes=payload.get("free_disk_bytes"),
        source_commit=payload.get("source_commit"),
        remote_source_commit=payload.get("remote_source_commit"),
        attempt_exists=payload.get("attempt_exists"),
        result_exists=payload.get("result_exists"),
    )
    if payload != expected:
        raise ValueError("T20.36m runtime preflight drifted")


def build_inference_permit(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> dict[str, Any]:
    verify_runtime_preflight(
        runtime_preflight,
        sources=sources,
        authority_identity=authority_identity,
    )
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
            "frozen_score_identity_sha256": sources[
                "frozen_score_identity_sha256"
            ],
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime_preflight[
                "identity_sha256"
            ],
            "required_source_commit": runtime_preflight["source_commit"],
            "authorized_attempt_count": 1,
            "authorized_actions": [
                "simulation_model_construction",
                "simulation_model_load",
                "simulation_model_inference",
                "persist_reproduced_action_tensors",
                "score_frozen_gate_b",
            ],
            "inference_seeds": list(INFERENCE_SEEDS),
            "repeats_per_seed": 2,
            "expected_action_chunk_sha256s": list(EXPECTED_ACTION_HASHES),
            "attempt_marker_path": str(ATTEMPT_PATH),
            "tensor_artifact_path": str(TENSOR_PATH),
            "marker_must_precede_checkpoint_tensor_read": True,
            "existing_hashes_must_match_before_scoring": True,
            "local_execution_eligible_after_remote_preservation": True,
            "optimizer_created": False,
            "optimizer_training": False,
            "training_retry": False,
            "new_seed": False,
            "extra_repeat": False,
            "threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "policy_track_selected": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_inference_permit(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36m inference permit")
    expected = build_inference_permit(
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.36m inference permit drifted")


def build_attempt_marker(
    *, permit: dict[str, Any], authority_identity: str, source_commit: str
) -> dict[str, Any]:
    verify_signed_payload(permit, label="T20.36m inference permit")
    _sha(authority_identity, "authority identity")
    _commit(source_commit, "attempt source commit")
    if (
        permit.get("authority_decision_identity_sha256") != authority_identity
        or permit.get("authorized_attempt_count") != 1
        or permit.get("inference_seeds") != list(INFERENCE_SEEDS)
        or permit.get("repeats_per_seed") != 2
        or permit.get("expected_action_chunk_sha256s")
        != list(EXPECTED_ACTION_HASHES)
        or permit.get("marker_must_precede_checkpoint_tensor_read") is not True
    ):
        raise ValueError("T20.36m attempt permit drifted")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "source_checkpoint_identity_sha256": permit[
                "source_checkpoint_identity_sha256"
            ],
            "source_run_identity_sha256": permit["source_run_identity_sha256"],
            "frozen_gate_identity_sha256": permit["frozen_gate_identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "inference_permit_identity_sha256": permit["identity_sha256"],
            "source_commit": source_commit,
            "attempt_number": 1,
            "created_before_checkpoint_tensor_read": True,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "tensor_artifact_written": False,
        }
    )


def verify_attempt_marker(
    payload: dict[str, Any], *, permit: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.36m attempt marker")
    expected = build_attempt_marker(
        permit=permit,
        authority_identity=authority_identity,
        source_commit=payload.get("source_commit"),
    )
    if payload != expected:
        raise ValueError("T20.36m attempt marker drifted")


def score_action_tensor(
    *,
    tensor: list[list[float]],
    target: list[list[float]],
    thresholds: dict[str, dict[str, float]],
) -> dict[str, Any]:
    predicted = _matrix(tensor, label="decoded tensor")
    expected = _matrix(target, label="target tensor")
    if set(thresholds) != {"reach", "grasp"} or any(
        set(thresholds[group]) != set(JOINT_NAMES) for group in thresholds
    ):
        raise ValueError("T20.36m frozen threshold matrix drifted")
    violations = []
    errors = []
    normalized = []
    for timestep, (predicted_row, expected_row) in enumerate(
        zip(predicted, expected, strict=True)
    ):
        group = "reach" if timestep < REACH_STOP_EXCLUSIVE else "grasp"
        for index, joint in enumerate(JOINT_NAMES):
            threshold = thresholds[group][joint]
            if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
                raise ValueError("T20.36m threshold must be finite and positive")
            threshold = float(threshold)
            if not math.isfinite(threshold) or threshold <= 0:
                raise ValueError("T20.36m threshold must be finite and positive")
            error = abs(predicted_row[index] - expected_row[index])
            errors.append(error)
            normalized.append(error / threshold)
            if error > threshold:
                violations.append(
                    {
                        "timestep": timestep,
                        "phase_group": group,
                        "joint_name": joint,
                        "predicted_action_rad": predicted_row[index],
                        "target_action_rad": expected_row[index],
                        "absolute_error_rad": error,
                        "frozen_threshold_rad": threshold,
                        "excess_rad": error - threshold,
                    }
                )
    return {
        "passed": not violations,
        "maximum_absolute_error_rad": max(errors),
        "mean_absolute_error_rad": sum(errors) / len(errors),
        "maximum_threshold_ratio": max(normalized),
        "violation_count": len(violations),
        "violations": violations,
    }


def build_tensor_artifact(
    *,
    attempt: dict[str, Any],
    rows: list[dict[str, Any]],
    target: list[list[float]],
) -> dict[str, Any]:
    verify_signed_payload(attempt, label="T20.36m attempt marker")
    if len(rows) != len(INFERENCE_SEEDS):
        raise ValueError("T20.36m tensor row count drifted")
    normalized = []
    for index, (seed, expected_hash, row) in enumerate(
        zip(INFERENCE_SEEDS, EXPECTED_ACTION_HASHES, rows, strict=True)
    ):
        first = _matrix(row.get("first"), label="first decoded tensor")
        second = _matrix(row.get("second"), label="second decoded tensor")
        first_hash = hashlib.sha256(canonical_json_bytes(first)).hexdigest()
        second_hash = hashlib.sha256(canonical_json_bytes(second)).hexdigest()
        if (
            row.get("seed_index") != index
            or row.get("inference_seed") != seed
            or first_hash != expected_hash
            or second_hash != expected_hash
            or first != second
        ):
            raise ValueError("T20.36m reproduced tensor hash or repeat drifted")
        normalized.append(
            {
                "seed_index": index,
                "inference_seed": seed,
                "first_action_chunk_sha256": first_hash,
                "second_action_chunk_sha256": second_hash,
                "repeat_maximum_absolute_difference_rad": 0.0,
                "first": first,
                "second": second,
            }
        )
    return sign_payload(
        {
            "schema_version": TENSOR_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "attempt_identity_sha256": attempt["identity_sha256"],
            "source_checkpoint_identity_sha256": attempt[
                "source_checkpoint_identity_sha256"
            ],
            "target_action_sha256": hashlib.sha256(
                canonical_json_bytes(_matrix(target, label="target tensor"))
            ).hexdigest(),
            "shape_per_tensor": [TARGET_HORIZON, len(JOINT_NAMES)],
            "tensor_count": 10,
            "rows": normalized,
            "all_expected_hashes_reproduced": True,
            "all_repeats_bit_identical": True,
            "optimizer_created": False,
            "optimizer_training": False,
            "new_seed": False,
            "extra_repeat": False,
            "threshold_changed": False,
            "gate_c_authorized": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def build_run_summary(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    permit: dict[str, Any],
    attempt: dict[str, Any],
    tensor_artifact: dict[str, Any],
    target: list[list[float]],
) -> dict[str, Any]:
    verify_signed_payload(tensor_artifact, label="T20.36m tensor artifact")
    thresholds = sources["frozen_gate"]["amended_gate_b_conjunction"][
        "phase_joint_maximum_error_rad"
    ]
    score_rows = []
    for row in tensor_artifact["rows"]:
        score = score_action_tensor(
            tensor=row["first"], target=target, thresholds=thresholds
        )
        score_rows.append(
            {
                "seed_index": row["seed_index"],
                "inference_seed": row["inference_seed"],
                "action_chunk_sha256": row["first_action_chunk_sha256"],
                **score,
            }
        )
    amended_pass = all(row["passed"] for row in score_rows)
    retained_ratio = sources["source_run"][
        "final_to_baseline_supervised_objective_ratio"
    ]
    objective_threshold = sources["frozen_gate"]["amended_gate_b_conjunction"][
        "maximum_objective_ratio"
    ]
    objective_pass = retained_ratio <= objective_threshold
    amended_pass = amended_pass and objective_pass
    return sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "authority_decision_identity_sha256": authority_identity,
            "inference_permit_identity_sha256": permit["identity_sha256"],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "tensor_artifact_identity_sha256": tensor_artifact["identity_sha256"],
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
            "retained_objective_ratio": retained_ratio,
            "retained_objective_ratio_threshold": objective_threshold,
            "retained_objective_ratio_passed": objective_pass,
            "all_expected_hashes_reproduced": True,
            "all_repeats_bit_identical": True,
            "score_rows": score_rows,
            "amended_gate_b_passed": amended_pass,
            "decision": (
                "smolvla_amended_gate_b_pass"
                if amended_pass
                else "smolvla_amended_gate_b_fail"
            ),
            "checkpoint_tensor_read": True,
            "model_constructed": True,
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": False,
            "optimizer_training": False,
            "new_seed": False,
            "extra_repeat": False,
            "threshold_changed": False,
            "gate_c_authorized": False,
            "gate_c_executed": False,
            "policy_track_selected": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def build_result(
    *, sources: dict[str, Any], run: dict[str, Any]
) -> dict[str, Any]:
    verify_signed_payload(run, label="T20.36m run summary")
    passed = run.get("amended_gate_b_passed") is True
    score_summary = [
        {
            "seed_index": row["seed_index"],
            "inference_seed": row["inference_seed"],
            "action_chunk_sha256": row["action_chunk_sha256"],
            "passed": row["passed"],
            "maximum_absolute_error_rad": row["maximum_absolute_error_rad"],
            "maximum_threshold_ratio": row["maximum_threshold_ratio"],
            "violation_count": row["violation_count"],
        }
        for row in run["score_rows"]
    ]
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "run_identity_sha256": run["identity_sha256"],
            "tensor_artifact_identity_sha256": run[
                "tensor_artifact_identity_sha256"
            ],
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
            "all_expected_hashes_reproduced": run[
                "all_expected_hashes_reproduced"
            ],
            "all_repeats_bit_identical": run["all_repeats_bit_identical"],
            "amended_gate_b_passed": passed,
            "score_summary": score_summary,
            "total_violation_count": sum(
                row["violation_count"] for row in score_summary
            ),
            "decision": (
                "route_separate_gate_c_authority_request"
                if passed
                else "close_learned_policy_gate_b_branch"
            ),
            "gate_c_route_open": passed,
            "gate_c_authorized": False,
            "gate_c_executed": False,
            "policy_track_selected": False,
            "simulation_policy_accepted": False,
            "promotion_eligible": False,
            "physical_transfer_ready": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "new_seed": False,
            "extra_repeat": False,
            "threshold_changed": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_tensor_artifact(
    payload: dict[str, Any], *, attempt: dict[str, Any], target: list[list[float]]
) -> None:
    verify_signed_payload(payload, label="T20.36m tensor artifact")
    expected = build_tensor_artifact(
        attempt=attempt,
        rows=payload.get("rows"),
        target=target,
    )
    if payload != expected:
        raise ValueError("T20.36m tensor artifact drifted")


def verify_run_summary(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
    permit: dict[str, Any],
    attempt: dict[str, Any],
    tensor_artifact: dict[str, Any],
    target: list[list[float]],
) -> None:
    verify_signed_payload(payload, label="T20.36m run summary")
    expected = build_run_summary(
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        target=target,
    )
    if payload != expected:
        raise ValueError("T20.36m run summary drifted")


def verify_result(
    payload: dict[str, Any], *, sources: dict[str, Any], run: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36m result")
    expected = build_result(sources=sources, run=run)
    if payload != expected:
        raise ValueError("T20.36m result drifted")


def build_failure(
    *,
    permit: dict[str, Any],
    attempt: dict[str, Any],
    failure_stage: str,
    error_type: str,
    error_message: str,
    checkpoint_tensor_read: bool,
    model_constructed: bool,
    model_loaded: bool,
    model_inference: bool,
    tensor_artifact_written: bool,
) -> dict[str, Any]:
    if not all(isinstance(value, bool) for value in (
        checkpoint_tensor_read,
        model_constructed,
        model_loaded,
        model_inference,
        tensor_artifact_written,
    )):
        raise ValueError("T20.36m failure state must be boolean")
    if not all(isinstance(value, str) and value.strip() for value in (
        failure_stage,
        error_type,
        error_message,
    )):
        raise ValueError("T20.36m failure details must be nonblank")
    return sign_payload(
        {
            "schema_version": FAILURE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "inference_permit_identity_sha256": permit["identity_sha256"],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "failure_stage": failure_stage,
            "error_type": error_type,
            "error_message": error_message,
            "checkpoint_tensor_read": checkpoint_tensor_read,
            "model_constructed": model_constructed,
            "model_loaded": model_loaded,
            "model_inference": model_inference,
            "tensor_artifact_written": tensor_artifact_written,
            "optimizer_created": False,
            "optimizer_training": False,
            "new_seed": False,
            "extra_repeat": False,
            "threshold_changed": False,
            "gate_c_authorized": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def build_failure_result(
    *, sources: dict[str, Any], failure: dict[str, Any]
) -> dict[str, Any]:
    verify_signed_payload(failure, label="T20.36m failure")
    return sign_payload(
        {
            "schema_version": FAILURE_RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "decision": "tensor_reproduction_runtime_failure",
            "failure_identity_sha256": failure["identity_sha256"],
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
            "amended_gate_b_passed": False,
            "gate_c_route_open": False,
            "gate_c_authorized": False,
            "simulation_policy_accepted": False,
            "promotion_eligible": False,
            "physical_transfer_ready": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "threshold_changed": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def load_live_contracts(
    *, authority_identity: str, repo_root: Path = REPO_ROOT
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    sources = load_verified_sources(repo_root=root)
    preflight = load_strict_json(root / RUNTIME_PREFLIGHT_PATH)
    verify_runtime_preflight(
        preflight,
        sources=sources,
        authority_identity=authority_identity,
    )
    permit = load_strict_json(root / INFERENCE_PERMIT_PATH)
    verify_inference_permit(
        permit,
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=preflight,
    )
    return sources, preflight, permit


def _matrix(value: Any, *, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != TARGET_HORIZON:
        raise ValueError(f"T20.36m {label} must be 50x6")
    result = []
    for row in value:
        if not isinstance(row, list) or len(row) != len(JOINT_NAMES):
            raise ValueError(f"T20.36m {label} must be 50x6")
        normalized = []
        for item in row:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError(f"T20.36m {label} must be finite")
            numeric = float(item)
            if not math.isfinite(numeric):
                raise ValueError(f"T20.36m {label} must be finite")
            normalized.append(numeric)
        result.append(normalized)
    return result


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36m {label} must be sha256")
    return value


def _commit(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36m {label} must be a full commit")
    return value
