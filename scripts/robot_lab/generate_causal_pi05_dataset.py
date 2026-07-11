#!/usr/bin/env python3
"""Generate contact-causal SceneSmith demonstrations for PI0.5 adaptation."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scenesmith.robot_lab import build_so101_desk_sort_scene, export_so101_desk_sort_scene
from scenesmith.robot_lab.causal_sort_expert import (
    BODY_JOINT_OFFSETS_DEG,
    BODY_JOINT_SIGNS,
    JOINT_NAMES,
    SIMULATION_HOME,
    TASK,
    CausalSortExpert,
    CausalSortExpertConfig,
)
from scenesmith.robot_lab.domain_randomization import apply_mujoco_randomization, randomize_scene
from scenesmith.robot_lab.pi05_dataset_contract import write_dataset_contract


DEFAULT_DESCRIPTION = (
    "Set up an SO-101 arm on a desk in a simulation room with two colored trays, "
    "one red and one blue, plus a set of red and blue cubes. The robot should sort "
    "each cube into the tray with the matching color."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repo-id", default="jakekinchen/scenesmith-so101-sort-causal")
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--seed", type=int, default=6100)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--proof-every", type=int, default=5)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--push-to-hub", action="store_true")
    args = parser.parse_args()

    if args.episodes <= 0 or args.fps <= 0 or args.image_size <= 0:
        parser.error("--episodes, --fps, and --image-size must be positive")
    if args.output_root.exists():
        if not args.overwrite:
            parser.error(f"{args.output_root} exists; pass --overwrite to replace it")
        shutil.rmtree(args.output_root)

    _add_lerobot_to_path()
    from lerobot.datasets import LeRobotDataset

    dataset_root = args.output_root / "dataset"
    dataset = LeRobotDataset.create(
        repo_id=args.repo_id,
        fps=args.fps,
        root=dataset_root,
        robot_type="so101_follower",
        features=_features(args.image_size),
        use_videos=False,
        image_writer_processes=0,
        image_writer_threads=0,
    )
    base_scene = build_so101_desk_sort_scene(DEFAULT_DESCRIPTION)
    config = CausalSortExpertConfig(control_hz=args.fps, image_size=args.image_size)
    episode_reports: list[dict[str, Any]] = []
    sidecar_path = args.output_root / "causal_frames.jsonl"
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    with sidecar_path.open("w", encoding="utf-8") as sidecar:
        for episode_index in range(args.episodes):
            seed = args.seed + episode_index
            scene, manifest = randomize_scene(base_scene, seed)
            episode_dir = args.output_root / "episodes" / f"episode-{episode_index:03d}-seed-{seed}"
            export_dir = episode_dir / "scene_export"
            export_so101_desk_sort_scene(scene, export_dir)
            xml_path = export_dir / "mujoco" / "scene.xml"
            apply_mujoco_randomization(xml_path, manifest)
            _write_json(episode_dir / "domain_randomization_manifest.json", manifest)

            image_hashes = {"top": set(), "wrist": set()}
            contact_frames = 0
            proof_dir = episode_dir / "proof_frames"
            save_proof = episode_index == 0 or episode_index == args.episodes - 1

            def add_frame(frame: dict[str, Any], images: dict[str, np.ndarray]) -> None:
                nonlocal contact_frames
                dataset.add_frame(
                    {
                        "observation.images.top": images["top"].copy(),
                        "observation.images.wrist": images["wrist"].copy(),
                        "observation.state": np.asarray(frame["state"], dtype=np.float32),
                        "action": np.asarray(frame["action"], dtype=np.float32),
                        "task": TASK,
                    }
                )
                contact_frames += int(bool(frame["robot_cube_contacts"]))
                for role, image in images.items():
                    image_hashes[role].add(hashlib.sha256(image.tobytes()).hexdigest())
                sidecar.write(
                    json.dumps(
                        {"episode_index": episode_index, "seed": seed, **frame},
                        sort_keys=True,
                    )
                    + "\n"
                )
                if save_proof and frame["frame_index"] % max(1, args.proof_every) == 0:
                    _save_image(
                        proof_dir / "top" / f"{frame['frame_index']:06d}.jpg",
                        images["top"],
                    )
                    _save_image(
                        proof_dir / "wrist" / f"{frame['frame_index']:06d}.jpg",
                        images["wrist"],
                    )

            expert = CausalSortExpert(
                scene,
                xml_path,
                seed=seed,
                frame_sink=add_frame,
                config=config,
                brightness=float(manifest["observation_augmentation"]["brightness_scale"]),
                noise_std=float(manifest["observation_augmentation"]["camera_noise_std"]),
            )
            try:
                report = expert.run()
                _save_image(episode_dir / "final_top.png", expert.render("cam1_overhead"))
                _save_image(episode_dir / "final_wrist.png", expert.render("cam2_wrist"))
                _save_image(episode_dir / "final_side.png", expert.render("cam0_side"))
            finally:
                expert.close()

            if report["status"] != "pass":
                _write_json(episode_dir / "causal_episode_summary.json", report)
                raise RuntimeError(f"Causal expert failed episode {episode_index}: {report}")
            dataset.save_episode(parallel_encoding=False)
            report.update(
                {
                    "episode_index": episode_index,
                    "scene_id": scene.scene_id,
                    "contact_frames": contact_frames,
                    "unique_images": {key: len(value) for key, value in image_hashes.items()},
                    "randomization_manifest": str(
                        episode_dir / "domain_randomization_manifest.json"
                    ),
                    "scene_xml": str(xml_path),
                    "final_renders": {
                        "top": str(episode_dir / "final_top.png"),
                        "wrist": str(episode_dir / "final_wrist.png"),
                        "side": str(episode_dir / "final_side.png"),
                    },
                }
            )
            _write_json(episode_dir / "causal_episode_summary.json", report)
            episode_reports.append(report)
            print(
                json.dumps(
                    {
                        "episode": episode_index,
                        "seed": seed,
                        "frames": report["frames"],
                        "status": report["status"],
                        "sorted": report["final_score"]["sorted_count"],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    dataset.finalize()
    dataset_contract = write_dataset_contract(dataset_root, task_conditioning="episode_task")
    if args.push_to_hub:
        dataset.push_to_hub(
            private=True,
            tags=["lerobot", "scenesmith", "so101", "pi05", "simulation"],
        )

    total_frames = sum(int(report["frames"]) for report in episode_reports)
    summary = {
        "schema_version": "scenesmith.causal_pi05_dataset.v1",
        "status": "pass",
        "repo_id": args.repo_id,
        "dataset_root": str(dataset_root),
        "episodes": args.episodes,
        "total_frames": total_frames,
        "fps": args.fps,
        "task": TASK,
        "features": _features(args.image_size),
        "body_joint_signs": list(BODY_JOINT_SIGNS),
        "body_joint_offsets_deg": list(BODY_JOINT_OFFSETS_DEG),
        "simulation_home": list(SIMULATION_HOME),
        "object_motion_mode": "mujoco_contact_plus_contact_gated_weld_assist",
        "all_episodes_sorted": all(report["final_score"]["success"] for report in episode_reports),
        "all_grasps_contact_gated": all(report["all_grasps_contact_gated"] for report in episode_reports),
        "hub_pushed": args.push_to_hub,
        "sidecar": str(sidecar_path),
        "dataset_contract": dataset_contract,
        "episode_summaries": [
            str(
                args.output_root
                / "episodes"
                / f"episode-{index:03d}-seed-{args.seed + index}"
                / "causal_episode_summary.json"
            )
            for index in range(args.episodes)
        ],
    }
    _write_json(args.output_root / "dataset_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _features(image_size: int) -> dict[str, dict[str, Any]]:
    return {
        "observation.images.top": {
            "dtype": "image",
            "shape": (3, image_size, image_size),
            "names": ["channel", "height", "width"],
        },
        "observation.images.wrist": {
            "dtype": "image",
            "shape": (3, image_size, image_size),
            "names": ["channel", "height", "width"],
        },
        "observation.state": {
            "dtype": "float32",
            "shape": (6,),
            "names": list(JOINT_NAMES),
        },
        "action": {
            "dtype": "float32",
            "shape": (6,),
            "names": list(JOINT_NAMES),
        },
    }


def _add_lerobot_to_path() -> None:
    from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack

    activate_lerobot_stack(repo_root=Path(__file__).resolve().parents[2], stage="collection")


def _save_image(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels, mode="RGB").save(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
