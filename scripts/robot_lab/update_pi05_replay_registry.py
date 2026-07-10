#!/usr/bin/env python3
"""Add a correction dataset to the bounded PI0.5 replay registry."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.replay_registry import (
    register_correction_dataset,
    write_replay_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--cycle-id", required=True)
    parser.add_argument("--max-sources", type=int, default=8)
    parser.add_argument("--max-frames", type=int, default=20000)
    args = parser.parse_args()
    registry = register_correction_dataset(
        args.registry,
        args.dataset_root,
        cycle_id=args.cycle_id,
        max_sources=args.max_sources,
        max_frames=args.max_frames,
    )
    write_replay_registry(args.registry, registry)
    print(json.dumps(registry, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
