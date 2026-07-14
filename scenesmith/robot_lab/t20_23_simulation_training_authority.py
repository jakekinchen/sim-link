"""Central T20.23 simulation-only training authority composition."""

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
from scenesmith.robot_lab.simulation_training_spec import (
    verify_training_spec_file as verify_t20_1_spec,
)
from scenesmith.robot_lab.t20_23_recovery_augmented_preflight import (
    DATASET_MANIFEST_PATH,
    REPO_ROOT,
    TRAINING_SPEC_PATH,
    verify_training_spec_file,
)


OWNER_GRANT_SCHEMA_VERSION = "scenesmith.owner_training_authorization.v1"
OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_23_owner_training_authorization.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_23_simulation_training_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_23_simulation_training_authority_decision.json"
)
EVALUATION_TIME = "2026-07-14T17:15:00-05:00"
VALID_FROM = "2026-07-14T12:20:57-05:00"
VALID_UNTIL = "2026-07-21T03:05:00-05:00"
AUTHORIZED_ACTIONS = (
    "simulation_model_load",
    "simulation_model_inference",
    "simulation_optimizer_training",
    "simulation_policy_evaluation",
)


def build_owner_training_grant(
    *, training_spec: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": OWNER_GRANT_SCHEMA_VERSION,
            "authorization_id": "t20_23_recovery_augmented_simulation_training_owner_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": "t20_23_recovery_augmented_simulation_only_training",
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


def verify_owner_training_grant(
    payload: dict[str, Any],
    *,
    training_spec: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.23 owner simulation-training grant")
    expected = build_owner_training_grant(
        training_spec=training_spec, repo_root=repo_root
    )
    if payload != expected:
        raise ValueError("T20.23 owner training grant drifted from its simulation-only scope")


def write_owner_training_grant(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    spec = verify_training_spec_file(repo_root=repo_root)
    grant = build_owner_training_grant(training_spec=spec, repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / OWNER_GRANT_PATH, grant)
    return grant


def build_production_authority(
    *, repo_root: Path = REPO_ROOT
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    spec = verify_training_spec_file(repo_root=root)
    owner = load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_training_grant(owner, training_spec=spec, repo_root=root)
    t20_1_spec = verify_t20_1_spec(repo_root=root)
    shared = _shared_refs(t20_1_spec)
    dataset_ref = _signed_ref(root, DATASET_MANIFEST_PATH, "T20.23 dataset manifest")
    nominal_ref = _ref_from_spec(root, spec, "nominal_source_manifest_ref")
    recovery_ref = _ref_from_spec(root, spec, "recovery_package_manifest_ref")
    spec_ref = artifact_ref(path=TRAINING_SPEC_PATH, payload=spec, repo_root=root)
    owner_ref = artifact_ref(path=OWNER_GRANT_PATH, payload=owner, repo_root=root)
    evidence = {
        "required_training_authority_present": [owner_ref],
        "structural_contract_valid": [shared["structural_twin"], spec_ref],
        "executable_stack_valid": [shared["executable_stack"], spec_ref],
        "coordinate_contract_valid": [shared["coordinate_contract"], spec_ref],
        "normalization_contract_valid": [dataset_ref, spec_ref],
        "experience_compiler_valid": [
            shared["compiler_replay_audit"],
            nominal_ref,
            recovery_ref,
            spec_ref,
        ],
        "required_simulation_properties_available": [
            nominal_ref,
            recovery_ref,
            dataset_ref,
            spec_ref,
        ],
    }
    contract = build_authority_contract()
    requirements = {row["prerequisite_id"]: row for row in contract["prerequisites"]}
    claims = []
    for prerequisite_id, refs in sorted(evidence.items()):
        requirement = requirements[prerequisite_id]
        provenance = requirement["allowed_provenance_classes"][0]
        claims.append(
            build_capability_claim(
                claim_id=f"t20_23_{prerequisite_id}",
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
                        artifact_kind="t20_23_source_bound_training_evidence",
                        artifact_schema_version=ref["schema_version"],
                        artifact_identity_sha256=ref["identity_sha256"],
                        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                        provenance_class=provenance,
                    )
                    for ref in refs
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
        raise ValueError("T20.23 authority exceeded simulation-training scope")
    return request, decision


def write_production_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    request, decision = build_production_authority(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / REQUEST_PATH, request)
    dump_canonical_json(Path(repo_root) / DECISION_PATH, decision)
    return {"request": request, "decision": decision}


def verify_production_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected_request, expected_decision = build_production_authority(repo_root=repo_root)
    request = load_strict_json(Path(repo_root) / REQUEST_PATH)
    decision = load_strict_json(Path(repo_root) / DECISION_PATH)
    if request != expected_request:
        raise ValueError("T20.23 authority request drifted from live verified sources")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.23 authority decision drifted from recomposition")
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    return {"request": request, "decision": decision}


def require_active_t20_23_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    verified = verify_production_authority(repo_root=repo_root)
    current = now or datetime.now().astimezone()
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("Current T20.23 authority time must carry a UTC offset")
    if current < datetime.fromisoformat(VALID_FROM):
        raise ValueError("T20.23 simulation-training authority is not yet active")
    if current > datetime.fromisoformat(VALID_UNTIL):
        raise ValueError("T20.23 simulation-training authority has expired")
    return verified


def _shared_refs(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = spec.get("source_artifacts")
    if not isinstance(sources, dict):
        raise ValueError("T20.23 shared authority sources are missing")
    required = (
        "structural_twin",
        "executable_stack",
        "coordinate_contract",
        "compiler_replay_audit",
    )
    result = {}
    for name in required:
        row = sources.get(name)
        if not isinstance(row, dict):
            raise ValueError(f"T20.23 shared authority source is missing: {name}")
        result[name] = dict(row)
    return result


def _ref_from_spec(root: Path, spec: dict[str, Any], key: str) -> dict[str, Any]:
    ref = spec.get(key)
    if not isinstance(ref, dict):
        raise ValueError(f"T20.23 specification reference is missing: {key}")
    payload = load_strict_json(root / ref["path"])
    expected = artifact_ref(path=Path(ref["path"]), payload=payload, repo_root=root)
    if ref != expected:
        raise ValueError(f"T20.23 specification reference drifted: {key}")
    return expected


def _signed_ref(root: Path, path: Path, label: str) -> dict[str, Any]:
    payload = load_strict_json(root / path)
    verify_signed_payload(payload, label=label)
    return artifact_ref(path=path, payload=payload, repo_root=root)
