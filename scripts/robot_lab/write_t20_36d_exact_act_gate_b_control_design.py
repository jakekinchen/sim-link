#!/usr/bin/env python3
"""Write or verify the pure T20.36d ACT Gate B control design."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_36d_exact_act_gate_b_control_design import (  # noqa: E402
    verify_spec_file,
    write_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    spec = verify_spec_file() if args.verify else write_spec()
    print(spec["identity_sha256"], spec["execution_task_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
