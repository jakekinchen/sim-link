"""Tests for the finite low-impact two-jaw MuJoCo search."""

from __future__ import annotations

import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.mujoco_grasp_contact_search import (
    build_mujoco_grasp_contact_search,
    verify_mujoco_grasp_contact_search,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "configurations/robot_lab/mujoco_grasp_contact_search.json"


class MujocoGraspContactSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_finds_low_impact_contact(self) -> None:
        payload = load_strict_json(ARTIFACT)

        verify_mujoco_grasp_contact_search(payload)
        self.assertEqual(payload, build_mujoco_grasp_contact_search())
        selected = payload["selected_candidate"]
        self.assertLessEqual(selected["maximum_contact_force_n"], 5.0)
        self.assertGreater(selected["close_two_jaw_frames"], 0)
        self.assertEqual(selected["hold_two_jaw_frames"], 8)
        self.assertTrue(payload["selected_validation_two_pass_exact_determinism"])
        self.assertEqual(
            payload["source_anchor_attempt_identity_sha256"],
            "32f14feba6c10e501082c0438ee4b0cd80ee530d4c143468b5af20f5ad29626e",
        )
        self.assertFalse(payload["physical_measurement_claimed"])

    def test_unassisted_lift_is_truthfully_rejected(self) -> None:
        payload = load_strict_json(ARTIFACT)
        validation = payload["selected_unassisted_validation"]

        self.assertFalse(validation["contact_gated_assist_ever_active"])
        self.assertFalse(validation["summary"]["unassisted_lift_clearance_maintained"])
        self.assertEqual(validation["summary"]["lift_hold_two_jaw_frames"], 0)
        self.assertFalse(payload["metric_gripper_aperture_profile_complete"])
        self.assertFalse(payload["unassisted_mujoco_grasp_success"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
