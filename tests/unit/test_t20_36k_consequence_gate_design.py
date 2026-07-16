import unittest

from copy import deepcopy

import numpy as np

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.t20_36k_consequence_gate_design import (
    JOINT_NAMES,
    PERTURBATION_MAGNITUDES_RAD,
    PHASE_GROUPS,
    ROLLOUT_FRAMES,
    REPO_ROOT,
    RESULT_PATH,
    build_perturbed_actions,
    derive_threshold_rows,
    phase_group_for_frame,
    verify_design,
)


class T2036kConsequenceGateDesignTest(unittest.TestCase):
    def test_phase_groups_cover_the_exact_horizon_once(self) -> None:
        observed = [phase_group_for_frame(index) for index in range(ROLLOUT_FRAMES)]
        self.assertEqual(set(observed), set(PHASE_GROUPS))
        self.assertEqual(len(observed), 244)

    def test_perturbation_grid_is_bounded_symmetric_and_candidate_independent(self) -> None:
        self.assertEqual(
            PERTURBATION_MAGNITUDES_RAD,
            (0.01, 0.025, 0.05, 0.1, 0.2, 0.4),
        )
        nominal = np.zeros((ROLLOUT_FRAMES, len(JOINT_NAMES)), dtype=np.float64)
        positive = build_perturbed_actions(
            nominal, joint_name="wrist_roll", phase_group="reach", signed_delta_rad=0.05
        )
        negative = build_perturbed_actions(
            nominal, joint_name="wrist_roll", phase_group="reach", signed_delta_rad=-0.05
        )
        mask = np.asarray(
            [phase_group_for_frame(index) == "reach" for index in range(ROLLOUT_FRAMES)]
        )
        np.testing.assert_array_equal(positive[mask, 4], np.full(mask.sum(), 0.05))
        np.testing.assert_array_equal(negative[mask, 4], np.full(mask.sum(), -0.05))
        np.testing.assert_array_equal(positive[~mask], nominal[~mask])
        np.testing.assert_array_equal(negative[~mask], nominal[~mask])

    def test_perturbation_rejects_non_grid_and_non_finite_inputs(self) -> None:
        nominal = np.zeros((ROLLOUT_FRAMES, len(JOINT_NAMES)), dtype=np.float64)
        with self.assertRaisesRegex(ValueError, "pre-registered grid"):
            build_perturbed_actions(
                nominal, joint_name="wrist_roll", phase_group="reach", signed_delta_rad=0.051
            )
        nominal[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            build_perturbed_actions(
                nominal, joint_name="wrist_roll", phase_group="reach", signed_delta_rad=0.05
            )

    def test_threshold_derivation_uses_only_paired_consequences(self) -> None:
        pairs = []
        for magnitude in PERTURBATION_MAGNITUDES_RAD:
            pairs.append(
                {
                    "joint_name": "shoulder_lift",
                    "phase_group": "lift",
                    "magnitude_rad": magnitude,
                    "both_signs_consequence_passed": magnitude < 0.1,
                }
            )
        rows = derive_threshold_rows(pairs, require_complete_matrix=False)
        row = next(
            item
            for item in rows
            if item["joint_name"] == "shoulder_lift" and item["phase_group"] == "lift"
        )
        self.assertEqual(row["first_observed_consequence_delta_rad"], 0.1)
        self.assertEqual(row["largest_evidenced_safe_symmetric_delta_rad"], 0.05)
        self.assertEqual(row["amendment_ceiling_rad"], 0.05)
        self.assertEqual(row["sensitivity_class"], "consequence_sensitive")

    def test_threshold_derivation_keeps_critical_floor_and_bounded_freedom(self) -> None:
        pairs = []
        for joint, group, failure in (
            ("gripper", "grasp", 0.01),
            ("wrist_roll", "reach", None),
        ):
            for magnitude in PERTURBATION_MAGNITUDES_RAD:
                pairs.append(
                    {
                        "joint_name": joint,
                        "phase_group": group,
                        "magnitude_rad": magnitude,
                        "both_signs_consequence_passed": failure is None or magnitude < failure,
                    }
                )
        rows = derive_threshold_rows(pairs, require_complete_matrix=False)
        gripper = next(item for item in rows if item["joint_name"] == "gripper")
        wrist = next(item for item in rows if item["joint_name"] == "wrist_roll")
        self.assertEqual(gripper["sensitivity_class"], "critical_at_resolution_floor")
        self.assertEqual(gripper["amendment_ceiling_rad"], 0.01)
        self.assertEqual(wrist["sensitivity_class"], "insensitive_through_bounded_grid")
        self.assertEqual(wrist["amendment_ceiling_rad"], 0.4)

    def test_threshold_derivation_rejects_missing_grid_and_fails_closed_on_non_monotonic_pass(self) -> None:
        incomplete = [
            {
                "joint_name": "gripper",
                "phase_group": "grasp",
                "magnitude_rad": 0.01,
                "both_signs_consequence_passed": True,
            }
        ]
        with self.assertRaisesRegex(ValueError, "complete perturbation grid"):
            derive_threshold_rows(incomplete)
        non_monotonic = [
            {
                "joint_name": "gripper",
                "phase_group": "grasp",
                "magnitude_rad": magnitude,
                "both_signs_consequence_passed": magnitude != 0.025,
            }
            for magnitude in PERTURBATION_MAGNITUDES_RAD
        ]
        row = derive_threshold_rows(non_monotonic, require_complete_matrix=False)[0]
        self.assertTrue(row["non_monotonic_outcome_observed"])
        self.assertEqual(row["first_observed_consequence_delta_rad"], 0.025)
        self.assertEqual(row["largest_evidenced_safe_symmetric_delta_rad"], 0.01)
        self.assertEqual(row["amendment_ceiling_rad"], 0.01)

    def test_materialized_design_verifies_and_rejects_candidate_derived_thresholds(self) -> None:
        payload = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_design(payload)
        self.assertEqual(payload["perturbation_spec"]["pair_count"], 252)
        self.assertFalse(payload["gate_b_threshold_changed"])
        mutation = deepcopy(payload)
        mutation["candidate_evidence_context_only"]["used_for_threshold_derivation"] = True
        mutation = sign_payload(mutation)
        with self.assertRaisesRegex(ValueError, "must not derive"):
            verify_design(mutation)


if __name__ == "__main__":
    unittest.main()
