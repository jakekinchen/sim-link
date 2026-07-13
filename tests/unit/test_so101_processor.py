"""Tests for the named canonical SO-101 processor."""

from __future__ import annotations

import math
import random
import unittest

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.so101_coordinates import mujoco_to_lerobot
from scenesmith.robot_lab.so101_processor import (
    ACTION_MODE,
    CANONICAL_REPRESENTATION,
    CONTRACT_PATH,
    JOINT_NAMES,
    MUJOCO_REPRESENTATION,
    CanonicalSO101Processor,
    REPO_ROOT,
    build_so101_processor_contract,
    verify_so101_processor_contract,
)


class SO101ProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = CanonicalSO101Processor()

    def test_checked_contract_is_deterministic_and_bounded(self) -> None:
        payload = load_strict_json(REPO_ROOT / CONTRACT_PATH)
        verify_so101_processor_contract(payload, repo_root=REPO_ROOT)
        self.assertEqual(payload, build_so101_processor_contract(repo_root=REPO_ROOT))
        self.assertFalse(payload["normalization_bundle_valid"])
        self.assertFalse(payload["compiled_training_frames"])
        self.assertFalse(payload["simulation_training_ready"])

    def test_randomized_round_trip(self) -> None:
        generator = random.Random(1702)
        for _ in range(256):
            source = [
                generator.uniform(low, high)
                for low, high in self.processor.limits(MUJOCO_REPRESENTATION)
            ]
            canonical = self.processor.transform(
                source,
                source_representation=MUJOCO_REPRESENTATION,
                target_representation=CANONICAL_REPRESENTATION,
            )
            replay = self.processor.transform(
                canonical,
                source_representation=CANONICAL_REPRESENTATION,
                target_representation=MUJOCO_REPRESENTATION,
            )
            for expected, observed in zip(source, replay, strict=True):
                self.assertAlmostEqual(expected, observed, places=12)

    def test_permuted_joint_order_is_rejected(self) -> None:
        names = list(JOINT_NAMES)
        names[0], names[1] = names[1], names[0]
        with self.assertRaisesRegex(ValueError, "permuted"):
            self.processor.transform(
                [0.0] * 6,
                source_representation=MUJOCO_REPRESENTATION,
                target_representation=CANONICAL_REPRESENTATION,
                ordered_joint_names=names,
            )

    def test_action_mode_is_explicit_absolute_only(self) -> None:
        with self.assertRaisesRegex(ValueError, "absolute action mode only"):
            self.processor.validate(
                [0.0] * 6,
                representation=CANONICAL_REPRESENTATION,
                action_mode="delta",
            )

    def test_pure_transform_does_not_clamp(self) -> None:
        source = self.processor.transform(
            [0.0, -0.55, 1.05, -0.48, 0.0, 0.35],
            source_representation=MUJOCO_REPRESENTATION,
            target_representation=CANONICAL_REPRESENTATION,
        )
        source[5] = 120.0
        transformed = self.processor.transform(
            source,
            source_representation=CANONICAL_REPRESENTATION,
            target_representation=MUJOCO_REPRESENTATION,
        )
        self.assertGreater(
            transformed[5], self.processor.limits(MUJOCO_REPRESENTATION)[5][1]
        )
        with self.assertRaisesRegex(ValueError, "gripper is outside"):
            self.processor.validate(
                source, representation=CANONICAL_REPRESENTATION
            )

    def test_safety_limiting_logs_requested_and_executed(self) -> None:
        requested = self.processor.transform(
            [0.0, -0.55, 1.05, -0.48, 0.0, 0.35],
            source_representation=MUJOCO_REPRESENTATION,
            target_representation=CANONICAL_REPRESENTATION,
        )
        requested[5] = 120.0
        original = requested.copy()
        result = self.processor.limit(
            requested, representation=CANONICAL_REPRESENTATION
        )
        self.assertEqual(requested, original)
        self.assertEqual(result["requested_values"], original)
        self.assertEqual(result["executed_values"][5], 100.0)
        self.assertEqual(result["clipped_indices"], [5])
        self.assertEqual(result["clipped_joint_names"], ["gripper"])
        self.assertTrue(result["safety_limited"])

    def test_gripper_transform_is_monotonic(self) -> None:
        values = []
        for gripper in (-0.17453, 0.35, 1.74533):
            values.append(
                self.processor.transform(
                    [0.0] * 5 + [gripper],
                    source_representation=MUJOCO_REPRESENTATION,
                    target_representation=CANONICAL_REPRESENTATION,
                )[5]
            )
        self.assertLess(values[0], values[1])
        self.assertLess(values[1], values[2])

    def test_golden_pose_matches_legacy_in_range_mapping(self) -> None:
        source = [0.0, -0.55, 1.05, -0.48, 0.0, 0.35]
        observed = self.processor.transform(
            source,
            source_representation=MUJOCO_REPRESENTATION,
            target_representation=CANONICAL_REPRESENTATION,
        )
        expected = mujoco_to_lerobot(source)
        for left, right in zip(observed, expected, strict=True):
            self.assertAlmostEqual(left, right, places=12)

    def test_non_finite_and_boolean_values_are_rejected(self) -> None:
        for bad in (float("nan"), float("inf"), True):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "finite numbers"):
                    self.processor.transform(
                        [0.0] * 5 + [bad],
                        source_representation=MUJOCO_REPRESENTATION,
                        target_representation=CANONICAL_REPRESENTATION,
                    )

    def test_malformed_containers_fail_with_contract_errors(self) -> None:
        for bad in (None, 1.0, {name: 0.0 for name in JOINT_NAMES}):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "exactly six ordered values"):
                    self.processor.transform(
                        bad,
                        source_representation=MUJOCO_REPRESENTATION,
                        target_representation=CANONICAL_REPRESENTATION,
                    )
        with self.assertRaisesRegex(ValueError, "joint names are missing"):
            self.processor.transform(
                [0.0] * 6,
                source_representation=MUJOCO_REPRESENTATION,
                target_representation=CANONICAL_REPRESENTATION,
                ordered_joint_names=None,
            )

    def test_limits_accept_exact_endpoints(self) -> None:
        for representation in (MUJOCO_REPRESENTATION, CANONICAL_REPRESENTATION):
            lows = [bounds[0] for bounds in self.processor.limits(representation)]
            highs = [bounds[1] for bounds in self.processor.limits(representation)]
            self.assertEqual(self.processor.validate(lows, representation=representation), lows)
            self.assertEqual(self.processor.validate(highs, representation=representation), highs)


if __name__ == "__main__":
    unittest.main()
