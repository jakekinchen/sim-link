from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.leader_arm_bridge import KNOWN_PHYSICAL_FOLLOWER_PORT
from scenesmith.robot_lab.live_readonly_observation import (
    enumerate_serial_identity_holders,
)
import scenesmith.robot_lab.static_pose_session_review as review_module
from scenesmith.robot_lab.static_pose_session_review import (
    REDACTED_STATIC_POSE_LIVE_SESSION_REVIEW_SCHEMA_VERSION,
    build_redacted_static_pose_live_session_review_manifest,
    verify_redacted_static_pose_live_session_review_manifest,
    write_redacted_static_pose_live_session_review_manifest,
)


SESSION_ID = "brief-055-fixture-session"
PREFLIGHT_AT = "2026-07-11T15:34:59-05:00"
STARTED_AT = "2026-07-11T15:35:00-05:00"
COMPLETED_AT = "2026-07-11T15:35:10-05:00"
FOLLOWER_ALIAS = KNOWN_PHYSICAL_FOLLOWER_PORT.replace("/dev/cu.", "/dev/tty.", 1)
SENSITIVE_PRIVATE_ROOT = Path("/private/fixture/SENSITIVE_PRIVATE_ROOT")
SENSITIVE_CAMERA_NAME = "SENSITIVE_CAMERA_NAME_NEVER_TRACK"
SENSITIVE_CAMERA_UNIQUE_ID = "SENSITIVE_CAMERA_UNIQUE_ID_NEVER_TRACK"
SENSITIVE_CAMERA_MODEL_ID = "SENSITIVE_CAMERA_MODEL_ID_NEVER_TRACK"
SENSITIVE_USB_SERIAL = "SENSITIVE_USB_SERIAL_NEVER_TRACK"
SENSITIVE_DOCTOR_REPORT = "SENSITIVE_DOCTOR_REPORT_NEVER_TRACK"
SENSITIVE_ROLLOUT_PATH = "/private/SENSITIVE_ROLLOUT_PATH_NEVER_TRACK.jsonl"

AUTHORITY_NOT_GRANTED = [
    "live_candidate_session_accepted",
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]


def _holder_snapshot() -> dict:
    def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(command, 1, "", "")

    return enumerate_serial_identity_holders(
        KNOWN_PHYSICAL_FOLLOWER_PORT,
        [FOLLOWER_ALIAS],
        run_command=runner,
        path_exists=lambda path: True,
    )


def _source_reference(name: str, marker: str) -> dict:
    return {
        "logical_path": f"configurations/robot_lab/SENSITIVE_{name}.json",
        "schema_version": f"fixture.{name}.v1",
        "identity_sha256": marker * 64,
        "file_sha256": marker.upper().encode().hex()[:64].ljust(64, "0"),
        "size_bytes": 100 + ord(marker),
    }


def _contract() -> dict:
    camera_records = []
    for index, marker in enumerate(("a", "b"), start=17):
        camera_records.append(
            {
                "stable_camera_identity_sha256": marker * 64,
                "capture_camera_identity_sha256": chr(ord(marker) + 2) * 64,
                "resolved_camera": {
                    "index": index,
                    "name": f"{SENSITIVE_CAMERA_NAME}_{index}",
                    "unique_id": f"{SENSITIVE_CAMERA_UNIQUE_ID}_{index}",
                    "model_id": f"{SENSITIVE_CAMERA_MODEL_ID}_{index}",
                    "input_mode": {
                        "pixel_format": "uyvy422",
                        "width": 640,
                        "height": 480,
                        "framerate_fps": 30,
                    },
                },
            }
        )
    return sign_payload(
        {
            "schema_version": "scenesmith.static_pose_live_candidate_contract.v1",
            "contract_name": "pi05_static_pose_live_candidate",
            "qualification_scope": "local_static_pose_live_candidate_contract",
            "evidence_mode": "private_source_bound_live_candidate_contract",
            "execution_class": "live_candidate",
            "hardware_access_authorized": True,
            "session_id": SESSION_ID,
            "project_state_identity_sha256": "1" * 64,
            "presence_lease_identity_sha256": "2" * 64,
            "discovery_identity_sha256": "3" * 64,
            "source_artifacts": {
                "accepted_manifest": _source_reference("manifest", "4"),
                "calibration_profile": _source_reference("profile", "5"),
                "static_pose_contract": _source_reference("static", "6"),
            },
            "follower_identity": {
                "usb": {
                    "serial_number": SENSITIVE_USB_SERIAL,
                    "canonical_path": KNOWN_PHYSICAL_FOLLOWER_PORT,
                    "observed_aliases": [FOLLOWER_ALIAS],
                }
            },
            "serial_identity_paths": [
                KNOWN_PHYSICAL_FOLLOWER_PORT,
                FOLLOWER_ALIAS,
            ],
            "cameras": camera_records,
            "proof_labels": [],
            "local_capabilities": ["static_pose_live_candidate_contract_valid"],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED[1:]),
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "private_output_required": True,
        }
    )


def _profile() -> dict:
    return sign_payload(
        {
            "schema_version": "scenesmith.hardware_execution_profile_evidence.v1",
            "thread_id": "brief-055-fixture-thread",
            "doctor_report": {"secret": SENSITIVE_DOCTOR_REPORT},
            "rollout_reference": {"path": SENSITIVE_ROLLOUT_PATH},
            "approval_policy": "never",
            "sandbox_mode": "danger-full-access",
            "local_capabilities": [
                "hardware_supervised_runtime_profile_observed"
            ],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED[1:]),
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
        }
    )


def _camera_batches() -> list[dict]:
    batches = []
    for camera_index, marker in enumerate(("a", "b")):
        batches.append(
            {
                "stable_camera_identity_sha256": marker * 64,
                "input_mode": {
                    "pixel_format": "uyvy422",
                    "width": 640,
                    "height": 480,
                    "framerate_fps": 30,
                },
                "frames": [
                    {
                        "frame_index": frame_index,
                        "frame_sha256": str(
                            camera_index * 2 + frame_index + 6
                        )
                        * 64,
                        "width": 640,
                        "height": 480,
                        "channels": 3,
                        "encoding": "png",
                    }
                    for frame_index in range(2)
                ],
            }
        )
    return batches


def _result(contract: dict, profile: dict, static_contract: dict) -> dict:
    holder = _holder_snapshot()
    operation_counts = {
        "construct_attempts": 1,
        "construct_successes": 1,
        "connect_attempts": 1,
        "connect_successes": 1,
        "position_read_attempts": 12,
        "position_read_successes": 12,
        "read_retries": 0,
        "camera_batch_attempts": 2,
        "camera_batch_successes": 2,
        "camera_frame_reads": 4,
        "close_attempts": 1,
        "close_successes": 1,
        "motor_register_writes": 0,
        "configuration_writes": 0,
        "torque_changes": 0,
        "motion_commands": 0,
        "unexpected_operations": 0,
    }
    timing = {
        "bracket_started_monotonic_ns": 1_000_000_000,
        "bracket_finished_monotonic_ns": 1_100_000_000,
        "bracket_duration_ns": 100_000_000,
        "camera_receive_started_monotonic_ns": 1_020_000_000,
        "camera_receive_finished_monotonic_ns": 1_080_000_000,
        "camera_receive_duration_ns": 60_000_000,
        "maximum_bracket_duration_ns": 5_000_000_000,
    }
    return sign_payload(
        {
            "schema_version": "scenesmith.static_pose_live_candidate_result.v2",
            "result_name": "pi05_static_pose_live_candidate_runtime",
            "qualification_scope": "local_static_pose_live_candidate_runtime",
            "evidence_mode": "private_source_bound_live_candidate_runtime",
            "execution_class": "live_candidate",
            "candidate_only": True,
            "verified_at": STARTED_AT,
            "candidate_contract_identity_sha256": contract["identity_sha256"],
            "static_pose_contract_identity_sha256": static_contract[
                "identity_sha256"
            ],
            "project_state_identity_sha256": contract[
                "project_state_identity_sha256"
            ],
            "presence_lease_identity_sha256": contract[
                "presence_lease_identity_sha256"
            ],
            "discovery_identity_sha256": contract["discovery_identity_sha256"],
            "hardware_execution_profile_identity_sha256": profile[
                "identity_sha256"
            ],
            "capture": {
                "runtime_started_monotonic_ns": 990_000_000,
                "runtime_finished_monotonic_ns": 1_110_000_000,
                "runtime_duration_ns": 120_000_000,
                "pre_open_holder_snapshot": holder,
                "post_close_holder_snapshot": copy.deepcopy(holder),
                "q_before": [
                    {"joint_name": "shoulder_pan", "raw_position": 987654321}
                ],
                "q_after": [
                    {"joint_name": "shoulder_pan", "raw_position": 987654322}
                ],
                "cameras": _camera_batches(),
                "operation_counts": operation_counts,
                "transport_audit": {
                    "hardware_opened": True,
                    "physical_follower_commanded": False,
                },
                "camera_audits": [{"camera": 0}, {"camera": 1}],
                "lifecycle_events": [
                    "pre_open_holder",
                    "construct",
                    "connect",
                    "q_before",
                    "camera_0",
                    "camera_1",
                    "q_after",
                    "close",
                    "post_close_holder",
                ],
                "hardware_opened": True,
                "physical_follower_commanded": False,
            },
            "measurements": {
                "joint_drift": [
                    {
                        "joint_name": "shoulder_pan",
                        "raw_before": 987654321,
                        "raw_after": 987654322,
                        "absolute_delta": 0.1,
                    }
                ],
                "maximum_body_drift_degrees": 0.1,
                "gripper_drift_percent": 0.2,
                "timing": timing,
                "operation_counts": copy.deepcopy(operation_counts),
                "static_pose_within_tolerance": True,
            },
            "resolved_camera_binding": [
                {
                    "stable_camera_identity_sha256": marker * 64,
                    "capture_camera_identity_sha256": chr(ord(marker) + 2) * 64,
                    "numeric_index": index,
                }
                for index, marker in enumerate(("a", "b"), start=17)
            ],
            "proof_labels": [],
            "local_capabilities": [
                "source_bound_static_pose_live_candidate_runtime_observed"
            ],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED[1:]),
            "hardware_opened": True,
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "private_output_required": True,
            "tracked_redacted_manifest_written": False,
        }
    )


def _private_evidence(contract: dict, profile: dict, result: dict) -> dict:
    return sign_payload(
        {
            "schema_version": (
                "scenesmith.static_pose_live_candidate_private_success.v1"
            ),
            "evidence_name": "pi05_static_pose_live_candidate_private_success",
            "qualification_scope": "local_static_pose_live_candidate_runtime",
            "evidence_mode": "local_private_live_candidate_success",
            "status": "candidate_observed",
            "session_id": SESSION_ID,
            "candidate_only": True,
            "candidate_contract_identity_sha256": contract["identity_sha256"],
            "hardware_execution_profile_identity_sha256": profile[
                "identity_sha256"
            ],
            "candidate_result_identity_sha256": result["identity_sha256"],
            "candidate_result": copy.deepcopy(result),
            "completed_at": COMPLETED_AT,
            "proof_labels": [],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED[1:]),
            "hardware_opened": True,
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "tracked_redacted_manifest_written": False,
        }
    )


def _reference(private_evidence: dict) -> dict:
    return {
        "relative_path": (
            f"{SESSION_ID}/{private_evidence['identity_sha256']}/"
            "private_success.json"
        ),
        "schema_version": private_evidence["schema_version"],
        "identity_sha256": private_evidence["identity_sha256"],
        "file_sha256": "e" * 64,
        "size_bytes": 123456,
    }


def _private_root_identity(path: Path) -> str:
    normalized = path.resolve().as_posix() if path.is_absolute() else path.as_posix()
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def _receipt(
    contract: dict,
    profile: dict,
    result: dict,
    private_evidence: dict,
    reference: dict,
) -> dict:
    return sign_payload(
        {
            "schema_version": "scenesmith.static_pose_live_session_receipt.v1",
            "receipt_name": "pi05_static_pose_live_candidate_session",
            "qualification_scope": "local_static_pose_live_candidate_session",
            "evidence_mode": "private_candidate_session_receipt",
            "status": "candidate_observed",
            "session_id": SESSION_ID,
            "candidate_only": True,
            "preflight_at": PREFLIGHT_AT,
            "started_at": STARTED_AT,
            "completed_at": COMPLETED_AT,
            "candidate_contract_identity_sha256": contract["identity_sha256"],
            "hardware_execution_profile_identity_sha256": profile[
                "identity_sha256"
            ],
            "candidate_result_identity_sha256": result["identity_sha256"],
            "private_evidence_identity_sha256": private_evidence[
                "identity_sha256"
            ],
            "private_reference": copy.deepcopy(reference),
            "private_reference_sha256": hashlib.sha256(
                canonical_json_bytes(reference)
            ).hexdigest(),
            "private_root_identity_sha256": _private_root_identity(
                SENSITIVE_PRIVATE_ROOT
            ),
            "proof_labels": [],
            "local_capabilities": [
                "private_static_pose_live_session_receipt_valid"
            ],
            "authority_not_granted": copy.deepcopy(AUTHORITY_NOT_GRANTED[1:]),
            "hardware_opened": True,
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "tracked_redacted_manifest_written": False,
        }
    )


class StaticPoseSessionReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.static_contract = sign_payload(
            {
                "schema_version": "scenesmith.static_pose_bracket_contract.v2",
                "contract_name": "fixture-static-contract",
            }
        )
        self.contract = _contract()
        self.profile = _profile()
        self.result = _result(
            self.contract,
            self.profile,
            self.static_contract,
        )
        self.private_evidence = _private_evidence(
            self.contract,
            self.profile,
            self.result,
        )
        self.reference = _reference(self.private_evidence)
        self.receipt = _receipt(
            self.contract,
            self.profile,
            self.result,
            self.private_evidence,
            self.reference,
        )

    def _arguments(self) -> dict:
        return {
            "session_receipt": self.receipt,
            "candidate_contract": self.contract,
            "hardware_execution_profile": self.profile,
            "candidate_result": self.result,
            "private_evidence": self.private_evidence,
            "private_reference": self.reference,
            "private_root": SENSITIVE_PRIVATE_ROOT,
            "static_pose_contract": self.static_contract,
            "calibration_path": Path("SENSITIVE_CALIBRATION_PATH.json"),
            "calibration_profile_path": Path("SENSITIVE_PROFILE_PATH.json"),
            "manifest_path": Path("SENSITIVE_MANIFEST_PATH.json"),
        }

    @contextmanager
    def _patched_receipt_verifier(self):
        with patch.object(
            review_module,
            "verify_static_pose_live_session_receipt",
        ) as verifier:
            yield verifier

    def test_manifest_is_deterministic_redacted_and_candidate_only(self):
        with self._patched_receipt_verifier() as receipt_verifier:
            first = build_redacted_static_pose_live_session_review_manifest(
                **self._arguments()
            )
            second = build_redacted_static_pose_live_session_review_manifest(
                **self._arguments()
            )
            verify_redacted_static_pose_live_session_review_manifest(
                first,
                **self._arguments(),
            )
        self.assertEqual(first, second)
        self.assertEqual(receipt_verifier.call_count, 3)
        self.assertEqual(
            first["schema_version"],
            REDACTED_STATIC_POSE_LIVE_SESSION_REVIEW_SCHEMA_VERSION,
        )
        self.assertEqual(first["status"], "candidate_observed_pending_review")
        self.assertEqual(first["proof_labels"], [])
        self.assertEqual(
            first["local_capabilities"],
            ["redacted_static_pose_live_candidate_session_review_conformant"],
        )
        self.assertEqual(first["authority_not_granted"], AUTHORITY_NOT_GRANTED)
        self.assertFalse(first["accepted_as_static_pose_bracketed_observation"])
        self.assertFalse(first["accepted_as_policy_shadow_input"])
        self.assertNotIn("relative_path", first["private_artifact"])
        encoded = json.dumps(first, sort_keys=True)
        for secret in (
            self.reference["relative_path"],
            SENSITIVE_PRIVATE_ROOT.as_posix(),
            SENSITIVE_CAMERA_NAME,
            SENSITIVE_CAMERA_UNIQUE_ID,
            SENSITIVE_CAMERA_MODEL_ID,
            SENSITIVE_USB_SERIAL,
            SENSITIVE_DOCTOR_REPORT,
            SENSITIVE_ROLLOUT_PATH,
            KNOWN_PHYSICAL_FOLLOWER_PORT,
            FOLLOWER_ALIAS,
            "SENSITIVE_CALIBRATION_PATH",
            "SENSITIVE_PROFILE_PATH",
            "SENSITIVE_MANIFEST_PATH",
            "987654321",
            "987654322",
        ):
            self.assertNotIn(secret, encoded)
        self.assertNotIn("q_before", encoded)
        self.assertNotIn("q_after", encoded)
        self.assertNotIn("joint_drift\"", encoded)
        for camera in first["camera_observation_summary"]:
            self.assertNotIn("numeric_index", camera)
            self.assertNotIn("resolved_camera", camera)

    def test_builder_rejects_failure_fixture_or_source_substitution(self):
        cases = []

        failure = copy.deepcopy(self.private_evidence)
        failure["schema_version"] = (
            "scenesmith.static_pose_live_candidate_private_failure.v1"
        )
        failure["status"] = "rejected"
        cases.append(("failure evidence", "private_evidence", sign_payload(failure)))

        fixture = copy.deepcopy(self.result)
        fixture["execution_class"] = "deterministic_candidate_fixture"
        cases.append(("fixture result", "candidate_result", sign_payload(fixture)))

        for label, key, value in (
            (
                "contract",
                "candidate_contract",
                sign_payload({**self.contract, "session_id": "substituted"}),
            ),
            (
                "profile",
                "hardware_execution_profile",
                sign_payload({**self.profile, "thread_id": "substituted"}),
            ),
            (
                "result",
                "candidate_result",
                sign_payload({**self.result, "verified_at": COMPLETED_AT}),
            ),
            (
                "static contract",
                "static_pose_contract",
                sign_payload({**self.static_contract, "contract_name": "changed"}),
            ),
            (
                "private reference",
                "private_reference",
                {**self.reference, "file_sha256": "0" * 64},
            ),
            (
                "private root",
                "private_root",
                Path("/private/fixture/substituted-root"),
            ),
        ):
            cases.append((label, key, value))

        receipt = copy.deepcopy(self.receipt)
        receipt["status"] = "accepted"
        cases.append(("receipt", "session_receipt", sign_payload(receipt)))

        result_authority = copy.deepcopy(self.result)
        result_authority["motion_authority_granted"] = True
        cases.append(
            (
                "result authority",
                "candidate_result",
                sign_payload(result_authority),
            )
        )

        profile_authority = copy.deepcopy(self.profile)
        profile_authority["approval_policy"] = "on-request"
        cases.append(
            (
                "profile authority",
                "hardware_execution_profile",
                sign_payload(profile_authority),
            )
        )

        private_authority = copy.deepcopy(self.private_evidence)
        private_authority["policy_inference_run"] = True
        cases.append(
            (
                "private authority",
                "private_evidence",
                sign_payload(private_authority),
            )
        )

        with self._patched_receipt_verifier():
            for label, key, value in cases:
                with self.subTest(case=label):
                    arguments = self._arguments()
                    arguments[key] = value
                    with self.assertRaises(ValueError):
                        build_redacted_static_pose_live_session_review_manifest(
                            **arguments
                        )

    def test_verifier_rejects_resigned_authority_and_field_drift(self):
        with self._patched_receipt_verifier():
            manifest = build_redacted_static_pose_live_session_review_manifest(
                **self._arguments()
            )
            mutations = (
                lambda value: value.__setitem__(
                    "proof_labels", ["static_pose_bracketed_observation"]
                ),
                lambda value: value.__setitem__(
                    "local_capabilities", ["physical_transfer_ready"]
                ),
                lambda value: value.__setitem__(
                    "accepted_as_static_pose_bracketed_observation", True
                ),
                lambda value: value.__setitem__("physical_follower_commanded", True),
                lambda value: value.__setitem__(
                    "candidate_result_identity_sha256", "0" * 64
                ),
                lambda value: value.__setitem__("extra_field", "forged"),
                lambda value: value.pop("privacy"),
            )
            for mutate in mutations:
                changed = copy.deepcopy(manifest)
                mutate(changed)
                with self.assertRaises(ValueError):
                    verify_redacted_static_pose_live_session_review_manifest(
                        sign_payload(changed),
                        **self._arguments(),
                    )

    def test_writer_is_exclusive_scoped_and_independently_reread(self):
        with (
            self._patched_receipt_verifier(),
            tempfile.TemporaryDirectory() as directory,
        ):
            repo_root = Path(directory).resolve()
            output_directory = repo_root / "configurations/robot_lab"
            output_directory.mkdir(parents=True)
            output_path = output_directory / (
                f"pi05_static_pose_live_session_{SESSION_ID}.redacted.json"
            )
            manifest = build_redacted_static_pose_live_session_review_manifest(
                **self._arguments()
            )
            reference = write_redacted_static_pose_live_session_review_manifest(
                manifest,
                output_path=output_path,
                repo_root=repo_root,
                **self._arguments(),
            )
            self.assertEqual(
                reference["logical_path"],
                output_path.relative_to(repo_root).as_posix(),
            )
            self.assertEqual(reference["identity_sha256"], manifest["identity_sha256"])
            self.assertEqual(
                reference["file_sha256"],
                hashlib.sha256(output_path.read_bytes()).hexdigest(),
            )
            with self.assertRaisesRegex(ValueError, "new|exists|immutable"):
                write_redacted_static_pose_live_session_review_manifest(
                    manifest,
                    output_path=output_path,
                    repo_root=repo_root,
                    **self._arguments(),
                )

    def test_writer_rejects_escape_wrong_name_and_alias(self):
        with (
            self._patched_receipt_verifier(),
            tempfile.TemporaryDirectory() as directory,
        ):
            repo_root = Path(directory).resolve()
            configuration_root = repo_root / "configurations"
            robot_lab = configuration_root / "robot_lab"
            robot_lab.mkdir(parents=True)
            manifest = build_redacted_static_pose_live_session_review_manifest(
                **self._arguments()
            )
            for path in (
                repo_root / "escaped.redacted.json",
                robot_lab / "wrong-name.redacted.json",
                robot_lab / "../escaped.redacted.json",
            ):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    write_redacted_static_pose_live_session_review_manifest(
                        manifest,
                        output_path=path,
                        repo_root=repo_root,
                        **self._arguments(),
                    )

        with (
            self._patched_receipt_verifier(),
            tempfile.TemporaryDirectory() as directory,
        ):
            repo_root = Path(directory).resolve()
            configurations = repo_root / "configurations"
            real_robot_lab = repo_root / "real-robot-lab"
            configurations.mkdir()
            real_robot_lab.mkdir()
            (configurations / "robot_lab").symlink_to(
                real_robot_lab,
                target_is_directory=True,
            )
            output_path = configurations / "robot_lab" / (
                f"pi05_static_pose_live_session_{SESSION_ID}.redacted.json"
            )
            manifest = build_redacted_static_pose_live_session_review_manifest(
                **self._arguments()
            )
            with self.assertRaisesRegex(ValueError, "alias|symlink"):
                write_redacted_static_pose_live_session_review_manifest(
                    manifest,
                    output_path=output_path,
                    repo_root=repo_root,
                    **self._arguments(),
                )

    def test_writer_detects_corrupted_exclusive_write_without_retry(self):
        with (
            self._patched_receipt_verifier(),
            tempfile.TemporaryDirectory() as directory,
        ):
            repo_root = Path(directory).resolve()
            output_directory = repo_root / "configurations/robot_lab"
            output_directory.mkdir(parents=True)
            output_path = output_directory / (
                f"pi05_static_pose_live_session_{SESSION_ID}.redacted.json"
            )
            manifest = build_redacted_static_pose_live_session_review_manifest(
                **self._arguments()
            )

            def corrupt(path: Path, encoded: bytes) -> None:
                with path.open("xb") as stream:
                    stream.write(b"{}\n")

            with patch.object(
                review_module,
                "_write_exclusive_bytes",
                side_effect=corrupt,
            ) as writer, self.assertRaisesRegex(ValueError, "reread|content"):
                write_redacted_static_pose_live_session_review_manifest(
                    manifest,
                    output_path=output_path,
                    repo_root=repo_root,
                    **self._arguments(),
                )
            writer.assert_called_once()
            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
