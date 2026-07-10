#!/usr/bin/env python3
"""Write a validated PI0.5 contract beside an existing LeRobot dataset."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.pi05_dataset_contract import (
    DATASET_CONTRACT_FILENAME,
    write_dataset_contract,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument(
        "--task-conditioning",
        choices=("episode_task", "frame_stage_task", "frame_policy_task"),
        required=True,
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    destination = args.dataset_root / DATASET_CONTRACT_FILENAME
    if destination.exists() and not args.overwrite:
        parser.error(f"{destination} exists; pass --overwrite to replace it")
    contract = write_dataset_contract(
        args.dataset_root,
        task_conditioning=args.task_conditioning,
    )
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
