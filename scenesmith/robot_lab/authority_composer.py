"""Fail-closed composition of scoped robot-lab evidence into global authority.

Component artifacts may report local facts.  This module is the sole production
path that can emit SceneSmith's global readiness decisions.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.census_runtime_binding import (
    EXPECTED_READ_REGISTER_WIDTHS,
)


AUTHORITY_CONTRACT_SCHEMA_VERSION = "scenesmith.authority_composition_contract.v1"
CAPABILITY_CLAIM_SCHEMA_VERSION = "scenesmith.component_capability_claim.v1"
EVIDENCE_REF_SCHEMA_VERSION = "scenesmith.capability_evidence_ref.v1"
COMPOSITION_REQUEST_SCHEMA_VERSION = "scenesmith.authority_composition_request.v1"
AUTHORITY_DECISION_SCHEMA_VERSION = "scenesmith.authority_composition_decision.v1"
SIMULATION_POLICY_ACCEPTANCE_SCHEMA_VERSION = (
    "scenesmith.simulation_policy_acceptance_decision.v1"
)
T19_1_READONLY_SESSION_REQUEST_SCHEMA_VERSION = (
    "scenesmith.t19_1_readonly_session_request.v1"
)
T19_1_READONLY_SESSION_DECISION_SCHEMA_VERSION = (
    "scenesmith.t19_1_readonly_session_decision.v1"
)
T19_1_READONLY_SESSION_PERMIT_SCHEMA_VERSION = (
    "scenesmith.t19_1_readonly_session_permit.v1"
)
RGB_CAMERA_CENSUS_REQUEST_SCHEMA_VERSION = (
    "scenesmith.rgb_camera_census_request.v1"
)
RGB_CAMERA_CENSUS_DECISION_SCHEMA_VERSION = (
    "scenesmith.rgb_camera_census_decision.v1"
)
RGB_CAMERA_CENSUS_PERMIT_SCHEMA_VERSION = (
    "scenesmith.rgb_camera_census_permit.v1"
)

DEFAULT_AUTHORITY_CONTRACT_PATH = Path(
    "configurations/robot_lab/pi05_authority_composition_contract.json"
)
DEFAULT_AUTHORITY_DECISION_PATH = Path(
    "configurations/robot_lab/pi05_authority_decision.fixture_denied.json"
)
DEFAULT_AUTHORITY_SUBJECT_ID = "pi05_so101_sorting_system"
DEFAULT_AUTHORITY_SCOPE_ID = "pi05_so101_authority"
DEFAULT_EVALUATION_TIME = "2026-07-11T02:14:07-05:00"
DEFAULT_T20_8_EVALUATION_TIME = "2026-07-14T09:30:00-05:00"
DEFAULT_T20_8_RUN_ROOT = Path(
    "outputs/robot_lab/t20_7_four_model_training_run_001"
)
REQUIRED_POLICY_ACCEPTANCE_REPEAT_COUNT = 3
T19_1_MAX_SESSION_SECONDS = 300
T19_1_MAX_REGISTER_READ_COUNT = 54
T19_1_READ_PLAN = tuple(
    {
        "register": register,
        "width_bytes": width_bytes,
        "servo_ids": list(range(1, 7)),
    }
    for register, width_bytes in EXPECTED_READ_REGISTER_WIDTHS.items()
)
T19_1_READONLY_ALLOWED_OPERATIONS = (
    "serial_metadata_enumeration",
    "serial_identity_holder_snapshot",
    "serial_connect_without_handshake",
    "scalar_allowlisted_register_read",
    "serial_disconnect_without_torque_change",
)
T19_1_READONLY_AUTHORITY_NOT_GRANTED = (
    "camera_access",
    "register_write",
    "torque_change",
    "motion",
    "calibration",
    "policy_actuation",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "external_compute",
    "brev_compute",
)
RGB_CAMERA_CENSUS_MAX_SESSION_SECONDS = 600
RGB_CAMERA_CENSUS_ALLOWED_OPERATIONS = (
    "camera_metadata_enumeration",
    "named_avfoundation_rgb_open",
    "one_png_frame_capture_per_camera",
    "named_avfoundation_rgb_close",
)
RGB_CAMERA_CENSUS_TARGETS = (
    {
        "camera_role": "d405_uvc_rgb",
        "required_name_substring": "RealSense",
        "required_model_substrings": ["VendorID_32902", "ProductID_2907"],
    },
    {
        "camera_role": "c922_rgb",
        "required_name_substring": "C922",
        "required_model_substrings": [],
    },
)
RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED = (
    "depth_stream",
    "librealsense",
    "serial_access",
    "register_read",
    "register_write",
    "torque_change",
    "motion",
    "audio_capture",
    "calibration",
    "clock_synchronization",
    "inference",
    "optimizer_training",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "external_compute",
    "brev_compute",
)

GLOBAL_DECISION_IDS = (
    "simulation_training_ready",
    "physical_transfer_ready",
    "promotion_eligible",
)

SIMULATION_PREREQUISITES = (
    "required_training_authority_present",
    "structural_contract_valid",
    "executable_stack_valid",
    "coordinate_contract_valid",
    "normalization_contract_valid",
    "experience_compiler_valid",
    "required_simulation_properties_available",
)
PHYSICAL_PREREQUISITES = (
    "physical_hardware_identity_verified",
    "actuator_and_timing_qualification_passed",
    "camera_qualification_passed",
    "contact_qualification_passed",
    "held_out_twin_metrics_passed",
)
PROMOTION_PREREQUISITES = (
    "policy_artifact_and_training_provenance_valid",
    "appropriate_evaluation_tier_passed",
    "required_deployment_authority_present",
    "no_safety_or_proof_state_violation",
)
LOCAL_CAPABILITY_IDS = (
    "artifact_schema_valid",
    "inertial_compilation_valid",
    "inertial_model_usable_for_simulation",
    "physical_measurement_evidence_verified",
)

PROVENANCE_CLASSES = (
    "repository",
    "simulation",
    "synthetic",
    "fixture",
    "replay",
    "physical",
    "policy_evaluation",
    "deployment_authority",
    "safety_review",
)

FORBIDDEN_COMPONENT_FIELDS = (
    "authority",
    "physical_qualification_authority",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "training_or_promotion_authority",
)

DENIAL_REASONS = {
    "CLAIM_FALSE": "The scoped component capability was explicitly false.",
    "EVIDENCE_EXPIRED": "The claim validity interval ended before composition.",
    "EVIDENCE_NOT_YET_VALID": "The claim was not valid at composition time.",
    "EVIDENCE_STALE": "The evidence exceeded its declared freshness window.",
    "EVIDENCE_SUBSTITUTION": "Evidence metadata did not bind to the claim subject, scope, or provenance.",
    "FORGED_GLOBAL_AUTHORITY_FIELD": "A component payload carried a forbidden global-authority field.",
    "ISSUER_NOT_AUTHORIZED": "The claim issuer was not authorized for the prerequisite.",
    "MISSING_PREREQUISITE": "One or more required prerequisite facts were not satisfied.",
    "NON_AUTHORIZING_COMPOSITION_MODE": "The composition was explicitly generated as non-authorizing fixture evidence.",
    "PROVENANCE_CLASS_NOT_ALLOWED": "The evidence provenance class was not allowed for the prerequisite.",
    "SCOPE_MISMATCH": "The claim scope did not match the composition scope.",
    "SUBJECT_MISMATCH": "The claim subject did not match the composition subject.",
    "UPSTREAM_DECISION_DENIED": "A prerequisite global decision was denied.",
}

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def build_authority_contract() -> dict[str, Any]:
    authorities = _authority_registry()
    prerequisites = [
        _prerequisite(
            prerequisite_id="required_training_authority_present",
            provenance=("deployment_authority",),
            issuers=("scenesmith.deployment_authority.v1",),
            authorities=authorities,
        ),
        _prerequisite(
            prerequisite_id="structural_contract_valid",
            provenance=("repository", "simulation"),
            issuers=("scenesmith.repository_verifier.v1",),
            authorities=authorities,
        ),
        _prerequisite(
            prerequisite_id="executable_stack_valid",
            provenance=("repository",),
            issuers=("scenesmith.repository_verifier.v1",),
            authorities=authorities,
        ),
        _prerequisite(
            prerequisite_id="coordinate_contract_valid",
            provenance=("repository", "simulation"),
            issuers=("scenesmith.repository_verifier.v1",),
            authorities=authorities,
        ),
        _prerequisite(
            prerequisite_id="normalization_contract_valid",
            provenance=("repository", "simulation"),
            issuers=("scenesmith.repository_verifier.v1",),
            authorities=authorities,
        ),
        _prerequisite(
            prerequisite_id="experience_compiler_valid",
            provenance=("repository", "simulation"),
            issuers=("scenesmith.repository_verifier.v1",),
            authorities=authorities,
        ),
        _prerequisite(
            prerequisite_id="required_simulation_properties_available",
            provenance=("simulation",),
            issuers=("scenesmith.simulation_qualification_authority.v1",),
            authorities=authorities,
        ),
    ]
    prerequisites.extend(
        _prerequisite(
            prerequisite_id=prerequisite_id,
            provenance=("physical",),
            issuers=("scenesmith.physical_qualification_authority.v1",),
            authorities=authorities,
        )
        for prerequisite_id in PHYSICAL_PREREQUISITES
    )
    prerequisites.extend(
        [
            _prerequisite(
                prerequisite_id="policy_artifact_and_training_provenance_valid",
                provenance=("policy_evaluation",),
                issuers=("scenesmith.policy_evaluation_authority.v1",),
                authorities=authorities,
            ),
            _prerequisite(
                prerequisite_id="appropriate_evaluation_tier_passed",
                provenance=("policy_evaluation",),
                issuers=("scenesmith.policy_evaluation_authority.v1",),
                authorities=authorities,
            ),
            _prerequisite(
                prerequisite_id="required_deployment_authority_present",
                provenance=("deployment_authority",),
                issuers=("scenesmith.deployment_authority.v1",),
                authorities=authorities,
            ),
            _prerequisite(
                prerequisite_id="no_safety_or_proof_state_violation",
                provenance=("safety_review",),
                issuers=("scenesmith.safety_authority.v1",),
                authorities=authorities,
            ),
        ]
    )
    capability_ids = sorted(
        set(LOCAL_CAPABILITY_IDS)
        | set(SIMULATION_PREREQUISITES)
        | set(PHYSICAL_PREREQUISITES)
        | set(PROMOTION_PREREQUISITES)
    )
    payload = {
        "schema_version": AUTHORITY_CONTRACT_SCHEMA_VERSION,
        "contract_id": "pi05_so101_central_authority_composition",
        "capabilities": [
            {
                "capability_id": capability_id,
                "kind": (
                    "local_component_fact"
                    if capability_id in LOCAL_CAPABILITY_IDS
                    else "global_prerequisite_fact"
                ),
            }
            for capability_id in capability_ids
        ],
        "provenance_classes": list(PROVENANCE_CLASSES),
        "issuer_registry": [authorities[key] for key in sorted(authorities)],
        "prerequisites": prerequisites,
        "global_decisions": [
            {
                "decision_id": "simulation_training_ready",
                "expression": _all_expression("prerequisite", SIMULATION_PREREQUISITES),
            },
            {
                "decision_id": "physical_transfer_ready",
                "expression": {
                    "operator": "all",
                    "terms": [
                        {"kind": "decision", "id": "simulation_training_ready"},
                        *[
                            {"kind": "prerequisite", "id": prerequisite_id}
                            for prerequisite_id in PHYSICAL_PREREQUISITES
                        ],
                    ],
                },
            },
            {
                "decision_id": "promotion_eligible",
                "expression": _all_expression("prerequisite", PROMOTION_PREREQUISITES),
            },
        ],
        "denial_reasons": dict(sorted(DENIAL_REASONS.items())),
        "forbidden_component_fields": list(FORBIDDEN_COMPONENT_FIELDS),
    }
    return sign_payload(payload)


def validate_authority_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != AUTHORITY_CONTRACT_SCHEMA_VERSION:
        raise ValueError("Unsupported authority composition contract schema")
    verify_signed_payload(payload, label="Authority composition contract")
    capability_items = payload.get("capabilities")
    if not isinstance(capability_items, list) or not capability_items:
        raise ValueError("Authority contract capabilities are required")
    capability_ids: set[str] = set()
    for item in capability_items:
        if not isinstance(item, dict) or set(item) != {"capability_id", "kind"}:
            raise ValueError("Authority contract capability definitions are malformed")
        capability_id = _identifier(item.get("capability_id"), label="capability_id")
        if capability_id in capability_ids:
            raise ValueError(f"Duplicate capability_id: {capability_id}")
        capability_ids.add(capability_id)
        if item.get("kind") not in {"local_component_fact", "global_prerequisite_fact"}:
            raise ValueError(f"Unknown capability kind: {capability_id}")

    declared_provenance = payload.get("provenance_classes")
    if declared_provenance != list(PROVENANCE_CLASSES):
        raise ValueError("Authority contract provenance classes drifted")
    registry = _validate_issuer_registry(payload.get("issuer_registry"))

    prerequisite_items = payload.get("prerequisites")
    if not isinstance(prerequisite_items, list) or not prerequisite_items:
        raise ValueError("Authority contract prerequisites are required")
    prerequisite_ids: set[str] = set()
    for item in prerequisite_items:
        if not isinstance(item, dict) or set(item) != {
            "prerequisite_id",
            "capability_id",
            "allowed_provenance_classes",
            "authorized_issuers",
        }:
            raise ValueError("Authority contract prerequisite definition is malformed")
        prerequisite_id = _identifier(item.get("prerequisite_id"), label="prerequisite_id")
        if prerequisite_id in prerequisite_ids:
            raise ValueError(f"Duplicate prerequisite_id: {prerequisite_id}")
        prerequisite_ids.add(prerequisite_id)
        if item.get("capability_id") not in capability_ids:
            raise ValueError(f"Prerequisite references unknown capability: {prerequisite_id}")
        provenance = item.get("allowed_provenance_classes")
        if not isinstance(provenance, list) or not provenance:
            raise ValueError(f"Prerequisite provenance is missing: {prerequisite_id}")
        if len(set(provenance)) != len(provenance):
            raise ValueError(f"Duplicate prerequisite provenance: {prerequisite_id}")
        if any(value not in PROVENANCE_CLASSES for value in provenance):
            raise ValueError(f"Unknown prerequisite provenance: {prerequisite_id}")
        issuers = item.get("authorized_issuers")
        if not isinstance(issuers, list) or not issuers:
            raise ValueError(f"Prerequisite authorized issuer is missing: {prerequisite_id}")
        for issuer in issuers:
            if not isinstance(issuer, dict):
                raise ValueError(f"Prerequisite authorized issuer is malformed: {prerequisite_id}")
            authority_id = issuer.get("authority_id")
            if authority_id not in registry or issuer != registry[authority_id]:
                raise ValueError(f"Prerequisite authorized issuer is unknown: {prerequisite_id}")

    decisions = payload.get("global_decisions")
    if not isinstance(decisions, list) or not decisions:
        raise ValueError("Authority contract global decisions are required")
    decision_ids: set[str] = set()
    for item in decisions:
        if not isinstance(item, dict) or set(item) != {"decision_id", "expression"}:
            raise ValueError("Global decision definition is malformed")
        decision_id = _identifier(item.get("decision_id"), label="decision_id")
        if decision_id in decision_ids:
            raise ValueError(f"Duplicate global decision: {decision_id}")
        decision_ids.add(decision_id)
    if tuple(item["decision_id"] for item in decisions) != GLOBAL_DECISION_IDS:
        raise ValueError("Global decision identifiers or ordering drifted")

    graph: dict[str, set[str]] = {}
    for item in decisions:
        graph[item["decision_id"]] = _validate_expression(
            item["expression"],
            prerequisite_ids=prerequisite_ids,
            decision_ids=decision_ids,
        )
    _reject_decision_cycles(graph)
    if payload.get("denial_reasons") != dict(sorted(DENIAL_REASONS.items())):
        raise ValueError("Authority contract denial reasons drifted")
    if payload.get("forbidden_component_fields") != list(FORBIDDEN_COMPONENT_FIELDS):
        raise ValueError("Authority contract forbidden component fields drifted")


def verify_authority_contract(payload: dict[str, Any]) -> None:
    validate_authority_contract(payload)
    if payload != build_authority_contract():
        raise ValueError("Authority composition contract drifted from production definition")


def build_evidence_ref(
    *,
    artifact_kind: str,
    artifact_schema_version: str,
    artifact_identity_sha256: str,
    subject_id: str,
    scope_id: str,
    provenance_class: str,
) -> dict[str, Any]:
    payload = {
        "schema_version": EVIDENCE_REF_SCHEMA_VERSION,
        "artifact_kind": require_nonblank(artifact_kind, label="artifact_kind"),
        "artifact_schema_version": require_nonblank(
            artifact_schema_version,
            label="artifact_schema_version",
        ),
        "artifact_identity_sha256": _sha256(
            artifact_identity_sha256,
            label="artifact_identity_sha256",
        ),
        "subject_id": require_nonblank(subject_id, label="evidence subject_id"),
        "scope_id": require_nonblank(scope_id, label="evidence scope_id"),
        "provenance_class": _provenance(provenance_class),
    }
    payload["evidence_identity_sha256"] = _content_identity(payload)
    return payload


def build_capability_claim(
    *,
    claim_id: str,
    capability_id: str,
    value: bool,
    subject_id: str,
    scope_id: str,
    provenance_class: str,
    issuer: dict[str, Any],
    validity: dict[str, Any],
    evidence_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    copied_evidence = json.loads(json.dumps(evidence_refs))
    copied_evidence.sort(key=lambda item: str(item.get("evidence_identity_sha256", "")))
    payload = {
        "schema_version": CAPABILITY_CLAIM_SCHEMA_VERSION,
        "claim_id": _identifier(claim_id, label="claim_id"),
        "capability_id": _identifier(capability_id, label="capability_id"),
        "value": value,
        "subject_id": require_nonblank(subject_id, label="claim subject_id"),
        "scope_id": require_nonblank(scope_id, label="claim scope_id"),
        "provenance_class": _provenance(provenance_class),
        "issuer": json.loads(json.dumps(issuer)),
        "validity": json.loads(json.dumps(validity)),
        "evidence_refs": copied_evidence,
    }
    signed = sign_payload(payload)
    validate_capability_claim(signed, known_capability_ids=_known_capability_ids())
    return signed


def validate_capability_claim(
    payload: dict[str, Any],
    *,
    known_capability_ids: set[str],
) -> None:
    allowed_fields = {
        "schema_version",
        "claim_id",
        "capability_id",
        "value",
        "subject_id",
        "scope_id",
        "provenance_class",
        "issuer",
        "validity",
        "evidence_refs",
        "identity_sha256",
    }
    if set(payload) != allowed_fields:
        raise ValueError("Capability claim fields are malformed or ambiguous")
    if payload.get("schema_version") != CAPABILITY_CLAIM_SCHEMA_VERSION:
        raise ValueError("Unsupported capability claim schema")
    verify_signed_payload(payload, label="Capability claim")
    _identifier(payload.get("claim_id"), label="claim_id")
    capability_id = _identifier(payload.get("capability_id"), label="capability_id")
    if capability_id not in known_capability_ids:
        raise ValueError(f"Unknown capability: {capability_id}")
    if not isinstance(payload.get("value"), bool):
        raise ValueError(f"Capability claim value must be boolean: {capability_id}")
    require_nonblank(payload.get("subject_id"), label="claim subject_id")
    require_nonblank(payload.get("scope_id"), label="claim scope_id")
    _provenance(payload.get("provenance_class"))
    _validate_issuer(payload.get("issuer"))
    _validate_validity(payload.get("validity"))
    evidence_refs = payload.get("evidence_refs")
    if not isinstance(evidence_refs, list):
        raise ValueError(f"Capability claim evidence_refs must be a list: {capability_id}")
    if payload["value"] and not evidence_refs:
        raise ValueError(f"Positive capability claim requires evidence: {capability_id}")
    identities: set[str] = set()
    for evidence in evidence_refs:
        _validate_evidence_ref(evidence)
        identity = evidence["evidence_identity_sha256"]
        if identity in identities:
            raise ValueError(f"Duplicate capability evidence identity: {identity}")
        identities.add(identity)


def build_composition_request(
    *,
    subject_id: str,
    scope_id: str,
    evaluation_time: str,
    claims: list[dict[str, Any]],
    composition_mode: str = "production",
) -> dict[str, Any]:
    contract = build_authority_contract()
    copied_claims = json.loads(json.dumps(claims))
    _validate_claim_set(copied_claims, contract=contract)
    copied_claims.sort(
        key=lambda claim: (
            claim["capability_id"],
            claim["claim_id"],
            claim["identity_sha256"],
        )
    )
    payload = {
        "schema_version": COMPOSITION_REQUEST_SCHEMA_VERSION,
        "contract_ref": {
            "schema_version": contract["schema_version"],
            "identity_sha256": contract["identity_sha256"],
        },
        "subject_id": require_nonblank(subject_id, label="composition subject_id"),
        "scope_id": require_nonblank(scope_id, label="composition scope_id"),
        "evaluation_time": _canonical_timestamp(evaluation_time, label="evaluation_time"),
        "composition_mode": _composition_mode(composition_mode),
        "claims": copied_claims,
    }
    return sign_payload(payload)


def compose_authority(request: dict[str, Any]) -> dict[str, Any]:
    contract = build_authority_contract()
    _validate_request_shell(request, contract=contract)
    forged_fields = sorted(
        _find_forbidden_fields(request.get("claims"), forbidden=set(FORBIDDEN_COMPONENT_FIELDS))
    )
    mode_denials = (
        {"NON_AUTHORIZING_COMPOSITION_MODE"}
        if request["composition_mode"] == "fixture"
        else set()
    )
    if forged_fields:
        return _compose_validated(
            request,
            contract=contract,
            claims=[],
            rejected_component_fields=forged_fields,
            forced_denial_codes={"FORGED_GLOBAL_AUTHORITY_FIELD"} | mode_denials,
        )
    claims = request.get("claims")
    _validate_claim_set(claims, contract=contract)
    return _compose_validated(
        request,
        contract=contract,
        claims=claims,
        rejected_component_fields=[],
        forced_denial_codes=mode_denials,
    )


def verify_authority_decision(
    payload: dict[str, Any],
    *,
    request: dict[str, Any],
) -> None:
    if payload.get("schema_version") != AUTHORITY_DECISION_SCHEMA_VERSION:
        raise ValueError("Unsupported authority composition decision schema")
    verify_signed_payload(payload, label="Authority composition decision")
    expected_composition_identity = _composition_identity(payload)
    if payload.get("composition_identity_sha256") != expected_composition_identity:
        raise ValueError("Authority composition identity hash is invalid")
    expected = compose_authority(request)
    if payload != expected:
        raise ValueError("Authority composition decision drifted from independent recomputation")


def require_global_decision(
    payload: dict[str, Any],
    *,
    request: dict[str, Any],
    decision_id: str,
) -> None:
    if decision_id not in GLOBAL_DECISION_IDS:
        raise ValueError(f"Unknown global decision: {decision_id}")
    verify_authority_decision(payload, request=request)
    decisions = payload.get("global_decisions")
    if not isinstance(decisions, list):
        raise ValueError("Authority composition decisions are missing")
    result = next((item for item in decisions if item.get("decision_id") == decision_id), None)
    if not isinstance(result, dict) or result.get("granted") is not True:
        raise ValueError(f"Central composer withheld global decision: {decision_id}")


def build_current_authority_decision(
    *,
    repo_root: Path,
    inertial_artifact_path: Path | None = None,
    intake_path: Path | None = None,
    evaluation_time: str = DEFAULT_EVALUATION_TIME,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from scenesmith.robot_lab.measured_inertial_intake import (
        DEFAULT_ASSEMBLY_INERTIALS_PATH,
        DEFAULT_MEASURED_MASS_INTAKE_PATH,
        verify_assembly_inertials,
    )

    selected_artifact_path = inertial_artifact_path or DEFAULT_ASSEMBLY_INERTIALS_PATH
    selected_intake_path = intake_path or DEFAULT_MEASURED_MASS_INTAKE_PATH
    artifact = load_strict_json(_resolve(repo_root, selected_artifact_path))
    verify_assembly_inertials(
        artifact,
        repo_root=repo_root,
        intake_path=_relative_to_repo(repo_root, selected_intake_path),
    )
    claims = _inertial_capability_claims(
        artifact,
        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
    )
    request = build_composition_request(
        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
        evaluation_time=evaluation_time,
        claims=claims,
        composition_mode="fixture",
    )
    return request, compose_authority(request)


def write_authority_artifacts(
    *,
    repo_root: Path,
    contract_path: Path = DEFAULT_AUTHORITY_CONTRACT_PATH,
    decision_path: Path = DEFAULT_AUTHORITY_DECISION_PATH,
) -> dict[str, Any]:
    contract = build_authority_contract()
    _, decision = build_current_authority_decision(repo_root=repo_root)
    dump_canonical_json(_resolve(repo_root, contract_path), contract)
    dump_canonical_json(_resolve(repo_root, decision_path), decision)
    return {"contract": contract, "decision": decision}


def verify_authority_artifacts(
    *,
    repo_root: Path,
    contract_path: Path = DEFAULT_AUTHORITY_CONTRACT_PATH,
    decision_path: Path = DEFAULT_AUTHORITY_DECISION_PATH,
) -> dict[str, Any]:
    contract = load_strict_json(_resolve(repo_root, contract_path))
    decision = load_strict_json(_resolve(repo_root, decision_path))
    verify_authority_contract(contract)
    request, expected_decision = build_current_authority_decision(repo_root=repo_root)
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("Tracked authority decision drifted from current repo artifacts")
    return {"contract": contract, "decision": decision}


def build_simulation_policy_acceptance_decision(
    *,
    repo_root: Path,
    run_root: Path = DEFAULT_T20_8_RUN_ROOT,
    evaluation_time: str = DEFAULT_T20_8_EVALUATION_TIME,
) -> dict[str, Any]:
    """Compose T20.8 only after independently verifying every T20.6/T20.7 source."""

    from scenesmith.robot_lab.model_bakeoff import (
        MODEL_ORDER,
        verify_model_training_gate,
    )
    from scenesmith.robot_lab.model_bakeoff_evaluation import (
        verify_model_evaluation_gate,
    )
    from scenesmith.robot_lab.phase_outcome_evaluation import (
        verify_phase_outcome_fixture,
    )
    from scenesmith.robot_lab.strict_grasp import verify_strict_grasp_v2_fixture

    root = Path(repo_root).resolve()
    runs = _resolve(root, run_root).resolve()
    if not runs.is_relative_to(root):
        raise ValueError("T20.8 run root escapes the repository")
    semantic_path = root / "configurations/robot_lab/t20_6_phase_outcome_evaluation.json"
    strict_path = root / "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json"
    plan_path = root / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
    semantic = load_strict_json(semantic_path)
    strict = load_strict_json(strict_path)
    plan = load_strict_json(plan_path)
    verify_strict_grasp_v2_fixture(strict)
    verify_phase_outcome_fixture(semantic, strict)

    training_gate_path = runs / "run_summary.json"
    evaluation_gate_path = runs / "evaluation_summary.json"
    training_gate = load_strict_json(training_gate_path)
    evaluation_gate = load_strict_json(evaluation_gate_path)
    training_results = []
    evaluation_results = []
    for model_id in MODEL_ORDER:
        model_root = runs / model_id
        training_path = model_root / "run_summary.json"
        evaluation_path = runs / "closed_loop" / f"{model_id}.json"
        training = load_strict_json(training_path)
        evaluation = load_strict_json(evaluation_path)
        _verify_checkpoint_manifest(model_root, training["checkpoint_files"])
        training_file_sha256 = _file_sha256(training_path)
        training_results.append(
            (str(training_path.relative_to(root)), training, training_file_sha256)
        )
        evaluation_results.append(
            (
                str(evaluation_path.relative_to(root)),
                evaluation,
                _file_sha256(evaluation_path),
                training,
                training_file_sha256,
            )
        )
    verify_model_training_gate(training_gate, plan, training_results)
    verify_model_evaluation_gate(
        evaluation_gate,
        plan,
        training_gate,
        evaluation_results,
    )
    sources = {
        "strict_v2": _source_ref(root, strict_path, strict),
        "semantic_fixture": _source_ref(root, semantic_path, semantic),
        "model_bakeoff_plan": _source_ref(root, plan_path, plan),
        "training_gate": _source_ref(root, training_gate_path, training_gate),
        "evaluation_gate": _source_ref(root, evaluation_gate_path, evaluation_gate),
    }
    return _compose_simulation_policy_acceptance_core(
        semantic_fixture=semantic,
        evaluation_gate=evaluation_gate,
        source_evidence=sources,
        evaluation_time=evaluation_time,
    )


def verify_simulation_policy_acceptance_decision(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    run_root: Path = DEFAULT_T20_8_RUN_ROOT,
    evaluation_time: str = DEFAULT_T20_8_EVALUATION_TIME,
) -> None:
    """Recompute the central T20.8 decision from source bytes."""

    if payload.get("schema_version") != SIMULATION_POLICY_ACCEPTANCE_SCHEMA_VERSION:
        raise ValueError("Unsupported simulation policy acceptance decision schema")
    verify_signed_payload(payload, label="Simulation policy acceptance decision")
    expected = build_simulation_policy_acceptance_decision(
        repo_root=repo_root,
        run_root=run_root,
        evaluation_time=evaluation_time,
    )
    if payload != expected:
        raise ValueError("Simulation policy acceptance decision drifted from sources")


def verify_simulation_policy_acceptance_core(
    payload: dict[str, Any],
    *,
    semantic_fixture: dict[str, Any],
    evaluation_gate: dict[str, Any],
    source_evidence: dict[str, Any],
    evaluation_time: str,
) -> None:
    """Reject re-signed policy decisions that differ from mechanical recomposition."""

    verify_signed_payload(payload, label="Simulation policy acceptance decision")
    expected = _compose_simulation_policy_acceptance_core(
        semantic_fixture=semantic_fixture,
        evaluation_gate=evaluation_gate,
        source_evidence=source_evidence,
        evaluation_time=evaluation_time,
    )
    if payload != expected:
        raise ValueError("Simulation policy acceptance core drifted from evidence")


def _compose_simulation_policy_acceptance_core(
    *,
    semantic_fixture: dict[str, Any],
    evaluation_gate: dict[str, Any],
    source_evidence: dict[str, Any],
    evaluation_time: str,
) -> dict[str, Any]:
    """Mechanically derive acceptance after callers verify the supplied evidence."""

    selected_model_id = evaluation_gate.get("winner_model_id")
    model_results = evaluation_gate.get("model_results", [])
    selected = next(
        (item for item in model_results if item.get("model_id") == selected_model_id),
        None,
    )
    measured_repeat_count = (
        1
        if selected is not None
        and selected.get("simulation_semantic_strict_success") is True
        else 0
    )
    criteria = {
        "semantic_contract_conformant": _acceptance_margin(
            int(
                semantic_fixture.get("all_required_adversarial_cases_rejected") is True
                and semantic_fixture.get("positive", {})
                .get("strict_evaluation", {})
                .get("strict_grasp_success")
                is True
            ),
            1,
            "==",
        ),
        "selected_checkpoint_count": _acceptance_margin(
            int(selected is not None), 1, "=="
        ),
        "strict_success_repeat_count": _acceptance_margin(
            measured_repeat_count,
            REQUIRED_POLICY_ACCEPTANCE_REPEAT_COUNT,
            ">=",
        ),
        "selected_projected_action_frames": _acceptance_margin(
            None if selected is None else selected.get("projected_action_frame_count"),
            0,
            "==",
        ),
        "selected_active_assist_frames": _acceptance_margin(
            None if selected is None else selected.get("active_assist_frame_count"),
            0,
            "==",
        ),
        "selected_rendered_keyframe_count": _acceptance_margin(
            None if selected is None else selected.get("rendered_keyframe_count"),
            5,
            "==",
        ),
        "t20_7_strict_success_count": _acceptance_margin(
            evaluation_gate.get("strict_success_count"), 1, ">="
        ),
    }
    accepted = all(value["passed"] for value in criteria.values())
    denial_reasons = [
        name for name, value in criteria.items() if not value["passed"]
    ]
    return sign_payload(
        {
            "schema_version": SIMULATION_POLICY_ACCEPTANCE_SCHEMA_VERSION,
            "task_id": "T20.8",
            "decision_id": "simulation_policy_accepted",
            "composer": "scenesmith.robot_lab.authority_composer",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "evaluation_time": _canonical_timestamp(
                evaluation_time, label="T20.8 evaluation_time"
            ),
            "source_evidence": json.loads(json.dumps(source_evidence)),
            "selected_model_id": selected_model_id,
            "measured_strict_success_rollout_count": measured_repeat_count,
            "required_strict_success_rollout_count": REQUIRED_POLICY_ACCEPTANCE_REPEAT_COUNT,
            "criteria": criteria,
            "denial_reasons": denial_reasons,
            "all_source_evidence_verified": True,
            "terminal_occupancy_sufficient_for_acceptance": False,
            "simulation_policy_accepted": accepted,
            "physical_transfer_eligible": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "authority_granted": ["simulation_policy_accepted"] if accepted else [],
            "authority_withheld": [
                decision_id
                for decision_id, granted in (
                    ("simulation_policy_accepted", accepted),
                    ("physical_transfer_ready", False),
                    ("promotion_eligible", False),
                )
                if not granted
            ],
        }
    )


def _compose_validated(
    request: dict[str, Any],
    *,
    contract: dict[str, Any],
    claims: list[dict[str, Any]],
    rejected_component_fields: list[str],
    forced_denial_codes: set[str],
) -> dict[str, Any]:
    claim_index = {claim["capability_id"]: claim for claim in claims}
    prerequisite_results = {
        spec["prerequisite_id"]: _evaluate_prerequisite(
            spec,
            claim=claim_index.get(spec["capability_id"]),
            request=request,
        )
        for spec in contract["prerequisites"]
    }
    decision_specs = {
        item["decision_id"]: item for item in contract["global_decisions"]
    }
    memo: dict[str, dict[str, Any]] = {}

    def evaluate(decision_id: str) -> dict[str, Any]:
        if decision_id in memo:
            return memo[decision_id]
        spec = decision_specs[decision_id]
        satisfied: set[str] = set()
        missing: set[str] = set()
        reasons: set[str] = set(forced_denial_codes)
        consumed: set[str] = set()
        for term in spec["expression"]["terms"]:
            if term["kind"] == "prerequisite":
                result = prerequisite_results[term["id"]]
                if result["satisfied"]:
                    satisfied.add(term["id"])
                    consumed.update(result["consumed_evidence_identities"])
                else:
                    missing.add(term["id"])
                    reasons.update(result["denial_reason_codes"])
            else:
                upstream = evaluate(term["id"])
                satisfied.update(upstream["satisfied_prerequisite_ids"])
                consumed.update(upstream["consumed_evidence_identities"])
                if not upstream["granted"]:
                    missing.update(upstream["missing_prerequisite_ids"])
                    reasons.update(upstream["denial_reason_codes"])
                    reasons.add("UPSTREAM_DECISION_DENIED")
        granted = not missing and not reasons
        if missing:
            reasons.add("MISSING_PREREQUISITE")
        result = {
            "decision_id": decision_id,
            "granted": granted,
            "evaluated_expression": json.loads(json.dumps(spec["expression"])),
            "satisfied_prerequisite_ids": sorted(satisfied),
            "missing_prerequisite_ids": sorted(missing),
            "denial_reason_codes": sorted(reasons),
            "consumed_evidence_identities": sorted(consumed),
        }
        memo[decision_id] = result
        return result

    global_decisions = [evaluate(decision_id) for decision_id in GLOBAL_DECISION_IDS]
    core = {
        "schema_version": AUTHORITY_DECISION_SCHEMA_VERSION,
        "contract_ref": json.loads(json.dumps(request["contract_ref"])),
        "request_identity_sha256": request["identity_sha256"],
        "subject_id": request["subject_id"],
        "scope_id": request["scope_id"],
        "evaluation_time": request["evaluation_time"],
        "composition_mode": request["composition_mode"],
        "input_claim_identity_sha256s": sorted(
            claim["identity_sha256"] for claim in claims
        ),
        "rejected_component_fields": rejected_component_fields,
        "global_decisions": global_decisions,
        "authority_granted": [
            item["decision_id"] for item in global_decisions if item["granted"]
        ],
        "authority_withheld": [
            item["decision_id"] for item in global_decisions if not item["granted"]
        ],
    }
    core["composition_identity_sha256"] = _content_identity(core)
    return sign_payload(core)


def _evaluate_prerequisite(
    spec: dict[str, Any],
    *,
    claim: dict[str, Any] | None,
    request: dict[str, Any],
) -> dict[str, Any]:
    prerequisite_id = spec["prerequisite_id"]
    if claim is None:
        return {
            "prerequisite_id": prerequisite_id,
            "satisfied": False,
            "denial_reason_codes": ["MISSING_PREREQUISITE"],
            "consumed_evidence_identities": [],
        }
    reasons: set[str] = set()
    if claim["value"] is not True:
        reasons.add("CLAIM_FALSE")
    if claim["subject_id"] != request["subject_id"]:
        reasons.add("SUBJECT_MISMATCH")
    if claim["scope_id"] != request["scope_id"]:
        reasons.add("SCOPE_MISMATCH")
    if claim["provenance_class"] not in spec["allowed_provenance_classes"]:
        reasons.add("PROVENANCE_CLASS_NOT_ALLOWED")
    if claim["issuer"] not in spec["authorized_issuers"]:
        reasons.add("ISSUER_NOT_AUTHORIZED")

    evaluation_time = _parse_timestamp(request["evaluation_time"], label="evaluation_time")
    validity = claim["validity"]
    observed_at = _parse_timestamp(validity["observed_at"], label="observed_at")
    valid_from = _parse_timestamp(validity["valid_from"], label="valid_from")
    valid_until = _parse_timestamp(validity["valid_until"], label="valid_until")
    if evaluation_time < valid_from or evaluation_time < observed_at:
        reasons.add("EVIDENCE_NOT_YET_VALID")
    if evaluation_time > valid_until:
        reasons.add("EVIDENCE_EXPIRED")
    if (evaluation_time - observed_at).total_seconds() > validity["max_age_seconds"]:
        reasons.add("EVIDENCE_STALE")

    for evidence in claim["evidence_refs"]:
        if (
            evidence["subject_id"] != claim["subject_id"]
            or evidence["scope_id"] != claim["scope_id"]
            or evidence["provenance_class"] != claim["provenance_class"]
        ):
            reasons.add("EVIDENCE_SUBSTITUTION")
    consumed = []
    if not reasons:
        consumed = sorted(
            evidence["artifact_identity_sha256"] for evidence in claim["evidence_refs"]
        )
    return {
        "prerequisite_id": prerequisite_id,
        "satisfied": not reasons,
        "denial_reason_codes": sorted(reasons),
        "consumed_evidence_identities": consumed,
    }


def _inertial_capability_claims(
    artifact: dict[str, Any],
    *,
    subject_id: str,
    scope_id: str,
) -> list[dict[str, Any]]:
    capabilities = artifact.get("capabilities")
    if not isinstance(capabilities, dict):
        raise ValueError("Assembly inertials must expose local capabilities")
    if set(capabilities) != set(LOCAL_CAPABILITY_IDS):
        raise ValueError("Assembly inertials local capability set drifted")
    qualification_scope = artifact.get("qualification_scope")
    if qualification_scope in {"synthetic_test_only", "fixture_evidence"}:
        provenance_class = "fixture"
    elif qualification_scope == "physical_measurement_evidence":
        provenance_class = "physical"
    else:
        provenance_class = "repository"
    issuer = _authority_registry()["scenesmith.measured_inertial_compiler.v2"]
    evidence = build_evidence_ref(
        artifact_kind="assembly_inertials",
        artifact_schema_version=artifact["schema_version"],
        artifact_identity_sha256=artifact["identity_sha256"],
        subject_id=subject_id,
        scope_id=scope_id,
        provenance_class=provenance_class,
    )
    validity = {
        "observed_at": "2026-07-11T02:09:58-05:00",
        "valid_from": "2026-07-11T02:09:58-05:00",
        "valid_until": "2026-07-12T02:09:58-05:00",
        "max_age_seconds": 86400,
    }
    claims = []
    for capability_id in LOCAL_CAPABILITY_IDS:
        value = capabilities.get(capability_id)
        if not isinstance(value, bool):
            raise ValueError(f"Assembly inertials capability must be boolean: {capability_id}")
        claims.append(
            build_capability_claim(
                claim_id=f"assembly_inertials_{capability_id}",
                capability_id=capability_id,
                value=value,
                subject_id=subject_id,
                scope_id=scope_id,
                provenance_class=provenance_class,
                issuer=issuer,
                validity=validity,
                evidence_refs=[evidence] if value else [],
            )
        )
    return claims


def _validate_request_shell(request: dict[str, Any], *, contract: dict[str, Any]) -> None:
    allowed_fields = {
        "schema_version",
        "contract_ref",
        "subject_id",
        "scope_id",
        "evaluation_time",
        "composition_mode",
        "claims",
        "identity_sha256",
    }
    if not isinstance(request, dict) or set(request) != allowed_fields:
        raise ValueError("Authority composition request fields are malformed")
    if request.get("schema_version") != COMPOSITION_REQUEST_SCHEMA_VERSION:
        raise ValueError("Unsupported authority composition request schema")
    verify_signed_payload(request, label="Authority composition request")
    expected_ref = {
        "schema_version": contract["schema_version"],
        "identity_sha256": contract["identity_sha256"],
    }
    if request.get("contract_ref") != expected_ref:
        raise ValueError("Authority composition request contract reference drifted")
    require_nonblank(request.get("subject_id"), label="composition subject_id")
    require_nonblank(request.get("scope_id"), label="composition scope_id")
    _canonical_timestamp(request.get("evaluation_time"), label="evaluation_time")
    _composition_mode(request.get("composition_mode"))
    if not isinstance(request.get("claims"), list):
        raise ValueError("Authority composition request claims must be a list")


def _validate_claim_set(claims: Any, *, contract: dict[str, Any]) -> None:
    if not isinstance(claims, list):
        raise ValueError("Authority composition request claims must be a list")
    known = {item["capability_id"] for item in contract["capabilities"]}
    claim_ids: set[str] = set()
    identities: set[str] = set()
    by_capability: dict[str, dict[str, Any]] = {}
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("Capability claims must be objects")
        validate_capability_claim(claim, known_capability_ids=known)
        claim_id = claim["claim_id"]
        identity = claim["identity_sha256"]
        if identity in identities:
            raise ValueError(f"Duplicate claim identity: {identity}")
        identities.add(identity)
        if claim_id in claim_ids:
            raise ValueError(f"Duplicate claim_id: {claim_id}")
        claim_ids.add(claim_id)
        capability_id = claim["capability_id"]
        prior = by_capability.get(capability_id)
        if prior is not None:
            if prior["value"] != claim["value"]:
                raise ValueError(f"Contradictory capability claims: {capability_id}")
            raise ValueError(f"Ambiguous duplicate capability claims: {capability_id}")
        by_capability[capability_id] = claim


def _validate_evidence_ref(payload: Any) -> None:
    fields = {
        "schema_version",
        "artifact_kind",
        "artifact_schema_version",
        "artifact_identity_sha256",
        "subject_id",
        "scope_id",
        "provenance_class",
        "evidence_identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != fields:
        raise ValueError("Capability evidence reference is malformed")
    if payload.get("schema_version") != EVIDENCE_REF_SCHEMA_VERSION:
        raise ValueError("Unsupported capability evidence reference schema")
    require_nonblank(payload.get("artifact_kind"), label="evidence artifact_kind")
    require_nonblank(
        payload.get("artifact_schema_version"),
        label="evidence artifact_schema_version",
    )
    _sha256(payload.get("artifact_identity_sha256"), label="artifact_identity_sha256")
    require_nonblank(payload.get("subject_id"), label="evidence subject_id")
    require_nonblank(payload.get("scope_id"), label="evidence scope_id")
    _provenance(payload.get("provenance_class"))
    expected = _content_identity(
        {key: value for key, value in payload.items() if key != "evidence_identity_sha256"}
    )
    if payload.get("evidence_identity_sha256") != expected:
        raise ValueError("Capability evidence identity hash is invalid")


def _validate_validity(payload: Any) -> None:
    fields = {"observed_at", "valid_from", "valid_until", "max_age_seconds"}
    if not isinstance(payload, dict) or set(payload) != fields:
        raise ValueError("Capability claim validity is malformed")
    observed = _parse_timestamp(payload["observed_at"], label="observed_at")
    valid_from = _parse_timestamp(payload["valid_from"], label="valid_from")
    valid_until = _parse_timestamp(payload["valid_until"], label="valid_until")
    if valid_until <= valid_from:
        raise ValueError("Capability claim validity interval is empty or reversed")
    if observed < valid_from or observed > valid_until:
        raise ValueError("Capability claim observed_at falls outside its validity interval")
    max_age = payload.get("max_age_seconds")
    if isinstance(max_age, bool) or not isinstance(max_age, int) or max_age <= 0:
        raise ValueError("Capability claim max_age_seconds must be a positive integer")


def _validate_issuer(payload: Any) -> None:
    if not isinstance(payload, dict) or set(payload) != {
        "authority_id",
        "authority_identity_sha256",
    }:
        raise ValueError("Capability claim issuer is malformed")
    require_nonblank(payload.get("authority_id"), label="issuer authority_id")
    _sha256(
        payload.get("authority_identity_sha256"),
        label="issuer authority_identity_sha256",
    )


def _validate_issuer_registry(payload: Any) -> dict[str, dict[str, str]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("Authority contract issuer registry is required")
    registry: dict[str, dict[str, str]] = {}
    for item in payload:
        _validate_issuer(item)
        authority_id = item["authority_id"]
        if authority_id in registry:
            raise ValueError(f"Duplicate issuer authority_id: {authority_id}")
        registry[authority_id] = item
    return registry


def _validate_expression(
    payload: Any,
    *,
    prerequisite_ids: set[str],
    decision_ids: set[str],
) -> set[str]:
    if not isinstance(payload, dict) or set(payload) != {"operator", "terms"}:
        raise ValueError("Decision expression is malformed or ambiguous")
    if payload.get("operator") != "all":
        raise ValueError("Only the fail-closed all operator is supported")
    terms = payload.get("terms")
    if not isinstance(terms, list) or not terms:
        raise ValueError("Decision expression terms are required")
    seen: set[tuple[str, str]] = set()
    dependencies: set[str] = set()
    for term in terms:
        if not isinstance(term, dict) or set(term) != {"kind", "id"}:
            raise ValueError("Decision expression term is malformed or ambiguous")
        kind = term.get("kind")
        identifier = _identifier(term.get("id"), label="expression term id")
        key = (str(kind), identifier)
        if key in seen:
            raise ValueError(f"Duplicate expression term: {kind}:{identifier}")
        seen.add(key)
        if kind == "prerequisite":
            if identifier not in prerequisite_ids:
                raise ValueError(f"Decision expression references unknown prerequisite: {identifier}")
        elif kind == "decision":
            if identifier not in decision_ids:
                raise ValueError(f"Decision expression references unknown decision: {identifier}")
            dependencies.add(identifier)
        else:
            raise ValueError(f"Decision expression term kind is unknown: {kind}")
    return dependencies


def _reject_decision_cycles(graph: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ValueError(f"Decision graph cycle detected at: {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for decision_id in graph:
        visit(decision_id)


def _authority_registry() -> dict[str, dict[str, str]]:
    authority_ids = (
        "scenesmith.deployment_authority.v1",
        "scenesmith.measured_inertial_compiler.v2",
        "scenesmith.physical_qualification_authority.v1",
        "scenesmith.policy_evaluation_authority.v1",
        "scenesmith.repository_verifier.v1",
        "scenesmith.safety_authority.v1",
        "scenesmith.simulation_qualification_authority.v1",
    )
    return {
        authority_id: {
            "authority_id": authority_id,
            "authority_identity_sha256": hashlib.sha256(
                f"scenesmith.authority.identity.v1:{authority_id}".encode("utf-8")
            ).hexdigest(),
        }
        for authority_id in authority_ids
    }


def _prerequisite(
    *,
    prerequisite_id: str,
    provenance: tuple[str, ...],
    issuers: tuple[str, ...],
    authorities: dict[str, dict[str, str]],
) -> dict[str, Any]:
    return {
        "prerequisite_id": prerequisite_id,
        "capability_id": prerequisite_id,
        "allowed_provenance_classes": list(provenance),
        "authorized_issuers": [authorities[issuer] for issuer in issuers],
    }


def _all_expression(kind: str, identifiers: tuple[str, ...]) -> dict[str, Any]:
    return {
        "operator": "all",
        "terms": [{"kind": kind, "id": identifier} for identifier in identifiers],
    }


def _known_capability_ids() -> set[str]:
    return {item["capability_id"] for item in build_authority_contract()["capabilities"]}


def _acceptance_margin(
    measured: int | float | None,
    threshold: int | float,
    comparison: str,
) -> dict[str, Any]:
    if measured is None:
        return {
            "measured": None,
            "threshold": threshold,
            "comparison": comparison,
            "margin": None,
            "passed": False,
        }
    if comparison == ">=":
        margin = float(measured) - float(threshold)
        passed = margin >= 0
    elif comparison == "==":
        margin = -abs(float(measured) - float(threshold))
        passed = measured == threshold
    else:
        raise ValueError("Unsupported T20.8 acceptance comparison")
    if margin == 0:
        margin = 0.0
    return {
        "measured": measured,
        "threshold": threshold,
        "comparison": comparison,
        "margin": margin,
        "passed": passed,
    }


def compose_t19_1_readonly_session_authority(
    *,
    project_state: dict[str, Any],
    runtime_profile: dict[str, Any],
    repo_root: Path,
    session_id: str,
    issued_at: str,
    expires_at: str,
    private_output_dir: str,
    manifest_output: str,
    repository_state_loader: Callable[..., dict[str, Any]] | None = None,
    runtime_profile_verifier: Callable[..., None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    """Mechanically compose one finite T19.1 physical read-only session."""

    root = Path(repo_root).resolve()
    session = require_nonblank(session_id, label="T19.1 session_id")
    if re.fullmatch(r"[a-z0-9][a-z0-9._-]{7,127}", session) is None:
        raise ValueError("T19.1 session_id is malformed")
    private_relative = _t19_1_scoped_relative_path(
        root=root,
        value=private_output_dir,
        required_root=Path("outputs/robot_lab/t19_1/private"),
        label="T19.1 private output",
    )
    manifest_relative = _t19_1_scoped_relative_path(
        root=root,
        value=manifest_output,
        required_root=Path("configurations/robot_lab"),
        label="T19.1 manifest output",
    )
    if Path(manifest_relative).suffix != ".json":
        raise ValueError("T19.1 manifest output must be JSON")
    if Path(private_relative).name != session:
        raise ValueError("T19.1 private output must be named by the exact session")

    issued = _parse_timestamp(issued_at, label="T19.1 issued_at")
    expires = _parse_timestamp(expires_at, label="T19.1 expires_at")
    branch = require_nonblank(project_state.get("branch"), label="project branch")
    loader = repository_state_loader or _capture_t19_1_repository_state
    repository_state = loader(repo_root=root, branch=branch)
    _validate_t19_1_repository_state(repository_state)
    runtime_identity = _sha256(
        runtime_profile.get("identity_sha256"),
        label="T19.1 runtime profile identity",
    )

    task = copy.deepcopy(project_state.get("tasks", {}).get("T19.1"))
    owner_window = copy.deepcopy(
        project_state.get("owner_authority", {}).get(
            "current_hardware_access_window"
        )
    )
    state_projection = {
        "schema_version": project_state.get("schema_version"),
        "branch": branch,
        "run_window": {
            "hard_closeout": project_state.get("run_window", {}).get(
                "hard_closeout"
            ),
            "hardware_authority": project_state.get("run_window", {}).get(
                "hardware_authority"
            ),
        },
        "owner_window": owner_window,
        "prerequisite_tasks": {
            task_id: {"state": project_state.get("tasks", {}).get(task_id, {}).get("state")}
            for task_id in ("T16.5a", "T16.5b")
        },
        "task": task,
    }
    request = sign_payload(
        {
            "schema_version": T19_1_READONLY_SESSION_REQUEST_SCHEMA_VERSION,
            "request_name": "pi05_t19_1_readonly_hardware_census_session",
            "task_id": "T19.1",
            "session_id": session,
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
            "branch": branch,
            "repository_state": copy.deepcopy(repository_state),
            "remote_boundary_commit": repository_state["remote_head"],
            "runtime_profile_identity_sha256": runtime_identity,
            "private_output_dir": private_relative,
            "manifest_output": manifest_relative,
            "source_state": state_projection,
            "source_state_identity_sha256": hashlib.sha256(
                canonical_json_bytes(state_projection)
            ).hexdigest(),
        }
    )

    satisfied: list[str] = []
    missing: list[str] = []
    denials: list[str] = []

    def prerequisite(condition: bool, name: str, denial: str) -> None:
        if condition:
            satisfied.append(name)
        else:
            missing.append(name)
            denials.append(denial)

    prerequisite(
        project_state.get("tasks", {}).get("T16.5a", {}).get("state")
        == "verified"
        and project_state.get("tasks", {}).get("T16.5b", {}).get("state")
        == "verified",
        "m16_readonly_prerequisites_verified",
        "M16_READONLY_PREREQUISITES_NOT_VERIFIED",
    )
    prerequisite(
        isinstance(task, dict)
        and task.get("state") == "in_progress"
        and task.get("active_brief_id") == "212",
        "t19_1_task_and_brief_active",
        "T19_1_TASK_NOT_ACTIVE",
    )
    prerequisite(
        isinstance(task, dict) and task.get("live_gate") == "open",
        "t19_1_live_gate_open",
        "T19_1_LIVE_GATE_NOT_OPEN",
    )
    prerequisite(
        isinstance(task, dict)
        and task.get("session_limit") == 1
        and task.get("sessions_started") == 0,
        "single_session_unused",
        "T19_1_SESSION_ALREADY_CONSUMED_OR_AMBIGUOUS",
    )
    owner_state = (
        "owner_presence_and_access_granted_pending_central_and_session_permits"
    )
    prerequisite(
        project_state.get("run_window", {}).get("hardware_authority")
        == owner_state
        and isinstance(owner_window, dict)
        and owner_window.get("state") == owner_state
        and owner_window.get("owner_present") is True
        and owner_window.get("hardware_access_authorized") is True
        and owner_window.get("physical_access_performed_in_window") is False,
        "owner_present_read_authority_consistent",
        "OWNER_READ_AUTHORITY_NOT_CONSISTENT",
    )

    owner_window_active = False
    finite_window_valid = False
    try:
        owner_start = _parse_timestamp(
            owner_window.get("recorded_at_approximate"),
            label="T19.1 owner window start",
        )
        owner_end = _parse_timestamp(
            owner_window.get("valid_through_approximate"),
            label="T19.1 owner window end",
        )
        hard_closeout = _parse_timestamp(
            project_state.get("run_window", {}).get("hard_closeout"),
            label="T19.1 run hard closeout",
        )
        effective_end = min(owner_end, hard_closeout)
        owner_window_active = owner_start <= issued < effective_end
        duration = int((expires - issued).total_seconds())
        finite_window_valid = (
            0 < duration <= T19_1_MAX_SESSION_SECONDS
            and expires <= effective_end
        )
    except (AttributeError, TypeError, ValueError):
        owner_window_active = False
        finite_window_valid = False
    prerequisite(
        owner_window_active,
        "owner_window_active",
        "OWNER_WINDOW_INACTIVE",
    )
    prerequisite(
        finite_window_valid,
        "finite_session_window_valid",
        "FINITE_SESSION_WINDOW_INVALID",
    )

    runtime_valid = True
    verifier = runtime_profile_verifier or _verify_t19_1_runtime_profile
    try:
        verifier(runtime_profile, repo_root=root, now=issued.isoformat())
    except (OSError, RuntimeError, TypeError, ValueError):
        runtime_valid = False
    prerequisite(
        runtime_valid,
        "same_thread_full_access_no_prompt_runtime_verified",
        "RUNTIME_PROFILE_NOT_VERIFIED",
    )
    repository_aligned = (
        repository_state.get("branch") == branch
        and branch == "codex/pi05-autolearn-loop"
        and len(
            {
                repository_state.get("head"),
                repository_state.get("upstream_head"),
                repository_state.get("remote_head"),
            }
        )
        == 1
        and repository_state.get("scoped_source_diff_clean") is True
        and repository_state.get("gate_state_diff_clean") is True
    )
    prerequisite(
        repository_aligned,
        "exact_branch_remote_boundary_confirmed",
        "REMOTE_BOUNDARY_NOT_CONFIRMED",
    )

    granted = not missing
    decision = sign_payload(
        {
            "schema_version": T19_1_READONLY_SESSION_DECISION_SCHEMA_VERSION,
            "decision_id": "t19_1_readonly_hardware_census_session",
            "request_identity_sha256": request["identity_sha256"],
            "task_id": "T19.1",
            "granted": granted,
            "satisfied_prerequisites": sorted(satisfied),
            "missing_prerequisites": sorted(missing),
            "denial_reasons": sorted(set(denials)),
            "remote_boundary_commit": repository_state["remote_head"],
            "runtime_profile_identity_sha256": runtime_identity,
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
            "authority_granted": (
                ["t19_1_readonly_hardware_census_session_authorized"]
                if granted
                else []
            ),
            "authority_not_granted": list(T19_1_READONLY_AUTHORITY_NOT_GRANTED),
        }
    )
    if not granted:
        return request, decision, None

    permit = sign_payload(
        {
            "schema_version": T19_1_READONLY_SESSION_PERMIT_SCHEMA_VERSION,
            "permit_name": "pi05_t19_1_one_use_readonly_hardware_census",
            "task_id": "T19.1",
            "session_id": session,
            "request_identity_sha256": request["identity_sha256"],
            "decision_identity_sha256": decision["identity_sha256"],
            "runtime_profile_identity_sha256": runtime_identity,
            "branch": branch,
            "remote_boundary_commit": repository_state["remote_head"],
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
            "use_limit": 1,
            "maximum_register_read_count": T19_1_MAX_REGISTER_READ_COUNT,
            "read_plan": copy.deepcopy(list(T19_1_READ_PLAN)),
            "expected_servo_ids": list(range(1, 7)),
            "allowed_operations": list(T19_1_READONLY_ALLOWED_OPERATIONS),
            "register_write_count": 0,
            "torque_change_count": 0,
            "motion_command_count": 0,
            "camera_access": False,
            "private_output_dir": private_relative,
            "manifest_output": manifest_relative,
            "authority_not_granted": list(T19_1_READONLY_AUTHORITY_NOT_GRANTED),
        }
    )
    return request, decision, permit


def verify_t19_1_readonly_session_authority(
    *,
    request: dict[str, Any],
    decision: dict[str, Any],
    permit: dict[str, Any] | None,
    project_state: dict[str, Any],
    runtime_profile: dict[str, Any],
    repo_root: Path,
    now: str,
    repository_state_loader: Callable[..., dict[str, Any]] | None = None,
    runtime_profile_verifier: Callable[..., None] | None = None,
) -> None:
    """Recompose a T19.1 session and reject re-signed or stale authority."""

    verify_signed_payload(request, label="T19.1 read-only session request")
    verify_signed_payload(decision, label="T19.1 read-only session decision")
    if request.get("schema_version") != T19_1_READONLY_SESSION_REQUEST_SCHEMA_VERSION:
        raise ValueError("T19.1 request schema is unsupported")
    if decision.get("schema_version") != T19_1_READONLY_SESSION_DECISION_SCHEMA_VERSION:
        raise ValueError("T19.1 decision schema is unsupported")
    expected_request, expected_decision, expected_permit = (
        compose_t19_1_readonly_session_authority(
            project_state=project_state,
            runtime_profile=runtime_profile,
            repo_root=repo_root,
            session_id=request.get("session_id"),
            issued_at=request.get("issued_at"),
            expires_at=request.get("expires_at"),
            private_output_dir=request.get("private_output_dir"),
            manifest_output=request.get("manifest_output"),
            repository_state_loader=repository_state_loader,
            runtime_profile_verifier=runtime_profile_verifier,
        )
    )
    if request != expected_request:
        raise ValueError("T19.1 request drifted from central recomposition")
    if decision != expected_decision:
        raise ValueError("T19.1 central decision or boundary drifted")
    if decision.get("granted") is not True:
        if permit is not None:
            raise ValueError("Denied T19.1 decision cannot carry a permit")
        return
    if permit is None:
        raise ValueError("Granted T19.1 decision is missing its permit")
    verify_signed_payload(permit, label="T19.1 read-only session permit")
    if permit != expected_permit:
        raise ValueError("T19.1 permit drifted from central decision")
    observed = _parse_timestamp(now, label="T19.1 permit verification time")
    issued = _parse_timestamp(permit.get("issued_at"), label="T19.1 permit issued_at")
    expires = _parse_timestamp(permit.get("expires_at"), label="T19.1 permit expires_at")
    if observed < issued or observed > expires:
        raise ValueError("T19.1 permit is not active")
    verifier = runtime_profile_verifier or _verify_t19_1_runtime_profile
    verifier(runtime_profile, repo_root=Path(repo_root).resolve(), now=observed.isoformat())


def compose_rgb_camera_census_authority(
    *,
    project_state: dict[str, Any],
    runtime_profile: dict[str, Any],
    repo_root: Path,
    session_id: str,
    issued_at: str,
    expires_at: str,
    private_output_dir: str,
    manifest_output: str,
    repository_state_loader: Callable[..., dict[str, Any]] | None = None,
    runtime_profile_verifier: Callable[..., None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    """Compose one finite, camera-only D405/C922 RGB census."""

    root = Path(repo_root).resolve()
    session = require_nonblank(session_id, label="RGB camera census session_id")
    if re.fullmatch(r"[a-z0-9][a-z0-9._-]{7,127}", session) is None:
        raise ValueError("RGB camera census session_id is malformed")
    private_relative = _t19_1_scoped_relative_path(
        root=root,
        value=private_output_dir,
        required_root=Path("outputs/robot_lab/rgb_camera_census/private"),
        label="RGB camera census private output",
    )
    manifest_relative = _t19_1_scoped_relative_path(
        root=root,
        value=manifest_output,
        required_root=Path("configurations/robot_lab"),
        label="RGB camera census manifest output",
    )
    if Path(private_relative).name != session:
        raise ValueError("RGB camera census private output must match session_id")
    if Path(manifest_relative).suffix != ".json":
        raise ValueError("RGB camera census manifest output must be JSON")

    issued = _parse_timestamp(issued_at, label="RGB camera census issued_at")
    expires = _parse_timestamp(expires_at, label="RGB camera census expires_at")
    branch = require_nonblank(project_state.get("branch"), label="project branch")
    loader = repository_state_loader or _capture_rgb_camera_census_repository_state
    repository_state = loader(repo_root=root, branch=branch)
    _validate_t19_1_repository_state(repository_state)
    runtime_identity = _sha256(
        runtime_profile.get("identity_sha256"),
        label="RGB camera census runtime profile identity",
    )
    task = copy.deepcopy(project_state.get("support_tasks", {}).get("K3"))
    owner_window = copy.deepcopy(
        project_state.get("owner_authority", {}).get(
            "current_rgb_camera_census_window"
        )
    )
    state_projection = {
        "schema_version": project_state.get("schema_version"),
        "branch": branch,
        "owner_window": owner_window,
        "support_task": task,
    }
    request = sign_payload(
        {
            "schema_version": RGB_CAMERA_CENSUS_REQUEST_SCHEMA_VERSION,
            "request_name": "owner_present_d405_c922_rgb_camera_census",
            "task_id": "K3",
            "session_id": session,
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
            "branch": branch,
            "repository_state": copy.deepcopy(repository_state),
            "remote_boundary_commit": repository_state["remote_head"],
            "runtime_profile_identity_sha256": runtime_identity,
            "private_output_dir": private_relative,
            "manifest_output": manifest_relative,
            "source_state": state_projection,
            "source_state_identity_sha256": hashlib.sha256(
                canonical_json_bytes(state_projection)
            ).hexdigest(),
        }
    )

    satisfied: list[str] = []
    missing: list[str] = []
    denials: list[str] = []

    def prerequisite(condition: bool, name: str, denial: str) -> None:
        if condition:
            satisfied.append(name)
        else:
            missing.append(name)
            denials.append(denial)

    prerequisite(
        isinstance(task, dict)
        and task.get("state") == "in_progress"
        and task.get("active_brief_id") == "228",
        "k3_brief_228_active",
        "K3_BRIEF_228_NOT_ACTIVE",
    )
    prerequisite(
        isinstance(task, dict) and task.get("live_gate") == "open",
        "k3_live_gate_open",
        "K3_LIVE_GATE_NOT_OPEN",
    )
    prerequisite(
        isinstance(task, dict)
        and task.get("session_limit") == 1
        and task.get("sessions_started") == 0,
        "one_camera_session_unused",
        "K3_SESSION_ALREADY_CONSUMED_OR_AMBIGUOUS",
    )
    expected_window_state = (
        "owner_presence_and_rgb_camera_access_granted_pending_"
        "central_and_session_permits"
    )
    required_scope = {
        "d405_uvc_rgb_metadata_and_one_frame",
        "c922_rgb_metadata_and_one_frame",
        "coarse_host_observation_latency",
    }
    required_forbidden = {
        "depth_stream",
        "librealsense",
        "serial_access",
        "register_read",
        "register_write",
        "torque_change",
        "motion",
        "audio_capture",
        "inference",
        "training",
        "network_access",
        "external_compute",
        "brev_compute",
        "physical_qualification",
        "physical_transfer",
        "promotion",
    }
    prerequisite(
        isinstance(owner_window, dict)
        and owner_window.get("state") == expected_window_state
        and owner_window.get("owner_present") is True
        and owner_window.get("camera_access_authorized") is True
        and set(owner_window.get("scope", [])) == required_scope
        and required_forbidden.issubset(
            set(owner_window.get("not_authorized", []))
        )
        and owner_window.get("physical_access_performed_in_window") is False,
        "owner_present_rgb_only_authority_consistent",
        "OWNER_RGB_CAMERA_AUTHORITY_NOT_CONSISTENT",
    )
    owner_window_active = False
    finite_window_valid = False
    try:
        owner_start = _parse_timestamp(
            owner_window.get("recorded_at"), label="RGB camera owner window start"
        )
        owner_end = _parse_timestamp(
            owner_window.get("valid_through"), label="RGB camera owner window end"
        )
        owner_window_active = owner_start <= issued < owner_end
        duration = int((expires - issued).total_seconds())
        finite_window_valid = (
            0 < duration <= RGB_CAMERA_CENSUS_MAX_SESSION_SECONDS
            and expires <= owner_end
        )
    except (AttributeError, TypeError, ValueError):
        owner_window_active = False
        finite_window_valid = False
    prerequisite(owner_window_active, "owner_window_active", "OWNER_WINDOW_INACTIVE")
    prerequisite(
        finite_window_valid,
        "finite_camera_session_window_valid",
        "FINITE_CAMERA_SESSION_WINDOW_INVALID",
    )

    verifier = runtime_profile_verifier or _verify_t19_1_runtime_profile
    runtime_valid = True
    try:
        verifier(runtime_profile, repo_root=root, now=issued.isoformat())
    except (OSError, RuntimeError, TypeError, ValueError):
        runtime_valid = False
    prerequisite(
        runtime_valid,
        "same_thread_full_access_no_prompt_runtime_verified",
        "RUNTIME_PROFILE_NOT_VERIFIED",
    )
    repository_aligned = (
        repository_state.get("branch") == branch
        and branch == "codex/pi05-autolearn-loop"
        and len(
            {
                repository_state.get("head"),
                repository_state.get("upstream_head"),
                repository_state.get("remote_head"),
            }
        )
        == 1
        and repository_state.get("scoped_source_diff_clean") is True
        and repository_state.get("gate_state_diff_clean") is True
    )
    prerequisite(
        repository_aligned,
        "exact_branch_remote_boundary_confirmed",
        "REMOTE_BOUNDARY_NOT_CONFIRMED",
    )

    granted = not missing
    decision = sign_payload(
        {
            "schema_version": RGB_CAMERA_CENSUS_DECISION_SCHEMA_VERSION,
            "decision_id": "owner_present_d405_c922_rgb_camera_census",
            "request_identity_sha256": request["identity_sha256"],
            "task_id": "K3",
            "granted": granted,
            "satisfied_prerequisites": sorted(satisfied),
            "missing_prerequisites": sorted(missing),
            "denial_reasons": sorted(set(denials)),
            "remote_boundary_commit": repository_state["remote_head"],
            "runtime_profile_identity_sha256": runtime_identity,
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
            "authority_granted": (
                ["owner_present_rgb_camera_census_session_authorized"]
                if granted
                else []
            ),
            "authority_not_granted": list(
                RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED
            ),
        }
    )
    if not granted:
        return request, decision, None

    permit = sign_payload(
        {
            "schema_version": RGB_CAMERA_CENSUS_PERMIT_SCHEMA_VERSION,
            "permit_name": "one_use_d405_c922_rgb_camera_census",
            "task_id": "K3",
            "session_id": session,
            "request_identity_sha256": request["identity_sha256"],
            "decision_identity_sha256": decision["identity_sha256"],
            "runtime_profile_identity_sha256": runtime_identity,
            "branch": branch,
            "remote_boundary_commit": repository_state["remote_head"],
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
            "use_limit": 1,
            "target_cameras": copy.deepcopy(list(RGB_CAMERA_CENSUS_TARGETS)),
            "maximum_camera_open_count": 2,
            "frame_count_per_camera": 1,
            "maximum_capture_duration_seconds": (
                RGB_CAMERA_CENSUS_MAX_SESSION_SECONDS
            ),
            "allowed_operations": list(RGB_CAMERA_CENSUS_ALLOWED_OPERATIONS),
            "rgb_stream_authorized": True,
            "depth_stream_authorized": False,
            "serial_access_authorized": False,
            "motion_authorized": False,
            "audio_capture_authorized": False,
            "private_output_dir": private_relative,
            "manifest_output": manifest_relative,
            "authority_not_granted": list(
                RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED
            ),
        }
    )
    return request, decision, permit


def verify_rgb_camera_census_authority(
    *,
    request: dict[str, Any],
    decision: dict[str, Any],
    permit: dict[str, Any] | None,
    project_state: dict[str, Any],
    runtime_profile: dict[str, Any],
    repo_root: Path,
    now: str,
    repository_state_loader: Callable[..., dict[str, Any]] | None = None,
    runtime_profile_verifier: Callable[..., None] | None = None,
) -> None:
    """Recompose and verify one fresh camera-only authority boundary."""

    verify_signed_payload(request, label="RGB camera census request")
    verify_signed_payload(decision, label="RGB camera census decision")
    if request.get("schema_version") != RGB_CAMERA_CENSUS_REQUEST_SCHEMA_VERSION:
        raise ValueError("RGB camera census request schema is unsupported")
    if decision.get("schema_version") != RGB_CAMERA_CENSUS_DECISION_SCHEMA_VERSION:
        raise ValueError("RGB camera census decision schema is unsupported")
    expected = compose_rgb_camera_census_authority(
        project_state=project_state,
        runtime_profile=runtime_profile,
        repo_root=repo_root,
        session_id=request.get("session_id"),
        issued_at=request.get("issued_at"),
        expires_at=request.get("expires_at"),
        private_output_dir=request.get("private_output_dir"),
        manifest_output=request.get("manifest_output"),
        repository_state_loader=repository_state_loader,
        runtime_profile_verifier=runtime_profile_verifier,
    )
    if request != expected[0] or decision != expected[1]:
        raise ValueError("RGB camera central authority drifted")
    if decision.get("granted") is not True:
        if permit is not None:
            raise ValueError("Denied RGB camera decision cannot carry a permit")
        return
    if permit is None:
        raise ValueError("Granted RGB camera decision is missing its permit")
    verify_signed_payload(permit, label="RGB camera census permit")
    if permit != expected[2]:
        raise ValueError("RGB camera census permit drifted from central decision")
    observed = _parse_timestamp(now, label="RGB camera permit verification time")
    issued = _parse_timestamp(permit.get("issued_at"), label="RGB camera issued_at")
    expires = _parse_timestamp(permit.get("expires_at"), label="RGB camera expires_at")
    if observed < issued or observed > expires:
        raise ValueError("RGB camera census permit is not active")
    verifier = runtime_profile_verifier or _verify_t19_1_runtime_profile
    verifier(runtime_profile, repo_root=Path(repo_root).resolve(), now=observed.isoformat())


def _verify_t19_1_runtime_profile(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    now: str,
) -> None:
    from scenesmith.robot_lab.hardware_execution_profile import (
        verify_hardware_execution_profile_evidence,
    )

    verify_hardware_execution_profile_evidence(
        payload,
        repo_root=repo_root,
        now=now,
        expected_thread_id=require_nonblank(
            payload.get("thread_id"), label="T19.1 runtime thread ID"
        ),
    )


def _capture_t19_1_repository_state(
    *,
    repo_root: Path,
    branch: str,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()

    def run(arguments: list[str]) -> str:
        completed = subprocess.run(
            arguments,
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0 or completed.stderr.strip():
            raise RuntimeError("T19.1 repository boundary command failed")
        return completed.stdout.strip()

    observed_branch = run(["git", "branch", "--show-current"])
    head = run(["git", "rev-parse", "HEAD"])
    upstream = run(["git", "rev-parse", "@{upstream}"])
    remote_output = run(
        [
            "git",
            "ls-remote",
            "--heads",
            "origin",
            f"refs/heads/{branch}",
        ]
    )
    remote_lines = [line.split() for line in remote_output.splitlines() if line]
    if len(remote_lines) != 1 or len(remote_lines[0]) != 2:
        raise ValueError("T19.1 remote branch did not resolve exactly once")

    def diff_clean(paths: list[str]) -> bool:
        completed = subprocess.run(
            ["git", "diff", "--quiet", "--", *paths],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode not in {0, 1} or completed.stderr.strip():
            raise RuntimeError("T19.1 scoped repository diff check failed")
        return completed.returncode == 0

    return {
        "branch": observed_branch,
        "head": head,
        "upstream_head": upstream,
        "remote_head": remote_lines[0][0],
        "scoped_source_diff_clean": diff_clean(
            [
                "scenesmith/robot_lab/authority_composer.py",
                "scenesmith/robot_lab/live_readonly_observation.py",
                "scenesmith/robot_lab/t19_1_readonly_hardware_snapshot.py",
                "scripts/robot_lab/run_t19_1_readonly_hardware_snapshot.py",
            ]
        ),
        "gate_state_diff_clean": diff_clean(
            ["docs/autonomous-workflow/project_state.json"]
        ),
    }


def _validate_t19_1_repository_state(payload: Any) -> None:
    if not isinstance(payload, dict) or set(payload) != {
        "branch",
        "head",
        "upstream_head",
        "remote_head",
        "scoped_source_diff_clean",
        "gate_state_diff_clean",
    }:
        raise ValueError("T19.1 repository state is malformed")
    require_nonblank(payload.get("branch"), label="T19.1 repository branch")
    if (
        not isinstance(payload.get("scoped_source_diff_clean"), bool)
        or not isinstance(payload.get("gate_state_diff_clean"), bool)
    ):
        raise ValueError("T19.1 repository clean-state evidence is malformed")
    for field in ("head", "upstream_head", "remote_head"):
        value = require_nonblank(payload.get(field), label=f"T19.1 repository {field}")
        if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError(f"T19.1 repository {field} is not a commit identity")


def _capture_rgb_camera_census_repository_state(
    *, repo_root: Path, branch: str
) -> dict[str, Any]:
    root = Path(repo_root).resolve()

    def run(arguments: list[str]) -> str:
        completed = subprocess.run(
            arguments,
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0 or completed.stderr.strip():
            raise RuntimeError("RGB camera repository boundary command failed")
        return completed.stdout.strip()

    observed_branch = run(["git", "branch", "--show-current"])
    head = run(["git", "rev-parse", "HEAD"])
    upstream = run(["git", "rev-parse", "@{upstream}"])
    remote_output = run(
        [
            "git",
            "ls-remote",
            "--heads",
            "origin",
            f"refs/heads/{branch}",
        ]
    )
    remote_lines = [line.split() for line in remote_output.splitlines() if line]
    if len(remote_lines) != 1 or len(remote_lines[0]) != 2:
        raise ValueError("RGB camera remote branch did not resolve exactly once")

    def diff_clean(paths: list[str]) -> bool:
        completed = subprocess.run(
            ["git", "diff", "--quiet", "--", *paths],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode not in {0, 1} or completed.stderr.strip():
            raise RuntimeError("RGB camera scoped repository diff check failed")
        return completed.returncode == 0

    return {
        "branch": observed_branch,
        "head": head,
        "upstream_head": upstream,
        "remote_head": remote_lines[0][0],
        "scoped_source_diff_clean": diff_clean(
            [
                "scenesmith/robot_lab/authority_composer.py",
                "scenesmith/robot_lab/hardware_execution_profile.py",
                "scenesmith/robot_lab/rgb_camera_census.py",
                "scripts/robot_lab/run_rgb_camera_census.py",
                "tests/unit/test_rgb_camera_census.py",
                "tests/unit/test_static_pose_live_execution.py",
                "docs/briefs/228-owner-present-rgb-camera-census.md",
            ]
        ),
        "gate_state_diff_clean": diff_clean(
            ["docs/autonomous-workflow/project_state.json"]
        ),
    }


def _t19_1_scoped_relative_path(
    *,
    root: Path,
    value: Any,
    required_root: Path,
    label: str,
) -> str:
    text = require_nonblank(value, label=label)
    relative = Path(text)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} escapes the repository")
    resolved = (root / relative).resolve()
    required = (root / required_root).resolve()
    if not resolved.is_relative_to(required) or resolved == required:
        raise ValueError(f"{label} escapes its required root")
    return resolved.relative_to(root).as_posix()


def _source_ref(repo_root: Path, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(repo_root)),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": _file_sha256(path),
    }


def _verify_checkpoint_manifest(model_root: Path, files: dict[str, Any]) -> None:
    root = model_root.resolve()
    if not isinstance(files, dict) or not files:
        raise ValueError("T20.8 checkpoint manifest is empty")
    for relative_path, expected in files.items():
        path = (model_root / relative_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("T20.8 checkpoint path is unavailable or escapes its run")
        if (
            _file_sha256(path) != expected.get("sha256")
            or path.stat().st_size != expected.get("size_bytes")
        ):
            raise ValueError("T20.8 checkpoint bytes drifted")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find_forbidden_fields(payload: Any, *, forbidden: set[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in forbidden:
                found.add(key)
            found.update(_find_forbidden_fields(value, forbidden=forbidden))
    elif isinstance(payload, list):
        for value in payload:
            found.update(_find_forbidden_fields(value, forbidden=forbidden))
    return found


def _composition_identity(payload: dict[str, Any]) -> str:
    unsigned = {
        key: value
        for key, value in payload.items()
        if key not in {"identity_sha256", "composition_identity_sha256"}
    }
    return _content_identity(unsigned)


def _content_identity(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _identifier(value: Any, *, label: str) -> str:
    identifier = require_nonblank(value, label=label)
    if not _IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValueError(f"{label} must be a stable lowercase identifier")
    return identifier


def _sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if not _SHA256_PATTERN.fullmatch(digest):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest


def _provenance(value: Any) -> str:
    provenance = require_nonblank(value, label="provenance_class")
    if provenance not in PROVENANCE_CLASSES:
        raise ValueError(f"Unknown provenance class: {provenance}")
    return provenance


def _composition_mode(value: Any) -> str:
    mode = require_nonblank(value, label="composition_mode")
    if mode not in {"production", "fixture"}:
        raise ValueError(f"Unknown authority composition mode: {mode}")
    return mode


def _parse_timestamp(value: Any, *, label: str) -> datetime:
    timestamp = require_nonblank(value, label=label)
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a UTC offset")
    return parsed


def _canonical_timestamp(value: Any, *, label: str) -> str:
    parsed = _parse_timestamp(value, label=label)
    return parsed.isoformat()


def _resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _relative_to_repo(repo_root: Path, path: Path) -> Path:
    if not path.is_absolute():
        return path
    try:
        return path.relative_to(repo_root)
    except ValueError:
        return path
