"""Tests for the deterministic nominal-anchor MuJoCo grasp attempt."""

from __future__ import annotations

import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.mujoco_anchor_grasp import (
    build_mujoco_anchor_grasp_attempt,
    verify_mujoco_anchor_grasp_attempt,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "configurations/robot_lab/mujoco_anchor_grasp_attempt.json"


class MujocoAnchorGraspTests(unittest.TestCase):
    def test_checked_attempt_is_deterministic_and_truthfully_rejected(self) -> None:
        payload = load_strict_json(ARTIFACT)

        verify_mujoco_anchor_grasp_attempt(payload)
        self.assertEqual(payload, build_mujoco_anchor_grasp_attempt())
        self.assertEqual(payload["mujoco_report"]["status"], "pass")
        self.assertTrue(payload["mujoco_report"]["all_grasps_contact_gated"])
        evaluation = payload["strict_evaluation"]
        self.assertFalse(evaluation["strict_grasp_success"])
        self.assertFalse(evaluation["pure_policy_success"])
        self.assertIn(
            "actuator_current_measurement_missing",
            evaluation["failure_reasons"],
        )
        self.assertIn(
            "gripper_aperture_measurement_missing",
            evaluation["failure_reasons"],
        )

    def test_attempt_preserves_source_and_authority_boundaries(self) -> None:
        payload = load_strict_json(ARTIFACT)

        self.assertEqual(payload["anchor_dimensions_m"], [0.05, 0.035, 0.03])
        self.assertEqual(payload["anchor_mass_kg"], 0.025)
        self.assertFalse(payload["physical_measurement_claimed"])
        self.assertGreater(payload["raw_frame_count"], 0)
        self.assertEqual(payload["raw_frame_count"], len(payload["raw_frames"]))
        self.assertTrue(any(frame["grasp_assists_active"] for frame in payload["raw_frames"]))
        self.assertFalse(payload["unassisted_mujoco_grasp_success"])
        self.assertFalse(payload["physical_twin_qualified"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
