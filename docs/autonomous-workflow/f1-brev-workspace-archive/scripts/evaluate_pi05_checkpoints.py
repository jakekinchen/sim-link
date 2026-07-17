#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import os
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


TASK = "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."
CHECKPOINT_STEPS = (1000, 2000, 3000, 4000, 5000)
VARIANTS = (("chunk_50", 50), ("receding_10", 10))


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def sign(payload: dict) -> dict:
    result = copy.deepcopy(payload)
    result.pop("identity_sha256", None)
    result["identity_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def checkpoint_dir(training_root: Path, step: int) -> Path:
    direct = training_root / "checkpoints" / f"{step:06d}" / "pretrained_model"
    if direct.is_dir():
        return direct
    matches = [p / "pretrained_model" for p in (training_root / "checkpoints").iterdir() if p.is_dir() and p.name.isdigit() and int(p.name) == step]
    if len(matches) != 1 or not matches[0].is_dir():
        raise FileNotFoundError(f"checkpoint {step} not found")
    return matches[0]


class ChunkAdapter:
    def __init__(self, *, policy: Any, preprocessor: Any, postprocessor: Any, torch: Any, prepare: Any, to_lerobot: Any, to_mujoco: Any, n_action_steps: int, checkpoint_step: int):
        self.policy = policy
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor
        self.torch = torch
        self.prepare = prepare
        self.to_lerobot = to_lerobot
        self.to_mujoco = to_mujoco
        self.n_action_steps = n_action_steps
        self.checkpoint_step = checkpoint_step
        self.queue: deque[np.ndarray] = deque()
        self.frame_index = 0
        self.decode_count = 0

    def __call__(self, images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        if not self.queue:
            self.decode(images, state)
        self.frame_index += 1
        return self.queue.popleft().copy()

    def decode(self, images: dict[str, np.ndarray], state: np.ndarray) -> None:
        raw = {
            "observation.images.base_0_rgb": images["top"].copy(),
            "observation.images.left_wrist_0_rgb": images["wrist"].copy(),
            "observation.state": np.asarray(self.to_lerobot(state[:6]), dtype=np.float32),
        }
        prepared = self.prepare(raw, self.torch.device("cuda"), task=TASK, robot_type="so101_follower")
        seed = 20260717 + self.checkpoint_step * 100 + self.n_action_steps * 10 + self.frame_index
        self.torch.manual_seed(seed)
        with self.torch.inference_mode():
            normalized = self.policy.predict_action_chunk(self.preprocessor(prepared)).squeeze(0)
        physical = []
        for action in normalized:
            canonical = self.postprocessor(action.unsqueeze(0))
            values = canonical.detach().cpu().float().numpy().reshape(-1)
            if values.shape != (6,) or not np.isfinite(values).all():
                raise ValueError("invalid PI0.5 action")
            physical.append(self.to_mujoco(values.tolist()))
        rows = np.asarray(physical, dtype=np.float64)
        self.queue.extend(row.copy() for row in rows[: self.n_action_steps])
        self.decode_count += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "outputs/evaluations"
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)

    sys.path.insert(0, str(root / "deps/lerobot/src"))
    sys.path.insert(0, str(root / "sim-link"))
    os.environ.update({
        "HF_HOME": str(root / "huggingface"),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "CUDA_VISIBLE_DEVICES": "0",
    })
    import torch
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class, make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from scenesmith.robot_lab.act_grasp_closed_loop import FORCE_BEARING_RELEASE_CLEARANCE_BASIS, run_policy_grasp_closed_loop
    from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable for policy inference")
    training_log_sha = sha(root / "receipts/TRAINING.log")
    receipts = []
    for step in CHECKPOINT_STEPS:
        checkpoint = checkpoint_dir(root / "outputs/training", step)
        model_path = checkpoint / "model.safetensors"
        checkpoint_sha = sha(model_path)
        checkpoint_config_sha = sha(checkpoint / "config.json")
        config = PreTrainedConfig.from_pretrained(checkpoint, local_files_only=True)
        config.device = "cuda"
        config.dtype = "bfloat16"
        config.compile_model = False
        config.n_action_steps = 50
        policy_class = get_policy_class(config.type)
        policy = policy_class.from_pretrained(checkpoint, config=config, local_files_only=True, strict=True).to("cuda").eval()
        preprocessor, postprocessor = make_pre_post_processors(
            policy_cfg=config,
            pretrained_path=checkpoint,
            preprocessor_overrides={"device_processor": {"device": "cuda"}},
            postprocessor_overrides={"device_processor": {"device": "cpu"}},
        )
        for variant_id, n_action_steps in VARIANTS:
            policy.reset()
            adapter = ChunkAdapter(
                policy=policy,
                preprocessor=preprocessor,
                postprocessor=postprocessor,
                torch=torch,
                prepare=prepare_observation_for_inference,
                to_lerobot=mujoco_to_lerobot,
                to_mujoco=lerobot_to_mujoco,
                n_action_steps=n_action_steps,
                checkpoint_step=step,
            )
            rollout = run_policy_grasp_closed_loop(
                adapter,
                checkpoint_sha256=checkpoint_sha,
                training_run_summary_sha256=training_log_sha,
                seed=0,
                schema_version="sim_link.f1_pi05_cpu_mujoco_rollout.v1",
                task_id="F1",
                evidence_mode=f"checkpoint_{step}_{variant_id}",
                policy_label="pi05_r0_full_finetune",
                release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
                capture_images=True,
            )
            receipt = sign({
                "schema_version": "sim_link.f1_pi05_checkpoint_evaluation.v1",
                "evaluated_at": datetime.now().astimezone().isoformat(),
                "checkpoint_step": step,
                "checkpoint_path": str(checkpoint),
                "checkpoint_model_sha256": checkpoint_sha,
                "checkpoint_config_sha256": checkpoint_config_sha,
                "variant_id": variant_id,
                "n_action_steps": n_action_steps,
                "simulation_device": "cpu",
                "model_device": "cuda:0",
                "decode_count": adapter.decode_count,
                "rollout": rollout,
                "hardware_accessed": False,
                "camera_accessed": False,
                "serial_accessed": False,
                "physical_motion": False,
                "physical_transfer_ready": False,
                "promotion_eligible": False,
            })
            path = output / f"step_{step:05d}_{variant_id}.json"
            path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            receipts.append(receipt)
            print(step, variant_id, rollout["simulation_semantic_strict_success"], rollout["maximum_anchor_lift_m"], rollout["terminal_outcome"], flush=True)
        del policy
        gc.collect()
        torch.cuda.empty_cache()

    best = max(
        receipts,
        key=lambda row: (
            bool(row["rollout"]["simulation_semantic_strict_success"]),
            float(row["rollout"]["maximum_anchor_lift_m"]),
            int(row["checkpoint_step"]),
            row["variant_id"] == "chunk_50",
        ),
    )
    summary = sign({
        "schema_version": "sim_link.f1_pi05_evaluation_summary.v1",
        "status": "complete",
        "evaluation_count": len(receipts),
        "checkpoint_steps": list(CHECKPOINT_STEPS),
        "variants": [name for name, _ in VARIANTS],
        "best_checkpoint_step": best["checkpoint_step"],
        "best_checkpoint_path": best["checkpoint_path"],
        "best_checkpoint_model_sha256": best["checkpoint_model_sha256"],
        "best_checkpoint_config_sha256": best["checkpoint_config_sha256"],
        "best_variant_id": best["variant_id"],
        "best_strict_success": best["rollout"]["simulation_semantic_strict_success"],
        "best_maximum_anchor_lift_m": best["rollout"]["maximum_anchor_lift_m"],
        "best_terminal_outcome": best["rollout"]["terminal_outcome"],
        "f2_endpoint_coordination_required": bool(best["rollout"]["simulation_semantic_strict_success"]),
        "hardware_accessed": False,
        "camera_accessed": False,
        "serial_accessed": False,
        "physical_motion": False,
    })
    (output / "EVALUATION_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(summary["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
