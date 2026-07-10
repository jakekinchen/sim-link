#!/usr/bin/env python3
"""Serve a persistent local LeRobot policy for SceneSmith control loops."""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.so101_coordinates import (
    BODY_JOINT_OFFSETS_DEG,
    BODY_JOINT_SIGNS,
    lerobot_to_mujoco,
    mujoco_to_lerobot,
)


DEFAULT_POLICY = (
    REPO_ROOT
    / "outputs"
    / "robot_lab"
    / "so101_desk_cube_sort"
    / "train"
    / "pi05_smoke_physical_wrist_mps_1step"
    / "checkpoints"
    / "000001"
    / "pretrained_model"
)
DEFAULT_BODY_JOINT_SIGNS = BODY_JOINT_SIGNS
DEFAULT_BODY_JOINT_OFFSETS_DEG = BODY_JOINT_OFFSETS_DEG


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8833)
    parser.add_argument("--policy-repo", default=str(DEFAULT_POLICY))
    parser.add_argument("--device", default="mps")
    parser.add_argument("--num-steps", type=int, default=4)
    parser.add_argument(
        "--action-horizon",
        type=int,
        default=5,
        help="Maximum actions to execute before observing and replanning.",
    )
    parser.add_argument(
        "--camera-map",
        help=(
            "JSON object mapping policy image feature keys to base, wrist, overhead, "
            "or empty. Use this when a checkpoint renamed its training cameras."
        ),
    )
    parser.add_argument(
        "--simulation-home",
        help="JSON six-value MuJoCo control pose used to initialize neural evaluations.",
    )
    parser.add_argument(
        "--task-override",
        help="Use the checkpoint's exact training instruction instead of the scene prompt.",
    )
    parser.add_argument(
        "--body-joint-signs",
        default=json.dumps(DEFAULT_BODY_JOINT_SIGNS),
        help="JSON five-value raw-policy to MuJoCo joint sign map.",
    )
    parser.add_argument(
        "--body-joint-offsets-deg",
        default=json.dumps(DEFAULT_BODY_JOINT_OFFSETS_DEG),
        help="JSON five-value offsets in q_deg = raw_deg * sign + offset_deg.",
    )
    args = parser.parse_args()

    print(
        json.dumps(
            {
                "status": "loading",
                "policy_repo": args.policy_repo,
                "device": args.device,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    runtime = LocalPolicyRuntime(
        args.policy_repo,
        args.device,
        args.num_steps,
        args.action_horizon,
        _parse_camera_map(args.camera_map),
        _parse_six_values(args.simulation_home, "simulation_home"),
        args.task_override,
        _parse_five_values(args.body_joint_signs, "body_joint_signs"),
        _parse_five_values(args.body_joint_offsets_deg, "body_joint_offsets_deg"),
    )
    handler = _handler_factory(runtime)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        json.dumps(
            {
                "status": "serving",
                "url": f"http://{args.host}:{args.port}",
                **runtime.status(),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


class LocalPolicyRuntime:
    def __init__(
        self,
        repo_id: str,
        device: str,
        num_steps: int,
        action_horizon: int = 5,
        camera_map: dict[str, str] | None = None,
        simulation_home: list[float] | None = None,
        task_override: str | None = None,
        body_joint_signs: list[float] | None = None,
        body_joint_offsets_deg: list[float] | None = None,
    ):
        started = time.time()
        if device == "mps":
            os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        _add_lerobot_to_path()
        import torch
        from lerobot.configs import PreTrainedConfig
        from lerobot.policies import get_policy_class, make_pre_post_processors
        from lerobot.policies.utils import prepare_observation_for_inference

        import lerobot.policies.molmoact2.processor_molmoact2  # noqa: F401
        import lerobot.policies.pi0.processor_pi0  # noqa: F401
        import lerobot.policies.pi05.processor_pi05  # noqa: F401
        import lerobot.policies.smolvla.processor_smolvla  # noqa: F401

        cfg = PreTrainedConfig.from_pretrained(repo_id, local_files_only=True)
        cfg.device = device
        cfg.use_amp = False
        if hasattr(cfg, "enable_inference_cuda_graph"):
            cfg.enable_inference_cuda_graph = False
        for field in ("num_inference_steps", "num_steps"):
            if hasattr(cfg, field):
                current = getattr(cfg, field)
                setattr(cfg, field, num_steps if current is None else min(int(current), num_steps))
        _limit_action_horizon(cfg, action_horizon)

        self.repo_id = repo_id
        self.device = device
        self.policy_type = cfg.type
        self.input_features = cfg.input_features or {}
        self.action_horizon = int(getattr(cfg, "n_action_steps", 1))
        self.camera_map = camera_map or {}
        self.simulation_home = simulation_home
        self.task_override = task_override.strip() if task_override else None
        self.body_joint_signs = body_joint_signs or list(DEFAULT_BODY_JOINT_SIGNS)
        self.body_joint_offsets_deg = body_joint_offsets_deg or list(
            DEFAULT_BODY_JOINT_OFFSETS_DEG
        )
        self.torch = torch
        self.torch_device = torch.device(device)
        policy_cls = get_policy_class(self.policy_type)
        self.policy, self.peft_adapter = _load_policy_model(
            policy_cls,
            repo_id,
            cfg,
        )
        self.policy = self.policy.to(self.torch_device).eval()
        self.preprocessor, self.postprocessor = make_pre_post_processors(
            policy_cfg=cfg,
            pretrained_path=repo_id,
            pretrained_revision=getattr(cfg, "pretrained_revision", None),
            preprocessor_overrides={"device_processor": {"device": device}},
            postprocessor_overrides={"device_processor": {"device": "cpu"}},
        )
        self.state_dim = _preprocessor_state_dim(
            self.preprocessor,
            _feature_shape_dim(self.input_features.get("observation.state"), 32),
        )
        self.prepare_observation_for_inference = prepare_observation_for_inference
        self.lock = threading.Lock()
        self.loaded_at = time.time()
        self.load_duration_s = round(self.loaded_at - started, 3)
        self.reset()

    def reset(self, seed: int | None = None) -> None:
        with getattr(self, "lock", _NullLock()):
            if seed is not None:
                self.torch.manual_seed(int(seed))
            if hasattr(self.policy, "reset"):
                self.policy.reset()
            self.inference_seed = int(seed) if seed is not None else None
            self.action_requests = 0
            self.inference_replans = 0

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "policy_repo": self.repo_id,
            "policy_type": self.policy_type,
            "peft_adapter": self.peft_adapter,
            "device": self.device,
            "load_duration_s": self.load_duration_s,
            "input_features": sorted(self.input_features),
            "raw_state_dim": self.state_dim,
            "camera_map": self.camera_map,
            "simulation_home_mujoco": self.simulation_home,
            "task_override": self.task_override,
            "body_joint_signs": self.body_joint_signs,
            "body_joint_offsets_deg": self.body_joint_offsets_deg,
            "action_horizon": self.action_horizon,
            "action_requests": self.action_requests,
            "inference_replans": self.inference_replans,
            "inference_seed": self.inference_seed,
            "physical_follower_commanded": False,
        }

    def action(self, payload: dict[str, Any]) -> dict[str, Any]:
        started = time.time()
        images = {
            role: _load_rgb(Path(payload["images"][role]))
            for role in ("base", "wrist", "overhead")
        }
        state = _mujoco_state_to_lerobot(
            payload["state"],
            self.body_joint_signs,
            self.body_joint_offsets_deg,
        )
        raw_observation = _raw_observation_for_policy(
            self.policy_type,
            images,
            state,
            self.input_features,
            self.camera_map,
            self.state_dim,
        )
        prepared = self.prepare_observation_for_inference(
            raw_observation,
            self.torch_device,
            task=(
                self.task_override
                or str(payload.get("task") or "Sort each cube into its matching tray.")
            ),
            robot_type="so101_follower",
        )
        with self.lock, self.torch.inference_mode():
            replanned = self.action_requests % self.action_horizon == 0
            if replanned and self.action_requests > 0 and hasattr(self.policy, "reset"):
                self.policy.reset()
            processed = self.preprocessor(prepared)
            raw_action = self.policy.select_action(processed)
            postprocessed = self.postprocessor(raw_action)
            self.action_requests += 1
            if replanned:
                self.inference_replans += 1
        values = _tensor_to_float_list(postprocessed)
        return {
            "ok": True,
            "policy_repo": self.repo_id,
            "policy_type": self.policy_type,
            "device": self.device,
            "action_lerobot": values,
            "action_mujoco": _lerobot_action_to_mujoco(
                values,
                self.body_joint_signs,
                self.body_joint_offsets_deg,
            ),
            "action_horizon": self.action_horizon,
            "replanned": replanned,
            "action_request": self.action_requests,
            "inference_replans": self.inference_replans,
            "latency_s": round(time.time() - started, 6),
            "physical_follower_commanded": False,
        }


class _NullLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None


def _handler_factory(runtime: LocalPolicyRuntime):
    class PolicyHandler(BaseHTTPRequestHandler):
        server_version = "SceneSmithLocalPolicyActionServer/0.1"

        def do_GET(self) -> None:  # noqa: N802
            if self.path.rstrip("/") == "/status":
                self._send_json({"ok": True, **runtime.status()})
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            try:
                if self.path.rstrip("/") == "/reset":
                    payload = self._read_json_body()
                    runtime.reset(payload.get("seed"))
                    self._send_json({"ok": True, **runtime.status()})
                    return
                if self.path.rstrip("/") == "/action":
                    self._send_json(runtime.action(self._read_json_body()))
                    return
                self.send_error(HTTPStatus.NOT_FOUND)
            except Exception as exc:  # noqa: BLE001
                self._send_json(
                    {"ok": False, "error": str(exc)},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("content-length") or 0)
            if length <= 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def _send_json(self, payload: dict[str, Any], *, status=HTTPStatus.OK) -> None:
            body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            sys.stderr.write(f"[local-policy-action-server] {format % args}\n")

    return PolicyHandler


def _add_lerobot_to_path() -> None:
    source = REPO_ROOT / "external" / "lerobot" / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))


def _load_policy_model(policy_cls, repo_id: str, config):
    if not _has_cached_adapter_config(repo_id):
        return (
            policy_cls.from_pretrained(
                repo_id,
                config=config,
                local_files_only=True,
            ),
            False,
        )

    from peft import PeftConfig, PeftModel

    peft_config = PeftConfig.from_pretrained(repo_id, local_files_only=True)
    base_repo = peft_config.base_model_name_or_path
    if not base_repo:
        raise ValueError(f"PEFT checkpoint {repo_id} does not declare a base model")
    base_policy = policy_cls.from_pretrained(
        base_repo,
        config=config,
        local_files_only=True,
    )
    return (
        PeftModel.from_pretrained(
            base_policy,
            repo_id,
            config=peft_config,
            is_trainable=False,
            local_files_only=True,
        ),
        True,
    )


def _has_cached_adapter_config(repo_id: str) -> bool:
    path = Path(repo_id).expanduser()
    if path.is_dir():
        return (path / "adapter_config.json").is_file()
    try:
        from huggingface_hub import try_to_load_from_cache

        cached = try_to_load_from_cache(repo_id, "adapter_config.json")
    except (ImportError, ValueError):
        return False
    return isinstance(cached, str) and Path(cached).is_file()


def _load_rgb(path: Path) -> np.ndarray:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Observation image not found: {resolved}")
    with Image.open(resolved) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def _raw_observation_for_policy(
    policy_type,
    images,
    state,
    input_features,
    camera_map: dict[str, str] | None = None,
    state_dim: int | None = None,
):
    if policy_type in {"pi0", "pi05"}:
        observation: dict[str, np.ndarray] = {}
        image_keys = [key for key in input_features if key.startswith("observation.images.")]
        fallback = [images["base"], images["wrist"], images["overhead"]]
        for index, key in enumerate(sorted(image_keys)):
            role = (camera_map or {}).get(key) or _camera_role_for_feature_key(key)
            if role == "empty":
                observation[key] = np.zeros_like(fallback[0])
            else:
                observation[key] = (
                    images[role] if role else fallback[min(index, 2)]
                ).copy()
        raw_state_dim = state_dim or _feature_shape_dim(
            input_features.get("observation.state"), 32
        )
        observation["observation.state"] = _pad_state(state, raw_state_dim)
        return observation
    if policy_type == "smolvla":
        return {
            "observation.images.camera1": images["base"].copy(),
            "observation.images.camera2": images["wrist"].copy(),
            "observation.images.camera3": images["overhead"].copy(),
            "observation.image": images["base"].copy(),
            "observation.image2": images["wrist"].copy(),
            "observation.image3": images["overhead"].copy(),
            "observation.state": state,
        }
    raise ValueError(f"Unsupported persistent policy type: {policy_type}")


def _camera_role_for_feature_key(key: str) -> str | None:
    """Map common LeRobot camera names onto SceneSmith's three rendered views."""
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


def _parse_six_values(value: str | None, name: str) -> list[float] | None:
    if not value:
        return None
    payload = json.loads(value)
    if not isinstance(payload, list) or len(payload) != 6:
        raise ValueError(f"{name} must be a JSON list of six numbers")
    return [float(item) for item in payload]


def _parse_five_values(value: str, name: str) -> list[float]:
    payload = json.loads(value)
    if not isinstance(payload, list) or len(payload) != 5:
        raise ValueError(f"{name} must be a JSON list of five numbers")
    result = [float(item) for item in payload]
    if name == "body_joint_signs" and any(item == 0 for item in result):
        raise ValueError("body_joint_signs cannot contain zero")
    return result


def _limit_action_horizon(config: Any, action_horizon: int) -> None:
    if action_horizon <= 0:
        raise ValueError("action_horizon must be positive")
    if not hasattr(config, "n_action_steps"):
        return
    current = getattr(config, "n_action_steps")
    config.n_action_steps = (
        action_horizon if current is None else min(int(current), action_horizon)
    )


def _feature_shape_dim(feature: Any, fallback: int) -> int:
    shape = getattr(feature, "shape", None)
    if isinstance(feature, dict):
        shape = feature.get("shape")
    return int(shape[0]) if shape else fallback


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
    padded = np.zeros((dim,), dtype=np.float32)
    count = min(dim, len(state))
    padded[:count] = state[:count]
    return padded


def _mujoco_state_to_lerobot(
    values: list[float],
    signs: list[float] | tuple[float, ...] = DEFAULT_BODY_JOINT_SIGNS,
    offsets_deg: list[float] | tuple[float, ...] = DEFAULT_BODY_JOINT_OFFSETS_DEG,
) -> np.ndarray:
    return np.asarray(mujoco_to_lerobot(values, signs, offsets_deg), dtype=np.float32)


def _lerobot_action_to_mujoco(
    values: list[float],
    signs: list[float] | tuple[float, ...] = DEFAULT_BODY_JOINT_SIGNS,
    offsets_deg: list[float] | tuple[float, ...] = DEFAULT_BODY_JOINT_OFFSETS_DEG,
) -> list[float]:
    return lerobot_to_mujoco(values, signs, offsets_deg, round_digits=6)


def _tensor_to_float_list(value: Any) -> list[float]:
    if hasattr(value, "detach"):
        array = value.detach().cpu().float().numpy()
    else:
        array = np.asarray(value, dtype=np.float32)
    return [round(float(item), 6) for item in array.reshape(-1).tolist()]


if __name__ == "__main__":
    raise SystemExit(main())
