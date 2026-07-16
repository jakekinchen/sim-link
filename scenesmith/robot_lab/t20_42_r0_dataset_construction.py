"""T20.42/R0 deterministic dataset-construction and preflight contracts.

This module is deliberately model-free and rollout-free. It freezes the
candidate/split plan, proves dataset-admission behavior with a fixture-only
manifest, and emits a fail-closed preflight for a later one-use generation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "T20.42"
CONSTRUCTION_SCHEMA_VERSION = "scenesmith.t20_42_r0_construction_spec.v1"
ADMISSION_FIXTURE_SCHEMA_VERSION = "scenesmith.t20_42_r0_dataset_admission_fixture.v1"
PREFLIGHT_SCHEMA_VERSION = "scenesmith.t20_42_r0_construction_preflight.v1"

ROUTE_DECISION_PATH = Path(
    "docs/autonomous-workflow/owner-route-decision-2026-07-16-t20-41.md"
)
ROUTE_DECISION_COMMIT = "e9d0507ce7c79ed77997d1c2334db9a14c6fbf1d"
ROUTE_DECISION_FILE_SHA256 = (
    "ae75bb594ab93a046afe848b3befb6bb919485f4814f1ab423aad9c36cbea1d5"
)
T17_MANIFEST_PATH = Path(
    "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
)
T20_18_GATE_PATH = Path(
    "configurations/robot_lab/t20_18_recovery_episode_package_gate.json"
)
T20_23_DATASET_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_23_recovery_augmented_dataset_manifest.json"
)
T20_23_TRAINING_SPEC_PATH = Path(
    "configurations/robot_lab/t20_23_recovery_augmented_training_spec.json"
)
CONSTRUCTION_SPEC_PATH = Path(
    "configurations/robot_lab/t20_42_r0_construction_spec.json"
)
ADMISSION_FIXTURE_PATH = Path(
    "configurations/robot_lab/t20_42_r0_admission_fixture.json"
)
PREFLIGHT_PATH = Path("configurations/robot_lab/t20_42_r0_construction_preflight.json")

EXPECTED_IDENTITIES = {
    "t17_manifest": "3860158e201e457146a167cfa778da14f210d88fa223cb075a1ec6d422ecfd1a",
    "t20_18_gate": "c6f365151550e58f5edf7d52e51d7f1b3742995331c038fc571e66e3bc9e7b73",
    "t20_23_dataset_manifest": "f12c95a3cdf3e0005fa093000a5e44e1cddd08dbfb049ab405f462e2c9e760fa",
    "t20_23_training_spec": "5ad2f407d5df49752c65180addbda033888fdcc5869fc5c9a546669bb94a58aa",
}
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)
TRAIN_PLANAR_MICROMETERS = (-1000, -500, 0, 500, 1000)
TRAIN_YAW_MICRORADIANS = (-30000, -15000, 0, 15000, 30000)
FRESH_BAND_X_MICROMETERS = 750
FRESH_BAND_Y_MICROMETERS = (-750, 0, 750)
FRESH_BAND_YAW_MICRORADIANS = (-22500, 0, 22500)
MINIMUM_NEW_NOMINAL_SUCCESSES = 64
OWNER_NEW_NOMINAL_CEILING = 128
BASE_NOMINAL_EPISODES = 6
BASE_RECOVERY_EPISODES = 4
BASE_EPISODES = BASE_NOMINAL_EPISODES + BASE_RECOVERY_EPISODES
OPTIONAL_NEW_RECOVERY_COUNT = 0

EXECUTION_FIELDS = (
    "r0_episode_generation_executed",
    "dataset_materialized",
    "model_loaded",
    "model_inference",
    "optimizer_created",
    "optimizer_training",
    "learned_policy_rollout",
    "gate_c_executed",
    "archive_replay_activated",
    "hardware_accessed",
    "camera_accessed",
    "serial_accessed",
    "physical_motion",
    "network_accessed",
    "external_compute_started",
    "brev_compute_started",
    "physical_transfer_ready",
    "promotion_eligible",
    "r1_activated",
)
REQUIRED_BEFORE_GENERATION = (
    "implementation_committed_and_origin_confirmed",
    "same_agent_adversarial_review_accepted",
    "fresh_central_generation_decision_granted",
    "fresh_runtime_preflight_valid",
    "one_use_generation_permit_valid",
)


def load_source_snapshot(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Read and verify only compact tracked sources; no raw episode bytes."""

    root = Path(repo_root).resolve()
    route_path = _safe_file(root, ROUTE_DECISION_PATH)
    snapshot = {
        "route_decision_file_sha256": _sha256_file(route_path),
        "route_decision_ref": {
            "path": str(ROUTE_DECISION_PATH),
            "git_commit": ROUTE_DECISION_COMMIT,
            "file_sha256": _sha256_file(route_path),
        },
    }
    for label, path in (
        ("t17_manifest", T17_MANIFEST_PATH),
        ("t20_18_gate", T20_18_GATE_PATH),
        ("t20_23_dataset_manifest", T20_23_DATASET_MANIFEST_PATH),
        ("t20_23_training_spec", T20_23_TRAINING_SPEC_PATH),
    ):
        payload = load_strict_json(_safe_file(root, path))
        snapshot[label] = payload
        snapshot[f"{label}_ref"] = artifact_ref(
            path=path, payload=payload, repo_root=root
        )
    verify_source_snapshot(snapshot)
    return snapshot


def verify_source_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise ValueError("T20.42 source snapshot is invalid")
    if snapshot.get("route_decision_file_sha256") != ROUTE_DECISION_FILE_SHA256:
        raise ValueError("T20.42 owner route decision file drifted")
    if snapshot.get("route_decision_ref") != {
        "path": str(ROUTE_DECISION_PATH),
        "git_commit": ROUTE_DECISION_COMMIT,
        "file_sha256": ROUTE_DECISION_FILE_SHA256,
    }:
        raise ValueError("T20.42 owner route decision reference drifted")
    for label in EXPECTED_IDENTITIES:
        payload = snapshot.get(label)
        if not isinstance(payload, dict):
            raise ValueError(f"T20.42 source is missing: {label}")
        verify_signed_payload(payload, label=f"T20.42 {label}")
        if payload.get("identity_sha256") != EXPECTED_IDENTITIES[label]:
            raise ValueError(f"T20.42 source identity drifted: {label}")
        reference = snapshot.get(f"{label}_ref")
        _verify_ref_shape(reference, label=f"T20.42 {label} reference")
        if reference.get("identity_sha256") != EXPECTED_IDENTITIES[label]:
            raise ValueError(f"T20.42 source reference identity drifted: {label}")
    _verify_t20_23_training_spec_compact(snapshot["t20_23_training_spec"])
    _verify_source_relationships(snapshot)


def build_construction_spec(*, source_snapshot: dict[str, Any]) -> dict[str, Any]:
    verify_source_snapshot(source_snapshot)
    historical_specs = source_snapshot["t17_manifest"].get("episode_specs")
    if not isinstance(historical_specs, list) or len(historical_specs) != 8:
        raise ValueError("T20.42 historical episode specifications drifted")
    historical_keys = {_historical_pose_key(row) for row in historical_specs}
    source_initial_state_ref = _source_initial_state_ref(source_snapshot)

    training_candidates: list[dict[str, Any]] = []
    seed = 42000
    for x_um in TRAIN_PLANAR_MICROMETERS:
        for y_um in TRAIN_PLANAR_MICROMETERS:
            for yaw_urad in TRAIN_YAW_MICRORADIANS:
                pose_key = (x_um, y_um, yaw_urad)
                if pose_key in historical_keys:
                    continue
                training_candidates.append(
                    _candidate(
                        seed=seed,
                        x_um=x_um,
                        y_um=y_um,
                        yaw_urad=yaw_urad,
                        split_role="training_candidate",
                        source_initial_state_key=source_initial_state_ref["key"],
                    )
                )
                seed += 1
    training_candidates.sort(key=lambda row: row["candidate_id"])

    fresh_held_out: list[dict[str, Any]] = []
    seed = 43000
    for y_um in FRESH_BAND_Y_MICROMETERS:
        for yaw_urad in FRESH_BAND_YAW_MICRORADIANS:
            fresh_held_out.append(
                _candidate(
                    seed=seed,
                    x_um=FRESH_BAND_X_MICROMETERS,
                    y_um=y_um,
                    yaw_urad=yaw_urad,
                    split_role="evaluation_only_fresh_pose_band",
                    source_initial_state_key=source_initial_state_ref["key"],
                )
            )
            seed += 1
    fresh_held_out.sort(key=lambda row: row["candidate_id"])

    maximum_successes = len(training_candidates)
    payload = {
        "schema_version": CONSTRUCTION_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "scope": "r0_dataset_expansion_by_construction_pre_generation_contract",
        "route_decision_ref": dict(source_snapshot["route_decision_ref"]),
        "source_artifact_refs": {
            label: dict(source_snapshot[f"{label}_ref"])
            for label in EXPECTED_IDENTITIES
        },
        "verified_base_membership": _base_membership(source_snapshot),
        "existing_held_out_episodes": _existing_held_out(source_snapshot),
        "construction": {
            "pose_envelope": {
                "maximum_absolute_planar_offset_m": 0.001,
                "maximum_absolute_yaw_offset_rad": 0.03,
                "source": "T17.5b verified episode-variation envelope",
            },
            "source_initial_state_refs": [source_initial_state_ref],
            "initialization_variation": {
                "mode": "source_fixed_no_verified_nonzero_delta_envelope",
                "joint_names": list(JOINT_NAMES),
                "allowed_delta_rad": [0.0] * len(JOINT_NAMES),
                "nonzero_delta_authorized": False,
            },
            "training_candidate_count": len(training_candidates),
            "training_candidates": training_candidates,
            "fresh_held_out_candidate_count": len(fresh_held_out),
            "fresh_held_out_candidates": fresh_held_out,
            "required_new_nominal_successes": {
                "minimum": MINIMUM_NEW_NOMINAL_SUCCESSES,
                "maximum": maximum_successes,
                "owner_ceiling": OWNER_NEW_NOMINAL_CEILING,
            },
            "optional_new_recovery_count": OPTIONAL_NEW_RECOVERY_COUNT,
            "adaptive_resampling": False,
            "post_outcome_candidate_mutation": False,
            "physics_parameter_randomization": False,
            "prohibited_randomization_axes": [
                "mass",
                "friction",
                "damping",
                "actuator",
                "camera",
                "lighting",
                "object_family",
                "task_family",
            ],
            "strict_v2_only_training_admission": True,
            "unassisted_scripted_expert_only": True,
            "geometry_target_rederived_per_candidate": True,
        },
        "dataset_contract": {
            "verified_base_episode_count": BASE_EPISODES,
            "verified_base_nominal_episode_count": BASE_NOMINAL_EPISODES,
            "verified_base_recovery_episode_count": BASE_RECOVERY_EPISODES,
            "verified_base_included_exactly_once": True,
            "new_nominal_success_minimum": MINIMUM_NEW_NOMINAL_SUCCESSES,
            "new_nominal_success_maximum": maximum_successes,
            "optional_new_recovery_count": OPTIONAL_NEW_RECOVERY_COUNT,
            "implicit_resampling_or_weighting": False,
            "failed_or_held_out_training_rows": 0,
            "normalization": "MEAN_STD",
            "statistics_source": "frozen_training_split_only",
            "existing_held_out_seeds": [6, 7],
            "fresh_pose_band_training_rows": 0,
            "raw_store_append_only": True,
            "actions_padded_or_inferred": False,
            "compiler_path": [
                "append_only_raw_store",
                "frame_segment_compiler",
                "unpadded_window_index",
                "package_lerobot_dataset",
            ],
        },
        "generation_plan": {
            "attempt_count": 1,
            "training_candidate_ids": [
                row["candidate_id"] for row in training_candidates
            ],
            "fresh_held_out_candidate_ids": [
                row["candidate_id"] for row in fresh_held_out
            ],
            "existing_held_out_seeds_referenced_without_regeneration": [6, 7],
            "retry_or_manifest_extension_authorized": False,
        },
        "execution_state": {field: False for field in EXECUTION_FIELDS},
        "required_before_generation": list(REQUIRED_BEFORE_GENERATION),
        "authority_not_granted": [
            "r0_episode_generation_execution",
            "model_construction",
            "model_inference",
            "optimizer_training",
            "learned_policy_rollout",
            "gate_c_execution",
            "threshold_change",
            "archive_replay",
            "hardware",
            "network_access",
            "external_compute",
            "brev_compute",
            "physical_transfer",
            "promotion",
            "r1_activation",
        ],
    }
    signed = sign_payload(payload)
    _validate_construction_shape(signed)
    return signed


def verify_construction_spec(
    payload: dict[str, Any], *, source_snapshot: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.42 R0 construction specification")
    _validate_construction_shape(payload)
    expected = build_construction_spec(source_snapshot=source_snapshot)
    if canonical_json_bytes(payload) != canonical_json_bytes(expected):
        raise ValueError("T20.42 R0 construction specification drifted")


def build_admission_fixture(*, construction_spec: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(
        construction_spec, label="T20.42 construction spec for admission fixture"
    )
    _validate_construction_shape(construction_spec)
    candidates = construction_spec["construction"]["training_candidates"]
    selected = candidates[:MINIMUM_NEW_NOMINAL_SUCCESSES]
    rejected = candidates[MINIMUM_NEW_NOMINAL_SUCCESSES:]
    base = [dict(row) for row in construction_spec["verified_base_membership"]]
    new_successes = [
        {
            "candidate_id": row["candidate_id"],
            "seed": row["seed"],
            "strict_v2_success": True,
            "included_in_training_dataset": True,
            "included_in_dataset_statistics": True,
        }
        for row in selected
    ]
    statistics_ids = [
        *[row["membership_id"] for row in base],
        *[row["candidate_id"] for row in new_successes],
    ]
    payload = {
        "schema_version": ADMISSION_FIXTURE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "evidence_mode": "fixture_only_no_episode_generation",
        "construction_spec_identity_sha256": construction_spec["identity_sha256"],
        "training_membership": {
            "verified_base_episodes": base,
            "new_nominal_successes": new_successes,
            "optional_new_recoveries": [],
        },
        "excluded_evidence": {
            "failed_candidate_ids": [row["candidate_id"] for row in rejected],
            "fresh_held_out_candidate_ids": [
                row["candidate_id"]
                for row in construction_spec["construction"][
                    "fresh_held_out_candidates"
                ]
            ],
            "existing_held_out_episode_ids": [
                row["raw_rollout_record_identity_sha256"]
                for row in construction_spec["existing_held_out_episodes"]
            ],
        },
        "statistics_contract": {
            "normalization": "MEAN_STD",
            "source": "frozen_training_split_only",
            "training_episode_ids": statistics_ids,
            "failed_episode_rows": 0,
            "held_out_episode_rows": 0,
        },
        "counts": {
            "verified_base_episode_count": len(base),
            "new_nominal_success_count": len(new_successes),
            "optional_new_recovery_count": 0,
            "training_episode_count": len(statistics_ids),
            "failed_candidate_count": len(rejected),
            "fresh_held_out_candidate_count": construction_spec["construction"][
                "fresh_held_out_candidate_count"
            ],
            "existing_held_out_episode_count": len(
                construction_spec["existing_held_out_episodes"]
            ),
        },
        "r0_dataset_materialized": False,
        "r0_episode_generation_executed": False,
        "model_loaded": False,
        "optimizer_training": False,
        "hardware_accessed": False,
        "network_accessed": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "authority_not_granted": [
            "dataset_materialized",
            "episode_generation",
            "model_inference",
            "optimizer_training",
            "policy_acceptance",
            "physical_transfer",
            "promotion",
        ],
    }
    signed = sign_payload(payload)
    _validate_admission_fixture_shape(signed, construction_spec=construction_spec)
    return signed


def verify_admission_fixture(
    payload: dict[str, Any], *, construction_spec: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.42 dataset-admission fixture")
    _validate_admission_fixture_shape(payload, construction_spec=construction_spec)
    expected = build_admission_fixture(construction_spec=construction_spec)
    if canonical_json_bytes(payload) != canonical_json_bytes(expected):
        raise ValueError("T20.42 dataset-admission fixture drifted")


def build_preflight(
    *, construction_spec_ref: dict[str, Any], admission_fixture_ref: dict[str, Any]
) -> dict[str, Any]:
    construction_ref = _verified_ref_copy(
        construction_spec_ref,
        expected_path=CONSTRUCTION_SPEC_PATH,
        expected_schema=CONSTRUCTION_SCHEMA_VERSION,
        label="T20.42 construction spec",
    )
    fixture_ref = _verified_ref_copy(
        admission_fixture_ref,
        expected_path=ADMISSION_FIXTURE_PATH,
        expected_schema=ADMISSION_FIXTURE_SCHEMA_VERSION,
        label="T20.42 admission fixture",
    )
    payload = {
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "scope": "r0_contract_implementation_pre_generation_fail_closed",
        "construction_spec_ref": construction_ref,
        "admission_fixture_ref": fixture_ref,
        "product_path": {
            "entrypoint": "scripts/robot_lab/write_t20_42_r0_dataset_construction.py",
            "current_mode": "write_or_verify_contract_artifacts_only",
            "generation_runner_exposed": False,
        },
        "construction_contract_valid": True,
        "admission_fixture_valid": True,
        "generation_ready": False,
        "required_before_generation": list(REQUIRED_BEFORE_GENERATION),
        **{field: False for field in EXECUTION_FIELDS},
        "authority_not_granted": [
            "r0_episode_generation_execution",
            "dataset_materialization",
            "model_construction",
            "model_inference",
            "optimizer_creation",
            "optimizer_training",
            "learned_policy_rollout",
            "gate_c_execution",
            "hardware",
            "network_access",
            "external_compute",
            "brev_compute",
            "physical_transfer",
            "promotion",
            "r1_activation",
        ],
    }
    return sign_payload(payload)


def verify_preflight(
    payload: dict[str, Any],
    *,
    construction_spec_ref: dict[str, Any],
    admission_fixture_ref: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.42 construction preflight")
    if payload.get("schema_version") != PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("T20.42 preflight schema drifted")
    for field in EXECUTION_FIELDS:
        if payload.get(field) is not False:
            raise ValueError(f"T20.42 preflight authority escalated: {field}")
    if payload.get("generation_ready") is not False:
        raise ValueError("T20.42 preflight incorrectly grants generation readiness")
    expected = build_preflight(
        construction_spec_ref=construction_spec_ref,
        admission_fixture_ref=admission_fixture_ref,
    )
    if canonical_json_bytes(payload) != canonical_json_bytes(expected):
        raise ValueError("T20.42 construction preflight drifted")


def write_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    targets = (
        root / CONSTRUCTION_SPEC_PATH,
        root / ADMISSION_FIXTURE_PATH,
        root / PREFLIGHT_PATH,
    )
    if any(path.exists() for path in targets):
        raise FileExistsError("T20.42 contract artifacts already exist; use --verify")
    sources = load_source_snapshot(repo_root=root)
    spec = build_construction_spec(source_snapshot=sources)
    fixture = build_admission_fixture(construction_spec=spec)
    spec_ref = _prospective_artifact_ref(CONSTRUCTION_SPEC_PATH, spec)
    fixture_ref = _prospective_artifact_ref(ADMISSION_FIXTURE_PATH, fixture)
    preflight = build_preflight(
        construction_spec_ref=spec_ref, admission_fixture_ref=fixture_ref
    )
    parent = (root / CONSTRUCTION_SPEC_PATH).parent
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="t20-42-r0-", dir=parent) as raw:
        temporary = Path(raw)
        staged = (
            (temporary / CONSTRUCTION_SPEC_PATH.name, targets[0], spec),
            (temporary / ADMISSION_FIXTURE_PATH.name, targets[1], fixture),
            (temporary / PREFLIGHT_PATH.name, targets[2], preflight),
        )
        for temporary_path, _target, payload in staged:
            dump_canonical_json(temporary_path, payload)
        for temporary_path, target, _payload in staged:
            os.replace(temporary_path, target)
    return verify_artifacts(repo_root=root)


def verify_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = load_source_snapshot(repo_root=root)
    spec_path = _safe_file(root, CONSTRUCTION_SPEC_PATH)
    fixture_path = _safe_file(root, ADMISSION_FIXTURE_PATH)
    preflight_path = _safe_file(root, PREFLIGHT_PATH)
    spec = load_strict_json(spec_path)
    fixture = load_strict_json(fixture_path)
    preflight = load_strict_json(preflight_path)
    verify_construction_spec(spec, source_snapshot=sources)
    verify_admission_fixture(fixture, construction_spec=spec)
    spec_ref = artifact_ref(path=CONSTRUCTION_SPEC_PATH, payload=spec, repo_root=root)
    fixture_ref = artifact_ref(
        path=ADMISSION_FIXTURE_PATH, payload=fixture, repo_root=root
    )
    verify_preflight(
        preflight,
        construction_spec_ref=spec_ref,
        admission_fixture_ref=fixture_ref,
    )
    return {
        "construction_spec": spec,
        "admission_fixture": fixture,
        "preflight": preflight,
    }


def _verify_source_relationships(snapshot: dict[str, Any]) -> None:
    t17 = snapshot["t17_manifest"]
    gate = snapshot["t20_18_gate"]
    dataset = snapshot["t20_23_dataset_manifest"]
    training = snapshot["t20_23_training_spec"]
    if (
        t17.get("configured_episode_count") != 8
        or t17.get("realized_episode_count") != 8
    ):
        raise ValueError("T20.42 T17.5b episode count drifted")
    if t17.get("runtime_failure_count") != 0:
        raise ValueError("T20.42 T17.5b source contains runtime failures")
    if gate.get("episode_count") != 8 or gate.get("outcome_class_counts") != {
        "failure": 2,
        "near_failure": 2,
        "recovery": 4,
    }:
        raise ValueError("T20.42 T20.18 recovery source drifted")
    if (
        dataset.get("episode_count") != BASE_EPISODES
        or dataset.get("eligible_episode_count") != BASE_EPISODES
    ):
        raise ValueError("T20.42 T20.23 dataset membership count drifted")
    episodes = dataset.get("episodes")
    if not isinstance(episodes, list) or len(episodes) != BASE_EPISODES:
        raise ValueError("T20.42 T20.23 dataset episode list drifted")
    expected_ids = [
        *[
            row.get("raw_rollout_record_identity_sha256")
            for row in training.get("nominal_training_episodes", [])
        ],
        *[
            row.get("identity_sha256")
            for row in training.get("recovery_training_episodes", [])
        ],
    ]
    actual_ids = [row.get("raw_rollout_identity_sha256") for row in episodes]
    if actual_ids != expected_ids or len(set(actual_ids)) != BASE_EPISODES:
        raise ValueError("T20.42 T20.23 dataset/source membership drifted")
    held_out = training.get("held_out_episodes")
    if not isinstance(held_out, list) or [row.get("seed") for row in held_out] != [
        6,
        7,
    ]:
        raise ValueError("T20.42 held-out seed membership drifted")
    if any(
        row.get("included_in_training_dataset") is not False
        or row.get("included_in_dataset_statistics") is not False
        for row in held_out
    ):
        raise ValueError("T20.42 existing held-out evidence leaked")


def _verify_t20_23_training_spec_compact(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != (
        "scenesmith.t20_23_recovery_augmented_training_spec.v1"
    ):
        raise ValueError("T20.42 T20.23 training specification schema drifted")
    if (
        payload.get("dataset_mixture_frozen") is not True
        or payload.get("simulation_only") is not True
    ):
        raise ValueError("T20.42 T20.23 dataset scope drifted")
    for field in (
        "model_loaded",
        "model_inference",
        "optimizer_training",
        "simulation_rollout_executed",
        "simulation_training_ready",
        "simulation_policy_accepted",
        "physical_transfer_ready",
        "promotion_eligible",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
    ):
        if payload.get(field) is not False:
            raise ValueError(f"T20.42 T20.23 source authority drifted: {field}")
    nominal = payload.get("nominal_training_episodes")
    recovery = payload.get("recovery_training_episodes")
    diagnostic = payload.get("diagnostic_episodes")
    held_out = payload.get("held_out_episodes")
    if not isinstance(nominal, list) or [row.get("seed") for row in nominal] != list(
        range(BASE_NOMINAL_EPISODES)
    ):
        raise ValueError("T20.42 T20.23 nominal membership drifted")
    if not isinstance(recovery, list) or len(recovery) != BASE_RECOVERY_EPISODES:
        raise ValueError("T20.42 T20.23 recovery membership drifted")
    if any(
        row.get("outcome_class") != "recovery"
        or row.get("included_in_training_dataset") is not True
        or row.get("included_in_dataset_statistics") is not True
        for row in recovery
    ):
        raise ValueError("T20.42 T20.23 recovery admission drifted")
    if not isinstance(diagnostic, list) or len(diagnostic) != 4:
        raise ValueError("T20.42 T20.23 diagnostic membership drifted")
    if any(
        row.get("included_in_training_dataset") is not False
        or row.get("included_in_dataset_statistics") is not False
        for row in diagnostic
    ):
        raise ValueError("T20.42 T20.23 diagnostic evidence leaked")
    if not isinstance(held_out, list) or [row.get("seed") for row in held_out] != [
        6,
        7,
    ]:
        raise ValueError("T20.42 T20.23 held-out membership drifted")
    contract = payload.get("dataset_contract")
    if not isinstance(contract, dict) or contract.get("episode_count") != BASE_EPISODES:
        raise ValueError("T20.42 T20.23 dataset contract drifted")
    if (
        contract.get("frame_count") != 2330
        or contract.get("implicit_resampling_or_duplication") is not False
    ):
        raise ValueError("T20.42 T20.23 count/resampling contract drifted")
    manifest_ref = payload.get("dataset_manifest_ref")
    if (
        not isinstance(manifest_ref, dict)
        or manifest_ref.get("identity_sha256")
        != EXPECTED_IDENTITIES["t20_23_dataset_manifest"]
    ):
        raise ValueError("T20.42 T20.23 dataset reference drifted")


def _source_initial_state_ref(snapshot: dict[str, Any]) -> dict[str, Any]:
    seed_zero = next(
        (row for row in snapshot["t17_manifest"]["episodes"] if row.get("seed") == 0),
        None,
    )
    if not isinstance(seed_zero, dict):
        raise ValueError("T20.42 seed-zero source state reference is missing")
    identity = _require_sha(
        seed_zero.get("raw_rollout_record_identity_sha256"),
        label="T20.42 seed-zero rollout identity",
    )
    return {
        "key": "t17_5b_seed_0_frame_0_joint_position_mujoco_rad",
        "manifest_identity_sha256": snapshot["t17_manifest"]["identity_sha256"],
        "raw_rollout_identity_sha256": identity,
        "json_pointer": "/frames/0/observations/joint_position_mujoco_rad",
        "joint_names": list(JOINT_NAMES),
        "local_raw_bytes_required_at_generation": True,
        "nonzero_initial_delta_authorized": False,
    }


def _candidate(
    *,
    seed: int,
    x_um: int,
    y_um: int,
    yaw_urad: int,
    split_role: str,
    source_initial_state_key: str,
) -> dict[str, Any]:
    row = {
        "seed": seed,
        "split_role": split_role,
        "planar_offset_m": [x_um / 1_000_000.0, y_um / 1_000_000.0],
        "yaw_offset_rad": yaw_urad / 1_000_000.0,
        "source_initial_state_key": source_initial_state_key,
        "initial_joint_delta_rad": [0.0] * len(JOINT_NAMES),
        "initialization_reachability": "source_state_identity_zero_delta",
        "geometry_target_rederived": True,
        "unassisted": True,
        "strict_v2_required": True,
        "physics_parameter_randomization": False,
    }
    return {
        "candidate_id": hashlib.sha256(canonical_json_bytes(row)).hexdigest(),
        **row,
    }


def _historical_pose_key(row: dict[str, Any]) -> tuple[int, int, int]:
    if not isinstance(row, dict):
        raise ValueError("T20.42 historical pose row is invalid")
    offset = row.get("planar_offset_m")
    yaw = row.get("yaw_offset_rad")
    if not isinstance(offset, list) or len(offset) != 2:
        raise ValueError("T20.42 historical planar offset is invalid")
    values = [*offset, yaw]
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        for value in values
    ):
        raise ValueError("T20.42 historical pose contains a non-number")
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("T20.42 historical pose contains a non-finite number")
    return (
        round(float(offset[0]) * 1_000_000),
        round(float(offset[1]) * 1_000_000),
        round(float(yaw) * 1_000_000),
    )


def _base_membership(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in snapshot["t20_23_dataset_manifest"]["episodes"]:
        index = row.get("episode_index")
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index != len(result)
        ):
            raise ValueError("T20.42 verified base episode order drifted")
        identity = _require_sha(
            row.get("raw_rollout_identity_sha256"),
            label="T20.42 verified base rollout identity",
        )
        result.append(
            {
                "membership_id": identity,
                "episode_index": index,
                "source_class": (
                    "nominal_strict_success"
                    if index < BASE_NOMINAL_EPISODES
                    else "policy_visited_recovery"
                ),
                "frame_count": _positive_int(
                    row.get("frame_count"), label="T20.42 verified base frame count"
                ),
                "episode_content_sha256": _require_sha(
                    row.get("episode_content_sha256"),
                    label="T20.42 verified base content identity",
                ),
                "included_exactly_once": True,
                "included_in_training_dataset": True,
                "included_in_dataset_statistics": True,
            }
        )
    return result


def _existing_held_out(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "seed": row["seed"],
            "frame_count": row["frame_count"],
            "raw_rollout_record_identity_sha256": row[
                "raw_rollout_record_identity_sha256"
            ],
            "episode_file_sha256": row["episode_file_sha256"],
            "included_in_training_dataset": False,
            "included_in_dataset_statistics": False,
            "referenced_without_regeneration": True,
        }
        for row in snapshot["t20_23_training_spec"]["held_out_episodes"]
    ]


def _validate_construction_shape(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != CONSTRUCTION_SCHEMA_VERSION:
        raise ValueError("T20.42 construction schema drifted")
    construction = payload.get("construction")
    if not isinstance(construction, dict):
        raise ValueError("T20.42 construction body is missing")
    training = construction.get("training_candidates")
    fresh = construction.get("fresh_held_out_candidates")
    if not isinstance(training, list) or not (
        MINIMUM_NEW_NOMINAL_SUCCESSES <= len(training) <= OWNER_NEW_NOMINAL_CEILING
    ):
        raise ValueError("T20.42 training candidate count is outside route bounds")
    if construction.get("training_candidate_count") != len(training):
        raise ValueError("T20.42 training candidate count drifted")
    if not isinstance(fresh, list) or len(fresh) != 9:
        raise ValueError("T20.42 fresh held-out pose band drifted")
    if construction.get("fresh_held_out_candidate_count") != len(fresh):
        raise ValueError("T20.42 fresh held-out count drifted")
    _validate_candidate_rows(training, expected_role="training_candidate")
    _validate_candidate_rows(fresh, expected_role="evaluation_only_fresh_pose_band")
    training_keys = {_pose_key(row) for row in training}
    fresh_keys = {_pose_key(row) for row in fresh}
    if training_keys & fresh_keys:
        raise ValueError("T20.42 training and fresh held-out pose bands overlap")
    if construction.get("optional_new_recovery_count") != 0:
        raise ValueError("T20.42 unregistered recovery branch entered the contract")
    for field in (
        "adaptive_resampling",
        "post_outcome_candidate_mutation",
        "physics_parameter_randomization",
    ):
        if construction.get(field) is not False:
            raise ValueError(f"T20.42 forbidden construction mode enabled: {field}")
    if len(payload.get("verified_base_membership", [])) != BASE_EPISODES:
        raise ValueError("T20.42 verified base membership drifted")
    if [row.get("seed") for row in payload.get("existing_held_out_episodes", [])] != [
        6,
        7,
    ]:
        raise ValueError("T20.42 existing held-out membership drifted")
    if payload.get("dataset_contract", {}).get("normalization") != "MEAN_STD":
        raise ValueError("T20.42 dataset normalization contract drifted")
    for field in EXECUTION_FIELDS:
        if payload.get("execution_state", {}).get(field) is not False:
            raise ValueError(f"T20.42 construction authority escalated: {field}")
    if payload.get("required_before_generation") != list(REQUIRED_BEFORE_GENERATION):
        raise ValueError("T20.42 generation prerequisites drifted")


def _validate_candidate_rows(rows: list[dict[str, Any]], *, expected_role: str) -> None:
    ids: list[str] = []
    seeds: list[int] = []
    poses: list[tuple[int, int, int]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("T20.42 candidate row is invalid")
        candidate_id = _require_sha(
            row.get("candidate_id"), label="T20.42 candidate ID"
        )
        unsigned = {key: value for key, value in row.items() if key != "candidate_id"}
        if hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest() != candidate_id:
            raise ValueError("T20.42 candidate content identity drifted")
        seed = row.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("T20.42 candidate seed is invalid")
        if row.get("split_role") != expected_role:
            raise ValueError("T20.42 candidate split role drifted")
        if row.get("initial_joint_delta_rad") != [0.0] * len(JOINT_NAMES):
            raise ValueError("T20.42 unverified nonzero initialization delta")
        if row.get("physics_parameter_randomization") is not False:
            raise ValueError("T20.42 physics randomization is prohibited")
        if (
            row.get("unassisted") is not True
            or row.get("strict_v2_required") is not True
        ):
            raise ValueError("T20.42 candidate actor/oracle contract drifted")
        pose = _pose_key(row)
        if abs(pose[0]) > 1000 or abs(pose[1]) > 1000 or abs(pose[2]) > 30000:
            raise ValueError("T20.42 candidate exceeds the verified pose envelope")
        ids.append(candidate_id)
        seeds.append(seed)
        poses.append(pose)
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        raise ValueError("T20.42 candidate IDs are duplicated or nondeterministic")
    if len(set(seeds)) != len(seeds) or len(set(poses)) != len(poses):
        raise ValueError("T20.42 candidate seeds or poses are duplicated")


def _validate_admission_fixture_shape(
    payload: dict[str, Any], *, construction_spec: dict[str, Any]
) -> None:
    verify_signed_payload(
        construction_spec, label="T20.42 construction spec for fixture verification"
    )
    _validate_construction_shape(construction_spec)
    if payload.get("schema_version") != ADMISSION_FIXTURE_SCHEMA_VERSION:
        raise ValueError("T20.42 admission fixture schema drifted")
    if payload.get("evidence_mode") != "fixture_only_no_episode_generation":
        raise ValueError("T20.42 admission fixture evidence mode drifted")
    if payload.get("construction_spec_identity_sha256") != construction_spec.get(
        "identity_sha256"
    ):
        raise ValueError("T20.42 admission fixture source drifted")
    membership = payload.get("training_membership")
    if not isinstance(membership, dict):
        raise ValueError("T20.42 admission membership is missing")
    base = membership.get("verified_base_episodes")
    new = membership.get("new_nominal_successes")
    recovery = membership.get("optional_new_recoveries")
    if base != construction_spec["verified_base_membership"]:
        raise ValueError("T20.42 verified base was omitted, duplicated, or mutated")
    if not isinstance(new, list) or len(new) != MINIMUM_NEW_NOMINAL_SUCCESSES:
        raise ValueError("T20.42 fixture new-success count drifted")
    allowed = {
        row["candidate_id"]
        for row in construction_spec["construction"]["training_candidates"]
    }
    new_ids = [row.get("candidate_id") for row in new]
    if len(set(new_ids)) != len(new_ids) or not set(new_ids) <= allowed:
        raise ValueError("T20.42 fixture contains duplicate or unknown success")
    if any(
        row.get("strict_v2_success") is not True
        or row.get("included_in_training_dataset") is not True
        or row.get("included_in_dataset_statistics") is not True
        for row in new
    ):
        raise ValueError("T20.42 non-success entered fixture training")
    if recovery != []:
        raise ValueError("T20.42 fixture contains an unregistered recovery")
    expected_stats = [
        *[row["membership_id"] for row in base],
        *new_ids,
    ]
    statistics = payload.get("statistics_contract")
    if (
        not isinstance(statistics, dict)
        or statistics.get("training_episode_ids") != expected_stats
    ):
        raise ValueError("T20.42 fixture statistics membership leaked or drifted")
    if (
        statistics.get("normalization") != "MEAN_STD"
        or statistics.get("source") != "frozen_training_split_only"
    ):
        raise ValueError("T20.42 fixture statistics contract drifted")
    excluded = payload.get("excluded_evidence")
    if not isinstance(excluded, dict):
        raise ValueError("T20.42 fixture exclusions are missing")
    failed_ids = excluded.get("failed_candidate_ids")
    fresh_ids = excluded.get("fresh_held_out_candidate_ids")
    existing_ids = excluded.get("existing_held_out_episode_ids")
    if set(failed_ids or []) & set(expected_stats):
        raise ValueError("T20.42 failed candidate entered training/statistics")
    if set(fresh_ids or []) & set(expected_stats):
        raise ValueError("T20.42 fresh held-out candidate entered training/statistics")
    if set(existing_ids or []) & set(expected_stats):
        raise ValueError("T20.42 existing held-out episode entered training/statistics")
    if (
        payload.get("r0_dataset_materialized") is not False
        or payload.get("r0_episode_generation_executed") is not False
    ):
        raise ValueError("T20.42 fixture was relabelled as executed evidence")


def _pose_key(row: dict[str, Any]) -> tuple[int, int, int]:
    offset = row.get("planar_offset_m")
    yaw = row.get("yaw_offset_rad")
    if not isinstance(offset, list) or len(offset) != 2:
        raise ValueError("T20.42 candidate planar offset is invalid")
    values = [*offset, yaw]
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        for value in values
    ):
        raise ValueError("T20.42 candidate pose contains a non-number")
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("T20.42 candidate pose contains a non-finite number")
    return (
        round(float(offset[0]) * 1_000_000),
        round(float(offset[1]) * 1_000_000),
        round(float(yaw) * 1_000_000),
    )


def _verified_ref_copy(
    value: dict[str, Any], *, expected_path: Path, expected_schema: str, label: str
) -> dict[str, Any]:
    _verify_ref_shape(value, label=label)
    if value.get("path") != str(expected_path):
        raise ValueError(f"{label} path drifted")
    if value.get("schema_version") != expected_schema:
        raise ValueError(f"{label} schema drifted")
    return dict(value)


def _verify_ref_shape(value: Any, *, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} is missing")
    path = value.get("path")
    if (
        not isinstance(path, str)
        or not path
        or Path(path).is_absolute()
        or ".." in Path(path).parts
    ):
        raise ValueError(f"{label} path is invalid")
    schema = value.get("schema_version")
    if not isinstance(schema, str) or not schema:
        raise ValueError(f"{label} schema is invalid")
    _require_sha(value.get("identity_sha256"), label=f"{label} identity")
    _require_sha(value.get("file_sha256"), label=f"{label} file hash")


def _prospective_artifact_ref(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    formatted = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    return {
        "path": str(path),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(formatted).hexdigest(),
    }


def _safe_file(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("T20.42 source path is unsafe")
    unresolved = root / relative
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"T20.42 source path is aliased: {relative}")
    path = unresolved.resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError("T20.42 source path escapes the checkout") from error
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"T20.42 source is missing or aliased: {relative}")
    return path


def _require_sha(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return value


def _positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
