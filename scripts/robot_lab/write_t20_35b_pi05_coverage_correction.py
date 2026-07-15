#!/usr/bin/env python3
"""Write or verify the optimizer-free T20.35b PI0.5 coverage correction."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_35b_pi05_coverage_correction import (  # noqa: E402
    verify_correction_file,
    write_correction,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = (
        verify_correction_file(repo_root=REPO_ROOT)
        if args.verify
        else write_correction(repo_root=REPO_ROOT)
    )
    print(result["identity_sha256"], result["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
