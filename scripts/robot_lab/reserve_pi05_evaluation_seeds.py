#!/usr/bin/env python3
"""Reserve rotating development or one-use audit seeds before evaluation."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.seed_registry import reserve_evaluation_seeds, write_seed_registry


def _seeds(value: str) -> tuple[int, ...]:
    return tuple(int(item) for item in value.split(",") if item)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--cycle-id", required=True)
    parser.add_argument("--tier", choices=("development", "audit"), required=True)
    parser.add_argument("--seeds", type=_seeds, required=True)
    parser.add_argument("--development-pool", type=_seeds, required=True)
    parser.add_argument("--audit-pool", type=_seeds, required=True)
    parser.add_argument("--development-rotation-window", type=int, default=2)
    args = parser.parse_args()
    registry = reserve_evaluation_seeds(
        args.registry,
        cycle_id=args.cycle_id,
        tier=args.tier,
        seeds=args.seeds,
        development_pool=args.development_pool,
        audit_pool=args.audit_pool,
        development_rotation_window=args.development_rotation_window,
    )
    write_seed_registry(args.registry, registry)
    print(json.dumps(registry, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
