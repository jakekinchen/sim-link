import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36o_baseline_capture import (
    BASELINE_PERMIT_PATH,
    CHUNK_START_FRAMES,
    EXECUTED_LENGTHS,
    INFERENCE_SEEDS,
    build_result,
    build_run_summary,
    build_tensor_artifact,
    build_trajectory_artifact,
    build_attempt_marker,
    build_baseline_permit,
    build_runtime_preflight,
    score_action_tensor,
    verify_tensor_artifact,
    verify_trajectory_artifact,
    verify_result,
    verify_run_summary,
)


class T2036oBaselineCaptureContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sources = {
            "bridge_spec_identity_sha256": "1" * 64,
            "checkpoint_identity_sha256": "2" * 64,
            "source_run_identity_sha256": "3" * 64,
            "source_result_identity_sha256": "4" * 64,
            "frozen_gate_identity_sha256": "5" * 64,
            "lerobot_stack_identity_sha256": "6" * 64,
            "required_dependency_versions": {"torch": "2.11.0"},
            "checkpoint_tree": [
                {"path": "model.safetensors", "sha256": "7" * 64, "size_bytes": 1}
            ],
            "snapshot_revision": "8" * 40,
            "snapshot_tree": [
                {"path": "model.safetensors", "sha256": "9" * 64, "size_bytes": 2}
            ],
            "probe_seed_by_start": [
                {"start_frame": start, "inference_seeds": list(INFERENCE_SEEDS)}
                for start in CHUNK_START_FRAMES
            ],
            "base_noise_sha256_by_seed": [character * 64 for character in "abcde"],
            "target_bindings": [
                {
                    "start_frame": start,
                    "executed_length": length,
                    "padded_target_action_sha256": "f" * 64,
                    "executed_mask_sha256": "0" * 64,
                }
                for start, length in zip(CHUNK_START_FRAMES, EXECUTED_LENGTHS, strict=True)
            ],
            "expected_start_zero_hashes": [character * 64 for character in "12345"],
        }

    def _preflight(self):
        return build_runtime_preflight(
            sources=self.sources,
            authority_identity="a" * 64,
            python_major_minor=[3, 12],
            mps_available=True,
            checkpoint_tree=self.sources["checkpoint_tree"],
            dependency_versions=self.sources["required_dependency_versions"],
            snapshot_revision=self.sources["snapshot_revision"],
            snapshot_tree=self.sources["snapshot_tree"],
            free_disk_bytes=10_000_000_000,
            source_commit="b" * 40,
            remote_source_commit="b" * 40,
            attempt_exists=False,
            result_exists=False,
        )

    def test_permit_binds_exact_probe_matrix_and_no_optimizer(self) -> None:
        permit = build_baseline_permit(
            sources=self.sources,
            authority_identity="a" * 64,
            runtime_preflight=self._preflight(),
        )
        self.assertEqual(permit["chunk_start_frames"], list(CHUNK_START_FRAMES))
        self.assertEqual(permit["executed_lengths"], list(EXECUTED_LENGTHS))
        self.assertEqual(permit["inference_seeds"], list(INFERENCE_SEEDS))
        self.assertEqual(permit["repeats_per_start_seed"], 2)
        self.assertEqual(permit["decoded_chunk_count"], 50)
        self.assertEqual(permit["denoise_step_record_count"], 500)
        self.assertEqual(permit["expected_start_zero_hashes"], self.sources["expected_start_zero_hashes"])
        self.assertFalse(permit["optimizer_created"])
        self.assertFalse(permit["optimizer_training"])
        self.assertFalse(permit["gate_c_authorized"])
        self.assertEqual(str(BASELINE_PERMIT_PATH), "configurations/robot_lab/t20_36o_baseline_capture_permit.json")

    def test_preflight_fails_closed_on_remote_or_existing_output(self) -> None:
        kwargs = {
            "sources": self.sources,
            "authority_identity": "a" * 64,
            "python_major_minor": [3, 12],
            "mps_available": True,
            "checkpoint_tree": self.sources["checkpoint_tree"],
            "dependency_versions": self.sources["required_dependency_versions"],
            "snapshot_revision": self.sources["snapshot_revision"],
            "snapshot_tree": self.sources["snapshot_tree"],
            "free_disk_bytes": 10_000_000_000,
            "source_commit": "b" * 40,
            "remote_source_commit": "c" * 40,
            "attempt_exists": False,
            "result_exists": False,
        }
        with self.assertRaises(ValueError):
            build_runtime_preflight(**kwargs)
        kwargs["remote_source_commit"] = kwargs["source_commit"]
        kwargs["result_exists"] = True
        with self.assertRaises(ValueError):
            build_runtime_preflight(**kwargs)

    def test_signed_mutation_cannot_expand_permit(self) -> None:
        permit = build_baseline_permit(
            sources=self.sources,
            authority_identity="a" * 64,
            runtime_preflight=self._preflight(),
        )
        drift = copy.deepcopy(permit)
        drift["optimizer_created"] = True
        self.assertNotEqual(sign_payload(drift), permit)

    def test_marker_precedes_checkpoint_and_model_actions(self) -> None:
        permit = build_baseline_permit(
            sources=self.sources,
            authority_identity="a" * 64,
            runtime_preflight=self._preflight(),
        )
        marker = build_attempt_marker(
            permit=permit,
            authority_identity="a" * 64,
            source_commit="b" * 40,
        )
        self.assertTrue(marker["created_before_checkpoint_tensor_read"])
        self.assertFalse(marker["checkpoint_tensor_read"])
        self.assertFalse(marker["model_constructed"])
        self.assertFalse(marker["optimizer_created"])

    def test_exact_frozen_gate_masks_only_unexecuted_tail(self) -> None:
        thresholds = {
            "reach": {
                "shoulder_pan": 0.1,
                "shoulder_lift": 0.05,
                "elbow_flex": 0.1,
                "wrist_flex": 0.4,
                "wrist_roll": 0.4,
                "gripper": 0.1,
            },
            "grasp": {
                "shoulder_pan": 0.1,
                "shoulder_lift": 0.05,
                "elbow_flex": 0.1,
                "wrist_flex": 0.1,
                "wrist_roll": 0.4,
                "gripper": 0.025,
            },
        }
        target = [[0.0] * 6 for _ in range(50)]
        predicted = [[0.0] * 6 for _ in range(50)]
        predicted[31][5] = 0.09
        predicted[32][5] = 0.09
        predicted[49][5] = 10.0
        score = score_action_tensor(
            tensor=predicted,
            target=target,
            executed_mask=[True] * 44 + [False] * 6,
            thresholds=thresholds,
        )
        self.assertFalse(score["passed"])
        self.assertEqual(score["executed_timestep_count"], 44)
        self.assertEqual(score["violation_count"], 1)
        self.assertEqual(score["violations"][0]["timestep"], 32)
        self.assertEqual(score["violations"][0]["phase_group"], "grasp")

    def test_tensor_artifact_requires_start_zero_hashes_and_exact_repeats(self) -> None:
        permit = build_baseline_permit(
            sources=self.sources,
            authority_identity="a" * 64,
            runtime_preflight=self._preflight(),
        )
        marker = build_attempt_marker(
            permit=permit,
            authority_identity="a" * 64,
            source_commit="b" * 40,
        )
        rows = []
        expected_hashes = []
        for start_index, (start, length) in enumerate(
            zip(CHUNK_START_FRAMES, EXECUTED_LENGTHS, strict=True)
        ):
            for seed_index, seed in enumerate(INFERENCE_SEEDS):
                tensor = [
                    [float(start_index), float(seed_index), 0.0, 0.0, 0.0, 0.0]
                    for _ in range(50)
                ]
                if start == 0:
                    from scenesmith.robot_lab.artifact_contract import canonical_json_bytes
                    import hashlib

                    expected_hashes.append(
                        hashlib.sha256(canonical_json_bytes(tensor)).hexdigest()
                    )
                for repeat_index in range(2):
                    rows.append(
                        {
                            "start_index": start_index,
                            "start_frame": start,
                            "executed_length": length,
                            "seed_index": seed_index,
                            "inference_seed": seed,
                            "repeat_index": repeat_index,
                            "decoded_action_chunk": tensor,
                        }
                    )
        permit = dict(permit)
        permit["expected_start_zero_hashes"] = expected_hashes
        permit = sign_payload(permit)
        marker = build_attempt_marker(
            permit=permit,
            authority_identity="a" * 64,
            source_commit="b" * 40,
        )
        artifact = build_tensor_artifact(
            attempt=marker,
            permit=permit,
            rows=rows,
        )
        verify_tensor_artifact(artifact, attempt=marker, permit=permit)
        self.assertEqual(artifact["tensor_count"], 50)
        self.assertTrue(artifact["all_start_zero_hashes_reproduced"])
        self.assertTrue(artifact["all_repeats_bit_identical"])

        matrix = [[0.0] * 32 for _ in range(50)]
        steps = [
            {
                "step_index": step_index,
                "time": 1.0 - step_index / 10,
                "state": matrix,
                "learned_velocity": matrix,
            }
            for step_index in range(10)
        ]
        trajectory_rows = [
            {
                **{
                    key: row[key]
                    for key in (
                        "start_index",
                        "start_frame",
                        "executed_length",
                        "seed_index",
                        "inference_seed",
                        "repeat_index",
                    )
                },
                "base_noise_sha256": permit["base_noise_sha256_by_seed"][
                    row["seed_index"]
                ],
                "decoded_action_chunk_sha256": row[
                    "decoded_action_chunk_sha256"
                ],
                "steps": steps,
            }
            for row in artifact["rows"]
        ]
        trajectory = build_trajectory_artifact(
            attempt=marker,
            permit=permit,
            tensor_artifact=artifact,
            rows=trajectory_rows,
        )
        verify_trajectory_artifact(
            trajectory,
            attempt=marker,
            permit=permit,
            tensor_artifact=artifact,
        )
        self.assertEqual(trajectory["trajectory_count"], 50)
        self.assertEqual(trajectory["denoise_step_record_count"], 500)
        self.assertEqual(
            trajectory["matrix_encoding"],
            "base64_float32_little_endian_c_order",
        )
        thresholds = {
            phase: {joint: 0.1 for joint in (
                "shoulder_pan",
                "shoulder_lift",
                "elbow_flex",
                "wrist_flex",
                "wrist_roll",
                "gripper",
            )}
            for phase in ("reach", "grasp")
        }
        sources = {
            "bridge_spec": {
                "identity_sha256": permit["bridge_spec_identity_sha256"],
                "acceptance": {
                    "phase_joint_maximum_error_rad": thresholds,
                    "maximum_source_batch_objective_ratio": 0.1,
                    "strict_uniform_maximum_absolute_error_rad_report_only": 0.05,
                },
                "source_windows": [
                    {
                        "start_frame": start,
                        "padded_target_action_mujoco_rad": [[0.0] * 6 for _ in range(50)],
                        "executed_mask": [True] * length + [False] * (50 - length),
                        "padded_target_action_sha256": "8" * 64,
                        "executed_mask_sha256": "9" * 64,
                    }
                    for start, length in zip(
                        CHUNK_START_FRAMES, EXECUTED_LENGTHS, strict=True
                    )
                ],
            },
            "x_runtime": {
                "source_result": {
                    "final_to_source_gate_baseline_objective_ratio": 0.01
                }
            },
        }
        run = build_run_summary(
            sources=sources,
            authority_identity="a" * 64,
            permit=permit,
            attempt=marker,
            tensor_artifact=artifact,
            trajectory_artifact=trajectory,
        )
        verify_run_summary(
            run,
            sources=sources,
            authority_identity="a" * 64,
            permit=permit,
            attempt=marker,
            tensor_artifact=artifact,
            trajectory_artifact=trajectory,
        )
        result = build_result(run=run)
        verify_result(result, run=run)
        self.assertFalse(result["amended_bridge_gate_passed"])
        self.assertFalse(result["gate_c_request_eligible"])
        self.assertFalse(result["unexecuted_tail_scored"])

        drift = copy.deepcopy(rows)
        drift[1]["decoded_action_chunk"][0][0] = 99.0
        with self.assertRaises(ValueError):
            build_tensor_artifact(attempt=marker, permit=permit, rows=drift)


if __name__ == "__main__":
    unittest.main()
