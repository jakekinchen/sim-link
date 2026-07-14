"""T20.20 privileged-versus-observable strict-v2 evaluator tests."""

from __future__ import annotations

import copy
import math
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.observer_role_evaluator import (
    TASK_PREDICATES,
    build_observer_role_evaluator_fixture,
    evaluate_observer_role,
    verify_observer_role_evaluator_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STRICT_V2_PATH = (
    REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json"
)
FIXTURE_PATH = (
    REPO_ROOT / "configurations/robot_lab/t20_20_observer_role_evaluator.json"
)


class ObserverRoleEvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.strict_v2 = load_strict_json(STRICT_V2_PATH)
        cls.fixture = load_strict_json(FIXTURE_PATH)
        cls.contract = cls.fixture["contract"]

    def test_fixture_is_source_bound_deterministic_and_role_separated(self) -> None:
        verify_observer_role_evaluator_fixture(self.fixture, self.strict_v2)
        self.assertEqual(
            self.fixture,
            build_observer_role_evaluator_fixture(self.strict_v2),
        )
        self.assertEqual(
            self.fixture["source_strict_v2_identity_sha256"],
            self.strict_v2["identity_sha256"],
        )
        roles = self.contract["roles"]
        self.assertEqual(
            roles["simulator_privileged"]["predicate_vocabulary"],
            roles["hardware_observable"]["predicate_vocabulary"],
        )
        self.assertEqual(
            tuple(roles["hardware_observable"]["predicate_vocabulary"]),
            TASK_PREDICATES,
        )
        self.assertTrue(
            set(roles["simulator_privileged"]["allowed_fields"]).isdisjoint(
                roles["hardware_observable"]["role_specific_fields"]
            )
        )

    def test_complete_equivalent_positive_and_negative_cases_agree(self) -> None:
        report = self.fixture["simulator_consistency_report"]
        verify_signed_payload(report, label="simulator consistency report")
        self.assertTrue(report["all_complete_cases_consistent"])
        self.assertEqual(report["complete_case_count"], 2)
        cases = {case["case_id"]: case for case in report["complete_cases"]}

        positive = cases["complete_positive"]
        self.assertTrue(positive["privileged_result"]["task_success"])
        self.assertTrue(positive["observable_result"]["task_success"])
        self.assertTrue(positive["predicate_values_identical"])

        negative = cases["stable_hold_negative"]
        self.assertFalse(negative["privileged_result"]["task_success"])
        self.assertFalse(negative["observable_result"]["task_success"])
        self.assertFalse(
            negative["privileged_result"]["predicates"]["stable_hold_valid"]["value"]
        )
        self.assertTrue(negative["predicate_values_identical"])

    def test_missing_observation_fails_closed_without_inference(self) -> None:
        evidence = copy.deepcopy(self.fixture["cases"]["observable_positive"])
        evidence.pop("stable_hold_event_observed")

        result = evaluate_observer_role(
            self.contract,
            role="hardware_observable",
            evidence=evidence,
        )

        predicate = result["predicates"]["stable_hold_valid"]
        self.assertFalse(result["task_success"])
        self.assertFalse(predicate["value"])
        self.assertEqual(predicate["availability"], "not_observed")
        self.assertIn(
            "required_observation_missing:stable_hold_event_observed",
            predicate["reasons"],
        )

    def test_privileged_field_in_observable_role_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.fixture["cases"]["observable_positive"])
        evidence["object_position_m"] = [0.22, 0.0, 0.365]
        with self.assertRaisesRegex(ValueError, "role leakage"):
            evaluate_observer_role(
                self.contract,
                role="hardware_observable",
                evidence=evidence,
            )

    def test_claimed_success_and_unknown_fields_are_rejected(self) -> None:
        evidence = copy.deepcopy(self.fixture["cases"]["observable_positive"])
        evidence["task_success"] = True
        with self.assertRaisesRegex(ValueError, "undeclared evidence field"):
            evaluate_observer_role(
                self.contract,
                role="hardware_observable",
                evidence=evidence,
            )

        drifted_contract = copy.deepcopy(self.contract)
        drifted_contract["roles"]["hardware_observable"]["allowed_fields"].append(
            "task_success"
        )
        with self.assertRaisesRegex(ValueError, "contract drifted"):
            evaluate_observer_role(
                sign_payload(drifted_contract),
                role="hardware_observable",
                evidence=evidence,
            )

    def test_evaluator_state_cannot_become_actor_input(self) -> None:
        evidence = copy.deepcopy(self.fixture["cases"]["observable_positive"])
        evidence["actor_input_field_names"].append(
            "observer_role_evaluator.predicates.stable_hold_valid"
        )

        result = evaluate_observer_role(
            self.contract,
            role="hardware_observable",
            evidence=evidence,
        )

        self.assertFalse(result["task_success"])
        self.assertIn("evaluator_state_leaked_to_actor", result["failure_reasons"])

    def test_nonfinite_or_malformed_observations_are_rejected(self) -> None:
        evidence = copy.deepcopy(self.fixture["cases"]["observable_positive"])
        evidence["measured_joint_positions_rad"][0] = math.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            evaluate_observer_role(
                self.contract,
                role="hardware_observable",
                evidence=evidence,
            )

        evidence = copy.deepcopy(self.fixture["cases"]["observable_positive"])
        evidence["evidence_source"] = "camera_vlm_inference"
        with self.assertRaisesRegex(ValueError, "not allowed"):
            evaluate_observer_role(
                self.contract,
                role="hardware_observable",
                evidence=evidence,
            )

        evidence = copy.deepcopy(self.fixture["cases"]["observable_positive"])
        evidence["observed_phase_order"] = ["approach", "approach"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            evaluate_observer_role(
                self.contract,
                role="hardware_observable",
                evidence=evidence,
            )

    def test_rejection_cases_and_authority_remain_fail_closed(self) -> None:
        report = self.fixture["simulator_consistency_report"]
        self.assertTrue(report["missing_observation_rejected"])
        self.assertTrue(report["privileged_role_leakage_rejected"])
        self.assertTrue(report["claimed_success_spoof_rejected"])
        self.assertFalse(self.fixture["hardware_observation_performed"])
        self.assertFalse(self.fixture["physical_qualification_granted"])
        self.assertFalse(self.fixture["simulation_training_ready"])
        self.assertFalse(self.fixture["simulation_policy_accepted"])

        drifted = copy.deepcopy(self.fixture)
        drifted["physical_qualification_granted"] = True
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_observer_role_evaluator_fixture(
                sign_payload(drifted), self.strict_v2
            )


if __name__ == "__main__":
    unittest.main()
