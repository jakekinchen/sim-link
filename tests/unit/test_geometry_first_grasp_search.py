"""Tests for the bounded geometry-first grasp search."""
from __future__ import annotations
import unittest
from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact
class GeometryFirstGraspSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_holdout_is_isolated(self) -> None:
        stored = load_frozen_artifact("geometry_first_grasp_search")
        self.assertEqual(stored["training_candidate_count"], 12)
        self.assertTrue(stored["holdout"]["excluded_from_selection"])
        self.assertFalse(stored["friction_or_compliance_tuned"])
        self.assertEqual(stored["search_status"], "retired_degenerate_design")
        self.assertGreaterEqual(
            stored["reuse_requirements"]["minimum_candidate_count"],
            5 * stored["reuse_requirements"]["largest_halton_base"],
        )
        self.assertTrue(stored["reuse_requirements"]["vertical_band_must_be_rederived"])
        for candidate in stored["candidates"]:
            if candidate.get("setup_valid"):
                self.assertIn("normal_alignment", candidate["gate_margins"])
                self.assertIn("failed_gate_margins", candidate)
    def test_search_withholds_dynamic_grasp_and_training(self) -> None:
        stored = load_frozen_artifact("geometry_first_grasp_search")
        self.assertFalse(stored["actual_mujoco_grasp_success"])
        self.assertFalse(stored["simulation_training_ready"])
if __name__ == "__main__": unittest.main()
