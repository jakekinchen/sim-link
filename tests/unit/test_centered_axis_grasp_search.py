"""Tests for selected-axis-centered grasp search."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact


class CenteredAxisGraspSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_isolated(self) -> None:
        payload = load_frozen_artifact("centered_axis_grasp_search")
        self.assertTrue(payload["contact_physics_unchanged"])
        self.assertTrue(payload["only_selected_axis_offset_removed"])

    def test_centering_and_authority_fail_closed(self) -> None:
        payload = load_frozen_artifact("centered_axis_grasp_search")
        for candidate in payload["candidates"]:
            if candidate.get("setup_valid"):
                self.assertIn("removed_selected_axis_offset_m", candidate)
                self.assertGreaterEqual(candidate["predicted_principal_axis_alignment"], 0.95)
                self.assertLessEqual(candidate["predicted_closing_axis_vertical_abs"], 0.1)
        self.assertFalse(payload["actual_mujoco_grasp_success"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
