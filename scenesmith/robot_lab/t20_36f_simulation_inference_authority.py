"""Central simulation-only inference authority for T20.36f."""

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
from scenesmith.robot_lab.t20_36d_exact_act_gate_b_control_design import SPEC_PATH
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (
    RESULT_PATH as SOURCE_RESULT_PATH,
)
from scenesmith.robot_lab.t20_36e_simulation_training_authority import (
    DECISION_PATH as SOURCE_DECISION_PATH,
    REQUEST_PATH as SOURCE_REQUEST_PATH,
)
from scenesmith.robot_lab.t20_36f_act_decode_localization import (
    EXPECTED_CHECKPOINT_IDENTITY,
    REPO_ROOT,
    load_verified_sources,
)


OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_36f_owner_inference_authorization.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_36f_simulation_inference_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_36f_simulation_inference_authority_decision.json"
)
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T23:27:47-05:00"
EVALUATION_TIME = "2026-07-15T19:30:00-05:00"
AUTHORIZED_ACTIONS = (
    "simulation_model_load",
    "simulation_model_inference",
)


def build_owner_grant(
    *, sources: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root)
    return sign_payload(
        {
            "schema_version": "scenesmith.owner_inference_authorization.v1",
            "authorization_id": "t20_36f_act_decode_localization_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": "one_exact_act_checkpoint_decode_localization",
            "source_result_ref": artifact_ref(
                path=SOURCE_RESULT_PATH,
                payload=sources["source_result"],
                repo_root=root,
            ),
            "source_spec_ref": artifact_ref(
                path=SPEC_PATH,
                payload=sources["spec"],
                repo_root=root,
            ),
            "source_checkpoint_identity_sha256": EXPECTED_CHECKPOINT_IDENTITY,
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "authorized_attempt_count": 1,
            "optimizer_authorized": False,
            "training_retry_authorized": False,
            "policy_track_selection_authorized": False,
            "smolvla_entry_authorized": False,
            "gate_b_amendment_authorized": False,
            "gate_c_authorized": False,
            "simulation_only": True,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "issued_at": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "authorization_source": (
                "owner_resumed_goal_loop_and_evidence_routed_"
                "post_act_decode_localization_2026_07_15"
            ),
        }
    )


def verify_owner_grant(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.36f owner inference grant")
    if payload != build_owner_grant(sources=sources, repo_root=repo_root):
        raise ValueError("T20.36f owner inference grant drifted")


def build_production_authority(
    *, repo_root: Path = REPO_ROOT
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    sources = load_verified_sources(repo_root=root)
    owner = load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_grant(owner, sources=sources, repo_root=root)
    source_request = load_strict_json(root / SOURCE_REQUEST_PATH)
    source_decision = load_strict_json(root / SOURCE_DECISION_PATH)
    verify_authority_decision(source_decision, request=source_request)
    require_global_decision(
        source_decision,
        request=source_request,
        decision_id="simulation_training_ready",
    )
    refs = {
        "owner": artifact_ref(
            path=OWNER_GRANT_PATH, payload=owner, repo_root=root
        ),
        "spec": artifact_ref(
            path=SPEC_PATH, payload=sources["spec"], repo_root=root
        ),
        "result": artifact_ref(
            path=SOURCE_RESULT_PATH,
            payload=sources["source_result"],
            repo_root=root,
        ),
        "source_authority": artifact_ref(
            path=SOURCE_DECISION_PATH,
            payload=source_decision,
            repo_root=root,
        ),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [refs["source_authority"], refs["spec"]],
        "executable_stack_valid": [refs["source_authority"], refs["result"]],
        "coordinate_contract_valid": [refs["spec"], refs["result"]],
        "normalization_contract_valid": [refs["spec"], refs["result"]],
        "experience_compiler_valid": [refs["source_authority"], refs["spec"]],
        "required_simulation_properties_available": [
            refs["spec"],
            refs["result"],
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
                claim_id=f"t20_36f_{prerequisite_id}",
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
                        artifact_kind="t20_36f_act_decode_localization_evidence",
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
        raise ValueError("T20.36f central authority exceeded inference scope")
    return request, decision


def write_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_verified_sources(repo_root=root)
    owner = build_owner_grant(sources=sources, repo_root=root)
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
        raise ValueError("T20.36f authority request drifted")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.36f authority decision drifted")
    return {"request": request, "decision": decision}


def require_active_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    result = verify_authority(repo_root=repo_root)
    current = now or datetime.now().astimezone()
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("T20.36f authority time must carry a UTC offset")
    if current < datetime.fromisoformat(VALID_FROM):
        raise ValueError("T20.36f authority is not active yet")
    if current > datetime.fromisoformat(VALID_UNTIL):
        raise ValueError("T20.36f authority has expired")
    return result
