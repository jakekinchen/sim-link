#!/usr/bin/env python3
"""Materialize or verify the T20.23 recovery-augmented LeRobotDataset."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    from scenesmith.robot_lab.t20_23_recovery_augmented_preflight import (
        materialize_dataset,
        verify_training_spec_file,
        write_training_spec,
    )
    if args.verify:
        spec = verify_training_spec_file(repo_root=REPO_ROOT)
    else:
        materialize_dataset(repo_root=REPO_ROOT)
        spec = write_training_spec(repo_root=REPO_ROOT)["training_spec"]
    print(spec["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
