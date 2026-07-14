"""Tests for the bounded T20.19 recovery-controller ensemble."""

from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_19_discrete_recovery_ensemble import (
    build_cell_manifest,
    build_scorecard,
    transform_actions,
    verify_cell_manifest,
    verify_scorecard,
)


class T2019DiscreteRecoveryEnsembleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = build_cell_manifest(
            recovery_manifest_identity_sha256="a" * 64,
            recovery_package_identity_sha256="b" * 64,
            source_branch_id="c" * 64,
        )

    def test_manifest_has_exact_one_factor_only_twelve_cell_grid(self) -> None:
        verify_cell_manifest(self.manifest)
        self.assertEqual(self.manifest["cell_count"], 12)
        self.assertEqual(self.manifest["cells"][0]["cell_id"], "nominal")
        self.assertEqual(
            [row["factor"] for row in self.manifest["cells"]],
            [
                "nominal",
                "cube_x_offset_m",
                "cube_x_offset_m",
                "cube_y_offset_m",
                "cube_y_offset_m",
                "object_friction_multiplier",
                "object_friction_multiplier",
                "command_delay_frames",
                "command_delay_frames",
                "action_hold_frames",
                "gripper_command_scale",
                "gripper_command_scale",
            ],
        )
        interaction = copy.deepcopy(self.manifest)
        interaction["cells"][1]["value"] = {"x": 0.004, "friction": 1.2}
        with self.assertRaisesRegex(ValueError, "finite|factor|value"):
            verify_cell_manifest(sign_payload(interaction))
        out_of_bounds = copy.deepcopy(self.manifest)
        out_of_bounds["cells"][1]["value"] = 0.005
        with self.assertRaisesRegex(ValueError, "bound|drift"):
            verify_cell_manifest(sign_payload(out_of_bounds))

    def test_delay_hold_and_gripper_transforms_are_fixed_length_and_explicit(self) -> None:
        actions = [[float(index)] * 5 + [1.0 + index] for index in range(5)]
        initial = [-1.0] * 6
        cells = {row["cell_id"]: row for row in self.manifest["cells"]}
        delayed, provenance = transform_actions(actions, cells["command_delay_2"], initial)
        self.assertEqual(len(delayed), len(actions))
        self.assertEqual(delayed[:2], [initial, initial])
        self.assertEqual(delayed[2:], actions[:-2])
        self.assertEqual(provenance, "deterministic_command_delay")
        held, provenance = transform_actions(actions, cells["action_hold_2"], initial)
        self.assertEqual(held, [actions[0], actions[0], actions[2], actions[2], actions[4]])
        self.assertEqual(provenance, "deterministic_action_hold")
        scaled, provenance = transform_actions(actions, cells["gripper_scale_high"], initial)
        self.assertEqual([row[:5] for row in scaled], [row[:5] for row in actions])
        self.assertAlmostEqual(scaled[0][5], 1.05)
        self.assertEqual(provenance, "deterministic_gripper_scale")
        nominal, provenance = transform_actions(actions, cells["nominal"], initial)
        self.assertEqual(nominal, actions)
        self.assertEqual(provenance, "measured_source")

    def test_scorecard_is_derived_and_orders_worst_cell_deterministically(self) -> None:
        results = []
        for index, cell in enumerate(self.manifest["cells"]):
            success = index < 8
            trace = f"{index + 1:064x}"
            results.append(
                {
                    "cell_id": cell["cell_id"],
                    "first_trace_sha256": trace,
                    "second_trace_sha256": trace,
                    "simulation_semantic_strict_success": success,
                    "strict_contact_frame_count": 136 if success else index,
                    "maximum_anchor_lift_m": 0.036 if success else index / 10000,
                    "terminal_outcome": "strict_success" if success else "no_strict_grasp_contact",
                }
            )
        scorecard = build_scorecard(self.manifest, results)
        verify_scorecard(scorecard, self.manifest)
        self.assertEqual(scorecard["success_count"], 8)
        self.assertEqual(scorecard["success_rate"], 8 / 12)
        self.assertTrue(scorecard["nominal_strict_success"])
        self.assertEqual(scorecard["worst_cell_id"], "command_delay_2")
        self.assertFalse(scorecard["posterior_calibrated"])
        drift = copy.deepcopy(scorecard)
        drift["success_count"] = 12
        with self.assertRaisesRegex(ValueError, "drift"):
            verify_scorecard(sign_payload(drift), self.manifest)

    def test_replay_and_authority_escalation_fail_closed(self) -> None:
        results = []
        for index, cell in enumerate(self.manifest["cells"]):
            results.append(
                {
                    "cell_id": cell["cell_id"],
                    "first_trace_sha256": f"{index + 1:064x}",
                    "second_trace_sha256": f"{index + 1:064x}",
                    "simulation_semantic_strict_success": True,
                    "strict_contact_frame_count": 136,
                    "maximum_anchor_lift_m": 0.036,
                    "terminal_outcome": "strict_success",
                }
            )
        results[1]["second_trace_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "replay"):
            build_scorecard(self.manifest, results)
        elevated = copy.deepcopy(self.manifest)
        elevated["posterior_calibrated"] = True
        with self.assertRaisesRegex(ValueError, "authority"):
            verify_cell_manifest(sign_payload(elevated))


if __name__ == "__main__":
    unittest.main()
