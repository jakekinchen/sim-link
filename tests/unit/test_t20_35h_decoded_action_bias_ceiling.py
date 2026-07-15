from __future__ import annotations

import copy
import math
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_35h_decoded_action_bias_ceiling import (
    build_bias_ceiling,
    verify_bias_ceiling,
)


SEEDS = [20260721, 20260722, 20260723, 20260724, 20260725]


class T2035HDecodedActionBiasCeilingTests(unittest.TestCase):
    def test_global_channel_bias_passes_and_has_priority(self) -> None:
        target = self._target()
        chunks = self._chunks(
            target,
            bias=lambda _t, joint: 0.07 if joint in (4, 5) else 0.01,
            seed_offsets=[-0.008, -0.004, 0.0, 0.004, 0.008],
        )
        ceiling = self._build(target, chunks)
        self.assertTrue(ceiling["global_output_channel_bias"]["ceiling_passed"])
        self.assertTrue(
            ceiling["time_conditioned_output_channel_bias"]["ceiling_passed"]
        )
        self.assertEqual(
            ceiling["preferred_ceiling_class"], "global_output_channel_bias"
        )
        self.assertEqual(
            ceiling["selected_next_hypothesis"],
            "global_decoded_action_bias_ceiling_passes_route_model_internal_output_bias_correction",
        )
        self.assertFalse(ceiling["gate_b_passed"])
        self.assertFalse(ceiling["action_correction_selected"])
        verify_bias_ceiling(
            ceiling,
            source_result_identity="a" * 64,
            source_result_file_sha256="b" * 64,
            target_chunk=target,
            baseline_decoded_chunks=chunks,
        )

    def test_time_conditioned_bias_passes_when_global_fails(self) -> None:
        target = self._target()
        chunks = self._chunks(
            target,
            bias=lambda timestep, _joint: 0.08 if timestep < 25 else -0.08,
            seed_offsets=[-0.004, -0.002, 0.0, 0.002, 0.004],
        )
        ceiling = self._build(target, chunks)
        self.assertFalse(ceiling["global_output_channel_bias"]["ceiling_passed"])
        self.assertTrue(
            ceiling["time_conditioned_output_channel_bias"]["ceiling_passed"]
        )
        self.assertEqual(
            ceiling["preferred_ceiling_class"],
            "time_conditioned_output_channel_bias",
        )
        self.assertEqual(
            ceiling["selected_next_hypothesis"],
            "time_conditioned_decoded_action_bias_ceiling_passes_route_action_head_time_conditioning_correction",
        )

    def test_failed_but_improved_bias_routes_variance(self) -> None:
        target = self._target()
        chunks = self._chunks(
            target,
            bias=lambda _t, _joint: 0.09,
            seed_offsets=[-0.06, -0.03, 0.0, 0.03, 0.06],
        )
        ceiling = self._build(target, chunks)
        conditioned = ceiling["time_conditioned_output_channel_bias"]
        self.assertFalse(conditioned["ceiling_passed"])
        self.assertTrue(conditioned["improves_baseline_worst_fold_maximum"])
        self.assertTrue(conditioned["improves_baseline_aggregate_mean"])
        self.assertEqual(
            ceiling["selected_next_hypothesis"],
            "bias_ceiling_improves_but_fails_route_residual_variance_localization",
        )

    def test_bias_rejection_and_adversarial_drift_fail_closed(self) -> None:
        target = self._target()
        chunks = self._chunks(
            target,
            bias=lambda _t, _joint: 0.0,
            seed_offsets=[-0.10, -0.05, 0.0, 0.05, 0.10],
        )
        ceiling = self._build(target, chunks)
        self.assertEqual(
            ceiling["selected_next_hypothesis"],
            "bias_only_correction_rejected_route_representation_action_head_localization",
        )
        for mutation in (
            lambda value: value["global_output_channel_bias"]["folds"][0][
                "calibration_seeds"
            ].append(SEEDS[0]),
            lambda value: value["time_conditioned_output_channel_bias"]["folds"][0].update(
                threshold_exceedance_count=0
            ),
            lambda value: value.update(gate_b_passed=True),
            lambda value: value.update(model_loaded=True),
        ):
            drift = copy.deepcopy(ceiling)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_bias_ceiling(
                    sign_payload(drift),
                    source_result_identity="a" * 64,
                    source_result_file_sha256="b" * 64,
                    target_chunk=target,
                    baseline_decoded_chunks=chunks,
                )

        malformed = copy.deepcopy(chunks)
        malformed[0]["decoded_action_chunk"][0][0] = math.nan
        with self.assertRaises(ValueError):
            self._build(target, malformed)

    def test_source_lineage_seed_order_shape_and_hash_fail_closed(self) -> None:
        target = self._target()
        chunks = self._chunks(
            target,
            bias=lambda _t, _joint: 0.02,
            seed_offsets=[-0.004, -0.002, 0.0, 0.002, 0.004],
        )
        ceiling = self._build(target, chunks)
        with self.assertRaises(ValueError):
            verify_bias_ceiling(
                ceiling,
                source_result_identity="c" * 64,
                source_result_file_sha256="b" * 64,
                target_chunk=target,
                baseline_decoded_chunks=chunks,
            )
        with self.assertRaises(ValueError):
            build_bias_ceiling(
                source_result_identity="not-a-sha",
                source_result_file_sha256="b" * 64,
                target_chunk=target,
                baseline_decoded_chunks=chunks,
            )
        reordered = copy.deepcopy(chunks)
        reordered.reverse()
        with self.assertRaises(ValueError):
            self._build(target, reordered)
        malformed_target = copy.deepcopy(target)
        malformed_target.pop()
        with self.assertRaises(ValueError):
            self._build(malformed_target, chunks)
        bad_hash = copy.deepcopy(chunks)
        bad_hash[0]["decoded_action_chunk_sha256"] = "d" * 64
        with self.assertRaises(ValueError):
            self._build(target, bad_hash)

    def test_verifier_tolerates_only_sub_femtoscale_derived_float_drift(self) -> None:
        target = self._target()
        chunks = self._chunks(
            target,
            bias=lambda _t, _joint: 0.02,
            seed_offsets=[-0.004, -0.002, 0.0, 0.002, 0.004],
        )
        ceiling = self._build(target, chunks)
        tolerated = copy.deepcopy(ceiling)
        tolerated["global_output_channel_bias"][
            "aggregate_mean_absolute_error_rad"
        ] += 5e-16
        verify_bias_ceiling(
            sign_payload(tolerated),
            source_result_identity="a" * 64,
            source_result_file_sha256="b" * 64,
            target_chunk=target,
            baseline_decoded_chunks=chunks,
        )
        rejected = copy.deepcopy(ceiling)
        rejected["global_output_channel_bias"][
            "aggregate_mean_absolute_error_rad"
        ] += 2e-15
        with self.assertRaisesRegex(ValueError, "bias ceiling drifted"):
            verify_bias_ceiling(
                sign_payload(rejected),
                source_result_identity="a" * 64,
                source_result_file_sha256="b" * 64,
                target_chunk=target,
                baseline_decoded_chunks=chunks,
            )

    def _build(self, target: list[list[float]], chunks: list[dict]) -> dict:
        return build_bias_ceiling(
            source_result_identity="a" * 64,
            source_result_file_sha256="b" * 64,
            target_chunk=target,
            baseline_decoded_chunks=chunks,
        )

    @staticmethod
    def _target() -> list[list[float]]:
        return [
            [0.002 * timestep + 0.01 * joint for joint in range(6)]
            for timestep in range(50)
        ]

    @staticmethod
    def _chunks(
        target: list[list[float]],
        *,
        bias,
        seed_offsets: list[float],
    ) -> list[dict]:
        return [
            {
                "inference_seed": seed,
                "decoded_action_chunk": [
                    [
                        target[timestep][joint]
                        - bias(timestep, joint)
                        + seed_offsets[seed_index]
                        for joint in range(6)
                    ]
                    for timestep in range(50)
                ],
            }
            for seed_index, seed in enumerate(SEEDS)
        ]


if __name__ == "__main__":
    unittest.main()
