import copy
import math
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.quantitative_strict_v2_receipt import (
    build_quantitative_margin,
    build_quantitative_receipt,
    load_verified_sources,
    summarize_predicates,
)


class QuantitativeStrictV2ReceiptTest(unittest.TestCase):
    def test_directional_and_range_margins_have_one_sign_convention(self) -> None:
        cases = [
            ("lower", 3.0, "gte", 2.0, 2.0, 0.5, True),
            ("lower_boundary", 2.0, "gte", 2.0, 2.0, 0.0, True),
            ("upper", 3.0, "lte", 5.0, 5.0, 0.4, True),
            ("upper_boundary", 5.0, "lte", 5.0, 5.0, 0.0, True),
            ("range", 3.0, "range", [2.0, 5.0], 2.0, 0.5, True),
            ("lower_fail", 1.0, "gte", 2.0, 2.0, -0.5, False),
            ("upper_fail", 6.0, "lte", 5.0, 5.0, -0.2, False),
            ("range_fail", 6.0, "range", [2.0, 5.0], 2.0, -0.5, False),
        ]
        for predicate, observed, comparator, threshold, scale, margin, passed in cases:
            with self.subTest(predicate=predicate):
                row = build_quantitative_margin(
                    predicate_id=predicate,
                    observed_value=observed,
                    comparator=comparator,
                    threshold=threshold,
                    normalization_scale=scale,
                    units="unit",
                )
                self.assertAlmostEqual(row["normalized_signed_margin"], margin)
                self.assertEqual(row["effective_passed"], passed)

    def test_equality_and_guards_fail_closed_without_compensation(self) -> None:
        passed = build_quantitative_margin(
            predicate_id="hard_guard",
            observed_value=True,
            comparator="eq",
            threshold=True,
            normalization_scale=1.0,
            units="boolean",
        )
        blocked = build_quantitative_margin(
            predicate_id="hard_guard",
            observed_value=True,
            comparator="eq",
            threshold=True,
            normalization_scale=1.0,
            units="boolean",
            actor_valid=False,
            evidence_valid=False,
        )
        self.assertEqual(passed["normalized_signed_margin"], 1.0)
        self.assertTrue(passed["effective_passed"])
        self.assertFalse(blocked["effective_passed"])
        self.assertEqual(
            blocked["blocking_reasons"],
            ["actor_guard_failed", "evidence_guard_failed"],
        )
        summary = summarize_predicates(
            predicates=[blocked],
            source_strict_success=False,
        )
        self.assertEqual(summary["hard_guard_blocker_count"], 1)
        self.assertEqual(summary["effective_bottleneck"]["kind"], "hard_guard")
        self.assertEqual(
            summary["effective_bottleneck"]["predicate_id"], "hard_guard"
        )
        self.assertIsNone(
            summary["effective_bottleneck"]["normalized_signed_margin"]
        )

    def test_genuine_conjunction_contradiction_fails_closed(self) -> None:
        passed = build_quantitative_margin(
            predicate_id="declared_success",
            observed_value=True,
            comparator="eq",
            threshold=True,
            normalization_scale=1.0,
            units="boolean",
        )
        with self.assertRaisesRegex(ValueError, "contradicts source evaluator"):
            summarize_predicates(
                predicates=[passed],
                source_strict_success=False,
            )

    def test_missing_bound_sources_fail_before_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                load_verified_sources(repo_root=Path(directory))

    def test_nonfinite_zero_scale_and_inverted_ranges_fail(self) -> None:
        common = {
            "predicate_id": "bad",
            "observed_value": 1.0,
            "comparator": "gte",
            "threshold": 0.0,
            "normalization_scale": 1.0,
            "units": "unit",
        }
        for mutation in (
            {"observed_value": math.nan},
            {"threshold": math.inf},
            {"normalization_scale": 0.0},
            {"normalization_scale": -1.0},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    build_quantitative_margin(**{**common, **mutation})
        with self.assertRaises(ValueError):
            build_quantitative_margin(
                **{
                    **common,
                    "comparator": "range",
                    "threshold": [2.0, 1.0],
                }
            )

    def test_example_receipt_matches_source_without_overclaiming(self) -> None:
        sources = load_verified_sources()
        receipt = build_quantitative_receipt(sources=sources)
        self.assertTrue(receipt["hard_conjunction_passed"])
        self.assertTrue(receipt["source_strict_success_agrees"])
        self.assertFalse(receipt["pure_policy_success"])
        self.assertFalse(receipt["actual_mujoco_grasp_success"])
        self.assertFalse(receipt["physical_proof"])
        self.assertFalse(receipt["average_or_compensating_pass_allowed"])
        self.assertEqual(receipt["hard_guard_blockers"], [])
        self.assertEqual(receipt["hard_guard_blocker_count"], 0)
        self.assertEqual(
            receipt["effective_bottleneck"]["kind"], "normalized_margin"
        )
        self.assertGreater(receipt["predicate_count"], 25)
        minimum = min(
            receipt["predicates"],
            key=lambda row: row["normalized_signed_margin"],
        )
        self.assertEqual(receipt["bottleneck_predicate_id"], minimum["predicate_id"])

    def test_signed_source_drift_fails_before_receipt(self) -> None:
        sources = load_verified_sources()
        drift = copy.deepcopy(sources)
        drift["fixture"] = copy.deepcopy(sources["fixture"])
        drift["fixture"]["positive"]["evaluation"]["strict_grasp_success"] = False
        with self.assertRaises(ValueError):
            build_quantitative_receipt(sources=drift)


if __name__ == "__main__":
    unittest.main()
