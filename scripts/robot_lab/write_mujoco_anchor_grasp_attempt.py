#!/usr/bin/env python3
"""Write or verify the deterministic nominal-anchor MuJoCo grasp attempt."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.mujoco_anchor_grasp import (
    build_mujoco_anchor_grasp_attempt,
    verify_mujoco_anchor_grasp_attempt,
)


OUTPUT = REPO_ROOT / "configurations/robot_lab/mujoco_anchor_grasp_attempt.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_mujoco_anchor_grasp_attempt()
    if args.verify:
        stored = load_strict_json(OUTPUT)
        if stored != payload:
            raise ValueError("Checked MuJoCo anchor grasp attempt drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("MuJoCo anchor grasp attempt exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_mujoco_anchor_grasp_attempt(load_strict_json(OUTPUT))
    print(
        json.dumps(
            {
                "status": status,
                "identity_sha256": payload["identity_sha256"],
                "raw_frame_count": payload["raw_frame_count"],
                "two_pass_exact_determinism": payload["two_pass_exact_determinism"],
                "mujoco_report_status": payload["mujoco_report"]["status"],
                "strict_grasp_success": payload["strict_evaluation"][
                    "strict_grasp_success"
                ],
                "failure_reasons": payload["strict_evaluation"]["failure_reasons"],
                "simulation_training_ready": payload["simulation_training_ready"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
