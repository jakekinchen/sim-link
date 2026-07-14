#!/usr/bin/env python3
"""Evaluate one T20.7 trained model in the fixed held-out MuJoCo loop."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.act_grasp_closed_loop import run_policy_grasp_closed_loop
from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.model_bakeoff import (
    MODEL_ORDER,
    verify_model_training_result,
)
from scenesmith.robot_lab.simulation_training_authority import (
    require_active_simulation_training_authority,
)
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot
from scripts.robot_lab.compose_t20_7_model_training_gate import (
    _verify_checkpoint_files,
)
from scripts.robot_lab.run_t20_7_model_training import (
    TASK,
    _load_act,
    _load_diffusion,
    _model_contract,
    _set_offline_runtime,
    _snapshot,
    _verify_model_sources,
)


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
SCHEMA_VERSION = "scenesmith.t20_7_model_closed_loop.v1"
INFERENCE_SEED = 1703
HELD_OUT_SEED = 2
ACTION_HORIZON = 5


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODEL_ORDER, required=True)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require_active_simulation_training_authority(repo_root=REPO_ROOT)
    training_run = _resolve(args.training_run)
    output = _resolve(args.output)
    if output.exists():
        raise ValueError("T20.7 closed-loop outputs are immutable")

    plan = load_strict_json(PLAN_PATH)
    summary_path = training_run / "run_summary.json"
    summary = load_strict_json(summary_path)
    if summary.get("model_id") != args.model:
        raise ValueError("T20.7 closed-loop model and training-run identity differ")
    verify_model_training_result(summary, plan)
    _verify_checkpoint_files(training_run, summary["checkpoint_files"])

    _set_offline_runtime()
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    import torch

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.7 closed-loop evaluation requires local MPS")
    torch.manual_seed(INFERENCE_SEED)
    policy, policy_action, inference_steps = _load_policy_action(
        args.model, training_run, plan, torch
    )
    policy.reset()
    checkpoint_sha256 = _primary_checkpoint_sha256(summary)
    payload = run_policy_grasp_closed_loop(
        policy_action,
        checkpoint_sha256=checkpoint_sha256,
        training_run_summary_sha256=_sha(summary_path),
        seed=HELD_OUT_SEED,
        schema_version=SCHEMA_VERSION,
        task_id="T20.7",
        evidence_mode="held_out_seed_equal_sample_four_model_bakeoff_mujoco",
        policy_label=args.model,
    )
    payload.pop("identity_sha256")
    payload.update(
        {
            "model_id": args.model,
            "source_plan_identity_sha256": plan["identity_sha256"],
            "source_training_result_identity_sha256": summary["identity_sha256"],
            "model_inference_executed": True,
            "policy_runtime": {
                "python": sys.version.split()[0],
                "torch": torch.__version__,
                "device": "mps",
                "dtype": "float32",
                "offline": True,
                "inference_seed": INFERENCE_SEED,
                "action_horizon": ACTION_HORIZON,
                "maximum_open_loop_duration_frames": ACTION_HORIZON,
                "initial_policy_reset_count": 1,
                "inference_replan_count": _replan_count(payload["frame_count"]),
                "queue_refill_count": _replan_count(payload["frame_count"]),
                "denoising_steps_where_applicable": inference_steps,
                "lerobot_stack_identity_sha256": stack["identity_sha256"],
            },
        }
    )
    payload = sign_payload(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print(
        args.model,
        payload["identity_sha256"],
        payload["terminal_outcome"],
        payload["maximum_anchor_lift_m"],
    )
    return 0


def _load_policy_action(model_id: str, training_run: Path, plan: dict, torch):
    if model_id in ("pi05", "smolvla"):
        return _load_vla_policy_action(model_id, training_run, plan, torch)
    if model_id == "act":
        policy, _preprocessor, _source = _load_act(torch)
        inference_steps = None
    else:
        policy, _preprocessor, _source = _load_diffusion(torch)
        inference_steps = policy.config.num_inference_steps
    checkpoint = training_run / "checkpoint" / "model_state.pt"
    saved = torch.load(checkpoint, map_location="mps", weights_only=True)
    if saved.get("model_id") != model_id:
        raise ValueError("T20.7 checkpoint model identity drifted")
    policy.load_state_dict(saved["model"], strict=True)
    policy.eval()

    def policy_action(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        from PIL import Image

        batch = {
            "observation.images.top_rgb": _image_tensor(images["top"], Image, torch),
            "observation.images.wrist_rgb": _image_tensor(
                images["wrist"], Image, torch
            ),
            "observation.state": torch.as_tensor(state)
            .unsqueeze(0)
            .float()
            .to("mps"),
        }
        with torch.inference_mode():
            action = policy.select_action(batch)
        values = action.detach().cpu().float().numpy().reshape(-1)
        if values.shape != (6,) or not np.isfinite(values).all():
            raise ValueError("T20.7 policy emitted a non-finite or wrong-shaped action")
        return values.astype(np.float64)

    return policy, policy_action, inference_steps


def _load_vla_policy_action(model_id, training_run, plan, torch):
    if model_id == "pi05":
        import lerobot.policies.pi05.processor_pi05  # noqa: F401
    else:
        import lerobot.policies.smolvla.processor_smolvla  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class, make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from peft import PeftConfig, PeftModel

    model_contract = _model_contract(plan, model_id)
    _verify_model_sources(model_contract)
    snapshot = _snapshot(model_contract["initialization"])
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.compile_model = False
    config.n_action_steps = ACTION_HORIZON
    config.pretrained_path = str(snapshot)
    policy_class = get_policy_class(config.type)
    base = policy_class.from_pretrained(
        snapshot, config=config, local_files_only=True, strict=True
    )
    adapter_path = training_run / "checkpoint"
    peft_config = PeftConfig.from_pretrained(adapter_path, local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot.resolve():
        raise ValueError("T20.7 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base,
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

    def policy_action(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        if model_id == "pi05":
            raw = {
                "observation.images.top": images["top"].copy(),
                "observation.images.wrist": images["wrist"].copy(),
            }
        else:
            raw = {
                "observation.images.camera1": images["top"].copy(),
                "observation.images.camera2": images["wrist"].copy(),
                "observation.images.camera3": np.zeros_like(images["top"]),
            }
        raw["observation.state"] = np.asarray(
            mujoco_to_lerobot(state[:6]), dtype=np.float32
        )
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
            raise ValueError("T20.7 VLA emitted a non-finite or wrong-shaped action")
        return np.asarray(lerobot_to_mujoco(values.tolist()), dtype=np.float64)

    inference_steps = getattr(config, "num_inference_steps", None)
    if inference_steps is None:
        inference_steps = getattr(config, "num_steps", None)
    return policy, policy_action, inference_steps


def _image_tensor(image: np.ndarray, image_module, torch):
    resized = np.asarray(
        image_module.fromarray(image).resize(
            (64, 64), image_module.Resampling.BILINEAR
        ),
        dtype=np.uint8,
    ).copy()
    return (
        torch.as_tensor(resized)
        .permute(2, 0, 1)
        .unsqueeze(0)
        .float()
        .div(255)
        .to("mps")
    )


def _primary_checkpoint_sha256(summary: dict) -> str:
    preferred = (
        "checkpoint/adapter_model.safetensors",
        "checkpoint/model_state.pt",
    )
    for path in preferred:
        if path in summary["checkpoint_files"]:
            return summary["checkpoint_files"][path]["sha256"]
    raise ValueError("T20.7 primary checkpoint file is absent")


def _replan_count(frame_count: int) -> int:
    if frame_count <= 0:
        raise ValueError("T20.7 closed-loop frame count must be positive")
    return (frame_count + ACTION_HORIZON - 1) // ACTION_HORIZON


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
