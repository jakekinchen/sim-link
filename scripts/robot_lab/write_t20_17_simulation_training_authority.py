#!/usr/bin/env python3
"""Write or verify T20.17 central simulation-training authority."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--verify-live", action="store_true")
    args = parser.parse_args()
    activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    from scenesmith.robot_lab.t20_17_simulation_training_authority import (
        require_active_t20_17_authority,
        verify_production_authority,
        write_owner_training_grant,
        write_production_authority,
    )
    if args.write:
        write_owner_training_grant()
        payload = write_production_authority()
    elif args.verify:
        payload = verify_production_authority()
    else:
        payload = require_active_t20_17_authority()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
