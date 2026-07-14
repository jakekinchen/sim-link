#!/usr/bin/env python3
"""Evaluate the T20.14 checkpoint in the corrected fixed seed-2 loop."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.act_grasp_closed_loop import (
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    run_policy_grasp_closed_loop,
)
from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes
from scenesmith.robot_lab.learned_action_localization import analyze_model_actions
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.simulation_training_authority import (
    require_active_simulation_training_authority,
)
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot
from scripts.robot_lab.run_t20_7_model_closed_loop import INFERENCE_SEED, _replan_count
from scripts.robot_lab.run_t20_7_model_training import (
    TASK,
    _model_contract,
    _set_offline_runtime,
    _snapshot,
    _verify_model_sources,
)


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
NORMALIZER_PATH = REPO_ROOT / "outputs/robot_lab/t20_13_dataset_bound_pi05_normalizer.json"
SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
)
T20_10_PATH = REPO_ROOT / "outputs/robot_lab/t20_10_release_reconciliation_run_001.json"
SCHEMA_VERSION = "scenesmith.t20_14_dataset_normalized_pi05_closed_loop.v1"
SEED = 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    training_run = _resolve(args.training_run)
    output = _resolve(args.output)
    if output.exists():
        raise ValueError("T20.14 closed-loop output already exists")
    summary_path = training_run / "run_summary.json"
    summary = load_strict_json(summary_path)
    verify_signed_payload(summary, label="T20.14 training result")
    _verify_summary(summary)
    checkpoint = training_run / "checkpoint/adapter_model.safetensors"
    expected_checkpoint = summary["checkpoint_files"][
        "checkpoint/adapter_model.safetensors"
    ]["sha256"]
    if _sha(checkpoint) != expected_checkpoint:
        raise ValueError("T20.14 checkpoint hash drifted")
    plan = load_strict_json(PLAN_PATH)
    verify_signed_payload(plan, label="T20.14 source T20.7 plan")
    normalizer = load_strict_json(NORMALIZER_PATH)
    verify_signed_payload(normalizer, label="T20.14 source T20.13 normalizer")
    if normalizer["identity_sha256"] != summary["source_normalizer_identity_sha256"]:
        raise ValueError("T20.14 training/inference normalizer identity differs")

    manifest = load_strict_json(SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    entry = next(item for item in manifest["episodes"] if item["seed"] == SEED)
    source_episode = load_strict_json(default_store_root() / entry["relative_path"])
    t20_10 = load_strict_json(T20_10_PATH)
    source_anchor_start = t20_10["corrected_oracle_rollout"]["anchor_start_position_m"]

    _set_offline_runtime()
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class
    from lerobot.policies.pi05.processor_pi05 import make_pi05_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from peft import PeftConfig, PeftModel

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.14 closed loop requires local MPS")
    torch.manual_seed(INFERENCE_SEED)
    contract = _model_contract(plan, "pi05")
    _verify_model_sources(contract)
    snapshot = _snapshot(contract["initialization"])
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.compile_model = False
    config.n_action_steps = 5
    config.pretrained_path = str(snapshot)
    policy_class = get_policy_class(config.type)
    base = policy_class.from_pretrained(
        snapshot, config=config, local_files_only=True, strict=True
    )
    adapter_path = training_run / "checkpoint"
    peft_config = PeftConfig.from_pretrained(adapter_path, local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot.resolve():
        raise ValueError("T20.14 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base,
        adapter_path,
        config=peft_config,
        is_trainable=False,
        local_files_only=True,
    ).to("mps").eval()
    dataset_stats = _dataset_stats(normalizer, torch)
    preprocessor, postprocessor = make_pi05_pre_post_processors(
        config, dataset_stats=dataset_stats
    )
    policy.reset()

    def policy_action(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        raw = {
            "observation.images.base_0_rgb": images["top"].copy(),
            "observation.images.left_wrist_0_rgb": images["wrist"].copy(),
            "observation.state": np.asarray(
                mujoco_to_lerobot(state[:6]), dtype=np.float32
            ),
        }
        prepared = prepare_observation_for_inference(
            raw,
            torch.device("mps"),
            task=TASK,
            robot_type="so101_follower",
        )
        with torch.inference_mode():
            normalized = policy.select_action(preprocessor(prepared))
            canonical = postprocessor(normalized)
        values = canonical.detach().cpu().float().numpy().reshape(-1)
        if values.shape != (6,) or not np.isfinite(values).all():
            raise ValueError("T20.14 PI0.5 emitted an invalid action")
        return np.asarray(lerobot_to_mujoco(values.tolist()), dtype=np.float64)

    observed_frames = []
    rollout = run_policy_grasp_closed_loop(
        policy_action,
        checkpoint_sha256=expected_checkpoint,
        training_run_summary_sha256=_sha(summary_path),
        seed=SEED,
        schema_version=SCHEMA_VERSION,
        task_id="T20.14",
        evidence_mode="dataset_normalized_pi05_fixed_seed_force_bearing_release",
        policy_label="pi05_dataset_normalized",
        frame_observer=observed_frames.append,
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    )
    validate_rendered_keyframes(rollout["rendered_keyframes"])
    diagnostics = analyze_model_actions(
        source_episode["frames"],
        observed_frames,
        source_anchor_start_position_m=source_anchor_start,
    )
    payload = sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.14",
            "model_id": "pi05",
            "source_training_identity_sha256": summary["identity_sha256"],
            "source_training_file_sha256": _sha(summary_path),
            "source_normalizer_identity_sha256": normalizer["identity_sha256"],
            "source_episode_file_sha256": entry["episode_file_sha256"],
            "source_t20_10_identity_sha256": t20_10["identity_sha256"],
            "action_error_diagnostics": diagnostics,
            "closed_loop": rollout,
            "policy_runtime": {
                "python": sys.version.split()[0],
                "torch": torch.__version__,
                "device": "mps",
                "dtype": "float32",
                "offline": True,
                "inference_seed": INFERENCE_SEED,
                "action_horizon": 5,
                "queue_refill_count": _replan_count(rollout["frame_count"]),
                "denoising_steps": config.num_inference_steps,
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
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print(
        payload["identity_sha256"],
        rollout["simulation_semantic_strict_success"],
        rollout["maximum_anchor_lift_m"],
        diagnostics["initial_gripper_absolute_error_rad"],
    )
    return 0


def _verify_summary(summary: dict) -> None:
    required = {
        "schema_version": "scenesmith.t20_14_dataset_normalized_pi05_training.v1",
        "task_id": "T20.14",
        "model_id": "pi05",
        "optimizer_update_count": 20,
        "microbatch_count": 20,
        "optimizer_training": True,
        "model_inference_executed": False,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    if any(summary.get(key) != value for key, value in required.items()):
        raise ValueError("T20.14 training result contract drifted")
    if summary.get("normalization", {}).get("loss_dimension_weights") != [1.0] * 6:
        raise ValueError("T20.14 training result loss weights drifted")


def _dataset_stats(normalizer, torch):
    return {
        key: {
            name: torch.tensor(values[name], dtype=torch.float32)
            for name in ("mean", "std")
        }
        for key, values in {
            "observation.state": normalizer["fitted_statistics"]["state"],
            "action": normalizer["fitted_statistics"]["action"],
        }.items()
    }


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
