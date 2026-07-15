#!/usr/bin/env python3
"""Materialize or verify the T20.35r full-path-correction spec."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_35r_full_path_self_consistency_correction import (  # noqa: E402
    verify_training_spec_file,
    write_training_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = (
        verify_training_spec_file(repo_root=REPO_ROOT)
        if args.verify
        else write_training_spec(repo_root=REPO_ROOT)
    )
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
