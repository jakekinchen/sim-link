#!/usr/bin/env python3
"""Write or verify the read-only T20.36c local policy-track preflight."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_36c_local_policy_track_preflight import (  # noqa: E402
    verify_audit_file,
    write_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    audit = verify_audit_file() if args.verify else write_audit()
    print(audit["identity_sha256"], audit["selected_next_hypothesis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
