"""Bounded live read-only SO-101 census and finite camera evidence."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import queue
import re
import subprocess
import sys
import threading

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
    run_readonly_census,
    verify_live_census_contract,
)


OPERATOR_PRESENCE_LEASE_SCHEMA_VERSION = "scenesmith.operator_presence_lease.v1"
LIVE_DISCOVERY_SCHEMA_VERSION = "scenesmith.live_readonly_discovery.v1"
LIVE_EXECUTION_CONTRACT_SCHEMA_VERSION = (
    "scenesmith.live_readonly_observation_contract.v1"
)
LIVE_SERVO_RESULT_SCHEMA_VERSION = "scenesmith.live_readonly_servo_result.v1"
PRIVATE_OBSERVATION_SCHEMA_VERSION = "scenesmith.live_readonly_observation_private.v1"
REDACTED_MANIFEST_SCHEMA_VERSION = "scenesmith.live_readonly_observation_manifest.v1"

MAX_PRESENCE_LEASE_SECONDS = 600
MAX_EXECUTION_DURATION_SECONDS = 120
DEFAULT_FRAME_COUNT_PER_CAMERA = 2
CAMERA_READ_TIMEOUT_SECONDS = 5
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
    for field in ("serial_number", "manufacturer", "product", "location", "hwid"):
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
    aliases = sorted(follower_paths - {KNOWN_PHYSICAL_FOLLOWER_PORT})
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
    for field in (
        "serial_candidates",
        "avfoundation_devices",
        "system_cameras",
    ):
        if expected[field] != observed[field]:
            raise ValueError(f"Discovery stability check detected {field} drift")


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


def parse_system_camera_devices(payload: dict[str, Any]) -> list[dict[str, Any]]:
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
    normalized = [_normalize_system_camera(camera) for camera in observed]
    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for camera in normalized:
        unique[(camera["name"], camera["unique_id"], camera["model_id"])] = camera
    return list(unique.values())


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
    result: list[dict[str, Any]] = []
    for index in sorted(camera_indexes):
        av_device = av_by_index.get(index)
        if av_device is None:
            raise ValueError(f"Selected AVFoundation camera index is missing: {index}")
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
    previous_timestamp = -1
    for camera in execution_contract["cameras"]:
        instance: FiniteCamera | None = None
        primary_error: BaseException | None = None
        release_error: BaseException | None = None
        try:
            instance = camera_factory(copy.deepcopy(camera))
            instance.open()
            for frame_index in range(execution_contract["frame_count_per_camera"]):
                started = monotonic_ns()
                frame = instance.read()
                finished = monotonic_ns()
                if started <= previous_timestamp or finished < started:
                    raise ValueError("Camera timestamps regressed")
                previous_timestamp = finished
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
        if primary_error is not None and release_error is not None:
            raise BaseExceptionGroup(
                "Camera capture failed and release also failed",
                [primary_error, release_error],
            )
        if primary_error is not None:
            raise primary_error
        if release_error is not None:
            raise release_error
    return frames


def build_private_observation_evidence(
    *,
    execution_contract: dict[str, Any],
    servo_result: dict[str, Any],
    frames: list[dict[str, Any]],
    pre_open_discovery: dict[str, Any],
    post_close_discovery: dict[str, Any],
) -> dict[str, Any]:
    _verify_live_servo_result(servo_result, execution_contract=execution_contract)
    _verify_captured_frames(frames, execution_contract=execution_contract)
    verify_discovery_stability(execution_contract["discovery"], pre_open_discovery)
    verify_discovery_stability(execution_contract["discovery"], post_close_discovery)
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
        "discovery_stability": "exact_metadata_match_before_open_and_after_close",
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
            "continuous_recording_sessions": 0,
        },
        "transport_trace": copy.deepcopy(servo_result["transport_trace"]),
        "servo_observation_interval_monotonic_ns": [
            servo_result["observation_started_monotonic_ns"],
            servo_result["observation_finished_monotonic_ns"],
        ],
        "cameras": copy.deepcopy(execution_contract["cameras"]),
        "frames": frame_metadata,
        "max_host_observed_skew_ns": max(skews),
        "timestamp_scope": "host_receive_intervals_not_hardware_clock_sync",
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
    verify_signed_payload(private_evidence, label="Private observation evidence")
    _verify_private_bundle_refs(private_bundle_refs, private_evidence=private_evidence)
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
            for frame in private_evidence["frames"]
            if frame["camera"]["index"] == camera["index"]
        ]
        cameras.append(
            {
                "camera_identity_sha256": _sha256_payload(camera),
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
        "discovery_stability": private_evidence["discovery_stability"],
        "pre_open_discovery_identity_sha256": private_evidence[
            "pre_open_discovery_identity_sha256"
        ],
        "post_close_discovery_identity_sha256": private_evidence[
            "post_close_discovery_identity_sha256"
        ],
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
        records.append(
            {
                "device": port.device,
                "aliases": [],
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
    return (
        parse_avfoundation_video_devices(
            "\n".join((avfoundation.stdout, avfoundation.stderr))
        ),
        parse_system_camera_devices(json.loads(profiler.stdout)),
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


class OpenCVFiniteCamera:
    """Open one AVFoundation camera without changing capture properties."""

    def __init__(
        self,
        index: int,
        *,
        read_timeout_seconds: int = CAMERA_READ_TIMEOUT_SECONDS,
    ):
        self._index = index
        self._read_timeout_seconds = read_timeout_seconds
        self._capture: Any = None
        self._cv2: Any = None

    def open(self) -> None:
        import cv2

        self._cv2 = cv2
        self._capture = cv2.VideoCapture(self._index, cv2.CAP_AVFOUNDATION)
        if not self._capture.isOpened():
            raise ConnectionError(f"Failed to open AVFoundation camera {self._index}")

    def read(self) -> dict[str, Any]:
        if self._capture is None or self._cv2 is None:
            raise RuntimeError("Camera is not open")
        result_queue: queue.Queue[tuple[bool, Any] | BaseException] = queue.Queue(
            maxsize=1
        )

        def worker() -> None:
            try:
                result_queue.put(self._capture.read())
            except BaseException as exc:
                result_queue.put(exc)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        try:
            result = result_queue.get(timeout=self._read_timeout_seconds)
        except queue.Empty as exc:
            raise TimeoutError(
                f"AVFoundation camera {self._index} read exceeded "
                f"{self._read_timeout_seconds}s"
            ) from exc
        if isinstance(result, BaseException):
            raise result
        success, frame = result
        if not success or frame is None:
            raise RuntimeError(f"AVFoundation camera {self._index} read failed")
        success, encoded = self._cv2.imencode(".png", frame)
        if not success:
            raise RuntimeError(f"AVFoundation camera {self._index} PNG encoding failed")
        height, width, channels = frame.shape
        return {
            "frame_bytes": encoded.tobytes(),
            "encoding": "png",
            "width": int(width),
            "height": int(height),
            "channels": int(channels),
        }

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None


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
    if payload.get("schema_version") != LIVE_DISCOVERY_SCHEMA_VERSION:
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
        or [_normalize_system_camera(item) for item in system_cameras] != system_cameras
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


def _normalize_system_camera(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "name",
        "unique_id",
        "model_id",
    }:
        raise ValueError("System camera fields are malformed")
    return {
        "name": require_nonblank(payload.get("name"), label="system camera name"),
        "unique_id": require_nonblank(
            payload.get("unique_id"), label="system camera unique_id"
        ),
        "model_id": require_nonblank(
            payload.get("model_id"), label="system camera model_id"
        ),
    }


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
    if not isinstance(counts, dict):
        raise ValueError("Live servo operation counts are missing")
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
    if trace[0].get("handshake") is not False:
        raise ValueError("Live servo transport trace used a handshake")
    if trace[-1].get("disable_torque") is not False:
        raise ValueError("Live servo transport trace changed torque on close")
    if trace[0].get("outcome") != "success" or trace[-1].get("outcome") != "success":
        raise ValueError("Live servo transport connect or close failed")
    read_events = [event for event in trace if event.get("operation") == "read"]
    if len(read_events) != counts.get("read_attempts"):
        raise ValueError("Live servo read trace count drifted")
    if sum(event.get("outcome") == "success" for event in read_events) != counts.get(
        "read_successes"
    ):
        raise ValueError("Live servo successful read count drifted")
    if sum(
        event.get("outcome") == "transient_error" for event in read_events
    ) != counts.get("read_retries"):
        raise ValueError("Live servo retry trace count drifted")
    for event in read_events:
        if event.get("register") not in EXPECTED_READ_REGISTER_WIDTHS:
            raise ValueError("Live servo trace contains an unknown register")
        if event.get("motor") not in _EXPECTED_SERVO_NAMES:
            raise ValueError("Live servo trace contains an unknown motor")
        if event.get("normalize") is not False or event.get("num_retry") != 0:
            raise ValueError("Live servo trace read flags drifted")
        if event.get("outcome") not in {"success", "transient_error"}:
            raise ValueError("Live servo trace contains an invalid read outcome")
        if event.get("outcome") == "success":
            value = event.get("raw_value")
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("Live servo trace contains a malformed raw value")


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
