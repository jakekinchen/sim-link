from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.hardware_execution_profile import (
    capture_hardware_execution_profile_evidence,
    verify_codex_execution_profile_files,
    verify_hardware_execution_profile_evidence,
)
from scenesmith.robot_lab.leader_arm_bridge import KNOWN_PHYSICAL_FOLLOWER_PORT
from scenesmith.robot_lab.live_readonly_observation import (
    stable_camera_identity_sha256,
)
from scenesmith.robot_lab.static_pose_live_candidate import (
    STATIC_POSE_LIVE_CANDIDATE_CONTRACT_SCHEMA_VERSION,
    STATIC_POSE_LIVE_CANDIDATE_RESULT_SCHEMA_VERSION,
)
import scenesmith.robot_lab.static_pose_live_execution as execution_module
from scenesmith.robot_lab.static_pose_live_execution import (
    build_pinned_static_pose_bus_spec,
    build_private_static_pose_candidate_failure_evidence,
    build_private_static_pose_candidate_success_evidence,
    make_pinned_static_pose_camera_factory,
    make_pinned_static_pose_transport_factory,
    verify_pinned_ffmpeg_executable,
    verify_private_static_pose_candidate_evidence_reference,
    verify_private_static_pose_candidate_failure_evidence,
    verify_private_static_pose_candidate_success_evidence,
    write_private_static_pose_candidate_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CAPTURED_AT = "2026-07-11T14:30:00-05:00"
VERIFIED_AT = "2026-07-11T14:31:00-05:00"
THREAD_ID = os.environ.get(
    "CODEX_THREAD_ID",
    "019f5006-2455-7941-bc76-b992dd96f8a8",
)
FOLLOWER_ALIAS = KNOWN_PHYSICAL_FOLLOWER_PORT.replace("/dev/cu.", "/dev/tty.", 1)


class _Clock:
    def __init__(self) -> None:
        self.value = 1_000_000_000

    def __call__(self) -> int:
        value = self.value
        self.value += 1_000_000
        return value


class _FakeRawBus:
    def __init__(self) -> None:
        self.connected = False
        self.connect_calls: list[bool] = []
        self.read_calls: list[tuple[str, str, bool, int]] = []
        self.disconnect_calls: list[bool] = []

    def connect(self, *, handshake: bool) -> None:
        self.connect_calls.append(handshake)
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
        return 2048

    def disconnect(self, *, disable_torque: bool) -> None:
        self.disconnect_calls.append(disable_torque)
        self.connected = False


class _FakePinnedCamera:
    evidence_mode = "live_injected_camera"

    def __init__(self, spec: dict) -> None:
        self.spec = copy.deepcopy(spec)


def _doctor_report(
    *,
    approval_policy: str = "OnRequest",
    cwd: Path = REPO_ROOT,
) -> dict:
    return {
        "schemaVersion": 1,
        "generatedAt": "1783798200s since unix epoch",
        "overallStatus": "ok",
        "codexVersion": "0.143.0",
        "checks": {
            "config.load": {
                "id": "config.load",
                "category": "config",
                "status": "ok",
                "summary": "config loaded",
                "details": {"cwd": str(cwd)},
                "remediation": None,
                "durationMs": 0,
            },
            "runtime.provenance": {
                "id": "runtime.provenance",
                "category": "runtime",
                "status": "ok",
                "summary": "running npm on macos-aarch64",
                "details": {
                    "current executable": (
                        "/opt/homebrew/lib/node_modules/@openai/codex/"
                        "node_modules/@openai/codex-darwin-arm64/vendor/"
                        "aarch64-apple-darwin/bin/codex"
                    ),
                    "version": "0.143.0",
                },
                "remediation": None,
                "durationMs": 0,
            },
            "sandbox.helpers": {
                "id": "sandbox.helpers",
                "category": "sandbox",
                "status": "ok",
                "summary": "sandbox configuration is readable",
                "details": {
                    "approval policy": approval_policy,
                    "filesystem sandbox": "unrestricted",
                },
                "remediation": None,
                "durationMs": 0,
            },
        },
    }


def _runtime_capture(
    *,
    approval_policy: str = "on-request",
    sandbox_mode: str = "danger-full-access",
    repo_root: Path = REPO_ROOT,
) -> dict:
    context = {
        "turn_id": "brief-053-fixture-turn",
        "cwd": str(repo_root),
        "approval_policy": approval_policy,
        "sandbox_policy": {"type": sandbox_mode},
        "model": "gpt-5.6-sol",
        "effort": "max",
        "multi_agent_mode": "explicitRequestOnly",
    }
    return {
        "rollout_reference": {
            "relative_path": (
                "sessions/2026/07/11/"
                f"rollout-2026-07-11T14-30-00-{THREAD_ID}.jsonl"
            ),
            "session_meta_identity_sha256": "a" * 64,
            "turn_context_line_number": 2,
        },
        "active_runtime_context": context,
        "active_runtime_context_sha256": hashlib.sha256(
            canonical_json_bytes(context)
        ).hexdigest(),
    }


def _runtime_loader(**kwargs) -> dict:
    return _runtime_capture(repo_root=kwargs["repo_root"])


def _copy_profile_tree(destination: Path) -> None:
    source = REPO_ROOT / ".codex"
    (destination / ".codex/profiles").mkdir(parents=True)
    for relative in (
        Path("config.toml"),
        Path("profiles/hardware-supervised.toml"),
        Path("profiles/offline-autonomous.toml"),
    ):
        target = destination / ".codex" / relative
        target.write_bytes((source / relative).read_bytes())


def _profile_evidence(*, repo_root: Path = REPO_ROOT) -> dict:
    report = _doctor_report(cwd=repo_root)

    def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(report),
            "",
        )

    return capture_hardware_execution_profile_evidence(
        repo_root=repo_root,
        captured_at=CAPTURED_AT,
        environment={"CODEX_THREAD_ID": THREAD_ID},
        run_command=runner,
        runtime_context_loader=_runtime_loader,
    )


def _candidate_contract() -> dict:
    cameras = []
    for index, pixel_format in enumerate(("uyvy422", "yuyv422")):
        mode = {
            "pixel_format": pixel_format,
            "width": 640,
            "height": 480,
            "framerate_fps": 30,
        }
        resolved = {
            "index": index,
            "name": f"Fixture Camera {index}",
            "unique_id": f"fixture-{index}",
            "model_id": f"fixture-model-{index}",
            "input_mode": copy.deepcopy(mode),
        }
        stable = stable_camera_identity_sha256(resolved)
        capture = hashlib.sha256(canonical_json_bytes(resolved)).hexdigest()
        cameras.append(
            {
                "stable_camera_identity_sha256": stable,
                "capture_camera_identity_sha256": capture,
                "resolved_camera": resolved,
                "static_camera_contract": {
                    "stable_camera_identity_sha256": stable,
                    "input_mode": copy.deepcopy(mode),
                    "required_frame_count": 2,
                    "required_encoding": "png",
                    "required_channels": 3,
                },
            }
        )
    return sign_payload(
        {
            "schema_version": STATIC_POSE_LIVE_CANDIDATE_CONTRACT_SCHEMA_VERSION,
            "contract_name": "pi05_static_pose_live_candidate",
            "qualification_scope": "local_static_pose_live_candidate_contract",
            "execution_class": "live_candidate",
            "evidence_mode": "private_source_bound_live_candidate_contract",
            "hardware_access_authorized": True,
            "session_id": "brief-053-fixture-session",
            "follower_identity": {
                "device_role": "so101_follower_observation_target",
                "usb": {
                    "vendor_id_hex": "0483",
                    "product_id_hex": "5740",
                    "serial_number": "fixture-follower",
                    "canonical_path": KNOWN_PHYSICAL_FOLLOWER_PORT,
                    "observed_aliases": [FOLLOWER_ALIAS],
                },
                "bus": {
                    "protocol_family": "feetech",
                    "protocol_version": 0,
                    "baudrate": 1_000_000,
                },
            },
            "serial_identity_paths": [
                KNOWN_PHYSICAL_FOLLOWER_PORT,
                FOLLOWER_ALIAS,
            ],
            "cameras": cameras,
            "proof_labels": [],
            "local_capabilities": ["static_pose_live_candidate_contract_valid"],
            "authority_not_granted": [
                "static_pose_bracketed_observation",
                "policy_shadow_input_valid",
                "policy_shadow",
                "physical_twin_qualified",
                "physical_transfer_ready",
                "promotion_eligible",
                "simulation_training_ready",
                "supervised_micro_motion",
            ],
            "physical_follower_commanded": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "private_output_required": True,
            "hardware_accessed": False,
        }
    )


def _candidate_result(contract: dict, profile: dict) -> dict:
    return sign_payload(
        {
            "schema_version": STATIC_POSE_LIVE_CANDIDATE_RESULT_SCHEMA_VERSION,
            "result_name": "pi05_static_pose_live_candidate_runtime",
            "qualification_scope": "local_static_pose_live_candidate_runtime",
            "execution_class": "live_candidate",
            "evidence_mode": "private_source_bound_live_candidate_runtime",
            "candidate_only": True,
            "candidate_contract_identity_sha256": contract["identity_sha256"],
            "hardware_execution_profile_identity_sha256": profile[
                "identity_sha256"
            ],
            "local_capabilities": [
                "source_bound_static_pose_live_candidate_runtime_observed"
            ],
            "proof_labels": [],
            "authority_not_granted": copy.deepcopy(
                contract["authority_not_granted"]
            ),
            "hardware_opened": True,
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "private_output_required": True,
            "tracked_redacted_manifest_written": False,
        }
    )


class HardwareExecutionProfileTests(unittest.TestCase):
    def test_profile_files_keep_default_safe_and_separate_offline_authority(self):
        profiles = verify_codex_execution_profile_files(repo_root=REPO_ROOT)
        self.assertEqual(profiles["project_default"]["sandbox_mode"], "workspace-write")
        self.assertEqual(profiles["project_default"]["approval_policy"], "on-request")
        self.assertEqual(
            profiles["hardware_supervised"]["sandbox_mode"],
            "danger-full-access",
        )
        self.assertEqual(
            profiles["hardware_supervised"]["approval_policy"],
            "on-request",
        )
        self.assertEqual(
            profiles["offline_autonomous"]["approval_policy"],
            "never",
        )
        self.assertFalse(profiles["hardware_supervised"]["features"]["multi_agent"])
        self.assertFalse(profiles["offline_autonomous"]["features"]["multi_agent"])

    def test_capture_uses_exact_doctor_command_and_binds_actual_runtime(self):
        observed: dict = {}

        def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            observed.update({"command": command, "kwargs": kwargs})
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(_doctor_report()),
                "",
            )

        evidence = capture_hardware_execution_profile_evidence(
            repo_root=REPO_ROOT,
            captured_at=CAPTURED_AT,
            environment={"CODEX_THREAD_ID": THREAD_ID},
            run_command=runner,
            runtime_context_loader=_runtime_loader,
        )
        self.assertEqual(
            observed["command"],
            [
                "/opt/homebrew/bin/codex",
                "--ask-for-approval",
                "on-request",
                "--sandbox",
                "danger-full-access",
                "doctor",
                "--json",
                "--summary",
                "--no-color",
            ],
        )
        self.assertFalse(observed["kwargs"]["shell"])
        self.assertEqual(evidence["thread_id"], THREAD_ID)
        self.assertEqual(evidence["approval_policy"], "on-request")
        self.assertEqual(evidence["sandbox_mode"], "danger-full-access")
        self.assertEqual(
            evidence["source_mode"],
            "live_codex_doctor_and_active_rollout_runtime_capture",
        )
        self.assertFalse(evidence["synthetic"])
        verify_hardware_execution_profile_evidence(
            evidence,
            repo_root=REPO_ROOT,
            now=VERIFIED_AT,
            expected_thread_id=THREAD_ID,
            runtime_context_loader=_runtime_loader,
        )

    def test_capture_resolves_the_exact_active_rollout_and_latest_turn_context(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)
            rollout = (
                codex_home
                / "sessions/2026/07/11"
                / f"rollout-2026-07-11T14-30-00-{THREAD_ID}.jsonl"
            )
            rollout.parent.mkdir(parents=True)
            context = {
                **_runtime_capture()["active_runtime_context"],
                "summary": "private fixture summary not copied into evidence",
            }
            records = [
                {"type": "session_meta", "payload": {"id": THREAD_ID}},
                {"type": "turn_context", "payload": context},
            ]
            rollout.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )

            def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
                return subprocess.CompletedProcess(
                    command,
                    0,
                    json.dumps(_doctor_report()),
                    "",
                )

            evidence = capture_hardware_execution_profile_evidence(
                repo_root=REPO_ROOT,
                captured_at=CAPTURED_AT,
                environment={
                    "CODEX_THREAD_ID": THREAD_ID,
                    "CODEX_HOME": str(codex_home),
                },
                run_command=runner,
            )
        self.assertEqual(
            evidence["rollout_reference"]["relative_path"],
            rollout.relative_to(codex_home).as_posix(),
        )
        self.assertEqual(evidence["active_runtime_context"]["turn_id"], context["turn_id"])
        self.assertNotIn("summary", evidence["active_runtime_context"])

    def test_never_stale_cross_thread_synthetic_and_profile_drift_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _copy_profile_tree(root)
            evidence = _profile_evidence(repo_root=root)
            with self.assertRaisesRegex(ValueError, "stale"):
                verify_hardware_execution_profile_evidence(
                    evidence,
                    repo_root=root,
                    now="2026-07-11T14:36:00-05:00",
                    expected_thread_id=THREAD_ID,
                    runtime_context_loader=_runtime_loader,
                )
            with self.assertRaisesRegex(ValueError, "thread"):
                verify_hardware_execution_profile_evidence(
                    evidence,
                    repo_root=root,
                    now=VERIFIED_AT,
                    expected_thread_id="different-thread",
                    runtime_context_loader=_runtime_loader,
                )
            changed = copy.deepcopy(evidence)
            changed["synthetic"] = True
            with self.assertRaisesRegex(ValueError, "source classification"):
                verify_hardware_execution_profile_evidence(
                    sign_payload(changed),
                    repo_root=root,
                    now=VERIFIED_AT,
                    expected_thread_id=THREAD_ID,
                    runtime_context_loader=_runtime_loader,
                )
            (root / ".codex/profiles/hardware-supervised.toml").write_text(
                "sandbox_mode = \"danger-full-access\"\n"
                "approval_policy = \"never\"\n"
                "[features]\nmulti_agent = false\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "profile|approval"):
                verify_hardware_execution_profile_evidence(
                    evidence,
                    repo_root=root,
                    now=VERIFIED_AT,
                    expected_thread_id=THREAD_ID,
                    runtime_context_loader=_runtime_loader,
                )

            (root / ".codex/profiles/hardware-supervised.toml").write_bytes(
                (REPO_ROOT / ".codex/profiles/hardware-supervised.toml").read_bytes()
            )
            source = root / ".codex/profiles/offline-autonomous.toml"
            replacement = root / ".codex/profiles/offline-copy.toml"
            replacement.write_bytes(source.read_bytes())
            source.unlink()
            source.symlink_to(replacement.name)
            with self.assertRaisesRegex(ValueError, "aliased"):
                verify_codex_execution_profile_files(repo_root=root)

        report = _doctor_report(approval_policy="Never")

        def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            return subprocess.CompletedProcess(command, 0, json.dumps(report), "")

        with self.assertRaisesRegex(ValueError, "on-request"):
            capture_hardware_execution_profile_evidence(
                repo_root=REPO_ROOT,
                captured_at=CAPTURED_AT,
                environment={"CODEX_THREAD_ID": THREAD_ID},
                run_command=runner,
                runtime_context_loader=_runtime_loader,
            )

        with self.assertRaisesRegex(ValueError, "[Aa]ctive.*on-request"):
            capture_hardware_execution_profile_evidence(
                repo_root=REPO_ROOT,
                captured_at=CAPTURED_AT,
                environment={"CODEX_THREAD_ID": THREAD_ID},
                run_command=lambda *args, **kwargs: self.fail(
                    "doctor must not run for an ineligible active thread"
                ),
                runtime_context_loader=lambda **kwargs: _runtime_capture(
                    approval_policy="never",
                    repo_root=kwargs["repo_root"],
                ),
            )


class PinnedLiveFactoryTests(unittest.TestCase):
    def test_pinned_feetech_factory_is_one_shot_and_exposes_only_no_write_adapter(self):
        contract = _candidate_contract()
        spec = build_pinned_static_pose_bus_spec(contract, repo_root=REPO_ROOT)
        self.assertEqual(spec["port"], KNOWN_PHYSICAL_FOLLOWER_PORT)
        self.assertEqual(spec["protocol_version"], 0)
        self.assertEqual(spec["baudrate"], 1_000_000)
        self.assertEqual([motor["servo_id"] for motor in spec["motors"]], list(range(1, 7)))
        self.assertEqual(spec["allowed_registers"], ["Present_Position"])
        self.assertFalse(spec["connect_handshake"])
        self.assertFalse(spec["disconnect_disable_torque"])

        raw_bus = _FakeRawBus()
        profile = _profile_evidence()
        with patch.object(
            execution_module,
            "verify_hardware_execution_profile_evidence",
        ) as profile_verifier, patch.object(
            execution_module,
            "verify_static_pose_live_candidate_contract",
        ) as contract_verifier, patch.object(
            execution_module,
            "_construct_pinned_feetech_bus",
            return_value=raw_bus,
        ) as constructor:
            factory = make_pinned_static_pose_transport_factory(
                contract,
                hardware_execution_profile=profile,
                project_state={},
                static_pose_contract={},
                calibration_path=Path("fixture-calibration.json"),
                calibration_profile_path=Path("fixture-profile.json"),
                manifest_path=Path("fixture-manifest.json"),
                now=VERIFIED_AT,
                repo_root=REPO_ROOT,
                monotonic_ns=_Clock(),
            )
            transport = factory(copy.deepcopy(contract))
            self.assertEqual(transport.evidence_mode, "live_injected_transport")
            transport.connect()
            self.assertEqual(
                transport.read_position("shoulder_pan", 1),
                2048,
            )
            transport.close()
            with self.assertRaisesRegex(RuntimeError, "one-shot"):
                factory(copy.deepcopy(contract))
        constructor.assert_called_once()
        profile_verifier.assert_called_once()
        contract_verifier.assert_called_once()
        self.assertEqual(raw_bus.connect_calls, [False])
        self.assertEqual(
            raw_bus.read_calls,
            [("Present_Position", "shoulder_pan", False, 0)],
        )
        self.assertEqual(raw_bus.disconnect_calls, [False])
        audit = transport.audit()
        self.assertEqual(audit["motor_register_writes"], 0)
        self.assertEqual(audit["torque_changes"], 0)
        self.assertEqual(audit["motion_commands"], 0)
        for forbidden in (
            "write",
            "sync_write",
            "enable_torque",
            "disable_torque",
            "calibrate",
            "send_action",
        ):
            self.assertFalse(hasattr(transport, forbidden), forbidden)

    def test_pinned_camera_factory_binds_exact_mode_count_binary_and_one_use_each(self):
        contract = _candidate_contract()
        executable = verify_pinned_ffmpeg_executable()
        self.assertEqual(executable["path"], "/opt/homebrew/bin/ffmpeg")
        self.assertEqual(executable["version"], "8.0.1")
        created: list[dict] = []
        profile = _profile_evidence()

        def construct(spec: dict, *, monotonic_ns):
            created.append(copy.deepcopy(spec))
            return _FakePinnedCamera(spec)

        with patch.object(
            execution_module,
            "verify_hardware_execution_profile_evidence",
        ) as profile_verifier, patch.object(
            execution_module,
            "verify_static_pose_live_candidate_contract",
        ) as contract_verifier, patch.object(
            execution_module,
            "_construct_pinned_ffmpeg_camera",
            side_effect=construct,
        ):
            factory = make_pinned_static_pose_camera_factory(
                contract,
                hardware_execution_profile=profile,
                project_state={},
                static_pose_contract={},
                calibration_path=Path("fixture-calibration.json"),
                calibration_profile_path=Path("fixture-profile.json"),
                manifest_path=Path("fixture-manifest.json"),
                now=VERIFIED_AT,
                monotonic_ns=_Clock(),
            )
            for camera in contract["cameras"]:
                instance = factory(
                    copy.deepcopy(camera["resolved_camera"]),
                    copy.deepcopy(camera["static_camera_contract"]),
                )
                self.assertEqual(instance.evidence_mode, "live_injected_camera")
            with self.assertRaisesRegex(RuntimeError, "already consumed"):
                camera = contract["cameras"][0]
                factory(
                    copy.deepcopy(camera["resolved_camera"]),
                    copy.deepcopy(camera["static_camera_contract"]),
                )
        self.assertEqual(len(created), 2)
        profile_verifier.assert_called_once()
        contract_verifier.assert_called_once()
        self.assertTrue(all(spec["expected_frame_count"] == 2 for spec in created))
        self.assertTrue(all(spec["framerate_fps"] == 30 for spec in created))
        self.assertTrue(all(spec["ffmpeg"] == executable for spec in created))

    def test_active_runtime_change_during_doctor_capture_rejects(self):
        captures = iter(
            [
                _runtime_capture(),
                {
                    **_runtime_capture(),
                    "active_runtime_context": {
                        **_runtime_capture()["active_runtime_context"],
                        "turn_id": "changed-during-capture",
                    },
                },
            ]
        )

        def loader(**kwargs) -> dict:
            return next(captures)

        with self.assertRaisesRegex(ValueError, "changed during"):
            capture_hardware_execution_profile_evidence(
                repo_root=REPO_ROOT,
                captured_at=CAPTURED_AT,
                environment={"CODEX_THREAD_ID": THREAD_ID},
                run_command=lambda command, **kwargs: subprocess.CompletedProcess(
                    command,
                    0,
                    json.dumps(_doctor_report()),
                    "",
                ),
                runtime_context_loader=loader,
            )

    def test_factory_rejects_resigned_path_protocol_camera_or_authority_drift(self):
        contract = _candidate_contract()
        cases = (
            (
                "path",
                lambda value: value["follower_identity"]["usb"].__setitem__(
                    "canonical_path", "/dev/cu.different"
                ),
            ),
            (
                "protocol",
                lambda value: value["follower_identity"]["bus"].__setitem__(
                    "protocol_version", 1
                ),
            ),
            (
                "fixture class",
                lambda value: value.__setitem__(
                    "execution_class", "deterministic_candidate_fixture"
                ),
            ),
            (
                "proof",
                lambda value: value.__setitem__(
                    "proof_labels", ["static_pose_bracketed_observation"]
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                changed = copy.deepcopy(contract)
                mutate(changed)
                with self.assertRaises(ValueError):
                    build_pinned_static_pose_bus_spec(
                        sign_payload(changed),
                        repo_root=REPO_ROOT,
                    )

        changed = copy.deepcopy(contract)
        changed["cameras"][0]["static_camera_contract"]["required_frame_count"] = 3
        changed = sign_payload(changed)
        with patch.object(
            execution_module,
            "verify_hardware_execution_profile_evidence",
        ), patch.object(
            execution_module,
            "verify_static_pose_live_candidate_contract",
        ), self.assertRaisesRegex(ValueError, "camera|frame"):
            make_pinned_static_pose_camera_factory(
                changed,
                hardware_execution_profile=_profile_evidence(),
                project_state={},
                static_pose_contract={},
                calibration_path=Path("fixture-calibration.json"),
                calibration_profile_path=Path("fixture-profile.json"),
                manifest_path=Path("fixture-manifest.json"),
                now=VERIFIED_AT,
                monotonic_ns=_Clock(),
            )


class PrivateCandidateEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = _candidate_contract()
        self.profile = _profile_evidence()
        self.result = _candidate_result(self.contract, self.profile)

    def test_success_and_failure_are_fixed_candidate_only_private_classes(self):
        success = build_private_static_pose_candidate_success_evidence(
            candidate_contract=self.contract,
            hardware_execution_profile=self.profile,
            candidate_result=self.result,
            completed_at=VERIFIED_AT,
        )
        failure = build_private_static_pose_candidate_failure_evidence(
            candidate_contract=self.contract,
            hardware_execution_profile=self.profile,
            error=BaseExceptionGroup(
                "runtime and cleanup failed",
                [RuntimeError("camera failed"), OSError("holder check failed")],
            ),
            failed_at=VERIFIED_AT,
        )
        verify_private_static_pose_candidate_success_evidence(
            success,
            repo_root=REPO_ROOT,
            now=VERIFIED_AT,
            expected_thread_id=THREAD_ID,
        )
        verify_private_static_pose_candidate_failure_evidence(
            failure,
            repo_root=REPO_ROOT,
            now=VERIFIED_AT,
            expected_thread_id=THREAD_ID,
        )
        self.assertEqual(success["status"], "candidate_observed")
        self.assertEqual(failure["status"], "rejected")
        self.assertEqual(success["proof_labels"], [])
        self.assertEqual(failure["proof_labels"], [])
        self.assertTrue(success["candidate_only"])
        self.assertTrue(failure["candidate_only"])
        self.assertEqual(failure["error_types"], ["OSError", "RuntimeError"])
        self.assertEqual(failure["error_leaf_count"], 2)
        self.assertNotIn("error_messages", failure)
        verify_private_static_pose_candidate_success_evidence(
            success,
            repo_root=REPO_ROOT,
            now="2026-07-12T14:31:00-05:00",
            expected_thread_id=THREAD_ID,
        )

    def test_re_signed_success_failure_class_contract_profile_and_proof_drift_reject(self):
        success = build_private_static_pose_candidate_success_evidence(
            candidate_contract=self.contract,
            hardware_execution_profile=self.profile,
            candidate_result=self.result,
            completed_at=VERIFIED_AT,
        )
        mutations = (
            lambda value: value.__setitem__("status", "rejected"),
            lambda value: value.__setitem__(
                "proof_labels", ["static_pose_bracketed_observation"]
            ),
            lambda value: value.__setitem__("candidate_only", False),
            lambda value: value.__setitem__(
                "candidate_contract_identity_sha256", "0" * 64
            ),
            lambda value: value.__setitem__(
                "hardware_execution_profile_identity_sha256", "0" * 64
            ),
        )
        for mutate in mutations:
            changed = copy.deepcopy(success)
            mutate(changed)
            with self.assertRaises(ValueError):
                verify_private_static_pose_candidate_success_evidence(
                    sign_payload(changed),
                    repo_root=REPO_ROOT,
                    now=VERIFIED_AT,
                    expected_thread_id=THREAD_ID,
                )
        changed = copy.deepcopy(success)
        changed_result = copy.deepcopy(changed["candidate_result"])
        changed_result["hardware_execution_profile_identity_sha256"] = "0" * 64
        changed["candidate_result"] = sign_payload(changed_result)
        changed["candidate_result_identity_sha256"] = changed[
            "candidate_result"
        ]["identity_sha256"]
        with self.assertRaisesRegex(ValueError, "profile|result"):
            verify_private_static_pose_candidate_success_evidence(
                sign_payload(changed),
                repo_root=REPO_ROOT,
                now=VERIFIED_AT,
                expected_thread_id=THREAD_ID,
            )

    def test_content_addressed_writer_is_exclusive_and_reference_rehashes(self):
        evidence = build_private_static_pose_candidate_success_evidence(
            candidate_contract=self.contract,
            hardware_execution_profile=self.profile,
            candidate_result=self.result,
            completed_at=VERIFIED_AT,
        )
        with tempfile.TemporaryDirectory() as directory:
            private_root = Path(directory) / "private"
            private_root.mkdir()
            reference = write_private_static_pose_candidate_evidence(
                private_root=private_root,
                evidence=evidence,
            )
            expected_relative = (
                f"{self.contract['session_id']}/"
                f"{evidence['identity_sha256']}/private_success.json"
            )
            self.assertEqual(reference["relative_path"], expected_relative)
            verify_private_static_pose_candidate_evidence_reference(
                reference,
                private_root=private_root,
                evidence=evidence,
            )
            with self.assertRaisesRegex(ValueError, "new|immutable|exists"):
                write_private_static_pose_candidate_evidence(
                    private_root=private_root,
                    evidence=evidence,
                )
            failure = build_private_static_pose_candidate_failure_evidence(
                candidate_contract=self.contract,
                hardware_execution_profile=self.profile,
                error=RuntimeError("later fixture failure"),
                failed_at=VERIFIED_AT,
            )
            with self.assertRaisesRegex(ValueError, "session|immutable|exists"):
                write_private_static_pose_candidate_evidence(
                    private_root=private_root,
                    evidence=failure,
                )
            evidence_path = private_root / reference["relative_path"]
            evidence_path.write_bytes(evidence_path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "hash|size|content"):
                verify_private_static_pose_candidate_evidence_reference(
                    reference,
                    private_root=private_root,
                    evidence=evidence,
                )

    def test_writer_rejects_symlink_root_and_unsafe_session(self):
        evidence = build_private_static_pose_candidate_failure_evidence(
            candidate_contract=self.contract,
            hardware_execution_profile=self.profile,
            error=RuntimeError("fixture failure"),
            failed_at=VERIFIED_AT,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            link = root / "private"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                write_private_static_pose_candidate_evidence(
                    private_root=link,
                    evidence=evidence,
                )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_parent = root / "real-parent"
            real_private = real_parent / "private"
            real_private.mkdir(parents=True)
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                write_private_static_pose_candidate_evidence(
                    private_root=linked_parent / "private",
                    evidence=evidence,
                )
        changed_contract = copy.deepcopy(self.contract)
        changed_contract["session_id"] = "../escape"
        changed_contract = sign_payload(changed_contract)
        with self.assertRaisesRegex(ValueError, "session"):
            build_private_static_pose_candidate_failure_evidence(
                candidate_contract=changed_contract,
                hardware_execution_profile=self.profile,
                error=RuntimeError("fixture failure"),
                failed_at=VERIFIED_AT,
            )


if __name__ == "__main__":
    unittest.main()
