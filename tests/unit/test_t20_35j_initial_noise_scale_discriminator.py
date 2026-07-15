from __future__ import annotations

import copy
import hashlib
import math
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35j_initial_noise_scale_discriminator import (
    build_evaluation_permit,
    build_evaluation_spec,
    build_result,
    verify_evaluation_permit,
    verify_evaluation_spec,
    verify_result,
)


class T2035JInitialNoiseScaleDiscriminatorTests(unittest.TestCase):
    def test_largest_passing_candidate_closes_gate_b(self) -> None:
        spec, permit, attempt, target, baseline = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            scale_evaluations=[
                self._evaluation(1.0, baseline),
                self._evaluation(0.5, self._chunks(0.04, 0.004)),
                self._evaluation(0.0, self._chunks(0.03, 0.0)),
            ],
        )
        self.assertTrue(result["gate_b_passed"])
        self.assertEqual(result["selected_initial_noise_scale"], 0.5)
        self.assertEqual(
            result["selected_next_hypothesis"],
            "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction",
        )
        verify_result(
            result,
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
        )

    def test_positive_nonpass_and_rejection_remain_distinct(self) -> None:
        spec, permit, attempt, target, baseline = self._contract()
        positive = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            scale_evaluations=[
                self._evaluation(1.0, baseline),
                self._evaluation(0.5, self._chunks(0.08, 0.01)),
                self._evaluation(0.0, self._chunks(0.07, 0.0)),
            ],
        )
        self.assertFalse(positive["gate_b_passed"])
        self.assertEqual(positive["selected_initial_noise_scale"], 0.0)
        self.assertEqual(
            positive["selected_next_hypothesis"],
            "initial_noise_scale_positive_but_gate_b_closed_route_sampler_distribution_audit",
        )

        rejected = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            scale_evaluations=[
                self._evaluation(1.0, baseline),
                self._evaluation(0.5, self._chunks(0.12, 0.03)),
                self._evaluation(0.0, self._chunks(0.11, 0.0)),
            ],
        )
        self.assertIsNone(rejected["selected_initial_noise_scale"])
        self.assertEqual(
            rejected["selected_next_hypothesis"],
            "initial_noise_scale_rejected_route_model_robustness_correction",
        )

    def test_spec_permit_and_result_drift_fail_closed(self) -> None:
        spec, permit, attempt, target, baseline = self._contract()
        for mutation in (
            lambda value: value.update(initial_noise_scales=[1.0, 0.25, 0.0]),
            lambda value: value["inference_seeds"].reverse(),
            lambda value: value.update(num_inference_steps=20),
            lambda value: value.update(sampler_source_sha256="f" * 64),
            lambda value: value.update(optimizer_training=True),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_evaluation_spec(sign_payload(drift), expected_spec=spec)
        for mutation in (
            lambda value: value.update(exactly_one_evaluation_attempt_authorized=False),
            lambda value: value["authorized_actions"].append("optimizer_training"),
            lambda value: value.update(brev_compute_authorized=True),
        ):
            drift = copy.deepcopy(permit)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_evaluation_permit(sign_payload(drift), spec=spec)

        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            scale_evaluations=[
                self._evaluation(1.0, baseline),
                self._evaluation(0.5, self._chunks(0.04, 0.004)),
                self._evaluation(0.0, self._chunks(0.03, 0.0)),
            ],
        )
        for mutation in (
            lambda value: value["scale_evaluations"][0]["decoded_action_chunks"][0].update(
                decoded_action_chunk_sha256="f" * 64
            ),
            lambda value: value["scale_evaluations"][1].update(
                aggregate_mean_raw_decoded_spread_rad=0.9
            ),
            lambda value: value.update(selected_initial_noise_scale=0.0),
            lambda value: value.update(gate_b_passed=False),
            lambda value: value.update(optimizer_created=True),
        ):
            drift = copy.deepcopy(result)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_result(
                    sign_payload(drift),
                    spec=spec,
                    permit=permit,
                    attempt=attempt,
                    target_chunk=target,
                )

    def test_nonfinite_scale_order_baseline_and_attempt_fail_closed(self) -> None:
        spec, permit, attempt, target, baseline = self._contract()
        evaluations = [
            self._evaluation(1.0, baseline),
            self._evaluation(0.5, self._chunks(0.04, 0.004)),
            self._evaluation(0.0, self._chunks(0.03, 0.0)),
        ]
        malformed = copy.deepcopy(evaluations)
        malformed[1]["decoded_action_chunks"][0]["decoded_action_chunk"][0][0] = math.nan
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                target_chunk=target,
                scale_evaluations=malformed,
            )
        reordered = [evaluations[0], evaluations[2], evaluations[1]]
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                target_chunk=target,
                scale_evaluations=reordered,
            )
        noise_drift = copy.deepcopy(evaluations)
        noise_drift[1]["decoded_action_chunks"][0]["base_noise_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "base noise changed"):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                target_chunk=target,
                scale_evaluations=noise_drift,
            )
        baseline_drift = copy.deepcopy(evaluations)
        baseline_drift[0]["decoded_action_chunks"][0]["decoded_action_chunk"][0][0] += 0.001
        with self.assertRaisesRegex(ValueError, "baseline failed exact reproduction"):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                target_chunk=target,
                scale_evaluations=baseline_drift,
            )
        bad_attempt = copy.deepcopy(attempt)
        bad_attempt["one_evaluation_permit_consumed"] = False
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                permit=permit,
                attempt=sign_payload(bad_attempt),
                target_chunk=target,
                scale_evaluations=evaluations,
            )

    def test_result_verifier_tolerates_only_sub_femtoscale_derived_float_drift(self) -> None:
        spec, permit, attempt, target, baseline = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            scale_evaluations=[
                self._evaluation(1.0, baseline),
                self._evaluation(0.5, self._chunks(0.04, 0.004)),
                self._evaluation(0.0, self._chunks(0.03, 0.0)),
            ],
        )
        tolerated = copy.deepcopy(result)
        tolerated["scale_evaluations"][0][
            "aggregate_mean_raw_decoded_spread_rad"
        ] += 5e-16
        verify_result(
            sign_payload(tolerated),
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
        )
        rejected = copy.deepcopy(result)
        rejected["scale_evaluations"][0][
            "aggregate_mean_raw_decoded_spread_rad"
        ] += 2e-15
        with self.assertRaisesRegex(ValueError, "noise-scale result drifted"):
            verify_result(
                sign_payload(rejected),
                spec=spec,
                permit=permit,
                attempt=attempt,
                target_chunk=target,
            )

    @classmethod
    def _contract(cls):
        target = [[0.0] * 6 for _ in range(50)]
        baseline = cls._chunks(0.10, 0.02)
        cadence_spec = sign_payload(
            {
                "schema_version": "fixture.t20_35g_spec.v1",
                "checkpoint_identity_sha256": "a" * 64,
                "checkpoint_tree": [{"path": "model", "sha256": "b" * 64}],
                "trainable_parameter_names_sha256": "c" * 64,
                "trainable_parameter_count": 100,
                "paligemma_trainable_parameter_count": 0,
                "dataset_action_chunk_sha256": cls._matrix_hash(target),
                "inference_seeds": [row["inference_seed"] for row in baseline],
                "source_final_to_baseline_objective_ratio": 0.004,
                "source_objective_ratio_within_threshold": True,
                "lerobot_stack_identity_sha256": "d" * 64,
            }
        )
        cadence_result = sign_payload(
            {
                "schema_version": "fixture.t20_35g_result.v1",
                "baseline_reproduced_exactly": True,
                "gate_b_passed": False,
                "cadence_effect_positive": False,
                "selected_next_hypothesis": "denoising_cadence_rejected_route_output_bias_correction",
                "cadence_evaluations": [
                    {
                        "num_inference_steps": 10,
                        "decoded_action_chunks": [
                            {
                                **row,
                                "decoded_action_chunk_sha256": cls._matrix_hash(
                                    row["decoded_action_chunk"]
                                ),
                            }
                            for row in baseline
                        ],
                    }
                ],
            }
        )
        variance_report = sign_payload(
            {
                "schema_version": "fixture.t20_35i.v1",
                "variance_classification": "distributed_seed_channel_variance",
                "selected_next_hypothesis": "run_separately_reviewed_inference_only_initial_noise_scale_discriminator",
                "threshold_exceedance_count": 96,
                "gate_b_passed": False,
            }
        )
        spec = build_evaluation_spec(
            variance_report=variance_report,
            cadence_spec=cadence_spec,
            cadence_result=cadence_result,
            sampler_source_sha256="e" * 64,
        )
        permit = build_evaluation_permit(spec=spec)
        attempt = sign_payload(
            {
                "schema_version": "scenesmith.t20_35j_evaluation_attempt.v1",
                "task_id": "T20.35j",
                "evaluation_spec_identity_sha256": spec["identity_sha256"],
                "evaluation_permit_identity_sha256": permit["identity_sha256"],
                "started_at": "2026-07-15T11:00:00-05:00",
                "one_evaluation_permit_consumed": True,
                "checkpoint_tree_verified": True,
                "model_loaded_at_marker": False,
                "model_inference_at_marker": False,
                "optimizer_created_at_marker": False,
                "optimizer_training": False,
                "checkpoint_mutated": False,
                "closed_loop_rollout": False,
                "physical_actuation": False,
                "external_compute_started": False,
                "brev_compute_started": False,
            }
        )
        return spec, permit, attempt, target, baseline

    @staticmethod
    def _chunks(error: float, spread: float):
        offsets = (-spread, -spread / 2, 0.0, spread / 2, spread)
        return [
            {
                "inference_seed": seed,
                "base_noise_sha256": hashlib.sha256(
                    f"noise-{seed}".encode("utf-8")
                ).hexdigest(),
                "decoded_action_chunk": [[error + offsets[index]] * 6 for _ in range(50)],
            }
            for index, seed in enumerate(
                (20260721, 20260722, 20260723, 20260724, 20260725)
            )
        ]

    @staticmethod
    def _evaluation(scale: float, chunks: list[dict]):
        return {"initial_noise_scale": scale, "decoded_action_chunks": chunks}

    @staticmethod
    def _matrix_hash(matrix: list[list[float]]) -> str:
        return hashlib.sha256(canonical_json_bytes(matrix)).hexdigest()


if __name__ == "__main__":
    unittest.main()
