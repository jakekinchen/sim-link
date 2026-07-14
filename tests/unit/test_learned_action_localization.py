import copy
import unittest

from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.learned_action_localization import analyze_model_actions


class LearnedActionLocalizationTest(unittest.TestCase):
    def test_first_frame_and_per_joint_errors_are_measured(self) -> None:
        source, model = self._frames()
        model[0]["policy_requested_action"][5] += 0.25
        result = analyze_model_actions(
            source,
            model,
            source_anchor_start_position_m=[0.22, 0.0, 0.325],
        )
        self.assertEqual(result["first_action_divergence"]["frame_index"], 0)
        self.assertEqual(result["first_action_divergence"]["joint_name"], "gripper")
        self.assertEqual(result["initial_gripper_absolute_error_rad"], 0.25)
        self.assertTrue(
            result["initial_observation_comparison"]["identical_within_tolerance"]
        )
        self.assertEqual(set(result["initial_action_absolute_error_rad"]), set(JOINT_NAMES))

    def test_phase_or_nonfinite_drift_rejects(self) -> None:
        source, model = self._frames()
        model[1]["phase"] = "wrong"
        with self.assertRaisesRegex(ValueError, "phase"):
            analyze_model_actions(
                source, model, source_anchor_start_position_m=[0.22, 0.0, 0.325]
            )
        source, model = self._frames()
        model[0]["policy_requested_action"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            analyze_model_actions(
                source, model, source_anchor_start_position_m=[0.22, 0.0, 0.325]
            )

    @staticmethod
    def _frames():
        source = []
        model = []
        phases = ["approach"] * 14 + ["pregrasp"] * 18 + ["close"] * 36 + ["grasp_hold"] * 8 + ["unassisted_lift"] * 24 + ["unsupported_lift_hold"] * 12 + ["recording_stable_hold"] * 64 + ["lower"] * 24 + ["release"] * 12 + ["release_settle"] * 8 + ["retreat"] * 24
        for phase in phases:
            action = [0.0] * 6
            source.append(
                {
                    "source_phase": phase,
                    "actions": {"requested": {"values": action}},
                    "observations": {
                        "joint_position_mujoco_rad": [0.0] * 6,
                        "joint_velocity_mujoco_rad_s": [0.0] * 6,
                    },
                }
            )
            model.append(
                {
                    "phase": phase,
                    "policy_requested_action": list(action),
                    "mujoco_qpos": [0.0] * 6,
                    "mujoco_qvel": [0.0] * 6,
                    "cube_positions_m": {"object": [0.22, 0.0, 0.325]},
                }
            )
        return source, model


if __name__ == "__main__":
    unittest.main()
