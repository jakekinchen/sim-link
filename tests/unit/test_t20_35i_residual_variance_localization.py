from __future__ import annotations

import copy
import hashlib
import math
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35i_residual_variance_localization import (
    build_variance_localization,
    classify_variance,
    verify_variance_localization,
)


SEEDS = [20260721, 20260722, 20260723, 20260724, 20260725]


class T2035IResidualVarianceLocalizationTests(unittest.TestCase):
    def test_distributed_fixture_routes_initial_noise_scale(self) -> None:
        target, raw, corrected, hashes = self._distributed_sources()
        report = self._build(target, raw, corrected, hashes)
        self.assertEqual(report["threshold_exceedance_count"], 300)
        self.assertEqual(
            report["variance_classification"], "distributed_seed_channel_variance"
        )
        self.assertEqual(
            report["selected_next_hypothesis"],
            "run_separately_reviewed_inference_only_initial_noise_scale_discriminator",
        )
        self.assertEqual(report["exceedance_seed_coverage_count"], 5)
        self.assertFalse(report["gate_b_passed"])
        self.assertFalse(report["action_correction_selected"])
        verify_variance_localization(
            report,
            source_ceiling_identity="a" * 64,
            target_chunk=target,
            raw_decoded_chunks=raw,
            corrected_action_chunks=corrected,
            expected_corrected_hashes=hashes,
        )

    def test_classification_precedence_and_tie_breaking(self) -> None:
        cases = (
            (61, [100, 0, 0, 0, 0], [100, 0, 0, 0, 0, 0], "chunk_boundary_variance"),
            (0, [50, 20, 10, 10, 10], [20, 20, 20, 20, 10, 10], "single_seed_variance"),
            (0, [40, 35, 10, 10, 5], [20, 20, 20, 20, 10, 10], "top_two_seed_variance"),
            (0, [20, 20, 20, 20, 20], [50, 20, 10, 10, 5, 5], "single_channel_variance"),
            (0, [20, 20, 20, 20, 20], [40, 35, 10, 5, 5, 5], "top_two_channel_variance"),
            (0, [20, 20, 20, 20, 20], [20, 20, 20, 20, 10, 10], "distributed_seed_channel_variance"),
        )
        for boundary, seed_counts, channel_counts, expected in cases:
            with self.subTest(expected=expected):
                result = classify_variance(
                    total_exceedances=100,
                    boundary_exceedance_count=boundary,
                    per_seed_counts=seed_counts,
                    per_channel_counts=channel_counts,
                )
                self.assertEqual(result["variance_classification"], expected)
        tie = classify_variance(
            total_exceedances=100,
            boundary_exceedance_count=0,
            per_seed_counts=[40, 40, 10, 5, 5],
            per_channel_counts=[20, 20, 20, 20, 10, 10],
        )
        self.assertEqual(
            [row["inference_seed"] for row in tie["ranked_seed_counts"][:2]],
            SEEDS[:2],
        )

    def test_five_fourths_identity_and_hash_drift_fail_closed(self) -> None:
        target, raw, corrected, hashes = self._distributed_sources()
        report = self._build(target, raw, corrected, hashes)
        identity_drift = copy.deepcopy(corrected)
        identity_drift[0]["corrected_action_chunk"][0][0] += 1e-6
        identity_hashes = copy.deepcopy(hashes)
        identity_hashes[0]["corrected_action_chunk_sha256"] = hashlib.sha256(
            canonical_json_bytes(identity_drift[0]["corrected_action_chunk"])
        ).hexdigest()
        with self.assertRaisesRegex(ValueError, "five-fourths identity"):
            self._build(target, raw, identity_drift, identity_hashes)
        bad_hashes = copy.deepcopy(hashes)
        bad_hashes[0]["corrected_action_chunk_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "corrected action hash"):
            self._build(target, raw, corrected, bad_hashes)

        drift = copy.deepcopy(report)
        drift["exceedances"][0]["raw_decoded_spread_rad"] = 0.0
        with self.assertRaises(ValueError):
            verify_variance_localization(
                sign_payload(drift),
                source_ceiling_identity="a" * 64,
                target_chunk=target,
                raw_decoded_chunks=raw,
                corrected_action_chunks=corrected,
                expected_corrected_hashes=hashes,
            )

    def test_nonfinite_shape_seed_and_forbidden_flag_drift_fail_closed(self) -> None:
        target, raw, corrected, hashes = self._distributed_sources()
        report = self._build(target, raw, corrected, hashes)
        for mutation in (
            lambda value: value.update(model_loaded=True),
            lambda value: value.update(gate_b_passed=True),
            lambda value: value.update(action_correction_selected=True),
            lambda value: value.update(
                selected_next_hypothesis="run_optimizer_training"
            ),
        ):
            drift = copy.deepcopy(report)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_variance_localization(
                    sign_payload(drift),
                    source_ceiling_identity="a" * 64,
                    target_chunk=target,
                    raw_decoded_chunks=raw,
                    corrected_action_chunks=corrected,
                    expected_corrected_hashes=hashes,
                )
        nonfinite = copy.deepcopy(raw)
        nonfinite[0]["decoded_action_chunk"][0][0] = math.inf
        with self.assertRaises(ValueError):
            self._build(target, nonfinite, corrected, hashes)
        reordered = copy.deepcopy(corrected)
        reordered.reverse()
        with self.assertRaises(ValueError):
            self._build(target, raw, reordered, hashes)
        malformed = copy.deepcopy(target)
        malformed.pop()
        with self.assertRaises(ValueError):
            self._build(malformed, raw, corrected, hashes)

    def test_verifier_tolerates_only_sub_femtoscale_derived_float_drift(self) -> None:
        target, raw, corrected, hashes = self._distributed_sources()
        report = self._build(target, raw, corrected, hashes)
        tolerated = copy.deepcopy(report)
        tolerated["aggregate_mean_raw_decoded_spread_rad"] += 5e-16
        verify_variance_localization(
            sign_payload(tolerated),
            source_ceiling_identity="a" * 64,
            target_chunk=target,
            raw_decoded_chunks=raw,
            corrected_action_chunks=corrected,
            expected_corrected_hashes=hashes,
        )
        rejected = copy.deepcopy(report)
        rejected["aggregate_mean_raw_decoded_spread_rad"] += 2e-15
        with self.assertRaisesRegex(ValueError, "variance localization drifted"):
            verify_variance_localization(
                sign_payload(rejected),
                source_ceiling_identity="a" * 64,
                target_chunk=target,
                raw_decoded_chunks=raw,
                corrected_action_chunks=corrected,
                expected_corrected_hashes=hashes,
            )

    def _build(self, target, raw, corrected, hashes):
        return build_variance_localization(
            source_ceiling_identity="a" * 64,
            target_chunk=target,
            raw_decoded_chunks=raw,
            corrected_action_chunks=corrected,
            expected_corrected_hashes=hashes,
        )

    @staticmethod
    def _distributed_sources():
        target = [[0.0] * 6 for _ in range(50)]
        raw_matrices = [[[0.0] * 6 for _ in range(50)] for _ in SEEDS]
        for timestep in range(50):
            for joint in range(6):
                active_seed = (timestep + joint) % 5
                for seed_index in range(5):
                    raw_matrices[seed_index][timestep][joint] = (
                        0.1 if seed_index == active_seed else -0.025
                    )
        corrected_matrices = []
        for seed_index in range(5):
            corrected_matrices.append(
                [
                    [
                        1.25
                        * (
                            raw_matrices[seed_index][timestep][joint]
                            - sum(
                                matrix[timestep][joint] for matrix in raw_matrices
                            )
                            / 5
                        )
                        for joint in range(6)
                    ]
                    for timestep in range(50)
                ]
            )
        raw = [
            {"inference_seed": seed, "decoded_action_chunk": matrix}
            for seed, matrix in zip(SEEDS, raw_matrices, strict=True)
        ]
        corrected = [
            {"inference_seed": seed, "corrected_action_chunk": matrix}
            for seed, matrix in zip(SEEDS, corrected_matrices, strict=True)
        ]
        hashes = [
            {
                "inference_seed": seed,
                "corrected_action_chunk_sha256": hashlib.sha256(
                    canonical_json_bytes(matrix)
                ).hexdigest(),
            }
            for seed, matrix in zip(SEEDS, corrected_matrices, strict=True)
        ]
        return target, raw, corrected, hashes


if __name__ == "__main__":
    unittest.main()
