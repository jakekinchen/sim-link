"""Central simulation-only authority for the T20.36 bounded campaign."""

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
from scenesmith.robot_lab.t20_23_simulation_training_authority import (
    DECISION_PATH as T20_23_DECISION_PATH,
    REQUEST_PATH as T20_23_REQUEST_PATH,
)
from scenesmith.robot_lab.t20_35x_simulation_training_authority import (
    DECISION_PATH as T20_35X_DECISION_PATH,
    REQUEST_PATH as T20_35X_REQUEST_PATH,
)
from scenesmith.robot_lab.t20_36_bounded_corrected_coverage import (
    RECOVERY_MANIFEST_PATH,
    REPO_ROOT,
    SPEC_PATH,
    X_RESULT_PATH,
    load_source_artifacts,
    verify_training_spec,
)


OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_36_owner_training_authorization.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_36_simulation_training_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_36_simulation_training_authority_decision.json"
)
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T23:27:47-05:00"
EVALUATION_TIME = "2026-07-15T17:15:00-05:00"


def build_owner_grant(
    *, training_spec: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": "scenesmith.owner_training_authorization.v1",
            "authorization_id": "t20_36_bounded_corrected_coverage_campaign_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": "one_t20_36_simulation_only_bounded_corrected_coverage_campaign_with_ordered_conditional_evaluation",
            "source_training_spec_ref": artifact_ref(
                path=SPEC_PATH,
                payload=training_spec,
                repo_root=Path(repo_root),
            ),
            "authorized_actions": list(training_spec["authorized_actions"]),
            "authorized_attempt_count": 1,
            "ordered_gate_enforcement_required": True,
            "simulation_only": True,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "issued_at": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "authorization_source": "owner_resumed_sim_link_goal_loop_and_pre_registered_gate_b_pass_to_gate_c_2026_07_15",
        }
    )


def verify_owner_grant(
    payload: dict[str, Any],
    *,
    training_spec: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.36 owner training grant")
    if payload != build_owner_grant(
        training_spec=training_spec, repo_root=repo_root
    ):
        raise ValueError("T20.36 owner grant drifted")


def build_production_authority(
    *, repo_root: Path = REPO_ROOT
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_training_spec(spec, **sources)
    owner = load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_grant(owner, training_spec=spec, repo_root=root)
    x_result = load_strict_json(root / X_RESULT_PATH)
    recovery_manifest = load_strict_json(root / RECOVERY_MANIFEST_PATH)
    verify_signed_payload(x_result, label="T20.36 Gate B evidence")
    verify_signed_payload(recovery_manifest, label="T20.36 recovery dataset")
    inherited = []
    for request_path, decision_path, label in (
        (T20_23_REQUEST_PATH, T20_23_DECISION_PATH, "dataset"),
        (T20_35X_REQUEST_PATH, T20_35X_DECISION_PATH, "Gate B correction"),
    ):
        request = load_strict_json(root / request_path)
        decision = load_strict_json(root / decision_path)
        verify_authority_decision(decision, request=request)
        require_global_decision(
            decision, request=request, decision_id="simulation_training_ready"
        )
        inherited.append((label, decision_path, decision))
    refs = {
        "owner": artifact_ref(path=OWNER_GRANT_PATH, payload=owner, repo_root=root),
        "spec": artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root),
        "gate_b": artifact_ref(path=X_RESULT_PATH, payload=x_result, repo_root=root),
        "dataset": artifact_ref(
            path=RECOVERY_MANIFEST_PATH,
            payload=recovery_manifest,
            repo_root=root,
        ),
        "dataset_authority": artifact_ref(
            path=inherited[0][1], payload=inherited[0][2], repo_root=root
        ),
        "correction_authority": artifact_ref(
            path=inherited[1][1], payload=inherited[1][2], repo_root=root
        ),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [
            refs["dataset_authority"],
            refs["correction_authority"],
            refs["spec"],
            refs["gate_b"],
        ],
        "executable_stack_valid": [refs["correction_authority"], refs["spec"]],
        "coordinate_contract_valid": [refs["dataset"], refs["spec"]],
        "normalization_contract_valid": [refs["gate_b"], refs["spec"]],
        "experience_compiler_valid": [refs["dataset_authority"], refs["dataset"]],
        "required_simulation_properties_available": [
            refs["dataset"],
            refs["gate_b"],
            refs["spec"],
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
                claim_id=f"t20_36_{prerequisite_id}",
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
                    "max_age_seconds": 57600,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind="t20_36_bounded_corrected_coverage_evidence",
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
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.36 central authority exceeded training-only scope")
    return request, decision


def write_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_training_spec(spec, **sources)
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
        raise ValueError("T20.36 authority request drifted")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.36 authority decision drifted")
    return {"request": request, "decision": decision}


def require_active_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    result = verify_authority(repo_root=repo_root)
    current = now or datetime.now().astimezone()
    if current < datetime.fromisoformat(VALID_FROM):
        raise ValueError("T20.36 authority is not active yet")
    if current > datetime.fromisoformat(VALID_UNTIL):
        raise ValueError("T20.36 authority has expired")
    return result
