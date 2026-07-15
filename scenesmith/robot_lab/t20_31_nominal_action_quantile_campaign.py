"""Bounded official-LeRobot runner for the T20.31 quantile ablation."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    sign_payload,
)
from scenesmith.robot_lab.t20_17_clean_base_preflight import EXPECTED_MODEL_REVISION
from scenesmith.robot_lab.t20_24_recovery_augmented_campaign import (
    _file_tree,
    parse_finite_loss_trace,
)
from scenesmith.robot_lab.t20_30_nominal_action_quantile_preflight import (
    DATASET_REPO_ID,
    DATASET_ROOT,
    EXPECTED_UPDATES,
    REPO_ROOT,
    TRAINING_SEED,
    verify_preflight_lightweight,
)
from scenesmith.robot_lab.t20_30_simulation_training_authority import (
    require_active_authority,
)


HELD_OUT_SEEDS = (6, 7)
RUN_ROOT = Path("outputs/robot_lab/t20_31_nominal_action_quantile_run_001")
TRAINING_OUTPUT_DIR = Path("training")
INVOCATION_PATH = Path("invocation.json")
TRAIN_LOG_PATH = Path("train.log")
RUN_SUMMARY_PATH = Path("run_summary.json")
RESULT_GATE_PATH = Path(
    "configurations/robot_lab/t20_31_nominal_action_quantile_result_gate.json"
)


def build_training_argv(
    *, python: Path, dataset_root: Path, model_snapshot_root: Path, output_root: Path
) -> list[str]:
    return [
        str(python),
        "-m",
        "lerobot.scripts.lerobot_train",
        f"--dataset.repo_id={DATASET_REPO_ID}",
        f"--dataset.root={dataset_root}",
        "--dataset.image_transforms.enable=false",
        "--dataset.return_uint8=true",
        f"--policy.path={model_snapshot_root}",
        "--policy.device=mps",
        "--policy.use_amp=false",
        "--policy.push_to_hub=false",
        "--peft.r=4",
        "--peft.lora_alpha=4",
        "--batch_size=1",
        "--num_workers=0",
        "--persistent_workers=false",
        f"--steps={EXPECTED_UPDATES}",
        f"--seed={TRAINING_SEED}",
        "--env_eval_freq=0",
        "--eval_steps=0",
        "--log_freq=1",
        "--save_checkpoint=true",
        f"--save_freq={EXPECTED_UPDATES}",
        f"--output_dir={output_root}",
        "--job_name=t20_31_nominal_action_quantile_run_001",
        "--wandb.enable=false",
        "--job.target=local",
    ]


def verify_run_summary(summary: dict[str, Any]) -> None:
    expected = {
        "schema_version": "scenesmith.t20_31_nominal_action_quantile_run.v1",
        "optimizer_update_count": EXPECTED_UPDATES,
        "all_losses_finite": True,
        "held_out_evaluation_executed": False,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError("T20.31 run summary contract drifted")
    paths = {row.get("path") for row in summary.get("checkpoint_tree", [])}
    required = {
        "adapter_model.safetensors",
        "adapter_config.json",
        "policy_preprocessor.json",
        "policy_postprocessor.json",
    }
    if not required.issubset(paths):
        raise ValueError("T20.31 run summary lacks checkpoint evidence")


def run_campaign(*, repo_root: Path = REPO_ROOT, python: Path | None = None) -> dict:
    root = Path(repo_root)
    preflight = verify_preflight_lightweight(repo_root=root)
    authority = require_active_authority(repo_root=root)
    spec = preflight["training_spec"]
    if spec["campaign"]["optimizer_update_count"] != EXPECTED_UPDATES:
        raise ValueError("T20.31 optimizer bound drifted")
    run_root = root / RUN_ROOT
    if run_root.exists():
        raise FileExistsError(f"T20.31 run root already exists: {run_root}")
    revision = spec["campaign"]["model_revision"]
    if revision != EXPECTED_MODEL_REVISION:
        raise ValueError("T20.31 base revision drifted")
    model_root = (
        Path.home()
        / ".cache/huggingface/hub/models--lerobot--pi05_base/snapshots"
        / revision
    )
    run_root.mkdir(parents=True, exist_ok=False)
    argv = build_training_argv(
        python=python or Path(sys.executable),
        dataset_root=root / DATASET_ROOT,
        model_snapshot_root=model_root,
        output_root=run_root / TRAINING_OUTPUT_DIR,
    )
    invocation = sign_payload(
        {
            "schema_version": "scenesmith.t20_31_nominal_action_quantile_invocation.v1",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority["decision"][
                "identity_sha256"
            ],
            "argv": argv,
            "environment": {
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "WANDB_DISABLED": "true",
            },
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )
    dump_canonical_json(run_root / INVOCATION_PATH, invocation)
    environment = os.environ.copy()
    environment.update(invocation["environment"])
    with (run_root / TRAIN_LOG_PATH).open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            argv,
            cwd=root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end="", flush=True)
        return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"Official LeRobot training exited with {return_code}")
    trace = parse_finite_loss_trace(
        run_root / TRAIN_LOG_PATH, expected_updates=EXPECTED_UPDATES
    )
    checkpoint = run_root / "training/checkpoints/last/pretrained_model"
    if not checkpoint.is_dir():
        raise ValueError("T20.31 final checkpoint is missing")
    files = _file_tree(checkpoint)
    summary = sign_payload(
        {
            "schema_version": "scenesmith.t20_31_nominal_action_quantile_run.v1",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority["decision"][
                "identity_sha256"
            ],
            "invocation_identity_sha256": invocation["identity_sha256"],
            "optimizer_update_count": len(trace),
            "baseline_loss": trace[0]["loss"],
            "final_loss": trace[-1]["loss"],
            "minimum_loss": min(row["loss"] for row in trace),
            "all_losses_finite": True,
            "loss_trace": trace,
            "checkpoint_tree": files,
            "checkpoint_identity_sha256": hashlib.sha256(
                canonical_json_bytes(files)
            ).hexdigest(),
            "held_out_evaluation_executed": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )
    dump_canonical_json(run_root / RUN_SUMMARY_PATH, summary)
    verify_run_summary(summary)
    return summary
