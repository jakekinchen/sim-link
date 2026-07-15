"""Central simulation-only authority for the T20.30 quantile ablation."""

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
    VALID_FROM,
    VALID_UNTIL,
    verify_production_authority as verify_t20_23_authority,
)
from scenesmith.robot_lab.t20_30_nominal_action_quantile_preflight import (
    MANIFEST_PATH,
    REPO_ROOT,
    T20_29_PATH,
    TRAINING_SPEC_PATH,
    verify_preflight,
)


OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_30_owner_training_authorization.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_30_simulation_training_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_30_simulation_training_authority_decision.json"
)
EVALUATION_TIME = "2026-07-14T19:15:00-05:00"
AUTHORIZED_ACTIONS = (
    "simulation_model_load",
    "simulation_model_inference",
    "simulation_optimizer_training",
    "simulation_policy_evaluation",
)


def build_owner_grant(
    *, training_spec: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": "scenesmith.owner_training_authorization.v1",
            "authorization_id": "t20_30_nominal_action_quantile_ablation_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": "t20_30_simulation_only_quantile_ablation",
            "source_training_spec_ref": artifact_ref(
                path=TRAINING_SPEC_PATH,
                payload=training_spec,
                repo_root=Path(repo_root),
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
    payload: dict[str, Any],
    *,
    training_spec: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.30 owner training grant")
    if payload != build_owner_grant(
        training_spec=training_spec, repo_root=repo_root
    ):
        raise ValueError("T20.30 owner grant drifted from simulation-only scope")


def build_production_authority(
    *, repo_root: Path = REPO_ROOT
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    preflight = verify_preflight(repo_root=root)
    spec = preflight["training_spec"]
    manifest = preflight["manifest"]
    owner = load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_grant(owner, training_spec=spec, repo_root=root)
    t20_23 = verify_t20_23_authority(repo_root=root)["decision"]
    t20_29 = load_strict_json(root / T20_29_PATH)
    verify_signed_payload(t20_29, label="T20.29 counterfactual")
    refs = {
        "owner": artifact_ref(
            path=OWNER_GRANT_PATH, payload=owner, repo_root=root
        ),
        "manifest": artifact_ref(
            path=MANIFEST_PATH, payload=manifest, repo_root=root
        ),
        "spec": artifact_ref(
            path=TRAINING_SPEC_PATH, payload=spec, repo_root=root
        ),
        "t20_23": artifact_ref(
            path=Path(
                "configurations/robot_lab/"
                "t20_23_simulation_training_authority_decision.json"
            ),
            payload=t20_23,
            repo_root=root,
        ),
        "t20_29": artifact_ref(path=T20_29_PATH, payload=t20_29, repo_root=root),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [refs["t20_23"], refs["spec"]],
        "executable_stack_valid": [refs["t20_23"], refs["spec"]],
        "coordinate_contract_valid": [refs["t20_23"], refs["spec"]],
        "normalization_contract_valid": [
            refs["manifest"],
            refs["spec"],
            refs["t20_29"],
        ],
        "experience_compiler_valid": [refs["t20_23"], refs["manifest"]],
        "required_simulation_properties_available": [
            refs["manifest"],
            refs["spec"],
        ],
    }
    contract = build_authority_contract()
    requirements = {
        row["prerequisite_id"]: row for row in contract["prerequisites"]
    }
    claims = []
    for prerequisite_id, evidence_refs in sorted(evidence.items()):
        requirement = requirements[prerequisite_id]
        provenance = requirement["allowed_provenance_classes"][0]
        claims.append(
            build_capability_claim(
                claim_id=f"t20_30_{prerequisite_id}",
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
                        artifact_kind="t20_30_quantile_ablation_evidence",
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
        raise ValueError("T20.30 central authority exceeded training-only scope")
    return request, decision


def write_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    spec = verify_preflight(repo_root=root)["training_spec"]
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
        raise ValueError("T20.30 authority request drifted from live sources")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.30 authority decision drifted from recomposition")
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    return {"request": request, "decision": decision}


def require_active_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    result = verify_authority(repo_root=repo_root)
    current = now or datetime.now().astimezone()
    if current < datetime.fromisoformat(VALID_FROM):
        raise ValueError("T20.30 authority is not active yet")
    if current > datetime.fromisoformat(VALID_UNTIL):
        raise ValueError("T20.30 authority has expired")
    return result
