"""Tests for the bounded geometry-first grasp search."""
from __future__ import annotations
import unittest
from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.geometry_first_grasp_search import REPO_ROOT, build_geometry_first_grasp_search, verify_geometry_first_grasp_search
ARTIFACT = REPO_ROOT / "configurations/robot_lab/geometry_first_grasp_search.json"
class GeometryFirstGraspSearchTests(unittest.TestCase):
    def test_checked_search_is_deterministic_and_holdout_is_isolated(self) -> None:
        stored = load_strict_json(ARTIFACT); verify_geometry_first_grasp_search(stored)
        self.assertEqual(stored, build_geometry_first_grasp_search())
        self.assertEqual(stored["training_candidate_count"], 12)
        self.assertTrue(stored["holdout"]["excluded_from_selection"])
        self.assertFalse(stored["friction_or_compliance_tuned"])
    def test_search_withholds_dynamic_grasp_and_training(self) -> None:
        stored = load_strict_json(ARTIFACT)
        self.assertFalse(stored["actual_mujoco_grasp_success"])
        self.assertFalse(stored["simulation_training_ready"])
if __name__ == "__main__": unittest.main()
