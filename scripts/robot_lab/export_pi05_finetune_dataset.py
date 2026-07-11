#!/usr/bin/env python3
"""Export a SceneSmith SO-101 sorting rollout as a PI05 LeRobotDataset.

This is a smoke-finetuning dataset bridge. It records the SceneSmith task,
three camera observations, padded SO-101 state, and padded SO-101 actions using
the feature keys expected by `lerobot/pi05_base`.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


PI05_IMAGE_KEYS = (
    "observation.images.base_0_rgb",
    "observation.images.left_wrist_0_rgb",
    "observation.images.right_wrist_0_rgb",
)
TASK = "Sort each cube into the same-colored tray: red cubes into the red tray and blue cubes into the blue tray."
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-json", type=Path, required=True)
    parser.add_argument("--trajectory-json", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repo-id", default="gauntlet/scenesmith-so101-pi05-smoke")
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--frames-per-waypoint", type=int, default=4)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    _add_lerobot_to_path()
    from lerobot.datasets import LeRobotDataset

    if args.output_root.exists():
        if not args.overwrite:
            raise SystemExit(f"{args.output_root} already exists; pass --overwrite to replace it.")
        shutil.rmtree(args.output_root)

    scene = json.loads(args.scene_json.read_text(encoding="utf-8"))
    trajectory = json.loads(args.trajectory_json.read_text(encoding="utf-8"))
    frames = _expanded_frames(trajectory, args.frames_per_waypoint)
    image_triplet = _load_image_triplet(args.scene_json.parent, args.image_size)

    dataset = LeRobotDataset.create(
        repo_id=args.repo_id,
        fps=args.fps,
        root=args.output_root,
        robot_type="so101_follower",
        features=_features(),
        use_videos=False,
        image_writer_processes=0,
        image_writer_threads=0,
    )

    for episode_index in range(args.episodes):
        episode_frames = _episode_variant(frames, episode_index)
        for frame in episode_frames:
            state = _pad32(_radians_to_degrees(frame["robot_control"]))
            action = _pad32(_radians_to_degrees(frame["next_robot_control"]))
            dataset.add_frame(
                {
                    **{key: image.copy() for key, image in zip(PI05_IMAGE_KEYS, image_triplet, strict=True)},
                    "observation.state": state,
                    "action": action,
                    "task": scene.get("policy", {}).get("task") or TASK,
                }
            )
        dataset.save_episode(parallel_encoding=False)

    dataset.finalize()
    summary = {
        "status": "pass",
        "repo_id": args.repo_id,
        "root": str(args.output_root),
        "episodes": args.episodes,
        "frames_per_episode": len(frames),
        "total_frames": args.episodes * len(frames),
        "fps": args.fps,
        "features": sorted(_features()),
        "source_scene": str(args.scene_json),
        "source_trajectory": str(args.trajectory_json),
        "image_sources": _image_source_paths(args.scene_json.parent),
        "task": scene.get("policy", {}).get("task") or TASK,
    }
    summary_path = args.output_root / "scenesmith_export_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.verify:
        loaded = LeRobotDataset(args.repo_id, root=args.output_root, return_uint8=True)
        item = loaded[0]
        summary["verified"] = {
            "num_frames": loaded.num_frames,
            "num_episodes": loaded.num_episodes,
            "task": item["task"],
            "state_shape": list(item["observation.state"].shape),
            "action_shape": list(item["action"].shape),
            "image_shapes": {
                key: list(item[key].shape) for key in PI05_IMAGE_KEYS
            },
        }
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _add_lerobot_to_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack

    activate_lerobot_stack(repo_root=repo_root, stage="collection")


def _features() -> dict[str, dict[str, Any]]:
    names32 = list(JOINT_NAMES) + [f"pad_{index}" for index in range(26)]
    features: dict[str, dict[str, Any]] = {
        key: {"dtype": "image", "shape": (3, 224, 224), "names": ["channel", "height", "width"]}
        for key in PI05_IMAGE_KEYS
    }
    features["observation.state"] = {"dtype": "float32", "shape": (32,), "names": names32}
    features["action"] = {"dtype": "float32", "shape": (32,), "names": names32}
    return features


def _load_image_triplet(output_dir: Path, image_size: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sources = _image_source_paths(output_dir)
    return (
        _load_resized_rgb(Path(sources["base"]), image_size),
        _load_resized_rgb(Path(sources["wrist"]), image_size),
        _load_resized_rgb(Path(sources["overhead"]), image_size),
    )


def _image_source_paths(output_dir: Path) -> dict[str, str]:
    candidates = (
        ("base", output_dir / "mujoco" / "render-cam0-side.png"),
        ("wrist", output_dir / "mujoco" / "render-cam2-wrist.png"),
        ("overhead", output_dir / "mujoco" / "render-cam1-overhead.png"),
    )
    missing = [str(path) for _, path in candidates if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing image observations: {missing}")
    return {role: str(path) for role, path in candidates}


def _load_resized_rgb(path: Path, image_size: int) -> np.ndarray:
    with Image.open(path) as image:
        resized = image.convert("RGB").resize((image_size, image_size), Image.Resampling.BILINEAR)
    return np.asarray(resized, dtype=np.uint8)


def _expanded_frames(trajectory: list[dict[str, Any]], frames_per_waypoint: int) -> list[dict[str, Any]]:
    if not trajectory:
        raise ValueError("Trajectory is empty.")
    controls = [
        _control6(row.get("robot_control"))
        for row in trajectory
        if isinstance(row.get("robot_control"), list)
    ]
    if not controls:
        raise ValueError("Trajectory has no robot_control entries.")

    expanded: list[dict[str, Any]] = []
    for index, control in enumerate(controls):
        next_control = controls[min(index + 1, len(controls) - 1)]
        for sub_index in range(frames_per_waypoint):
            alpha = sub_index / max(1, frames_per_waypoint)
            interp = [
                (1.0 - alpha) * current + alpha * nxt
                for current, nxt in zip(control, next_control, strict=True)
            ]
            expanded.append({"robot_control": interp, "next_robot_control": next_control})
    return expanded


def _episode_variant(frames: list[dict[str, Any]], episode_index: int) -> list[dict[str, Any]]:
    if episode_index == 0:
        return frames
    scale = 1.0 + min(0.04, episode_index * 0.01)
    variant: list[dict[str, Any]] = []
    for frame in frames:
        variant.append(
            {
                "robot_control": _scaled_control(frame["robot_control"], scale),
                "next_robot_control": _scaled_control(frame["next_robot_control"], scale),
            }
        )
    return variant


def _scaled_control(control: list[float], scale: float) -> list[float]:
    scaled = [value * scale for value in control]
    limits = [(-2.1, 2.1), (-1.6, 1.6), (-1.8, 1.8), (-1.8, 1.8), (-2.5, 2.5), (0.0, 1.1)]
    return [min(high, max(low, value)) for value, (low, high) in zip(scaled, limits, strict=True)]


def _control6(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) < 6:
        raise ValueError(f"Expected six-value robot_control, got {value!r}")
    return [float(item) for item in value[:6]]


def _radians_to_degrees(control: list[float]) -> list[float]:
    return [math.degrees(value) for value in control]


def _pad32(values: list[float]) -> np.ndarray:
    padded = np.zeros((32,), dtype=np.float32)
    n = min(len(values), 32)
    padded[:n] = np.asarray(values[:n], dtype=np.float32)
    return padded


if __name__ == "__main__":
    raise SystemExit(main())
