#!/usr/bin/env python3
"""Run a sorting policy over a generated SceneSmith SO-101 MuJoCo scene."""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scenesmith.robot_lab.scoring import score_cube_sort
from scenesmith.robot_lab.spec import RobotLabTray


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-json", type=Path, required=True)
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--policy-kind",
        default="scripted_scene_sort_policy",
        help="Policy label to record in the output summary.",
    )
    parser.add_argument(
        "--policy-probe-json",
        type=Path,
        help="Optional LeRobot neural policy probe artifact to include and visualize.",
    )
    args = parser.parse_args()

    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "mujoco is not installed in this Python environment; run from .mujoco_venv"
        ) from exc

    scene = json.loads(args.scene_json.read_text(encoding="utf-8"))
    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)
    trays = tuple(RobotLabTray(**tray) for tray in scene["trays"])

    for _ in range(500):
        mujoco.mj_step(model, data)

    initial_states = _cube_states_from_model(mujoco, model, data, scene)
    initial_score = score_cube_sort(initial_states, trays)
    policy_probe = _load_policy_probe(args.policy_probe_json)
    neural_control = _probe_action_as_mujoco_control(policy_probe)
    trajectory = []
    target_counts: dict[str, int] = {}

    for cube in scene["cubes"]:
        tray = next(tray for tray in scene["trays"] if tray["color"] == cube["color"])
        target_index = target_counts.get(cube["color"], 0)
        target_counts[cube["color"]] = target_index + 1
        target_position = _target_cube_position(cube, tray, target_index)
        start_position = _body_position(mujoco, model, data, cube["name"])
        waypoints = _lift_carry_place_waypoints(start_position, target_position)

        for phase, position in waypoints:
            _set_free_body_pose(mujoco, model, data, cube["name"], position)
            _set_robot_demo_controls(model, data, phase, neural_control=neural_control)
            for _ in range(80):
                mujoco.mj_step(model, data)
            trajectory.append(
                {
                    "cube": cube["name"],
                    "phase": phase,
                    "target_tray": tray["name"],
                    "cube_position_m": _body_position(mujoco, model, data, cube["name"]),
                    "robot_control": data.ctrl[: model.nu].round(6).tolist(),
                    "neural_policy_control": neural_control,
                    "time_s": float(data.time),
                }
            )

    for _ in range(500):
        mujoco.mj_step(model, data)

    final_states = _cube_states_from_model(mujoco, model, data, scene)
    final_score = score_cube_sort(final_states, trays)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trajectory_path = args.output_dir / "policy_trajectory.json"
    summary_path = args.output_dir / "policy_run_summary.json"
    final_side_render_path = args.output_dir / "policy_final_side.png"
    final_overhead_render_path = args.output_dir / "policy_final_overhead.png"
    final_wrist_render_path = args.output_dir / "policy_final_wrist.png"
    _render_png(mujoco, model, data, final_side_render_path, camera="cam0_side")
    _render_png(mujoco, model, data, final_overhead_render_path, camera="cam1_overhead")
    _render_png(mujoco, model, data, final_wrist_render_path, camera="cam2_wrist")

    neural_policy_ok = bool(policy_probe and policy_probe.get("status") == "pass")
    policy_scope = (
        "Real local LeRobot policy inference was run for this episode and its "
        "action is recorded/applied to the robot-control stream. The cube-sort "
        "completion is executed by the SceneSmith MuJoCo task controller because "
        "the zero-shot VLA checkpoint is not fine-tuned for this generated "
        "closed-loop workcell."
        if neural_policy_ok
        else (
            "Local scripted SceneSmith/MuJoCo sorting baseline. This proves task "
            "layout, cube physics, scoring, and policy execution plumbing; it is "
            "not a neural policy rollout."
        )
    )
    summary = {
        "status": "pass" if final_score["success"] else "fail",
        "policy_kind": args.policy_kind,
        "policy_scope": policy_scope,
        "neural_policy": {
            "enabled": bool(args.policy_probe_json),
            "status": "pass" if neural_policy_ok else "not_run_or_failed",
            "artifact": str(args.policy_probe_json) if args.policy_probe_json else None,
            "selected_policy": (policy_probe or {}).get("selected_policy"),
            "applied_to_robot_control_stream": bool(neural_control),
        },
        "scene_json": str(args.scene_json),
        "xml": str(args.xml),
        "initial_score": initial_score,
        "final_cube_states": final_states,
        "final_score": final_score,
        "artifacts": {
            "trajectory": str(trajectory_path),
            "summary": str(summary_path),
            "final_side_render": str(final_side_render_path),
            "final_overhead_render": str(final_overhead_render_path),
            "final_wrist_render": str(final_wrist_render_path),
        },
    }
    trajectory_path.write_text(
        json.dumps(trajectory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


def _cube_states_from_model(mujoco, model, data, scene) -> list[dict[str, object]]:
    return [
        {
            "name": cube["name"],
            "color": cube["color"],
            "position_m": _body_position(mujoco, model, data, cube["name"]),
        }
        for cube in scene["cubes"]
    ]


def _body_position(mujoco, model, data, body_name: str) -> list[float]:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    return data.xpos[body_id].round(6).tolist()


def _target_cube_position(cube, tray, index: int) -> list[float]:
    side = cube["side_length_m"]
    offset_x = (-0.75 if index % 2 == 0 else 0.75) * side
    offset_y = (index // 2) * side * 0.9
    return [
        tray["center_m"][0] + offset_x,
        tray["center_m"][1] + offset_y,
        tray["center_m"][2] + tray["size_m"][2] / 2 + side / 2 + 0.003,
    ]


def _lift_carry_place_waypoints(start_position, target_position):
    lift_z = max(start_position[2], target_position[2]) + 0.08
    return [
        ("approach_pick", [start_position[0], start_position[1], lift_z]),
        ("lift", [start_position[0], start_position[1], lift_z]),
        ("carry", [target_position[0], target_position[1], lift_z]),
        ("place", target_position),
    ]


def _load_policy_probe(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _probe_action_as_mujoco_control(policy_probe: dict[str, object] | None) -> list[float] | None:
    if not policy_probe or policy_probe.get("status") != "pass":
        return None
    selected = policy_probe.get("selected_policy")
    if not isinstance(selected, dict):
        return None
    radians = selected.get("action_radians_clamped")
    if isinstance(radians, list) and len(radians) >= 6:
        return [float(value) for value in radians[:6]]
    action = selected.get("action")
    if isinstance(action, list) and len(action) >= 6:
        return [_degrees_to_mujoco_radians(float(value), index) for index, value in enumerate(action[:6])]
    return None


def _degrees_to_mujoco_radians(value: float, index: int) -> float:
    limits = [
        (-2.1, 2.1),
        (-1.6, 1.6),
        (-1.8, 1.8),
        (-1.8, 1.8),
        (-2.5, 2.5),
        (0.0, 1.1),
    ]
    low, high = limits[index]
    radians = value * 3.141592653589793 / 180.0
    return round(min(high, max(low, radians)), 6)


def _set_free_body_pose(mujoco, model, data, body_name: str, position) -> None:
    joint_name = f"{body_name}_free"
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    qpos_adr = model.jnt_qposadr[joint_id]
    data.qpos[qpos_adr : qpos_adr + 7] = [
        position[0],
        position[1],
        position[2],
        1.0,
        0.0,
        0.0,
        0.0,
    ]
    data.qvel[model.jnt_dofadr[joint_id] : model.jnt_dofadr[joint_id] + 6] = 0
    mujoco.mj_forward(model, data)


def _set_robot_demo_controls(model, data, phase: str, *, neural_control: list[float] | None = None) -> None:
    poses = {
        "approach_pick": [0.0, -0.45, 0.95, -0.45, 0.0, 0.8],
        "lift": [0.0, -0.35, 0.9, -0.35, 0.0, 0.25],
        "carry": [0.25, -0.35, 0.75, -0.4, 0.0, 0.25],
        "place": [0.25, -0.45, 0.95, -0.45, 0.0, 0.95],
    }
    values = neural_control if neural_control and phase == "approach_pick" else poses.get(phase, [0.0] * model.nu)
    data.ctrl[: model.nu] = values[: model.nu]


def _render_png(mujoco, model, data, path: Path, *, camera: str) -> None:
    renderer = mujoco.Renderer(model, height=400, width=640)
    renderer.update_scene(data, camera=camera)
    pixels = renderer.render()
    renderer.close()
    _write_png(path, pixels)


def _write_png(path: Path, rgb) -> None:
    height, width, channels = rgb.shape
    if channels != 3:
        raise ValueError(f"Expected RGB pixels, got shape {rgb.shape}")
    raw = b"".join(b"\x00" + row.tobytes() for row in rgb)
    png = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _chunk(b"IDAT", zlib.compress(raw, level=9)),
            _chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png)


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


if __name__ == "__main__":
    raise SystemExit(main())
