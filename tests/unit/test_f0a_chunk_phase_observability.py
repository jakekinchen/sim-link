from __future__ import annotations

import base64
import copy
import hashlib
import io
import unittest

from PIL import Image

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.f0a_chunk_phase_observability import (
    POLICY_INPUT_KEYS,
    analyze_cadence_coupling,
    analyze_decode_progress,
    analyze_observation_contract,
    analyze_reversal_alias,
    build_f0a_result,
    cosine,
    image_pair_mae,
    nearest_rank_percentile,
    phase_for_frame,
    verify_f0a_result,
)


class F0aChunkPhaseObservabilityTests(unittest.TestCase):
    def test_observation_contract_exposes_dropped_direction_fields(self) -> None:
        contract = self._contract()
        self.assertEqual(contract["consumed_policy_input_keys"], list(POLICY_INPUT_KEYS))
        self.assertTrue(contract["dataset_has_timestamp_column"])
        self.assertTrue(contract["raw_has_joint_velocity"])
        self.assertTrue(contract["direction_disambiguating_fields_omitted"])
        self.assertTrue(all(contract["consumed_field_omissions"].values()))

    def test_percentile_cosine_and_zero_norm_are_deterministic(self) -> None:
        self.assertEqual(nearest_rank_percentile([4.0, 1.0, 3.0, 2.0], 0.5), 2.0)
        self.assertAlmostEqual(cosine([1.0, 0.0], [-1.0, 0.0]), -1.0)
        self.assertIsNone(cosine([0.0, 0.0], [1.0, 0.0]))

    def test_decode_progress_aligns_frame_200_to_lower_183(self) -> None:
        comparisons = []
        for index in range(244):
            source = [0.0, index * 0.001, 0.0, 0.0, 0.0, 0.25]
            candidate = list(source)
            if index == 200:
                candidate = [0.0, 0.183, 0.0, 0.0, 0.0, 0.25]
            comparisons.append(
                {
                    "frame_index": index,
                    "phase": phase_for_frame(index),
                    "source_qpos_rad": source,
                    "candidate_qpos_rad": candidate,
                }
            )
        result = analyze_decode_progress(
            comparisons=comparisons,
            state_standard_deviation=[1.0] * 6,
            decode_starts=[0, 50, 100, 150, 200],
            f0_release_shift_frames=20,
        )
        self.assertEqual(result["frame_200_nearest_lower"]["frame_index"], 183)
        self.assertEqual(result["frame_200_lower_state_lag_frames"], 17)
        self.assertTrue(result["lag_alignment_supported"])

    def test_reversal_alias_uses_images_velocity_and_future_targets(self) -> None:
        frames = self._frames(conflicting=True)
        result = analyze_reversal_alias(
            source_frames=frames,
            state_standard_deviation=[1.0] * 6,
        )
        self.assertEqual(result["alias_pass_count"], 24)
        self.assertTrue(result["source_corridor_alias_supported"])
        self.assertTrue(all(row["alias_pass"] for row in result["pair_rows"]))
        self.assertEqual(image_pair_mae(frames, 76, 176)["mean"], 0.0)

    def test_zero_target_norm_does_not_invent_alias_conflict(self) -> None:
        result = analyze_reversal_alias(
            source_frames=self._frames(conflicting=False),
            state_standard_deviation=[1.0] * 6,
        )
        self.assertEqual(result["alias_pass_count"], 0)
        self.assertFalse(result["source_corridor_alias_supported"])
        self.assertTrue(
            all(row["next_ten_arm_displacement_cosine"] is None for row in result["pair_rows"])
        )

    def test_signed_result_routes_cadence_before_training(self) -> None:
        result = self._result()
        verify_f0a_result(result)
        self.assertTrue(result["findings"]["reversal_observability_defect_supported"])
        self.assertTrue(result["findings"]["tail_cadence_gate_coupling_supported"])
        self.assertEqual(
            result["selected_route"],
            "open_separately_reviewed_f0b_hybrid_tail_cadence_evaluation",
        )
        self.assertFalse(result["corrective_training_selected"])
        self.assertFalse(result["single_corrective_rung_consumed"])
        self.assertEqual(sum(result["f0b_hybrid_schedule"]["executed_lengths"]), 244)

    def test_resigned_route_and_authority_mutations_fail(self) -> None:
        result = self._result()
        for field, value in (
            ("selected_route", "train_now"),
            ("model_inference", True),
            ("optimizer_training", True),
            ("training_lock", "open"),
        ):
            drift = copy.deepcopy(result)
            drift[field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    verify_f0a_result(sign_payload(drift))

    def _result(self):
        contract = self._contract()
        comparisons = []
        for index in range(244):
            source = [0.0, index * 0.001, 0.0, 0.0, 0.0, 0.25]
            candidate = list(source)
            if index == 200:
                candidate = [0.0, 0.183, 0.0, 0.0, 0.0, 0.25]
            comparisons.append(
                {
                    "frame_index": index,
                    "phase": phase_for_frame(index),
                    "source_qpos_rad": source,
                    "candidate_qpos_rad": candidate,
                }
            )
        progress = analyze_decode_progress(
            comparisons=comparisons,
            state_standard_deviation=[1.0] * 6,
            decode_starts=[0, 50, 100, 150, 200],
            f0_release_shift_frames=20,
        )
        alias = analyze_reversal_alias(
            source_frames=self._frames(conflicting=True),
            state_standard_deviation=[1.0] * 6,
        )
        cadence = analyze_cadence_coupling(
            decode_progress=progress,
            decode_starts=[0, 50, 100, 150, 200],
            release_gate_passed=False,
            retreat_final_clear_passed=True,
        )
        return build_f0a_result(
            source_refs=[
                {
                    "label": "fixture",
                    "path": "fixture.json",
                    "file_sha256": "1" * 64,
                    "size_bytes": 1,
                }
            ],
            source_semantics=self._semantics(),
            observation_contract=contract,
            decode_progress=progress,
            reversal_alias=alias,
            cadence_coupling=cadence,
        )

    def _contract(self):
        return analyze_observation_contract(
            dataset_feature_keys=[
                *POLICY_INPUT_KEYS,
                "action",
                "timestamp",
                "frame_index",
            ],
            raw_actor_input_fields=[
                "observation.top_rgb",
                "observation.wrist_rgb",
                "observation.joint_position",
                "observation.joint_velocity",
            ],
            source_semantics=self._semantics(),
        )

    @staticmethod
    def _semantics():
        return {
            "act_config_has_exactly_two_images_and_six_state_inputs": True,
            "act_runner_decodes_only_at_queue_empty": True,
            "act_runner_feeds_qpos_only_state_slice": True,
            "dataset_state_feature_has_six_positions": True,
            "dataset_timestamp_not_policy_input": True,
            "phase_plan_matches_frozen_244_frames": True,
            "raw_actor_fields_include_joint_velocity": True,
        }

    @classmethod
    def _frames(cls, *, conflicting: bool):
        image = cls._image_payload()
        frames = []
        for index in range(244):
            qpos = [0.0] * 6
            qvel = [0.0] * 6
            action = [0.0] * 6
            if 76 <= index <= 118:
                qpos[1] = min(index - 76, 23) * 0.001
                qvel[1] = 1.0
                if conflicting:
                    action[1] = (index - 76) * 0.02
            if 176 <= index <= 218:
                qpos[1] = min(index - 176, 23) * 0.001
                qvel[1] = -1.0
                if conflicting:
                    action[1] = -(index - 176) * 0.02
            frames.append(
                {
                    "frame_index": index,
                    "phase": phase_for_frame(index),
                    "qpos_rad": qpos,
                    "qvel_rad_s": qvel,
                    "action_rad": action,
                    "images": {"top": image, "wrist": image},
                }
            )
        return frames

    @staticmethod
    def _image_payload():
        output = io.BytesIO()
        Image.new("RGB", (256, 256), color=(20, 40, 60)).save(output, format="PNG")
        png = output.getvalue()
        return {
            "channels": 3,
            "encoding": "png",
            "height": 256,
            "width": 256,
            "image_sha256": hashlib.sha256(png).hexdigest(),
            "png_base64": base64.b64encode(png).decode("ascii"),
        }


if __name__ == "__main__":
    unittest.main()
