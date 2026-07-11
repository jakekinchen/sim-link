from __future__ import annotations

import ast
import copy
import hashlib
import json
import struct
import subprocess
import tempfile
import unittest
import zlib

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.leader_arm_bridge import (
    DEFAULT_LEADER_PORT,
    KNOWN_PHYSICAL_FOLLOWER_PORT,
)
from scenesmith.robot_lab.live_readonly_observation import (
    AuditedReadOnlyBusBackend,
    FFmpegNamedFiniteCamera,
    MAX_CAMERA_FAILURE_PREVIEW_BYTES,
    NamedCameraCaptureError,
    build_live_discovery_snapshot,
    build_live_execution_contract,
    build_operator_presence_lease,
    build_private_capture_failure_evidence,
    build_private_observation_evidence,
    build_redacted_observation_manifest,
    capture_finite_camera_frames,
    enumerate_serial_identity_holders,
    execute_live_servo_census,
    parse_avfoundation_video_devices,
    parse_serial_device_holders,
    parse_system_camera_devices,
    require_no_serial_device_holders,
    require_no_serial_identity_holders,
    resolve_camera_selection,
    resolve_follower_identity,
    verify_discovery_stability,
    verify_live_execution_contract,
    verify_operator_presence_lease,
    verify_redacted_observation_manifest,
    verify_serial_identity_holder_stability,
    verify_serial_identity_holder_snapshot,
    write_private_capture_failure_record,
    write_private_observation_bundle,
)
from scenesmith.robot_lab.readonly_servo_census import (
    build_live_census_contract,
    verify_live_census_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_STATE = copy.deepcopy(
    load_strict_json(REPO_ROOT / "docs" / "autonomous-workflow" / "project_state.json")
)
PROJECT_STATE["tasks"]["T16.5b"]["live_gate"] = "open"
SESSION_ID = "t16-5b-test-session"
ISSUED_AT = "2026-07-11T04:45:00-05:00"
VALID_UNTIL = "2026-07-11T04:50:00-05:00"
FOLLOWER_TTY_ALIAS = KNOWN_PHYSICAL_FOLLOWER_PORT.replace("/dev/cu.", "/dev/tty.", 1)
LEADER_TTY_ALIAS = DEFAULT_LEADER_PORT.replace("/dev/cu.", "/dev/tty.", 1)


def _serial_candidates() -> list[dict]:
    return [
        {
            "device": KNOWN_PHYSICAL_FOLLOWER_PORT,
            "aliases": [FOLLOWER_TTY_ALIAS],
            "vid": 0x0483,
            "pid": 0x5740,
            "serial_number": "5B3D0406411",
            "manufacturer": "STMicroelectronics",
            "product": "STM32 Virtual ComPort",
            "location": "1-2",
            "hwid": "USB VID:PID=0483:5740 SER=5B3D0406411",
        },
        {
            "device": DEFAULT_LEADER_PORT,
            "aliases": [LEADER_TTY_ALIAS],
            "vid": 0x0483,
            "pid": 0x5740,
            "serial_number": "5B3D0448141",
            "manufacturer": "STMicroelectronics",
            "product": "STM32 Virtual ComPort",
            "location": "1-3",
            "hwid": "USB VID:PID=0483:5740 SER=5B3D0448141",
        },
    ]


def _avfoundation_devices() -> list[dict]:
    return [
        {"index": 0, "name": "Desk Side Camera"},
        {"index": 1, "name": "Desk Overhead Camera"},
    ]


def _system_cameras() -> list[dict]:
    return [
        {
            "name": "Desk Side Camera",
            "unique_id": "side-camera-001",
            "model_id": "UVC Camera Vendor_1234 Product_0001",
        },
        {
            "name": "Desk Overhead Camera",
            "unique_id": "overhead-camera-001",
            "model_id": "UVC Camera Vendor_1234 Product_0002",
        },
    ]


def _lease() -> dict:
    return build_operator_presence_lease(
        project_state=PROJECT_STATE,
        session_id=SESSION_ID,
        issued_at=ISSUED_AT,
        valid_until=VALID_UNTIL,
    )


def _discovery() -> dict:
    return build_live_discovery_snapshot(
        session_id=SESSION_ID,
        captured_at=ISSUED_AT,
        serial_candidates=_serial_candidates(),
        avfoundation_devices=_avfoundation_devices(),
        system_cameras=_system_cameras(),
    )


def _execution_contract() -> dict:
    return build_live_execution_contract(
        project_state=PROJECT_STATE,
        presence_lease=_lease(),
        discovery=_discovery(),
        camera_indexes=[0, 1],
        calibration_path=(
            Path.home()
            / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
        ),
        issued_at=ISSUED_AT,
        expires_at=VALID_UNTIL,
        frame_count_per_camera=2,
    )


def _zero_holder_snapshot() -> dict:
    def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(command, 1, "", "")

    return enumerate_serial_identity_holders(
        KNOWN_PHYSICAL_FOLLOWER_PORT,
        [FOLLOWER_TTY_ALIAS],
        run_command=runner,
        path_exists=lambda path: True,
    )


def _png_frame(
    *,
    width: int = 4,
    height: int = 3,
    marker: bytes = b"x",
    valid_compression: bool = True,
) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    pixel = (marker or b"x")[0]
    raw_scanlines = b"".join(
        b"\x00" + bytes([pixel]) * (width * 3) for _ in range(height)
    )
    compressed = zlib.compress(raw_scanlines) if valid_compression else b"not-zlib"
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


class _TickingClock:
    def __init__(self, start: int = 1_000_000_000, step: int = 1_000_000):
        self.value = start
        self.step = step

    def __call__(self) -> int:
        value = self.value
        self.value += self.step
        return value


class _FakeBus:
    def __init__(self, *, transient_once: bool = False):
        self.calls: list[tuple] = []
        self.is_connected = False
        self.transient_once = transient_once
        self.transient_sent = False

    def connect(self, *, handshake: bool) -> None:
        self.calls.append(("connect", handshake))
        self.is_connected = True

    def read(
        self,
        register: str,
        motor: str,
        *,
        normalize: bool,
        num_retry: int,
    ) -> int:
        self.calls.append(("read", register, motor, normalize, num_retry))
        if (
            self.transient_once
            and not self.transient_sent
            and motor == "elbow_flex"
            and register == "Present_Position"
        ):
            self.transient_sent = True
            raise ConnectionError("simulated CRC timeout")
        servo_id = {
            "shoulder_pan": 1,
            "shoulder_lift": 2,
            "elbow_flex": 3,
            "wrist_flex": 4,
            "wrist_roll": 5,
            "gripper": 6,
        }[motor]
        return {
            "Model_Number": 777,
            "Firmware_Major_Version": 3,
            "Firmware_Minor_Version": 10 + servo_id,
            "ID": servo_id,
            "Baud_Rate": 0,
            "Torque_Enable": 0,
            "Present_Position": 1900 + servo_id * 10,
            "Present_Voltage": 120,
            "Present_Temperature": 24 + servo_id,
        }[register]

    def disconnect(self, *, disable_torque: bool) -> None:
        self.calls.append(("disconnect", disable_torque))
        self.is_connected = False

    def write(self, *args, **kwargs) -> None:
        raise AssertionError("write must never be called")


class _FakeCamera:
    def __init__(
        self,
        index: int,
        *,
        fail_read: bool = False,
        fail_release: bool = False,
    ):
        self.index = index
        self.fail_read = fail_read
        self.fail_release = fail_release
        self.calls: list[str] = []
        self.frame_index = 0

    def open(self) -> None:
        self.calls.append("open")

    def read(self) -> dict:
        self.calls.append("read")
        if self.fail_read:
            raise RuntimeError("camera read failed")
        payload = f"png-camera-{self.index}-frame-{self.frame_index}".encode()
        self.frame_index += 1
        return {
            "frame_bytes": payload,
            "encoding": "png",
            "width": 640,
            "height": 480,
            "channels": 3,
        }

    def release(self) -> None:
        self.calls.append("release")
        if self.fail_release:
            raise RuntimeError("camera release failed")


class _FakeFFmpegProcess:
    def __init__(
        self,
        *,
        stdout: bytes,
        stderr: bytes = b"",
        final_returncode: int = 0,
        timeout_count: int = 0,
    ):
        self.stdout_payload = stdout
        self.stderr_payload = stderr
        self.final_returncode = final_returncode
        self.timeout_count = timeout_count
        self.returncode: int | None = None
        self.calls: list[str] = []

    def communicate(self, *, timeout: int) -> tuple[bytes, bytes]:
        self.calls.append(f"communicate:{timeout}")
        if self.timeout_count:
            self.timeout_count -= 1
            raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=timeout)
        self.returncode = self.final_returncode
        return self.stdout_payload, self.stderr_payload

    def terminate(self) -> None:
        self.calls.append("terminate")

    def kill(self) -> None:
        self.calls.append("kill")


class _WrongIdentityBus(_FakeBus):
    def read(
        self,
        register: str,
        motor: str,
        *,
        normalize: bool,
        num_retry: int,
    ) -> int:
        value = super().read(
            register,
            motor,
            normalize=normalize,
            num_retry=num_retry,
        )
        if register == "Model_Number" and motor == "shoulder_pan":
            return 999
        return value


class _TorqueEnabledBus(_FakeBus):
    def read(
        self,
        register: str,
        motor: str,
        *,
        normalize: bool,
        num_retry: int,
    ) -> int:
        value = super().read(
            register,
            motor,
            normalize=normalize,
            num_retry=num_retry,
        )
        if register == "Torque_Enable" and motor == "wrist_flex":
            return 1
        return value


class LiveReadonlyObservationTests(unittest.TestCase):
    def test_presence_lease_is_short_scoped_and_fails_closed(self):
        lease = _lease()
        verify_operator_presence_lease(
            lease,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
        )
        self.assertEqual(lease["scope"], "live_read_only_census_and_camera_capture")
        self.assertEqual(lease["validity_seconds"], 300)
        self.assertEqual(
            lease["authority_id"], PROJECT_STATE["owner_authority"]["authority_id"]
        )

        with self.assertRaisesRegex(ValueError, "expired"):
            verify_operator_presence_lease(
                lease,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:50:01-05:00",
            )
        too_long = copy.deepcopy(lease)
        too_long["valid_until"] = "2026-07-11T05:00:01-05:00"
        too_long["validity_seconds"] = 901
        too_long = sign_payload(too_long)
        with self.assertRaisesRegex(ValueError, "duration"):
            verify_operator_presence_lease(
                too_long,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
            )
        closed_state = copy.deepcopy(PROJECT_STATE)
        closed_state["tasks"]["T16.5b"]["live_gate"] = "closed"
        with self.assertRaisesRegex(ValueError, "live gate"):
            verify_operator_presence_lease(
                lease,
                project_state=closed_state,
                now="2026-07-11T04:47:00-05:00",
            )

    def test_discovery_resolves_exact_follower_and_rejects_ambiguity(self):
        discovery = _discovery()
        identity = resolve_follower_identity(discovery)
        self.assertEqual(
            identity["usb"]["canonical_path"], KNOWN_PHYSICAL_FOLLOWER_PORT
        )
        self.assertEqual(identity["usb"]["serial_number"], "5B3D0406411")
        self.assertEqual(identity["usb"]["observed_aliases"], [FOLLOWER_TTY_ALIAS])
        self.assertEqual(identity["bus"]["protocol_version"], 0)

        missing_optional_label = copy.deepcopy(discovery)
        missing_optional_label["serial_candidates"][0]["manufacturer"] = None
        missing_optional_label = sign_payload(missing_optional_label)
        self.assertEqual(
            resolve_follower_identity(missing_optional_label),
            identity,
        )

        ambiguous = copy.deepcopy(discovery)
        duplicate = copy.deepcopy(ambiguous["serial_candidates"][0])
        duplicate["aliases"] = []
        ambiguous["serial_candidates"].append(duplicate)
        ambiguous = sign_payload(ambiguous)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            resolve_follower_identity(ambiguous)

        collision = copy.deepcopy(discovery)
        collision["serial_candidates"][1]["serial_number"] = "5B3D0406411"
        collision = sign_payload(collision)
        with self.assertRaisesRegex(ValueError, "leader|role"):
            resolve_follower_identity(collision)

    def test_discovery_stability_and_missing_identity_fail_closed(self):
        expected = _discovery()
        observed = build_live_discovery_snapshot(
            session_id=SESSION_ID,
            captured_at="2026-07-11T04:46:00-05:00",
            serial_candidates=_serial_candidates(),
            avfoundation_devices=_avfoundation_devices(),
            system_cameras=_system_cameras(),
        )
        verify_discovery_stability(expected, observed)

        changed = copy.deepcopy(observed)
        changed["serial_candidates"][0]["location"] = "9-9"
        changed = sign_payload(changed)
        with self.assertRaisesRegex(ValueError, "serial_candidates"):
            verify_discovery_stability(expected, changed)

        missing_serial = copy.deepcopy(expected)
        missing_serial["serial_candidates"][0]["serial_number"] = None
        missing_serial = sign_payload(missing_serial)
        with self.assertRaisesRegex(ValueError, "serial_number"):
            resolve_follower_identity(missing_serial)

    def test_discovery_stability_uses_camera_names_not_ephemeral_indexes(self):
        expected = _discovery()
        swapped = copy.deepcopy(expected)
        (
            swapped["avfoundation_devices"][0]["name"],
            swapped["avfoundation_devices"][1]["name"],
        ) = (
            swapped["avfoundation_devices"][1]["name"],
            swapped["avfoundation_devices"][0]["name"],
        )
        swapped["system_cameras"].reverse()
        swapped = sign_payload(swapped)
        verify_discovery_stability(expected, swapped)

        stable_drift = copy.deepcopy(swapped)
        stable_drift["avfoundation_devices"][0]["name"] = "Replacement Camera"
        stable_drift["system_cameras"][0]["name"] = "Replacement Camera"
        stable_drift = sign_payload(stable_drift)
        with self.assertRaisesRegex(ValueError, "stable camera identity"):
            verify_discovery_stability(expected, stable_drift)

        duplicate_name = copy.deepcopy(expected)
        duplicate_name["avfoundation_devices"][1]["name"] = duplicate_name[
            "avfoundation_devices"
        ][0]["name"]
        duplicate_name = sign_payload(duplicate_name)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve_camera_selection(duplicate_name, [0])

    def test_serial_holder_parser_and_zero_holder_gate_fail_closed(self):
        holders = parse_serial_device_holders("p62234\ncpython3.13\nf15\ntCHR\n")
        self.assertEqual(
            holders,
            [
                {
                    "pid": 62234,
                    "command": "python3.13",
                    "file_descriptors": ["15"],
                    "file_types": ["CHR"],
                }
            ],
        )
        with self.assertRaisesRegex(ValueError, "independent holder"):
            require_no_serial_device_holders(holders)
        require_no_serial_device_holders([])
        with self.assertRaisesRegex(ValueError, "unknown field"):
            parse_serial_device_holders("p1\ncbus\nzunexpected\n")

    def test_serial_identity_holder_gate_checks_canonical_and_tty_alias(self):
        alias = FOLLOWER_TTY_ALIAS
        outputs = {
            KNOWN_PHYSICAL_FOLLOWER_PORT: (1, ""),
            alias: (0, "p62234\ncpython3.13\nf15\ntCHR\n"),
        }

        def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            returncode, stdout = outputs[command[-1]]
            return subprocess.CompletedProcess(command, returncode, stdout, "")

        snapshot = enumerate_serial_identity_holders(
            KNOWN_PHYSICAL_FOLLOWER_PORT,
            [alias],
            run_command=runner,
            path_exists=lambda path: True,
        )
        verify_serial_identity_holder_snapshot(snapshot)
        self.assertEqual(snapshot["paths_checked"], [KNOWN_PHYSICAL_FOLLOWER_PORT, alias])
        self.assertEqual(snapshot["per_path_holder_counts"], [0, 1])
        self.assertEqual(snapshot["deduplicated_holder_count"], 1)
        self.assertEqual(snapshot["deduplicated_holders"][0]["paths"], [alias])
        with self.assertRaisesRegex(ValueError, "1 independent holder"):
            require_no_serial_identity_holders(snapshot)

    def test_serial_identity_holder_gate_deduplicates_same_fd_across_aliases(self):
        output = "p62234\ncpython3.13\nf15\ntCHR\n"

        def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            return subprocess.CompletedProcess(command, 0, output, "")

        snapshot = enumerate_serial_identity_holders(
            KNOWN_PHYSICAL_FOLLOWER_PORT,
            [FOLLOWER_TTY_ALIAS],
            run_command=runner,
            path_exists=lambda path: True,
        )
        self.assertEqual(snapshot["per_path_holder_counts"], [1, 1])
        self.assertEqual(snapshot["deduplicated_holder_count"], 1)
        self.assertEqual(
            snapshot["deduplicated_holders"][0]["paths"],
            [KNOWN_PHYSICAL_FOLLOWER_PORT, FOLLOWER_TTY_ALIAS],
        )

    def test_serial_identity_holder_gate_preserves_distinct_processes(self):
        outputs = {
            KNOWN_PHYSICAL_FOLLOWER_PORT: "p10\ncone\nf3\ntCHR\n",
            FOLLOWER_TTY_ALIAS: "p11\nctwo\nf4\ntCHR\n",
        }

        def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            return subprocess.CompletedProcess(command, 0, outputs[command[-1]], "")

        snapshot = enumerate_serial_identity_holders(
            KNOWN_PHYSICAL_FOLLOWER_PORT,
            [FOLLOWER_TTY_ALIAS],
            run_command=runner,
            path_exists=lambda path: True,
        )
        self.assertEqual(snapshot["deduplicated_holder_count"], 2)
        self.assertEqual(
            [holder["pid"] for holder in snapshot["deduplicated_holders"]],
            [10, 11],
        )

    def test_serial_identity_holder_stability_rejects_alias_existence_drift(self):
        def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            return subprocess.CompletedProcess(command, 1, "", "")

        before = enumerate_serial_identity_holders(
            KNOWN_PHYSICAL_FOLLOWER_PORT,
            [FOLLOWER_TTY_ALIAS],
            run_command=runner,
            path_exists=lambda path: True,
        )
        after = enumerate_serial_identity_holders(
            KNOWN_PHYSICAL_FOLLOWER_PORT,
            [FOLLOWER_TTY_ALIAS],
            run_command=runner,
            path_exists=lambda path: path == KNOWN_PHYSICAL_FOLLOWER_PORT,
        )
        require_no_serial_identity_holders(before)
        with self.assertRaisesRegex(ValueError, "existence drift"):
            verify_serial_identity_holder_stability(before, after)

    def test_serial_identity_holder_gate_rejects_alias_and_command_drift(self):
        with self.assertRaisesRegex(ValueError, "signed follower alias"):
            enumerate_serial_identity_holders(
                KNOWN_PHYSICAL_FOLLOWER_PORT,
                [],
                run_command=lambda *args, **kwargs: None,
                path_exists=lambda path: True,
            )

        def failed_runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            return subprocess.CompletedProcess(command, 2, "", "failure")

        with self.assertRaisesRegex(RuntimeError, "command failed"):
            enumerate_serial_identity_holders(
                KNOWN_PHYSICAL_FOLLOWER_PORT,
                [FOLLOWER_TTY_ALIAS],
                run_command=failed_runner,
                path_exists=lambda path: True,
            )

    def test_camera_metadata_parsers_and_selection_are_exact(self):
        ffmpeg = """
[AVFoundation indev @ 0x1] AVFoundation video devices:
[AVFoundation indev @ 0x1] [0] Desk Side Camera
[AVFoundation indev @ 0x1] [1] Desk Overhead Camera
[AVFoundation indev @ 0x1] AVFoundation audio devices:
[AVFoundation indev @ 0x1] [0] MacBook Microphone
"""
        system_payload = {
            "SPCameraDataType": [
                {
                    "_name": "Desk Side Camera",
                    "spcamera_unique-id": "side-camera-001",
                    "spcamera_model-id": "UVC Camera Vendor_1234 Product_0001",
                },
                {
                    "_name": "Desk Overhead Camera",
                    "spcamera_unique-id": "overhead-camera-001",
                    "spcamera_model-id": "UVC Camera Vendor_1234 Product_0002",
                },
            ]
        }
        self.assertEqual(
            parse_avfoundation_video_devices(ffmpeg), _avfoundation_devices()
        )
        self.assertEqual(parse_system_camera_devices(system_payload), _system_cameras())
        selected = resolve_camera_selection(_discovery(), [1, 0])
        self.assertEqual([camera["index"] for camera in selected], [0, 1])

        duplicate = copy.deepcopy(_discovery())
        duplicate["system_cameras"].append(
            copy.deepcopy(duplicate["system_cameras"][0])
        )
        duplicate = sign_payload(duplicate)
        with self.assertRaisesRegex(ValueError, "exactly one|ambiguous"):
            resolve_camera_selection(duplicate, [0])

    def test_live_contract_is_protocol_zero_and_rejects_resigned_drift(self):
        discovery = _discovery()
        identity = resolve_follower_identity(discovery)
        contract = build_live_census_contract(
            observed_device_identity=identity,
            session_id=SESSION_ID,
            presence_lease_identity_sha256=_lease()["identity_sha256"],
            discovery_identity_sha256=discovery["identity_sha256"],
            calibration_file_sha256="a" * 64,
            issued_at=ISSUED_AT,
            expires_at=VALID_UNTIL,
        )
        verify_live_census_contract(contract)
        self.assertEqual(
            contract["target_device_identity"]["bus"]["protocol_version"], 0
        )
        changed = copy.deepcopy(contract)
        changed["target_device_identity"]["bus"]["protocol_version"] = 1
        changed = sign_payload(changed)
        with self.assertRaisesRegex(ValueError, "protocol"):
            verify_live_census_contract(changed)

    def test_execution_contract_binds_lease_discovery_calibration_and_cameras(self):
        contract = _execution_contract()
        verify_live_execution_contract(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
        )
        self.assertEqual(contract["frame_count_per_camera"], 2)
        self.assertEqual(contract["camera_read_timeout_seconds"], 5)
        self.assertEqual([camera["index"] for camera in contract["cameras"]], [0, 1])
        self.assertEqual(
            contract["live_census_contract"]["target_device_identity"]["bus"][
                "protocol_version"
            ],
            0,
        )
        changed = copy.deepcopy(contract)
        changed["presence_lease_identity_sha256"] = "0" * 64
        changed = sign_payload(changed)
        with self.assertRaisesRegex(ValueError, "lease"):
            verify_live_execution_contract(
                changed,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
            )

    def test_audited_bus_calls_only_no_handshake_reads_and_no_write_close(self):
        bus = _FakeBus(transient_once=True)
        backend = AuditedReadOnlyBusBackend(bus=bus, monotonic_ns=_TickingClock())
        backend.connect(handshake=False)
        self.assertEqual(
            backend.read(
                "Model_Number",
                "shoulder_pan",
                normalize=False,
                num_retry=0,
            ),
            777,
        )
        backend.disconnect(disable_torque=False)
        self.assertEqual(
            bus.calls,
            [
                ("connect", False),
                ("read", "Model_Number", "shoulder_pan", False, 0),
                ("disconnect", False),
            ],
        )
        self.assertFalse(hasattr(backend, "write"))
        self.assertFalse(hasattr(backend, "disable_torque"))

    def test_live_servo_census_retries_once_and_never_commands_follower(self):
        contract = _execution_contract()
        bus = _FakeBus(transient_once=True)
        result = execute_live_servo_census(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            bus_factory=lambda census_contract: bus,
            monotonic_ns=_TickingClock(),
        )
        self.assertEqual(result["proof_label"], "live_read_only_census_observed")
        self.assertTrue(result["hardware_opened"])
        self.assertFalse(result["physical_follower_commanded"])
        self.assertEqual(result["operation_counts"]["read_attempts"], 55)
        self.assertEqual(result["operation_counts"]["read_retries"], 1)
        self.assertEqual(result["operation_counts"]["motor_register_writes"], 0)
        self.assertTrue(
            all(servo["torque_enabled"] is False for servo in result["servos"])
        )
        self.assertEqual(bus.calls[0], ("connect", False))
        self.assertEqual(bus.calls[-1], ("disconnect", False))

    def test_live_servo_identity_and_resigned_trace_tampering_fail_closed(self):
        contract = _execution_contract()
        with self.assertRaisesRegex(ValueError, "model"):
            execute_live_servo_census(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                bus_factory=lambda census_contract: _WrongIdentityBus(),
                monotonic_ns=_TickingClock(),
            )

        result = execute_live_servo_census(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            bus_factory=lambda census_contract: _FakeBus(),
            monotonic_ns=_TickingClock(),
        )
        frames = capture_finite_camera_frames(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            camera_factory=lambda camera: _FakeCamera(camera["index"]),
            monotonic_ns=_TickingClock(start=2_000_000_000),
            wall_time=lambda: "2026-07-11T04:47:00-05:00",
        )
        tampered = copy.deepcopy(result)
        tampered["transport_trace"][1]["operation"] = "write"
        tampered = sign_payload(tampered)
        with self.assertRaisesRegex(ValueError, "unexpected operation"):
            build_private_observation_evidence(
                execution_contract=contract,
                servo_result=tampered,
                frames=frames,
                pre_open_discovery=_discovery(),
                post_close_discovery=_discovery(),
                pre_open_serial_holder_snapshot=_zero_holder_snapshot(),
                post_close_serial_holder_snapshot=_zero_holder_snapshot(),
            )

        torque_trace = copy.deepcopy(result)
        torque_event = next(
            event
            for event in torque_trace["transport_trace"]
            if event.get("operation") == "read"
            and event.get("motor") == "wrist_flex"
            and event.get("register") == "Torque_Enable"
        )
        torque_event["raw_value"] = 1
        with self.assertRaisesRegex(ValueError, "torque is not disabled"):
            build_private_observation_evidence(
                execution_contract=contract,
                servo_result=sign_payload(torque_trace),
                frames=frames,
                pre_open_discovery=_discovery(),
                post_close_discovery=_discovery(),
                pre_open_serial_holder_snapshot=_zero_holder_snapshot(),
                post_close_serial_holder_snapshot=_zero_holder_snapshot(),
            )

        decoded_tamper = copy.deepcopy(result)
        decoded_tamper["servos"][3]["torque_enabled"] = True
        with self.assertRaisesRegex(ValueError, "decoded evidence"):
            build_private_observation_evidence(
                execution_contract=contract,
                servo_result=sign_payload(decoded_tamper),
                frames=frames,
                pre_open_discovery=_discovery(),
                post_close_discovery=_discovery(),
                pre_open_serial_holder_snapshot=_zero_holder_snapshot(),
                post_close_serial_holder_snapshot=_zero_holder_snapshot(),
            )

    def test_live_servo_census_rejects_one_enabled_servo_and_closes_no_write(self):
        contract = _execution_contract()
        bus = _TorqueEnabledBus()
        with self.assertRaisesRegex(ValueError, "torque is not disabled"):
            execute_live_servo_census(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                bus_factory=lambda census_contract: bus,
                monotonic_ns=_TickingClock(),
            )
        self.assertEqual(bus.calls[-1], ("disconnect", False))
        self.assertFalse(any(call[0] == "write" for call in bus.calls))

    def test_camera_capture_is_finite_timestamped_and_releases_once(self):
        contract = _execution_contract()
        cameras: dict[int, _FakeCamera] = {}

        def factory(camera: dict) -> _FakeCamera:
            instance = _FakeCamera(camera["index"])
            cameras[camera["index"]] = instance
            return instance

        frames = capture_finite_camera_frames(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            camera_factory=factory,
            monotonic_ns=_TickingClock(),
            wall_time=lambda: "2026-07-11T04:47:00-05:00",
        )
        self.assertEqual(len(frames), 4)
        self.assertTrue(all(frame["frame_sha256"] for frame in frames))
        for camera in cameras.values():
            self.assertEqual(camera.calls, ["open", "read", "read", "release"])

    def test_named_ffmpeg_camera_is_name_bound_finite_and_audited(self):
        camera_identity = _execution_contract()["cameras"][0]
        process = _FakeFFmpegProcess(
            stdout=_png_frame(marker=b"one") + _png_frame(marker=b"two")
        )
        invocation: dict = {}

        def popen_factory(command: list[str], **kwargs) -> _FakeFFmpegProcess:
            invocation["command"] = command
            invocation["kwargs"] = kwargs
            return process

        camera = FFmpegNamedFiniteCamera(
            camera_identity,
            expected_frame_count=2,
            read_timeout_seconds=5,
            monotonic_ns=_TickingClock(),
            popen_factory=popen_factory,
        )
        camera.open()
        first = camera.read()
        second = camera.read()
        with self.assertRaisesRegex(RuntimeError, "finite frame count"):
            camera.read()
        camera.release()

        self.assertEqual(first["width"], 4)
        self.assertEqual(first["height"], 3)
        self.assertEqual(first["channels"], 3)
        self.assertNotEqual(first["frame_bytes"], second["frame_bytes"])
        input_index = invocation["command"].index("-i") + 1
        self.assertEqual(
            invocation["command"][input_index],
            f"{camera_identity['name']}:none",
        )
        self.assertFalse(invocation["kwargs"]["shell"])
        audit = camera.audit()
        self.assertEqual(audit["subprocess_start_successes"], 1)
        self.assertEqual(audit["subprocess_communicate_successes"], 1)
        self.assertEqual(audit["subprocess_wait_successes"], 1)
        self.assertEqual(audit["frames_delivered"], 2)
        self.assertEqual(audit["release_successes"], 1)
        self.assertEqual(audit["subprocess_terminate_attempts"], 0)

    def test_named_ffmpeg_camera_rejects_bad_streams_and_cleans_timeout(self):
        camera_identity = _execution_contract()["cameras"][0]
        valid = _png_frame(marker=b"one") + _png_frame(marker=b"two")
        cases = (
            (valid[:-5], b"", 0, "truncated"),
            (valid + b"extra", b"", 0, "extra trailing"),
            (
                _png_frame(valid_compression=False) + _png_frame(),
                b"",
                0,
                "compressed pixels",
            ),
            (valid, b"", 1, "subprocess failed"),
            (valid, b"ffmpeg warning", 0, "emitted stderr"),
        )
        for stdout, stderr, returncode, message in cases:
            with self.subTest(message=message):
                process = _FakeFFmpegProcess(
                    stdout=stdout,
                    stderr=stderr,
                    final_returncode=returncode,
                )
                camera = FFmpegNamedFiniteCamera(
                    camera_identity,
                    expected_frame_count=2,
                    monotonic_ns=_TickingClock(),
                    popen_factory=lambda *args, process=process, **kwargs: process,
                )
                camera.open()
                with self.assertRaisesRegex((ValueError, RuntimeError), message):
                    camera.read()
                camera.release()

        timed_out = _FakeFFmpegProcess(stdout=valid, timeout_count=2)
        camera = FFmpegNamedFiniteCamera(
            camera_identity,
            expected_frame_count=2,
            monotonic_ns=_TickingClock(),
            popen_factory=lambda *args, **kwargs: timed_out,
        )
        camera.open()
        with self.assertRaisesRegex(TimeoutError, "exceeded"):
            camera.read()
        camera.release()
        self.assertIn("terminate", timed_out.calls)
        self.assertIn("kill", timed_out.calls)
        audit = camera.audit()
        self.assertEqual(audit["subprocess_terminate_attempts"], 1)
        self.assertEqual(audit["subprocess_kill_attempts"], 1)
        self.assertEqual(audit["subprocess_communicate_attempts"], 3)
        self.assertEqual(audit["subprocess_wait_attempts"], 3)

    def test_named_ffmpeg_failure_diagnostic_is_bounded_redacted_and_signed(self):
        contract = _execution_contract()
        camera_identity = contract["cameras"][0]
        stderr = (
            b"camera="
            + camera_identity["name"].encode()
            + b" unique="
            + camera_identity["unique_id"].encode()
            + b" model="
            + camera_identity["model_id"].encode()
            + b" path=/Users/kelly/private/camera.log token=5B3D0406411\x00\xff "
            + b"x" * (MAX_CAMERA_FAILURE_PREVIEW_BYTES * 2)
        )
        process = _FakeFFmpegProcess(
            stdout=b"partial-png",
            stderr=stderr,
            final_returncode=7,
        )

        def factory(camera: dict) -> FFmpegNamedFiniteCamera:
            return FFmpegNamedFiniteCamera(
                camera,
                expected_frame_count=2,
                monotonic_ns=_TickingClock(),
                popen_factory=lambda *args, **kwargs: process,
            )

        with self.assertRaises(NamedCameraCaptureError) as captured:
            capture_finite_camera_frames(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                camera_factory=factory,
                monotonic_ns=_TickingClock(),
                wall_time=lambda: "2026-07-11T04:47:00-05:00",
            )
        diagnostic = captured.exception.diagnostic
        verify_signed_payload(diagnostic, label="Named camera failure diagnostic")
        self.assertEqual(diagnostic["stage"], "subprocess_nonzero_exit")
        self.assertEqual(diagnostic["return_code"], 7)
        self.assertEqual(diagnostic["stdout"]["byte_count"], len(b"partial-png"))
        self.assertEqual(
            diagnostic["stdout"]["sha256"], hashlib.sha256(b"partial-png").hexdigest()
        )
        self.assertEqual(diagnostic["stderr"]["byte_count"], len(stderr))
        self.assertEqual(
            diagnostic["stderr"]["sha256"], hashlib.sha256(stderr).hexdigest()
        )
        self.assertTrue(diagnostic["stderr"]["preview_truncated"])
        preview = diagnostic["stderr"]["sanitized_preview"]
        self.assertLessEqual(len(preview), MAX_CAMERA_FAILURE_PREVIEW_BYTES)
        self.assertNotIn(camera_identity["name"], preview)
        self.assertNotIn(camera_identity["unique_id"], preview)
        self.assertNotIn(camera_identity["model_id"], preview)
        self.assertNotIn("/Users/kelly", preview)
        self.assertNotIn("5B3D0406411", preview)
        self.assertNotIn("\x00", preview)
        self.assertEqual(diagnostic["primary_error_type"], "RuntimeError")
        self.assertIsNone(diagnostic["cleanup_error_type"])
        self.assertIsInstance(captured.exception.__cause__, RuntimeError)
        self.assertEqual(diagnostic["subprocess_audit"]["release_successes"], 1)
        self.assertFalse(diagnostic["physical_follower_commanded"])
        self.assertEqual(diagnostic["proof_labels"], [])

    def test_named_ffmpeg_failure_preserves_primary_and_cleanup_errors(self):
        contract = _execution_contract()
        process = _FakeFFmpegProcess(
            stdout=b"partial",
            stderr=b"device unavailable",
            final_returncode=3,
        )

        class FailingReleaseCamera(FFmpegNamedFiniteCamera):
            def release(self) -> None:
                super().release()
                raise RuntimeError("release failed")

        def factory(camera: dict) -> FFmpegNamedFiniteCamera:
            return FailingReleaseCamera(
                camera,
                expected_frame_count=2,
                monotonic_ns=_TickingClock(),
                popen_factory=lambda *args, **kwargs: process,
            )

        with self.assertRaises(BaseExceptionGroup) as captured:
            capture_finite_camera_frames(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                camera_factory=factory,
                monotonic_ns=_TickingClock(),
                wall_time=lambda: "2026-07-11T04:47:00-05:00",
            )
        self.assertEqual(len(captured.exception.exceptions), 2)
        primary, cleanup = captured.exception.exceptions
        self.assertIsInstance(primary, NamedCameraCaptureError)
        self.assertIsInstance(primary.__cause__, RuntimeError)
        self.assertEqual(primary.diagnostic["cleanup_error_type"], "RuntimeError")
        self.assertIn("release failed", str(cleanup))

    def test_named_ffmpeg_timeout_diagnostic_binds_terminate_kill_cleanup(self):
        contract = _execution_contract()
        process = _FakeFFmpegProcess(
            stdout=_png_frame(marker=b"one") + _png_frame(marker=b"two"),
            timeout_count=2,
        )

        def factory(camera: dict) -> FFmpegNamedFiniteCamera:
            return FFmpegNamedFiniteCamera(
                camera,
                expected_frame_count=2,
                monotonic_ns=_TickingClock(),
                popen_factory=lambda *args, **kwargs: process,
            )

        with self.assertRaises(NamedCameraCaptureError) as captured:
            capture_finite_camera_frames(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                camera_factory=factory,
                monotonic_ns=_TickingClock(),
                wall_time=lambda: "2026-07-11T04:47:00-05:00",
            )
        diagnostic = captured.exception.diagnostic
        self.assertEqual(diagnostic["stage"], "subprocess_timeout")
        self.assertIsInstance(captured.exception.__cause__, TimeoutError)
        self.assertEqual(
            diagnostic["subprocess_audit"]["subprocess_terminate_attempts"], 1
        )
        self.assertEqual(
            diagnostic["subprocess_audit"]["subprocess_kill_attempts"], 1
        )
        self.assertIn("terminate", process.calls)
        self.assertIn("kill", process.calls)

    def test_named_ffmpeg_diagnostic_exact_bound_and_resigned_tamper_fail_closed(self):
        contract = _execution_contract()
        stderr = b"x" * MAX_CAMERA_FAILURE_PREVIEW_BYTES
        process = _FakeFFmpegProcess(
            stdout=b"partial",
            stderr=stderr,
            final_returncode=4,
        )

        def factory(camera: dict) -> FFmpegNamedFiniteCamera:
            return FFmpegNamedFiniteCamera(
                camera,
                expected_frame_count=2,
                monotonic_ns=_TickingClock(),
                popen_factory=lambda *args, **kwargs: process,
            )

        with self.assertRaises(NamedCameraCaptureError) as captured:
            capture_finite_camera_frames(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                camera_factory=factory,
                monotonic_ns=_TickingClock(),
                wall_time=lambda: "2026-07-11T04:47:00-05:00",
            )
        diagnostic = captured.exception.diagnostic
        self.assertFalse(diagnostic["stderr"]["preview_truncated"])
        self.assertEqual(
            len(diagnostic["stderr"]["sanitized_preview"]),
            MAX_CAMERA_FAILURE_PREVIEW_BYTES,
        )
        tampered = copy.deepcopy(diagnostic)
        tampered["proof_labels"] = ["physical_observation_capture"]
        tampered = sign_payload(tampered)
        with self.assertRaisesRegex(ValueError, "authority fields"):
            NamedCameraCaptureError(tampered)

    def test_private_camera_failure_record_is_signed_immutable_and_label_free(self):
        contract = _execution_contract()
        process = _FakeFFmpegProcess(
            stdout=b"partial",
            stderr=b"camera input unavailable",
            final_returncode=2,
        )

        def factory(camera: dict) -> FFmpegNamedFiniteCamera:
            return FFmpegNamedFiniteCamera(
                camera,
                expected_frame_count=2,
                monotonic_ns=_TickingClock(),
                popen_factory=lambda *args, **kwargs: process,
            )

        with self.assertRaises(NamedCameraCaptureError) as captured:
            capture_finite_camera_frames(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                camera_factory=factory,
                monotonic_ns=_TickingClock(),
                wall_time=lambda: "2026-07-11T04:47:00-05:00",
            )
        servo_result = execute_live_servo_census(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            bus_factory=lambda census_contract: _FakeBus(),
            monotonic_ns=_TickingClock(),
        )
        failure = build_private_capture_failure_evidence(
            execution_contract=contract,
            servo_result=servo_result,
            error=captured.exception,
            pre_open_discovery=_discovery(),
            pre_open_serial_holder_snapshot=_zero_holder_snapshot(),
            post_close_serial_holder_snapshot=_zero_holder_snapshot(),
            failed_at="2026-07-11T04:47:01-05:00",
            elapsed_seconds=1.25,
        )
        verify_signed_payload(failure, label="Private capture failure evidence")
        self.assertEqual(failure["proof_labels"], [])
        self.assertFalse(failure["tracked_success_manifest_written"])
        self.assertFalse(failure["physical_follower_commanded"])
        self.assertEqual(
            failure["serial_identity_holder_counts"],
            {"pre_open": 0, "post_close": 0},
        )
        self.assertEqual(
            failure["camera_failure_diagnostic"]["identity_sha256"],
            captured.exception.diagnostic["identity_sha256"],
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "failure"
            reference = write_private_capture_failure_record(
                output_directory=output,
                failure_evidence=failure,
            )
            written = load_strict_json(output / "private_capture_failure.json")
            self.assertEqual(written, failure)
            self.assertEqual(
                reference["sha256"],
                hashlib.sha256(
                    (output / reference["filename"]).read_bytes()
                ).hexdigest(),
            )
            with self.assertRaisesRegex(ValueError, "new and immutable"):
                write_private_capture_failure_record(
                    output_directory=output,
                    failure_evidence=failure,
                )

    def test_named_ffmpeg_audits_flow_into_private_and_redacted_evidence(self):
        contract = _execution_contract()
        clock = _TickingClock(start=2_000_000_000)

        def camera_factory(camera_identity: dict) -> FFmpegNamedFiniteCamera:
            process = _FakeFFmpegProcess(
                stdout=_png_frame(marker=b"one") + _png_frame(marker=b"two")
            )
            return FFmpegNamedFiniteCamera(
                camera_identity,
                expected_frame_count=2,
                monotonic_ns=clock,
                popen_factory=lambda *args, process=process, **kwargs: process,
            )

        frames = capture_finite_camera_frames(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            camera_factory=camera_factory,
            monotonic_ns=clock,
            wall_time=lambda: "2026-07-11T04:47:00-05:00",
        )
        servo_result = execute_live_servo_census(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            bus_factory=lambda census_contract: _FakeBus(),
            monotonic_ns=_TickingClock(),
        )
        private = build_private_observation_evidence(
            execution_contract=contract,
            servo_result=servo_result,
            frames=frames,
            pre_open_discovery=_discovery(),
            post_close_discovery=_discovery(),
            pre_open_serial_holder_snapshot=_zero_holder_snapshot(),
            post_close_serial_holder_snapshot=_zero_holder_snapshot(),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            refs = write_private_observation_bundle(
                output_directory=Path(temporary_directory) / "bundle",
                private_evidence=private,
                frames=frames,
            )
            manifest = build_redacted_observation_manifest(
                private_evidence=private,
                private_bundle_refs=refs,
            )
        counts = private["camera_operation_counts"]
        self.assertEqual(counts["subprocess_start_successes"], 2)
        self.assertEqual(counts["subprocess_communicate_successes"], 2)
        self.assertEqual(counts["subprocess_wait_successes"], 2)
        self.assertEqual(counts["subprocess_terminate_attempts"], 0)
        self.assertEqual(counts["subprocess_kill_attempts"], 0)
        self.assertEqual(counts["capture_property_writes"], 0)
        self.assertEqual(
            private["serial_identity_holder_counts"],
            {
                "pre_open": 0,
                "post_close": 0,
            },
        )
        self.assertEqual(
            {
                stage: evidence["deduplicated_holder_count"]
                for stage, evidence in manifest[
                    "serial_identity_holder_evidence"
                ].items()
            },
            private["serial_identity_holder_counts"],
        )
        for stage, evidence in manifest["serial_identity_holder_evidence"].items():
            self.assertEqual(evidence["path_count"], 2)
            self.assertEqual(evidence["per_path_holder_counts"], [0, 0])
            self.assertEqual(len(evidence["path_identity_sha256"]), 2)
            self.assertTrue(evidence["paths_all_existed"])
            self.assertEqual(
                evidence["snapshot_identity_sha256"],
                private["serial_identity_holder_snapshot_sha256"][stage],
            )
        self.assertTrue(
            all(camera["camera_backend_audit_sha256"] for camera in manifest["cameras"])
        )

    def test_camera_primary_and_release_errors_are_both_preserved(self):
        contract = _execution_contract()

        def factory(camera: dict) -> _FakeCamera:
            return _FakeCamera(camera["index"], fail_read=True, fail_release=True)

        with self.assertRaises(BaseExceptionGroup) as captured:
            capture_finite_camera_frames(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                camera_factory=factory,
                monotonic_ns=_TickingClock(),
                wall_time=lambda: "2026-07-11T04:47:00-05:00",
            )
        self.assertEqual(len(captured.exception.exceptions), 2)
        self.assertIn("read", str(captured.exception.exceptions[0]))
        self.assertIn("release", str(captured.exception.exceptions[1]))

    def test_camera_timestamp_and_private_frame_hash_fail_closed(self):
        contract = _execution_contract()
        with self.assertRaisesRegex(ValueError, "timestamps regressed"):
            capture_finite_camera_frames(
                contract,
                project_state=PROJECT_STATE,
                now="2026-07-11T04:47:00-05:00",
                camera_factory=lambda camera: _FakeCamera(camera["index"]),
                monotonic_ns=_TickingClock(step=0),
                wall_time=lambda: "2026-07-11T04:47:00-05:00",
            )

        frames = capture_finite_camera_frames(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            camera_factory=lambda camera: _FakeCamera(camera["index"]),
            monotonic_ns=_TickingClock(),
            wall_time=lambda: "2026-07-11T04:47:00-05:00",
        )
        frames[0]["frame_bytes"] = b"tampered"
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ValueError, "content hash"):
                write_private_observation_bundle(
                    output_directory=Path(temporary_directory) / "bundle",
                    private_evidence=sign_payload({"placeholder": True}),
                    frames=frames,
                )

    def test_private_evidence_and_redacted_manifest_keep_raw_data_separate(self):
        contract = _execution_contract()
        bus = _FakeBus()
        servo_result = execute_live_servo_census(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            bus_factory=lambda census_contract: bus,
            monotonic_ns=_TickingClock(),
        )
        frames = capture_finite_camera_frames(
            contract,
            project_state=PROJECT_STATE,
            now="2026-07-11T04:47:00-05:00",
            camera_factory=lambda camera: _FakeCamera(camera["index"]),
            monotonic_ns=_TickingClock(start=2_000_000_000),
            wall_time=lambda: "2026-07-11T04:47:00-05:00",
        )
        private = build_private_observation_evidence(
            execution_contract=contract,
            servo_result=servo_result,
            frames=frames,
            pre_open_discovery=_discovery(),
            post_close_discovery=_discovery(),
            pre_open_serial_holder_snapshot=_zero_holder_snapshot(),
            post_close_serial_holder_snapshot=_zero_holder_snapshot(),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            refs = write_private_observation_bundle(
                output_directory=Path(temporary_directory) / "bundle",
                private_evidence=private,
                frames=frames,
            )
            manifest = build_redacted_observation_manifest(
                private_evidence=private,
                private_bundle_refs=refs,
            )
            with self.assertRaisesRegex(ValueError, "new and immutable"):
                write_private_observation_bundle(
                    output_directory=Path(temporary_directory) / "bundle",
                    private_evidence=private,
                    frames=frames,
                )
            verify_redacted_observation_manifest(
                manifest,
                private_evidence=private,
                private_bundle_refs=refs,
            )
        private_json = json.dumps(private, sort_keys=True)
        manifest_json = json.dumps(manifest, sort_keys=True)
        self.assertIn("5B3D0406411", private_json)
        self.assertNotIn("5B3D0406411", manifest_json)
        self.assertNotIn(KNOWN_PHYSICAL_FOLLOWER_PORT, manifest_json)
        self.assertNotIn(FOLLOWER_TTY_ALIAS, manifest_json)
        self.assertNotIn("side-camera-001", manifest_json)
        self.assertNotIn('"frame_bytes":', manifest_json)
        self.assertEqual(
            manifest["proof_labels"],
            ["live_read_only_census_observed", "physical_observation_capture"],
        )
        self.assertFalse(manifest["physical_follower_commanded"])
        self.assertEqual(manifest["camera_operation_counts"]["read_successes"], 4)
        self.assertEqual(
            manifest["camera_operation_counts"]["continuous_recording_sessions"], 0
        )

    def test_live_module_and_cli_have_no_write_or_robot_aggregate_surface(self):
        for relative_path in (
            "scenesmith/robot_lab/live_readonly_observation.py",
            "scripts/robot_lab/run_live_readonly_observation.py",
        ):
            source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            tree = ast.parse(source)
            called_attributes = {
                node.func.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            called_names = {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            self.assertTrue(
                {
                    "write",
                    "sync_write",
                    "enable_torque",
                    "disable_torque",
                    "configure",
                    "calibrate",
                    "setup_motor",
                    "scan",
                    "send_action",
                    "set",
                }.isdisjoint(called_attributes)
            )
            self.assertTrue({"SOFollower", "SO101Follower"}.isdisjoint(called_names))
            self.assertNotIn("VideoCapture", source)


if __name__ == "__main__":
    unittest.main()
