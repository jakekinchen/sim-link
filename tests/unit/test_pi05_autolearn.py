from __future__ import annotations

import unittest

from scenesmith.robot_lab.autolearn import (
    PromotionGate,
    decide_promotion,
    is_dagger_correction_frame,
    policy_expert_delta_l2,
    select_training_frames,
    summarize_evaluation,
    validate_dagger_episode_scope,
)


def _frame(source: str, *, intervention: bool = False, motion: str = "contact_physics"):
    return {
        "action_source": source,
        "is_intervention": intervention,
        "human_action": [0.2] * 6 if intervention else None,
        "policy_action": [0.0] * 6,
        "executed_action": [0.1] * 6,
        "object_motion_mode": motion,
    }


def _episode(
    seed: int,
    *,
    success: bool,
    sorted_count: int,
    controller_frames: int = 0,
    grasp_activations: int = 0,
    scripted: bool = False,
    physical: bool = False,
):
    return {
        "seed": seed,
        "status": "pass" if success else "fail",
        "final_score": {"success": success, "sorted_count": sorted_count},
        "intervention": {
            "frames": 0,
            "physical_follower_commanded": physical,
            "safety_report": {"physical_follower_commanded": physical},
        },
        "policy_runtime": {"physical_follower_commanded": physical},
        "proof_scope": {
            "scripted_object_motion": scripted,
            "object_motion_modes": ["contact_physics_neural_policy"],
            "grasp_assist": {
                "activation_count": grasp_activations,
                "post_place_controller": {
                    "executed_frames": controller_frames,
                    "tray_transfer_executed_frames": 0,
                    "recovery_pick_executed_frames": 0,
                },
            },
        },
    }


class DaggerFrameTests(unittest.TestCase):
    def test_selects_controller_and_human_corrections_only(self):
        policy = _frame("policy")
        transfer = _frame("contact_gated_tray_transfer")
        human = _frame("physical_leader", intervention=True)
        selected = select_training_frames([policy, transfer, human], "dagger_corrections")
        self.assertEqual(selected, [transfer, human])
        self.assertTrue(is_dagger_correction_frame(transfer))
        self.assertAlmostEqual(policy_expert_delta_l2(transfer), 6**0.5 * 0.1)

    def test_rejects_scripted_motion(self):
        frame = _frame("contact_gated_recovery_pick", motion="scripted_cube_teleport")
        self.assertFalse(is_dagger_correction_frame(frame))

    def test_scope_requires_neural_non_scripted_episode(self):
        summary = {
            "proof_scope": {
                "scripted_object_motion": False,
                "neural_policy_actions_applied_to_simulation": True,
            },
            "intervention": {"physical_follower_commanded": False},
            "policy_runtime": {"physical_follower_commanded": False},
        }
        validate_dagger_episode_scope(summary, [_frame("contact_reflex_post_place")])
        summary["proof_scope"]["scripted_object_motion"] = True
        with self.assertRaisesRegex(ValueError, "scripted_object_motion"):
            validate_dagger_episode_scope(summary, [_frame("contact_reflex_post_place")])


class PromotionTests(unittest.TestCase):
    def test_accepts_complete_unassisted_improvement(self):
        seeds = (7100, 7101, 7102, 7103)
        baseline = summarize_evaluation(
            {"results": [_episode(seed, success=False, sorted_count=1) for seed in seeds]}
        )
        candidate = summarize_evaluation(
            {"results": [_episode(seed, success=True, sorted_count=4) for seed in seeds]}
        )
        decision = decide_promotion(
            baseline,
            candidate,
            PromotionGate(expected_seeds=seeds, min_pure_success_rate=0.75),
        )
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reasons, ())

    def test_rejects_assisted_success(self):
        seeds = (7100, 7101)
        baseline = summarize_evaluation(
            {"results": [_episode(seed, success=False, sorted_count=0) for seed in seeds]}
        )
        candidate = summarize_evaluation(
            {
                "results": [
                    _episode(seed, success=True, sorted_count=4, controller_frames=50)
                    for seed in seeds
                ]
            }
        )
        decision = decide_promotion(
            baseline,
            candidate,
            PromotionGate(expected_seeds=seeds, min_pure_success_rate=0.5),
        )
        self.assertFalse(decision.accepted)
        self.assertIn("candidate_contains_controller_or_human_assistance", decision.reasons)

    def test_rejects_incomplete_seed_set_and_physical_command(self):
        baseline = summarize_evaluation(
            {"results": [_episode(7100, success=False, sorted_count=0)]}
        )
        candidate = summarize_evaluation(
            {"results": [_episode(7100, success=True, sorted_count=4, physical=True)]}
        )
        decision = decide_promotion(
            baseline,
            candidate,
            PromotionGate(expected_seeds=(7100, 7101), min_pure_success_rate=0.5),
        )
        self.assertFalse(decision.accepted)
        self.assertIn("candidate_seed_set_incomplete", decision.reasons)
        self.assertIn("candidate_commanded_physical_follower", decision.reasons)


if __name__ == "__main__":
    unittest.main()
