"""Bounded official-LeRobot runner for the T20.17 clean-base campaign."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, dump_canonical_json, sign_payload
from scenesmith.robot_lab.t20_17_clean_base_preflight import (
    DATASET_REPO_ID,
    DATASET_ROOT,
    EXPECTED_MODEL_REVISION,
    REPO_ROOT,
    verify_training_spec_file,
)
from scenesmith.robot_lab.t20_17_simulation_training_authority import require_active_t20_17_authority


EXPECTED_UPDATES = 250
RUN_ROOT = Path("outputs/robot_lab/t20_17_clean_base_run_001")
INVOCATION_PATH = Path("invocation.json")
TRAIN_LOG_PATH = Path("train.log")
RUN_SUMMARY_PATH = Path("run_summary.json")
_STEP = re.compile(r"(?:^|\s)step:(\d+)(?:\s|$)")
_LOSS = re.compile(r"(?:^|\s)loss:([^\s]+)(?:\s|$)")


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
        "--seed=20260714",
        "--env_eval_freq=0",
        "--eval_steps=0",
        "--log_freq=1",
        "--save_checkpoint=true",
        f"--save_freq={EXPECTED_UPDATES}",
        f"--output_dir={output_root}",
        "--job_name=t20_17_clean_base_run_001",
        "--wandb.enable=false",
        "--job.target=local",
    ]


def parse_finite_loss_trace(path: Path, *, expected_updates: int = EXPECTED_UPDATES) -> list[dict[str, Any]]:
    by_step: dict[int, float] = {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        step_match = _STEP.search(line)
        loss_match = _LOSS.search(line)
        if not step_match or not loss_match:
            continue
        step = int(step_match.group(1).replace(",", ""))
        loss = float(loss_match.group(1))
        if not math.isfinite(loss):
            raise ValueError(f"T20.17 training loss is non-finite at step {step}")
        by_step[step] = loss
    expected = list(range(1, expected_updates + 1))
    if sorted(by_step) != expected:
        raise ValueError("T20.17 training log does not contain every bounded optimizer update")
    return [{"step": step, "loss": by_step[step]} for step in expected]


def run_campaign(*, repo_root: Path = REPO_ROOT, python: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root)
    spec = verify_training_spec_file(repo_root=root)
    authority = require_active_t20_17_authority(repo_root=root)
    run_root = root / RUN_ROOT
    if run_root.exists():
        raise FileExistsError(f"T20.17 run root already exists: {run_root}")
    revision = spec["model_snapshot"]["revision"]
    if revision != EXPECTED_MODEL_REVISION:
        raise ValueError("T20.17 campaign base revision drifted")
    model_root = Path.home() / ".cache/huggingface/hub/models--lerobot--pi05_base/snapshots" / revision
    dataset_root = root / DATASET_ROOT
    run_root.mkdir(parents=True, exist_ok=False)
    argv = build_training_argv(
        python=python or Path(sys.executable),
        dataset_root=dataset_root,
        model_snapshot_root=model_root,
        output_root=run_root,
    )
    invocation = sign_payload({
        "schema_version": "scenesmith.t20_17_clean_base_invocation.v1",
        "training_spec_identity_sha256": spec["identity_sha256"],
        "authority_decision_identity_sha256": authority["decision"]["identity_sha256"],
        "argv": argv,
        "environment": {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "WANDB_DISABLED": "true",
        },
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    })
    dump_canonical_json(run_root / INVOCATION_PATH, invocation)
    env = os.environ.copy()
    env.update(invocation["environment"])
    with (run_root / TRAIN_LOG_PATH).open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            argv,
            cwd=root,
            env=env,
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
        raise RuntimeError(f"Official LeRobot training exited with status {return_code}")
    trace = parse_finite_loss_trace(run_root / TRAIN_LOG_PATH)
    checkpoint_root = run_root / "checkpoints" / "last" / "pretrained_model"
    if not checkpoint_root.is_dir():
        raise ValueError("T20.17 final LeRobot checkpoint is missing")
    files = _file_tree(checkpoint_root)
    summary = sign_payload({
        "schema_version": "scenesmith.t20_17_clean_base_run.v1",
        "training_spec_identity_sha256": spec["identity_sha256"],
        "authority_decision_identity_sha256": authority["decision"]["identity_sha256"],
        "invocation_identity_sha256": invocation["identity_sha256"],
        "optimizer_update_count": len(trace),
        "baseline_loss": trace[0]["loss"],
        "final_loss": trace[-1]["loss"],
        "minimum_loss": min(row["loss"] for row in trace),
        "all_losses_finite": True,
        "loss_trace": trace,
        "checkpoint_tree": files,
        "checkpoint_identity_sha256": hashlib.sha256(canonical_json_bytes(files)).hexdigest(),
        "held_out_evaluation_executed": False,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "authority_not_granted": [
            "simulation_policy_accepted", "physical_transfer_ready", "promotion_eligible",
            "physical_actuation", "external_compute", "brev_compute",
        ],
    })
    dump_canonical_json(run_root / RUN_SUMMARY_PATH, summary)
    return summary


def _file_tree(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        rows.append({"path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size, "sha256": digest.hexdigest()})
    if not rows:
        raise ValueError("T20.17 checkpoint tree is empty")
    return rows
