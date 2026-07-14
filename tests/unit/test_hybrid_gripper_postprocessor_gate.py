import unittest

from scenesmith.robot_lab.hybrid_gripper_postprocessor_gate import (
    derive_hybrid_finding,
)


class HybridGripperPostprocessorGateTest(unittest.TestCase):
    def test_negative_unclipped_rollout_selects_clean_base(self) -> None:
        result = derive_hybrid_finding(
            {"clipped_or_projected_call_count": 0},
            {"simulation_semantic_strict_success": False},
        )
        self.assertTrue(result["hybrid_gripper_postprocessor_retired"])
        self.assertFalse(result["coordinate_clipping_caused_failure"])
        self.assertIn("clean_pi05_base", result["selected_next_hypothesis"])

    def test_clipping_preempts_model_hypothesis(self) -> None:
        result = derive_hybrid_finding(
            {"clipped_or_projected_call_count": 2},
            {"simulation_semantic_strict_success": False},
        )
        self.assertFalse(result["hybrid_gripper_postprocessor_retired"])
        self.assertTrue(result["coordinate_clipping_caused_failure"])
        self.assertIn("clipping", result["selected_next_hypothesis"])


if __name__ == "__main__":
    unittest.main()
