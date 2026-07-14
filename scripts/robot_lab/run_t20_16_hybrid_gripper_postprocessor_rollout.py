#!/usr/bin/env python3
"""Run the T20.16 checkpoint-arm/dataset-gripper PI0.5 strict rollout."""

from __future__ import annotations

import argparse
import copy
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
    canonical_json_bytes,
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
from scripts.robot_lab.run_t20_15_state_action_normalizer_ablation import _jsonable
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
ABLATION_PATH = REPO_ROOT / "outputs/robot_lab/t20_15_state_action_normalizer_ablation.json"
T20_14_ROOT = REPO_ROOT / "outputs/robot_lab/t20_14_dataset_normalized_pi05_run_001"
TRAINING_PATH = T20_14_ROOT / "run_summary.json"
CHECKPOINT_PATH = T20_14_ROOT / "checkpoint/adapter_model.safetensors"
MANIFEST_PATH = REPO_ROOT / "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
T20_10_PATH = REPO_ROOT / "outputs/robot_lab/t20_10_release_reconciliation_run_001.json"
SCHEMA_VERSION = "scenesmith.t20_16_hybrid_gripper_postprocessor_rollout.v1"
SEED = 2
PREFLIGHT_TOLERANCE_RAD = 1e-6


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    if args.check:
        _check(output)
        return 0
    if output.exists():
        raise ValueError("T20.16 rollout output already exists")
    require_active_simulation_training_authority(repo_root=REPO_ROOT)

    plan = _load_signed(PLAN_PATH, "T20.16 plan")
    normalizer = _load_signed(NORMALIZER_PATH, "T20.16 dataset normalizer")
    ablation = _load_signed(ABLATION_PATH, "T20.16 source ablation")
    training = _load_signed(TRAINING_PATH, "T20.16 training result")
    t20_10 = _load_signed(T20_10_PATH, "T20.16 corrected oracle")
    if (
        ablation.get("finding", {}).get("selected_next_hypothesis")
        != "dataset_action_unnormalization_dominates"
        or training.get("task_id") != "T20.14"
        or normalizer.get("task_id") != "T20.13"
    ):
        raise ValueError("T20.16 source hypothesis drifted")
    checkpoint_sha256 = training["checkpoint_files"][
        "checkpoint/adapter_model.safetensors"
    ]["sha256"]
    if _sha(CHECKPOINT_PATH) != checkpoint_sha256:
        raise ValueError("T20.16 checkpoint hash drifted")
    manifest = load_strict_json(MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    episode_entry = next(row for row in manifest["episodes"] if row["seed"] == SEED)
    episode_path = default_store_root() / episode_entry["relative_path"]
    source_episode = load_strict_json(episode_path)
    source_frame = source_episode["frames"][0]

    _set_offline_runtime()
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class, make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from peft import PeftConfig, PeftModel

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.16 requires local MPS")
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
    peft_config = PeftConfig.from_pretrained(T20_14_ROOT / "checkpoint", local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot.resolve():
        raise ValueError("T20.16 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base,
        T20_14_ROOT / "checkpoint",
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
    hybrid_post = copy.deepcopy(checkpoint_post)
    checkpoint_action_stats = _jsonable(checkpoint_post.steps[0].stats["action"])
    hybrid_action_stats = copy.deepcopy(checkpoint_action_stats)
    dataset_action_stats = normalizer["fitted_statistics"]["action"]
    for statistic in ("mean", "std"):
        hybrid_action_stats[statistic][5] = dataset_action_stats[statistic][5]
    hybrid_post.steps[0].stats["action"] = hybrid_action_stats
    hybrid_post.steps[0].to(
        device=hybrid_post.steps[0].device, dtype=hybrid_post.steps[0].dtype
    )
    processor_evidence = _processor_evidence(
        checkpoint_pre,
        checkpoint_post,
        hybrid_post,
        checkpoint_action_stats,
        hybrid_action_stats,
        dataset_action_stats,
    )

    conversion_roundtrip_errors = []

    def policy_action(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        require_active_simulation_training_authority(repo_root=REPO_ROOT)
        raw = {
            "observation.images.top": images["top"].copy(),
            "observation.images.wrist": images["wrist"].copy(),
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
            normalized = policy.select_action(checkpoint_pre(prepared))
            canonical = hybrid_post(normalized)
        values = canonical.detach().cpu().float().numpy().reshape(-1)
        if values.shape != (6,) or not np.isfinite(values).all():
            raise ValueError("T20.16 PI0.5 emitted an invalid action")
        mujoco = np.asarray(lerobot_to_mujoco(values.tolist()), dtype=np.float64)
        roundtrip = np.asarray(mujoco_to_lerobot(mujoco), dtype=np.float64)
        conversion_roundtrip_errors.append(float(np.max(np.abs(roundtrip - values))))
        return mujoco

    torch.manual_seed(INFERENCE_SEED)
    policy.reset()
    first_images = {
        "top": _decode(source_frame["observations"]["top"]),
        "wrist": _decode(source_frame["observations"]["wrist"]),
    }
    first_state = np.asarray(
        source_frame["observations"]["joint_position_mujoco_rad"], dtype=np.float64
    )
    preflight_action = policy_action(first_images, first_state)
    oracle_action = np.asarray(
        source_frame["actions"]["requested"]["values"], dtype=np.float64
    )
    preflight_error = np.abs(preflight_action - oracle_action)
    expected_cell = next(
        row
        for row in ablation["cells"]
        if row["cell_id"] == "checkpoint_state_dataset_action"
    )
    expected_arm = expected_cell["initial_non_gripper_mae_rad"]
    expected_gripper = expected_cell["initial_gripper_absolute_error_rad"]
    measured_arm = float(np.mean(preflight_error[:5]))
    measured_gripper = float(preflight_error[5])
    arm_margin = PREFLIGHT_TOLERANCE_RAD - abs(measured_arm - 0.030880688091355503)
    gripper_margin = PREFLIGHT_TOLERANCE_RAD - abs(measured_gripper - expected_gripper)
    if arm_margin < 0.0 or gripper_margin < 0.0:
        raise ValueError("T20.16 hybrid frame-zero preflight missed its prediction")

    torch.manual_seed(INFERENCE_SEED)
    policy.reset()
    observed_frames = []
    rollout = run_policy_grasp_closed_loop(
        policy_action,
        checkpoint_sha256=checkpoint_sha256,
        training_run_summary_sha256=_sha(TRAINING_PATH),
        seed=SEED,
        schema_version=SCHEMA_VERSION,
        task_id="T20.16",
        evidence_mode="checkpoint_state_arm_dataset_gripper_fixed_seed",
        policy_label="pi05_hybrid_gripper_postprocessor",
        frame_observer=observed_frames.append,
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    )
    validate_rendered_keyframes(rollout["rendered_keyframes"])
    diagnostics = analyze_model_actions(
        source_episode["frames"],
        observed_frames,
        source_anchor_start_position_m=t20_10["corrected_oracle_rollout"][
            "anchor_start_position_m"
        ],
    )
    max_roundtrip = max(conversion_roundtrip_errors)
    payload = sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.16",
            "model_id": "pi05",
            "sources": {
                "plan": _ref(PLAN_PATH, plan),
                "normalizer": _ref(NORMALIZER_PATH, normalizer),
                "ablation": _ref(ABLATION_PATH, ablation),
                "training": _ref(TRAINING_PATH, training),
                "t20_10": _ref(T20_10_PATH, t20_10),
                "checkpoint_sha256": checkpoint_sha256,
                "episode_file_sha256": episode_entry["episode_file_sha256"],
            },
            "processor_evidence": processor_evidence,
            "frame_zero_preflight": {
                "canonical_action_mujoco_rad": preflight_action.tolist(),
                "oracle_absolute_error_rad": preflight_error.tolist(),
                "measured_non_gripper_mae_rad": measured_arm,
                "expected_non_gripper_mae_rad": 0.030880688091355503,
                "non_gripper_tolerance_margin_rad": arm_margin,
                "measured_gripper_error_rad": measured_gripper,
                "expected_gripper_error_rad": expected_gripper,
                "gripper_tolerance_margin_rad": gripper_margin,
                "source_ablation_checkpoint_dataset_arm_mae_rad": expected_arm,
                "passed": True,
            },
            "action_error_diagnostics": diagnostics,
            "closed_loop": rollout,
            "coordinate_conversion": {
                "model_call_count": len(conversion_roundtrip_errors),
                "maximum_lerobot_roundtrip_error": max_roundtrip,
                "clipped_or_projected_call_count": sum(
                    value > 1e-6 for value in conversion_roundtrip_errors
                ),
            },
            "runtime": {
                "python": sys.version.split()[0],
                "torch": torch.__version__,
                "device": "mps",
                "dtype": "float32",
                "offline": True,
                "inference_seed": INFERENCE_SEED,
                "action_horizon": 5,
                "queue_refill_count": _replan_count(rollout["frame_count"]),
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
    _verify(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print(
        payload["identity_sha256"],
        rollout["simulation_semantic_strict_success"],
        rollout["maximum_anchor_lift_m"],
        diagnostics["initial_gripper_absolute_error_rad"],
    )
    return 0


def _processor_evidence(
    checkpoint_pre,
    checkpoint_post,
    hybrid_post,
    checkpoint_stats,
    hybrid_stats,
    dataset_stats,
) -> dict:
    if (
        type(checkpoint_pre.steps[2]).__name__ != "NormalizerProcessorStep"
        or type(checkpoint_post.steps[0]).__name__ != "UnnormalizerProcessorStep"
        or type(hybrid_post.steps[0]).__name__ != "UnnormalizerProcessorStep"
    ):
        raise ValueError("T20.16 processor step identity drifted")
    for statistic in ("mean", "std"):
        if (
            hybrid_stats[statistic][:5] != checkpoint_stats[statistic][:5]
            or hybrid_stats[statistic][5] != dataset_stats[statistic][5]
        ):
            raise ValueError("T20.16 hybrid statistics drifted")
    return {
        "checkpoint_state_preprocessor_unchanged": True,
        "checkpoint_arm_action_statistics_unchanged": True,
        "dataset_gripper_mean_std_substituted": True,
        "checkpoint_action_statistics_sha256": _stats_sha(checkpoint_stats),
        "hybrid_action_statistics_sha256": _stats_sha(hybrid_stats),
        "dataset_action_statistics_sha256": _stats_sha(dataset_stats),
        "gripper_index": 5,
    }


def _verify(payload: dict) -> None:
    verify_signed_payload(payload, label="T20.16 hybrid rollout")
    rollout = payload.get("closed_loop", {})
    verify_signed_payload(rollout, label="T20.16 nested rollout")
    validate_rendered_keyframes(rollout.get("rendered_keyframes"))
    if (
        payload.get("task_id") != "T20.16"
        or payload.get("frame_zero_preflight", {}).get("passed") is not True
        or rollout.get("frame_count") != 244
        or rollout.get("projected_action_frame_count") != 0
        or rollout.get("active_assist_frame_count") != 0
        or payload.get("model_inference_executed") is not True
        or payload.get("optimizer_training") is not False
        or payload.get("simulation_policy_accepted") is not False
        or payload.get("physical_actuation") is not False
        or payload.get("external_compute_started") is not False
        or payload.get("brev_compute_started") is not False
    ):
        raise ValueError("T20.16 hybrid rollout contract drifted")


def _check(path: Path) -> None:
    payload = load_strict_json(path)
    _verify(payload)
    expected = {
        "plan": PLAN_PATH,
        "normalizer": NORMALIZER_PATH,
        "ablation": ABLATION_PATH,
        "training": TRAINING_PATH,
        "t20_10": T20_10_PATH,
    }
    for source_id, source_path in expected.items():
        reference = payload["sources"][source_id]
        if reference["path"] != _relative(source_path) or reference[
            "file_sha256"
        ] != _sha(source_path):
            raise ValueError(f"T20.16 source drifted: {source_id}")
    print("verified", _relative(path), payload["identity_sha256"])


def _decode(value: dict) -> np.ndarray:
    import base64
    import io

    from PIL import Image

    raw = base64.b64decode(value["png_base64"], validate=True)
    if hashlib.sha256(raw).hexdigest() != value["image_sha256"]:
        raise ValueError("T20.16 source image hash drifted")
    return np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"), dtype=np.uint8).copy()


def _load_signed(path: Path, label: str) -> dict:
    payload = load_strict_json(path)
    verify_signed_payload(payload, label=label)
    return payload


def _ref(path: Path, payload: dict) -> dict:
    return {
        "path": _relative(path),
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": _sha(path),
    }


def _stats_sha(value) -> str:
    return hashlib.sha256(canonical_json_bytes(_jsonable(value))).hexdigest()


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
