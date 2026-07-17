"""Manual, separately rooted replacement for the interrupted T20.43c run.

The first T20.43c permit is immutable and consumed.  This module never reuses
that permit or its paths.  It binds the terminal interruption, creates one new
owner-directed replacement authority epoch, and adapts the reviewed T20.43c
runner to a disjoint layout.  The training recipe and zero-update equivalence
gate remain unchanged.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess

from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_43b_r1_act_contracts import (
    CHECKPOINT_SCHEDULE,
    EVALUATION_ACTION_STEPS,
    MAXIMUM_OPTIMIZER_UPDATES,
)
from scenesmith.robot_lab import t20_43c_act_continuation as base
from scenesmith.robot_lab import (
    t20_43c_act_continuation_materialization as base_materialization,
)
from scenesmith.robot_lab import t20_43c_act_continuation_runner as base_runner


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_TASK_ID = base.TASK_ID
BASE_VERIFY_RENDERER_SMOKE = base.verify_renderer_smoke
TASK_ID = "T20.43c-R2"
OWNER_INSTRUCTION = (
    "Overnight foundation run: W0 finish T20.43c unhurried; the run has all "
    "night, and an infrastructure failure closes it without automatic retry."
)
AUTHORIZATION_ID = "t20_43c_one_manual_replacement_after_directive_interruption"
OWNER_DIRECTION_PATH = Path(
    "docs/autonomous-workflow/owner-addendum-2026-07-16-t20-43c-manual-replacement.md"
)
MINIMUM_COMPLETION_BUDGET_SECONDS = 4 * 60 * 60
MAXIMUM_AUTHORITY_SECONDS = 8 * 60 * 60

PRIOR_MARKER_PATH = base.MARKER_PATH
PRIOR_EQUIVALENCE_PATH = base.EQUIVALENCE_PATH
PRIOR_FAILURE_PATH = base.FAILURE_PATH
PRIOR_RUN_ROOT = base.RUN_ROOT
PRIOR_MARKER_IDENTITY = (
    "e086c293505385d8d85b095d86f993a65266b70abe7047bc83d5bba319d9ed60"
)
PRIOR_EQUIVALENCE_IDENTITY = (
    "85087b2ae94d54ea493ec49a10e6a183369b43c6160e73f79205a7624bb65014"
)
PRIOR_FAILURE_IDENTITY = (
    "d848a1a8d9c803c0d8782e2c51c102cfd4550f1ca5bf22a629a16f34f834bd68"
)
PRIOR_PARTIAL_TREE_IDENTITY = (
    "e0aea95f9df15e4cc0fb817875d8c887d6b9ece6723b48f029114c18ade169b9"
)
PRIOR_OPTIMIZER_UPDATE_COUNT = 728

OWNER_PATH = Path("configurations/robot_lab/t20_43c_r2_act_owner_authorization.json")
REQUEST_PATH = Path("configurations/robot_lab/t20_43c_r2_act_authority_request.json")
DECISION_PATH = Path("configurations/robot_lab/t20_43c_r2_act_authority_decision.json")
RUNTIME_PATH = Path("configurations/robot_lab/t20_43c_r2_act_runtime_preflight.json")
PERMIT_PATH = Path("configurations/robot_lab/t20_43c_r2_act_permit.json")
ACCEPTANCE_PATH = Path(
    "configurations/robot_lab/t20_43c_r2_act_pre_run_acceptance.json"
)
MARKER_PATH = Path("configurations/robot_lab/t20_43c_r2_act_replacement_marker.json")
EQUIVALENCE_PATH = Path(
    "configurations/robot_lab/t20_43c_r2_act_equivalence_receipt.json"
)
RESULT_PATH = Path("configurations/robot_lab/t20_43c_r2_act_standard_result.json")
SCORECARD_PATH = Path("configurations/robot_lab/t20_43c_r2_act_scorecard.json")
RETENTION_PATH = Path("configurations/robot_lab/t20_43c_r2_act_retention_receipt.json")
FINAL_RECEIPT_PATH = Path("configurations/robot_lab/t20_43c_r2_act_final_receipt.json")
FAILURE_PATH = Path("configurations/robot_lab/t20_43c_r2_act_terminal_failure.json")

RUN_ROOT = Path("outputs/robot_lab/t20_43c_r2_act_replacement_run_001")
CHECKPOINT_ROOT = RUN_ROOT / "checkpoints"
ROLLOUT_ROOT = RUN_ROOT / "rollouts"
VIDEO_ROOT = RUN_ROOT / "mirrors"
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
PROGRESS_PATH = RUN_ROOT / "progress.json"

AUTHORITY_PATHS = (OWNER_PATH, REQUEST_PATH, DECISION_PATH, RUNTIME_PATH, PERMIT_PATH)
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
IMPLEMENTATION_SCOPED_PATHS = (
    Path("scenesmith/robot_lab/t20_43c_act_continuation.py"),
    Path("scenesmith/robot_lab/t20_43c_act_continuation_runner.py"),
    Path("scenesmith/robot_lab/t20_43c_manual_replacement.py"),
    Path("scripts/robot_lab/materialize_t20_43c_manual_replacement.py"),
    Path("scripts/robot_lab/write_t20_43c_manual_replacement_acceptance.py"),
    Path("scripts/robot_lab/run_t20_43c_manual_replacement.py"),
    Path("scripts/robot_lab/render_rollout_mirror_v2.py"),
    Path("tests/unit/test_t20_43c_manual_replacement.py"),
    OWNER_DIRECTION_PATH,
    Path("docs/briefs/229-t20-43c-manual-replacement.md"),
)

OWNER_SCHEMA = "scenesmith.t20_43c_r2_act_owner_authorization.v1"
RUNTIME_SCHEMA = "scenesmith.t20_43c_r2_act_runtime_preflight.v1"
PERMIT_SCHEMA = "scenesmith.t20_43c_r2_act_permit.v1"
ACCEPTANCE_SCHEMA = "scenesmith.t20_43c_r2_act_pre_run_acceptance.v1"
MARKER_SCHEMA = "scenesmith.t20_43c_r2_act_replacement_marker.v1"
EQUIVALENCE_SCHEMA = "scenesmith.t20_43c_r2_act_equivalence_receipt.v1"
RETENTION_SCHEMA = "scenesmith.t20_43c_r2_act_retention_receipt.v1"
FINAL_RECEIPT_SCHEMA = "scenesmith.t20_43c_r2_act_final_receipt.v1"
FAILURE_SCHEMA = "scenesmith.t20_43c_r2_act_terminal_failure.v1"


def load_prior_interruption(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Verify the consumed first continuation and its immutable partial tree."""

    root = Path(repo_root).resolve()
    marker = load_strict_json(root / PRIOR_MARKER_PATH)
    equivalence = load_strict_json(root / PRIOR_EQUIVALENCE_PATH)
    failure = load_strict_json(root / PRIOR_FAILURE_PATH)
    base_sources = base.load_continuation_sources(repo_root=root)
    permit = load_strict_json(root / base.PERMIT_PATH)
    base.verify_continuation_marker(marker, permit=permit)
    base.verify_equivalence_receipt(equivalence, marker=marker)
    partial_tree = base_runner._partial_run_tree(root / PRIOR_RUN_ROOT)
    base.verify_terminal_failure(failure, marker=marker, partial_run_tree=partial_tree)
    expected = {
        "marker": PRIOR_MARKER_IDENTITY,
        "equivalence": PRIOR_EQUIVALENCE_IDENTITY,
        "failure": PRIOR_FAILURE_IDENTITY,
        "partial_tree": PRIOR_PARTIAL_TREE_IDENTITY,
    }
    actual = {
        "marker": marker.get("identity_sha256"),
        "equivalence": equivalence.get("identity_sha256"),
        "failure": failure.get("identity_sha256"),
        "partial_tree": failure.get("partial_run_tree_identity_sha256"),
    }
    if actual != expected:
        raise ValueError("T20.43c-R2 prior interruption identity drifted")
    progress = failure.get("progress")
    if (
        not isinstance(progress, dict)
        or progress.get("optimizer_update_count") != PRIOR_OPTIMIZER_UPDATE_COUNT
        or progress.get("optimizer_training") is not True
        or failure.get("retry_authorized") is not False
    ):
        raise ValueError("T20.43c-R2 prior interruption progress drifted")
    return {
        "base_sources": base_sources,
        "marker": marker,
        "equivalence": equivalence,
        "failure": failure,
        "partial_tree": partial_tree,
    }


def build_owner_grant(
    *, required_source_commit: str, valid_from: str, valid_until: str
) -> dict[str, Any]:
    start, stop = _authority_window(valid_from, valid_until)
    return sign_payload(
        {
            "schema_version": OWNER_SCHEMA,
            "task_id": TASK_ID,
            "authorization_id": AUTHORIZATION_ID,
            "owner_instruction": OWNER_INSTRUCTION,
            "owner_direction_path": OWNER_DIRECTION_PATH.as_posix(),
            "required_source_commit": _commit(required_source_commit),
            "subject_id": base.DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": base.DEFAULT_AUTHORITY_SCOPE_ID,
            "prior_continuation_marker_identity_sha256": PRIOR_MARKER_IDENTITY,
            "prior_equivalence_identity_sha256": PRIOR_EQUIVALENCE_IDENTITY,
            "prior_terminal_failure_identity_sha256": PRIOR_FAILURE_IDENTITY,
            "prior_partial_tree_identity_sha256": PRIOR_PARTIAL_TREE_IDENTITY,
            "prior_optimizer_update_count": PRIOR_OPTIMIZER_UPDATE_COUNT,
            "source_attempt_identity_sha256": base.SOURCE_ATTEMPT_IDENTITY,
            "source_failure_identity_sha256": base.SOURCE_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": base.SOURCE_CHECKPOINT_IDENTITY,
            "source_trace_identity_sha256": base.SOURCE_TRACE_IDENTITY,
            "authorized_actions": [
                "construct_one_fresh_seeded_act_replacement",
                "prove_bit_exact_zero_update_equivalence",
                "create_one_empty_adamw_optimizer",
                "execute_unchanged_updates_1_through_10000",
                "run_fixed_dual_semantics_simulation_evaluations",
                "render_and_retain_signed_mirror_mp4",
            ],
            "authorized_attempt_count": 1,
            "replacement_ordinal": 2,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "minimum_completion_budget_seconds": MINIMUM_COMPLETION_BUDGET_SECONDS,
            "fresh_manual_replacement_authorized": True,
            "automatic_retry_authorized": False,
            "retry_after_this_attempt_authorized": False,
            "recipe_change_authorized": False,
            "simulation_only": True,
            "issued_at": start.isoformat(),
            "valid_from": start.isoformat(),
            "valid_until": stop.isoformat(),
            "maximum_authority_seconds": MAXIMUM_AUTHORITY_SECONDS,
            **_false_authority_fields(),
        }
    )


def verify_owner_grant(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.43c-R2 owner grant")
    expected = build_owner_grant(
        required_source_commit=payload.get("required_source_commit"),
        valid_from=payload.get("valid_from"),
        valid_until=payload.get("valid_until"),
    )
    if payload != expected:
        raise ValueError("T20.43c-R2 owner grant drifted")


def verify_source_renderer_smoke(payload: dict[str, Any]) -> None:
    """Verify the immutable T20.43c smoke without relabeling it as R2."""

    with _patched_attributes(
        base,
        {
            "TASK_ID": BASE_TASK_ID,
            "verify_renderer_smoke": BASE_VERIFY_RENDERER_SMOKE,
        },
    ):
        BASE_VERIFY_RENDERER_SMOKE(payload)


def build_central_authority(
    *, sources: dict[str, Any], smoke: dict[str, Any], owner: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    with _patched_base_contract():
        return base.build_central_authority(sources=sources, smoke=smoke, owner=owner)


def build_runtime_preflight(
    *,
    sources: dict[str, Any],
    smoke: dict[str, Any],
    owner: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    with _patched_base_contract():
        return base.build_runtime_preflight(
            sources=sources,
            smoke=smoke,
            owner=owner,
            request=request,
            decision=decision,
            snapshot=snapshot,
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
    with _patched_base_contract():
        base.verify_runtime_preflight(
            payload,
            sources=sources,
            smoke=smoke,
            owner=owner,
            request=request,
            decision=decision,
        )


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
            "prior_terminal_failure_identity_sha256": PRIOR_FAILURE_IDENTITY,
            "prior_partial_tree_identity_sha256": PRIOR_PARTIAL_TREE_IDENTITY,
            "source_attempt_identity_sha256": base.SOURCE_ATTEMPT_IDENTITY,
            "source_failure_identity_sha256": base.SOURCE_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": base.SOURCE_CHECKPOINT_IDENTITY,
            "source_trace_identity_sha256": base.SOURCE_TRACE_IDENTITY,
            "authorized_attempt_count": 1,
            "replacement_ordinal": 2,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "evaluation_action_steps": list(EVALUATION_ACTION_STEPS),
            "replacement_marker_path": MARKER_PATH.as_posix(),
            "marker_precedes_checkpoint_tensor_read_and_model_construction": True,
            "equivalence_required_before_update_1": True,
            "minimum_completion_budget_seconds": MINIMUM_COMPLETION_BUDGET_SECONDS,
            "fresh_manual_replacement_authorized": True,
            "automatic_retry_authorized": False,
            "retry_after_this_attempt_authorized": False,
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
    verify_signed_payload(payload, label="T20.43c-R2 permit")
    expected = build_permit(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )
    if payload != expected:
        raise ValueError("T20.43c-R2 permit drifted")


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
            "decision": "ACCEPT_ONE_T20_43C_MANUAL_REPLACEMENT",
            "authority_commit": _commit(authority_commit),
            "reviewer_decision_id": str(reviewer_decision_id),
            "reviewer_path": str(reviewer_path),
            "reviewer_file_sha256": _sha(reviewer_file_sha256),
            "permit_identity_sha256": permit["identity_sha256"],
            "prior_terminal_failure_identity_sha256": PRIOR_FAILURE_IDENTITY,
            "replacement_marker_exists": False,
            "checkpoint_tensor_read_or_model_action_executed": False,
            "fresh_manual_replacement_authorized": True,
            "retry_after_this_attempt_authorized": False,
            **_false_authority_fields(),
        }
    )


def verify_acceptance(payload: dict[str, Any], *, permit: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.43c-R2 acceptance")
    expected = build_acceptance(
        authority_commit=payload.get("authority_commit"),
        reviewer_decision_id=payload.get("reviewer_decision_id"),
        reviewer_path=payload.get("reviewer_path"),
        reviewer_file_sha256=payload.get("reviewer_file_sha256"),
        permit=permit,
    )
    if payload != expected:
        raise ValueError("T20.43c-R2 acceptance drifted")


def build_replacement_marker(
    *, permit: dict[str, Any], source_commit: str, started_at: str
) -> dict[str, Any]:
    started = _aware_time(started_at, label="replacement start")
    return sign_payload(
        {
            "schema_version": MARKER_SCHEMA,
            "task_id": TASK_ID,
            "permit_identity_sha256": permit["identity_sha256"],
            "attempt_ordinal": 1,
            "replacement_ordinal": 2,
            "source_commit": _commit(source_commit),
            "started_at": started.isoformat(),
            "prior_continuation_marker_identity_sha256": PRIOR_MARKER_IDENTITY,
            "prior_terminal_failure_identity_sha256": PRIOR_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": base.SOURCE_CHECKPOINT_IDENTITY,
            "created_before_checkpoint_tensor_read": True,
            "created_before_model_construction": True,
            "created_before_optimizer_creation": True,
            "permit_consumed": True,
            "fresh_manual_replacement": True,
            "retry_after_this_attempt_authorized": False,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            **_false_authority_fields(),
        }
    )


def verify_replacement_marker(
    payload: dict[str, Any], *, permit: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.43c-R2 marker")
    expected = build_replacement_marker(
        permit=permit,
        source_commit=payload.get("source_commit"),
        started_at=payload.get("started_at"),
    )
    if payload != expected:
        raise ValueError("T20.43c-R2 replacement marker drifted")


def build_equivalence_receipt(
    *, marker: dict[str, Any], **tensor_evidence: Any
) -> dict[str, Any]:
    with _patched_base_contract():
        original = base.build_equivalence_receipt(marker=marker, **tensor_evidence)
    payload = {
        key: value for key, value in original.items() if key != "identity_sha256"
    }
    payload.update(
        {
            "prior_terminal_failure_identity_sha256": PRIOR_FAILURE_IDENTITY,
            "fresh_manual_replacement": True,
            "retry_after_this_attempt_authorized": False,
        }
    )
    return sign_payload(payload)


def verify_equivalence_receipt(
    payload: dict[str, Any], *, marker: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.43c-R2 equivalence")
    evidence = {
        key: payload.get(key)
        for key in (
            "tensor_key_count",
            "tensor_element_count",
            "tensor_dtype_counts",
            "compared_tensor_sha256",
        )
    }
    if payload != build_equivalence_receipt(marker=marker, **evidence):
        raise ValueError("T20.43c-R2 equivalence receipt drifted")


def build_retention_receipt(
    *, result: dict[str, Any], run: dict[str, Any], local_output_trees: dict[str, Any]
) -> dict[str, Any]:
    if set(local_output_trees) != {"checkpoints", "rollouts", "mirrors"}:
        raise ValueError("T20.43c-R2 retention tree set drifted")
    for label, tree in local_output_trees.items():
        _validate_file_tree(tree, label=f"retention {label}")
    return sign_payload(
        {
            "schema_version": RETENTION_SCHEMA,
            "task_id": TASK_ID,
            "result_identity_sha256": result["identity_sha256"],
            "run_identity_sha256": run["identity_sha256"],
            "prior_terminal_failure_identity_sha256": PRIOR_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": base.SOURCE_CHECKPOINT_IDENTITY,
            "local_output_trees": local_output_trees,
            "prior_boundary_rewritten": False,
            "large_outputs_tracked_in_git": False,
            "compact_evidence_tracked_in_git": True,
            "fresh_manual_replacement": True,
            "retry_after_this_attempt_authorized": False,
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
            "prior_continuation_marker_identity_sha256": PRIOR_MARKER_IDENTITY,
            "prior_terminal_failure_identity_sha256": PRIOR_FAILURE_IDENTITY,
            "source_checkpoint_identity_sha256": base.SOURCE_CHECKPOINT_IDENTITY,
            "replacement_marker_identity_sha256": marker["identity_sha256"],
            "equivalence_receipt_identity_sha256": equivalence["identity_sha256"],
            "standard_result_identity_sha256": result["identity_sha256"],
            "retention_receipt_identity_sha256": retention["identity_sha256"],
            "optimizer_update_count": result["optimizer_update_count"],
            "gate_c_passed": result["gate_c_passed"],
            "first_gate_c_pass": result["first_gate_c_pass"],
            "prior_interruption_preserved": True,
            "zero_update_equivalence_proven": True,
            "fresh_manual_replacement": True,
            "retry_after_this_attempt_authorized": False,
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
    if (
        not isinstance(progress, dict)
        or not isinstance(progress.get("stage"), str)
        or not progress["stage"]
        or isinstance(progress.get("optimizer_update_count"), bool)
        or not isinstance(progress.get("optimizer_update_count"), int)
        or not 0 <= progress["optimizer_update_count"] <= MAXIMUM_OPTIMIZER_UPDATES
        or isinstance(progress.get("training_batches_consumed"), bool)
        or not isinstance(progress.get("training_batches_consumed"), int)
        or not 0 <= progress["training_batches_consumed"] <= MAXIMUM_OPTIMIZER_UPDATES
    ):
        raise ValueError("T20.43c-R2 terminal progress drifted")
    for key, value in progress.items():
        if key not in {
            "stage",
            "optimizer_update_count",
            "training_batches_consumed",
        } and not isinstance(value, bool):
            raise ValueError(f"T20.43c-R2 terminal progress field drifted: {key}")
    _validate_file_tree(partial_run_tree, label="terminal partial")
    if (
        not isinstance(error_type, str)
        or not error_type
        or not isinstance(error_message, str)
    ):
        raise ValueError("T20.43c-R2 terminal error fields drifted")
    return sign_payload(
        {
            "schema_version": FAILURE_SCHEMA,
            "task_id": TASK_ID,
            "replacement_marker_identity_sha256": marker["identity_sha256"],
            "prior_terminal_failure_identity_sha256": PRIOR_FAILURE_IDENTITY,
            "progress": progress,
            "partial_run_tree": partial_run_tree,
            "partial_run_tree_identity_sha256": hashlib.sha256(
                canonical_json_bytes(partial_run_tree)
            ).hexdigest(),
            "error_type": str(error_type),
            "error_message": error_message[:2000],
            "fresh_manual_replacement": True,
            "retry_after_this_attempt_authorized": False,
            **_false_authority_fields(),
        }
    )


def verify_terminal_failure(
    payload: dict[str, Any],
    *,
    marker: dict[str, Any],
    partial_run_tree: list[dict[str, Any]],
) -> None:
    verify_signed_payload(payload, label="T20.43c-R2 terminal failure")
    expected = build_terminal_failure(
        marker=marker,
        progress=payload.get("progress"),
        partial_run_tree=partial_run_tree,
        error_type=payload.get("error_type"),
        error_message=payload.get("error_message"),
    )
    if payload != expected:
        raise ValueError("T20.43c-R2 terminal failure drifted")


def collect_runtime_snapshot(
    *, required_source_commit: str, smoke: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    load_prior_interruption(repo_root=root)
    for relative in IMPLEMENTATION_SCOPED_PATHS:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(
                f"T20.43c-R2 implementation path is absent or aliased: {relative}"
            )
        tracked = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--error-unmatch",
                relative.as_posix(),
            ],
            capture_output=True,
            check=False,
        )
        if tracked.returncode != 0:
            raise ValueError(
                f"T20.43c-R2 implementation path is not tracked: {relative}"
            )
    with _patched_attributes(
        base_materialization,
        {
            "IMPLEMENTATION_SCOPED_PATHS": IMPLEMENTATION_SCOPED_PATHS,
            "OUTPUT_PATHS": OUTPUT_PATHS,
        },
    ):
        return base_materialization.collect_runtime_snapshot(
            required_source_commit=required_source_commit,
            smoke=smoke,
            repo_root=root,
        )


def build_materialization_bundle(
    *,
    sources: dict[str, Any],
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    smoke: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    owner = build_owner_grant(
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    request, decision = build_central_authority(
        sources=sources, smoke=smoke, owner=owner
    )
    runtime = build_runtime_preflight(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        snapshot=snapshot,
    )
    permit = build_permit(
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )
    return {
        OWNER_PATH.as_posix(): owner,
        REQUEST_PATH.as_posix(): request,
        DECISION_PATH.as_posix(): decision,
        RUNTIME_PATH.as_posix(): runtime,
        PERMIT_PATH.as_posix(): permit,
    }


def verify_materialization_bundle(
    bundle: dict[str, dict[str, Any]],
    *,
    sources: dict[str, Any],
    smoke: dict[str, Any],
) -> None:
    if list(bundle) != [path.as_posix() for path in AUTHORITY_PATHS]:
        raise ValueError("T20.43c-R2 authority bundle path/order drifted")
    owner = bundle[OWNER_PATH.as_posix()]
    request = bundle[REQUEST_PATH.as_posix()]
    decision = bundle[DECISION_PATH.as_posix()]
    runtime = bundle[RUNTIME_PATH.as_posix()]
    permit = bundle[PERMIT_PATH.as_posix()]
    expected_request, expected_decision = build_central_authority(
        sources=sources, smoke=smoke, owner=owner
    )
    if request != expected_request or decision != expected_decision:
        raise ValueError("T20.43c-R2 central authority drifted")
    verify_permit(
        permit,
        sources=sources,
        smoke=smoke,
        owner=owner,
        request=request,
        decision=decision,
        runtime=runtime,
    )


def materialize_live_authority(
    *,
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    prior = load_prior_interruption(repo_root=root)
    smoke = load_strict_json(root / base.SMOKE_RECEIPT_PATH)
    base._verify_live_renderer_smoke(smoke, repo_root=root)
    snapshot = collect_runtime_snapshot(
        required_source_commit=required_source_commit,
        smoke=smoke,
        repo_root=root,
    )
    bundle = build_materialization_bundle(
        sources=prior["base_sources"],
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
        smoke=smoke,
        snapshot=snapshot,
    )
    verify_materialization_bundle(bundle, sources=prior["base_sources"], smoke=smoke)
    _write_bundle_exclusively(bundle, repo_root=root)
    return bundle


def verify_materialized_authority(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    prior = load_prior_interruption(repo_root=root)
    smoke = load_strict_json(root / base.SMOKE_RECEIPT_PATH)
    base._verify_live_renderer_smoke(smoke, repo_root=root)
    bundle = {
        base.SMOKE_RECEIPT_PATH.as_posix(): smoke,
        **{path.as_posix(): load_strict_json(root / path) for path in AUTHORITY_PATHS},
    }
    authority_only = {key: bundle[key] for key in map(Path.as_posix, AUTHORITY_PATHS)}
    verify_materialization_bundle(
        authority_only, sources=prior["base_sources"], smoke=smoke
    )
    return bundle


def write_acceptance(
    *,
    authority_commit: str,
    reviewer_decision_id: str,
    reviewer_path: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    if os.path.lexists(root / ACCEPTANCE_PATH):
        raise FileExistsError("T20.43c-R2 acceptance already exists")
    bundle = verify_materialized_authority(repo_root=root)
    permit = bundle[PERMIT_PATH.as_posix()]
    reviewer = root / reviewer_path
    if not reviewer.is_file() or reviewer.is_symlink():
        raise ValueError("T20.43c-R2 reviewer evidence is absent or aliased")
    acceptance = build_acceptance(
        authority_commit=authority_commit,
        reviewer_decision_id=reviewer_decision_id,
        reviewer_path=reviewer_path,
        reviewer_file_sha256=_sha_file(reviewer),
        permit=permit,
    )
    verify_acceptance(acceptance, permit=permit)
    dump_canonical_json(root / ACCEPTANCE_PATH, acceptance)
    return acceptance


def run_authorized_manual_replacement(
    *, started_at: str, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    bundle = verify_materialized_authority(repo_root=root)
    owner = bundle[OWNER_PATH.as_posix()]
    _require_completion_budget(owner=owner, started_at=started_at)
    with _patched_runner_contract():
        try:
            return base_runner.run_authorized_continuation(
                started_at=started_at, repo_root=root
            )
        except KeyboardInterrupt as error:
            _record_keyboard_interruption(root=root, error=error)
            raise


def verify_all_manual_replacement_outputs(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    with _patched_runner_contract():
        return base_runner.verify_all_continuation_outputs(repo_root=repo_root)


def _record_keyboard_interruption(*, root: Path, error: KeyboardInterrupt) -> None:
    if (
        not (root / MARKER_PATH).is_file()
        or (root / FAILURE_PATH).exists()
        or (root / FINAL_RECEIPT_PATH).exists()
    ):
        return
    marker = load_strict_json(root / MARKER_PATH)
    progress = (
        load_strict_json(root / PROGRESS_PATH)
        if (root / PROGRESS_PATH).is_file()
        else {
            "stage": "unknown_after_marker",
            "optimizer_update_count": 0,
            "training_batches_consumed": 0,
            "equivalence_proven": False,
        }
    )
    partial_tree = base_runner._partial_run_tree(root / RUN_ROOT)
    failure = build_terminal_failure(
        marker=marker,
        progress=progress,
        partial_run_tree=partial_tree,
        error_type=type(error).__name__,
        error_message=str(error) or repr(error),
    )
    dump_canonical_json(root / FAILURE_PATH, failure)
    verify_terminal_failure(failure, marker=marker, partial_run_tree=partial_tree)


def _require_completion_budget(*, owner: dict[str, Any], started_at: str) -> None:
    started = _aware_time(started_at, label="replacement start")
    valid_from = _aware_time(owner.get("valid_from"), label="authority valid_from")
    valid_until = _aware_time(owner.get("valid_until"), label="authority valid_until")
    if not valid_from <= started <= valid_until:
        raise ValueError("T20.43c-R2 start is outside authority window")
    if (valid_until - started).total_seconds() < MINIMUM_COMPLETION_BUDGET_SECONDS:
        raise ValueError("T20.43c-R2 completion budget is insufficient before marker")


@contextlib.contextmanager
def _patched_base_contract() -> Iterator[None]:
    with _patched_attributes(
        base,
        {
            "TASK_ID": TASK_ID,
            "OWNER_PATH": OWNER_PATH,
            "REQUEST_PATH": REQUEST_PATH,
            "DECISION_PATH": DECISION_PATH,
            "RUNTIME_PATH": RUNTIME_PATH,
            "PERMIT_PATH": PERMIT_PATH,
            "ACCEPTANCE_PATH": ACCEPTANCE_PATH,
            "MARKER_PATH": MARKER_PATH,
            "EQUIVALENCE_PATH": EQUIVALENCE_PATH,
            "RESULT_PATH": RESULT_PATH,
            "SCORECARD_PATH": SCORECARD_PATH,
            "RETENTION_PATH": RETENTION_PATH,
            "FINAL_RECEIPT_PATH": FINAL_RECEIPT_PATH,
            "FAILURE_PATH": FAILURE_PATH,
            "RUN_ROOT": RUN_ROOT,
            "CHECKPOINT_ROOT": CHECKPOINT_ROOT,
            "ROLLOUT_ROOT": ROLLOUT_ROOT,
            "VIDEO_ROOT": VIDEO_ROOT,
            "RUN_SUMMARY_PATH": RUN_SUMMARY_PATH,
            "PROGRESS_PATH": PROGRESS_PATH,
            "OUTPUT_PATHS": OUTPUT_PATHS,
            "OWNER_SCHEMA": OWNER_SCHEMA,
            "RUNTIME_SCHEMA": RUNTIME_SCHEMA,
            "PERMIT_SCHEMA": PERMIT_SCHEMA,
            "ACCEPTANCE_SCHEMA": ACCEPTANCE_SCHEMA,
            "MARKER_SCHEMA": MARKER_SCHEMA,
            "EQUIVALENCE_SCHEMA": EQUIVALENCE_SCHEMA,
            "RETENTION_SCHEMA": RETENTION_SCHEMA,
            "FINAL_RECEIPT_SCHEMA": FINAL_RECEIPT_SCHEMA,
            "FAILURE_SCHEMA": FAILURE_SCHEMA,
            "verify_renderer_smoke": verify_source_renderer_smoke,
            "verify_owner_grant": verify_owner_grant,
            "build_permit": build_permit,
            "verify_permit": verify_permit,
        },
    ):
        yield


@contextlib.contextmanager
def _patched_runner_contract() -> Iterator[None]:
    replacements = {
        "OWNER_PATH": OWNER_PATH,
        "PERMIT_PATH": PERMIT_PATH,
        "ACCEPTANCE_PATH": ACCEPTANCE_PATH,
        "MARKER_PATH": MARKER_PATH,
        "EQUIVALENCE_PATH": EQUIVALENCE_PATH,
        "RESULT_PATH": RESULT_PATH,
        "SCORECARD_PATH": SCORECARD_PATH,
        "RETENTION_PATH": RETENTION_PATH,
        "FINAL_RECEIPT_PATH": FINAL_RECEIPT_PATH,
        "FAILURE_PATH": FAILURE_PATH,
        "RUN_ROOT": RUN_ROOT,
        "CHECKPOINT_ROOT": CHECKPOINT_ROOT,
        "ROLLOUT_ROOT": ROLLOUT_ROOT,
        "VIDEO_ROOT": VIDEO_ROOT,
        "RUN_SUMMARY_PATH": RUN_SUMMARY_PATH,
        "PROGRESS_PATH": PROGRESS_PATH,
        "IMPLEMENTATION_SCOPED_PATHS": IMPLEMENTATION_SCOPED_PATHS,
        "build_continuation_marker": build_replacement_marker,
        "verify_continuation_marker": verify_replacement_marker,
        "build_equivalence_receipt": build_equivalence_receipt,
        "verify_equivalence_receipt": verify_equivalence_receipt,
        "build_retention_receipt": build_retention_receipt,
        "build_final_receipt": build_final_receipt,
        "build_terminal_failure": build_terminal_failure,
        "verify_terminal_failure": verify_terminal_failure,
        "verify_acceptance": verify_acceptance,
        "verify_materialized_authority": verify_materialized_authority,
    }
    with _patched_attributes(base_runner, replacements):
        yield


@contextlib.contextmanager
def _patched_attributes(module: Any, replacements: dict[str, Any]) -> Iterator[None]:
    previous = {name: getattr(module, name) for name in replacements}
    try:
        for name, value in replacements.items():
            setattr(module, name, value)
        yield
    finally:
        for name, value in previous.items():
            setattr(module, name, value)


def _write_bundle_exclusively(
    bundle: dict[str, dict[str, Any]], *, repo_root: Path
) -> None:
    for relative in AUTHORITY_PATHS:
        target = repo_root / relative
        if os.path.lexists(target) or _path_or_parent_is_symlink(repo_root, relative):
            raise FileExistsError(f"T20.43c-R2 authority target is unsafe: {relative}")
    for relative in AUTHORITY_PATHS:
        target = repo_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = (
            json.dumps(
                bundle[relative.as_posix()], indent=2, sort_keys=True, allow_nan=False
            )
            + "\n"
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(target, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())


def _authority_window(valid_from: str, valid_until: str) -> tuple[datetime, datetime]:
    start = _aware_time(valid_from, label="authority valid_from")
    stop = _aware_time(valid_until, label="authority valid_until")
    seconds = (stop - start).total_seconds()
    if seconds <= 0 or seconds > MAXIMUM_AUTHORITY_SECONDS:
        raise ValueError("T20.43c-R2 authority window is invalid")
    return start, stop


def _aware_time(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"T20.43c-R2 {label} must be a timestamp")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"T20.43c-R2 {label} must be timezone-aware")
    return parsed


def _false_authority_fields() -> dict[str, bool]:
    return {field: False for field in base.FALSE_AUTHORITY_FIELDS}


def _sha(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("T20.43c-R2 expected a SHA-256 digest")
    int(value, 16)
    return value


def _commit(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise ValueError("T20.43c-R2 expected a full commit SHA")
    int(value, 16)
    return value


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_or_parent_is_symlink(root: Path, relative: Path) -> bool:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False


def _validate_file_tree(value: Any, *, label: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"T20.43c-R2 {label} tree must be a list")
    paths: list[str] = []
    for row in value:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "sha256", "size_bytes"}
            or not isinstance(row["path"], str)
            or not row["path"]
            or Path(row["path"]).is_absolute()
            or ".." in Path(row["path"]).parts
            or isinstance(row["size_bytes"], bool)
            or not isinstance(row["size_bytes"], int)
            or row["size_bytes"] < 0
        ):
            raise ValueError(f"T20.43c-R2 {label} tree row drifted")
        _sha(row["sha256"])
        paths.append(row["path"])
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError(f"T20.43c-R2 {label} tree path order drifted")


__all__ = [
    name
    for name in globals()
    if name.isupper()
    or name.startswith(("build_", "verify_", "load_", "materialize_", "run_", "write_"))
]
