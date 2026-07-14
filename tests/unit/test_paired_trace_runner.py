"""T20.21 offline thin paired-trace runner tests."""

from __future__ import annotations

import copy
import math
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.paired_trace_runner import (
    MISMATCH_CATEGORIES,
    build_paired_trace_runner_fixture,
    compare_paired_traces,
    verify_paired_trace_runner_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OBSERVER_PATH = (
    REPO_ROOT / "configurations/robot_lab/t20_20_observer_role_evaluator.json"
)
FIXTURE_PATH = REPO_ROOT / "configurations/robot_lab/t20_21_paired_trace_runner.json"


def resign(payload: dict) -> dict:
    changed = copy.deepcopy(payload)
    changed.pop("identity_sha256", None)
    return sign_payload(changed)


class PairedTraceRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.observer = load_strict_json(OBSERVER_PATH)
        cls.fixture = load_strict_json(FIXTURE_PATH)
        cls.contract = cls.fixture["contract"]
        cls.simulator = cls.fixture["traces"]["simulator"]
        cls.observable = cls.fixture["traces"]["observable"]

    def test_fixture_is_source_bound_and_deterministic(self) -> None:
        verify_paired_trace_runner_fixture(self.fixture, self.observer)
        self.assertEqual(
            self.fixture,
            build_paired_trace_runner_fixture(self.observer),
        )
        self.assertEqual(
            self.fixture["source_observer_fixture_identity_sha256"],
            self.observer["identity_sha256"],
        )

    def test_exact_pair_matches_without_mutating_inputs(self) -> None:
        simulator = copy.deepcopy(self.simulator)
        observable = copy.deepcopy(self.observable)

        result = compare_paired_traces(self.contract, simulator, observable)

        self.assertTrue(result["matched"])
        self.assertTrue(result["downstream_comparison_eligible"])
        self.assertTrue(result["event_time_comparison_eligible"])
        self.assertEqual(result["mismatch_categories"], [])
        self.assertEqual(result["joint_max_abs_error_rad"], 0.0)
        self.assertEqual(result["issued_action_max_abs_error_rad"], 0.0)
        self.assertEqual(result["measured_action_max_abs_error_rad"], 0.0)
        self.assertEqual(result["event_elapsed_time_delta_ns"], {
            "grasp_contact": 0,
            "release_complete": 0,
            "stable_hold": 0,
        })
        self.assertEqual(simulator, self.simulator)
        self.assertEqual(observable, self.observable)

    def test_every_fixed_mismatch_category_is_routed(self) -> None:
        diagnostics = self.fixture["diagnostic_cases"]
        self.assertEqual(set(MISMATCH_CATEGORIES), set(diagnostics))
        for category in MISMATCH_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(
                    category,
                    diagnostics[category]["result"]["mismatch_categories"],
                )
                self.assertFalse(diagnostics[category]["result"]["matched"])
                self.assertFalse(
                    diagnostics[category]["result"]["calibration_update_selected"]
                )
                self.assertFalse(
                    diagnostics[category]["result"]["twin_update_selected"]
                )
        self.assertFalse(
            diagnostics["clock_source_mismatch"]["result"][
                "event_time_comparison_eligible"
            ]
        )

    def test_action_variants_remain_distinct(self) -> None:
        issued = self.fixture["diagnostic_cases"]["issued_action_mismatch"]["result"]
        measured = self.fixture["diagnostic_cases"]["measured_action_mismatch"][
            "result"
        ]
        proposed = self.fixture["diagnostic_cases"]["proposed_command_mismatch"][
            "result"
        ]

        self.assertIn("issued_action_mismatch", issued["mismatch_categories"])
        self.assertNotIn("measured_action_mismatch", issued["mismatch_categories"])
        self.assertIn("measured_action_mismatch", measured["mismatch_categories"])
        self.assertNotIn("issued_action_mismatch", measured["mismatch_categories"])
        self.assertFalse(proposed["proposed_command_sequence_identical"])

    def test_missing_action_variant_and_role_order_fail_closed(self) -> None:
        observable = copy.deepcopy(self.observable)
        observable["frames"][1].pop("measured_action_rad")
        observable = resign(observable)
        with self.assertRaisesRegex(ValueError, "missing frame field"):
            compare_paired_traces(self.contract, self.simulator, observable)

        with self.assertRaisesRegex(ValueError, "simulator_privileged"):
            compare_paired_traces(self.contract, self.observable, self.simulator)

        aliased = copy.deepcopy(self.observable)
        aliased["trace_id"] = self.simulator["trace_id"]
        with self.assertRaisesRegex(ValueError, "distinct trace_id"):
            compare_paired_traces(self.contract, self.simulator, resign(aliased))

    def test_signed_mutation_and_malformed_values_are_rejected(self) -> None:
        mutated = copy.deepcopy(self.observable)
        mutated["frames"][1]["joint_position_rad"][0] = 0.11
        with self.assertRaisesRegex(ValueError, "identity hash"):
            compare_paired_traces(self.contract, self.simulator, mutated)

        nonfinite = copy.deepcopy(self.observable)
        nonfinite["frames"][0]["joint_position_rad"][0] = math.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            compare_paired_traces(self.contract, self.simulator, nonfinite)

        wrong_width = copy.deepcopy(self.observable)
        wrong_width["q0_rad"] = [0.0] * 5
        with self.assertRaisesRegex(ValueError, "six values"):
            compare_paired_traces(self.contract, self.simulator, resign(wrong_width))

    def test_temporal_event_and_field_spoofs_are_rejected(self) -> None:
        false_q0 = copy.deepcopy(self.observable)
        false_q0["q0_rad"][0] = 0.02
        with self.assertRaisesRegex(ValueError, "first joint position"):
            compare_paired_traces(self.contract, self.simulator, resign(false_q0))

        nonmonotonic = copy.deepcopy(self.observable)
        nonmonotonic["frames"][2]["timestamp_ns"] = 50_000_000
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            compare_paired_traces(
                self.contract, self.simulator, resign(nonmonotonic)
            )

        duplicate = copy.deepcopy(self.observable)
        duplicate["frames"][1]["events"].append("grasp_contact")
        with self.assertRaisesRegex(ValueError, "duplicate event"):
            compare_paired_traces(self.contract, self.simulator, resign(duplicate))

        pixels = copy.deepcopy(self.observable)
        pixels["frames"][0]["image_rgb"] = "not-allowed"
        with self.assertRaisesRegex(ValueError, "undeclared frame field"):
            compare_paired_traces(self.contract, self.simulator, resign(pixels))

        privileged = copy.deepcopy(self.observable)
        privileged["frames"][0]["object_position_m"] = [0.0, 0.0, 0.0]
        with self.assertRaisesRegex(ValueError, "role leakage"):
            compare_paired_traces(self.contract, self.simulator, resign(privileged))

    def test_fixture_withholds_physical_and_update_authority(self) -> None:
        self.assertFalse(self.fixture["hardware_observation_performed"])
        self.assertFalse(self.fixture["live_robot_executed"])
        self.assertFalse(self.fixture["calibration_updated"])
        self.assertFalse(self.fixture["twin_updated"])
        self.assertFalse(self.fixture["physical_qualification_granted"])
        self.assertFalse(self.fixture["simulation_policy_accepted"])

        drifted = copy.deepcopy(self.fixture)
        drifted["twin_updated"] = True
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_paired_trace_runner_fixture(resign(drifted), self.observer)

        drifted_contract = copy.deepcopy(self.contract)
        drifted_contract["thresholds"]["joint_max_abs_error_rad"] = 1.0
        with self.assertRaisesRegex(ValueError, "contract drifted"):
            compare_paired_traces(
                resign(drifted_contract), self.simulator, self.observable
            )


if __name__ == "__main__":
    unittest.main()
