"""Focused tests for the canonical SO-101 coordinate bridge."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.so101_coordinates import BODY_JOINT_OFFSETS_DEG


class SO101CoordinateTests(unittest.TestCase):
    def test_legacy_policy_dataset_offsets_remain_unchanged(self) -> None:
        self.assertEqual(BODY_JOINT_OFFSETS_DEG, (0.0, -105.85, 89.58, 0.0, 0.0))

if __name__ == "__main__":
    unittest.main()
