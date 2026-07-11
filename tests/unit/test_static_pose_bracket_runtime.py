from __future__ import annotations

import copy
import subprocess
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.leader_arm_bridge import KNOWN_PHYSICAL_FOLLOWER_PORT
from scenesmith.robot_lab.live_readonly_observation import (
    enumerate_serial_identity_holders,
)
from scenesmith.robot_lab.static_pose_bracket import (
    build_fixture_static_pose_observation,
)
from scenesmith.robot_lab.static_pose_bracket_runtime import (
    STATIC_POSE_BRACKET_RUNTIME_RESULT_SCHEMA_VERSION,
    InjectedStaticPoseBusAdapter,
    run_static_pose_bracket_fixture_runtime,
    verify_static_pose_bracket_runtime_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_PATH = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
PROFILE_PATH = REPO_ROOT / "configurations/robot_lab/pi05_calibration_profile.json"
MANIFEST_PATH = (
    REPO_ROOT
    / "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
CONTRACT_PATH = (
    REPO_ROOT / "configurations/robot_lab/pi05_static_pose_bracket_contract.json"
)
FOLLOWER_TTY_ALIAS = KNOWN_PHYSICAL_FOLLOWER_PORT.replace(
    "cu.", "tty.", 1
)


class _Clock:
    def __init__(self, start: int = 1_000_000_000, step: int = 10_000_000):
        self.value = start
        self.step = step

    def __call__(self) -> int:
        value = self.value
        self.value += self.step
        return value


def _holder_snapshot(
    *,
    held_alias: bool = False,
    all_paths_exist: bool = True,
) -> dict:
    def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
        path = command[-1]
        if held_alias and path == FOLLOWER_TTY_ALIAS:
            return subprocess.CompletedProcess(
                command,
                0,
                "p77\nctest-holder\nf4\ntCHR\n",
                "",
            )
        return subprocess.CompletedProcess(command, 1, "", "")

    return enumerate_serial_identity_holders(
        KNOWN_PHYSICAL_FOLLOWER_PORT,
        [FOLLOWER_TTY_ALIAS],
        run_command=runner,
        path_exists=lambda path: all_paths_exist,
    )


class _FakeTransport:
    def __init__(
        self,
        contract: dict,
        events: list[str],
        *,
        fail_connect: bool = False,
        fail_read_index: int | None = None,
        fail_close: bool = False,
        audit_mutation: tuple[str, object] | None = None,
    ):
        fixture = build_fixture_static_pose_observation(contract)
        self.before = {
            item["joint_name"]: item["raw_position"] for item in fixture["q_before"]
        }
        self.after = {
            item["joint_name"]: item["raw_position"] for item in fixture["q_after"]
        }
        self.events = events
        self.fail_connect = fail_connect
        self.fail_read_index = fail_read_index
        self.fail_close = fail_close
        self.audit_mutation = audit_mutation
        self.is_connected = False
        self.connect_calls = 0
        self.read_calls = 0
        self.close_calls = 0

    @property
    def evidence_mode(self) -> str:
        return "deterministic_fixture"

    def connect(self) -> None:
        self.events.append("transport:connect")
        self.connect_calls += 1
        if self.fail_connect:
            raise RuntimeError("transport connect failed")
        self.is_connected = True

    def read_position(self, joint_name: str, servo_id: int) -> int:
        if not self.is_connected:
            raise RuntimeError("transport is disconnected")
        self.events.append(f"transport:read:{joint_name}")
        self.read_calls += 1
        if self.fail_read_index == self.read_calls:
            raise RuntimeError("transport read failed")
        source = self.before if self.read_calls <= 6 else self.after
        return source[joint_name]

    def close(self) -> None:
        self.events.append("transport:close")
        self.close_calls += 1
        self.is_connected = False
        if self.fail_close:
            raise RuntimeError("transport close failed")

    def audit(self) -> dict:
        payload = {
            "hardware_opened": False,
            "connect_calls": self.connect_calls,
            "read_calls": self.read_calls,
            "close_calls": self.close_calls,
            "motor_register_writes": 0,
            "configuration_writes": 0,
            "torque_changes": 0,
            "motion_commands": 0,
            "unexpected_operations": 0,
            "physical_follower_commanded": False,
        }
        if self.audit_mutation is not None:
            payload[self.audit_mutation[0]] = self.audit_mutation[1]
        return payload


class _FakeCamera:
    def __init__(
        self,
        camera: dict,
        events: list[str],
        transport: _FakeTransport,
        *,
        fail_open: bool = False,
        fail_read: bool = False,
        fail_release: bool = False,
        audit_mutation: tuple[str, object] | None = None,
        frame_mutation: tuple[str, object] | None = None,
        drop_transport_on_release: bool = False,
    ):
        self.camera = camera
        self.events = events
        self.transport = transport
        self.fail_open = fail_open
        self.fail_read = fail_read
        self.fail_release = fail_release
        self.audit_mutation = audit_mutation
        self.frame_mutation = frame_mutation
        self.drop_transport_on_release = drop_transport_on_release
        self.open_calls = 0
        self.open_successes = 0
        self.read_calls = 0
        self.read_successes = 0
        self.release_calls = 0
        self.release_successes = 0

    def open(self) -> None:
        self.events.append(f"camera:{self.camera['camera_identity_sha256']}:open")
        self.open_calls += 1
        if not self.transport.is_connected:
            raise AssertionError("camera opened while transport was closed")
        if self.fail_open:
            raise RuntimeError("camera open failed")
        self.open_successes += 1

    def read(self) -> dict:
        self.events.append(f"camera:{self.camera['camera_identity_sha256']}:read")
        self.read_calls += 1
        if not self.transport.is_connected:
            raise AssertionError("camera read while transport was closed")
        if self.fail_read:
            raise RuntimeError("camera read failed")
        self.read_successes += 1
        payload = {
            "frame_bytes": (
                f"fixture-{self.camera['camera_identity_sha256']}-{self.read_calls}"
            ).encode(),
            "encoding": "png",
            "width": self.camera["input_mode"]["width"],
            "height": self.camera["input_mode"]["height"],
            "channels": self.camera["required_channels"],
        }
        if self.frame_mutation is not None:
            payload[self.frame_mutation[0]] = self.frame_mutation[1]
        return payload

    def release(self) -> None:
        self.events.append(f"camera:{self.camera['camera_identity_sha256']}:release")
        self.release_calls += 1
        if self.drop_transport_on_release:
            self.transport.is_connected = False
        if self.fail_release:
            raise RuntimeError("camera release failed")
        self.release_successes += 1

    def audit(self) -> dict:
        payload = {
            "open_attempts": self.open_calls,
            "open_successes": self.open_successes,
            "read_attempts": self.read_calls,
            "read_successes": self.read_successes,
            "release_attempts": self.release_calls,
            "release_successes": self.release_successes,
            "capture_property_writes": 0,
            "continuous_recording_sessions": 0,
            "unexpected_operations": 0,
        }
        if self.audit_mutation is not None:
            payload[self.audit_mutation[0]] = self.audit_mutation[1]
        return payload


class _RawBackend:
    def __init__(self):
        self.calls: list[tuple] = []
        self.is_connected = False

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
        return 2000

    def disconnect(self, *, disable_torque: bool) -> None:
        self.calls.append(("disconnect", disable_torque))
        self.is_connected = False

    def write(self, *args, **kwargs) -> None:
        raise AssertionError("write must never be called")


class StaticPoseBracketRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_strict_json(CONTRACT_PATH)

    def _run(
        self,
        *,
        transport_options: dict | None = None,
        camera_options: dict | None = None,
        pre_holder: dict | None = None,
        post_holder_factory=None,
    ) -> tuple[dict, _FakeTransport, list[_FakeCamera], list[str]]:
        events: list[str] = []
        transport = _FakeTransport(
            self.contract,
            events,
            **(transport_options or {}),
        )
        cameras: list[_FakeCamera] = []

        def camera_factory(camera: dict) -> _FakeCamera:
            instance = _FakeCamera(
                camera,
                events,
                transport,
                **(camera_options or {}),
            )
            cameras.append(instance)
            return instance

        before = pre_holder or _holder_snapshot()
        post_factory = post_holder_factory or (lambda: _holder_snapshot())
        result = run_static_pose_bracket_fixture_runtime(
            self.contract,
            calibration_path=CALIBRATION_PATH,
            calibration_profile_path=PROFILE_PATH,
            manifest_path=MANIFEST_PATH,
            transport_factory=lambda: transport,
            camera_factory=camera_factory,
            pre_open_holder_snapshot=before,
            post_close_holder_snapshot_factory=post_factory,
            monotonic_ns=_Clock(),
        )
        return result, transport, cameras, events

    def test_fixture_runtime_orders_bus_camera_reads_and_no_write_cleanup(self):
        result, transport, cameras, events = self._run()
        verify_static_pose_bracket_runtime_result(
            result,
            contract=self.contract,
            pre_open_holder_snapshot=_holder_snapshot(),
            post_close_holder_snapshot=_holder_snapshot(),
        )
        self.assertEqual(
            result["schema_version"],
            STATIC_POSE_BRACKET_RUNTIME_RESULT_SCHEMA_VERSION,
        )
        self.assertEqual(
            result["local_capabilities"],
            ["fixture_static_pose_bracket_runtime_conformant"],
        )
        self.assertEqual(transport.connect_calls, 1)
        self.assertEqual(transport.read_calls, 12)
        self.assertEqual(transport.close_calls, 1)
        self.assertFalse(transport.is_connected)
        self.assertEqual(len(cameras), 2)
        self.assertTrue(all(camera.read_successes == 2 for camera in cameras))
        first_camera = next(
            index
            for index, event in enumerate(events)
            if event.startswith("camera:")
        )
        before_reads = [
            index for index, event in enumerate(events) if event.startswith("transport:read:")
        ][:6]
        after_reads = [
            index for index, event in enumerate(events) if event.startswith("transport:read:")
        ][6:]
        self.assertLess(max(before_reads), first_camera)
        self.assertGreater(min(after_reads), first_camera)
        self.assertEqual(events[-1], "transport:close")
        self.assertFalse(result["hardware_opened"])
        self.assertFalse(result["physical_follower_commanded"])

    def test_injected_adapter_exposes_only_no_handshake_read_and_no_torque_close(self):
        backend = _RawBackend()
        adapter = InjectedStaticPoseBusAdapter(
            backend=backend,
            servo_names={
                1: "shoulder_pan",
                2: "shoulder_lift",
                3: "elbow_flex",
                4: "wrist_flex",
                5: "wrist_roll",
                6: "gripper",
            },
        )
        adapter.connect()
        self.assertEqual(adapter.read_position("shoulder_pan", 1), 2000)
        adapter.close()
        self.assertEqual(
            backend.calls,
            [
                ("connect", False),
                ("read", "Present_Position", "shoulder_pan", False, 0),
                ("disconnect", False),
            ],
        )
        self.assertFalse(hasattr(adapter, "write"))
        self.assertFalse(hasattr(adapter, "disable_torque"))

    def test_pre_open_holder_blocks_before_transport_construction(self):
        constructed = False

        def transport_factory():
            nonlocal constructed
            constructed = True
            raise AssertionError("must not construct")

        with self.assertRaisesRegex(ValueError, "independent holder"):
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=transport_factory,
                camera_factory=lambda camera: None,
                pre_open_holder_snapshot=_holder_snapshot(held_alias=True),
                post_close_holder_snapshot_factory=lambda: _holder_snapshot(),
                monotonic_ns=_Clock(),
            )
        self.assertFalse(constructed)

    def test_factory_failure_still_runs_post_holder_check(self):
        post_checks = 0

        def failing_factory():
            raise RuntimeError("transport construction failed")

        def post_holder() -> dict:
            nonlocal post_checks
            post_checks += 1
            return _holder_snapshot()

        with self.assertRaisesRegex(RuntimeError, "transport construction failed"):
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=failing_factory,
                camera_factory=lambda camera: None,
                pre_open_holder_snapshot=_holder_snapshot(),
                post_close_holder_snapshot_factory=post_holder,
                monotonic_ns=_Clock(),
            )
        self.assertEqual(post_checks, 1)

    def test_fixture_runtime_refuses_live_adapter_before_backend_connect(self):
        backend = _RawBackend()
        adapter = InjectedStaticPoseBusAdapter(
            backend=backend,
            servo_names={
                1: "shoulder_pan",
                2: "shoulder_lift",
                3: "elbow_flex",
                4: "wrist_flex",
                5: "wrist_roll",
                6: "gripper",
            },
        )
        with self.assertRaisesRegex(ValueError, "refuses a non-fixture transport"):
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=lambda: adapter,
                camera_factory=lambda camera: None,
                pre_open_holder_snapshot=_holder_snapshot(),
                post_close_holder_snapshot_factory=lambda: _holder_snapshot(),
                monotonic_ns=_Clock(),
            )
        self.assertEqual(backend.calls, [])

    def test_connect_and_read_failures_still_close_and_check_post_holder(self):
        for label, options, message in (
            ("connect", {"fail_connect": True}, "transport connect failed"),
            ("before read", {"fail_read_index": 3}, "transport read failed"),
            ("after read", {"fail_read_index": 9}, "transport read failed"),
        ):
            with self.subTest(label=label):
                events: list[str] = []
                transport = _FakeTransport(self.contract, events, **options)
                post_checks = 0

                def post_holder() -> dict:
                    nonlocal post_checks
                    post_checks += 1
                    return _holder_snapshot()

                with self.assertRaisesRegex(RuntimeError, message):
                    run_static_pose_bracket_fixture_runtime(
                        self.contract,
                        calibration_path=CALIBRATION_PATH,
                        calibration_profile_path=PROFILE_PATH,
                        manifest_path=MANIFEST_PATH,
                        transport_factory=lambda: transport,
                        camera_factory=lambda camera: _FakeCamera(
                            camera, events, transport
                        ),
                        pre_open_holder_snapshot=_holder_snapshot(),
                        post_close_holder_snapshot_factory=post_holder,
                        monotonic_ns=_Clock(),
                    )
                self.assertEqual(transport.close_calls, 1)
                self.assertEqual(post_checks, 1)
                self.assertFalse(transport.is_connected)

    def test_camera_open_read_and_release_failures_preserve_transport_cleanup(self):
        for label, options, message in (
            ("open", {"fail_open": True}, "camera open failed"),
            ("read", {"fail_read": True}, "camera read failed"),
            ("release", {"fail_release": True}, "camera release failed"),
        ):
            with self.subTest(label=label):
                events: list[str] = []
                transport = _FakeTransport(self.contract, events)
                cameras: list[_FakeCamera] = []

                def camera_factory(camera: dict) -> _FakeCamera:
                    instance = _FakeCamera(camera, events, transport, **options)
                    cameras.append(instance)
                    return instance

                with self.assertRaisesRegex(BaseException, message):
                    run_static_pose_bracket_fixture_runtime(
                        self.contract,
                        calibration_path=CALIBRATION_PATH,
                        calibration_profile_path=PROFILE_PATH,
                        manifest_path=MANIFEST_PATH,
                        transport_factory=lambda: transport,
                        camera_factory=camera_factory,
                        pre_open_holder_snapshot=_holder_snapshot(),
                        post_close_holder_snapshot_factory=lambda: _holder_snapshot(),
                        monotonic_ns=_Clock(),
                    )
                self.assertEqual(transport.close_calls, 1)
                self.assertFalse(transport.is_connected)
                self.assertEqual(cameras[0].release_calls, 1)

    def test_camera_primary_and_release_failures_are_both_preserved(self):
        events: list[str] = []
        transport = _FakeTransport(self.contract, events)
        with self.assertRaises(BaseExceptionGroup) as captured:
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=lambda: transport,
                camera_factory=lambda camera: _FakeCamera(
                    camera,
                    events,
                    transport,
                    fail_read=True,
                    fail_release=True,
                ),
                pre_open_holder_snapshot=_holder_snapshot(),
                post_close_holder_snapshot_factory=lambda: _holder_snapshot(),
                monotonic_ns=_Clock(),
            )
        self.assertIn("2 sub-exceptions", str(captured.exception))
        self.assertEqual(transport.close_calls, 1)

    def test_camera_semantic_and_audit_drift_reject_after_transport_cleanup(self):
        cases = (
            (
                "dimensions",
                {"frame_mutation": ("height", 479)},
                "frame semantics drifted",
            ),
            (
                "property write",
                {"audit_mutation": ("capture_property_writes", 1)},
                "camera audit drifted",
            ),
            (
                "continuous",
                {"audit_mutation": ("continuous_recording_sessions", 1)},
                "camera audit drifted",
            ),
            (
                "unexpected",
                {"audit_mutation": ("unexpected_operations", 1)},
                "camera audit drifted",
            ),
        )
        for label, options, message in cases:
            with self.subTest(label=label):
                events: list[str] = []
                transport = _FakeTransport(self.contract, events)
                with self.assertRaisesRegex(ValueError, message):
                    run_static_pose_bracket_fixture_runtime(
                        self.contract,
                        calibration_path=CALIBRATION_PATH,
                        calibration_profile_path=PROFILE_PATH,
                        manifest_path=MANIFEST_PATH,
                        transport_factory=lambda: transport,
                        camera_factory=lambda camera: _FakeCamera(
                            camera,
                            events,
                            transport,
                            **options,
                        ),
                        pre_open_holder_snapshot=_holder_snapshot(),
                        post_close_holder_snapshot_factory=lambda: _holder_snapshot(),
                        monotonic_ns=_Clock(),
                    )
                self.assertEqual(transport.close_calls, 1)
                self.assertFalse(transport.is_connected)

    def test_camera_cannot_drop_transport_between_position_phases(self):
        events: list[str] = []
        transport = _FakeTransport(self.contract, events)
        with self.assertRaisesRegex(RuntimeError, "disconnected the transport"):
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=lambda: transport,
                camera_factory=lambda camera: _FakeCamera(
                    camera,
                    events,
                    transport,
                    drop_transport_on_release=True,
                ),
                pre_open_holder_snapshot=_holder_snapshot(),
                post_close_holder_snapshot_factory=lambda: _holder_snapshot(),
                monotonic_ns=_Clock(),
            )
        self.assertEqual(transport.close_calls, 1)
        self.assertFalse(transport.is_connected)

    def test_primary_close_and_post_holder_failures_are_all_preserved(self):
        events: list[str] = []
        transport = _FakeTransport(
            self.contract,
            events,
            fail_read_index=2,
            fail_close=True,
        )
        with self.assertRaises(BaseExceptionGroup) as captured:
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=lambda: transport,
                camera_factory=lambda camera: _FakeCamera(camera, events, transport),
                pre_open_holder_snapshot=_holder_snapshot(),
                post_close_holder_snapshot_factory=lambda: _holder_snapshot(
                    held_alias=True
                ),
                monotonic_ns=_Clock(),
            )
        rendered = str(captured.exception)
        self.assertIn("3 sub-exceptions", rendered)
        self.assertEqual(transport.close_calls, 1)

    def test_transport_audit_write_torque_motion_and_unexpected_drift_reject(self):
        for field in (
            "motor_register_writes",
            "configuration_writes",
            "torque_changes",
            "motion_commands",
            "unexpected_operations",
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "transport audit drifted"):
                    self._run(transport_options={"audit_mutation": (field, 1)})

    def test_post_holder_nonzero_rejects_after_no_write_close(self):
        events: list[str] = []
        transport = _FakeTransport(self.contract, events)
        with self.assertRaisesRegex(ValueError, "independent holder"):
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=lambda: transport,
                camera_factory=lambda camera: _FakeCamera(camera, events, transport),
                pre_open_holder_snapshot=_holder_snapshot(),
                post_close_holder_snapshot_factory=lambda: _holder_snapshot(
                    held_alias=True
                ),
                monotonic_ns=_Clock(),
            )
        self.assertEqual(transport.close_calls, 1)

    def test_static_pose_drift_rejects_only_after_close_and_post_holder(self):
        events: list[str] = []
        transport = _FakeTransport(self.contract, events)
        transport.after["shoulder_pan"] = transport.before["shoulder_pan"] + 10
        post_checks = 0

        def post_holder() -> dict:
            nonlocal post_checks
            post_checks += 1
            return _holder_snapshot()

        with self.assertRaisesRegex(ValueError, "shoulder_pan drift exceeds tolerance"):
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=lambda: transport,
                camera_factory=lambda camera: _FakeCamera(camera, events, transport),
                pre_open_holder_snapshot=_holder_snapshot(),
                post_close_holder_snapshot_factory=post_holder,
                monotonic_ns=_Clock(),
            )
        self.assertEqual(transport.close_calls, 1)
        self.assertEqual(post_checks, 1)
        self.assertFalse(transport.is_connected)

    def test_regressing_global_clock_releases_camera_closes_and_rejects(self):
        events: list[str] = []
        transport = _FakeTransport(self.contract, events)
        values = iter(
            [
                100,
                110,
                120,
                130,
                140,
                135,
            ]
        )
        cameras: list[_FakeCamera] = []

        def camera_factory(camera: dict) -> _FakeCamera:
            instance = _FakeCamera(camera, events, transport)
            cameras.append(instance)
            return instance

        with self.assertRaisesRegex(ValueError, "monotonic clock regressed"):
            run_static_pose_bracket_fixture_runtime(
                self.contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                transport_factory=lambda: transport,
                camera_factory=camera_factory,
                pre_open_holder_snapshot=_holder_snapshot(),
                post_close_holder_snapshot_factory=lambda: _holder_snapshot(),
                monotonic_ns=lambda: next(values),
            )
        self.assertEqual(transport.close_calls, 1)
        self.assertFalse(transport.is_connected)
        self.assertEqual(cameras[0].release_calls, 1)

    def test_runtime_result_resigned_authority_holder_and_lifecycle_drift_reject(self):
        result, _, _, _ = self._run()
        cases = (
            (
                "authority",
                lambda payload: payload.__setitem__("physical_transfer_ready", True),
            ),
            (
                "holder",
                lambda payload: payload["serial_holder_evidence"][
                    "post_close"
                ].__setitem__("deduplicated_holder_count", 1),
            ),
            (
                "lifecycle",
                lambda payload: payload["lifecycle_events"].append("write"),
            ),
            (
                "nested evaluation",
                lambda payload: payload["evaluation"].__setitem__(
                    "static_pose_within_tolerance", False
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                tampered = copy.deepcopy(result)
                mutate(tampered)
                if label == "nested evaluation":
                    tampered["evaluation"] = sign_payload(tampered["evaluation"])
                tampered = sign_payload(tampered)
                with self.assertRaises(ValueError):
                    verify_static_pose_bracket_runtime_result(
                        tampered,
                        contract=self.contract,
                        pre_open_holder_snapshot=_holder_snapshot(),
                        post_close_holder_snapshot=_holder_snapshot(),
                    )


if __name__ == "__main__":
    unittest.main()
