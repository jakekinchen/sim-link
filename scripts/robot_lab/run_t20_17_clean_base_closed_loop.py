#!/usr/bin/env python3
"""Evaluate the T20.17 clean-base candidate unassisted on frozen seed 6."""

from __future__ import annotations

import hashlib
import os
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
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.scripted_grasp_episode_generation import default_store_root, verify_episode_store
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot
from scenesmith.robot_lab.t20_17_clean_base_campaign import RUN_ROOT, RUN_SUMMARY_PATH, verify_run_summary
from scenesmith.robot_lab.t20_17_clean_base_preflight import EXPECTED_MODEL_REVISION, SOURCE_MANIFEST_PATH, TASK
from scenesmith.robot_lab.t20_17_simulation_training_authority import require_active_t20_17_authority


SEED = 6
INFERENCE_SEED = 20260714
ACTION_HORIZON = 5
SCHEMA_VERSION = "scenesmith.t20_17_clean_base_closed_loop.v1"
OUTPUT_PATH = Path("held_out_seed_6_closed_loop.json")


def main() -> int:
    require_active_t20_17_authority(repo_root=REPO_ROOT)
    run_root = REPO_ROOT / RUN_ROOT
    summary_path = run_root / RUN_SUMMARY_PATH
    summary = load_strict_json(summary_path)
    verify_signed_payload(summary, label="T20.17 clean-base training run")
    verify_run_summary(summary)
    checkpoint = run_root / "training/checkpoints/last/pretrained_model"
    _verify_checkpoint(checkpoint, summary)
    output = run_root / OUTPUT_PATH
    if output.exists():
        raise FileExistsError("T20.17 held-out evaluation output already exists")
    manifest = load_strict_json(REPO_ROOT / SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    source_entry = next(row for row in manifest["episodes"] if row["seed"] == SEED)
    if source_entry["outcome"]["strict_success"] is not True:
        raise ValueError("T20.17 held-out source episode is not strict-success evidence")

    os.environ.update({
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "PYTORCH_ENABLE_MPS_FALLBACK": "1",
    })
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class, make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from peft import PeftConfig, PeftModel

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.17 held-out evaluation requires local MPS")
    config = PreTrainedConfig.from_pretrained(checkpoint, local_files_only=True)
    snapshot = Path(config.pretrained_path).resolve()
    if snapshot.name != EXPECTED_MODEL_REVISION or not (snapshot / "model.safetensors").is_file():
        raise ValueError("T20.17 evaluation base snapshot binding drifted")
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.compile_model = False
    config.n_action_steps = ACTION_HORIZON
    policy_class = get_policy_class(config.type)
    base = policy_class.from_pretrained(snapshot, config=config, local_files_only=True, strict=True)
    peft_config = PeftConfig.from_pretrained(checkpoint, local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot:
        raise ValueError("T20.17 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base, checkpoint, config=peft_config, is_trainable=False, local_files_only=True
    ).to("mps").eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=checkpoint,
        preprocessor_overrides={"device_processor": {"device": "mps"}},
        postprocessor_overrides={"device_processor": {"device": "cpu"}},
    )
    torch.manual_seed(INFERENCE_SEED)
    policy.reset()

    def policy_action(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        raw = {
            "observation.images.base_0_rgb": images["top"].copy(),
            "observation.images.left_wrist_0_rgb": images["wrist"].copy(),
            "observation.state": np.asarray(mujoco_to_lerobot(state[:6]), dtype=np.float32),
        }
        prepared = prepare_observation_for_inference(
            raw, torch.device("mps"), task=TASK, robot_type="so101_follower"
        )
        with torch.inference_mode():
            normalized = policy.select_action(preprocessor(prepared))
            canonical = postprocessor(normalized)
        values = canonical.detach().cpu().float().numpy().reshape(-1)
        if values.shape != (6,) or not np.isfinite(values).all():
            raise ValueError("T20.17 candidate emitted a non-finite or wrong-shaped action")
        return np.asarray(lerobot_to_mujoco(values.tolist()), dtype=np.float64)

    adapter_sha = next(row["sha256"] for row in summary["checkpoint_tree"] if row["path"] == "adapter_model.safetensors")
    rollout = run_policy_grasp_closed_loop(
        policy_action,
        checkpoint_sha256=adapter_sha,
        training_run_summary_sha256=_sha(summary_path),
        seed=SEED,
        schema_version=SCHEMA_VERSION,
        task_id="T20.17",
        evidence_mode="clean_base_dataset_native_pi05_held_out_seed_6_unassisted",
        policy_label="pi05_clean_base_lora_rank4",
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    )
    validate_rendered_keyframes(rollout["rendered_keyframes"])
    payload = sign_payload({
        "schema_version": SCHEMA_VERSION,
        "task_id": "T20.17",
        "source_training_identity_sha256": summary["identity_sha256"],
        "source_training_file_sha256": _sha(summary_path),
        "source_episode_file_sha256": source_entry["episode_file_sha256"],
        "source_episode_raw_rollout_identity_sha256": source_entry["raw_rollout_record_identity_sha256"],
        "closed_loop": rollout,
        "policy_runtime": {
            "device": "mps",
            "dtype": "float32",
            "offline": True,
            "inference_seed": INFERENCE_SEED,
            "action_horizon": ACTION_HORIZON,
            "base_revision": EXPECTED_MODEL_REVISION,
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
    })
    dump_canonical_json(output, payload)
    print(payload["identity_sha256"], rollout["simulation_semantic_strict_success"], rollout["maximum_anchor_lift_m"], rollout["terminal_outcome"])
    return 0


def _verify_checkpoint(checkpoint: Path, summary: dict) -> None:
    for row in summary["checkpoint_tree"]:
        path = checkpoint / row["path"]
        if not path.is_file() or path.stat().st_size != row["size_bytes"] or _sha(path) != row["sha256"]:
            raise ValueError(f"T20.17 checkpoint file drifted: {row['path']}")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
