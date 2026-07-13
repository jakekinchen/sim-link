"""Tests for the v2 antipodal-contact strict grasp gate."""

from __future__ import annotations

import copy
import math
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.strict_grasp import (
    analytic_grasp_trajectory,
    build_strict_grasp_v2_fixture,
    evaluate_antipodal_contact_witness,
    evaluate_strict_grasp,
    strict_grasp_spec_v2,
    verify_strict_grasp_v2_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
V1_FIXTURE = REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator.fixture.json"
V2_FIXTURE = (
    REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json"
)
V1_IDENTITY = "4f0bad3c9f12fc648a7eed25a9f9fcaf7b8a1c63ca312e3a13f2c20d0f3120d8"


class StrictGraspV2Tests(unittest.TestCase):
    def test_v2_positive_passes_antipodal_proxy_without_policy_relabel(self) -> None:
        spec = strict_grasp_spec_v2()
        trajectory = analytic_grasp_trajectory(spec)

        result = evaluate_strict_grasp(
            spec,
            trajectory,
            claimed_proof_mode="analytic_expert",
        )

        self.assertTrue(result["strict_grasp_success"])
        self.assertFalse(result["pure_policy_success"])
        self.assertTrue(result["antipodal_contact_proxy_valid"])

    def test_missing_short_same_side_and_nonfinite_witnesses_fail(self) -> None:
        spec = strict_grasp_spec_v2()
        base = analytic_grasp_trajectory(spec)
        cases = {}

        missing = copy.deepcopy(base)
        missing[3].pop("contact_geometry_witness")
        cases["missing"] = missing

        short = copy.deepcopy(base)
        short[3]["contact_geometry_witness"]["contact_points_m"][1] = [-0.005, 0, 0]
        cases["short"] = short

        same_side = copy.deepcopy(base)
        same_side[3]["contact_geometry_witness"]["contact_normals"][1] = [1, 0, 0]
        cases["same_side"] = same_side

        nonfinite = copy.deepcopy(base)
        nonfinite[3]["contact_geometry_witness"]["contact_points_m"][0][0] = math.nan
        cases["nonfinite"] = nonfinite

        same_jaw = copy.deepcopy(base)
        same_jaw[3]["contact_geometry_witness"]["jaw_ids"] = ["jaw", "jaw"]
        cases["same_jaw"] = same_jaw

        misaligned = copy.deepcopy(base)
        misaligned[3]["contact_geometry_witness"]["contact_normals"] = [
            [0, 1, 0],
            [0, -1, 0],
        ]
        cases["misaligned"] = misaligned

        for name, trajectory in cases.items():
            with self.subTest(name=name):
                result = evaluate_strict_grasp(
                    spec,
                    trajectory,
                    claimed_proof_mode="analytic_expert",
                )
                self.assertFalse(result["strict_grasp_success"])
                self.assertIn(
                    "antipodal_contact_geometry_invalid",
                    result["failure_reasons"],
                )

    def test_checked_v2_fixture_is_deterministic_and_v1_is_unchanged(self) -> None:
        v1 = load_strict_json(V1_FIXTURE)
        v2 = load_strict_json(V2_FIXTURE)

        self.assertEqual(v1["identity_sha256"], V1_IDENTITY)
        verify_strict_grasp_v2_fixture(v2)
        self.assertEqual(v2, build_strict_grasp_v2_fixture())
        self.assertTrue(v2["positive"]["evaluation"]["strict_grasp_success"])
        self.assertTrue(v2["all_negatives_rejected_for_expected_reason"])
        self.assertFalse(v2["actual_mujoco_grasp_success"])
        self.assertFalse(v2["simulation_training_ready"])

    def test_witness_evaluator_reports_measured_geometry(self) -> None:
        spec = strict_grasp_spec_v2()
        witness = analytic_grasp_trajectory(spec)[3]["contact_geometry_witness"]

        result = evaluate_antipodal_contact_witness(
            witness,
            spec["antipodal_contact_requirement"],
        )

        self.assertTrue(result["valid"])
        self.assertAlmostEqual(result["contact_span_m"], 0.03)
        self.assertAlmostEqual(result["normal_dot"], -1.0)


if __name__ == "__main__":
    unittest.main()
