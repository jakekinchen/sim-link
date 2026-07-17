"""Refresh-only administrative authority for the unconsumed T20.43b attempt.

Epoch 1 remains immutable.  This module can issue only a separately named,
time-bounded epoch 2 for replacement ordinal 1 / attempt ordinal 1 after it
reconstructs epoch 1 and proves that the sole marker and all run outputs remain
absent.  It is model-free and never constructs a policy or optimizer.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

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
from scenesmith.robot_lab.t20_43b_r1_act_contracts import (
    ATTEMPT_PATH,
    AUTHORITY_PATHS,
    BRANCH,
    CHECKPOINT_ROOT,
    CHECKPOINT_SCHEDULE,
    DECISION_PATH,
    EVALUATION_ACTION_STEPS,
    EXPECTED_DEPENDENCIES,
    FAILURE_PATH,
    GATE_A_PATH,
    MAXIMUM_OPTIMIZER_UPDATES,
    MUJOCO_SUPPORT_SITE_PACKAGES,
    OWNER_GRANT_PATH,
    PERMIT_PATH,
    PRE_RUN_ACCEPTANCE_PATH,
    RENDERER_SMOKE_RECEIPT_PATH,
    RESNET18_CACHE_BYTES,
    RESNET18_CACHE_PATH,
    RESNET18_CACHE_SHA256,
    RESULT_PATH,
    RETENTION_PATH,
    ROLLOUT_ROOT,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    RUNTIME_PREFLIGHT_PATH,
    SCORECARD_PATH,
    SPEC_PATH,
    STABLE_RUNNER_INTERPRETER,
    VIDEO_ROOT,
    load_verified_sources,
    verify_pre_run_acceptance,
    verify_spec,
)
from scenesmith.robot_lab.t20_43b_r1_act_materialization import (
    IMPLEMENTATION_SCOPED_PATHS,
    verify_materialized_authority,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "T20.43b"
REFRESH_EPOCH = 2
REPLACEMENT_ORDINAL = 1
ATTEMPT_ORDINAL = 1
MAXIMUM_AUTHORITY_SECONDS = 8 * 60 * 60
MINIMUM_FREE_DISK_BYTES = 10 * 1024**3
REFRESH_OWNER_INSTRUCTION = "resolve this final unresolved question we had"

BASE_SPEC_IDENTITY = "13c5bb4b2cadf8c451a25e7c11e9e0a1d824468f593774fdb60dbf7fa5197461"
BASE_GATE_A_IDENTITY = (
    "ea65f3d1298b936e24c88f5c1e3810eb6cd6c93dc1bc8a088af6323748048798"
)
BASE_RENDERER_SMOKE_IDENTITY = (
    "35224058860ec408fea30e679ad0fdf440364d8ae38c5cb3412446b9c213cbd8"
)
BASE_OWNER_IDENTITY = "09111fcb84dd5554f3d73c7964e94cda3028148c15f3c1e5cdb5789c4b95106f"
BASE_DECISION_IDENTITY = (
    "3b534f91daed81a67fb8d2ad211cdd42855939c58b4df1d153b11e2840e4395b"
)
BASE_RUNTIME_IDENTITY = (
    "549c0db2fa6ee525c02db38aa4f2e0dc566bf6d12a40c6b805905c53ae923df0"
)
BASE_PERMIT_IDENTITY = (
    "c7e8e1ca60007442cf7ec34cf5a56722b768c07d67585f82d8266c09d658f469"
)
BASE_ACCEPTANCE_IDENTITY = (
    "525de8dc417d9522c94573d4b781e8631126c9346029c961821eedbf9b1af772"
)
BASE_CLOSEOUT_REVIEWER_PATH = Path(
    "docs/reviewer-messages/302-close-t20-43b-window-with-unconsumed-permit.md"
)
BASE_CLOSEOUT_REVIEWER_FILE_SHA256 = (
    "e49706f23eeb50ffe7a70cd006a051ecf444f0811009bb31baab3b17629fe403"
)

REFRESH_OWNER_PATH = Path(
    "configurations/robot_lab/t20_43b_r1_act_owner_authorization_epoch_002.json"
)
REFRESH_REQUEST_PATH = Path(
    "configurations/robot_lab/t20_43b_r1_act_authority_request_epoch_002.json"
)
REFRESH_DECISION_PATH = Path(
    "configurations/robot_lab/t20_43b_r1_act_authority_decision_epoch_002.json"
)
REFRESH_RUNTIME_PATH = Path(
    "configurations/robot_lab/t20_43b_r1_act_runtime_preflight_epoch_002.json"
)
REFRESH_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_43b_r1_act_permit_epoch_002.json"
)
REFRESH_ACCEPTANCE_PATH = Path(
    "configurations/robot_lab/t20_43b_r1_act_pre_run_acceptance_epoch_002.json"
)

REFRESH_AUTHORITY_PATHS = (
    REFRESH_OWNER_PATH,
    REFRESH_REQUEST_PATH,
    REFRESH_DECISION_PATH,
    REFRESH_RUNTIME_PATH,
    REFRESH_PERMIT_PATH,
)
REFRESH_OUTPUT_PATHS = (
    ATTEMPT_PATH,
    RESULT_PATH,
    FAILURE_PATH,
    RETENTION_PATH,
    SCORECARD_PATH,
    RUN_ROOT,
    CHECKPOINT_ROOT,
    ROLLOUT_ROOT,
    VIDEO_ROOT,
    RUN_SUMMARY_PATH,
)
BASE_IMMUTABLE_PATHS = (*AUTHORITY_PATHS, PRE_RUN_ACCEPTANCE_PATH)
REFRESH_IMPLEMENTATION_SCOPED_PATHS = (
    *IMPLEMENTATION_SCOPED_PATHS,
    Path("scenesmith/robot_lab/t20_43b_r1_act_authority_refresh.py"),
    Path("scripts/robot_lab/materialize_t20_43b_r1_act_authority_refresh.py"),
    Path("scripts/robot_lab/write_t20_43b_r1_act_refresh_acceptance.py"),
    Path("tests/unit/test_t20_43b_r1_act_authority_refresh.py"),
)

OWNER_SCHEMA_VERSION = "scenesmith.t20_43b_r1_act_owner_authorization_refresh.v1"
RUNTIME_SCHEMA_VERSION = "scenesmith.t20_43b_r1_act_runtime_refresh.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_43b_r1_act_permit_refresh.v1"
ACCEPTANCE_SCHEMA_VERSION = "scenesmith.t20_43b_r1_act_refresh_acceptance.v1"


def build_refresh_owner_grant(
    *,
    spec: dict[str, Any],
    base_bundle: dict[str, dict[str, Any]],
    base_acceptance: dict[str, Any],
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
) -> dict[str, Any]:
    _verify_base_inputs(spec, base_bundle, base_acceptance)
    start, stop = _authority_window(valid_from, valid_until)
    return sign_payload(
        {
            "schema_version": OWNER_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "authorization_id": "t20_43b_attempt_1_administrative_epoch_2",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "refresh_epoch": REFRESH_EPOCH,
            "replacement_ordinal": REPLACEMENT_ORDINAL,
            "attempt_ordinal": ATTEMPT_ORDINAL,
            "refresh_is_second_replacement": False,
            "refresh_is_second_attempt": False,
            "owner_instruction": REFRESH_OWNER_INSTRUCTION,
            "spec_identity_sha256": spec["identity_sha256"],
            "base_owner_grant_identity_sha256": BASE_OWNER_IDENTITY,
            "base_authority_decision_identity_sha256": BASE_DECISION_IDENTITY,
            "base_runtime_preflight_identity_sha256": BASE_RUNTIME_IDENTITY,
            "base_permit_identity_sha256": BASE_PERMIT_IDENTITY,
            "base_acceptance_identity_sha256": BASE_ACCEPTANCE_IDENTITY,
            "base_closeout_reviewer_path": BASE_CLOSEOUT_REVIEWER_PATH.as_posix(),
            "base_closeout_reviewer_file_sha256": (BASE_CLOSEOUT_REVIEWER_FILE_SHA256),
            "required_source_commit": _commit(required_source_commit),
            "authorized_actions": [
                "load_cached_resnet18_backbone",
                "construct_fresh_act_policy",
                "run_act_model_inference",
                "create_adamw_optimizer",
                "execute_exactly_10000_simulation_training_updates",
                "save_fixed_schedule_checkpoints",
                "run_fixed_schedule_dual_semantics_mujoco_evaluations",
                "render_and_retain_signed_mirror_mp4",
            ],
            "authorized_attempt_count": 1,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "retry_or_sweep_authorized": False,
            "correction_objective_authorized": False,
            "threshold_change_authorized": False,
            "simulation_only": True,
            "issued_at": start.isoformat(),
            "valid_from": start.isoformat(),
            "valid_until": stop.isoformat(),
            "maximum_authority_seconds": MAXIMUM_AUTHORITY_SECONDS,
            **_prohibited_grants(),
        }
    )


def verify_refresh_owner_grant(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    base_bundle: dict[str, dict[str, Any]],
    base_acceptance: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.43b epoch-2 owner grant")
    expected = build_refresh_owner_grant(
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
        required_source_commit=payload.get("required_source_commit"),
        valid_from=payload.get("valid_from"),
        valid_until=payload.get("valid_until"),
    )
    if payload != expected:
        raise ValueError("T20.43b epoch-2 owner grant drifted")


def build_refresh_central_authority(
    *,
    sources: dict[str, Any],
    spec: dict[str, Any],
    base_bundle: dict[str, dict[str, Any]],
    owner_grant: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    base_acceptance = load_strict_json(REPO_ROOT / PRE_RUN_ACCEPTANCE_PATH)
    _verify_base_inputs(spec, base_bundle, base_acceptance)
    verify_refresh_owner_grant(
        owner_grant,
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
    )
    gate_a = base_bundle[GATE_A_PATH.as_posix()]
    renderer_smoke = base_bundle[RENDERER_SMOKE_RECEIPT_PATH.as_posix()]
    refs = {
        "owner": _prospective_ref(REFRESH_OWNER_PATH, owner_grant),
        "spec": artifact_ref(path=SPEC_PATH, payload=spec, repo_root=REPO_ROOT),
        "gate_a": artifact_ref(path=GATE_A_PATH, payload=gate_a, repo_root=REPO_ROOT),
        "renderer_smoke": artifact_ref(
            path=RENDERER_SMOKE_RECEIPT_PATH,
            payload=renderer_smoke,
            repo_root=REPO_ROOT,
        ),
        "base_permit": artifact_ref(
            path=PERMIT_PATH,
            payload=base_bundle[PERMIT_PATH.as_posix()],
            repo_root=REPO_ROOT,
        ),
        "r0_result": dict(sources["source_refs"]["r0_result"]),
        "r0_mixture": dict(sources["source_refs"]["r0_mixture"]),
        "r0_statistics": dict(sources["source_refs"]["r0_statistics"]),
        "r0_dataset": dict(sources["source_refs"]["r0_dataset_manifest"]),
        "inherited_decision": dict(sources["source_refs"]["inherited_decision"]),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [
            refs["spec"],
            refs["base_permit"],
            refs["r0_result"],
        ],
        "executable_stack_valid": [
            refs["gate_a"],
            refs["renderer_smoke"],
            refs["spec"],
        ],
        "coordinate_contract_valid": [refs["gate_a"], refs["r0_dataset"]],
        "normalization_contract_valid": [
            refs["gate_a"],
            refs["r0_statistics"],
        ],
        "experience_compiler_valid": [refs["r0_mixture"], refs["r0_dataset"]],
        "required_simulation_properties_available": [
            refs["inherited_decision"],
            refs["gate_a"],
        ],
    }
    requirements = {
        row["prerequisite_id"]: row
        for row in build_authority_contract()["prerequisites"]
    }
    claims = []
    for prerequisite_id, evidence_refs in sorted(evidence.items()):
        requirement = requirements[prerequisite_id]
        provenance = requirement["allowed_provenance_classes"][0]
        claims.append(
            build_capability_claim(
                claim_id=f"t20_43b_epoch_2_{prerequisite_id}",
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
                    "max_age_seconds": MAXIMUM_AUTHORITY_SECONDS,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind="t20_43b_r1_act_epoch_2_evidence",
                        artifact_schema_version=ref["schema_version"],
                        artifact_identity_sha256=ref["identity_sha256"],
                        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                        provenance_class=provenance,
                    )
                    for ref in evidence_refs
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
        decision, request=request, decision_id="simulation_training_ready"
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.43b epoch-2 central authority exceeded simulation")
    return request, decision


def build_refresh_runtime_preflight(
    *,
    spec: dict[str, Any],
    base_bundle: dict[str, dict[str, Any]],
    base_acceptance: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_snapshot: dict[str, Any],
) -> dict[str, Any]:
    _verify_base_inputs(spec, base_bundle, base_acceptance)
    verify_refresh_owner_grant(
        owner_grant,
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
    )
    verify_authority_decision(decision, request=request)
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.43b epoch-2 decision escalated")
    _verify_runtime_snapshot(runtime_snapshot, owner_grant=owner_grant)
    return sign_payload(
        {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "refresh_epoch": REFRESH_EPOCH,
            "replacement_ordinal": REPLACEMENT_ORDINAL,
            "attempt_ordinal": ATTEMPT_ORDINAL,
            "spec_identity_sha256": spec["identity_sha256"],
            "base_permit_identity_sha256": BASE_PERMIT_IDENTITY,
            "base_acceptance_identity_sha256": BASE_ACCEPTANCE_IDENTITY,
            "owner_grant_identity_sha256": owner_grant["identity_sha256"],
            "authority_request_identity_sha256": request["identity_sha256"],
            "authority_decision_identity_sha256": decision["identity_sha256"],
            **runtime_snapshot,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "learned_policy_rollout": False,
            "gate_c_executed": False,
            **_false_authority_fields(),
        }
    )


def verify_refresh_runtime_preflight(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    base_bundle: dict[str, dict[str, Any]],
    base_acceptance: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.43b epoch-2 runtime preflight")
    excluded = {
        "schema_version",
        "task_id",
        "refresh_epoch",
        "replacement_ordinal",
        "attempt_ordinal",
        "spec_identity_sha256",
        "base_permit_identity_sha256",
        "owner_grant_identity_sha256",
        "authority_request_identity_sha256",
        "authority_decision_identity_sha256",
        "identity_sha256",
        "model_constructed",
        "model_loaded",
        "model_inference",
        "optimizer_created",
        "optimizer_training",
        "learned_policy_rollout",
        "gate_c_executed",
        *_false_authority_fields(),
    }
    snapshot = {key: value for key, value in payload.items() if key not in excluded}
    expected = build_refresh_runtime_preflight(
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
        runtime_snapshot=snapshot,
    )
    if payload != expected:
        raise ValueError("T20.43b epoch-2 runtime preflight drifted")


def build_refresh_permit(
    *,
    spec: dict[str, Any],
    base_bundle: dict[str, dict[str, Any]],
    base_acceptance: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_preflight: dict[str, Any],
) -> dict[str, Any]:
    verify_refresh_runtime_preflight(
        runtime_preflight,
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
    )
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "refresh_epoch": REFRESH_EPOCH,
            "replacement_ordinal": REPLACEMENT_ORDINAL,
            "attempt_ordinal": ATTEMPT_ORDINAL,
            "refresh_is_second_replacement": False,
            "refresh_is_second_attempt": False,
            "spec_identity_sha256": spec["identity_sha256"],
            "base_permit_identity_sha256": BASE_PERMIT_IDENTITY,
            "base_acceptance_identity_sha256": BASE_ACCEPTANCE_IDENTITY,
            "owner_grant_identity_sha256": owner_grant["identity_sha256"],
            "authority_decision_identity_sha256": decision["identity_sha256"],
            "runtime_preflight_identity_sha256": runtime_preflight["identity_sha256"],
            "required_source_commit": owner_grant["required_source_commit"],
            "authorized_attempt_count": 1,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "evaluation_action_steps": list(EVALUATION_ACTION_STEPS),
            "attempt_marker_path": ATTEMPT_PATH.as_posix(),
            "marker_precedes_backbone_tensor_read_model_inference_optimizer": True,
            "retry_or_sweep_authorized": False,
            "correction_objective_authorized": False,
            "threshold_change_authorized": False,
            "hardware_authorized": False,
            "network_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "t20_45_authorized": False,
        }
    )


def verify_refresh_permit(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    base_bundle: dict[str, dict[str, Any]],
    base_acceptance: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.43b epoch-2 permit")
    expected = build_refresh_permit(
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.43b epoch-2 permit drifted")


def build_refresh_acceptance(
    *,
    authority_commit: str,
    reviewer_decision_id: str,
    reviewer_path: str,
    reviewer_file_sha256: str,
    permit: dict[str, Any],
) -> dict[str, Any]:
    if (
        permit.get("refresh_epoch") != REFRESH_EPOCH
        or permit.get("replacement_ordinal") != REPLACEMENT_ORDINAL
        or permit.get("attempt_ordinal") != ATTEMPT_ORDINAL
        or permit.get("authorized_attempt_count") != 1
        or permit.get("retry_or_sweep_authorized") is not False
    ):
        raise ValueError("T20.43b epoch-2 acceptance permit drifted")
    return sign_payload(
        {
            "schema_version": ACCEPTANCE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "decision": "ACCEPT_T20_43B_EPOCH_2_ATTEMPT_1",
            "refresh_epoch": REFRESH_EPOCH,
            "replacement_ordinal": REPLACEMENT_ORDINAL,
            "attempt_ordinal": ATTEMPT_ORDINAL,
            "authority_commit": _commit(authority_commit),
            "reviewer_decision_id": str(reviewer_decision_id),
            "reviewer_path": reviewer_path,
            "reviewer_file_sha256": _sha(reviewer_file_sha256),
            "permit_identity_sha256": permit["identity_sha256"],
            "attempt_marker_exists": False,
            "model_or_optimizer_action_executed": False,
            "retry_authorized": False,
            **_false_authority_fields(),
        }
    )


def verify_refresh_acceptance(
    payload: dict[str, Any], *, permit: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.43b epoch-2 acceptance")
    expected = build_refresh_acceptance(
        authority_commit=payload.get("authority_commit"),
        reviewer_decision_id=payload.get("reviewer_decision_id"),
        reviewer_path=payload.get("reviewer_path"),
        reviewer_file_sha256=payload.get("reviewer_file_sha256"),
        permit=permit,
    )
    if payload != expected:
        raise ValueError("T20.43b epoch-2 acceptance drifted")


def materialize_refresh_authority(
    *,
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    sources = load_verified_sources(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_spec(spec, sources=sources)
    base_bundle = verify_materialized_authority(repo_root=root)
    base_acceptance = load_strict_json(root / PRE_RUN_ACCEPTANCE_PATH)
    verify_pre_run_acceptance(
        base_acceptance, permit=base_bundle[PERMIT_PATH.as_posix()]
    )
    if any(
        os.path.lexists(root / path)
        for path in (*REFRESH_AUTHORITY_PATHS, REFRESH_ACCEPTANCE_PATH)
    ):
        raise FileExistsError("T20.43b epoch-2 authority artifact already exists")
    owner = build_refresh_owner_grant(
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    request, decision = build_refresh_central_authority(
        sources=sources,
        spec=spec,
        base_bundle=base_bundle,
        owner_grant=owner,
    )
    snapshot = collect_refresh_runtime_snapshot(
        required_source_commit=required_source_commit,
        repo_root=root,
    )
    runtime = build_refresh_runtime_preflight(
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_snapshot=snapshot,
    )
    permit = build_refresh_permit(
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_preflight=runtime,
    )
    bundle = {
        REFRESH_OWNER_PATH.as_posix(): owner,
        REFRESH_REQUEST_PATH.as_posix(): request,
        REFRESH_DECISION_PATH.as_posix(): decision,
        REFRESH_RUNTIME_PATH.as_posix(): runtime,
        REFRESH_PERMIT_PATH.as_posix(): permit,
    }
    _write_bundle_exclusively(bundle, repo_root=root)
    verify_refresh_authority(repo_root=root)
    return bundle


def verify_refresh_authority(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    sources = load_verified_sources(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_spec(spec, sources=sources)
    base_bundle = verify_materialized_authority(repo_root=root)
    base_acceptance = load_strict_json(root / PRE_RUN_ACCEPTANCE_PATH)
    verify_pre_run_acceptance(
        base_acceptance, permit=base_bundle[PERMIT_PATH.as_posix()]
    )
    bundle = {
        path.as_posix(): load_strict_json(root / path)
        for path in REFRESH_AUTHORITY_PATHS
    }
    owner = bundle[REFRESH_OWNER_PATH.as_posix()]
    request = bundle[REFRESH_REQUEST_PATH.as_posix()]
    decision = bundle[REFRESH_DECISION_PATH.as_posix()]
    runtime = bundle[REFRESH_RUNTIME_PATH.as_posix()]
    permit = bundle[REFRESH_PERMIT_PATH.as_posix()]
    verify_refresh_owner_grant(
        owner,
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
    )
    expected_request, expected_decision = build_refresh_central_authority(
        sources=sources,
        spec=spec,
        base_bundle=base_bundle,
        owner_grant=owner,
    )
    if request != expected_request or decision != expected_decision:
        raise ValueError("T20.43b epoch-2 central authority drifted")
    verify_refresh_permit(
        permit,
        spec=spec,
        base_bundle=base_bundle,
        base_acceptance=base_acceptance,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_preflight=runtime,
    )
    return bundle


def verify_effective_refresh_authority(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    bundle = verify_refresh_authority(repo_root=root)
    acceptance = load_strict_json(root / REFRESH_ACCEPTANCE_PATH)
    verify_refresh_acceptance(acceptance, permit=bundle[REFRESH_PERMIT_PATH.as_posix()])
    return {**bundle, REFRESH_ACCEPTANCE_PATH.as_posix(): acceptance}


def collect_refresh_runtime_snapshot(
    *, required_source_commit: str, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    if Path(sys.executable).resolve() != (root / STABLE_RUNNER_INTERPRETER).resolve():
        raise ValueError("T20.43b epoch-2 materializer interpreter drifted")
    head = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    if branch != BRANCH:
        raise ValueError("T20.43b epoch-2 branch drifted")
    _require_ancestor(root, required_source_commit, head)
    _require_ancestor(root, head, f"refs/remotes/origin/{BRANCH}")
    dirty = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *[path.as_posix() for path in REFRESH_IMPLEMENTATION_SCOPED_PATHS],
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    scoped_dirty = sorted(line[3:] for line in dirty.splitlines() if len(line) >= 4)
    diff = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--quiet",
            required_source_commit,
            head,
            "--",
            *[path.as_posix() for path in REFRESH_IMPLEMENTATION_SCOPED_PATHS],
        ],
        check=False,
    )
    if diff.returncode != 0:
        raise ValueError("T20.43b epoch-2 reviewed implementation changed")
    if _sha_file(RESNET18_CACHE_PATH) != RESNET18_CACHE_SHA256:
        raise ValueError("T20.43b epoch-2 cached backbone drifted")
    base_bundle = verify_materialized_authority(repo_root=root)
    base_acceptance = load_strict_json(root / PRE_RUN_ACCEPTANCE_PATH)
    verify_pre_run_acceptance(
        base_acceptance, permit=base_bundle[PERMIT_PATH.as_posix()]
    )
    output_state = {
        path.as_posix(): {
            "exists": os.path.lexists(root / path),
            "is_symlink": _path_or_parent_is_symlink(root, path),
        }
        for path in REFRESH_OUTPUT_PATHS
    }
    if any(
        row != {"exists": False, "is_symlink": False} for row in output_state.values()
    ):
        raise FileExistsError("T20.43b epoch-2 marker/output path is not absent")
    return {
        "source_commit": required_source_commit,
        "branch": branch,
        "origin_contains_source_commit": True,
        "scoped_dirty_paths": scoped_dirty,
        "dependencies": _dependency_versions(),
        "mps_available": _mps_available(),
        "free_disk_bytes": shutil.disk_usage(root).free,
        "network_enabled": False,
        "dependency_fallback_enabled": False,
        "cached_backbone_file_sha256": RESNET18_CACHE_SHA256,
        "cached_backbone_size_bytes": RESNET18_CACHE_BYTES,
        "mujoco_support_site_packages": str(MUJOCO_SUPPORT_SITE_PACKAGES),
        "mujoco_support_tree_identity_sha256": _tree_identity(
            MUJOCO_SUPPORT_SITE_PACKAGES
        ),
        "renderer_smoke_identity_sha256": BASE_RENDERER_SMOKE_IDENTITY,
        "renderer_interpreter": STABLE_RUNNER_INTERPRETER.as_posix(),
        "renderer_interpreter_matches_runner": True,
        "renderer_smoke_exit_code": 0,
        "base_artifact_file_sha256": {
            path.as_posix(): _sha_file(root / path) for path in BASE_IMMUTABLE_PATHS
        },
        "base_closeout_reviewer_file_sha256": _sha_file(
            root / BASE_CLOSEOUT_REVIEWER_PATH
        ),
        "base_acceptance_identity_sha256": base_acceptance["identity_sha256"],
        "output_path_state": output_state,
        "attempt_marker_exists": False,
    }


def _verify_base_inputs(
    spec: dict[str, Any],
    base_bundle: dict[str, dict[str, Any]],
    base_acceptance: dict[str, Any],
) -> None:
    verify_signed_payload(spec, label="T20.43b epoch-2 base spec")
    exact = {
        GATE_A_PATH.as_posix(): BASE_GATE_A_IDENTITY,
        RENDERER_SMOKE_RECEIPT_PATH.as_posix(): BASE_RENDERER_SMOKE_IDENTITY,
        OWNER_GRANT_PATH.as_posix(): BASE_OWNER_IDENTITY,
        DECISION_PATH.as_posix(): BASE_DECISION_IDENTITY,
        RUNTIME_PREFLIGHT_PATH.as_posix(): BASE_RUNTIME_IDENTITY,
        PERMIT_PATH.as_posix(): BASE_PERMIT_IDENTITY,
    }
    if spec.get("identity_sha256") != BASE_SPEC_IDENTITY:
        raise ValueError("T20.43b epoch-2 base spec drifted")
    for path, identity in exact.items():
        if base_bundle.get(path, {}).get("identity_sha256") != identity:
            raise ValueError(f"T20.43b epoch-2 base artifact drifted: {path}")
    verify_pre_run_acceptance(
        base_acceptance, permit=base_bundle[PERMIT_PATH.as_posix()]
    )
    if base_acceptance.get("identity_sha256") != BASE_ACCEPTANCE_IDENTITY:
        raise ValueError("T20.43b epoch-2 base acceptance drifted")


def _verify_runtime_snapshot(
    snapshot: dict[str, Any], *, owner_grant: dict[str, Any]
) -> None:
    required = {
        "source_commit",
        "branch",
        "origin_contains_source_commit",
        "scoped_dirty_paths",
        "dependencies",
        "mps_available",
        "free_disk_bytes",
        "network_enabled",
        "dependency_fallback_enabled",
        "cached_backbone_file_sha256",
        "cached_backbone_size_bytes",
        "mujoco_support_site_packages",
        "mujoco_support_tree_identity_sha256",
        "renderer_smoke_identity_sha256",
        "renderer_interpreter",
        "renderer_interpreter_matches_runner",
        "renderer_smoke_exit_code",
        "base_artifact_file_sha256",
        "base_closeout_reviewer_file_sha256",
        "base_acceptance_identity_sha256",
        "output_path_state",
        "attempt_marker_exists",
    }
    if set(snapshot) != required:
        raise ValueError("T20.43b epoch-2 runtime field set drifted")
    if (
        snapshot["source_commit"] != owner_grant["required_source_commit"]
        or snapshot["branch"] != BRANCH
        or snapshot["origin_contains_source_commit"] is not True
        or snapshot["scoped_dirty_paths"] != []
        or snapshot["dependencies"] != EXPECTED_DEPENDENCIES
        or snapshot["mps_available"] is not True
        or snapshot["free_disk_bytes"] < MINIMUM_FREE_DISK_BYTES
        or snapshot["network_enabled"] is not False
        or snapshot["dependency_fallback_enabled"] is not False
        or snapshot["cached_backbone_file_sha256"] != RESNET18_CACHE_SHA256
        or snapshot["cached_backbone_size_bytes"] != RESNET18_CACHE_BYTES
        or snapshot["mujoco_support_site_packages"] != str(MUJOCO_SUPPORT_SITE_PACKAGES)
        or snapshot["renderer_smoke_identity_sha256"] != BASE_RENDERER_SMOKE_IDENTITY
        or snapshot["renderer_interpreter"] != STABLE_RUNNER_INTERPRETER.as_posix()
        or snapshot["renderer_interpreter_matches_runner"] is not True
        or snapshot["renderer_smoke_exit_code"] != 0
        or snapshot["base_closeout_reviewer_file_sha256"]
        != BASE_CLOSEOUT_REVIEWER_FILE_SHA256
        or snapshot["base_acceptance_identity_sha256"] != BASE_ACCEPTANCE_IDENTITY
        or snapshot["attempt_marker_exists"] is not False
    ):
        raise ValueError("T20.43b epoch-2 runtime facts failed closed")
    _sha(snapshot["mujoco_support_tree_identity_sha256"])
    expected_base_files = {
        path.as_posix(): _sha_file(REPO_ROOT / path) for path in BASE_IMMUTABLE_PATHS
    }
    if snapshot["base_artifact_file_sha256"] != expected_base_files:
        raise ValueError("T20.43b epoch-2 immutable base bytes drifted")
    expected_outputs = {path.as_posix() for path in REFRESH_OUTPUT_PATHS}
    if set(snapshot["output_path_state"]) != expected_outputs or any(
        row != {"exists": False, "is_symlink": False}
        for row in snapshot["output_path_state"].values()
    ):
        raise ValueError("T20.43b epoch-2 output paths failed closed")


def _write_bundle_exclusively(
    bundle: dict[str, dict[str, Any]], *, repo_root: Path
) -> None:
    root = Path(repo_root).resolve()
    if list(bundle) != [path.as_posix() for path in REFRESH_AUTHORITY_PATHS]:
        raise ValueError("T20.43b epoch-2 authority bundle order drifted")
    for relative in REFRESH_AUTHORITY_PATHS:
        target = root / relative
        if os.path.lexists(target) or _path_or_parent_is_symlink(root, relative):
            raise FileExistsError(f"T20.43b epoch-2 unsafe target: {relative}")
    for relative in REFRESH_AUTHORITY_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = (
            json.dumps(
                bundle[relative.as_posix()], indent=2, sort_keys=True, allow_nan=False
            )
            + "\n"
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(target, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())


def _dependency_versions() -> dict[str, str]:
    import datasets
    import lerobot
    import mujoco
    import numpy
    import pyarrow
    import torch
    import torchvision

    from PIL import __version__ as pillow_version

    return {
        "python": platform.python_version(),
        "torch": str(torch.__version__),
        "torchvision": str(torchvision.__version__),
        "datasets": str(datasets.__version__),
        "mujoco": str(mujoco.__version__),
        "numpy": str(numpy.__version__),
        "pillow": str(pillow_version),
        "pyarrow": str(pyarrow.__version__),
        "lerobot": str(lerobot.__version__),
    }


def _mps_available() -> bool:
    import torch

    return bool(torch.backends.mps.is_available())


def _authority_window(valid_from: str, valid_until: str) -> tuple[datetime, datetime]:
    start = _aware_time(valid_from, label="authority start")
    stop = _aware_time(valid_until, label="authority stop")
    seconds = (stop - start).total_seconds()
    if seconds <= 0 or seconds > MAXIMUM_AUTHORITY_SECONDS:
        raise ValueError("T20.43b epoch-2 authority window is invalid")
    return start, stop


def _prospective_ref(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    file_bytes = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    )
    return {
        "path": path.as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
    }


def _prohibited_grants() -> dict[str, bool]:
    return {
        "hardware_authorized": False,
        "camera_authorized": False,
        "serial_authorized": False,
        "physical_motion_authorized": False,
        "network_authorized": False,
        "external_compute_authorized": False,
        "brev_compute_authorized": False,
        "physical_transfer_authorized": False,
        "promotion_authorized": False,
        "t20_45_authorized": False,
    }


def _false_authority_fields() -> dict[str, bool]:
    return {
        "hardware_accessed": False,
        "camera_accessed": False,
        "serial_accessed": False,
        "physical_motion": False,
        "physical_actuation": False,
        "network_accessed": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "physical_transfer_ready": False,
        "promotion_eligible": False,
        "t20_45_activated": False,
    }


def _path_or_parent_is_symlink(root: Path, relative: Path) -> bool:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False


def _tree_identity(root: Path) -> str:
    rows = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and not path.is_symlink():
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": _sha_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    return hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


def _require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    if (
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "merge-base",
                "--is-ancestor",
                ancestor,
                descendant,
            ],
            check=False,
        ).returncode
        != 0
    ):
        raise ValueError(f"T20.43b epoch-2 ancestry failed: {ancestor} -> {descendant}")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _aware_time(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"T20.43b epoch-2 {label} must be ISO text")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"T20.43b epoch-2 {label} lacks UTC offset")
    return parsed


def _commit(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise ValueError("T20.43b epoch-2 expected a commit")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("T20.43b epoch-2 expected a commit") from error
    return value


def _sha(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("T20.43b epoch-2 expected SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("T20.43b epoch-2 expected SHA-256") from error
    return value


__all__ = [
    "BASE_IMMUTABLE_PATHS",
    "BASE_CLOSEOUT_REVIEWER_FILE_SHA256",
    "REFRESH_ACCEPTANCE_PATH",
    "REFRESH_AUTHORITY_PATHS",
    "REFRESH_DECISION_PATH",
    "REFRESH_IMPLEMENTATION_SCOPED_PATHS",
    "REFRESH_OUTPUT_PATHS",
    "REFRESH_OWNER_INSTRUCTION",
    "REFRESH_OWNER_PATH",
    "REFRESH_PERMIT_PATH",
    "REFRESH_REQUEST_PATH",
    "REFRESH_OUTPUT_PATHS",
    "REFRESH_RUNTIME_PATH",
    "build_refresh_acceptance",
    "build_refresh_central_authority",
    "build_refresh_owner_grant",
    "build_refresh_permit",
    "build_refresh_runtime_preflight",
    "collect_refresh_runtime_snapshot",
    "materialize_refresh_authority",
    "verify_effective_refresh_authority",
    "verify_refresh_acceptance",
    "verify_refresh_authority",
    "verify_refresh_owner_grant",
    "verify_refresh_permit",
    "verify_refresh_runtime_preflight",
]
