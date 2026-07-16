"""One-use, zero-write physical SO-101 servo census for T19.1."""

from __future__ import annotations

import copy
import hashlib
import shutil

from pathlib import Path
from typing import Any, Callable

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.authority_composer import (
    T19_1_MAX_REGISTER_READ_COUNT,
    T19_1_READONLY_ALLOWED_OPERATIONS,
    T19_1_READONLY_AUTHORITY_NOT_GRANTED,
    T19_1_READONLY_SESSION_PERMIT_SCHEMA_VERSION,
    T19_1_READ_PLAN,
)
from scenesmith.robot_lab.live_readonly_observation import (
    AuditedReadOnlyBusBackend,
    build_live_discovery_snapshot,
    construct_pinned_feetech_bus,
    enumerate_serial_candidates,
    enumerate_serial_identity_holders,
    require_no_serial_identity_holders,
    resolve_follower_identity,
    verify_live_discovery_snapshot,
    verify_live_servo_result,
    verify_serial_identity_holder_snapshot,
    verify_serial_identity_holder_stability,
)
from scenesmith.robot_lab.readonly_servo_census import (
    InjectedReadOnlyBusAdapter,
    build_live_census_contract,
    run_readonly_census,
    verify_live_census_contract,
)


T19_1_PRIVATE_SNAPSHOT_SCHEMA_VERSION = (
    "scenesmith.t19_1_readonly_hardware_snapshot_private.v1"
)
T19_1_REDACTED_MANIFEST_SCHEMA_VERSION = (
    "scenesmith.t19_1_readonly_hardware_snapshot_manifest.v1"
)
T19_1_LIVE_SERVO_RESULT_SCHEMA_VERSION = "scenesmith.live_readonly_servo_result.v2"
T19_1_PROOF_LABEL = "t19_1_live_readonly_hardware_snapshot_observed"


class _NoRetryRawBus:
    """Convert transport connection errors into a terminal, one-attempt failure."""

    def __init__(self, bus: Any):
        self._bus = bus

    def connect(self, *, handshake: bool) -> None:
        self._bus.connect(handshake=handshake)

    def read(
        self,
        register: str,
        motor: str,
        *,
        normalize: bool,
        num_retry: int,
    ) -> int:
        try:
            return self._bus.read(
                register,
                motor,
                normalize=normalize,
                num_retry=num_retry,
            )
        except ConnectionError as exc:
            raise RuntimeError("T19.1 terminal read failure; retry prohibited") from exc

    def disconnect(self, *, disable_torque: bool) -> None:
        self._bus.disconnect(disable_torque=disable_torque)


def capture_t19_1_serial_discovery(
    *,
    session_id: str,
    captured_at: str,
    serial_enumerator: Callable[[], list[dict[str, Any]]] = enumerate_serial_candidates,
) -> dict[str, Any]:
    """Enumerate only serial metadata; cameras are intentionally untouched."""

    return build_live_discovery_snapshot(
        session_id=session_id,
        captured_at=captured_at,
        serial_candidates=serial_enumerator(),
        avfoundation_devices=[],
        system_cameras=[],
    )


def execute_t19_1_readonly_servo_census(
    *,
    permit: dict[str, Any],
    discovery: dict[str, Any],
    calibration_file_sha256: str,
    bus_factory: Callable[[dict[str, Any]], Any],
    monotonic_ns: Callable[[], int],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute the exact six-servo/54-read/no-retry T19.1 census."""

    _verify_t19_1_permit_safety_contract(permit)
    verify_live_discovery_snapshot(discovery)
    if discovery.get("avfoundation_devices") != [] or discovery.get(
        "system_cameras"
    ) != []:
        raise ValueError("T19.1 serial discovery cannot contain camera metadata")
    if discovery.get("session_id") != permit.get("session_id"):
        raise ValueError("T19.1 discovery session drifted from permit")
    observed_identity = resolve_follower_identity(discovery)
    contract = build_live_census_contract(
        observed_device_identity=observed_identity,
        session_id=permit["session_id"],
        presence_lease_identity_sha256=permit["identity_sha256"],
        discovery_identity_sha256=discovery["identity_sha256"],
        calibration_file_sha256=calibration_file_sha256,
        issued_at=permit["issued_at"],
        expires_at=permit["expires_at"],
    )
    captured: dict[str, Any] = {}

    def transport_factory() -> InjectedReadOnlyBusAdapter:
        raw_bus = _NoRetryRawBus(bus_factory(contract))
        backend = AuditedReadOnlyBusBackend(
            bus=raw_bus,
            monotonic_ns=monotonic_ns,
        )
        captured["backend"] = backend
        target = contract["target_device_identity"]
        device_identity = {
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
            device_identity=device_identity,
            servo_names={
                servo["servo_id"]: servo["joint_name"]
                for servo in contract["expected_servos"]
            },
        )

    started = monotonic_ns()
    run = run_readonly_census(contract, transport_factory)
    finished = monotonic_ns()
    backend = captured.get("backend")
    if backend is None:
        raise RuntimeError("T19.1 live census backend was not constructed")
    counts = run["operation_counts"]
    if (
        counts.get("read_attempts") != T19_1_MAX_REGISTER_READ_COUNT
        or counts.get("read_successes") != T19_1_MAX_REGISTER_READ_COUNT
        or counts.get("read_retries") != 0
    ):
        raise ValueError("T19.1 live census did not preserve the exact 54-read plan")
    result = sign_payload(
        {
            "schema_version": T19_1_LIVE_SERVO_RESULT_SCHEMA_VERSION,
            "result_name": "pi05_live_readonly_servo_census",
            "qualification_scope": "physical_observation",
            "evidence_mode": "live_physical_read_only",
            "proof_label": "live_read_only_census_observed",
            "execution_contract_identity_sha256": permit["identity_sha256"],
            "census_contract_identity_sha256": contract["identity_sha256"],
            "observation_started_monotonic_ns": started,
            "observation_finished_monotonic_ns": finished,
            "transport_trace": backend.trace(),
            **run,
        }
    )
    verify_live_servo_result(
        result,
        execution_contract_identity_sha256=permit["identity_sha256"],
        live_census_contract=contract,
    )
    if any(servo.get("torque_enable_raw") != 0 for servo in result["servos"]):
        raise ValueError("T19.1 observed a torque-enabled servo")
    return contract, result


def build_t19_1_private_snapshot(
    *,
    runtime_profile_identity_sha256: str,
    request: dict[str, Any],
    decision: dict[str, Any],
    permit: dict[str, Any],
    discovery: dict[str, Any],
    census_contract: dict[str, Any],
    servo_result: dict[str, Any],
    pre_open_holders: dict[str, Any],
    post_close_holders: dict[str, Any],
    completed_at: str,
) -> dict[str, Any]:
    payload = {
        "schema_version": T19_1_PRIVATE_SNAPSHOT_SCHEMA_VERSION,
        "snapshot_name": "pi05_t19_1_private_readonly_hardware_snapshot",
        "qualification_scope": "physical_observation",
        "evidence_mode": "local_private_live_physical_read_only",
        "status": "accepted",
        "proof_labels": [T19_1_PROOF_LABEL],
        "session_id": permit.get("session_id"),
        "completed_at": completed_at,
        "runtime_profile_identity_sha256": runtime_profile_identity_sha256,
        "request": copy.deepcopy(request),
        "decision": copy.deepcopy(decision),
        "permit": copy.deepcopy(permit),
        "discovery": copy.deepcopy(discovery),
        "census_contract": copy.deepcopy(census_contract),
        "servo_result": copy.deepcopy(servo_result),
        "serial_identity_holder_snapshots": {
            "pre_open": copy.deepcopy(pre_open_holders),
            "post_close": copy.deepcopy(post_close_holders),
        },
        "operation_counts": copy.deepcopy(servo_result.get("operation_counts")),
        "hardware_opened": True,
        "physical_follower_commanded": False,
        "register_write_count": 0,
        "torque_change_count": 0,
        "motion_command_count": 0,
        "camera_accessed": False,
        "authority_not_granted": list(T19_1_READONLY_AUTHORITY_NOT_GRANTED),
    }
    signed = sign_payload(payload)
    verify_t19_1_private_snapshot(signed)
    return signed


def verify_t19_1_private_snapshot(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T19.1 private hardware snapshot")
    if (
        payload.get("schema_version") != T19_1_PRIVATE_SNAPSHOT_SCHEMA_VERSION
        or payload.get("snapshot_name")
        != "pi05_t19_1_private_readonly_hardware_snapshot"
        or payload.get("qualification_scope") != "physical_observation"
        or payload.get("evidence_mode")
        != "local_private_live_physical_read_only"
        or payload.get("status") != "accepted"
        or payload.get("proof_labels") != [T19_1_PROOF_LABEL]
    ):
        raise ValueError("T19.1 private snapshot classification drifted")
    request = payload.get("request")
    decision = payload.get("decision")
    permit = payload.get("permit")
    for name, artifact in (
        ("request", request),
        ("decision", decision),
        ("permit", permit),
    ):
        if not isinstance(artifact, dict):
            raise ValueError(f"T19.1 private snapshot {name} is missing")
        verify_signed_payload(artifact, label=f"T19.1 embedded {name}")
    if (
        decision.get("granted") is not True
        or decision.get("request_identity_sha256") != request.get("identity_sha256")
        or permit.get("request_identity_sha256") != request.get("identity_sha256")
        or permit.get("decision_identity_sha256") != decision.get("identity_sha256")
        or payload.get("session_id") != permit.get("session_id")
        or payload.get("runtime_profile_identity_sha256")
        != permit.get("runtime_profile_identity_sha256")
    ):
        raise ValueError("T19.1 private snapshot authority linkage drifted")
    discovery = payload.get("discovery")
    verify_live_discovery_snapshot(discovery)
    if (
        discovery.get("session_id") != permit.get("session_id")
        or discovery.get("avfoundation_devices") != []
        or discovery.get("system_cameras") != []
    ):
        raise ValueError("T19.1 private snapshot discovery drifted")
    expected_identity = resolve_follower_identity(discovery)
    contract = payload.get("census_contract")
    verify_live_census_contract(contract)
    target = contract["target_device_identity"]
    observed_target = {
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
    if (
        observed_target != expected_identity
        or contract.get("session_id") != permit.get("session_id")
        or contract.get("presence_lease_identity_sha256")
        != permit.get("identity_sha256")
        or contract.get("discovery_identity_sha256")
        != discovery.get("identity_sha256")
    ):
        raise ValueError("T19.1 census contract source linkage drifted")
    result = payload.get("servo_result")
    verify_live_servo_result(
        result,
        execution_contract_identity_sha256=permit["identity_sha256"],
        live_census_contract=contract,
    )
    holders = payload.get("serial_identity_holder_snapshots")
    if not isinstance(holders, dict) or set(holders) != {"pre_open", "post_close"}:
        raise ValueError("T19.1 holder snapshots are incomplete")
    for snapshot in holders.values():
        verify_serial_identity_holder_snapshot(snapshot)
        require_no_serial_identity_holders(snapshot)
    verify_serial_identity_holder_stability(holders["pre_open"], holders["post_close"])
    counts = result["operation_counts"]
    if (
        payload.get("operation_counts") != counts
        or counts.get("read_attempts") != T19_1_MAX_REGISTER_READ_COUNT
        or counts.get("read_successes") != T19_1_MAX_REGISTER_READ_COUNT
        or counts.get("read_retries") != 0
        or any(servo.get("torque_enable_raw") != 0 for servo in result["servos"])
    ):
        raise ValueError("T19.1 private snapshot census invariants drifted")
    if (
        payload.get("hardware_opened") is not True
        or payload.get("physical_follower_commanded") is not False
        or payload.get("register_write_count") != 0
        or payload.get("torque_change_count") != 0
        or payload.get("motion_command_count") != 0
        or payload.get("camera_accessed") is not False
        or payload.get("authority_not_granted")
        != list(T19_1_READONLY_AUTHORITY_NOT_GRANTED)
    ):
        raise ValueError("T19.1 private snapshot authority fields drifted")


def write_t19_1_private_snapshot(
    *,
    output_directory: Path,
    private_snapshot: dict[str, Any],
) -> dict[str, Any]:
    verify_t19_1_private_snapshot(private_snapshot)
    output = Path(output_directory)
    if output.exists():
        raise ValueError("T19.1 private output directory must be new and immutable")
    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        raise ValueError("T19.1 private temporary output already exists")
    try:
        temporary.mkdir(parents=True, exist_ok=False)
        path = temporary / "private_readonly_hardware_snapshot.json"
        dump_canonical_json(path, private_snapshot)
        reference = {
            "filename": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
            "identity_sha256": private_snapshot["identity_sha256"],
        }
        temporary.replace(output)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        raise
    return reference


def build_t19_1_redacted_manifest(
    *,
    private_snapshot: dict[str, Any],
    private_reference: dict[str, Any],
) -> dict[str, Any]:
    verify_t19_1_private_snapshot(private_snapshot)
    _verify_private_reference(private_reference, private_snapshot=private_snapshot)
    result = private_snapshot["servo_result"]
    holders = private_snapshot["serial_identity_holder_snapshots"]
    payload = {
        "schema_version": T19_1_REDACTED_MANIFEST_SCHEMA_VERSION,
        "manifest_name": "pi05_t19_1_readonly_hardware_snapshot",
        "qualification_scope": "physical_observation",
        "evidence_mode": "tracked_redacted_live_physical_read_only",
        "status": "accepted",
        "proof_labels": [T19_1_PROOF_LABEL],
        "session_id": private_snapshot["session_id"],
        "completed_at": private_snapshot["completed_at"],
        "private_reference": copy.deepcopy(private_reference),
        "request_identity_sha256": private_snapshot["request"]["identity_sha256"],
        "decision_identity_sha256": private_snapshot["decision"]["identity_sha256"],
        "permit_identity_sha256": private_snapshot["permit"]["identity_sha256"],
        "runtime_profile_identity_sha256": private_snapshot[
            "runtime_profile_identity_sha256"
        ],
        "discovery_identity_sha256": private_snapshot["discovery"][
            "identity_sha256"
        ],
        "target_device_identity_sha256": hashlib.sha256(
            canonical_json_bytes(result["target_device_identity"])
        ).hexdigest(),
        "census_contract_identity_sha256": private_snapshot["census_contract"][
            "identity_sha256"
        ],
        "servo_result_identity_sha256": result["identity_sha256"],
        "servos": copy.deepcopy(result["servos"]),
        "operation_counts": copy.deepcopy(result["operation_counts"]),
        "serial_identity_holder_snapshot_sha256": {
            name: snapshot["identity_sha256"] for name, snapshot in holders.items()
        },
        "serial_identity_holder_counts": {
            name: snapshot["deduplicated_holder_count"]
            for name, snapshot in holders.items()
        },
        "hardware_opened": True,
        "physical_follower_commanded": False,
        "register_write_count": 0,
        "torque_change_count": 0,
        "motion_command_count": 0,
        "camera_accessed": False,
        "authority_not_granted": list(T19_1_READONLY_AUTHORITY_NOT_GRANTED),
    }
    return sign_payload(payload)


def verify_t19_1_redacted_manifest(
    payload: dict[str, Any],
    *,
    private_snapshot: dict[str, Any],
    private_reference: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T19.1 redacted hardware manifest")
    expected = build_t19_1_redacted_manifest(
        private_snapshot=private_snapshot,
        private_reference=private_reference,
    )
    if payload != expected:
        raise ValueError("T19.1 redacted manifest drifted from private evidence")
    serialized = canonical_json_bytes(payload)
    serial_number = private_snapshot["servo_result"]["target_device_identity"][
        "usb"
    ]["serial_number"].encode("utf-8")
    if serial_number in serialized:
        raise ValueError("T19.1 redacted manifest leaked the hardware serial")


def _verify_private_reference(
    payload: Any,
    *,
    private_snapshot: dict[str, Any],
) -> None:
    if not isinstance(payload, dict) or set(payload) != {
        "filename",
        "sha256",
        "size_bytes",
        "identity_sha256",
    }:
        raise ValueError("T19.1 private reference is malformed")
    if (
        payload.get("filename") != "private_readonly_hardware_snapshot.json"
        or payload.get("identity_sha256") != private_snapshot.get("identity_sha256")
        or not isinstance(payload.get("size_bytes"), int)
        or payload["size_bytes"] <= 0
    ):
        raise ValueError("T19.1 private reference drifted")
    for field in ("sha256", "identity_sha256"):
        digest = require_nonblank(payload.get(field), label=f"T19.1 reference {field}")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"T19.1 reference {field} is invalid")


def _verify_t19_1_permit_safety_contract(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T19.1 session permit")
    if (
        payload.get("schema_version")
        != T19_1_READONLY_SESSION_PERMIT_SCHEMA_VERSION
        or payload.get("permit_name")
        != "pi05_t19_1_one_use_readonly_hardware_census"
        or payload.get("task_id") != "T19.1"
        or payload.get("use_limit") != 1
        or payload.get("maximum_register_read_count")
        != T19_1_MAX_REGISTER_READ_COUNT
        or payload.get("read_plan") != list(T19_1_READ_PLAN)
        or payload.get("expected_servo_ids") != list(range(1, 7))
        or payload.get("allowed_operations")
        != list(T19_1_READONLY_ALLOWED_OPERATIONS)
        or payload.get("register_write_count") != 0
        or payload.get("torque_change_count") != 0
        or payload.get("motion_command_count") != 0
        or payload.get("camera_access") is not False
        or payload.get("authority_not_granted")
        != list(T19_1_READONLY_AUTHORITY_NOT_GRANTED)
    ):
        raise ValueError("T19.1 permit safety contract drifted")


def default_t19_1_bus_factory(
    *,
    repo_root: Path,
) -> Callable[[dict[str, Any]], Any]:
    return lambda contract: construct_pinned_feetech_bus(
        repo_root=Path(repo_root).resolve(),
        census_contract=contract,
    )
