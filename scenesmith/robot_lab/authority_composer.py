"""Fail-closed composition of scoped robot-lab evidence into global authority.

Component artifacts may report local facts.  This module is the sole production
path that can emit SceneSmith's global readiness decisions.
"""

from __future__ import annotations

import hashlib
import json
import re

from datetime import datetime
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)


AUTHORITY_CONTRACT_SCHEMA_VERSION = "scenesmith.authority_composition_contract.v1"
CAPABILITY_CLAIM_SCHEMA_VERSION = "scenesmith.component_capability_claim.v1"
EVIDENCE_REF_SCHEMA_VERSION = "scenesmith.capability_evidence_ref.v1"
COMPOSITION_REQUEST_SCHEMA_VERSION = "scenesmith.authority_composition_request.v1"
AUTHORITY_DECISION_SCHEMA_VERSION = "scenesmith.authority_composition_decision.v1"

DEFAULT_AUTHORITY_CONTRACT_PATH = Path(
    "configurations/robot_lab/pi05_authority_composition_contract.json"
)
DEFAULT_AUTHORITY_DECISION_PATH = Path(
    "configurations/robot_lab/pi05_authority_decision.fixture_denied.json"
)
DEFAULT_AUTHORITY_SUBJECT_ID = "pi05_so101_sorting_system"
DEFAULT_AUTHORITY_SCOPE_ID = "pi05_so101_authority"
DEFAULT_EVALUATION_TIME = "2026-07-11T02:14:07-05:00"

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
