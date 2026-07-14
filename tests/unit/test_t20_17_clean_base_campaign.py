from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scenesmith.robot_lab.t20_17_clean_base_campaign import (
    EXPECTED_UPDATES,
    build_training_argv,
    parse_finite_loss_trace,
)


class T2017CleanBaseCampaignTests(unittest.TestCase):
    def test_training_argv_is_exact_local_offline_package_campaign(self) -> None:
        argv = build_training_argv(
            python=Path("/runtime/python"),
            dataset_root=Path("/repo/dataset"),
            model_snapshot_root=Path("/cache/pi05"),
            output_root=Path("/repo/run/training"),
        )
        joined = " ".join(str(item) for item in argv)
        for required in (
            "lerobot.scripts.lerobot_train",
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
            "--output_dir=/repo/run/training",
        ):
            self.assertIn(required, joined)
        for forbidden in ("cuda", "hf jobs", "--resume=true"):
            self.assertNotIn(forbidden, joined.lower())

    def test_loss_trace_requires_all_finite_updates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.log"
            path.write_text(
                "INFO 2026 train.py: step:1 smpl:1 ep:0 epch:0.00 loss:3.5 grdn:1.2 lr:1e-5 updt_s:1 data_s:1\n"
                "INFO 2026 train.py: step:2 smpl:2 ep:0 epch:0.00 loss:2.5 grdn:1.1 lr:1e-5 updt_s:1 data_s:1\n",
                encoding="utf-8",
            )
            trace = parse_finite_loss_trace(path, expected_updates=2)
            self.assertEqual([row["step"] for row in trace], [1, 2])
            self.assertEqual(trace[-1]["loss"], 2.5)
            path.write_text("step:1 loss:nan\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                parse_finite_loss_trace(path, expected_updates=1)


if __name__ == "__main__":
    unittest.main()
