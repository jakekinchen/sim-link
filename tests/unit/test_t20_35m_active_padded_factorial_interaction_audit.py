from __future__ import annotations

import copy
import math
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_35m_active_padded_factorial_interaction_audit import (
    build_factorial_interaction_audit,
    verify_factorial_interaction_audit,
)


class T2035mActivePaddedFactorialInteractionAuditTests(unittest.TestCase):
    def test_active_dominant_context_dependent_result_routes_near_zero_scale(self) -> None:
        audit = self._audit(self._conditions())
        verify_factorial_interaction_audit(audit)
        self.assertTrue(audit["active_noise_harmful_at_both_padded_settings_all_metrics"])
        self.assertTrue(audit["padded_noise_accuracy_effect_changes_sign_by_active_setting"])
        self.assertEqual(audit["best_noise_condition"], "active_zero_padded_normal")
        self.assertEqual(
            audit["interaction_classification"],
            "active_noise_dominant_with_context_dependent_padded_interaction",
        )
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "run_separately_reviewed_near_zero_active_noise_scale_discriminator_with_padded_normal",
        )

    def test_all_contrasts_preserve_factorial_signs(self) -> None:
        audit = self._audit(self._conditions())
        worst = audit["metric_contrasts"][0]
        self.assertAlmostEqual(
            worst["active_noise_effect_with_padded_zero"], 0.1141727289855956 - 0.07336017777404802
        )
        self.assertAlmostEqual(
            worst["active_noise_effect_with_padded_normal"], 0.15032132878119553 - 0.06639793229785562
        )
        self.assertAlmostEqual(
            worst["padded_noise_effect_with_active_zero"], 0.06639793229785562 - 0.07336017777404802
        )
        self.assertAlmostEqual(
            worst["padded_noise_effect_with_active_normal"], 0.15032132878119553 - 0.1141727289855956
        )
        self.assertAlmostEqual(
            worst["active_padded_interaction"],
            0.15032132878119553
            - 0.1141727289855956
            - 0.06639793229785562
            + 0.07336017777404802,
        )

    def test_order_nonfinite_negative_and_gate_drift_fail(self) -> None:
        reordered = self._conditions()
        reordered[1], reordered[2] = reordered[2], reordered[1]
        with self.assertRaises(ValueError):
            self._audit(reordered)
        for field, value in (
            ("worst_seed_maximum_error_rad", math.nan),
            ("aggregate_mean_absolute_error_rad", -0.1),
            ("aggregate_mean_raw_decoded_spread_rad", math.inf),
        ):
            malformed = self._conditions()
            malformed[0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    self._audit(malformed)
        gate = self._conditions()
        gate[2]["all_decoded_chunks_within_threshold"] = True
        with self.assertRaises(ValueError):
            self._audit(gate)

    def test_derived_and_authority_mutations_fail_verification(self) -> None:
        audit = self._audit(self._conditions())
        for field, value in (
            ("best_noise_condition", "active_zero_padded_zero"),
            ("gate_b_passed", True),
            ("model_loaded", True),
            ("optimizer_training", True),
        ):
            drift = copy.deepcopy(audit)
            drift[field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    verify_factorial_interaction_audit(sign_payload(drift))

    @staticmethod
    def _audit(conditions: list[dict]) -> dict:
        return build_factorial_interaction_audit(
            t20_35l_result_identity="1" * 64,
            condition_metrics=conditions,
            source_gate_b_passed=False,
        )

    @staticmethod
    def _conditions() -> list[dict]:
        return [
            {
                "noise_condition": "active_normal_padded_normal",
                "worst_seed_maximum_error_rad": 0.15032132878119553,
                "aggregate_mean_absolute_error_rad": 0.030990397665380236,
                "aggregate_mean_raw_decoded_spread_rad": 0.04639243967987639,
                "all_decoded_chunks_within_threshold": False,
            },
            {
                "noise_condition": "active_normal_padded_zero",
                "worst_seed_maximum_error_rad": 0.1141727289855956,
                "aggregate_mean_absolute_error_rad": 0.02850444550507093,
                "aggregate_mean_raw_decoded_spread_rad": 0.034543991306687,
                "all_decoded_chunks_within_threshold": False,
            },
            {
                "noise_condition": "active_zero_padded_normal",
                "worst_seed_maximum_error_rad": 0.06639793229785562,
                "aggregate_mean_absolute_error_rad": 0.02090788045588213,
                "aggregate_mean_raw_decoded_spread_rad": 0.009969666828294787,
                "all_decoded_chunks_within_threshold": False,
            },
            {
                "noise_condition": "active_zero_padded_zero",
                "worst_seed_maximum_error_rad": 0.07336017777404802,
                "aggregate_mean_absolute_error_rad": 0.024130379933735208,
                "aggregate_mean_raw_decoded_spread_rad": 0.0,
                "all_decoded_chunks_within_threshold": False,
            },
        ]


if __name__ == "__main__":
    unittest.main()
