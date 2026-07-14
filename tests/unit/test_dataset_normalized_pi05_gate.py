import unittest

from scenesmith.robot_lab.dataset_normalized_pi05_gate import (
    derive_action_error_effect,
)
from scenesmith.robot_lab.experience_records import JOINT_NAMES


class DatasetNormalizedPi05GateTest(unittest.TestCase):
    def test_gripper_improvement_and_broad_arm_regression_are_separate(self) -> None:
        baseline = self._diagnostics([0.01] * 5, 0.75)
        candidate = self._diagnostics([0.7] * 5, 0.24)
        result = derive_action_error_effect(baseline, candidate)
        self.assertTrue(result["gripper_improved"])
        self.assertAlmostEqual(result["gripper_error_improvement_rad"], 0.51)
        self.assertTrue(result["non_gripper_regressed"])
        self.assertAlmostEqual(result["non_gripper_error_ratio"], 70.0)

    def test_missing_or_nonfinite_joint_error_rejects(self) -> None:
        baseline = self._diagnostics([0.01] * 5, 0.75)
        candidate = self._diagnostics([0.7] * 5, 0.24)
        del candidate["initial_action_absolute_error_rad"]["wrist_roll"]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            derive_action_error_effect(baseline, candidate)
        candidate = self._diagnostics([0.7] * 5, 0.24)
        candidate["initial_gripper_absolute_error_rad"] = float("nan")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            derive_action_error_effect(baseline, candidate)

    @staticmethod
    def _diagnostics(arm: list[float], gripper: float) -> dict:
        return {
            "initial_action_absolute_error_rad": {
                name: value
                for name, value in zip(
                    JOINT_NAMES, [*arm, gripper], strict=True
                )
            },
            "initial_gripper_absolute_error_rad": gripper,
            "dominant_initial_error_joint": "wrist_roll",
        }


if __name__ == "__main__":
    unittest.main()
