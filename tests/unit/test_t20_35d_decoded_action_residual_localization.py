from __future__ import annotations

import copy
import hashlib
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (
    INFERENCE_SEEDS,
    JOINT_NAMES,
    build_evaluation_permit,
    build_report,
    verify_evaluation_permit,
    verify_report,
)
from scripts.robot_lab.run_t20_35d_residual_localization import _verify_attempt


class T2035DDecodedActionResidualLocalizationTests(unittest.TestCase):
    def test_joint_specific_residual_is_localized(self) -> None:
        target = self._target()
        chunks = self._chunks(target)
        for row in chunks:
            for timestep in range(10, 20):
                row["decoded_action_chunk"][timestep][2] = 0.06
        report, spec, permit = self._report(target, chunks)
        self.assertEqual(report["residual_classification"], "joint_specific_residual")
        self.assertEqual(
            report["selected_next_hypothesis"],
            "inspect_joint_normalization_or_output_projection",
        )
        elbow = report["per_joint_summary"][2]
        self.assertEqual(elbow["joint_name"], JOINT_NAMES[2])
        self.assertEqual(elbow["threshold_exceedance_count"], 50)
        verify_report(report, spec=spec, permit=permit)

    def test_chunk_boundary_residual_is_localized(self) -> None:
        target = self._target()
        chunks = self._chunks(target)
        for row in chunks:
            for timestep in (0, 1, 48, 49):
                for joint in range(6):
                    row["decoded_action_chunk"][timestep][joint] = 0.06
        report, _, _ = self._report(target, chunks)
        self.assertEqual(report["residual_classification"], "chunk_boundary_residual")
        self.assertEqual(report["boundary_exceedance_fraction"], 1.0)

    def test_joint_and_boundary_concentration_is_distinct(self) -> None:
        target = self._target()
        chunks = self._chunks(target)
        for row in chunks:
            for timestep in range(5):
                row["decoded_action_chunk"][timestep][4] = 0.06
        report, _, _ = self._report(target, chunks)
        self.assertEqual(
            report["residual_classification"],
            "joint_and_chunk_boundary_concentrated",
        )

    def test_distributed_residual_is_not_overclassified(self) -> None:
        target = self._target()
        chunks = self._chunks(target)
        for row in chunks:
            for joint in range(6):
                row["decoded_action_chunk"][10 + joint][joint] = 0.06
        report, _, _ = self._report(target, chunks)
        self.assertEqual(
            report["residual_classification"], "distributed_decoding_residual"
        )

    def test_hash_metric_seed_and_nonfinite_drift_fail_closed(self) -> None:
        target = self._target()
        chunks = self._chunks(target)
        spec = self._spec(target, chunks)
        permit = build_evaluation_permit(spec=spec)
        for mutation in (
            lambda value: value[0]["decoded_action_chunk"][0].__setitem__(0, 0.01),
            lambda value: value.reverse(),
            lambda value: value[0]["decoded_action_chunk"][0].__setitem__(0, float("nan")),
        ):
            drift = copy.deepcopy(chunks)
            mutation(drift)
            with self.assertRaises(ValueError):
                build_report(
                    spec=spec,
                    permit=permit,
                    replay_attempt_identity="d" * 64,
                    target_chunk=target,
                    replay_chunks=drift,
                )

    def test_permit_cannot_add_optimizer_or_external_authority(self) -> None:
        target = self._target()
        chunks = self._chunks(target)
        spec = self._spec(target, chunks)
        permit = build_evaluation_permit(spec=spec)
        verify_evaluation_permit(permit, spec=spec)
        for mutation in (
            lambda value: value.update(optimizer_training_authorized=True),
            lambda value: value["authorized_actions"].append("simulation_optimizer_training"),
            lambda value: value.update(external_compute_authorized=True),
        ):
            drift = copy.deepcopy(permit)
            mutation(drift)
            with self.assertRaisesRegex(ValueError, "permit drifted"):
                verify_evaluation_permit(sign_payload(drift), spec=spec)

    def test_attempt_marker_precedes_model_and_forbids_optimizer(self) -> None:
        marker = sign_payload(
            {
                "schema_version": "scenesmith.t20_35d_replay_attempt.v1",
                "task_id": "T20.35d",
                "evaluation_spec_identity_sha256": "a" * 64,
                "evaluation_permit_identity_sha256": "b" * 64,
                "started_at": "2026-07-15T10:00:00-05:00",
                "one_replay_permit_consumed": True,
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
        _verify_attempt(marker, spec_identity="a" * 64, permit_identity="b" * 64)
        drift = copy.deepcopy(marker)
        drift["optimizer_created_at_marker"] = True
        with self.assertRaisesRegex(ValueError, "attempt drifted"):
            _verify_attempt(
                sign_payload(drift),
                spec_identity="a" * 64,
                permit_identity="b" * 64,
            )

    @staticmethod
    def _target() -> list[list[float]]:
        return [[0.0] * 6 for _ in range(50)]

    @staticmethod
    def _chunks(target: list[list[float]]) -> list[dict]:
        return [
            {
                "inference_seed": seed,
                "decoded_action_chunk": copy.deepcopy(target),
            }
            for seed in INFERENCE_SEEDS
        ]

    @classmethod
    def _spec(cls, target: list[list[float]], chunks: list[dict]) -> dict:
        expected = []
        for row in chunks:
            matrix = row["decoded_action_chunk"]
            errors = [
                abs(matrix[timestep][joint] - target[timestep][joint])
                for timestep in range(50)
                for joint in range(6)
            ]
            expected.append(
                {
                    "inference_seed": row["inference_seed"],
                    "decoded_action_chunk_sha256": hashlib.sha256(
                        canonical_json_bytes(matrix)
                    ).hexdigest(),
                    "mean_absolute_error_rad": sum(errors) / len(errors),
                    "maximum_absolute_error_rad": max(errors),
                }
            )
        return sign_payload(
            {
                "schema_version": "scenesmith.t20_35d_residual_localization_spec.v1",
                "task_id": "T20.35d",
                "dataset_action_chunk_sha256": hashlib.sha256(
                    canonical_json_bytes(target)
                ).hexdigest(),
                "t20_35c_result_identity_sha256": "a" * 64,
                "source_run_identity_sha256": "b" * 64,
                "checkpoint_identity_sha256": "c" * 64,
                "expected_decoded_action_chunks": expected,
            }
        )

    @classmethod
    def _report(cls, target: list[list[float]], chunks: list[dict]):
        spec = cls._spec(target, chunks)
        permit = build_evaluation_permit(spec=spec)
        report = build_report(
            spec=spec,
            permit=permit,
            replay_attempt_identity="d" * 64,
            target_chunk=target,
            replay_chunks=chunks,
        )
        return report, spec, permit


if __name__ == "__main__":
    unittest.main()
