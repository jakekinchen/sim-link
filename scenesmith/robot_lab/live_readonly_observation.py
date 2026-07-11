"""Bounded live read-only SO-101 census and finite camera evidence."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import zlib

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Protocol

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.census_runtime_binding import (
    EXPECTED_READ_REGISTER_WIDTHS,
    EXPECTED_RUNTIME_SEMANTICS,
    verify_census_runtime_source_bindings,
)
from scenesmith.robot_lab.leader_arm_bridge import (
    DEFAULT_LEADER_PORT,
    KNOWN_PHYSICAL_FOLLOWER_PORT,
)
from scenesmith.robot_lab.readonly_servo_census import (
    InjectedReadOnlyBusAdapter,
    TransientReadError,
    build_live_census_contract,
    decode_readonly_servo_observations,
    run_readonly_census,
    verify_live_census_contract,
)


OPERATOR_PRESENCE_LEASE_SCHEMA_VERSION = "scenesmith.operator_presence_lease.v1"
LIVE_DISCOVERY_SCHEMA_VERSION = "scenesmith.live_readonly_discovery.v2"
LEGACY_LIVE_DISCOVERY_SCHEMA_VERSION = "scenesmith.live_readonly_discovery.v1"
LIVE_EXECUTION_CONTRACT_SCHEMA_VERSION = (
    "scenesmith.live_readonly_observation_contract.v3"
)
LEGACY_LIVE_EXECUTION_CONTRACT_SCHEMA_VERSION = (
    "scenesmith.live_readonly_observation_contract.v2"
)
LIVE_SERVO_RESULT_SCHEMA_VERSION = "scenesmith.live_readonly_servo_result.v2"
PRIVATE_OBSERVATION_SCHEMA_VERSION = "scenesmith.live_readonly_observation_private.v4"
REDACTED_MANIFEST_SCHEMA_VERSION = "scenesmith.live_readonly_observation_manifest.v4"
CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION = (
    "scenesmith.named_camera_failure_diagnostic.v3"
)
LEGACY_CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION = (
    "scenesmith.named_camera_failure_diagnostic.v2"
)
OLDEST_CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION = (
    "scenesmith.named_camera_failure_diagnostic.v1"
)
PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION = (
    "scenesmith.live_readonly_capture_failure_private.v4"
)
LEGACY_FULL_PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION = (
    "scenesmith.live_readonly_capture_failure_private.v3"
)
LEGACY_PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION = (
    "scenesmith.live_readonly_capture_failure_private.v2"
)
SERIAL_IDENTITY_HOLDER_SNAPSHOT_SCHEMA_VERSION = (
    "scenesmith.serial_identity_holder_snapshot.v1"
)

MAX_PRESENCE_LEASE_SECONDS = 600
MAX_EXECUTION_DURATION_SECONDS = 120
DEFAULT_FRAME_COUNT_PER_CAMERA = 2
CAMERA_READ_TIMEOUT_SECONDS = 5
CAMERA_FRAMERATE_FPS = 30
CAMERA_FRAMERATE_MATCH_TOLERANCE_FPS = 0.01
CAMERA_PIXEL_FORMAT_PRIORITY = ("uyvy422", "yuyv422", "nv12", "0rgb", "bgr0")
CAMERA_PIXEL_FORMAT_BY_FOURCC = {
    "2vuy": "uyvy422",
    "yuvs": "yuyv422",
    "420v": "nv12",
    "ARGB": "0rgb",
    "BGRA": "bgr0",
}
_SWIFT_CAMERA_MODE_METADATA_SOURCE = r'''
import AVFoundation
import CoreMedia
import Foundation

var cameras: [[String: Any]] = []
let discovery = AVCaptureDevice.DiscoverySession(
    deviceTypes: [.external],
    mediaType: .video,
    position: .unspecified
)
for device in discovery.devices {
    var formats: [[String: Any]] = []
    for format in device.formats {
        let description = format.formatDescription
        let dimensions = CMVideoFormatDescriptionGetDimensions(description)
        let subtype = CMFormatDescriptionGetMediaSubType(description)
        let bytes: [UInt8] = [
            UInt8((subtype >> 24) & 0xff),
            UInt8((subtype >> 16) & 0xff),
            UInt8((subtype >> 8) & 0xff),
            UInt8(subtype & 0xff),
        ]
        let fourcc = String(bytes: bytes, encoding: .macOSRoman) ?? ""
        for range in format.videoSupportedFrameRateRanges {
            formats.append([
                "fourcc": fourcc,
                "width": Int(dimensions.width),
                "height": Int(dimensions.height),
                "min_framerate_fps": range.minFrameRate,
                "max_framerate_fps": range.maxFrameRate,
            ])
        }
    }
    cameras.append([
        "name": device.localizedName,
        "unique_id": device.uniqueID,
        "model_id": device.modelID,
        "formats": formats,
    ])
}
let data = try JSONSerialization.data(withJSONObject: ["cameras": cameras])
print(String(data: data, encoding: .utf8)!)
'''
FFMPEG_EXECUTABLE = Path("/opt/homebrew/bin/ffmpeg")
MAX_PNG_FRAME_BYTES = 64 * 1024 * 1024
MAX_CAMERA_FAILURE_PREVIEW_BYTES = 2048
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DEFAULT_FOLLOWER_CALIBRATION_PATH = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)

_LEASE_OPERATIONS = [
    "usb_serial_camera_metadata_discovery",
    "follower_scalar_allowlisted_reads",
    "finite_camera_frame_capture",
]
_ALLOWED_EXECUTION_OPERATIONS = [
    "serial_connect_without_handshake",
    "scalar_allowlisted_register_read",
    "serial_disconnect_without_torque_change",
    "finite_camera_open_read_release",
]
_FORBIDDEN_EXECUTION_OPERATIONS = [
    "calibrate",
    "configure",
    "disable_torque",
    "enable_torque",
    "goal_position",
    "motion",
    "scan",
    "send_action",
    "setup_motor",
    "sync_write",
    "write",
    "write_register",
]
_EXPECTED_SERVO_NAMES = {
    item["joint_name"]: item["servo_id"]
    for item in EXPECTED_RUNTIME_SEMANTICS["follower_joint_map"]
}


class FiniteCamera(Protocol):
    def open(self) -> None: ...

    def read(self) -> dict[str, Any]: ...

    def release(self) -> None: ...


class NamedCameraCaptureError(RuntimeError):
    """Generic public failure carrying bounded, signed private diagnostics."""

    def __init__(self, diagnostic: dict[str, Any]):
        _verify_named_camera_failure_diagnostic(diagnostic)
        self.diagnostic = copy.deepcopy(diagnostic)
        super().__init__(
            f"Named camera capture failed at {diagnostic.get('stage', 'unknown')}"
        )


def build_operator_presence_lease(
    *,
    project_state: dict[str, Any],
    session_id: str,
    issued_at: str,
    valid_until: str,
) -> dict[str, Any]:
    issued = _parse_time(issued_at, label="presence lease issued_at")
    expires = _parse_time(valid_until, label="presence lease valid_until")
    validity_seconds = int((expires - issued).total_seconds())
    payload = {
        "schema_version": OPERATOR_PRESENCE_LEASE_SCHEMA_VERSION,
        "lease_name": "pi05_owner_present_live_readonly_lease",
        "session_id": require_nonblank(session_id, label="presence lease session_id"),
        "authority_id": project_state.get("owner_authority", {}).get("authority_id"),
        "presence_basis": "owner_message_present_for_day",
        "source_confirmation_recorded_at": project_state.get("owner_authority", {})
        .get("final_operator_confirmation", {})
        .get("recorded_at"),
        "scope": "live_read_only_census_and_camera_capture",
        "allowed_operations": list(_LEASE_OPERATIONS),
        "issued_at": issued_at,
        "valid_until": valid_until,
        "validity_seconds": validity_seconds,
    }
    signed = sign_payload(payload)
    verify_operator_presence_lease(
        signed,
        project_state=project_state,
        now=issued_at,
    )
    return signed


def verify_operator_presence_lease(
    payload: dict[str, Any],
    *,
    project_state: dict[str, Any],
    now: str,
) -> None:
    allowed_fields = {
        "schema_version",
        "lease_name",
        "session_id",
        "authority_id",
        "presence_basis",
        "source_confirmation_recorded_at",
        "scope",
        "allowed_operations",
        "issued_at",
        "valid_until",
        "validity_seconds",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Operator-presence lease fields are malformed")
    if payload.get("schema_version") != OPERATOR_PRESENCE_LEASE_SCHEMA_VERSION:
        raise ValueError("Unsupported operator-presence lease schema")
    verify_signed_payload(payload, label="Operator-presence lease")
    if payload.get("lease_name") != "pi05_owner_present_live_readonly_lease":
        raise ValueError("Operator-presence lease name is invalid")
    require_nonblank(payload.get("session_id"), label="presence lease session_id")
    owner_authority = project_state.get("owner_authority")
    if not isinstance(owner_authority, dict):
        raise ValueError("Project state owner authority is missing")
    confirmation = owner_authority.get("final_operator_confirmation")
    if (
        not isinstance(confirmation, dict)
        or confirmation.get("state") != "granted"
        or confirmation.get("no_second_prompt_required") is not True
    ):
        raise ValueError("Owner confirmation is not granted in project state")
    if project_state.get("tasks", {}).get("T16.5a", {}).get("state") != "verified":
        raise ValueError("T16.5a is not verified for a live read-only lease")
    if project_state.get("tasks", {}).get("T16.5b", {}).get("live_gate") != "open":
        raise ValueError("T16.5b live gate is not open")
    if payload.get("authority_id") != owner_authority.get("authority_id"):
        raise ValueError("Operator-presence lease authority drifted")
    if payload.get("presence_basis") != "owner_message_present_for_day":
        raise ValueError("Operator-presence lease basis is invalid")
    if payload.get("source_confirmation_recorded_at") != confirmation.get(
        "recorded_at"
    ):
        raise ValueError("Operator-presence lease source confirmation drifted")
    if payload.get("scope") != "live_read_only_census_and_camera_capture":
        raise ValueError("Operator-presence lease scope is invalid")
    if payload.get("allowed_operations") != _LEASE_OPERATIONS:
        raise ValueError("Operator-presence lease operations drifted")
    issued = _parse_time(payload.get("issued_at"), label="presence lease issued_at")
    expires = _parse_time(
        payload.get("valid_until"), label="presence lease valid_until"
    )
    observed = _parse_time(now, label="presence lease verification time")
    source_time = _parse_time(
        confirmation.get("recorded_at"),
        label="owner confirmation recorded_at",
    )
    hard_closeout = _parse_time(
        project_state.get("run_window", {}).get("hard_closeout"),
        label="run hard closeout",
    )
    validity_seconds = int((expires - issued).total_seconds())
    if issued < source_time:
        raise ValueError("Operator-presence lease predates owner confirmation")
    if validity_seconds <= 0 or validity_seconds > MAX_PRESENCE_LEASE_SECONDS:
        raise ValueError("Operator-presence lease duration is invalid")
    if payload.get("validity_seconds") != validity_seconds:
        raise ValueError("Operator-presence lease duration drifted")
    if expires > hard_closeout:
        raise ValueError("Operator-presence lease outlives the hard closeout")
    if observed < issued:
        raise ValueError("Operator-presence lease is not active yet")
    if observed > expires:
        raise ValueError("Operator-presence lease expired")


def build_live_discovery_snapshot(
    *,
    session_id: str,
    captured_at: str,
    serial_candidates: list[dict[str, Any]],
    avfoundation_devices: list[dict[str, Any]],
    system_cameras: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "schema_version": LIVE_DISCOVERY_SCHEMA_VERSION,
        "discovery_name": "pi05_live_readonly_metadata_discovery",
        "session_id": require_nonblank(session_id, label="discovery session_id"),
        "captured_at": captured_at,
        "serial_candidates": [
            _normalize_serial_candidate(candidate) for candidate in serial_candidates
        ],
        "avfoundation_devices": [
            _normalize_avfoundation_device(device) for device in avfoundation_devices
        ],
        "system_cameras": [
            _normalize_system_camera(camera) for camera in system_cameras
        ],
        "serial_ports_opened": 0,
        "cameras_opened": 0,
    }
    signed = sign_payload(payload)
    _verify_discovery_snapshot(signed)
    return signed


def resolve_follower_identity(discovery: dict[str, Any]) -> dict[str, Any]:
    _verify_discovery_snapshot(discovery)
    matches = [
        candidate
        for candidate in discovery["serial_candidates"]
        if KNOWN_PHYSICAL_FOLLOWER_PORT in {candidate["device"], *candidate["aliases"]}
    ]
    if len(matches) != 1:
        raise ValueError("Discovery must resolve exactly one pinned follower candidate")
    follower = matches[0]
    # macOS may omit the descriptive manufacturer label even when the stable
    # VID/PID/serial/path/location/HWID identity is complete. Keep that label in
    # the signed discovery record, but do not make it an authority prerequisite.
    for field in ("serial_number", "product", "location", "hwid"):
        require_nonblank(follower.get(field), label=f"follower discovery {field}")
    for field in ("vid", "pid"):
        value = follower.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 0xFFFF
        ):
            raise ValueError(f"Follower discovery {field} is incomplete")
    follower_paths = {follower["device"], *follower["aliases"]}
    forbidden_paths = {DEFAULT_LEADER_PORT, _paired_tty_alias(DEFAULT_LEADER_PORT)}
    if follower_paths & forbidden_paths:
        raise ValueError("Follower discovery collides with a leader role alias")
    leader_candidates = [
        candidate
        for candidate in discovery["serial_candidates"]
        if forbidden_paths & {candidate["device"], *candidate["aliases"]}
    ]
    if any(
        candidate.get("serial_number") == follower["serial_number"]
        for candidate in leader_candidates
    ):
        raise ValueError("Follower and leader role identities share one USB serial")
    aliases = sorted(
        (follower_paths - {KNOWN_PHYSICAL_FOLLOWER_PORT})
        | {_paired_tty_alias(KNOWN_PHYSICAL_FOLLOWER_PORT)}
    )
    return {
        "device_role": "so101_follower_observation_target",
        "usb": {
            "vendor_id_hex": f"{follower['vid']:04x}",
            "product_id_hex": f"{follower['pid']:04x}",
            "serial_number": follower["serial_number"],
            "canonical_path": KNOWN_PHYSICAL_FOLLOWER_PORT,
            "observed_aliases": aliases,
        },
        "bus": {
            "protocol_family": "feetech",
            "protocol_version": EXPECTED_RUNTIME_SEMANTICS["sts3215_protocol_version"],
            "baudrate": EXPECTED_RUNTIME_SEMANTICS["default_baudrate"],
        },
    }


def verify_discovery_stability(
    expected: dict[str, Any],
    observed: dict[str, Any],
) -> None:
    _verify_discovery_snapshot(expected)
    _verify_discovery_snapshot(observed)
    if expected["session_id"] != observed["session_id"]:
        raise ValueError("Discovery stability session identity drifted")
    if expected["serial_candidates"] != observed["serial_candidates"]:
        raise ValueError("Discovery stability check detected serial_candidates drift")
    if _stable_camera_discovery_identity(expected) != _stable_camera_discovery_identity(
        observed
    ):
        raise ValueError(
            "Discovery stability check detected stable camera identity drift"
        )


def parse_avfoundation_video_devices(output: str) -> list[dict[str, Any]]:
    if not isinstance(output, str):
        raise ValueError("AVFoundation discovery output must be text")
    in_video_section = False
    devices: list[dict[str, Any]] = []
    for line in output.splitlines():
        if "AVFoundation video devices:" in line:
            in_video_section = True
            continue
        if "AVFoundation audio devices:" in line:
            in_video_section = False
            continue
        if not in_video_section:
            continue
        match = re.search(r"\[(\d+)\]\s+(.+?)\s*$", line)
        if match:
            devices.append(
                {
                    "index": int(match.group(1)),
                    "name": match.group(2),
                }
            )
    return [_normalize_avfoundation_device(device) for device in devices]


def parse_system_camera_devices(
    payload: dict[str, Any],
    *,
    supported_modes_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("System camera discovery payload must be an object")
    observed: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if "_name" in value and "spcamera_unique-id" in value:
                observed.append(
                    {
                        "name": value.get("_name"),
                        "unique_id": value.get("spcamera_unique-id"),
                        "model_id": value.get("spcamera_model-id"),
                    }
                )
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload.get("SPCameraDataType", payload))
    supported_modes = parse_system_camera_supported_modes(supported_modes_payload)
    normalized = []
    for camera in observed:
        key = (camera["name"], camera["unique_id"], camera["model_id"])
        normalized.append(
            _normalize_system_camera(
                {
                    **camera,
                    "supported_modes": supported_modes.get(key, []),
                }
            )
        )
    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for camera in normalized:
        key = (camera["name"], camera["unique_id"], camera["model_id"])
        if key in unique:
            raise ValueError("System camera identity is duplicated")
        unique[key] = camera
    if set(supported_modes) != set(unique):
        raise ValueError("System camera supported-mode identities do not match")
    return list(unique.values())


def parse_system_camera_supported_modes(
    payload: dict[str, Any],
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    if not isinstance(payload, dict) or set(payload) != {"cameras"}:
        raise ValueError("System camera supported-mode payload is malformed")
    cameras = payload.get("cameras")
    if not isinstance(cameras, list) or not cameras:
        raise ValueError("System camera supported-mode list is empty")
    result: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for camera in cameras:
        if not isinstance(camera, dict) or set(camera) != {
            "name",
            "unique_id",
            "model_id",
            "formats",
        }:
            raise ValueError("System camera supported-mode record is malformed")
        key = (
            require_nonblank(camera.get("name"), label="mode camera name"),
            require_nonblank(camera.get("unique_id"), label="mode camera unique_id"),
            require_nonblank(camera.get("model_id"), label="mode camera model_id"),
        )
        if key in result:
            raise ValueError("System camera supported-mode identity is duplicated")
        formats = camera.get("formats")
        if not isinstance(formats, list) or not formats:
            raise ValueError("System camera supported modes are empty")
        normalized = []
        for item in formats:
            if not isinstance(item, dict) or set(item) != {
                "fourcc",
                "width",
                "height",
                "min_framerate_fps",
                "max_framerate_fps",
            }:
                raise ValueError("System camera format metadata is malformed")
            pixel_format = CAMERA_PIXEL_FORMAT_BY_FOURCC.get(item.get("fourcc"))
            if pixel_format is None:
                continue
            normalized.append(
                _normalize_camera_supported_mode(
                    {
                        "pixel_format": pixel_format,
                        "width": item["width"],
                        "height": item["height"],
                        "min_framerate_fps": item["min_framerate_fps"],
                        "max_framerate_fps": item["max_framerate_fps"],
                    }
                )
            )
        if not normalized:
            raise ValueError("System camera has no supported reviewed pixel format")
        ordered = sorted(normalized, key=_camera_supported_mode_sort_key)
        if len({_camera_supported_mode_key(item) for item in ordered}) != len(ordered):
            raise ValueError("System camera supported modes contain duplicates")
        result[key] = ordered
    return result


def resolve_camera_selection(
    discovery: dict[str, Any],
    camera_indexes: list[int],
) -> list[dict[str, Any]]:
    _verify_discovery_snapshot(discovery)
    if (
        not isinstance(camera_indexes, list)
        or not camera_indexes
        or len(camera_indexes) > 2
        or any(
            isinstance(index, bool) or not isinstance(index, int)
            for index in camera_indexes
        )
        or len(set(camera_indexes)) != len(camera_indexes)
    ):
        raise ValueError("Camera selection requires one or two unique integer indexes")
    av_by_index = {
        device["index"]: device for device in discovery["avfoundation_devices"]
    }
    _stable_camera_discovery_identity(discovery)
    result: list[dict[str, Any]] = []
    for index in sorted(camera_indexes):
        av_device = av_by_index.get(index)
        if av_device is None:
            raise ValueError(f"Selected AVFoundation camera index is missing: {index}")
        if (
            sum(
                device["name"] == av_device["name"]
                for device in discovery["avfoundation_devices"]
            )
            != 1
        ):
            raise ValueError(
                f"Selected AVFoundation camera name is ambiguous: {av_device['name']}"
            )
        matches = [
            camera
            for camera in discovery["system_cameras"]
            if camera["name"] == av_device["name"]
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Camera identity must map exactly one system device: {av_device['name']}"
            )
        result.append(
            {
                "index": index,
                "name": av_device["name"],
                "unique_id": matches[0]["unique_id"],
                "model_id": matches[0]["model_id"],
                "input_mode": select_camera_input_mode(matches[0]),
            }
        )
    if len({camera["unique_id"] for camera in result}) != len(result):
        raise ValueError("Selected camera identities are ambiguous")
    return result


def build_live_execution_contract(
    *,
    project_state: dict[str, Any],
    presence_lease: dict[str, Any],
    discovery: dict[str, Any],
    camera_indexes: list[int],
    calibration_path: Path,
    issued_at: str,
    expires_at: str,
    frame_count_per_camera: int = DEFAULT_FRAME_COUNT_PER_CAMERA,
) -> dict[str, Any]:
    verify_operator_presence_lease(
        presence_lease,
        project_state=project_state,
        now=issued_at,
    )
    _verify_discovery_snapshot(discovery)
    if discovery.get("schema_version") != LIVE_DISCOVERY_SCHEMA_VERSION:
        raise ValueError("New live execution requires supported-mode discovery v2")
    if presence_lease["session_id"] != discovery["session_id"]:
        raise ValueError("Lease and discovery session identities differ")
    follower_identity = resolve_follower_identity(discovery)
    cameras = resolve_camera_selection(discovery, camera_indexes)
    calibration = _calibration_reference(calibration_path)
    live_census_contract = build_live_census_contract(
        observed_device_identity=follower_identity,
        session_id=presence_lease["session_id"],
        presence_lease_identity_sha256=presence_lease["identity_sha256"],
        discovery_identity_sha256=discovery["identity_sha256"],
        calibration_file_sha256=calibration["sha256"],
        issued_at=issued_at,
        expires_at=expires_at,
    )
    payload = {
        "schema_version": LIVE_EXECUTION_CONTRACT_SCHEMA_VERSION,
        "contract_name": "pi05_live_readonly_census_and_observation",
        "qualification_scope": "physical_observation",
        "session_id": presence_lease["session_id"],
        "presence_lease": copy.deepcopy(presence_lease),
        "presence_lease_identity_sha256": presence_lease["identity_sha256"],
        "discovery": copy.deepcopy(discovery),
        "discovery_identity_sha256": discovery["identity_sha256"],
        "calibration": calibration,
        "cameras": cameras,
        "frame_count_per_camera": frame_count_per_camera,
        "camera_framerate_fps": CAMERA_FRAMERATE_FPS,
        "camera_read_timeout_seconds": CAMERA_READ_TIMEOUT_SECONDS,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "max_duration_seconds": MAX_EXECUTION_DURATION_SECONDS,
        "allowed_operations": list(_ALLOWED_EXECUTION_OPERATIONS),
        "forbidden_operations": list(_FORBIDDEN_EXECUTION_OPERATIONS),
        "live_census_contract": live_census_contract,
        "physical_follower_commanded": False,
    }
    signed = sign_payload(payload)
    verify_live_execution_contract(
        signed,
        project_state=project_state,
        now=issued_at,
    )
    return signed


def verify_live_execution_contract(
    payload: dict[str, Any],
    *,
    project_state: dict[str, Any],
    now: str,
) -> None:
    allowed_fields = {
        "schema_version",
        "contract_name",
        "qualification_scope",
        "session_id",
        "presence_lease",
        "presence_lease_identity_sha256",
        "discovery",
        "discovery_identity_sha256",
        "calibration",
        "cameras",
        "frame_count_per_camera",
        "camera_framerate_fps",
        "camera_read_timeout_seconds",
        "issued_at",
        "expires_at",
        "max_duration_seconds",
        "allowed_operations",
        "forbidden_operations",
        "live_census_contract",
        "physical_follower_commanded",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Live execution contract fields are malformed")
    if payload.get("schema_version") != LIVE_EXECUTION_CONTRACT_SCHEMA_VERSION:
        raise ValueError("Unsupported live execution contract schema")
    verify_signed_payload(payload, label="Live execution contract")
    if payload.get("contract_name") != "pi05_live_readonly_census_and_observation":
        raise ValueError("Live execution contract name is invalid")
    if payload.get("qualification_scope") != "physical_observation":
        raise ValueError("Live execution contract scope is invalid")
    lease = payload.get("presence_lease")
    verify_operator_presence_lease(lease, project_state=project_state, now=now)
    if payload.get("presence_lease_identity_sha256") != lease["identity_sha256"]:
        raise ValueError("Live execution contract lease linkage drifted")
    discovery = payload.get("discovery")
    _verify_discovery_snapshot(discovery)
    if payload.get("discovery_identity_sha256") != discovery["identity_sha256"]:
        raise ValueError("Live execution contract discovery linkage drifted")
    if (
        payload.get("session_id") != lease["session_id"]
        or payload.get("session_id") != discovery["session_id"]
    ):
        raise ValueError("Live execution contract session linkage drifted")
    if (
        payload.get("issued_at") != lease["issued_at"]
        or payload.get("expires_at") != lease["valid_until"]
    ):
        raise ValueError(
            "Live execution contract validity must equal the presence lease"
        )
    if payload.get("max_duration_seconds") != MAX_EXECUTION_DURATION_SECONDS:
        raise ValueError("Live execution duration bound drifted")
    if payload.get("camera_read_timeout_seconds") != CAMERA_READ_TIMEOUT_SECONDS:
        raise ValueError("Live execution camera read timeout drifted")
    framerate = payload.get("camera_framerate_fps")
    if (
        isinstance(framerate, bool)
        or not isinstance(framerate, int)
        or framerate != CAMERA_FRAMERATE_FPS
    ):
        raise ValueError("Live execution camera framerate drifted")
    frame_count = payload.get("frame_count_per_camera")
    if (
        isinstance(frame_count, bool)
        or not isinstance(frame_count, int)
        or not 1 <= frame_count <= 3
    ):
        raise ValueError("Live execution camera frame count is invalid")
    if payload.get("cameras") != resolve_camera_selection(
        discovery,
        [camera.get("index") for camera in payload.get("cameras", [])],
    ):
        raise ValueError("Live execution camera identity drifted")
    calibration = payload.get("calibration")
    if calibration != _calibration_reference(Path(calibration.get("path", ""))):
        raise ValueError("Live execution calibration identity drifted")
    if payload.get("allowed_operations") != _ALLOWED_EXECUTION_OPERATIONS:
        raise ValueError("Live execution allowed operations drifted")
    if payload.get("forbidden_operations") != _FORBIDDEN_EXECUTION_OPERATIONS:
        raise ValueError("Live execution forbidden operations drifted")
    if payload.get("physical_follower_commanded") is not False:
        raise ValueError("Live execution contract cannot command the follower")
    census_contract = payload.get("live_census_contract")
    verify_live_census_contract(census_contract)
    if census_contract["session_id"] != payload["session_id"]:
        raise ValueError("Live census session linkage drifted")
    if (
        census_contract["presence_lease_identity_sha256"]
        != payload["presence_lease_identity_sha256"]
        or census_contract["discovery_identity_sha256"]
        != payload["discovery_identity_sha256"]
        or census_contract["calibration_file_sha256"] != calibration["sha256"]
    ):
        raise ValueError("Live census evidence linkage drifted")
    expected_identity = resolve_follower_identity(discovery)
    target = census_contract["target_device_identity"]
    observed_from_target = {
        "device_role": target["device_role"],
        "usb": {
            "vendor_id_hex": target["usb"]["vendor_id_hex"],
            "product_id_hex": target["usb"]["product_id_hex"],
            "serial_number": target["usb"]["serial_number"],
            "canonical_path": target["usb"]["canonical_path"],
            "observed_aliases": target["usb"]["allowed_aliases"],
        },
        "bus": target["bus"],
    }
    if observed_from_target != expected_identity:
        raise ValueError("Live census follower identity drifted from discovery")


class AuditedReadOnlyBusBackend:
    """Expose only the exact reviewed raw-bus calls and retain an operation trace."""

    def __init__(self, *, bus: Any, monotonic_ns: Callable[[], int]):
        self._bus = bus
        self._monotonic_ns = monotonic_ns
        self._events: list[dict[str, Any]] = []

    def connect(self, *, handshake: bool) -> None:
        if handshake is not False:
            raise ValueError("Live read-only bus handshake must be false")
        event = self._event("connect", {"handshake": False})
        try:
            self._bus.connect(handshake=False)
        except BaseException as exc:
            event["outcome"] = "error"
            event["error_type"] = type(exc).__name__
            raise
        event["outcome"] = "success"

    def read(
        self,
        register: str,
        motor: str,
        *,
        normalize: bool,
        num_retry: int,
    ) -> int:
        if register not in EXPECTED_READ_REGISTER_WIDTHS:
            raise ValueError(f"Live bus register is not allowlisted: {register}")
        if motor not in _EXPECTED_SERVO_NAMES:
            raise ValueError(f"Live bus motor name is not allowlisted: {motor}")
        if normalize is not False or num_retry != 0:
            raise ValueError("Live bus reads require normalize=false and num_retry=0")
        event = self._event(
            "read",
            {
                "register": register,
                "motor": motor,
                "normalize": False,
                "num_retry": 0,
            },
        )
        try:
            value = self._bus.read(
                register,
                motor,
                normalize=False,
                num_retry=0,
            )
        except ConnectionError as exc:
            event["outcome"] = "transient_error"
            event["error_type"] = type(exc).__name__
            raise TransientReadError(str(exc)) from exc
        except BaseException as exc:
            event["outcome"] = "error"
            event["error_type"] = type(exc).__name__
            raise
        event["outcome"] = "success"
        event["raw_value"] = value
        return value

    def disconnect(self, *, disable_torque: bool) -> None:
        if disable_torque is not False:
            raise ValueError("Live read-only bus disconnect must not disable torque")
        event = self._event("disconnect", {"disable_torque": False})
        try:
            self._bus.disconnect(disable_torque=False)
        except BaseException as exc:
            event["outcome"] = "error"
            event["error_type"] = type(exc).__name__
            raise
        event["outcome"] = "success"

    def trace(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._events)

    def _event(self, operation: str, fields: dict[str, Any]) -> dict[str, Any]:
        event = {
            "sequence": len(self._events),
            "operation": operation,
            "monotonic_ns": self._monotonic_ns(),
            **fields,
        }
        self._events.append(event)
        return event


def execute_live_servo_census(
    execution_contract: dict[str, Any],
    *,
    project_state: dict[str, Any],
    now: str,
    bus_factory: Callable[[dict[str, Any]], Any],
    monotonic_ns: Callable[[], int],
) -> dict[str, Any]:
    verify_live_execution_contract(
        execution_contract,
        project_state=project_state,
        now=now,
    )
    census_contract = execution_contract["live_census_contract"]
    captured: dict[str, Any] = {}

    def transport_factory() -> InjectedReadOnlyBusAdapter:
        bus = bus_factory(census_contract)
        backend = AuditedReadOnlyBusBackend(bus=bus, monotonic_ns=monotonic_ns)
        captured["backend"] = backend
        target = census_contract["target_device_identity"]
        observed_identity = {
            "device_role": target["device_role"],
            "usb": {
                "vendor_id_hex": target["usb"]["vendor_id_hex"],
                "product_id_hex": target["usb"]["product_id_hex"],
                "serial_number": target["usb"]["serial_number"],
                "canonical_path": target["usb"]["canonical_path"],
                "observed_aliases": target["usb"]["allowed_aliases"],
            },
            "bus": target["bus"],
        }
        return InjectedReadOnlyBusAdapter(
            backend=backend,
            device_identity=observed_identity,
            servo_names={
                servo["servo_id"]: servo["joint_name"]
                for servo in census_contract["expected_servos"]
            },
        )

    started = monotonic_ns()
    run = run_readonly_census(census_contract, transport_factory)
    finished = monotonic_ns()
    backend = captured.get("backend")
    if backend is None:
        raise RuntimeError("Live census backend was not constructed")
    if run["hardware_opened"] is not True:
        raise ValueError("Live census did not conservatively record hardware open")
    result = sign_payload(
        {
            "schema_version": LIVE_SERVO_RESULT_SCHEMA_VERSION,
            "result_name": "pi05_live_readonly_servo_census",
            "qualification_scope": "physical_observation",
            "evidence_mode": "live_physical_read_only",
            "proof_label": "live_read_only_census_observed",
            "execution_contract_identity_sha256": execution_contract["identity_sha256"],
            "census_contract_identity_sha256": census_contract["identity_sha256"],
            "observation_started_monotonic_ns": started,
            "observation_finished_monotonic_ns": finished,
            "transport_trace": backend.trace(),
            **run,
        }
    )
    _verify_live_servo_result(result, execution_contract=execution_contract)
    return result


def capture_finite_camera_frames(
    execution_contract: dict[str, Any],
    *,
    project_state: dict[str, Any],
    now: str,
    camera_factory: Callable[[dict[str, Any]], FiniteCamera],
    monotonic_ns: Callable[[], int],
    wall_time: Callable[[], str],
) -> list[dict[str, Any]]:
    verify_live_execution_contract(
        execution_contract,
        project_state=project_state,
        now=now,
    )
    frames: list[dict[str, Any]] = []
    previous_interval: tuple[int, int] | None = None
    for camera in execution_contract["cameras"]:
        first_camera_frame = len(frames)
        instance: FiniteCamera | None = None
        primary_error: BaseException | None = None
        release_error: BaseException | None = None
        try:
            instance = camera_factory(copy.deepcopy(camera))
            instance.open()
            for frame_index in range(execution_contract["frame_count_per_camera"]):
                call_started = monotonic_ns()
                frame = instance.read()
                call_finished = monotonic_ns()
                started = frame.get(
                    "receive_started_monotonic_ns",
                    call_started,
                )
                finished = frame.get(
                    "receive_finished_monotonic_ns",
                    call_finished,
                )
                if (
                    isinstance(started, bool)
                    or not isinstance(started, int)
                    or isinstance(finished, bool)
                    or not isinstance(finished, int)
                    or finished <= started
                    or (
                        previous_interval is not None
                        and (started, finished) < previous_interval
                    )
                ):
                    raise ValueError("Camera timestamps regressed")
                previous_interval = (started, finished)
                frame_bytes = (
                    frame.get("frame_bytes") if isinstance(frame, dict) else None
                )
                if not isinstance(frame_bytes, bytes) or not frame_bytes:
                    raise ValueError("Camera frame bytes are missing")
                encoding = frame.get("encoding")
                if encoding not in {"png", "jpeg"}:
                    raise ValueError("Camera frame encoding is unsupported")
                dimensions = [
                    frame.get("width"),
                    frame.get("height"),
                    frame.get("channels"),
                ]
                if any(
                    isinstance(value, bool) or not isinstance(value, int) or value <= 0
                    for value in dimensions
                ):
                    raise ValueError("Camera frame dimensions are invalid")
                frames.append(
                    {
                        "camera": copy.deepcopy(camera),
                        "frame_index": frame_index,
                        "host_wall_time": _validated_wall_time(wall_time()),
                        "receive_started_monotonic_ns": started,
                        "receive_finished_monotonic_ns": finished,
                        "encoding": encoding,
                        "width": dimensions[0],
                        "height": dimensions[1],
                        "channels": dimensions[2],
                        "frame_sha256": hashlib.sha256(frame_bytes).hexdigest(),
                        "private_relative_path": (
                            f"camera-{camera['index']}-frame-{frame_index}.{encoding}"
                        ),
                        "frame_bytes": frame_bytes,
                    }
                )
        except BaseException as exc:
            primary_error = exc
        finally:
            if instance is not None:
                try:
                    instance.release()
                except BaseException as exc:
                    release_error = exc
        diagnostic_error: BaseException | None = None
        if primary_error is not None and instance is not None:
            diagnostic_method = getattr(instance, "failure_diagnostic", None)
            if callable(diagnostic_method):
                original_primary = primary_error
                try:
                    diagnostic = diagnostic_method(
                        primary_error=original_primary,
                        cleanup_error=release_error,
                    )
                    wrapped = NamedCameraCaptureError(diagnostic)
                    wrapped.__cause__ = original_primary
                    primary_error = wrapped
                except BaseException as exc:
                    diagnostic_error = exc
        grouped_errors = [
            error
            for error in (primary_error, release_error, diagnostic_error)
            if error is not None
        ]
        if len(grouped_errors) > 1:
            raise BaseExceptionGroup(
                "Camera capture, cleanup, or diagnostic construction failed",
                grouped_errors,
            )
        if primary_error is not None:
            raise primary_error
        if release_error is not None:
            raise release_error
        if diagnostic_error is not None:
            raise diagnostic_error
        audit_method = getattr(instance, "audit", None)
        if callable(audit_method):
            backend_audit = audit_method()
        else:
            backend_audit = _injected_camera_backend_audit(
                camera=camera,
                frame_count=execution_contract["frame_count_per_camera"],
                framerate_fps=execution_contract["camera_framerate_fps"],
            )
        _verify_camera_backend_audit(
            backend_audit,
            camera=camera,
            expected_frame_count=execution_contract["frame_count_per_camera"],
            expected_framerate_fps=execution_contract["camera_framerate_fps"],
        )
        for frame in frames[first_camera_frame:]:
            frame["camera_backend_audit"] = copy.deepcopy(backend_audit)
    return frames


def build_private_capture_failure_evidence(
    *,
    execution_contract: dict[str, Any],
    servo_result: dict[str, Any],
    error: BaseException,
    pre_open_discovery: dict[str, Any],
    pre_open_serial_holder_snapshot: dict[str, Any],
    post_close_serial_holder_snapshot: dict[str, Any],
    failed_at: str,
    elapsed_seconds: float,
) -> dict[str, Any]:
    verify_signed_payload(execution_contract, label="Live execution contract")
    _verify_live_servo_result(servo_result, execution_contract=execution_contract)
    verify_discovery_stability(execution_contract["discovery"], pre_open_discovery)
    require_no_serial_identity_holders(pre_open_serial_holder_snapshot)
    require_no_serial_identity_holders(post_close_serial_holder_snapshot)
    verify_serial_identity_holder_stability(
        pre_open_serial_holder_snapshot,
        post_close_serial_holder_snapshot,
    )
    diagnostic = _extract_named_camera_failure_diagnostic(error)
    verify_signed_payload(diagnostic, label="Named camera failure diagnostic")
    if (
        isinstance(elapsed_seconds, bool)
        or not isinstance(elapsed_seconds, (int, float))
        or not math.isfinite(float(elapsed_seconds))
        or elapsed_seconds < 0
    ):
        raise ValueError("Private capture failure elapsed time is invalid")
    payload = {
        "schema_version": PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION,
        "evidence_name": "pi05_live_readonly_private_capture_failure",
        "qualification_scope": "physical_observation",
        "evidence_mode": "local_private_rejected_physical_read_only_attempt",
        "status": "rejected",
        "session_id": execution_contract["session_id"],
        "execution_contract": copy.deepcopy(execution_contract),
        "execution_contract_identity_sha256": execution_contract["identity_sha256"],
        "presence_lease_identity_sha256": execution_contract[
            "presence_lease_identity_sha256"
        ],
        "discovery_identity_sha256": execution_contract[
            "discovery_identity_sha256"
        ],
        "pre_open_discovery_identity_sha256": pre_open_discovery["identity_sha256"],
        "servo_result": copy.deepcopy(servo_result),
        "servo_result_identity_sha256": servo_result["identity_sha256"],
        "target_device_identity_sha256": _sha256_payload(
            servo_result["target_device_identity"]
        ),
        "operation_counts": copy.deepcopy(servo_result["operation_counts"]),
        "camera_failure_diagnostic": copy.deepcopy(diagnostic),
        "camera_failure_diagnostic_identity_sha256": diagnostic["identity_sha256"],
        "error_types": _flatten_error_types(error),
        "serial_identity_holder_snapshots": {
            "pre_open": copy.deepcopy(pre_open_serial_holder_snapshot),
            "post_close": copy.deepcopy(post_close_serial_holder_snapshot),
        },
        "serial_identity_holder_counts": {
            "pre_open": pre_open_serial_holder_snapshot[
                "deduplicated_holder_count"
            ],
            "post_close": post_close_serial_holder_snapshot[
                "deduplicated_holder_count"
            ],
        },
        "serial_identity_holder_snapshot_sha256": {
            "pre_open": pre_open_serial_holder_snapshot["identity_sha256"],
            "post_close": post_close_serial_holder_snapshot["identity_sha256"],
        },
        "failed_at": _validated_wall_time(failed_at),
        "elapsed_seconds": float(elapsed_seconds),
        "private_success_bundle_written": False,
        "tracked_success_manifest_written": False,
        "proof_labels": [],
        "hardware_opened": True,
        "physical_follower_commanded": False,
    }
    signed = sign_payload(payload)
    verify_private_capture_failure_evidence(signed)
    return signed


def write_private_capture_failure_record(
    *,
    output_directory: Path,
    failure_evidence: dict[str, Any],
) -> dict[str, Any]:
    verify_private_capture_failure_evidence(failure_evidence)
    if output_directory.exists():
        raise ValueError(
            "Private capture failure output directory must be new and immutable"
        )
    temporary_directory = output_directory.with_name(
        output_directory.name + ".tmp"
    )
    if temporary_directory.exists():
        raise ValueError("Private capture failure temporary directory already exists")
    try:
        temporary_directory.mkdir(parents=True, exist_ok=False)
        temporary_path = temporary_directory / "private_capture_failure.json"
        dump_canonical_json(temporary_path, failure_evidence)
        reference = {
            "filename": temporary_path.name,
            "sha256": hashlib.sha256(temporary_path.read_bytes()).hexdigest(),
            "size_bytes": temporary_path.stat().st_size,
            "identity_sha256": failure_evidence["identity_sha256"],
        }
        temporary_directory.replace(output_directory)
    except BaseException:
        if temporary_directory.exists():
            shutil.rmtree(temporary_directory, ignore_errors=True)
        raise
    return reference


def verify_private_capture_failure_evidence(payload: dict[str, Any]) -> None:
    failure_schema = (
        payload.get("schema_version") if isinstance(payload, dict) else None
    )
    allowed_fields = {
        "schema_version",
        "evidence_name",
        "qualification_scope",
        "evidence_mode",
        "status",
        "session_id",
        "execution_contract_identity_sha256",
        "presence_lease_identity_sha256",
        "discovery_identity_sha256",
        "pre_open_discovery_identity_sha256",
        "servo_result_identity_sha256",
        "target_device_identity_sha256",
        "operation_counts",
        "camera_failure_diagnostic",
        "camera_failure_diagnostic_identity_sha256",
        "error_types",
        "serial_identity_holder_snapshots",
        "serial_identity_holder_counts",
        "serial_identity_holder_snapshot_sha256",
        "failed_at",
        "elapsed_seconds",
        "private_success_bundle_written",
        "tracked_success_manifest_written",
        "proof_labels",
        "hardware_opened",
        "physical_follower_commanded",
        "identity_sha256",
    }
    full_failure_schemas = {
        PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION,
        LEGACY_FULL_PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION,
    }
    if failure_schema in full_failure_schemas:
        allowed_fields.update({"execution_contract", "servo_result"})
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Private capture failure evidence fields are malformed")
    if failure_schema not in {
        PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION,
        LEGACY_FULL_PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION,
        LEGACY_PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION,
    }:
        raise ValueError("Unsupported private capture failure evidence schema")
    verify_signed_payload(payload, label="Private capture failure evidence")
    if (
        payload.get("evidence_name")
        != "pi05_live_readonly_private_capture_failure"
        or payload.get("qualification_scope") != "physical_observation"
        or payload.get("evidence_mode")
        != "local_private_rejected_physical_read_only_attempt"
        or payload.get("status") != "rejected"
    ):
        raise ValueError("Private capture failure evidence classification drifted")
    for field in (
        "session_id",
        "execution_contract_identity_sha256",
        "presence_lease_identity_sha256",
        "discovery_identity_sha256",
        "pre_open_discovery_identity_sha256",
        "servo_result_identity_sha256",
        "target_device_identity_sha256",
    ):
        require_nonblank(payload.get(field), label=f"capture failure {field}")
    diagnostic = payload.get("camera_failure_diagnostic")
    if not isinstance(diagnostic, dict):
        raise ValueError("Private capture failure diagnostic is missing")
    _verify_named_camera_failure_diagnostic(diagnostic)
    if (
        payload.get("camera_failure_diagnostic_identity_sha256")
        != diagnostic.get("identity_sha256")
    ):
        raise ValueError("Private capture failure diagnostic identity drifted")
    if failure_schema in full_failure_schemas:
        execution_contract = payload.get("execution_contract")
        if not isinstance(execution_contract, dict):
            raise ValueError("Private capture failure execution contract is missing")
        verify_signed_payload(
            execution_contract,
            label="Private capture failure execution contract",
        )
        expected_contract_schema = (
            LIVE_EXECUTION_CONTRACT_SCHEMA_VERSION
            if failure_schema == PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION
            else LEGACY_LIVE_EXECUTION_CONTRACT_SCHEMA_VERSION
        )
        if (
            execution_contract.get("schema_version") != expected_contract_schema
            or payload.get("execution_contract_identity_sha256")
            != execution_contract.get("identity_sha256")
            or payload.get("session_id") != execution_contract.get("session_id")
            or payload.get("presence_lease_identity_sha256")
            != execution_contract.get("presence_lease_identity_sha256")
            or payload.get("discovery_identity_sha256")
            != execution_contract.get("discovery_identity_sha256")
        ):
            raise ValueError("Private capture failure execution contract drifted")
        if failure_schema == PRIVATE_CAPTURE_FAILURE_SCHEMA_VERSION:
            embedded_discovery = execution_contract.get("discovery")
            _verify_discovery_snapshot(embedded_discovery)
            expected_cameras = resolve_camera_selection(
                embedded_discovery,
                [
                    camera.get("index")
                    for camera in execution_contract.get("cameras", [])
                ],
            )
            if execution_contract.get("cameras") != expected_cameras:
                raise ValueError(
                    "Private capture failure contract camera modes drifted"
                )
        servo_result = payload.get("servo_result")
        if not isinstance(servo_result, dict):
            raise ValueError("Private capture failure servo result is missing")
        _verify_live_servo_result(
            servo_result,
            execution_contract=execution_contract,
        )
        if (
            payload.get("servo_result_identity_sha256")
            != servo_result.get("identity_sha256")
            or payload.get("target_device_identity_sha256")
            != _sha256_payload(servo_result.get("target_device_identity"))
            or payload.get("operation_counts") != servo_result.get("operation_counts")
        ):
            raise ValueError("Private capture failure servo result linkage drifted")
        cameras_by_identity = {
            _sha256_payload(camera): camera
            for camera in execution_contract["cameras"]
        }
        diagnostic_camera = cameras_by_identity.get(
            diagnostic.get("camera_identity_sha256")
        )
        if (
            diagnostic_camera is None
            or diagnostic.get("subprocess_audit", {}).get(
                "requested_framerate_fps"
            )
            != execution_contract.get("camera_framerate_fps")
        ):
            raise ValueError("Private capture failure camera mode linkage drifted")
        if (
            execution_contract.get("schema_version")
            == LIVE_EXECUTION_CONTRACT_SCHEMA_VERSION
            and diagnostic.get("subprocess_audit", {}).get("requested_input_mode")
            != diagnostic_camera.get("input_mode")
        ):
            raise ValueError("Private capture failure camera input mode drifted")
    holders = payload.get("serial_identity_holder_snapshots")
    counts = payload.get("serial_identity_holder_counts")
    holder_hashes = payload.get("serial_identity_holder_snapshot_sha256")
    if (
        not isinstance(holders, dict)
        or set(holders) != {"pre_open", "post_close"}
        or not isinstance(counts, dict)
        or set(counts) != {"pre_open", "post_close"}
        or not isinstance(holder_hashes, dict)
        or set(holder_hashes) != {"pre_open", "post_close"}
    ):
        raise ValueError("Private capture failure holder evidence is malformed")
    for stage in ("pre_open", "post_close"):
        require_no_serial_identity_holders(holders[stage])
        if counts[stage] != holders[stage]["deduplicated_holder_count"]:
            raise ValueError("Private capture failure holder count drifted")
        if holder_hashes[stage] != holders[stage]["identity_sha256"]:
            raise ValueError("Private capture failure holder identity drifted")
    verify_serial_identity_holder_stability(
        holders["pre_open"],
        holders["post_close"],
    )
    elapsed = payload.get("elapsed_seconds")
    if (
        isinstance(elapsed, bool)
        or not isinstance(elapsed, (int, float))
        or not math.isfinite(float(elapsed))
        or elapsed < 0
    ):
        raise ValueError("Private capture failure elapsed time is invalid")
    _validated_wall_time(payload.get("failed_at"))
    error_types = payload.get("error_types")
    if (
        not isinstance(error_types, list)
        or not error_types
        or any(not isinstance(value, str) or not value for value in error_types)
    ):
        raise ValueError("Private capture failure error types are malformed")
    if (
        payload.get("private_success_bundle_written") is not False
        or payload.get("tracked_success_manifest_written") is not False
        or payload.get("proof_labels") != []
        or payload.get("hardware_opened") is not True
        or payload.get("physical_follower_commanded") is not False
    ):
        raise ValueError("Private capture failure authority fields drifted")


def _extract_named_camera_failure_diagnostic(error: BaseException) -> dict[str, Any]:
    if isinstance(error, NamedCameraCaptureError):
        return copy.deepcopy(error.diagnostic)
    if isinstance(error, BaseExceptionGroup):
        matches = []
        for child in error.exceptions:
            try:
                matches.append(_extract_named_camera_failure_diagnostic(child))
            except ValueError:
                continue
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Capture failure contains ambiguous camera diagnostics")
    raise ValueError("Capture failure does not contain a named-camera diagnostic")


def _flatten_error_types(error: BaseException) -> list[str]:
    result = [type(error).__name__]
    if isinstance(error, BaseExceptionGroup):
        for child in error.exceptions:
            result.extend(_flatten_error_types(child))
    cause = error.__cause__
    if cause is not None:
        result.extend(_flatten_error_types(cause))
    return result


def build_private_observation_evidence(
    *,
    execution_contract: dict[str, Any],
    servo_result: dict[str, Any],
    frames: list[dict[str, Any]],
    pre_open_discovery: dict[str, Any],
    post_close_discovery: dict[str, Any],
    pre_open_serial_holder_snapshot: dict[str, Any],
    post_close_serial_holder_snapshot: dict[str, Any],
) -> dict[str, Any]:
    _verify_live_servo_result(servo_result, execution_contract=execution_contract)
    _verify_captured_frames(frames, execution_contract=execution_contract)
    verify_discovery_stability(execution_contract["discovery"], pre_open_discovery)
    verify_discovery_stability(execution_contract["discovery"], post_close_discovery)
    require_no_serial_identity_holders(pre_open_serial_holder_snapshot)
    require_no_serial_identity_holders(post_close_serial_holder_snapshot)
    verify_serial_identity_holder_stability(
        pre_open_serial_holder_snapshot,
        post_close_serial_holder_snapshot,
    )
    servo_midpoint = (
        servo_result["observation_started_monotonic_ns"]
        + servo_result["observation_finished_monotonic_ns"]
    ) // 2
    frame_metadata = []
    skews = []
    for frame in frames:
        metadata = {key: value for key, value in frame.items() if key != "frame_bytes"}
        frame_metadata.append(metadata)
        frame_midpoint = (
            frame["receive_started_monotonic_ns"]
            + frame["receive_finished_monotonic_ns"]
        ) // 2
        skews.append(abs(frame_midpoint - servo_midpoint))
    camera_backend_audits = []
    for camera in execution_contract["cameras"]:
        matching = [
            frame["camera_backend_audit"]
            for frame in frames
            if frame["camera"] == camera
        ]
        if not matching or any(audit != matching[0] for audit in matching[1:]):
            raise ValueError("Camera backend audit drifted across captured frames")
        camera_backend_audits.append(copy.deepcopy(matching[0]))
    payload = {
        "schema_version": PRIVATE_OBSERVATION_SCHEMA_VERSION,
        "evidence_name": "pi05_live_readonly_private_observation",
        "qualification_scope": "physical_observation",
        "evidence_mode": "local_private_physical_read_only",
        "session_id": execution_contract["session_id"],
        "execution_contract_identity_sha256": execution_contract["identity_sha256"],
        "presence_lease_identity_sha256": execution_contract[
            "presence_lease_identity_sha256"
        ],
        "discovery_identity_sha256": execution_contract["discovery_identity_sha256"],
        "pre_open_discovery_identity_sha256": pre_open_discovery["identity_sha256"],
        "post_close_discovery_identity_sha256": post_close_discovery["identity_sha256"],
        "camera_framerate_fps": execution_contract["camera_framerate_fps"],
        "serial_identity_holder_snapshots": {
            "pre_open": copy.deepcopy(pre_open_serial_holder_snapshot),
            "post_close": copy.deepcopy(post_close_serial_holder_snapshot),
        },
        "serial_identity_holder_counts": {
            "pre_open": pre_open_serial_holder_snapshot[
                "deduplicated_holder_count"
            ],
            "post_close": post_close_serial_holder_snapshot[
                "deduplicated_holder_count"
            ],
        },
        "serial_identity_holder_snapshot_sha256": {
            "pre_open": pre_open_serial_holder_snapshot["identity_sha256"],
            "post_close": post_close_serial_holder_snapshot["identity_sha256"],
        },
        "discovery_stability": (
            "exact_serial_and_stable_camera_identity_match_"
            "numeric_index_churn_allowed"
        ),
        "calibration": copy.deepcopy(execution_contract["calibration"]),
        "target_device_identity": copy.deepcopy(servo_result["target_device_identity"]),
        "servos": copy.deepcopy(servo_result["servos"]),
        "operation_counts": copy.deepcopy(servo_result["operation_counts"]),
        "camera_operation_counts": {
            "construct_attempts": len(execution_contract["cameras"]),
            "construct_successes": len(execution_contract["cameras"]),
            "open_attempts": len(execution_contract["cameras"]),
            "open_successes": len(execution_contract["cameras"]),
            "read_attempts": len(frames),
            "read_successes": len(frames),
            "release_attempts": len(execution_contract["cameras"]),
            "release_successes": len(execution_contract["cameras"]),
            "subprocess_start_attempts": sum(
                audit["subprocess_start_attempts"] for audit in camera_backend_audits
            ),
            "subprocess_start_successes": sum(
                audit["subprocess_start_successes"] for audit in camera_backend_audits
            ),
            "subprocess_communicate_attempts": sum(
                audit["subprocess_communicate_attempts"]
                for audit in camera_backend_audits
            ),
            "subprocess_communicate_successes": sum(
                audit["subprocess_communicate_successes"]
                for audit in camera_backend_audits
            ),
            "subprocess_wait_attempts": sum(
                audit["subprocess_wait_attempts"] for audit in camera_backend_audits
            ),
            "subprocess_wait_successes": sum(
                audit["subprocess_wait_successes"] for audit in camera_backend_audits
            ),
            "subprocess_terminate_attempts": sum(
                audit["subprocess_terminate_attempts"]
                for audit in camera_backend_audits
            ),
            "subprocess_terminate_successes": sum(
                audit["subprocess_terminate_successes"]
                for audit in camera_backend_audits
            ),
            "subprocess_kill_attempts": sum(
                audit["subprocess_kill_attempts"] for audit in camera_backend_audits
            ),
            "subprocess_kill_successes": sum(
                audit["subprocess_kill_successes"] for audit in camera_backend_audits
            ),
            "capture_property_writes": sum(
                audit["capture_property_writes"] for audit in camera_backend_audits
            ),
            "continuous_recording_sessions": sum(
                audit["continuous_recording_sessions"]
                for audit in camera_backend_audits
            ),
        },
        "camera_backend_audits": camera_backend_audits,
        "transport_trace": copy.deepcopy(servo_result["transport_trace"]),
        "servo_observation_interval_monotonic_ns": [
            servo_result["observation_started_monotonic_ns"],
            servo_result["observation_finished_monotonic_ns"],
        ],
        "cameras": copy.deepcopy(execution_contract["cameras"]),
        "frames": frame_metadata,
        "max_host_observed_skew_ns": max(skews),
        "timestamp_scope": (
            "host_ffmpeg_batch_receive_intervals_not_hardware_clock_sync"
        ),
        "proof_labels": [
            "live_read_only_census_observed",
            "physical_observation_capture",
        ],
        "hardware_opened": True,
        "physical_follower_commanded": False,
    }
    return sign_payload(payload)


def write_private_observation_bundle(
    *,
    output_directory: Path,
    private_evidence: dict[str, Any],
    frames: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_signed_payload(private_evidence, label="Private observation evidence")
    if output_directory.exists():
        raise ValueError(
            "Private observation output directory must be new and immutable"
        )
    prepared_frames = []
    for frame in frames:
        relative_path = Path(frame["private_relative_path"])
        if relative_path.name != str(relative_path):
            raise ValueError("Private frame path must be a basename")
        frame_bytes = frame["frame_bytes"]
        if hashlib.sha256(frame_bytes).hexdigest() != frame["frame_sha256"]:
            raise ValueError("Private frame bytes do not match their content hash")
        prepared_frames.append((relative_path, frame_bytes))
    output_directory.mkdir(parents=True, exist_ok=False)
    frame_refs = []
    for relative_path, frame_bytes in prepared_frames:
        path = output_directory / relative_path
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(frame_bytes)
        temporary.replace(path)
        frame_refs.append(
            {
                "filename": relative_path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
    evidence_path = output_directory / "private_observation.json"
    dump_canonical_json(evidence_path, private_evidence)
    return {
        "evidence": {
            "filename": evidence_path.name,
            "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            "size_bytes": evidence_path.stat().st_size,
        },
        "frames": sorted(frame_refs, key=lambda item: item["filename"]),
    }


def build_redacted_observation_manifest(
    *,
    private_evidence: dict[str, Any],
    private_bundle_refs: dict[str, Any],
) -> dict[str, Any]:
    if private_evidence.get("schema_version") != PRIVATE_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("Unsupported private observation evidence schema")
    verify_signed_payload(private_evidence, label="Private observation evidence")
    _verify_private_bundle_refs(private_bundle_refs, private_evidence=private_evidence)
    holder_snapshots = private_evidence.get("serial_identity_holder_snapshots")
    holder_counts = private_evidence.get("serial_identity_holder_counts")
    holder_hashes = private_evidence.get("serial_identity_holder_snapshot_sha256")
    if (
        not isinstance(holder_snapshots, dict)
        or set(holder_snapshots) != {"pre_open", "post_close"}
        or not isinstance(holder_counts, dict)
        or set(holder_counts) != {"pre_open", "post_close"}
        or not isinstance(holder_hashes, dict)
        or set(holder_hashes) != {"pre_open", "post_close"}
    ):
        raise ValueError("Private observation serial holder evidence is malformed")
    for stage in ("pre_open", "post_close"):
        snapshot = holder_snapshots[stage]
        require_no_serial_identity_holders(snapshot)
        if holder_counts[stage] != snapshot["deduplicated_holder_count"]:
            raise ValueError("Private observation serial holder count drifted")
        if holder_hashes[stage] != snapshot["identity_sha256"]:
            raise ValueError("Private observation serial holder identity drifted")
    verify_serial_identity_holder_stability(
        holder_snapshots["pre_open"],
        holder_snapshots["post_close"],
    )
    if private_evidence.get("camera_framerate_fps") != CAMERA_FRAMERATE_FPS:
        raise ValueError("Private observation camera framerate drifted")
    usb = private_evidence["target_device_identity"]["usb"]
    servo_identity = [
        {
            "servo_id": servo["servo_id"],
            "joint_name": servo["joint_name"],
            "model": servo["model"],
            "model_number": servo["model_number"],
            "firmware_version": servo["firmware_version"],
        }
        for servo in private_evidence["servos"]
    ]
    cameras = []
    for camera in private_evidence["cameras"]:
        matching_audits = [
            audit
            for audit in private_evidence["camera_backend_audits"]
            if audit["camera_identity_sha256"] == _sha256_payload(camera)
        ]
        if len(matching_audits) != 1:
            raise ValueError("Private camera backend audit identity is ambiguous")
        matching_frames = [
            frame
            for frame in private_evidence["frames"]
            if frame["camera"]["index"] == camera["index"]
        ]
        for frame in matching_frames:
            _require_frame_dimensions_match_camera(frame, camera=camera)
        camera_frames = [
            {
                key: frame[key]
                for key in (
                    "frame_index",
                    "host_wall_time",
                    "receive_started_monotonic_ns",
                    "receive_finished_monotonic_ns",
                    "encoding",
                    "width",
                    "height",
                    "channels",
                    "frame_sha256",
                )
            }
            for frame in matching_frames
        ]
        cameras.append(
            {
                "camera_identity_sha256": _sha256_payload(camera),
                "camera_backend_audit_sha256": _sha256_payload(matching_audits[0]),
                "input_mode": copy.deepcopy(camera["input_mode"]),
                "frames": camera_frames,
            }
        )
    payload = {
        "schema_version": REDACTED_MANIFEST_SCHEMA_VERSION,
        "manifest_name": "pi05_live_readonly_observation_redacted",
        "qualification_scope": "physical_observation",
        "evidence_mode": "tracked_redacted_physical_read_only_manifest",
        "session_id": private_evidence["session_id"],
        "private_evidence_identity_sha256": private_evidence["identity_sha256"],
        "private_bundle_refs": copy.deepcopy(private_bundle_refs),
        "usb_identity_sha256": _sha256_payload(usb),
        "calibration_file_sha256": private_evidence["calibration"]["sha256"],
        "servo_identity": servo_identity,
        "servo_observation_sha256": _sha256_payload(private_evidence["servos"]),
        "operation_counts": copy.deepcopy(private_evidence["operation_counts"]),
        "camera_operation_counts": copy.deepcopy(
            private_evidence["camera_operation_counts"]
        ),
        "camera_framerate_fps": private_evidence["camera_framerate_fps"],
        "discovery_stability": private_evidence["discovery_stability"],
        "pre_open_discovery_identity_sha256": private_evidence[
            "pre_open_discovery_identity_sha256"
        ],
        "post_close_discovery_identity_sha256": private_evidence[
            "post_close_discovery_identity_sha256"
        ],
        "serial_identity_holder_evidence": {
            stage: _redacted_serial_identity_holder_evidence(snapshot)
            for stage, snapshot in holder_snapshots.items()
        },
        "cameras": cameras,
        "max_host_observed_skew_ns": private_evidence["max_host_observed_skew_ns"],
        "timestamp_scope": private_evidence["timestamp_scope"],
        "proof_labels": copy.deepcopy(private_evidence["proof_labels"]),
        "privacy": {
            "raw_usb_serial_included": False,
            "raw_device_path_included": False,
            "raw_camera_identity_included": False,
            "raw_frame_bytes_included": False,
        },
        "hardware_opened": True,
        "physical_follower_commanded": False,
    }
    return sign_payload(payload)


def verify_redacted_observation_manifest(
    payload: dict[str, Any],
    *,
    private_evidence: dict[str, Any],
    private_bundle_refs: dict[str, Any],
) -> None:
    if payload.get("schema_version") != REDACTED_MANIFEST_SCHEMA_VERSION:
        raise ValueError("Unsupported redacted observation manifest schema")
    verify_signed_payload(payload, label="Redacted observation manifest")
    expected = build_redacted_observation_manifest(
        private_evidence=private_evidence,
        private_bundle_refs=private_bundle_refs,
    )
    if payload != expected:
        raise ValueError("Redacted observation manifest drifted from private evidence")


def enumerate_serial_candidates() -> list[dict[str, Any]]:
    from serial.tools import list_ports

    records = []
    for port in list_ports.comports():
        paired_alias = _paired_tty_alias(port.device)
        records.append(
            {
                "device": port.device,
                "aliases": (
                    [paired_alias]
                    if paired_alias != port.device and Path(paired_alias).exists()
                    else []
                ),
                "vid": port.vid,
                "pid": port.pid,
                "serial_number": port.serial_number,
                "manufacturer": port.manufacturer,
                "product": port.product,
                "location": port.location,
                "hwid": port.hwid,
            }
        )
    return _merge_serial_aliases(records)


def parse_serial_device_holders(output: str) -> list[dict[str, Any]]:
    if not isinstance(output, str):
        raise ValueError("Serial holder discovery output must be text")
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in output.splitlines():
        if not line:
            continue
        tag, value = line[0], line[1:]
        if tag == "p":
            if current is not None:
                records.append(current)
            try:
                pid = int(value)
            except ValueError as exc:
                raise ValueError("Serial holder PID is malformed") from exc
            if pid <= 0:
                raise ValueError("Serial holder PID is invalid")
            current = {
                "pid": pid,
                "command": None,
                "file_descriptors": [],
                "file_types": [],
            }
        elif current is None:
            raise ValueError("Serial holder discovery field precedes its process")
        elif tag == "c":
            if current["command"] is not None:
                raise ValueError("Serial holder command is duplicated")
            current["command"] = require_nonblank(
                value,
                label="serial holder command",
            )
        elif tag == "f":
            current["file_descriptors"].append(
                require_nonblank(value, label="serial holder file descriptor")
            )
        elif tag == "t":
            current["file_types"].append(
                require_nonblank(value, label="serial holder file type")
            )
        else:
            raise ValueError("Serial holder discovery contains an unknown field")
    if current is not None:
        records.append(current)
    for record in records:
        if (
            record["command"] is None
            or not record["file_descriptors"]
            or len(record["file_descriptors"]) != len(record["file_types"])
        ):
            raise ValueError("Serial holder discovery record is incomplete")
        descriptor_types = sorted(
            zip(record["file_descriptors"], record["file_types"], strict=True)
        )
        record["file_descriptors"] = [item[0] for item in descriptor_types]
        record["file_types"] = [item[1] for item in descriptor_types]
    if len({record["pid"] for record in records}) != len(records):
        raise ValueError("Serial holder discovery repeats a process")
    return sorted(records, key=lambda record: record["pid"])


def enumerate_serial_device_holders(device_path: str) -> list[dict[str, Any]]:
    if device_path != KNOWN_PHYSICAL_FOLLOWER_PORT:
        raise ValueError("Serial holder discovery path is not the pinned follower")
    return _enumerate_serial_holders_for_path(
        device_path,
        run_command=subprocess.run,
    )


def enumerate_serial_identity_holders(
    canonical_path: str,
    observed_aliases: list[str],
    *,
    run_command: Callable[..., Any] = subprocess.run,
    path_exists: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    if canonical_path != KNOWN_PHYSICAL_FOLLOWER_PORT:
        raise ValueError("Serial identity canonical path is not the pinned follower")
    expected_aliases = [_paired_tty_alias(KNOWN_PHYSICAL_FOLLOWER_PORT)]
    if observed_aliases != expected_aliases:
        raise ValueError("Serial identity signed follower alias set is incomplete")
    exists = path_exists or (lambda path: Path(path).exists())
    paths_checked = [canonical_path, *observed_aliases]
    per_path = []
    for path in paths_checked:
        holders = _enumerate_serial_holders_for_path(
            path,
            run_command=run_command,
        )
        per_path.append(
            {
                "path": path,
                "path_exists": bool(exists(path)),
                "holders": holders,
                "holder_count": len(holders),
            }
        )
    deduplicated = _deduplicate_identity_holders(per_path)
    payload = {
        "schema_version": SERIAL_IDENTITY_HOLDER_SNAPSHOT_SCHEMA_VERSION,
        "snapshot_name": "pi05_follower_serial_identity_holders",
        "canonical_path": canonical_path,
        "observed_aliases": list(observed_aliases),
        "paths_checked": paths_checked,
        "per_path": per_path,
        "per_path_holder_counts": [item["holder_count"] for item in per_path],
        "deduplicated_holders": deduplicated,
        "deduplicated_holder_count": len(deduplicated),
    }
    signed = sign_payload(payload)
    verify_serial_identity_holder_snapshot(signed)
    return signed


def verify_serial_identity_holder_snapshot(payload: dict[str, Any]) -> None:
    allowed_fields = {
        "schema_version",
        "snapshot_name",
        "canonical_path",
        "observed_aliases",
        "paths_checked",
        "per_path",
        "per_path_holder_counts",
        "deduplicated_holders",
        "deduplicated_holder_count",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Serial identity holder snapshot fields are malformed")
    if (
        payload.get("schema_version")
        != SERIAL_IDENTITY_HOLDER_SNAPSHOT_SCHEMA_VERSION
        or payload.get("snapshot_name")
        != "pi05_follower_serial_identity_holders"
    ):
        raise ValueError("Serial identity holder snapshot classification drifted")
    verify_signed_payload(payload, label="Serial identity holder snapshot")
    canonical = payload.get("canonical_path")
    aliases = payload.get("observed_aliases")
    expected_aliases = [_paired_tty_alias(KNOWN_PHYSICAL_FOLLOWER_PORT)]
    expected_paths = [KNOWN_PHYSICAL_FOLLOWER_PORT, *expected_aliases]
    if canonical != KNOWN_PHYSICAL_FOLLOWER_PORT or aliases != expected_aliases:
        raise ValueError("Serial identity holder snapshot path identity drifted")
    if payload.get("paths_checked") != expected_paths:
        raise ValueError("Serial identity holder snapshot path coverage drifted")
    per_path = payload.get("per_path")
    if not isinstance(per_path, list) or len(per_path) != len(expected_paths):
        raise ValueError("Serial identity per-path holder evidence is incomplete")
    for expected_path, record in zip(expected_paths, per_path, strict=True):
        if not isinstance(record, dict) or set(record) != {
            "path",
            "path_exists",
            "holders",
            "holder_count",
        }:
            raise ValueError("Serial identity per-path holder record is malformed")
        if record.get("path") != expected_path or not isinstance(
            record.get("path_exists"), bool
        ):
            raise ValueError("Serial identity per-path path evidence drifted")
        holders = record.get("holders")
        _verify_normalized_serial_device_holders(holders)
        if record.get("holder_count") != len(holders):
            raise ValueError("Serial identity per-path holder count drifted")
    counts = [record["holder_count"] for record in per_path]
    if payload.get("per_path_holder_counts") != counts:
        raise ValueError("Serial identity holder count vector drifted")
    deduplicated = _deduplicate_identity_holders(per_path)
    if payload.get("deduplicated_holders") != deduplicated or payload.get(
        "deduplicated_holder_count"
    ) != len(deduplicated):
        raise ValueError("Serial identity deduplicated holder evidence drifted")


def require_no_serial_identity_holders(payload: dict[str, Any]) -> None:
    verify_serial_identity_holder_snapshot(payload)
    if not all(record["path_exists"] for record in payload["per_path"]):
        raise ValueError("Follower serial identity path does not exist")
    count = payload["deduplicated_holder_count"]
    if count:
        raise ValueError(
            f"Follower serial identity has {count} independent holder(s)"
        )


def verify_serial_identity_holder_stability(
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    verify_serial_identity_holder_snapshot(before)
    verify_serial_identity_holder_snapshot(after)
    for field in ("canonical_path", "observed_aliases", "paths_checked"):
        if before[field] != after[field]:
            raise ValueError("Serial identity holder path set drifted")
    before_exists = [record["path_exists"] for record in before["per_path"]]
    after_exists = [record["path_exists"] for record in after["per_path"]]
    if before_exists != after_exists:
        raise ValueError("Serial identity holder path existence drifted")


def _redacted_serial_identity_holder_evidence(
    snapshot: dict[str, Any],
) -> dict[str, Any]:
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


def _enumerate_serial_holders_for_path(
    device_path: str,
    *,
    run_command: Callable[..., Any],
) -> list[dict[str, Any]]:
    result = run_command(
        ["/usr/sbin/lsof", "-nP", "-F", "pcft", device_path],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError("Serial holder discovery command failed")
    if result.stderr.strip():
        raise RuntimeError("Serial holder discovery command emitted stderr")
    holders = parse_serial_device_holders(result.stdout)
    if result.returncode == 1 and holders:
        raise ValueError("Serial holder discovery status contradicts its output")
    return holders


def _deduplicate_identity_holders(
    per_path: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    units: dict[tuple[int, str, str], dict[str, Any]] = {}
    for record in per_path:
        path = record["path"]
        for holder in record["holders"]:
            for descriptor, file_type in zip(
                holder["file_descriptors"],
                holder["file_types"],
                strict=True,
            ):
                key = (holder["pid"], descriptor, file_type)
                unit = units.setdefault(
                    key,
                    {"command": holder["command"], "paths": set()},
                )
                if unit["command"] != holder["command"]:
                    raise ValueError(
                        "Serial identity holder command drifted for one PID/file descriptor"
                    )
                unit["paths"].add(path)
    return [
        {
            "pid": pid,
            "command": unit["command"],
            "file_descriptor": descriptor,
            "file_type": file_type,
            "paths": [
                path
                for path in [
                    KNOWN_PHYSICAL_FOLLOWER_PORT,
                    _paired_tty_alias(KNOWN_PHYSICAL_FOLLOWER_PORT),
                ]
                if path in unit["paths"]
            ],
        }
        for (pid, descriptor, file_type), unit in sorted(units.items())
    ]


def require_no_serial_device_holders(holders: list[dict[str, Any]]) -> None:
    _verify_normalized_serial_device_holders(holders)
    if holders:
        raise ValueError(
            f"Follower serial device has {len(holders)} independent holder(s)"
        )


def _verify_normalized_serial_device_holders(holders: Any) -> None:
    if not isinstance(holders, list):
        raise ValueError("Serial holder snapshot must be a list")
    if any(
        not isinstance(record, dict)
        or set(record) != {"pid", "command", "file_descriptors", "file_types"}
        or isinstance(record["pid"], bool)
        or not isinstance(record["pid"], int)
        or record["pid"] <= 0
        or not isinstance(record["command"], str)
        or not record["command"]
        or not isinstance(record["file_descriptors"], list)
        or not record["file_descriptors"]
        or record["file_descriptors"] != sorted(record["file_descriptors"])
        or any(
            not isinstance(value, str) or not value
            for value in record["file_descriptors"]
        )
        or not isinstance(record["file_types"], list)
        or len(record["file_types"]) != len(record["file_descriptors"])
        or record["file_types"] != sorted(record["file_types"])
        or any(
            not isinstance(value, str) or not value for value in record["file_types"]
        )
        for record in holders
    ) or holders != sorted(holders, key=lambda record: record["pid"]):
        raise ValueError("Serial holder snapshot is not normalized")
    if len({record["pid"] for record in holders}) != len(holders):
        raise ValueError("Serial holder snapshot repeats a process")


def enumerate_camera_metadata() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profiler = subprocess.run(
        ["/usr/sbin/system_profiler", "SPCameraDataType", "-json"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    avfoundation = subprocess.run(
        [
            "/opt/homebrew/bin/ffmpeg",
            "-hide_banner",
            "-f",
            "avfoundation",
            "-list_devices",
            "true",
            "-i",
            "",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    supported_modes = subprocess.run(
        ["/usr/bin/xcrun", "swift", "-e", _SWIFT_CAMERA_MODE_METADATA_SOURCE],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if supported_modes.stderr.strip():
        raise RuntimeError("Camera supported-mode metadata emitted stderr")
    return (
        parse_avfoundation_video_devices(
            "\n".join((avfoundation.stdout, avfoundation.stderr))
        ),
        parse_system_camera_devices(
            json.loads(profiler.stdout),
            supported_modes_payload=json.loads(supported_modes.stdout),
        ),
    )


def capture_live_discovery(*, session_id: str, captured_at: str) -> dict[str, Any]:
    avfoundation_devices, system_cameras = enumerate_camera_metadata()
    return build_live_discovery_snapshot(
        session_id=session_id,
        captured_at=captured_at,
        serial_candidates=enumerate_serial_candidates(),
        avfoundation_devices=avfoundation_devices,
        system_cameras=system_cameras,
    )


def construct_pinned_feetech_bus(
    *,
    repo_root: Path,
    census_contract: dict[str, Any],
) -> Any:
    verify_census_runtime_source_bindings(repo_root=repo_root)
    verify_live_census_contract(census_contract)
    source_root = repo_root / "external" / "lerobot" / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    from lerobot.motors import Motor, MotorNormMode
    from lerobot.motors.feetech import FeetechMotorsBus

    implementation_path = Path(inspect.getfile(FeetechMotorsBus)).resolve()
    try:
        implementation_path.relative_to(source_root.resolve())
    except ValueError as exc:
        raise ValueError(
            "Live census imported an unpinned LeRobot implementation"
        ) from exc

    motors = {}
    for servo in census_contract["expected_servos"]:
        norm_mode = (
            MotorNormMode.RANGE_0_100
            if servo["joint_name"] == "gripper"
            else MotorNormMode.DEGREES
        )
        motors[servo["joint_name"]] = Motor(
            servo["servo_id"],
            servo["model"],
            norm_mode,
        )
    return FeetechMotorsBus(
        port=census_contract["target_device_identity"]["usb"]["canonical_path"],
        motors=motors,
        calibration=None,
        protocol_version=census_contract["target_device_identity"]["bus"][
            "protocol_version"
        ],
    )


class FFmpegNamedFiniteCamera:
    """Capture one finite PNG batch by exact AVFoundation camera name."""

    def __init__(
        self,
        camera: dict[str, Any],
        *,
        expected_frame_count: int,
        framerate_fps: int = CAMERA_FRAMERATE_FPS,
        read_timeout_seconds: int = CAMERA_READ_TIMEOUT_SECONDS,
        monotonic_ns: Callable[[], int],
        popen_factory: Callable[..., Any] = subprocess.Popen,
    ):
        if not isinstance(camera, dict) or set(camera) != {
            "index",
            "name",
            "unique_id",
            "model_id",
            "input_mode",
        }:
            raise ValueError("Named camera identity fields are malformed")
        name = require_nonblank(camera.get("name"), label="named camera name")
        if any(character in name for character in ("\x00", "\n", "\r", ":")):
            raise ValueError("Named camera name is unsafe for AVFoundation input")
        require_nonblank(camera.get("unique_id"), label="named camera unique_id")
        require_nonblank(camera.get("model_id"), label="named camera model_id")
        if (
            isinstance(expected_frame_count, bool)
            or not isinstance(expected_frame_count, int)
            or not 1 <= expected_frame_count <= 3
        ):
            raise ValueError("Named camera frame count is invalid")
        if (
            isinstance(read_timeout_seconds, bool)
            or not isinstance(read_timeout_seconds, int)
            or read_timeout_seconds <= 0
        ):
            raise ValueError("Named camera timeout is invalid")
        if (
            isinstance(framerate_fps, bool)
            or not isinstance(framerate_fps, int)
            or framerate_fps != CAMERA_FRAMERATE_FPS
        ):
            raise ValueError("Named camera framerate is not the reviewed mode")
        input_mode = _normalize_camera_input_mode(camera.get("input_mode"))
        if input_mode["framerate_fps"] != framerate_fps:
            raise ValueError("Named camera input mode and framerate differ")
        self._camera = copy.deepcopy(camera)
        self._input_mode = input_mode
        self._expected_frame_count = expected_frame_count
        self._framerate_fps = framerate_fps
        self._read_timeout_seconds = read_timeout_seconds
        self._monotonic_ns = monotonic_ns
        self._popen_factory = popen_factory
        self._process: Any = None
        self._frames: list[dict[str, Any]] | None = None
        self._read_index = 0
        self._opened = False
        self._released = False
        self._communicated = False
        self._failure_context: dict[str, Any] | None = None
        self._audit = {
            "backend": "ffmpeg_named_avfoundation",
            "camera_identity_sha256": _sha256_payload(self._camera),
            "requested_framerate_fps": self._framerate_fps,
            "requested_input_mode": copy.deepcopy(self._input_mode),
            "subprocess_start_attempts": 0,
            "subprocess_start_successes": 0,
            "subprocess_communicate_attempts": 0,
            "subprocess_communicate_successes": 0,
            "subprocess_wait_attempts": 0,
            "subprocess_wait_successes": 0,
            "subprocess_terminate_attempts": 0,
            "subprocess_terminate_successes": 0,
            "subprocess_kill_attempts": 0,
            "subprocess_kill_successes": 0,
            "release_attempts": 0,
            "release_successes": 0,
            "frames_delivered": 0,
            "capture_property_writes": 0,
            "continuous_recording_sessions": 0,
        }

    def open(self) -> None:
        if self._opened or self._released:
            raise RuntimeError("Named camera open lifecycle is invalid")
        self._audit["subprocess_start_attempts"] += 1
        command = [
            str(FFMPEG_EXECUTABLE),
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "avfoundation",
            "-pixel_format",
            self._input_mode["pixel_format"],
            "-video_size",
            f"{self._input_mode['width']}x{self._input_mode['height']}",
            "-framerate",
            str(self._framerate_fps),
            "-i",
            f"{self._camera['name']}:none",
            "-an",
            "-sn",
            "-dn",
            "-frames:v",
            str(self._expected_frame_count),
            "-f",
            "image2pipe",
            "-pix_fmt",
            "rgb24",
            "-vcodec",
            "png",
            "pipe:1",
        ]
        try:
            self._process = self._popen_factory(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except BaseException:
            self._set_failure_context(
                stage="subprocess_start",
                return_code=None,
                stdout=b"",
                stderr=b"",
            )
            raise
        self._audit["subprocess_start_successes"] += 1
        self._opened = True

    def read(self) -> dict[str, Any]:
        if not self._opened or self._released or self._process is None:
            raise RuntimeError("Named camera is not open")
        if self._frames is None:
            self._capture_batch()
        if self._read_index >= self._expected_frame_count:
            raise RuntimeError("Named camera read exceeded the finite frame count")
        frame = copy.deepcopy(self._frames[self._read_index])
        self._read_index += 1
        self._audit["frames_delivered"] += 1
        return frame

    def release(self) -> None:
        if self._released:
            raise RuntimeError("Named camera release called more than once")
        self._audit["release_attempts"] += 1
        self._released = True
        if self._process is not None and not self._communicated:
            self._terminate_unfinished_process()
        self._process = None
        self._audit["release_successes"] += 1

    def audit(self) -> dict[str, Any]:
        return copy.deepcopy(self._audit)

    def failure_diagnostic(
        self,
        *,
        primary_error: BaseException,
        cleanup_error: BaseException | None,
    ) -> dict[str, Any]:
        context = copy.deepcopy(self._failure_context)
        if context is None:
            context = self._failure_context_payload(
                stage="camera_lifecycle",
                return_code=getattr(self._process, "returncode", None),
                stdout=b"",
                stderr=b"",
            )
        payload = {
            "schema_version": CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION,
            "diagnostic_name": "pi05_named_camera_capture_failure",
            "stage": context["stage"],
            "camera_identity_sha256": _sha256_payload(self._camera),
            "return_code": context["return_code"],
            "stdout": context["stdout"],
            "stderr": context["stderr"],
            "subprocess_audit": copy.deepcopy(self._audit),
            "primary_error_type": type(primary_error).__name__,
            "cleanup_error_type": (
                type(cleanup_error).__name__ if cleanup_error is not None else None
            ),
            "proof_labels": [],
            "physical_follower_commanded": False,
        }
        signed = sign_payload(payload)
        _verify_named_camera_failure_diagnostic(signed)
        return signed

    def _capture_batch(self) -> None:
        self._audit["subprocess_communicate_attempts"] += 1
        self._audit["subprocess_wait_attempts"] += 1
        started = self._monotonic_ns()
        try:
            stdout, stderr = self._process.communicate(
                timeout=self._read_timeout_seconds
            )
        except subprocess.TimeoutExpired as exc:
            self._set_failure_context(
                stage="subprocess_timeout",
                return_code=getattr(self._process, "returncode", None),
                stdout=b"",
                stderr=b"",
            )
            raise TimeoutError(
                "Named AVFoundation camera finite batch exceeded "
                f"{self._read_timeout_seconds}s"
            ) from exc
        finished = self._monotonic_ns()
        self._communicated = True
        self._audit["subprocess_communicate_successes"] += 1
        self._audit["subprocess_wait_successes"] += 1
        if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
            self._set_failure_context(
                stage="subprocess_output_type",
                return_code=getattr(self._process, "returncode", None),
                stdout=stdout if isinstance(stdout, bytes) else b"",
                stderr=stderr if isinstance(stderr, bytes) else b"",
            )
            raise ValueError("Named camera subprocess output must be bytes")
        if self._process.returncode != 0:
            self._set_failure_context(
                stage="subprocess_nonzero_exit",
                return_code=self._process.returncode,
                stdout=stdout,
                stderr=stderr,
            )
            raise RuntimeError("Named camera ffmpeg subprocess failed")
        if stderr.strip():
            self._set_failure_context(
                stage="subprocess_stderr",
                return_code=self._process.returncode,
                stdout=stdout,
                stderr=stderr,
            )
            raise RuntimeError("Named camera ffmpeg emitted stderr")
        try:
            parsed = _parse_exact_png_stream(
                stdout,
                expected_frame_count=self._expected_frame_count,
            )
            for frame in parsed:
                _require_frame_dimensions_match_camera(
                    frame,
                    camera=self._camera,
                )
        except BaseException:
            self._set_failure_context(
                stage="png_validation",
                return_code=self._process.returncode,
                stdout=stdout,
                stderr=stderr,
            )
            raise
        for frame in parsed:
            frame["receive_started_monotonic_ns"] = started
            frame["receive_finished_monotonic_ns"] = finished
        self._frames = parsed

    def _terminate_unfinished_process(self) -> None:
        self._audit["subprocess_terminate_attempts"] += 1
        self._process.terminate()
        self._audit["subprocess_terminate_successes"] += 1
        self._audit["subprocess_communicate_attempts"] += 1
        self._audit["subprocess_wait_attempts"] += 1
        try:
            stdout, stderr = self._process.communicate(
                timeout=self._read_timeout_seconds
            )
        except subprocess.TimeoutExpired:
            self._audit["subprocess_kill_attempts"] += 1
            self._process.kill()
            self._audit["subprocess_kill_successes"] += 1
            self._audit["subprocess_communicate_attempts"] += 1
            self._audit["subprocess_wait_attempts"] += 1
            stdout, stderr = self._process.communicate(
                timeout=self._read_timeout_seconds
            )
        self._audit["subprocess_communicate_successes"] += 1
        self._audit["subprocess_wait_successes"] += 1
        self._communicated = True
        if isinstance(stdout, bytes) and isinstance(stderr, bytes):
            stage = (
                self._failure_context["stage"]
                if self._failure_context is not None
                else "subprocess_cleanup"
            )
            self._set_failure_context(
                stage=stage,
                return_code=getattr(self._process, "returncode", None),
                stdout=stdout,
                stderr=stderr,
            )

    def _set_failure_context(
        self,
        *,
        stage: str,
        return_code: int | None,
        stdout: bytes,
        stderr: bytes,
    ) -> None:
        self._failure_context = self._failure_context_payload(
            stage=stage,
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
        )

    def _failure_context_payload(
        self,
        *,
        stage: str,
        return_code: int | None,
        stdout: bytes,
        stderr: bytes,
    ) -> dict[str, Any]:
        return {
            "stage": require_nonblank(stage, label="camera failure stage"),
            "return_code": return_code,
            "stdout": _camera_failure_stream_summary(
                stdout,
                camera=self._camera,
                include_preview=False,
            ),
            "stderr": _camera_failure_stream_summary(
                stderr,
                camera=self._camera,
                include_preview=True,
            ),
        }


def _camera_failure_stream_summary(
    payload: bytes,
    *,
    camera: dict[str, Any],
    include_preview: bool,
) -> dict[str, Any]:
    if not isinstance(payload, bytes):
        raise ValueError("Camera failure subprocess stream must be bytes")
    summary: dict[str, Any] = {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    if not include_preview:
        return summary
    preview_bytes = payload[:MAX_CAMERA_FAILURE_PREVIEW_BYTES]
    preview = preview_bytes.decode("utf-8", errors="replace")
    preview = preview.replace("\r\n", "\n").replace("\r", "\n")
    preview = "".join(
        character
        if character in {"\n", "\t"} or 0x20 <= ord(character) <= 0x7E
        else "?"
        for character in preview
    )
    for field in ("name", "unique_id", "model_id"):
        sensitive = camera.get(field)
        if isinstance(sensitive, str) and sensitive:
            preview = preview.replace(sensitive, f"<redacted-camera-{field}>")
    preview = re.sub(
        r"/(?:Users|dev|private|tmp|Volumes)(?:/[^\s'\"]+)+",
        "<redacted-path>",
        preview,
    )
    preview = re.sub(
        r"\b(?=[A-Za-z0-9_-]{10,}\b)(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]+\b",
        "<redacted-token>",
        preview,
    )
    redaction_truncated = len(preview) > MAX_CAMERA_FAILURE_PREVIEW_BYTES
    preview = preview[:MAX_CAMERA_FAILURE_PREVIEW_BYTES]
    summary.update(
        {
            "preview_source_byte_count": len(preview_bytes),
            "preview_max_bytes": MAX_CAMERA_FAILURE_PREVIEW_BYTES,
            "preview_truncated": (
                len(payload) > MAX_CAMERA_FAILURE_PREVIEW_BYTES
                or redaction_truncated
            ),
            "sanitized_preview": preview,
            "sanitization": (
                "utf8_replace_control_normalize_exact_camera_path_"
                "and_serial_like_token_redaction"
            ),
        }
    )
    return summary


def _verify_named_camera_failure_diagnostic(payload: dict[str, Any]) -> None:
    allowed_fields = {
        "schema_version",
        "diagnostic_name",
        "stage",
        "camera_identity_sha256",
        "return_code",
        "stdout",
        "stderr",
        "subprocess_audit",
        "primary_error_type",
        "cleanup_error_type",
        "proof_labels",
        "physical_follower_commanded",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Named camera failure diagnostic fields are malformed")
    diagnostic_schema = payload.get("schema_version")
    if (
        diagnostic_schema
        not in {
            CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION,
            LEGACY_CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION,
            OLDEST_CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION,
        }
        or payload.get("diagnostic_name")
        != "pi05_named_camera_capture_failure"
        or payload.get("stage")
        not in {
            "subprocess_start",
            "subprocess_timeout",
            "subprocess_output_type",
            "subprocess_nonzero_exit",
            "subprocess_stderr",
            "subprocess_cleanup",
            "png_validation",
            "camera_lifecycle",
        }
    ):
        raise ValueError("Named camera failure diagnostic classification drifted")
    verify_signed_payload(payload, label="Named camera failure diagnostic")
    camera_identity = payload.get("camera_identity_sha256")
    if not isinstance(camera_identity, str) or re.fullmatch(
        r"[0-9a-f]{64}", camera_identity
    ) is None:
        raise ValueError("Named camera failure identity is malformed")
    return_code = payload.get("return_code")
    if (
        return_code is not None
        and (isinstance(return_code, bool) or not isinstance(return_code, int))
    ):
        raise ValueError("Named camera failure return code is malformed")
    stdout = payload.get("stdout")
    stderr = payload.get("stderr")
    if not isinstance(stdout, dict) or set(stdout) != {"byte_count", "sha256"}:
        raise ValueError("Named camera failure stdout summary is malformed")
    stderr_fields = {
        "byte_count",
        "sha256",
        "preview_source_byte_count",
        "preview_max_bytes",
        "preview_truncated",
        "sanitized_preview",
        "sanitization",
    }
    if not isinstance(stderr, dict) or set(stderr) != stderr_fields:
        raise ValueError("Named camera failure stderr summary is malformed")
    for label, stream in (("stdout", stdout), ("stderr", stderr)):
        count = stream.get("byte_count")
        digest = stream.get("sha256")
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise ValueError(f"Named camera failure {label} summary is invalid")
    if (
        isinstance(stderr.get("preview_source_byte_count"), bool)
        or not isinstance(stderr.get("preview_source_byte_count"), int)
        or not 0
        <= stderr["preview_source_byte_count"]
        <= min(stderr["byte_count"], MAX_CAMERA_FAILURE_PREVIEW_BYTES)
        or stderr.get("preview_max_bytes") != MAX_CAMERA_FAILURE_PREVIEW_BYTES
        or not isinstance(stderr.get("preview_truncated"), bool)
        or not isinstance(stderr.get("sanitized_preview"), str)
        or len(stderr["sanitized_preview"]) > MAX_CAMERA_FAILURE_PREVIEW_BYTES
        or stderr.get("sanitization")
        != (
            "utf8_replace_control_normalize_exact_camera_path_"
            "and_serial_like_token_redaction"
        )
    ):
        raise ValueError("Named camera failure stderr preview is invalid")
    if (
        stderr["byte_count"] > MAX_CAMERA_FAILURE_PREVIEW_BYTES
        and stderr["preview_truncated"] is not True
    ):
        raise ValueError("Named camera failure stderr truncation is invalid")
    audit = payload.get("subprocess_audit")
    count_fields = {
        "subprocess_start_attempts",
        "subprocess_start_successes",
        "subprocess_communicate_attempts",
        "subprocess_communicate_successes",
        "subprocess_wait_attempts",
        "subprocess_wait_successes",
        "subprocess_terminate_attempts",
        "subprocess_terminate_successes",
        "subprocess_kill_attempts",
        "subprocess_kill_successes",
        "release_attempts",
        "release_successes",
        "frames_delivered",
        "capture_property_writes",
        "continuous_recording_sessions",
    }
    audit_allowed_fields = {"backend", "camera_identity_sha256", *count_fields}
    if diagnostic_schema in {
        CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION,
        LEGACY_CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION,
    }:
        audit_allowed_fields.add("requested_framerate_fps")
    if diagnostic_schema == CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION:
        audit_allowed_fields.add("requested_input_mode")
    if (
        not isinstance(audit, dict)
        or set(audit) != audit_allowed_fields
        or audit.get("backend") != "ffmpeg_named_avfoundation"
        or audit.get("camera_identity_sha256") != camera_identity
        or any(
            isinstance(audit.get(field), bool)
            or not isinstance(audit.get(field), int)
            or audit[field] < 0
            for field in count_fields
        )
    ):
        raise ValueError("Named camera failure subprocess audit is malformed")
    if diagnostic_schema in {
        CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION,
        LEGACY_CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION,
    } and (
        isinstance(audit.get("requested_framerate_fps"), bool)
        or audit.get("requested_framerate_fps") != CAMERA_FRAMERATE_FPS
    ):
        raise ValueError("Named camera failure subprocess framerate drifted")
    if diagnostic_schema == CAMERA_FAILURE_DIAGNOSTIC_SCHEMA_VERSION:
        _normalize_camera_input_mode(audit.get("requested_input_mode"))
    if (
        not isinstance(payload.get("primary_error_type"), str)
        or not payload["primary_error_type"]
        or (
            payload.get("cleanup_error_type") is not None
            and (
                not isinstance(payload["cleanup_error_type"], str)
                or not payload["cleanup_error_type"]
            )
        )
        or payload.get("proof_labels") != []
        or payload.get("physical_follower_commanded") is not False
    ):
        raise ValueError("Named camera failure authority fields drifted")


def _parse_exact_png_stream(
    payload: bytes,
    *,
    expected_frame_count: int,
) -> list[dict[str, Any]]:
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("Named camera PNG stream is empty")
    if len(payload) > expected_frame_count * MAX_PNG_FRAME_BYTES:
        raise ValueError("Named camera PNG stream exceeds its finite byte bound")
    frames = []
    offset = 0
    for _ in range(expected_frame_count):
        frame_start = offset
        if payload[offset : offset + len(PNG_SIGNATURE)] != PNG_SIGNATURE:
            raise ValueError("Named camera PNG signature is missing")
        offset += len(PNG_SIGNATURE)
        width: int | None = None
        height: int | None = None
        channels: int | None = None
        first_chunk = True
        seen_idat = False
        compressed_scanlines = bytearray()
        while True:
            if offset + 12 > len(payload):
                raise ValueError("Named camera PNG stream is truncated")
            length = struct.unpack(">I", payload[offset : offset + 4])[0]
            chunk_type = payload[offset + 4 : offset + 8]
            if length > MAX_PNG_FRAME_BYTES:
                raise ValueError("Named camera PNG chunk exceeds its byte bound")
            chunk_end = offset + 12 + length
            if chunk_end > len(payload):
                raise ValueError("Named camera PNG chunk is truncated")
            data = payload[offset + 8 : offset + 8 + length]
            observed_crc = struct.unpack(
                ">I", payload[offset + 8 + length : chunk_end]
            )[0]
            expected_crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
            if observed_crc != expected_crc:
                raise ValueError("Named camera PNG chunk CRC is invalid")
            if first_chunk:
                if chunk_type != b"IHDR" or length != 13:
                    raise ValueError("Named camera PNG IHDR is malformed")
                (
                    width,
                    height,
                    bit_depth,
                    color_type,
                    compression,
                    filtering,
                    interlace,
                ) = struct.unpack(">IIBBBBB", data)
                if (
                    width <= 0
                    or height <= 0
                    or width > 16384
                    or height > 16384
                    or bit_depth != 8
                    or color_type != 2
                    or compression != 0
                    or filtering != 0
                    or interlace != 0
                ):
                    raise ValueError(
                        "Named camera PNG dimensions or format are invalid"
                    )
                channels = 3
                first_chunk = False
            elif chunk_type == b"IHDR":
                raise ValueError("Named camera PNG contains a duplicate IHDR")
            elif chunk_type == b"IDAT":
                seen_idat = True
                compressed_scanlines.extend(data)
            offset = chunk_end
            if chunk_type == b"IEND":
                if length != 0 or not seen_idat:
                    raise ValueError("Named camera PNG IEND is malformed")
                break
            if offset - frame_start > MAX_PNG_FRAME_BYTES:
                raise ValueError("Named camera PNG frame exceeds its byte bound")
        try:
            scanlines = zlib.decompress(bytes(compressed_scanlines))
        except zlib.error as exc:
            raise ValueError("Named camera PNG compressed pixels are invalid") from exc
        row_size = 1 + width * channels
        if len(scanlines) != height * row_size or any(
            scanlines[row * row_size] > 4 for row in range(height)
        ):
            raise ValueError("Named camera PNG scanline shape is invalid")
        frame_bytes = payload[frame_start:offset]
        frames.append(
            {
                "frame_bytes": frame_bytes,
                "encoding": "png",
                "width": width,
                "height": height,
                "channels": channels,
            }
        )
    if offset != len(payload):
        raise ValueError("Named camera PNG stream has extra trailing bytes or frames")
    return frames


def _stable_camera_discovery_identity(payload: dict[str, Any]) -> dict[str, Any]:
    avfoundation = payload.get("avfoundation_devices")
    system_cameras = payload.get("system_cameras")
    if not isinstance(avfoundation, list) or not isinstance(system_cameras, list):
        raise ValueError("Stable camera discovery fields are missing")
    names = [device.get("name") for device in avfoundation]
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("Stable AVFoundation camera name is malformed")
    if len(names) != len(set(names)):
        raise ValueError("Stable AVFoundation camera names are ambiguous")
    system_names = [camera.get("name") for camera in system_cameras]
    unique_ids = [camera.get("unique_id") for camera in system_cameras]
    if len(system_names) != len(set(system_names)):
        raise ValueError("Stable system camera names are ambiguous")
    if len(unique_ids) != len(set(unique_ids)):
        raise ValueError("Stable system camera unique IDs are ambiguous")
    if set(names) != set(system_names):
        raise ValueError("AVFoundation and system stable camera names differ")
    return {
        "avfoundation_names": sorted(names),
        "system_cameras": sorted(
            [copy.deepcopy(camera) for camera in system_cameras],
            key=lambda camera: (
                camera["name"],
                camera["unique_id"],
                camera["model_id"],
            ),
        ),
    }


def _injected_camera_backend_audit(
    *,
    camera: dict[str, Any],
    frame_count: int,
    framerate_fps: int,
) -> dict[str, Any]:
    return {
        "backend": "injected_finite_camera",
        "camera_identity_sha256": _sha256_payload(camera),
        "requested_framerate_fps": framerate_fps,
        "requested_input_mode": copy.deepcopy(camera["input_mode"]),
        "subprocess_start_attempts": 0,
        "subprocess_start_successes": 0,
        "subprocess_communicate_attempts": 0,
        "subprocess_communicate_successes": 0,
        "subprocess_wait_attempts": 0,
        "subprocess_wait_successes": 0,
        "subprocess_terminate_attempts": 0,
        "subprocess_terminate_successes": 0,
        "subprocess_kill_attempts": 0,
        "subprocess_kill_successes": 0,
        "release_attempts": 1,
        "release_successes": 1,
        "frames_delivered": frame_count,
        "capture_property_writes": 0,
        "continuous_recording_sessions": 0,
    }


def _verify_camera_backend_audit(
    payload: dict[str, Any],
    *,
    camera: dict[str, Any],
    expected_frame_count: int,
    expected_framerate_fps: int,
) -> None:
    count_fields = {
        "subprocess_start_attempts",
        "subprocess_start_successes",
        "subprocess_communicate_attempts",
        "subprocess_communicate_successes",
        "subprocess_wait_attempts",
        "subprocess_wait_successes",
        "subprocess_terminate_attempts",
        "subprocess_terminate_successes",
        "subprocess_kill_attempts",
        "subprocess_kill_successes",
        "release_attempts",
        "release_successes",
        "frames_delivered",
        "capture_property_writes",
        "continuous_recording_sessions",
    }
    allowed_fields = {
        "backend",
        "camera_identity_sha256",
        "requested_framerate_fps",
        "requested_input_mode",
        *count_fields,
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Camera backend audit fields are malformed")
    if payload.get("backend") not in {
        "ffmpeg_named_avfoundation",
        "injected_finite_camera",
    }:
        raise ValueError("Camera backend audit type is invalid")
    if payload.get("camera_identity_sha256") != _sha256_payload(camera):
        raise ValueError("Camera backend audit identity drifted")
    if (
        isinstance(payload.get("requested_framerate_fps"), bool)
        or payload.get("requested_framerate_fps") != expected_framerate_fps
        or expected_framerate_fps != CAMERA_FRAMERATE_FPS
    ):
        raise ValueError("Camera backend audit framerate drifted")
    if payload.get("requested_input_mode") != camera.get("input_mode"):
        raise ValueError("Camera backend audit input mode drifted")
    _normalize_camera_input_mode(payload["requested_input_mode"])
    if any(
        isinstance(payload.get(field), bool)
        or not isinstance(payload.get(field), int)
        or payload[field] < 0
        for field in count_fields
    ):
        raise ValueError("Camera backend audit count is malformed")
    if (
        payload["release_attempts"] != 1
        or payload["release_successes"] != 1
        or payload["frames_delivered"] != expected_frame_count
        or payload["capture_property_writes"] != 0
        or payload["continuous_recording_sessions"] != 0
    ):
        raise ValueError("Camera backend audit finite lifecycle drifted")
    if payload["backend"] == "ffmpeg_named_avfoundation":
        if (
            payload["subprocess_start_attempts"] != 1
            or payload["subprocess_start_successes"] != 1
            or payload["subprocess_communicate_attempts"] != 1
            or payload["subprocess_communicate_successes"] != 1
            or payload["subprocess_wait_attempts"] != 1
            or payload["subprocess_wait_successes"] != 1
            or payload["subprocess_terminate_attempts"] != 0
            or payload["subprocess_terminate_successes"] != 0
            or payload["subprocess_kill_attempts"] != 0
            or payload["subprocess_kill_successes"] != 0
        ):
            raise ValueError("Named camera accepted subprocess lifecycle drifted")
    elif any(
        payload[field] != 0 for field in count_fields if field.startswith("subprocess_")
    ):
        raise ValueError("Injected camera unexpectedly reported a subprocess")


def _verify_discovery_snapshot(payload: dict[str, Any]) -> None:
    allowed_fields = {
        "schema_version",
        "discovery_name",
        "session_id",
        "captured_at",
        "serial_candidates",
        "avfoundation_devices",
        "system_cameras",
        "serial_ports_opened",
        "cameras_opened",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Live discovery snapshot fields are malformed")
    discovery_schema = payload.get("schema_version")
    if discovery_schema not in {
        LIVE_DISCOVERY_SCHEMA_VERSION,
        LEGACY_LIVE_DISCOVERY_SCHEMA_VERSION,
    }:
        raise ValueError("Unsupported live discovery snapshot schema")
    verify_signed_payload(payload, label="Live discovery snapshot")
    if payload.get("discovery_name") != "pi05_live_readonly_metadata_discovery":
        raise ValueError("Live discovery snapshot name is invalid")
    require_nonblank(payload.get("session_id"), label="discovery session_id")
    _parse_time(payload.get("captured_at"), label="discovery captured_at")
    if payload.get("serial_ports_opened") != 0 or payload.get("cameras_opened") != 0:
        raise ValueError("Metadata discovery cannot claim opened devices")
    serials = payload.get("serial_candidates")
    cameras = payload.get("avfoundation_devices")
    system_cameras = payload.get("system_cameras")
    if (
        not isinstance(serials, list)
        or [_normalize_serial_candidate(item) for item in serials] != serials
    ):
        raise ValueError("Live discovery serial candidates are malformed")
    if (
        not isinstance(cameras, list)
        or [_normalize_avfoundation_device(item) for item in cameras] != cameras
    ):
        raise ValueError("Live discovery AVFoundation devices are malformed")
    if (
        not isinstance(system_cameras, list)
        or [
            _normalize_system_camera(
                item,
                allow_legacy=(
                    discovery_schema == LEGACY_LIVE_DISCOVERY_SCHEMA_VERSION
                ),
            )
            for item in system_cameras
        ]
        != system_cameras
    ):
        raise ValueError("Live discovery system cameras are malformed")


def _normalize_serial_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "device",
        "aliases",
        "vid",
        "pid",
        "serial_number",
        "manufacturer",
        "product",
        "location",
        "hwid",
    }
    if not isinstance(payload, dict) or set(payload) != fields:
        raise ValueError("Serial discovery candidate fields are malformed")
    device = require_nonblank(payload.get("device"), label="serial discovery device")
    aliases = payload.get("aliases")
    if not isinstance(aliases, list) or any(
        not isinstance(alias, str) or not alias for alias in aliases
    ):
        raise ValueError("Serial discovery aliases are malformed")
    aliases = sorted(set(aliases))
    if device in aliases:
        raise ValueError("Serial discovery aliases repeat the canonical device")
    for field in ("vid", "pid"):
        value = payload.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 0xFFFF
        ):
            raise ValueError(f"Serial discovery {field} is invalid")
    for field in ("serial_number", "manufacturer", "product", "location", "hwid"):
        value = payload.get(field)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Serial discovery {field} is invalid")
    return {
        "device": device,
        "aliases": aliases,
        "vid": payload.get("vid"),
        "pid": payload.get("pid"),
        "serial_number": payload.get("serial_number"),
        "manufacturer": payload.get("manufacturer"),
        "product": payload.get("product"),
        "location": payload.get("location"),
        "hwid": payload.get("hwid"),
    }


def _normalize_avfoundation_device(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"index", "name"}:
        raise ValueError("AVFoundation device fields are malformed")
    index = payload.get("index")
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("AVFoundation camera index is invalid")
    return {
        "index": index,
        "name": require_nonblank(payload.get("name"), label="AVFoundation camera name"),
    }


def _normalize_system_camera(
    payload: dict[str, Any],
    *,
    allow_legacy: bool = False,
) -> dict[str, Any]:
    expected_fields = {"name", "unique_id", "model_id"}
    if not allow_legacy:
        expected_fields.add("supported_modes")
    if not isinstance(payload, dict) or set(payload) != expected_fields:
        raise ValueError("System camera fields are malformed")
    result = {
        "name": require_nonblank(payload.get("name"), label="system camera name"),
        "unique_id": require_nonblank(
            payload.get("unique_id"), label="system camera unique_id"
        ),
        "model_id": require_nonblank(
            payload.get("model_id"), label="system camera model_id"
        ),
    }
    if allow_legacy:
        return result
    modes = payload.get("supported_modes")
    if not isinstance(modes, list) or not modes:
        raise ValueError("System camera supported modes are empty")
    normalized = [_normalize_camera_supported_mode(mode) for mode in modes]
    ordered = sorted(normalized, key=_camera_supported_mode_sort_key)
    if normalized != ordered:
        raise ValueError("System camera supported modes are not normalized")
    if len({_camera_supported_mode_key(item) for item in ordered}) != len(ordered):
        raise ValueError("System camera supported modes contain duplicates")
    result["supported_modes"] = ordered
    return result


def _normalize_camera_supported_mode(payload: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "pixel_format",
        "width",
        "height",
        "min_framerate_fps",
        "max_framerate_fps",
    }
    if not isinstance(payload, dict) or set(payload) != fields:
        raise ValueError("Camera supported-mode fields are malformed")
    pixel_format = payload.get("pixel_format")
    if pixel_format not in CAMERA_PIXEL_FORMAT_PRIORITY:
        raise ValueError("Camera supported pixel format is not reviewed")
    width = payload.get("width")
    height = payload.get("height")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 8192
        for value in (width, height)
    ):
        raise ValueError("Camera supported-mode dimensions are invalid")
    minimum = payload.get("min_framerate_fps")
    maximum = payload.get("max_framerate_fps")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        for value in (minimum, maximum)
    ):
        raise ValueError("Camera supported-mode framerate bounds are invalid")
    minimum = float(minimum)
    maximum = float(maximum)
    if minimum <= 0 or maximum < minimum or maximum > 240:
        raise ValueError("Camera supported-mode framerate bounds are invalid")
    return {
        "pixel_format": pixel_format,
        "width": width,
        "height": height,
        "min_framerate_fps": minimum,
        "max_framerate_fps": maximum,
    }


def _camera_supported_mode_key(mode: dict[str, Any]) -> tuple[Any, ...]:
    return (
        mode["pixel_format"],
        mode["width"],
        mode["height"],
        mode["min_framerate_fps"],
        mode["max_framerate_fps"],
    )


def _camera_supported_mode_sort_key(mode: dict[str, Any]) -> tuple[Any, ...]:
    return (
        mode["width"] * mode["height"],
        mode["width"],
        mode["height"],
        CAMERA_PIXEL_FORMAT_PRIORITY.index(mode["pixel_format"]),
        mode["min_framerate_fps"],
        mode["max_framerate_fps"],
    )


def select_camera_input_mode(camera: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_system_camera(camera)
    candidates = [
        mode
        for mode in normalized["supported_modes"]
        if (
            mode["min_framerate_fps"] - CAMERA_FRAMERATE_MATCH_TOLERANCE_FPS
            <= CAMERA_FRAMERATE_FPS
            <= mode["max_framerate_fps"]
            + CAMERA_FRAMERATE_MATCH_TOLERANCE_FPS
        )
    ]
    if not candidates:
        raise ValueError("Camera has no signed supported mode at exact 30 fps")
    selected = min(candidates, key=_camera_supported_mode_sort_key)
    return _normalize_camera_input_mode({
        "pixel_format": selected["pixel_format"],
        "width": selected["width"],
        "height": selected["height"],
        "framerate_fps": CAMERA_FRAMERATE_FPS,
    })


def _normalize_camera_input_mode(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "pixel_format",
        "width",
        "height",
        "framerate_fps",
    }:
        raise ValueError("Selected camera input-mode fields are malformed")
    pixel_format = payload.get("pixel_format")
    width = payload.get("width")
    height = payload.get("height")
    framerate = payload.get("framerate_fps")
    if pixel_format not in CAMERA_PIXEL_FORMAT_PRIORITY:
        raise ValueError("Selected camera input pixel format is not reviewed")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 8192
        for value in (width, height)
    ):
        raise ValueError("Selected camera input dimensions are invalid")
    if (
        isinstance(framerate, bool)
        or not isinstance(framerate, int)
        or framerate != CAMERA_FRAMERATE_FPS
    ):
        raise ValueError("Selected camera input framerate drifted")
    return {
        "pixel_format": pixel_format,
        "width": width,
        "height": height,
        "framerate_fps": framerate,
    }


def _require_frame_dimensions_match_camera(
    frame: dict[str, Any],
    *,
    camera: dict[str, Any],
) -> None:
    if not isinstance(frame, dict):
        raise ValueError("Captured camera frame metadata is malformed")
    input_mode = _normalize_camera_input_mode(camera.get("input_mode"))
    dimensions = (frame.get("width"), frame.get("height"))
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in dimensions
    ):
        raise ValueError("Captured camera frame dimensions are malformed")
    if dimensions != (input_mode["width"], input_mode["height"]):
        raise ValueError(
            "Captured camera frame dimensions drifted from the signed input mode"
        )


def _merge_serial_aliases(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for record in records:
        normalized = _normalize_serial_candidate(record)
        key = tuple(
            normalized[field]
            for field in (
                "vid",
                "pid",
                "serial_number",
                "manufacturer",
                "product",
                "location",
                "hwid",
            )
        )
        groups.setdefault(key, []).append(normalized)
    merged = []
    for group in groups.values():
        paths = sorted(
            {path for item in group for path in [item["device"], *item["aliases"]]}
        )
        canonical = next(
            (path for path in paths if path.startswith("/dev/cu.")), paths[0]
        )
        base = dict(group[0])
        base["device"] = canonical
        base["aliases"] = sorted(set(paths) - {canonical})
        merged.append(_normalize_serial_candidate(base))
    return sorted(merged, key=lambda item: item["device"])


def _calibration_reference(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if resolved != DEFAULT_FOLLOWER_CALIBRATION_PATH.resolve():
        raise ValueError(
            "Live execution calibration path is not the pinned follower calibration"
        )
    if not resolved.is_file():
        raise ValueError("Pinned follower calibration file is missing")
    return {
        "path": str(resolved),
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        "size_bytes": resolved.stat().st_size,
    }


def _verify_live_servo_result(
    payload: dict[str, Any],
    *,
    execution_contract: dict[str, Any],
) -> None:
    allowed_fields = {
        "schema_version",
        "result_name",
        "qualification_scope",
        "evidence_mode",
        "proof_label",
        "execution_contract_identity_sha256",
        "census_contract_identity_sha256",
        "observation_started_monotonic_ns",
        "observation_finished_monotonic_ns",
        "transport_trace",
        "target_device_identity",
        "servos",
        "operation_counts",
        "hardware_opened",
        "physical_follower_commanded",
        "lifecycle_state",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Live servo result fields are malformed")
    if payload.get("schema_version") != LIVE_SERVO_RESULT_SCHEMA_VERSION:
        raise ValueError("Unsupported live servo result schema")
    verify_signed_payload(payload, label="Live servo result")
    if payload.get("proof_label") != "live_read_only_census_observed":
        raise ValueError("Live servo result proof label is invalid")
    if payload.get("result_name") != "pi05_live_readonly_servo_census":
        raise ValueError("Live servo result name is invalid")
    if payload.get("evidence_mode") != "live_physical_read_only":
        raise ValueError("Live servo evidence mode is invalid")
    if payload.get("qualification_scope") != "physical_observation":
        raise ValueError("Live servo result scope is invalid")
    if (
        payload.get("execution_contract_identity_sha256")
        != execution_contract["identity_sha256"]
    ):
        raise ValueError("Live servo result execution linkage drifted")
    if (
        payload.get("census_contract_identity_sha256")
        != execution_contract["live_census_contract"]["identity_sha256"]
    ):
        raise ValueError("Live servo result census linkage drifted")
    census_contract = execution_contract["live_census_contract"]
    target = census_contract["target_device_identity"]
    expected_device_identity = {
        "device_role": target["device_role"],
        "usb": {
            "vendor_id_hex": target["usb"]["vendor_id_hex"],
            "product_id_hex": target["usb"]["product_id_hex"],
            "serial_number": target["usb"]["serial_number"],
            "canonical_path": target["usb"]["canonical_path"],
            "observed_aliases": target["usb"]["allowed_aliases"],
        },
        "bus": target["bus"],
    }
    if payload.get("target_device_identity") != expected_device_identity:
        raise ValueError("Live servo result target device identity drifted")
    if payload.get("hardware_opened") is not True:
        raise ValueError("Live servo result must record hardware opened")
    if payload.get("physical_follower_commanded") is not False:
        raise ValueError("Live servo result cannot command the follower")
    if payload.get("lifecycle_state") != "closed":
        raise ValueError("Live servo result lifecycle is not closed")
    started = payload.get("observation_started_monotonic_ns")
    finished = payload.get("observation_finished_monotonic_ns")
    if (
        isinstance(started, bool)
        or not isinstance(started, int)
        or isinstance(finished, bool)
        or not isinstance(finished, int)
        or finished <= started
    ):
        raise ValueError("Live servo observation interval is invalid")
    counts = payload.get("operation_counts")
    expected_count_fields = {
        "construct_attempts",
        "construct_successes",
        "connect_attempts",
        "connect_successes",
        "read_attempts",
        "read_successes",
        "read_retries",
        "close_attempts",
        "close_successes",
        "motor_register_writes",
        "torque_changes",
        "motion_commands",
        "unexpected_operations",
    }
    if not isinstance(counts, dict) or set(counts) != expected_count_fields:
        raise ValueError("Live servo operation counts are missing")
    for field in expected_count_fields:
        value = counts[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"Live servo result count is invalid: {field}")
    for field in (
        "construct_attempts",
        "construct_successes",
        "connect_attempts",
        "connect_successes",
        "close_attempts",
        "close_successes",
    ):
        if counts[field] != 1:
            raise ValueError(f"Live servo lifecycle count drifted: {field}")
    for field in (
        "motor_register_writes",
        "torque_changes",
        "motion_commands",
        "unexpected_operations",
    ):
        if counts.get(field) != 0:
            raise ValueError(f"Live servo result has a nonzero unsafe count: {field}")
    trace = payload.get("transport_trace")
    if not isinstance(trace, list) or not trace:
        raise ValueError("Live servo transport trace is missing")
    if [event.get("sequence") for event in trace] != list(range(len(trace))):
        raise ValueError("Live servo transport trace sequence drifted")
    timestamps = [event.get("monotonic_ns") for event in trace]
    if (
        any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in timestamps
        )
        or timestamps != sorted(set(timestamps))
        or timestamps[0] <= started
        or timestamps[-1] >= finished
    ):
        raise ValueError("Live servo transport trace timestamps are invalid")
    operations = [event.get("operation") for event in trace]
    if operations[0] != "connect" or operations[-1] != "disconnect":
        raise ValueError("Live servo transport lifecycle is invalid")
    if operations.count("connect") != 1 or operations.count("disconnect") != 1:
        raise ValueError("Live servo transport lifecycle is ambiguous")
    if any(
        operation not in {"connect", "read", "disconnect"} for operation in operations
    ):
        raise ValueError("Live servo transport trace contains an unexpected operation")
    if set(trace[0]) != {
        "sequence",
        "operation",
        "monotonic_ns",
        "handshake",
        "outcome",
    } or trace[0].get("handshake") is not False:
        raise ValueError("Live servo transport trace used a handshake")
    if set(trace[-1]) != {
        "sequence",
        "operation",
        "monotonic_ns",
        "disable_torque",
        "outcome",
    } or trace[-1].get("disable_torque") is not False:
        raise ValueError("Live servo transport trace changed torque on close")
    if trace[0].get("outcome") != "success" or trace[-1].get("outcome") != "success":
        raise ValueError("Live servo transport connect or close failed")
    read_events = trace[1:-1]
    if len(read_events) != counts.get("read_attempts"):
        raise ValueError("Live servo read trace count drifted")
    raw_by_servo, reconstructed_retries = _reconstruct_live_servo_reads(
        read_events,
        census_contract=census_contract,
    )
    expected_read_successes = len(census_contract["expected_servos"]) * len(
        census_contract["read_plan"]
    )
    if (
        counts["read_successes"] != expected_read_successes
        or counts["read_retries"] != reconstructed_retries
        or counts["read_attempts"] != expected_read_successes + reconstructed_retries
    ):
        raise ValueError("Live servo read and retry counts drifted")
    decoded = decode_readonly_servo_observations(
        contract=census_contract,
        raw_by_servo=raw_by_servo,
    )
    if payload.get("servos") != decoded:
        raise ValueError("Live servo decoded evidence drifted from the transport trace")


def _reconstruct_live_servo_reads(
    read_events: list[dict[str, Any]],
    *,
    census_contract: dict[str, Any],
) -> tuple[dict[int, dict[str, int]], int]:
    cursor = 0
    retry_count = 0
    raw_by_servo: dict[int, dict[str, int]] = {}
    max_retries = census_contract["retry_policy"]["max_read_retries"]
    for servo in census_contract["expected_servos"]:
        servo_id = servo["servo_id"]
        motor = servo["joint_name"]
        raw_by_servo[servo_id] = {}
        for plan in census_contract["read_plan"]:
            register = plan["register"]
            attempts = 0
            while True:
                if cursor >= len(read_events):
                    raise ValueError("Live servo trace is missing an allowlisted read")
                event = read_events[cursor]
                cursor += 1
                attempts += 1
                common_fields = {
                    "sequence",
                    "operation",
                    "monotonic_ns",
                    "register",
                    "motor",
                    "normalize",
                    "num_retry",
                    "outcome",
                }
                if (
                    event.get("operation") != "read"
                    or event.get("motor") != motor
                    or event.get("register") != register
                    or event.get("normalize") is not False
                    or event.get("num_retry") != 0
                ):
                    raise ValueError("Live servo trace read order or flags drifted")
                outcome = event.get("outcome")
                if outcome == "transient_error":
                    if set(event) != common_fields | {"error_type"}:
                        raise ValueError("Live servo transient read fields are malformed")
                    require_nonblank(
                        event.get("error_type"),
                        label="live servo transient error type",
                    )
                    retry_count += 1
                    if attempts > max_retries:
                        raise ValueError("Live servo trace retry bound was exceeded")
                    continue
                if outcome != "success" or set(event) != common_fields | {"raw_value"}:
                    raise ValueError("Live servo successful read fields are malformed")
                raw_value = event.get("raw_value")
                if isinstance(raw_value, bool) or not isinstance(raw_value, int):
                    raise ValueError("Live servo trace contains a malformed raw value")
                raw_by_servo[servo_id][register] = raw_value
                break
    if cursor != len(read_events):
        raise ValueError("Live servo trace contains extra reads")
    return raw_by_servo, retry_count


def _verify_captured_frames(
    frames: list[dict[str, Any]],
    *,
    execution_contract: dict[str, Any],
) -> None:
    expected_count = (
        len(execution_contract["cameras"])
        * execution_contract["frame_count_per_camera"]
    )
    if not isinstance(frames, list) or len(frames) != expected_count:
        raise ValueError("Captured frame count drifted from the execution contract")
    expected_cameras = {
        camera["index"]: camera for camera in execution_contract["cameras"]
    }
    for frame in frames:
        camera = frame.get("camera")
        if (
            not isinstance(camera, dict)
            or expected_cameras.get(camera.get("index")) != camera
        ):
            raise ValueError("Captured frame camera identity drifted")
        frame_bytes = frame.get("frame_bytes")
        if not isinstance(frame_bytes, bytes) or hashlib.sha256(
            frame_bytes
        ).hexdigest() != frame.get("frame_sha256"):
            raise ValueError("Captured frame content hash is invalid")
        _require_frame_dimensions_match_camera(frame, camera=camera)
        _verify_camera_backend_audit(
            frame.get("camera_backend_audit"),
            camera=camera,
            expected_frame_count=execution_contract["frame_count_per_camera"],
            expected_framerate_fps=execution_contract["camera_framerate_fps"],
        )


def _verify_private_bundle_refs(
    payload: dict[str, Any],
    *,
    private_evidence: dict[str, Any],
) -> None:
    if not isinstance(payload, dict) or set(payload) != {"evidence", "frames"}:
        raise ValueError("Private observation bundle refs are malformed")
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict) or set(evidence) != {
        "filename",
        "sha256",
        "size_bytes",
    }:
        raise ValueError("Private observation evidence ref is malformed")
    expected_evidence_bytes = (
        json.dumps(
            private_evidence,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if evidence != {
        "filename": "private_observation.json",
        "sha256": hashlib.sha256(expected_evidence_bytes).hexdigest(),
        "size_bytes": len(expected_evidence_bytes),
    }:
        raise ValueError("Private observation evidence ref drifted")
    frames = payload.get("frames")
    if not isinstance(frames, list) or len(frames) != len(private_evidence["frames"]):
        raise ValueError("Private frame refs are incomplete")
    expected_frame_hashes = {
        frame["private_relative_path"]: frame["frame_sha256"]
        for frame in private_evidence["frames"]
    }
    if {frame.get("filename") for frame in frames} != set(expected_frame_hashes):
        raise ValueError("Private frame ref filenames drifted")
    for frame in frames:
        if not isinstance(frame, dict) or set(frame) != {
            "filename",
            "sha256",
            "size_bytes",
        }:
            raise ValueError("Private frame ref is malformed")
        _require_sha256(frame.get("sha256"), label="private frame file hash")
        if frame["sha256"] != expected_frame_hashes[frame["filename"]]:
            raise ValueError("Private frame ref content hash drifted")
        if (
            isinstance(frame.get("size_bytes"), bool)
            or not isinstance(frame.get("size_bytes"), int)
            or frame["size_bytes"] <= 0
        ):
            raise ValueError("Private frame ref size is invalid")


def _parse_time(value: Any, *, label: str) -> datetime:
    text = require_nonblank(value, label=label)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a UTC offset")
    return parsed


def _validated_wall_time(value: Any) -> str:
    text = require_nonblank(value, label="camera host wall time")
    _parse_time(text, label="camera host wall time")
    return text


def _paired_tty_alias(path: str) -> str:
    return path.replace("/dev/cu.", "/dev/tty.", 1)


def _require_sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
