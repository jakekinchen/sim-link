#!/usr/bin/env python3
"""Relabel a causal PI0.5 dataset with phase-specific task instructions."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

from collections import defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scenesmith.robot_lab.pi05_dataset_contract import write_dataset_contract


TASKS = (
    "Sort each colored block onto the plate of the matching color.",
    "Pick up one red block and place it in the red plate.",
    "Pick up one blue block and place it in the blue plate.",
    "Return the arm home before sorting the next block.",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--push-to-hub", action="store_true")
    args = parser.parse_args()

    if args.output_root.exists():
        if not args.overwrite:
            parser.error(f"{args.output_root} exists; pass --overwrite to replace it")
        shutil.rmtree(args.output_root)
    shutil.copytree(args.source_root, args.output_root, copy_function=os.link)

    phases_by_episode: dict[int, list[str]] = defaultdict(list)
    with args.sidecar.open("r", encoding="utf-8") as rows:
        for line in rows:
            row = json.loads(line)
            phases_by_episode[int(row["episode_index"])].append(str(row["phase"]))

    task_ids_by_episode = {
        episode: [_task_index(phase) for phase in phases]
        for episode, phases in phases_by_episode.items()
    }
    data_files = sorted(args.output_root.glob("data/chunk-*/file-*.parquet"))
    if len(data_files) != len(task_ids_by_episode):
        raise RuntimeError(
            f"Expected {len(task_ids_by_episode)} data files, found {len(data_files)}"
        )
    for episode_index, path in enumerate(data_files):
        table = pq.read_table(path)
        task_ids = task_ids_by_episode[episode_index]
        if len(task_ids) != table.num_rows:
            raise RuntimeError(
                f"Episode {episode_index}: {len(task_ids)} phases for {table.num_rows} rows"
            )
        updated = table.set_column(
            table.schema.get_field_index("task_index"),
            "task_index",
            pa.array(task_ids, type=pa.int64()),
        )
        _replace_parquet(path, updated)

    tasks_path = args.output_root / "meta" / "tasks.parquet"
    tasks_frame = pd.DataFrame(
        {"task_index": range(len(TASKS))},
        index=pd.Index(TASKS, name="task"),
    )
    tasks_temporary = tasks_path.with_suffix(tasks_path.suffix + ".tmp")
    tasks_frame.to_parquet(tasks_temporary)
    os.replace(tasks_temporary, tasks_path)
    episodes_path = args.output_root / "meta" / "episodes" / "chunk-000" / "file-000.parquet"
    episodes = pq.read_table(episodes_path)
    episode_tasks = [
        [TASKS[index] for index in dict.fromkeys(task_ids_by_episode[episode])]
        for episode in range(episodes.num_rows)
    ]
    episodes = episodes.set_column(
        episodes.schema.get_field_index("tasks"),
        "tasks",
        pa.array(episode_tasks, type=episodes.schema.field("tasks").type),
    )
    _replace_parquet(episodes_path, episodes)

    info_path = args.output_root / "meta" / "info.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    info["total_tasks"] = len(TASKS)
    info_path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    dataset_contract = write_dataset_contract(
        args.output_root,
        task_conditioning="frame_stage_task",
    )

    report = {
        "status": "pass",
        "repo_id": args.repo_id,
        "episodes": len(task_ids_by_episode),
        "frames": sum(len(values) for values in task_ids_by_episode.values()),
        "tasks": list(TASKS),
        "phase_task_counts": {
            TASKS[index]: sum(values.count(index) for values in task_ids_by_episode.values())
            for index in range(len(TASKS))
        },
        "hub_pushed": args.push_to_hub,
        "dataset_contract": dataset_contract,
    }
    (args.output_root / "stage_task_relabel_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if args.push_to_hub:
        from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack

        activate_lerobot_stack(
            repo_root=Path(__file__).resolve().parents[2], stage="collection"
        )
        from lerobot.datasets import LeRobotDataset

        dataset = LeRobotDataset(repo_id=args.repo_id, root=args.output_root)
        dataset.push_to_hub(
            private=True,
            tags=["lerobot", "scenesmith", "so101", "pi05", "stage-conditioned"],
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _task_index(phase: str) -> int:
    if phase in {"reset_settle", "final_settle"}:
        return 0
    if phase.endswith(("_post_release_settle", "_retreat", "_safe_traverse", "_return_home")):
        return 3
    if phase.startswith("red_cube_"):
        return 1
    if phase.startswith("blue_cube_"):
        return 2
    raise ValueError(f"Unknown causal expert phase: {phase}")


def _replace_parquet(path: Path, table: pa.Table) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    pq.write_table(table, temporary, compression="zstd")
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
