"""Tests for the explicit-pad proxy rerun."""
from __future__ import annotations
import unittest
from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.explicit_pad_proxy_search import REPO_ROOT, build_explicit_pad_proxy_search, verify_explicit_pad_proxy_search
ARTIFACT=REPO_ROOT/"configurations/robot_lab/explicit_pad_proxy_search.json"
class ExplicitPadProxySearchTests(unittest.TestCase):
    def test_checked_proxy_rerun_is_deterministic_and_isolated(self)->None:
        stored=load_strict_json(ARTIFACT); verify_explicit_pad_proxy_search(stored); self.assertEqual(stored,build_explicit_pad_proxy_search())
        self.assertTrue(stored["candidate_design_identical_to_source"]); self.assertTrue(stored["composite_jaw_geometry_retained"]); self.assertTrue(stored["composite_jaw_contact_masks_disabled"])
    def test_proxy_rerun_withholds_dynamic_grasp_and_training(self)->None:
        stored=load_strict_json(ARTIFACT); self.assertFalse(stored["actual_mujoco_grasp_success"]); self.assertFalse(stored["simulation_training_ready"])
if __name__=="__main__": unittest.main()
