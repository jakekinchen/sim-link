"""Signed, source-bound semantic profile for the accepted SO-101 calibration."""

from __future__ import annotations

import hashlib

from collections import Counter
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)


CALIBRATION_PROFILE_SCHEMA_VERSION = "scenesmith.calibration_profile.v1"
ACCEPTED_MANIFEST_SCHEMA_VERSION = "scenesmith.live_readonly_observation_manifest.v4"
ACCEPTED_LIVE_MANIFEST_IDENTITY = (
    "eff3c82444efd38b6a2e240b1137846ad835222fd86ed330cf274343e1e28c5f"
)
EXPECTED_CALIBRATION_FILE_SHA256 = (
    "192404b6d3c1337495d69649969459aa9d3f66816cd916c67da2588815e93ec4"
)
EXPECTED_CALIBRATION_FILE_SIZE_BYTES = 770
EXPECTED_JOINT_IDS = {
    "shoulder_pan": 1,
    "shoulder_lift": 2,
    "elbow_flex": 3,
    "wrist_flex": 4,
    "wrist_roll": 5,
    "gripper": 6,
}
RAW_POSITION_MIN = 0
RAW_POSITION_MAX = 4095
HOMING_OFFSET_MIN = -2047
HOMING_OFFSET_MAX = 2047

_CALIBRATION_FIELDS = {
    "id",
    "drive_mode",
    "homing_offset",
    "range_min",
    "range_max",
}
_REQUIRED_LIVE_PROOF_LABELS = {
    "live_read_only_census_observed",
    "physical_observation_capture",
}


def build_calibration_profile(
    *,
    calibration_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Build the exact offline profile bound to the accepted T16.5b evidence."""

    calibration_path = Path(calibration_path)
    manifest_path = Path(manifest_path)
    calibration = load_strict_json(calibration_path)
    normalized_calibration = _validate_calibration(calibration)
    calibration_sha256 = _sha256_file(calibration_path)
    calibration_size = calibration_path.stat().st_size
    if (
        calibration_sha256 != EXPECTED_CALIBRATION_FILE_SHA256
        or calibration_size != EXPECTED_CALIBRATION_FILE_SIZE_BYTES
    ):
        raise ValueError("Pinned follower calibration source identity drifted")

    manifest = load_strict_json(manifest_path)
    servo_identity = _validate_accepted_manifest(manifest)
    if manifest.get("calibration_file_sha256") != calibration_sha256:
        raise ValueError("Accepted live manifest calibration identity drifted")

    live_by_name = {item["joint_name"]: item for item in servo_identity}
    joints = []
    for joint_name, servo_id in EXPECTED_JOINT_IDS.items():
        source = normalized_calibration[joint_name]
        live = live_by_name[joint_name]
        normalization = (
            _gripper_normalization()
            if joint_name == "gripper"
            else _body_normalization()
        )
        joints.append(
            {
                "joint_name": joint_name,
                "servo_id": servo_id,
                "model": live["model"],
                "model_number": live["model_number"],
                "firmware_version": live["firmware_version"],
                "drive_mode": source["drive_mode"],
                "homing_offset": source["homing_offset"],
                "homing_offset_units": "decoded_sts3215_sign_magnitude_ticks",
                "range_min": source["range_min"],
                "range_max": source["range_max"],
                "range_units": "raw_position_ticks",
                "normalization": normalization,
            }
        )

    profile = {
        "schema_version": CALIBRATION_PROFILE_SCHEMA_VERSION,
        "profile_name": "pi05_follower_arm_calibration_profile",
        "evidence_mode": "tracked_content_addressed_offline_semantic_validation",
        "qualification_scope": "local_calibration_semantics",
        "source_calibration": {
            "logical_name": "lerobot_so_follower_follower_arm",
            "sha256": calibration_sha256,
            "size_bytes": calibration_size,
            "raw_path_included": False,
        },
        "accepted_live_manifest": {
            "logical_path": (
                "configurations/robot_lab/"
                "pi05_live_readonly_observation.redacted.json"
            ),
            "schema_version": manifest["schema_version"],
            "identity_sha256": manifest["identity_sha256"],
            "file_sha256": _sha256_file(manifest_path),
            "size_bytes": manifest_path.stat().st_size,
        },
        "servo_identity_sha256": hashlib.sha256(
            canonical_json_bytes(servo_identity)
        ).hexdigest(),
        "joint_count": len(joints),
        "joints": joints,
        "normalization_contract": {
            "lerobot_use_degrees": True,
            "body_mode": "degrees",
            "gripper_mode": "range_0_100",
            "sts3215_resolution_ticks": RAW_POSITION_MAX + 1,
            "gripper_polarity": "0_closed_100_open",
        },
        "local_capabilities": ["calibration_profile_semantically_valid"],
        "authority_not_granted": [
            "physical_twin_qualified",
            "physical_transfer_ready",
            "policy_shadow_input_valid",
            "promotion_eligible",
            "simulation_training_ready",
            "supervised_micro_motion",
        ],
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "policy_inference_run": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
        "privacy": {
            "raw_calibration_path_included": False,
            "raw_device_path_included": False,
            "raw_usb_serial_included": False,
        },
    }
    return sign_payload(profile)


def verify_calibration_profile(
    profile: dict[str, Any],
    *,
    calibration_path: Path,
    manifest_path: Path,
) -> None:
    """Rebuild from pinned sources and reject signed semantic substitution."""

    if not isinstance(profile, dict):
        raise ValueError("Calibration profile must be an object")
    if profile.get("schema_version") != CALIBRATION_PROFILE_SCHEMA_VERSION:
        raise ValueError("Calibration profile schema version is unsupported")
    verify_signed_payload(profile, label="Calibration profile")
    expected = build_calibration_profile(
        calibration_path=calibration_path,
        manifest_path=manifest_path,
    )
    if canonical_json_bytes(profile) != canonical_json_bytes(expected):
        raise ValueError("Calibration profile semantic or source drift detected")


def _validate_calibration(payload: dict[str, Any]) -> dict[str, dict[str, int]]:
    if set(payload) != set(EXPECTED_JOINT_IDS):
        raise ValueError("Calibration must contain exactly the expected six joints")

    normalized: dict[str, dict[str, int]] = {}
    ids = []
    for joint_name in EXPECTED_JOINT_IDS:
        item = payload.get(joint_name)
        if not isinstance(item, dict) or set(item) != _CALIBRATION_FIELDS:
            raise ValueError(f"Calibration {joint_name} fields are invalid")
        values = {
            field: _require_integer(item.get(field), label=f"{joint_name} {field}")
            for field in _CALIBRATION_FIELDS
        }
        ids.append(values["id"])
        if values["drive_mode"] != 0:
            raise ValueError(f"Calibration {joint_name} drive_mode must be zero")
        if not HOMING_OFFSET_MIN <= values["homing_offset"] <= HOMING_OFFSET_MAX:
            raise ValueError(f"Calibration {joint_name} homing_offset is outside signed domain")
        if not RAW_POSITION_MIN <= values["range_min"] <= RAW_POSITION_MAX:
            raise ValueError(f"Calibration {joint_name} range_min is outside raw domain")
        if not RAW_POSITION_MIN <= values["range_max"] <= RAW_POSITION_MAX:
            raise ValueError(f"Calibration {joint_name} range_max is outside raw domain")
        if values["range_min"] >= values["range_max"]:
            raise ValueError(
                f"Calibration {joint_name} range_min must be less than range_max"
            )
        normalized[joint_name] = values

    duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        raise ValueError(f"Calibration has duplicate servo id: {duplicate_ids[0]}")
    for joint_name, expected_id in EXPECTED_JOINT_IDS.items():
        if normalized[joint_name]["id"] != expected_id:
            raise ValueError(f"Calibration {joint_name} servo id mismatch")
    return normalized


def _validate_accepted_manifest(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("schema_version") != ACCEPTED_MANIFEST_SCHEMA_VERSION:
        raise ValueError("Accepted live manifest schema version drifted")
    verify_signed_payload(payload, label="Accepted live manifest")
    if payload.get("identity_sha256") != ACCEPTED_LIVE_MANIFEST_IDENTITY:
        raise ValueError("Accepted live manifest identity drifted")
    if payload.get("physical_follower_commanded") is not False:
        raise ValueError("Accepted live manifest commanded the physical follower")
    if set(payload.get("proof_labels", [])) != _REQUIRED_LIVE_PROOF_LABELS:
        raise ValueError("Accepted live manifest proof labels drifted")

    servo_identity = payload.get("servo_identity")
    if not isinstance(servo_identity, list) or len(servo_identity) != 6:
        raise ValueError("Accepted live manifest requires six servo identities")
    by_name: dict[str, dict[str, Any]] = {}
    ids = []
    for item in servo_identity:
        if not isinstance(item, dict):
            raise ValueError("Accepted live manifest servo identity is invalid")
        name = require_nonblank(item.get("joint_name"), label="live joint_name")
        servo_id = _require_integer(item.get("servo_id"), label=f"{name} servo_id")
        if name in by_name:
            raise ValueError(f"Accepted live manifest duplicate joint: {name}")
        by_name[name] = item
        ids.append(servo_id)

    if set(by_name) != set(EXPECTED_JOINT_IDS):
        raise ValueError("Accepted live manifest joint identity drifted")
    if len(set(ids)) != len(ids):
        raise ValueError("Accepted live manifest has duplicate servo ids")
    normalized = []
    for name, expected_id in EXPECTED_JOINT_IDS.items():
        item = by_name[name]
        if item.get("servo_id") != expected_id:
            raise ValueError(f"Accepted live manifest {name} servo id mismatch")
        if item.get("model") != "sts3215" or item.get("model_number") != 777:
            raise ValueError(f"Accepted live manifest {name} model identity drifted")
        normalized.append(
            {
                "joint_name": name,
                "servo_id": expected_id,
                "model": "sts3215",
                "model_number": 777,
                "firmware_version": require_nonblank(
                    item.get("firmware_version"),
                    label=f"{name} firmware_version",
                ),
            }
        )
    return normalized


def _body_normalization() -> dict[str, Any]:
    return {
        "mode": "degrees",
        "input_units": "raw_position_ticks",
        "output_units": "degrees",
        "formula": "(raw_value - ((range_min + range_max) / 2)) * 360 / 4095",
        "input_clamping": "none_in_lerobot_degree_mode",
        "drive_mode_reversal_applied": False,
        "range_midpoint_defines_zero_degrees": True,
    }


def _gripper_normalization() -> dict[str, Any]:
    return {
        "mode": "range_0_100",
        "input_units": "raw_position_ticks",
        "output_units": "normalized_percent",
        "formula": "clamp((raw_value - range_min) / (range_max - range_min), 0, 1) * 100",
        "input_clamping": "range_min_to_range_max",
        "drive_mode_reversal_applied": False,
        "normalized_0_raw_endpoint": "range_min",
        "normalized_0_physical_meaning": "closed",
        "normalized_100_raw_endpoint": "range_max",
        "normalized_100_physical_meaning": "open",
    }


def _require_integer(value: Any, *, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
