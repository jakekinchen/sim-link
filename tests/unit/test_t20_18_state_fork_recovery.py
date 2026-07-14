"""Tests for bounded policy-visited MuJoCo recovery branches."""

from __future__ import annotations

import copy
import math
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_18_state_fork_recovery import (
    PHASE_ROLES,
    build_branch_record,
    build_recovery_manifest,
    capture_integration_state,
    restore_integration_state,
    select_parent_snapshots,
    verify_recovery_manifest,
)


class T2018StateForkRecoveryTests(unittest.TestCase):
    def test_mujoco_integration_state_round_trip_is_exact(self) -> None:
        try:
            import mujoco
        except ImportError:
            self.skipTest("requires the pinned MuJoCo runtime")
        model = mujoco.MjModel.from_xml_string(
            """<mujoco><worldbody><body><joint name='j' type='hinge'/>
            <geom type='capsule' size='.02 .1'/></body></worldbody>
            <actuator><motor joint='j'/></actuator></mujoco>"""
        )
        data = mujoco.MjData(model)
        data.time = 1.25
        data.qpos[0] = 0.3
        data.qvel[0] = -0.2
        data.ctrl[0] = 0.1
        mujoco.mj_forward(model, data)
        snapshot = capture_integration_state(
            mujoco,
            model,
            data,
            frame_index=7,
            phase="approach",
            observation_state=[0.3, -0.2],
            requested_action=[0.1],
            applied_action=[0.1],
            object_pose=[0.0, 0.0, 0.1, 1.0, 0.0, 0.0, 0.0],
            source_evaluation_identity_sha256="a" * 64,
        )
        data.time = 9.0
        data.qpos[0] = -0.7
        data.qvel[0] = 0.9
        data.ctrl[0] = -0.4
        restored = restore_integration_state(mujoco, model, data, snapshot)
        self.assertEqual(restored, snapshot["integration_state"])
        self.assertEqual(float(data.time), 1.25)
        self.assertEqual(float(data.qpos[0]), 0.3)
        self.assertEqual(float(data.qvel[0]), -0.2)
        self.assertEqual(float(data.ctrl[0]), 0.1)

    def test_parent_selection_is_deterministic_and_phase_complete(self) -> None:
        phases = (
            ["approach"] * 14
            + ["pregrasp"] * 18
            + ["close"] * 36
            + ["grasp_hold"] * 8
            + ["unassisted_lift"] * 24
            + ["unsupported_lift_hold"] * 12
            + ["recording_stable_hold"] * 64
            + ["lower"] * 24
            + ["release"] * 12
            + ["release_settle"] * 8
            + ["retreat"] * 24
        )
        captures = [self._snapshot(index, phase) for index, phase in enumerate(phases)]
        selected = select_parent_snapshots(captures)
        self.assertEqual([row["phase_role"] for row in selected], list(PHASE_ROLES))
        self.assertEqual(
            [row["frame_index"] for row in selected],
            [6, 49, 71, 205],
        )
        self.assertEqual(selected, select_parent_snapshots(copy.deepcopy(captures)))
        duplicate = copy.deepcopy(captures)
        duplicate[-1] = self._snapshot(0, "retreat")
        with self.assertRaisesRegex(ValueError, "contiguous|duplicate"):
            select_parent_snapshots(duplicate)

    def test_branch_provenance_bounds_and_observed_labels_fail_closed(self) -> None:
        parent = self._snapshot(49, "close")
        parent["phase_role"] = "grasp"
        branch = build_branch_record(
            parent,
            generation_reason="recover_from_policy_close_miss",
            perturbation={"joint_delta_rad": [0.0] * 6},
            measured_actions=[[0.1] * 6, [0.2] * 6],
            action_source_record_ids=["b" * 64, "c" * 64],
            observed_result={
                "simulation_semantic_strict_success": False,
                "strict_contact_frame_count": 3,
                "maximum_anchor_lift_m": 0.001,
            },
            replay_evidence=self._replay(),
        )
        self.assertEqual(branch["outcome_class"], "near_failure")
        self.assertFalse(branch["actions_padded"])
        self.assertFalse(branch["actions_inferred"])
        bad = {"joint_delta_rad": [0.0, 0.0, 0.0, 0.0, 0.0, 0.051]}
        with self.assertRaisesRegex(ValueError, "perturbation"):
            build_branch_record(
                parent,
                generation_reason="too_large",
                perturbation=bad,
                measured_actions=[[0.1] * 6],
                action_source_record_ids=["b" * 64],
                observed_result={
                    "simulation_semantic_strict_success": False,
                    "strict_contact_frame_count": 0,
                    "maximum_anchor_lift_m": 0.0,
                },
                replay_evidence=self._replay(),
            )
        nonfinite = copy.deepcopy(parent)
        nonfinite["integration_state"][0] = math.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            select_parent_snapshots(
                [self._snapshot(i, "approach") if i else nonfinite for i in range(244)]
            )

    def test_manifest_rejects_aliases_tampering_and_authority_escalation(self) -> None:
        parents = [
            dict(self._snapshot(index, phase), phase_role=role)
            for role, index, phase in (
                ("approach", 6, "approach"),
                ("grasp", 49, "close"),
                ("hold", 71, "grasp_hold"),
                ("release", 205, "release"),
            )
        ]
        branches = [
            build_branch_record(
                parent,
                generation_reason=f"bounded_{parent['phase_role']}_correction",
                perturbation={"joint_delta_rad": [0.0] * 6},
                measured_actions=[[0.1] * 6],
                action_source_record_ids=[f"{index + 1:064x}"],
                observed_result={
                    "simulation_semantic_strict_success": index == 0,
                    "strict_contact_frame_count": 1 if index == 1 else 0,
                    "maximum_anchor_lift_m": 0.026 if index == 0 else 0.0,
                },
                replay_evidence=self._replay(),
            )
            for index, parent in enumerate(parents)
        ]
        manifest = build_recovery_manifest(
            source_refs=self._source_refs(),
            t18_4_identity_sha256="d" * 64,
            t20_17_evaluation_identity_sha256="a" * 64,
            t20_17_action_sequence_sha256="e" * 64,
            reproduced_action_sequence_sha256="e" * 64,
            reproduced_terminal_outcome="no_strict_grasp_contact",
            parents=parents,
            branches=branches,
        )
        verify_recovery_manifest(manifest)
        duplicate = copy.deepcopy(manifest)
        duplicate["branches"].append(copy.deepcopy(duplicate["branches"][0]))
        duplicate["branch_count"] += 1
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verify_recovery_manifest(sign_payload(duplicate))
        elevated = copy.deepcopy(manifest)
        elevated["optimizer_training"] = True
        with self.assertRaisesRegex(ValueError, "authority"):
            verify_recovery_manifest(sign_payload(elevated))
        mismatch = copy.deepcopy(manifest)
        mismatch["reproduced_action_sequence_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "reproduce"):
            verify_recovery_manifest(sign_payload(mismatch))

    @staticmethod
    def _snapshot(index: int, phase: str) -> dict:
        from scenesmith.robot_lab.t20_18_state_fork_recovery import build_parent_snapshot

        return build_parent_snapshot(
            frame_index=index,
            phase=phase,
            integration_state_spec=8191,
            integration_state=[float(index), 0.0, 1.0],
            observation_state=[0.0] * 12,
            requested_action=[0.0] * 6,
            applied_action=[0.0] * 6,
            object_pose=[0.0, 0.0, 0.1, 1.0, 0.0, 0.0, 0.0],
            source_evaluation_identity_sha256="a" * 64,
        )

    @staticmethod
    def _replay() -> dict:
        return {
            "first_trace_sha256": "9" * 64,
            "second_trace_sha256": "9" * 64,
            "frame_count": 1,
            "absolute_tolerance": 0.0,
        }

    @staticmethod
    def _source_refs() -> dict:
        labels = (
            "t18_4_manifest",
            "t20_17_result_gate",
            "t20_17_evaluation",
            "t20_17_training_summary",
            "t20_17_adapter",
            "held_out_source_episode",
        )
        return {
            label: {
                "path": f"evidence/{index}-{label}.json",
                "file_sha256": f"{index + 10:064x}",
                "identity_sha256": f"{index + 20:064x}",
            }
            for index, label in enumerate(labels)
        }


if __name__ == "__main__":
    unittest.main()
