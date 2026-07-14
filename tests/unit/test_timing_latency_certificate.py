"""T20.22 offline timing and latency certificate tests."""

from __future__ import annotations

import copy
import math
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.timing_latency_certificate import (
    TIMING_MISMATCH_CATEGORIES,
    build_timing_latency_fixture,
    evaluate_timing_certificate,
    verify_timing_latency_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PAIRED_PATH = REPO_ROOT / "configurations/robot_lab/t20_21_paired_trace_runner.json"
FIXTURE_PATH = REPO_ROOT / "configurations/robot_lab/t20_22_timing_latency_certificate.json"


def resign(payload: dict) -> dict:
    changed = copy.deepcopy(payload)
    changed.pop("identity_sha256", None)
    return sign_payload(changed)


class TimingLatencyCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paired = load_strict_json(PAIRED_PATH)
        cls.fixture = load_strict_json(FIXTURE_PATH)
        cls.contract = cls.fixture["contract"]
        cls.certificate = cls.fixture["passing_certificate"]

    def test_fixture_is_source_bound_and_deterministic(self) -> None:
        verify_timing_latency_fixture(self.fixture, self.paired)
        self.assertEqual(self.fixture, build_timing_latency_fixture(self.paired))
        self.assertEqual(
            self.fixture["source_paired_trace_fixture_identity_sha256"],
            self.paired["identity_sha256"],
        )

    def test_passing_certificate_derives_expected_metrics(self) -> None:
        certificate = copy.deepcopy(self.certificate)
        result = evaluate_timing_certificate(self.contract, certificate)

        self.assertTrue(result["timing_valid"])
        self.assertEqual(result["timing_mismatch_categories"], [])
        self.assertEqual(result["maximum_frame_age_ns"], 10_000_000)
        self.assertEqual(result["maximum_frame_skew_ns"], 2_000_000)
        self.assertEqual(result["maximum_observation_assembly_ns"], 5_000_000)
        self.assertEqual(result["maximum_action_transport_ns"], 5_000_000)
        self.assertEqual(result["minimum_action_hold_ns"], 50_000_000)
        self.assertEqual(result["maximum_action_hold_ns"], 50_000_000)
        self.assertEqual(result["mean_control_period_ns"], 100_000_000)
        self.assertEqual(result["maximum_control_jitter_ns"], 0)
        self.assertEqual(result["maximum_inference_latency_ns"], 20_000_000)
        self.assertEqual(result["observation_drop_count"], 0)
        self.assertEqual(result["deadline_miss_count"], 0)
        self.assertFalse(result["dynamics_error_attribution_blocked_by_timing"])
        self.assertFalse(result["dynamics_error_proven"])
        result["clock_sources"]["sensor_a"] = "changed_after_evaluation"
        self.assertEqual(certificate, self.certificate)

    def test_all_fixed_timing_mismatches_are_routed_and_block_dynamics(self) -> None:
        diagnostics = self.fixture["diagnostic_cases"]
        self.assertEqual(set(diagnostics), set(TIMING_MISMATCH_CATEGORIES))
        for category in TIMING_MISMATCH_CATEGORIES:
            with self.subTest(category=category):
                result = diagnostics[category]["result"]
                self.assertIn(category, result["timing_mismatch_categories"])
                self.assertFalse(result["timing_valid"])
                self.assertTrue(
                    result["dynamics_error_attribution_blocked_by_timing"]
                )
                self.assertFalse(result["dynamics_error_proven"])
                self.assertFalse(result["calibration_update_selected"])
                self.assertFalse(result["twin_update_selected"])

    def test_clock_domain_mismatch_withholds_cross_stream_metrics(self) -> None:
        result = self.fixture["diagnostic_cases"]["clock_domain_mismatch"]["result"]
        self.assertFalse(result["cross_stream_metrics_available"])
        self.assertIsNone(result["maximum_frame_age_ns"])
        self.assertIsNone(result["maximum_action_transport_ns"])
        self.assertIsNone(result["deadline_miss_count"])

    def test_unknown_aggregate_and_clock_keys_fail_closed(self) -> None:
        aggregate = copy.deepcopy(self.certificate)
        aggregate["maximum_frame_age_ns"] = 0
        with self.assertRaisesRegex(ValueError, "undeclared certificate field"):
            evaluate_timing_certificate(self.contract, resign(aggregate))

        clock = copy.deepcopy(self.certificate)
        clock["clock_sources"]["camera"] = "synthetic_monotonic_ns"
        with self.assertRaisesRegex(ValueError, "clock source keys"):
            evaluate_timing_certificate(self.contract, resign(clock))

    def test_invalid_cycle_and_timestamp_semantics_fail_closed(self) -> None:
        noninteger = copy.deepcopy(self.certificate)
        noninteger["samples"][0]["control_cycle_timestamp_ns"] = 100_000_000.0
        with self.assertRaisesRegex(ValueError, "integer nanoseconds"):
            evaluate_timing_certificate(self.contract, resign(noninteger))

        nonfinite = copy.deepcopy(self.certificate)
        nonfinite["samples"][0]["control_cycle_timestamp_ns"] = math.nan
        with self.assertRaisesRegex(ValueError, "integer nanoseconds"):
            evaluate_timing_certificate(self.contract, nonfinite)

        nonmonotonic = copy.deepcopy(self.certificate)
        nonmonotonic["samples"][1]["control_cycle_timestamp_ns"] = (
            nonmonotonic["samples"][0]["control_cycle_timestamp_ns"]
        )
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            evaluate_timing_certificate(self.contract, resign(nonmonotonic))

        duplicate = copy.deepcopy(self.certificate)
        duplicate["samples"][1]["cycle_index"] = 0
        with self.assertRaisesRegex(ValueError, "contiguous"):
            evaluate_timing_certificate(self.contract, resign(duplicate))

        future = copy.deepcopy(self.certificate)
        future["samples"][0]["sensor_frame_timestamps_ns"]["sensor_a"] = (
            future["samples"][0]["control_cycle_timestamp_ns"] + 1
        )
        with self.assertRaisesRegex(ValueError, "future sensor frame"):
            evaluate_timing_certificate(self.contract, resign(future))

        invalid_order = copy.deepcopy(self.certificate)
        invalid_order["samples"][0]["action_issued_timestamp_ns"] = (
            invalid_order["samples"][0]["action_proposed_timestamp_ns"] - 1
        )
        with self.assertRaisesRegex(ValueError, "causal order"):
            evaluate_timing_certificate(self.contract, resign(invalid_order))

        half_inference = copy.deepcopy(self.certificate)
        half_inference["samples"][0]["inference_end_timestamp_ns"] = None
        with self.assertRaisesRegex(ValueError, "both present or both null"):
            evaluate_timing_certificate(self.contract, resign(half_inference))

    def test_signed_mutation_and_contract_drift_are_rejected(self) -> None:
        mutated = copy.deepcopy(self.certificate)
        mutated["samples"][0]["observation_dropped"] = True
        with self.assertRaisesRegex(ValueError, "identity hash"):
            evaluate_timing_certificate(self.contract, mutated)

        contract = copy.deepcopy(self.contract)
        contract["thresholds"]["maximum_frame_age_ns"] = 1_000_000_000
        with self.assertRaisesRegex(ValueError, "contract drifted"):
            evaluate_timing_certificate(resign(contract), self.certificate)

    def test_fixture_withholds_live_physical_and_update_authority(self) -> None:
        self.assertFalse(self.fixture["hardware_observation_performed"])
        self.assertFalse(self.fixture["live_probe_executed"])
        self.assertFalse(self.fixture["clock_synchronization_proven"])
        self.assertFalse(self.fixture["calibration_updated"])
        self.assertFalse(self.fixture["twin_updated"])
        self.assertFalse(self.fixture["physical_qualification_granted"])

        drifted = copy.deepcopy(self.fixture)
        drifted["calibration_updated"] = True
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_timing_latency_fixture(resign(drifted), self.paired)


if __name__ == "__main__":
    unittest.main()
