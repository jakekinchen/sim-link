"""Tests for the grasp-specific semantic evaluator and analytic fixtures."""

from __future__ import annotations

import math
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.strict_grasp import (
    STRICT_GRASP_PHASES,
    analytic_grasp_trajectory,
    build_strict_grasp_fixture,
    evaluate_strict_grasp,
    strict_grasp_spec,
    verify_strict_grasp_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator.fixture.json"


class StrictGraspTests(unittest.TestCase):
    def test_analytic_expert_passes_semantics_but_is_not_pure_policy(self) -> None:
        spec = strict_grasp_spec()
        trajectory = analytic_grasp_trajectory(spec)

        result = evaluate_strict_grasp(
            spec,
            trajectory,
            claimed_proof_mode="analytic_expert",
        )

        self.assertEqual(result["observed_phase_order"], list(STRICT_GRASP_PHASES))
        self.assertTrue(result["strict_grasp_success"])
        self.assertFalse(result["pure_policy_success"])
        self.assertEqual(result["proof_mode"], "analytic_expert")
        self.assertEqual(result["failure_reasons"], [])

    def test_identical_policy_owned_trace_is_classified_separately(self) -> None:
        spec = strict_grasp_spec()
        trajectory = analytic_grasp_trajectory(
            spec,
            controller_owner="policy",
            control_mode="policy",
        )

        result = evaluate_strict_grasp(
            spec,
            trajectory,
            claimed_proof_mode="strict_policy",
        )

        self.assertTrue(result["strict_grasp_success"])
        self.assertTrue(result["pure_policy_success"])
        self.assertEqual(result["proof_mode"], "strict_policy")

    def test_adversarial_fixtures_all_fail_for_their_expected_reason(self) -> None:
        payload = build_strict_grasp_fixture()

        self.assertTrue(payload["positive"]["evaluation"]["strict_grasp_success"])
        for case in payload["adversarial_negatives"]:
            with self.subTest(case=case["case_id"]):
                self.assertFalse(case["evaluation"]["strict_grasp_success"])
                self.assertIn(
                    case["expected_failure_reason"],
                    case["evaluation"]["failure_reasons"],
                )

    def test_nonfinite_and_reordered_traces_fail_closed(self) -> None:
        spec = strict_grasp_spec()
        nonfinite = analytic_grasp_trajectory(spec)
        nonfinite[4]["object_speed_m_s"] = math.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            evaluate_strict_grasp(spec, nonfinite, claimed_proof_mode="analytic_expert")

        reordered = analytic_grasp_trajectory(spec)
        reordered[1]["phase"], reordered[2]["phase"] = (
            reordered[2]["phase"],
            reordered[1]["phase"],
        )
        result = evaluate_strict_grasp(
            spec,
            reordered,
            claimed_proof_mode="analytic_expert",
        )
        self.assertIn("phase_order_invalid", result["failure_reasons"])

    def test_malformed_contact_and_safety_fields_fail_closed(self) -> None:
        spec = strict_grasp_spec()
        negative_current = analytic_grasp_trajectory(spec)
        negative_current[0]["actuator_current_ma_max"] = -1.0
        with self.assertRaisesRegex(ValueError, "non-negative"):
            evaluate_strict_grasp(
                spec,
                negative_current,
                claimed_proof_mode="analytic_expert",
            )

        boolean_contacts = analytic_grasp_trajectory(spec)
        boolean_contacts[2]["fingertip_contacts"] = True
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            evaluate_strict_grasp(
                spec,
                boolean_contacts,
                claimed_proof_mode="analytic_expert",
            )

        string_safety_flag = analytic_grasp_trajectory(spec)
        string_safety_flag[0]["forbidden_collision"] = "false"
        with self.assertRaisesRegex(ValueError, "boolean"):
            evaluate_strict_grasp(
                spec,
                string_safety_flag,
                claimed_proof_mode="analytic_expert",
            )

    def test_missing_physical_metrics_reject_without_inventing_values(self) -> None:
        spec = strict_grasp_spec()
        trajectory = analytic_grasp_trajectory(spec)
        for frame in trajectory:
            frame["actuator_current_ma_max"] = None
            frame["gripper_aperture_m"] = None

        result = evaluate_strict_grasp(
            spec,
            trajectory,
            claimed_proof_mode="analytic_expert",
        )

        self.assertFalse(result["strict_grasp_success"])
        self.assertIn("actuator_current_measurement_missing", result["failure_reasons"])
        self.assertIn("gripper_aperture_measurement_missing", result["failure_reasons"])

    def test_checked_fixture_is_deterministic_and_withholds_authority(self) -> None:
        payload = load_strict_json(FIXTURE)

        verify_strict_grasp_fixture(payload)
        self.assertEqual(payload, build_strict_grasp_fixture())
        self.assertFalse(payload["physical_anchor_observation"]["measurements_complete"])
        self.assertIsNone(payload["physical_anchor_observation"]["mass_kg"])
        self.assertFalse(payload["physical_twin_qualified"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
