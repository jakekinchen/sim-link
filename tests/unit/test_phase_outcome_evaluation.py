"""T20.6 phase-level outcome-versus-strict semantic evaluation tests."""

from __future__ import annotations

import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.phase_outcome_evaluation import (
    CAPABILITY_STAGES,
    build_phase_outcome_fixture,
    verify_phase_outcome_fixture,
)
from scenesmith.robot_lab.strict_grasp import verify_strict_grasp_v2_fixture


REPO_ROOT = Path(__file__).resolve().parents[2]
STRICT_V2_PATH = (
    REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json"
)
FIXTURE_PATH = (
    REPO_ROOT / "configurations/robot_lab/t20_6_phase_outcome_evaluation.json"
)


class PhaseOutcomeEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.strict_v2 = load_strict_json(STRICT_V2_PATH)
        cls.fixture = load_strict_json(FIXTURE_PATH)

    def test_checked_fixture_is_source_bound_and_deterministic(self) -> None:
        verify_strict_grasp_v2_fixture(self.strict_v2)
        verify_phase_outcome_fixture(self.fixture, self.strict_v2)
        self.assertEqual(self.fixture, build_phase_outcome_fixture(self.strict_v2))
        self.assertEqual(
            self.fixture["source_strict_v2_identity_sha256"],
            self.strict_v2["identity_sha256"],
        )

    def test_positive_records_complete_stage_witness_and_strict_success(self) -> None:
        positive = self.fixture["positive"]

        self.assertEqual(
            [entry["stage"] for entry in positive["capability_stage_witness"]],
            list(CAPABILITY_STAGES),
        )
        self.assertTrue(
            all(entry["witness_complete"] for entry in positive["capability_stage_witness"])
        )
        self.assertTrue(positive["terminal_outcome"]["object_reached_target"])
        self.assertTrue(positive["terminal_outcome"]["stable_target_occupancy"])
        self.assertTrue(positive["strict_evaluation"]["strict_grasp_success"])
        self.assertFalse(positive["strict_evaluation"]["pure_policy_success"])

    def test_required_adversarial_outcomes_stay_truthful_but_fail_strict(self) -> None:
        cases = {case["case_id"]: case for case in self.fixture["adversarial_cases"]}
        self.assertEqual(
            set(cases),
            {
                "putt_without_grasp",
                "planar_slide_without_lift",
                "ballistic_throw_after_momentary_contact",
                "terminal_occupancy_without_verified_release",
                "scripted_object_motion",
                "assistance_relabelled_as_policy",
                "stage_witness_drift",
                "actor_privilege_leakage",
            },
        )
        for case_id, case in cases.items():
            with self.subTest(case_id=case_id):
                self.assertTrue(case["terminal_outcome"]["object_reached_target"])
                self.assertTrue(case["terminal_outcome"]["stable_target_occupancy"])
                self.assertFalse(case["strict_evaluation"]["strict_grasp_success"])
                self.assertIn(
                    case["expected_failure_reason"],
                    case["strict_evaluation"]["failure_reasons"],
                )
        stage_drift = cases["stage_witness_drift"]["capability_stage_witness"]
        approach_witness = next(
            row for row in stage_drift if row["stage"] == "approach"
        )
        self.assertFalse(approach_witness["witness_complete"])

    def test_artifact_denies_policy_acceptance_and_elevated_authority(self) -> None:
        self.assertTrue(self.fixture["all_required_adversarial_cases_rejected"])
        self.assertFalse(self.fixture["simulation_policy_accepted"])
        self.assertFalse(self.fixture["actual_mujoco_policy_success"])
        self.assertFalse(self.fixture["physical_transfer_eligible"])
        self.assertFalse(self.fixture["hardware_accessed"])

    def test_resigned_artifact_or_source_drift_is_rejected(self) -> None:
        changed = copy.deepcopy(self.fixture)
        changed["adversarial_cases"][0]["terminal_outcome"][
            "object_reached_target"
        ] = False
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_phase_outcome_fixture(sign_payload(changed), self.strict_v2)

        changed_source = copy.deepcopy(self.strict_v2)
        changed_source["positive"]["trajectory"][0]["mechanism"] = "slide"
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_phase_outcome_fixture(
                self.fixture,
                sign_payload(changed_source),
            )


if __name__ == "__main__":
    unittest.main()
