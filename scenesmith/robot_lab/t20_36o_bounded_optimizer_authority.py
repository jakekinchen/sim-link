"""Central authority, preflight, and permit for T20.36o bounded correction."""

from __future__ import annotations

import hashlib

from datetime import datetime
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
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
    RESULT_PATH as SOURCE_RESULT_PATH,
    SPEC_PATH as SOURCE_SPEC_PATH,
)
from scenesmith.robot_lab.t20_36n_tensor_reproduction import (
    load_verified_sources as load_x_runtime_sources,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_spec import (
    RETENTION_RECEIPT_PATH,
    SPEC_PATH as OPTIMIZER_SPEC_PATH,
    load_verified_sources as load_optimizer_sources,
    verify_optimizer_spec,
)
from scenesmith.robot_lab.t20_36o_episode_bridge_design import (
    SPEC_PATH as BRIDGE_SPEC_PATH,
)
from scenesmith.robot_lab.t20_36o_baseline_capture import (
    RESULT_PATH as BASELINE_RESULT_PATH,
    TRAJECTORY_PATH,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_owner_authorization.json"
)
REQUEST_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_authority_decision.json"
)
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_runtime_preflight.json"
)
TRAINING_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_training_permit.json"
)
RUN_ROOT = Path("outputs/robot_lab/t20_36o_bounded_optimizer_run_001")
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
TRACKED_ATTEMPT_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_attempt.json"
)
RESULT_PATH = Path("configurations/robot_lab/t20_36o_optimizer_result.json")
FAILURE_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_failure_result.json"
)
CHECKPOINT_ROOT = RUN_ROOT / "checkpoint"
VALID_FROM = "2026-07-16T01:44:12-05:00"
VALID_UNTIL = "2026-07-16T09:44:12-05:00"
EVALUATION_TIME = VALID_FROM
MINIMUM_FREE_DISK_BYTES = 8 * 1024 * 1024 * 1024
RUNTIME_SCHEMA_VERSION = "scenesmith.t20_36o_optimizer_runtime_preflight.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_36o_optimizer_training_permit.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_36o_optimizer_attempt.v1"
EXPECTED_SPEC_IDENTITY = (
    "50e0569d430fe268f103ee20210b06f25f23a4c6f0efe43d4621a1b4ea32ed26"
)
AUTHORIZED_ACTIONS = (
    "simulation_model_construction_once",
    "simulation_model_load_x_once",
    "simulation_optimizer_creation_once",
    "simulation_optimizer_training_up_to_2500_updates",
    "paired_unique_standard_replay_each_update",
    "registered_bridge_probes_at_500_step_intervals",
    "persist_first_confirmed_passing_checkpoint_or_final_negative",
)


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    optimizer_sources = load_optimizer_sources(repo_root=root)
    spec = load_strict_json(root / OPTIMIZER_SPEC_PATH)
    verify_optimizer_spec(spec, sources=optimizer_sources)
    x_runtime = load_x_runtime_sources(repo_root=root)
    inherited_request = load_strict_json(root / INHERITED_REQUEST_PATH)
    inherited_decision = load_strict_json(root / INHERITED_DECISION_PATH)
    verify_authority_decision(inherited_decision, request=inherited_request)
    require_global_decision(
        inherited_decision,
        request=inherited_request,
        decision_id="simulation_training_ready",
    )
    base_model_spec = load_strict_json(root / BASE_MODEL_SPEC_PATH)
    verify_signed_payload(base_model_spec, label="T20.36o optimizer base model spec")
    if (
        spec.get("identity_sha256") != EXPECTED_SPEC_IDENTITY
        or spec.get("source_checkpoint_identity_sha256")
        != x_runtime.get("checkpoint_identity_sha256")
        or spec.get("optimizer_update_count_ceiling") != 2500
        or spec.get("correction_example_count") != 250
        or spec.get("optimizer_created") is not False
    ):
        raise ValueError("T20.36o optimizer authority source drifted")
    return {
        "optimizer_spec": spec,
        "optimizer_sources": optimizer_sources,
        "x_runtime": x_runtime,
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
            "schema_version": "scenesmith.owner_training_authorization.v1",
            "authorization_id": "t20_36o_x_episode_0_bounded_optimizer_grant",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "authorization_scope": (
                "one_local_simulation_only_retained_path_correction_with_"
                "paired_standard_replay_and_2500_update_ceiling"
            ),
            "optimizer_spec_ref": artifact_ref(
                path=OPTIMIZER_SPEC_PATH,
                payload=sources["optimizer_spec"],
                repo_root=root,
            ),
            "baseline_result_ref": artifact_ref(
                path=BASELINE_RESULT_PATH,
                payload=sources["optimizer_sources"]["baseline_result"],
                repo_root=root,
            ),
            "retention_receipt_ref": artifact_ref(
                path=RETENTION_RECEIPT_PATH,
                payload=sources["optimizer_sources"]["retention_receipt"],
                repo_root=root,
            ),
            "source_checkpoint_identity_sha256": sources["x_runtime"][
                "checkpoint_identity_sha256"
            ],
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "authorized_attempt_count": 1,
            "correction_example_count": 250,
            "uses_per_example_ceiling": 10,
            "optimizer_update_count_ceiling": 2500,
            "standard_replay_update_count_ceiling": 2500,
            "probe_update_counts": [500, 1000, 1500, 2000, 2500],
            "first_confirmed_pass_stops_training": True,
            "retry_authorized": False,
            "threshold_change_authorized": False,
            "gate_c_authorized": False,
            "network_access_authorized": False,
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
                "and_pre_registered_t20_36o_baseline_fail_route"
            ),
        }
    )


def verify_owner_grant(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> None:
    verify_signed_payload(payload, label="T20.36o optimizer owner grant")
    if payload != build_owner_grant(sources=sources, repo_root=repo_root):
        raise ValueError("T20.36o optimizer owner grant drifted")


def build_production_authority(
    *,
    sources: dict[str, Any],
    owner: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root)
    verify_owner_grant(owner, sources=sources, repo_root=root)
    optimizer_sources = sources["optimizer_sources"]
    refs = {
        "owner": artifact_ref(path=OWNER_GRANT_PATH, payload=owner, repo_root=root)
        if (root / OWNER_GRANT_PATH).exists()
        else _pending_ref(OWNER_GRANT_PATH, owner),
        "optimizer_spec": artifact_ref(
            path=OPTIMIZER_SPEC_PATH,
            payload=sources["optimizer_spec"],
            repo_root=root,
        ),
        "bridge_spec": artifact_ref(
            path=BRIDGE_SPEC_PATH,
            payload=optimizer_sources["bridge_spec"],
            repo_root=root,
        ),
        "baseline_result": artifact_ref(
            path=BASELINE_RESULT_PATH,
            payload=optimizer_sources["baseline_result"],
            repo_root=root,
        ),
        "trajectories": artifact_ref(
            path=TRAJECTORY_PATH,
            payload=optimizer_sources["baseline_trajectories"],
            repo_root=root,
        ),
        "receipt": artifact_ref(
            path=RETENTION_RECEIPT_PATH,
            payload=optimizer_sources["retention_receipt"],
            repo_root=root,
        ),
        "source_spec": artifact_ref(
            path=SOURCE_SPEC_PATH,
            payload=optimizer_sources["source_spec"],
            repo_root=root,
        ),
        "source_result": artifact_ref(
            path=SOURCE_RESULT_PATH,
            payload=optimizer_sources["source_result"],
            repo_root=root,
        ),
        "base_model_spec": artifact_ref(
            path=BASE_MODEL_SPEC_PATH,
            payload=sources["base_model_spec"],
            repo_root=root,
        ),
        "inherited": artifact_ref(
            path=INHERITED_DECISION_PATH,
            payload=sources["inherited_decision"],
            repo_root=root,
        ),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [
            refs["inherited"],
            refs["optimizer_spec"],
            refs["base_model_spec"],
        ],
        "executable_stack_valid": [
            refs["source_spec"],
            refs["source_result"],
            refs["receipt"],
        ],
        "coordinate_contract_valid": [refs["bridge_spec"], refs["source_spec"]],
        "normalization_contract_valid": [refs["optimizer_spec"]],
        "experience_compiler_valid": [refs["optimizer_spec"], refs["trajectories"]],
        "required_simulation_properties_available": [
            refs["baseline_result"],
            refs["bridge_spec"],
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
                claim_id=f"t20_36o_optimizer_{prerequisite_id}",
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
                        artifact_kind="t20_36o_optimizer_evidence",
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
        decision,
        request=request,
        decision_id="simulation_training_ready",
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.36o optimizer central authority exceeded scope")
    return request, decision


def build_runtime_preflight(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    python_major_minor: list[int],
    mps_available: bool,
    checkpoint_tree: list[dict[str, Any]],
    dependency_versions: dict[str, str],
    snapshot_revision: str,
    snapshot_tree: list[dict[str, Any]],
    free_disk_bytes: int,
    source_commit: str,
    remote_source_commit: str,
    attempt_exists: bool,
    result_exists: bool,
    output_checkpoint_exists: bool,
) -> dict[str, Any]:
    x_runtime = sources["x_runtime"]
    _sha(authority_identity, "authority identity")
    if (
        python_major_minor != [3, 12]
        or mps_available is not True
        or checkpoint_tree != x_runtime["checkpoint_tree"]
        or dependency_versions != x_runtime["required_dependency_versions"]
        or snapshot_revision != x_runtime["snapshot_revision"]
        or snapshot_tree != x_runtime["snapshot_tree"]
        or isinstance(free_disk_bytes, bool)
        or not isinstance(free_disk_bytes, int)
        or free_disk_bytes < MINIMUM_FREE_DISK_BYTES
        or source_commit != remote_source_commit
        or attempt_exists is not False
        or result_exists is not False
        or output_checkpoint_exists is not False
    ):
        raise ValueError("T20.36o optimizer runtime preflight failed closed")
    return sign_payload(
        {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "task_id": "T20.36o",
            "optimizer_spec_identity_sha256": sources["optimizer_spec"][
                "identity_sha256"
            ],
            "authority_decision_identity_sha256": authority_identity,
            "source_checkpoint_identity_sha256": x_runtime[
                "checkpoint_identity_sha256"
            ],
            "lerobot_stack_identity_sha256": x_runtime[
                "lerobot_stack_identity_sha256"
            ],
            "python_major_minor": python_major_minor,
            "mps_available": True,
            "checkpoint_tree": checkpoint_tree,
            "checkpoint_bytes_hashed": True,
            "checkpoint_tensor_deserialized": False,
            "dependency_versions": dependency_versions,
            "snapshot_revision": snapshot_revision,
            "snapshot_tree": snapshot_tree,
            "snapshot_tree_identity_sha256": hashlib.sha256(
                canonical_json_bytes(snapshot_tree)
            ).hexdigest(),
            "snapshot_files_hashed_without_tensor_deserialization": True,
            "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
            "free_disk_bytes": free_disk_bytes,
            "source_commit": source_commit,
            "remote_source_commit": remote_source_commit,
            "remote_source_commit_matches": True,
            "attempt_exists": False,
            "result_exists": False,
            "output_checkpoint_exists": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "gate_c_authorized": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
) -> None:
    verify_signed_payload(payload, label="T20.36o optimizer preflight")
    expected = build_runtime_preflight(
        sources=sources,
        authority_identity=authority_identity,
        python_major_minor=payload.get("python_major_minor"),
        mps_available=payload.get("mps_available"),
        checkpoint_tree=payload.get("checkpoint_tree"),
        dependency_versions=payload.get("dependency_versions"),
        snapshot_revision=payload.get("snapshot_revision"),
        snapshot_tree=payload.get("snapshot_tree"),
        free_disk_bytes=payload.get("free_disk_bytes"),
        source_commit=payload.get("source_commit"),
        remote_source_commit=payload.get("remote_source_commit"),
        attempt_exists=payload.get("attempt_exists"),
        result_exists=payload.get("result_exists"),
        output_checkpoint_exists=payload.get("output_checkpoint_exists"),
    )
    if payload != expected:
        raise ValueError("T20.36o optimizer runtime preflight drifted")


def build_training_permit(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> dict[str, Any]:
    verify_runtime_preflight(
        runtime_preflight,
        sources=sources,
        authority_identity=authority_identity,
    )
    schedule = sources["optimizer_spec"]["correction_schedule"]
    _validate_schedule(schedule)
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": "T20.36o",
            "optimizer_spec_identity_sha256": sources["optimizer_spec"][
                "identity_sha256"
            ],
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime_preflight[
                "identity_sha256"
            ],
            "source_checkpoint_identity_sha256": sources["x_runtime"][
                "checkpoint_identity_sha256"
            ],
            "snapshot_revision": runtime_preflight["snapshot_revision"],
            "snapshot_tree_identity_sha256": runtime_preflight[
                "snapshot_tree_identity_sha256"
            ],
            "required_source_commit": runtime_preflight["source_commit"],
            "authorized_actions": list(AUTHORIZED_ACTIONS),
            "authorized_attempt_count": 1,
            "construction_seed": schedule["training_seed"],
            "correction_example_count": 250,
            "sample_index_by_update": schedule["sample_index_by_update"],
            "standard_replay_seed_by_update": schedule[
                "standard_replay_seed_by_update"
            ],
            "optimizer_update_count_ceiling": 2500,
            "uses_per_example_ceiling": 10,
            "probe_update_counts": [500, 1000, 1500, 2000, 2500],
            "probe_starts": [0, 50, 100, 150, 200],
            "probe_inference_seeds": [
                20260721,
                20260722,
                20260723,
                20260724,
                20260725,
            ],
            "probe_repeats": 2,
            "baseline_probe_result_identity_sha256": sources[
                "optimizer_sources"
            ]["baseline_result"]["identity_sha256"],
            "first_complete_confirmed_pass_stops_training": True,
            "negative_at_ceiling_stops_without_retry": True,
            "attempt_marker_path": ATTEMPT_PATH.as_posix(),
            "tracked_attempt_path": TRACKED_ATTEMPT_PATH.as_posix(),
            "result_path": RESULT_PATH.as_posix(),
            "output_checkpoint_root": CHECKPOINT_ROOT.as_posix(),
            "marker_must_precede_checkpoint_tensor_read": True,
            "marker_must_precede_model_construction": True,
            "marker_must_precede_optimizer_creation": True,
            "local_execution_eligible_after_remote_preservation": True,
            "retry_authorized": False,
            "threshold_changed": False,
            "gate_c_authorized": False,
            "gate_c_executed": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_training_permit(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36o optimizer permit")
    if payload != build_training_permit(
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    ):
        raise ValueError("T20.36o optimizer permit drifted")


def build_attempt_marker(
    *, permit: dict[str, Any], source_commit: str
) -> dict[str, Any]:
    verify_signed_payload(permit, label="T20.36o optimizer permit")
    _commit(source_commit, "attempt source commit")
    if (
        permit.get("authorized_attempt_count") != 1
        or permit.get("optimizer_update_count_ceiling") != 2500
        or permit.get("marker_must_precede_optimizer_creation") is not True
        or permit.get("retry_authorized") is not False
    ):
        raise ValueError("T20.36o optimizer attempt permit drifted")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": "T20.36o",
            "optimizer_spec_identity_sha256": permit[
                "optimizer_spec_identity_sha256"
            ],
            "training_permit_identity_sha256": permit["identity_sha256"],
            "authority_decision_identity_sha256": permit[
                "authority_decision_identity_sha256"
            ],
            "source_checkpoint_identity_sha256": permit[
                "source_checkpoint_identity_sha256"
            ],
            "source_commit": source_commit,
            "attempt_number": 1,
            "created_before_checkpoint_tensor_read": True,
            "created_before_model_construction": True,
            "created_before_optimizer_creation": True,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_loaded": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "optimizer_update_count": 0,
            "checkpoint_written": False,
            "gate_c_authorized": False,
        }
    )


def verify_attempt_marker(
    payload: dict[str, Any], *, permit: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36o optimizer attempt")
    if payload != build_attempt_marker(
        permit=permit,
        source_commit=payload.get("source_commit"),
    ):
        raise ValueError("T20.36o optimizer attempt marker drifted")


def require_active_authority(
    *, repo_root: Path = REPO_ROOT, now: datetime | None = None
) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_verified_sources(repo_root=root)
    owner = load_strict_json(root / OWNER_GRANT_PATH)
    verify_owner_grant(owner, sources=sources, repo_root=root)
    expected_request, expected_decision = build_production_authority(
        sources=sources,
        owner=owner,
        repo_root=root,
    )
    request = load_strict_json(root / REQUEST_PATH)
    decision = load_strict_json(root / DECISION_PATH)
    if request != expected_request:
        raise ValueError("T20.36o optimizer authority request drifted")
    verify_authority_decision(decision, request=request)
    if decision != expected_decision:
        raise ValueError("T20.36o optimizer authority decision drifted")
    current = now or datetime.now().astimezone()
    if current < datetime.fromisoformat(VALID_FROM) or current > datetime.fromisoformat(
        VALID_UNTIL
    ):
        raise ValueError("T20.36o optimizer authority is inactive")
    return {
        "sources": sources,
        "owner_grant": owner,
        "request": request,
        "decision": decision,
    }


def _pending_ref(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(
            (__import__("json").dumps(payload, indent=2, sort_keys=True) + "\n").encode()
        ).hexdigest(),
    }


def _validate_schedule(schedule: dict[str, Any]) -> None:
    sample_order = schedule.get("sample_index_by_update")
    replay_seeds = schedule.get("standard_replay_seed_by_update")
    if (
        schedule.get("optimizer") != "AdamW"
        or schedule.get("learning_rate") != 2.5e-5
        or schedule.get("optimizer_update_count_ceiling") != 2500
        or schedule.get("uses_per_example_ceiling") != 10
        or schedule.get("standard_replay_update_count") != 2500
        or schedule.get("probe_update_counts")
        != [0, 500, 1000, 1500, 2000, 2500]
        or schedule.get("selection_rule") != "first_complete_confirmed_pass"
        or schedule.get("retry_authorized") is not False
        or not isinstance(sample_order, list)
        or len(sample_order) != 2500
        or any(sample_order.count(index) != 10 for index in range(250))
        or not isinstance(replay_seeds, list)
        or len(replay_seeds) != 2500
        or len(set(replay_seeds)) != 2500
    ):
        raise ValueError("T20.36o optimizer schedule drifted")


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36o {label} must be SHA-256")
    return value


def _commit(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36o {label} must be a full commit")
    return value
