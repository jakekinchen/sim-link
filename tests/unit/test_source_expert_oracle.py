import copy
import unittest

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.grasp_evidence import KEYFRAME_PHASES, encode_png_image
from scenesmith.robot_lab.source_expert_oracle import (
    analyze_source_oracle,
    build_source_oracle_artifact,
    verify_source_oracle_artifact,
)


class SourceExpertOracleTest(unittest.TestCase):
    def test_exact_execution_exposes_source_semantic_mismatch(self) -> None:
        stored, regenerated, oracle = self._frames()
        result = analyze_source_oracle(
            stored,
            regenerated,
            oracle,
            source_outcome={"strict_success": True, "gate_margins": {"retreat_final_contact_clear": {}}},
            oracle_rollout=self._rollout(),
        )
        self.assertTrue(result["execution_adapter_reproduced_source_trajectory"])
        self.assertIsNone(result["first_execution_divergence"])
        self.assertTrue(result["source_vs_acceptance_semantic_mismatch"])
        self.assertEqual(
            result["mismatch_kind"],
            "release_clear_gate_absent_from_source_training_success_contract",
        )

    def test_first_state_divergence_is_reported(self) -> None:
        stored, regenerated, oracle = self._frames()
        oracle[0]["mujoco_qpos"][2] = 0.01
        result = analyze_source_oracle(
            stored,
            regenerated,
            oracle,
            source_outcome={"strict_success": True, "gate_margins": {}},
            oracle_rollout=self._rollout(),
        )
        self.assertFalse(result["execution_adapter_reproduced_source_trajectory"])
        self.assertEqual(result["first_execution_divergence"]["frame_index"], 0)
        self.assertIn(
            "joint_position_abs_error_rad",
            result["first_execution_divergence"]["failed_dimensions"],
        )

    def test_authority_escalation_is_rejected(self) -> None:
        stored, regenerated, oracle = self._frames()
        rollout = self._rollout()
        rollout.update(
            {
                "schema_version": "scenesmith.t20_9_source_expert_oracle.v1",
                "task_id": "T20.9",
                "evidence_mode": "source_expert_action_oracle_through_policy_closed_loop_adapter",
                "policy_label": "source_expert_oracle",
                "seed": 2,
                "frame_count": 244,
                "policy_controls_owned_all_frames": True,
                "policy_action_sequence_sha256": "a" * 64,
                "simulation_policy_accepted": False,
                "physical_actuation": False,
                "external_compute_started": False,
                "brev_compute_started": False,
                "physical_transfer_ready": False,
                "promotion_eligible": False,
                "rendered_keyframes": self._keyframes(),
            }
        )
        rollout = sign_payload(rollout)
        diagnostics = analyze_source_oracle(
            stored,
            regenerated,
            oracle,
            source_outcome={"strict_success": True, "gate_margins": {}},
            oracle_rollout=rollout,
        )
        diagnostics["frame_count"] = 244
        artifact = build_source_oracle_artifact(
            source_refs={
                "source_episode_regenerated_byte_identically": True,
                "episode": {
                    "seed": 2,
                    "frame_count": 244,
                    "source_action_sequence_sha256": "a" * 64,
                    "file_sha256": "b" * 64,
                },
            },
            t20_7_evaluation_ref={"strict_success_count": 0, "winner_model_id": None},
            oracle_rollout=rollout,
            diagnostics=diagnostics,
        )
        verify_source_oracle_artifact(artifact)
        escalated = copy.deepcopy(artifact)
        escalated.pop("identity_sha256")
        escalated["simulation_policy_accepted"] = True
        with self.assertRaisesRegex(ValueError, "authority"):
            verify_source_oracle_artifact(sign_payload(escalated))

    @staticmethod
    def _frames():
        stored = []
        regenerated = []
        oracle = []
        for index, phase in enumerate(("release_settle", "retreat")):
            action = [float(index)] * 6
            qpos = [float(index + 1)] * 6
            qvel = [0.0] * 6
            geoms = ["fixed_fingertip_pad_collision"] if phase == "release_settle" else []
            stored.append(
                {
                    "source_phase": phase,
                    "actions": {"requested": {"values": action}},
                    "observations": {
                        "joint_position_mujoco_rad": qpos,
                        "joint_velocity_mujoco_rad_s": qvel,
                    },
                }
            )
            regenerated.append(
                {
                    "phase": phase,
                    "mujoco_requested_action": action,
                    "mujoco_qpos": qpos,
                    "mujoco_qvel": qvel,
                    "cube_positions_m": {"object": [0.0, 0.0, 0.3]},
                    "all_robot_object_contact_geoms": geoms,
                }
            )
            oracle.append(
                {
                    "phase": phase,
                    "policy_requested_action": action,
                    "mujoco_qpos": list(qpos),
                    "mujoco_qvel": qvel,
                    "cube_positions_m": {"object": [0.0, 0.0, 0.3]},
                    "all_robot_object_contact_geoms": geoms,
                }
            )
        return stored, regenerated, oracle

    @staticmethod
    def _rollout():
        return {
            "simulation_semantic_strict_success": False,
            "failed_gate_margins": [{"gate": "release_final_contact_clear"}],
            "projected_action_frame_count": 0,
            "active_assist_frame_count": 0,
        }

    @staticmethod
    def _keyframes():
        image = np.zeros((256, 256, 3), dtype=np.uint8)
        encoded = encode_png_image(image, image_size=256)
        return [
            {
                "phase": phase,
                "frame_index": index,
                "images": {"top": encoded, "wrist": encoded},
            }
            for index, phase in enumerate(KEYFRAME_PHASES)
        ]


if __name__ == "__main__":
    unittest.main()
