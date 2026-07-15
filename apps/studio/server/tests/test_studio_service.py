from __future__ import annotations

import base64
import json
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
        self._text("docs/reviewer-messages/002-new.md", "new")
        self._text("docs/briefs/003-brief.md", "brief")
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
        self.assertEqual(document["content"], "brief")
        self.assertEqual(document["filename"], "003-brief.md")

        cases = (
            ("session-logs", "003-brief.md", 404),
            ("briefs", "../003-brief.md", 400),
            ("briefs", "/tmp/003-brief.md", 400),
            ("briefs", "003-missing.md", 404),
        )
        for kind, filename, expected_status in cases:
            with self.subTest(kind=kind, filename=filename):
                with self.assertRaises(StudioServiceError) as caught:
                    self.service.document(kind, filename)
                self.assertEqual(caught.exception.status_code, expected_status)


if __name__ == "__main__":
    unittest.main()
