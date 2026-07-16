#!/usr/bin/env python3
"""Materialize or verify the reviewed T20.43 Gate A/authority bundle."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_43_r1_act_materialization import (  # noqa: E402
    materialize_live_authority,
    verify_materialized_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--required-source-commit")
    parser.add_argument("--valid-from")
    parser.add_argument("--valid-until")
    args = parser.parse_args()
    if args.verify:
        bundle = verify_materialized_authority(repo_root=REPO_ROOT)
    else:
        if not all((args.required_source_commit, args.valid_from, args.valid_until)):
            parser.error(
                "materialization requires --required-source-commit, --valid-from, and --valid-until"
            )
        bundle = materialize_live_authority(
            required_source_commit=args.required_source_commit,
            valid_from=args.valid_from,
            valid_until=args.valid_until,
            repo_root=REPO_ROOT,
        )
    for path, payload in bundle.items():
        print(path, payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
