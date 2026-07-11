"""Injected fixture runtime for the static-pose bracket lifecycle contract."""

from __future__ import annotations

import copy
import hashlib

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.live_readonly_observation import (
    require_no_serial_identity_holders,
    verify_serial_identity_holder_snapshot,
    verify_serial_identity_holder_stability,
)
from scenesmith.robot_lab.static_pose_bracket import (
    EXPECTED_OPERATION_COUNTS,
    STATIC_POSE_BRACKET_OBSERVATION_SCHEMA_VERSION,
    evaluate_static_pose_bracket,
    verify_static_pose_bracket_contract,
    verify_static_pose_bracket_result,
)


STATIC_POSE_BRACKET_RUNTIME_RESULT_SCHEMA_VERSION = (
    "scenesmith.static_pose_bracket_runtime_result.v2"
)
MAX_FIXTURE_FRAME_BYTES = 8 * 1024 * 1024

_RUNTIME_AUTHORITY_NOT_GRANTED = [
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]


class StaticPoseTransport(Protocol):
    @property
    def evidence_mode(self) -> str: ...

    @property
    def is_connected(self) -> bool: ...

    def connect(self) -> None: ...

    def read_position(self, joint_name: str, servo_id: int) -> int: ...

    def close(self) -> None: ...

    def audit(self) -> dict[str, Any]: ...


class FiniteStaticPoseCamera(Protocol):
    def open(self) -> None: ...

    def read(self) -> dict[str, Any]: ...

    def release(self) -> None: ...

    def audit(self) -> dict[str, Any]: ...


class InjectedStaticPoseBusAdapter:
    """Expose only no-handshake read and no-torque close on an injected bus."""

    def __init__(self, *, backend: Any, servo_names: dict[int, str]):
        if set(servo_names) != set(range(1, 7)):
            raise ValueError("Static pose adapter requires exact servo IDs 1-6")
        if len(set(servo_names.values())) != 6:
            raise ValueError("Static pose adapter servo names must be unique")
        self._backend = backend
        self._servo_names = dict(servo_names)
        self._is_connected = False
        self._connect_attempted = False
        self._closed = False
        self._audit = {
            "hardware_opened": False,
            "connect_calls": 0,
            "read_calls": 0,
            "close_calls": 0,
            "motor_register_writes": 0,
            "configuration_writes": 0,
            "torque_changes": 0,
            "motion_commands": 0,
            "unexpected_operations": 0,
            "physical_follower_commanded": False,
        }

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def evidence_mode(self) -> str:
        return "live_injected_transport"

    def connect(self) -> None:
        if self._connect_attempted or self._closed:
            self._audit["unexpected_operations"] += 1
            raise RuntimeError("Static pose adapter connect lifecycle is invalid")
        self._audit["connect_calls"] += 1
        self._audit["hardware_opened"] = True
        self._connect_attempted = True
        self._backend.connect(handshake=False)
        self._is_connected = True

    def read_position(self, joint_name: str, servo_id: int) -> int:
        if not self._is_connected:
            self._audit["unexpected_operations"] += 1
            raise RuntimeError("Static pose adapter is disconnected")
        expected_name = self._servo_names.get(servo_id)
        if expected_name != joint_name:
            self._audit["unexpected_operations"] += 1
            raise ValueError("Static pose adapter servo identity mismatch")
        self._audit["read_calls"] += 1
        return self._backend.read(
            "Present_Position",
            joint_name,
            normalize=False,
            num_retry=0,
        )

    def close(self) -> None:
        if self._closed:
            self._audit["unexpected_operations"] += 1
            raise RuntimeError("Static pose adapter close called more than once")
        self._audit["close_calls"] += 1
        self._closed = True
        if self._connect_attempted:
            try:
                self._backend.disconnect(disable_torque=False)
            finally:
                self._connect_attempted = False
                self._is_connected = False
        else:
            self._is_connected = False

    def audit(self) -> dict[str, Any]:
        return copy.deepcopy(self._audit)


def run_static_pose_bracket_fixture_runtime(
    contract: dict[str, Any],
    *,
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    transport_factory: Callable[[], StaticPoseTransport],
    camera_factory: Callable[[dict[str, Any]], FiniteStaticPoseCamera],
    pre_open_holder_snapshot: dict[str, Any],
    post_close_holder_snapshot_factory: Callable[[], dict[str, Any]],
    monotonic_ns: Callable[[], int],
) -> dict[str, Any]:
    """Execute the complete fixture lifecycle with cleanup on every failure."""

    verify_static_pose_bracket_contract(
        contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
    )
    require_no_serial_identity_holders(pre_open_holder_snapshot)
    strict_clock = _StrictMonotonicClock(monotonic_ns)
    lifecycle_events = ["pre_open_holder"]
    counts = {field: 0 for field in EXPECTED_OPERATION_COUNTS}
    transport: StaticPoseTransport | None = None
    q_before: list[dict[str, Any]] = []
    q_after: list[dict[str, Any]] = []
    camera_batches: list[dict[str, Any]] = []
    camera_audits: list[dict[str, Any]] = []
    timing: dict[str, int] = {}
    primary_error: BaseException | None = None
    close_error: BaseException | None = None
    post_holder_error: BaseException | None = None
    post_close_holder_snapshot: dict[str, Any] | None = None

    try:
        counts["construct_attempts"] += 1
        transport = transport_factory()
        counts["construct_successes"] += 1
        lifecycle_events.append("construct")
        if transport.evidence_mode != "deterministic_fixture":
            raise ValueError(
                "Static pose fixture runtime refuses a non-fixture transport"
            )

        counts["connect_attempts"] += 1
        transport.connect()
        counts["connect_successes"] += 1
        lifecycle_events.append("connect")
        if not transport.is_connected:
            raise RuntimeError("Static pose transport did not report connected state")

        timing["q_before_started_monotonic_ns"] = _monotonic(strict_clock)
        q_before = _read_position_phase(
            contract,
            transport=transport,
            phase="q_before",
            counts=counts,
            lifecycle_events=lifecycle_events,
        )
        timing["q_before_finished_monotonic_ns"] = _monotonic(strict_clock)

        for camera_index, camera in enumerate(contract["cameras"]):
            counts["camera_batch_attempts"] += 1
            batch, audit, interval = _capture_camera_batch(
                camera,
                camera_index=camera_index,
                transport=transport,
                camera_factory=camera_factory,
                monotonic_ns=strict_clock,
                lifecycle_events=lifecycle_events,
            )
            counts["camera_batch_successes"] += 1
            counts["camera_frame_reads"] += len(batch["frames"])
            camera_batches.append(batch)
            camera_audits.append(audit)
            if camera_index == 0:
                timing["camera_receive_started_monotonic_ns"] = interval[0]
            timing["camera_receive_finished_monotonic_ns"] = interval[1]

        timing["q_after_started_monotonic_ns"] = _monotonic(strict_clock)
        q_after = _read_position_phase(
            contract,
            transport=transport,
            phase="q_after",
            counts=counts,
            lifecycle_events=lifecycle_events,
        )
        timing["q_after_finished_monotonic_ns"] = _monotonic(strict_clock)
    except BaseException as exc:
        primary_error = exc
    finally:
        if transport is not None:
            counts["close_attempts"] += 1
            try:
                transport.close()
                counts["close_successes"] += 1
                lifecycle_events.append("close")
            except BaseException as exc:
                close_error = exc
        if counts["construct_attempts"]:
            try:
                post_close_holder_snapshot = post_close_holder_snapshot_factory()
                require_no_serial_identity_holders(post_close_holder_snapshot)
                verify_serial_identity_holder_stability(
                    pre_open_holder_snapshot,
                    post_close_holder_snapshot,
                )
                lifecycle_events.append("post_close_holder")
            except BaseException as exc:
                post_holder_error = exc

    errors = [
        error
        for error in (primary_error, close_error, post_holder_error)
        if error is not None
    ]
    if len(errors) > 1:
        raise BaseExceptionGroup(
            "Static pose runtime failed and cleanup evidence also failed",
            errors,
        )
    if errors:
        raise errors[0]
    if transport is None or post_close_holder_snapshot is None:
        raise RuntimeError("Static pose runtime lifecycle is incomplete")
    if transport.is_connected:
        raise RuntimeError("Static pose transport remained connected after close")

    transport_audit = _validate_transport_audit(
        transport.audit(),
        expected_hardware_opened=False,
    )
    _apply_transport_audit_counts(counts, audit=transport_audit)
    if counts != EXPECTED_OPERATION_COUNTS:
        raise ValueError("Static pose runtime operation counts drifted")
    _validate_camera_audits(camera_audits, contract=contract)
    if lifecycle_events != _expected_lifecycle_events(contract):
        raise ValueError("Static pose runtime lifecycle order drifted")

    observation = sign_payload(
        {
            "schema_version": STATIC_POSE_BRACKET_OBSERVATION_SCHEMA_VERSION,
            "observation_name": "pi05_static_pose_bracket_fixture_observation",
            "evidence_mode": "deterministic_fixture",
            "contract_identity_sha256": contract["identity_sha256"],
            "timing": timing,
            "q_before": q_before,
            "cameras": camera_batches,
            "q_after": q_after,
            "operation_counts": dict(counts),
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "fixture_only": True,
        }
    )
    evaluation = evaluate_static_pose_bracket(
        contract=contract,
        observation=observation,
    )
    result = _build_runtime_result(
        contract=contract,
        pre_open_holder_snapshot=pre_open_holder_snapshot,
        post_close_holder_snapshot=post_close_holder_snapshot,
        observation=observation,
        evaluation=evaluation,
        transport_audit=transport_audit,
        camera_audits=camera_audits,
        lifecycle_events=lifecycle_events,
        operation_counts=counts,
    )
    verify_static_pose_bracket_runtime_result(
        result,
        contract=contract,
        pre_open_holder_snapshot=pre_open_holder_snapshot,
        post_close_holder_snapshot=post_close_holder_snapshot,
    )
    return result


def verify_static_pose_bracket_runtime_result(
    result: dict[str, Any],
    *,
    contract: dict[str, Any],
    pre_open_holder_snapshot: dict[str, Any],
    post_close_holder_snapshot: dict[str, Any],
) -> None:
    """Verify all signed nested fixture evidence and fail closed on drift."""

    allowed_fields = {
        "schema_version",
        "result_name",
        "evidence_mode",
        "qualification_scope",
        "contract_identity_sha256",
        "serial_holder_evidence",
        "observation",
        "evaluation",
        "transport_audit",
        "camera_audits",
        "lifecycle_events",
        "operation_counts",
        "local_capabilities",
        "authority_not_granted",
        "hardware_opened",
        "physical_follower_commanded",
        "policy_inference_run",
        "motion_authority_granted",
        "training_authority_granted",
        "identity_sha256",
    }
    if not isinstance(result, dict) or set(result) != allowed_fields:
        raise ValueError("Static pose runtime result fields are invalid")
    if (
        result.get("schema_version")
        != STATIC_POSE_BRACKET_RUNTIME_RESULT_SCHEMA_VERSION
        or result.get("result_name")
        != "pi05_static_pose_bracket_fixture_runtime"
        or result.get("evidence_mode") != "injected_fixture_runtime"
        or result.get("qualification_scope") != "fixture_static_pose_runtime"
    ):
        raise ValueError("Static pose runtime result classification drifted")
    verify_signed_payload(result, label="Static pose runtime result")
    if result.get("contract_identity_sha256") != contract.get("identity_sha256"):
        raise ValueError("Static pose runtime result contract identity drifted")

    require_no_serial_identity_holders(pre_open_holder_snapshot)
    require_no_serial_identity_holders(post_close_holder_snapshot)
    verify_serial_identity_holder_stability(
        pre_open_holder_snapshot,
        post_close_holder_snapshot,
    )
    expected_holder_evidence = {
        "pre_open": _redacted_holder_evidence(pre_open_holder_snapshot),
        "post_close": _redacted_holder_evidence(post_close_holder_snapshot),
    }
    if result.get("serial_holder_evidence") != expected_holder_evidence:
        raise ValueError("Static pose runtime holder evidence drifted")

    observation = result.get("observation")
    evaluation = result.get("evaluation")
    if not isinstance(observation, dict) or not isinstance(evaluation, dict):
        raise ValueError("Static pose runtime nested evidence is missing")
    verify_static_pose_bracket_result(
        evaluation,
        contract=contract,
        observation=observation,
    )
    transport_audit = _validate_transport_audit(
        result.get("transport_audit"),
        expected_hardware_opened=False,
    )
    _validate_camera_audits(result.get("camera_audits"), contract=contract)
    if result.get("lifecycle_events") != _expected_lifecycle_events(contract):
        raise ValueError("Static pose runtime lifecycle evidence drifted")
    if result.get("operation_counts") != EXPECTED_OPERATION_COUNTS:
        raise ValueError("Static pose runtime operation counts drifted")
    counts = dict(result["operation_counts"])
    _apply_transport_audit_counts(counts, audit=transport_audit)
    if counts != EXPECTED_OPERATION_COUNTS:
        raise ValueError("Static pose runtime transport/count evidence drifted")
    if (
        result.get("local_capabilities")
        != ["fixture_static_pose_bracket_runtime_conformant"]
        or result.get("authority_not_granted") != _RUNTIME_AUTHORITY_NOT_GRANTED
        or result.get("hardware_opened") is not False
        or result.get("physical_follower_commanded") is not False
        or result.get("policy_inference_run") is not False
        or result.get("motion_authority_granted") is not False
        or result.get("training_authority_granted") is not False
    ):
        raise ValueError("Static pose runtime authority fields drifted")


def _read_position_phase(
    contract: dict[str, Any],
    *,
    transport: StaticPoseTransport,
    phase: str,
    counts: dict[str, int],
    lifecycle_events: list[str],
) -> list[dict[str, Any]]:
    values = []
    for joint in contract["joints"]:
        counts["position_read_attempts"] += 1
        raw_position = transport.read_position(
            joint["joint_name"],
            joint["servo_id"],
        )
        counts["position_read_successes"] += 1
        lifecycle_events.append(f"{phase}:{joint['joint_name']}")
        values.append(
            {
                "joint_name": joint["joint_name"],
                "servo_id": joint["servo_id"],
                "raw_position": raw_position,
            }
        )
    return values


def _capture_camera_batch(
    camera: dict[str, Any],
    *,
    camera_index: int,
    transport: StaticPoseTransport,
    camera_factory: Callable[[dict[str, Any]], FiniteStaticPoseCamera],
    monotonic_ns: Callable[[], int],
    lifecycle_events: list[str],
) -> tuple[dict[str, Any], dict[str, Any], tuple[int, int]]:
    instance: FiniteStaticPoseCamera | None = None
    primary_error: BaseException | None = None
    release_error: BaseException | None = None
    frames = []
    interval_started: int | None = None
    interval_finished: int | None = None
    try:
        if not transport.is_connected:
            raise RuntimeError("Static pose camera began with transport disconnected")
        instance = camera_factory(copy.deepcopy(camera))
        instance.open()
        lifecycle_events.append(f"camera_{camera_index}:open")
        for frame_index in range(camera["required_frame_count"]):
            if not transport.is_connected:
                raise RuntimeError("Static pose camera ran while transport was closed")
            started = _monotonic(monotonic_ns)
            frame = instance.read()
            finished = _monotonic(monotonic_ns)
            if finished <= started:
                raise ValueError("Static pose camera timestamp interval is invalid")
            if interval_started is None:
                interval_started = started
            interval_finished = finished
            frames.append(_normalize_fixture_frame(frame, expected=camera, index=frame_index))
            lifecycle_events.append(f"camera_{camera_index}:frame_{frame_index}")
    except BaseException as exc:
        primary_error = exc
    finally:
        if instance is not None:
            try:
                instance.release()
                lifecycle_events.append(f"camera_{camera_index}:release")
            except BaseException as exc:
                release_error = exc

    errors = [error for error in (primary_error, release_error) if error is not None]
    if len(errors) > 1:
        raise BaseExceptionGroup(
            "Static pose camera capture and release both failed",
            errors,
        )
    if errors:
        raise errors[0]
    if instance is None or interval_started is None or interval_finished is None:
        raise RuntimeError("Static pose camera lifecycle is incomplete")
    if not transport.is_connected:
        raise RuntimeError("Static pose camera lifecycle disconnected the transport")
    audit = _validate_camera_audit(
        instance.audit(),
        camera=camera,
    )
    return (
        {
            "stable_camera_identity_sha256": camera[
                "stable_camera_identity_sha256"
            ],
            "input_mode": copy.deepcopy(camera["input_mode"]),
            "frames": frames,
        },
        audit,
        (interval_started, interval_finished),
    )


def _normalize_fixture_frame(
    frame: Any,
    *,
    expected: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    required_fields = {"frame_bytes", "encoding", "width", "height", "channels"}
    if not isinstance(frame, dict) or set(frame) != required_fields:
        raise ValueError("Static pose fixture camera frame fields are invalid")
    frame_bytes = frame.get("frame_bytes")
    if (
        not isinstance(frame_bytes, bytes)
        or not frame_bytes
        or len(frame_bytes) > MAX_FIXTURE_FRAME_BYTES
    ):
        raise ValueError("Static pose fixture camera frame bytes are missing")
    if (
        frame.get("encoding") != expected["required_encoding"]
        or frame.get("width") != expected["input_mode"]["width"]
        or frame.get("height") != expected["input_mode"]["height"]
        or frame.get("channels") != expected["required_channels"]
    ):
        raise ValueError("Static pose fixture camera frame semantics drifted")
    return {
        "frame_index": index,
        "frame_sha256": hashlib.sha256(frame_bytes).hexdigest(),
        "width": frame["width"],
        "height": frame["height"],
        "channels": frame["channels"],
        "encoding": frame["encoding"],
    }


def _build_runtime_result(
    *,
    contract: dict[str, Any],
    pre_open_holder_snapshot: dict[str, Any],
    post_close_holder_snapshot: dict[str, Any],
    observation: dict[str, Any],
    evaluation: dict[str, Any],
    transport_audit: dict[str, Any],
    camera_audits: list[dict[str, Any]],
    lifecycle_events: list[str],
    operation_counts: dict[str, int],
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": STATIC_POSE_BRACKET_RUNTIME_RESULT_SCHEMA_VERSION,
            "result_name": "pi05_static_pose_bracket_fixture_runtime",
            "evidence_mode": "injected_fixture_runtime",
            "qualification_scope": "fixture_static_pose_runtime",
            "contract_identity_sha256": contract["identity_sha256"],
            "serial_holder_evidence": {
                "pre_open": _redacted_holder_evidence(pre_open_holder_snapshot),
                "post_close": _redacted_holder_evidence(
                    post_close_holder_snapshot
                ),
            },
            "observation": copy.deepcopy(observation),
            "evaluation": copy.deepcopy(evaluation),
            "transport_audit": copy.deepcopy(transport_audit),
            "camera_audits": copy.deepcopy(camera_audits),
            "lifecycle_events": list(lifecycle_events),
            "operation_counts": dict(operation_counts),
            "local_capabilities": [
                "fixture_static_pose_bracket_runtime_conformant"
            ],
            "authority_not_granted": list(_RUNTIME_AUTHORITY_NOT_GRANTED),
            "hardware_opened": False,
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
        }
    )


def _validate_transport_audit(
    value: Any,
    *,
    expected_hardware_opened: bool,
) -> dict[str, Any]:
    expected_fields = {
        "hardware_opened",
        "connect_calls",
        "read_calls",
        "close_calls",
        "motor_register_writes",
        "configuration_writes",
        "torque_changes",
        "motion_commands",
        "unexpected_operations",
        "physical_follower_commanded",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise ValueError("Static pose transport audit fields are invalid")
    expected = {
        "hardware_opened": expected_hardware_opened,
        "connect_calls": 1,
        "read_calls": 12,
        "close_calls": 1,
        "motor_register_writes": 0,
        "configuration_writes": 0,
        "torque_changes": 0,
        "motion_commands": 0,
        "unexpected_operations": 0,
        "physical_follower_commanded": False,
    }
    if value != expected:
        raise ValueError("Static pose transport audit drifted")
    return copy.deepcopy(value)


def _apply_transport_audit_counts(
    counts: dict[str, int],
    *,
    audit: dict[str, Any],
) -> None:
    for field in (
        "motor_register_writes",
        "configuration_writes",
        "torque_changes",
        "motion_commands",
        "unexpected_operations",
    ):
        counts[field] = audit[field]


def _validate_camera_audit(
    value: Any,
    *,
    camera: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        "open_attempts": 1,
        "open_successes": 1,
        "read_attempts": camera["required_frame_count"],
        "read_successes": camera["required_frame_count"],
        "release_attempts": 1,
        "release_successes": 1,
        "capture_property_writes": 0,
        "continuous_recording_sessions": 0,
        "unexpected_operations": 0,
    }
    if not isinstance(value, dict) or value != expected:
        raise ValueError("Static pose camera audit drifted")
    return {
        "stable_camera_identity_sha256": camera[
            "stable_camera_identity_sha256"
        ],
        **copy.deepcopy(value),
    }


def _validate_camera_audits(value: Any, *, contract: dict[str, Any]) -> None:
    if not isinstance(value, list) or len(value) != len(contract["cameras"]):
        raise ValueError("Static pose camera audit set is incomplete")
    for audit, camera in zip(value, contract["cameras"], strict=True):
        expected = {
            "stable_camera_identity_sha256": camera[
                "stable_camera_identity_sha256"
            ],
            "open_attempts": 1,
            "open_successes": 1,
            "read_attempts": camera["required_frame_count"],
            "read_successes": camera["required_frame_count"],
            "release_attempts": 1,
            "release_successes": 1,
            "capture_property_writes": 0,
            "continuous_recording_sessions": 0,
            "unexpected_operations": 0,
        }
        if audit != expected:
            raise ValueError("Static pose camera audit drifted")


def _redacted_holder_evidence(snapshot: dict[str, Any]) -> dict[str, Any]:
    verify_serial_identity_holder_snapshot(snapshot)
    return {
        "snapshot_identity_sha256": snapshot["identity_sha256"],
        "path_count": len(snapshot["paths_checked"]),
        "path_identity_sha256": [
            hashlib.sha256(path.encode("utf-8")).hexdigest()
            for path in snapshot["paths_checked"]
        ],
        "paths_all_existed": all(
            record["path_exists"] for record in snapshot["per_path"]
        ),
        "per_path_holder_counts": list(snapshot["per_path_holder_counts"]),
        "deduplicated_holder_count": snapshot["deduplicated_holder_count"],
        "holder_set_sha256": hashlib.sha256(
            canonical_json_bytes(snapshot["deduplicated_holders"])
        ).hexdigest(),
    }


def _expected_lifecycle_events(contract: dict[str, Any]) -> list[str]:
    events = ["pre_open_holder", "construct", "connect"]
    events.extend(f"q_before:{joint['joint_name']}" for joint in contract["joints"])
    for camera_index, camera in enumerate(contract["cameras"]):
        events.append(f"camera_{camera_index}:open")
        events.extend(
            f"camera_{camera_index}:frame_{frame_index}"
            for frame_index in range(camera["required_frame_count"])
        )
        events.append(f"camera_{camera_index}:release")
    events.extend(f"q_after:{joint['joint_name']}" for joint in contract["joints"])
    events.extend(["close", "post_close_holder"])
    return events


def _monotonic(clock: Callable[[], int]) -> int:
    value = clock()
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("Static pose runtime monotonic clock is invalid")
    return value


class _StrictMonotonicClock:
    def __init__(self, clock: Callable[[], int]):
        self._clock = clock
        self._previous: int | None = None

    def __call__(self) -> int:
        value = self._clock()
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("Static pose runtime monotonic clock is invalid")
        if self._previous is not None and value <= self._previous:
            raise ValueError("Static pose runtime monotonic clock regressed")
        self._previous = value
        return value
