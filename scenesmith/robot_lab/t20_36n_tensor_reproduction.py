"""Fail-closed contracts for T20.36n T20.35x tensor reproduction."""

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
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (
    RUNTIME_PREFLIGHT_PATH as SOURCE_RUNTIME_PREFLIGHT_PATH,
    TRAINING_PERMIT_PATH as SOURCE_TRAINING_PERMIT_PATH,
    verify_runtime_preflight as verify_source_runtime_preflight,
    verify_training_permit as verify_source_training_permit,
)
from scenesmith.robot_lab.t20_36l_frozen_consequence_gate import (
    JOINT_NAMES,
    RESULT_PATH as FROZEN_SCORE_PATH,
    SPEC_PATH as FROZEN_GATE_PATH,
)
from scenesmith.robot_lab.t20_36n_tensor_reproduction_authority import (
    EXPECTED_CHECKPOINT_IDENTITY,
    EXPECTED_FROZEN_GATE_IDENTITY,
    EXPECTED_FROZEN_SCORE_IDENTITY,
    EXPECTED_T20_35X_RESULT_IDENTITY,
    EXPECTED_T20_35X_RUN_IDENTITY,
    REPO_ROOT,
    load_verified_sources as load_authority_sources,
)
from scripts.robot_lab.run_t20_35x_physical_gate_joint_weighted_correction import (
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
)


TASK_ID = "T20.36n"
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36n_tensor_reproduction_preflight.json"
)
INFERENCE_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36n_tensor_reproduction_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_36n_tensor_reproduction_result.json"
)
RUN_ROOT = Path("outputs/robot_lab/t20_36n_tensor_reproduction_run_001")
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
TRACKED_ATTEMPT_PATH = Path(
    "configurations/robot_lab/t20_36n_tensor_reproduction_attempt.json"
)
TENSOR_PATH = Path("configurations/robot_lab/t20_36n_decoded_action_tensors.json")
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
FAILURE_PATH = RUN_ROOT / "failure.json"
FAILURE_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36n_tensor_reproduction_failure_result.json"
)
RUNTIME_SCHEMA_VERSION = "scenesmith.t20_36n_tensor_reproduction_preflight.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_36n_tensor_reproduction_permit.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_36n_tensor_reproduction_attempt.v1"
TENSOR_SCHEMA_VERSION = "scenesmith.t20_36n_decoded_action_tensors.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_36n_tensor_reproduction_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36n_tensor_reproduction_result.v1"
FAILURE_SCHEMA_VERSION = "scenesmith.t20_36n_tensor_reproduction_failure.v1"
FAILURE_RESULT_SCHEMA_VERSION = (
    "scenesmith.t20_36n_tensor_reproduction_failure_result.v1"
)
INFERENCE_SEEDS = (20260721, 20260722, 20260723, 20260724, 20260725)
EXPECTED_ACTION_HASHES = (
    "ab47fa1dd0631f72c7147cbc40e0588fa9161df8ed96a2d6382744a834968762",
    "daeb453986f1449bb8b9058ea2946e1ec9eb178ad51d930b26a8fb5bfd85cc02",
    "34a758673ce8e9cb484d56f367f99af5c1fac966b3e06f83896b7bee64f206c0",
    "8a89f1a9c248c5994d925e413d3961bf404c5f4cec7b77945a4dcf2294f3ba8a",
    "6b95263746dead2b582dba92bf8de6a10b63c4c416a7d1094b55aabe0a7809e1",
)
MINIMUM_FREE_DISK_BYTES = 2 * 1024 * 1024 * 1024
TARGET_HORIZON = 50
REACH_STOP_EXCLUSIVE = 32


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    authority_sources = load_authority_sources(repo_root=root)
    spec = authority_sources["t20_35x_spec"]
    run = authority_sources["t20_35x_run"]
    base_model_spec = authority_sources["base_model_spec"]
    source_runtime_preflight = load_strict_json(root / SOURCE_RUNTIME_PREFLIGHT_PATH)
    source_training_permit = load_strict_json(root / SOURCE_TRAINING_PERMIT_PATH)
    source_authority_identity = run["authority_decision_identity_sha256"]
    verify_source_runtime_preflight(
        source_runtime_preflight,
        spec=spec,
        authority_identity=source_authority_identity,
    )
    verify_source_training_permit(
        source_training_permit,
        spec=spec,
        authority_identity=source_authority_identity,
        runtime_preflight=source_runtime_preflight,
    )
    frozen_gate = authority_sources["frozen_gate"]
    frozen_score = authority_sources["frozen_score"]
    hashes = tuple(
        row.get("decoded_action_chunk_sha256")
        for row in run["decoded_action_chunks"]
    )
    if hashes != EXPECTED_ACTION_HASHES:
        raise ValueError("T20.36n source action hashes drifted")
    snapshot = base_model_spec["model_snapshot"]
    if (
        snapshot.get("revision") != spec["model"]["revision"]
        or snapshot.get("repo_id") != spec["model"]["repo_id"]
        or not isinstance(snapshot.get("files"), list)
    ):
        raise ValueError("T20.36n base-model snapshot source drifted")
    snapshot_tree = snapshot["files"]
    return {
        "checkpoint_identity_sha256": EXPECTED_CHECKPOINT_IDENTITY,
        "source_run_identity_sha256": EXPECTED_T20_35X_RUN_IDENTITY,
        "source_result_identity_sha256": EXPECTED_T20_35X_RESULT_IDENTITY,
        "frozen_gate_identity_sha256": EXPECTED_FROZEN_GATE_IDENTITY,
        "frozen_score_identity_sha256": EXPECTED_FROZEN_SCORE_IDENTITY,
        "checkpoint_tree": run["checkpoint_tree"],
        "source_runtime_preflight_identity_sha256": source_runtime_preflight[
            "identity_sha256"
        ],
        "source_training_permit_identity_sha256": source_training_permit[
            "identity_sha256"
        ],
        "lerobot_stack_identity_sha256": spec["lerobot_stack_identity_sha256"],
        "batch_evidence_identity_sha256": spec["dataset_action_chunk_sha256"],
        "required_dependency_versions": spec["required_dependency_versions"],
        "snapshot_revision": snapshot["revision"],
        "snapshot_tree": snapshot_tree,
        "snapshot_tree_identity_sha256": hashlib.sha256(
            canonical_json_bytes(snapshot_tree)
        ).hexdigest(),
        "source_run": run,
        "source_result": authority_sources["t20_35x_result"],
        "t20_35x_spec": spec,
        "frozen_gate": frozen_gate,
        "frozen_score": frozen_score,
        "source_runtime_preflight": source_runtime_preflight,
        "source_training_permit": source_training_permit,
    }


def build_runtime_preflight(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    python_major_minor: list[int],
    mps_available: bool,
    checkpoint_tree: list[dict[str, Any]],
    dependency_versions: dict[str, str],
    snapshot_revision: str,
    snapshot_tree: list[dict[str, Any]],
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
        "source_runtime_preflight_identity_sha256",
        "source_training_permit_identity_sha256",
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
        or dependency_versions != sources.get("required_dependency_versions")
        or snapshot_revision != sources.get("snapshot_revision")
        or snapshot_tree != sources.get("snapshot_tree")
        or isinstance(free_disk_bytes, bool)
        or not isinstance(free_disk_bytes, int)
        or free_disk_bytes < MINIMUM_FREE_DISK_BYTES
        or source_commit != remote_source_commit
        or attempt_exists is not False
        or result_exists is not False
    ):
        raise ValueError("T20.36n runtime preflight failed closed")
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
            "source_runtime_preflight_identity_sha256": sources[
                "source_runtime_preflight_identity_sha256"
            ],
            "source_training_permit_identity_sha256": sources[
                "source_training_permit_identity_sha256"
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
            "dependency_versions": dependency_versions,
            "offline_dependency_restore_only": True,
            "snapshot_revision": snapshot_revision,
            "snapshot_tree": snapshot_tree,
            "snapshot_tree_identity_sha256": hashlib.sha256(
                canonical_json_bytes(snapshot_tree)
            ).hexdigest(),
            "snapshot_files_hashed_without_tensor_deserialization": True,
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
    verify_signed_payload(payload, label="T20.36n runtime preflight")
    expected = build_runtime_preflight(
        sources=sources,
        authority_identity=authority_identity,
        python_major_minor=payload.get("python_major_minor"),
        mps_available=payload.get("mps_available"),
        checkpoint_tree=payload.get("checkpoint_tree"),
        dependency_versions=payload.get("dependency_versions"),
        snapshot_revision=payload.get("snapshot_revision"),
        snapshot_tree=payload.get("snapshot_tree"),
        free_disk_bytes=payload.get("free_disk_bytes"),
        source_commit=payload.get("source_commit"),
        remote_source_commit=payload.get("remote_source_commit"),
        attempt_exists=payload.get("attempt_exists"),
        result_exists=payload.get("result_exists"),
    )
    if payload != expected:
        raise ValueError("T20.36n runtime preflight drifted")


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
            "snapshot_revision": runtime_preflight["snapshot_revision"],
            "snapshot_tree_identity_sha256": runtime_preflight[
                "snapshot_tree_identity_sha256"
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
    verify_signed_payload(payload, label="T20.36n inference permit")
    expected = build_inference_permit(
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.36n inference permit drifted")


def build_attempt_marker(
    *, permit: dict[str, Any], authority_identity: str, source_commit: str
) -> dict[str, Any]:
    verify_signed_payload(permit, label="T20.36n inference permit")
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
        raise ValueError("T20.36n attempt permit drifted")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "source_checkpoint_identity_sha256": permit[
                "source_checkpoint_identity_sha256"
            ],
            "source_run_identity_sha256": permit["source_run_identity_sha256"],
            "frozen_gate_identity_sha256": permit["frozen_gate_identity_sha256"],
            "snapshot_revision": permit["snapshot_revision"],
            "snapshot_tree_identity_sha256": permit[
                "snapshot_tree_identity_sha256"
            ],
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
    verify_signed_payload(payload, label="T20.36n attempt marker")
    expected = build_attempt_marker(
        permit=permit,
        authority_identity=authority_identity,
        source_commit=payload.get("source_commit"),
    )
    if payload != expected:
        raise ValueError("T20.36n attempt marker drifted")


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
        raise ValueError("T20.36n frozen threshold matrix drifted")
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
                raise ValueError("T20.36n threshold must be finite and positive")
            threshold = float(threshold)
            if not math.isfinite(threshold) or threshold <= 0:
                raise ValueError("T20.36n threshold must be finite and positive")
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
    verify_signed_payload(attempt, label="T20.36n attempt marker")
    if len(rows) != len(INFERENCE_SEEDS):
        raise ValueError("T20.36n tensor row count drifted")
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
            raise ValueError("T20.36n reproduced tensor hash or repeat drifted")
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
    verify_signed_payload(tensor_artifact, label="T20.36n tensor artifact")
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
    retained_ratio = sources["source_result"][
        "final_to_source_gate_baseline_objective_ratio"
    ]
    objective_threshold = sources["frozen_gate"]["amended_gate_b_conjunction"][
        "maximum_objective_ratio"
    ]
    objective_pass = retained_ratio <= objective_threshold
    amended_pass = amended_pass and objective_pass
    uniform_gate_pass = all(
        row["maximum_absolute_error_rad"] <= 0.05 for row in score_rows
    ) and objective_pass
    return sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "authority_decision_identity_sha256": authority_identity,
            "inference_permit_identity_sha256": permit["identity_sha256"],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "tensor_artifact_identity_sha256": tensor_artifact["identity_sha256"],
            "tracked_tensor_artifact_path": str(TENSOR_PATH),
            "target_action_sha256": tensor_artifact["target_action_sha256"],
            "target_action": _matrix(target, label="run target tensor"),
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "snapshot_revision": permit["snapshot_revision"],
            "snapshot_tree_identity_sha256": permit[
                "snapshot_tree_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
            "retained_objective_ratio": retained_ratio,
            "retained_objective_ratio_threshold": objective_threshold,
            "retained_objective_ratio_passed": objective_pass,
            "all_expected_hashes_reproduced": True,
            "all_repeats_bit_identical": True,
            "score_rows": score_rows,
            "amended_gate_b_passed": amended_pass,
            "uniform_gate_b_passed": uniform_gate_pass,
            "decision": (
                "t20_35x_amended_gate_b_pass"
                if amended_pass
                else "t20_35x_amended_gate_b_fail"
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
    verify_signed_payload(run, label="T20.36n run summary")
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
            "authority_decision_identity_sha256": run[
                "authority_decision_identity_sha256"
            ],
            "inference_permit_identity_sha256": run[
                "inference_permit_identity_sha256"
            ],
            "attempt_identity_sha256": run["attempt_identity_sha256"],
            "tracked_attempt_path": str(TRACKED_ATTEMPT_PATH),
            "tensor_artifact_identity_sha256": run[
                "tensor_artifact_identity_sha256"
            ],
            "tracked_tensor_artifact_path": run["tracked_tensor_artifact_path"],
            "target_action_sha256": run["target_action_sha256"],
            "target_action": run["target_action"],
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "snapshot_revision": run["snapshot_revision"],
            "snapshot_tree_identity_sha256": run[
                "snapshot_tree_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
            "all_expected_hashes_reproduced": run[
                "all_expected_hashes_reproduced"
            ],
            "all_repeats_bit_identical": run["all_repeats_bit_identical"],
            "amended_gate_b_passed": passed,
            "uniform_gate_b_passed": run["uniform_gate_b_passed"],
            "score_summary": score_summary,
            "total_violation_count": sum(
                row["violation_count"] for row in score_summary
            ),
            "decision": (
                "route_separate_gate_c_authority_request"
                if passed
                else "complete_three_candidate_comparison_negative"
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
    verify_signed_payload(payload, label="T20.36n tensor artifact")
    expected = build_tensor_artifact(
        attempt=attempt,
        rows=payload.get("rows"),
        target=target,
    )
    if payload != expected:
        raise ValueError("T20.36n tensor artifact drifted")


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
    verify_signed_payload(payload, label="T20.36n run summary")
    expected = build_run_summary(
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        target=target,
    )
    if payload != expected:
        raise ValueError("T20.36n run summary drifted")


def verify_result(
    payload: dict[str, Any], *, sources: dict[str, Any], run: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36n result")
    expected = build_result(sources=sources, run=run)
    if payload != expected:
        raise ValueError("T20.36n result drifted")


def verify_tracked_result(
    *,
    attempt: dict[str, Any],
    tensor_artifact: dict[str, Any],
    result: dict[str, Any],
    sources: dict[str, Any],
) -> None:
    """Rescore tracked tensors without ignored attempt/run artifacts."""
    verify_signed_payload(attempt, label="T20.36n tracked attempt")
    verify_signed_payload(tensor_artifact, label="T20.36n tracked tensor artifact")
    verify_signed_payload(result, label="T20.36n tracked result")
    target = _matrix(result.get("target_action"), label="tracked result target")
    target_sha256 = hashlib.sha256(canonical_json_bytes(target)).hexdigest()
    if (
        tensor_artifact.get("schema_version") != TENSOR_SCHEMA_VERSION
        or tensor_artifact.get("task_id") != TASK_ID
        or result.get("schema_version") != RESULT_SCHEMA_VERSION
        or result.get("task_id") != TASK_ID
        or result.get("tracked_tensor_artifact_path") != str(TENSOR_PATH)
        or result.get("tracked_attempt_path") != str(TRACKED_ATTEMPT_PATH)
        or result.get("attempt_identity_sha256") != attempt.get("identity_sha256")
        or tensor_artifact.get("attempt_identity_sha256")
        != attempt.get("identity_sha256")
        or result.get("inference_permit_identity_sha256")
        != attempt.get("inference_permit_identity_sha256")
        or result.get("authority_decision_identity_sha256")
        != attempt.get("authority_decision_identity_sha256")
        or attempt.get("task_id") != TASK_ID
        or attempt.get("attempt_number") != 1
        or attempt.get("created_before_checkpoint_tensor_read") is not True
        or result.get("tensor_artifact_identity_sha256")
        != tensor_artifact.get("identity_sha256")
        or result.get("target_action_sha256") != target_sha256
        or tensor_artifact.get("target_action_sha256") != target_sha256
        or result.get("source_run_identity_sha256")
        != sources["source_run_identity_sha256"]
        or result.get("source_result_identity_sha256")
        != sources["source_result_identity_sha256"]
        or result.get("source_checkpoint_identity_sha256")
        != sources["checkpoint_identity_sha256"]
        or result.get("frozen_gate_identity_sha256")
        != sources["frozen_gate_identity_sha256"]
        or result.get("snapshot_revision") != sources["snapshot_revision"]
        or result.get("snapshot_tree_identity_sha256")
        != sources["snapshot_tree_identity_sha256"]
        or tensor_artifact.get("tensor_count") != 10
        or tensor_artifact.get("shape_per_tensor")
        != [TARGET_HORIZON, len(JOINT_NAMES)]
    ):
        raise ValueError("T20.36n tracked result lineage drifted")
    rows = tensor_artifact.get("rows")
    if not isinstance(rows, list) or len(rows) != len(INFERENCE_SEEDS):
        raise ValueError("T20.36n tracked tensor seed coverage drifted")
    thresholds = sources["frozen_gate"]["amended_gate_b_conjunction"][
        "phase_joint_maximum_error_rad"
    ]
    summaries = []
    for index, (seed, expected_hash, row) in enumerate(
        zip(INFERENCE_SEEDS, EXPECTED_ACTION_HASHES, rows, strict=True)
    ):
        first = _matrix(row.get("first"), label="tracked first tensor")
        second = _matrix(row.get("second"), label="tracked second tensor")
        first_hash = hashlib.sha256(canonical_json_bytes(first)).hexdigest()
        second_hash = hashlib.sha256(canonical_json_bytes(second)).hexdigest()
        if (
            row.get("seed_index") != index
            or row.get("inference_seed") != seed
            or first_hash != expected_hash
            or second_hash != expected_hash
            or first != second
        ):
            raise ValueError("T20.36n tracked tensor hash or repeat drifted")
        score = score_action_tensor(
            tensor=first,
            target=target,
            thresholds=thresholds,
        )
        summaries.append(
            {
                "seed_index": index,
                "inference_seed": seed,
                "action_chunk_sha256": first_hash,
                "passed": score["passed"],
                "maximum_absolute_error_rad": score[
                    "maximum_absolute_error_rad"
                ],
                "maximum_threshold_ratio": score["maximum_threshold_ratio"],
                "violation_count": score["violation_count"],
            }
        )
    objective_pass = (
        sources["source_result"]["final_to_source_gate_baseline_objective_ratio"]
        <= sources["frozen_gate"]["amended_gate_b_conjunction"][
            "maximum_objective_ratio"
        ]
    )
    amended_pass = objective_pass and all(row["passed"] for row in summaries)
    uniform_pass = objective_pass and all(
        row["maximum_absolute_error_rad"] <= 0.05 for row in summaries
    )
    total = sum(row["violation_count"] for row in summaries)
    if (
        summaries != result.get("score_summary")
        or total != result.get("total_violation_count")
        or amended_pass is not result.get("amended_gate_b_passed")
        or uniform_pass is not result.get("uniform_gate_b_passed")
        or result.get("gate_c_route_open") is not amended_pass
        or result.get("gate_c_authorized") is not False
        or result.get("optimizer_created") is not False
        or result.get("optimizer_training") is not False
        or result.get("physical_actuation") is not False
        or result.get("external_compute_started") is not False
        or result.get("brev_compute_started") is not False
    ):
        raise ValueError("T20.36n tracked tensor rescore drifted")


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
        raise ValueError("T20.36n failure state must be boolean")
    if not all(isinstance(value, str) and value.strip() for value in (
        failure_stage,
        error_type,
        error_message,
    )):
        raise ValueError("T20.36n failure details must be nonblank")
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
    verify_signed_payload(failure, label="T20.36n failure")
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
        raise ValueError(f"T20.36n {label} must be 50x6")
    result = []
    for row in value:
        if not isinstance(row, list) or len(row) != len(JOINT_NAMES):
            raise ValueError(f"T20.36n {label} must be 50x6")
        normalized = []
        for item in row:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError(f"T20.36n {label} must be finite")
            numeric = float(item)
            if not math.isfinite(numeric):
                raise ValueError(f"T20.36n {label} must be finite")
            normalized.append(numeric)
        result.append(normalized)
    return result


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36n {label} must be sha256")
    return value


def _commit(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36n {label} must be a full commit")
    return value
