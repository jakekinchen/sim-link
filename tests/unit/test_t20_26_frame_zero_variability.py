from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_26_frame_zero_variability import (
    BATCH_IDS,
    SAMPLE_SCHEDULE,
    build_batch,
    build_gate,
    verify_batch,
)


class T2026FrameZeroVariabilityTests(unittest.TestCase):
    def test_gate_separates_within_and_cross_process_variability(self) -> None:
        batches = [
            self._batch(candidate, batch_id, offset=0.01 * batch_id)
            for candidate in ("clean_base", "recovery_augmented")
            for batch_id in BATCH_IDS
        ]
        gate = build_gate(batches)
        self.assertTrue(gate["cross_process_same_seed_gap_reproduced"])
        self.assertEqual(
            gate["candidate_summaries"]["clean_base"][
                "within_process_same_seed_max_abs_difference_rad"
            ],
            0.0,
        )
        self.assertFalse(gate["action_applied"])
        self.assertFalse(gate["optimizer_training"])

    def test_batch_rejects_schedule_nonfinite_action_application_and_mutation(self) -> None:
        batch = self._batch("clean_base", 1, offset=0.0)
        for mutate, message in (
            (lambda p: p["samples"].reverse(), "schedule"),
            (lambda p: p.update(action_applied=True), "authority"),
        ):
            drift = copy.deepcopy(batch)
            mutate(drift)
            drift = sign_payload(drift)
            with self.assertRaisesRegex(ValueError, message):
                verify_batch(drift)
        mutation = copy.deepcopy(batch)
        mutation["samples"][0]["requested_action_rad"][0] += 1.0
        with self.assertRaisesRegex(ValueError, "identity hash"):
            verify_batch(mutation)

    def test_gate_rejects_reordered_batches_or_observation_substitution(self) -> None:
        batches = [
            self._batch(candidate, batch_id, offset=0.0)
            for candidate in ("clean_base", "recovery_augmented")
            for batch_id in BATCH_IDS
        ]
        with self.assertRaisesRegex(ValueError, "reordered"):
            build_gate([batches[1], batches[0], batches[2], batches[3]])
        substituted = copy.deepcopy(batches)
        substituted[-1]["observation"]["top_raw_sha256"] = "f" * 64
        substituted[-1] = sign_payload(substituted[-1])
        with self.assertRaisesRegex(ValueError, "identical observation"):
            build_gate(substituted)

    @staticmethod
    def _batch(candidate: str, batch_id: int, *, offset: float) -> dict:
        samples = [
            {
                "sample_id": sample_id,
                "mode": mode,
                "inference_seed": seed,
                "requested_action_rad": [
                    offset + (0.001 * index if mode == "distinct_seed_sample" else 0.0)
                ]
                * 6,
            }
            for index, (sample_id, mode, seed) in enumerate(SAMPLE_SCHEDULE)
        ]
        return build_batch(
            candidate_id=candidate,
            batch_id=batch_id,
            source_episode_file_sha256="a" * 64,
            source_episode_identity_sha256="b" * 64,
            training_identity_sha256="c" * 64,
            checkpoint_sha256=("d" if candidate == "clean_base" else "e") * 64,
            lerobot_stack_identity_sha256="f" * 64,
            observation={
                "seed": 6,
                "frame_index": 0,
                "phase": "approach",
                "top_raw_sha256": "1" * 64,
                "wrist_raw_sha256": "2" * 64,
                "qpos_rad": [0.0] * 6,
                "qvel_rad_s": [0.0] * 6,
                "source_state_max_abs_error": 0.0,
            },
            samples=samples,
        )


if __name__ == "__main__":
    unittest.main()
