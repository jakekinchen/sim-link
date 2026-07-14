#!/usr/bin/env python3
"""Write or verify the deterministic central T20.8 acceptance decision."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.authority_composer import (
    DEFAULT_T20_8_RUN_ROOT,
    build_simulation_policy_acceptance_decision,
    verify_simulation_policy_acceptance_decision,
)


DEFAULT_OUTPUT = Path(
    "configurations/robot_lab/t20_8_simulation_policy_acceptance_decision.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_T20_8_RUN_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    expected = build_simulation_policy_acceptance_decision(
        repo_root=REPO_ROOT,
        run_root=args.run_root,
    )
    if args.check:
        observed = load_strict_json(output)
        verify_simulation_policy_acceptance_decision(
            observed,
            repo_root=REPO_ROOT,
            run_root=args.run_root,
        )
        if observed != expected:
            raise ValueError("T20.8 tracked acceptance decision drifted")
        print(f"verified {output.relative_to(REPO_ROOT)} {observed['identity_sha256']}")
        return 0
    if output.exists() and load_strict_json(output) != expected:
        raise ValueError("T20.8 acceptance output exists with different bytes")
    dump_canonical_json(output, expected)
    print(f"wrote {output.relative_to(REPO_ROOT)} {expected['identity_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
