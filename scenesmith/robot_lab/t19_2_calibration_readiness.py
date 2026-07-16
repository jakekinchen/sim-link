"""Fail-closed, source-bound readiness matrix for physical calibration."""

from __future__ import annotations

import copy
import hashlib

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.calibration_profile import verify_calibration_profile
from scenesmith.robot_lab.timing_latency_certificate import (
    verify_timing_latency_fixture,
)


SCHEMA_VERSION = "scenesmith.t19_2_calibration_readiness.v1"
T19_1_PATH = Path(
    "configurations/robot_lab/t19_1_readonly_hardware_snapshot_20260716_0712.json"
)
CALIBRATION_PROFILE_PATH = Path("configurations/robot_lab/pi05_calibration_profile.json")
ACCEPTED_LIVE_MANIFEST_PATH = Path(
    "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
CAMERA_REVIEW_PATH = Path(
    "configurations/robot_lab/"
    "pi05_static_pose_live_session_t16-5c-20260713-0958-cdt.redacted.json"
)
TIMING_FIXTURE_PATH = Path(
    "configurations/robot_lab/t20_22_timing_latency_certificate.json"
)
RAW_CALIBRATION_PATH = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
REQUIRED_PHYSICAL_EVIDENCE = (
    "central_motion_session_authority_granted",
    "current_metric_calibration_target_observed",
    "camera_intrinsics_measured",
    "camera_to_robot_base_extrinsics_measured",
    "joint_offset_held_out_motion_samples",
    "gripper_metric_aperture_samples",
    "live_monotonic_timing_samples",
    "watchdog_deadman_stop_return_harness_verified",
)
AUTHORITY_NOT_GRANTED = (
    "camera_access",
    "serial_access",
    "register_write",
    "torque_change",
    "motion",
    "calibration_update",
    "twin_update",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "policy_actuation",
    "promotion_eligible",
    "external_compute",
    "brev_compute",
)


def build_t19_2_calibration_readiness(
    *,
    repo_root: Path,
    project_state: dict[str, Any],
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    t19_1_path = root / T19_1_PATH
    calibration_path = root / CALIBRATION_PROFILE_PATH
    accepted_manifest_path = root / ACCEPTED_LIVE_MANIFEST_PATH
    camera_path = root / CAMERA_REVIEW_PATH
    timing_path = root / TIMING_FIXTURE_PATH
    t19_1 = load_strict_json(t19_1_path)
    calibration = load_strict_json(calibration_path)
    camera_review = load_strict_json(camera_path)
    timing = load_strict_json(timing_path)
    for label, payload in (
        ("T19.1 snapshot", t19_1),
        ("camera review", camera_review),
    ):
        verify_signed_payload(payload, label=label)
    verify_calibration_profile(
        calibration,
        calibration_path=RAW_CALIBRATION_PATH,
        manifest_path=accepted_manifest_path,
    )
    verify_timing_latency_fixture(timing)

    t19_state = project_state.get("tasks", {}).get("T19.1", {})
    camera_state = (
        project_state.get("tasks", {})
        .get("T16.5c", {})
        .get("latest_observed_live_candidate", {})
        .get("review_manifest", {})
    )
    if (
        t19_state.get("state") != "verified"
        or t19_state.get("artifact", {}).get("identity_sha256")
        != t19_1.get("identity_sha256")
    ):
        raise ValueError("T19.2 readiness T19.1 state/source binding drifted")
    if camera_state.get("identity_sha256") != camera_review.get("identity_sha256"):
        raise ValueError("T19.2 readiness camera review/state binding drifted")
    if project_state.get("tasks", {}).get("T16.6", {}).get("state") != "pending":
        raise ValueError("T19.2 readiness T16.6 motion state drifted")

    present = {
        "fresh_readonly_servo_identity_and_telemetry": True,
        "joint_calibration_semantics_source_bound": True,
        "historical_camera_identity_and_mode_review_bound": True,
        "offline_timing_threshold_contract_bound": True,
    }
    required = [
        {"prerequisite_id": prerequisite, "satisfied": False, "evidence": None}
        for prerequisite in REQUIRED_PHYSICAL_EVIDENCE
    ]
    sources = {
        "t19_1_snapshot": _reference(root, t19_1_path, t19_1),
        "calibration_profile": _reference(root, calibration_path, calibration),
        "camera_review": _reference(root, camera_path, camera_review),
        "timing_fixture": _reference(root, timing_path, timing),
    }
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "report_name": "pi05_t19_2_physical_calibration_readiness",
            "evidence_mode": "offline_source_bound_readiness_audit",
            "qualification_scope": "physical_calibration_preflight",
            "source_artifacts": sources,
            "present_local_capabilities": present,
            "required_physical_evidence": required,
            "missing_prerequisite_ids": list(REQUIRED_PHYSICAL_EVIDENCE),
            "calibration_session_ready": False,
            "motion_authority_ready": False,
            "physical_twin_qualified": False,
            "physical_transfer_ready": False,
            "selected_next_slice": (
                "t19_2a_calibration_target_and_bounded_micro_motion_harness"
            ),
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "authority_granted": ["t19_2_calibration_readiness_matrix_valid"],
            "authority_not_granted": list(AUTHORITY_NOT_GRANTED),
        }
    )


def verify_t19_2_calibration_readiness(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    project_state: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T19.2 calibration readiness")
    expected = build_t19_2_calibration_readiness(
        repo_root=repo_root,
        project_state=project_state,
    )
    if payload != expected:
        raise ValueError("T19.2 calibration readiness drifted from exact sources")


def _reference(root: Path, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }
