"""T20.8 central simulation-policy acceptance tests."""

from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.authority_composer import (
    REQUIRED_POLICY_ACCEPTANCE_REPEAT_COUNT,
    _compose_simulation_policy_acceptance_core,
    verify_simulation_policy_acceptance_core,
)


class PolicyAcceptanceComposerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.semantic = {
            "all_required_adversarial_cases_rejected": True,
            "positive": {"strict_evaluation": {"strict_grasp_success": True}},
        }
        self.sources = {
            "semantic_fixture": {
                "path": "semantic.json",
                "schema_version": "test.v1",
                "identity_sha256": "1" * 64,
                "file_sha256": "2" * 64,
            }
        }

    def test_current_zero_success_gate_is_deterministically_denied(self) -> None:
        gate = {
            "winner_model_id": None,
            "strict_success_count": 0,
            "model_results": [],
        }
        decision = self._compose(gate)
        verify_signed_payload(decision, label="test policy acceptance decision")
        self.assertFalse(decision["simulation_policy_accepted"])
        self.assertIsNone(decision["selected_model_id"])
        self.assertEqual(decision["measured_strict_success_rollout_count"], 0)
        self.assertEqual(
            decision["required_strict_success_rollout_count"],
            REQUIRED_POLICY_ACCEPTANCE_REPEAT_COUNT,
        )
        self.assertEqual(decision, self._compose(copy.deepcopy(gate)))
        self.assertFalse(decision["physical_transfer_ready"])
        self.assertFalse(decision["promotion_eligible"])

    def test_one_strict_rollout_still_fails_repeat_requirement(self) -> None:
        gate = {
            "winner_model_id": "act",
            "strict_success_count": 1,
            "model_results": [
                {
                    "model_id": "act",
                    "simulation_semantic_strict_success": True,
                    "projected_action_frame_count": 0,
                    "active_assist_frame_count": 0,
                    "rendered_keyframe_count": 5,
                }
            ],
        }
        decision = self._compose(gate)
        self.assertFalse(decision["simulation_policy_accepted"])
        self.assertEqual(decision["measured_strict_success_rollout_count"], 1)
        self.assertEqual(
            decision["criteria"]["strict_success_repeat_count"]["margin"], -2.0
        )

    def test_resigned_decision_or_source_mutations_are_rejected(self) -> None:
        gate = {
            "winner_model_id": None,
            "strict_success_count": 0,
            "model_results": [],
        }
        expected = self._compose(gate)
        mutators = {
            "winner": lambda value: value.__setitem__("selected_model_id", "act"),
            "success count": lambda value: value.__setitem__(
                "measured_strict_success_rollout_count", 3
            ),
            "repeat threshold": lambda value: value.__setitem__(
                "required_strict_success_rollout_count", 1
            ),
            "projection": lambda value: value["criteria"][
                "selected_projected_action_frames"
            ].update({"measured": 0, "margin": 0.0, "passed": True}),
            "source identity": lambda value: value["source_evidence"][
                "semantic_fixture"
            ].__setitem__("identity_sha256", "9" * 64),
            "acceptance": lambda value: value.__setitem__(
                "simulation_policy_accepted", True
            ),
            "physical transfer": lambda value: value.__setitem__(
                "physical_transfer_ready", True
            ),
            "promotion": lambda value: value.__setitem__("promotion_eligible", True),
        }
        for label, mutate in mutators.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(expected)
                mutate(changed)
                changed = sign_payload(changed)
                verify_signed_payload(changed, label="resigned mutation")
                with self.assertRaisesRegex(ValueError, "drifted from evidence"):
                    verify_simulation_policy_acceptance_core(
                        changed,
                        semantic_fixture=self.semantic,
                        evaluation_gate=gate,
                        source_evidence=self.sources,
                        evaluation_time="2026-07-14T09:30:00-05:00",
                    )

    def _compose(self, gate: dict) -> dict:
        return _compose_simulation_policy_acceptance_core(
            semantic_fixture=self.semantic,
            evaluation_gate=gate,
            source_evidence=self.sources,
            evaluation_time="2026-07-14T09:30:00-05:00",
        )


if __name__ == "__main__":
    unittest.main()
