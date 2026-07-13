"""Tests for pad-midpoint targeting search."""
from __future__ import annotations
import unittest
from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.pad_midpoint_search import REPO_ROOT,build_pad_midpoint_search,verify_pad_midpoint_search
ARTIFACT=REPO_ROOT/"configurations/robot_lab/pad_midpoint_search.json"
class PadMidpointSearchTests(unittest.TestCase):
 def test_checked_search_is_deterministic_and_isolated(self)->None:
  x=load_strict_json(ARTIFACT);verify_pad_midpoint_search(x);self.assertEqual(x,build_pad_midpoint_search());self.assertTrue(x["candidate_design_identical_to_source"]);self.assertTrue(x["contact_physics_unchanged"])
 def test_withholds_dynamic_grasp_and_training(self)->None:
  x=load_strict_json(ARTIFACT);self.assertFalse(x["actual_mujoco_grasp_success"]);self.assertFalse(x["simulation_training_ready"])
if __name__=="__main__":unittest.main()
