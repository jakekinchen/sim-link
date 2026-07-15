from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_35w_step_coordinate_action_outlier_audit import (
    CELL_COUNT,
    JOINT_SQUARED_MASS_DOMINANCE_MIN,
    build_audit,
    load_source_artifacts,
    verify_audit,
)


class T2035wStepCoordinateActionOutlierAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_source_artifacts()

    def test_exact_joint_dominant_classification(self) -> None:
        audit = build_audit(**self.sources)
        self.assertEqual(audit["action_error_cell_count"], CELL_COUNT)
        self.assertEqual(audit["exceeding_cell_count"], 370)
        self.assertEqual(audit["dominant_joint_name"], "shoulder_lift")
        self.assertGreaterEqual(
            audit["dominant_joint_squared_error_mass_fraction"],
            JOINT_SQUARED_MASS_DOMINANCE_MIN,
        )
        self.assertTrue(audit["joint_dominant"])
        self.assertFalse(audit["normalized_joint_dominant"])
        self.assertEqual(
            audit["action_outlier_classification"],
            "physical_gate_joint_dominance_without_normalized_state_dominance",
        )
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "design_physical_gate_aligned_joint_weighted_standard_replay_correction",
        )

    def test_coverage_and_mass_recompute_exactly(self) -> None:
        audit = build_audit(**self.sources)
        self.assertEqual(len(audit["action_error_cells"]), 1500)
        self.assertEqual(len(audit["action_error_by_seed"]), 5)
        self.assertEqual(len(audit["action_error_by_joint"]), 6)
        self.assertEqual(len(audit["action_error_by_action_index"]), 50)
        self.assertEqual(len(audit["action_error_by_time_band"]), 5)
        self.assertAlmostEqual(
            sum(
                row["squared_error_mass_fraction"]
                for row in audit["action_error_by_joint"]
            ),
            1.0,
        )
        self.assertAlmostEqual(
            audit["action_error_by_joint"][1]["squared_error_mass_fraction"],
            0.5065735960178129,
        )
        self.assertAlmostEqual(
            audit["action_error_by_joint"][4]["squared_error_mass_fraction"],
            0.29359458381692083,
        )

    def test_source_and_signed_audit_tamper_fail_closed(self) -> None:
        audit = build_audit(**self.sources)
        verify_audit(audit, **self.sources)
        drift = copy.deepcopy(audit)
        drift["gate_b_passed"] = True
        with self.assertRaises(ValueError):
            verify_audit(sign_payload(drift), **self.sources)
        source_drift = copy.deepcopy(self.sources["trajectory_result"])
        source_drift["selected_next_hypothesis"] = "different"
        with self.assertRaises(ValueError):
            build_audit(
                **{
                    **self.sources,
                    "trajectory_result": sign_payload(source_drift),
                }
            )

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
