"""Fail-closed preflight and permit for the T20.36o X baseline capture."""

from __future__ import annotations

import hashlib

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36o_baseline_inference_authority import (
    REPO_ROOT,
    load_verified_sources as load_authority_sources,
)


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
