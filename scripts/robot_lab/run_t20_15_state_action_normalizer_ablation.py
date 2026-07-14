#!/usr/bin/env python3
"""Run the no-optimizer T20.15 PI0.5 state/action normalizer 2x2 ablation."""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import os
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.simulation_training_authority import (
    require_active_simulation_training_authority,
)
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot
from scenesmith.robot_lab.state_action_normalizer_ablation import (
    CELL_ORDER,
    build_state_action_normalizer_ablation,
    verify_state_action_normalizer_ablation,
)
from scripts.robot_lab.run_t20_7_model_closed_loop import INFERENCE_SEED
from scripts.robot_lab.run_t20_7_model_training import (
    TASK,
    _model_contract,
    _set_offline_runtime,
    _snapshot,
    _verify_model_sources,
)


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
NORMALIZER_PATH = REPO_ROOT / "outputs/robot_lab/t20_13_dataset_bound_pi05_normalizer.json"
T20_14_ROOT = REPO_ROOT / "outputs/robot_lab/t20_14_dataset_normalized_pi05_run_001"
TRAINING_PATH = T20_14_ROOT / "run_summary.json"
EVALUATION_PATH = T20_14_ROOT / "evaluation_summary.json"
CLOSED_LOOP_PATH = T20_14_ROOT / "closed_loop.json"
CHECKPOINT_PATH = T20_14_ROOT / "checkpoint/adapter_model.safetensors"
MANIFEST_PATH = REPO_ROOT / "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
SEED = 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    if args.check:
        _check_stored_output(output)
        return 0
    if output.exists():
        raise ValueError("T20.15 ablation output already exists")
    require_active_simulation_training_authority(repo_root=REPO_ROOT)

    plan = _load_signed(PLAN_PATH, "T20.15 T20.7 plan")
    normalizer = _load_signed(NORMALIZER_PATH, "T20.15 T20.13 normalizer")
    training = _load_signed(TRAINING_PATH, "T20.15 T20.14 training")
    evaluation = _load_signed(EVALUATION_PATH, "T20.15 T20.14 evaluation")
    closed_loop = _load_signed(CLOSED_LOOP_PATH, "T20.15 T20.14 closed loop")
    _verify_sources(training, evaluation, closed_loop, normalizer)
    manifest = load_strict_json(MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    episode_entry = next(row for row in manifest["episodes"] if row["seed"] == SEED)
    episode_path = default_store_root() / episode_entry["relative_path"]
    episode = load_strict_json(episode_path)
    source_frame = episode["frames"][0]
    if source_frame["frame_index"] != 0 or source_frame["source_phase"] != "approach":
        raise ValueError("T20.15 source frame-zero identity drifted")
    expected_checkpoint = training["checkpoint_files"][
        "checkpoint/adapter_model.safetensors"
    ]["sha256"]
    if _sha(CHECKPOINT_PATH) != expected_checkpoint:
        raise ValueError("T20.15 checkpoint hash drifted")

    _set_offline_runtime()
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class, make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from peft import PeftConfig, PeftModel

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.15 requires the authorized local MPS runtime")
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
    adapter_path = T20_14_ROOT / "checkpoint"
    peft_config = PeftConfig.from_pretrained(adapter_path, local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot.resolve():
        raise ValueError("T20.15 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base,
        adapter_path,
        config=peft_config,
        is_trainable=False,
        local_files_only=True,
    ).to("mps").eval()
    checkpoint_pre, checkpoint_post = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=snapshot,
        preprocessor_overrides={"device_processor": {"device": "mps"}},
        postprocessor_overrides={"device_processor": {"device": "cpu"}},
    )
    dataset_pre = copy.deepcopy(checkpoint_pre)
    dataset_post = copy.deepcopy(checkpoint_post)
    checkpoint_state_stats = checkpoint_pre.steps[2].stats["observation.state"]
    checkpoint_action_stats = checkpoint_post.steps[0].stats["action"]
    dataset_state_stats = normalizer["fitted_statistics"]["state"]
    dataset_action_stats = normalizer["fitted_statistics"]["action"]
    dataset_pre.steps[2].stats["observation.state"] = dataset_state_stats
    dataset_pre.steps[2].to(
        device=dataset_pre.steps[2].device, dtype=dataset_pre.steps[2].dtype
    )
    dataset_post.steps[0].stats["action"] = dataset_action_stats
    dataset_post.steps[0].to(
        device=dataset_post.steps[0].device, dtype=dataset_post.steps[0].dtype
    )
    processor_evidence = _processor_evidence(
        checkpoint_pre,
        checkpoint_post,
        dataset_pre,
        dataset_post,
        checkpoint_state_stats,
        dataset_state_stats,
        checkpoint_action_stats,
        dataset_action_stats,
    )

    top = _decode_image(source_frame["observations"]["top"])
    wrist = _decode_image(source_frame["observations"]["wrist"])
    state = np.asarray(
        mujoco_to_lerobot(source_frame["observations"]["joint_position_mujoco_rad"]),
        dtype=np.float32,
    )
    oracle = source_frame["actions"]["requested"]["values"]
    preprocessors = {"checkpoint": checkpoint_pre, "dataset": dataset_pre}
    postprocessors = {"checkpoint": checkpoint_post, "dataset": dataset_post}
    conditions = [
        ("checkpoint", "checkpoint"),
        ("checkpoint", "dataset"),
        ("dataset", "checkpoint"),
        ("dataset", "dataset"),
    ]
    cells = []
    for cell_id, (state_mode, action_mode) in zip(
        CELL_ORDER, conditions, strict=True
    ):
        require_active_simulation_training_authority(repo_root=REPO_ROOT)
        policy.reset()
        torch.manual_seed(INFERENCE_SEED)
        raw = {
            "observation.images.top": top.copy(),
            "observation.images.wrist": wrist.copy(),
            "observation.state": state.copy(),
        }
        prepared = prepare_observation_for_inference(
            raw,
            torch.device("mps"),
            task=TASK,
            robot_type="so101_follower",
        )
        with torch.inference_mode():
            normalized = policy.select_action(preprocessors[state_mode](prepared))
            canonical = postprocessors[action_mode](normalized.clone())
        normalized_values = normalized.detach().cpu().float().numpy().reshape(-1)
        canonical_values = canonical.detach().cpu().float().numpy().reshape(-1)
        if (
            normalized_values.shape != (6,)
            or canonical_values.shape != (6,)
            or not np.isfinite(normalized_values).all()
            or not np.isfinite(canonical_values).all()
        ):
            raise ValueError("T20.15 model output is malformed or non-finite")
        mujoco_action = np.asarray(
            lerobot_to_mujoco(canonical_values.tolist()), dtype=np.float64
        )
        cells.append(
            {
                "cell_id": cell_id,
                "state_preprocessor": state_mode,
                "action_postprocessor": action_mode,
                "normalized_model_output": normalized_values.tolist(),
                "normalized_output_sha256": hashlib.sha256(
                    normalized_values.tobytes()
                ).hexdigest(),
                "canonical_action_lerobot": canonical_values.tolist(),
                "canonical_action_mujoco_rad": mujoco_action.tolist(),
                "oracle_absolute_error_rad": np.abs(
                    mujoco_action - np.asarray(oracle, dtype=np.float64)
                ).tolist(),
            }
        )
    expected_t20_14 = np.asarray(
        closed_loop["closed_loop"]["policy_requested_action_first"], dtype=np.float64
    )
    reproduced_t20_14 = np.asarray(
        cells[-1]["canonical_action_mujoco_rad"], dtype=np.float64
    )
    reproduction_error = float(np.max(np.abs(expected_t20_14 - reproduced_t20_14)))
    if reproduction_error > 1e-7:
        raise ValueError("T20.15 dataset/dataset cell did not reproduce T20.14 frame zero")

    sources = {
        "t20_7_plan": _ref(PLAN_PATH, plan),
        "t20_13_normalizer": _ref(NORMALIZER_PATH, normalizer),
        "t20_14_training": _ref(TRAINING_PATH, training),
        "t20_14_evaluation": _ref(EVALUATION_PATH, evaluation),
        "t20_14_closed_loop": _ref(CLOSED_LOOP_PATH, closed_loop),
        "t20_14_checkpoint": {
            "path": _relative(CHECKPOINT_PATH),
            "file_sha256": expected_checkpoint,
        },
        "seed_2_source_episode": {
            "path": _relative(episode_path),
            "file_sha256": episode_entry["episode_file_sha256"],
            "frame_index": 0,
            "top_image_sha256": source_frame["observations"]["top"]["image_sha256"],
            "wrist_image_sha256": source_frame["observations"]["wrist"][
                "image_sha256"
            ],
        },
        "t20_14_dataset_dataset_reproduction_max_error_rad": reproduction_error,
    }
    runtime = {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "device": "mps",
        "dtype": "float32",
        "offline": True,
        "inference_seed": INFERENCE_SEED,
        "action_horizon": 5,
        "model_inference_call_count": 4,
        "optimizer_step_count": 0,
        "simulation_step_count": 0,
        "lerobot_stack_identity_sha256": stack["identity_sha256"],
    }
    payload = build_state_action_normalizer_ablation(
        sources=sources,
        cells=cells,
        oracle_action_rad=oracle,
        processor_evidence=processor_evidence,
        runtime=runtime,
    )
    verify_state_action_normalizer_ablation(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print(
        payload["identity_sha256"],
        payload["finding"]["dominant_effect"],
        payload["finding"]["selected_next_hypothesis"],
    )
    return 0


def _processor_evidence(
    checkpoint_pre,
    checkpoint_post,
    dataset_pre,
    dataset_post,
    checkpoint_state_stats,
    dataset_state_stats,
    checkpoint_action_stats,
    dataset_action_stats,
) -> dict:
    if (
        type(checkpoint_pre.steps[2]).__name__ != "NormalizerProcessorStep"
        or type(checkpoint_post.steps[0]).__name__ != "UnnormalizerProcessorStep"
        or type(dataset_pre.steps[2]).__name__ != "NormalizerProcessorStep"
        or type(dataset_post.steps[0]).__name__ != "UnnormalizerProcessorStep"
    ):
        raise ValueError("T20.15 target processor step identity drifted")
    old_pre_stats = _jsonable(checkpoint_pre.steps[2].stats)
    new_pre_stats = _jsonable(dataset_pre.steps[2].stats)
    old_post_stats = _jsonable(checkpoint_post.steps[0].stats)
    new_post_stats = _jsonable(dataset_post.steps[0].stats)
    old_pre_other = {k: v for k, v in old_pre_stats.items() if k != "observation.state"}
    new_pre_other = {k: v for k, v in new_pre_stats.items() if k != "observation.state"}
    old_post_other = {k: v for k, v in old_post_stats.items() if k != "action"}
    new_post_other = {k: v for k, v in new_post_stats.items() if k != "action"}
    pre_other_identical = old_pre_other == new_pre_other
    post_other_identical = old_post_other == new_post_other
    if not pre_other_identical or not post_other_identical:
        raise ValueError("T20.15 changed non-target processor statistics")
    if (
        new_pre_stats["observation.state"] != _jsonable(dataset_state_stats)
        or new_post_stats["action"] != _jsonable(dataset_action_stats)
        or old_pre_stats["observation.state"] == new_pre_stats["observation.state"]
        or old_post_stats["action"] == new_post_stats["action"]
    ):
        raise ValueError("T20.15 target processor statistics were not isolated")
    return {
        "checkpoint_pipeline_loaded_from_pinned_snapshot": True,
        "checkpoint_preprocessor_normalizer_step_index": 2,
        "checkpoint_postprocessor_unnormalizer_step_index": 0,
        "only_state_statistics_replaced_in_dataset_state_preprocessor": True,
        "only_action_statistics_replaced_in_dataset_action_postprocessor": True,
        "all_other_preprocessor_statistics_identical": pre_other_identical,
        "all_other_postprocessor_statistics_identical": post_other_identical,
        "checkpoint_state_statistics_sha256": _stats_sha(checkpoint_state_stats),
        "dataset_state_statistics_sha256": _stats_sha(dataset_state_stats),
        "checkpoint_action_statistics_sha256": _stats_sha(checkpoint_action_stats),
        "dataset_action_statistics_sha256": _stats_sha(dataset_action_stats),
    }


def _verify_sources(training, evaluation, closed_loop, normalizer) -> None:
    if (
        training.get("task_id") != "T20.14"
        or training.get("optimizer_update_count") != 20
        or training.get("source_normalizer_identity_sha256")
        != normalizer.get("identity_sha256")
        or evaluation.get("task_id") != "T20.14"
        or evaluation.get("finding", {}).get("selected_next_hypothesis")
        != "state_vs_action_normalizer_ablation_before_more_optimizer_updates"
        or closed_loop.get("task_id") != "T20.14"
    ):
        raise ValueError("T20.15 source contract drifted")


def _check_stored_output(output: Path) -> None:
    payload = load_strict_json(output)
    verify_state_action_normalizer_ablation(payload)
    expected_paths = {
        "t20_7_plan": _relative(PLAN_PATH),
        "t20_13_normalizer": _relative(NORMALIZER_PATH),
        "t20_14_training": _relative(TRAINING_PATH),
        "t20_14_evaluation": _relative(EVALUATION_PATH),
        "t20_14_closed_loop": _relative(CLOSED_LOOP_PATH),
        "t20_14_checkpoint": _relative(CHECKPOINT_PATH),
    }
    for source_id, expected_path in expected_paths.items():
        source = payload["sources"][source_id]
        if source.get("path") != expected_path:
            raise ValueError(f"T20.15 source path drifted: {source_id}")
        path = REPO_ROOT / expected_path
        if _sha(path) != source.get("file_sha256"):
            raise ValueError(f"T20.15 source file hash drifted: {source_id}")
        if "identity_sha256" in source:
            linked = load_strict_json(path)
            verify_signed_payload(linked, label=f"T20.15 source {source_id}")
            if linked["identity_sha256"] != source["identity_sha256"]:
                raise ValueError(f"T20.15 source identity drifted: {source_id}")
    manifest = load_strict_json(MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    episode_entry = next(row for row in manifest["episodes"] if row["seed"] == SEED)
    expected_episode_path = _relative(
        default_store_root() / episode_entry["relative_path"]
    )
    episode = payload["sources"]["seed_2_source_episode"]
    if episode.get("path") != expected_episode_path:
        raise ValueError("T20.15 seed-2 episode path drifted")
    episode_path = REPO_ROOT / episode["path"]
    if (
        _sha(episode_path) != episode["file_sha256"]
        or episode["file_sha256"] != episode_entry["episode_file_sha256"]
    ):
        raise ValueError("T20.15 seed-2 episode hash drifted")
    if payload["sources"]["t20_14_dataset_dataset_reproduction_max_error_rad"] > 1e-7:
        raise ValueError("T20.15 T20.14 reproduction margin drifted")
    print("verified", _relative(output), payload["identity_sha256"])


def _load_signed(path: Path, label: str) -> dict:
    payload = load_strict_json(path)
    verify_signed_payload(payload, label=label)
    return payload


def _decode_image(value: dict) -> np.ndarray:
    from PIL import Image

    raw = base64.b64decode(value["png_base64"], validate=True)
    if hashlib.sha256(raw).hexdigest() != value["image_sha256"]:
        raise ValueError("T20.15 source image hash drifted")
    image = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"), dtype=np.uint8)
    if image.shape != (value["height"], value["width"], 3):
        raise ValueError("T20.15 source image shape drifted")
    return image.copy()


def _ref(path: Path, payload: dict) -> dict:
    return {
        "path": _relative(path),
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": _sha(path),
    }


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _stats_sha(value) -> str:
    return hashlib.sha256(canonical_json_bytes(_jsonable(value))).hexdigest()


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "detach"):
        return value.detach().cpu().numpy().tolist()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    raise SystemExit(main())
