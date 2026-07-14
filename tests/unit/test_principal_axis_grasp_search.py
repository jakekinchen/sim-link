"""Tests for principal-axis-aligned grasp search."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact


class PrincipalAxisGraspSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_isolated(self) -> None:
        payload = load_frozen_artifact("principal_axis_grasp_search")
        self.assertTrue(payload["contact_physics_unchanged"])
        self.assertTrue(payload["candidate_inputs_except_wrist_roll_unchanged"])

    def test_alignment_and_authority_fail_closed(self) -> None:
        payload = load_frozen_artifact("principal_axis_grasp_search")
        measured_alignment_failure = False
        for candidate in payload["candidates"]:
            if candidate.get("setup_valid"):
                self.assertGreaterEqual(
                    candidate["predicted_principal_axis_alignment"], 0.8
                )
            if "gate_margins" in candidate:
                margin = candidate["gate_margins"].get("principal_axis_alignment")
                if margin is not None:
                    self.assertEqual(margin["threshold"], 0.8)
                    self.assertIn("principal_axis_alignment", {
                        failure["gate"]
                        for failure in candidate["failed_gate_margins"]
                    })
                    measured_alignment_failure |= margin["measured"] is not None
        self.assertTrue(measured_alignment_failure)
        self.assertFalse(payload["actual_mujoco_grasp_success"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
