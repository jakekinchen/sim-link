"""Central one-use inference authority for T20.36m tensor reproduction."""

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
from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (
    SPEC_PATH as SMOLVLA_SPEC_PATH,
)
from scenesmith.robot_lab.t20_36j_exact_smolvla_gate_b import (
    RUN_RESULT_PATH as SMOLVLA_RESULT_PATH,
    RUN_SUMMARY_PATH as SMOLVLA_RUN_PATH,
)
from scenesmith.robot_lab.t20_36l_frozen_consequence_gate import (
    RESULT_PATH as FROZEN_SCORE_PATH,
    SPEC_PATH as FROZEN_GATE_PATH,
    verify_result as verify_frozen_score,
    verify_spec as verify_frozen_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_36m_owner_tensor_reproduction_authorization.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_36m_simulation_inference_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_36m_simulation_inference_authority_decision.json"
)
VALID_FROM = "2026-07-16T01:44:12-05:00"
VALID_UNTIL = "2026-07-16T09:44:12-05:00"
EVALUATION_TIME = VALID_FROM
AUTHORIZED_ACTIONS = (
    "simulation_model_construction",
    "simulation_model_load",
    "simulation_model_inference",
    "persist_reproduced_action_tensors",
    "score_frozen_gate_b",
)
INFERENCE_SEED_COUNT = 5
REPEATS_PER_SEED = 2
EXPECTED_SMOLVLA_RUN_IDENTITY = (
    "7e7304c5217bed1c95ae5403c009d1f4aa78a75c387f5449299dd50421d2a1bb"
)
EXPECTED_SMOLVLA_RESULT_IDENTITY = (
    "08ef923d1ebcffde26055834db271e92bb068e0eb09f75c60078f2d8b548c4a1"
)
EXPECTED_CHECKPOINT_IDENTITY = (
    "32f0bd3035a984d3b0ee2a752c1195fd252f61e9b2a560d1762e856f44ce81fa"
)
EXPECTED_FROZEN_GATE_IDENTITY = (
    "463477dc91e3fb36b0550b88d461a788709a7258f9825ad6644f98bf0c77e48f"
)
EXPECTED_FROZEN_SCORE_IDENTITY = (
    "0f8ae393c48a2b7384033ac37b9994959a1a826565f00319e03115e53da786f1"
)


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    paths = {
        "smolvla_spec": SMOLVLA_SPEC_PATH,
        "smolvla_run": SMOLVLA_RUN_PATH,
        "smolvla_result": SMOLVLA_RESULT_PATH,
        "frozen_gate": FROZEN_GATE_PATH,
        "frozen_score": FROZEN_SCORE_PATH,
    }
    sources = {name: load_strict_json(root / path) for name, path in paths.items()}
    for name, payload in sources.items():
        verify_signed_payload(payload, label=f"T20.36m {name}")
    verify_frozen_gate(sources["frozen_gate"], repo_root=root)
    verify_frozen_score(
        sources["frozen_score"], spec=sources["frozen_gate"], repo_root=root
    )
    run = sources["smolvla_run"]
    result = sources["smolvla_result"]
    if (
        run.get("identity_sha256") != EXPECTED_SMOLVLA_RUN_IDENTITY
        or result.get("identity_sha256") != EXPECTED_SMOLVLA_RESULT_IDENTITY
        or run.get("checkpoint_identity_sha256") != EXPECTED_CHECKPOINT_IDENTITY
        or sources["frozen_gate"].get("identity_sha256")
        != EXPECTED_FROZEN_GATE_IDENTITY
        or sources["frozen_score"].get("identity_sha256")
        != EXPECTED_FROZEN_SCORE_IDENTITY
    ):
        raise ValueError("T20.36m frozen source identity drifted")
    inherited_request = load_strict_json(root / T20_23_REQUEST_PATH)
    inherited_decision = load_strict_json(root / T20_23_DECISION_PATH)
    verify_authority_decision(inherited_decision, request=inherited_request)
    require_global_decision(
        inherited_decision,
        request=inherited_request,
        decision_id="simulation_training_ready",
    )
    return {
        **sources,
        "paths": paths,
        "inherited_request": inherited_request,
        "inherited_decision": inherited_decision,
    }


def build_owner_grant(
    *, sources: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root)
    return sign_payload(
        {
            "schema_version": "scenesmith.owner_inference_authorization.v1",
            "authorization_id": "t20_36m_smolvla_tensor_reproduction_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": (
                "one_exact_retained_smolvla_five_seed_two_repeat_tensor_"
                "reproduction_and_frozen_gate_score"
            ),
            "source_run_ref": artifact_ref(
                path=SMOLVLA_RUN_PATH,
                payload=sources["smolvla_run"],
                repo_root=root,
            ),
            "source_result_ref": artifact_ref(
                path=SMOLVLA_RESULT_PATH,
                payload=sources["smolvla_result"],
                repo_root=root,
            ),
            "frozen_gate_ref": artifact_ref(
                path=FROZEN_GATE_PATH,
                payload=sources["frozen_gate"],
                repo_root=root,
            ),
            "frozen_score_ref": artifact_ref(
                path=FROZEN_SCORE_PATH,
                payload=sources["frozen_score"],
                repo_root=root,
            ),
            "source_checkpoint_identity_sha256": EXPECTED_CHECKPOINT_IDENTITY,
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "authorized_attempt_count": 1,
            "inference_seed_count": INFERENCE_SEED_COUNT,
            "repeats_per_seed": REPEATS_PER_SEED,
            "existing_hashes_must_reproduce_before_scoring": True,
            "network_access_authorized": False,
            "optimizer_authorized": False,
            "training_retry_authorized": False,
            "threshold_change_authorized": False,
            "gate_c_authorized": False,
            "policy_track_selection_authorized": False,
            "simulation_only": True,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "issued_at": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "authorization_source": (
                "owner_eight_hour_research_critique_continue_authorization_"
                "2026_07_16"
            ),
        }
    )


def verify_owner_grant(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.36m owner inference grant")
    if payload != build_owner_grant(sources=sources, repo_root=repo_root):
        raise ValueError("T20.36m owner inference grant drifted")


def build_production_authority(
    *,
    sources: dict[str, Any] | None = None,
    owner: dict[str, Any] | None = None,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    sources = sources or load_verified_sources(repo_root=root)
    owner = owner or load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_grant(owner, sources=sources, repo_root=root)
    refs = {
        "owner": artifact_ref(path=OWNER_GRANT_PATH, payload=owner, repo_root=root)
        if (root / OWNER_GRANT_PATH).is_file()
        else _pending_ref(OWNER_GRANT_PATH, owner),
        "smolvla_spec": artifact_ref(
            path=SMOLVLA_SPEC_PATH,
            payload=sources["smolvla_spec"],
            repo_root=root,
        ),
        "smolvla_run": artifact_ref(
            path=SMOLVLA_RUN_PATH,
            payload=sources["smolvla_run"],
            repo_root=root,
        ),
        "smolvla_result": artifact_ref(
            path=SMOLVLA_RESULT_PATH,
            payload=sources["smolvla_result"],
            repo_root=root,
        ),
        "frozen_gate": artifact_ref(
            path=FROZEN_GATE_PATH,
            payload=sources["frozen_gate"],
            repo_root=root,
        ),
        "frozen_score": artifact_ref(
            path=FROZEN_SCORE_PATH,
            payload=sources["frozen_score"],
            repo_root=root,
        ),
        "inherited_authority": artifact_ref(
            path=T20_23_DECISION_PATH,
            payload=sources["inherited_decision"],
            repo_root=root,
        ),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [
            refs["inherited_authority"],
            refs["smolvla_spec"],
            refs["frozen_gate"],
        ],
        "executable_stack_valid": [
            refs["smolvla_run"],
            refs["smolvla_result"],
        ],
        "coordinate_contract_valid": [refs["smolvla_spec"], refs["frozen_gate"]],
        "normalization_contract_valid": [refs["smolvla_spec"], refs["smolvla_run"]],
        "experience_compiler_valid": [
            refs["inherited_authority"],
            refs["smolvla_spec"],
        ],
        "required_simulation_properties_available": [
            refs["smolvla_result"],
            refs["frozen_gate"],
            refs["frozen_score"],
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
                claim_id=f"t20_36m_{prerequisite_id}",
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
                        artifact_kind="t20_36m_tensor_reproduction_evidence",
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
        raise ValueError("T20.36m central authority exceeded inference scope")
    return request, decision


def write_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_verified_sources(repo_root=root)
    owner = build_owner_grant(sources=sources, repo_root=root)
    dump_canonical_json(root / OWNER_GRANT_PATH, owner)
    request, decision = build_production_authority(
        sources=sources, owner=owner, repo_root=root
    )
    dump_canonical_json(root / REQUEST_PATH, request)
    dump_canonical_json(root / DECISION_PATH, decision)
    return {"owner_grant": owner, "request": request, "decision": decision}


def verify_authority(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_verified_sources(repo_root=root)
    owner = load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_grant(owner, sources=sources, repo_root=root)
    expected_request, expected_decision = build_production_authority(
        sources=sources, owner=owner, repo_root=root
    )
    request = load_strict_json(root / REQUEST_PATH)
    decision = load_strict_json(root / DECISION_PATH)
    if request != expected_request:
        raise ValueError("T20.36m authority request drifted")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.36m authority decision drifted")
    return {"owner_grant": owner, "request": request, "decision": decision}


def require_active_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    result = verify_authority(repo_root=repo_root)
    current = now or datetime.now().astimezone()
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("T20.36m authority time must carry a UTC offset")
    if current < datetime.fromisoformat(VALID_FROM):
        raise ValueError("T20.36m authority is not active yet")
    if current > datetime.fromisoformat(VALID_UNTIL):
        raise ValueError("T20.36m authority has expired")
    return result


def _pending_ref(path: Path, payload: dict[str, Any]) -> dict[str, str]:
    import json
    import hashlib

    data = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    return {
        "path": str(path),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(data).hexdigest(),
    }
