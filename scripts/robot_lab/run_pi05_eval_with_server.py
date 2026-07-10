#!/usr/bin/env python3
"""Evaluate one PI0.5 checkpoint with a temporary local MPS policy service."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time

from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.so101_coordinates import (
    BODY_JOINT_OFFSETS_DEG,
    BODY_JOINT_SIGNS,
)


DEFAULT_CAMERA_MAP = (
    '{"observation.images.base_0_rgb":"overhead",'
    '"observation.images.left_wrist_0_rgb":"wrist",'
    '"observation.images.right_wrist_0_rgb":"empty"}'
)
DEFAULT_HOME = "[0.050438,-1.697719,1.549157,1.059675,-0.053182,1.6]"
DEFAULT_SIGNS = json.dumps(BODY_JOINT_SIGNS)
DEFAULT_OFFSETS = json.dumps(BODY_JOINT_OFFSETS_DEG)


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    if args.episodes <= 0 or args.max_policy_steps <= 0:
        parser.error("--episodes and --max-policy-steps must be positive")
    if _status_ready(args.policy_port, timeout_s=0.25):
        parser.error(f"Policy port {args.policy_port} is already in use")

    server_log = args.server_log or args.output_dir / "policy-server.log"
    server_log.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("HF_HUB_OFFLINE", "1")
    env.setdefault("TRANSFORMERS_OFFLINE", "1")
    env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    process = None
    with server_log.open("wb") as log_handle:
        try:
            process = subprocess.Popen(
                _server_argv(args),
                cwd=REPO_ROOT,
                env=env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            _wait_for_server(process, args.policy_port, args.server_ready_timeout)
            completed = subprocess.run(
                _evaluation_argv(args),
                cwd=REPO_ROOT,
                env=env,
                timeout=args.evaluation_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print("PI0.5 evaluation exceeded its timeout", file=sys.stderr)
            return 124
        finally:
            if process is not None:
                _stop_process_group(process)

    batch_path = args.output_dir / "intervention_batch_summary.json"
    if not batch_path.is_file():
        print(f"Evaluation did not write {batch_path}", file=sys.stderr)
        return completed.returncode if "completed" in locals() else 1
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    if int(batch.get("episodes") or 0) != args.episodes:
        print("Evaluation batch is incomplete", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "complete",
                "task_status": batch.get("status"),
                "episodes": batch.get("episodes"),
                "batch_summary": str(batch_path),
                "policy_repo": args.policy_repo,
                "device": args.device,
                "grasp_assist_mode": args.grasp_assist_mode,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if args.require_task_success and batch.get("status") != "pass":
        return 1
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-repo", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--episodes", type=int, required=True)
    parser.add_argument("--device", default="mps")
    parser.add_argument("--policy-port", type=int, default=8840)
    parser.add_argument("--num-steps", type=int, default=10)
    parser.add_argument("--action-horizon", type=int, default=15)
    parser.add_argument("--max-policy-steps", type=int, default=6000)
    parser.add_argument("--control-hz", type=int, default=30)
    parser.add_argument("--precontact-stall-steps", type=int, default=240)
    parser.add_argument("--precontact-min-progress-m", type=float, default=0.005)
    parser.add_argument("--precontact-contact-distance-m", type=float, default=0.05)
    parser.add_argument(
        "--grasp-assist-mode",
        choices=(
            "none",
            "policy_gripper",
            "contact_reflex",
            "policy_gripper_tray_release",
            "policy_gripper_tray_transfer",
        ),
        default="policy_gripper",
    )
    parser.add_argument("--server-python", default="external/leLab/.venv/bin/python")
    parser.add_argument("--mujoco-python", default="./.mujoco_venv/bin/python")
    parser.add_argument("--server-log", type=Path)
    parser.add_argument("--server-ready-timeout", type=float, default=300.0)
    parser.add_argument("--evaluation-timeout", type=float, default=21600.0)
    parser.add_argument("--require-task-success", action="store_true")
    return parser


def _server_argv(args: argparse.Namespace) -> list[str]:
    return [
        args.server_python,
        "scripts/robot_lab/local_policy_action_server.py",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.policy_port),
        "--policy-repo",
        args.policy_repo,
        "--device",
        args.device,
        "--num-steps",
        str(args.num_steps),
        "--action-horizon",
        str(args.action_horizon),
        "--camera-map",
        DEFAULT_CAMERA_MAP,
        "--simulation-home",
        DEFAULT_HOME,
        "--body-joint-signs",
        DEFAULT_SIGNS,
        "--body-joint-offsets-deg",
        DEFAULT_OFFSETS,
    ]


def _evaluation_argv(args: argparse.Namespace) -> list[str]:
    return [
        args.mujoco_python,
        "scripts/robot_lab/run_randomized_intervention_eval.py",
        "--output-dir",
        str(args.output_dir),
        "--seed",
        str(args.seed),
        "--episodes",
        str(args.episodes),
        "--correction-source",
        "none",
        "--policy-source",
        "http",
        "--policy-url",
        f"http://127.0.0.1:{args.policy_port}",
        "--max-policy-steps",
        str(args.max_policy_steps),
        "--grasp-assist-mode",
        args.grasp_assist_mode,
        "--control-hz",
        str(args.control_hz),
        "--precontact-stall-steps",
        str(args.precontact_stall_steps),
        "--precontact-min-progress-m",
        str(args.precontact_min_progress_m),
        "--precontact-contact-distance-m",
        str(args.precontact_contact_distance_m),
    ]


def _wait_for_server(process: subprocess.Popen, port: int, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Policy server exited early with code {process.returncode}")
        if _status_ready(port, timeout_s=0.5):
            return
        time.sleep(0.25)
    raise TimeoutError(f"Policy server was not ready within {timeout_s} seconds")


def _status_ready(port: int, *, timeout_s: float) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/status", timeout=timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return bool(payload.get("ok") and payload.get("ready"))
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return False


def _stop_process_group(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
