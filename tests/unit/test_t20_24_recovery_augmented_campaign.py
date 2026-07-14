from __future__ import annotations

import copy
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.t20_24_recovery_augmented_campaign import (
    EXPECTED_UPDATES,
    build_result_gate,
    build_training_argv,
    parse_finite_loss_trace,
    verify_run_summary,
)


class T2024RecoveryAugmentedCampaignTests(unittest.TestCase):
    def test_training_argv_is_exact_bounded_local_mps_campaign(self) -> None:
        argv = build_training_argv(
            python=Path("/runtime/python"),
            dataset_root=Path("/repo/dataset"),
            model_snapshot_root=Path("/cache/pi05"),
            output_root=Path("/repo/run/training"),
        )
        joined = " ".join(argv)
        for required in (
            "lerobot.scripts.lerobot_train",
            "--dataset.repo_id=scenesmith/t20-23-anchor-grasp-recovery-train",
            "--dataset.root=/repo/dataset",
            "--policy.path=/cache/pi05",
            "--policy.device=mps",
            "--peft.r=4",
            "--batch_size=1",
            f"--steps={EXPECTED_UPDATES}",
            "--seed=20260714",
            "--env_eval_freq=0",
            "--policy.push_to_hub=false",
            "--wandb.enable=false",
            "--job.target=local",
            "--job_name=t20_24_recovery_augmented_run_002",
        ):
            self.assertIn(required, joined)
        for forbidden in ("cuda", "--resume=true", "push_to_hub=true"):
            self.assertNotIn(forbidden, joined.lower())

    def test_loss_trace_requires_every_finite_update(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "train.log"
            path.write_text("step:1 loss:2.0\nstep:2 loss:1.0\n", encoding="utf-8")
            self.assertEqual(
                [row["loss"] for row in parse_finite_loss_trace(path, expected_updates=2)],
                [2.0, 1.0],
            )
            path.write_text("step:1 loss:inf\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-finite"):
                parse_finite_loss_trace(path, expected_updates=1)

    def test_run_summary_rejects_update_or_authority_drift(self) -> None:
        summary = {
            "schema_version": "scenesmith.t20_24_recovery_augmented_run.v1",
            "optimizer_update_count": 500,
            "all_losses_finite": True,
            "held_out_evaluation_executed": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "checkpoint_tree": [
                {"path": "adapter_model.safetensors"},
                {"path": "adapter_config.json"},
                {"path": "policy_preprocessor.json"},
            ],
        }
        verify_run_summary(summary)
        for key, value in (("optimizer_update_count", 499), ("physical_actuation", True)):
            drift = copy.deepcopy(summary)
            drift[key] = value
            with self.assertRaises(ValueError):
                verify_run_summary(drift)

    def test_result_gate_records_two_seed_positive_without_policy_acceptance(self) -> None:
        gate = build_result_gate(
            training_ref={"identity_sha256": "a" * 64},
            evaluation_refs=[
                {"seed": seed, "identity_sha256": f"{seed:064x}"}
                for seed in (6, 7)
            ],
            training_summary={
                "optimizer_update_count": 500,
                "baseline_loss": 1.0,
                "final_loss": 0.1,
                "minimum_loss": 0.05,
            },
            evaluations=[self._rollout(6, True), self._rollout(7, True)],
        )
        self.assertEqual(gate["strict_success_count"], 2)
        self.assertEqual(gate["decision"], "candidate_passed_two_seed_strict_v2")
        self.assertTrue(gate["candidate_two_seed_strict_success"])
        self.assertFalse(gate["simulation_policy_accepted"])
        self.assertFalse(gate["promotion_eligible"])

    def test_result_gate_records_negative_and_rejects_seed_or_assist_drift(self) -> None:
        refs = [
            {"seed": seed, "identity_sha256": f"{seed:064x}"}
            for seed in (6, 7)
        ]
        summary = {
            "optimizer_update_count": 500,
            "baseline_loss": 1.0,
            "final_loss": 0.1,
            "minimum_loss": 0.05,
        }
        gate = build_result_gate(
            training_ref={"identity_sha256": "a" * 64},
            evaluation_refs=refs,
            training_summary=summary,
            evaluations=[self._rollout(6, True), self._rollout(7, False)],
        )
        self.assertEqual(gate["strict_success_count"], 1)
        self.assertEqual(gate["decision"], "candidate_failed_two_seed_strict_v2")
        wrong_seed = self._rollout(8, False)
        with self.assertRaisesRegex(ValueError, "seed coverage"):
            build_result_gate(
                training_ref={"identity_sha256": "a" * 64},
                evaluation_refs=refs,
                training_summary=summary,
                evaluations=[self._rollout(6, True), wrong_seed],
            )
        assisted = self._rollout(7, False)
        assisted["active_assist_frame_count"] = 1
        with self.assertRaisesRegex(ValueError, "assisted"):
            build_result_gate(
                training_ref={"identity_sha256": "a" * 64},
                evaluation_refs=refs,
                training_summary=summary,
                evaluations=[self._rollout(6, True), assisted],
            )

    @staticmethod
    def _rollout(seed: int, success: bool) -> dict:
        return {
            "seed": seed,
            "frame_count": 244,
            "simulation_semantic_strict_success": success,
            "terminal_outcome": "strict_success" if success else "no_strict_grasp_contact",
            "maximum_anchor_lift_m": 0.04 if success else 0.0,
            "projected_action_frame_count": 0,
            "active_assist_frame_count": 0,
        }


if __name__ == "__main__":
    unittest.main()
