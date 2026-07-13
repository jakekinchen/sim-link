#!/usr/bin/env python3
"""Write or verify the geometry-derived unilateral-jaw grasp proof."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.geometry_derived_unilateral_grasp import build_geometry_derived_unilateral_grasp, verify_geometry_derived_unilateral_grasp

OUTPUT = REPO_ROOT / "configurations/robot_lab/geometry_derived_unilateral_grasp.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_geometry_derived_unilateral_grasp()
    if args.verify:
        if load_strict_json(OUTPUT) != payload:
            raise ValueError("Checked geometry-derived grasp proof drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("Geometry-derived grasp proof exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_geometry_derived_unilateral_grasp(load_strict_json(OUTPUT))
    print(json.dumps({
        "status": status,
        "identity_sha256": payload["identity_sha256"],
        "derived_close_target_rad": payload["derivation"]["derived_close_target_rad"],
        "unassisted_mujoco_grasp_success": payload["unassisted_mujoco_grasp_success"],
        "preclose_object_displacement_m": payload["trajectory"]["preclose_object_displacement_m"],
        "strict_v2_valid_frame_counts": payload["trajectory"]["full_lift_cycle"]["strict_v2_valid_frame_counts"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
