"""Tests for the nominal contact-span and contact-property sweep."""

from __future__ import annotations

import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.mujoco_contact_property_sweep import (
    build_mujoco_contact_property_sweep,
    verify_mujoco_contact_property_sweep,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "configurations/robot_lab/mujoco_contact_property_sweep.json"


class MujocoContactPropertySweepTests(unittest.TestCase):
    def test_checked_sweep_is_deterministic_and_source_bound(self) -> None:
        payload = load_strict_json(ARTIFACT)

        verify_mujoco_contact_property_sweep(payload)
        self.assertEqual(payload, build_mujoco_contact_property_sweep())
        self.assertEqual(
            payload["source_contact_search_identity_sha256"],
            "abf05433677d9ac367a44622dd1544c99a766c47e27d2288acfcf4c949ad74cd",
        )
        self.assertTrue(payload["baseline_two_pass_exact_determinism"])
        self.assertFalse(payload["physical_measurement_claimed"])

    def test_contact_span_is_metric_but_not_physical_aperture(self) -> None:
        payload = load_strict_json(ARTIFACT)

        low, high = payload["contact_span_range_m"]
        self.assertGreater(low, 0.0)
        self.assertGreaterEqual(high, low)
        self.assertEqual(
            payload["metric_profile_scope"],
            "mujoco_contact_point_span_not_physical_aperture",
        )
        self.assertFalse(payload["metric_physical_gripper_aperture_profile_complete"])

    def test_training_grid_and_untouched_holdout_do_not_grant_success(self) -> None:
        payload = load_strict_json(ARTIFACT)

        self.assertEqual(payload["training_grid"]["candidate_count"], 12)
        self.assertTrue(payload["holdout"]["excluded_from_selection"])
        self.assertEqual(payload["training_success_count"], 0)
        self.assertIsNone(payload["selected_training_candidate"])
        self.assertFalse(payload["holdout"]["result"]["unassisted_lift_clearance_maintained"])
        self.assertFalse(payload["unassisted_mujoco_grasp_success"])
        self.assertFalse(payload["simulation_training_ready"])


if __name__ == "__main__":
    unittest.main()
