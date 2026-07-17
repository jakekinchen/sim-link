#!/usr/bin/env python3
"""Materialize one model-free T20.43c-R2 authority epoch."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_43c_manual_replacement import (  # noqa: E402
    materialize_live_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--required-source-commit", required=True)
    parser.add_argument("--valid-from", required=True)
    parser.add_argument("--valid-until", required=True)
    args = parser.parse_args()
    bundle = materialize_live_authority(
        required_source_commit=args.required_source_commit,
        valid_from=args.valid_from,
        valid_until=args.valid_until,
        repo_root=REPO_ROOT,
    )
    print(
        json.dumps(
            {path: payload["identity_sha256"] for path, payload in bundle.items()},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
