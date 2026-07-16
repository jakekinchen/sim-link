"""Fail-closed authority contracts for one T20.42/R0 generation attempt.

This module is construction-only.  It can deterministically build and verify
prospective authority, runtime-preflight, permit, and attempt-marker payloads,
but it never materializes authority artifacts or executes a candidate.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform

from datetime import datetime
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.authority_composer import (
    DEFAULT_AUTHORITY_SCOPE_ID,
    DEFAULT_AUTHORITY_SUBJECT_ID,
    build_authority_contract,
    build_capability_claim,
    build_composition_request,
    build_evidence_ref,
    compose_authority,
    require_global_decision,
    verify_authority_decision,
)
from scenesmith.robot_lab.t20_42_r0_dataset_construction import (
    ADMISSION_FIXTURE_PATH,
    CONSTRUCTION_SPEC_PATH,
    PREFLIGHT_PATH as CONSTRUCTION_PREFLIGHT_PATH,
    verify_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "T20.42a"
BRANCH = "codex/pi05-autolearn-loop"
OWNER_GRANT_SCHEMA_VERSION = "scenesmith.t20_42a_r0_owner_authorization.v1"
RUNTIME_PREFLIGHT_SCHEMA_VERSION = (
    "scenesmith.t20_42a_r0_generation_runtime_preflight.v1"
)
PERMIT_SCHEMA_VERSION = "scenesmith.t20_42a_r0_generation_permit.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_42_r0_generation_attempt.v1"

OWNER_GRANT_PATH = Path("configurations/robot_lab/t20_42a_r0_owner_authorization.json")
INHERITED_REQUEST_PATH = Path(
    "configurations/robot_lab/t20_23_simulation_training_authority_request.json"
)
INHERITED_DECISION_PATH = Path(
    "configurations/robot_lab/t20_23_simulation_training_authority_decision.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_42a_r0_generation_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_42a_r0_generation_authority_decision.json"
)
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_42a_r0_generation_runtime_preflight.json"
)
PERMIT_PATH = Path("configurations/robot_lab/t20_42a_r0_generation_permit.json")
ATTEMPT_PATH = Path("configurations/robot_lab/t20_42_r0_generation_attempt.json")
RESULT_PATH = Path("configurations/robot_lab/t20_42_r0_generation_result.json")
MIXTURE_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_42_r0_dataset_mixture_manifest.json"
)
STATISTICS_PATH = Path("configurations/robot_lab/t20_42_r0_dataset_statistics.json")
RETENTION_RECEIPT_PATH = Path(
    "configurations/robot_lab/t20_42_r0_retention_receipt.json"
)
RUN_ROOT = Path("outputs/robot_lab/t20_42_r0_generation_run_001")
RAW_STORE_ROOT = RUN_ROOT / "raw_store"
COMPILER_ROOT = RUN_ROOT / "frame_segment_compiler"
WINDOW_ROOT = RUN_ROOT / "unpadded_window_index"
LEROBOT_DATASET_ROOT = RUN_ROOT / "lerobot_dataset"

MINIMUM_FREE_DISK_BYTES = 10 * 1024**3
MAXIMUM_AUTHORITY_SECONDS = 8 * 60 * 60
REQUIRED_DEPENDENCIES = (
    "python",
    "mujoco",
    "numpy",
    "pillow",
    "pyarrow",
    "lerobot",
)
AUTHORIZED_ACTIONS = (
    "execute_fixed_scripted_expert_manifest_once",
    "retain_strict_v2_outcomes_and_quarantines",
    "compile_append_only_raw_store",
    "materialize_one_package_lerobot_dataset",
    "compute_training_only_mean_std",
    "write_compact_signed_result_mixture_statistics",
)
OUTPUT_PATHS = (
    ATTEMPT_PATH,
    RUN_ROOT,
    RAW_STORE_ROOT,
    COMPILER_ROOT,
    WINDOW_ROOT,
    LEROBOT_DATASET_ROOT,
    RESULT_PATH,
    MIXTURE_MANIFEST_PATH,
    STATISTICS_PATH,
    RETENTION_RECEIPT_PATH,
)
PROHIBITED_AUTHORITY_FIELDS = (
    "network_access_authorized",
    "model_or_optimizer_authorized",
    "hardware_authorized",
    "external_compute_authorized",
    "brev_compute_authorized",
    "physical_transfer_authorized",
    "promotion_authorized",
    "r1_authorized",
)

EXPECTED_CONSTRUCTION_IDENTITIES = {
    "construction_spec": (
        "b58a6b31d0a3d892cfce8e319c4736d2da9aab2864663a5b2fc89c752e221458"
    ),
    "admission_fixture": (
        "b7b1eb7746cf3736a12ae7f0fa3e7bffdf58a92cf702d8d7648366e7350553ba"
    ),
    "construction_preflight": (
        "5ff8c5cca2abfe3ceb2b15296fb065c66ff416b98888eb3dba0a1a9074136250"
    ),
}
EXPECTED_SOURCE_REFS = {
    "construction_spec_ref": {
        "path": CONSTRUCTION_SPEC_PATH.as_posix(),
        "schema_version": "scenesmith.t20_42_r0_construction_spec.v1",
        "identity_sha256": EXPECTED_CONSTRUCTION_IDENTITIES["construction_spec"],
        "file_sha256": (
            "accb216dc17165c5cdc1ad01cd9173fa8838590325a16abd3020c4230a26d86a"
        ),
    },
    "admission_fixture_ref": {
        "path": ADMISSION_FIXTURE_PATH.as_posix(),
        "schema_version": "scenesmith.t20_42_r0_dataset_admission_fixture.v1",
        "identity_sha256": EXPECTED_CONSTRUCTION_IDENTITIES["admission_fixture"],
        "file_sha256": (
            "ee5ff97f85b2e117c34d2c8ec0e54b5081393cbb9a09321c30728488e5657e06"
        ),
    },
    "construction_preflight_ref": {
        "path": CONSTRUCTION_PREFLIGHT_PATH.as_posix(),
        "schema_version": "scenesmith.t20_42_r0_construction_preflight.v1",
        "identity_sha256": EXPECTED_CONSTRUCTION_IDENTITIES["construction_preflight"],
        "file_sha256": (
            "e7558a46126e9e6ecd5018f5ba305af7961e1e73e0c23bcd07de57b85e39fff6"
        ),
    },
    "inherited_decision_ref": {
        "path": INHERITED_DECISION_PATH.as_posix(),
        "schema_version": "scenesmith.authority_composition_decision.v1",
        "identity_sha256": (
            "6c2b822ce1d89aecea26d0914f1b3a503bd142d6f2feb62f4481fbda37a5dad5"
        ),
        "file_sha256": (
            "7fe1df6f47a54b754fa6489fa714b26235a60968def1fda5f7b5485e0ba1f968"
        ),
    },
}


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Load the reviewed compact R0 boundary and inherited central decision."""

    root = Path(repo_root).resolve()
    construction = verify_artifacts(repo_root=root)
    sources = {
        "construction_spec": construction["construction_spec"],
        "admission_fixture": construction["admission_fixture"],
        "construction_preflight": construction["preflight"],
    }
    for label, expected_identity in EXPECTED_CONSTRUCTION_IDENTITIES.items():
        if sources[label].get("identity_sha256") != expected_identity:
            raise ValueError(f"T20.42a reviewed source drifted: {label}")
    inherited_request = load_strict_json(root / INHERITED_REQUEST_PATH)
    inherited_decision = load_strict_json(root / INHERITED_DECISION_PATH)
    verify_authority_decision(inherited_decision, request=inherited_request)
    require_global_decision(
        inherited_decision,
        request=inherited_request,
        decision_id="simulation_training_ready",
    )
    if inherited_decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.42a inherited authority exceeded simulation scope")
    sources.update(
        {
            "inherited_request": inherited_request,
            "inherited_decision": inherited_decision,
            "construction_spec_ref": artifact_ref(
                path=CONSTRUCTION_SPEC_PATH,
                payload=sources["construction_spec"],
                repo_root=root,
            ),
            "admission_fixture_ref": artifact_ref(
                path=ADMISSION_FIXTURE_PATH,
                payload=sources["admission_fixture"],
                repo_root=root,
            ),
            "construction_preflight_ref": artifact_ref(
                path=CONSTRUCTION_PREFLIGHT_PATH,
                payload=sources["construction_preflight"],
                repo_root=root,
            ),
            "inherited_decision_ref": artifact_ref(
                path=INHERITED_DECISION_PATH,
                payload=inherited_decision,
                repo_root=root,
            ),
        }
    )
    _verify_fixed_manifest(sources["construction_spec"])
    return sources


def build_owner_grant(
    *,
    sources: dict[str, Any],
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
) -> dict[str, Any]:
    _verify_sources(sources)
    source_commit = _commit(required_source_commit, label="required source commit")
    start, stop = _authority_window(valid_from, valid_until)
    generation_plan = sources["construction_spec"]["generation_plan"]
    return sign_payload(
        {
            "schema_version": OWNER_GRANT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "authorization_id": "t20_42a_r0_one_use_generation_owner_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": (
                "one_local_simulation_only_fixed_manifest_r0_dataset_generation"
            ),
            "construction_spec_ref": dict(sources["construction_spec_ref"]),
            "admission_fixture_ref": dict(sources["admission_fixture_ref"]),
            "construction_preflight_ref": dict(sources["construction_preflight_ref"]),
            "required_source_commit": source_commit,
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "authorized_attempt_count": 1,
            "training_candidate_count": len(generation_plan["training_candidate_ids"]),
            "fresh_held_out_candidate_count": len(
                generation_plan["fresh_held_out_candidate_ids"]
            ),
            "existing_held_out_seeds": list(
                generation_plan[
                    "existing_held_out_seeds_referenced_without_regeneration"
                ]
            ),
            "strict_v2_only_training_admission": True,
            "training_split_only_mean_std": True,
            "existing_held_out_seed_regeneration_authorized": False,
            "adaptive_manifest_extension_authorized": False,
            "retry_authorized": False,
            "simulation_only": True,
            **_prohibited_authority_flags(),
            "issued_at": start.isoformat(),
            "valid_from": start.isoformat(),
            "valid_until": stop.isoformat(),
            "maximum_authority_seconds": MAXIMUM_AUTHORITY_SECONDS,
            "authorization_source": (
                "owner_t20_41_r0_route_and_explicit_t20_42a_proceed_instruction"
            ),
        }
    )


def verify_owner_grant(payload: dict[str, Any], *, sources: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.42a owner grant")
    expected = build_owner_grant(
        sources=sources,
        required_source_commit=payload.get("required_source_commit"),
        valid_from=payload.get("valid_from"),
        valid_until=payload.get("valid_until"),
    )
    if canonical_json_bytes(payload) != canonical_json_bytes(expected):
        raise ValueError("T20.42a owner grant drifted")


def build_central_authority(
    *, sources: dict[str, Any], owner_grant: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    verify_owner_grant(owner_grant, sources=sources)
    refs = {
        "owner": _prospective_artifact_ref(OWNER_GRANT_PATH, owner_grant),
        "construction_spec": dict(sources["construction_spec_ref"]),
        "admission_fixture": dict(sources["admission_fixture_ref"]),
        "construction_preflight": dict(sources["construction_preflight_ref"]),
        "inherited_decision": dict(sources["inherited_decision_ref"]),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [
            refs["inherited_decision"],
            refs["construction_spec"],
        ],
        "executable_stack_valid": [
            refs["construction_preflight"],
            refs["inherited_decision"],
        ],
        "coordinate_contract_valid": [refs["construction_spec"]],
        "normalization_contract_valid": [
            refs["construction_spec"],
            refs["admission_fixture"],
        ],
        "experience_compiler_valid": [
            refs["inherited_decision"],
            refs["construction_spec"],
        ],
        "required_simulation_properties_available": [
            refs["construction_spec"],
            refs["admission_fixture"],
        ],
    }
    requirements = {
        row["prerequisite_id"]: row
        for row in build_authority_contract()["prerequisites"]
    }
    max_age = int(
        (
            datetime.fromisoformat(owner_grant["valid_until"])
            - datetime.fromisoformat(owner_grant["valid_from"])
        ).total_seconds()
    )
    claims = []
    for prerequisite_id, evidence_refs in sorted(evidence.items()):
        requirement = requirements[prerequisite_id]
        provenance = requirement["allowed_provenance_classes"][0]
        claims.append(
            build_capability_claim(
                claim_id=f"t20_42a_{prerequisite_id}",
                capability_id=prerequisite_id,
                value=True,
                subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                provenance_class=provenance,
                issuer=requirement["authorized_issuers"][0],
                validity={
                    "observed_at": owner_grant["valid_from"],
                    "valid_from": owner_grant["valid_from"],
                    "valid_until": owner_grant["valid_until"],
                    "max_age_seconds": max_age,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind="t20_42a_r0_generation_evidence",
                        artifact_schema_version=reference["schema_version"],
                        artifact_identity_sha256=reference["identity_sha256"],
                        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                        provenance_class=provenance,
                    )
                    for reference in evidence_refs
                ],
            )
        )
    request = build_composition_request(
        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
        evaluation_time=owner_grant["valid_from"],
        claims=claims,
        composition_mode="production",
    )
    decision = compose_authority(request)
    require_global_decision(
        decision,
        request=request,
        decision_id="simulation_training_ready",
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.42a central authority exceeded simulation scope")
    return request, decision


def fixture_runtime_snapshot(*, source_commit: str) -> dict[str, Any]:
    commit = _commit(source_commit, label="runtime source commit")
    return {
        "source_commit": commit,
        "branch": BRANCH,
        "origin_contains_source_commit": True,
        "scoped_dirty_paths": [],
        "dependencies": {
            "python": "3.12.fixture",
            "mujoco": "3.3.5.fixture",
            "numpy": "fixture",
            "pillow": "fixture",
            "pyarrow": "fixture",
            "lerobot": "package.fixture",
        },
        "platform": {
            "system": platform.system() or "fixture-system",
            "machine": platform.machine() or "fixture-machine",
            "python_implementation": platform.python_implementation(),
        },
        "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
        "free_disk_bytes": MINIMUM_FREE_DISK_BYTES + 1024**3,
        "network_enabled": False,
        "dependency_fallback_enabled": False,
        "authority_artifacts_materialized": False,
        "attempt_marker_exists": False,
        "r0_episode_generation_executed": False,
        "output_path_state": {
            path.as_posix(): {"exists": False, "is_symlink": False}
            for path in OUTPUT_PATHS
        },
    }


def build_runtime_preflight(
    *,
    sources: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_snapshot: dict[str, Any],
) -> dict[str, Any]:
    _verify_authority_pair(
        sources=sources,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
    )
    runtime = _validated_runtime_snapshot(runtime_snapshot, owner_grant=owner_grant)
    return sign_payload(
        {
            "schema_version": RUNTIME_PREFLIGHT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "scope": "prospective_one_use_r0_generation_runtime_preflight",
            "construction_spec_ref": dict(sources["construction_spec_ref"]),
            "admission_fixture_ref": dict(sources["admission_fixture_ref"]),
            "construction_preflight_ref": dict(sources["construction_preflight_ref"]),
            "owner_grant_ref": _prospective_artifact_ref(OWNER_GRANT_PATH, owner_grant),
            "central_request_ref": _prospective_artifact_ref(REQUEST_PATH, request),
            "central_decision_ref": _prospective_artifact_ref(DECISION_PATH, decision),
            "source_commit": runtime["source_commit"],
            "branch": runtime["branch"],
            "origin_contains_source_commit": True,
            "scoped_dirty_paths": [],
            "dependencies": dict(runtime["dependencies"]),
            "platform": dict(runtime["platform"]),
            "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
            "free_disk_bytes": runtime["free_disk_bytes"],
            "network_enabled": False,
            "dependency_fallback_enabled": False,
            "output_path_state": json.loads(json.dumps(runtime["output_path_state"])),
            "all_output_paths_absent": True,
            "all_output_paths_unaliased": True,
            "authority_artifacts_materialized": False,
            "attempt_marker_exists": False,
            "r0_episode_generation_executed": False,
            **_prohibited_authority_flags(),
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_snapshot: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.42a generation runtime preflight")
    expected = build_runtime_preflight(
        sources=sources,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
        runtime_snapshot=runtime_snapshot,
    )
    if canonical_json_bytes(payload) != canonical_json_bytes(expected):
        raise ValueError("T20.42a generation runtime preflight drifted")


def build_permit(
    *,
    sources: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_preflight: dict[str, Any],
) -> dict[str, Any]:
    runtime_snapshot = _runtime_snapshot_from_preflight(runtime_preflight)
    verify_runtime_preflight(
        runtime_preflight,
        sources=sources,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
        runtime_snapshot=runtime_snapshot,
    )
    plan = sources["construction_spec"]["generation_plan"]
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "scope": "one_use_fixed_manifest_r0_generation_permit",
            "construction_spec_ref": dict(sources["construction_spec_ref"]),
            "owner_grant_ref": _prospective_artifact_ref(OWNER_GRANT_PATH, owner_grant),
            "central_request_ref": _prospective_artifact_ref(REQUEST_PATH, request),
            "central_decision_ref": _prospective_artifact_ref(DECISION_PATH, decision),
            "runtime_preflight_ref": _prospective_artifact_ref(
                RUNTIME_PREFLIGHT_PATH, runtime_preflight
            ),
            "required_source_commit": runtime_preflight["source_commit"],
            "valid_from": owner_grant["valid_from"],
            "valid_until": owner_grant["valid_until"],
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "authorized_attempt_count": 1,
            "training_candidate_ids": list(plan["training_candidate_ids"]),
            "fresh_held_out_candidate_ids": list(plan["fresh_held_out_candidate_ids"]),
            "existing_held_out_seeds_referenced_without_regeneration": list(
                plan["existing_held_out_seeds_referenced_without_regeneration"]
            ),
            "strict_v2_only_training_admission": True,
            "minimum_new_nominal_successes": 64,
            "maximum_new_nominal_successes": 119,
            "raw_store_append_only": True,
            "base_dataset_included_exactly_once": True,
            "mean_std_training_rows_only": True,
            "fresh_held_out_training_rows": 0,
            "attempt_marker_path": ATTEMPT_PATH.as_posix(),
            "output_paths": [path.as_posix() for path in OUTPUT_PATHS],
            "marker_must_precede_first_candidate": True,
            "permit_consumed_by_marker_creation": True,
            "existing_held_out_seed_regeneration_authorized": False,
            "adaptive_manifest_extension_authorized": False,
            "retry_authorized": False,
            "simulation_only": True,
            **_prohibited_authority_flags(),
        }
    )


def verify_permit(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.42a generation permit")
    expected = build_permit(
        sources=sources,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
        runtime_preflight=runtime_preflight,
    )
    if canonical_json_bytes(payload) != canonical_json_bytes(expected):
        raise ValueError("T20.42a generation permit drifted")


def build_attempt_marker(
    *, permit: dict[str, Any], source_commit: str, started_at: str
) -> dict[str, Any]:
    _verify_permit_shell(permit)
    commit = _commit(source_commit, label="attempt source commit")
    if commit != permit["required_source_commit"]:
        raise ValueError("T20.42 attempt source commit drifted")
    started = _offset_time(started_at, label="attempt started_at")
    valid_from = _offset_time(permit["valid_from"], label="permit valid_from")
    valid_until = _offset_time(permit["valid_until"], label="permit valid_until")
    if started < valid_from or started > valid_until:
        raise ValueError("T20.42 attempt starts outside the permit window")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": "T20.42",
            "generation_permit_identity_sha256": permit["identity_sha256"],
            "construction_spec_identity_sha256": permit["construction_spec_ref"][
                "identity_sha256"
            ],
            "source_commit": commit,
            "started_at": started.isoformat(),
            "attempt_ordinal": 1,
            "permit_consumed": True,
            "created_before_first_candidate": True,
            "candidate_execution_count": 0,
            "first_candidate_executed": False,
            "r0_episode_generation_executed": False,
            "dataset_materialized": False,
            "model_or_optimizer_action": False,
            **_prohibited_authority_flags(),
        }
    )


def verify_attempt_marker(payload: dict[str, Any], *, permit: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.42 R0 generation attempt marker")
    expected = build_attempt_marker(
        permit=permit,
        source_commit=payload.get("source_commit"),
        started_at=payload.get("started_at"),
    )
    if canonical_json_bytes(payload) != canonical_json_bytes(expected):
        raise ValueError("T20.42 R0 generation attempt marker drifted")


def write_attempt_marker(
    payload: dict[str, Any],
    *,
    permit: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> Path:
    """Exclusively persist the permit-consuming marker and never overwrite it."""

    verify_attempt_marker(payload, permit=permit)
    if permit.get("attempt_marker_path") != ATTEMPT_PATH.as_posix():
        raise ValueError("T20.42 attempt marker path drifted")
    root = Path(repo_root)
    resolved_root = root.resolve()
    relative = Path(permit["attempt_marker_path"])
    _safe_relative_path(relative, label="attempt marker path")
    target = root / relative
    parent = target.parent
    _reject_existing_symlinks(root, relative.parent)
    parent.mkdir(parents=True, exist_ok=True)
    _reject_existing_symlinks(root, relative.parent)
    if not parent.resolve().is_relative_to(resolved_root):
        raise ValueError("T20.42 attempt marker parent escapes the checkout")
    data = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(target, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    persisted = load_strict_json(target)
    verify_attempt_marker(persisted, permit=permit)
    return target


def _verify_sources(sources: dict[str, Any]) -> None:
    if not isinstance(sources, dict):
        raise ValueError("T20.42a sources are missing")
    for label, identity in EXPECTED_CONSTRUCTION_IDENTITIES.items():
        payload = sources.get(label)
        if not isinstance(payload, dict):
            raise ValueError(f"T20.42a source is missing: {label}")
        verify_signed_payload(payload, label=f"T20.42a {label}")
        if payload.get("identity_sha256") != identity:
            raise ValueError(f"T20.42a source identity drifted: {label}")
    _verify_fixed_manifest(sources["construction_spec"])
    request = sources.get("inherited_request")
    decision = sources.get("inherited_decision")
    if not isinstance(request, dict) or not isinstance(decision, dict):
        raise ValueError("T20.42a inherited central authority is missing")
    verify_authority_decision(decision, request=request)
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.42a inherited authority exceeded simulation scope")
    for key, expected_reference in EXPECTED_SOURCE_REFS.items():
        reference = sources.get(key)
        if reference != expected_reference:
            raise ValueError(f"T20.42a source reference drifted: {key}")


def _verify_fixed_manifest(spec: dict[str, Any]) -> None:
    plan = spec.get("generation_plan")
    construction = spec.get("construction")
    dataset = spec.get("dataset_contract")
    if not isinstance(plan, dict) or not isinstance(construction, dict):
        raise ValueError("T20.42a fixed manifest is missing")
    if not isinstance(dataset, dict):
        raise ValueError("T20.42a dataset contract is missing")
    training = plan.get("training_candidate_ids")
    fresh = plan.get("fresh_held_out_candidate_ids")
    if (
        plan.get("attempt_count") != 1
        or not isinstance(training, list)
        or len(training) != 119
        or len(set(training)) != 119
        or not isinstance(fresh, list)
        or len(fresh) != 9
        or len(set(fresh)) != 9
        or set(training) & set(fresh)
        or plan.get("existing_held_out_seeds_referenced_without_regeneration") != [6, 7]
        or plan.get("retry_or_manifest_extension_authorized") is not False
        or construction.get("training_candidate_count") != 119
        or construction.get("fresh_held_out_candidate_count") != 9
        or construction.get("adaptive_resampling") is not False
        or construction.get("physics_parameter_randomization") is not False
        or dataset.get("normalization") != "MEAN_STD"
        or dataset.get("statistics_source") != "frozen_training_split_only"
    ):
        raise ValueError("T20.42a fixed manifest drifted")
    for identifier in [*training, *fresh]:
        _sha(identifier, label="candidate identity")


def _verify_authority_pair(
    *,
    sources: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    expected_request, expected_decision = build_central_authority(
        sources=sources, owner_grant=owner_grant
    )
    if canonical_json_bytes(request) != canonical_json_bytes(expected_request):
        raise ValueError("T20.42a central request drifted")
    verify_authority_decision(decision, request=request)
    if canonical_json_bytes(decision) != canonical_json_bytes(expected_decision):
        raise ValueError("T20.42a central decision drifted")
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )


def _validated_runtime_snapshot(
    payload: dict[str, Any], *, owner_grant: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("T20.42a runtime snapshot is missing")
    try:
        canonical_json_bytes(payload)
    except (TypeError, ValueError) as error:
        raise ValueError("T20.42a runtime snapshot is not strict JSON") from error
    expected_keys = {
        "source_commit",
        "branch",
        "origin_contains_source_commit",
        "scoped_dirty_paths",
        "dependencies",
        "platform",
        "minimum_free_disk_bytes",
        "free_disk_bytes",
        "network_enabled",
        "dependency_fallback_enabled",
        "authority_artifacts_materialized",
        "attempt_marker_exists",
        "r0_episode_generation_executed",
        "output_path_state",
    }
    if set(payload) != expected_keys:
        raise ValueError("T20.42a runtime snapshot fields drifted")
    free_disk = payload.get("free_disk_bytes")
    minimum = payload.get("minimum_free_disk_bytes")
    if (
        payload.get("source_commit") != owner_grant["required_source_commit"]
        or payload.get("branch") != BRANCH
        or payload.get("origin_contains_source_commit") is not True
        or payload.get("scoped_dirty_paths") != []
        or isinstance(minimum, bool)
        or not isinstance(minimum, int)
        or minimum != MINIMUM_FREE_DISK_BYTES
        or isinstance(free_disk, bool)
        or not isinstance(free_disk, int)
        or free_disk > 2**63 - 1
        or free_disk < MINIMUM_FREE_DISK_BYTES
        or payload.get("network_enabled") is not False
        or payload.get("dependency_fallback_enabled") is not False
        or payload.get("authority_artifacts_materialized") is not False
        or payload.get("attempt_marker_exists") is not False
        or payload.get("r0_episode_generation_executed") is not False
    ):
        raise ValueError("T20.42a runtime facts failed closed")
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, dict) or set(dependencies) != set(
        REQUIRED_DEPENDENCIES
    ):
        raise ValueError("T20.42a runtime dependencies drifted")
    for dependency in REQUIRED_DEPENDENCIES:
        _nonblank(dependencies.get(dependency), label=f"{dependency} version")
    platform_facts = payload.get("platform")
    if not isinstance(platform_facts, dict) or set(platform_facts) != {
        "system",
        "machine",
        "python_implementation",
    }:
        raise ValueError("T20.42a runtime platform facts drifted")
    for name, value in platform_facts.items():
        _nonblank(value, label=f"platform {name}")
    output_state = payload.get("output_path_state")
    expected_paths = [path.as_posix() for path in OUTPUT_PATHS]
    if not isinstance(output_state, dict) or set(output_state) != set(expected_paths):
        raise ValueError("T20.42a runtime output path set drifted")
    for relative, state in output_state.items():
        _safe_relative_path(Path(relative), label="runtime output path")
        if state != {"exists": False, "is_symlink": False}:
            raise ValueError(f"T20.42a output path is present or aliased: {relative}")
    return json.loads(json.dumps(payload))


def _runtime_snapshot_from_preflight(payload: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(payload, label="T20.42a generation runtime preflight")
    return {
        "source_commit": payload.get("source_commit"),
        "branch": payload.get("branch"),
        "origin_contains_source_commit": payload.get("origin_contains_source_commit"),
        "scoped_dirty_paths": payload.get("scoped_dirty_paths"),
        "dependencies": payload.get("dependencies"),
        "platform": payload.get("platform"),
        "minimum_free_disk_bytes": payload.get("minimum_free_disk_bytes"),
        "free_disk_bytes": payload.get("free_disk_bytes"),
        "network_enabled": payload.get("network_enabled"),
        "dependency_fallback_enabled": payload.get("dependency_fallback_enabled"),
        "authority_artifacts_materialized": payload.get(
            "authority_artifacts_materialized"
        ),
        "attempt_marker_exists": payload.get("attempt_marker_exists"),
        "r0_episode_generation_executed": payload.get("r0_episode_generation_executed"),
        "output_path_state": payload.get("output_path_state"),
    }


def _verify_permit_shell(permit: dict[str, Any]) -> None:
    verify_signed_payload(permit, label="T20.42a generation permit")
    training = permit.get("training_candidate_ids")
    fresh = permit.get("fresh_held_out_candidate_ids")
    if (
        permit.get("schema_version") != PERMIT_SCHEMA_VERSION
        or permit.get("authorized_actions") != list(AUTHORIZED_ACTIONS)
        or permit.get("authorized_attempt_count") != 1
        or not isinstance(training, list)
        or len(training) != 119
        or len(set(training)) != 119
        or not isinstance(fresh, list)
        or len(fresh) != 9
        or len(set(fresh)) != 9
        or set(training) & set(fresh)
        or permit.get("existing_held_out_seeds_referenced_without_regeneration")
        != [6, 7]
        or not isinstance(permit.get("construction_spec_ref"), dict)
        or permit.get("construction_spec_ref", {}).get("identity_sha256")
        != EXPECTED_CONSTRUCTION_IDENTITIES["construction_spec"]
        or permit.get("attempt_marker_path") != ATTEMPT_PATH.as_posix()
        or permit.get("output_paths") != [path.as_posix() for path in OUTPUT_PATHS]
        or permit.get("minimum_new_nominal_successes") != 64
        or permit.get("maximum_new_nominal_successes") != 119
        or permit.get("strict_v2_only_training_admission") is not True
        or permit.get("mean_std_training_rows_only") is not True
        or permit.get("fresh_held_out_training_rows") != 0
        or permit.get("marker_must_precede_first_candidate") is not True
        or permit.get("permit_consumed_by_marker_creation") is not True
        or permit.get("retry_authorized") is not False
        or permit.get("adaptive_manifest_extension_authorized") is not False
    ):
        raise ValueError("T20.42a permit shell drifted")
    _commit(permit.get("required_source_commit"), label="permit source commit")
    _authority_window(permit.get("valid_from"), permit.get("valid_until"))
    for identifier in [*training, *fresh]:
        _sha(identifier, label="permit candidate identity")
    for field in PROHIBITED_AUTHORITY_FIELDS:
        if permit.get(field) is not False:
            raise ValueError(f"T20.42a permit authority escalated: {field}")


def _prospective_artifact_ref(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(payload, label=f"prospective artifact {path}")
    _safe_relative_path(path, label="prospective artifact path")
    formatted = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    return {
        "path": path.as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(formatted).hexdigest(),
    }


def _authority_window(valid_from: Any, valid_until: Any) -> tuple[datetime, datetime]:
    start = _offset_time(valid_from, label="authority valid_from")
    stop = _offset_time(valid_until, label="authority valid_until")
    duration = (stop - start).total_seconds()
    if duration <= 0 or duration > MAXIMUM_AUTHORITY_SECONDS:
        raise ValueError(
            "T20.42a authority window must be positive and at most 8 hours"
        )
    return start, stop


def _offset_time(value: Any, *, label: str) -> datetime:
    text = _nonblank(value, label=label)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"T20.42a {label} is not ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"T20.42a {label} must carry a UTC offset")
    return parsed


def _prohibited_authority_flags() -> dict[str, bool]:
    return {field: False for field in PROHIBITED_AUTHORITY_FIELDS}


def _safe_relative_path(path: Path, *, label: str) -> None:
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"T20.42a {label} is unsafe")


def _reject_existing_symlinks(root: Path, relative: Path) -> None:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError("T20.42 attempt marker path is aliased")


def _commit(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.42a {label} must be a full lowercase commit")
    return value


def _sha(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.42a {label} must be lowercase SHA-256")
    return value


def _nonblank(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"T20.42a {label} must be nonblank")
    return value.strip()
