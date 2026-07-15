from __future__ import annotations

import copy
import hashlib
import math
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35n_near_zero_active_noise_scale_discriminator import (
    active_noise_mask,
    build_evaluation_permit,
    build_evaluation_spec,
    build_result,
    verify_evaluation_permit,
    verify_evaluation_spec,
    verify_result,
)


class T2035nNearZeroActiveNoiseScaleDiscriminatorTests(unittest.TestCase):
    def test_active_masks_preserve_padded_standard_normal(self) -> None:
        self.assertEqual(
            active_noise_mask(0.25, active_dimensions=6, maximum_dimensions=32),
            [0.25] * 6 + [1.0] * 26,
        )
        self.assertEqual(
            active_noise_mask(0.5, active_dimensions=6, maximum_dimensions=32),
            [0.5] * 6 + [1.0] * 26,
        )

    def test_largest_passing_interior_scale_routes_gate_c_review(self) -> None:
        spec, permit, attempt, source, target = self._contract()
        result = self._result(
            spec,
            permit,
            attempt,
            source,
            target,
            self._chunks(0.035, 0.004),
            self._chunks(0.04, 0.005),
        )
        self.assertTrue(result["gate_b_passed"])
        self.assertEqual(result["selected_active_noise_scale"], 0.5)
        self.assertEqual(
            result["selected_next_hypothesis"],
            "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction",
        )

    def test_interior_optimum_and_zero_endpoint_remain_distinct(self) -> None:
        spec, permit, attempt, source, target = self._contract()
        interior = self._result(
            spec,
            permit,
            attempt,
            source,
            target,
            self._chunks(0.06, 0.004),
            self._chunks(0.08, 0.01),
        )
        self.assertFalse(interior["gate_b_passed"])
        self.assertEqual(interior["selected_active_noise_scale"], 0.25)
        self.assertEqual(
            interior["selected_next_hypothesis"],
            "refine_active_noise_scale_around_selected_interior",
        )
        endpoint = self._result(
            spec,
            permit,
            attempt,
            source,
            target,
            self._chunks(0.075, 0.01),
            self._chunks(0.09, 0.02),
        )
        self.assertEqual(endpoint["selected_active_noise_scale"], 0.0)
        self.assertEqual(
            endpoint["selected_next_hypothesis"],
            "active_zero_endpoint_optimum_route_model_flow_consistency_correction",
        )

    def test_spec_permit_result_and_noise_hash_drift_fail_closed(self) -> None:
        spec, permit, attempt, source, target = self._contract()
        for mutation in (
            lambda value: value.update(evaluated_active_noise_scales=[0.2, 0.5]),
            lambda value: value.update(padded_noise_scale=0.0),
            lambda value: value.update(num_inference_steps=20),
            lambda value: value.update(optimizer_training=True),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_evaluation_spec(sign_payload(drift), expected_spec=spec)
        for mutation in (
            lambda value: value.update(exactly_one_evaluation_attempt_authorized=False),
            lambda value: value.update(brev_compute_authorized=True),
        ):
            drift = copy.deepcopy(permit)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_evaluation_permit(sign_payload(drift), spec=spec)
        result = self._result(
            spec,
            permit,
            attempt,
            source,
            target,
            self._chunks(0.06, 0.004),
            self._chunks(0.08, 0.01),
        )
        for mutation in (
            lambda value: value.update(gate_b_passed=True),
            lambda value: value.update(selected_active_noise_scale=0.5),
            lambda value: value.update(optimizer_created=True),
            lambda value: value["active_scale_evaluations"][1].update(
                aggregate_mean_raw_decoded_spread_rad=0.9
            ),
        ):
            drift = copy.deepcopy(result)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_result(
                    sign_payload(drift),
                    spec=spec,
                    permit=permit,
                    attempt=attempt,
                    source_result=source,
                    target_chunk=target,
                )
        noise_drift = self._evaluation(0.25, self._chunks(0.06, 0.004))
        noise_drift["decoded_action_chunks"][0]["base_noise_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "base noise"):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                source_result=source,
                target_chunk=target,
                evaluated_active_scales=[
                    noise_drift,
                    self._evaluation(0.5, self._chunks(0.08, 0.01)),
                ],
            )

    def test_nonfinite_and_consumed_attempt_fail_closed(self) -> None:
        spec, permit, attempt, source, target = self._contract()
        malformed = self._chunks(0.06, 0.004)
        malformed[0]["decoded_action_chunk"][0][0] = math.nan
        with self.assertRaises(ValueError):
            self._result(
                spec,
                permit,
                attempt,
                source,
                target,
                malformed,
                self._chunks(0.08, 0.01),
            )
        bad_attempt = copy.deepcopy(attempt)
        bad_attempt["one_evaluation_permit_consumed"] = False
        with self.assertRaises(ValueError):
            self._result(
                spec,
                permit,
                sign_payload(bad_attempt),
                source,
                target,
                self._chunks(0.06, 0.004),
                self._chunks(0.08, 0.01),
            )

    @classmethod
    def _contract(cls):
        target = [[0.0] * 6 for _ in range(50)]
        active_zero = cls._chunks(0.066, 0.01)
        active_one = cls._chunks(0.15, 0.046)
        source_spec = sign_payload(
            {
                "schema_version": "fixture.t20_35l_spec.v1",
                "checkpoint_identity_sha256": "a" * 64,
                "checkpoint_tree": [{"path": "model", "sha256": "b" * 64}],
                "trainable_parameter_names_sha256": "c" * 64,
                "trainable_parameter_count": 100,
                "paligemma_trainable_parameter_count": 0,
                "dataset_action_chunk_sha256": cls._matrix_hash(target),
                "lerobot_stack_identity_sha256": "d" * 64,
                "sampler_source_sha256": "e" * 64,
                "source_final_to_baseline_objective_ratio": 0.004,
                "source_objective_ratio_within_threshold": True,
                "base_noise_sha256_by_seed": [
                    row["base_noise_sha256"] for row in active_zero
                ],
            }
        )
        source_result = sign_payload(
            {
                "schema_version": "fixture.t20_35l_result.v1",
                "noise_mask_classification": "joint_active_and_padded_noise_sensitivity",
                "selected_next_hypothesis": "audit_joint_active_padded_flow_robustness",
                "gate_b_passed": False,
                "condition_evaluations": [
                    cls._source_condition(
                        "active_normal_padded_normal", active_one, target
                    ),
                    cls._source_condition(
                        "active_normal_padded_zero", cls._chunks(0.11, 0.03), target
                    ),
                    cls._source_condition(
                        "active_zero_padded_normal", active_zero, target
                    ),
                    cls._source_condition(
                        "active_zero_padded_zero", cls._chunks(0.073, 0.0), target
                    ),
                ],
            }
        )
        audit = sign_payload(
            {
                "schema_version": "fixture.t20_35m.v1",
                "t20_35l_result_identity_sha256": source_result["identity_sha256"],
                "interaction_classification": "active_noise_dominant_with_context_dependent_padded_interaction",
                "selected_next_hypothesis": "run_separately_reviewed_near_zero_active_noise_scale_discriminator_with_padded_normal",
                "best_noise_condition": "active_zero_padded_normal",
                "active_noise_harmful_at_both_padded_settings_all_metrics": True,
                "gate_b_passed": False,
            }
        )
        spec = build_evaluation_spec(
            factorial_audit=audit,
            source_spec=source_spec,
            source_result=source_result,
        )
        permit = build_evaluation_permit(spec=spec)
        attempt = sign_payload(
            {
                "schema_version": "scenesmith.t20_35n_evaluation_attempt.v1",
                "task_id": "T20.35n",
                "evaluation_spec_identity_sha256": spec["identity_sha256"],
                "evaluation_permit_identity_sha256": permit["identity_sha256"],
                "started_at": "2026-07-15T13:30:00-05:00",
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
        return spec, permit, attempt, source_result, target

    @classmethod
    def _result(cls, spec, permit, attempt, source, target, quarter, half):
        return build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_result=source,
            target_chunk=target,
            evaluated_active_scales=[
                cls._evaluation(0.25, quarter),
                cls._evaluation(0.5, half),
            ],
        )

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
        return {"active_noise_scale": scale, "decoded_action_chunks": chunks}

    @classmethod
    def _source_condition(cls, condition: str, chunks: list[dict], target):
        rows = []
        for row in chunks:
            errors = [
                abs(row["decoded_action_chunk"][t][j] - target[t][j])
                for t in range(50)
                for j in range(6)
            ]
            rows.append(
                {
                    **row,
                    "decoded_action_chunk_sha256": cls._matrix_hash(
                        row["decoded_action_chunk"]
                    ),
                    "mean_absolute_error_rad": sum(errors) / len(errors),
                    "maximum_absolute_error_rad": max(errors),
                }
            )
        spreads = [
            max(row["decoded_action_chunk"][t][j] for row in chunks)
            - min(row["decoded_action_chunk"][t][j] for row in chunks)
            for t in range(50)
            for j in range(6)
        ]
        return {
            "noise_condition": condition,
            "decoded_action_chunks": rows,
            "all_decoded_chunks_within_threshold": all(
                row["maximum_absolute_error_rad"] <= 0.05 for row in rows
            ),
            "worst_seed_maximum_error_rad": max(
                row["maximum_absolute_error_rad"] for row in rows
            ),
            "aggregate_mean_absolute_error_rad": sum(
                row["mean_absolute_error_rad"] for row in rows
            )
            / len(rows),
            "aggregate_mean_raw_decoded_spread_rad": sum(spreads) / len(spreads),
        }

    @staticmethod
    def _matrix_hash(matrix: list[list[float]]) -> str:
        return hashlib.sha256(canonical_json_bytes(matrix)).hexdigest()


if __name__ == "__main__":
    unittest.main()
