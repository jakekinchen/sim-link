import unittest

from scenesmith.robot_lab.act_grasp_closed_loop import PHASE_PLAN, ROLLOUT_FRAMES, _margin, phase_for_frame


class ActGraspClosedLoopTest(unittest.TestCase):
    def test_phase_plan_covers_exact_episode_horizon(self) -> None:
        observed = [phase_for_frame(index) for index in range(ROLLOUT_FRAMES)]
        self.assertEqual(ROLLOUT_FRAMES, 244)
        for phase, count in PHASE_PLAN:
            self.assertEqual(observed.count(phase), count)

    def test_phase_index_fails_closed(self) -> None:
        for value in (-1, ROLLOUT_FRAMES, True):
            with self.assertRaises(ValueError):
                phase_for_frame(value)

    def test_gate_margin_reports_measurement_and_threshold(self) -> None:
        self.assertTrue(_margin(8, 8, ">=")["passed"])
        failed = _margin(0.79, 0.8, ">=")
        self.assertFalse(failed["passed"])
        self.assertAlmostEqual(failed["margin"], -0.01)
        self.assertFalse(_margin(1, 0, "==")["passed"])


if __name__ == "__main__":
    unittest.main()
