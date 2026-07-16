#!/usr/bin/env python3
"""Write or verify T20.36h's central simulation-training authority."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_36h_simulation_training_authority import (  # noqa: E402
    verify_authority,
    write_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = (
        verify_authority(repo_root=REPO_ROOT)
        if args.verify
        else write_authority(repo_root=REPO_ROOT)
    )
    print(result["decision"]["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
