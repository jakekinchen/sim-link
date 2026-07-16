from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36o_episode_bridge_design import (
    CHUNK_START_FRAMES,
    CORRECTION_EXAMPLE_COUNT,
    EXECUTED_LENGTHS,
    OPTIMIZER_UPDATE_COUNT,
    SPEC_PATH,
    build_bridge_spec,
    load_verified_sources,
    verify_bridge_spec,
    verify_bridge_spec_file,
)


class T2036oEpisodeBridgeDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_verified_sources()
        cls.spec = build_bridge_spec(sources=cls.sources)

    def test_queue_contract_uses_real_fifty_action_cadence(self) -> None:
        contract = self.spec["execution_contract"]
        self.assertEqual(contract["n_action_steps"], 50)
        self.assertEqual(contract["queue_reset_count"], 1)
        self.assertEqual(contract["chunk_start_frames"], list(CHUNK_START_FRAMES))
        self.assertEqual(contract["executed_lengths"], list(EXECUTED_LENGTHS))
        self.assertEqual(contract["prediction_count"], 250)
        self.assertEqual(contract["executed_action_count"], 244)
        self.assertEqual(contract["unexecuted_tail_count"], 6)
        self.assertFalse(contract["legacy_action_horizon_5_allowed"])

    def test_windows_bind_source_frames_phases_and_final_tail_mask(self) -> None:
        windows = self.spec["source_windows"]
        self.assertEqual([row["start_frame"] for row in windows], [0, 50, 100, 150, 200])
        self.assertEqual(
            [row["start_task_phase"] for row in windows],
            ["approach", "close", "stable_hold", "stable_hold", "release"],
        )
        for row, expected_length in zip(windows, EXECUTED_LENGTHS, strict=True):
            self.assertEqual(row["executed_length"], expected_length)
            self.assertEqual(sum(row["executed_mask"]), expected_length)
            self.assertEqual(row["source_frame_indices"], list(range(row["start_frame"], row["start_frame"] + expected_length)))
            self.assertEqual(len(row["padded_target_action_mujoco_rad"]), 50)
            self.assertEqual(len(row["padded_target_action_lerobot_deg"]), 50)
        final = windows[-1]
        self.assertEqual(final["executed_mask"], [True] * 44 + [False] * 6)
        self.assertEqual(
            final["padded_target_action_mujoco_rad"][44:],
            [final["padded_target_action_mujoco_rad"][43]] * 6,
        )
        self.assertFalse(final["unexecuted_tail_actor_valid"])
        self.assertFalse(final["unexecuted_tail_gate_valid"])

    def test_correction_schedule_preserves_x_exposure_and_replay_ratio(self) -> None:
        schedule = self.spec["correction_schedule"]
        self.assertEqual(CORRECTION_EXAMPLE_COUNT, 250)
        self.assertEqual(OPTIMIZER_UPDATE_COUNT, 2500)
        self.assertEqual(schedule["correction_example_count"], 250)
        self.assertEqual(schedule["optimizer_update_count_ceiling"], 2500)
        counts = [schedule["sample_index_by_update"].count(i) for i in range(250)]
        self.assertEqual(counts, [10] * 250)
        self.assertEqual(schedule["standard_replay_update_count"], 2500)
        self.assertEqual(len(set(schedule["standard_replay_seed_by_update"])), 2500)
        self.assertEqual(schedule["probe_update_counts"], [0, 500, 1000, 1500, 2000, 2500])
        self.assertEqual(schedule["selection_rule"], "first_complete_confirmed_pass")

    def test_acceptance_preserves_the_exact_frozen_phase_mapping(self) -> None:
        acceptance = self.spec["acceptance"]
        self.assertEqual(
            acceptance["timestep_phase_mapping"],
            {"reach": [0, 32], "grasp": [32, 50]},
        )
        self.assertEqual(
            acceptance["phase_joint_maximum_error_rad"],
            {
                "reach": {
                    "shoulder_pan": 0.1,
                    "shoulder_lift": 0.05,
                    "elbow_flex": 0.1,
                    "wrist_flex": 0.4,
                    "wrist_roll": 0.4,
                    "gripper": 0.1,
                },
                "grasp": {
                    "shoulder_pan": 0.1,
                    "shoulder_lift": 0.05,
                    "elbow_flex": 0.1,
                    "wrist_flex": 0.1,
                    "wrist_roll": 0.4,
                    "gripper": 0.025,
                },
            },
        )
        self.assertEqual(
            acceptance["threshold_rule"],
            "exact_frozen_relative_timestep_phase_mapping_per_chunk",
        )
        self.assertTrue(acceptance["all_executed_actions_must_pass"])
        self.assertFalse(acceptance["unexecuted_tail_is_scored"])

    def test_semantic_or_authority_drift_fails_closed(self) -> None:
        for mutation in (
            lambda value: value["execution_contract"].update(n_action_steps=5),
            lambda value: value["execution_contract"].update(queue_reset_count=5),
            lambda value: value["source_windows"][-1].update(executed_mask=[True] * 50),
            lambda value: value["source_windows"][-1].update(unexecuted_tail_actor_valid=True),
            lambda value: value["correction_schedule"].update(optimizer_update_count_ceiling=2501),
            lambda value: value.update(optimizer_created=True),
        ):
            drift = copy.deepcopy(self.spec)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_bridge_spec(sign_payload(drift), sources=self.sources)

    def test_archived_spec_reconstructs_exactly(self) -> None:
        self.assertEqual(verify_bridge_spec_file()["identity_sha256"], self.spec["identity_sha256"])
        self.assertEqual(str(SPEC_PATH), "configurations/robot_lab/t20_36o_episode_bridge_design.json")


if __name__ == "__main__":
    unittest.main()
