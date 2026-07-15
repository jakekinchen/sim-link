from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36a_objective_interference_audit import (
    HISTORY_WINDOW_SIZE,
    build_audit,
    classify_interference,
    load_source_artifacts,
    verify_audit,
)


class T2036aObjectiveInterferenceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_source_artifacts()

    def test_exact_sources_classify_weighted_objective_gate_aliasing(self) -> None:
        audit = build_audit(**self.sources)
        self.assertEqual(audit["history_update_count"], 500)
        self.assertEqual(audit["history_window_size"], HISTORY_WINDOW_SIZE)
        self.assertEqual(len(audit["history_windows"]), 20)
        self.assertTrue(audit["source_gate_b_passed"])
        self.assertFalse(audit["campaign_gate_b_passed"])
        self.assertTrue(audit["joint_weighted_correction_improved"])
        self.assertTrue(audit["raw_correction_worsened"])
        self.assertTrue(audit["every_decoded_seed_maximum_worsened"])
        self.assertEqual(
            audit["interference_classification"],
            "weighted_objective_physical_gate_aliasing_under_coverage",
        )
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "design_gate_equivalent_retention_guard_before_any_training_proposal",
        )

    def test_exact_seed_and_objective_changes_are_recomputed(self) -> None:
        audit = build_audit(**self.sources)
        self.assertEqual(len(audit["decoded_action_change_by_seed"]), 5)
        self.assertGreater(
            audit["campaign_to_source_standard_objective_ratio"], 10.0
        )
        self.assertLess(
            audit["campaign_to_source_joint_weighted_correction_ratio"], 1.0
        )
        self.assertGreater(
            audit["campaign_to_source_raw_correction_ratio"], 1.0
        )
        self.assertGreater(
            audit["campaign_to_source_worst_action_error_ratio"], 4.0
        )

    def test_stale_nonfinite_short_threshold_and_decoded_drift_fail_closed(self) -> None:
        stale = copy.deepcopy(self.sources["source_result"])
        stale["gate_b_passed"] = False
        with self.assertRaises(ValueError):
            build_audit(
                **{**self.sources, "source_result": sign_payload(stale)}
            )

        nonfinite = copy.deepcopy(self.sources["campaign_run"])
        nonfinite["per_update_standard_coverage_objective"][0] = float("nan")
        with self.assertRaises(ValueError):
            build_audit(
                **{**self.sources, "campaign_run": sign_payload(nonfinite)}
            )

        short = copy.deepcopy(self.sources["campaign_run"])
        short["gradient_norms_before_clip"].pop()
        with self.assertRaises(ValueError):
            build_audit(**{**self.sources, "campaign_run": sign_payload(short)})

        threshold = copy.deepcopy(self.sources["campaign_spec"])
        threshold["gate_b"]["maximum_action_error_rad"] = 0.06
        with self.assertRaises(ValueError):
            build_audit(
                **{**self.sources, "campaign_spec": sign_payload(threshold)}
            )

        decoded = copy.deepcopy(self.sources["campaign_run"])
        decoded["decoded_action_chunks"][0]["maximum_absolute_error_rad"] = 0.01
        with self.assertRaises(ValueError):
            build_audit(
                **{**self.sources, "campaign_run": sign_payload(decoded)}
            )

    def test_classification_is_exclusive_and_tamper_fails_closed(self) -> None:
        self.assertEqual(
            classify_interference(
                weighted_ratio=0.5,
                raw_ratio=1.5,
                every_decoded_seed_maximum_worsened=True,
            )[0],
            "weighted_objective_physical_gate_aliasing_under_coverage",
        )
        self.assertEqual(
            classify_interference(
                weighted_ratio=1.2,
                raw_ratio=1.4,
                every_decoded_seed_maximum_worsened=True,
            )[0],
            "broad_correction_objective_regression_under_coverage",
        )
        self.assertEqual(
            classify_interference(
                weighted_ratio=0.8,
                raw_ratio=0.9,
                every_decoded_seed_maximum_worsened=True,
            )[0],
            "insufficient_recorded_evidence_for_interference_classification",
        )
        audit = build_audit(**self.sources)
        drift = copy.deepcopy(audit)
        drift["interference_classification"] = "different"
        with self.assertRaises(ValueError):
            verify_audit(sign_payload(drift), **self.sources)

    def test_all_new_authority_and_mutation_fields_remain_closed(self) -> None:
        audit = build_audit(**self.sources)
        for field in (
            "checkpoint_read",
            "model_loaded",
            "model_inference",
            "optimizer_created",
            "optimizer_training",
            "checkpoint_mutated",
            "dataset_mutated",
            "statistics_changed",
            "gate_b_threshold_changed",
            "second_campaign_authorized",
            "closed_loop_rollout",
            "simulation_policy_accepted",
            "physical_actuation",
            "external_compute_started",
            "brev_compute_started",
            "physical_transfer_ready",
            "promotion_eligible",
        ):
            self.assertFalse(audit[field])


if __name__ == "__main__":
    unittest.main()
