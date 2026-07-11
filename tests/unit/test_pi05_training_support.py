from __future__ import annotations

import copy
import math
import unittest

from scenesmith.robot_lab.pi05_training_support import (
    JOINT_ORDER,
    STATE_STATISTIC_ORDER,
    build_state_support_audit,
    verify_state_support_audit,
)


NORMALIZER_SHA256 = "a" * 64


def _source() -> dict:
    return {
        "checkpoint_processor_snapshot": {
            "checkpoint_config": {
                "normalization_mapping": {
                    "ACTION": "MEAN_STD",
                    "STATE": "MEAN_STD",
                    "VISUAL": "IDENTITY",
                }
            },
            "files": [
                {
                    "filename": (
                        "policy_preprocessor_step_2_"
                        "normalizer_processor.safetensors"
                    ),
                    "sha256": NORMALIZER_SHA256,
                }
            ],
        }
    }


def _statistics() -> dict:
    q10 = [-2.0] * 6
    q10[3] = -1.0
    q90 = [2.0] * 6
    q90[3] = 1.0
    q99 = [3.0] * 6
    q99[3] = 1.5
    return {
        "count": 100.0,
        "min": [-4.0, -4.0, -4.0, -2.0, -4.0, -4.0],
        "q01": [-3.0, -3.0, -3.0, -1.5, -3.0, -3.0],
        "q10": q10,
        "q50": [0.0] * 6,
        "q90": q90,
        "q99": q99,
        "max": [4.0, 4.0, 4.0, 2.0, 4.0, 4.0],
        "mean": [0.0] * 6,
        "std": [1.0] * 6,
    }


STATE_VALUES = [0.0, 0.5, -0.5, -3.0, 0.9, 1.1]
NORMALIZED_VALUES = list(STATE_VALUES)
DISCRETIZED_VALUES = [128, 192, 64, -1, 243, 255]


class Pi05TrainingSupportTests(unittest.TestCase):
    def build(self, *, statistics: dict | None = None, source: dict | None = None) -> dict:
        return build_state_support_audit(
            statistics or _statistics(),
            state_values=STATE_VALUES,
            normalized_values=NORMALIZED_VALUES,
            discretized_values=DISCRETIZED_VALUES,
            source_contract=source or _source(),
        )

    def verify(self, payload: dict, *, source: dict | None = None) -> None:
        verify_state_support_audit(
            payload,
            state_values=STATE_VALUES,
            discretized_values=DISCRETIZED_VALUES,
            source=source or _source(),
        )

    def test_build_and_verify_classifies_support_not_standard_deviation(self) -> None:
        payload = self.build()
        self.verify(payload)
        self.assertEqual(payload["statistic_order"], STATE_STATISTIC_ORDER)
        self.assertEqual(payload["summary"]["outside_mean_plus_minus_std_joints"], [
            "wrist_flex",
            "gripper",
        ])
        self.assertEqual(payload["summary"]["outside_observed_min_max_joints"], [
            "wrist_flex"
        ])
        joints = {item["joint_name"]: item for item in payload["joints"]}
        self.assertEqual(
            joints["wrist_flex"]["support_class"],
            "outside_observed_training_min_max",
        )
        self.assertEqual(joints["gripper"]["support_class"], "within_q01_q99")

    def test_joint_order_is_exact(self) -> None:
        payload = self.build()
        self.assertEqual([item["joint_name"] for item in payload["joints"]], JOINT_ORDER)

    def test_missing_statistic_is_rejected(self) -> None:
        statistics = _statistics()
        statistics.pop("q99")
        with self.assertRaises(ValueError):
            self.build(statistics=statistics)

    def test_nonfinite_statistic_is_rejected(self) -> None:
        statistics = _statistics()
        statistics["q50"][0] = math.inf
        with self.assertRaises(ValueError):
            self.build(statistics=statistics)

    def test_unordered_quantiles_are_rejected(self) -> None:
        statistics = _statistics()
        statistics["q99"][0] = -3.5
        with self.assertRaises(ValueError):
            self.build(statistics=statistics)

    def test_nonpositive_standard_deviation_is_rejected(self) -> None:
        statistics = _statistics()
        statistics["std"][0] = 0.0
        with self.assertRaises(ValueError):
            self.build(statistics=statistics)

    def test_normalized_value_drift_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_state_support_audit(
                _statistics(),
                state_values=STATE_VALUES,
                normalized_values=[*NORMALIZED_VALUES[:-1], 0.0],
                discretized_values=DISCRETIZED_VALUES,
                source_contract=_source(),
            )

    def test_discretized_value_drift_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_state_support_audit(
                _statistics(),
                state_values=STATE_VALUES,
                normalized_values=NORMALIZED_VALUES,
                discretized_values=[127, *DISCRETIZED_VALUES[1:]],
                source_contract=_source(),
            )

    def test_checkpoint_normalization_mode_drift_is_rejected(self) -> None:
        payload = self.build()
        source = _source()
        source["checkpoint_processor_snapshot"]["checkpoint_config"][
            "normalization_mapping"
        ]["STATE"] = "QUANTILES"
        with self.assertRaises(ValueError):
            self.verify(payload, source=source)

    def test_normalizer_file_substitution_is_rejected(self) -> None:
        payload = self.build()
        source = _source()
        source["checkpoint_processor_snapshot"]["files"][0]["sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            self.verify(payload, source=source)

    def test_hard_domain_relabel_is_rejected(self) -> None:
        payload = self.build()
        payload["discretizer"]["reference_interval_is_hard_validity_domain"] = True
        with self.assertRaises(ValueError):
            self.verify(payload)

    def test_clipping_relabel_is_rejected(self) -> None:
        payload = self.build()
        payload["clipping_applied"] = True
        with self.assertRaises(ValueError):
            self.verify(payload)

    def test_wrist_false_acceptance_is_rejected(self) -> None:
        payload = self.build()
        payload["joints"][3]["support_class"] = "within_q01_q99"
        with self.assertRaises(ValueError):
            self.verify(payload)

    def test_gripper_false_rejection_is_rejected(self) -> None:
        payload = self.build()
        payload["summary"]["outside_observed_min_max_joints"].append("gripper")
        with self.assertRaises(ValueError):
            self.verify(payload)

    def test_policy_shadow_or_actuation_escalation_is_rejected(self) -> None:
        for field in (
            "policy_shadow_input_valid_granted",
            "physical_policy_actuation_eligible",
        ):
            with self.subTest(field=field):
                payload = self.build()
                payload["summary"][field] = True
                with self.assertRaises(ValueError):
                    self.verify(payload)


if __name__ == "__main__":
    unittest.main()
