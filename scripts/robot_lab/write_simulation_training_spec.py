#!/usr/bin/env python3
"""Write or independently verify the bounded T20.1 simulation training spec."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.simulation_training_spec import (
    SPEC_PATH,
    TENSOR_VIEW_PATH,
    verify_training_spec_file,
    write_training_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--verify", action="store_true")
    parser.add_argument("--spec", type=Path, default=SPEC_PATH)
    parser.add_argument("--tensor-view", type=Path, default=TENSOR_VIEW_PATH)
    args = parser.parse_args()
    if args.write:
        payload = write_training_spec(
            repo_root=REPO_ROOT,
            spec_path=args.spec,
            tensor_view_path=args.tensor_view,
        )
    else:
        payload = verify_training_spec_file(
            repo_root=REPO_ROOT,
            spec_path=args.spec,
            tensor_view_path=args.tensor_view,
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
