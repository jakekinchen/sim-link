import unittest

from copy import deepcopy

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36m_tensor_reproduction import (
    EXPECTED_ACTION_HASHES,
    INFERENCE_SEEDS,
    build_attempt_marker,
    build_inference_permit,
    build_runtime_preflight,
    score_action_tensor,
)


class T2036mTensorReproductionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sources = {
            "checkpoint_identity_sha256": "a" * 64,
            "source_run_identity_sha256": "b" * 64,
            "source_result_identity_sha256": "c" * 64,
            "frozen_gate_identity_sha256": "d" * 64,
            "frozen_score_identity_sha256": "e" * 64,
            "checkpoint_tree": [{"path": "model.safetensors", "sha256": "f" * 64, "size_bytes": 1}],
            "installed_closure_identity_sha256": "1" * 64,
            "processor_smoke_identity_sha256": "2" * 64,
            "lerobot_stack_identity_sha256": "3" * 64,
            "batch_evidence_identity_sha256": "4" * 64,
        }

    def test_preflight_and_permit_are_inference_only_and_marker_first(self) -> None:
        preflight = build_runtime_preflight(
            sources=self.sources,
            authority_identity="5" * 64,
            python_major_minor=[3, 12],
            mps_available=True,
            checkpoint_tree=self.sources["checkpoint_tree"],
            free_disk_bytes=10_000_000_000,
            source_commit="6" * 40,
            remote_source_commit="6" * 40,
            attempt_exists=False,
            result_exists=False,
        )
        permit = build_inference_permit(
            sources=self.sources,
            authority_identity="5" * 64,
            runtime_preflight=preflight,
        )
        self.assertEqual(permit["inference_seeds"], list(INFERENCE_SEEDS))
        self.assertEqual(permit["expected_action_chunk_sha256s"], list(EXPECTED_ACTION_HASHES))
        self.assertTrue(permit["marker_must_precede_checkpoint_tensor_read"])
        self.assertFalse(permit["optimizer_created"])
        marker = build_attempt_marker(
            permit=permit,
            authority_identity="5" * 64,
            source_commit="6" * 40,
        )
        self.assertTrue(marker["created_before_checkpoint_tensor_read"])
        self.assertFalse(marker["model_loaded"])

    def test_preflight_fails_closed_on_remote_or_existing_output(self) -> None:
        kwargs = dict(
            sources=self.sources,
            authority_identity="5" * 64,
            python_major_minor=[3, 12],
            mps_available=True,
            checkpoint_tree=self.sources["checkpoint_tree"],
            free_disk_bytes=10_000_000_000,
            source_commit="6" * 40,
            remote_source_commit="7" * 40,
            attempt_exists=False,
            result_exists=False,
        )
        with self.assertRaisesRegex(ValueError, "preflight"):
            build_runtime_preflight(**kwargs)
        kwargs["remote_source_commit"] = kwargs["source_commit"]
        kwargs["result_exists"] = True
        with self.assertRaisesRegex(ValueError, "preflight"):
            build_runtime_preflight(**kwargs)

    def test_tensor_score_uses_frozen_phase_joint_conjunction(self) -> None:
        thresholds = {
            "reach": {name: 0.1 for name in ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")},
            "grasp": {name: 0.05 for name in ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")},
        }
        target = [[0.0] * 6 for _ in range(50)]
        tensor = deepcopy(target)
        tensor[31][4] = 0.1
        passing = score_action_tensor(tensor=tensor, target=target, thresholds=thresholds)
        self.assertTrue(passing["passed"])
        tensor[32][5] = 0.051
        failed = score_action_tensor(tensor=tensor, target=target, thresholds=thresholds)
        self.assertFalse(failed["passed"])
        witness = failed["violations"][0]
        self.assertEqual((witness["phase_group"], witness["joint_name"]), ("grasp", "gripper"))

    def test_permit_rejects_authority_escalation(self) -> None:
        preflight = build_runtime_preflight(
            sources=self.sources,
            authority_identity="5" * 64,
            python_major_minor=[3, 12],
            mps_available=True,
            checkpoint_tree=self.sources["checkpoint_tree"],
            free_disk_bytes=10_000_000_000,
            source_commit="6" * 40,
            remote_source_commit="6" * 40,
            attempt_exists=False,
            result_exists=False,
        )
        permit = build_inference_permit(
            sources=self.sources,
            authority_identity="5" * 64,
            runtime_preflight=preflight,
        )
        mutation = sign_payload({**permit, "optimizer_created": True})
        self.assertNotEqual(mutation, permit)


if __name__ == "__main__":
    unittest.main()
