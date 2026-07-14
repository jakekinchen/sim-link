"""Production-only T20.1 authority composition for bounded simulation training."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_artifact_ref,
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
    SCHEMA_VERSION as TRAINING_SPEC_SCHEMA_VERSION,
    SPEC_PATH,
    verify_training_spec_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER_GRANT_SCHEMA_VERSION = "scenesmith.owner_training_authorization.v1"
OWNER_GRANT_PATH = Path("configurations/robot_lab/t20_1_owner_training_authorization.json")
REQUEST_PATH = Path("configurations/robot_lab/t20_1_simulation_training_authority_request.json")
DECISION_PATH = Path("configurations/robot_lab/t20_1_simulation_training_authority_decision.json")
EVALUATION_TIME = "2026-07-14T03:06:00-05:00"
VALID_FROM = "2026-07-14T03:05:00-05:00"
VALID_UNTIL = "2026-07-21T03:05:00-05:00"
AUTHORIZED_ACTIONS = (
    "simulation_model_load",
    "simulation_model_inference",
    "simulation_optimizer_training",
    "simulation_policy_evaluation",
)


def build_owner_training_grant(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    spec = verify_training_spec_file(repo_root=root)
    return sign_payload(
        {
            "schema_version": OWNER_GRANT_SCHEMA_VERSION,
            "authorization_id": "t20_1_simulation_training_owner_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": "t20_1_simulation_only_training",
            "source_training_spec_ref": artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root),
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "simulation_only": True,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "issued_at": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "authorization_source": "explicit_owner_training_ready_direction",
        }
    )


def write_owner_training_grant(
    *, repo_root: Path = REPO_ROOT, owner_grant_path: Path = OWNER_GRANT_PATH
) -> dict[str, Any]:
    payload = build_owner_training_grant(repo_root=repo_root)
    dump_canonical_json(_resolve(Path(repo_root), owner_grant_path), payload)
    return payload


def verify_owner_training_grant(
    payload: dict[str, Any], *, repo_root: Path = REPO_ROOT
) -> None:
    verify_signed_payload(payload, label="owner simulation-training grant")
    if payload != build_owner_training_grant(repo_root=repo_root):
        raise ValueError("Owner simulation-training grant drifted from the authorized scope")


def build_production_authority(
    *, repo_root: Path = REPO_ROOT, owner_grant_path: Path = OWNER_GRANT_PATH
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    spec = verify_training_spec_file(repo_root=root)
    owner = load_strict_json(_resolve(root, owner_grant_path))
    verify_owner_training_grant(owner, repo_root=root)
    owner_ref = artifact_ref(path=owner_grant_path, payload=owner, repo_root=root)
    sources = _verify_spec_sources(root, spec)
    contract = build_authority_contract()
    requirements = {item["prerequisite_id"]: item for item in contract["prerequisites"]}
    expected_ids = {
        "required_training_authority_present",
        "structural_contract_valid",
        "executable_stack_valid",
        "coordinate_contract_valid",
        "normalization_contract_valid",
        "experience_compiler_valid",
        "required_simulation_properties_available",
    }
    if set(requirements) & expected_ids != expected_ids:
        raise ValueError("Simulation authority contract lacks a required prerequisite")
    evidence = {
        "required_training_authority_present": [owner_ref],
        "structural_contract_valid": [sources["structural_twin"], artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root)],
        "executable_stack_valid": [sources["executable_stack"], artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root)],
        "coordinate_contract_valid": [sources["coordinate_contract"], artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root)],
        "normalization_contract_valid": [artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root)],
        "experience_compiler_valid": [sources["compiler_replay_audit"], artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root)],
        "required_simulation_properties_available": [sources["episode_store"], artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root)],
    }
    claims = []
    for prerequisite_id in sorted(expected_ids):
        requirement = requirements[prerequisite_id]
        provenance = requirement["allowed_provenance_classes"][0]
        claims.append(
            build_capability_claim(
                claim_id=f"t20_1_{prerequisite_id}",
                capability_id=prerequisite_id,
                value=True,
                subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                provenance_class=provenance,
                issuer=requirement["authorized_issuers"][0],
                validity={
                    "observed_at": VALID_FROM,
                    "valid_from": VALID_FROM,
                    "valid_until": VALID_UNTIL,
                    "max_age_seconds": 604800,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind="source_bound_training_evidence",
                        artifact_schema_version=ref["schema_version"],
                        artifact_identity_sha256=ref["identity_sha256"],
                        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                        provenance_class=provenance,
                    )
                    for ref in evidence[prerequisite_id]
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
        raise ValueError("Production training authority exceeded simulation-only scope")
    return request, decision


def write_production_authority(
    *,
    repo_root: Path = REPO_ROOT,
    owner_grant_path: Path = OWNER_GRANT_PATH,
    request_path: Path = REQUEST_PATH,
    decision_path: Path = DECISION_PATH,
) -> dict[str, Any]:
    root = Path(repo_root)
    request, decision = build_production_authority(repo_root=root, owner_grant_path=owner_grant_path)
    dump_canonical_json(_resolve(root, request_path), request)
    dump_canonical_json(_resolve(root, decision_path), decision)
    return {"request": request, "decision": decision}


def verify_production_authority(
    *,
    repo_root: Path = REPO_ROOT,
    owner_grant_path: Path = OWNER_GRANT_PATH,
    request_path: Path = REQUEST_PATH,
    decision_path: Path = DECISION_PATH,
) -> dict[str, Any]:
    root = Path(repo_root)
    expected_request, expected_decision = build_production_authority(
        repo_root=root, owner_grant_path=owner_grant_path
    )
    request = load_strict_json(_resolve(root, request_path))
    decision = load_strict_json(_resolve(root, decision_path))
    if request != expected_request:
        raise ValueError("Production training authority request drifted from verified sources")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("Production training authority decision drifted from recomputation")
    require_global_decision(decision, request=request, decision_id="simulation_training_ready")
    return {"request": request, "decision": decision}


def _verify_spec_sources(root: Path, spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = spec.get("source_artifacts")
    if not isinstance(sources, dict):
        raise ValueError("T20.1 source artifacts are missing")
    result = {}
    for name in ("structural_twin", "executable_stack", "coordinate_contract", "compiler_replay_audit", "episode_store"):
        reference = sources.get(name)
        if not isinstance(reference, dict):
            raise ValueError(f"T20.1 {name} reference is missing")
        path = _resolve(root, Path(reference.get("path", "")))
        payload = load_strict_json(path)
        verify_signed_payload(payload, label=f"T20.1 authority {name}")
        expected = artifact_ref(path=Path(reference["path"]), payload=payload, repo_root=root)
        verify_artifact_ref(reference, expected, label=f"T20.1 {name}")
        result[name] = expected
    _validate_authority_sources(result, spec)
    return result


def _validate_authority_sources(sources: dict[str, dict[str, Any]], spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != TRAINING_SPEC_SCHEMA_VERSION or spec.get("simulation_only") is not True:
        raise ValueError("T20.1 training specification scope drifted")
    if spec.get("training_input_scope") != "simulation_only_source_bound_act_overfit":
        raise ValueError("T20.1 training input scope is not production-authorizable")
    if spec.get("actor_privileged_fields_available") is not False:
        raise ValueError("T20.1 training specification exposes privileged actor fields")
    if any(spec.get(field) is not False for field in ("optimizer_training", "simulation_training_ready", "physical_actuation", "external_compute_started", "brev_compute_started")):
        raise ValueError("T20.1 specification carries unauthorized execution state")
    if sources["structural_twin"]["schema_version"] != "scenesmith.structural_twin_diff.v1":
        raise ValueError("T20.1 structural evidence schema drifted")
    if sources["executable_stack"]["schema_version"] != "scenesmith.robotics_dependency_lock.v2":
        raise ValueError("T20.1 executable-stack evidence schema drifted")
    if sources["coordinate_contract"]["schema_version"] != "scenesmith.so101_canonical_processor_contract.v1":
        raise ValueError("T20.1 coordinate evidence schema drifted")
    if sources["compiler_replay_audit"]["schema_version"] != "scenesmith.compiler_window_replay_audit.v1":
        raise ValueError("T20.1 compiler evidence schema drifted")
    if sources["episode_store"]["schema_version"] != "scenesmith.scripted_grasp_episode_store.v1":
        raise ValueError("T20.1 simulation evidence schema drifted")


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


__all__ = [
    "DECISION_PATH",
    "EVALUATION_TIME",
    "OWNER_GRANT_PATH",
    "REQUEST_PATH",
    "build_owner_training_grant",
    "build_production_authority",
    "verify_production_authority",
    "write_owner_training_grant",
    "write_production_authority",
]
