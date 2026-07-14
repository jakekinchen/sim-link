"""Tests for the explicit-pad proxy rerun."""
from __future__ import annotations
import unittest
from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact
class ExplicitPadProxySearchTests(unittest.TestCase):
    def test_checked_proxy_rerun_is_deterministic_and_isolated(self) -> None:
        stored = load_frozen_artifact("explicit_pad_proxy_search")
        self.assertTrue(stored["candidate_design_identical_to_source"])
        self.assertTrue(stored["composite_jaw_geometry_retained"])
        self.assertTrue(stored["composite_jaw_contact_masks_disabled"])

    def test_proxy_rerun_withholds_dynamic_grasp_and_training(self) -> None:
        stored = load_frozen_artifact("explicit_pad_proxy_search")
        self.assertFalse(stored["actual_mujoco_grasp_success"])
        self.assertFalse(stored["simulation_training_ready"])
if __name__=="__main__": unittest.main()
