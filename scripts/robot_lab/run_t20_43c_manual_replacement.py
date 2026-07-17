#!/usr/bin/env python3
"""Run or verify the one-use T20.43c-R2 manual replacement."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_43c_manual_replacement import (  # noqa: E402
    run_authorized_manual_replacement,
    verify_all_manual_replacement_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--started-at")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        result = verify_all_manual_replacement_outputs(repo_root=REPO_ROOT)
    else:
        if not args.started_at:
            parser.error("--started-at is required unless --verify is used")
        result = run_authorized_manual_replacement(
            started_at=args.started_at, repo_root=REPO_ROOT
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
