#!/usr/bin/env python3
"""Materialize or verify the compact T20.42/R0 pre-run authority boundary."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_42b_r0_materialization import (  # noqa: E402
    materialize_live_authority,
    verify_materialized_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--required-source-commit")
    parser.add_argument("--valid-from")
    parser.add_argument("--valid-until")
    args = parser.parse_args()
    if args.write:
        if not all((args.required_source_commit, args.valid_from, args.valid_until)):
            parser.error("--write requires source commit and validity window")
        bundle = materialize_live_authority(
            required_source_commit=args.required_source_commit,
            valid_from=args.valid_from,
            valid_until=args.valid_until,
            repo_root=REPO_ROOT,
        )
    else:
        bundle = verify_materialized_authority(repo_root=REPO_ROOT)
    print(
        json.dumps(
            {
                "status": "verified",
                "artifact_count": len(bundle),
                "artifacts": {
                    path: payload["identity_sha256"] for path, payload in bundle.items()
                },
                "attempt_marker_exists": False,
                "r0_episode_generation_executed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
