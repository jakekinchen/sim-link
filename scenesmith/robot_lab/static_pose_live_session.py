"""Fail-closed production orchestration for one static-pose live candidate."""

from __future__ import annotations

import copy
import hashlib
import os

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.hardware_execution_profile import (
    verify_hardware_execution_profile_evidence,
)
from scenesmith.robot_lab.static_pose_live_candidate import (
    run_static_pose_live_candidate,
    verify_static_pose_live_candidate_contract,
    verify_static_pose_live_candidate_result_from_embedded_authority,
)
from scenesmith.robot_lab.static_pose_live_execution import (
    build_private_static_pose_candidate_failure_evidence,
    build_private_static_pose_candidate_success_evidence,
    make_pinned_static_pose_camera_factory,
    make_pinned_static_pose_transport_factory,
    verify_private_static_pose_candidate_evidence_reference,
    verify_private_static_pose_candidate_evidence_destination,
    verify_private_static_pose_candidate_failure_evidence,
    verify_private_static_pose_candidate_success_evidence,
    write_private_static_pose_candidate_evidence,
)


STATIC_POSE_LIVE_SESSION_RECEIPT_SCHEMA_VERSION = (
    "scenesmith.static_pose_live_session_receipt.v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]

_AUTHORITY_NOT_GRANTED = [
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]


class StaticPoseLiveSessionRejected(RuntimeError):
    """A started candidate session that durably recorded a rejected outcome."""

    def __init__(
        self,
        *,
        private_evidence: dict[str, Any],
        private_reference: dict[str, Any],
    ) -> None:
        super().__init__("Static-pose live candidate session was rejected")
        self.private_evidence = copy.deepcopy(private_evidence)
        self.private_reference = copy.deepcopy(private_reference)


def run_pinned_static_pose_live_session(
    candidate_contract: dict[str, Any],
    *,
    hardware_execution_profile: dict[str, Any],
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    private_root: Path,
    pre_open_holder_snapshot: dict[str, Any],
    post_close_holder_snapshot_factory: Callable[[], dict[str, Any]],
    monotonic_ns: Callable[[], int],
    wall_time: Callable[[], str],
) -> dict[str, Any]:
    """Run one candidate and return it only after durable private success proof."""

    preflight_at = _normalized_time(wall_time(), label="live session preflight_at")
    thread_id = require_nonblank(
        os.environ.get("CODEX_THREAD_ID"),
        label="active Codex live-session thread ID",
    )

    # This entire preflight precedes the started-session boundary: a rejection
    # here creates no private session path and cannot invoke a hardware factory.
    verify_hardware_execution_profile_evidence(
        hardware_execution_profile,
        repo_root=REPO_ROOT,
        now=preflight_at,
        expected_thread_id=thread_id,
    )
    verify_static_pose_live_candidate_contract(
        candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=preflight_at,
    )
    verify_private_static_pose_candidate_evidence_destination(
        private_root=private_root,
        session_id=candidate_contract["session_id"],
    )
    transport_factory = make_pinned_static_pose_transport_factory(
        candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=preflight_at,
        repo_root=REPO_ROOT,
        monotonic_ns=monotonic_ns,
    )
    camera_factory = make_pinned_static_pose_camera_factory(
        candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=preflight_at,
        monotonic_ns=monotonic_ns,
    )

    started_at = _normalized_time(wall_time(), label="live session started_at")
    if _parse_time(started_at, label="live session started_at") < _parse_time(
        preflight_at,
        label="live session preflight_at",
    ):
        raise ValueError("Static-pose live session clock regressed during preflight")

    # The session is now started. Every outcome below must either persist and
    # reverify exactly one artifact or raise while withholding the result.
    try:
        candidate_result = run_static_pose_live_candidate(
            candidate_contract,
            hardware_execution_profile=hardware_execution_profile,
            project_state=project_state,
            static_pose_contract=static_pose_contract,
            calibration_path=calibration_path,
            calibration_profile_path=calibration_profile_path,
            manifest_path=manifest_path,
            now=started_at,
            transport_factory=transport_factory,
            camera_factory=camera_factory,
            pre_open_holder_snapshot=pre_open_holder_snapshot,
            post_close_holder_snapshot_factory=(
                post_close_holder_snapshot_factory
            ),
            monotonic_ns=monotonic_ns,
        )
    except BaseException as primary_error:
        try:
            failed_at = _normalized_time(wall_time(), label="live session failed_at")
        except BaseException as time_error:
            primary_error = BaseExceptionGroup(
                "Static-pose live session failed and failure timing failed",
                [primary_error, time_error],
            )
            failed_at = started_at
        if _parse_time(failed_at, label="live session failed_at") < _parse_time(
            started_at,
            label="live session started_at",
        ):
            primary_error = BaseExceptionGroup(
                "Static-pose live session failed with wall-clock regression",
                [
                    primary_error,
                    ValueError("Static-pose live session failure clock regressed"),
                ],
            )
            failed_at = started_at
        try:
            private_failure, private_reference = _persist_private_rejection(
                candidate_contract=candidate_contract,
                hardware_execution_profile=hardware_execution_profile,
                primary_error=primary_error,
                failed_at=failed_at,
                thread_id=thread_id,
                private_root=private_root,
            )
        except BaseException as evidence_error:
            raise BaseExceptionGroup(
                "Static-pose live session and private failure persistence failed",
                [primary_error, evidence_error],
            )
        raise StaticPoseLiveSessionRejected(
            private_evidence=private_failure,
            private_reference=private_reference,
        ) from primary_error

    completion_error: BaseException | None = None
    try:
        completed_at = _normalized_time(
            wall_time(),
            label="live session completed_at",
        )
    except BaseException as time_error:
        completion_error = time_error
        completed_at = started_at
    if completion_error is None and _parse_time(
        completed_at,
        label="live session completed_at",
    ) < _parse_time(started_at, label="live session started_at"):
        completion_error = ValueError(
            "Static-pose live session completion clock regressed"
        )
        completed_at = started_at
    if completion_error is not None:
        try:
            private_failure, private_reference = _persist_private_rejection(
                candidate_contract=candidate_contract,
                hardware_execution_profile=hardware_execution_profile,
                primary_error=completion_error,
                failed_at=started_at,
                thread_id=thread_id,
                private_root=private_root,
            )
        except BaseException as evidence_error:
            raise BaseExceptionGroup(
                "Static-pose completion clock and private failure persistence failed",
                [completion_error, evidence_error],
            )
        raise StaticPoseLiveSessionRejected(
            private_evidence=private_failure,
            private_reference=private_reference,
        ) from completion_error
    try:
        private_success = build_private_static_pose_candidate_success_evidence(
            candidate_contract=candidate_contract,
            hardware_execution_profile=hardware_execution_profile,
            candidate_result=candidate_result,
            completed_at=completed_at,
        )
        verify_private_static_pose_candidate_success_evidence(
            private_success,
            repo_root=REPO_ROOT,
            now=completed_at,
            expected_thread_id=thread_id,
        )
        private_reference = write_private_static_pose_candidate_evidence(
            private_root=private_root,
            evidence=private_success,
        )
        verify_private_static_pose_candidate_evidence_reference(
            private_reference,
            private_root=private_root,
            evidence=private_success,
        )
        receipt = build_static_pose_live_session_receipt(
            candidate_contract=candidate_contract,
            hardware_execution_profile=hardware_execution_profile,
            candidate_result=candidate_result,
            private_evidence=private_success,
            private_reference=private_reference,
            private_root=private_root,
            preflight_at=preflight_at,
            started_at=started_at,
            completed_at=completed_at,
        )
        verify_static_pose_live_session_receipt(
            receipt,
            candidate_contract=candidate_contract,
            hardware_execution_profile=hardware_execution_profile,
            candidate_result=candidate_result,
            private_evidence=private_success,
            private_reference=private_reference,
            private_root=private_root,
            static_pose_contract=static_pose_contract,
            calibration_path=calibration_path,
            calibration_profile_path=calibration_profile_path,
            manifest_path=manifest_path,
        )
    except BaseException as evidence_error:
        withholding_error = RuntimeError(
            "Static-pose candidate result withheld because private success "
            "persistence or receipt verification failed"
        )
        raise BaseExceptionGroup(
            "Static-pose candidate succeeded but its durable boundary failed",
            [withholding_error, evidence_error],
        )

    return {
        "candidate_result": copy.deepcopy(candidate_result),
        "private_evidence": copy.deepcopy(private_success),
        "private_reference": copy.deepcopy(private_reference),
        "session_receipt": receipt,
    }


def build_static_pose_live_session_receipt(
    *,
    candidate_contract: dict[str, Any],
    hardware_execution_profile: dict[str, Any],
    candidate_result: dict[str, Any],
    private_evidence: dict[str, Any],
    private_reference: dict[str, Any],
    private_root: Path,
    preflight_at: str,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    """Build a candidate-only receipt after the private artifact is available."""

    preflight = _parse_time(preflight_at, label="session receipt preflight_at")
    started = _parse_time(started_at, label="session receipt started_at")
    completed = _parse_time(completed_at, label="session receipt completed_at")
    if started < preflight or completed < started:
        raise ValueError("Static-pose live session receipt interval is invalid")
    for label, payload in (
        ("candidate contract", candidate_contract),
        ("hardware execution profile", hardware_execution_profile),
        ("candidate result", candidate_result),
        ("private success evidence", private_evidence),
    ):
        verify_signed_payload(payload, label=label)
    payload = {
        "schema_version": STATIC_POSE_LIVE_SESSION_RECEIPT_SCHEMA_VERSION,
        "receipt_name": "pi05_static_pose_live_candidate_session",
        "qualification_scope": "local_static_pose_live_candidate_session",
        "evidence_mode": "private_candidate_session_receipt",
        "status": "candidate_observed",
        "session_id": candidate_contract["session_id"],
        "candidate_only": True,
        "preflight_at": preflight.isoformat(),
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "candidate_contract_identity_sha256": candidate_contract[
            "identity_sha256"
        ],
        "hardware_execution_profile_identity_sha256": (
            hardware_execution_profile["identity_sha256"]
        ),
        "candidate_result_identity_sha256": candidate_result["identity_sha256"],
        "private_evidence_identity_sha256": private_evidence["identity_sha256"],
        "private_reference": copy.deepcopy(private_reference),
        "private_reference_sha256": hashlib.sha256(
            canonical_json_bytes(private_reference)
        ).hexdigest(),
        "private_root_identity_sha256": _private_root_identity(private_root),
        "local_capabilities": ["private_static_pose_live_session_receipt_valid"],
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "hardware_opened": True,
        "physical_follower_commanded": False,
        "policy_inference_run": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
        "tracked_redacted_manifest_written": False,
    }
    return sign_payload(payload)


def verify_static_pose_live_session_receipt(
    receipt: dict[str, Any],
    *,
    candidate_contract: dict[str, Any],
    hardware_execution_profile: dict[str, Any],
    candidate_result: dict[str, Any],
    private_evidence: dict[str, Any],
    private_reference: dict[str, Any],
    private_root: Path,
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
) -> None:
    """Independently verify every retained source and receipt authority field."""

    allowed_fields = {
        "schema_version",
        "receipt_name",
        "qualification_scope",
        "evidence_mode",
        "status",
        "session_id",
        "candidate_only",
        "preflight_at",
        "started_at",
        "completed_at",
        "candidate_contract_identity_sha256",
        "hardware_execution_profile_identity_sha256",
        "candidate_result_identity_sha256",
        "private_evidence_identity_sha256",
        "private_reference",
        "private_reference_sha256",
        "private_root_identity_sha256",
        "local_capabilities",
        "proof_labels",
        "authority_not_granted",
        "hardware_opened",
        "physical_follower_commanded",
        "policy_inference_run",
        "motion_authority_granted",
        "training_authority_granted",
        "tracked_redacted_manifest_written",
        "identity_sha256",
    }
    if not isinstance(receipt, dict) or set(receipt) != allowed_fields:
        raise ValueError("Static-pose live session receipt fields are malformed")
    verify_signed_payload(receipt, label="Static-pose live session receipt")
    for label, payload in (
        ("candidate contract", candidate_contract),
        ("hardware execution profile", hardware_execution_profile),
        ("candidate result", candidate_result),
        ("private success evidence", private_evidence),
    ):
        verify_signed_payload(payload, label=label)
    preflight = _parse_time(receipt.get("preflight_at"), label="receipt preflight_at")
    started = _parse_time(receipt.get("started_at"), label="receipt started_at")
    completed = _parse_time(receipt.get("completed_at"), label="receipt completed_at")
    if started < preflight or completed < started:
        raise ValueError("Static-pose live session receipt interval drifted")
    verify_hardware_execution_profile_evidence(
        hardware_execution_profile,
        repo_root=REPO_ROOT,
        now=completed.isoformat(),
        expected_thread_id=hardware_execution_profile.get("thread_id"),
        require_active_runtime=False,
    )
    verify_static_pose_live_candidate_result_from_embedded_authority(
        candidate_result,
        candidate_contract=candidate_contract,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
    )
    verify_private_static_pose_candidate_success_evidence(
        private_evidence,
        repo_root=REPO_ROOT,
        now=completed.isoformat(),
        expected_thread_id=hardware_execution_profile["thread_id"],
    )
    verify_private_static_pose_candidate_evidence_reference(
        private_reference,
        private_root=private_root,
        evidence=private_evidence,
    )
    if (
        receipt.get("schema_version")
        != STATIC_POSE_LIVE_SESSION_RECEIPT_SCHEMA_VERSION
        or receipt.get("receipt_name")
        != "pi05_static_pose_live_candidate_session"
        or receipt.get("qualification_scope")
        != "local_static_pose_live_candidate_session"
        or receipt.get("evidence_mode") != "private_candidate_session_receipt"
        or receipt.get("status") != "candidate_observed"
        or receipt.get("session_id") != candidate_contract.get("session_id")
        or receipt.get("candidate_only") is not True
        or receipt.get("candidate_contract_identity_sha256")
        != candidate_contract.get("identity_sha256")
        or receipt.get("hardware_execution_profile_identity_sha256")
        != hardware_execution_profile.get("identity_sha256")
        or receipt.get("candidate_result_identity_sha256")
        != candidate_result.get("identity_sha256")
        or receipt.get("private_evidence_identity_sha256")
        != private_evidence.get("identity_sha256")
        or receipt.get("private_reference") != private_reference
        or receipt.get("private_reference_sha256")
        != hashlib.sha256(canonical_json_bytes(private_reference)).hexdigest()
        or receipt.get("private_root_identity_sha256")
        != _private_root_identity(private_root)
        or candidate_result.get("candidate_contract_identity_sha256")
        != candidate_contract.get("identity_sha256")
        or candidate_result.get("verified_at") != receipt.get("started_at")
        or candidate_result.get("hardware_execution_profile_identity_sha256")
        != hardware_execution_profile.get("identity_sha256")
        or private_evidence.get("candidate_contract_identity_sha256")
        != candidate_contract.get("identity_sha256")
        or private_evidence.get("session_id")
        != candidate_contract.get("session_id")
        or private_evidence.get("hardware_execution_profile_identity_sha256")
        != hardware_execution_profile.get("identity_sha256")
        or private_evidence.get("candidate_result_identity_sha256")
        != candidate_result.get("identity_sha256")
        or private_evidence.get("completed_at") != receipt.get("completed_at")
        or private_evidence.get("status") != "candidate_observed"
        or receipt.get("local_capabilities")
        != ["private_static_pose_live_session_receipt_valid"]
        or receipt.get("proof_labels") != []
        or receipt.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
        or receipt.get("hardware_opened") is not True
        or receipt.get("physical_follower_commanded") is not False
        or receipt.get("policy_inference_run") is not False
        or receipt.get("motion_authority_granted") is not False
        or receipt.get("training_authority_granted") is not False
        or receipt.get("tracked_redacted_manifest_written") is not False
    ):
        raise ValueError("Static-pose live session receipt source or authority drifted")


def _persist_private_rejection(
    *,
    candidate_contract: dict[str, Any],
    hardware_execution_profile: dict[str, Any],
    primary_error: BaseException,
    failed_at: str,
    thread_id: str,
    private_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    private_failure = build_private_static_pose_candidate_failure_evidence(
        candidate_contract=candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        error=primary_error,
        failed_at=failed_at,
    )
    verify_private_static_pose_candidate_failure_evidence(
        private_failure,
        repo_root=REPO_ROOT,
        now=failed_at,
        expected_thread_id=thread_id,
    )
    private_reference = write_private_static_pose_candidate_evidence(
        private_root=private_root,
        evidence=private_failure,
    )
    verify_private_static_pose_candidate_evidence_reference(
        private_reference,
        private_root=private_root,
        evidence=private_failure,
    )
    return private_failure, private_reference


def _private_root_identity(path: Path) -> str:
    root = Path(path)
    if root.is_absolute():
        normalized = root.resolve().as_posix()
    else:
        normalized = root.as_posix()
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def _normalized_time(value: Any, *, label: str) -> str:
    return _parse_time(value, label=label).isoformat()


def _parse_time(value: Any, *, label: str) -> datetime:
    text = require_nonblank(value, label=label)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a UTC offset")
    return parsed
