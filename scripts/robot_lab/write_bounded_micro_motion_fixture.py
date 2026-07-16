#!/usr/bin/env python3
"""Write or verify the T19.2b bounded-motion plan and fixture result."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.bounded_micro_motion_harness import (
    build_bounded_micro_motion_plan,
    build_bounded_motion_fixture_result,
    verify_bounded_micro_motion_plan,
    verify_bounded_motion_fixture_result,
)

PLAN = ROOT / "configurations/robot_lab/t19_2b_bounded_micro_motion_plan.json"
RESULT = ROOT / "configurations/robot_lab/t19_2b_bounded_micro_motion_fixture.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        plan = load_strict_json(PLAN)
        result = load_strict_json(RESULT)
        verify_bounded_micro_motion_plan(plan, repo_root=ROOT)
        verify_bounded_motion_fixture_result(result, repo_root=ROOT)
        status = "verified"
    else:
        if PLAN.exists() or RESULT.exists():
            raise ValueError("Bounded motion artifacts exist; use --verify")
        plan = build_bounded_micro_motion_plan(repo_root=ROOT)
        result = build_bounded_motion_fixture_result(repo_root=ROOT)
        dump_canonical_json(PLAN, plan)
        dump_canonical_json(RESULT, result)
        status = "written"
    print(json.dumps({"status":status,"plan_identity_sha256":plan["identity_sha256"],"result_identity_sha256":result["identity_sha256"],"delta_degrees":plan["delta_degrees"],"write_count":result["write_count"],"returned_to_baseline":result["returned_to_baseline"],"hardware_accessed":result["hardware_accessed"]},indent=2,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
