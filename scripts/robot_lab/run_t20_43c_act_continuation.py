#!/usr/bin/env python3
"""Execute or verify the sole T20.43c ACT continuation."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_43c_act_continuation_runner import (  # noqa: E402
    run_authorized_continuation,
    verify_all_continuation_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--started-at")
    args = parser.parse_args()
    if args.verify:
        payload = verify_all_continuation_outputs(repo_root=REPO_ROOT)
    else:
        if not args.started_at:
            parser.error("execution requires --started-at")
        payload = run_authorized_continuation(
            started_at=args.started_at, repo_root=REPO_ROOT
        )
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
