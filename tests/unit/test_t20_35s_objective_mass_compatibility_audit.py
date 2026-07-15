from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_35s_objective_mass_compatibility_audit import (
    LATE_OBJECTIVE_MASS_DOMINANCE_THRESHOLD,
    build_audit,
    load_source_artifacts,
    verify_audit,
)


class T2035sObjectiveMassCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_source_artifacts()

    def test_exact_objective_mass_and_compatibility_classification(self) -> None:
        audit = build_audit(**self.sources)
        self.assertEqual(len(audit["objective_by_step"]), 10)
        self.assertEqual(len(audit["objective_by_seed"]), 5)
        self.assertEqual(audit["improved_example_count"], 41)
        self.assertGreaterEqual(
            audit["last_two_step_baseline_objective_mass_fraction"],
            LATE_OBJECTIVE_MASS_DOMINANCE_THRESHOLD,
        )
        self.assertTrue(audit["late_objective_mass_dominance"])
        self.assertTrue(audit["standard_objective_interference"])
        self.assertEqual(
            audit["objective_compatibility_classification"],
            "terminal_objective_mass_dominance_with_standard_interference",
        )
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "design_time_normalized_standard_replay_correction",
        )

    def test_step_and_seed_coverage_recompute_exactly(self) -> None:
        audit = build_audit(**self.sources)
        self.assertAlmostEqual(
            sum(
                row["baseline_objective_mass_fraction"]
                for row in audit["objective_by_step"]
            ),
            1.0,
        )
        self.assertEqual(
            [row["improved_example_count"] for row in audit["objective_by_step"]],
            [5, 4, 3, 3, 3, 4, 4, 5, 5, 5],
        )
        self.assertEqual(
            [row["improved_example_count"] for row in audit["objective_by_seed"]],
            [10, 10, 7, 4, 10],
        )

    def test_stale_route_nonfinite_and_reordered_examples_fail_closed(self) -> None:
        route = copy.deepcopy(self.sources["training_result"])
        route["selected_next_hypothesis"] = "different"
        with self.assertRaises(ValueError):
            build_audit(
                **{**self.sources, "training_result": sign_payload(route)}
            )
        nonfinite = copy.deepcopy(self.sources["training_run"])
        nonfinite["baseline_objective_by_example"][0] = float("nan")
        with self.assertRaises(ValueError):
            build_audit(**{**self.sources, "training_run": sign_payload(nonfinite)})
        reordered = copy.deepcopy(self.sources["training_spec"])
        reordered["correction_examples"][0], reordered["correction_examples"][1] = (
            reordered["correction_examples"][1],
            reordered["correction_examples"][0],
        )
        with self.assertRaises(ValueError):
            build_audit(**{**self.sources, "training_spec": sign_payload(reordered)})

    def test_signed_audit_tamper_fails_closed(self) -> None:
        audit = build_audit(**self.sources)
        verify_audit(audit, **self.sources)
        drift = copy.deepcopy(audit)
        drift["gate_b_passed"] = True
        with self.assertRaises(ValueError):
            verify_audit(sign_payload(drift), **self.sources)

    def test_all_authority_and_mutation_fields_remain_closed(self) -> None:
        audit = build_audit(**self.sources)
        for field in (
            "model_loaded",
            "model_inference",
            "optimizer_created",
            "optimizer_training",
            "checkpoint_read",
            "checkpoint_mutated",
            "dataset_mutated",
            "action_correction_selected",
            "closed_loop_rollout",
            "simulation_policy_accepted",
            "physical_actuation",
            "external_compute_started",
            "brev_compute_started",
            "physical_transfer_ready",
            "promotion_eligible",
            "gate_b_passed",
        ):
            self.assertFalse(audit[field])


if __name__ == "__main__":
    unittest.main()
