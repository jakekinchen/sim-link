"""Redacted tracked-review boundary for a successful live candidate session."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.live_readonly_observation import (
    require_no_serial_identity_holders,
    verify_serial_identity_holder_stability,
)
from scenesmith.robot_lab.hardware_execution_profile import (
    HARDWARE_APPROVAL_POLICY,
    HARDWARE_SANDBOX_MODE,
)
from scenesmith.robot_lab.static_pose_bracket import EXPECTED_OPERATION_COUNTS
from scenesmith.robot_lab.static_pose_live_session import (
    STATIC_POSE_LIVE_SESSION_RECEIPT_SCHEMA_VERSION,
    verify_static_pose_live_session_receipt,
)


REDACTED_STATIC_POSE_LIVE_SESSION_REVIEW_SCHEMA_VERSION = (
    "scenesmith.static_pose_live_session_review_manifest.v1"
)

_LIVE_CONTRACT_SCHEMA_VERSION = "scenesmith.static_pose_live_candidate_contract.v1"
_LIVE_RESULT_SCHEMA_VERSION = "scenesmith.static_pose_live_candidate_result.v2"
_HARDWARE_PROFILE_SCHEMA_VERSION = (
    "scenesmith.hardware_execution_profile_evidence.v1"
)
_PRIVATE_SUCCESS_SCHEMA_VERSION = (
    "scenesmith.static_pose_live_candidate_private_success.v1"
)
_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_SOURCE_ARTIFACT_KEYS = {
    "accepted_manifest",
    "calibration_profile",
    "static_pose_contract",
}
_SOURCE_AUTHORITY_NOT_GRANTED = [
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]
_AUTHORITY_NOT_GRANTED = [
    "live_candidate_session_accepted",
    *_SOURCE_AUTHORITY_NOT_GRANTED,
]
_FRAME_FIELDS = {
    "frame_index",
    "frame_sha256",
    "width",
    "height",
    "channels",
    "encoding",
}
_INPUT_MODE_FIELDS = {
    "pixel_format",
    "width",
    "height",
    "framerate_fps",
}
_SAFE_TIMING_FIELDS = {
    "bracket_duration_ns",
    "camera_receive_duration_ns",
    "maximum_bracket_duration_ns",
}


def build_redacted_static_pose_live_session_review_manifest(
    *,
    session_receipt: dict[str, Any],
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
) -> dict[str, Any]:
    """Build a deterministic, label-free view of fully verified private success."""

    _verify_review_sources(
        session_receipt=session_receipt,
        candidate_contract=candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        candidate_result=candidate_result,
        private_evidence=private_evidence,
        private_reference=private_reference,
        private_root=private_root,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
    )
    return _build_redacted_manifest(
        session_receipt=session_receipt,
        candidate_contract=candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        candidate_result=candidate_result,
        private_evidence=private_evidence,
        private_reference=private_reference,
    )


def verify_redacted_static_pose_live_session_review_manifest(
    payload: dict[str, Any],
    *,
    session_receipt: dict[str, Any],
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
    """Rebuild the redacted view from private sources and reject any drift."""

    if not isinstance(payload, dict):
        raise ValueError("Redacted live-session review manifest must be an object")
    if (
        payload.get("schema_version")
        != REDACTED_STATIC_POSE_LIVE_SESSION_REVIEW_SCHEMA_VERSION
    ):
        raise ValueError("Redacted live-session review manifest schema is unsupported")
    verify_signed_payload(payload, label="Redacted live-session review manifest")
    _verify_review_sources(
        session_receipt=session_receipt,
        candidate_contract=candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        candidate_result=candidate_result,
        private_evidence=private_evidence,
        private_reference=private_reference,
        private_root=private_root,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
    )
    expected = _build_redacted_manifest(
        session_receipt=session_receipt,
        candidate_contract=candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        candidate_result=candidate_result,
        private_evidence=private_evidence,
        private_reference=private_reference,
    )
    if payload != expected:
        raise ValueError(
            "Redacted live-session review manifest drifted from private sources"
        )


def write_redacted_static_pose_live_session_review_manifest(
    payload: dict[str, Any],
    *,
    output_path: Path,
    repo_root: Path,
    session_receipt: dict[str, Any],
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
) -> dict[str, Any]:
    """Exclusively write one fully verified manifest to its exact tracked path."""

    verify_redacted_static_pose_live_session_review_manifest(
        payload,
        session_receipt=session_receipt,
        candidate_contract=candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        candidate_result=candidate_result,
        private_evidence=private_evidence,
        private_reference=private_reference,
        private_root=private_root,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
    )
    root = _validated_repository_root(repo_root)
    session_id = _validated_session_id(payload.get("session_id"))
    configuration_root = root / "configurations" / "robot_lab"
    if (
        not configuration_root.is_dir()
        or _has_symlink_between(root, configuration_root)
    ):
        raise ValueError("Tracked live-session review directory is missing or aliased")
    expected = configuration_root / (
        f"pi05_static_pose_live_session_{session_id}.redacted.json"
    )
    unresolved = Path(output_path)
    candidate = unresolved if unresolved.is_absolute() else root / unresolved
    candidate = Path(os.path.abspath(candidate))
    if candidate != expected:
        raise ValueError("Tracked live-session review path is outside its exact scope")
    if _has_symlink_between(root, candidate):
        raise ValueError("Tracked live-session review path contains a symlink alias")
    if candidate.exists() or candidate.is_symlink():
        raise ValueError("Tracked live-session review path must be new and immutable")

    encoded = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    _write_exclusive_bytes(candidate, encoded)
    try:
        observed_bytes = candidate.read_bytes()
        observed = load_strict_json(candidate)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Tracked live-session review artifact reread failed") from exc
    if observed_bytes != encoded or observed != payload:
        raise ValueError(
            "Tracked live-session review artifact content drifted on reread"
        )
    return {
        "logical_path": candidate.relative_to(root).as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(observed_bytes).hexdigest(),
        "size_bytes": len(observed_bytes),
    }


def _verify_review_sources(
    *,
    session_receipt: dict[str, Any],
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
    for label, value in (
        ("session receipt", session_receipt),
        ("candidate contract", candidate_contract),
        ("hardware execution profile", hardware_execution_profile),
        ("candidate result", candidate_result),
        ("private success evidence", private_evidence),
        ("static pose contract", static_pose_contract),
    ):
        if not isinstance(value, dict):
            raise ValueError(f"Redacted review {label} must be an object")
        verify_signed_payload(value, label=f"Redacted review {label}")

    session_id = _validated_session_id(candidate_contract.get("session_id"))
    if (
        session_receipt.get("schema_version")
        != STATIC_POSE_LIVE_SESSION_RECEIPT_SCHEMA_VERSION
        or session_receipt.get("receipt_name")
        != "pi05_static_pose_live_candidate_session"
        or session_receipt.get("qualification_scope")
        != "local_static_pose_live_candidate_session"
        or session_receipt.get("evidence_mode")
        != "private_candidate_session_receipt"
        or session_receipt.get("status") != "candidate_observed"
        or session_receipt.get("candidate_only") is not True
        or session_receipt.get("session_id") != session_id
        or session_receipt.get("proof_labels") != []
        or session_receipt.get("local_capabilities")
        != ["private_static_pose_live_session_receipt_valid"]
        or session_receipt.get("authority_not_granted")
        != _SOURCE_AUTHORITY_NOT_GRANTED
        or session_receipt.get("hardware_opened") is not True
        or session_receipt.get("physical_follower_commanded") is not False
        or session_receipt.get("policy_inference_run") is not False
        or session_receipt.get("motion_authority_granted") is not False
        or session_receipt.get("training_authority_granted") is not False
        or session_receipt.get("tracked_redacted_manifest_written") is not False
    ):
        raise ValueError("Redacted review session receipt classification drifted")
    if (
        candidate_contract.get("schema_version") != _LIVE_CONTRACT_SCHEMA_VERSION
        or candidate_contract.get("contract_name")
        != "pi05_static_pose_live_candidate"
        or candidate_contract.get("qualification_scope")
        != "local_static_pose_live_candidate_contract"
        or candidate_contract.get("evidence_mode")
        != "private_source_bound_live_candidate_contract"
        or candidate_contract.get("execution_class") != "live_candidate"
        or candidate_contract.get("hardware_access_authorized") is not True
        or candidate_contract.get("local_capabilities")
        != ["static_pose_live_candidate_contract_valid"]
        or candidate_contract.get("proof_labels") != []
        or candidate_contract.get("authority_not_granted")
        != _SOURCE_AUTHORITY_NOT_GRANTED
        or candidate_contract.get("hardware_accessed") is not False
        or candidate_contract.get("physical_follower_commanded") is not False
        or candidate_contract.get("motion_authority_granted") is not False
        or candidate_contract.get("training_authority_granted") is not False
        or candidate_contract.get("private_output_required") is not True
    ):
        raise ValueError("Redacted review candidate contract classification drifted")
    if (
        hardware_execution_profile.get("schema_version")
        != _HARDWARE_PROFILE_SCHEMA_VERSION
        or hardware_execution_profile.get("approval_policy")
        != HARDWARE_APPROVAL_POLICY
        or hardware_execution_profile.get("sandbox_mode") != HARDWARE_SANDBOX_MODE
        or hardware_execution_profile.get("local_capabilities")
        != ["hardware_supervised_runtime_profile_observed"]
        or hardware_execution_profile.get("proof_labels") != []
        or hardware_execution_profile.get("authority_not_granted")
        != _SOURCE_AUTHORITY_NOT_GRANTED
        or hardware_execution_profile.get("hardware_accessed") is not False
        or hardware_execution_profile.get("physical_follower_commanded") is not False
        or hardware_execution_profile.get("motion_authority_granted") is not False
        or hardware_execution_profile.get("training_authority_granted") is not False
    ):
        raise ValueError("Redacted review hardware profile classification drifted")
    if (
        candidate_result.get("schema_version") != _LIVE_RESULT_SCHEMA_VERSION
        or candidate_result.get("result_name")
        != "pi05_static_pose_live_candidate_runtime"
        or candidate_result.get("qualification_scope")
        != "local_static_pose_live_candidate_runtime"
        or candidate_result.get("evidence_mode")
        != "private_source_bound_live_candidate_runtime"
        or candidate_result.get("execution_class") != "live_candidate"
        or candidate_result.get("candidate_only") is not True
        or candidate_result.get("proof_labels") != []
        or candidate_result.get("local_capabilities")
        != ["source_bound_static_pose_live_candidate_runtime_observed"]
        or candidate_result.get("authority_not_granted")
        != _SOURCE_AUTHORITY_NOT_GRANTED
        or candidate_result.get("hardware_opened") is not True
        or candidate_result.get("physical_follower_commanded") is not False
        or candidate_result.get("policy_inference_run") is not False
        or candidate_result.get("motion_authority_granted") is not False
        or candidate_result.get("training_authority_granted") is not False
        or candidate_result.get("private_output_required") is not True
        or candidate_result.get("tracked_redacted_manifest_written") is not False
    ):
        raise ValueError("Redacted review candidate result classification drifted")
    if (
        private_evidence.get("schema_version")
        != _PRIVATE_SUCCESS_SCHEMA_VERSION
        or private_evidence.get("status") != "candidate_observed"
        or private_evidence.get("evidence_name")
        != "pi05_static_pose_live_candidate_private_success"
        or private_evidence.get("qualification_scope")
        != "local_static_pose_live_candidate_runtime"
        or private_evidence.get("evidence_mode")
        != "local_private_live_candidate_success"
        or private_evidence.get("candidate_only") is not True
        or private_evidence.get("session_id") != session_id
        or private_evidence.get("completed_at")
        != session_receipt.get("completed_at")
        or private_evidence.get("proof_labels") != []
        or private_evidence.get("authority_not_granted")
        != _SOURCE_AUTHORITY_NOT_GRANTED
        or private_evidence.get("hardware_opened") is not True
        or private_evidence.get("physical_follower_commanded") is not False
        or private_evidence.get("policy_inference_run") is not False
        or private_evidence.get("motion_authority_granted") is not False
        or private_evidence.get("training_authority_granted") is not False
        or private_evidence.get("tracked_redacted_manifest_written") is not False
        or private_evidence.get("candidate_result") != candidate_result
    ):
        raise ValueError("Redacted review private success classification drifted")

    _verify_private_reference(private_reference, private_evidence=private_evidence)
    reference_sha256 = _sha256_payload(private_reference)
    private_root_sha256 = _private_root_identity(private_root)
    if (
        session_receipt.get("candidate_contract_identity_sha256")
        != candidate_contract.get("identity_sha256")
        or session_receipt.get("hardware_execution_profile_identity_sha256")
        != hardware_execution_profile.get("identity_sha256")
        or session_receipt.get("candidate_result_identity_sha256")
        != candidate_result.get("identity_sha256")
        or session_receipt.get("private_evidence_identity_sha256")
        != private_evidence.get("identity_sha256")
        or session_receipt.get("private_reference") != private_reference
        or session_receipt.get("private_reference_sha256") != reference_sha256
        or session_receipt.get("private_root_identity_sha256")
        != private_root_sha256
        or candidate_result.get("candidate_contract_identity_sha256")
        != candidate_contract.get("identity_sha256")
        or candidate_result.get("hardware_execution_profile_identity_sha256")
        != hardware_execution_profile.get("identity_sha256")
        or candidate_result.get("static_pose_contract_identity_sha256")
        != static_pose_contract.get("identity_sha256")
        or candidate_result.get("project_state_identity_sha256")
        != candidate_contract.get("project_state_identity_sha256")
        or candidate_result.get("presence_lease_identity_sha256")
        != candidate_contract.get("presence_lease_identity_sha256")
        or candidate_result.get("discovery_identity_sha256")
        != candidate_contract.get("discovery_identity_sha256")
        or private_evidence.get("candidate_contract_identity_sha256")
        != candidate_contract.get("identity_sha256")
        or private_evidence.get("hardware_execution_profile_identity_sha256")
        != hardware_execution_profile.get("identity_sha256")
        or private_evidence.get("candidate_result_identity_sha256")
        != candidate_result.get("identity_sha256")
    ):
        raise ValueError("Redacted review source identity linkage drifted")
    _validated_source_artifacts(candidate_contract.get("source_artifacts"))

    verify_static_pose_live_session_receipt(
        session_receipt,
        candidate_contract=candidate_contract,
        hardware_execution_profile=hardware_execution_profile,
        candidate_result=candidate_result,
        private_evidence=private_evidence,
        private_reference=private_reference,
        private_root=private_root,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
    )


def _build_redacted_manifest(
    *,
    session_receipt: dict[str, Any],
    candidate_contract: dict[str, Any],
    hardware_execution_profile: dict[str, Any],
    candidate_result: dict[str, Any],
    private_evidence: dict[str, Any],
    private_reference: dict[str, Any],
) -> dict[str, Any]:
    capture = candidate_result["capture"]
    measurements = candidate_result["measurements"]
    if (
        not isinstance(capture, dict)
        or capture.get("hardware_opened") is not True
        or capture.get("physical_follower_commanded") is not False
    ):
        raise ValueError("Redacted review capture authority fields drifted")
    pre_open = capture["pre_open_holder_snapshot"]
    post_close = capture["post_close_holder_snapshot"]
    require_no_serial_identity_holders(pre_open)
    require_no_serial_identity_holders(post_close)
    verify_serial_identity_holder_stability(pre_open, post_close)
    operation_counts = _validated_nonnegative_integer_map(
        measurements.get("operation_counts"),
        label="redacted review operation counts",
    )
    if operation_counts != capture.get("operation_counts"):
        raise ValueError("Redacted review measurement/capture operation counts drifted")
    timing = _redacted_timing_summary(measurements.get("timing"))
    if measurements.get("static_pose_within_tolerance") is not True:
        raise ValueError("Redacted review requires a within-tolerance candidate")
    if operation_counts != EXPECTED_OPERATION_COUNTS:
        raise ValueError("Redacted review operation-count contract drifted")
    cameras = _redacted_camera_summary(
        candidate_result,
        candidate_contract=candidate_contract,
    )
    runtime_duration = _nonnegative_integer(
        capture.get("runtime_duration_ns"),
        label="redacted review runtime duration",
    )
    joint_drift = measurements.get("joint_drift")
    if not isinstance(joint_drift, list) or not joint_drift:
        raise ValueError("Redacted review joint drift evidence is missing")

    payload = {
        "schema_version": (
            REDACTED_STATIC_POSE_LIVE_SESSION_REVIEW_SCHEMA_VERSION
        ),
        "manifest_name": "pi05_static_pose_live_candidate_session_review",
        "qualification_scope": "local_static_pose_live_candidate_session_review",
        "evidence_mode": "tracked_redacted_private_candidate_session_review",
        "status": "candidate_observed_pending_review",
        "review_decision_required": True,
        "session_id": candidate_contract["session_id"],
        "candidate_only": True,
        "session_receipt_identity_sha256": session_receipt["identity_sha256"],
        "candidate_contract_identity_sha256": candidate_contract[
            "identity_sha256"
        ],
        "hardware_execution_profile_identity_sha256": (
            hardware_execution_profile["identity_sha256"]
        ),
        "candidate_result_identity_sha256": candidate_result["identity_sha256"],
        "private_evidence_identity_sha256": private_evidence["identity_sha256"],
        "source_artifacts": _redacted_source_artifacts(
            candidate_contract["source_artifacts"]
        ),
        "private_artifact": {
            "schema_version": private_reference["schema_version"],
            "identity_sha256": private_reference["identity_sha256"],
            "file_sha256": private_reference["file_sha256"],
            "size_bytes": private_reference["size_bytes"],
            "private_reference_sha256": session_receipt[
                "private_reference_sha256"
            ],
            "relative_path_included": False,
            "private_root_included": False,
        },
        "session_interval": {
            "preflight_at": session_receipt["preflight_at"],
            "started_at": session_receipt["started_at"],
            "completed_at": session_receipt["completed_at"],
        },
        "static_pose_summary": {
            "static_pose_within_tolerance": True,
            "maximum_body_drift_degrees": _finite_nonnegative(
                measurements.get("maximum_body_drift_degrees"),
                label="redacted review maximum body drift",
            ),
            "gripper_drift_percent": _finite_nonnegative(
                measurements.get("gripper_drift_percent"),
                label="redacted review gripper drift",
            ),
            "joint_drift_sha256": _sha256_payload(joint_drift),
            "timing": timing,
            "operation_counts": operation_counts,
        },
        "serial_holder_summary": {
            "pre_open": _redacted_holder_summary(pre_open),
            "post_close": _redacted_holder_summary(post_close),
            "identity_stable": True,
        },
        "camera_observation_summary": cameras,
        "runtime_summary": {
            "runtime_duration_ns": runtime_duration,
            "transport_audit_sha256": _sha256_payload(
                capture.get("transport_audit")
            ),
            "camera_audits_sha256": _sha256_payload(
                capture.get("camera_audits")
            ),
            "lifecycle_events_sha256": _sha256_payload(
                capture.get("lifecycle_events")
            ),
            "hardware_opened": True,
            "physical_follower_commanded": False,
        },
        "privacy": {
            "private_relative_path_included": False,
            "private_root_included": False,
            "embedded_contract_included": False,
            "embedded_hardware_profile_included": False,
            "embedded_candidate_result_included": False,
            "embedded_private_evidence_included": False,
            "doctor_report_included": False,
            "rollout_path_included": False,
            "raw_usb_serial_included": False,
            "raw_device_paths_included": False,
            "raw_camera_identity_included": False,
            "numeric_camera_index_included": False,
            "raw_joint_positions_included": False,
            "raw_frame_bytes_included": False,
        },
        "local_capabilities": [
            "redacted_static_pose_live_candidate_session_review_conformant"
        ],
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "hardware_opened": True,
        "physical_follower_commanded": False,
        "policy_inference_run": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
        "accepted_as_static_pose_bracketed_observation": False,
        "accepted_as_policy_shadow_input": False,
    }
    return sign_payload(payload)


def _redacted_camera_summary(
    candidate_result: dict[str, Any],
    *,
    candidate_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    capture = candidate_result.get("capture")
    batches = capture.get("cameras") if isinstance(capture, dict) else None
    bindings = candidate_result.get("resolved_camera_binding")
    contract_cameras = candidate_contract.get("cameras")
    if (
        not isinstance(batches, list)
        or not isinstance(bindings, list)
        or not isinstance(contract_cameras, list)
        or len(batches) != 2
        or len(bindings) != 2
        or len(contract_cameras) != 2
    ):
        raise ValueError("Redacted review requires exactly two camera observations")
    output = []
    frame_hashes: list[str] = []
    for batch, binding, contract_camera in zip(
        batches,
        bindings,
        contract_cameras,
        strict=True,
    ):
        if not isinstance(batch, dict) or set(batch) != {
            "stable_camera_identity_sha256",
            "input_mode",
            "frames",
        }:
            raise ValueError("Redacted review camera batch fields drifted")
        if not isinstance(binding, dict) or set(binding) != {
            "stable_camera_identity_sha256",
            "capture_camera_identity_sha256",
            "numeric_index",
        }:
            raise ValueError("Redacted review camera binding fields drifted")
        if not isinstance(contract_camera, dict):
            raise ValueError("Redacted review contract camera is malformed")
        stable = _require_sha256(
            batch.get("stable_camera_identity_sha256"),
            label="redacted review stable camera identity",
        )
        if stable != binding.get("stable_camera_identity_sha256"):
            raise ValueError("Redacted review stable camera identity drifted")
        capture_identity = _require_sha256(
            binding.get("capture_camera_identity_sha256"),
            label="redacted review capture camera identity",
        )
        _nonnegative_integer(
            binding.get("numeric_index"),
            label="redacted review numeric camera index",
        )
        input_mode = batch.get("input_mode")
        if not isinstance(input_mode, dict) or set(input_mode) != _INPUT_MODE_FIELDS:
            raise ValueError("Redacted review camera input mode fields drifted")
        resolved = contract_camera.get("resolved_camera")
        if (
            contract_camera.get("stable_camera_identity_sha256") != stable
            or contract_camera.get("capture_camera_identity_sha256")
            != capture_identity
            or not isinstance(resolved, dict)
            or resolved.get("input_mode") != input_mode
            or resolved.get("index") != binding.get("numeric_index")
        ):
            raise ValueError("Redacted review contract/result camera linkage drifted")
        require_nonblank(
            input_mode.get("pixel_format"),
            label="redacted review camera pixel format",
        )
        for field in ("width", "height", "framerate_fps"):
            _positive_integer(
                input_mode.get(field),
                label=f"redacted review camera {field}",
            )
        frames = batch.get("frames")
        if not isinstance(frames, list) or not frames:
            raise ValueError("Redacted review camera frames are missing")
        redacted_frames = []
        for expected_index, frame in enumerate(frames):
            if not isinstance(frame, dict) or set(frame) != _FRAME_FIELDS:
                raise ValueError("Redacted review frame fields drifted")
            if (
                type(frame.get("frame_index")) is not int
                or frame.get("frame_index") != expected_index
            ):
                raise ValueError("Redacted review frame index drifted")
            digest = _require_sha256(
                frame.get("frame_sha256"),
                label="redacted review frame",
            )
            frame_hashes.append(digest)
            if (
                frame.get("width") != input_mode["width"]
                or frame.get("height") != input_mode["height"]
                or frame.get("channels") != 3
                or frame.get("encoding") != "png"
            ):
                raise ValueError("Redacted review frame dimensions or encoding drifted")
            redacted_frames.append(copy.deepcopy(frame))
        output.append(
            {
                "stable_camera_identity_sha256": stable,
                "capture_camera_identity_sha256": capture_identity,
                "input_mode": copy.deepcopy(input_mode),
                "frames": redacted_frames,
            }
        )
    if len({item["stable_camera_identity_sha256"] for item in output}) != 2:
        raise ValueError("Redacted review stable camera identities are ambiguous")
    if len({item["capture_camera_identity_sha256"] for item in output}) != 2:
        raise ValueError("Redacted review capture camera identities are ambiguous")
    if len(frame_hashes) != len(set(frame_hashes)):
        raise ValueError("Redacted review frame identities are ambiguous")
    return output


def _redacted_holder_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    require_no_serial_identity_holders(snapshot)
    return {
        "snapshot_identity_sha256": snapshot["identity_sha256"],
        "serial_identity_sha256": _sha256_payload(
            {
                "canonical_path": snapshot["canonical_path"],
                "observed_aliases": snapshot["observed_aliases"],
                "paths_checked": snapshot["paths_checked"],
            }
        ),
        "path_count": len(snapshot["paths_checked"]),
        "path_identity_sha256": [
            hashlib.sha256(path.encode("utf-8")).hexdigest()
            for path in snapshot["paths_checked"]
        ],
        "paths_all_existed": all(
            record["path_exists"] for record in snapshot["per_path"]
        ),
        "per_path_holder_counts": list(snapshot["per_path_holder_counts"]),
        "per_path_holder_snapshot_sha256": [
            _sha256_payload(record["holders"]) for record in snapshot["per_path"]
        ],
        "deduplicated_holder_count": snapshot["deduplicated_holder_count"],
        "normalized_holder_snapshot_sha256": _sha256_payload(
            snapshot["deduplicated_holders"]
        ),
    }


def _redacted_source_artifacts(value: Any) -> dict[str, Any]:
    artifacts = _validated_source_artifacts(value)
    return {
        name: {
            "schema_version": reference["schema_version"],
            "identity_sha256": reference["identity_sha256"],
            "file_sha256": reference["file_sha256"],
            "size_bytes": reference["size_bytes"],
            "logical_path_included": False,
        }
        for name, reference in sorted(artifacts.items())
    }


def _validated_source_artifacts(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _SOURCE_ARTIFACT_KEYS:
        raise ValueError("Redacted review source artifact set drifted")
    for name, reference in value.items():
        if not isinstance(reference, dict) or set(reference) != {
            "logical_path",
            "schema_version",
            "identity_sha256",
            "file_sha256",
            "size_bytes",
        }:
            raise ValueError(f"Redacted review {name} reference fields drifted")
        require_nonblank(
            reference.get("logical_path"),
            label=f"redacted review {name} logical path",
        )
        require_nonblank(
            reference.get("schema_version"),
            label=f"redacted review {name} schema",
        )
        _require_sha256(
            reference.get("identity_sha256"),
            label=f"redacted review {name} identity",
        )
        _require_sha256(
            reference.get("file_sha256"),
            label=f"redacted review {name} file",
        )
        _positive_integer(
            reference.get("size_bytes"),
            label=f"redacted review {name} size",
        )
    return value


def _verify_private_reference(
    value: Any,
    *,
    private_evidence: dict[str, Any],
) -> None:
    if not isinstance(value, dict) or set(value) != {
        "relative_path",
        "schema_version",
        "identity_sha256",
        "file_sha256",
        "size_bytes",
    }:
        raise ValueError("Redacted review private reference fields drifted")
    relative = Path(
        require_nonblank(
            value.get("relative_path"),
            label="redacted review private relative path",
        )
    )
    if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 3:
        raise ValueError("Redacted review private relative path is unsafe")
    expected_relative = Path(
        _validated_session_id(private_evidence.get("session_id")),
        _require_sha256(
            private_evidence.get("identity_sha256"),
            label="redacted review private evidence identity",
        ),
        "private_success.json",
    )
    if relative != expected_relative:
        raise ValueError("Redacted review private relative path identity drifted")
    if (
        value.get("schema_version") != private_evidence.get("schema_version")
        or value.get("identity_sha256")
        != private_evidence.get("identity_sha256")
    ):
        raise ValueError("Redacted review private reference identity drifted")
    _require_sha256(value.get("file_sha256"), label="redacted review private file")
    _positive_integer(value.get("size_bytes"), label="redacted review private size")


def _redacted_timing_summary(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError("Redacted review timing evidence is missing")
    if not _SAFE_TIMING_FIELDS.issubset(value):
        raise ValueError("Redacted review timing evidence is incomplete")
    summary = {
        field: _nonnegative_integer(
            value.get(field),
            label=f"redacted review {field}",
        )
        for field in sorted(_SAFE_TIMING_FIELDS)
    }
    if (
        summary["bracket_duration_ns"]
        > summary["maximum_bracket_duration_ns"]
        or summary["camera_receive_duration_ns"]
        > summary["bracket_duration_ns"]
    ):
        raise ValueError("Redacted review timing bounds drifted")
    return summary


def _validated_nonnegative_integer_map(value: Any, *, label: str) -> dict[str, int]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} must be a nonempty object")
    output: dict[str, int] = {}
    for key, item in value.items():
        name = require_nonblank(key, label=f"{label} key")
        output[name] = _nonnegative_integer(item, label=f"{label} {name}")
    return output


def _finite_nonnegative(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite nonnegative number")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return number


def _nonnegative_integer(value: Any, *, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _positive_integer(value: Any, *, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _validated_session_id(value: Any) -> str:
    session_id = require_nonblank(value, label="redacted review session ID")
    if not _SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError("Redacted review session ID is unsafe")
    return session_id


def _validated_repository_root(value: Path) -> Path:
    unresolved = Path(value)
    if unresolved.is_symlink() or not unresolved.is_dir():
        raise ValueError("Tracked live-session review repository root is invalid")
    absolute = Path(os.path.abspath(unresolved))
    resolved = unresolved.resolve()
    if absolute != resolved:
        raise ValueError("Tracked live-session review repository root is aliased")
    return resolved


def _has_symlink_between(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    candidate = root
    if candidate.is_symlink():
        return True
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            return True
    return False


def _write_exclusive_bytes(path: Path, encoded: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(encoded)


def _private_root_identity(path: Path) -> str:
    root = Path(path)
    normalized = root.resolve().as_posix() if root.is_absolute() else root.as_posix()
    return _sha256_payload(normalized)


def _sha256_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest
