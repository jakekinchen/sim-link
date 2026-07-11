#!/usr/bin/env python3
"""Export synchronized SceneSmith intervention episodes as a LeRobot dataset."""

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

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.autolearn import (
    is_dagger_correction_frame,
    policy_expert_delta_l2,
    select_dagger_context_frames,
    select_training_frames,
    validate_dagger_episode_scope,
)
from scenesmith.robot_lab.so101_coordinates import coordinate_contract, mujoco_to_lerobot
from scenesmith.robot_lab.pi05_dataset_contract import write_dataset_contract


PI05_IMAGE_KEYS = (
    "observation.images.base_0_rgb",
    "observation.images.left_wrist_0_rgb",
    "observation.images.right_wrist_0_rgb",
)
CAUSAL_IMAGE_KEYS = (
    "observation.images.top",
    "observation.images.wrist",
)
IMAGE_ROLES = ("base", "wrist", "overhead")
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
    parser.add_argument("--episode-summary", type=Path, action="append", default=[])
    parser.add_argument("--batch-summary", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repo-id", default="gauntlet/scenesmith-so101-interventions")
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--frame-selection",
        choices=("intervention_only", "dagger_corrections", "dagger_context", "all"),
        default="intervention_only",
        help=(
            "Export human interventions, privileged DAgger controller corrections, "
            "or all frames for replay/pipeline tests."
        ),
    )
    parser.add_argument("--context-before", type=int, default=30)
    parser.add_argument("--context-after", type=int, default=30)
    parser.add_argument(
        "--dataset-schema",
        choices=("intervention", "pi05_causal"),
        default="intervention",
        help=(
            "Use the full intervention audit schema, or the compact six-axis "
            "PI0.5 causal-training schema used by the accepted sorting adapter."
        ),
    )
    parser.add_argument(
        "--allow-scripted-harness",
        action="store_true",
        help="Allow explicitly test-only simulated intervention episodes.",
    )
    args = parser.parse_args()

    summary_paths = _summary_paths(args.episode_summary, args.batch_summary)
    if not summary_paths:
        parser.error("Pass --episode-summary at least once or provide --batch-summary")
    if args.fps <= 0 or args.image_size <= 0:
        parser.error("--fps and --image-size must be positive")

    _add_lerobot_to_path()
    from lerobot.datasets import LeRobotDataset

    if args.output_root.exists():
        if not args.overwrite:
            raise SystemExit(f"{args.output_root} already exists; pass --overwrite to replace it.")
        shutil.rmtree(args.output_root)

    dataset = LeRobotDataset.create(
        repo_id=args.repo_id,
        fps=args.fps,
        root=args.output_root,
        robot_type="so101_follower",
        features=_features(args.image_size, args.dataset_schema),
        use_videos=False,
        image_writer_processes=0,
        image_writer_threads=0,
    )

    sidecar_rows: list[dict[str, Any]] = []
    episode_reports: list[dict[str, Any]] = []
    dataset_episode_index = 0
    for source_episode_index, summary_path in enumerate(summary_paths):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        trajectory_path = Path(summary["artifacts"]["trajectory"])
        source_frames = json.loads(trajectory_path.read_text(encoding="utf-8"))["frames"]
        if not source_frames:
            raise ValueError(f"Intervention trajectory is empty: {trajectory_path}")
        frames = (
            select_dagger_context_frames(
                source_frames,
                before=args.context_before,
                after=args.context_after,
            )
            if args.frame_selection == "dagger_context"
            else select_training_frames(source_frames, args.frame_selection)
        )
        _validate_training_scope(
            summary,
            args.allow_scripted_harness,
            frame_selection=args.frame_selection,
            frames=frames,
        )
        if not frames:
            raise ValueError(
                f"No frames matched --frame-selection={args.frame_selection}: {trajectory_path}"
            )

        episode_dir = summary_path.parent
        for segment_index, run in enumerate(_split_contiguous_runs(frames)):
            image_hashes: set[str] = set()
            intervention_count = 0
            correction_count = 0
            correction_source_counts: dict[str, int] = {}
            correction_deltas: list[float] = []
            for frame in run:
                frame_task = _frame_task(
                    frame,
                    summary,
                    require_frame_task=args.frame_selection in {"dagger_corrections", "dagger_context"},
                )
                images, sources = _load_frame_images(episode_dir, frame, args.image_size)
                image_hashes.update(_sha256(Path(path)) for path in sources.values())
                state6 = mujoco_to_lerobot(_control6(frame["observation"]["state"]))
                executed6 = mujoco_to_lerobot(_control6(frame["executed_action"]))
                policy6 = mujoco_to_lerobot(_control6(frame["policy_action"]))
                human_raw = frame.get("human_action")
                human6 = (
                    mujoco_to_lerobot(_control6(human_raw))
                    if human_raw is not None
                    else [0.0] * 6
                )
                is_intervention = bool(frame.get("is_intervention"))
                is_expert_correction = is_dagger_correction_frame(frame)
                intervention_count += int(is_intervention)
                correction_count += int(is_expert_correction)
                if is_expert_correction:
                    source = str(frame.get("action_source") or "unknown")
                    correction_source_counts[source] = correction_source_counts.get(source, 0) + 1
                    correction_deltas.append(policy_expert_delta_l2(frame))
                if args.dataset_schema == "pi05_causal":
                    dataset_frame = {
                        "observation.images.top": images[2].copy(),
                        "observation.images.wrist": images[1].copy(),
                        "observation.state": np.asarray(state6, dtype=np.float32),
                        "action": np.asarray(executed6, dtype=np.float32),
                        "task": frame_task,
                    }
                else:
                    dataset_frame = {
                        **{
                            key: image.copy()
                            for key, image in zip(PI05_IMAGE_KEYS, images, strict=True)
                        },
                        "observation.state": _pad32(state6),
                        "action": _pad32(executed6),
                        "policy_action": _pad32(policy6),
                        "human_action": _pad32(human6),
                        "is_intervention": np.asarray([is_intervention], dtype=bool),
                        "is_expert_correction": np.asarray([is_expert_correction], dtype=bool),
                        "deadman_fresh": np.asarray(
                            [bool(frame.get("deadman_fresh"))], dtype=bool
                        ),
                        "randomization_seed": np.asarray(
                            [int(summary["seed"])], dtype=np.int64
                        ),
                        "task": frame_task,
                    }
                dataset.add_frame(dataset_frame)
                sidecar_rows.append(
                    {
                        "episode_index": dataset_episode_index,
                        "source_episode_index": source_episode_index,
                        "segment_index": segment_index,
                        "frame_index": int(frame["frame_index"]),
                        "time_s": frame["time_s"],
                        "phase": frame["phase"],
                        "policy_task": frame_task,
                        "is_intervention": is_intervention,
                        "is_expert_correction": is_expert_correction,
                        "replay_role": frame.get("replay_role", "expert_correction"),
                        "intervention_event": frame.get("intervention_event"),
                        "action_source": frame.get("action_source"),
                        "policy_action": frame.get("policy_action"),
                        "human_action": human_raw,
                        "executed_action": frame.get("executed_action"),
                        "deadman": {
                            "armed": frame.get("deadman_armed"),
                            "takeover": frame.get("deadman_takeover"),
                            "fresh": frame.get("deadman_fresh"),
                            "age_s": frame.get("deadman_age_s"),
                            "sequence": frame.get("deadman_sequence"),
                        },
                        "failure_reason": frame.get("failure_reason"),
                        "seed": summary.get("seed"),
                        "scene_id": summary.get("scene_id"),
                        "object_motion_mode": frame.get("object_motion_mode"),
                        "observation_images": sources,
                        "transition": frame.get("transition"),
                    }
                )

            dataset.save_episode(parallel_encoding=False)
            episode_reports.append(
                {
                    "episode_index": dataset_episode_index,
                    "source_episode_index": source_episode_index,
                    "segment_index": segment_index,
                    "source_summary": str(summary_path),
                    "frames": len(run),
                    "source_frames": len(source_frames),
                    "source_frame_start": int(run[0]["frame_index"]),
                    "source_frame_end": int(run[-1]["frame_index"]),
                    "intervention_frames": intervention_count,
                    "expert_correction_frames": correction_count,
                    "correction_source_counts": correction_source_counts,
                    "mean_policy_expert_delta_l2": (
                        sum(correction_deltas) / len(correction_deltas)
                        if correction_deltas
                        else 0.0
                    ),
                    "unique_source_images": len(image_hashes),
                    "expected_source_images": len(run) * len(_image_keys(args.dataset_schema)),
                    "proof_scope": summary.get("proof_scope"),
                }
            )
            dataset_episode_index += 1

    dataset.finalize()
    task_conditioning = (
        "frame_policy_task"
        if args.frame_selection in {"dagger_corrections", "dagger_context"}
        else "episode_task"
    )
    dataset_contract = write_dataset_contract(
        args.output_root,
        task_conditioning=task_conditioning,
    )
    sidecar_path = args.output_root / "scenesmith_intervention_sidecar.jsonl"
    sidecar_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in sidecar_rows),
        encoding="utf-8",
    )
    export_summary: dict[str, Any] = {
        "schema_version": "scenesmith.intervention_dataset_export.v2",
        "status": "pass",
        "repo_id": args.repo_id,
        "root": str(args.output_root),
        "source_episode_summaries": [str(path) for path in summary_paths],
        "num_episodes": len(episode_reports),
        "num_frames": len(sidecar_rows),
        "num_intervention_frames": sum(row["is_intervention"] for row in sidecar_rows),
        "num_expert_correction_frames": sum(
            row["is_expert_correction"] for row in sidecar_rows
        ),
        "replay_role_counts": {
            role: sum(row["replay_role"] == role for row in sidecar_rows)
            for role in sorted({row["replay_role"] for row in sidecar_rows})
        },
        "fps": args.fps,
        "features": sorted(_features(args.image_size, args.dataset_schema)),
        "sidecar": str(sidecar_path),
        "task": _task(json.loads(summary_paths[0].read_text(encoding="utf-8"))),
        "allow_scripted_harness": args.allow_scripted_harness,
        "frame_selection": args.frame_selection,
        "dataset_schema": args.dataset_schema,
        "coordinate_contract": coordinate_contract(),
        "dataset_contract": dataset_contract,
        "episodes": episode_reports,
    }

    if args.verify:
        loaded = LeRobotDataset(args.repo_id, root=args.output_root, return_uint8=True)
        item = loaded[0]
        verified: dict[str, Any] = {
            "num_frames": loaded.num_frames,
            "num_episodes": loaded.num_episodes,
            "task": item["task"],
            "state_shape": list(item["observation.state"].shape),
            "action_shape": list(item["action"].shape),
            "image_shapes": {
                key: list(item[key].shape)
                for key in _image_keys(args.dataset_schema)
            },
        }
        if args.dataset_schema == "intervention":
            verified.update(
                {
                    "policy_action_shape": list(item["policy_action"].shape),
                    "human_action_shape": list(item["human_action"].shape),
                    "intervention_shape": list(item["is_intervention"].shape),
                    "expert_correction_shape": list(item["is_expert_correction"].shape),
                }
            )
        export_summary["verified"] = verified

    summary_path = args.output_root / "scenesmith_intervention_export_summary.json"
    summary_path.write_text(
        json.dumps(export_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(export_summary, indent=2, sort_keys=True))
    return 0


def _summary_paths(episode_summaries: list[Path], batch_summary: Path | None) -> list[Path]:
    paths = [path.resolve() for path in episode_summaries]
    if batch_summary is not None:
        payload = json.loads(batch_summary.read_text(encoding="utf-8"))
        paths.extend(Path(path).resolve() for path in payload.get("episode_summaries", []))
    return list(dict.fromkeys(paths))


def _split_contiguous_runs(frames: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Split selected frames before LeRobot can construct chunks across source gaps."""

    if not frames:
        return []
    runs: list[list[dict[str, Any]]] = [[frames[0]]]
    previous = int(frames[0]["frame_index"])
    for frame in frames[1:]:
        current = int(frame["frame_index"])
        if current <= previous:
            raise ValueError("Selected training frames must be strictly ordered")
        if current != previous + 1:
            runs.append([])
        runs[-1].append(frame)
        previous = current
    return runs


def _validate_training_scope(
    summary: dict[str, Any],
    allow_scripted_harness: bool,
    *,
    frame_selection: str,
    frames: list[dict[str, Any]],
) -> None:
    if frame_selection in {"dagger_corrections", "dagger_context"}:
        validate_dagger_episode_scope(summary, frames)
        return
    scope = summary.get("proof_scope", {})
    if scope.get("physical_leader_frames_are_training_eligible"):
        return
    if allow_scripted_harness:
        return
    raise ValueError(
        "Episode is a simulated/scripted intervention harness, not a human correction demo. "
        "Pass --allow-scripted-harness only for pipeline tests."
    )


def _add_lerobot_to_path() -> None:
    from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack

    activate_lerobot_stack(repo_root=REPO_ROOT, stage="collection")


def _image_keys(dataset_schema: str) -> tuple[str, ...]:
    return CAUSAL_IMAGE_KEYS if dataset_schema == "pi05_causal" else PI05_IMAGE_KEYS


def _features(image_size: int, dataset_schema: str = "intervention") -> dict[str, dict[str, Any]]:
    if dataset_schema == "pi05_causal":
        names6 = [f"{name}.pos" for name in JOINT_NAMES]
        return {
            **{
                key: {
                    "dtype": "image",
                    "shape": (3, image_size, image_size),
                    "names": ["channel", "height", "width"],
                }
                for key in CAUSAL_IMAGE_KEYS
            },
            "observation.state": {
                "dtype": "float32",
                "shape": (6,),
                "names": names6,
            },
            "action": {
                "dtype": "float32",
                "shape": (6,),
                "names": names6,
            },
        }
    if dataset_schema != "intervention":
        raise ValueError(f"Unknown dataset schema: {dataset_schema}")
    names32 = list(JOINT_NAMES) + [f"pad_{index}" for index in range(26)]
    features: dict[str, dict[str, Any]] = {
        key: {
            "dtype": "image",
            "shape": (3, image_size, image_size),
            "names": ["channel", "height", "width"],
        }
        for key in PI05_IMAGE_KEYS
    }
    for key in ("observation.state", "action", "policy_action", "human_action"):
        features[key] = {"dtype": "float32", "shape": (32,), "names": names32}
    features["is_intervention"] = {"dtype": "bool", "shape": (1,), "names": None}
    features["is_expert_correction"] = {"dtype": "bool", "shape": (1,), "names": None}
    features["deadman_fresh"] = {"dtype": "bool", "shape": (1,), "names": None}
    features["randomization_seed"] = {"dtype": "int64", "shape": (1,), "names": None}
    return features


def _observation_image_paths(frame: dict[str, Any]) -> dict[str, str]:
    observation = frame["observation"]
    if "retained_images" in observation:
        if not observation["retained_images"]:
            raise ValueError(
                "Selected frame has no retained synchronized images; collect training data at stride 1"
            )
        relative_paths = observation["retained_images"]
    else:
        relative_paths = observation["images"]
    return relative_paths


def _load_frame_images(
    episode_dir: Path,
    frame: dict[str, Any],
    image_size: int,
) -> tuple[tuple[np.ndarray, ...], dict[str, str]]:
    relative_paths = _observation_image_paths(frame)
    sources = {role: episode_dir / relative_paths[role] for role in IMAGE_ROLES}
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing synchronized image observations: {missing}")
    images = tuple(_load_resized_rgb(sources[role], image_size) for role in IMAGE_ROLES)
    return images, {role: str(path) for role, path in sources.items()}


def _load_resized_rgb(path: Path, image_size: int) -> np.ndarray:
    with Image.open(path) as image:
        resized = image.convert("RGB").resize((image_size, image_size), Image.Resampling.BILINEAR)
    return np.asarray(resized, dtype=np.uint8)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _task(summary: dict[str, Any]) -> str:
    return summary.get("task") or "Sort each cube into the same-colored tray."


def _frame_task(
    frame: dict[str, Any], summary: dict[str, Any], *, require_frame_task: bool
) -> str:
    task = frame.get("policy_task")
    if isinstance(task, str) and task.strip():
        return task.strip()
    if require_frame_task:
        raise ValueError(
            "DAgger correction frame lacks the exact policy_task used during collection"
        )
    return _task(summary)


def _control6(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) < 6:
        raise ValueError(f"Expected six-value SO-101 control, got {value!r}")
    return [float(item) for item in value[:6]]


def _pad32(values: list[float]) -> np.ndarray:
    padded = np.zeros((32,), dtype=np.float32)
    n = min(len(values), 32)
    padded[:n] = np.asarray(values[:n], dtype=np.float32)
    return padded


if __name__ == "__main__":
    raise SystemExit(main())
