from __future__ import annotations

import copy
import hashlib
import math
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35o_flow_trajectory_consistency_audit import (
    build_evaluation_permit,
    build_evaluation_spec,
    build_result,
    verify_evaluation_permit,
    verify_evaluation_spec,
    verify_result,
)


class T2035oFlowTrajectoryConsistencyAuditTests(unittest.TestCase):
    def test_late_concentrated_residual_routes_terminal_consistency(self) -> None:
        spec, permit, attempt, source, target, normalized_target = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_result=source,
            target_chunk=target,
            normalized_padded_target=normalized_target,
            trajectory_evaluations=self._trajectories(
                source, normalized_target, late_residual=True
            ),
        )
        verify_result(
            result,
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_result=source,
            target_chunk=target,
        )
        self.assertGreaterEqual(result["last_three_step_active_residual_fraction"], 0.5)
        self.assertEqual(
            result["flow_residual_classification"],
            "late_step_active_flow_residual_concentrated",
        )
        self.assertEqual(
            result["selected_next_hypothesis"],
            "design_terminal_time_flow_consistency_training_correction",
        )
        self.assertFalse(result["gate_b_passed"])

    def test_reference_velocity_and_residual_are_recomputed_exactly(self) -> None:
        spec, permit, attempt, source, target, normalized_target = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_result=source,
            target_chunk=target,
            normalized_padded_target=normalized_target,
            trajectory_evaluations=self._trajectories(
                source, normalized_target, late_residual=False
            ),
        )
        step = result["trajectory_evaluations"][0]["steps"][0]
        self.assertEqual(step["time"], 1.0)
        self.assertAlmostEqual(step["active_velocity_residual_maximum"], 0.01)
        self.assertAlmostEqual(step["active_velocity_residual_mean_absolute"], 0.01)
        self.assertEqual(len(step["active_velocity_residual_mean_absolute_by_channel"]), 6)
        self.assertEqual(
            result["flow_residual_classification"], "distributed_active_flow_residual"
        )
        self.assertEqual(
            result["selected_next_hypothesis"],
            "design_full_path_flow_consistency_training_correction",
        )

    def test_channel_concentration_routes_dominant_channel_audit(self) -> None:
        spec, permit, attempt, source, target, normalized_target = self._contract()
        trajectories = self._trajectories(
            source, normalized_target, late_residual=False
        )
        for row in trajectories:
            for step in row["steps"]:
                state = step["state"]
                ideal = [
                    [
                        (state[t][j] - normalized_target[t][j]) / step["time"]
                        for j in range(32)
                    ]
                    for t in range(50)
                ]
                step["learned_velocity"] = [
                    [ideal[t][j] + (0.1 if j == 2 else 0.0) for j in range(32)]
                    for t in range(50)
                ]
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_result=source,
            target_chunk=target,
            normalized_padded_target=normalized_target,
            trajectory_evaluations=trajectories,
        )
        self.assertEqual(result["dominant_active_channel_index"], 2)
        self.assertEqual(
            result["flow_residual_classification"],
            "active_channel_flow_residual_concentrated",
        )
        self.assertEqual(
            result["selected_next_hypothesis"],
            "audit_dominant_active_channel_training_semantics",
        )

    def test_spec_permit_result_and_authority_drift_fail_closed(self) -> None:
        spec, permit, attempt, source, target, normalized_target = self._contract()
        for mutation in (
            lambda value: value.update(active_noise_scale=0.25),
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
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_result=source,
            target_chunk=target,
            normalized_padded_target=normalized_target,
            trajectory_evaluations=self._trajectories(
                source, normalized_target, late_residual=True
            ),
        )
        for mutation in (
            lambda value: value.update(gate_b_passed=True),
            lambda value: value.update(optimizer_created=True),
            lambda value: value["trajectory_evaluations"][0]["steps"][0].update(
                active_velocity_residual_maximum=9.0
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

    def test_nonfinite_wrong_endpoint_and_bad_attempt_fail_closed(self) -> None:
        spec, permit, attempt, source, target, normalized_target = self._contract()
        trajectories = self._trajectories(source, normalized_target, late_residual=True)
        trajectories[0]["steps"][0]["learned_velocity"][0][0] = math.nan
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                source_result=source,
                target_chunk=target,
                normalized_padded_target=normalized_target,
                trajectory_evaluations=trajectories,
            )
        trajectories = self._trajectories(source, normalized_target, late_residual=True)
        trajectories[0]["decoded_action_chunk"][0][0] += 0.001
        with self.assertRaisesRegex(ValueError, "decoded endpoint"):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                source_result=source,
                target_chunk=target,
                normalized_padded_target=normalized_target,
                trajectory_evaluations=trajectories,
            )
        bad_attempt = copy.deepcopy(attempt)
        bad_attempt["one_evaluation_permit_consumed"] = False
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                permit=permit,
                attempt=sign_payload(bad_attempt),
                source_result=source,
                target_chunk=target,
                normalized_padded_target=normalized_target,
                trajectory_evaluations=self._trajectories(
                    source, normalized_target, late_residual=True
                ),
            )

    def test_target_padding_step_grid_and_initial_state_fail_closed(self) -> None:
        for mutation in (
            lambda normalized, trajectories: normalized[0].__setitem__(6, 0.1),
            lambda normalized, trajectories: trajectories[0]["steps"].pop(),
            lambda normalized, trajectories: trajectories[0]["steps"][0].update(
                time=0.95
            ),
            lambda normalized, trajectories: trajectories[0]["steps"][0]["state"][
                0
            ].__setitem__(0, 0.1),
        ):
            spec, permit, attempt, source, target, normalized_target = self._contract()
            trajectories = self._trajectories(
                source, normalized_target, late_residual=True
            )
            mutation(normalized_target, trajectories)
            with self.assertRaises(ValueError):
                build_result(
                    spec=spec,
                    permit=permit,
                    attempt=attempt,
                    source_result=source,
                    target_chunk=target,
                    normalized_padded_target=normalized_target,
                    trajectory_evaluations=trajectories,
                )

    @classmethod
    def _contract(cls):
        target = [[0.0] * 6 for _ in range(50)]
        endpoint = cls._chunks(0.06, 0.005)
        source_spec = sign_payload(
            {
                "schema_version": "fixture.t20_35n_spec.v1",
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
                    row["base_noise_sha256"] for row in endpoint
                ],
            }
        )
        source_result = sign_payload(
            {
                "schema_version": "fixture.t20_35n_result.v1",
                "selected_active_noise_scale": 0.0,
                "gate_b_passed": False,
                "selected_next_hypothesis": "active_zero_endpoint_optimum_route_model_flow_consistency_correction",
                "active_scale_evaluations": [
                    cls._source_scale(0.0, endpoint, target),
                    cls._source_scale(0.25, cls._chunks(0.08, 0.01), target),
                    cls._source_scale(0.5, cls._chunks(0.1, 0.02), target),
                    cls._source_scale(1.0, cls._chunks(0.15, 0.04), target),
                ],
            }
        )
        spec = build_evaluation_spec(
            source_spec=source_spec,
            source_result=source_result,
        )
        permit = build_evaluation_permit(spec=spec)
        attempt = sign_payload(
            {
                "schema_version": "scenesmith.t20_35o_evaluation_attempt.v1",
                "task_id": "T20.35o",
                "evaluation_spec_identity_sha256": spec["identity_sha256"],
                "evaluation_permit_identity_sha256": permit["identity_sha256"],
                "started_at": "2026-07-15T14:00:00-05:00",
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
        normalized_target = [[0.0] * 32 for _ in range(50)]
        return spec, permit, attempt, source_result, target, normalized_target

    @classmethod
    def _trajectories(cls, source, normalized_target, *, late_residual: bool):
        endpoint = source["active_scale_evaluations"][0]["decoded_action_chunks"]
        rows = []
        for seed_index, seed in enumerate(
            (20260721, 20260722, 20260723, 20260724, 20260725)
        ):
            steps = []
            for step_index in range(10):
                time = round(1.0 - step_index / 10, 12)
                state = [[0.0] * 32 for _ in range(50)]
                for row in state:
                    for channel in range(6, 32):
                        row[channel] = 0.1 + seed_index * 0.001
                ideal = [
                    [
                        (state[t][j] - normalized_target[t][j]) / time
                        for j in range(32)
                    ]
                    for t in range(50)
                ]
                residual = 0.1 if late_residual and step_index >= 7 else 0.01
                velocity = [
                    [ideal[t][j] + (residual if j < 6 else 0.005) for j in range(32)]
                    for t in range(50)
                ]
                steps.append(
                    {
                        "step_index": step_index,
                        "time": time,
                        "state": state,
                        "learned_velocity": velocity,
                    }
                )
            rows.append(
                {
                    "inference_seed": seed,
                    "base_noise_sha256": endpoint[seed_index]["base_noise_sha256"],
                    "decoded_action_chunk": copy.deepcopy(
                        endpoint[seed_index]["decoded_action_chunk"]
                    ),
                    "steps": steps,
                }
            )
        return rows

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

    @classmethod
    def _source_scale(cls, scale: float, chunks: list[dict], target):
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
            "active_noise_scale": scale,
            "padded_noise_scale": 1.0,
            "decoded_action_chunks": rows,
            "all_decoded_chunks_within_threshold": False,
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
