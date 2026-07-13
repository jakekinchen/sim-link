from __future__ import annotations

import copy
import subprocess
import unittest

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.leader_arm_bridge import (
    DEFAULT_LEADER_PORT,
    KNOWN_PHYSICAL_FOLLOWER_PORT,
)
from scenesmith.robot_lab.live_readonly_observation import (
    build_live_discovery_snapshot,
    build_operator_presence_lease,
    enumerate_serial_identity_holders,
    stable_camera_identity_sha256,
)
from scenesmith.robot_lab.static_pose_bracket import (
    build_fixture_static_pose_observation,
)
from scenesmith.robot_lab.static_pose_bracket_runtime import (
    InjectedStaticPoseBusAdapter,
)
import scenesmith.robot_lab.static_pose_live_candidate as candidate_module
from scenesmith.robot_lab.static_pose_live_candidate import (
    HARDWARE_APPROVAL_POLICY,
    HARDWARE_EXECUTION_PROFILE,
    LIVE_GATE_SCOPE,
    build_static_pose_live_candidate_contract,
    build_static_pose_live_candidate_fixture_contract,
    resolve_static_pose_candidate_cameras,
    run_static_pose_live_candidate,
    run_static_pose_live_candidate_fixture,
    verify_static_pose_live_candidate_fixture_contract,
    verify_static_pose_live_candidate_fixture_result,
    verify_static_pose_live_candidate_fixture_result_from_embedded_authority,
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
ISSUED_AT = "2026-07-11T14:00:00-05:00"
VALID_UNTIL = "2026-07-11T14:04:00-05:00"
SESSION_ID = "t16-5c-static-pose-candidate-test"
FOLLOWER_ALIAS = KNOWN_PHYSICAL_FOLLOWER_PORT.replace("/dev/cu.", "/dev/tty.", 1)
LEADER_ALIAS = DEFAULT_LEADER_PORT.replace("/dev/cu.", "/dev/tty.", 1)


class _Clock:
    def __init__(self, start: int = 1_000_000_000, step: int = 10_000_000):
        self.value = start
        self.step = step

    def __call__(self) -> int:
        value = self.value
        self.value += self.step
        return value


class _FakeLiveBackend:
    def __init__(self, static_contract: dict):
        fixture = build_fixture_static_pose_observation(static_contract)
        self.before = {
            item["joint_name"]: item["raw_position"] for item in fixture["q_before"]
        }
        self.after = {
            item["joint_name"]: item["raw_position"] for item in fixture["q_after"]
        }
        self.connected = False
        self.connect_calls = []
        self.read_calls = []
        self.disconnect_calls = []

    def connect(self, *, handshake: bool) -> None:
        self.connect_calls.append(handshake)
        if handshake is not False:
            raise AssertionError("candidate backend handshake must be false")
        self.connected = True

    def read(
        self,
        register: str,
        motor: str,
        *,
        normalize: bool,
        num_retry: int,
    ) -> int:
        self.read_calls.append((register, motor, normalize, num_retry))
        if not self.connected:
            raise RuntimeError("candidate backend is disconnected")
        if register != "Present_Position" or normalize is not False or num_retry != 0:
            raise AssertionError("candidate backend read flags drifted")
        source = self.before if len(self.read_calls) <= 6 else self.after
        return source[motor]

    def disconnect(self, *, disable_torque: bool) -> None:
        self.disconnect_calls.append(disable_torque)
        if disable_torque is not False:
            raise AssertionError("candidate backend cannot change torque")
        self.connected = False


class _FakeLiveCamera:
    def __init__(
        self,
        resolved_camera: dict,
        static_camera: dict,
        transport,
    ):
        self.resolved_camera = resolved_camera
        self.static_camera = static_camera
        self.transport = transport
        self.open_calls = 0
        self.read_calls = 0
        self.release_calls = 0

    @property
    def evidence_mode(self) -> str:
        return "source_bound_candidate_fixture_camera"

    def open(self) -> None:
        if not self.transport.is_connected:
            raise RuntimeError("candidate camera opened without serial connection")
        self.open_calls += 1

    def read(self) -> dict:
        if not self.transport.is_connected:
            raise RuntimeError("candidate camera read without serial connection")
        self.read_calls += 1
        return {
            "frame_bytes": (
                f"candidate-{self.resolved_camera['index']}-{self.read_calls}"
            ).encode(),
            "encoding": "png",
            "width": self.static_camera["input_mode"]["width"],
            "height": self.static_camera["input_mode"]["height"],
            "channels": self.static_camera["required_channels"],
        }

    def release(self) -> None:
        self.release_calls += 1

    def audit(self) -> dict:
        return {
            "open_attempts": self.open_calls,
            "open_successes": self.open_calls,
            "read_attempts": self.read_calls,
            "read_successes": self.read_calls,
            "release_attempts": self.release_calls,
            "release_successes": self.release_calls,
            "capture_property_writes": 0,
            "continuous_recording_sessions": 0,
            "unexpected_operations": 0,
        }


class _FixtureCandidateTransport:
    evidence_mode = "source_bound_candidate_fixture_transport"

    def __init__(self, backend: _FakeLiveBackend, servo_names: dict[int, str]):
        self.backend = backend
        self.servo_names = servo_names
        self.is_connected = False
        self.connect_calls = 0
        self.read_calls = 0
        self.close_calls = 0

    def connect(self) -> None:
        self.connect_calls += 1
        self.backend.connect(handshake=False)
        self.is_connected = True

    def read_position(self, joint_name: str, servo_id: int) -> int:
        if not self.is_connected or self.servo_names.get(servo_id) != joint_name:
            raise RuntimeError("candidate fixture transport identity drifted")
        self.read_calls += 1
        return self.backend.read(
            "Present_Position",
            joint_name,
            normalize=False,
            num_retry=0,
        )

    def close(self) -> None:
        self.close_calls += 1
        try:
            self.backend.disconnect(disable_torque=False)
        finally:
            self.is_connected = False

    def audit(self) -> dict:
        return {
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


class StaticPoseLiveCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_state = copy.deepcopy(
            load_strict_json(
                REPO_ROOT / "docs/autonomous-workflow/project_state.json"
            )
        )
        self.project_state["run_window"]["hard_closeout"] = (
            "2026-07-11T14:10:00-05:00"
        )
        gate = self.project_state["tasks"]["T16.5b"]
        gate.update(
            {
                "live_gate": "open",
                "live_gate_opened_at": ISSUED_AT,
                "live_gate_valid_until": "2026-07-11T14:05:00-05:00",
                "live_gate_session_limit": 1,
                "live_gate_sessions_started": 0,
                "live_gate_scope": LIVE_GATE_SCOPE,
                "live_gate_execution_profile": HARDWARE_EXECUTION_PROFILE,
                "live_gate_approval_policy": HARDWARE_APPROVAL_POLICY,
                "live_gate_review_decision_id": "fixture-review-078",
            }
        )
        self.static_contract = load_strict_json(CONTRACT_PATH)
        self.manifest = load_strict_json(MANIFEST_PATH)
        self.discovery = self._discovery()
        self.lease = build_operator_presence_lease(
            project_state=self.project_state,
            session_id=SESSION_ID,
            issued_at=ISSUED_AT,
            valid_until=VALID_UNTIL,
        )

    def _discovery(self, *, indexes: tuple[int, int] = (0, 1)) -> dict:
        cameras = [
            {
                "name": "Fixture Side Camera",
                "unique_id": "fixture-side-001",
                "model_id": "Fixture Model Side",
                "supported_modes": [
                    {
                        "pixel_format": "uyvy422",
                        "width": 640,
                        "height": 480,
                        "min_framerate_fps": 30.0,
                        "max_framerate_fps": 30.0,
                    }
                ],
            },
            {
                "name": "Fixture Overhead Camera",
                "unique_id": "fixture-overhead-001",
                "model_id": "Fixture Model Overhead",
                "supported_modes": [
                    {
                        "pixel_format": "yuyv422",
                        "width": 640,
                        "height": 480,
                        "min_framerate_fps": 30.0,
                        "max_framerate_fps": 30.0,
                    }
                ],
            },
        ]
        return build_live_discovery_snapshot(
            session_id=SESSION_ID,
            captured_at=ISSUED_AT,
            serial_candidates=[
                {
                    "device": KNOWN_PHYSICAL_FOLLOWER_PORT,
                    "aliases": [FOLLOWER_ALIAS],
                    "vid": 0x0483,
                    "pid": 0x5740,
                    "serial_number": "fixture-follower",
                    "manufacturer": "Fixture",
                    "product": "Fixture Follower",
                    "location": "fixture-1",
                    "hwid": "fixture-follower-hwid",
                },
                {
                    "device": DEFAULT_LEADER_PORT,
                    "aliases": [LEADER_ALIAS],
                    "vid": 0x0483,
                    "pid": 0x5740,
                    "serial_number": "fixture-leader",
                    "manufacturer": "Fixture",
                    "product": "Fixture Leader",
                    "location": "fixture-2",
                    "hwid": "fixture-leader-hwid",
                },
            ],
            avfoundation_devices=[
                {"index": indexes[0], "name": cameras[0]["name"]},
                {"index": indexes[1], "name": cameras[1]["name"]},
            ],
            system_cameras=cameras,
        )

    @contextmanager
    def _accepted_identity_patches(self):
        expected_camera_hashes = [
            camera["stable_camera_identity_sha256"]
            for camera in self.static_contract["cameras"]
        ]
        camera_hash_by_name = {
            "Fixture Side Camera": expected_camera_hashes[0],
            "Fixture Overhead Camera": expected_camera_hashes[1],
        }
        original_payload_hash = candidate_module._sha256_payload

        def stable_hash(camera: dict) -> str:
            return camera_hash_by_name.get(
                camera.get("name"),
                stable_camera_identity_sha256(camera),
            )

        def payload_hash(payload) -> str:
            if isinstance(payload, dict) and set(payload) == {
                "vendor_id_hex",
                "product_id_hex",
                "serial_number",
                "canonical_path",
                "observed_aliases",
            }:
                return self.manifest["usb_identity_sha256"]
            return original_payload_hash(payload)

        def verify_profile(payload: dict, **kwargs) -> None:
            if payload != self._hardware_profile():
                raise ValueError("fixture hardware profile drifted")

        with patch.object(
            candidate_module,
            "stable_camera_identity_sha256",
            side_effect=stable_hash,
        ), patch.object(
            candidate_module,
            "_sha256_payload",
            side_effect=payload_hash,
        ), patch.object(
            candidate_module,
            "verify_hardware_execution_profile_evidence",
            side_effect=verify_profile,
        ):
            yield

    def _contract(self, *, live: bool = False) -> dict:
        builder = (
            build_static_pose_live_candidate_contract
            if live
            else build_static_pose_live_candidate_fixture_contract
        )
        return builder(
            project_state=self.project_state,
            presence_lease=self.lease,
            discovery=self.discovery,
            static_pose_contract=self.static_contract,
            calibration_path=CALIBRATION_PATH,
            calibration_profile_path=PROFILE_PATH,
            manifest_path=MANIFEST_PATH,
            issued_at=ISSUED_AT,
            expires_at=VALID_UNTIL,
        )

    def _holder_snapshot(self) -> dict:
        def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            return subprocess.CompletedProcess(command, 1, "", "")

        return enumerate_serial_identity_holders(
            KNOWN_PHYSICAL_FOLLOWER_PORT,
            [FOLLOWER_ALIAS],
            run_command=runner,
            path_exists=lambda path: True,
        )

    def _hardware_profile(self) -> dict:
        return {"fixture_profile": SESSION_ID, "identity_sha256": "f" * 64}

    def _run(self) -> tuple[dict, dict]:
        contract = self._contract()
        runtime: dict = {}

        def transport_factory(candidate_contract: dict):
            backend = _FakeLiveBackend(self.static_contract)
            transport = _FixtureCandidateTransport(
                backend,
                servo_names={
                    joint["servo_id"]: joint["joint_name"]
                    for joint in self.static_contract["joints"]
                },
            )
            runtime.update({"backend": backend, "transport": transport})
            return transport

        def camera_factory(resolved: dict, static: dict):
            camera = _FakeLiveCamera(resolved, static, runtime["transport"])
            runtime.setdefault("cameras", []).append(camera)
            return camera

        result = run_static_pose_live_candidate_fixture(
            contract,
            project_state=self.project_state,
            static_pose_contract=self.static_contract,
            calibration_path=CALIBRATION_PATH,
            calibration_profile_path=PROFILE_PATH,
            manifest_path=MANIFEST_PATH,
            now="2026-07-11T14:01:00-05:00",
            transport_factory=transport_factory,
            camera_factory=camera_factory,
            pre_open_holder_snapshot=self._holder_snapshot(),
            post_close_holder_snapshot_factory=self._holder_snapshot,
            monotonic_ns=_Clock(),
        )
        runtime["contract"] = contract
        return result, runtime

    def test_builds_and_runs_candidate_only_no_write_lifecycle(self):
        with self._accepted_identity_patches():
            result, runtime = self._run()
            verify_static_pose_live_candidate_fixture_result(
                result,
                candidate_contract=runtime["contract"],
                project_state=self.project_state,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                now="2026-07-11T14:01:00-05:00",
            )
            verify_static_pose_live_candidate_fixture_result_from_embedded_authority(
                result,
                candidate_contract=runtime["contract"],
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
            )
        self.assertTrue(result["candidate_only"])
        self.assertEqual(
            runtime["contract"]["execution_class"],
            "deterministic_candidate_fixture",
        )
        self.assertFalse(runtime["contract"]["hardware_access_authorized"])
        self.assertEqual(result["execution_class"], "deterministic_candidate_fixture")
        self.assertEqual(
            result["evidence_mode"],
            "deterministic_source_bound_live_candidate_fixture",
        )
        self.assertEqual(result["proof_labels"], [])
        self.assertEqual(
            result["local_capabilities"],
            ["source_bound_static_pose_live_candidate_runtime_conformant"],
        )
        self.assertFalse(result["hardware_opened"])
        self.assertFalse(result["capture"]["hardware_opened"])
        self.assertFalse(result["physical_follower_commanded"])
        self.assertFalse(result["tracked_redacted_manifest_written"])
        self.assertEqual(runtime["backend"].connect_calls, [False])
        self.assertEqual(len(runtime["backend"].read_calls), 12)
        self.assertTrue(
            all(
                register == "Present_Position"
                and normalize is False
                and retries == 0
                for register, _, normalize, retries in runtime["backend"].read_calls
            )
        )
        self.assertEqual(runtime["backend"].disconnect_calls, [False])
        self.assertTrue(result["measurements"]["static_pose_within_tolerance"])

    def test_contract_ignores_unselected_avfoundation_only_source(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["avfoundation_devices"].append(
            {"index": 2, "name": "Capture screen 0"}
        )
        self.discovery = sign_payload(discovery)
        with self._accepted_identity_patches():
            contract = self._contract()
        self.assertEqual(
            [camera["resolved_camera"]["index"] for camera in contract["cameras"]],
            [0, 1],
        )

    def test_fresh_numeric_index_churn_resolves_stable_camera_order(self):
        self.discovery = self._discovery(indexes=(9, 3))
        with self._accepted_identity_patches():
            contract = self._contract(live=True)
        self.assertEqual(contract["execution_class"], "live_candidate")
        self.assertTrue(contract["hardware_access_authorized"])
        self.assertEqual(
            [camera["resolved_camera"]["index"] for camera in contract["cameras"]],
            [9, 3],
        )
        self.assertEqual(
            [
                camera["stable_camera_identity_sha256"]
                for camera in contract["cameras"]
            ],
            [
                camera["stable_camera_identity_sha256"]
                for camera in self.static_contract["cameras"]
            ],
        )
        post_closeout_state = copy.deepcopy(self.project_state)
        post_closeout_state["tasks"]["T16.5c"]["latest_verified_brief_id"] = "052"
        post_closeout_state["tasks"]["T16.5c"]["completed_brief_ids"].append("052")
        post_closeout_lease = build_operator_presence_lease(
            project_state=post_closeout_state,
            session_id=SESSION_ID,
            issued_at=ISSUED_AT,
            valid_until=VALID_UNTIL,
        )
        with self._accepted_identity_patches():
            build_static_pose_live_candidate_contract(
                project_state=post_closeout_state,
                presence_lease=post_closeout_lease,
                discovery=self.discovery,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                issued_at=ISSUED_AT,
                expires_at=VALID_UNTIL,
            )

    def test_closed_consumed_expired_or_wrong_scope_gate_rejects(self):
        cases = (
            ("closed", lambda gate: gate.update({"live_gate": "closed"})),
            (
                "consumed",
                lambda gate: gate.update({"live_gate_sessions_started": 1}),
            ),
            (
                "limit",
                lambda gate: gate.update({"live_gate_session_limit": 2}),
            ),
            (
                "scope",
                lambda gate: gate.update({"live_gate_scope": "different"}),
            ),
            (
                "execution profile",
                lambda gate: gate.update(
                    {"live_gate_execution_profile": "offline_autonomous"}
                ),
            ),
            (
                "expiry",
                lambda gate: gate.update(
                    {"live_gate_valid_until": "2026-07-11T14:03:00-05:00"}
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                state = copy.deepcopy(self.project_state)
                mutate(state["tasks"]["T16.5b"])
                with self._accepted_identity_patches(), self.assertRaises(ValueError):
                    build_static_pose_live_candidate_contract(
                        project_state=state,
                        presence_lease=self.lease,
                        discovery=self.discovery,
                        static_pose_contract=self.static_contract,
                        calibration_path=CALIBRATION_PATH,
                        calibration_profile_path=PROFILE_PATH,
                        manifest_path=MANIFEST_PATH,
                        issued_at=ISSUED_AT,
                        expires_at=VALID_UNTIL,
                    )

    def test_gate_revalidation_precedes_transport_construction(self):
        with self._accepted_identity_patches():
            contract = self._contract(live=True)
        state = copy.deepcopy(self.project_state)
        state["tasks"]["T16.5b"]["live_gate"] = "closed"
        constructed = []
        with self._accepted_identity_patches(), self.assertRaisesRegex(
            ValueError, "project state|live gate"
        ):
            run_static_pose_live_candidate(
                contract,
                hardware_execution_profile=self._hardware_profile(),
                project_state=state,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                now="2026-07-11T14:01:00-05:00",
                transport_factory=lambda contract: constructed.append(True),
                camera_factory=lambda resolved, static: None,
                pre_open_holder_snapshot=self._holder_snapshot(),
                post_close_holder_snapshot_factory=self._holder_snapshot,
                monotonic_ns=_Clock(),
            )
        self.assertEqual(constructed, [])

    def test_hardware_profile_revalidation_precedes_transport_construction(self):
        with self._accepted_identity_patches():
            contract = self._contract(live=True)
        constructed = []
        with self._accepted_identity_patches(), patch.object(
            candidate_module,
            "verify_hardware_execution_profile_evidence",
            side_effect=ValueError("hardware profile is not no-prompt"),
        ), self.assertRaisesRegex(ValueError, "profile.*no-prompt"):
            run_static_pose_live_candidate(
                contract,
                hardware_execution_profile=self._hardware_profile(),
                project_state=self.project_state,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                now="2026-07-11T14:01:00-05:00",
                transport_factory=lambda contract: constructed.append(True),
                camera_factory=lambda resolved, static: None,
                pre_open_holder_snapshot=self._holder_snapshot(),
                post_close_holder_snapshot_factory=self._holder_snapshot,
                monotonic_ns=_Clock(),
            )
        self.assertEqual(constructed, [])

    def test_expired_lease_and_holder_path_drift_precede_construction(self):
        with self._accepted_identity_patches():
            contract = self._contract(live=True)
        constructed = []
        with self._accepted_identity_patches(), self.assertRaisesRegex(
            ValueError, "expired"
        ):
            run_static_pose_live_candidate(
                contract,
                hardware_execution_profile=self._hardware_profile(),
                project_state=self.project_state,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                now="2026-07-11T14:04:01-05:00",
                transport_factory=lambda contract: constructed.append(True),
                camera_factory=lambda resolved, static: None,
                pre_open_holder_snapshot=self._holder_snapshot(),
                post_close_holder_snapshot_factory=self._holder_snapshot,
                monotonic_ns=_Clock(),
            )
        self.assertEqual(constructed, [])

        wrong_paths = copy.deepcopy(self._holder_snapshot())
        wrong_paths["paths_checked"].reverse()
        with self._accepted_identity_patches(), self.assertRaisesRegex(
            ValueError, "holder path"
        ):
            run_static_pose_live_candidate(
                contract,
                hardware_execution_profile=self._hardware_profile(),
                project_state=self.project_state,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                now="2026-07-11T14:01:00-05:00",
                transport_factory=lambda contract: constructed.append(True),
                camera_factory=lambda resolved, static: None,
                pre_open_holder_snapshot=wrong_paths,
                post_close_holder_snapshot_factory=self._holder_snapshot,
                monotonic_ns=_Clock(),
            )
        self.assertEqual(constructed, [])

    def test_follower_usb_and_stable_camera_substitution_reject(self):
        with self.assertRaisesRegex(ValueError, "follower USB identity"):
            with patch.object(
                candidate_module,
                "stable_camera_identity_sha256",
                side_effect=lambda camera: self.static_contract["cameras"][
                    0 if camera["name"] == "Fixture Side Camera" else 1
                ]["stable_camera_identity_sha256"],
            ):
                self._contract()

        changed = copy.deepcopy(self.discovery)
        changed["system_cameras"][1]["name"] = "Different Camera"
        changed["avfoundation_devices"][1]["name"] = "Different Camera"
        changed = sign_payload(changed)
        with self._accepted_identity_patches(), self.assertRaisesRegex(
            ValueError, "exactly one stable target"
        ):
            resolve_static_pose_candidate_cameras(
                discovery=changed,
                static_pose_contract=self.static_contract,
            )

        changed_mode = copy.deepcopy(self.discovery)
        changed_mode["system_cameras"][1]["supported_modes"][0].update(
            {"width": 1280, "height": 720}
        )
        changed_mode = sign_payload(changed_mode)
        with self._accepted_identity_patches(), self.assertRaisesRegex(
            ValueError, "input mode drifted"
        ):
            resolve_static_pose_candidate_cameras(
                discovery=changed_mode,
                static_pose_contract=self.static_contract,
            )

    def test_runner_refuses_unmarked_transport_and_camera_backends(self):
        with self._accepted_identity_patches():
            contract = self._contract(live=True)

        class WrongTransport:
            evidence_mode = "deterministic_fixture"
            is_connected = False
            connect_calls = 0

            def connect(self):
                self.connect_calls += 1

            def close(self):
                pass

            def audit(self):
                raise AssertionError("wrong transport audit must not be used")

        wrong_transport = WrongTransport()
        with self._accepted_identity_patches(), self.assertRaisesRegex(
            ValueError, "transport evidence mode"
        ):
            run_static_pose_live_candidate(
                contract,
                hardware_execution_profile=self._hardware_profile(),
                project_state=self.project_state,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                now="2026-07-11T14:01:00-05:00",
                transport_factory=lambda contract: wrong_transport,
                camera_factory=lambda resolved, static: None,
                pre_open_holder_snapshot=self._holder_snapshot(),
                post_close_holder_snapshot_factory=self._holder_snapshot,
                monotonic_ns=_Clock(),
            )
        self.assertEqual(wrong_transport.connect_calls, 0)

        runtime = {}

        def transport_factory(candidate_contract: dict):
            backend = _FakeLiveBackend(self.static_contract)
            transport = InjectedStaticPoseBusAdapter(
                backend=backend,
                servo_names={
                    joint["servo_id"]: joint["joint_name"]
                    for joint in self.static_contract["joints"]
                },
            )
            runtime.update({"backend": backend, "transport": transport})
            return transport

        class WrongCamera(_FakeLiveCamera):
            @property
            def evidence_mode(self) -> str:
                return "deterministic_fixture"

        with self._accepted_identity_patches(), self.assertRaisesRegex(
            ValueError, "camera evidence mode"
        ):
            run_static_pose_live_candidate(
                contract,
                hardware_execution_profile=self._hardware_profile(),
                project_state=self.project_state,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
                now="2026-07-11T14:01:00-05:00",
                transport_factory=transport_factory,
                camera_factory=lambda resolved, static: WrongCamera(
                    resolved, static, runtime["transport"]
                ),
                pre_open_holder_snapshot=self._holder_snapshot(),
                post_close_holder_snapshot_factory=self._holder_snapshot,
                monotonic_ns=_Clock(),
            )
        self.assertFalse(runtime["backend"].connected)
        self.assertEqual(runtime["backend"].disconnect_calls, [False])

    def test_noncanonical_source_path_rejects_before_candidate_creation(self):
        with self._accepted_identity_patches(), self.assertRaisesRegex(
            ValueError, "path is not canonical"
        ):
            build_static_pose_live_candidate_contract(
                project_state=self.project_state,
                presence_lease=self.lease,
                discovery=self.discovery,
                static_pose_contract=self.static_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=MANIFEST_PATH,
                manifest_path=PROFILE_PATH,
                issued_at=ISSUED_AT,
                expires_at=VALID_UNTIL,
            )

    def test_resigned_contract_and_result_authority_or_capture_drift_reject(self):
        with self._accepted_identity_patches():
            result, runtime = self._run()
            contract = runtime["contract"]
            changed_contract = copy.deepcopy(contract)
            changed_contract["proof_labels"] = ["static_pose_bracketed_observation"]
            with self.assertRaisesRegex(ValueError, "source or semantics drifted"):
                verify_static_pose_live_candidate_fixture_contract(
                    sign_payload(changed_contract),
                    project_state=self.project_state,
                    static_pose_contract=self.static_contract,
                    calibration_path=CALIBRATION_PATH,
                    calibration_profile_path=PROFILE_PATH,
                    manifest_path=MANIFEST_PATH,
                    now="2026-07-11T14:01:00-05:00",
                )
            with self.assertRaisesRegex(ValueError, "execution class drifted"):
                candidate_module.verify_static_pose_live_candidate_contract(
                    contract,
                    project_state=self.project_state,
                    static_pose_contract=self.static_contract,
                    calibration_path=CALIBRATION_PATH,
                    calibration_profile_path=PROFILE_PATH,
                    manifest_path=MANIFEST_PATH,
                    now="2026-07-11T14:01:00-05:00",
                )

            cases = (
                (
                    "execution class",
                    lambda payload: payload.__setitem__(
                        "execution_class", "live_candidate"
                    ),
                    "execution class drifted",
                ),
                (
                    "proof",
                    lambda payload: payload.__setitem__(
                        "proof_labels", ["static_pose_bracketed_observation"]
                    ),
                    "authority fields",
                ),
                (
                    "measurement",
                    lambda payload: payload["measurements"].__setitem__(
                        "maximum_body_drift_degrees", 0
                    ),
                    "measurements drifted",
                ),
                (
                    "write",
                    lambda payload: payload["capture"]["transport_audit"].__setitem__(
                        "motor_register_writes", 1
                    ),
                    "transport audit drifted",
                ),
                (
                    "duration",
                    lambda payload: payload["capture"].__setitem__(
                        "runtime_duration_ns",
                        payload["capture"]["runtime_duration_ns"] + 1,
                    ),
                    "duration is invalid",
                ),
                (
                    "holder",
                    lambda payload: payload["capture"][
                        "post_close_holder_snapshot"
                    ]["paths_checked"].reverse(),
                    "identity|path|snapshot",
                ),
            )
            for label, mutate, message in cases:
                with self.subTest(label=label):
                    changed = copy.deepcopy(result)
                    mutate(changed)
                    with self.assertRaisesRegex(ValueError, message):
                        verify_static_pose_live_candidate_fixture_result(
                            sign_payload(changed),
                            candidate_contract=contract,
                            project_state=self.project_state,
                            static_pose_contract=self.static_contract,
                            calibration_path=CALIBRATION_PATH,
                            calibration_profile_path=PROFILE_PATH,
                            manifest_path=MANIFEST_PATH,
                            now="2026-07-11T14:01:00-05:00",
                        )

    def test_candidate_module_has_no_discovery_or_hardware_constructor_call(self):
        source = (
            REPO_ROOT
            / "scenesmith/robot_lab/static_pose_live_candidate.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "capture_live_discovery(",
            "enumerate_serial_candidates(",
            "enumerate_camera_metadata(",
            "construct_pinned_feetech_bus(",
            "subprocess.Popen(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
