"""Fail-closed pre-run and result contracts for T20.36h SmolVLA Gate B."""

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
from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (
    ATTEMPT_PATH,
    EVALUATION_UPDATE_SCHEDULE,
    INFERENCE_SEEDS,
    MAXIMUM_OPTIMIZER_UPDATES,
    OBJECTIVE_SEEDS,
    RESULT_PATH,
    SPEC_PATH,
    verify_spec_file as verify_design_spec_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ATTEMPT_PATH.parent
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
FAILURE_PATH = RUN_ROOT / "failure.json"
FAILURE_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36h_exact_smolvla_gate_b_failure_result.json"
)
CHECKPOINT_ROOT = RUN_ROOT / "checkpoint"
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36h_exact_smolvla_gate_b_preflight.json"
)
TRAINING_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36h_exact_smolvla_gate_b_permit.json"
)
TASK_ID = "T20.36h"
EXPECTED_SPEC_IDENTITY = (
    "fb217f3e142bf082cc8628928bdb2b26c5abdaf8e3355ecd04c32ae17ff8f175"
)
RUNTIME_PREFLIGHT_SCHEMA_VERSION = (
    "scenesmith.t20_36h_exact_smolvla_gate_b_preflight.v1"
)
TRAINING_PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_36h_exact_smolvla_gate_b_permit.v1"
)
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_36h_exact_smolvla_gate_b_attempt.v1"
EVALUATION_SCHEMA_VERSION = (
    "scenesmith.t20_36h_exact_smolvla_gate_b_evaluation.v1"
)
RUN_SCHEMA_VERSION = "scenesmith.t20_36h_exact_smolvla_gate_b_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36h_exact_smolvla_gate_b_result.v1"
FAILURE_SCHEMA_VERSION = "scenesmith.t20_36h_exact_smolvla_gate_b_failure.v1"
FAILURE_RESULT_SCHEMA_VERSION = (
    "scenesmith.t20_36h_exact_smolvla_gate_b_failure_result.v1"
)
MINIMUM_FREE_DISK_BYTES = 6 * 1024 * 1024 * 1024
SMOKE_SEED = 20260800
EXPECTED_DEPENDENCY_VERSIONS = {
    "datasets": "4.8.5",
    "lerobot": "0.6.1",
    "numpy": "2.2.6",
    "pyarrow": "24.0.0",
    "safetensors": "0.8.0",
    "tokenizers": "0.22.2",
    "torch": "2.11.0",
    "torchvision": "0.26.0",
    "transformers": "5.5.4",
}


def load_verified_spec(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    return verify_design_spec_file(repo_root=repo_root)


def build_runtime_preflight(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    python_major_minor: list[int],
    dependency_versions: dict[str, str],
    mps_available: bool,
    lerobot_stack_identity_sha256: str,
    free_disk_bytes: int,
    batch_evidence: dict[str, Any],
    checkpoint_tree: list[dict[str, Any]],
    source_commit: str,
    remote_source_commit: str,
    branch: str,
    scoped_dirty_paths: list[str],
    attempt_exists: bool,
    run_exists: bool,
    result_exists: bool,
) -> dict[str, Any]:
    _verify_spec(spec)
    _sha(authority_identity, "authority identity")
    _sha(lerobot_stack_identity_sha256, "LeRobot stack identity")
    _commit(source_commit, "source commit")
    _commit(remote_source_commit, "remote source commit")
    checkpoints = _checkpoint_inventory(checkpoint_tree, spec=spec)
    _validate_batch_evidence(batch_evidence, spec=spec)
    if (
        python_major_minor != [3, 12]
        or dependency_versions != EXPECTED_DEPENDENCY_VERSIONS
        or mps_available is not True
        or isinstance(free_disk_bytes, bool)
        or not isinstance(free_disk_bytes, int)
        or free_disk_bytes < MINIMUM_FREE_DISK_BYTES
        or source_commit != remote_source_commit
        or branch != "codex/pi05-autolearn-loop"
        or scoped_dirty_paths != []
        or attempt_exists is not False
        or run_exists is not False
        or result_exists is not False
    ):
        raise ValueError("T20.36h runtime preflight failed closed")
    return sign_payload(
        {
            "schema_version": RUNTIME_PREFLIGHT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "python_major_minor": python_major_minor,
            "dependency_versions": dict(dependency_versions),
            "mps_available": True,
            "lerobot_stack_identity_sha256": lerobot_stack_identity_sha256,
            "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
            "free_disk_bytes": free_disk_bytes,
            "batch_evidence": batch_evidence,
            "checkpoint_tree": checkpoints,
            "checkpoint_tree_identity_sha256": hashlib.sha256(
                canonical_json_bytes(checkpoints)
            ).hexdigest(),
            "checkpoint_content_read_as_raw_bytes": True,
            "checkpoint_tensor_deserialized": False,
            "source_commit": source_commit,
            "remote_source_commit": remote_source_commit,
            "remote_source_commit_matches": True,
            "branch": branch,
            "scoped_dirty_paths": [],
            "attempt_exists": False,
            "run_exists": False,
            "result_exists": False,
            "offline_environment_required": True,
            "network_accessed": False,
            "weights_downloaded": False,
            "attempt_marker_created": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.36h runtime preflight")
    expected = build_runtime_preflight(
        spec=spec,
        authority_identity=authority_identity,
        python_major_minor=payload.get("python_major_minor"),
        dependency_versions=payload.get("dependency_versions"),
        mps_available=payload.get("mps_available"),
        lerobot_stack_identity_sha256=payload.get(
            "lerobot_stack_identity_sha256"
        ),
        free_disk_bytes=payload.get("free_disk_bytes"),
        batch_evidence=payload.get("batch_evidence"),
        checkpoint_tree=payload.get("checkpoint_tree"),
        source_commit=payload.get("source_commit"),
        remote_source_commit=payload.get("remote_source_commit"),
        branch=payload.get("branch"),
        scoped_dirty_paths=payload.get("scoped_dirty_paths"),
        attempt_exists=payload.get("attempt_exists"),
        run_exists=payload.get("run_exists"),
        result_exists=payload.get("result_exists"),
    )
    if payload != expected:
        raise ValueError("T20.36h runtime preflight drifted")


def build_training_permit(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> dict[str, Any]:
    verify_runtime_preflight(
        runtime_preflight,
        spec=spec,
        authority_identity=authority_identity,
    )
    return sign_payload(
        {
            "schema_version": TRAINING_PERMIT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime_preflight[
                "identity_sha256"
            ],
            "checkpoint_tree_identity_sha256": runtime_preflight[
                "checkpoint_tree_identity_sha256"
            ],
            "required_source_commit": runtime_preflight["source_commit"],
            "authorized_attempt_count": 1,
            "authorized_actions": [
                "simulation_model_construction",
                "simulation_model_inference",
                "simulation_optimizer_training",
            ],
            "evaluation_update_schedule": list(EVALUATION_UPDATE_SCHEDULE),
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "attempt_marker_path": str(ATTEMPT_PATH),
            "attempt_marker_must_precede_model_construction": True,
            "runtime_smoke_is_part_of_counted_attempt": True,
            "smoke_failure_consumes_attempt": True,
            "local_execution_eligible_after_remote_preservation": True,
            "retry_or_sweep_allowed": False,
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_training_permit(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36h training permit")
    expected = build_training_permit(
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.36h training permit drifted")


def build_attempt_marker(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    source_commit: str,
) -> dict[str, Any]:
    _verify_spec(spec)
    _sha(authority_identity, "authority identity")
    _commit(source_commit, "attempt source commit")
    verify_signed_payload(training_permit, label="T20.36h training permit")
    if (
        training_permit.get("training_spec_identity_sha256")
        != spec["identity_sha256"]
        or training_permit.get("authority_decision_identity_sha256")
        != authority_identity
        or training_permit.get("authorized_attempt_count") != 1
        or training_permit.get("smoke_failure_consumes_attempt") is not True
    ):
        raise ValueError("T20.36h attempt permit linkage drifted")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "training_permit_identity_sha256": training_permit[
                "identity_sha256"
            ],
            "source_commit": source_commit,
            "training_seed": spec["campaign"]["training_seed"],
            "attempt_number": 1,
            "created_before_model_construction": True,
            "model_constructed": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_attempt_marker(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36h attempt marker")
    expected = build_attempt_marker(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        source_commit=payload.get("source_commit"),
    )
    if payload != expected:
        raise ValueError("T20.36h attempt marker drifted")


def build_failure(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    failure_stage: str,
    error_type: str,
    error_message: str,
    optimizer_update_count: int,
    model_constructed: bool,
    model_loaded: bool,
    model_inference: bool,
    optimizer_created: bool,
    optimizer_training: bool,
) -> dict[str, Any]:
    _verify_spec(spec)
    verify_attempt_marker(
        attempt,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
    )
    if failure_stage not in {
        "model_construction",
        "runtime_smoke",
        "optimizer_training",
        "evaluation",
        "checkpoint_write",
    }:
        raise ValueError("T20.36h failure stage is invalid")
    if (
        not isinstance(error_type, str)
        or not error_type
        or not isinstance(error_message, str)
        or not error_message
        or len(error_message) > 2000
        or isinstance(optimizer_update_count, bool)
        or not isinstance(optimizer_update_count, int)
        or not 0 <= optimizer_update_count <= MAXIMUM_OPTIMIZER_UPDATES
        or any(
            not isinstance(value, bool)
            for value in (
                model_constructed,
                model_loaded,
                model_inference,
                optimizer_created,
                optimizer_training,
            )
        )
    ):
        raise ValueError("T20.36h failure evidence is invalid")
    return sign_payload(
        {
            "schema_version": FAILURE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "training_permit_identity_sha256": training_permit[
                "identity_sha256"
            ],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "failure_stage": failure_stage,
            "error_type": error_type,
            "error_message": error_message,
            "optimizer_update_count": optimizer_update_count,
            "attempt_consumed": True,
            "retry_or_sweep_allowed": False,
            "model_constructed": model_constructed,
            "checkpoint_tensor_read": model_constructed,
            "model_loaded": model_loaded,
            "model_inference": model_inference,
            "optimizer_created": optimizer_created,
            "optimizer_training": optimizer_training,
            "gate_b_passed": False,
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_failure(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36h failure")
    expected = build_failure(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
        failure_stage=payload.get("failure_stage"),
        error_type=payload.get("error_type"),
        error_message=payload.get("error_message"),
        optimizer_update_count=payload.get("optimizer_update_count"),
        model_constructed=payload.get("model_constructed"),
        model_loaded=payload.get("model_loaded"),
        model_inference=payload.get("model_inference"),
        optimizer_created=payload.get("optimizer_created"),
        optimizer_training=payload.get("optimizer_training"),
    )
    if payload != expected:
        raise ValueError("T20.36h failure evidence drifted")


def build_failure_result(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    failure: dict[str, Any],
) -> dict[str, Any]:
    verify_failure(
        failure,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
    )
    missing_num2words = (
        failure["error_type"] == "ImportError"
        and "num2words" in failure["error_message"]
    )
    return sign_payload(
        {
            "schema_version": FAILURE_RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "training_permit_identity_sha256": training_permit[
                "identity_sha256"
            ],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "failure_identity_sha256": failure["identity_sha256"],
            "failure_stage": failure["failure_stage"],
            "error_type": failure["error_type"],
            "error_message": failure["error_message"],
            "failure_class": (
                "missing_smolvla_extra_dependency"
                if missing_num2words
                else "bounded_smolvla_runtime_failure"
            ),
            "missing_dependency_observed": (
                "num2words" if missing_num2words else None
            ),
            "optimizer_update_count": failure["optimizer_update_count"],
            "attempt_consumed": True,
            "retry_or_sweep_allowed": False,
            "smolvla_gate_b_evaluated": False,
            "gate_b_passed": False,
            "decision": "smolvla_attempt_runtime_dependency_failure",
            "selected_next_hypothesis": (
                "audit_exact_smolvla_extra_dependency_closure_without_model_retry"
            ),
            "model_constructed": failure["model_constructed"],
            "checkpoint_tensor_read": failure["checkpoint_tensor_read"],
            "model_loaded": failure["model_loaded"],
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_failure_result(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    failure: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36h failure result")
    expected = build_failure_result(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
        failure=failure,
    )
    if payload != expected:
        raise ValueError("T20.36h failure result drifted")


def build_evaluation_row(
    *,
    optimizer_update_count: int,
    supervised_objective_by_seed: list[float],
    baseline_objective_mean: float,
    inference_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if (
        isinstance(optimizer_update_count, bool)
        or optimizer_update_count not in EVALUATION_UPDATE_SCHEDULE
    ):
        raise ValueError("T20.36h evaluation update is outside the schedule")
    objectives = _finite_trace(
        supervised_objective_by_seed,
        len(OBJECTIVE_SEEDS),
        "objective seed values",
    )
    objective = sum(objectives) / len(objectives)
    baseline = _positive(baseline_objective_mean, "baseline objective")
    if not isinstance(inference_rows, list) or len(inference_rows) != len(
        INFERENCE_SEEDS
    ):
        raise ValueError("T20.36h inference seed coverage drifted")
    rows = []
    for index, (seed, row) in enumerate(zip(INFERENCE_SEEDS, inference_rows)):
        if (
            not isinstance(row, dict)
            or row.get("seed_index") != index
            or row.get("inference_seed") != seed
        ):
            raise ValueError("T20.36h inference seed order drifted")
        first_hash = _sha(row.get("first_action_chunk_sha256"), "first action")
        second_hash = _sha(
            row.get("second_action_chunk_sha256"), "second action"
        )
        repeat_delta = _nonnegative(
            row.get("repeat_maximum_absolute_difference_rad"), "repeat delta"
        )
        rows.append(
            {
                "seed_index": index,
                "inference_seed": seed,
                "first_action_chunk_sha256": first_hash,
                "second_action_chunk_sha256": second_hash,
                "action_hashes_match": first_hash == second_hash,
                "repeat_maximum_absolute_difference_rad": repeat_delta,
                "mean_absolute_error_rad": _nonnegative(
                    row.get("mean_absolute_error_rad"), "mean action error"
                ),
                "maximum_absolute_error_rad": _nonnegative(
                    row.get("maximum_absolute_error_rad"), "maximum action error"
                ),
            }
        )
    deterministic = all(
        row["action_hashes_match"]
        and row["repeat_maximum_absolute_difference_rad"] == 0.0
        for row in rows
    )
    ratio = objective / baseline
    maximum_error = max(row["maximum_absolute_error_rad"] for row in rows)
    objective_pass = ratio <= 0.10
    action_pass = maximum_error <= 0.05
    return sign_payload(
        {
            "schema_version": EVALUATION_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "optimizer_update_count": optimizer_update_count,
            "objective_seeds": list(OBJECTIVE_SEEDS),
            "supervised_objective_by_seed": objectives,
            "supervised_objective_mean": objective,
            "baseline_objective_mean": baseline,
            "final_to_baseline_supervised_objective_ratio": ratio,
            "inference_rows": rows,
            "all_seed_repeats_deterministic": deterministic,
            "maximum_absolute_error_rad": maximum_error,
            "objective_ratio_within_threshold": objective_pass,
            "all_actions_within_threshold": action_pass,
            "gate_b_passed": objective_pass and action_pass and deterministic,
        }
    )


def build_run_summary(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    runtime_smoke: dict[str, Any],
    optimizer_update_count: int,
    per_update_objective: list[float],
    gradient_norms_before_clip: list[float],
    evaluations: list[dict[str, Any]],
    checkpoint_tree: list[dict[str, Any]],
) -> dict[str, Any]:
    _verify_spec(spec)
    _sha(authority_identity, "authority identity")
    verify_attempt_marker(
        attempt,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
    )
    smoke = _runtime_smoke(runtime_smoke)
    if (
        isinstance(optimizer_update_count, bool)
        or optimizer_update_count not in EVALUATION_UPDATE_SCHEDULE[1:]
    ):
        raise ValueError("T20.36h optimizer update count drifted")
    losses = _finite_trace(
        per_update_objective, optimizer_update_count, "objective trace"
    )
    gradients = _finite_trace(
        gradient_norms_before_clip, optimizer_update_count, "gradient trace"
    )
    normalized_evaluations = _validated_evaluations(evaluations)
    updates = [row["optimizer_update_count"] for row in normalized_evaluations]
    if (
        updates != EVALUATION_UPDATE_SCHEDULE[: len(updates)]
        or updates[-1] != optimizer_update_count
    ):
        raise ValueError("T20.36h evaluation schedule is incomplete or reordered")
    passing = [row for row in normalized_evaluations[1:] if row["gate_b_passed"]]
    passed = bool(passing)
    if passed and normalized_evaluations[-1] != passing[0]:
        raise ValueError("T20.36h run continued after its first Gate B pass")
    if not passed and updates != EVALUATION_UPDATE_SCHEDULE:
        raise ValueError("T20.36h failed run stopped before its ceiling")
    tree = _saved_checkpoint_tree(checkpoint_tree)
    final = normalized_evaluations[-1]
    return sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "training_permit_identity_sha256": training_permit[
                "identity_sha256"
            ],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "runtime_smoke": smoke,
            "optimizer_update_count": optimizer_update_count,
            "training_seed": spec["campaign"]["training_seed"],
            "per_update_objective": losses,
            "gradient_norms_before_clip": gradients,
            "evaluations": normalized_evaluations,
            "selected_checkpoint_update": optimizer_update_count,
            "checkpoint_tree": tree,
            "checkpoint_identity_sha256": hashlib.sha256(
                canonical_json_bytes(tree)
            ).hexdigest(),
            "gate_b_passed": passed,
            "decision": "smolvla_gate_b_pass" if passed else "smolvla_gate_b_fail",
            "selected_next_hypothesis": (
                "design_smolvla_gate_c_training_episode_reproduction"
                if passed
                else "localize_smolvla_architecture_optimizer_and_boundary_error"
            ),
            "final_to_baseline_supervised_objective_ratio": final[
                "final_to_baseline_supervised_objective_ratio"
            ],
            "final_maximum_absolute_error_rad": final[
                "maximum_absolute_error_rad"
            ],
            "model_constructed": True,
            "checkpoint_tensor_read": True,
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": True,
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_run_summary(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36h run summary")
    expected = build_run_summary(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
        runtime_smoke=payload.get("runtime_smoke"),
        optimizer_update_count=payload.get("optimizer_update_count"),
        per_update_objective=payload.get("per_update_objective"),
        gradient_norms_before_clip=payload.get("gradient_norms_before_clip"),
        evaluations=payload.get("evaluations"),
        checkpoint_tree=payload.get("checkpoint_tree"),
    )
    if payload != expected:
        raise ValueError("T20.36h run summary drifted")


def build_result(*, spec: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    _verify_spec(spec)
    _validate_run_intrinsic(run, spec=spec)
    passed = run.get("gate_b_passed") is True
    if run.get("decision") != (
        "smolvla_gate_b_pass" if passed else "smolvla_gate_b_fail"
    ):
        raise ValueError("T20.36h run decision drifted")
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "run_identity_sha256": run["identity_sha256"],
            "optimizer_update_count": run["optimizer_update_count"],
            "selected_checkpoint_update": run["selected_checkpoint_update"],
            "checkpoint_identity_sha256": run["checkpoint_identity_sha256"],
            "final_to_baseline_supervised_objective_ratio": run[
                "final_to_baseline_supervised_objective_ratio"
            ],
            "final_maximum_absolute_error_rad": run[
                "final_maximum_absolute_error_rad"
            ],
            "gate_b_passed": passed,
            "decision": run["decision"],
            "smolvla_one_batch_capability_verified": passed,
            "gate_c_design_routed": passed,
            "smolvla_localization_routed": not passed,
            "policy_track_selected": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "model_constructed": True,
            "checkpoint_tensor_read": True,
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": True,
            "optimizer_training": True,
            "physical_actuation": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_result(
    payload: dict[str, Any], *, spec: dict[str, Any], run: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36h result")
    if payload != build_result(spec=spec, run=run):
        raise ValueError("T20.36h result drifted")


def _validate_run_intrinsic(run: dict[str, Any], *, spec: dict[str, Any]) -> None:
    verify_signed_payload(run, label="T20.36h run summary")
    updates = run.get("optimizer_update_count")
    if (
        run.get("schema_version") != RUN_SCHEMA_VERSION
        or run.get("task_id") != TASK_ID
        or run.get("training_spec_identity_sha256") != spec["identity_sha256"]
        or isinstance(updates, bool)
        or updates not in EVALUATION_UPDATE_SCHEDULE[1:]
    ):
        raise ValueError("T20.36h run source linkage drifted")
    _runtime_smoke(run.get("runtime_smoke"))
    _finite_trace(run.get("per_update_objective"), updates, "objective trace")
    _finite_trace(
        run.get("gradient_norms_before_clip"), updates, "gradient trace"
    )
    evaluations = _validated_evaluations(run.get("evaluations"))
    schedule = [row["optimizer_update_count"] for row in evaluations]
    if (
        schedule != EVALUATION_UPDATE_SCHEDULE[: len(schedule)]
        or schedule[-1] != updates
    ):
        raise ValueError("T20.36h intrinsic evaluation schedule drifted")
    passing = [row for row in evaluations[1:] if row["gate_b_passed"]]
    if bool(passing) != run.get("gate_b_passed"):
        raise ValueError("T20.36h intrinsic gate decision drifted")
    if passing and evaluations[-1] != passing[0]:
        raise ValueError("T20.36h intrinsic run continued after pass")
    if not passing and schedule != EVALUATION_UPDATE_SCHEDULE:
        raise ValueError("T20.36h intrinsic failed run is incomplete")
    tree = _saved_checkpoint_tree(run.get("checkpoint_tree"))
    identity = hashlib.sha256(canonical_json_bytes(tree)).hexdigest()
    if identity != run.get("checkpoint_identity_sha256"):
        raise ValueError("T20.36h intrinsic checkpoint identity drifted")
    expected_decision = (
        "smolvla_gate_b_pass" if passing else "smolvla_gate_b_fail"
    )
    final = evaluations[-1]
    frozen_false = (
        "policy_track_selected",
        "gate_b_threshold_changed",
        "gate_c_authorized",
        "closed_loop_rollout",
        "simulation_policy_accepted",
        "physical_actuation",
        "network_accessed",
        "weights_downloaded",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if (
        run.get("decision") != expected_decision
        or run.get("selected_checkpoint_update") != updates
        or run.get("final_to_baseline_supervised_objective_ratio")
        != final["final_to_baseline_supervised_objective_ratio"]
        or run.get("final_maximum_absolute_error_rad")
        != final["maximum_absolute_error_rad"]
        or any(
            run.get(field) is not True
            for field in (
                "model_constructed",
                "checkpoint_tensor_read",
                "model_loaded",
                "model_inference",
                "optimizer_created",
                "optimizer_training",
            )
        )
        or any(run.get(field) is not False for field in frozen_false)
    ):
        raise ValueError("T20.36h intrinsic result or authority drifted")


def _verify_spec(spec: dict[str, Any]) -> None:
    verify_signed_payload(spec, label="T20.36h source spec")
    if (
        spec.get("identity_sha256") != EXPECTED_SPEC_IDENTITY
        or spec.get("execution_task_id") != TASK_ID
        or spec.get("campaign", {}).get("evaluation_update_schedule")
        != EVALUATION_UPDATE_SCHEDULE
        or spec.get("campaign", {}).get("maximum_optimizer_updates")
        != MAXIMUM_OPTIMIZER_UPDATES
        or spec.get("campaign", {}).get("scheduler") is not None
        or spec.get("gate", {}).get("maximum_physical_action_error_rad") != 0.05
        or spec.get("gate", {}).get(
            "maximum_final_to_baseline_supervised_objective_ratio"
        )
        != 0.10
    ):
        raise ValueError("T20.36h source spec drifted")


def _validate_batch_evidence(value: Any, *, spec: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ValueError("T20.36h batch evidence is missing")
    required = spec["canonical_batch"]["batch_evidence_required"]
    if (
        value.get("action_shape") != [50, 6]
        or value.get("action_pad_count") != 0
        or value.get("state_shape") != [6]
        or value.get("physical_action_chunk_sha256")
        != required["physical_action_chunk_sha256"]
        or value.get("physical_state_sha256")
        != required["physical_state_sha256"]
        or value.get("image_tensor_sha256", {}).get(
            "observation.images.base_0_rgb"
        )
        != required["base_image_tensor_sha256"]
        or value.get("image_tensor_sha256", {}).get(
            "observation.images.left_wrist_0_rgb"
        )
        != required["wrist_image_tensor_sha256"]
    ):
        raise ValueError("T20.36h batch evidence drifted")


def _checkpoint_inventory(
    values: Any, *, spec: dict[str, Any]
) -> list[dict[str, Any]]:
    expected = {}
    for group in ("policy", "vlm"):
        for row in spec["local_cache"][f"{group}_files"]:
            if row["is_weight_or_tensor_file"]:
                expected[f"{group}/{row['name']}"] = row["size_bytes"]
    if not isinstance(values, list) or len(values) != len(expected):
        raise ValueError("T20.36h checkpoint inventory coverage drifted")
    rows = []
    for row in values:
        if not isinstance(row, dict):
            raise ValueError("T20.36h checkpoint inventory row is invalid")
        path = row.get("path")
        size = row.get("size_bytes")
        if path not in expected or size != expected[path]:
            raise ValueError("T20.36h checkpoint inventory path or size drifted")
        rows.append(
            {"path": path, "size_bytes": size, "sha256": _sha(row.get("sha256"), path)}
        )
    rows.sort(key=lambda row: row["path"])
    if [row["path"] for row in rows] != sorted(expected):
        raise ValueError("T20.36h checkpoint inventory is duplicated or incomplete")
    return rows


def _runtime_smoke(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("T20.36h runtime smoke is missing")
    parameters = _inventory_counts(
        value.get("parameter_inventory"), "parameter", allow_empty=False
    )
    buffers = _inventory_counts(
        value.get("buffer_inventory"), "buffer", allow_empty=True
    )
    trainable = value.get("trainable_parameter_inventory")
    if not isinstance(trainable, list) or not trainable:
        raise ValueError("T20.36h trainable inventory is missing")
    rows = []
    allowed = (
        "model.vlm_with_expert.lm_expert.",
        "model.state_proj.",
        "model.action_in_proj.",
        "model.action_out_proj.",
        "model.action_time_mlp_in.",
        "model.action_time_mlp_out.",
    )
    for row in trainable:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("name"), str)
            or not row["name"].startswith(allowed)
            or row.get("device") != "mps:0"
            or not isinstance(row.get("dtype"), str)
            or isinstance(row.get("numel"), bool)
            or not isinstance(row.get("numel"), int)
            or row["numel"] <= 0
        ):
            raise ValueError("T20.36h trainable scope or device drifted")
        rows.append(dict(row))
    rows.sort(key=lambda row: row["name"])
    if len({row["name"] for row in rows}) != len(rows):
        raise ValueError("T20.36h trainable inventory contains duplicates")
    required_prefixes = (
        "model.vlm_with_expert.lm_expert.",
        "model.state_proj.",
        "model.action_in_proj.",
        "model.action_out_proj.",
        "model.action_time_mlp_in.",
        "model.action_time_mlp_out.",
    )
    if any(
        not any(row["name"].startswith(prefix) for row in rows)
        for prefix in required_prefixes
    ):
        raise ValueError("T20.36h required trainable pathway is missing")
    if (
        value.get("mps_forward_backward_passed") is not True
        or value.get("cpu_fallback_observed") is not False
    ):
        raise ValueError("T20.36h runtime smoke did not pass on MPS")
    return {
        "processed_action_shape": _exact_list(
            value.get("processed_action_shape"), [1, 50, 6], "action shape"
        ),
        "processed_state_shape": _exact_list(
            value.get("processed_state_shape"), [1, 6], "state shape"
        ),
        "processed_image_keys": _exact_list(
            value.get("processed_image_keys"),
            [
                "observation.images.base_0_rgb",
                "observation.images.left_wrist_0_rgb",
            ],
            "image keys",
        ),
        "parameter_inventory": parameters,
        "buffer_inventory": buffers,
        "trainable_parameter_inventory": rows,
        "trainable_parameter_count": sum(row["numel"] for row in rows),
        "smoke_loss": _nonnegative(value.get("smoke_loss"), "smoke loss"),
        "smoke_gradient_norm": _nonnegative(
            value.get("smoke_gradient_norm"), "smoke gradient norm"
        ),
        "mps_forward_backward_passed": True,
        "cpu_fallback_observed": False,
    }


def _inventory_counts(
    value: Any, label: str, *, allow_empty: bool
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValueError(f"T20.36h {label} inventory is missing")
    rows = []
    for row in value:
        if (
            not isinstance(row, dict)
            or row.get("device") != "mps:0"
            or not isinstance(row.get("dtype"), str)
            or isinstance(row.get("numel"), bool)
            or not isinstance(row.get("numel"), int)
            or row["numel"] < 0
        ):
            raise ValueError(f"T20.36h {label} inventory drifted")
        rows.append(dict(row))
    rows.sort(key=lambda row: (row["device"], row["dtype"]))
    if len({(row["device"], row["dtype"]) for row in rows}) != len(rows):
        raise ValueError(f"T20.36h {label} inventory contains duplicates")
    return rows


def _validated_evaluations(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) < 2:
        raise ValueError("T20.36h evaluation evidence is incomplete")
    rows = []
    baseline = None
    for index, row in enumerate(values):
        if not isinstance(row, dict):
            raise ValueError("T20.36h evaluation row is invalid")
        verify_signed_payload(row, label="T20.36h evaluation row")
        if index == 0:
            baseline = _positive(
                row.get("baseline_objective_mean"), "baseline objective"
            )
        expected = build_evaluation_row(
            optimizer_update_count=row.get("optimizer_update_count"),
            supervised_objective_by_seed=row.get(
                "supervised_objective_by_seed"
            ),
            baseline_objective_mean=baseline,
            inference_rows=row.get("inference_rows"),
        )
        if row != expected:
            raise ValueError("T20.36h evaluation row drifted")
        rows.append(row)
    return rows


def _saved_checkpoint_tree(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list) or not values:
        raise ValueError("T20.36h saved checkpoint tree is missing")
    rows = []
    for row in values:
        if not isinstance(row, dict):
            raise ValueError("T20.36h saved checkpoint row is invalid")
        path = row.get("path")
        size = row.get("size_bytes")
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or ".." in Path(path).parts
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size <= 0
        ):
            raise ValueError("T20.36h saved checkpoint path is unsafe")
        rows.append(
            {"path": path, "size_bytes": size, "sha256": _sha(row.get("sha256"), path)}
        )
    rows.sort(key=lambda row: row["path"])
    if len({row["path"] for row in rows}) != len(rows):
        raise ValueError("T20.36h saved checkpoint tree contains duplicates")
    required = {
        "config.json",
        "model.safetensors",
        "policy_preprocessor.json",
        "policy_postprocessor.json",
    }
    if not required.issubset({row["path"] for row in rows}):
        raise ValueError("T20.36h saved checkpoint tree is incomplete")
    return rows


def _finite_trace(values: Any, length: int, label: str) -> list[float]:
    if not isinstance(values, list) or len(values) != length:
        raise ValueError(f"T20.36h {label} length drifted")
    return [_nonnegative(value, label) for value in values]


def _exact_list(value: Any, expected: list[Any], label: str) -> list[Any]:
    if value != expected:
        raise ValueError(f"T20.36h {label} drifted")
    return list(value)


def _positive(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number <= 0:
        raise ValueError(f"T20.36h {label} must be positive")
    return number


def _nonnegative(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number < 0:
        raise ValueError(f"T20.36h {label} must be nonnegative")
    return number


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.36h {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.36h {label} must be finite")
    return number


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36h {label} is not a lowercase SHA-256")
    return value


def _commit(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36h {label} is not a full Git commit")
    return value
