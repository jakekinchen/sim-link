from __future__ import annotations

import copy
import ast
import subprocess
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.authority_composer import (
    compose_t19_1_readonly_session_authority,
    verify_t19_1_readonly_session_authority,
)
from scenesmith.robot_lab.leader_arm_bridge import KNOWN_PHYSICAL_FOLLOWER_PORT
from scenesmith.robot_lab.live_readonly_observation import (
    enumerate_serial_identity_holders,
)
from scenesmith.robot_lab.t19_1_readonly_hardware_snapshot import (
    build_t19_1_private_snapshot,
    build_t19_1_redacted_manifest,
    capture_t19_1_serial_discovery,
    execute_t19_1_readonly_servo_census,
    verify_t19_1_private_snapshot,
    verify_t19_1_redacted_manifest,
    write_t19_1_private_snapshot,
)


NOW = "2026-07-16T07:10:00-05:00"
EXPIRES = "2026-07-16T07:15:00-05:00"
BRANCH = "codex/pi05-autolearn-loop"
HEAD = "a" * 40


def _state() -> dict:
    return {
        "schema_version": "scenesmith.project_state.v1",
        "branch": BRANCH,
        "run_window": {
            "hard_closeout": "2026-07-16T09:44:12-05:00",
            "hardware_authority": (
                "owner_presence_and_access_granted_pending_central_and_session_permits"
            ),
        },
        "owner_authority": {
            "current_hardware_access_window": {
                "state": (
                    "owner_presence_and_access_granted_pending_central_and_session_permits"
                ),
                "recorded_at_approximate": "2026-07-16T02:05:00-05:00",
                "valid_through_approximate": "2026-07-16T10:05:00-05:00",
                "owner_present": True,
                "hardware_access_authorized": True,
                "physical_access_performed_in_window": False,
            }
        },
        "tasks": {
            "T16.5a": {"state": "verified"},
            "T16.5b": {"state": "verified"},
            "T19.1": {
                "state": "in_progress",
                "active_brief_id": "212",
                "live_gate": "open",
                "session_limit": 1,
                "sessions_started": 0,
            },
        },
    }


def _runtime_profile() -> dict:
    return sign_payload(
        {
            "schema_version": "test.hardware_profile.v1",
            "thread_id": "thread-1",
            "approval_policy": "never",
            "sandbox_mode": "danger-full-access",
        }
    )


def _repository_state() -> dict:
    return {
        "branch": BRANCH,
        "head": HEAD,
        "upstream_head": HEAD,
        "remote_head": HEAD,
        "scoped_source_diff_clean": True,
        "gate_state_diff_clean": True,
    }


def _profile_verifier(payload: dict, **_: object) -> None:
    if payload != _runtime_profile():
        raise ValueError("test runtime profile drifted")


def _serial_candidates() -> list[dict]:
    alias = KNOWN_PHYSICAL_FOLLOWER_PORT.replace("/dev/cu.", "/dev/tty.", 1)
    return [
        {
            "device": KNOWN_PHYSICAL_FOLLOWER_PORT,
            "aliases": [alias],
            "vid": 0x0483,
            "pid": 0x5740,
            "serial_number": "private-test-serial",
            "manufacturer": "STMicroelectronics",
            "product": "STM32 Virtual ComPort",
            "location": "1-2",
            "hwid": "USB VID:PID=0483:5740 SER=private-test-serial",
        }
    ]


class _TickingClock:
    def __init__(self) -> None:
        self.value = 1_000_000_000

    def __call__(self) -> int:
        result = self.value
        self.value += 1_000_000
        return result


class _FakeBus:
    def connect(self, *, handshake: bool) -> None:
        if handshake is not False:
            raise AssertionError("handshake must remain false")

    def read(
        self,
        register: str,
        motor: str,
        *,
        normalize: bool,
        num_retry: int,
    ) -> int:
        if normalize is not False or num_retry != 0:
            raise AssertionError("read flags drifted")
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
        if disable_torque is not False:
            raise AssertionError("disconnect must not change torque")

    def write(self, *args, **kwargs) -> None:
        raise AssertionError("write must never be called")


def _zero_holder_snapshot() -> dict:
    alias = KNOWN_PHYSICAL_FOLLOWER_PORT.replace("/dev/cu.", "/dev/tty.", 1)
    return enumerate_serial_identity_holders(
        KNOWN_PHYSICAL_FOLLOWER_PORT,
        [alias],
        run_command=lambda command, **kwargs: subprocess.CompletedProcess(
            command, 1, "", ""
        ),
        path_exists=lambda _: True,
    )


class T191ReadonlySessionAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "outputs/robot_lab/t19_1/private").mkdir(parents=True)
        (self.root / "configurations/robot_lab").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def compose(self, *, state: dict | None = None, repo: dict | None = None):
        return compose_t19_1_readonly_session_authority(
            project_state=state or _state(),
            runtime_profile=_runtime_profile(),
            repo_root=self.root,
            session_id="t19-1-20260716-0710-cdt",
            issued_at=NOW,
            expires_at=EXPIRES,
            private_output_dir=(
                "outputs/robot_lab/t19_1/private/t19-1-20260716-0710-cdt"
            ),
            manifest_output=(
                "configurations/robot_lab/"
                "t19_1_readonly_hardware_snapshot_20260716_0710.json"
            ),
            repository_state_loader=lambda **_: repo or _repository_state(),
            runtime_profile_verifier=_profile_verifier,
        )

    def test_grants_only_exact_remote_owner_present_readonly_session(self) -> None:
        request, decision, permit = self.compose()
        self.assertTrue(decision["granted"])
        self.assertEqual(decision["denial_reasons"], [])
        self.assertIsNotNone(permit)
        self.assertEqual(permit["maximum_register_read_count"], 54)
        self.assertEqual(len(permit["read_plan"]), 9)
        self.assertEqual(permit["register_write_count"], 0)
        self.assertEqual(permit["torque_change_count"], 0)
        self.assertEqual(permit["motion_command_count"], 0)
        verify_t19_1_readonly_session_authority(
            request=request,
            decision=decision,
            permit=permit,
            project_state=_state(),
            runtime_profile=_runtime_profile(),
            repo_root=self.root,
            now=NOW,
            repository_state_loader=lambda **_: _repository_state(),
            runtime_profile_verifier=_profile_verifier,
        )

    def test_closed_gate_denies_without_permit(self) -> None:
        state = _state()
        state["tasks"]["T19.1"]["live_gate"] = "closed"
        _, decision, permit = self.compose(state=state)
        self.assertFalse(decision["granted"])
        self.assertIn("T19_1_LIVE_GATE_NOT_OPEN", decision["denial_reasons"])
        self.assertIsNone(permit)

    def test_remote_mismatch_denies_without_permit(self) -> None:
        repo = _repository_state()
        repo["remote_head"] = "b" * 40
        _, decision, permit = self.compose(repo=repo)
        self.assertFalse(decision["granted"])
        self.assertIn("REMOTE_BOUNDARY_NOT_CONFIRMED", decision["denial_reasons"])
        self.assertIsNone(permit)

    def test_expired_owner_window_denies(self) -> None:
        state = _state()
        state["owner_authority"]["current_hardware_access_window"][
            "valid_through_approximate"
        ] = "2026-07-16T06:00:00-05:00"
        _, decision, permit = self.compose(state=state)
        self.assertFalse(decision["granted"])
        self.assertIn("OWNER_WINDOW_INACTIVE", decision["denial_reasons"])
        self.assertIsNone(permit)

    def test_forged_decision_is_rejected(self) -> None:
        request, decision, permit = self.compose()
        forged = copy.deepcopy(decision)
        forged["remote_boundary_commit"] = "b" * 40
        forged = sign_payload({k: v for k, v in forged.items() if k != "identity_sha256"})
        with self.assertRaisesRegex(ValueError, "decision|boundary"):
            verify_t19_1_readonly_session_authority(
                request=request,
                decision=forged,
                permit=permit,
                project_state=_state(),
                runtime_profile=_runtime_profile(),
                repo_root=self.root,
                now=NOW,
                repository_state_loader=lambda **_: _repository_state(),
                runtime_profile_verifier=_profile_verifier,
            )

    def test_private_output_path_escape_rejects_before_grant(self) -> None:
        with self.assertRaisesRegex(ValueError, "private output"):
            compose_t19_1_readonly_session_authority(
                project_state=_state(),
                runtime_profile=_runtime_profile(),
                repo_root=self.root,
                session_id="t19-1-20260716-0710-cdt",
                issued_at=NOW,
                expires_at=EXPIRES,
                private_output_dir="../escaped",
                manifest_output=(
                    "configurations/robot_lab/"
                    "t19_1_readonly_hardware_snapshot_20260716_0710.json"
                ),
                repository_state_loader=lambda **_: _repository_state(),
                runtime_profile_verifier=_profile_verifier,
            )

    def test_exact_fake_live_census_writes_private_and_redacted_evidence(self) -> None:
        request, decision, permit = self.compose()
        discovery = capture_t19_1_serial_discovery(
            session_id=permit["session_id"],
            captured_at=NOW,
            serial_enumerator=_serial_candidates,
        )
        contract, result = execute_t19_1_readonly_servo_census(
            permit=permit,
            discovery=discovery,
            calibration_file_sha256="c" * 64,
            bus_factory=lambda _: _FakeBus(),
            monotonic_ns=_TickingClock(),
        )
        private = build_t19_1_private_snapshot(
            runtime_profile_identity_sha256=_runtime_profile()["identity_sha256"],
            request=request,
            decision=decision,
            permit=permit,
            discovery=discovery,
            census_contract=contract,
            servo_result=result,
            pre_open_holders=_zero_holder_snapshot(),
            post_close_holders=_zero_holder_snapshot(),
            completed_at="2026-07-16T07:11:00-05:00",
        )
        verify_t19_1_private_snapshot(private)
        output = self.root / permit["private_output_dir"]
        reference = write_t19_1_private_snapshot(
            output_directory=output,
            private_snapshot=private,
        )
        manifest = build_t19_1_redacted_manifest(
            private_snapshot=private,
            private_reference=reference,
        )
        verify_t19_1_redacted_manifest(
            manifest,
            private_snapshot=private,
            private_reference=reference,
        )
        self.assertNotIn(
            "private-test-serial",
            str(manifest),
        )
        self.assertEqual(manifest["operation_counts"]["read_successes"], 54)
        self.assertEqual(manifest["register_write_count"], 0)

    def test_transient_read_is_terminal_and_never_retried(self) -> None:
        _, _, permit = self.compose()
        discovery = capture_t19_1_serial_discovery(
            session_id=permit["session_id"],
            captured_at=NOW,
            serial_enumerator=_serial_candidates,
        )

        class FailingBus(_FakeBus):
            calls = 0

            def read(self, *args, **kwargs):
                self.calls += 1
                raise ConnectionError("one terminal physical read failure")

        bus = FailingBus()
        with self.assertRaisesRegex(RuntimeError, "retry prohibited"):
            execute_t19_1_readonly_servo_census(
                permit=permit,
                discovery=discovery,
                calibration_file_sha256="c" * 64,
                bus_factory=lambda _: bus,
                monotonic_ns=_TickingClock(),
            )
        self.assertEqual(bus.calls, 1)

    def test_resigned_permit_read_count_drift_rejects(self) -> None:
        _, _, permit = self.compose()
        discovery = capture_t19_1_serial_discovery(
            session_id=permit["session_id"],
            captured_at=NOW,
            serial_enumerator=_serial_candidates,
        )
        drifted = copy.deepcopy(permit)
        drifted["maximum_register_read_count"] = 55
        drifted = sign_payload(
            {key: value for key, value in drifted.items() if key != "identity_sha256"}
        )
        with self.assertRaisesRegex(ValueError, "permit safety"):
            execute_t19_1_readonly_servo_census(
                permit=drifted,
                discovery=discovery,
                calibration_file_sha256="c" * 64,
                bus_factory=lambda _: _FakeBus(),
                monotonic_ns=_TickingClock(),
            )

    def test_production_t19_1_sources_have_no_write_or_camera_factory_calls(self) -> None:
        root = Path(__file__).resolve().parents[2]
        forbidden = {
            "write",
            "sync_write",
            "enable_torque",
            "disable_torque",
            "configure",
            "calibrate",
            "scan",
            "send_action",
            "enumerate_camera_metadata",
            "capture_finite_camera_frames",
        }
        for relative in (
            "scenesmith/robot_lab/t19_1_readonly_hardware_snapshot.py",
            "scripts/robot_lab/run_t19_1_readonly_hardware_snapshot.py",
        ):
            tree = ast.parse((root / relative).read_text(encoding="utf-8"))
            called = {
                node.func.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            self.assertFalse(called & forbidden, f"forbidden calls in {relative}")


if __name__ == "__main__":
    unittest.main()
