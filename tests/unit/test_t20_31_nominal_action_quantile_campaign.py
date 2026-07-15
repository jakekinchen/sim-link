from __future__ import annotations

import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.t20_30_nominal_action_quantile_preflight import (
    EXPECTED_UPDATES,
)
from scenesmith.robot_lab.t20_31_nominal_action_quantile_campaign import (
    build_result_gate,
    build_training_argv,
    verify_run_summary,
)


class T2031NominalActionQuantileCampaignTests(unittest.TestCase):
    def test_argv_is_exact_same_seed_local_mps_campaign(self) -> None:
        argv = build_training_argv(
            python=Path("/runtime/python"),
            dataset_root=Path("/repo/dataset"),
            model_snapshot_root=Path("/cache/pi05"),
            output_root=Path("/repo/run/training"),
        )
        joined = " ".join(argv)
        for value in (
            "--dataset.repo_id=scenesmith/t20-30-recovery-clean-action-quantiles",
            "--dataset.root=/repo/dataset",
            "--policy.device=mps",
            "--peft.r=4",
            "--batch_size=1",
            f"--steps={EXPECTED_UPDATES}",
            "--seed=20260714",
            "--job.target=local",
        ):
            self.assertIn(value, joined)
        self.assertNotIn("cuda", joined.lower())

    def test_summary_rejects_update_or_authority_drift(self) -> None:
        summary = {
            "schema_version": "scenesmith.t20_31_nominal_action_quantile_run.v1",
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
                {"path": "policy_postprocessor.json"},
            ],
        }
        verify_run_summary(summary)
        for key, value in (
            ("optimizer_update_count", 499),
            ("physical_actuation", True),
        ):
            drift = copy.deepcopy(summary)
            drift[key] = value
            with self.assertRaises(ValueError):
                verify_run_summary(drift)

    def test_result_gate_records_negative_without_acceptance(self) -> None:
        summary = self._summary()
        gate = build_result_gate(
            training_ref={"identity_sha256": "a" * 64},
            evaluation_refs=[
                {"seed": seed, "identity_sha256": f"{seed:064x}"}
                for seed in (6, 7)
            ],
            training_summary=summary,
            evaluations=[self._rollout(6, False), self._rollout(7, False)],
            checkpoint_action_quantiles_match_t20_30=True,
        )
        self.assertEqual(gate["strict_success_count"], 0)
        self.assertFalse(gate["simulation_policy_accepted"])
        with self.assertRaisesRegex(ValueError, "quantiles"):
            build_result_gate(
                training_ref={"identity_sha256": "a" * 64},
                evaluation_refs=[
                    {"seed": seed, "identity_sha256": f"{seed:064x}"}
                    for seed in (6, 7)
                ],
                training_summary=summary,
                evaluations=[self._rollout(6, False), self._rollout(7, False)],
                checkpoint_action_quantiles_match_t20_30=False,
            )

    @staticmethod
    def _summary() -> dict:
        return {
            "schema_version": "scenesmith.t20_31_nominal_action_quantile_run.v1",
            "optimizer_update_count": 500,
            "baseline_loss": 1.0,
            "final_loss": 0.4,
            "minimum_loss": 0.02,
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
                {"path": "policy_postprocessor.json"},
            ],
        }

    @staticmethod
    def _rollout(seed: int, success: bool) -> dict:
        return {
            "seed": seed,
            "frame_count": 244,
            "simulation_semantic_strict_success": success,
            "terminal_outcome": "strict_success" if success else "no_contact",
            "maximum_anchor_lift_m": 0.04 if success else 0.0,
            "projected_action_frame_count": 0,
            "active_assist_frame_count": 0,
        }


if __name__ == "__main__":
    unittest.main()
