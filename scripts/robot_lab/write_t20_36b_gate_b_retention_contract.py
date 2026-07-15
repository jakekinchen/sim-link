#!/usr/bin/env python3
"""Write or verify the pure T20.36b Gate B retention contract fixture."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_36b_gate_b_retention_contract import (  # noqa: E402
    verify_fixture_artifact_files,
    write_fixture_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    spec, decision = (
        verify_fixture_artifact_files(repo_root=REPO_ROOT)
        if args.verify
        else write_fixture_artifacts(repo_root=REPO_ROOT)
    )
    print(spec["identity_sha256"], decision["identity_sha256"], decision["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
