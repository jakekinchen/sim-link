"""Fail-closed contracts for the zero-update T20.43c ACT continuation.

This module is model-free.  It preserves the complete T20.43b failure boundary,
issues separately named continuation authority, and defines the signed marker,
equivalence, terminal, and outer-receipt contracts.  Model construction and the
training loop live in :mod:`t20_43c_act_continuation_runner`.
"""

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
from scenesmith.robot_lab.t20_43b_r1_act_contracts import (
    BRANCH,
    CHECKPOINT_SCHEDULE,
    EVALUATION_ACTION_STEPS,
    EXPECTED_DEPENDENCIES,
    GATE_A_PATH as SOURCE_GATE_A_PATH,
    MAXIMUM_OPTIMIZER_UPDATES,
    SPEC_PATH as SOURCE_SPEC_PATH,
    TRAINING_SEED,
    load_verified_sources as load_t20_43b_sources,
    verify_gate_a,
    verify_spec,
)
from scenesmith.robot_lab.t20_43b_r1_act_runner import (
    ATTEMPT_PATH as SOURCE_ATTEMPT_PATH,
    RUN_ROOT as SOURCE_RUN_ROOT,
    verify_all_outputs as verify_t20_43b_outputs,
    verify_trace as verify_t20_43b_trace,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "T20.43c"
OWNER_INSTRUCTION = (
    "proceed, i authorize anything further actions that resolve this for us."
)
MAXIMUM_AUTHORITY_SECONDS = 8 * 60 * 60
MINIMUM_FREE_DISK_BYTES = 10 * 1024**3

SOURCE_CHECKPOINT_PATH = SOURCE_RUN_ROOT / "checkpoints/step_00000"
SOURCE_TRACE_PATH = SOURCE_RUN_ROOT / "rollouts/step_00000_chunk_50.json"
SOURCE_CHECKPOINT_IDENTITY = (
    "916200d071995a84577a53dc35b552e2f7db2452194adf8cc18b9a6d54ec8b55"
)
SOURCE_MODEL_FILE_SHA256 = (
    "acc865fb2504849ce39a403b08c5bff6b6660460d5622d3089f243c8868cf912"
)
SOURCE_TRACE_IDENTITY = (
    "b707b815ab3b204e29dbbc8e50114307058019da3116f8f5ac496c1b6e05f4bd"
)
SOURCE_TRACE_FILE_SHA256 = (
    "0c01265d4536bff9f2220a0e6e26462342b5987927204db7b998f7e50f3eac46"
)
SOURCE_ATTEMPT_IDENTITY = (
    "d67cf38e7d7a441da93c3af55cdcfeefe64b55ce9cf3f0b95894299a88fdca09"
)
SOURCE_FAILURE_IDENTITY = (
    "89b6dbff17f5da345b1c8d8fa9951989eda092998b702737dd7da16c42db2e92"
)

OWNER_PATH = Path("configurations/robot_lab/t20_43c_act_owner_authorization.json")
REQUEST_PATH = Path("configurations/robot_lab/t20_43c_act_authority_request.json")
DECISION_PATH = Path("configurations/robot_lab/t20_43c_act_authority_decision.json")
RUNTIME_PATH = Path("configurations/robot_lab/t20_43c_act_runtime_preflight.json")
PERMIT_PATH = Path("configurations/robot_lab/t20_43c_act_permit.json")
ACCEPTANCE_PATH = Path("configurations/robot_lab/t20_43c_act_pre_run_acceptance.json")
MARKER_PATH = Path("configurations/robot_lab/t20_43c_act_continuation_marker.json")
EQUIVALENCE_PATH = Path("configurations/robot_lab/t20_43c_act_equivalence_receipt.json")
RESULT_PATH = Path("configurations/robot_lab/t20_43c_act_standard_result.json")
SCORECARD_PATH = Path("configurations/robot_lab/t20_43c_act_scorecard.json")
RETENTION_PATH = Path("configurations/robot_lab/t20_43c_act_retention_receipt.json")
FINAL_RECEIPT_PATH = Path(
    "configurations/robot_lab/t20_43c_act_final_continuation_receipt.json"
)
FAILURE_PATH = Path("configurations/robot_lab/t20_43c_act_terminal_failure.json")

RUN_ROOT = Path("outputs/robot_lab/t20_43c_act_continuation_run_001")
CHECKPOINT_ROOT = RUN_ROOT / "checkpoints"
ROLLOUT_ROOT = RUN_ROOT / "rollouts"
VIDEO_ROOT = RUN_ROOT / "mirrors"
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
PROGRESS_PATH = RUN_ROOT / "progress.json"
SMOKE_ROOT = Path("outputs/robot_lab/t20_43c_renderer_smoke_001")
SMOKE_VIDEO_PATH = SMOKE_ROOT / "checkpoint_0_chunk_50.mp4"
SMOKE_MANIFEST_PATH = SMOKE_VIDEO_PATH.with_suffix(".manifest.json")
SMOKE_RECEIPT_PATH = Path("configurations/robot_lab/t20_43c_renderer_smoke.json")

AUTHORITY_PATHS = (
    SMOKE_RECEIPT_PATH,
    OWNER_PATH,
    REQUEST_PATH,
    DECISION_PATH,
    RUNTIME_PATH,
    PERMIT_PATH,
)
OUTPUT_PATHS = (
    ACCEPTANCE_PATH,
    MARKER_PATH,
    EQUIVALENCE_PATH,
    RESULT_PATH,
    SCORECARD_PATH,
    RETENTION_PATH,
    FINAL_RECEIPT_PATH,
    FAILURE_PATH,
    RUN_ROOT,
)

OWNER_SCHEMA = "scenesmith.t20_43c_act_owner_authorization.v1"
SMOKE_SCHEMA = "scenesmith.t20_43c_renderer_smoke.v1"
RUNTIME_SCHEMA = "scenesmith.t20_43c_act_runtime_preflight.v1"
PERMIT_SCHEMA = "scenesmith.t20_43c_act_permit.v1"
ACCEPTANCE_SCHEMA = "scenesmith.t20_43c_act_pre_run_acceptance.v1"
MARKER_SCHEMA = "scenesmith.t20_43c_act_continuation_marker.v1"
EQUIVALENCE_SCHEMA = "scenesmith.t20_43c_act_equivalence_receipt.v1"
RETENTION_SCHEMA = "scenesmith.t20_43c_act_retention_receipt.v1"
FINAL_RECEIPT_SCHEMA = "scenesmith.t20_43c_act_final_continuation_receipt.v1"
FAILURE_SCHEMA = "scenesmith.t20_43c_act_terminal_failure.v1"

FALSE_AUTHORITY_FIELDS = (
    "hardware_authorized",
    "network_authorized",
    "external_compute_authorized",
    "brev_compute_authorized",
    "physical_transfer_authorized",
    "promotion_authorized",
    "t20_45_authorized",
)


def load_continuation_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Verify and return the immutable model-free T20.43b source boundary."""

    root = Path(repo_root).resolve()
    terminal = verify_t20_43b_outputs(repo_root=root)
    if terminal.get("identity_sha256") != SOURCE_FAILURE_IDENTITY:
        raise ValueError("T20.43c source failure identity drifted")
    source_bundle = load_t20_43b_sources(repo_root=root)
    spec = load_strict_json(root / SOURCE_SPEC_PATH)
    gate_a = load_strict_json(root / SOURCE_GATE_A_PATH)
    verify_spec(spec, sources=source_bundle)
    verify_gate_a(gate_a, spec=spec)
    attempt = load_strict_json(root / SOURCE_ATTEMPT_PATH)
    trace = load_strict_json(root / SOURCE_TRACE_PATH)
    verify_t20_43b_trace(trace)
    checkpoint_tree = _file_tree(root / SOURCE_CHECKPOINT_PATH)
    checkpoint_identity = hashlib.sha256(
        canonical_json_bytes(checkpoint_tree)
    ).hexdigest()
    if attempt.get("identity_sha256") != SOURCE_ATTEMPT_IDENTITY:
        raise ValueError("T20.43c source attempt identity drifted")
    if checkpoint_identity != SOURCE_CHECKPOINT_IDENTITY:
        raise ValueError("T20.43c source checkpoint identity drifted")
    if (
        _sha_file(root / SOURCE_CHECKPOINT_PATH / "model.safetensors")
        != SOURCE_MODEL_FILE_SHA256
    ):
        raise ValueError("T20.43c source model file drifted")
    if trace.get("identity_sha256") != SOURCE_TRACE_IDENTITY:
        raise ValueError("T20.43c source trace identity drifted")
    if _sha_file(root / SOURCE_TRACE_PATH) != SOURCE_TRACE_FILE_SHA256:
        raise ValueError("T20.43c source trace file drifted")
    return {
        "source_bundle": source_bundle,
        "spec": spec,
        "gate_a": gate_a,
        "attempt": attempt,
        "failure": terminal,
        "checkpoint_tree": checkpoint_tree,
        "trace": trace,
    }


def build_renderer_smoke(*, evidence: dict[str, Any]) -> dict[str, Any]:
    required = {
        "trace_file_sha256": SOURCE_TRACE_FILE_SHA256,
        "trace_identity_sha256": SOURCE_TRACE_IDENTITY,
        "renderer_v2_file_sha256": evidence.get("renderer_v2_file_sha256"),
        "legacy_renderer_file_sha256": evidence.get("legacy_renderer_file_sha256"),
        "video_file_sha256": evidence.get("video_file_sha256"),
        "video_size_bytes": evidence.get("video_size_bytes"),
        "manifest_identity_sha256": evidence.get("manifest_identity_sha256"),
        "manifest_file_sha256": evidence.get("manifest_file_sha256"),
        "runner_interpreter": evidence.get("runner_interpreter"),
        "resumed_after_post_render_materialization_failure": evidence.get(
            "resumed_after_post_render_materialization_failure"
        ),
        "exit_code": 0,
    }
    _sha(required["renderer_v2_file_sha256"])
    _sha(required["legacy_renderer_file_sha256"])
    _sha(required["video_file_sha256"])
    _sha(required["manifest_identity_sha256"])
    _sha(required["manifest_file_sha256"])
    if (
        not isinstance(required["video_size_bytes"], int)
        or required["video_size_bytes"] <= 0
    ):
        raise ValueError("T20.43c renderer smoke video is empty")
    if (
        not isinstance(required["runner_interpreter"], str)
        or not required["runner_interpreter"]
    ):
        raise ValueError("T20.43c renderer smoke interpreter is absent")
    if not isinstance(
        required["resumed_after_post_render_materialization_failure"], bool
    ):
        raise ValueError("T20.43c renderer smoke resume state is invalid")
    return sign_payload(
        {
            "schema_version": SMOKE_SCHEMA,
            "task_id": TASK_ID,
            "source_trace_path": SOURCE_TRACE_PATH.as_posix(),
            "output_video_path": SMOKE_VIDEO_PATH.as_posix(),
            "output_manifest_path": SMOKE_MANIFEST_PATH.as_posix(),
            **required,
            "actual_t20_43b_trace_schema_dispatched": True,
            "model_or_weight_action_executed": False,
            "network_accessed": False,
            **_false_authority_fields(),
        }
    )


def verify_renderer_smoke(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.43c renderer smoke")
    evidence = {
        key: payload.get(key)
        for key in (
            "renderer_v2_file_sha256",
            "legacy_renderer_file_sha256",
            "video_file_sha256",
            "video_size_bytes",
            "manifest_identity_sha256",
            "manifest_file_sha256",
            "runner_interpreter",
            "resumed_after_post_render_materialization_failure",
        )
    }
    if payload != build_renderer_smoke(evidence=evidence):
        raise ValueError("T20.43c renderer smoke drifted")


def build_owner_grant(
    *, required_source_commit: str, valid_from: str, valid_until: str
) -> dict[str, Any]:
    start, stop = _authority_window(valid_from, valid_until)
    return sign_payload(
        {
            "schema_version": OWNER_SCHEMA,
            "task_id": TASK_ID,
            "authorization_id": "t20_43c_one_zero_update_act_continuation",
            "owner_instruction": OWNER_INSTRUCTION,
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "required_source_commit": _commit(required_source_commit),
            "source_attempt_identity_sha256": SOURCE_ATTEMPT_IDENTITY,
            "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
            "source_trace_identity_sha256": SOURCE_TRACE_IDENTITY,
            "authorized_actions": [
                "construct_fresh_seeded_act_for_equivalence",
                "read_and_compare_source_checkpoint_after_marker",
                "create_empty_adamw_optimizer",
                "continue_exact_updates_1_through_10000",
                "run_fixed_dual_semantics_simulation_evaluations",
                "render_and_retain_signed_mirror_mp4",
            ],
            "authorized_attempt_count": 1,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "retry_or_sweep_authorized": False,
            "fresh_replacement_authorized": False,
            "equivalence_required_before_update_1": True,
            "simulation_only": True,
            "issued_at": start.isoformat(),
            "valid_from": start.isoformat(),
            "valid_until": stop.isoformat(),
            "maximum_authority_seconds": MAXIMUM_AUTHORITY_SECONDS,
            **_false_authority_fields(),
        }
    )


def verify_owner_grant(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.43c owner grant")
    expected = build_owner_grant(
        required_source_commit=payload.get("required_source_commit"),
        valid_from=payload.get("valid_from"),
        valid_until=payload.get("valid_until"),
    )
    if payload != expected:
        raise ValueError("T20.43c owner grant drifted")


def build_central_authority(
    *, sources: dict[str, Any], smoke: dict[str, Any], owner: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    verify_renderer_smoke(smoke)
    verify_owner_grant(owner)
    spec = sources["spec"]
    gate_a = sources["gate_a"]
    source_bundle = sources["source_bundle"]
    refs = {
        "owner": _prospective_ref(OWNER_PATH, owner),
        "smoke": _prospective_ref(SMOKE_RECEIPT_PATH, smoke),
        "spec": artifact_ref(path=SOURCE_SPEC_PATH, payload=spec, repo_root=REPO_ROOT),
        "gate_a": artifact_ref(
            path=SOURCE_GATE_A_PATH, payload=gate_a, repo_root=REPO_ROOT
        ),
        "r0_result": dict(source_bundle["source_refs"]["r0_result"]),
        "r0_mixture": dict(source_bundle["source_refs"]["r0_mixture"]),
        "r0_statistics": dict(source_bundle["source_refs"]["r0_statistics"]),
        "r0_dataset": dict(source_bundle["source_refs"]["r0_dataset_manifest"]),
        "inherited_decision": dict(source_bundle["source_refs"]["inherited_decision"]),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [refs["spec"], refs["r0_result"]],
        "executable_stack_valid": [refs["gate_a"], refs["smoke"], refs["spec"]],
        "coordinate_contract_valid": [refs["gate_a"], refs["r0_dataset"]],
        "normalization_contract_valid": [refs["gate_a"], refs["r0_statistics"]],
        "experience_compiler_valid": [refs["r0_mixture"], refs["r0_dataset"]],
        "required_simulation_properties_available": [
            refs["inherited_decision"],
            refs["gate_a"],
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
                claim_id=f"t20_43c_{prerequisite_id}",
                capability_id=prerequisite_id,
                value=True,
                subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                provenance_class=provenance,
                issuer=requirement["authorized_issuers"][0],
                validity={
                    "observed_at": owner["valid_from"],
                    "valid_from": owner["valid_from"],
                    "valid_until": owner["valid_until"],
                    "max_age_seconds": MAXIMUM_AUTHORITY_SECONDS,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind="t20_43c_act_continuation_evidence",
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
        evaluation_time=owner["valid_from"],
        claims=claims,
        composition_mode="production",
    )
    decision = compose_authority(request)
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.43c central authority exceeded simulation training")
    return request, decision


def build_runtime_preflight(
    *,
    sources: dict[str, Any],
    smoke: dict[str, Any],
    owner: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    verify_renderer_smoke(smoke)
    verify_owner_grant(owner)
    verify_authority_decision(decision, request=request)
    _verify_runtime_snapshot(snapshot, owner=owner, sources=sources, smoke=smoke)
    return sign_payload(
        {
            "schema_version": RUNTIME_SCHEMA,
            "task_id": TASK_ID,
            "owner_identity_sha256": owner["identity_sha256"],
            "authority_request_identity_sha256": request["identity_sha256"],
            "authority_decision_identity_sha256": decision["identity_sha256"],
            "renderer_smoke_identity_sha256": smoke["identity_sha256"],
            **snapshot,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "learned_policy_rollout": False,
            "gate_c_executed": False,
            **_false_authority_fields(),
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    smoke: dict[str, Any],
    owner: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.43c runtime preflight")
    excluded = {
        "schema_version",
        "task_id",
        "owner_identity_sha256",
        "authority_request_identity_sha256",
        "authority_decision_identity_sha256",
        "renderer_smoke_identity_sha256",
        "identity_sha256",
        "checkpoint_tensor_read",
        "model_constructed",
        "model_loaded",
        "model_inference",
        "optimizer_created",
        "optimizer_training",
        "learned_policy_rollout",
        "gate_c_executed",
        *FALSE_AUTHORITY_FIELDS,
    }
    snapshot = {key: value for key, value in payload.items() if key not in excluded}
    expected = build_runtime_preflight(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        snapshot=snapshot,
    )
    if payload != expected:
        raise ValueError("T20.43c runtime preflight drifted")


def build_permit(
    *,
    sources: dict[str, Any],
    smoke: dict[str, Any],
    owner: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    verify_runtime_preflight(
        runtime,
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
    )
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA,
            "task_id": TASK_ID,
            "owner_identity_sha256": owner["identity_sha256"],
            "authority_decision_identity_sha256": decision["identity_sha256"],
            "runtime_preflight_identity_sha256": runtime["identity_sha256"],
            "required_source_commit": owner["required_source_commit"],
            "source_attempt_identity_sha256": SOURCE_ATTEMPT_IDENTITY,
            "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
            "source_trace_identity_sha256": SOURCE_TRACE_IDENTITY,
            "authorized_attempt_count": 1,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "evaluation_action_steps": list(EVALUATION_ACTION_STEPS),
            "continuation_marker_path": MARKER_PATH.as_posix(),
            "marker_precedes_checkpoint_tensor_read_and_model_construction": True,
            "equivalence_required_before_update_1": True,
            "retry_or_sweep_authorized": False,
            "fresh_replacement_authorized": False,
            **_false_authority_fields(),
        }
    )


def verify_permit(
    payload: dict[str, Any],
    *,
    sources: dict[str, Any],
    smoke: dict[str, Any],
    owner: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.43c permit")
    expected = build_permit(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )
    if payload != expected:
        raise ValueError("T20.43c permit drifted")


def build_acceptance(
    *,
    authority_commit: str,
    reviewer_decision_id: str,
    reviewer_path: str,
    reviewer_file_sha256: str,
    permit: dict[str, Any],
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": ACCEPTANCE_SCHEMA,
            "task_id": TASK_ID,
            "decision": "ACCEPT_ONE_T20_43C_ZERO_UPDATE_ACT_CONTINUATION",
            "authority_commit": _commit(authority_commit),
            "reviewer_decision_id": str(reviewer_decision_id),
            "reviewer_path": str(reviewer_path),
            "reviewer_file_sha256": _sha(reviewer_file_sha256),
            "permit_identity_sha256": permit["identity_sha256"],
            "continuation_marker_exists": False,
            "checkpoint_tensor_read_or_model_action_executed": False,
            "retry_authorized": False,
            **_false_authority_fields(),
        }
    )


def verify_acceptance(payload: dict[str, Any], *, permit: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.43c pre-run acceptance")
    expected = build_acceptance(
        authority_commit=payload.get("authority_commit"),
        reviewer_decision_id=payload.get("reviewer_decision_id"),
        reviewer_path=payload.get("reviewer_path"),
        reviewer_file_sha256=payload.get("reviewer_file_sha256"),
        permit=permit,
    )
    if payload != expected:
        raise ValueError("T20.43c pre-run acceptance drifted")


def build_continuation_marker(
    *, permit: dict[str, Any], source_commit: str, started_at: str
) -> dict[str, Any]:
    started = _aware_time(started_at, label="continuation start")
    return sign_payload(
        {
            "schema_version": MARKER_SCHEMA,
            "task_id": TASK_ID,
            "permit_identity_sha256": permit["identity_sha256"],
            "attempt_ordinal": 1,
            "source_commit": _commit(source_commit),
            "started_at": started.isoformat(),
            "source_attempt_identity_sha256": SOURCE_ATTEMPT_IDENTITY,
            "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
            "source_trace_identity_sha256": SOURCE_TRACE_IDENTITY,
            "created_before_checkpoint_tensor_read": True,
            "created_before_model_construction": True,
            "created_before_optimizer_creation": True,
            "permit_consumed": True,
            "retry_authorized": False,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            **_false_authority_fields(),
        }
    )


def verify_continuation_marker(
    payload: dict[str, Any], *, permit: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.43c continuation marker")
    expected = build_continuation_marker(
        permit=permit,
        source_commit=payload.get("source_commit"),
        started_at=payload.get("started_at"),
    )
    if payload != expected:
        raise ValueError("T20.43c continuation marker drifted")


def build_equivalence_receipt(
    *,
    marker: dict[str, Any],
    tensor_key_count: int,
    tensor_element_count: int,
    tensor_dtype_counts: dict[str, int],
    compared_tensor_sha256: str,
) -> dict[str, Any]:
    if not isinstance(tensor_key_count, int) or tensor_key_count <= 0:
        raise ValueError("T20.43c equivalence tensor key count is invalid")
    if not isinstance(tensor_element_count, int) or tensor_element_count <= 0:
        raise ValueError("T20.43c equivalence tensor element count is invalid")
    if not isinstance(tensor_dtype_counts, dict) or not tensor_dtype_counts:
        raise ValueError("T20.43c equivalence dtype counts are invalid")
    return sign_payload(
        {
            "schema_version": EQUIVALENCE_SCHEMA,
            "task_id": TASK_ID,
            "continuation_marker_identity_sha256": marker["identity_sha256"],
            "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
            "source_model_file_sha256": SOURCE_MODEL_FILE_SHA256,
            "training_seed": TRAINING_SEED,
            "tensor_key_count": tensor_key_count,
            "tensor_element_count": tensor_element_count,
            "tensor_dtype_counts": tensor_dtype_counts,
            "compared_tensor_sha256": _sha(compared_tensor_sha256),
            "key_sets_exact": True,
            "shapes_exact": True,
            "dtypes_exact": True,
            "tensor_values_bit_exact": True,
            "maximum_absolute_error": 0.0,
            "optimizer_class": "torch.optim.AdamW",
            "optimizer_state_entry_count": 0,
            "optimizer_step_count": 0,
            "training_batches_consumed": 0,
            "sampler_seed": TRAINING_SEED,
            "sampler_unadvanced": True,
            "checkpoint_tensor_read": True,
            "model_constructed": True,
            "model_inference": False,
            "optimizer_created": True,
            "optimizer_training": False,
            "learned_policy_rollout": False,
            "gate_c_executed": False,
            **_false_authority_fields(),
        }
    )


def verify_equivalence_receipt(
    payload: dict[str, Any], *, marker: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.43c equivalence receipt")
    expected = build_equivalence_receipt(
        marker=marker,
        tensor_key_count=payload.get("tensor_key_count"),
        tensor_element_count=payload.get("tensor_element_count"),
        tensor_dtype_counts=payload.get("tensor_dtype_counts"),
        compared_tensor_sha256=payload.get("compared_tensor_sha256"),
    )
    if payload != expected:
        raise ValueError("T20.43c equivalence receipt drifted")


def build_retention_receipt(
    *, result: dict[str, Any], run: dict[str, Any], local_output_trees: dict[str, Any]
) -> dict[str, Any]:
    if set(local_output_trees) != {"checkpoints", "rollouts", "mirrors"}:
        raise ValueError("T20.43c retention tree set drifted")
    return sign_payload(
        {
            "schema_version": RETENTION_SCHEMA,
            "task_id": TASK_ID,
            "result_identity_sha256": result["identity_sha256"],
            "run_identity_sha256": run["identity_sha256"],
            "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
            "source_trace_identity_sha256": SOURCE_TRACE_IDENTITY,
            "local_output_trees": local_output_trees,
            "source_boundary_rewritten": False,
            "large_outputs_tracked_in_git": False,
            "compact_evidence_tracked_in_git": True,
            "retry_authorized": False,
            **_false_authority_fields(),
        }
    )


def build_final_receipt(
    *,
    marker: dict[str, Any],
    equivalence: dict[str, Any],
    result: dict[str, Any],
    retention: dict[str, Any],
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": FINAL_RECEIPT_SCHEMA,
            "task_id": TASK_ID,
            "status": result["status"],
            "source_attempt_identity_sha256": SOURCE_ATTEMPT_IDENTITY,
            "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
            "source_trace_identity_sha256": SOURCE_TRACE_IDENTITY,
            "continuation_marker_identity_sha256": marker["identity_sha256"],
            "equivalence_receipt_identity_sha256": equivalence["identity_sha256"],
            "standard_result_identity_sha256": result["identity_sha256"],
            "retention_receipt_identity_sha256": retention["identity_sha256"],
            "optimizer_update_count": result["optimizer_update_count"],
            "gate_c_passed": result["gate_c_passed"],
            "first_gate_c_pass": result["first_gate_c_pass"],
            "original_failure_preserved": True,
            "zero_update_continuation_proven": True,
            "retry_authorized": False,
            **_false_authority_fields(),
        }
    )


def build_terminal_failure(
    *,
    marker: dict[str, Any],
    progress: dict[str, Any],
    partial_run_tree: list[dict[str, Any]],
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": FAILURE_SCHEMA,
            "task_id": TASK_ID,
            "continuation_marker_identity_sha256": marker["identity_sha256"],
            "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
            "progress": progress,
            "partial_run_tree": partial_run_tree,
            "partial_run_tree_identity_sha256": hashlib.sha256(
                canonical_json_bytes(partial_run_tree)
            ).hexdigest(),
            "error_type": str(error_type),
            "error_message": str(error_message),
            "retry_authorized": False,
            **_false_authority_fields(),
        }
    )


def verify_terminal_failure(
    payload: dict[str, Any],
    *,
    marker: dict[str, Any],
    partial_run_tree: list[dict[str, Any]],
) -> None:
    verify_signed_payload(payload, label="T20.43c terminal failure")
    expected = build_terminal_failure(
        marker=marker,
        progress=payload.get("progress"),
        partial_run_tree=partial_run_tree,
        error_type=payload.get("error_type"),
        error_message=payload.get("error_message"),
    )
    if payload != expected:
        raise ValueError("T20.43c terminal failure drifted")


def _verify_runtime_snapshot(
    snapshot: dict[str, Any],
    *,
    owner: dict[str, Any],
    sources: dict[str, Any],
    smoke: dict[str, Any],
) -> None:
    required = {
        "source_commit",
        "branch",
        "origin_contains_source_commit",
        "scoped_dirty_paths",
        "dependencies",
        "mps_available",
        "free_disk_bytes",
        "network_enabled",
        "source_attempt_identity_sha256",
        "source_failure_identity_sha256",
        "source_checkpoint_identity_sha256",
        "source_model_file_sha256",
        "source_trace_identity_sha256",
        "source_trace_file_sha256",
        "source_partial_tree_identity_sha256",
        "output_path_state",
        "authority_artifacts_materialized",
        "continuation_marker_exists",
    }
    if set(snapshot) != required:
        raise ValueError("T20.43c runtime snapshot fields drifted")
    if (
        snapshot["source_commit"] != owner["required_source_commit"]
        or snapshot["branch"] != BRANCH
    ):
        raise ValueError("T20.43c runtime source drifted")
    if (
        snapshot["origin_contains_source_commit"] is not True
        or snapshot["scoped_dirty_paths"]
    ):
        raise ValueError("T20.43c reviewed source is not preserved cleanly")
    if snapshot["dependencies"] != EXPECTED_DEPENDENCIES:
        raise ValueError("T20.43c dependency versions drifted")
    if (
        snapshot["mps_available"] is not True
        or snapshot["network_enabled"] is not False
    ):
        raise ValueError("T20.43c runtime device/network drifted")
    if (
        not isinstance(snapshot["free_disk_bytes"], int)
        or snapshot["free_disk_bytes"] < MINIMUM_FREE_DISK_BYTES
    ):
        raise ValueError("T20.43c free disk is insufficient")
    expected = {
        "source_attempt_identity_sha256": SOURCE_ATTEMPT_IDENTITY,
        "source_failure_identity_sha256": SOURCE_FAILURE_IDENTITY,
        "source_checkpoint_identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
        "source_model_file_sha256": SOURCE_MODEL_FILE_SHA256,
        "source_trace_identity_sha256": SOURCE_TRACE_IDENTITY,
        "source_trace_file_sha256": SOURCE_TRACE_FILE_SHA256,
        "source_partial_tree_identity_sha256": hashlib.sha256(
            canonical_json_bytes(sources["failure"]["partial_run_tree"])
        ).hexdigest(),
    }
    for key, value in expected.items():
        if snapshot.get(key) != value:
            raise ValueError(f"T20.43c runtime immutable linkage drifted: {key}")
    if (
        snapshot["authority_artifacts_materialized"] is not False
        or snapshot["continuation_marker_exists"] is not False
    ):
        raise ValueError("T20.43c runtime was collected after authority/model action")
    output_state = snapshot["output_path_state"]
    if set(output_state) != {path.as_posix() for path in OUTPUT_PATHS} or any(
        state != {"exists": False, "is_symlink": False}
        for state in output_state.values()
    ):
        raise ValueError("T20.43c output path is not absent and safe")


def verify_materialized_authority(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    sources = load_continuation_sources(repo_root=root)
    bundle = {
        path.as_posix(): load_strict_json(root / path) for path in AUTHORITY_PATHS
    }
    smoke = bundle[SMOKE_RECEIPT_PATH.as_posix()]
    _verify_live_renderer_smoke(smoke, repo_root=root)
    owner = bundle[OWNER_PATH.as_posix()]
    request = bundle[REQUEST_PATH.as_posix()]
    decision = bundle[DECISION_PATH.as_posix()]
    runtime = bundle[RUNTIME_PATH.as_posix()]
    permit = bundle[PERMIT_PATH.as_posix()]
    expected_request, expected_decision = build_central_authority(
        sources=sources, smoke=smoke, owner=owner
    )
    if request != expected_request or decision != expected_decision:
        raise ValueError("T20.43c central authority drifted")
    verify_permit(
        permit,
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )
    return bundle


def _verify_live_renderer_smoke(payload: dict[str, Any], *, repo_root: Path) -> None:
    verify_renderer_smoke(payload)
    video = repo_root / SMOKE_VIDEO_PATH
    manifest_path = repo_root / SMOKE_MANIFEST_PATH
    if (
        not video.is_file()
        or video.is_symlink()
        or not manifest_path.is_file()
        or manifest_path.is_symlink()
    ):
        raise ValueError("T20.43c live renderer smoke outputs are absent or aliased")
    manifest = load_strict_json(manifest_path)
    verify_signed_payload(manifest, label="T20.43c live renderer smoke manifest")
    expected = {
        "video_file_sha256": _sha_file(video),
        "video_size_bytes": video.stat().st_size,
        "manifest_identity_sha256": manifest["identity_sha256"],
        "manifest_file_sha256": _sha_file(manifest_path),
        "renderer_v2_file_sha256": _sha_file(
            repo_root / "scripts/robot_lab/render_rollout_mirror_v2.py"
        ),
        "legacy_renderer_file_sha256": _sha_file(
            repo_root / "scripts/robot_lab/render_rollout_mirror.py"
        ),
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"T20.43c live renderer smoke drifted: {key}")
    if (
        manifest.get("trace_identity_sha256") != SOURCE_TRACE_IDENTITY
        or manifest.get("output_sha256") != payload["video_file_sha256"]
    ):
        raise ValueError("T20.43c live renderer smoke manifest linkage drifted")


def _authority_window(valid_from: str, valid_until: str) -> tuple[datetime, datetime]:
    start = _aware_time(valid_from, label="authority valid_from")
    stop = _aware_time(valid_until, label="authority valid_until")
    seconds = (stop - start).total_seconds()
    if seconds <= 0 or seconds > MAXIMUM_AUTHORITY_SECONDS:
        raise ValueError("T20.43c authority window is invalid")
    return start, stop


def _aware_time(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"T20.43c {label} must be a timestamp")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"T20.43c {label} must be timezone-aware")
    return parsed


def _prospective_ref(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(_canonical_file_bytes(payload)).hexdigest(),
    }


def _canonical_file_bytes(payload: dict[str, Any]) -> bytes:
    import json

    return (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def _file_tree(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and not path.is_symlink():
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": _sha_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    return rows


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("T20.43c expected a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("T20.43c expected a SHA-256 hex digest") from exc
    return value


def _commit(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise ValueError("T20.43c expected a full commit SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("T20.43c expected a full commit SHA") from exc
    return value


def _false_authority_fields() -> dict[str, bool]:
    return {field: False for field in FALSE_AUTHORITY_FIELDS}


__all__ = [
    name
    for name in globals()
    if name.isupper() or name.startswith(("build_", "verify_", "load_"))
]
