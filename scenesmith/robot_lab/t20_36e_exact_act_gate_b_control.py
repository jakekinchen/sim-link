"""Fail-closed runtime and result contracts for the T20.36e ACT control."""

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
from scenesmith.robot_lab.t20_36d_exact_act_gate_b_control_design import (
    EVALUATION_REPETITIONS,
    EVALUATION_UPDATE_SCHEDULE,
    MAXIMUM_OPTIMIZER_UPDATES,
    SPEC_PATH,
    verify_spec_file as verify_design_spec_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36e_exact_act_gate_b_control_preflight.json"
)
TRAINING_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36e_exact_act_gate_b_control_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_36e_exact_act_gate_b_control_result.json"
)
RUN_ROOT = Path("outputs/robot_lab/t20_36e_exact_act_gate_b_control_run_001")
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
CHECKPOINT_ROOT = RUN_ROOT / "checkpoint"
RUNTIME_PREFLIGHT_SCHEMA_VERSION = (
    "scenesmith.t20_36e_exact_act_gate_b_control_preflight.v1"
)
TRAINING_PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_36e_exact_act_gate_b_control_permit.v1"
)
ATTEMPT_SCHEMA_VERSION = (
    "scenesmith.t20_36e_exact_act_gate_b_control_attempt.v1"
)
RUN_SCHEMA_VERSION = "scenesmith.t20_36e_exact_act_gate_b_control_run.v1"
RESULT_SCHEMA_VERSION = (
    "scenesmith.t20_36e_exact_act_gate_b_control_result.v1"
)
TASK_ID = "T20.36e"
EXPECTED_SPEC_IDENTITY = (
    "45c90dc05578546e589cbde28ac3f072e0a8b87c2dd1001f343a8d7f4d586a4b"
)
EXPECTED_DEPENDENCY_VERSIONS = {
    "datasets": "4.8.5",
    "lerobot": "0.6.1",
    "numpy": "2.2.6",
    "pyarrow": "24.0.0",
    "torch": "2.11.0",
    "torchvision": "0.26.0",
}
MINIMUM_FREE_DISK_BYTES = 6 * 1024 * 1024 * 1024
EXPECTED_BATCH_EVIDENCE = {
    "dataset_episode_index": 0,
    "dataset_frame_index": 0,
    "action_shape": [50, 6],
    "action_pad_count": 0,
    "state_shape": [6],
    "image_shapes": {
        "observation.images.base_0_rgb": [3, 256, 256],
        "observation.images.left_wrist_0_rgb": [3, 256, 256],
    },
    "image_tensor_sha256": {
        "observation.images.base_0_rgb": (
            "5ed2cbd3740a3a377bf705eb6fb0bad4b1d0c9d40a8ef91ed0eaadac65e3fa87"
        ),
        "observation.images.left_wrist_0_rgb": (
            "10362eecfea21ed2cda3b0fe4f4b7246700b0dea13237b9575af323c2d9a649d"
        ),
    },
    "physical_action_chunk_sha256": (
        "5698babc07b2eebc8a3a96d33b28f03bbb33f1bec9b83a97d4e4f8a325c36b7e"
    ),
    "physical_state_sha256": (
        "efd3788785f8c60ac67d91fcb2e754c9b3c13d62798469fbf811a968c8941ec4"
    ),
    "maximum_source_action_error_rad": 7.109611699362972e-08,
    "maximum_source_state_error_rad": 4.207105996911764e-08,
    "maximum_coordinate_round_trip_error_rad": 2.220446049250313e-16,
    "task": (
        "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."
    ),
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
    source_commit: str,
    remote_source_commit: str,
    attempt_exists: bool,
    run_exists: bool,
    result_exists: bool,
) -> dict[str, Any]:
    _verify_spec(spec)
    _sha(authority_identity, "authority identity")
    _sha(lerobot_stack_identity_sha256, "LeRobot stack identity")
    _commit(source_commit, "source commit")
    _commit(remote_source_commit, "remote source commit")
    if (
        python_major_minor != [3, 12]
        or dependency_versions != EXPECTED_DEPENDENCY_VERSIONS
        or mps_available is not True
        or isinstance(free_disk_bytes, bool)
        or not isinstance(free_disk_bytes, int)
        or free_disk_bytes < MINIMUM_FREE_DISK_BYTES
        or batch_evidence != EXPECTED_BATCH_EVIDENCE
        or source_commit != remote_source_commit
        or attempt_exists is not False
        or run_exists is not False
        or result_exists is not False
    ):
        raise ValueError("T20.36e runtime preflight failed closed")
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
            "source_commit": source_commit,
            "remote_source_commit": remote_source_commit,
            "remote_source_commit_matches": True,
            "attempt_exists": False,
            "run_exists": False,
            "result_exists": False,
            "offline_environment_required": True,
            "network_accessed": False,
            "weights_downloaded": False,
            "checkpoint_tensor_read": False,
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
    verify_signed_payload(payload, label="T20.36e runtime preflight")
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
        source_commit=payload.get("source_commit"),
        remote_source_commit=payload.get("remote_source_commit"),
        attempt_exists=payload.get("attempt_exists"),
        run_exists=payload.get("run_exists"),
        result_exists=payload.get("result_exists"),
    )
    if payload != expected:
        raise ValueError("T20.36e runtime preflight drifted")


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
            "local_execution_eligible_after_remote_preservation": True,
            "retry_or_sweep_allowed": False,
            "policy_track_selected": False,
            "smolvla_entry_authorized": False,
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
    verify_signed_payload(payload, label="T20.36e training permit")
    expected = build_training_permit(
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.36e training permit drifted")
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
    verify_signed_payload(training_permit, label="T20.36e training permit")
    if (
        training_permit.get("training_spec_identity_sha256")
        != spec["identity_sha256"]
        or training_permit.get("authority_decision_identity_sha256")
        != authority_identity
        or training_permit.get("authorized_attempt_count") != 1
        or training_permit.get(
            "attempt_marker_must_precede_model_construction"
        )
        is not True
    ):
        raise ValueError("T20.36e attempt permit linkage drifted")
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
    verify_signed_payload(payload, label="T20.36e attempt marker")
    expected = build_attempt_marker(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        source_commit=payload.get("source_commit"),
    )
    if payload != expected:
        raise ValueError("T20.36e attempt marker drifted")


def build_evaluation_row(
    *,
    optimizer_update_count: int,
    supervised_objective_mean: float,
    baseline_objective_mean: float,
    repetition_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if (
        isinstance(optimizer_update_count, bool)
        or optimizer_update_count not in EVALUATION_UPDATE_SCHEDULE
    ):
        raise ValueError("T20.36e evaluation update is outside the schedule")
    objective = _nonnegative(supervised_objective_mean, "supervised objective")
    baseline = _positive(baseline_objective_mean, "baseline objective")
    if (
        not isinstance(repetition_rows, list)
        or len(repetition_rows) != EVALUATION_REPETITIONS
    ):
        raise ValueError("T20.36e deterministic repetition coverage drifted")
    normalized_rows = []
    for index, row in enumerate(repetition_rows):
        if not isinstance(row, dict) or row.get("repetition_index") != index:
            raise ValueError("T20.36e repetition order drifted")
        normalized_rows.append(
            {
                "repetition_index": index,
                "action_chunk_sha256": _sha(
                    row.get("action_chunk_sha256"), "action chunk"
                ),
                "mean_absolute_error_rad": _nonnegative(
                    row.get("mean_absolute_error_rad"), "mean action error"
                ),
                "maximum_absolute_error_rad": _nonnegative(
                    row.get("maximum_absolute_error_rad"), "maximum action error"
                ),
            }
        )
    hashes = {row["action_chunk_sha256"] for row in normalized_rows}
    ratio = objective / baseline
    maximum_error = max(row["maximum_absolute_error_rad"] for row in normalized_rows)
    objective_pass = ratio <= 0.10
    action_pass = maximum_error <= 0.05
    return sign_payload(
        {
            "schema_version": "scenesmith.t20_36e_act_control_evaluation.v1",
            "task_id": TASK_ID,
            "optimizer_update_count": optimizer_update_count,
            "supervised_objective_mean": objective,
            "baseline_objective_mean": baseline,
            "final_to_baseline_supervised_objective_ratio": ratio,
            "repetitions": normalized_rows,
            "all_repetition_action_hashes_match": len(hashes) == 1,
            "maximum_absolute_error_rad": maximum_error,
            "objective_ratio_within_threshold": objective_pass,
            "all_actions_within_threshold": action_pass,
            "gate_b_control_passed": (
                objective_pass and action_pass and len(hashes) == 1
            ),
        }
    )


def build_run_summary(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    training_permit: dict[str, Any],
    attempt: dict[str, Any],
    optimizer_update_count: int,
    per_update_objective: list[float],
    gradient_norms_before_clip: list[float],
    evaluations: list[dict[str, Any]],
    checkpoint_tree: list[dict[str, Any]],
    checkpoint_identity_sha256: str,
) -> dict[str, Any]:
    _verify_spec(spec)
    _sha(authority_identity, "authority identity")
    verify_signed_payload(training_permit, label="T20.36e training permit")
    verify_attempt_marker(
        attempt,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
    )
    if (
        training_permit.get("training_spec_identity_sha256")
        != spec["identity_sha256"]
        or training_permit.get("authority_decision_identity_sha256")
        != authority_identity
        or isinstance(optimizer_update_count, bool)
        or optimizer_update_count not in EVALUATION_UPDATE_SCHEDULE[1:]
    ):
        raise ValueError("T20.36e run permit or update count drifted")
    losses = _finite_trace(
        per_update_objective, optimizer_update_count, "objective trace"
    )
    gradients = _finite_trace(
        gradient_norms_before_clip, optimizer_update_count, "gradient trace"
    )
    normalized_evaluations = _validated_evaluations(evaluations)
    updates = [row["optimizer_update_count"] for row in normalized_evaluations]
    expected_prefix = EVALUATION_UPDATE_SCHEDULE[: len(updates)]
    if updates != expected_prefix or updates[-1] != optimizer_update_count:
        raise ValueError("T20.36e evaluation schedule is incomplete or reordered")
    passing = [
        row
        for row in normalized_evaluations[1:]
        if row["gate_b_control_passed"]
    ]
    passed = bool(passing)
    if passed:
        if normalized_evaluations[-1] != passing[0]:
            raise ValueError("T20.36e run continued after the first passing checkpoint")
    elif updates != EVALUATION_UPDATE_SCHEDULE:
        raise ValueError("T20.36e failed control stopped before the declared ceiling")
    tree = _checkpoint_tree(checkpoint_tree)
    if canonical_json_bytes(tree) != canonical_json_bytes(checkpoint_tree):
        raise ValueError("T20.36e checkpoint tree is not canonical")
    expected_checkpoint_identity = hashlib.sha256(
        canonical_json_bytes(tree)
    ).hexdigest()
    if checkpoint_identity_sha256 != expected_checkpoint_identity:
        raise ValueError("T20.36e checkpoint identity drifted")
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
            "optimizer_update_count": optimizer_update_count,
            "training_seed": spec["campaign"]["training_seed"],
            "per_update_objective": losses,
            "gradient_norms_before_clip": gradients,
            "evaluations": normalized_evaluations,
            "selected_checkpoint_update": optimizer_update_count,
            "checkpoint_tree": tree,
            "checkpoint_identity_sha256": checkpoint_identity_sha256,
            "gate_b_control_passed": passed,
            "decision": (
                "act_control_gate_b_pass" if passed else "act_control_gate_b_fail"
            ),
            "selected_next_hypothesis": (
                "design_smolvla_gate_b_entry"
                if passed
                else "diagnose_shared_pipeline_and_act_control_before_smolvla"
            ),
            "final_to_baseline_supervised_objective_ratio": final[
                "final_to_baseline_supervised_objective_ratio"
            ],
            "final_maximum_absolute_error_rad": final[
                "maximum_absolute_error_rad"
            ],
            "model_constructed": True,
            "model_inference": True,
            "optimizer_created": True,
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "policy_track_selected": False,
            "smolvla_entry_authorized": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
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
    verify_signed_payload(payload, label="T20.36e run summary")
    expected = build_run_summary(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=training_permit,
        attempt=attempt,
        optimizer_update_count=payload.get("optimizer_update_count"),
        per_update_objective=payload.get("per_update_objective"),
        gradient_norms_before_clip=payload.get("gradient_norms_before_clip"),
        evaluations=payload.get("evaluations"),
        checkpoint_tree=payload.get("checkpoint_tree"),
        checkpoint_identity_sha256=payload.get("checkpoint_identity_sha256"),
    )
    if payload != expected:
        raise ValueError("T20.36e run summary drifted")


def build_result(*, spec: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    _verify_spec(spec)
    _validate_run_intrinsic(run, spec=spec)
    passed = run["gate_b_control_passed"]
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
            "gate_b_control_passed": passed,
            "decision": run["decision"],
            "shared_batch_and_normalization_control_passed": passed,
            "shared_path_claim_limited_to_one_batch_statistics_and_round_trip": True,
            "pi05_decode_exonerated": False,
            "smolvla_entry_design_routed": passed,
            "failure_proves_dataset_fault": False,
            "act_is_product_policy": False,
            "model_constructed": True,
            "model_inference": True,
            "optimizer_created": True,
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "policy_track_selected": False,
            "smolvla_entry_authorized": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_result(
    payload: dict[str, Any], *, spec: dict[str, Any], run: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36e result")
    if payload != build_result(spec=spec, run=run):
        raise ValueError("T20.36e result drifted")


def _validate_run_intrinsic(run: dict[str, Any], *, spec: dict[str, Any]) -> None:
    verify_signed_payload(run, label="T20.36e run summary")
    if (
        run.get("schema_version") != RUN_SCHEMA_VERSION
        or run.get("task_id") != TASK_ID
        or run.get("training_spec_identity_sha256") != spec["identity_sha256"]
    ):
        raise ValueError("T20.36e run source linkage drifted")
    updates = run.get("optimizer_update_count")
    _finite_trace(run.get("per_update_objective"), updates, "objective trace")
    _finite_trace(run.get("gradient_norms_before_clip"), updates, "gradient trace")
    evaluations = _validated_evaluations(run.get("evaluations"))
    schedule = [row["optimizer_update_count"] for row in evaluations]
    if (
        schedule != EVALUATION_UPDATE_SCHEDULE[: len(schedule)]
        or schedule[-1] != updates
    ):
        raise ValueError("T20.36e intrinsic evaluation schedule drifted")
    passing = [row for row in evaluations[1:] if row["gate_b_control_passed"]]
    if bool(passing) != run.get("gate_b_control_passed"):
        raise ValueError("T20.36e intrinsic gate decision drifted")
    if passing and evaluations[-1] != passing[0]:
        raise ValueError("T20.36e intrinsic run continued after pass")
    if not passing and schedule != EVALUATION_UPDATE_SCHEDULE:
        raise ValueError("T20.36e intrinsic failed run is incomplete")
    tree = _checkpoint_tree(run.get("checkpoint_tree"))
    identity = hashlib.sha256(canonical_json_bytes(tree)).hexdigest()
    if identity != run.get("checkpoint_identity_sha256"):
        raise ValueError("T20.36e intrinsic checkpoint identity drifted")
    expected_decision = (
        "act_control_gate_b_pass" if passing else "act_control_gate_b_fail"
    )
    if run.get("decision") != expected_decision:
        raise ValueError("T20.36e intrinsic result label drifted")


def _validated_evaluations(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) < 2:
        raise ValueError("T20.36e evaluation evidence is incomplete")
    rows = []
    baseline = None
    for index, row in enumerate(values):
        if not isinstance(row, dict):
            raise ValueError("T20.36e evaluation row is invalid")
        verify_signed_payload(row, label="T20.36e evaluation row")
        if index == 0:
            baseline = _positive(
                row.get("baseline_objective_mean"), "baseline objective"
            )
        expected = build_evaluation_row(
            optimizer_update_count=row.get("optimizer_update_count"),
            supervised_objective_mean=row.get("supervised_objective_mean"),
            baseline_objective_mean=baseline,
            repetition_rows=row.get("repetitions"),
        )
        if row != expected:
            raise ValueError("T20.36e evaluation row drifted")
        rows.append(row)
    return rows


def _checkpoint_tree(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list) or not values:
        raise ValueError("T20.36e checkpoint tree is missing")
    rows = []
    for row in values:
        if not isinstance(row, dict):
            raise ValueError("T20.36e checkpoint tree row is invalid")
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
            raise ValueError("T20.36e checkpoint tree row is unsafe")
        rows.append(
            {"path": path, "size_bytes": size, "sha256": _sha(row.get("sha256"), path)}
        )
    rows.sort(key=lambda row: row["path"])
    if len({row["path"] for row in rows}) != len(rows):
        raise ValueError("T20.36e checkpoint tree contains duplicates")
    required = {"config.json", "model.safetensors"}
    if not required.issubset({row["path"] for row in rows}):
        raise ValueError("T20.36e checkpoint tree is incomplete")
    return rows


def _finite_trace(values: Any, length: Any, label: str) -> list[float]:
    if (
        isinstance(length, bool)
        or not isinstance(length, int)
        or length <= 0
        or not isinstance(values, list)
        or len(values) != length
    ):
        raise ValueError(f"T20.36e {label} length drifted")
    return [_nonnegative(value, label) for value in values]


def _verify_spec(spec: dict[str, Any]) -> None:
    verify_signed_payload(spec, label="T20.36e source spec")
    if (
        spec.get("identity_sha256") != EXPECTED_SPEC_IDENTITY
        or spec.get("execution_task_id") != TASK_ID
        or spec.get("campaign", {}).get("evaluation_update_schedule")
        != EVALUATION_UPDATE_SCHEDULE
        or spec.get("campaign", {}).get("maximum_optimizer_updates")
        != MAXIMUM_OPTIMIZER_UPDATES
        or spec.get("gate", {}).get("maximum_physical_action_error_rad") != 0.05
        or spec.get("gate", {}).get(
            "maximum_final_to_baseline_supervised_objective_ratio"
        )
        != 0.10
    ):
        raise ValueError("T20.36e source spec drifted")


def _positive(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number <= 0:
        raise ValueError(f"T20.36e {label} must be positive")
    return number


def _nonnegative(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number < 0:
        raise ValueError(f"T20.36e {label} must be nonnegative")
    return number


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.36e {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.36e {label} must be finite")
    return number


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36e {label} is not a lowercase SHA-256")
    return value


def _commit(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36e {label} is not a full Git commit")
    return value
