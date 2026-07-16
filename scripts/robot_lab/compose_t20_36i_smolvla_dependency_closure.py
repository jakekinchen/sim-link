#!/usr/bin/env python3
"""Write or verify T20.36i's exact SmolVLA dependency-closure audit."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_36i_smolvla_dependency_closure import (  # noqa: E402
    verify_result_file,
    write_result,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = (
        verify_result_file(repo_root=REPO_ROOT)
        if args.verify
        else write_result(repo_root=REPO_ROOT)
    )
    print(result["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
