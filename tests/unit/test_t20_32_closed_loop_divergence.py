from __future__ import annotations

import copy
import hashlib
import json
import unittest

from scenesmith.robot_lab.act_grasp_closed_loop import PHASE_PLAN
from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_32_closed_loop_divergence import (
    ADAPTER_IDS,
    ALL_SEEDS,
    build_localization_report,
    build_threshold_contract,
    build_trace_payload,
    verify_localization_report,
    verify_trace_payload,
)


class T2032ClosedLoopDivergenceTests(unittest.TestCase):
    def test_frame_zero_training_seed_failure_routes_memorization_plumbing(self) -> None:
        threshold = build_threshold_contract()
        traces = [
            self._trace(adapter, seed, threshold=threshold, onset=0, strict=False)
            for adapter in ADAPTER_IDS
            for seed in ALL_SEEDS
        ]
        report = build_localization_report(threshold=threshold, traces=traces)
        self.assertEqual(
            report["selected_next_gate_hypothesis"],
            "gate_b_memorization_or_model_plumbing",
        )
        self.assertEqual(report["lowest_unmet_capability_gate"], "B")
        self.assertFalse(report["optimizer_training"])
        self.assertFalse(report["simulation_policy_accepted"])
        verify_localization_report(report, threshold=threshold, traces=traces)

    def test_aligned_training_seed_then_chunk_boundary_routes_gate_c(self) -> None:
        threshold = build_threshold_contract()
        traces = [
            self._trace(
                adapter,
                seed,
                threshold=threshold,
                onset=5 if seed == 0 else 0,
                strict=False,
            )
            for adapter in ADAPTER_IDS
            for seed in ALL_SEEDS
        ]
        report = build_localization_report(threshold=threshold, traces=traces)
        self.assertEqual(
            report["selected_next_gate_hypothesis"],
            "gate_c_action_chunk_execution_semantics",
        )
        self.assertEqual(report["lowest_unmet_capability_gate"], "C")

    def test_training_seed_success_routes_dataset_coverage(self) -> None:
        threshold = build_threshold_contract()
        traces = [
            self._trace(
                adapter,
                seed,
                threshold=threshold,
                onset=None if seed == 0 else 0,
                strict=seed == 0,
            )
            for adapter in ADAPTER_IDS
            for seed in ALL_SEEDS
        ]
        report = build_localization_report(threshold=threshold, traces=traces)
        self.assertEqual(
            report["selected_next_gate_hypothesis"],
            "gate_d_dataset_coverage",
        )
        self.assertEqual(report["lowest_unmet_capability_gate"], "D")

    def test_trace_rejects_shape_seed_adapter_projection_and_authority_drift(self) -> None:
        threshold = build_threshold_contract()
        base = self._trace(
            ADAPTER_IDS[0], 0, threshold=threshold, onset=5, strict=False
        )
        for mutate, message in (
            (lambda p: p["comparisons"].pop(), "244"),
            (lambda p: p.update(seed=9), "coverage"),
            (lambda p: p.update(adapter_id="unknown"), "coverage"),
            (
                lambda p: p["closed_loop"].update(projected_action_frame_count=1),
                "projection",
            ),
            (lambda p: p.update(physical_actuation=True), "authority"),
        ):
            payload = copy.deepcopy(base)
            mutate(payload)
            if payload["closed_loop"] != base["closed_loop"]:
                payload["closed_loop"] = sign_payload(payload["closed_loop"])
            payload = sign_payload(payload)
            with self.assertRaisesRegex(ValueError, message):
                verify_trace_payload(payload, threshold=threshold)

    def test_report_rejects_missing_reordered_and_threshold_drift(self) -> None:
        threshold = build_threshold_contract()
        traces = [
            self._trace(adapter, seed, threshold=threshold, onset=0, strict=False)
            for adapter in ADAPTER_IDS
            for seed in ALL_SEEDS
        ]
        with self.assertRaisesRegex(ValueError, "six"):
            build_localization_report(threshold=threshold, traces=traces[:-1])
        with self.assertRaisesRegex(ValueError, "order"):
            build_localization_report(
                threshold=threshold, traces=[traces[1], traces[0], *traces[2:]]
            )
        drifted = copy.deepcopy(threshold)
        drifted["action_divergence_threshold_rad"] *= 2
        drifted = sign_payload(drifted)
        with self.assertRaisesRegex(ValueError, "threshold"):
            verify_trace_payload(traces[0], threshold=drifted)

    @staticmethod
    def _trace(
        adapter: str,
        seed: int,
        *,
        threshold: dict,
        onset: int | None,
        strict: bool,
    ) -> dict:
        rows = []
        frame_index = 0
        for phase, count in PHASE_PLAN:
            for _ in range(count):
                source = [0.0] * 6
                error = 0.0 if onset is None or frame_index < onset else 0.1
                candidate = [error] * 5 + [0.0]
                rows.append(
                    {
                        "frame_index": frame_index,
                        "phase": phase,
                        "chunk_index": frame_index // 5,
                        "chunk_offset": frame_index % 5,
                        "source_requested_action_rad": source,
                        "source_applied_action_rad": source,
                        "candidate_requested_action_rad": candidate,
                        "candidate_applied_action_rad": candidate,
                        "source_qpos_rad": source,
                        "candidate_qpos_rad": (
                            source if frame_index == 0 else candidate
                        ),
                        "source_qvel_rad_s": source,
                        "candidate_qvel_rad_s": source,
                        "candidate_anchor_position_m": [0.2, 0.0, 0.325],
                        "candidate_strict_contact": False,
                    }
                )
                frame_index += 1
        action_bytes = json.dumps(
            [row["candidate_requested_action_rad"] for row in rows],
            separators=(",", ":"),
        ).encode()
        action_sha = hashlib.sha256(action_bytes).hexdigest()
        prior_identity = "e" * 64 if seed in (6, 7) else None
        return build_trace_payload(
            threshold=threshold,
            adapter_id=adapter,
            seed=seed,
            inference_seed=20260716 + seed,
            source_episode_file_sha256="a" * 64,
            source_episode_identity_sha256="b" * 64,
            training_identity_sha256="c" * 64,
            checkpoint_sha256="d" * 64,
            rows=rows,
            closed_loop=sign_payload({
                "seed": seed,
                "frame_count": 244,
                "policy_action_sequence_sha256": action_sha,
                "projected_action_frame_count": 0,
                "active_assist_frame_count": 0,
                "simulation_semantic_strict_success": strict,
                "terminal_outcome": "strict_success" if strict else "no_strict_grasp_contact",
            }),
            prior_evaluation_identity_sha256=prior_identity,
            prior_action_sequence_sha256=action_sha if prior_identity else None,
        )


if __name__ == "__main__":
    unittest.main()
