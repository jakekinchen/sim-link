#!/usr/bin/env python3
"""Serve a visual SceneSmith robot action server for SO-101 desk sorting."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time

from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.intervention_control import InterventionControlStore
from scenesmith.robot_lab.leader_arm_bridge import DEFAULT_LEADER_PORT

DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "robot_lab" / "so101_desk_cube_sort"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8822)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--mujoco-python",
        type=Path,
        default=REPO_ROOT / ".mujoco_venv" / "bin" / "python",
    )
    parser.add_argument(
        "--lerobot-python",
        type=Path,
        default=REPO_ROOT / "external" / "leLab" / ".venv" / "bin" / "python",
    )
    parser.add_argument("--policy-repo", default="lerobot/smolvla_base")
    parser.add_argument("--policy-device", default="mps")
    args = parser.parse_args()

    _ensure_scene_outputs(args.output_dir)
    mujoco_python = (
        args.mujoco_python
        if args.mujoco_python.is_absolute()
        else (Path.cwd() / args.mujoco_python).absolute()
    )
    lerobot_python = (
        args.lerobot_python
        if args.lerobot_python.is_absolute()
        else (Path.cwd() / args.lerobot_python).absolute()
    )
    handler = _handler_factory(
        args.output_dir.resolve(),
        mujoco_python,
        lerobot_python,
        args.policy_repo,
        args.policy_device,
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        json.dumps(
            {
                "status": "serving",
                "url": f"http://{args.host}:{args.port}/",
                "output_dir": str(args.output_dir.resolve()),
                "policy_repo": args.policy_repo,
                "policy_device": args.policy_device,
                "lerobot_python": str(lerobot_python),
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


def _ensure_scene_outputs(output_dir: Path) -> None:
    scene_json = output_dir / "scene.json"
    mujoco_xml = output_dir / "mujoco" / "scene.xml"
    viewer_urdf = output_dir / "viewer" / "so-101-urdf" / "urdf" / "so101_new_calib.urdf"
    fiducial_report = output_dir / "fiducials" / "apriltag_calibration_report.json"
    if (
        scene_json.exists()
        and mujoco_xml.exists()
        and viewer_urdf.exists()
        and fiducial_report.exists()
        and _scene_has_fiducials(scene_json)
    ):
        return
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "robot_lab" / "generate_so101_desk_sort.py"),
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
    )


def _scene_has_fiducials(scene_json: Path) -> bool:
    try:
        payload = json.loads(scene_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(payload.get("fiducials"))


def _served_path(output_dir: Path, path: Path) -> str:
    return "/" + path.resolve().relative_to(output_dir.resolve()).as_posix()


def _handler_factory(
    output_dir: Path,
    mujoco_python: Path,
    lerobot_python: Path,
    policy_repo: str,
    policy_device: str,
):
    class RobotActionHandler(SimpleHTTPRequestHandler):
        server_version = "SceneSmithRobotActionServer/0.1"
        episode_counter = 0
        intervention_lock = threading.Lock()
        intervention_control_path: Path | None = None
        intervention_progress_path: Path | None = None
        active_intervention_episode: str | None = None

        def translate_path(self, path: str) -> str:
            parsed = urlparse(path)
            clean_path = unquote(parsed.path.lstrip("/"))
            if not clean_path:
                return str(output_dir)
            return str((output_dir / clean_path).resolve())

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/action-server", "/action-server/"):
                self._send_html(ACTION_SERVER_HTML)
                return
            if parsed.path == "/api/status":
                self._send_json(self._status_payload())
                return
            if parsed.path == "/api/intervention/status":
                self._send_json(self._intervention_status_payload())
                return
            return super().do_GET()

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/intervention":
                self._update_intervention_control()
                return
            if parsed.path == "/api/randomized-episodes":
                self._run_randomized_intervention_episode()
                return
            if parsed.path != "/api/episodes":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            type(self).episode_counter += 1
            episode_id = f"episode-{type(self).episode_counter:04d}"
            started = time.time()
            episode_dir = output_dir / "episodes" / episode_id
            try:
                episode_dir.mkdir(parents=True, exist_ok=True)
                self._ensure_camera_renders()
                policy_probe_path = episode_dir / "neural_policy_probe.json"
                probe_env = os.environ.copy()
                probe_env.setdefault("HF_HUB_DISABLE_XET", "1")
                probe_env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
                subprocess.run(
                    [
                        str(lerobot_python),
                        str(
                            REPO_ROOT
                            / "scripts"
                            / "robot_lab"
                            / "run_lerobot_policy_probe.py"
                        ),
                        "--scene-json",
                        str(output_dir / "scene.json"),
                        "--output-dir",
                        str(output_dir),
                        "--policy-repo",
                        policy_repo,
                        "--device",
                        policy_device,
                        "--local-files-only",
                        "--output-json",
                        str(policy_probe_path),
                    ],
                    cwd=REPO_ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                    env=probe_env,
                )
                subprocess.run(
                    [
                        str(mujoco_python),
                        str(REPO_ROOT / "scripts" / "robot_lab" / "run_sort_policy.py"),
                        "--scene-json",
                        str(output_dir / "scene.json"),
                        "--xml",
                        str(output_dir / "mujoco" / "scene.xml"),
                        "--output-dir",
                        str(episode_dir),
                        "--policy-kind",
                        f"local_lerobot_{policy_repo.replace('/', '_')}_policy_backed_controller",
                        "--policy-probe-json",
                        str(policy_probe_path),
                    ],
                    cwd=REPO_ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                summary = json.loads((episode_dir / "policy_run_summary.json").read_text())
                trajectory = json.loads((episode_dir / "policy_trajectory.json").read_text())
                policy_probe = json.loads(policy_probe_path.read_text())
                payload = {
                    "ok": True,
                    "episode_id": episode_id,
                    "duration_s": round(time.time() - started, 3),
                    "mode": self._status_payload()["mode"],
                    "policy_probe": policy_probe,
                    "summary": summary,
                    "trajectory": trajectory,
                }
                self._send_json(payload)
            except subprocess.CalledProcessError as exc:
                self._send_json(
                    {
                        "ok": False,
                        "episode_id": episode_id,
                        "error": exc.stderr or exc.stdout or str(exc),
                    },
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

        def _run_randomized_intervention_episode(self) -> None:
            type(self).episode_counter += 1
            episode_id = f"randomized-{type(self).episode_counter:04d}"
            started = time.time()
            request_payload = self._read_json_body()
            seed = int(request_payload.get("seed") or 6204)
            episodes = max(1, min(20, int(request_payload.get("episodes") or 1)))
            force_failure = bool(request_payload.get("force_failure", False))
            correction_source = request_payload.get("correction_source") or "none"
            policy_source = request_payload.get("policy_source") or "http"
            grasp_assist_mode = (
                request_payload.get("grasp_assist_mode") or "policy_gripper"
            )
            if grasp_assist_mode not in {
                "policy_gripper",
                "contact_reflex",
                "policy_gripper_tray_release",
                "policy_gripper_tray_transfer",
            }:
                raise ValueError(f"Unknown grasp assist mode: {grasp_assist_mode}")
            policy_url = request_payload.get("policy_url") or "http://127.0.0.1:8833"
            max_policy_steps = max(
                1,
                min(10000, int(request_payload.get("max_policy_steps") or 6000)),
            )
            control_hz = max(1, min(60, int(request_payload.get("control_hz") or 30)))
            episode_root = output_dir / "intervention_episodes" / episode_id
            control_path = episode_root / "intervention_control.json"
            try:
                episode_root.mkdir(parents=True, exist_ok=True)
                control_store = InterventionControlStore(control_path)
                control_store.initialize(
                    armed=bool(request_payload.get("armed", False)),
                    source="action_server",
                )
                with type(self).intervention_lock:
                    type(self).intervention_control_path = control_path
                    type(self).intervention_progress_path = episode_root
                    type(self).active_intervention_episode = episode_id
                command = [
                    str(mujoco_python),
                    str(
                        REPO_ROOT
                        / "scripts"
                        / "robot_lab"
                        / "run_randomized_intervention_eval.py"
                    ),
                    "--scene-json",
                    str(output_dir / "scene.json"),
                    "--output-dir",
                    str(episode_root),
                    "--seed",
                    str(seed),
                    "--episodes",
                    str(episodes),
                    "--correction-source",
                    correction_source,
                    "--policy-source",
                    policy_source,
                    "--grasp-assist-mode",
                    grasp_assist_mode,
                    "--max-policy-steps",
                    str(max_policy_steps),
                    "--control-hz",
                    str(control_hz),
                    "--intervention-control",
                    str(control_path),
                ]
                if policy_source == "http":
                    command.extend(["--policy-url", policy_url])
                if force_failure:
                    command.append("--force-failure")
                if request_payload.get("leader_port"):
                    command.extend(["--leader-port", str(request_payload["leader_port"])])
                if request_payload.get("leader_config"):
                    command.extend(["--leader-config", str(request_payload["leader_config"])])
                if correction_source in {"physical_leader", "studio_leader"}:
                    command.append("--realtime")
                runner = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                batch_path = episode_root / "intervention_batch_summary.json"
                if not batch_path.exists():
                    raise RuntimeError(
                        f"intervention runner exited {runner.returncode} without a batch summary: "
                        f"{runner.stderr or runner.stdout}"
                    )
                batch_summary = json.loads(batch_path.read_text())
                expected_exit_code = 0 if batch_summary.get("status") == "pass" else 1
                if runner.returncode != expected_exit_code:
                    raise RuntimeError(
                        f"intervention runner exit {runner.returncode} disagrees with "
                        f"batch status {batch_summary.get('status')!r}: "
                        f"{runner.stderr or runner.stdout}"
                    )
                episode_payloads = []
                for result in batch_summary["results"]:
                    trajectory = json.loads(
                        Path(result["artifacts"]["trajectory"]).read_text()
                    )["frames"]
                    result_dir = Path(result["artifacts"]["summary"]).parent
                    episode_payloads.append(
                        {
                            "summary": result,
                            "trajectory": trajectory,
                            "camera_paths": {
                                "side": _served_path(
                                    output_dir, result_dir / "policy_final_side.png"
                                ),
                                "wrist": _served_path(
                                    output_dir, result_dir / "policy_final_wrist.png"
                                ),
                                "overhead": _served_path(
                                    output_dir, result_dir / "policy_final_overhead.png"
                                ),
                            },
                        }
                    )
                result = episode_payloads[-1]
                payload = {
                    "ok": True,
                    "runner_exit_code": runner.returncode,
                    "task_success": batch_summary.get("status") == "pass",
                    "episode_id": episode_id,
                    "duration_s": round(time.time() - started, 3),
                    "mode": "domain_randomized_intervention",
                    "summary": result["summary"],
                    "trajectory": result["trajectory"],
                    "camera_paths": result["camera_paths"],
                    "episodes": episode_payloads,
                    "batch_summary": batch_summary,
                    "randomization": {
                        "seed": seed,
                        "episodes": episodes,
                        "force_failure": force_failure,
                        "correction_source": correction_source,
                        "policy_source": policy_source,
                        "grasp_assist_mode": grasp_assist_mode,
                        "policy_url": policy_url if policy_source == "http" else None,
                        "max_policy_steps": max_policy_steps,
                        "control_hz": control_hz,
                    },
                }
                self._send_json(payload)
            except Exception as exc:
                error = (
                    exc.stderr or exc.stdout or str(exc)
                    if isinstance(exc, subprocess.CalledProcessError)
                    else str(exc)
                )
                self._send_json(
                    {
                        "ok": False,
                        "episode_id": episode_id,
                        "error": error,
                    },
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
            finally:
                try:
                    InterventionControlStore(control_path).update(
                        takeover=False,
                        source="action_server_complete",
                    )
                except OSError:
                    pass
                with type(self).intervention_lock:
                    type(self).active_intervention_episode = None

        def _update_intervention_control(self) -> None:
            request_payload = self._read_json_body()
            with type(self).intervention_lock:
                control_path = type(self).intervention_control_path
                episode_id = type(self).active_intervention_episode
            if control_path is None or episode_id is None:
                self._send_json(
                    {"ok": False, "error": "No randomized episode is active."},
                    status=HTTPStatus.CONFLICT,
                )
                return
            store = InterventionControlStore(control_path)
            current = store.read()
            armed = request_payload.get("armed")
            takeover = request_payload.get("takeover")
            next_armed = current.armed if armed is None else bool(armed)
            next_takeover = current.takeover if takeover is None else bool(takeover)
            if next_takeover and not next_armed:
                self._send_json(
                    {"ok": False, "error": "Arm intervention before takeover."},
                    status=HTTPStatus.CONFLICT,
                )
                return
            signal = store.update(
                armed=next_armed,
                takeover=next_takeover,
                source="browser_deadman",
            )
            self._send_json(
                {
                    "ok": True,
                    "episode_id": episode_id,
                    "deadman": self._deadman_payload(signal),
                }
            )

        def _intervention_status_payload(self) -> dict:
            with type(self).intervention_lock:
                control_path = type(self).intervention_control_path
                progress_root = type(self).intervention_progress_path
                episode_id = type(self).active_intervention_episode
            deadman = None
            if control_path is not None:
                deadman = self._deadman_payload(InterventionControlStore(control_path).read())

            progress = None
            progress_path = None
            if progress_root is not None:
                candidates = list(progress_root.glob("randomized-episode-*/intervention_progress.json"))
                if candidates:
                    progress_path = max(candidates, key=lambda path: path.stat().st_mtime)
            if progress_path is not None:
                try:
                    progress = json.loads(progress_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    progress = None
            if progress is not None and progress.get("camera_paths"):
                progress["served_camera_paths"] = {
                    role: _served_path(output_dir, progress_path.parent / relative)
                    for role, relative in progress["camera_paths"].items()
                }
            return {
                "ok": True,
                "active": episode_id is not None,
                "episode_id": episode_id,
                "deadman": deadman,
                "progress": progress,
                "physical_follower_commanded": False,
            }

        @staticmethod
        def _deadman_payload(signal) -> dict:
            return {
                "armed": signal.armed,
                "takeover": signal.takeover,
                "updated_at": signal.updated_at,
                "sequence": signal.sequence,
                "source": signal.source,
                "age_s": round(signal.age_s(), 6) if signal.updated_at else None,
                "fresh": signal.is_fresh(0.55),
            }

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("content-length") or 0)
            if length <= 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}

        def _status_payload(self) -> dict:
            mode = f"local_lerobot_policy_{policy_device}"
            return {
                "ok": True,
                "name": "SceneSmith SO-101 Robot Action Server",
                "policy_label": policy_repo,
                "policy_repo_id": policy_repo,
                "molmoact2_endpoint": os.environ.get("MOLMOACT2_ACTION_SERVER_URL"),
                "mode": mode,
                "mode_note": (
                    "The plus button runs a randomized contact-physics episode against "
                    "the persistent PI0.5 MPS policy. The scripted controller remains "
                    "available as an explicit diagnostic mode."
                ),
                "policy_device": policy_device,
                "lerobot_python": str(lerobot_python),
                "mujoco_python": str(mujoco_python),
                "randomized_intervention": {
                    "endpoint": "/api/randomized-episodes",
                    "control_endpoint": "/api/intervention",
                    "status_endpoint": "/api/intervention/status",
                    "policy_action_url": "http://127.0.0.1:8833",
                    "default_correction_source": "none",
                    "default_leader_port": DEFAULT_LEADER_PORT,
                    "deadman_timeout_s": 0.55,
                    "control_step_arbitration": True,
                    "physical_follower_commanded": False,
                },
                "fiducials": {
                    "enabled": True,
                    "calibration_report": "/fiducials/apriltag_calibration_report.json",
                    "policy_dependency": "none",
                },
                "scene_json": "/scene.json",
                "viewer_urdf": "/viewer/so-101-urdf/urdf/so101_new_calib.urdf",
                "cameras": {
                    "cam0": {"name": "cam0_side", "role": "base_side"},
                    "cam1": {"name": "cam1_overhead", "role": "overhead"},
                    "cam2": {"name": "cam2_wrist", "role": "wrist", "mount": "gripper"},
                },
            }

        def _ensure_camera_renders(self) -> None:
            render_targets = [
                ("cam0_side", output_dir / "mujoco" / "render-cam0-side.png"),
                ("cam1_overhead", output_dir / "mujoco" / "render-cam1-overhead.png"),
                ("cam2_wrist", output_dir / "mujoco" / "render-cam2-wrist.png"),
            ]
            missing = [(camera, path) for camera, path in render_targets if not path.exists()]
            for camera, path in missing:
                subprocess.run(
                    [
                        str(mujoco_python),
                        str(REPO_ROOT / "scripts" / "robot_lab" / "render_mujoco_scene.py"),
                        "--xml",
                        str(output_dir / "mujoco" / "scene.xml"),
                        "--camera",
                        camera,
                        "--width",
                        "640",
                        "--height",
                        "400",
                        "--output-png",
                        str(path),
                        "--output-json",
                        str(path.with_suffix(".json")),
                    ],
                    cwd=REPO_ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )

        def _send_html(self, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload: dict, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            sys.stderr.write(
                f"[robot-action-server] {self.address_string()} - {format % args}\n"
            )

    return RobotActionHandler


ACTION_SERVER_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SceneSmith SO-101 Action Server</title>
  <style>
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; font-family: Inter, Arial, sans-serif; background: #111418; color: #f7f8fb; }
    canvas { display: block; width: 100vw; height: 100vh; }
    .topbar { position: fixed; inset: 14px 14px auto 14px; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; pointer-events: none; }
    .panel { pointer-events: auto; background: rgba(17, 20, 24, 0.78); border: 1px solid rgba(255,255,255,0.16); backdrop-filter: blur(10px); padding: 12px 14px; max-width: min(560px, calc(100vw - 28px)); }
    .panel h1 { margin: 0 0 7px; font-size: 15px; line-height: 1.1; letter-spacing: 0; }
    .panel p { margin: 0; color: #d7dde7; font-size: 12px; line-height: 1.35; }
    .status { margin-top: 9px; display: flex; flex-wrap: wrap; gap: 7px; }
    .chip { display: inline-flex; align-items: center; gap: 6px; border: 1px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.06); padding: 5px 7px; font-size: 11px; color: #e5e9f0; }
    .dot { width: 7px; height: 7px; border-radius: 999px; background: #f1c232; }
    .dot.ready { background: #42d985; }
    .dot.busy { background: #66d9ff; }
    .dot.warn { background: #f1c232; }
    .controls { pointer-events: auto; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
    .control-row { display: flex; align-items: center; justify-content: flex-end; gap: 7px; width: min(520px, calc(100vw - 28px)); flex-wrap: wrap; }
    .small-control { height: 31px; border: 1px solid rgba(255,255,255,0.18); background: rgba(17, 20, 24, 0.78); color: #f7f8fb; padding: 0 8px; font-size: 12px; }
    .toggle { display: inline-flex; align-items: center; gap: 5px; border: 1px solid rgba(255,255,255,0.18); background: rgba(17, 20, 24, 0.78); padding: 7px 8px; font-size: 12px; white-space: nowrap; }
    .run-randomized { height: 31px; border: 1px solid rgba(255,255,255,0.22); background: #42d985; color: #07120c; padding: 0 10px; font-weight: 700; cursor: pointer; }
    .run-randomized:disabled { opacity: 0.48; cursor: progress; }
    .takeover { min-width: 152px; height: 38px; border: 1px solid rgba(255,255,255,0.24); background: #2d333b; color: #f7f8fb; padding: 0 12px; font-weight: 700; cursor: not-allowed; }
    .takeover.armed { background: #d84b3e; cursor: pointer; }
    .takeover.active { background: #f7d548; color: #16130a; }
    .plus { width: 54px; height: 54px; border: 1px solid rgba(255,255,255,0.24); border-radius: 999px; background: #f7d548; color: #16130a; font-size: 34px; line-height: 50px; cursor: pointer; box-shadow: 0 10px 26px rgba(0,0,0,0.34); }
    .plus:disabled { opacity: 0.45; cursor: progress; }
    .readout { min-width: 230px; text-align: right; background: rgba(17, 20, 24, 0.78); border: 1px solid rgba(255,255,255,0.16); padding: 10px 12px; font-size: 12px; color: #d9dee8; }
    .legend { position: fixed; left: 16px; bottom: 14px; display: flex; gap: 8px; flex-wrap: wrap; max-width: calc(100vw - 32px); }
    .legend span { display: inline-flex; align-items: center; gap: 6px; background: rgba(17, 20, 24, 0.72); border: 1px solid rgba(255,255,255,0.14); padding: 6px 8px; font-size: 12px; }
    .swatch { width: 11px; height: 11px; display: inline-block; }
    .camera-strip { position: fixed; right: 16px; bottom: 14px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; max-width: min(720px, calc(100vw - 32px)); pointer-events: none; }
    .camera-card { width: 154px; background: rgba(17, 20, 24, 0.78); border: 1px solid rgba(255,255,255,0.16); padding: 6px; }
    .camera-card img { display: block; width: 100%; aspect-ratio: 16 / 10; object-fit: cover; background: #0c0f13; }
    .camera-card span { display: block; margin-top: 5px; color: #e8edf4; font-size: 11px; line-height: 1.2; }
    @media (max-width: 900px) {
      .topbar { flex-direction: column; align-items: stretch; }
      .panel { max-width: calc(100vw - 104px); }
      .controls { width: calc(100vw - 28px); align-items: stretch; }
      .control-row { width: 100%; justify-content: flex-start; }
      .plus { position: fixed; top: 14px; right: 14px; z-index: 3; }
      .readout { min-width: 0; text-align: left; }
    }
  </style>
</head>
<body>
  <div class="topbar">
    <section class="panel">
      <h1>SceneSmith SO-101 Robot Action Server</h1>
      <p id="task">Loading workcell…</p>
      <div class="status">
        <span class="chip"><i id="serverDot" class="dot"></i><span id="serverMode">server pending</span></span>
        <span class="chip"><i id="robotDot" class="dot"></i><span id="robotMode">SO-101 pending</span></span>
        <span class="chip"><i id="episodeDot" class="dot"></i><span id="episodeMode">episode idle</span></span>
        <span class="chip"><i id="deadmanDot" class="dot warn"></i><span id="deadmanMode">intervention disarmed</span></span>
      </div>
    </section>
    <section class="controls">
      <button id="runEpisode" class="plus" title="Run one sorting episode" aria-label="Run one sorting episode">+</button>
      <div class="control-row">
        <input id="randomSeed" class="small-control" type="number" value="6204" min="0" step="1" title="Randomization seed" aria-label="Randomization seed" />
        <input id="batchSize" class="small-control" type="number" value="1" min="1" max="20" step="1" title="Episode batch size" aria-label="Episode batch size" />
        <select id="policySource" class="small-control" title="Policy source" aria-label="Policy source">
          <option value="http" selected>PI0.5 live</option>
          <option value="scripted">scripted proof</option>
        </select>
        <select id="graspAssistMode" class="small-control" title="Grasp mode" aria-label="Grasp mode">
          <option value="policy_gripper">policy jaw</option>
          <option value="policy_gripper_tray_release">policy jaw + tray release</option>
          <option value="policy_gripper_tray_transfer" selected>policy grasp + tray transfer</option>
          <option value="contact_reflex">contact reflex</option>
        </select>
        <input id="maxPolicySteps" class="small-control" type="number" value="6000" min="1" max="10000" step="1" title="Maximum neural policy steps" aria-label="Maximum neural policy steps" />
        <input id="controlHz" class="small-control" type="number" value="30" min="1" max="60" step="1" title="Policy control frequency" aria-label="Policy control frequency" />
        <select id="correctionSource" class="small-control" title="Correction source" aria-label="Correction source">
          <option value="none" selected>no correction</option>
          <option value="simulated_leader">sim leader</option>
          <option value="studio_leader">studio leader</option>
          <option value="physical_leader">physical leader</option>
        </select>
        <label class="toggle"><input id="forceFailure" type="checkbox" /> force fail</label>
        <button id="runRandomized" class="run-randomized" title="Run randomized intervention episode">randomized</button>
      </div>
      <div class="control-row">
        <input id="leaderPort" class="small-control" type="text" value="/dev/cu.usbmodem5B3D0448141" title="Physical leader serial port" aria-label="Physical leader serial port" />
        <input id="leaderConfig" class="small-control" type="text" value="leader_arm" title="Physical leader calibration config" aria-label="Physical leader calibration config" />
        <label class="toggle"><input id="armIntervention" type="checkbox" /> arm</label>
        <button id="holdTakeover" class="takeover" type="button" disabled>hold to intervene</button>
      </div>
      <div class="readout" id="readout">Ready.</div>
    </section>
  </div>
  <div class="legend" id="legend"></div>
  <div class="camera-strip" id="cameraStrip"></div>
  <script type="importmap">
    {
      "imports": {
        "three": "https://unpkg.com/three@0.177.0/build/three.module.js",
        "three/addons/": "https://unpkg.com/three@0.177.0/examples/jsm/",
        "three/examples/jsm/": "https://unpkg.com/three@0.177.0/examples/jsm/",
        "urdf-loader": "https://cdn.jsdelivr.net/npm/urdf-loader@0.12.7/src/URDFLoader.js"
      }
    }
  </script>
  <script type="module">
    import * as THREE from 'three';
    import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
    import URDFLoader from 'urdf-loader';

    THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
    const state = {
      sceneSpec: null,
      status: null,
      robotModel: null,
      cubes: new Map(),
      running: false,
      episodeCount: 0,
      animationDone: true,
      interventionPoll: null,
      deadmanHeartbeat: null,
      takeoverActive: false,
    };
    window.__SCENESMITH_ACTION_SERVER_READY = false;
    window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE = null;
    window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE = true;
    window.__SCENESMITH_INTERVENTION_STATUS = null;

    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x111418, 1);
    document.body.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111418);
    const camera = new THREE.PerspectiveCamera(43, window.innerWidth / window.innerHeight, 0.01, 10);
    camera.up.set(0, 0, 1);
    camera.position.set(0.72, -0.86, 0.72);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0.25, 0, 0.36);
    controls.enableDamping = true;

    scene.add(new THREE.HemisphereLight(0xffffff, 0x34383f, 1.2));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(0.4, -0.6, 1.4);
    scene.add(key);
    const root = new THREE.Group();
    scene.add(root);

    const [sceneSpec, status] = await Promise.all([
      fetch('/scene.json').then((r) => r.json()),
      fetch('/api/status').then((r) => r.json()),
    ]);
    state.sceneSpec = sceneSpec;
    state.status = status;
    window.__SCENESMITH_ROBOT_LAB_SCENE__ = sceneSpec;
    document.getElementById('task').textContent = sceneSpec.policy.task;
    updateServerStatus(status);

    addRoom(root, sceneSpec.room);
    addDesk(root, sceneSpec.desk);
    for (const fiducial of sceneSpec.fiducials || []) addFiducial(root, fiducial);
    for (const tray of sceneSpec.trays) addTray(root, tray);
    for (const cube of sceneSpec.cubes) addCube(root, cube);
    addLegend(sceneSpec);
    await addSO101Urdf(root, sceneSpec.robot);
    resetCubes();

    document.getElementById('runEpisode').addEventListener('click', runRandomizedEpisode);
    document.getElementById('runRandomized').addEventListener('click', runRandomizedEpisode);
    document.getElementById('armIntervention').addEventListener('change', onArmChanged);
    document.getElementById('correctionSource').addEventListener('change', updateTakeoverButton);
    document.getElementById('policySource').addEventListener('change', onPolicySourceChanged);
    const takeoverButton = document.getElementById('holdTakeover');
    takeoverButton.addEventListener('pointerdown', beginTakeover);
    takeoverButton.addEventListener('pointerup', endTakeover);
    takeoverButton.addEventListener('pointercancel', endTakeover);
    takeoverButton.addEventListener('lostpointercapture', endTakeover);
    window.addEventListener('pointerup', endTakeover);
    onPolicySourceChanged();
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    let frame = 0;
    function animate() {
      frame += 1;
      controls.update();
      renderer.render(scene, camera);
      window.__SCENESMITH_ACTION_SERVER_READY =
        frame > 2 && !!state.robotModel && (window.__SCENESMITH_SO101_URDF_SUMMARY?.meshObjectCount || 0) >= 10;
      requestAnimationFrame(animate);
    }
    animate();

    async function runEpisode() {
      if (state.running) return;
      state.running = true;
      state.animationDone = false;
      window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE = false;
      const button = document.getElementById('runEpisode');
      button.disabled = true;
      setEpisodeStatus('busy', 'running episode…');
      document.getElementById('readout').textContent = 'Calling /api/episodes…';
      resetCubes();
      try {
        const response = await fetch('/api/episodes', { method: 'POST' });
        const episode = await response.json();
        if (!response.ok || !episode.ok) throw new Error(episode.error || 'Episode failed');
        state.episodeCount += 1;
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE = episode;
        await animateTrajectory(episode.trajectory);
        updateCameraStrip(episode);
        const final = episode.summary.final_score;
        const policy = episode.summary.neural_policy?.selected_policy?.repo_id || 'policy';
        document.getElementById('readout').textContent =
          `${episode.episode_id}: ${policy} sorted ${final.sorted_count}/${final.total_count}`;
        setEpisodeStatus('ready', 'episode complete');
      } catch (error) {
        console.error(error);
        document.getElementById('readout').textContent = String(error);
        setEpisodeStatus('warn', 'episode failed');
      } finally {
        state.animationDone = true;
        state.running = false;
        button.disabled = false;
        window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE = true;
      }
    }

    async function runRandomizedEpisode() {
      if (state.running) return;
      state.running = true;
      state.animationDone = false;
      window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE = false;
      const button = document.getElementById('runRandomized');
      const plus = document.getElementById('runEpisode');
      button.disabled = true;
      plus.disabled = true;
      setEpisodeStatus('busy', 'running randomized intervention…');
      resetCubes();
      const seed = Number.parseInt(document.getElementById('randomSeed').value || '1000', 10);
      const correctionSource = document.getElementById('correctionSource').value;
      const policySource = document.getElementById('policySource').value;
      const graspAssistMode = document.getElementById('graspAssistMode').value;
      const maxPolicySteps = Math.max(1, Math.min(10000, Number.parseInt(document.getElementById('maxPolicySteps').value || '6000', 10)));
      const controlHz = Math.max(1, Math.min(60, Number.parseInt(document.getElementById('controlHz').value || '30', 10)));
      const forceFailure = document.getElementById('forceFailure').checked;
      const episodes = Math.max(1, Math.min(20, Number.parseInt(document.getElementById('batchSize').value || '1', 10)));
      const armed = document.getElementById('armIntervention').checked;
      updateTakeoverButton();
      startInterventionPolling();
      document.getElementById('readout').textContent = `Randomized seeds ${seed}–${seed + episodes - 1}: ${policySource}, ${graspAssistMode}, ${correctionSource}`;
      try {
        const response = await fetch('/api/randomized-episodes', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            seed,
            episodes,
            correction_source: correctionSource,
            policy_source: policySource,
            grasp_assist_mode: graspAssistMode,
            policy_url: 'http://127.0.0.1:8833',
            max_policy_steps: maxPolicySteps,
            control_hz: controlHz,
            force_failure: forceFailure,
            armed,
            leader_port: document.getElementById('leaderPort').value,
            leader_config: document.getElementById('leaderConfig').value,
          }),
        });
        const episode = await response.json();
        if (!response.ok || !episode.ok) throw new Error(episode.error || 'Randomized episode failed');
        window.__SCENESMITH_ACTION_SERVER_LAST_EPISODE = episode;
        for (const item of episode.episodes || [episode]) {
          await animateTrajectory(item.trajectory, 65);
          updateCameraStrip(item);
        }
        const final = episode.summary.final_score;
        const intervention = episode.summary.intervention;
        document.getElementById('readout').textContent =
          `${episode.episode_id}: ${episodes} episode${episodes === 1 ? '' : 's'}, final ${final.sorted_count}/${final.total_count}, intervention ${intervention.frames} frames`;
        if (episode.task_success) {
          setEpisodeStatus('ready', 'randomized batch complete');
        } else {
          setEpisodeStatus('warn', `episode complete: ${episode.summary.failure_reason || 'task failed'}`);
        }
        document.getElementById('randomSeed').value = String(seed + episodes);
      } catch (error) {
        console.error(error);
        document.getElementById('readout').textContent = String(error);
        setEpisodeStatus('warn', 'randomized episode failed');
      } finally {
        stopInterventionPolling();
        await endTakeover();
        state.animationDone = true;
        state.running = false;
        button.disabled = false;
        plus.disabled = false;
        updateTakeoverButton();
        window.__SCENESMITH_ACTION_SERVER_ANIMATION_DONE = true;
      }
    }

    async function onArmChanged() {
      updateTakeoverButton();
      if (!state.running) return;
      await postIntervention({
        armed: document.getElementById('armIntervention').checked,
        takeover: false,
      });
    }

    function onPolicySourceChanged() {
      const neural = document.getElementById('policySource').value === 'http';
      const correction = document.getElementById('correctionSource');
      if (neural && correction.value === 'simulated_leader') correction.value = 'none';
      const forceFailure = document.getElementById('forceFailure');
      if (neural) forceFailure.checked = false;
      forceFailure.disabled = neural;
      updateTakeoverButton();
    }

    function updateTakeoverButton() {
      const button = document.getElementById('holdTakeover');
      const armed = document.getElementById('armIntervention').checked;
      const physical = ['studio_leader', 'physical_leader'].includes(document.getElementById('correctionSource').value);
      const enabled = state.running && armed && physical;
      button.disabled = !enabled;
      button.className = `takeover${enabled ? ' armed' : ''}${state.takeoverActive ? ' active' : ''}`;
      button.textContent = state.takeoverActive ? 'intervening' : 'hold to intervene';
    }

    async function beginTakeover(event) {
      const button = document.getElementById('holdTakeover');
      if (button.disabled || state.takeoverActive) return;
      event.preventDefault();
      try { button.setPointerCapture(event.pointerId); } catch (_) {}
      state.takeoverActive = true;
      updateTakeoverButton();
      await postIntervention({ armed: true, takeover: true });
      clearInterval(state.deadmanHeartbeat);
      state.deadmanHeartbeat = setInterval(() => {
        void postIntervention({ armed: true, takeover: true });
      }, 180);
    }

    async function endTakeover() {
      if (!state.takeoverActive && !state.deadmanHeartbeat) return;
      state.takeoverActive = false;
      clearInterval(state.deadmanHeartbeat);
      state.deadmanHeartbeat = null;
      updateTakeoverButton();
      if (state.running) await postIntervention({ takeover: false });
    }

    async function postIntervention(payload) {
      try {
        const response = await fetch('/api/intervention', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (response.ok && result.ok) updateDeadmanUI(result.deadman);
        return result;
      } catch (_) {
        return null;
      }
    }

    function startInterventionPolling() {
      stopInterventionPolling();
      void pollInterventionStatus();
      state.interventionPoll = setInterval(() => void pollInterventionStatus(), 180);
    }

    function stopInterventionPolling() {
      clearInterval(state.interventionPoll);
      state.interventionPoll = null;
    }

    async function pollInterventionStatus() {
      try {
        const response = await fetch(`/api/intervention/status?t=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) return;
        const payload = await response.json();
        window.__SCENESMITH_INTERVENTION_STATUS = payload;
        if (payload.deadman) updateDeadmanUI(payload.deadman);
        const progress = payload.progress;
        if (!progress) return;
        const latest = progress.latest_frame;
        if (latest) {
          applyRobotControls(latest.executed_action || latest.robot_control || []);
          updateCubeStates(latest.transition?.next_cube_states || latest.observation?.cube_states || []);
        }
        if (progress.served_camera_paths) updateLiveCameraStrip(progress.served_camera_paths);
        if (progress.status === 'waiting_for_intervention') {
          setEpisodeStatus('warn', 'failure detected');
          document.getElementById('readout').textContent = 'Failure detected. Hold intervention to take control.';
        } else if (progress.phase) {
          setEpisodeStatus('busy', progress.phase.replaceAll('_', ' '));
        }
      } catch (_) {}
    }

    function updateDeadmanUI(deadman) {
      const dot = document.getElementById('deadmanDot');
      const mode = document.getElementById('deadmanMode');
      if (deadman?.takeover && deadman?.fresh) {
        dot.className = 'dot busy';
        mode.textContent = 'leader takeover';
      } else if (deadman?.armed) {
        dot.className = 'dot ready';
        mode.textContent = 'intervention armed';
      } else {
        dot.className = 'dot warn';
        mode.textContent = 'intervention disarmed';
      }
    }

    function updateCubeStates(cubeStates) {
      for (const cubeState of cubeStates) {
        const cube = state.cubes.get(cubeState.name);
        if (cube) cube.position.set(...cubeState.position_m);
      }
    }

    function updateLiveCameraStrip(paths) {
      updateCameraStrip({
        camera_paths: {
          side: paths.base,
          wrist: paths.wrist,
          overhead: paths.overhead,
        },
      });
    }

    async function animateTrajectory(trajectory, durationMs = 520) {
      for (const step of trajectory) {
        const cube = state.cubes.get(step.cube);
        if (!cube) continue;
        const start = cube.position.clone();
        const end = new THREE.Vector3(...step.cube_position_m);
        applyRobotControls(step.robot_control || []);
        await tween(durationMs, (t) => {
          cube.position.lerpVectors(start, end, smooth(t));
        });
      }
    }

    function resetCubes() {
      for (const cubeSpec of state.sceneSpec.cubes) {
        const cube = state.cubes.get(cubeSpec.name);
        if (cube) cube.position.set(...cubeSpec.initial_position_m);
      }
      applyRobotControls([0, -0.55, 1.05, -0.48, 0, 0.35]);
    }

    function applyRobotControls(values) {
      if (!state.robotModel || !values.length) return;
      const entries = state.sceneSpec.robot.joint_name_map || [];
      for (let index = 0; index < entries.length; index += 1) {
        const urdfName = entries[index][1];
        const value = values[index] ?? 0;
        if (typeof state.robotModel.setJointValue === 'function') state.robotModel.setJointValue(urdfName, value);
        else if (state.robotModel.joints?.[urdfName]?.setJointValue) state.robotModel.joints[urdfName].setJointValue(value);
      }
    }

    function tween(ms, apply) {
      const started = performance.now();
      return new Promise((resolve) => {
        function tick(now) {
          const t = Math.min(1, (now - started) / ms);
          apply(t);
          if (t < 1) requestAnimationFrame(tick);
          else resolve();
        }
        requestAnimationFrame(tick);
      });
    }

    function smooth(t) {
      return t * t * (3 - 2 * t);
    }

    function updateServerStatus(payload) {
      const mode = document.getElementById('serverMode');
      const dot = document.getElementById('serverDot');
      mode.textContent = `${payload.policy_label} on ${payload.policy_device}`;
      dot.className = 'dot ready';
    }

    function setEpisodeStatus(kind, text) {
      document.getElementById('episodeDot').className = `dot ${kind}`;
      document.getElementById('episodeMode').textContent = text;
    }

    function updateCameraStrip(episode) {
      const strip = document.getElementById('cameraStrip');
      const paths = episode.camera_paths || {
        side: `/episodes/${episode.episode_id}/policy_final_side.png`,
        wrist: `/episodes/${episode.episode_id}/policy_final_wrist.png`,
        overhead: `/episodes/${episode.episode_id}/policy_final_overhead.png`,
      };
      const views = [
        ['side', paths.side],
        ['wrist', paths.wrist],
        ['overhead', paths.overhead],
      ];
      strip.replaceChildren(...views.map(([label, src]) => {
        const card = document.createElement('figure');
        card.className = 'camera-card';
        const image = document.createElement('img');
        image.src = `${src}?t=${Date.now()}`;
        image.alt = `${label} camera`;
        image.dataset.cameraThumb = 'true';
        const caption = document.createElement('span');
        caption.textContent = label;
        card.append(image, caption);
        return card;
      }));
    }

    async function addSO101Urdf(parent, robotSpec) {
      const manager = new THREE.LoadingManager();
      const loader = new URDFLoader(manager);
      loader.packages = { so_arm_description: '/viewer/so-101-urdf' };
      loader.parseVisual = true;
      loader.parseCollision = false;
      return new Promise((resolve, reject) => {
        let model = null;
        manager.onLoad = () => {
          if (model) {
            state.robotModel = model;
            window.__SCENESMITH_SO101_URDF_SUMMARY = summarizeUrdfModel(model);
            window.__SCENESMITH_WRIST_CAMERA_VISUAL = addWristCameraVisual(model);
            document.getElementById('robotDot').className = 'dot ready';
            document.getElementById('robotMode').textContent = `SO-101 mesh ${window.__SCENESMITH_SO101_URDF_SUMMARY.meshObjectCount} objects`;
          }
          resolve();
        };
        manager.onError = (url) => reject(new Error(`Failed to load ${url}`));
        loader.load('/viewer/so-101-urdf/urdf/so101_new_calib.urdf', (robotModel) => {
          model = robotModel;
          robotModel.name = 'so101_real_urdf';
          robotModel.position.set(...robotSpec.base_position_m);
          parent.add(robotModel);
        }, undefined, reject);
      });
    }

    function addWristCameraVisual(robotModel) {
      const gripperLink = robotModel.links?.gripper || robotModel.getObjectByName('gripper');
      if (!gripperLink) return { added: false, reason: 'gripper link not found' };

      const group = new THREE.Group();
      group.name = 'scenesmith_wrist_camera';
      group.position.set(0.014, -0.0002, -0.078);
      group.quaternion.set(-0.452759, 0.4529, -0.519754, 0.565462);

      const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0x14171b, roughness: 0.58, metalness: 0.2 });
      const lensMaterial = new THREE.MeshStandardMaterial({ color: 0x05070a, roughness: 0.22, metalness: 0.55 });
      const glassMaterial = new THREE.MeshStandardMaterial({ color: 0x1b8cff, roughness: 0.12, metalness: 0.1, emissive: 0x042244, emissiveIntensity: 0.25 });

      const housing = new THREE.Mesh(new THREE.BoxGeometry(0.032, 0.024, 0.018), bodyMaterial);
      housing.name = 'wrist_camera_body_visual';
      group.add(housing);

      const mount = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.056, 0.008), bodyMaterial);
      mount.name = 'wrist_camera_mount_visual';
      mount.position.set(0, -0.034, 0.004);
      group.add(mount);

      const foot = new THREE.Mesh(new THREE.BoxGeometry(0.028, 0.016, 0.008), bodyMaterial);
      foot.name = 'wrist_camera_mount_foot_visual';
      foot.position.set(0, -0.064, 0.004);
      group.add(foot);

      const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.0055, 0.0055, 0.008, 28), lensMaterial);
      lens.name = 'wrist_camera_lens_visual';
      lens.rotation.x = Math.PI / 2;
      lens.position.set(0, 0, -0.011);
      group.add(lens);

      const glass = new THREE.Mesh(new THREE.CircleGeometry(0.0046, 28), glassMaterial);
      glass.name = 'wrist_camera_glass_visual';
      glass.position.set(0, 0, -0.0154);
      group.add(glass);

      gripperLink.add(group);
      return {
        added: true,
        parent: gripperLink.name || 'gripper',
        localPosition: [0.014, -0.0002, -0.078],
        localQuaternionWxyz: [0.565462, -0.452759, 0.4529, -0.519754],
        opticalAxis: '-Z',
      };
    }

    function summarizeUrdfModel(robotModel) {
      let meshObjectCount = 0;
      let triangleCount = 0;
      robotModel.traverse((object) => {
        if (object.isMesh) {
          meshObjectCount += 1;
          const geometry = object.geometry;
          if (geometry?.index) triangleCount += geometry.index.count / 3;
          else if (geometry?.attributes?.position) triangleCount += geometry.attributes.position.count / 3;
        }
      });
      return {
        meshObjectCount,
        triangleCount: Math.round(triangleCount),
        jointNames: Object.keys(robotModel.joints || {}),
      };
    }

    function addRoom(parent, room) {
      parent.add(box(room.size_m[0], room.size_m[1], 0.012, 0x2b3036, 0, 0, -0.006));
      parent.add(box(room.size_m[0], 0.018, room.size_m[2], 0x8f98a3, 0, room.size_m[1] / 2, room.size_m[2] / 2));
      parent.add(box(0.018, room.size_m[1], room.size_m[2], 0x7f8790, -room.size_m[0] / 2, 0, room.size_m[2] / 2));
      parent.add(box(0.018, room.size_m[1], room.size_m[2], 0x7f8790, room.size_m[0] / 2, 0, room.size_m[2] / 2));
    }

    function addDesk(parent, desk) {
      parent.add(box(desk.size_m[0], desk.size_m[1], desk.size_m[2], 0x9c8f7a, ...desk.center_m));
    }

    function addTray(parent, tray) {
      const color = colorHex(tray.color);
      const group = new THREE.Group();
      group.position.set(...tray.center_m);
      const base = box(tray.size_m[0], tray.size_m[1], tray.size_m[2], color, 0, 0, 0);
      base.material.opacity = 0.42;
      base.material.transparent = true;
      group.add(base);
      const rimH = 0.026, rimT = 0.006;
      group.add(box(tray.size_m[0], rimT, rimH, color, 0, -tray.size_m[1] / 2, tray.size_m[2] / 2 + rimH / 2));
      group.add(box(tray.size_m[0], rimT, rimH, color, 0, tray.size_m[1] / 2, tray.size_m[2] / 2 + rimH / 2));
      group.add(box(rimT, tray.size_m[1], rimH, color, -tray.size_m[0] / 2, 0, tray.size_m[2] / 2 + rimH / 2));
      group.add(box(rimT, tray.size_m[1], rimH, color, tray.size_m[0] / 2, 0, tray.size_m[2] / 2 + rimH / 2));
      parent.add(group);
    }

    function addCube(parent, cubeSpec) {
      const mesh = box(cubeSpec.side_length_m, cubeSpec.side_length_m, cubeSpec.side_length_m, colorHex(cubeSpec.color), ...cubeSpec.initial_position_m);
      mesh.name = cubeSpec.name;
      state.cubes.set(cubeSpec.name, mesh);
      parent.add(mesh);
    }

    function addFiducial(parent, fiducial) {
      const group = new THREE.Group();
      group.name = fiducial.name;
      group.position.set(...fiducial.position_m);
      const [rx, ry, rz] = fiducial.euler_deg || [0, 0, 0];
      group.rotation.set(THREE.MathUtils.degToRad(rx), THREE.MathUtils.degToRad(ry), THREE.MathUtils.degToRad(rz));
      const size = fiducial.size_m;
      const base = box(size, size, 0.002, 0xf1f1e8, 0, 0, 0);
      base.name = `${fiducial.name}_white_visual`;
      group.add(base);
      const rows = fiducial.grid || [];
      const cell = size / Math.max(1, rows.length);
      const half = size / 2;
      for (let row = 0; row < rows.length; row += 1) {
        for (let col = 0; col < rows[row].length; col += 1) {
          if (rows[row][col] !== '1') continue;
          const x = -half + cell * (col + 0.5);
          const y = half - cell * (row + 0.5);
          const marker = box(cell * 0.92, cell * 0.92, 0.0022, 0x050505, x, y, 0.002);
          marker.name = `${fiducial.name}_cell_${row}_${col}_visual`;
          group.add(marker);
        }
      }
      parent.add(group);
      window.__SCENESMITH_APRILTAG_VISUALS = [
        ...(window.__SCENESMITH_APRILTAG_VISUALS || []),
        {
          name: fiducial.name,
          family: fiducial.family,
          tagId: fiducial.tag_id,
          sizeM: fiducial.size_m,
          positionM: fiducial.position_m,
        },
      ];
    }

    function addLegend(spec) {
      const legend = document.getElementById('legend');
      for (const tray of spec.trays) {
        const item = document.createElement('span');
        item.innerHTML = `<i class="swatch" style="background:${cssColor(tray.color)}"></i>${tray.color} tray`;
        legend.appendChild(item);
      }
      const robot = document.createElement('span');
      robot.innerHTML = '<i class="swatch" style="background:#ffd11a"></i>SO-101 URDF';
      legend.appendChild(robot);
      const camera = document.createElement('span');
      camera.innerHTML = '<i class="swatch" style="background:#1b8cff"></i>wrist camera';
      legend.appendChild(camera);
      for (const fiducial of spec.fiducials || []) {
        const tag = document.createElement('span');
        tag.innerHTML = '<i class="swatch" style="background:#f1f1e8"></i>AprilTag';
        legend.appendChild(tag);
        break;
      }
    }

    function box(x, y, z, color, px, py, pz) {
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(x, y, z), mat(color));
      mesh.position.set(px, py, pz);
      return mesh;
    }

    function mat(color) {
      return new THREE.MeshStandardMaterial({ color, roughness: 0.65, metalness: 0.05 });
    }

    function colorHex(color) {
      return { red: 0xd71914, blue: 0x1648d8, green: 0x178a3d, yellow: 0xf0bc24, purple: 0x7848bd, orange: 0xf06b24 }[color] || 0x777777;
    }

    function cssColor(color) {
      return { red: '#d71914', blue: '#1648d8', green: '#178a3d', yellow: '#f0bc24', purple: '#7848bd', orange: '#f06b24' }[color] || '#777';
    }
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
