"""Central training-only authority for the T20.33 Gate B proof."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    dump_canonical_json,
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
from scenesmith.robot_lab.t20_17_clean_base_preflight import DATASET_MANIFEST_PATH
from scenesmith.robot_lab.t20_23_simulation_training_authority import (
    DECISION_PATH as T20_23_DECISION_PATH,
    REQUEST_PATH as T20_23_REQUEST_PATH,
    VALID_FROM,
    VALID_UNTIL,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    REPO_ROOT,
    SPEC_PATH,
    verify_training_spec_file,
)


OWNER_GRANT_PATH = Path("configurations/robot_lab/t20_33_owner_training_authorization.json")
REQUEST_PATH = Path("configurations/robot_lab/t20_33_simulation_training_authority_request.json")
DECISION_PATH = Path("configurations/robot_lab/t20_33_simulation_training_authority_decision.json")
EVALUATION_TIME = "2026-07-14T21:00:00-05:00"
AUTHORIZED_ACTIONS = (
    "simulation_model_load",
    "simulation_model_inference",
    "simulation_optimizer_training",
)


def build_owner_grant(*, training_spec: dict[str, Any], repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": "scenesmith.owner_training_authorization.v1",
            "authorization_id": "t20_33_gate_b_one_batch_memorization_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": "t20_33_simulation_only_one_batch_gate_b",
            "source_training_spec_ref": artifact_ref(
                path=SPEC_PATH, payload=training_spec, repo_root=Path(repo_root)
            ),
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "simulation_only": True,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "issued_at": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "authorization_source": "owner_goal_enact_sim_link_mvp_execution_plan",
        }
    )


def verify_owner_grant(
    payload: dict[str, Any], *, training_spec: dict[str, Any], repo_root: Path = REPO_ROOT
) -> None:
    verify_signed_payload(payload, label="T20.33 owner training grant")
    if payload != build_owner_grant(training_spec=training_spec, repo_root=repo_root):
        raise ValueError("T20.33 owner grant drifted from fixed simulation-only scope")


def build_production_authority(*, repo_root: Path = REPO_ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    spec = verify_training_spec_file(repo_root=root)
    owner = load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_grant(owner, training_spec=spec, repo_root=root)
    dataset_manifest = load_strict_json(root / DATASET_MANIFEST_PATH)
    verify_signed_payload(dataset_manifest, label="T20.33 T20.17 dataset manifest")
    inherited_request = load_strict_json(root / T20_23_REQUEST_PATH)
    inherited_decision = load_strict_json(root / T20_23_DECISION_PATH)
    verify_authority_decision(inherited_decision, request=inherited_request)
    require_global_decision(
        inherited_decision,
        request=inherited_request,
        decision_id="simulation_training_ready",
    )
    refs = {
        "owner": artifact_ref(path=OWNER_GRANT_PATH, payload=owner, repo_root=root),
        "spec": artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root),
        "dataset": artifact_ref(
            path=DATASET_MANIFEST_PATH, payload=dataset_manifest, repo_root=root
        ),
        "inherited": artifact_ref(
            path=T20_23_DECISION_PATH, payload=inherited_decision, repo_root=root
        ),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [refs["inherited"], refs["spec"]],
        "executable_stack_valid": [refs["inherited"], refs["spec"]],
        "coordinate_contract_valid": [refs["dataset"], refs["spec"]],
        "normalization_contract_valid": [refs["dataset"], refs["spec"]],
        "experience_compiler_valid": [refs["inherited"], refs["dataset"]],
        "required_simulation_properties_available": [refs["dataset"], refs["spec"]],
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
                claim_id=f"t20_33_{prerequisite_id}",
                capability_id=prerequisite_id,
                value=True,
                subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                provenance_class=provenance,
                issuer=requirement["authorized_issuers"][0],
                validity={
                    "observed_at": EVALUATION_TIME,
                    "valid_from": VALID_FROM,
                    "valid_until": VALID_UNTIL,
                    "max_age_seconds": 604800,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind="t20_33_one_batch_gate_b_evidence",
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
        evaluation_time=EVALUATION_TIME,
        claims=claims,
        composition_mode="production",
    )
    decision = compose_authority(request)
    require_global_decision(decision, request=request, decision_id="simulation_training_ready")
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.33 central authority exceeded training-only scope")
    return request, decision


def write_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    spec = verify_training_spec_file(repo_root=root)
    owner = build_owner_grant(training_spec=spec, repo_root=root)
    dump_canonical_json(root / OWNER_GRANT_PATH, owner)
    request, decision = build_production_authority(repo_root=root)
    dump_canonical_json(root / REQUEST_PATH, request)
    dump_canonical_json(root / DECISION_PATH, decision)
    return {"owner_grant": owner, "request": request, "decision": decision}


def verify_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    expected_request, expected_decision = build_production_authority(repo_root=root)
    request = load_strict_json(root / REQUEST_PATH)
    decision = load_strict_json(root / DECISION_PATH)
    if request != expected_request:
        raise ValueError("T20.33 authority request drifted from live sources")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.33 authority decision drifted from recomposition")
    return {"request": request, "decision": decision}


def require_active_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    result = verify_authority(repo_root=repo_root)
    current = now or datetime.now().astimezone()
    if current < datetime.fromisoformat(VALID_FROM):
        raise ValueError("T20.33 authority is not active yet")
    if current > datetime.fromisoformat(VALID_UNTIL):
        raise ValueError("T20.33 authority has expired")
    return result
