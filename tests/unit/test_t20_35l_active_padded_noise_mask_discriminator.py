from __future__ import annotations

import copy
import hashlib
import math
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35l_active_padded_noise_mask_discriminator import (
    build_evaluation_permit,
    build_evaluation_spec,
    build_result,
    noise_mask_for_condition,
    verify_evaluation_permit,
    verify_evaluation_spec,
    verify_result,
)


class T2035lActivePaddedNoiseMaskDiscriminatorTests(unittest.TestCase):
    def test_masks_are_exact_complements_over_six_and_twenty_six(self) -> None:
        active = noise_mask_for_condition(
            "active_normal_padded_zero", active_dimensions=6, maximum_dimensions=32
        )
        padded = noise_mask_for_condition(
            "active_zero_padded_normal", active_dimensions=6, maximum_dimensions=32
        )
        self.assertEqual(active, [1.0] * 6 + [0.0] * 26)
        self.assertEqual(padded, [0.0] * 6 + [1.0] * 26)
        self.assertEqual([a + b for a, b in zip(active, padded, strict=True)], [1.0] * 32)

    def test_padded_only_active_only_and_joint_routes_remain_distinct(self) -> None:
        spec, permit, attempt, source, target = self._contract()
        cases = (
            (
                self._chunks(0.07, 0.01),
                self._chunks(0.11, 0.03),
                "padded_noise_sensitivity_isolated",
                "audit_padded_noise_handling_and_trainable_invariance",
            ),
            (
                self._chunks(0.11, 0.03),
                self._chunks(0.07, 0.01),
                "active_action_noise_sensitivity_isolated",
                "audit_active_action_flow_consistency",
            ),
            (
                self._chunks(0.07, 0.01),
                self._chunks(0.08, 0.015),
                "joint_active_and_padded_noise_sensitivity",
                "audit_joint_active_padded_flow_robustness",
            ),
        )
        for active_chunks, padded_chunks, classification, route in cases:
            with self.subTest(classification=classification):
                result = self._result(
                    spec, permit, attempt, source, target, active_chunks, padded_chunks
                )
                self.assertFalse(result["gate_b_passed"])
                self.assertEqual(result["noise_mask_classification"], classification)
                self.assertEqual(result["selected_next_hypothesis"], route)
                verify_result(
                    result,
                    spec=spec,
                    permit=permit,
                    attempt=attempt,
                    source_result=source,
                    target_chunk=target,
                )

    def test_passing_mixed_mask_routes_only_gate_c_review(self) -> None:
        spec, permit, attempt, source, target = self._contract()
        result = self._result(
            spec,
            permit,
            attempt,
            source,
            target,
            self._chunks(0.04, 0.004),
            self._chunks(0.06, 0.01),
        )
        self.assertTrue(result["gate_b_passed"])
        self.assertEqual(result["selected_noise_condition"], "active_normal_padded_zero")
        self.assertEqual(
            result["selected_next_hypothesis"],
            "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction",
        )

    def test_spec_permit_result_and_authority_drift_fail_closed(self) -> None:
        spec, permit, attempt, source, target = self._contract()
        for mutation in (
            lambda value: value.update(active_action_dimension_count=7),
            lambda value: value["evaluated_noise_conditions"].reverse(),
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
            lambda value: value["authorized_actions"].append("optimizer_training"),
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
            self._chunks(0.07, 0.01),
            self._chunks(0.11, 0.03),
        )
        for mutation in (
            lambda value: value.update(gate_b_passed=True),
            lambda value: value.update(optimizer_created=True),
            lambda value: value.update(closed_loop_rollout=True),
            lambda value: value["condition_evaluations"][1].update(
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

    def test_nonfinite_wrong_noise_hash_and_bad_attempt_fail_closed(self) -> None:
        spec, permit, attempt, source, target = self._contract()
        active = self._evaluation(
            "active_normal_padded_zero", self._chunks(0.07, 0.01)
        )
        padded = self._evaluation(
            "active_zero_padded_normal", self._chunks(0.11, 0.03)
        )
        active["decoded_action_chunks"][0]["decoded_action_chunk"][0][0] = math.nan
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                source_result=source,
                target_chunk=target,
                mixed_condition_evaluations=[active, padded],
            )
        active = self._evaluation(
            "active_normal_padded_zero", self._chunks(0.07, 0.01)
        )
        active["decoded_action_chunks"][0]["base_noise_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "base noise"):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                source_result=source,
                target_chunk=target,
                mixed_condition_evaluations=[active, padded],
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
                self._chunks(0.07, 0.01),
                self._chunks(0.11, 0.03),
            )

    @classmethod
    def _contract(cls):
        target = [[0.0] * 6 for _ in range(50)]
        all_normal = cls._chunks(0.10, 0.02)
        all_zero = cls._chunks(0.07, 0.0)
        source_spec = sign_payload(
            {
                "schema_version": "fixture.t20_35j_spec.v1",
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
            }
        )
        source_result = sign_payload(
            {
                "schema_version": "fixture.t20_35j_result.v1",
                "initial_noise_scale_effect_positive": True,
                "selected_initial_noise_scale": 0.0,
                "gate_b_passed": False,
                "scale_evaluations": [
                    cls._source_evaluation(1.0, all_normal, target),
                    cls._source_evaluation(0.5, cls._chunks(0.08, 0.01), target),
                    cls._source_evaluation(0.0, all_zero, target),
                ],
            }
        )
        audit = sign_payload(
            {
                "schema_version": "fixture.t20_35k.v1",
                "t20_35j_result_identity_sha256": source_result["identity_sha256"],
                "sampler_classification": "matched_standard_normal_sampler_with_unsupervised_padded_noise_exposure",
                "selected_next_hypothesis": "run_separately_reviewed_active_vs_padded_noise_mask_discriminator",
                "supervised_action_dimension_count": 6,
                "maximum_action_dimension_count": 32,
                "padded_action_dimension_count": 26,
                "gate_b_passed": False,
            }
        )
        spec = build_evaluation_spec(
            sampler_audit=audit,
            source_spec=source_spec,
            source_result=source_result,
        )
        permit = build_evaluation_permit(spec=spec)
        attempt = sign_payload(
            {
                "schema_version": "scenesmith.t20_35l_evaluation_attempt.v1",
                "task_id": "T20.35l",
                "evaluation_spec_identity_sha256": spec["identity_sha256"],
                "evaluation_permit_identity_sha256": permit["identity_sha256"],
                "started_at": "2026-07-15T13:00:00-05:00",
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
    def _result(cls, spec, permit, attempt, source, target, active, padded):
        return build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_result=source,
            target_chunk=target,
            mixed_condition_evaluations=[
                cls._evaluation("active_normal_padded_zero", active),
                cls._evaluation("active_zero_padded_normal", padded),
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
    def _evaluation(condition: str, chunks: list[dict]):
        return {"noise_condition": condition, "decoded_action_chunks": chunks}

    @classmethod
    def _source_evaluation(cls, scale: float, chunks: list[dict], target):
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
            "initial_noise_scale": scale,
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
