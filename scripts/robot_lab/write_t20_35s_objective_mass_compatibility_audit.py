#!/usr/bin/env python3
"""Write or verify the model-free T20.35s objective-mass audit."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_35s_objective_mass_compatibility_audit import (  # noqa: E402
    verify_audit_file,
    write_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    audit = (
        verify_audit_file(repo_root=REPO_ROOT)
        if args.verify
        else write_audit(repo_root=REPO_ROOT)
    )
    print(audit["identity_sha256"], audit["selected_next_hypothesis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
