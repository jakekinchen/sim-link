"""Tests for geometry-derived unilateral-jaw grasp proof."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.geometry_derived_unilateral_grasp import _invert_aperture_curve
from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact


class GeometryDerivedUnilateralGraspTests(unittest.TestCase):
    def test_checked_proof_is_two_pass_deterministic(self) -> None:
        payload = load_frozen_artifact("geometry_derived_unilateral_grasp")
        self.assertTrue(payload["two_pass_exact_determinism"])
        self.assertTrue(payload["geometry_derived_controls"])
        self.assertGreaterEqual(len(payload["trajectory"]["rendered_keyframes"]), 3)
        self.assertLessEqual(len(payload["trajectory"]["rendered_keyframes"]), 5)

    def test_authority_is_bounded(self) -> None:
        payload = load_frozen_artifact("geometry_derived_unilateral_grasp")
        cycle = payload["trajectory"]["full_lift_cycle"]
        self.assertTrue(payload["unassisted_mujoco_grasp_success"])
        self.assertTrue(payload["actual_mujoco_grasp_success"])
        self.assertEqual(cycle["strict_v2_valid_frame_counts"]["grasp_hold"], 8)
        self.assertEqual(cycle["strict_v2_valid_frame_counts"]["unassisted_lift"], 24)
        self.assertEqual(cycle["strict_v2_valid_frame_counts"]["unsupported_lift_hold"], 12)
        self.assertEqual(cycle["strict_v2_valid_frame_counts"]["lower"], 24)
        self.assertEqual(cycle["unsupported_lift_hold_frame_count"], 12)
        self.assertEqual(cycle["active_assist_frame_count"], 0)
        self.assertEqual(payload["trajectory"]["nonpad_robot_object_contact_frame_count"], 0)
        self.assertTrue(payload["derivation"]["clearance_opposes_fixed_to_moving_axis"])
        self.assertTrue(cycle["retreat_final_contact_clear"])
        self.assertFalse(payload["simulation_training_ready"])
        self.assertFalse(payload["hardware_accessed"])
        self.assertFalse(payload["physical_follower_commanded"])

    def test_aperture_curve_inversion_is_linear(self) -> None:
        samples = [
            {"separation_m": 0.02, "gripper_qpos_rad": 0.1},
            {"separation_m": 0.04, "gripper_qpos_rad": 0.3},
        ]
        self.assertAlmostEqual(_invert_aperture_curve(samples, 0.03), 0.2)

    def test_aperture_curve_inversion_fails_closed(self) -> None:
        invalid_cases = (
            ([], 0.03),
            ([{"separation_m": 0.02, "gripper_qpos_rad": 0.1}], 0.02),
            ([{"separation_m": 0.02, "gripper_qpos_rad": 0.1}, {"separation_m": 0.02, "gripper_qpos_rad": 0.2}], 0.02),
            ([{"separation_m": 0.02, "gripper_qpos_rad": 0.1}, {"separation_m": 0.04, "gripper_qpos_rad": 0.3}], float("nan")),
        )
        for samples, target in invalid_cases:
            with self.subTest(samples=samples, target=target):
                with self.assertRaises(ValueError):
                    _invert_aperture_curve(samples, target)


if __name__ == "__main__":
    unittest.main()
