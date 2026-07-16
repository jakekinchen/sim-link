import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36o_baseline_capture import (
    BASELINE_PERMIT_PATH,
    CHUNK_START_FRAMES,
    EXECUTED_LENGTHS,
    INFERENCE_SEEDS,
    build_attempt_marker,
    build_baseline_permit,
    build_runtime_preflight,
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


if __name__ == "__main__":
    unittest.main()
