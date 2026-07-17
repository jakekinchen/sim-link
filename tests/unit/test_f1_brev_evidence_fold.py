from __future__ import annotations

import unittest
from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    verify_signed_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FOLD_PATH = REPO_ROOT / "configurations/robot_lab/f1_brev_evidence_fold.json"


class F1BrevEvidenceFoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fold = load_strict_json(FOLD_PATH)

    def test_fold_is_signed_and_source_bound(self) -> None:
        verify_signed_payload(self.fold, label="F1 Brev evidence fold")
        self.assertEqual(
            self.fold["receipts"]["run"]["identity_sha256"],
            "ca9a23b183c9854266d3960b66bc60f0d7cf4aea8d0dc40ad96293e9201d8716",
        )
        self.assertEqual(
            self.fold["receipts"]["teardown"]["identity_sha256"],
            "7343ad9fc1bc1802ec00bd13eab65807ca2d41818c8d59210957b980b2b66064",
        )

    def test_single_training_run_and_ten_rollouts_are_exact(self) -> None:
        training = self.fold["training"]
        evaluation = self.fold["evaluation"]
        self.assertTrue(training["full_finetune"])
        self.assertEqual(training["run_count"], 1)
        self.assertFalse(training["automatic_retry"])
        self.assertEqual(training["optimizer_update_count"], 5000)
        self.assertEqual(evaluation["rollout_count"], 10)
        self.assertEqual(evaluation["strict_success_count"], 0)
        self.assertEqual(len(self.fold["rollout_receipts"]), 10)
        self.assertEqual(
            len({row["identity_sha256"] for row in self.fold["rollout_receipts"]}),
            10,
        )

    def test_selected_partial_is_negative_not_gate_c(self) -> None:
        selected = self.fold["evaluation"]["selected"]
        self.assertEqual(selected["checkpoint_step"], 1000)
        self.assertEqual(selected["variant"], "chunk_50")
        self.assertEqual(selected["maximum_anchor_lift_m"], 0.03751930418757199)
        self.assertEqual(selected["failed_gates"], ["grasp_hold_strict_v2"])
        self.assertFalse(self.fold["evaluation"]["gate_c_passed"])
        self.assertFalse(self.fold["evaluation"]["gateway_result"])

    def test_retained_checkpoint_remains_off_repo(self) -> None:
        checkpoint = self.fold["retained_checkpoint"]
        self.assertFalse(checkpoint["included_in_repository"])
        self.assertTrue(checkpoint["verified_without_tensor_deserialization"])
        self.assertEqual(
            checkpoint["model_sha256"],
            "755544956570297f09f72c48874f5dc9643e02f14a0c934109b81a9e66aec7fb",
        )
        self.assertEqual(
            checkpoint["config_sha256"],
            "1f17178a8bf1a7d62f9ef89673b79eb4ef839158485e5c09dda2ad9c4eb125d9",
        )

    def test_cost_and_teardown_are_closed(self) -> None:
        self.assertEqual(self.fold["cost"]["actual_spend_usd"], 5.526)
        self.assertEqual(self.fold["teardown"]["remaining_resource_count"], 0)
        inventory = self.fold["canonical_closeout_inventory"]
        self.assertTrue(inventory["authenticated"])
        self.assertIsNone(inventory["workspaces"])
        self.assertEqual(inventory["remaining_resource_count"], 0)
        self.assertFalse(inventory["mutation_performed"])

    def test_fold_grants_no_new_authority(self) -> None:
        proof = self.fold["proof_boundary"]
        self.assertTrue(proof["policy_training_evidence_only"])
        for key, value in proof.items():
            if key != "policy_training_evidence_only":
                with self.subTest(key=key):
                    self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
