import copy
import unittest

from scenesmith.robot_lab.action_localization_gate import derive_next_hypothesis
from scenesmith.robot_lab.model_bakeoff import MODEL_ORDER


class ActionLocalizationGateTest(unittest.TestCase):
    def test_pi05_gripper_hypothesis_requires_small_arm_and_large_gripper_error(self) -> None:
        rows = self._rows()
        result = derive_next_hypothesis(rows)
        self.assertTrue(result["hypothesis_selected"])
        self.assertEqual(
            result["hypothesis_id"], "pi05_gripper_channel_semantics_or_weighting"
        )
        self.assertEqual(result["diagnostic_model_id"], "pi05")
        self.assertGreater(result["pi05_non_gripper_margin_rad"], 0.0)
        self.assertGreater(result["pi05_gripper_error_margin_rad"], 0.0)

    def test_broad_pi05_arm_error_rejects_single_channel_hypothesis(self) -> None:
        rows = self._rows()
        next(row for row in rows if row["model_id"] == "pi05")[
            "initial_non_gripper_mean_absolute_error_rad"
        ] = 0.2
        result = derive_next_hypothesis(rows)
        self.assertFalse(result["hypothesis_selected"])
        self.assertIsNone(result["diagnostic_model_id"])

    @staticmethod
    def _rows():
        return [
            {
                "model_id": model_id,
                "initial_non_gripper_mean_absolute_error_rad": (
                    0.03 if model_id == "pi05" else 0.5
                ),
                "initial_gripper_absolute_error_rad": (
                    0.75 if model_id == "pi05" else 1.0
                ),
                "first_action_divergence": {"frame_index": 0},
            }
            for model_id in MODEL_ORDER
        ]


if __name__ == "__main__":
    unittest.main()
