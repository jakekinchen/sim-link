#!/usr/bin/env python3
"""Run the bounded T20.24 official-LeRobot local-MPS campaign."""

from __future__ import annotations

import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack


def main() -> int:
    activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    from scenesmith.robot_lab.t20_24_recovery_augmented_campaign import run_campaign

    summary = run_campaign(repo_root=REPO_ROOT, python=Path(sys.executable))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
