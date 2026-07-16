"""Fail-closed preflight and permit for the T20.36o X baseline capture."""

from __future__ import annotations

import base64
import hashlib
import math
import struct

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36o_baseline_inference_authority import (
    REPO_ROOT,
    load_verified_sources as load_authority_sources,
)
from scenesmith.robot_lab.so101_processor import JOINT_NAMES


TASK_ID = "T20.36o"
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_capture_preflight.json"
)
BASELINE_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_capture_permit.json"
)
RUN_ROOT = Path("outputs/robot_lab/t20_36o_baseline_capture_run_001")
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
TRACKED_ATTEMPT_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_capture_attempt.json"
)
TENSOR_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_decoded_action_tensors.json"
)
TRAJECTORY_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_denoise_trajectories.json"
)
RESULT_PATH = Path("configurations/robot_lab/t20_36o_baseline_capture_result.json")
FAILURE_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_capture_failure_result.json"
)
RUNTIME_SCHEMA_VERSION = "scenesmith.t20_36o_baseline_capture_preflight.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_36o_baseline_capture_permit.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_36o_baseline_capture_attempt.v1"
TENSOR_SCHEMA_VERSION = "scenesmith.t20_36o_baseline_decoded_action_tensors.v1"
TRAJECTORY_SCHEMA_VERSION = (
    "scenesmith.t20_36o_baseline_denoise_trajectories.v1"
)
RUN_SCHEMA_VERSION = "scenesmith.t20_36o_baseline_capture_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36o_baseline_capture_result.v1"
FAILURE_SCHEMA_VERSION = "scenesmith.t20_36o_baseline_capture_failure.v1"
FAILURE_RESULT_SCHEMA_VERSION = (
    "scenesmith.t20_36o_baseline_capture_failure_result.v1"
)
CHUNK_START_FRAMES = (0, 50, 100, 150, 200)
EXECUTED_LENGTHS = (50, 50, 50, 50, 44)
INFERENCE_SEEDS = (20260721, 20260722, 20260723, 20260724, 20260725)
REPEATS_PER_START_SEED = 2
DENOISE_STEP_COUNT = 10
DECODED_CHUNK_COUNT = (
    len(CHUNK_START_FRAMES) * len(INFERENCE_SEEDS) * REPEATS_PER_START_SEED
)
DENOISE_STEP_RECORD_COUNT = DECODED_CHUNK_COUNT * DENOISE_STEP_COUNT
CONSTRUCTION_SEED = 20260718
MINIMUM_FREE_DISK_BYTES = 2 * 1024 * 1024 * 1024
TARGET_HORIZON = 50
ACTIVE_ACTION_DIMENSIONS = len(JOINT_NAMES)
MAXIMUM_ACTION_DIMENSIONS = 32
REACH_STOP_EXCLUSIVE = 32
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
FAILURE_PATH = RUN_ROOT / "failure.json"


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    authority_sources = load_authority_sources(repo_root=repo_root)
    bridge = authority_sources["bridge_spec"]
    x_runtime = authority_sources["x_runtime"]
    result = authority_sources["x_result"]
    starts = bridge["execution_contract"]["chunk_start_frames"]
    lengths = bridge["execution_contract"]["executed_lengths"]
    if starts != list(CHUNK_START_FRAMES) or lengths != list(EXECUTED_LENGTHS):
        raise ValueError("T20.36o baseline window contract drifted")
    probe_rows = bridge["probe_contract"]["probe_seed_by_start"]
    expected_probe_rows = [
        {"start_frame": start, "inference_seeds": list(INFERENCE_SEEDS)}
        for start in CHUNK_START_FRAMES
    ]
    if probe_rows != expected_probe_rows:
        raise ValueError("T20.36o baseline probe matrix drifted")
    target_bindings = [
        {
            "start_frame": row["start_frame"],
            "executed_length": row["executed_length"],
            "padded_target_action_sha256": row[
                "padded_target_action_sha256"
            ],
            "executed_mask_sha256": row["executed_mask_sha256"],
            "start_observation_identity_sha256": row["start_observation"][
                "identity_sha256"
            ],
            "dataset_observation_identity_sha256": row["dataset_observation"][
                "identity_sha256"
            ],
        }
        for row in bridge["source_windows"]
    ]
    start_zero_hashes = [
        row["action_chunk_sha256"] for row in result["score_summary"]
    ]
    if len(start_zero_hashes) != len(INFERENCE_SEEDS):
        raise ValueError("T20.36o start-zero hash coverage drifted")
    return {
        "bridge_spec_identity_sha256": bridge["identity_sha256"],
        "checkpoint_identity_sha256": x_runtime["checkpoint_identity_sha256"],
        "source_run_identity_sha256": x_runtime["source_run_identity_sha256"],
        "source_result_identity_sha256": x_runtime[
            "source_result_identity_sha256"
        ],
        "frozen_gate_identity_sha256": x_runtime["frozen_gate_identity_sha256"],
        "lerobot_stack_identity_sha256": x_runtime[
            "lerobot_stack_identity_sha256"
        ],
        "required_dependency_versions": x_runtime["required_dependency_versions"],
        "checkpoint_tree": x_runtime["checkpoint_tree"],
        "snapshot_revision": x_runtime["snapshot_revision"],
        "snapshot_tree": x_runtime["snapshot_tree"],
        "probe_seed_by_start": probe_rows,
        "base_noise_sha256_by_seed": bridge["probe_contract"][
            "base_noise_sha256_by_seed"
        ],
        "target_bindings": target_bindings,
        "expected_start_zero_hashes": start_zero_hashes,
        "bridge_spec": bridge,
        "x_runtime": x_runtime,
        "x_result": result,
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
    for name in (
        "bridge_spec_identity_sha256",
        "checkpoint_identity_sha256",
        "source_run_identity_sha256",
        "source_result_identity_sha256",
        "frozen_gate_identity_sha256",
        "lerobot_stack_identity_sha256",
    ):
        _sha(sources.get(name), name)
    _sha(authority_identity, "authority identity")
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
        raise ValueError("T20.36o baseline runtime preflight failed closed")
    return sign_payload(
        {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "bridge_spec_identity_sha256": sources[
                "bridge_spec_identity_sha256"
            ],
            "authority_decision_identity_sha256": authority_identity,
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
            "lerobot_stack_identity_sha256": sources[
                "lerobot_stack_identity_sha256"
            ],
            "python_major_minor": python_major_minor,
            "mps_available": True,
            "checkpoint_tree": checkpoint_tree,
            "dependency_versions": dependency_versions,
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
    verify_signed_payload(payload, label="T20.36o baseline runtime preflight")
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
        raise ValueError("T20.36o baseline runtime preflight drifted")


def build_baseline_permit(
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
            "bridge_spec_identity_sha256": sources[
                "bridge_spec_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": sources[
                "checkpoint_identity_sha256"
            ],
            "source_run_identity_sha256": sources["source_run_identity_sha256"],
            "source_result_identity_sha256": sources[
                "source_result_identity_sha256"
            ],
            "frozen_gate_identity_sha256": sources["frozen_gate_identity_sha256"],
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
                "simulation_model_construction_once",
                "simulation_model_load_once",
                "simulation_model_inference_exact_registered_probe_matrix",
                "persist_fifty_decoded_action_chunks",
                "persist_five_hundred_denoise_step_records",
                "score_frozen_bridge_acceptance",
            ],
            "chunk_start_frames": list(CHUNK_START_FRAMES),
            "executed_lengths": list(EXECUTED_LENGTHS),
            "probe_seed_by_start": sources["probe_seed_by_start"],
            "inference_seeds": list(INFERENCE_SEEDS),
            "base_noise_sha256_by_seed": sources[
                "base_noise_sha256_by_seed"
            ],
            "repeats_per_start_seed": REPEATS_PER_START_SEED,
            "denoise_step_count": DENOISE_STEP_COUNT,
            "decoded_chunk_count": DECODED_CHUNK_COUNT,
            "denoise_step_record_count": DENOISE_STEP_RECORD_COUNT,
            "expected_start_zero_hashes": sources[
                "expected_start_zero_hashes"
            ],
            "target_bindings": sources["target_bindings"],
            "construction_seed": CONSTRUCTION_SEED,
            "attempt_marker_path": ATTEMPT_PATH.as_posix(),
            "tensor_artifact_path": TENSOR_PATH.as_posix(),
            "trajectory_artifact_path": TRAJECTORY_PATH.as_posix(),
            "marker_must_precede_checkpoint_tensor_read": True,
            "base_noise_hash_must_precede_each_decode": True,
            "start_zero_hashes_must_match_before_new_evidence_is_accepted": True,
            "unexecuted_tail_must_remain_masked": True,
            "local_execution_eligible_after_remote_preservation": True,
            "optimizer_created": False,
            "optimizer_training": False,
            "training_authorized": False,
            "retry_authorized": False,
            "new_start": False,
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


def verify_baseline_permit(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36o baseline permit")
    expected = build_baseline_permit(
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.36o baseline permit drifted")


def build_attempt_marker(
    *, permit: dict[str, Any], authority_identity: str, source_commit: str
) -> dict[str, Any]:
    verify_signed_payload(permit, label="T20.36o baseline permit")
    _sha(authority_identity, "authority identity")
    _commit(source_commit, "source commit")
    if (
        permit.get("authority_decision_identity_sha256") != authority_identity
        or permit.get("authorized_attempt_count") != 1
        or permit.get("chunk_start_frames") != list(CHUNK_START_FRAMES)
        or permit.get("inference_seeds") != list(INFERENCE_SEEDS)
        or permit.get("repeats_per_start_seed") != REPEATS_PER_START_SEED
        or permit.get("marker_must_precede_checkpoint_tensor_read") is not True
        or permit.get("optimizer_created") is not False
    ):
        raise ValueError("T20.36o baseline attempt permit drifted")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "bridge_spec_identity_sha256": permit[
                "bridge_spec_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": permit[
                "source_checkpoint_identity_sha256"
            ],
            "authority_decision_identity_sha256": authority_identity,
            "baseline_permit_identity_sha256": permit["identity_sha256"],
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
            "trajectory_artifact_written": False,
        }
    )


def verify_attempt_marker(
    payload: dict[str, Any], *, permit: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.36o baseline attempt")
    expected = build_attempt_marker(
        permit=permit,
        authority_identity=authority_identity,
        source_commit=payload.get("source_commit"),
    )
    if payload != expected:
        raise ValueError("T20.36o baseline attempt marker drifted")


def score_action_tensor(
    *,
    tensor: list[list[float]],
    target: list[list[float]],
    executed_mask: list[bool],
    thresholds: dict[str, dict[str, float]],
) -> dict[str, Any]:
    predicted = _matrix(
        tensor,
        rows=TARGET_HORIZON,
        columns=ACTIVE_ACTION_DIMENSIONS,
        label="decoded action tensor",
    )
    expected = _matrix(
        target,
        rows=TARGET_HORIZON,
        columns=ACTIVE_ACTION_DIMENSIONS,
        label="target action tensor",
    )
    mask = _executed_mask(executed_mask)
    if set(thresholds) != {"reach", "grasp"} or any(
        set(thresholds[group]) != set(JOINT_NAMES) for group in thresholds
    ):
        raise ValueError("T20.36o frozen threshold matrix drifted")
    violations: list[dict[str, Any]] = []
    errors: list[float] = []
    normalized_errors: list[float] = []
    for timestep, (predicted_row, expected_row, executed) in enumerate(
        zip(predicted, expected, mask, strict=True)
    ):
        if not executed:
            continue
        phase_group = "reach" if timestep < REACH_STOP_EXCLUSIVE else "grasp"
        for joint_index, joint_name in enumerate(JOINT_NAMES):
            threshold = _finite_positive(
                thresholds[phase_group][joint_name],
                label="frozen joint threshold",
            )
            error = abs(predicted_row[joint_index] - expected_row[joint_index])
            errors.append(error)
            normalized_errors.append(error / threshold)
            if error > threshold:
                violations.append(
                    {
                        "timestep": timestep,
                        "phase_group": phase_group,
                        "joint_name": joint_name,
                        "predicted_action_rad": predicted_row[joint_index],
                        "target_action_rad": expected_row[joint_index],
                        "absolute_error_rad": error,
                        "frozen_threshold_rad": threshold,
                        "excess_rad": error - threshold,
                    }
                )
    if not errors:
        raise ValueError("T20.36o action score has no executed cells")
    return {
        "passed": not violations,
        "executed_timestep_count": sum(mask),
        "executed_cell_count": len(errors),
        "maximum_absolute_error_rad": max(errors),
        "mean_absolute_error_rad": sum(errors) / len(errors),
        "maximum_threshold_ratio": max(normalized_errors),
        "violation_count": len(violations),
        "violations": violations,
    }


def build_tensor_artifact(
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    authority_identity = attempt.get("authority_decision_identity_sha256")
    verify_attempt_marker(
        attempt,
        permit=permit,
        authority_identity=authority_identity,
    )
    expected_keys = _probe_keys()
    if not isinstance(rows, list) or len(rows) != len(expected_keys):
        raise ValueError("T20.36o decoded tensor coverage drifted")
    expected_start_zero = permit.get("expected_start_zero_hashes")
    if not isinstance(expected_start_zero, list) or len(expected_start_zero) != len(
        INFERENCE_SEEDS
    ):
        raise ValueError("T20.36o start-zero expected hash coverage drifted")
    normalized: list[dict[str, Any]] = []
    pair_values: dict[tuple[int, int], list[list[float]]] = {}
    for expected_key, row in zip(expected_keys, rows, strict=True):
        if any(row.get(name) != value for name, value in expected_key.items()):
            raise ValueError("T20.36o decoded tensor probe order drifted")
        tensor = _matrix(
            row.get("decoded_action_chunk"),
            rows=TARGET_HORIZON,
            columns=ACTIVE_ACTION_DIMENSIONS,
            label="decoded action tensor",
        )
        digest = hashlib.sha256(canonical_json_bytes(tensor)).hexdigest()
        if (
            expected_key["start_frame"] == 0
            and digest != expected_start_zero[expected_key["seed_index"]]
        ):
            raise ValueError("T20.36o start-zero action hash failed reproduction")
        pair_key = (expected_key["start_index"], expected_key["seed_index"])
        if expected_key["repeat_index"] == 0:
            pair_values[pair_key] = tensor
        elif pair_values.get(pair_key) != tensor:
            raise ValueError("T20.36o decoded action repeat drifted")
        normalized.append(
            {
                **expected_key,
                "decoded_action_chunk_sha256": digest,
                "decoded_action_chunk": tensor,
            }
        )
    return sign_payload(
        {
            "schema_version": TENSOR_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "attempt_identity_sha256": attempt["identity_sha256"],
            "baseline_permit_identity_sha256": permit["identity_sha256"],
            "bridge_spec_identity_sha256": permit[
                "bridge_spec_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": permit[
                "source_checkpoint_identity_sha256"
            ],
            "shape_per_tensor": [TARGET_HORIZON, ACTIVE_ACTION_DIMENSIONS],
            "tensor_count": len(normalized),
            "rows": normalized,
            "all_start_zero_hashes_reproduced": True,
            "all_repeats_bit_identical": True,
            **_false_execution_authority(),
        }
    )


def verify_tensor_artifact(
    payload: dict[str, Any], *, attempt: dict[str, Any], permit: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36o decoded tensor artifact")
    expected = build_tensor_artifact(
        attempt=attempt,
        permit=permit,
        rows=payload.get("rows"),
    )
    if payload != expected:
        raise ValueError("T20.36o decoded tensor artifact drifted")


def build_trajectory_artifact(
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    tensor_artifact: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_tensor_artifact(
        tensor_artifact,
        attempt=attempt,
        permit=permit,
    )
    expected_keys = _probe_keys()
    if not isinstance(rows, list) or len(rows) != len(expected_keys):
        raise ValueError("T20.36o denoise trajectory coverage drifted")
    tensor_rows = tensor_artifact["rows"]
    normalized: list[dict[str, Any]] = []
    pair_values: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for index, (expected_key, row, tensor_row) in enumerate(
        zip(expected_keys, rows, tensor_rows, strict=True)
    ):
        if any(row.get(name) != value for name, value in expected_key.items()):
            raise ValueError("T20.36o denoise trajectory probe order drifted")
        base_noise_sha256 = _sha(
            row.get("base_noise_sha256"), "base noise identity"
        )
        if base_noise_sha256 != permit["base_noise_sha256_by_seed"][
            expected_key["seed_index"]
        ]:
            raise ValueError("T20.36o denoise base noise drifted")
        if row.get("decoded_action_chunk_sha256") != tensor_row.get(
            "decoded_action_chunk_sha256"
        ):
            raise ValueError("T20.36o trajectory endpoint linkage drifted")
        steps = _trajectory_steps(row.get("steps"))
        path_sha256 = hashlib.sha256(canonical_json_bytes(steps)).hexdigest()
        pair_key = (expected_key["start_index"], expected_key["seed_index"])
        if expected_key["repeat_index"] == 0:
            pair_values[pair_key] = steps
        elif pair_values.get(pair_key) != steps:
            raise ValueError("T20.36o denoise trajectory repeat drifted")
        normalized.append(
            {
                **expected_key,
                "trajectory_index": index,
                "base_noise_sha256": base_noise_sha256,
                "decoded_action_chunk_sha256": tensor_row[
                    "decoded_action_chunk_sha256"
                ],
                "denoise_path_sha256": path_sha256,
                "steps": steps,
            }
        )
    return sign_payload(
        {
            "schema_version": TRAJECTORY_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "attempt_identity_sha256": attempt["identity_sha256"],
            "baseline_permit_identity_sha256": permit["identity_sha256"],
            "tensor_artifact_identity_sha256": tensor_artifact[
                "identity_sha256"
            ],
            "state_shape_per_step": [
                TARGET_HORIZON,
                MAXIMUM_ACTION_DIMENSIONS,
            ],
            "velocity_shape_per_step": [
                TARGET_HORIZON,
                MAXIMUM_ACTION_DIMENSIONS,
            ],
            "matrix_encoding": "base64_float32_little_endian_c_order",
            "trajectory_count": len(normalized),
            "denoise_step_record_count": len(normalized) * DENOISE_STEP_COUNT,
            "rows": normalized,
            "all_repeats_bit_identical": True,
            **_false_execution_authority(),
        }
    )


def verify_trajectory_artifact(
    payload: dict[str, Any],
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    tensor_artifact: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36o denoise trajectory artifact")
    expected = build_trajectory_artifact(
        attempt=attempt,
        permit=permit,
        tensor_artifact=tensor_artifact,
        rows=payload.get("rows"),
    )
    if payload != expected:
        raise ValueError("T20.36o denoise trajectory artifact drifted")


def build_run_summary(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    permit: dict[str, Any],
    attempt: dict[str, Any],
    tensor_artifact: dict[str, Any],
    trajectory_artifact: dict[str, Any],
) -> dict[str, Any]:
    verify_attempt_marker(
        attempt,
        permit=permit,
        authority_identity=authority_identity,
    )
    verify_tensor_artifact(
        tensor_artifact,
        attempt=attempt,
        permit=permit,
    )
    verify_trajectory_artifact(
        trajectory_artifact,
        attempt=attempt,
        permit=permit,
        tensor_artifact=tensor_artifact,
    )
    bridge = sources.get("bridge_spec")
    if (
        not isinstance(bridge, dict)
        or bridge.get("identity_sha256")
        != permit.get("bridge_spec_identity_sha256")
        or permit.get("authority_decision_identity_sha256")
        != authority_identity
    ):
        raise ValueError("T20.36o run source lineage drifted")
    windows = {
        row["start_frame"]: row for row in bridge.get("source_windows", [])
    }
    if list(windows) != list(CHUNK_START_FRAMES):
        raise ValueError("T20.36o run source window coverage drifted")
    thresholds = bridge["acceptance"]["phase_joint_maximum_error_rad"]
    tensor_rows = tensor_artifact["rows"]
    trajectory_rows = trajectory_artifact["rows"]
    score_rows = []
    for probe_index in range(len(CHUNK_START_FRAMES) * len(INFERENCE_SEEDS)):
        first_index = probe_index * REPEATS_PER_START_SEED
        second_index = first_index + 1
        first = tensor_rows[first_index]
        second = tensor_rows[second_index]
        first_path = trajectory_rows[first_index]
        second_path = trajectory_rows[second_index]
        window = windows[first["start_frame"]]
        score = score_action_tensor(
            tensor=first["decoded_action_chunk"],
            target=window["padded_target_action_mujoco_rad"],
            executed_mask=window["executed_mask"],
            thresholds=thresholds,
        )
        score_rows.append(
            {
                "probe_index": probe_index,
                "start_index": first["start_index"],
                "start_frame": first["start_frame"],
                "executed_length": first["executed_length"],
                "seed_index": first["seed_index"],
                "inference_seed": first["inference_seed"],
                "first_action_chunk_sha256": first[
                    "decoded_action_chunk_sha256"
                ],
                "second_action_chunk_sha256": second[
                    "decoded_action_chunk_sha256"
                ],
                "first_denoise_path_sha256": first_path[
                    "denoise_path_sha256"
                ],
                "second_denoise_path_sha256": second_path[
                    "denoise_path_sha256"
                ],
                "target_action_sha256": window[
                    "padded_target_action_sha256"
                ],
                "executed_mask_sha256": window["executed_mask_sha256"],
                **score,
            }
        )
    source_result = sources["x_runtime"]["source_result"]
    objective_ratio = _finite_nonnegative(
        source_result.get("final_to_source_gate_baseline_objective_ratio"),
        label="retained source objective ratio",
    )
    objective_threshold = _finite_positive(
        bridge["acceptance"]["maximum_source_batch_objective_ratio"],
        label="retained source objective threshold",
    )
    objective_passed = objective_ratio <= objective_threshold
    amended_passed = objective_passed and all(row["passed"] for row in score_rows)
    uniform_threshold = _finite_positive(
        bridge["acceptance"][
            "strict_uniform_maximum_absolute_error_rad_report_only"
        ],
        label="uniform report threshold",
    )
    uniform_passed = objective_passed and all(
        row["maximum_absolute_error_rad"] <= uniform_threshold
        for row in score_rows
    )
    return sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "authority_decision_identity_sha256": authority_identity,
            "baseline_permit_identity_sha256": permit["identity_sha256"],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "bridge_spec_identity_sha256": bridge["identity_sha256"],
            "source_checkpoint_identity_sha256": permit[
                "source_checkpoint_identity_sha256"
            ],
            "source_run_identity_sha256": permit["source_run_identity_sha256"],
            "source_result_identity_sha256": permit[
                "source_result_identity_sha256"
            ],
            "frozen_gate_identity_sha256": permit[
                "frozen_gate_identity_sha256"
            ],
            "snapshot_revision": permit["snapshot_revision"],
            "snapshot_tree_identity_sha256": permit[
                "snapshot_tree_identity_sha256"
            ],
            "tensor_artifact_identity_sha256": tensor_artifact[
                "identity_sha256"
            ],
            "tracked_tensor_artifact_path": TENSOR_PATH.as_posix(),
            "trajectory_artifact_identity_sha256": trajectory_artifact[
                "identity_sha256"
            ],
            "tracked_trajectory_artifact_path": TRAJECTORY_PATH.as_posix(),
            "decoded_chunk_count": tensor_artifact["tensor_count"],
            "denoise_step_record_count": trajectory_artifact[
                "denoise_step_record_count"
            ],
            "all_start_zero_hashes_reproduced": tensor_artifact[
                "all_start_zero_hashes_reproduced"
            ],
            "all_decoded_repeats_bit_identical": tensor_artifact[
                "all_repeats_bit_identical"
            ],
            "all_denoise_repeats_bit_identical": trajectory_artifact[
                "all_repeats_bit_identical"
            ],
            "unexecuted_tail_scored": False,
            "retained_source_objective_ratio": objective_ratio,
            "retained_source_objective_ratio_threshold": objective_threshold,
            "retained_source_objective_ratio_passed": objective_passed,
            "score_rows": score_rows,
            "amended_bridge_gate_passed": amended_passed,
            "strict_uniform_report_only_passed": uniform_passed,
            "decision": (
                "route_separate_gate_c_episode_0_authority_request"
                if amended_passed
                else "retain_trajectories_compose_separate_optimizer_authority"
            ),
            "checkpoint_tensor_read": True,
            "model_constructed": True,
            "model_loaded": True,
            "model_inference": True,
            "gate_c_request_eligible": amended_passed,
            "gate_c_route_open_under_owner_direction": True,
            **_false_execution_authority(),
        }
    )


def verify_run_summary(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
    permit: dict[str, Any],
    attempt: dict[str, Any],
    tensor_artifact: dict[str, Any],
    trajectory_artifact: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36o baseline run summary")
    expected = build_run_summary(
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        trajectory_artifact=trajectory_artifact,
    )
    if payload != expected:
        raise ValueError("T20.36o baseline run summary drifted")


def build_result(*, run: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(run, label="T20.36o baseline run summary")
    summaries = [
        {
            "probe_index": row["probe_index"],
            "start_frame": row["start_frame"],
            "executed_length": row["executed_length"],
            "inference_seed": row["inference_seed"],
            "action_chunk_sha256": row["first_action_chunk_sha256"],
            "denoise_path_sha256": row["first_denoise_path_sha256"],
            "passed": row["passed"],
            "maximum_absolute_error_rad": row[
                "maximum_absolute_error_rad"
            ],
            "maximum_threshold_ratio": row["maximum_threshold_ratio"],
            "violation_count": row["violation_count"],
            "violations": row["violations"],
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
            "baseline_permit_identity_sha256": run[
                "baseline_permit_identity_sha256"
            ],
            "attempt_identity_sha256": run["attempt_identity_sha256"],
            "tracked_attempt_path": TRACKED_ATTEMPT_PATH.as_posix(),
            "bridge_spec_identity_sha256": run[
                "bridge_spec_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": run[
                "source_checkpoint_identity_sha256"
            ],
            "source_run_identity_sha256": run["source_run_identity_sha256"],
            "source_result_identity_sha256": run[
                "source_result_identity_sha256"
            ],
            "frozen_gate_identity_sha256": run[
                "frozen_gate_identity_sha256"
            ],
            "snapshot_revision": run["snapshot_revision"],
            "snapshot_tree_identity_sha256": run[
                "snapshot_tree_identity_sha256"
            ],
            "tensor_artifact_identity_sha256": run[
                "tensor_artifact_identity_sha256"
            ],
            "tracked_tensor_artifact_path": run[
                "tracked_tensor_artifact_path"
            ],
            "trajectory_artifact_identity_sha256": run[
                "trajectory_artifact_identity_sha256"
            ],
            "tracked_trajectory_artifact_path": run[
                "tracked_trajectory_artifact_path"
            ],
            "decoded_chunk_count": run["decoded_chunk_count"],
            "denoise_step_record_count": run["denoise_step_record_count"],
            "all_start_zero_hashes_reproduced": run[
                "all_start_zero_hashes_reproduced"
            ],
            "all_decoded_repeats_bit_identical": run[
                "all_decoded_repeats_bit_identical"
            ],
            "all_denoise_repeats_bit_identical": run[
                "all_denoise_repeats_bit_identical"
            ],
            "unexecuted_tail_scored": False,
            "retained_source_objective_ratio": run[
                "retained_source_objective_ratio"
            ],
            "retained_source_objective_ratio_threshold": run[
                "retained_source_objective_ratio_threshold"
            ],
            "retained_source_objective_ratio_passed": run[
                "retained_source_objective_ratio_passed"
            ],
            "score_summary": summaries,
            "total_violation_count": sum(
                row["violation_count"] for row in summaries
            ),
            "amended_bridge_gate_passed": run[
                "amended_bridge_gate_passed"
            ],
            "strict_uniform_report_only_passed": run[
                "strict_uniform_report_only_passed"
            ],
            "decision": run["decision"],
            "gate_c_request_eligible": run["gate_c_request_eligible"],
            "gate_c_route_open_under_owner_direction": True,
            **_false_execution_authority(),
        }
    )


def verify_result(payload: dict[str, Any], *, run: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36o baseline result")
    if payload != build_result(run=run):
        raise ValueError("T20.36o baseline result drifted")


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
    trajectory_artifact_written: bool,
) -> dict[str, Any]:
    booleans = (
        checkpoint_tensor_read,
        model_constructed,
        model_loaded,
        model_inference,
        tensor_artifact_written,
        trajectory_artifact_written,
    )
    if not all(isinstance(value, bool) for value in booleans):
        raise ValueError("T20.36o failure state must be boolean")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (failure_stage, error_type, error_message)
    ):
        raise ValueError("T20.36o failure details must be nonblank")
    return sign_payload(
        {
            "schema_version": FAILURE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "baseline_permit_identity_sha256": permit["identity_sha256"],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "failure_stage": failure_stage,
            "error_type": error_type,
            "error_message": error_message,
            "checkpoint_tensor_read": checkpoint_tensor_read,
            "model_constructed": model_constructed,
            "model_loaded": model_loaded,
            "model_inference": model_inference,
            "tensor_artifact_written": tensor_artifact_written,
            "trajectory_artifact_written": trajectory_artifact_written,
            **_false_execution_authority(),
        }
    )


def build_failure_result(
    *, sources: dict[str, Any], failure: dict[str, Any]
) -> dict[str, Any]:
    verify_signed_payload(failure, label="T20.36o baseline failure")
    return sign_payload(
        {
            "schema_version": FAILURE_RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "decision": "baseline_capture_runtime_failure_no_retry",
            "failure_identity_sha256": failure["identity_sha256"],
            "bridge_spec_identity_sha256": sources["bridge_spec"][
                "identity_sha256"
            ],
            "source_checkpoint_identity_sha256": sources["x_runtime"][
                "checkpoint_identity_sha256"
            ],
            "amended_bridge_gate_passed": False,
            "gate_c_request_eligible": False,
            "gate_c_route_open_under_owner_direction": True,
            **_false_execution_authority(),
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
    permit = load_strict_json(root / BASELINE_PERMIT_PATH)
    verify_baseline_permit(
        permit,
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=preflight,
    )
    return sources, preflight, permit


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
        for repeat_index in range(REPEATS_PER_START_SEED)
    ]


def _trajectory_steps(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != DENOISE_STEP_COUNT:
        raise ValueError("T20.36o denoise trajectory must contain ten steps")
    result = []
    for step_index, row in enumerate(value):
        expected_time = 1.0 - step_index / DENOISE_STEP_COUNT
        if (
            not isinstance(row, dict)
            or row.get("step_index") != step_index
            or abs(_finite(row.get("time"), label="denoise time") - expected_time)
            > 1e-6
        ):
            raise ValueError("T20.36o denoise time grid drifted")
        result.append(
            {
                "step_index": step_index,
                "time": expected_time,
                **_encoded_f32_matrix(
                    row,
                    source_field="state",
                    encoded_field="state_f32le_base64",
                    digest_field="state_f32le_sha256",
                    label="denoise state",
                ),
                **_encoded_f32_matrix(
                    row,
                    source_field="learned_velocity",
                    encoded_field="learned_velocity_f32le_base64",
                    digest_field="learned_velocity_f32le_sha256",
                    label="denoise velocity",
                ),
            }
        )
    return result


def _encoded_f32_matrix(
    row: dict[str, Any],
    *,
    source_field: str,
    encoded_field: str,
    digest_field: str,
    label: str,
) -> dict[str, str]:
    if source_field in row:
        matrix = _matrix(
            row.get(source_field),
            rows=TARGET_HORIZON,
            columns=MAXIMUM_ACTION_DIMENSIONS,
            label=label,
        )
        flattened = [item for matrix_row in matrix for item in matrix_row]
        raw = struct.pack(f"<{len(flattened)}f", *flattened)
    else:
        encoded = row.get(encoded_field)
        if not isinstance(encoded, str) or not encoded:
            raise ValueError(f"T20.36o {label} encoded payload is missing")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as error:
            raise ValueError(
                f"T20.36o {label} encoded payload is invalid"
            ) from error
        expected_size = TARGET_HORIZON * MAXIMUM_ACTION_DIMENSIONS * 4
        if len(raw) != expected_size:
            raise ValueError(f"T20.36o {label} encoded shape drifted")
        values = struct.unpack(
            f"<{TARGET_HORIZON * MAXIMUM_ACTION_DIMENSIONS}f", raw
        )
        if any(not math.isfinite(value) for value in values):
            raise ValueError(f"T20.36o {label} encoded payload is non-finite")
    digest = hashlib.sha256(raw).hexdigest()
    if digest_field in row and row.get(digest_field) != digest:
        raise ValueError(f"T20.36o {label} encoded hash drifted")
    return {
        encoded_field: base64.b64encode(raw).decode("ascii"),
        digest_field: digest,
    }


def _matrix(
    value: Any, *, rows: int, columns: int, label: str
) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != rows:
        raise ValueError(f"T20.36o {label} must be {rows}x{columns}")
    result = []
    for row in value:
        if not isinstance(row, list) or len(row) != columns:
            raise ValueError(f"T20.36o {label} must be {rows}x{columns}")
        result.append([_finite(item, label=label) for item in row])
    return result


def _executed_mask(value: Any) -> list[bool]:
    if (
        not isinstance(value, list)
        or len(value) != TARGET_HORIZON
        or any(not isinstance(item, bool) for item in value)
    ):
        raise ValueError("T20.36o executed mask must be 50 booleans")
    executed_length = sum(value)
    if value != [True] * executed_length + [False] * (
        TARGET_HORIZON - executed_length
    ):
        raise ValueError("T20.36o only a terminal tail may be masked")
    return value


def _finite(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.36o {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.36o {label} must be finite")
    return number


def _finite_nonnegative(value: Any, *, label: str) -> float:
    number = _finite(value, label=label)
    if number < 0.0:
        raise ValueError(f"T20.36o {label} must be nonnegative")
    return number


def _finite_positive(value: Any, *, label: str) -> float:
    number = _finite(value, label=label)
    if number <= 0.0:
        raise ValueError(f"T20.36o {label} must be positive")
    return number


def _false_execution_authority() -> dict[str, bool]:
    return {
        "optimizer_created": False,
        "optimizer_training": False,
        "retry_authorized": False,
        "new_start": False,
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
        "physical_transfer_ready": False,
        "promotion_eligible": False,
    }


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36o {label} must be lowercase SHA-256")
    return value


def _commit(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36o {label} must be a lowercase commit")
    return value
