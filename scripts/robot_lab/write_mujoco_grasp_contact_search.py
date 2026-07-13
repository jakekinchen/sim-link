#!/usr/bin/env python3
"""Write or verify the deterministic low-impact two-jaw MuJoCo search."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.mujoco_grasp_contact_search import (
    build_mujoco_grasp_contact_search,
    verify_mujoco_grasp_contact_search,
)


OUTPUT = REPO_ROOT / "configurations/robot_lab/mujoco_grasp_contact_search.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_mujoco_grasp_contact_search()
    if args.verify:
        stored = load_strict_json(OUTPUT)
        if stored != payload:
            raise ValueError("Checked MuJoCo grasp contact search drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("MuJoCo grasp contact search exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_mujoco_grasp_contact_search(load_strict_json(OUTPUT))
    selected = payload["selected_candidate"]
    validation = payload["selected_unassisted_validation"]["summary"]
    print(
        json.dumps(
            {
                "status": status,
                "identity_sha256": payload["identity_sha256"],
                "candidate_count": payload["candidate_count"],
                "selected_candidate": selected,
                "selected_validation_two_pass_exact_determinism": payload[
                    "selected_validation_two_pass_exact_determinism"
                ],
                "unassisted_lift_clearance_maintained": validation[
                    "unassisted_lift_clearance_maintained"
                ],
                "lift_hold_two_jaw_frames": validation[
                    "lift_hold_two_jaw_frames"
                ],
                "simulation_training_ready": payload["simulation_training_ready"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
