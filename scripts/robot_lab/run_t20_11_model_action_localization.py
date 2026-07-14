#!/usr/bin/env python3
"""Run one T20.11 model and compare every requested action to the source oracle."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.act_grasp_closed_loop import (  # noqa: E402
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    run_policy_grasp_closed_loop,
)
from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.learned_action_localization import (  # noqa: E402
    SCHEMA_VERSION,
    analyze_model_actions,
    verify_model_action_localization,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.model_bakeoff import (  # noqa: E402
    MODEL_ORDER,
    verify_model_training_result,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (  # noqa: E402
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.simulation_training_authority import (  # noqa: E402
    require_active_simulation_training_authority,
)
from scripts.robot_lab.compose_t20_7_model_training_gate import (  # noqa: E402
    _verify_checkpoint_files,
)
from scripts.robot_lab.run_t20_7_model_closed_loop import (  # noqa: E402
    INFERENCE_SEED,
    _load_policy_action,
    _primary_checkpoint_sha256,
    _replan_count,
)
from scripts.robot_lab.run_t20_7_model_training import _set_offline_runtime  # noqa: E402


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
SOURCE_MANIFEST_PATH = REPO_ROOT / "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
T20_10_PATH = REPO_ROOT / "outputs/robot_lab/t20_10_release_reconciliation_run_001.json"
TRAINING_ROOT = REPO_ROOT / "outputs/robot_lab/t20_7_four_model_training_run_001"
ROLLOUT_SCHEMA_VERSION = "scenesmith.t20_11_corrected_model_closed_loop.v1"
EVIDENCE_MODE = "held_out_seed_model_action_localization_force_bearing_release"
SEED = 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODEL_ORDER)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    if output.exists():
        raise ValueError("T20.11 model localization output exists")
    training_run = TRAINING_ROOT / args.model
    plan = load_strict_json(PLAN_PATH)
    summary_path = training_run / "run_summary.json"
    summary = load_strict_json(summary_path)
    verify_model_training_result(summary, plan)
    _verify_checkpoint_files(training_run, summary["checkpoint_files"])

    manifest = load_strict_json(SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    entry = next(item for item in manifest["episodes"] if item["seed"] == SEED)
    source_episode_path = default_store_root() / entry["relative_path"]
    source_episode = load_strict_json(source_episode_path)
    t20_10 = load_strict_json(T20_10_PATH)
    source_anchor_start = t20_10["corrected_oracle_rollout"]["anchor_start_position_m"]

    _set_offline_runtime()
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    import torch

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.11 model localization requires local MPS")
    torch.manual_seed(INFERENCE_SEED)
    policy, policy_action, inference_steps = _load_policy_action(
        args.model, training_run, plan, torch
    )
    policy.reset()
    observed_frames: list[dict] = []
    rollout = run_policy_grasp_closed_loop(
        policy_action,
        checkpoint_sha256=_primary_checkpoint_sha256(summary),
        training_run_summary_sha256=_sha(summary_path),
        seed=SEED,
        schema_version=ROLLOUT_SCHEMA_VERSION,
        task_id="T20.11",
        evidence_mode=EVIDENCE_MODE,
        policy_label=args.model,
        frame_observer=observed_frames.append,
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    )
    diagnostics = analyze_model_actions(
        source_episode["frames"],
        observed_frames,
        source_anchor_start_position_m=source_anchor_start,
    )
    payload = sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.11",
            "model_id": args.model,
            "source_plan_identity_sha256": plan["identity_sha256"],
            "source_training_result_identity_sha256": summary["identity_sha256"],
            "source_training_result_file_sha256": _sha(summary_path),
            "source_episode_file_sha256": entry["episode_file_sha256"],
            "source_t20_10_identity_sha256": t20_10["identity_sha256"],
            "action_error_diagnostics": diagnostics,
            "corrected_closed_loop": rollout,
            "policy_runtime": {
                "python": sys.version.split()[0],
                "torch": torch.__version__,
                "device": "mps",
                "dtype": "float32",
                "offline": True,
                "inference_seed": INFERENCE_SEED,
                "action_horizon": 5,
                "queue_refill_count": _replan_count(rollout["frame_count"]),
                "denoising_steps_where_applicable": inference_steps,
                "lerobot_stack_identity_sha256": stack["identity_sha256"],
            },
            "model_inference_executed": True,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    verify_model_action_localization(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print(
        args.model,
        payload["identity_sha256"],
        diagnostics["dominant_initial_error_joint"],
        diagnostics["initial_action_maximum_absolute_error_rad"],
    )
    return 0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
