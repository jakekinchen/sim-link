#!/usr/bin/env python3
"""Build a deterministic source- and phase-balanced PI0.5 replay plan."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.balanced_replay import build_replay_plan, write_replay_plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--correction-sidecar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--correction-fraction", type=float, default=0.5)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    plan = build_replay_plan(
        args.dataset_root,
        args.correction_sidecar,
        draws=args.steps * args.batch_size,
        correction_fraction=args.correction_fraction,
        seed=args.seed,
    )
    write_replay_plan(args.output, plan)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
