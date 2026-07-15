from __future__ import annotations

import copy
import hashlib
import math
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35g_denoising_cadence_discriminator import (
    build_corrected_evaluation_spec,
    build_evaluation_permit,
    build_evaluation_spec,
    build_result,
    build_runtime_compatibility_preflight,
    verify_evaluation_permit,
    verify_evaluation_spec,
    verify_result,
    verify_runtime_compatibility_preflight,
)


class T2035GDenoisingCadenceDiscriminatorTests(unittest.TestCase):
    def test_smallest_passing_cadence_closes_gate_b(self) -> None:
        spec, permit, attempt, target, baseline = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            cadence_evaluations=[
                self._evaluation(10, baseline),
                self._evaluation(20, self._chunks(0.08)),
                self._evaluation(50, self._chunks(0.04)),
            ],
        )
        self.assertTrue(result["gate_b_passed"])
        self.assertEqual(result["selected_num_inference_steps"], 50)
        self.assertEqual(
            result["selected_next_hypothesis"],
            "gate_b_pass_route_gate_c_closed_loop_reproduction",
        )
        verify_result(
            result,
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
        )

    def test_directional_improvement_and_rejection_remain_distinct(self) -> None:
        spec, permit, attempt, target, baseline = self._contract()
        positive = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            cadence_evaluations=[
                self._evaluation(10, baseline),
                self._evaluation(20, self._chunks(0.08)),
                self._evaluation(50, self._chunks(0.07)),
            ],
        )
        self.assertFalse(positive["gate_b_passed"])
        self.assertEqual(positive["selected_num_inference_steps"], 50)
        self.assertEqual(
            positive["selected_next_hypothesis"],
            "cadence_effect_positive_but_gate_b_still_closed",
        )

        rejected = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            cadence_evaluations=[
                self._evaluation(10, baseline),
                self._evaluation(20, self._chunks(0.11)),
                self._evaluation(50, self._chunks(0.12)),
            ],
        )
        self.assertIsNone(rejected["selected_num_inference_steps"])
        self.assertEqual(
            rejected["selected_next_hypothesis"],
            "denoising_cadence_rejected_route_output_bias_correction",
        )

    def test_spec_and_permit_drift_fail_closed(self) -> None:
        spec, permit, _, _, _ = self._contract()
        for mutation in (
            lambda value: value.update(cadence_num_inference_steps=[10, 25, 50]),
            lambda value: value["inference_seeds"].reverse(),
            lambda value: value.update(checkpoint_identity_sha256="f" * 64),
            lambda value: value.update(optimizer_training=True),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_evaluation_spec(sign_payload(drift), source_spec=spec)
        for mutation in (
            lambda value: value["authorized_actions"].append(
                "simulation_optimizer_training"
            ),
            lambda value: value.update(exactly_one_evaluation_attempt_authorized=False),
            lambda value: value.update(external_compute_authorized=True),
        ):
            drift = copy.deepcopy(permit)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_evaluation_permit(sign_payload(drift), spec=spec)

    def test_result_hash_metric_route_nonfinite_and_flag_drift_fail_closed(self) -> None:
        spec, permit, attempt, target, baseline = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
            cadence_evaluations=[
                self._evaluation(10, baseline),
                self._evaluation(20, self._chunks(0.08)),
                self._evaluation(50, self._chunks(0.04)),
            ],
        )
        for mutation in (
            lambda value: value["cadence_evaluations"][0]["decoded_action_chunks"][0].update(
                decoded_action_chunk_sha256="f" * 64
            ),
            lambda value: value["cadence_evaluations"][1].update(
                worst_seed_maximum_error_rad=0.01
            ),
            lambda value: value.update(selected_num_inference_steps=20),
            lambda value: value.update(
                selected_next_hypothesis="cadence_effect_positive_but_gate_b_still_closed"
            ),
            lambda value: value.update(model_loaded=False),
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

        malformed = [
            self._evaluation(10, baseline),
            self._evaluation(20, self._chunks(0.08)),
            self._evaluation(50, self._chunks(0.04)),
        ]
        malformed[1]["decoded_action_chunks"][0]["decoded_action_chunk"][0][0] = math.nan
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                target_chunk=target,
                cadence_evaluations=malformed,
            )

    def test_consumed_runtime_failure_requires_distinct_python_312_spec_and_permit(self) -> None:
        spec, permit, attempt, _, _ = self._contract()
        preflight = build_runtime_compatibility_preflight(
            original_spec=spec,
            original_permit=permit,
            consumed_attempt=attempt,
        )
        verify_runtime_compatibility_preflight(
            preflight,
            original_spec=spec,
            original_permit=permit,
            consumed_attempt=attempt,
        )
        corrected = build_corrected_evaluation_spec(
            original_spec=spec, runtime_preflight=preflight
        )
        replacement_permit = build_evaluation_permit(spec=corrected)
        self.assertNotEqual(corrected["identity_sha256"], spec["identity_sha256"])
        self.assertNotEqual(
            replacement_permit["identity_sha256"], permit["identity_sha256"]
        )
        self.assertEqual(corrected["required_python_major_minor"], [3, 12])
        self.assertEqual(corrected["consumed_attempt_identity_sha256"], attempt["identity_sha256"])
        self.assertFalse(corrected["prior_attempt_reused"])

        drift = copy.deepcopy(preflight)
        drift["replacement_runtime_preflight"]["python_version"] = [3, 14, 2]
        with self.assertRaisesRegex(ValueError, "preflight drifted"):
            verify_runtime_compatibility_preflight(
                sign_payload(drift),
                original_spec=spec,
                original_permit=permit,
                consumed_attempt=attempt,
            )

    @classmethod
    def _contract(cls):
        target = [[0.0] * 6 for _ in range(50)]
        baseline = cls._chunks(0.10)
        report = sign_payload(
            {
                "schema_version": "fixture.t20_35d.v1",
                "target_action_chunk": target,
                "target_action_chunk_sha256": cls._matrix_hash(target),
                "replayed_chunks": [
                    {
                        "inference_seed": row["inference_seed"],
                        "decoded_action_chunk_sha256": cls._matrix_hash(
                            row["decoded_action_chunk"]
                        ),
                        "decoded_action_chunk": row["decoded_action_chunk"],
                    }
                    for row in baseline
                ],
            }
        )
        audit = sign_payload(
            {
                "schema_version": "fixture.t20_35f.v1",
                "source_contract": {
                    "t20_35d_report_identity_sha256": report["identity_sha256"]
                },
                "selected_next_hypothesis": "gate_b_inference_denoising_cadence_discriminator",
                "hard_saturation_detected": False,
                "all_selected_channels_systematic_bias_dominant": True,
            }
        )
        residual_spec = sign_payload(
            {
                "schema_version": "fixture.t20_35d_spec.v1",
                "checkpoint_identity_sha256": "a" * 64,
                "checkpoint_tree": [{"path": "model", "sha256": "b" * 64}],
                "dataset_action_chunk_sha256": cls._matrix_hash(target),
                "inference_seeds": [row["inference_seed"] for row in baseline],
            }
        )
        source_run = sign_payload(
            {
                "schema_version": "fixture.t20_35c_run.v1",
                "checkpoint_identity_sha256": "a" * 64,
                "checkpoint_tree": residual_spec["checkpoint_tree"],
                "trainable_parameter_names_sha256": "c" * 64,
                "trainable_parameter_count": 100,
                "paligemma_trainable_parameter_count": 0,
            }
        )
        source_result = sign_payload(
            {
                "schema_version": "fixture.t20_35c_result.v1",
                "run_identity_sha256": source_run["identity_sha256"],
                "final_to_baseline_objective_ratio": 0.004,
                "objective_ratio_within_threshold": True,
                "all_decoded_chunks_within_threshold": False,
            }
        )
        spec = build_evaluation_spec(
            audit=audit,
            residual_spec=residual_spec,
            residual_report=report,
            source_run=source_run,
            source_result=source_result,
        )
        permit = build_evaluation_permit(spec=spec)
        attempt = sign_payload(
            {
                "schema_version": "scenesmith.t20_35g_evaluation_attempt.v1",
                "task_id": "T20.35g",
                "evaluation_spec_identity_sha256": spec["identity_sha256"],
                "evaluation_permit_identity_sha256": permit["identity_sha256"],
                "started_at": "2026-07-15T10:00:00-05:00",
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
    def _chunks(error: float):
        return [
            {
                "inference_seed": seed,
                "decoded_action_chunk": [[error] * 6 for _ in range(50)],
            }
            for seed in (20260721, 20260722, 20260723, 20260724, 20260725)
        ]

    @staticmethod
    def _evaluation(step: int, chunks: list[dict]):
        return {"num_inference_steps": step, "decoded_action_chunks": chunks}

    @staticmethod
    def _matrix_hash(matrix: list[list[float]]) -> str:
        return hashlib.sha256(canonical_json_bytes(matrix)).hexdigest()


if __name__ == "__main__":
    unittest.main()
