from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.f0c_release_targeted_package import (
    ACTIVATION_COMMIT,
    CHECKPOINT_IDENTITY,
    PHYSICAL_L1_COEFFICIENTS,
    build_package,
    verify_package,
)


class F0cReleaseTargetedPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = build_package()

    def test_package_is_signed_and_reconstructs(self) -> None:
        verify_package(self.package)
        self.assertEqual(self.package["activation_commit"], ACTIVATION_COMMIT)
        self.assertEqual(self.package["status"], "packaged_for_fork_day_one")

    def test_budget_fails_closed_before_cutoff(self) -> None:
        budget = self.package["completion_budget"]
        self.assertFalse(budget["execute_before_cutoff"])
        self.assertEqual(budget["available_seconds"], 5048)
        self.assertEqual(budget["minimum_complete_boundary_seconds"], 6386.4)
        self.assertEqual(budget["shortfall_seconds"], 1338.4)

    def test_immutable_checkpoint_and_r0_are_exact(self) -> None:
        checkpoint = self.package["immutable_checkpoint"]
        self.assertEqual(checkpoint["identity_sha256"], CHECKPOINT_IDENTITY)
        self.assertFalse(checkpoint["overwrite_allowed"])
        dataset = self.package["dataset"]
        self.assertEqual(dataset["episode_count"], 129)
        self.assertEqual(dataset["frame_count"], 31366)
        self.assertEqual(dataset["window_count"], 59904)
        self.assertFalse(dataset["mutation_allowed"])

    def test_release_correction_is_single_factorized_contract(self) -> None:
        correction = self.package["release_correction"]
        self.assertEqual(
            correction["phase_start_importance_weights"],
            {"release": 4.0, "release_settle": 4.0, "all_other_eligible_phases": 1.0},
        )
        self.assertEqual(
            correction["normalized_l1_joint_coefficients"],
            PHYSICAL_L1_COEFFICIENTS,
        )
        self.assertTrue(correction["action_valid_mask_applied_before_reduction"])
        self.assertFalse(correction["new_episode_generation"])

    def test_evaluation_is_chunk_50_only_and_retry_closed(self) -> None:
        evaluation = self.package["evaluation"]
        self.assertEqual(evaluation["variant"], "chunk_50")
        self.assertFalse(evaluation["receding_10_in_scope"])
        self.assertEqual(evaluation["continuation_update_schedule"], [0, 500, 1000, 2000])
        self.assertEqual(evaluation["executed_lengths"], [50, 50, 50, 50, 44])
        self.assertFalse(self.package["retry_authorized"])

    def test_package_grants_no_execution_or_authority(self) -> None:
        for field in (
            "attempt_marker_created",
            "checkpoint_tensor_read",
            "model_constructed",
            "optimizer_created",
            "optimizer_training",
            "rollout_executed",
            "gate_c_executed",
            "network_accessed",
            "external_compute_started",
            "brev_compute_started",
            "hardware_accessed",
        ):
            with self.subTest(field=field):
                self.assertFalse(self.package[field])
        self.assertFalse(self.package["day_one"]["execution_entrypoint_implemented"])

    def test_any_budget_correction_or_authority_drift_fails(self) -> None:
        mutations = []
        budget = copy.deepcopy(self.package)
        budget["completion_budget"]["execute_before_cutoff"] = True
        mutations.append(budget)
        correction = copy.deepcopy(self.package)
        correction["release_correction"]["phase_start_importance_weights"]["release"] = 5.0
        mutations.append(correction)
        authority = copy.deepcopy(self.package)
        authority["optimizer_training"] = True
        mutations.append(authority)
        checkpoint = copy.deepcopy(self.package)
        checkpoint["immutable_checkpoint"]["identity_sha256"] = "0" * 64
        mutations.append(checkpoint)
        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    verify_package(payload)


if __name__ == "__main__":
    unittest.main()
