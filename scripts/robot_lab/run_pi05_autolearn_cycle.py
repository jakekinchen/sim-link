#!/usr/bin/env python3
"""Run one bounded PI0.5 DAgger, training, evaluation, and promotion cycle."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.autolearn_cycle import CycleRunner, load_cycle_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = args.config.resolve()
    config = load_cycle_config(config_path)
    runner = CycleRunner(config, repo_root=REPO_ROOT, config_path=config_path)
    try:
        manifest = runner.run(dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001
        print(f"autolearn cycle failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
