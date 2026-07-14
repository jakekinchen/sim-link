"""Tests for the post-yaw-settle grasp search."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact


class PostYawSettleSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_isolated(self) -> None:
        payload = load_frozen_artifact("post_yaw_settle_search")
        self.assertTrue(payload["candidate_design_identical_to_source"])
        self.assertTrue(payload["contact_physics_unchanged"])
        self.assertEqual(payload["post_yaw_settle_seconds"], 0.25)

    def test_motion_channels_and_authority_are_separate(self) -> None:
        payload = load_frozen_artifact("post_yaw_settle_search")
        for candidate in payload["candidates"]:
            if candidate.get("setup_valid"):
                self.assertIn("passive_settle_displacement_m", candidate)
                self.assertIn("preclose_object_displacement_m", candidate)
        self.assertFalse(payload["actual_mujoco_grasp_success"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
