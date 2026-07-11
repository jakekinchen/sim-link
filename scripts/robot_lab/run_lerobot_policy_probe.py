#!/usr/bin/env python3
"""Run one local LeRobot VLA inference from a SceneSmith SO-101 workcell."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback

from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "robot_lab" / "so101_desk_cube_sort"
DEFAULT_POLICY_REPOS = (
    "lerobot/MolmoAct2-SO100_101-LeRobot",
    "lerobot/smolvla_base",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--policy-repo",
        action="append",
        dest="policy_repos",
        help="Policy repo to try. May be repeated. Defaults to MolmoAct2 then SmolVLA.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Torch device. Use auto to try mps before cpu when available.",
    )
    parser.add_argument(
        "--num-steps",
        type=int,
        default=4,
        help="Small inference-step cap for policies that expose a sampling step count.",
    )
    parser.add_argument(
        "--camera-map",
        help="JSON mapping policy image keys to base, wrist, overhead, or empty.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Probe JSON path. Defaults to <output-dir>/lerobot/policy_probe.json.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Do not download missing Hub files. Useful for fast cache checks.",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(REPO_ROOT))
    from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack

    stack_identity = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")

    output_json = args.output_json or args.output_dir / "lerobot" / "policy_probe.json"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()

    report: dict[str, Any] = {
        "status": "fail",
        "scene_json": str(args.scene_json),
        "output_dir": str(args.output_dir),
        "policy_repos": list(args.policy_repos or DEFAULT_POLICY_REPOS),
        "attempts": [],
        "lerobot_stack_identity_sha256": stack_identity["identity_sha256"],
    }

    try:
        scene = json.loads(args.scene_json.read_text(encoding="utf-8"))
        observation_spec = _build_observation_spec(scene, args.output_dir)
    except Exception as exc:  # noqa: BLE001
        report["error"] = f"Failed to build SceneSmith observation: {exc}"
        report["traceback"] = traceback.format_exc(limit=20)
        _write_report(output_json, report, started)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    for repo_id in report["policy_repos"]:
        for device in _device_candidates(args.device):
            attempt = _run_attempt(
                repo_id=repo_id,
                device=device,
                scene=scene,
                observation_spec=observation_spec,
                num_steps=args.num_steps,
                local_files_only=args.local_files_only,
                camera_map=_parse_camera_map(args.camera_map),
            )
            report["attempts"].append(attempt)
            if attempt["status"] == "pass":
                report["status"] = "pass"
                report["selected_policy"] = {
                    "repo_id": repo_id,
                    "policy_type": attempt.get("policy_type"),
                    "device": device,
                    "action": attempt.get("postprocessed_action"),
                    "action_degrees": attempt.get("postprocessed_action_degrees"),
                    "action_radians_clamped": attempt.get(
                        "postprocessed_action_radians_clamped"
                    ),
                    "raw_action": attempt.get("raw_action"),
                    "latency_s": attempt.get("latency_s"),
                }
                _write_report(output_json, report, started)
                print(json.dumps(report, indent=2, sort_keys=True))
                return 0

    report["error"] = "No local LeRobot policy attempt produced an action."
    _write_report(output_json, report, started)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1


def _run_attempt(
    *,
    repo_id: str,
    device: str,
    scene: dict[str, Any],
    observation_spec: dict[str, Any],
    num_steps: int,
    local_files_only: bool,
    camera_map: dict[str, str],
) -> dict[str, Any]:
    started = time.time()
    attempt: dict[str, Any] = {
        "repo_id": repo_id,
        "device": device,
        "status": "fail",
        "input_image_paths": observation_spec["image_paths"],
        "input_image_roles": observation_spec["image_roles"],
        "state_units": "degrees",
        "task": scene["policy"]["task"],
    }

    try:
        import torch
        from lerobot.configs import PreTrainedConfig
        from lerobot.policies import get_policy_class, make_pre_post_processors
        from lerobot.policies.utils import prepare_observation_for_inference

        # Register policy-specific processor steps before loading serialized pipelines.
        import lerobot.policies.molmoact2.processor_molmoact2  # noqa: F401
        import lerobot.policies.pi0.processor_pi0  # noqa: F401
        import lerobot.policies.pi05.processor_pi05  # noqa: F401
        import lerobot.policies.smolvla.processor_smolvla  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        attempt["error"] = f"LeRobot imports failed: {exc}"
        attempt["traceback"] = traceback.format_exc(limit=20)
        attempt["latency_s"] = round(time.time() - started, 3)
        return attempt

    try:
        torch_device = torch.device(device)
        if device == "mps":
            os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        cfg = PreTrainedConfig.from_pretrained(
            repo_id,
            local_files_only=local_files_only,
        )
        cfg.device = device
        cfg.use_amp = False
        if hasattr(cfg, "enable_inference_cuda_graph"):
            cfg.enable_inference_cuda_graph = False
        if hasattr(cfg, "num_inference_steps"):
            current_num_inference_steps = getattr(cfg, "num_inference_steps")
            cfg.num_inference_steps = (
                num_steps
                if current_num_inference_steps is None
                else min(int(current_num_inference_steps), num_steps)
            )
        if hasattr(cfg, "num_steps"):
            current_num_steps = getattr(cfg, "num_steps")
            cfg.num_steps = (
                num_steps if current_num_steps is None else min(int(current_num_steps), num_steps)
            )

        policy_type = cfg.type
        attempt["policy_type"] = policy_type
        attempt["input_features"] = sorted((cfg.input_features or {}).keys())
        attempt["output_features"] = sorted((cfg.output_features or {}).keys())
        checkpoint_status = _checkpoint_cache_status(repo_id)
        if checkpoint_status is not None:
            attempt["checkpoint_cache"] = checkpoint_status

        policy_cls = get_policy_class(policy_type)
        policy = policy_cls.from_pretrained(
            repo_id,
            config=cfg,
            local_files_only=local_files_only,
        )
        policy = policy.to(torch_device).eval()
        if hasattr(policy, "reset"):
            policy.reset()

        preprocessor, postprocessor = make_pre_post_processors(
            policy_cfg=cfg,
            pretrained_path=repo_id,
            pretrained_revision=getattr(cfg, "pretrained_revision", None),
            preprocessor_overrides={"device_processor": {"device": device}},
            postprocessor_overrides={"device_processor": {"device": "cpu"}},
        )

        raw_observation = _raw_observation_for_policy(
            policy_type,
            observation_spec,
            cfg.input_features or {},
            camera_map,
            _preprocessor_state_dim(
                preprocessor,
                _feature_shape_dim(
                    (cfg.input_features or {}).get("observation.state"), fallback=32
                ),
            ),
        )
        prepared = prepare_observation_for_inference(
            raw_observation,
            torch_device,
            task=scene["policy"]["task"],
            robot_type="so101_follower",
        )
        processed = preprocessor(prepared)

        inference_started = time.time()
        with torch.inference_mode():
            raw_action = policy.select_action(processed)
            postprocessed_action = postprocessor(raw_action)
        inference_latency = time.time() - inference_started

        raw_action_np = _tensor_to_float_list(raw_action)
        postprocessed_action_np = _tensor_to_float_list(postprocessed_action)
        attempt.update(
            {
                "status": "pass",
                "latency_s": round(time.time() - started, 3),
                "inference_latency_s": round(inference_latency, 3),
                "raw_action_shape": list(raw_action.shape),
                "postprocessed_action_shape": list(postprocessed_action.shape),
                "raw_action": raw_action_np,
                "postprocessed_action": postprocessed_action_np,
                "postprocessed_action_degrees": postprocessed_action_np,
                "postprocessed_action_radians_clamped": _degrees_to_mujoco_radians(
                    postprocessed_action_np
                ),
            }
        )
        return attempt
    except Exception as exc:  # noqa: BLE001
        attempt["error"] = str(exc)
        attempt["traceback"] = traceback.format_exc(limit=30)
        attempt["latency_s"] = round(time.time() - started, 3)
        return attempt


def _device_candidates(device: str) -> list[str]:
    if device != "auto":
        return [device]
    try:
        import torch

        if torch.backends.mps.is_available():
            return ["mps", "cpu"]
    except Exception:  # noqa: BLE001
        pass
    return ["cpu"]


def _build_observation_spec(scene: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    role_paths = _resolve_camera_observation_paths(output_dir)

    robot = scene["robot"]
    joint_rad = [
        float(value)
        for _, value in robot.get("default_urdf_joint_positions_rad", [])
    ]
    if len(joint_rad) != 6:
        joint_rad = [0.0, -0.55, 1.05, -0.48, 0.0, 0.35]
    state_degrees = np.asarray(
        [
            math.degrees(joint_rad[0]),
            -math.degrees(joint_rad[1]),
            *[math.degrees(value) for value in joint_rad[2:5]],
            _mujoco_gripper_to_percent(joint_rad[5]),
        ],
        dtype=np.float32,
    )
    return {
        "image_paths": {role: str(path) for role, path in role_paths.items()},
        "image_roles": list(role_paths),
        "images": {role: _load_rgb(path) for role, path in role_paths.items()},
        "state_degrees": state_degrees,
    }


def _resolve_camera_observation_paths(output_dir: Path) -> dict[str, Path]:
    candidates = {
        "base": [
            output_dir / "mujoco" / "render-cam0-side.png",
            output_dir / "policy_run_pi05_probe" / "policy_final_side.png",
            output_dir / "episodes" / "episode-0001" / "policy_final_side.png",
        ],
        "wrist": [
            output_dir / "mujoco" / "render-cam2-wrist.png",
            output_dir / "policy_run_pi05_probe" / "policy_final_wrist.png",
            output_dir / "episodes" / "episode-0001" / "policy_final_wrist.png",
        ],
        "overhead": [
            output_dir / "mujoco" / "render-cam1-overhead.png",
            output_dir / "policy_run_pi05_probe" / "policy_final_overhead.png",
            output_dir / "episodes" / "episode-0001" / "policy_final_overhead.png",
        ],
    }
    resolved: dict[str, Path] = {}
    missing: dict[str, list[str]] = {}
    for role, paths in candidates.items():
        path = next((candidate for candidate in paths if candidate.exists()), None)
        if path is None:
            missing[role] = [str(candidate) for candidate in paths]
        else:
            resolved[role] = path
    if missing:
        raise FileNotFoundError(
            "Missing rendered camera observations. Render cam0_side, cam1_overhead, "
            f"and cam2_wrist before policy probing. Missing candidates: {missing}"
        )
    return resolved


def _load_rgb(path: Path) -> np.ndarray:
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise SystemExit("Pillow is required in the LeRobot environment for PNG loading.") from exc

    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def _raw_observation_for_policy(
    policy_type: str,
    observation_spec: dict[str, Any],
    input_features: dict[str, Any],
    camera_map: dict[str, str] | None = None,
    state_dim: int | None = None,
) -> dict[str, np.ndarray]:
    images = observation_spec["images"]
    state = observation_spec["state_degrees"].copy()
    if policy_type == "molmoact2":
        return {
            "observation.images.cam0": images["base"].copy(),
            "observation.images.cam1": images["overhead"].copy(),
            "observation.state": state,
        }
    if policy_type == "smolvla":
        return {
            "observation.images.camera1": images["base"].copy(),
            "observation.images.camera2": images["wrist"].copy(),
            "observation.images.camera3": images["overhead"].copy(),
            # The current smolvla_base processor stats still reference legacy keys.
            "observation.image": images["base"].copy(),
            "observation.image2": images["wrist"].copy(),
            "observation.image3": images["overhead"].copy(),
            "observation.state": state,
        }
    if policy_type in {"pi0", "pi05"}:
        observation: dict[str, np.ndarray] = {}
        image_keys = [
            key
            for key, feature in input_features.items()
            if key.startswith("observation.images.")
            and str(getattr(feature, "type", "")).endswith("VISUAL")
        ]
        if not image_keys:
            image_keys = [key for key in input_features if key.startswith("observation.images.")]
        fallback_order = [images["base"], images["wrist"], images["overhead"]]
        for index, key in enumerate(sorted(image_keys)):
            role = (camera_map or {}).get(key) or _camera_role_for_feature_key(key)
            if role == "empty":
                observation[key] = np.zeros_like(fallback_order[0])
            elif role:
                observation[key] = images[role].copy()
            else:
                observation[key] = fallback_order[min(index, len(fallback_order) - 1)].copy()
        raw_state_dim = state_dim or _feature_shape_dim(
            input_features.get("observation.state"), fallback=32
        )
        observation["observation.state"] = _pad_state(state, raw_state_dim)
        return observation
    return {
        "observation.images.cam0": images["base"].copy(),
        "observation.images.cam1": images["overhead"].copy(),
        "observation.state": state,
    }


def _camera_role_for_feature_key(key: str) -> str | None:
    name = key.rsplit(".", 1)[-1].lower()
    if "wrist" in name:
        return "wrist" if "left_wrist" in name or "right_wrist" not in name else "overhead"
    if any(token in name for token in ("top", "up", "overhead")):
        return "overhead"
    if name == "left":
        return "base"
    if any(token in name for token in ("base", "front", "side")):
        return "base"
    return None


def _parse_camera_map(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("camera_map must be a JSON object")
    allowed = {"base", "wrist", "overhead", "empty"}
    result = {str(key): str(role) for key, role in payload.items()}
    invalid = {key: role for key, role in result.items() if role not in allowed}
    if invalid:
        raise ValueError(f"camera_map contains invalid roles: {invalid}")
    return result


def _feature_shape_dim(feature: Any, *, fallback: int) -> int:
    shape = None
    if isinstance(feature, dict):
        shape = feature.get("shape")
    elif feature is not None:
        shape = getattr(feature, "shape", None)
    if shape:
        return int(shape[0])
    return fallback


def _preprocessor_state_dim(preprocessor: Any, fallback: int) -> int:
    for step in getattr(preprocessor, "steps", []):
        stats = getattr(step, "_tensor_stats", None)
        if not isinstance(stats, dict) or "observation.state" not in stats:
            continue
        state_stats = stats["observation.state"]
        for name in ("mean", "q50", "min", "max"):
            value = state_stats.get(name)
            if value is not None and hasattr(value, "numel"):
                return int(value.numel())
    return fallback


def _pad_state(state: np.ndarray, dim: int) -> np.ndarray:
    if len(state) == dim:
        return state.astype(np.float32, copy=True)
    padded = np.zeros((dim,), dtype=np.float32)
    n = min(len(state), dim)
    padded[:n] = state[:n]
    return padded


def _checkpoint_cache_status(repo_id: str) -> dict[str, Any] | None:
    try:
        from huggingface_hub import hf_hub_download

        path = Path(
            hf_hub_download(repo_id, "model.safetensors", local_files_only=True)
        )
    except Exception:
        return None
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
    }


def _tensor_to_float_list(value: Any) -> list[float]:
    if hasattr(value, "detach"):
        array = value.detach().cpu().float().numpy()
    else:
        array = np.asarray(value, dtype=np.float32)
    return [round(float(item), 6) for item in array.reshape(-1).tolist()]


def _degrees_to_mujoco_radians(values: list[float]) -> list[float]:
    if len(values) < 6:
        raise ValueError("Policy action must contain at least six values")
    limits = (
        (-1.91986, 1.91986),
        (-1.74533, 1.74533),
        (-1.69, 1.69),
        (-1.65806, 1.65806),
        (-2.74385, 2.84121),
    )
    body_degrees = [float(value) for value in values[:5]]
    body_degrees[1] *= -1.0
    body = [
        round(min(high, max(low, math.radians(value))), 6)
        for value, (low, high) in zip(body_degrees, limits, strict=True)
    ]
    low, high = (-0.17453, 1.74533)
    percent = min(100.0, max(0.0, float(values[5])))
    return [*body, round(low + (high - low) * percent / 100.0, 6)]


def _mujoco_gripper_to_percent(value: float) -> float:
    low, high = (-0.17453, 1.74533)
    return min(100.0, max(0.0, 100.0 * (float(value) - low) / (high - low)))


def _write_report(path: Path, report: dict[str, Any], started: float) -> None:
    report["duration_s"] = round(time.time() - started, 3)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
