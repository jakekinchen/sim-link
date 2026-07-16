import unittest

from scenesmith.robot_lab.act_grasp_closed_loop import (
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    LEGACY_RELEASE_CLEARANCE_BASIS,
    PHASE_PLAN,
    ROLLOUT_FRAMES,
    _margin,
    _release_final_clear,
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

    def test_capture_images_must_be_boolean_before_simulation(self) -> None:
        with self.assertRaisesRegex(ValueError, "capture_images"):
            run_policy_grasp_closed_loop(
                lambda images, state: state[:6],
                checkpoint_sha256="a" * 64,
                training_run_summary_sha256="b" * 64,
                seed=2,
                schema_version="schema.v1",
                task_id="test",
                evidence_mode="test",
                policy_label="test",
                capture_images="no",  # type: ignore[arg-type]
            )

    def test_release_clearance_distinguishes_force_from_geometry(self) -> None:
        zero_force_overlap = {
            "all_robot_object_contact_geoms": ["fixed_fingertip_pad_collision"],
            "pad_contact_aggregate": None,
            "nonpad_robot_object_contacts": [],
        }
        self.assertFalse(
            _release_final_clear(zero_force_overlap, LEGACY_RELEASE_CLEARANCE_BASIS)
        )
        self.assertTrue(
            _release_final_clear(
                zero_force_overlap, FORCE_BEARING_RELEASE_CLEARANCE_BASIS
            )
        )
        for mutation in (
            {"pad_contact_aggregate": {"normal_force_n": 0.1}},
            {"nonpad_robot_object_contacts": ["wrist_collision"]},
        ):
            frame = {**zero_force_overlap, **mutation}
            self.assertFalse(
                _release_final_clear(
                    frame, FORCE_BEARING_RELEASE_CLEARANCE_BASIS
                )
            )
        with self.assertRaisesRegex(ValueError, "unsupported"):
            _release_final_clear(zero_force_overlap, "unknown")


if __name__ == "__main__":
    unittest.main()
