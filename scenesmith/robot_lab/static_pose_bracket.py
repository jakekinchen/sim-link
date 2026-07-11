"""Offline contract and fixture verifier for static-pose-bracketed observation."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.calibration_profile import (
    ACCEPTED_LIVE_MANIFEST_IDENTITY,
    EXPECTED_JOINT_IDS,
    verify_calibration_profile,
)


STATIC_POSE_BRACKET_CONTRACT_SCHEMA_VERSION = (
    "scenesmith.static_pose_bracket_contract.v1"
)
STATIC_POSE_BRACKET_OBSERVATION_SCHEMA_VERSION = (
    "scenesmith.static_pose_bracket_observation.v1"
)
STATIC_POSE_BRACKET_RESULT_SCHEMA_VERSION = "scenesmith.static_pose_bracket_result.v1"
ACCEPTED_CALIBRATION_PROFILE_IDENTITY = (
    "b360b4f60077846c62128fe4d4cc33d1ee4e6e72aa7831fcb7c6706e6b6599b4"
)
ACCEPTED_STATIC_POSE_BRACKET_CONTRACT_IDENTITY = (
    "90e7baea43ebc059c09ef45b615c5808cf74abbbab87948a23536666acb43ceb"
)
BODY_TOLERANCE_DEGREES = 0.5
GRIPPER_TOLERANCE_PERCENT = 0.5
MAX_BRACKET_DURATION_NS = 5_000_000_000
EXPECTED_FRAME_COUNT_PER_CAMERA = 2

EXPECTED_OPERATION_COUNTS = {
    "construct_attempts": 1,
    "construct_successes": 1,
    "connect_attempts": 1,
    "connect_successes": 1,
    "position_read_attempts": 12,
    "position_read_successes": 12,
    "read_retries": 0,
    "close_attempts": 1,
    "close_successes": 1,
    "camera_batch_attempts": 2,
    "camera_batch_successes": 2,
    "camera_frame_reads": 4,
    "motor_register_writes": 0,
    "configuration_writes": 0,
    "torque_changes": 0,
    "motion_commands": 0,
    "unexpected_operations": 0,
}

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


def build_static_pose_bracket_contract(
    *,
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Build the exact no-write bracket contract from accepted source artifacts."""

    profile_path = Path(calibration_profile_path)
    manifest_path = Path(manifest_path)
    profile = load_strict_json(profile_path)
    manifest = load_strict_json(manifest_path)
    verify_calibration_profile(
        profile,
        calibration_path=Path(calibration_path),
        manifest_path=manifest_path,
    )
    if profile.get("identity_sha256") != ACCEPTED_CALIBRATION_PROFILE_IDENTITY:
        raise ValueError("Accepted CalibrationProfile identity drifted")
    verify_signed_payload(manifest, label="Accepted live manifest")
    if manifest.get("identity_sha256") != ACCEPTED_LIVE_MANIFEST_IDENTITY:
        raise ValueError("Accepted live manifest identity drifted")

    profile_joints = profile.get("joints")
    if not isinstance(profile_joints, list) or len(profile_joints) != 6:
        raise ValueError("CalibrationProfile must contain six joints")
    joints = []
    for index, (joint_name, servo_id) in enumerate(EXPECTED_JOINT_IDS.items()):
        source = profile_joints[index]
        if (
            source.get("joint_name") != joint_name
            or source.get("servo_id") != servo_id
        ):
            raise ValueError("CalibrationProfile ordered joint identity drifted")
        is_gripper = joint_name == "gripper"
        expected_mode = "range_0_100" if is_gripper else "degrees"
        if source.get("normalization", {}).get("mode") != expected_mode:
            raise ValueError(f"CalibrationProfile {joint_name} normalization drifted")
        joints.append(
            {
                "joint_name": joint_name,
                "servo_id": servo_id,
                "range_min": source["range_min"],
                "range_max": source["range_max"],
                "raw_units": "raw_position_ticks",
                "normalization_mode": expected_mode,
                "coordinate_units": "percent" if is_gripper else "degrees",
                "tolerance": (
                    GRIPPER_TOLERANCE_PERCENT
                    if is_gripper
                    else BODY_TOLERANCE_DEGREES
                ),
            }
        )

    manifest_cameras = manifest.get("cameras")
    if not isinstance(manifest_cameras, list) or len(manifest_cameras) != 2:
        raise ValueError("Accepted live manifest must contain two cameras")
    cameras = []
    for camera in manifest_cameras:
        identity = _require_sha256(
            camera.get("camera_identity_sha256"),
            label="accepted camera identity",
        )
        mode = _validate_input_mode(camera.get("input_mode"), label="accepted camera")
        cameras.append(
            {
                "camera_identity_sha256": identity,
                "input_mode": mode,
                "required_frame_count": EXPECTED_FRAME_COUNT_PER_CAMERA,
                "required_encoding": "png",
                "required_channels": 3,
            }
        )
    if len({camera["camera_identity_sha256"] for camera in cameras}) != 2:
        raise ValueError("Accepted camera identities must be unique")

    contract = {
        "schema_version": STATIC_POSE_BRACKET_CONTRACT_SCHEMA_VERSION,
        "contract_name": "pi05_static_pose_bracket_contract",
        "evidence_mode": "offline_contract_bound_to_accepted_physical_identities",
        "qualification_scope": "local_static_pose_bracket_contract",
        "calibration_profile": _tracked_reference(
            path=profile_path,
            logical_path="configurations/robot_lab/pi05_calibration_profile.json",
            payload=profile,
        ),
        "accepted_live_manifest": _tracked_reference(
            path=manifest_path,
            logical_path=(
                "configurations/robot_lab/"
                "pi05_live_readonly_observation.redacted.json"
            ),
            payload=manifest,
        ),
        "joint_count": len(joints),
        "joints": joints,
        "camera_count": len(cameras),
        "cameras": cameras,
        "read_plan": {
            "register": "Present_Position",
            "register_width_bytes": 2,
            "phase_order": ["q_before", "finite_camera_batch", "q_after"],
            "position_reads_per_phase": 6,
            "total_position_reads": 12,
            "raw_values_must_be_within_calibrated_range": True,
        },
        "timing_contract": {
            "clock": "host_monotonic_ns",
            "strict_camera_interval_enclosure": True,
            "maximum_bracket_duration_ns": MAX_BRACKET_DURATION_NS,
        },
        "serial_holder_contract": {
            "signed_snapshot_required": True,
            "canonical_and_observed_aliases_required": True,
            "pre_open_deduplicated_holder_count": 0,
            "post_close_deduplicated_holder_count": 0,
            "path_set_must_remain_stable": True,
        },
        "lifecycle_constraints": {
            "handshake": False,
            "disconnect_disable_torque": False,
            "teardown_may_write_register": False,
            "teardown_may_change_torque": False,
            "teardown_may_command_motion": False,
        },
        "operation_counts": dict(EXPECTED_OPERATION_COUNTS),
        "local_capabilities": ["static_pose_bracket_contract_valid"],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "policy_inference_run": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
        "privacy": {
            "raw_calibration_path_included": False,
            "raw_device_path_included": False,
            "raw_camera_name_included": False,
            "raw_usb_serial_included": False,
        },
    }
    return sign_payload(contract)


def verify_static_pose_bracket_contract(
    contract: dict[str, Any],
    *,
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
) -> None:
    """Rebuild the contract and reject re-signed semantic or source drift."""

    _validate_contract_invariants(contract)
    expected = build_static_pose_bracket_contract(
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
    )
    if canonical_json_bytes(contract) != canonical_json_bytes(expected):
        raise ValueError("Static pose bracket contract semantic or source drift detected")


def build_fixture_static_pose_observation(
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic fixture-only input for the production evaluator."""

    _validate_contract_invariants(contract)
    before_values = [2100, 2000, 1900, 2000, 2048, 1900]
    after_values = [2104, 2004, 1904, 2004, 2052, 1903]
    q_before = []
    q_after = []
    for joint, before, after in zip(
        contract["joints"],
        before_values,
        after_values,
        strict=True,
    ):
        identity = {
            "joint_name": joint["joint_name"],
            "servo_id": joint["servo_id"],
        }
        q_before.append({**identity, "raw_position": before})
        q_after.append({**identity, "raw_position": after})

    cameras = []
    for camera_index, camera in enumerate(contract["cameras"]):
        frames = []
        for frame_index in range(camera["required_frame_count"]):
            label = f"static-pose-fixture-camera-{camera_index}-frame-{frame_index}"
            frames.append(
                {
                    "frame_index": frame_index,
                    "frame_sha256": hashlib.sha256(label.encode("utf-8")).hexdigest(),
                    "width": camera["input_mode"]["width"],
                    "height": camera["input_mode"]["height"],
                    "channels": camera["required_channels"],
                    "encoding": camera["required_encoding"],
                }
            )
        cameras.append(
            {
                "camera_identity_sha256": camera["camera_identity_sha256"],
                "input_mode": dict(camera["input_mode"]),
                "frames": frames,
            }
        )

    observation = {
        "schema_version": STATIC_POSE_BRACKET_OBSERVATION_SCHEMA_VERSION,
        "observation_name": "pi05_static_pose_bracket_fixture_observation",
        "evidence_mode": "deterministic_fixture",
        "contract_identity_sha256": contract["identity_sha256"],
        "timing": {
            "q_before_started_monotonic_ns": 1_000_000_000,
            "q_before_finished_monotonic_ns": 1_020_000_000,
            "camera_receive_started_monotonic_ns": 1_100_000_000,
            "camera_receive_finished_monotonic_ns": 2_200_000_000,
            "q_after_started_monotonic_ns": 2_300_000_000,
            "q_after_finished_monotonic_ns": 2_320_000_000,
        },
        "q_before": q_before,
        "cameras": cameras,
        "q_after": q_after,
        "operation_counts": dict(EXPECTED_OPERATION_COUNTS),
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "policy_inference_run": False,
        "fixture_only": True,
    }
    return sign_payload(observation)


def evaluate_static_pose_bracket(
    *,
    contract: dict[str, Any],
    observation: dict[str, Any],
) -> dict[str, Any]:
    """Validate one fixture bracket and derive coordinate drift evidence."""

    _validate_contract_invariants(contract)
    verify_signed_payload(observation, label="Static pose bracket observation")
    _validate_observation_envelope(observation, contract=contract)
    before = _validate_positions(
        observation.get("q_before"),
        contract=contract,
        label="q_before",
    )
    after = _validate_positions(
        observation.get("q_after"),
        contract=contract,
        label="q_after",
    )
    timing_result = _validate_timing(observation.get("timing"), contract=contract)
    _validate_cameras(observation.get("cameras"), contract=contract)

    joint_drift = []
    for joint in contract["joints"]:
        name = joint["joint_name"]
        coordinate_before = _normalize_position(before[name], joint=joint)
        coordinate_after = _normalize_position(after[name], joint=joint)
        absolute_delta = abs(coordinate_after - coordinate_before)
        if not math.isfinite(absolute_delta):
            raise ValueError(f"{name} drift is non-finite")
        if absolute_delta > joint["tolerance"]:
            raise ValueError(f"{name} drift exceeds tolerance")
        joint_drift.append(
            {
                "joint_name": name,
                "servo_id": joint["servo_id"],
                "raw_before": before[name],
                "raw_after": after[name],
                "coordinate_before": coordinate_before,
                "coordinate_after": coordinate_after,
                "coordinate_units": joint["coordinate_units"],
                "absolute_delta": absolute_delta,
                "tolerance": joint["tolerance"],
                "within_tolerance": True,
            }
        )

    body_drift = [item["absolute_delta"] for item in joint_drift[:-1]]
    result = {
        "schema_version": STATIC_POSE_BRACKET_RESULT_SCHEMA_VERSION,
        "result_name": "pi05_static_pose_bracket_fixture_result",
        "evidence_mode": "deterministic_fixture_evaluation",
        "qualification_scope": "fixture_static_pose_bracket",
        "contract_identity_sha256": contract["identity_sha256"],
        "observation_identity_sha256": observation["identity_sha256"],
        "joint_drift": joint_drift,
        "maximum_body_drift_degrees": max(body_drift),
        "gripper_drift_percent": joint_drift[-1]["absolute_delta"],
        "timing": timing_result,
        "operation_counts": dict(observation["operation_counts"]),
        "static_pose_within_tolerance": True,
        "local_capabilities": ["fixture_static_pose_bracket_conformant"],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "policy_inference_run": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
    }
    return sign_payload(result)


def verify_static_pose_bracket_result(
    result: dict[str, Any],
    *,
    contract: dict[str, Any],
    observation: dict[str, Any],
) -> None:
    """Re-evaluate the fixture input and reject re-signed result drift."""

    if result.get("schema_version") != STATIC_POSE_BRACKET_RESULT_SCHEMA_VERSION:
        raise ValueError("Static pose bracket result schema version is unsupported")
    verify_signed_payload(result, label="Static pose bracket result")
    expected = evaluate_static_pose_bracket(
        contract=contract,
        observation=observation,
    )
    if canonical_json_bytes(result) != canonical_json_bytes(expected):
        raise ValueError("Static pose bracket result semantic drift detected")


def _validate_contract_invariants(contract: dict[str, Any]) -> None:
    if not isinstance(contract, dict):
        raise ValueError("Static pose bracket contract must be an object")
    if contract.get("schema_version") != STATIC_POSE_BRACKET_CONTRACT_SCHEMA_VERSION:
        raise ValueError("Static pose bracket contract schema version is unsupported")
    verify_signed_payload(contract, label="Static pose bracket contract")
    if (
        contract.get("identity_sha256")
        != ACCEPTED_STATIC_POSE_BRACKET_CONTRACT_IDENTITY
    ):
        raise ValueError(
            "Static pose bracket contract semantic or source drift: identity mismatch"
        )
    if (
        contract.get("calibration_profile", {}).get("identity_sha256")
        != ACCEPTED_CALIBRATION_PROFILE_IDENTITY
    ):
        raise ValueError("Static pose bracket CalibrationProfile identity drifted")
    if (
        contract.get("accepted_live_manifest", {}).get("identity_sha256")
        != ACCEPTED_LIVE_MANIFEST_IDENTITY
    ):
        raise ValueError("Static pose bracket accepted manifest identity drifted")
    if contract.get("operation_counts") != EXPECTED_OPERATION_COUNTS:
        raise ValueError("Static pose bracket contract operation counts drifted")
    if contract.get("hardware_accessed") is not False:
        raise ValueError("Static pose bracket contract hardware_accessed must be false")
    if contract.get("physical_follower_commanded") is not False:
        raise ValueError(
            "Static pose bracket contract physical_follower_commanded must be false"
        )


def _validate_observation_envelope(
    observation: dict[str, Any],
    *,
    contract: dict[str, Any],
) -> None:
    expected_fields = {
        "schema_version",
        "observation_name",
        "evidence_mode",
        "contract_identity_sha256",
        "timing",
        "q_before",
        "cameras",
        "q_after",
        "operation_counts",
        "hardware_accessed",
        "physical_follower_commanded",
        "policy_inference_run",
        "fixture_only",
        "identity_sha256",
    }
    if set(observation) != expected_fields:
        raise ValueError("Static pose bracket observation fields are invalid")
    if observation.get("schema_version") != STATIC_POSE_BRACKET_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("Static pose bracket observation schema version is unsupported")
    if observation.get("evidence_mode") != "deterministic_fixture":
        raise ValueError("Static pose bracket observation must be deterministic fixture evidence")
    if observation.get("contract_identity_sha256") != contract.get("identity_sha256"):
        raise ValueError("Static pose bracket observation contract identity drifted")
    if observation.get("operation_counts") != EXPECTED_OPERATION_COUNTS:
        raise ValueError("Static pose bracket observation operation counts drifted")
    if observation.get("hardware_accessed") is not False:
        raise ValueError("Static pose bracket observation hardware_accessed must be false")
    if observation.get("physical_follower_commanded") is not False:
        raise ValueError("physical_follower_commanded must be false")
    if observation.get("policy_inference_run") is not False:
        raise ValueError("Static pose bracket observation policy_inference_run must be false")
    if observation.get("fixture_only") is not True:
        raise ValueError("Static pose bracket observation must remain fixture-only")


def _validate_positions(
    values: Any,
    *,
    contract: dict[str, Any],
    label: str,
) -> dict[str, int]:
    if not isinstance(values, list) or len(values) != 6:
        raise ValueError(f"{label} must contain exactly six positions")
    identities = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError(f"{label} position must be an object")
        if set(item) != {"joint_name", "servo_id", "raw_position"}:
            raise ValueError(f"{label} position fields are invalid")
        identities.append((item.get("joint_name"), item.get("servo_id")))
    if len(set(identities)) != len(identities):
        raise ValueError(f"{label} has duplicate joint identity")

    normalized = {}
    for item, joint in zip(values, contract["joints"], strict=True):
        if (
            item.get("joint_name") != joint["joint_name"]
            or item.get("servo_id") != joint["servo_id"]
        ):
            raise ValueError(f"{label} servo identity mismatch")
        raw = item.get("raw_position")
        if type(raw) is not int:
            raise ValueError(f"{label} {joint['joint_name']} raw_position must be an integer")
        if not joint["range_min"] <= raw <= joint["range_max"]:
            raise ValueError(
                f"{label} {joint['joint_name']} raw_position is outside calibrated range"
            )
        normalized[joint["joint_name"]] = raw
    return normalized


def _validate_timing(values: Any, *, contract: dict[str, Any]) -> dict[str, int]:
    fields = (
        "q_before_started_monotonic_ns",
        "q_before_finished_monotonic_ns",
        "camera_receive_started_monotonic_ns",
        "camera_receive_finished_monotonic_ns",
        "q_after_started_monotonic_ns",
        "q_after_finished_monotonic_ns",
    )
    if not isinstance(values, dict) or set(values) != set(fields):
        raise ValueError("Static pose bracket timing fields are invalid")
    timestamps = []
    for field in fields:
        value = values.get(field)
        if type(value) is not int or value < 0:
            raise ValueError(f"Static pose bracket {field} must be a nonnegative integer")
        timestamps.append(value)
    if not timestamps[0] < timestamps[1] or not timestamps[4] < timestamps[5]:
        raise ValueError("Static pose bracket position read timing is invalid")
    if not timestamps[1] < timestamps[2] < timestamps[3] < timestamps[4]:
        raise ValueError("Static pose bracket camera interval is not enclosed by position reads")
    duration = timestamps[5] - timestamps[0]
    maximum = contract["timing_contract"]["maximum_bracket_duration_ns"]
    if duration > maximum:
        raise ValueError("Static pose bracket duration exceeds contract")
    return {
        "bracket_started_monotonic_ns": timestamps[0],
        "bracket_finished_monotonic_ns": timestamps[5],
        "bracket_duration_ns": duration,
        "camera_receive_started_monotonic_ns": timestamps[2],
        "camera_receive_finished_monotonic_ns": timestamps[3],
        "camera_receive_duration_ns": timestamps[3] - timestamps[2],
        "maximum_bracket_duration_ns": maximum,
    }


def _validate_cameras(values: Any, *, contract: dict[str, Any]) -> None:
    if not isinstance(values, list) or len(values) != 2:
        raise ValueError("Static pose bracket must contain exactly two camera batches")
    all_hashes = []
    for observed, expected in zip(values, contract["cameras"], strict=True):
        if not isinstance(observed, dict) or set(observed) != {
            "camera_identity_sha256",
            "input_mode",
            "frames",
        }:
            raise ValueError("Static pose bracket camera fields are invalid")
        if observed.get("camera_identity_sha256") != expected["camera_identity_sha256"]:
            raise ValueError("Static pose bracket camera identity mismatch")
        if observed.get("input_mode") != expected["input_mode"]:
            raise ValueError("Static pose bracket camera input mode mismatch")
        frames = observed.get("frames")
        if not isinstance(frames, list) or len(frames) != expected["required_frame_count"]:
            raise ValueError("Static pose bracket camera frame count mismatch")
        for frame_index, frame in enumerate(frames):
            if not isinstance(frame, dict) or set(frame) != {
                "frame_index",
                "frame_sha256",
                "width",
                "height",
                "channels",
                "encoding",
            }:
                raise ValueError("Static pose bracket frame fields are invalid")
            if frame.get("frame_index") != frame_index:
                raise ValueError("Static pose bracket frame index mismatch")
            frame_hash = _require_sha256(
                frame.get("frame_sha256"),
                label="static pose bracket frame",
            )
            all_hashes.append(frame_hash)
            if (
                frame.get("width") != expected["input_mode"]["width"]
                or frame.get("height") != expected["input_mode"]["height"]
            ):
                raise ValueError("Static pose bracket frame dimensions mismatch")
            if (
                frame.get("channels") != expected["required_channels"]
                or frame.get("encoding") != expected["required_encoding"]
            ):
                raise ValueError("Static pose bracket frame encoding mismatch")
    if len(set(all_hashes)) != len(all_hashes):
        raise ValueError("Static pose bracket frame hashes must be unique")


def _normalize_position(raw_position: int, *, joint: dict[str, Any]) -> float:
    range_min = joint["range_min"]
    range_max = joint["range_max"]
    if joint["normalization_mode"] == "degrees":
        midpoint = (range_min + range_max) / 2
        value = (raw_position - midpoint) * 360 / 4095
    elif joint["normalization_mode"] == "range_0_100":
        value = (raw_position - range_min) / (range_max - range_min) * 100
    else:
        raise ValueError(f"Unsupported normalization mode for {joint['joint_name']}")
    if not math.isfinite(value):
        raise ValueError(f"Non-finite normalized coordinate for {joint['joint_name']}")
    return value


def _validate_input_mode(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} input mode must be an object")
    if set(value) != {"pixel_format", "width", "height", "framerate_fps"}:
        raise ValueError(f"{label} input mode fields are invalid")
    pixel_format = value.get("pixel_format")
    if not isinstance(pixel_format, str) or not pixel_format:
        raise ValueError(f"{label} pixel format must be nonblank")
    normalized = {"pixel_format": pixel_format}
    for field in ("width", "height", "framerate_fps"):
        item = value.get(field)
        if type(item) is not int or item <= 0:
            raise ValueError(f"{label} {field} must be a positive integer")
        normalized[field] = item
    return normalized


def _tracked_reference(
    *,
    path: Path,
    logical_path: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "logical_path": logical_path,
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }


def _require_sha256(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} sha256 is invalid")
    return value
