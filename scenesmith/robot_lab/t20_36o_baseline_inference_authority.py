"""Central one-use authority for the T20.36o X baseline bridge capture."""

from __future__ import annotations

import hashlib
import json

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
from scenesmith.robot_lab.t20_17_clean_base_preflight import (
    TRAINING_SPEC_PATH as BASE_MODEL_SPEC_PATH,
)
from scenesmith.robot_lab.t20_23_simulation_training_authority import (
    DECISION_PATH as INHERITED_DECISION_PATH,
    REQUEST_PATH as INHERITED_REQUEST_PATH,
)
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (
    RESULT_PATH as T20_35X_RESULT_PATH,
    SPEC_PATH as T20_35X_SPEC_PATH,
)
from scenesmith.robot_lab.t20_36n_tensor_reproduction_authority import (
    T20_35X_RUN_PATH,
)
from scenesmith.robot_lab.t20_36n_tensor_reproduction import (
    load_verified_sources as load_x_runtime_sources,
)
from scenesmith.robot_lab.t20_36o_episode_bridge_design import (
    FROZEN_GATE_PATH,
    SPEC_PATH as BRIDGE_SPEC_PATH,
    T20_36N_RESULT_PATH,
    verify_bridge_spec_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_owner_authorization.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_inference_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_inference_authority_decision.json"
)
VALID_FROM = "2026-07-16T01:44:12-05:00"
VALID_UNTIL = "2026-07-16T09:44:12-05:00"
EVALUATION_TIME = VALID_FROM
AUTHORIZED_ACTIONS = (
    "simulation_model_construction_once",
    "simulation_model_load_once",
    "simulation_model_inference_exact_registered_probe_matrix",
    "persist_fifty_decoded_action_chunks",
    "persist_five_hundred_denoise_step_records",
    "score_frozen_bridge_acceptance",
)


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    bridge_spec = verify_bridge_spec_file(repo_root=root)
    x_sources = load_x_runtime_sources(repo_root=root)
    inherited_request = load_strict_json(root / INHERITED_REQUEST_PATH)
    inherited_decision = load_strict_json(root / INHERITED_DECISION_PATH)
    verify_authority_decision(inherited_decision, request=inherited_request)
    require_global_decision(
        inherited_decision,
        request=inherited_request,
        decision_id="simulation_training_ready",
    )
    base_model_spec = load_strict_json(root / BASE_MODEL_SPEC_PATH)
    verify_signed_payload(base_model_spec, label="T20.36o base model spec")
    result = load_strict_json(root / T20_36N_RESULT_PATH)
    verify_signed_payload(result, label="T20.36o X result")
    if (
        bridge_spec.get("identity_sha256")
        != "8294c63be101dbb1ea3536d2b2da1447d23ca9aa71d2145eb501452547c30c0c"
        or result.get("identity_sha256")
        != "f8d7866e852a9b9a288b724016abe104dc94bf631251023faa8d26dbf5b86eb7"
        or x_sources.get("checkpoint_identity_sha256")
        != bridge_spec.get("source_checkpoint_identity_sha256")
        or bridge_spec.get("execution_contract", {}).get("chunk_start_frames")
        != [0, 50, 100, 150, 200]
        or bridge_spec.get("probe_contract", {}).get("repeats_per_probe") != 2
    ):
        raise ValueError("T20.36o baseline authority source drifted")
    return {
        "bridge_spec": bridge_spec,
        "x_result": result,
        "x_runtime": x_sources,
        "base_model_spec": base_model_spec,
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
            "authorization_id": "t20_36o_x_episode_0_baseline_capture_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": (
                "one_exact_x_five_state_five_seed_two_repeat_decoded_and_"
                "denoise_path_capture_before_any_optimizer"
            ),
            "bridge_spec_ref": _ref_or_pending(
                BRIDGE_SPEC_PATH, sources["bridge_spec"], root
            ),
            "x_result_ref": artifact_ref(
                path=T20_36N_RESULT_PATH,
                payload=sources["x_result"],
                repo_root=root,
            ),
            "source_checkpoint_identity_sha256": sources["x_runtime"][
                "checkpoint_identity_sha256"
            ],
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "authorized_attempt_count": 1,
            "chunk_start_count": 5,
            "inference_seed_count_per_start": 5,
            "repeats_per_start_seed": 2,
            "decoded_chunk_count": 50,
            "denoise_step_count_per_chunk": 10,
            "denoise_step_record_count": 500,
            "start_zero_existing_hashes_must_reproduce": True,
            "baseline_capture_precedes_optimizer": True,
            "network_access_authorized": False,
            "optimizer_authorized": False,
            "training_authorized": False,
            "training_retry_authorized": False,
            "threshold_change_authorized": False,
            "gate_c_authorized": False,
            "policy_track_selection_authorized": False,
            "physical_hardware_authorized": False,
            "simulation_only": True,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "issued_at": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "authorization_source": (
                "owner_eight_hour_research_critique_continue_authorization_"
                "and_owner_priority_3_x_bridge_direction_2026_07_16"
            ),
        }
    )


def verify_owner_grant(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.36o baseline owner grant")
    if payload != build_owner_grant(sources=sources, repo_root=repo_root):
        raise ValueError("T20.36o baseline owner grant drifted")


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
    x_runtime = sources["x_runtime"]
    refs = {
        "owner": _ref_or_pending(OWNER_GRANT_PATH, owner, root),
        "bridge_spec": artifact_ref(
            path=BRIDGE_SPEC_PATH,
            payload=sources["bridge_spec"],
            repo_root=root,
        ),
        "x_result": artifact_ref(
            path=T20_36N_RESULT_PATH,
            payload=sources["x_result"],
            repo_root=root,
        ),
        "x_spec": artifact_ref(
            path=T20_35X_SPEC_PATH,
            payload=x_runtime["t20_35x_spec"],
            repo_root=root,
        ),
        "x_run": artifact_ref(
            path=T20_35X_RUN_PATH,
            payload=x_runtime["source_run"],
            repo_root=root,
        ),
        "x_source_result": artifact_ref(
            path=T20_35X_RESULT_PATH,
            payload=x_runtime["source_result"],
            repo_root=root,
        ),
        "base_model_spec": artifact_ref(
            path=BASE_MODEL_SPEC_PATH,
            payload=sources["base_model_spec"],
            repo_root=root,
        ),
        "frozen_gate": artifact_ref(
            path=FROZEN_GATE_PATH,
            payload=x_runtime["frozen_gate"],
            repo_root=root,
        ),
        "inherited_authority": artifact_ref(
            path=INHERITED_DECISION_PATH,
            payload=sources["inherited_decision"],
            repo_root=root,
        ),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [
            refs["inherited_authority"],
            refs["bridge_spec"],
            refs["base_model_spec"],
        ],
        "executable_stack_valid": [
            refs["x_run"],
            refs["x_source_result"],
            refs["x_result"],
        ],
        "coordinate_contract_valid": [refs["x_spec"], refs["frozen_gate"]],
        "normalization_contract_valid": [refs["x_spec"], refs["x_run"]],
        "experience_compiler_valid": [
            refs["inherited_authority"],
            refs["bridge_spec"],
        ],
        "required_simulation_properties_available": [
            refs["x_result"],
            refs["bridge_spec"],
            refs["frozen_gate"],
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
                claim_id=f"t20_36o_baseline_{prerequisite_id}",
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
                        artifact_kind="t20_36o_baseline_capture_evidence",
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
        raise ValueError("T20.36o central authority exceeded baseline scope")
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
        raise ValueError("T20.36o baseline authority request drifted")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.36o baseline authority decision drifted")
    return {"owner_grant": owner, "request": request, "decision": decision}


def require_active_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    result = verify_authority(repo_root=repo_root)
    current = now or datetime.now().astimezone()
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("T20.36o authority time must carry a UTC offset")
    if current < datetime.fromisoformat(VALID_FROM):
        raise ValueError("T20.36o baseline authority is not active yet")
    if current > datetime.fromisoformat(VALID_UNTIL):
        raise ValueError("T20.36o baseline authority has expired")
    return result


def _ref_or_pending(path: Path, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    if (root / path).is_file():
        return artifact_ref(path=path, payload=payload, repo_root=root)
    data = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    return {
        "path": path.as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(data).hexdigest(),
    }
