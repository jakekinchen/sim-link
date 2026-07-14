from __future__ import annotations

import copy
import hashlib
import json
import unittest

from scenesmith.robot_lab.act_grasp_closed_loop import PHASE_PLAN
from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_25_frozen_candidate_localization import (
    build_localization_gate,
    build_trace_payload,
    summarize_rows,
    verify_trace_payload,
)


class T2025FrozenCandidateLocalizationTests(unittest.TestCase):
    def test_trace_and_gate_localize_recovery_improvement_without_authority(self) -> None:
        traces = [
            self._trace(candidate, seed, error=0.20 if candidate == "clean_base" else 0.10)
            for candidate in ("clean_base", "recovery_augmented")
            for seed in (6, 7)
        ]
        gate = build_localization_gate(traces)
        self.assertEqual(gate["recovery_relative_effect"]["frame_zero"], "improved")
        self.assertEqual(gate["recovery_relative_effect"]["precontact"], "improved")
        self.assertAlmostEqual(
            gate["candidate_to_candidate_by_seed"]["6"][
                "frame_zero_action_mean_absolute_difference_rad"
            ],
            0.1,
        )
        self.assertEqual(
            gate["earliest_shared_failure_surface"],
            "identical_reset_prediction_error",
        )
        self.assertFalse(gate["optimizer_training"])
        self.assertFalse(gate["simulation_policy_accepted"])

    def test_gate_rejects_duplicate_coverage_and_signed_mutation(self) -> None:
        traces = [
            self._trace(candidate, seed, error=0.1)
            for candidate in ("clean_base", "recovery_augmented")
            for seed in (6, 7)
        ]
        duplicate = [traces[0], traces[0], traces[2], traces[3]]
        with self.assertRaisesRegex(ValueError, "coverage"):
            build_localization_gate(duplicate)
        with self.assertRaisesRegex(ValueError, "reordered"):
            build_localization_gate([traces[1], traces[0], traces[2], traces[3]])
        mutated = copy.deepcopy(traces[0])
        mutated["comparisons"][0]["candidate_action_rad"][0] += 0.1
        with self.assertRaisesRegex(ValueError, "identity hash"):
            verify_trace_payload(mutated)

    def test_trace_rejects_nonfinite_reordered_projection_and_authority(self) -> None:
        base = self._trace("clean_base", 6, error=0.1)
        nonfinite_rows = copy.deepcopy(base["comparisons"])
        nonfinite_rows[0]["candidate_action_rad"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            summarize_rows(nonfinite_rows)
        for mutate, message in (
            (lambda p: p["comparisons"][1].update(frame_index=2), "order"),
            (lambda p: p["closed_loop"].update(projected_action_frame_count=1), "projection"),
            (lambda p: p.update(physical_actuation=True), "authority"),
        ):
            payload = copy.deepcopy(base)
            mutate(payload)
            payload = sign_payload(payload)
            with self.assertRaisesRegex(ValueError, message):
                verify_trace_payload(payload)

    @staticmethod
    def _trace(candidate: str, seed: int, *, error: float) -> dict:
        rows = []
        index = 0
        for phase, count in PHASE_PLAN:
            for _ in range(count):
                source = [0.0] * 6
                action = [error] * 6
                rows.append({
                    "frame_index": index,
                    "phase": phase,
                    "source_action_rad": source,
                    "candidate_action_rad": action,
                    "source_qpos_rad": source,
                    "candidate_qpos_rad": source,
                    "source_qvel_rad_s": source,
                    "candidate_qvel_rad_s": source,
                })
                index += 1
        action_bytes = json.dumps(
            [row["candidate_action_rad"] for row in rows], separators=(",", ":")
        ).encode()
        digest = hashlib.sha256(action_bytes).hexdigest()
        return build_trace_payload(
            candidate_id=candidate,
            seed=seed,
            source_episode_file_sha256="a" * 64,
            source_episode_identity_sha256="b" * 64,
            training_identity_sha256="c" * 64,
            checkpoint_sha256="d" * 64,
            rows=rows,
            closed_loop={
                "seed": seed,
                "frame_count": 244,
                "policy_action_sequence_sha256": digest,
                "projected_action_frame_count": 0,
                "active_assist_frame_count": 0,
            },
        )


if __name__ == "__main__":
    unittest.main()
