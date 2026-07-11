"""Offline-first, no-write SO-101 servo census contracts and replay."""

from __future__ import annotations

import copy

from pathlib import Path
from typing import Any, Callable, Protocol

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.census_runtime_binding import (
    EXPECTED_READ_REGISTER_WIDTHS,
    EXPECTED_RUNTIME_SEMANTICS,
    RUNTIME_SOURCE_BINDINGS as _RUNTIME_SOURCE_BINDINGS,
    verify_census_runtime_source_bindings,
)


CENSUS_CONTRACT_SCHEMA_VERSION = "scenesmith.readonly_servo_census_contract.v2"
CENSUS_TRACE_SCHEMA_VERSION = "scenesmith.readonly_servo_census_trace.v1"
CENSUS_RESULT_SCHEMA_VERSION = "scenesmith.readonly_servo_census_result.v1"

DEFAULT_CENSUS_CONTRACT_PATH = Path(
    "configurations/robot_lab/pi05_readonly_servo_census_contract.fixture.json"
)
DEFAULT_CENSUS_TRACE_PATH = Path(
    "tests/fixtures/robot_lab/readonly_census/pi05_readonly_servo_census.trace.json"
)
DEFAULT_CENSUS_RESULT_PATH = Path(
    "tests/fixtures/robot_lab/readonly_census/pi05_readonly_servo_census.result.json"
)

_FOLLOWER_JOINT_MAP = tuple(EXPECTED_RUNTIME_SEMANTICS["follower_joint_map"])
_JOINTS = tuple((item["servo_id"], item["joint_name"]) for item in _FOLLOWER_JOINT_MAP)
_MODEL_NAMES = tuple(dict.fromkeys(item["model"] for item in _FOLLOWER_JOINT_MAP))
if _MODEL_NAMES != ("sts3215",):
    raise RuntimeError(
        "Pinned census runtime semantics contain an unexpected model set"
    )
_MODEL_NAME = _MODEL_NAMES[0]
_MODEL_NUMBER = EXPECTED_RUNTIME_SEMANTICS["sts3215_model_number"]
_MODEL_RESOLUTION = EXPECTED_RUNTIME_SEMANTICS["sts3215_resolution"]
_PROTOCOL_VERSION = EXPECTED_RUNTIME_SEMANTICS["sts3215_protocol_version"]
_DEFAULT_BAUDRATE = EXPECTED_RUNTIME_SEMANTICS["default_baudrate"]
_BAUDRATE_CODE_TO_VALUE = {
    EXPECTED_RUNTIME_SEMANTICS["sts3215_baud_code"]: _DEFAULT_BAUDRATE
}
_READ_PLAN = tuple(EXPECTED_READ_REGISTER_WIDTHS.items())
_READ_REGISTER_NAMES = {item[0] for item in _READ_PLAN}
_FORBIDDEN_OPERATIONS = (
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
    "torque_disabled",
    "write",
    "write_calibration",
    "write_register",
)
_TRANSPORT_AUDIT_FIELDS = {
    "connect_calls",
    "read_calls",
    "close_calls",
    "motor_register_writes",
    "torque_changes",
    "motion_commands",
    "unexpected_operations",
    "aborted_operations",
    "unconsumed_events",
    "hardware_opened",
    "physical_follower_commanded",
}


class TransientReadError(ConnectionError):
    """A declared retryable read failure from a narrow transport."""


class ReadOnlyServoTransport(Protocol):
    @property
    def device_identity(self) -> dict[str, Any]: ...

    @property
    def is_connected(self) -> bool: ...

    def connect(self) -> None: ...

    def read(self, register: str, servo_id: int) -> int: ...

    def close(self) -> None: ...

    def audit(self) -> dict[str, Any]: ...


class RecordedTraceTransport:
    """Replay one signed trace through the same narrow census interface."""

    def __init__(self, trace: dict[str, Any]):
        self._trace = copy.deepcopy(trace)
        self._events = self._trace.get("events")
        if not isinstance(self._events, list) or not self._events:
            raise ValueError("Recorded census trace events are required")
        self._index = 0
        self._is_connected = False
        self._read_attempts: dict[tuple[int, str], int] = {}
        self._audit = _empty_transport_audit(hardware_opened=False)
        event = self._consume("construct")
        if event.get("outcome") != "success":
            raise RuntimeError("Recorded transport construction failed")

    @property
    def device_identity(self) -> dict[str, Any]:
        return copy.deepcopy(self._trace["observed_device_identity"])

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self) -> None:
        self._audit["connect_calls"] += 1
        event = self._consume("connect")
        if event.get("outcome") != "success":
            raise ConnectionError(
                f"Recorded transport connect failed: {event.get('error_code')}"
            )
        self._is_connected = True

    def read(self, register: str, servo_id: int) -> int:
        if not self._is_connected:
            self._audit["unexpected_operations"] += 1
            raise RuntimeError("Recorded transport read attempted while disconnected")
        self._audit["read_calls"] += 1
        event = self._consume("read")
        key = (servo_id, register)
        attempt = self._read_attempts.get(key, 0) + 1
        self._read_attempts[key] = attempt
        if (
            event.get("servo_id") != servo_id
            or event.get("register") != register
            or event.get("attempt") != attempt
        ):
            self._audit["unexpected_operations"] += 1
            raise ValueError(
                "Recorded trace read order drifted: "
                f"expected id={servo_id} register={register} attempt={attempt}"
            )
        outcome = event.get("outcome")
        if outcome == "transient_error":
            raise TransientReadError(
                f"Recorded transient read failure: {event.get('error_code')}"
            )
        if outcome == "fatal_error":
            raise RuntimeError(f"Recorded read failure: {event.get('error_code')}")
        if outcome != "success":
            raise ValueError(f"Recorded read outcome is invalid: {outcome}")
        return event.get("raw_value")

    def close(self) -> None:
        self._audit["close_calls"] += 1
        if self._index >= len(self._events):
            self._audit["unexpected_operations"] += 1
            raise ValueError("Recorded transport close event is missing")
        if self._events[self._index].get("operation") != "close":
            close_index = next(
                (
                    index
                    for index in range(self._index, len(self._events))
                    if self._events[index].get("operation") == "close"
                ),
                None,
            )
            if close_index is None:
                self._audit["unexpected_operations"] += 1
                raise ValueError("Recorded transport close event is missing")
            self._audit["aborted_operations"] += close_index - self._index
            self._index = close_index
        event = self._consume("close")
        if event.get("disable_torque") is not False:
            self._audit["torque_changes"] += 1
            self._audit["motor_register_writes"] += 1
            raise ValueError("Recorded transport close attempted disable_torque")
        self._is_connected = False
        if event.get("outcome") == "close_error":
            raise RuntimeError(
                f"Recorded transport close failure: {event.get('error_code')}"
            )
        if event.get("outcome") != "success":
            raise ValueError("Recorded transport close outcome is invalid")

    def audit(self) -> dict[str, Any]:
        result = copy.deepcopy(self._audit)
        result["unconsumed_events"] = len(self._events) - self._index
        return result

    def _consume(self, expected_operation: str) -> dict[str, Any]:
        if self._index >= len(self._events):
            self._audit["unexpected_operations"] += 1
            raise ValueError(f"Recorded trace ended before {expected_operation}")
        event = self._events[self._index]
        if event.get("operation") != expected_operation:
            self._audit["unexpected_operations"] += 1
            raise ValueError(
                f"Recorded trace expected {expected_operation} but observed {event.get('operation')}"
            )
        self._index += 1
        return event


class InjectedReadOnlyBusAdapter:
    """Narrow an already-authorized raw bus without constructing live hardware."""

    def __init__(
        self,
        *,
        backend: Any,
        device_identity: dict[str, Any],
        servo_names: dict[int, str],
    ):
        if set(servo_names) != set(range(1, 7)):
            raise ValueError("Injected read-only adapter requires exact servo IDs 1-6")
        self._backend = backend
        self._device_identity = copy.deepcopy(device_identity)
        self._servo_names = dict(servo_names)
        self._is_connected = False
        self._connect_attempted = False
        self._closed = False
        self._audit = _empty_transport_audit(hardware_opened=False)

    @property
    def device_identity(self) -> dict[str, Any]:
        return copy.deepcopy(self._device_identity)

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self) -> None:
        if self._connect_attempted or self._closed:
            self._audit["unexpected_operations"] += 1
            raise RuntimeError(
                "Injected read-only adapter connect lifecycle is invalid"
            )
        self._audit["connect_calls"] += 1
        self._connect_attempted = True
        # A backend connect attempt may open the port before raising. Mark this
        # conservatively and guarantee the explicit no-write close below.
        self._audit["hardware_opened"] = True
        self._backend.connect(handshake=False)
        self._is_connected = True

    def read(self, register: str, servo_id: int) -> int:
        if not self._is_connected:
            self._audit["unexpected_operations"] += 1
            raise RuntimeError("Injected read-only adapter is disconnected")
        if register not in _READ_REGISTER_NAMES:
            self._audit["unexpected_operations"] += 1
            raise ValueError(
                f"Register is not on the read-only census allowlist: {register}"
            )
        motor = self._servo_names.get(servo_id)
        if motor is None:
            self._audit["unexpected_operations"] += 1
            raise ValueError(f"Unexpected servo ID: {servo_id}")
        self._audit["read_calls"] += 1
        return self._backend.read(
            register,
            motor,
            normalize=False,
            num_retry=0,
        )

    def close(self) -> None:
        if self._closed:
            self._audit["unexpected_operations"] += 1
            raise RuntimeError("Injected read-only adapter close called more than once")
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


def build_census_contract() -> dict[str, Any]:
    payload = {
        "schema_version": CENSUS_CONTRACT_SCHEMA_VERSION,
        "contract_name": "pi05_so101_offline_readonly_servo_census",
        "qualification_scope": "fixture_evidence",
        "proof_label": "census_trace_conformant",
        "target_device_identity": {
            "device_role": "so101_follower_observation_target",
            "usb": {
                "vendor_id_hex": "ffff",
                "product_id_hex": "0001",
                "serial_number": "fixture-so101-follower-001",
                "canonical_path": "/dev/cu.fixture-so101-follower",
                "allowed_aliases": ["/dev/tty.fixture-so101-follower"],
                "forbidden_aliases": [
                    "/dev/cu.fixture-so101-leader",
                    "/dev/tty.fixture-so101-leader",
                ],
            },
            "bus": {
                "protocol_family": "feetech",
                "protocol_version": _PROTOCOL_VERSION,
                "baudrate": _DEFAULT_BAUDRATE,
            },
        },
        "expected_servos": [
            {
                "servo_id": servo_id,
                "joint_name": joint_name,
                "model": _MODEL_NAME,
                "model_number": _MODEL_NUMBER,
            }
            for servo_id, joint_name in _JOINTS
        ],
        "read_plan": [
            {
                "register": register,
                "width_bytes": width,
                "raw_type": "integer",
            }
            for register, width in _READ_PLAN
        ],
        "retry_policy": {
            "max_read_retries": 1,
            "retryable_error_codes": ["crc_mismatch", "timeout"],
        },
        "forbidden_operations": list(_FORBIDDEN_OPERATIONS),
        "runtime_source_bindings": [
            dict(binding) for binding in _RUNTIME_SOURCE_BINDINGS
        ],
        "runtime_semantics": copy.deepcopy(EXPECTED_RUNTIME_SEMANTICS),
    }
    return sign_payload(payload)


def verify_census_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != CENSUS_CONTRACT_SCHEMA_VERSION:
        raise ValueError("Unsupported read-only census contract schema")
    verify_signed_payload(payload, label="Read-only census contract")
    expected = build_census_contract()
    if payload != expected:
        raise ValueError(
            "Read-only census contract drifted from the code-pinned identity/read plan"
        )


def build_recorded_census_trace(contract: dict[str, Any]) -> dict[str, Any]:
    verify_census_contract(contract)
    target = contract["target_device_identity"]
    observed_identity = {
        "device_role": target["device_role"],
        "usb": {
            "vendor_id_hex": target["usb"]["vendor_id_hex"],
            "product_id_hex": target["usb"]["product_id_hex"],
            "serial_number": target["usb"]["serial_number"],
            "canonical_path": target["usb"]["canonical_path"],
            "observed_aliases": list(target["usb"]["allowed_aliases"]),
        },
        "bus": copy.deepcopy(target["bus"]),
    }
    events: list[dict[str, Any]] = [
        {
            "sequence": 0,
            "operation": "construct",
            "outcome": "success",
            "error_code": None,
        },
        {
            "sequence": 1,
            "operation": "connect",
            "outcome": "success",
            "error_code": None,
        },
    ]
    positions = {1: 2048, 2: 1984, 3: 2112, 4: 2016, 5: 2056, 6: 1024}
    for servo in contract["expected_servos"]:
        servo_id = servo["servo_id"]
        raw_by_register = {
            "Model_Number": _MODEL_NUMBER,
            "Firmware_Major_Version": 3,
            "Firmware_Minor_Version": 10 + servo_id,
            "ID": servo_id,
            "Baud_Rate": 0,
            "Present_Position": positions[servo_id],
            "Present_Voltage": 120,
            "Present_Temperature": 24 + servo_id,
        }
        for plan in contract["read_plan"]:
            register = plan["register"]
            if servo_id == 3 and register == "Present_Position":
                events.append(
                    {
                        "sequence": len(events),
                        "operation": "read",
                        "servo_id": servo_id,
                        "register": register,
                        "attempt": 1,
                        "outcome": "transient_error",
                        "raw_value": None,
                        "error_code": "timeout",
                    }
                )
                attempt = 2
            else:
                attempt = 1
            events.append(
                {
                    "sequence": len(events),
                    "operation": "read",
                    "servo_id": servo_id,
                    "register": register,
                    "attempt": attempt,
                    "outcome": "success",
                    "raw_value": raw_by_register[register],
                    "error_code": None,
                }
            )
    events.append(
        {
            "sequence": len(events),
            "operation": "close",
            "outcome": "success",
            "error_code": None,
            "disable_torque": False,
        }
    )
    return sign_payload(
        {
            "schema_version": CENSUS_TRACE_SCHEMA_VERSION,
            "trace_name": "pi05_so101_offline_readonly_servo_census",
            "qualification_scope": "fixture_evidence",
            "contract_identity_sha256": contract["identity_sha256"],
            "transport_kind": "recorded_trace",
            "hardware_opened": False,
            "observed_device_identity": observed_identity,
            "events": events,
        }
    )


def verify_recorded_census_trace(
    payload: dict[str, Any],
    *,
    contract: dict[str, Any],
) -> None:
    verify_census_contract(contract)
    allowed_fields = {
        "schema_version",
        "trace_name",
        "qualification_scope",
        "contract_identity_sha256",
        "transport_kind",
        "hardware_opened",
        "observed_device_identity",
        "events",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Recorded census trace fields are malformed")
    if payload.get("schema_version") != CENSUS_TRACE_SCHEMA_VERSION:
        raise ValueError("Unsupported recorded census trace schema")
    verify_signed_payload(payload, label="Recorded census trace")
    if payload.get("trace_name") != "pi05_so101_offline_readonly_servo_census":
        raise ValueError("Recorded census trace name is invalid")
    if payload.get("qualification_scope") != "fixture_evidence":
        raise ValueError("Recorded census trace must remain fixture evidence")
    if payload.get("contract_identity_sha256") != contract["identity_sha256"]:
        raise ValueError("Recorded census trace contract identity drifted")
    if (
        payload.get("transport_kind") != "recorded_trace"
        or payload.get("hardware_opened") is not False
    ):
        raise ValueError("Recorded census trace cannot claim live hardware")
    _verify_observed_device_identity(
        payload.get("observed_device_identity"), contract=contract
    )
    events = payload.get("events")
    if not isinstance(events, list) or len(events) < 4:
        raise ValueError("Recorded census trace events are incomplete")
    if not all(isinstance(event, dict) for event in events):
        raise ValueError("Recorded census trace event is malformed")
    operations = [event.get("operation") for event in events]
    if (
        operations[0] != "construct"
        or operations[1] != "connect"
        or operations[-1] != "close"
    ):
        raise ValueError("Recorded census trace lifecycle order is invalid")
    if operations.count("construct") != 1 or operations.count("connect") != 1:
        raise ValueError(
            "Recorded census trace construct/connect lifecycle is ambiguous"
        )
    if operations.count("close") != 1:
        raise ValueError("Recorded census trace must close exactly once")
    if [event.get("sequence") for event in events if isinstance(event, dict)] != list(
        range(len(events))
    ):
        raise ValueError("Recorded census trace event sequence drifted")
    for event in events:
        _verify_trace_event(event, contract=contract)
    _verify_conformant_read_sequence(events, contract=contract)


def run_readonly_census(
    contract: dict[str, Any],
    transport_factory: Callable[[], ReadOnlyServoTransport],
) -> dict[str, Any]:
    verify_census_contract(contract)
    counts = {
        "construct_attempts": 1,
        "construct_successes": 0,
        "connect_attempts": 0,
        "connect_successes": 0,
        "read_attempts": 0,
        "read_successes": 0,
        "read_retries": 0,
        "close_attempts": 0,
        "close_successes": 0,
    }
    transport: ReadOnlyServoTransport | None = None
    primary_error: BaseException | None = None
    close_error: BaseException | None = None
    raw_by_servo: dict[int, dict[str, int]] = {}
    try:
        transport = transport_factory()
        counts["construct_successes"] = 1
        _verify_observed_device_identity(transport.device_identity, contract=contract)
        counts["connect_attempts"] += 1
        transport.connect()
        counts["connect_successes"] += 1
        if not transport.is_connected:
            raise RuntimeError(
                "Read-only census transport did not report connected state"
            )
        retry_policy = contract["retry_policy"]
        for servo in contract["expected_servos"]:
            servo_id = servo["servo_id"]
            raw_by_servo[servo_id] = {}
            for plan in contract["read_plan"]:
                register = plan["register"]
                raw_value: int | None = None
                for attempt_index in range(retry_policy["max_read_retries"] + 1):
                    counts["read_attempts"] += 1
                    try:
                        raw_value = transport.read(register, servo_id)
                    except TransientReadError as exc:
                        if attempt_index >= retry_policy["max_read_retries"]:
                            raise ConnectionError(
                                f"Read retry exhausted for servo {servo_id} register {register}"
                            ) from exc
                        counts["read_retries"] += 1
                        continue
                    counts["read_successes"] += 1
                    break
                raw_by_servo[servo_id][register] = _validate_raw_value(
                    register,
                    raw_value,
                    width_bytes=plan["width_bytes"],
                )
    except BaseException as exc:
        primary_error = exc
    finally:
        if transport is not None:
            counts["close_attempts"] += 1
            try:
                transport.close()
                counts["close_successes"] += 1
            except BaseException as exc:
                close_error = exc
    if primary_error is not None and close_error is not None:
        raise BaseExceptionGroup(
            "Read-only census failed and no-write cleanup also failed",
            [primary_error, close_error],
        )
    if primary_error is not None:
        raise primary_error
    if close_error is not None:
        raise close_error
    if transport is None:
        raise RuntimeError("Read-only census transport was not constructed")
    audit = _validate_transport_audit(transport.audit())
    if transport.is_connected:
        raise RuntimeError("Read-only census transport remained connected after close")
    if audit["connect_calls"] != counts["connect_attempts"]:
        raise ValueError("Transport connect audit drifted from census counts")
    if audit["read_calls"] != counts["read_attempts"]:
        raise ValueError("Transport read audit drifted from census counts")
    if audit["close_calls"] != counts["close_attempts"]:
        raise ValueError("Transport close audit drifted from census counts")
    for field in (
        "motor_register_writes",
        "torque_changes",
        "motion_commands",
        "unexpected_operations",
        "aborted_operations",
        "unconsumed_events",
    ):
        if audit[field] != 0:
            raise ValueError(f"Read-only census transport audit is nonzero: {field}")
    if audit["physical_follower_commanded"] is not False:
        raise ValueError("Read-only census transport reported a follower command")
    decoded = [
        _decode_servo(raw_by_servo[servo["servo_id"]], expected=servo)
        for servo in contract["expected_servos"]
    ]
    operation_counts = {
        **counts,
        "motor_register_writes": audit["motor_register_writes"],
        "torque_changes": audit["torque_changes"],
        "motion_commands": audit["motion_commands"],
        "unexpected_operations": audit["unexpected_operations"],
    }
    return {
        "target_device_identity": copy.deepcopy(transport.device_identity),
        "servos": decoded,
        "operation_counts": operation_counts,
        "hardware_opened": audit["hardware_opened"],
        "physical_follower_commanded": audit["physical_follower_commanded"],
        "lifecycle_state": "closed",
    }


def replay_recorded_census(
    contract: dict[str, Any],
    trace: dict[str, Any],
) -> dict[str, Any]:
    verify_recorded_census_trace(trace, contract=contract)
    run = run_readonly_census(contract, lambda: RecordedTraceTransport(trace))
    if run["hardware_opened"] is not False:
        raise ValueError("Recorded census replay cannot claim opened hardware")
    return sign_payload(
        {
            "schema_version": CENSUS_RESULT_SCHEMA_VERSION,
            "result_name": "pi05_so101_offline_readonly_servo_census",
            "qualification_scope": "fixture_evidence",
            "evidence_mode": "recorded_trace_replay",
            "proof_label": contract["proof_label"],
            "conformance_state": "census_trace_conformant",
            "contract_identity_sha256": contract["identity_sha256"],
            "trace_identity_sha256": trace["identity_sha256"],
            **run,
        }
    )


def verify_census_result(
    payload: dict[str, Any],
    *,
    contract: dict[str, Any],
    trace: dict[str, Any],
) -> None:
    if payload.get("schema_version") != CENSUS_RESULT_SCHEMA_VERSION:
        raise ValueError("Unsupported read-only census result schema")
    verify_signed_payload(payload, label="Read-only census result")
    expected = replay_recorded_census(contract, trace)
    if payload != expected:
        raise ValueError("Read-only census result drifted from deterministic replay")


def write_census_fixture_artifacts(
    *,
    repo_root: Path,
    contract_path: Path = DEFAULT_CENSUS_CONTRACT_PATH,
    trace_path: Path = DEFAULT_CENSUS_TRACE_PATH,
    result_path: Path = DEFAULT_CENSUS_RESULT_PATH,
) -> dict[str, Any]:
    verify_census_runtime_source_bindings(repo_root=repo_root)
    contract = build_census_contract()
    trace = build_recorded_census_trace(contract)
    result = replay_recorded_census(contract, trace)
    dump_canonical_json(_resolve(repo_root, contract_path), contract)
    dump_canonical_json(_resolve(repo_root, trace_path), trace)
    dump_canonical_json(_resolve(repo_root, result_path), result)
    return {"contract": contract, "trace": trace, "result": result}


def verify_census_fixture_artifacts(
    *,
    repo_root: Path,
    contract_path: Path = DEFAULT_CENSUS_CONTRACT_PATH,
    trace_path: Path = DEFAULT_CENSUS_TRACE_PATH,
    result_path: Path = DEFAULT_CENSUS_RESULT_PATH,
) -> dict[str, Any]:
    verify_census_runtime_source_bindings(repo_root=repo_root)
    contract = load_strict_json(_resolve(repo_root, contract_path))
    trace = load_strict_json(_resolve(repo_root, trace_path))
    result = load_strict_json(_resolve(repo_root, result_path))
    verify_census_contract(contract)
    if contract != build_census_contract():
        raise ValueError("Tracked read-only census contract drifted")
    verify_recorded_census_trace(trace, contract=contract)
    if trace != build_recorded_census_trace(contract):
        raise ValueError("Tracked read-only census trace drifted")
    verify_census_result(result, contract=contract, trace=trace)
    return {"contract": contract, "trace": trace, "result": result}


def _verify_trace_event(event: Any, *, contract: dict[str, Any]) -> None:
    if not isinstance(event, dict):
        raise ValueError("Recorded census trace event is malformed")
    operation = event.get("operation")
    if operation in contract["forbidden_operations"] or operation not in {
        "construct",
        "connect",
        "read",
        "close",
    }:
        raise ValueError(
            f"Recorded census trace contains forbidden operation: {operation}"
        )
    if operation in {"construct", "connect"}:
        if set(event) != {"sequence", "operation", "outcome", "error_code"}:
            raise ValueError(f"Recorded census {operation} event fields are malformed")
        if event.get("outcome") != "success" or event.get("error_code") is not None:
            raise ValueError(f"Recorded census {operation} must succeed in the fixture")
        return
    if operation == "close":
        if set(event) != {
            "sequence",
            "operation",
            "outcome",
            "error_code",
            "disable_torque",
        }:
            raise ValueError("Recorded census close event fields are malformed")
        if event.get("disable_torque") is not False:
            raise ValueError("Recorded census close disable_torque must be false")
        if event.get("outcome") not in {"success", "close_error"}:
            raise ValueError("Recorded census close outcome is invalid")
        return
    if set(event) != {
        "sequence",
        "operation",
        "servo_id",
        "register",
        "attempt",
        "outcome",
        "raw_value",
        "error_code",
    }:
        raise ValueError("Recorded census read event fields are malformed")
    if event.get("servo_id") not in set(range(1, 7)):
        raise ValueError("Recorded census read servo ID is invalid")
    if event.get("register") not in _READ_REGISTER_NAMES:
        raise ValueError(
            f"Recorded census read register is not allowed: {event.get('register')}"
        )
    attempt = event.get("attempt")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt <= 0:
        raise ValueError("Recorded census read attempt is invalid")
    outcome = event.get("outcome")
    if outcome == "success":
        _validate_raw_value(
            event["register"],
            event.get("raw_value"),
            width_bytes=dict(_READ_PLAN)[event["register"]],
        )
        if event.get("error_code") is not None:
            raise ValueError("Successful recorded read cannot carry an error code")
    elif outcome == "transient_error":
        if event.get("raw_value") is not None:
            raise ValueError("Transient recorded read cannot carry a value")
        if (
            event.get("error_code")
            not in contract["retry_policy"]["retryable_error_codes"]
        ):
            raise ValueError("Recorded read error code is not retryable")
    elif outcome == "fatal_error":
        if event.get("raw_value") is not None or not event.get("error_code"):
            raise ValueError("Fatal recorded read event is malformed")
    else:
        raise ValueError("Recorded census read outcome is invalid")


def _verify_conformant_read_sequence(
    events: list[dict[str, Any]],
    *,
    contract: dict[str, Any],
) -> None:
    reads = events[2:-1]
    cursor = 0
    max_retries = contract["retry_policy"]["max_read_retries"]
    for servo in contract["expected_servos"]:
        servo_id = servo["servo_id"]
        for plan in contract["read_plan"]:
            register = plan["register"]
            attempt = 0
            while True:
                if cursor >= len(reads):
                    raise ValueError(
                        "Recorded census trace is missing read: "
                        f"servo {servo_id} register {register}"
                    )
                event = reads[cursor]
                cursor += 1
                attempt += 1
                if event.get("operation") != "read":
                    raise ValueError(
                        "Recorded census trace read lifecycle is out of order"
                    )
                if (
                    event.get("servo_id") != servo_id
                    or event.get("register") != register
                    or event.get("attempt") != attempt
                ):
                    raise ValueError(
                        "Recorded census trace read order drifted: "
                        f"expected id={servo_id} register={register} attempt={attempt}"
                    )
                if event["outcome"] == "transient_error":
                    if attempt > max_retries:
                        raise ValueError(
                            "Recorded census trace retry bound was exceeded"
                        )
                    continue
                if event["outcome"] != "success":
                    raise ValueError(
                        "Conformant recorded census trace contains a failed read"
                    )
                if register == "ID" and event["raw_value"] != servo_id:
                    raise ValueError(
                        "Recorded census trace contains a duplicate or mismatched servo ID"
                    )
                break
    if cursor != len(reads):
        raise ValueError("Recorded census trace contains extra reads")
    close = events[-1]
    if close.get("outcome") != "success" or close.get("error_code") is not None:
        raise ValueError("Conformant recorded census trace close must succeed")


def _verify_observed_device_identity(payload: Any, *, contract: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or set(payload) != {"device_role", "usb", "bus"}:
        raise ValueError("Observed device identity fields are incomplete")
    target = contract["target_device_identity"]
    if payload.get("device_role") != target["device_role"]:
        raise ValueError("Observed device identity role mismatch")
    usb = payload.get("usb")
    if not isinstance(usb, dict) or set(usb) != {
        "vendor_id_hex",
        "product_id_hex",
        "serial_number",
        "canonical_path",
        "observed_aliases",
    }:
        raise ValueError(
            "Observed USB identity is incomplete; port-only identity is forbidden"
        )
    for field in ("vendor_id_hex", "product_id_hex", "serial_number", "canonical_path"):
        require_nonblank(usb.get(field), label=f"observed USB {field}")
    if usb["vendor_id_hex"] != target["usb"]["vendor_id_hex"]:
        raise ValueError("Observed device identity USB vendor mismatch")
    if usb["product_id_hex"] != target["usb"]["product_id_hex"]:
        raise ValueError("Observed device identity USB product mismatch")
    if usb["serial_number"] != target["usb"]["serial_number"]:
        raise ValueError("Observed device identity USB serial mismatch")
    if usb["canonical_path"] != target["usb"]["canonical_path"]:
        raise ValueError("Observed device identity canonical path mismatch")
    aliases = usb.get("observed_aliases")
    if not isinstance(aliases, list) or aliases != sorted(set(aliases)):
        raise ValueError("Observed device identity aliases are malformed")
    if set(aliases) & set(target["usb"]["forbidden_aliases"]):
        raise ValueError(
            "Observed device identity aliases include a forbidden role alias"
        )
    if aliases != target["usb"]["allowed_aliases"]:
        raise ValueError("Observed device identity aliases mismatch")
    if payload.get("bus") != target["bus"]:
        raise ValueError("Observed device identity bus protocol or baud mismatch")


def _validate_raw_value(register: str, value: Any, *, width_bytes: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"Read-only census register {register} requires an integer raw value"
        )
    if value < 0 or value >= 1 << (8 * width_bytes):
        raise ValueError(
            f"Read-only census register {register} raw value exceeds width"
        )
    if register == "Model_Number" and value != _MODEL_NUMBER:
        raise ValueError(f"Read-only census model number mismatch: {value}")
    if register == "ID" and value not in set(range(1, 7)):
        raise ValueError(f"Read-only census servo ID register is invalid: {value}")
    if register == "Baud_Rate" and value not in _BAUDRATE_CODE_TO_VALUE:
        raise ValueError(f"Read-only census baud code is unsupported: {value}")
    if register == "Present_Position" and value >= _MODEL_RESOLUTION:
        raise ValueError(
            f"Read-only census position is outside STS3215 resolution: {value}"
        )
    if register == "Present_Temperature" and value > 100:
        raise ValueError(
            f"Read-only census temperature is outside the declared range: {value}"
        )
    return value


def _decode_servo(raw: dict[str, int], *, expected: dict[str, Any]) -> dict[str, Any]:
    if set(raw) != _READ_REGISTER_NAMES:
        raise ValueError(
            f"Read-only census register shape mismatch for servo {expected['servo_id']}"
        )
    if raw["ID"] != expected["servo_id"]:
        raise ValueError(
            f"Read-only census servo identity mismatch: expected {expected['servo_id']} got {raw['ID']}"
        )
    if raw["Model_Number"] != expected["model_number"]:
        raise ValueError("Read-only census servo model mismatch")
    baudrate = _BAUDRATE_CODE_TO_VALUE[raw["Baud_Rate"]]
    return {
        "servo_id": expected["servo_id"],
        "joint_name": expected["joint_name"],
        "model": expected["model"],
        "model_number": raw["Model_Number"],
        "firmware_version": (
            f"{raw['Firmware_Major_Version']}.{raw['Firmware_Minor_Version']}"
        ),
        "baudrate": baudrate,
        "present_position_raw": raw["Present_Position"],
        "present_voltage_volts": round(raw["Present_Voltage"] / 10.0, 3),
        "present_temperature_celsius": raw["Present_Temperature"],
        "raw_registers": {key: raw[key] for key in sorted(raw)},
    }


def _empty_transport_audit(*, hardware_opened: bool) -> dict[str, Any]:
    return {
        "connect_calls": 0,
        "read_calls": 0,
        "close_calls": 0,
        "motor_register_writes": 0,
        "torque_changes": 0,
        "motion_commands": 0,
        "unexpected_operations": 0,
        "aborted_operations": 0,
        "unconsumed_events": 0,
        "hardware_opened": hardware_opened,
        "physical_follower_commanded": False,
    }


def _validate_transport_audit(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _TRANSPORT_AUDIT_FIELDS:
        raise ValueError("Read-only census transport audit fields are malformed")
    for field in _TRANSPORT_AUDIT_FIELDS - {
        "hardware_opened",
        "physical_follower_commanded",
    }:
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(
                f"Read-only census transport audit count is invalid: {field}"
            )
    if not isinstance(payload.get("hardware_opened"), bool):
        raise ValueError("Read-only census transport hardware_opened must be boolean")
    if not isinstance(payload.get("physical_follower_commanded"), bool):
        raise ValueError(
            "Read-only census transport follower command flag must be boolean"
        )
    return payload


def _resolve(repo_root: Path, path: Path) -> Path:
    resolved = path if path.is_absolute() else repo_root / path
    try:
        resolved.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(
            "Read-only census fixture path escapes the repository"
        ) from exc
    return resolved
