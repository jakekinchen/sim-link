#!/usr/bin/env python3
"""Write or verify the tracked robot-lab dependency lock."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.robotics_dependency_lock import (
    build_robotics_dependency_lock,
    verify_robotics_dependency_lock,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("configurations/robot_lab/pi05_robotics_dependency_lock.json"),
    )
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    if args.verify:
        payload = json.loads(output.read_text(encoding="utf-8"))
        verify_robotics_dependency_lock(payload, repo_root=REPO_ROOT)
    else:
        payload = build_robotics_dependency_lock(repo_root=REPO_ROOT)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(output)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
