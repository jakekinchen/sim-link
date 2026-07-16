#!/usr/bin/env python3
"""Run or independently verify the sole T20.44/R2 SmolVLA standard attempt."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_44_r2_smolvla_runner import (  # noqa: E402
    run_authorized_attempt,
    verify_all_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--started-at")
    args = parser.parse_args()
    if args.run and not args.started_at:
        parser.error("--run requires --started-at with a UTC offset")
    result = (
        run_authorized_attempt(started_at=args.started_at, repo_root=REPO_ROOT)
        if args.run
        else verify_all_outputs(repo_root=REPO_ROOT)
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "attempt_count",
                    "optimizer_update_count",
                    "checkpoint_count",
                    "rollout_count",
                    "gate_c_passed",
                    "first_gate_c_pass",
                    "identity_sha256",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
