from __future__ import annotations

import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.t20_30_nominal_action_quantile_preflight import (
    EXPECTED_UPDATES,
)
from scenesmith.robot_lab.t20_31_nominal_action_quantile_campaign import (
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


if __name__ == "__main__":
    unittest.main()
