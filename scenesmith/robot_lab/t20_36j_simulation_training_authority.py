"""Central simulation-only authority for the corrected T20.36j replacement."""

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
from scenesmith.robot_lab.t20_36d_exact_act_gate_b_control_design import (
    DATASET_MANIFEST_PATH,
)
from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (
    LOCAL_PREFLIGHT_PATH,
    REPO_ROOT,
    SPEC_PATH,
    verify_spec_file,
)
from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (
    EXPECTED_CACHE_MANIFEST_IDENTITY,
    EXPECTED_CONTRACT_IDENTITY,
    EXPECTED_OFFLINE_INSTALLS,
    RESULT_PATH as CORRECTED_CONTRACT_PATH,
    verify_contract_file,
)


OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_36j_owner_replacement_authorization.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_36j_simulation_training_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_36j_simulation_training_authority_decision.json"
)
VALID_FROM = "2026-07-16T00:33:37-05:00"
VALID_UNTIL = "2026-07-16T08:33:37-05:00"
EVALUATION_TIME = "2026-07-16T00:40:00-05:00"
AUTHORIZED_ACTIONS = (
    "offline_dependency_install",
    "offline_auto_processor_construction",
    "simulation_model_construction",
    "simulation_model_inference",
    "simulation_optimizer_training",
)
AUTHORIZATION_SOURCE = (
    "owner_proceed_and_authorize_exact_t20_36j_replacement_2026_07_16"
)


def build_owner_grant(
    *,
    training_spec: dict[str, Any],
    corrected_contract: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if (
        corrected_contract.get("identity_sha256") != EXPECTED_CONTRACT_IDENTITY
        or corrected_contract.get("source_identities", {}).get(
            "offline_cache_manifest"
        )
        != EXPECTED_CACHE_MANIFEST_IDENTITY
    ):
        raise ValueError("T20.36j corrected contract identity drifted")
    return sign_payload(
        {
            "schema_version": "scenesmith.owner_training_authorization.v1",
            "authorization_id": "t20_36j_corrected_smolvla_replacement_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": (
                "exact_offline_environment_correction_and_one_local_mps_"
                "smolvla_gate_b_replacement"
            ),
            "source_training_spec_ref": artifact_ref(
                path=SPEC_PATH,
                payload=training_spec,
                repo_root=Path(repo_root),
            ),
            "corrected_preflight_contract_ref": artifact_ref(
                path=CORRECTED_CONTRACT_PATH,
                payload=corrected_contract,
                repo_root=Path(repo_root),
            ),
            "offline_cache_manifest_identity_sha256": (
                EXPECTED_CACHE_MANIFEST_IDENTITY
            ),
            "exact_offline_install": [
                {"package": package, "version": version}
                for package, version in sorted(EXPECTED_OFFLINE_INSTALLS.items())
            ],
            "network_access_authorized": False,
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "authorized_attempt_count": 1,
            "maximum_optimizer_updates": training_spec["campaign"][
                "maximum_optimizer_updates"
            ],
            "stop_at_first_gate_pass": True,
            "retry_or_sweep_authorized": False,
            "smolvla_entry_authorized": True,
            "policy_track_selection_authorized": False,
            "gate_b_amendment_authorized": False,
            "gate_c_authorized": False,
            "simulation_only": True,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "issued_at": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "authorization_source": AUTHORIZATION_SOURCE,
        }
    )


def verify_owner_grant(
    payload: dict[str, Any],
    *,
    training_spec: dict[str, Any],
    corrected_contract: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.36j owner replacement grant")
    if payload != build_owner_grant(
        training_spec=training_spec,
        corrected_contract=corrected_contract,
        repo_root=repo_root,
    ):
        raise ValueError("T20.36j owner replacement grant drifted")


def build_production_authority(
    *, repo_root: Path = REPO_ROOT
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    spec = verify_spec_file(repo_root=root)
    contract = verify_contract_file(repo_root=root)
    owner = load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_grant(
        owner,
        training_spec=spec,
        corrected_contract=contract,
        repo_root=root,
    )
    local_preflight = load_strict_json(root / LOCAL_PREFLIGHT_PATH)
    dataset = load_strict_json(root / DATASET_MANIFEST_PATH)
    verify_signed_payload(local_preflight, label="T20.36j local policy preflight")
    verify_signed_payload(dataset, label="T20.36j canonical dataset manifest")
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
        "contract": artifact_ref(
            path=CORRECTED_CONTRACT_PATH, payload=contract, repo_root=root
        ),
        "spec": artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root),
        "preflight": artifact_ref(
            path=LOCAL_PREFLIGHT_PATH,
            payload=local_preflight,
            repo_root=root,
        ),
        "dataset": artifact_ref(
            path=DATASET_MANIFEST_PATH, payload=dataset, repo_root=root
        ),
        "dataset_authority": artifact_ref(
            path=T20_23_DECISION_PATH,
            payload=inherited_decision,
            repo_root=root,
        ),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [
            refs["dataset_authority"],
            refs["spec"],
            refs["contract"],
        ],
        "executable_stack_valid": [
            refs["preflight"],
            refs["spec"],
            refs["contract"],
        ],
        "coordinate_contract_valid": [refs["dataset"], refs["spec"]],
        "normalization_contract_valid": [refs["dataset"], refs["spec"]],
        "experience_compiler_valid": [
            refs["dataset_authority"],
            refs["dataset"],
            refs["spec"],
            refs["contract"],
        ],
        "required_simulation_properties_available": [
            refs["preflight"],
            refs["dataset"],
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
                claim_id=f"t20_36j_{prerequisite_id}",
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
                    "max_age_seconds": 28800,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind="t20_36j_corrected_smolvla_evidence",
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
        raise ValueError("T20.36j central authority exceeded training-only scope")
    return request, decision


def write_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    spec = verify_spec_file(repo_root=root)
    contract = verify_contract_file(repo_root=root)
    owner = build_owner_grant(
        training_spec=spec,
        corrected_contract=contract,
        repo_root=root,
    )
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
        raise ValueError("T20.36j authority request drifted")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.36j authority decision drifted")
    return {"request": request, "decision": decision}


def require_active_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    result = verify_authority(repo_root=repo_root)
    current = now or datetime.now().astimezone()
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("T20.36j authority time must carry a UTC offset")
    if current < datetime.fromisoformat(VALID_FROM):
        raise ValueError("T20.36j authority is not active yet")
    if current > datetime.fromisoformat(VALID_UNTIL):
        raise ValueError("T20.36j authority has expired")
    return result
