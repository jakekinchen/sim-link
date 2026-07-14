"""Tests for pad-midpoint targeting search."""
from __future__ import annotations
import unittest
from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact
class PadMidpointSearchTests(unittest.TestCase):
 def test_checked_search_is_deterministic_and_isolated(self)->None:
  x=load_frozen_artifact("pad_midpoint_search");self.assertTrue(x["candidate_design_identical_to_source"]);self.assertTrue(x["contact_physics_unchanged"])
 def test_withholds_dynamic_grasp_and_training(self)->None:
  x=load_frozen_artifact("pad_midpoint_search");self.assertFalse(x["actual_mujoco_grasp_success"]);self.assertFalse(x["simulation_training_ready"])
if __name__=="__main__":unittest.main()
