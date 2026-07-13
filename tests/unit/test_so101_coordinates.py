"""Focused tests for distinct legacy and physical-pose SO-101 coordinates."""

from __future__ import annotations

import math
import unittest

from scenesmith.robot_lab.so101_coordinates import BODY_JOINT_OFFSETS_DEG
from scenesmith.robot_lab.so101_physical_coordinates import (
    MIDPOINT_DIRECT_BODY_JOINT_OFFSETS_DEG,
    MIDPOINT_DIRECT_BODY_JOINT_SIGNS,
    MIDPOINT_DIRECT_CANDIDATE_SCHEMA_VERSION,
    lerobot_to_midpoint_mujoco_candidate,
    midpoint_direct_candidate_contract,
    midpoint_mujoco_candidate_to_lerobot,
)


class SO101CoordinateTests(unittest.TestCase):
    def test_legacy_policy_dataset_offsets_remain_unchanged(self) -> None:
        self.assertEqual(BODY_JOINT_OFFSETS_DEG, (0.0, -105.85, 89.58, 0.0, 0.0))

    def test_midpoint_direct_candidate_is_separately_versioned_and_scoped(self) -> None:
        contract = midpoint_direct_candidate_contract()

        self.assertEqual(
            contract["schema_version"], MIDPOINT_DIRECT_CANDIDATE_SCHEMA_VERSION
        )
        self.assertEqual(
            contract["body_joint_signs"], list(MIDPOINT_DIRECT_BODY_JOINT_SIGNS)
        )
        self.assertEqual(
            contract["body_joint_offsets_deg"],
            list(MIDPOINT_DIRECT_BODY_JOINT_OFFSETS_DEG),
        )
        self.assertEqual(contract["status"], "offline_diagnostic_candidate")
        self.assertFalse(contract["physical_twin_qualified"])
        self.assertIn("physical_actuation", contract["authority_not_granted"])

    def test_measured_q_after_maps_without_projection_and_round_trips(self) -> None:
        measured = [
            -5.186813186813186,
            -45.53846153846154,
            65.18681318681318,
            41.714285714285715,
            -63.956043956043956,
            7.957244655581948,
        ]

        mujoco = lerobot_to_midpoint_mujoco_candidate(measured)
        expected_body = [math.radians(value) for value in measured[:5]]
        for actual, expected in zip(mujoco[:5], expected_body, strict=True):
            self.assertAlmostEqual(actual, expected)
        round_trip = midpoint_mujoco_candidate_to_lerobot(mujoco)
        for actual, expected in zip(round_trip, measured, strict=True):
            self.assertAlmostEqual(actual, expected)

    def test_midpoint_candidate_rejects_implicit_projection(self) -> None:
        with self.assertRaisesRegex(ValueError, "shoulder_lift"):
            lerobot_to_midpoint_mujoco_candidate([0.0, -101.0, 0.0, 0.0, 0.0, 50.0])

        projected = lerobot_to_midpoint_mujoco_candidate(
            [0.0, -101.0, 0.0, 0.0, 0.0, 50.0],
            allow_limit_projection=True,
        )
        self.assertAlmostEqual(projected[1], math.radians(-100.0), places=5)

    def test_midpoint_candidate_rejects_nonfinite_and_wrong_width(self) -> None:
        for values in (
            [0.0] * 5,
            [0.0] * 7,
            [0.0, 0.0, math.nan, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, math.inf],
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    lerobot_to_midpoint_mujoco_candidate(values)


if __name__ == "__main__":
    unittest.main()
