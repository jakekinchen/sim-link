#!/usr/bin/env python3
"""Write or verify the production T20.1 simulation-training authority decision."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.simulation_training_authority import (
    DECISION_PATH,
    OWNER_GRANT_PATH,
    REQUEST_PATH,
    verify_production_authority,
    write_owner_training_grant,
    write_production_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--verify", action="store_true")
    parser.add_argument("--owner-grant", type=Path, default=OWNER_GRANT_PATH)
    parser.add_argument("--request", type=Path, default=REQUEST_PATH)
    parser.add_argument("--decision", type=Path, default=DECISION_PATH)
    args = parser.parse_args()
    if args.write:
        write_owner_training_grant(repo_root=REPO_ROOT, owner_grant_path=args.owner_grant)
        payload = write_production_authority(
            repo_root=REPO_ROOT,
            owner_grant_path=args.owner_grant,
            request_path=args.request,
            decision_path=args.decision,
        )
    else:
        payload = verify_production_authority(
            repo_root=REPO_ROOT,
            owner_grant_path=args.owner_grant,
            request_path=args.request,
            decision_path=args.decision,
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
