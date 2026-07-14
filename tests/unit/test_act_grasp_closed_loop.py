import unittest

from scenesmith.robot_lab.act_grasp_closed_loop import (
    PHASE_PLAN,
    ROLLOUT_FRAMES,
    _margin,
    phase_for_frame,
    run_policy_grasp_closed_loop,
)


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

    def test_generic_policy_contract_rejects_empty_labels_before_simulation(self) -> None:
        with self.assertRaisesRegex(ValueError, "task_id"):
            run_policy_grasp_closed_loop(
                lambda images, state: state[:6],
                checkpoint_sha256="a" * 64,
                training_run_summary_sha256="b" * 64,
                seed=2,
                schema_version="schema.v1",
                task_id="",
                evidence_mode="test",
                policy_label="test",
            )


if __name__ == "__main__":
    unittest.main()
