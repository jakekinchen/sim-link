"""Tests for principal-axis-aligned grasp search."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.principal_axis_grasp_search import (
    REPO_ROOT,
    build_principal_axis_grasp_search,
    verify_principal_axis_grasp_search,
)


ARTIFACT = REPO_ROOT / "configurations/robot_lab/principal_axis_grasp_search.json"


class PrincipalAxisGraspSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_isolated(self) -> None:
        payload = load_strict_json(ARTIFACT)
        verify_principal_axis_grasp_search(payload)
        self.assertEqual(payload, build_principal_axis_grasp_search())
        self.assertTrue(payload["contact_physics_unchanged"])
        self.assertTrue(payload["candidate_inputs_except_wrist_roll_unchanged"])

    def test_alignment_and_authority_fail_closed(self) -> None:
        payload = load_strict_json(ARTIFACT)
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
