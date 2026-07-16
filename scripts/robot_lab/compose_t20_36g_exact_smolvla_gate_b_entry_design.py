#!/usr/bin/env python3
"""Write or verify T20.36g's exact SmolVLA Gate B entry design."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (  # noqa: E402
    verify_spec_file,
    write_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    spec = (
        verify_spec_file(repo_root=REPO_ROOT)
        if args.verify
        else write_spec(repo_root=REPO_ROOT)
    )
    print(spec["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
