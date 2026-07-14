"""Tests for the finite low-impact two-jaw MuJoCo search."""

from __future__ import annotations

import unittest

from pathlib import Path

from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact


class MujocoGraspContactSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_finds_low_impact_contact(self) -> None:
        payload = load_frozen_artifact("mujoco_grasp_contact_search")
        selected = payload["selected_candidate"]
        self.assertLessEqual(selected["maximum_contact_force_n"], 5.0)
        self.assertGreater(selected["close_two_jaw_frames"], 0)
        self.assertEqual(selected["hold_two_jaw_frames"], 8)
        self.assertTrue(payload["selected_validation_two_pass_exact_determinism"])
        self.assertEqual(
            len(payload["selected_unassisted_validation"]["summary"]["rendered_keyframes"]),
            4,
        )
        self.assertEqual(
            payload["source_anchor_attempt_identity_sha256"],
            "f880cc5318d87a1da9bc6dfc65ce8afb1f4a9152414b2ef9e099726d9fb795cf",
        )
        self.assertFalse(payload["physical_measurement_claimed"])

    def test_unassisted_lift_is_truthfully_rejected(self) -> None:
        payload = load_frozen_artifact("mujoco_grasp_contact_search")
        validation = payload["selected_unassisted_validation"]

        self.assertFalse(validation["contact_gated_assist_ever_active"])
        self.assertFalse(validation["summary"]["unassisted_lift_clearance_maintained"])
        self.assertEqual(validation["summary"]["lift_hold_two_jaw_frames"], 0)
        self.assertFalse(payload["metric_gripper_aperture_profile_complete"])
        self.assertFalse(payload["unassisted_mujoco_grasp_success"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
