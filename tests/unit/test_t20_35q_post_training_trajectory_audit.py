from __future__ import annotations

import copy
import hashlib
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35q_post_training_trajectory_audit import (
    build_evaluation_permit,
    build_evaluation_spec,
    build_result,
    verify_evaluation_permit,
    verify_evaluation_spec,
    verify_result,
)


class T2035qPostTrainingTrajectoryAuditTests(unittest.TestCase):
    def test_early_residual_worsening_routes_full_path_interference(self) -> None:
        spec, permit, attempt, source, training_result, target, chunks = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_trajectory_result=source,
            training_result=training_result,
            target_chunk=target,
            new_trajectory_evaluations=self._new_trajectories(
                source, chunks, early_residual=True
            ),
        )
        verify_result(
            result,
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_trajectory_result=source,
            training_result=training_result,
            target_chunk=target,
        )
        self.assertEqual(
            result["earliest_material_active_target_residual_worsening_step"], 3
        )
        self.assertEqual(
            result["path_interference_classification"],
            "early_mid_path_interference",
        )
        self.assertEqual(
            result["selected_next_hypothesis"],
            "design_full_path_self_consistency_correction",
        )
        self.assertFalse(result["gate_b_passed"])

    def test_late_only_worsening_routes_off_trajectory_supervision(self) -> None:
        spec, permit, attempt, source, training_result, target, chunks = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_trajectory_result=source,
            training_result=training_result,
            target_chunk=target,
            new_trajectory_evaluations=self._new_trajectories(
                source, chunks, late_residual=True
            ),
        )
        self.assertEqual(
            result["earliest_material_active_target_residual_worsening_step"], 7
        )
        self.assertEqual(
            result["path_interference_classification"],
            "off_trajectory_terminal_supervision",
        )

    def test_padded_displacement_routes_padded_coupling(self) -> None:
        spec, permit, attempt, source, training_result, target, chunks = self._contract()
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_trajectory_result=source,
            training_result=training_result,
            target_chunk=target,
            new_trajectory_evaluations=self._new_trajectories(
                source, chunks, padded_displacement=True
            ),
        )
        self.assertEqual(
            result["path_interference_classification"], "padded_state_coupling"
        )
        self.assertEqual(
            result["selected_next_hypothesis"],
            "design_padded_state_invariance_correction",
        )

    def test_spec_permit_result_and_endpoint_drift_fail_closed(self) -> None:
        spec, permit, attempt, source, training_result, target, chunks = self._contract()
        for mutation in (
            lambda value: value.update(num_inference_steps=20),
            lambda value: value.update(optimizer_training=True),
            lambda value: value.update(active_noise_scale=1.0),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_evaluation_spec(sign_payload(drift), expected_spec=spec)
        drift = copy.deepcopy(permit)
        drift["brev_compute_authorized"] = True
        with self.assertRaises(ValueError):
            verify_evaluation_permit(sign_payload(drift), spec=spec)
        trajectories = self._new_trajectories(source, chunks, early_residual=True)
        trajectories[0]["decoded_action_chunk"][0][0] += 0.001
        with self.assertRaisesRegex(ValueError, "endpoint"):
            build_result(
                spec=spec,
                permit=permit,
                attempt=attempt,
                source_trajectory_result=source,
                training_result=training_result,
                target_chunk=target,
                new_trajectory_evaluations=trajectories,
            )
        result = build_result(
            spec=spec,
            permit=permit,
            attempt=attempt,
            source_trajectory_result=source,
            training_result=training_result,
            target_chunk=target,
            new_trajectory_evaluations=self._new_trajectories(
                source, chunks, early_residual=True
            ),
        )
        drift = copy.deepcopy(result)
        drift["gate_b_passed"] = True
        with self.assertRaises(ValueError):
            verify_result(
                sign_payload(drift),
                spec=spec,
                permit=permit,
                attempt=attempt,
                source_trajectory_result=source,
                training_result=training_result,
                target_chunk=target,
            )

    @classmethod
    def _contract(cls):
        target = [[0.0] * 6 for _ in range(50)]
        normalized_target = [[0.0] * 32 for _ in range(50)]
        source_rows = []
        chunks = cls._chunks(0.1)
        for seed_index, seed in enumerate(cls._seeds()):
            steps = []
            for step_index in range(10):
                time = 1.0 - step_index / 10
                state = [[0.0] * 6 + [0.1 + seed_index * 0.001] * 26 for _ in range(50)]
                velocity = [
                    [
                        (state[t][j] - normalized_target[t][j]) / time
                        + (0.01 if j < 6 else 0.005)
                        for j in range(32)
                    ]
                    for t in range(50)
                ]
                steps.append(
                    {
                        "step_index": step_index,
                        "time": time,
                        "state": state,
                        "state_sha256": cls._hash(state),
                        "learned_velocity": velocity,
                        "learned_velocity_sha256": cls._hash(velocity),
                    }
                )
            source_rows.append(
                {
                    "inference_seed": seed,
                    "base_noise_sha256": f"{seed_index + 10:064x}",
                    "decoded_action_chunk": [[0.06] * 6 for _ in range(50)],
                    "decoded_action_chunk_sha256": cls._hash([[0.06] * 6 for _ in range(50)]),
                    "steps": steps,
                }
            )
        source_result = sign_payload(
            {
                "schema_version": "fixture.t20_35o_result.v1",
                "normalized_padded_target": normalized_target,
                "normalized_padded_target_sha256": cls._hash(normalized_target),
                "trajectory_evaluations": source_rows,
                "flow_residual_classification": "late_step_active_flow_residual_concentrated",
                "gate_b_passed": False,
                "selected_next_hypothesis": "design_terminal_time_flow_consistency_training_correction",
            }
        )
        source_spec = sign_payload(
            {
                "schema_version": "fixture.t20_35o_spec.v1",
                "checkpoint_identity_sha256": "a" * 64,
                "checkpoint_tree": [{"path": "source", "sha256": "b" * 64}],
                "dataset_action_chunk_sha256": cls._hash(target),
                "lerobot_stack_identity_sha256": "c" * 64,
                "sampler_source_sha256": "d" * 64,
                "base_noise_sha256_by_seed": [row["base_noise_sha256"] for row in source_rows],
                "source_decoded_action_sha256_by_seed": [row["decoded_action_chunk_sha256"] for row in source_rows],
            }
        )
        training_run = sign_payload(
            {
                "schema_version": "fixture.t20_35p_run.v1",
                "checkpoint_identity_sha256": "e" * 64,
                "checkpoint_tree": [{"path": "new", "sha256": "f" * 64}],
            }
        )
        training_result = sign_payload(
            {
                "schema_version": "fixture.t20_35p_result.v1",
                "run_identity_sha256": training_run["identity_sha256"],
                "objective_ratio_within_threshold": True,
                "all_decoded_chunks_within_threshold": False,
                "gate_b_passed": False,
                "selected_next_hypothesis": "terminal_objective_pass_action_fail_route_post_training_trajectory_audit",
                "decoded_action_chunks": [
                    {
                        "inference_seed": row["inference_seed"],
                        "decoded_action_chunk_sha256": cls._hash(row["decoded_action_chunk"]),
                        "maximum_absolute_error_rad": 0.1,
                        "mean_absolute_error_rad": 0.05,
                    }
                    for row in chunks
                ],
            }
        )
        spec = build_evaluation_spec(
            source_spec=source_spec,
            source_result=source_result,
            training_run=training_run,
            training_result=training_result,
        )
        permit = build_evaluation_permit(spec=spec)
        attempt = sign_payload(
            {
                "schema_version": "scenesmith.t20_35q_evaluation_attempt.v1",
                "task_id": "T20.35q",
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
        return spec, permit, attempt, source_result, training_result, target, chunks

    @classmethod
    def _new_trajectories(
        cls,
        source,
        chunks,
        *,
        early_residual=False,
        late_residual=False,
        padded_displacement=False,
    ):
        rows = []
        for source_row, chunk in zip(source["trajectory_evaluations"], chunks, strict=True):
            steps = []
            for source_step in source_row["steps"]:
                step_index = source_step["step_index"]
                state = copy.deepcopy(source_step["state"])
                if padded_displacement:
                    for row in state:
                        for channel in range(6, 32):
                            row[channel] += 0.2
                extra = 0.0
                if early_residual and step_index >= 3:
                    extra = 0.1
                if late_residual and step_index >= 7:
                    extra = 0.1
                target = source["normalized_padded_target"]
                velocity = [
                    [
                        (state[t][j] - target[t][j]) / source_step["time"]
                        + (0.01 + extra if j < 6 else 0.005)
                        for j in range(32)
                    ]
                    for t in range(50)
                ]
                steps.append(
                    {
                        "step_index": step_index,
                        "time": source_step["time"],
                        "state": state,
                        "learned_velocity": velocity,
                    }
                )
            rows.append(
                {
                    "inference_seed": chunk["inference_seed"],
                    "base_noise_sha256": source_row["base_noise_sha256"],
                    "decoded_action_chunk": copy.deepcopy(chunk["decoded_action_chunk"]),
                    "steps": steps,
                }
            )
        return rows

    @classmethod
    def _chunks(cls, value):
        return [
            {
                "inference_seed": seed,
                "decoded_action_chunk": [[value + index * 0.001] * 6 for _ in range(50)],
            }
            for index, seed in enumerate(cls._seeds())
        ]

    @staticmethod
    def _seeds():
        return (20260721, 20260722, 20260723, 20260724, 20260725)

    @staticmethod
    def _hash(value):
        return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


if __name__ == "__main__":
    unittest.main()
