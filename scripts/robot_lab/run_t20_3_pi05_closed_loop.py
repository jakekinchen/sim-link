#!/usr/bin/env python3
"""Evaluate one saved T20.3 PI0.5 adapter in held-out MuJoCo closed loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.act_grasp_closed_loop import run_policy_grasp_closed_loop
from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.pi05_preprocessing_contract import (
    CHECKPOINT_REPOSITORY_ID,
    CHECKPOINT_REVISION,
    TOKENIZER_REVISION,
)
from scenesmith.robot_lab.simulation_training_authority import require_active_simulation_training_authority
from scenesmith.robot_lab.simulation_training_spec import SPEC_PATH
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot


TASK = "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."
SCHEMA_VERSION = "scenesmith.t20_3_pi05_closed_loop.v1"
ACTION_HORIZON = 5


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--task-id", choices=("T20.3", "T20.4"), default="T20.3")
    parser.add_argument("--expected-updates", type=int, choices=(250, 500, 1000), default=250)
    args = parser.parse_args()
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    training_run = _resolve(args.training_run)
    output = _resolve(args.output)
    if output.exists():
        raise ValueError("T20.3 closed-loop outputs are immutable")
    summary_path = training_run / "run_summary.json"
    adapter_path = training_run / "adapter"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _verify_training_run(
        summary,
        adapter_path,
        expected_task_id=args.task_id,
        expected_updates=args.expected_updates,
    )
    spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    if summary["source_training_spec_identity_sha256"] != spec["identity_sha256"]:
        raise ValueError("T20.3 adapter training-spec binding drifted")

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class, make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from peft import PeftConfig, PeftModel

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.3 closed-loop evaluation requires authorized local MPS")
    snapshot = _snapshot_root(CHECKPOINT_REPOSITORY_ID, CHECKPOINT_REVISION)
    tokenizer = _snapshot_root("google/paligemma-3b-pt-224", TOKENIZER_REVISION)
    if not snapshot.is_dir() or not (tokenizer / "tokenizer.json").is_file():
        raise FileNotFoundError("Pinned PI0.5 checkpoint or tokenizer snapshot is incomplete")
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.compile_model = False
    config.n_action_steps = ACTION_HORIZON
    config.pretrained_path = str(snapshot)
    policy_class = get_policy_class(config.type)
    base_policy = policy_class.from_pretrained(snapshot, config=config, local_files_only=True, strict=True)
    peft_config = PeftConfig.from_pretrained(adapter_path, local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot.resolve():
        raise ValueError("T20.3 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base_policy,
        adapter_path,
        config=peft_config,
        is_trainable=False,
        local_files_only=True,
    ).to("mps").eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=snapshot,
        preprocessor_overrides={"device_processor": {"device": "mps"}},
        postprocessor_overrides={"device_processor": {"device": "cpu"}},
    )
    torch.manual_seed(1703)
    policy.reset()

    def policy_action(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        raw = {
            "observation.images.top": images["top"].copy(),
            "observation.images.wrist": images["wrist"].copy(),
            "observation.state": np.asarray(mujoco_to_lerobot(state[:6]), dtype=np.float32),
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
            raise ValueError("PI0.5 postprocessor emitted a non-finite or wrong-shaped action")
        return np.asarray(lerobot_to_mujoco(values.tolist()), dtype=np.float64)

    payload = run_policy_grasp_closed_loop(
        policy_action,
        checkpoint_sha256=summary["adapter"]["checkpoint_files"]["adapter/adapter_model.safetensors"]["sha256"],
        training_run_summary_sha256=_sha(summary_path),
        seed=args.seed,
        schema_version=(
            SCHEMA_VERSION
            if args.task_id == "T20.3"
            else "scenesmith.t20_4_pi05_closed_loop.v1"
        ),
        task_id=args.task_id,
        evidence_mode=(
            "held_out_seed_closed_loop_pi05_lora_mujoco"
            if args.task_id == "T20.3"
            else "held_out_seed_closed_loop_pi05_update_ladder_mujoco"
        ),
        policy_label="PI0.5-LoRA",
    )
    payload["policy_runtime"] = {
        "device": "mps",
        "dtype": "float32",
        "offline": True,
        "action_horizon": ACTION_HORIZON,
        "inference_replan_count": (payload["frame_count"] + ACTION_HORIZON - 1) // ACTION_HORIZON,
        "num_inference_steps": config.num_inference_steps,
        "source_optimizer_update_count": summary.get("optimizer_update_count"),
        "coordinate_conversion": "mujoco_radians_to_lerobot_degrees_and_gripper_percent_then_inverse",
        "checkpoint_revision": CHECKPOINT_REVISION,
        "tokenizer_revision": TOKENIZER_REVISION,
    }
    payload.pop("identity_sha256")
    from scenesmith.robot_lab.artifact_contract import sign_payload

    payload = sign_payload(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print(json.dumps({key: payload[key] for key in ("identity_sha256", "terminal_outcome", "simulation_semantic_strict_success", "maximum_anchor_lift_m", "projected_action_frame_count", "failed_gate_margins")}, indent=2))
    return 0


def _verify_training_run(
    summary: dict,
    adapter_path: Path,
    *,
    expected_task_id: str = "T20.3",
    expected_updates: int = 250,
) -> None:
    if expected_task_id not in {"T20.3", "T20.4"}:
        raise ValueError("Unsupported PI0.5 evaluation task")
    if summary.get("task_id") != expected_task_id or summary.get("simulation_policy_accepted") is not False:
        raise ValueError(f"{expected_task_id} training summary contract drifted")
    if expected_task_id == "T20.4":
        if expected_updates not in {250, 500, 1000}:
            raise ValueError("Unsupported T20.4 optimizer-update rung")
        expected_microbatches = expected_updates * 2
        expected_counts = {
            "optimizer_update_count": expected_updates,
            "gradient_accumulation_steps": 2,
            "microbatch_count": expected_microbatches,
        }
        if any(summary.get(name) != value for name, value in expected_counts.items()):
            raise ValueError("T20.4 optimizer-update accounting drifted")
        loss = summary.get("loss", {})
        if (
            len(summary.get("realized_train_starts", [])) != expected_microbatches
            or len(loss.get("per_update", [])) != expected_updates
            or len(loss.get("per_microbatch", [])) != expected_microbatches
        ):
            raise ValueError("T20.4 sample or loss accounting drifted")
    files = summary.get("adapter", {}).get("checkpoint_files", {})
    required = {
        "adapter/adapter_config.json": adapter_path / "adapter_config.json",
        "adapter/adapter_model.safetensors": adapter_path / "adapter_model.safetensors",
    }
    for logical_path, path in required.items():
        expected = files.get(logical_path, {}).get("sha256")
        if not isinstance(expected, str) or not path.is_file() or _sha(path) != expected:
            raise ValueError(f"{expected_task_id} {logical_path} hash drifted from its run summary")


def _snapshot_root(repository_id: str, revision: str) -> Path:
    directory = "models--" + repository_id.replace("/", "--")
    return Path.home() / ".cache/huggingface/hub" / directory / "snapshots" / revision


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
