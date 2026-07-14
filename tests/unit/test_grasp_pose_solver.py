"""Tests for fixed-wrist grasp IK and object yaw."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.grasp_pose_solver import (
    APPROACH_MOTION_LIMIT_M,
    REPO_ROOT,
    POSITION_TOLERANCE_M,
    build_grasp_pose_solver_fixture,
    verify_grasp_pose_solver_fixture,
)


ARTIFACT = REPO_ROOT / "configurations/robot_lab/grasp_pose_solver.fixture.json"


class GraspPoseSolverTests(unittest.TestCase):
    def test_approach_motion_uses_pad_midpoint_ik_tolerance(self) -> None:
        self.assertEqual(APPROACH_MOTION_LIMIT_M, POSITION_TOLERANCE_M)
        self.assertEqual(APPROACH_MOTION_LIMIT_M, 0.001)

    def test_checked_fixture_is_deterministic_and_achieves_every_request(self) -> None:
        stored = load_strict_json(ARTIFACT)
        verify_grasp_pose_solver_fixture(stored)
        self.assertEqual(stored, build_grasp_pose_solver_fixture())
        self.assertEqual(stored["accepted_candidate_count"], stored["candidate_count"])
        for candidate in stored["candidates"]:
            self.assertLessEqual(candidate["position_residual_m"], stored["position_tolerance_m"])
            self.assertAlmostEqual(candidate["requested_wrist_flex_rad"], candidate["achieved_wrist_flex_rad"])
            self.assertAlmostEqual(candidate["requested_wrist_roll_rad"], candidate["achieved_wrist_roll_rad"])
            self.assertAlmostEqual(candidate["requested_object_yaw_rad"], candidate["achieved_object_yaw_rad"])
            self.assertEqual(len(candidate["requested_approach_axis_world"]), 3)
            self.assertEqual(len(candidate["achieved_approach_axis_world"]), 3)
            self.assertEqual(len(candidate["requested_closing_axis_world"]), 3)
            self.assertEqual(len(candidate["achieved_closing_axis_world"]), 3)
            self.assertFalse(candidate["initial_forbidden_self_collision_pairs"])
            self.assertFalse(candidate["forbidden_self_collision_pairs"])

    def test_fixture_withholds_search_contact_grasp_and_training(self) -> None:
        stored = load_strict_json(ARTIFACT)
        self.assertFalse(stored["orientation_search_executed"])
        self.assertFalse(stored["contact_simulation_executed"])
        self.assertFalse(stored["actual_mujoco_grasp_success"])
        self.assertFalse(stored["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
