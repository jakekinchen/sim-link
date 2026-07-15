from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import unittest

from pathlib import Path

from studio_service import StudioService, StudioServiceError


class StudioServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self._write(
            "docs/autonomous-workflow/project_state.json",
            {
                "run_window": {"simulation_only": True},
                "current_task": "T-test",
                "current_milestone": "test milestone",
                "latest_verified_task_implementation_boundary": {"commit": "abc123"},
            },
        )
        ledger = self.root / "docs/autonomous-workflow/experience-compiler-twin-task-ledger.md"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text("```text\ntraining_lock: closed\nrun_state: fixture\n```\n")
        self._text("docs/reviewer-messages/001-old.md", "old")
        self._text(
            "docs/reviewer-messages/002-new.md",
            "# Reviewer Decision 002 - Verify Fixture\n\n**Decision:** `PASS`\n",
        )
        self._text("docs/briefs/003-brief.md", "# Brief 003 - Fixture Slice\n")
        self._text("docs/session-logs/004-run.md", "# Session Log 004 - Fixture Run\n")
        self._text(
            "docs/manager-log/005-intervention.md",
            "# Manager Intervention 005 - Hold Fixture\n\n"
            "**Date:** 2026-07-15\n\n## Decision\n\n`HOLD`\n",
        )
        for observed, relative_path in enumerate(
            (
                "docs/reviewer-messages/001-old.md",
                "docs/reviewer-messages/002-new.md",
                "docs/briefs/003-brief.md",
                "docs/session-logs/004-run.md",
                "docs/manager-log/005-intervention.md",
            ),
            start=1,
        ):
            os.utime(self.root / relative_path, (observed, observed))
        self._write(
            "outputs/robot_lab/t17_5b_raw_store/expert_a.json",
            {
                "episode_spec": {"seed": 7},
                "outcome": {"strict_success": True},
                "frames": [
                    {
                        "frame_index": 0,
                        "task_phase": "approach",
                        "control_mode": "scripted",
                        "observations": {
                            "top": {
                                "encoding": "png",
                                "png_base64": base64.b64encode(b"fixture-png").decode(),
                            }
                        },
                    }
                ],
            },
        )
        self._write(
            "outputs/robot_lab/t20_32_closed_loop_divergence/trace_a.json",
            {
                "adapter_id": "adapter-a",
                "seed": 9,
                "closed_loop": {"frame_count": 1, "maximum_anchor_lift_m": 0.01},
                "comparisons": [
                    {
                        "frame_index": 0,
                        "phase": "lift",
                        "candidate_strict_contact": True,
                        "candidate_anchor_position_m": [0.1, 0.2, 0.3],
                    }
                ],
            },
        )
        self._text("outputs/robot_lab/rollout_mirror/trace_a.mp4", "mirror")
        preview = self.root / "outputs/robot_lab/workcells/cell_a/preview.png"
        preview.parent.mkdir(parents=True, exist_ok=True)
        preview.write_bytes(b"png")
        self._write(
            "outputs/robot_lab/workcells/cell_a/build_manifest.json",
            {
                "scene_id": "cell_a",
                "all_cubes_stable": True,
                "previews": {"cam0_side": str(preview)},
            },
        )
        self._write(
            "configurations/robot_lab/t20_fixture_result_gate.json",
            {
                "schema_version": "fixture.result.v1",
                "decision": "hold",
                "final_to_baseline_objective_ratio": 0.25,
            },
        )
        self._write(
            "configurations/robot_lab/pi05_live_readonly_observation.redacted.json",
            {
                "schema_version": "scenesmith.live_readonly_observation_manifest.v5",
                "identity_sha256": "a" * 64,
                "manifest_name": "fixture_live_observation",
                "session_id": "session-fixture",
                "evidence_mode": "tracked_redacted_physical_read_only_manifest",
                "qualification_scope": "physical_observation",
                "proof_labels": ["live_read_only_census_observed"],
                "discovery_stability": "stable",
                "hardware_opened": True,
                "physical_follower_commanded": False,
                "pre_open_discovery_identity_sha256": "pre-hash",
                "post_close_discovery_identity_sha256": "post-hash",
                "privacy": {"raw_device_path_included": False},
                "camera_operation_counts": {"capture_property_writes": 0},
                "cameras": [
                    {
                        "stable_camera_identity_sha256": "camera-hash",
                        "capture_camera_identity_sha256": "capture-hash",
                        "input_mode": {"width": 640, "height": 480},
                        "frames": [{"frame_index": 0}],
                    }
                ],
                "servo_identity": [
                    {
                        "servo_id": 1,
                        "joint_name": "shoulder_pan",
                        "model": "sts3215",
                        "model_number": 777,
                        "firmware_version": "3.9",
                    }
                ],
                "operation_counts": {"read_successes": 9, "motion_commands": 0},
            },
        )
        self._write(
            "configurations/robot_lab/pi05_readonly_servo_census_contract.fixture.json",
            {
                "schema_version": "scenesmith.readonly_servo_census_contract.v3",
                "identity_sha256": "b" * 64,
                "contract_name": "fixture_contract",
                "proof_label": "census_trace_conformant",
                "qualification_scope": "fixture_evidence",
                "expected_servos": [{"servo_id": 1}],
                "forbidden_operations": ["write", "motion"],
            },
        )
        self._write(
            "configurations/robot_lab/pi05_calibration_profile.json",
            {
                "schema_version": "scenesmith.calibration_profile.v1",
                "identity_sha256": "c" * 64,
                "profile_name": "fixture_calibration",
                "evidence_mode": "offline_semantic_validation",
                "qualification_scope": "local_calibration_semantics",
                "joint_count": 1,
                "joints": [
                    {
                        "servo_id": 1,
                        "joint_name": "shoulder_pan",
                        "model": "sts3215",
                        "firmware_version": "3.9",
                        "drive_mode": 0,
                        "homing_offset": 10,
                        "range_min": 100,
                        "range_max": 3000,
                        "normalization": {"mode": "degrees"},
                    }
                ],
                "normalization_contract": {"body_mode": "degrees"},
                "accepted_live_manifest": {
                    "file_sha256": hashlib.sha256(
                        (
                            self.root
                            / "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
                        ).read_bytes()
                    ).hexdigest(),
                    "identity_sha256": "a" * 64,
                },
                "hardware_accessed": False,
                "physical_follower_commanded": False,
                "motion_authority_granted": False,
                "training_authority_granted": False,
                "authority_not_granted": ["physical_transfer_ready"],
            },
        )
        self.service = StudioService(self.root)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write(self, relative_path: str, payload: dict[str, object]) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def _text(self, relative_path: str, body: str) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    def test_registry_reads_signed_artifact_shapes(self) -> None:
        status = self.service.status()
        self.assertEqual(status["current_task"], "T-test")
        self.assertEqual(status["ledger"]["training_lock"], "closed")
        self.assertEqual(status["recent_reviewer_decisions"][0], "002-new.md")
        self.assertEqual(status["recent_session_logs"][0], "004-run.md")
        self.assertEqual(
            status["recent_manager_interventions"][0], "005-intervention.md"
        )

        episode_registry = self.service.episodes()
        self.assertEqual(episode_registry["count"], 2)
        self.assertEqual(
            {episode["source"] for episode in episode_registry["episodes"]},
            {"expert", "policy_trace"},
        )
        self.assertEqual(
            self.service.episode_detail("trace/trace_a")["timeline"][0]["anchor_z_m"],
            0.3,
        )
        self.assertEqual(
            self.service.episode_frame("expert/expert_a", 0, "top"),
            b"fixture-png",
        )

        workcell_registry = self.service.workcells()
        self.assertEqual(workcell_registry["count"], 1)
        self.assertEqual(
            workcell_registry["workcells"][0]["previews"]["cam0_side"],
            "outputs/robot_lab/workcells/cell_a/preview.png",
        )
        self.assertEqual(
            self.service.tasks()["result_gates"][0]["final_to_baseline_objective_ratio"],
            0.25,
        )

        robot = self.service.robot()
        self.assertEqual(robot["mode"], "signed_artifacts_read_only")
        self.assertFalse(robot["registration"]["enabled"])
        self.assertEqual(robot["discovery"]["cameras"][0]["frame_count"], 1)
        self.assertEqual(robot["census"]["servos"][0]["joint_name"], "shoulder_pan")
        self.assertEqual(robot["census"]["contract"]["qualification_scope"], "fixture_evidence")
        self.assertEqual(robot["calibration"]["joints"][0]["normalization_mode"], "degrees")
        self.assertFalse(robot["calibration"]["motion_authority_granted"])

    def test_robot_registry_requires_fixed_signed_artifacts(self) -> None:
        self.service.robot_artifacts["calibration_profile"].unlink()
        with self.assertRaises(StudioServiceError) as caught:
            self.service.robot()
        self.assertEqual(caught.exception.status_code, 503)

    def test_robot_registry_rejects_stale_calibration_binding(self) -> None:
        path = self.service.robot_artifacts["calibration_profile"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["accepted_live_manifest"]["file_sha256"] = "0" * 64
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(StudioServiceError) as caught:
            self.service.robot()
        self.assertEqual(caught.exception.status_code, 503)

    def test_path_and_action_inputs_fail_closed(self) -> None:
        cases = (
            (lambda: self.service.episode_detail("expert/../escape"), 400),
            (lambda: self.service.episode_frame("trace/trace_a", 0, "top"), 404),
            (lambda: self.service.media_path("../../etc/passwd"), 404),
            (lambda: self.service.build_workcell({"scene_id": "bad id"}), 400),
            (lambda: self.service.render_mirror({"trace": "../trace_a.json"}), 400),
        )
        for operation, expected_status in cases:
            with self.subTest(expected_status=expected_status):
                with self.assertRaises(StudioServiceError) as caught:
                    operation()
                self.assertEqual(caught.exception.status_code, expected_status)

    def test_document_lookup_is_filename_only_and_whitelisted(self) -> None:
        document = self.service.document("briefs", "003-brief.md")
        self.assertEqual(document["content"], "# Brief 003 - Fixture Slice\n")
        self.assertEqual(document["filename"], "003-brief.md")
        self.assertEqual(document["source"], "docs/briefs/003-brief.md")
        self.assertEqual(len(document["sha256"]), 64)

        session_log = self.service.document("session-logs", "004-run.md")
        self.assertEqual(session_log["kind"], "session-logs")

        cases = (
            ("unknown", "003-brief.md", 404),
            ("briefs", "../003-brief.md", 400),
            ("briefs", "/tmp/003-brief.md", 400),
            ("briefs", "003-missing.md", 404),
        )
        for kind, filename, expected_status in cases:
            with self.subTest(kind=kind, filename=filename):
                with self.assertRaises(StudioServiceError) as caught:
                    self.service.document(kind, filename)
                self.assertEqual(caught.exception.status_code, expected_status)

    def test_event_registry_is_bounded_source_faithful_and_fail_closed(self) -> None:
        registry = self.service.events(limit=2)
        self.assertEqual(registry["total"], 5)
        self.assertEqual(registry["count"], 2)
        self.assertEqual(
            registry["time_basis"],
            "filesystem_mtime_observation_not_evidence_time",
        )
        self.assertEqual(
            [event["kind"] for event in registry["events"]],
            ["manager-log", "session-logs"],
        )
        manager = registry["events"][0]
        self.assertEqual(
            manager["title"], "Manager Intervention 005 - Hold Fixture"
        )
        self.assertEqual(manager["decision"], "HOLD")
        self.assertEqual(manager["recorded_date"], "2026-07-15")
        self.assertEqual(manager["source"], "docs/manager-log/005-intervention.md")
        self.assertEqual(len(manager["sha256"]), 64)

        secret = self.root / "secret.md"
        secret.write_text("outside whitelist", encoding="utf-8")
        leak = self.root / "docs/briefs/006-leak.md"
        leak.symlink_to(secret)
        with self.assertRaises(StudioServiceError) as caught:
            self.service.document("briefs", "006-leak.md")
        self.assertEqual(caught.exception.status_code, 404)
        self.assertNotIn(
            "briefs/006-leak.md",
            {event["id"] for event in self.service.events()["events"]},
        )

        for invalid_limit in (0, 501, True):
            with self.subTest(limit=invalid_limit):
                with self.assertRaises(StudioServiceError) as caught:
                    self.service.events(invalid_limit)
                self.assertEqual(caught.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
