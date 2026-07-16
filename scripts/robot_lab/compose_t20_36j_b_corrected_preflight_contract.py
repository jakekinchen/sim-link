#!/usr/bin/env python3
"""Write or verify T20.36j-B's corrected preflight contract."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (  # noqa: E402
    verify_contract_file,
    write_contract,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = (
        verify_contract_file(repo_root=REPO_ROOT)
        if args.verify
        else write_contract(repo_root=REPO_ROOT)
    )
    print(result["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
