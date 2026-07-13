#!/usr/bin/env python3
"""Write or verify the deterministic grasp pose-solver fixture."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.grasp_pose_solver import build_grasp_pose_solver_fixture, verify_grasp_pose_solver_fixture


OUTPUT = REPO_ROOT / "configurations/robot_lab/grasp_pose_solver.fixture.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_grasp_pose_solver_fixture()
    if args.verify:
        if load_strict_json(OUTPUT) != payload:
            raise ValueError("Checked grasp pose-solver fixture drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("Grasp pose-solver fixture exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_grasp_pose_solver_fixture(load_strict_json(OUTPUT))
    print(json.dumps({"status": status, "identity_sha256": payload["identity_sha256"], "candidate_count": payload["candidate_count"], "accepted_candidate_count": payload["accepted_candidate_count"], "simulation_training_ready": payload["simulation_training_ready"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
