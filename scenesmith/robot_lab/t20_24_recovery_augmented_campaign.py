"""Bounded official-LeRobot runner for the T20.24 recovery campaign."""

from __future__ import annotations

import hashlib
import math
import os
import re
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
from scenesmith.robot_lab.t20_23_recovery_augmented_preflight import (
    DATASET_REPO_ID,
    DATASET_ROOT,
    REPO_ROOT,
    verify_training_spec_file,
)
from scenesmith.robot_lab.t20_23_simulation_training_authority import (
    require_active_t20_23_authority,
)


EXPECTED_UPDATES = 500
HELD_OUT_SEEDS = (6, 7)
RUN_ROOT = Path("outputs/robot_lab/t20_24_recovery_augmented_run_001")
TRAINING_OUTPUT_DIR = Path("training")
INVOCATION_PATH = Path("invocation.json")
TRAIN_LOG_PATH = Path("train.log")
RUN_SUMMARY_PATH = Path("run_summary.json")
RESULT_GATE_PATH = Path(
    "configurations/robot_lab/t20_24_recovery_augmented_result_gate.json"
)
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
        "--job_name=t20_24_recovery_augmented_run_001",
        "--wandb.enable=false",
        "--job.target=local",
    ]


def parse_finite_loss_trace(
    path: Path, *, expected_updates: int = EXPECTED_UPDATES
) -> list[dict[str, Any]]:
    by_step: dict[int, float] = {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        step_match = _STEP.search(line)
        loss_match = _LOSS.search(line)
        if not step_match or not loss_match:
            continue
        step = int(step_match.group(1).replace(",", ""))
        loss = float(loss_match.group(1))
        if not math.isfinite(loss):
            raise ValueError(f"T20.24 training loss is non-finite at step {step}")
        by_step[step] = loss
    expected = list(range(1, expected_updates + 1))
    if sorted(by_step) != expected:
        raise ValueError("T20.24 training log does not contain every bounded update")
    return [{"step": step, "loss": by_step[step]} for step in expected]


def verify_run_summary(summary: dict[str, Any]) -> None:
    expected = {
        "schema_version": "scenesmith.t20_24_recovery_augmented_run.v1",
        "optimizer_update_count": EXPECTED_UPDATES,
        "all_losses_finite": True,
        "held_out_evaluation_executed": False,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError("T20.24 run summary contract drifted")
    paths = {
        row.get("path")
        for row in summary.get("checkpoint_tree", [])
        if isinstance(row, dict)
    }
    required = {
        "adapter_model.safetensors",
        "adapter_config.json",
        "policy_preprocessor.json",
    }
    if not required.issubset(paths):
        raise ValueError("T20.24 run summary lacks required checkpoint evidence")


def build_result_gate(
    *,
    training_ref: dict[str, Any],
    evaluation_refs: list[dict[str, Any]],
    training_summary: dict[str, Any],
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    if training_summary.get("optimizer_update_count") != EXPECTED_UPDATES:
        raise ValueError("T20.24 result optimizer accounting drifted")
    if not isinstance(evaluations, list) or [row.get("seed") for row in evaluations] != list(HELD_OUT_SEEDS):
        raise ValueError("T20.24 held-out seed coverage drifted")
    if not isinstance(evaluation_refs, list) or [row.get("seed") for row in evaluation_refs] != list(HELD_OUT_SEEDS):
        raise ValueError("T20.24 evaluation reference seed coverage drifted")
    rows = []
    strict_count = 0
    for seed, rollout, ref in zip(HELD_OUT_SEEDS, evaluations, evaluation_refs, strict=True):
        if rollout.get("frame_count") != 244:
            raise ValueError("T20.24 held-out rollout frame count drifted")
        if any(
            rollout.get(key) != 0
            for key in ("projected_action_frame_count", "active_assist_frame_count")
        ):
            raise ValueError("T20.24 result contains projected or assisted actions")
        success = rollout.get("simulation_semantic_strict_success")
        if not isinstance(success, bool):
            raise ValueError("T20.24 strict-success result is invalid")
        strict_count += int(success)
        rows.append(
            {
                "seed": seed,
                "evaluation_ref": {key: value for key, value in ref.items() if key != "seed"},
                "frame_count": 244,
                "terminal_outcome": rollout.get("terminal_outcome"),
                "simulation_semantic_strict_success": success,
                "maximum_anchor_lift_m": rollout.get("maximum_anchor_lift_m"),
                "projected_action_frame_count": 0,
                "active_assist_frame_count": 0,
            }
        )
    passed = strict_count == len(HELD_OUT_SEEDS)
    return sign_payload(
        {
            "schema_version": "scenesmith.t20_24_recovery_augmented_result_gate.v1",
            "training_ref": dict(training_ref),
            "optimizer_update_count": EXPECTED_UPDATES,
            "baseline_loss": training_summary["baseline_loss"],
            "final_loss": training_summary["final_loss"],
            "minimum_loss": training_summary["minimum_loss"],
            "held_out_results": rows,
            "held_out_seed_count": len(HELD_OUT_SEEDS),
            "strict_success_count": strict_count,
            "candidate_two_seed_strict_success": passed,
            "decision": (
                "candidate_passed_two_seed_strict_v2"
                if passed
                else "candidate_failed_two_seed_strict_v2"
            ),
            "simulation_policy_accepted": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "authority_granted": [
                "t20_24_two_seed_candidate_result_verified"
            ],
            "authority_not_granted": [
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
        }
    )


def run_campaign(*, repo_root: Path = REPO_ROOT, python: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root)
    spec = verify_training_spec_file(repo_root=root)
    authority = require_active_t20_23_authority(repo_root=root)
    if spec.get("campaign", {}).get("optimizer_update_count") != EXPECTED_UPDATES:
        raise ValueError("T20.24 campaign update bound drifted from T20.23")
    run_root = root / RUN_ROOT
    if run_root.exists():
        raise FileExistsError(f"T20.24 run root already exists: {run_root}")
    revision = spec["model_snapshot"]["revision"]
    if revision != EXPECTED_MODEL_REVISION:
        raise ValueError("T20.24 campaign base revision drifted")
    model_root = (
        Path.home()
        / ".cache/huggingface/hub/models--lerobot--pi05_base/snapshots"
        / revision
    )
    dataset_root = root / DATASET_ROOT
    run_root.mkdir(parents=True, exist_ok=False)
    argv = build_training_argv(
        python=python or Path(sys.executable),
        dataset_root=dataset_root,
        model_snapshot_root=model_root,
        output_root=run_root / TRAINING_OUTPUT_DIR,
    )
    invocation = sign_payload(
        {
            "schema_version": "scenesmith.t20_24_recovery_augmented_invocation.v1",
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
        }
    )
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
    checkpoint_root = (
        run_root / TRAINING_OUTPUT_DIR / "checkpoints/last/pretrained_model"
    )
    if not checkpoint_root.is_dir():
        raise ValueError("T20.24 final LeRobot checkpoint is missing")
    files = _file_tree(checkpoint_root)
    summary = sign_payload(
        {
            "schema_version": "scenesmith.t20_24_recovery_augmented_run.v1",
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
            "checkpoint_identity_sha256": hashlib.sha256(
                canonical_json_bytes(files)
            ).hexdigest(),
            "held_out_evaluation_executed": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "authority_not_granted": [
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
        }
    )
    dump_canonical_json(run_root / RUN_SUMMARY_PATH, summary)
    return summary


def _file_tree(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": digest.hexdigest(),
            }
        )
    if not rows:
        raise ValueError("T20.24 checkpoint tree is empty")
    return rows
