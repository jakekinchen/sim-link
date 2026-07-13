"""Tests for best-principal-axis grasp search."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.best_axis_grasp_search import (
    REPO_ROOT,
    build_best_axis_grasp_search,
    verify_best_axis_grasp_search,
)


ARTIFACT = REPO_ROOT / "configurations/robot_lab/best_axis_grasp_search.json"


class BestAxisGraspSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_isolated(self) -> None:
        payload = load_strict_json(ARTIFACT)
        verify_best_axis_grasp_search(payload)
        self.assertEqual(payload, build_best_axis_grasp_search())
        self.assertTrue(payload["contact_physics_unchanged"])
        self.assertTrue(payload["candidate_inputs_except_wrist_pose_unchanged"])

    def test_selected_axes_and_authority_fail_closed(self) -> None:
        payload = load_strict_json(ARTIFACT)
        for candidate in payload["candidates"]:
            if candidate.get("setup_valid"):
                self.assertIn(candidate["selected_object_principal_axis"], ("x", "y"))
                self.assertGreaterEqual(candidate["predicted_principal_axis_alignment"], 0.95)
                self.assertLessEqual(candidate["predicted_closing_axis_vertical_abs"], 0.1)
        self.assertFalse(payload["actual_mujoco_grasp_success"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
