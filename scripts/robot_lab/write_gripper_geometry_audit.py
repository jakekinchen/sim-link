#!/usr/bin/env python3
"""Write or verify the compiled SO-101 gripper geometry audit."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.gripper_contact_semantics import (
    build_gripper_geometry_audit,
    verify_gripper_geometry_audit,
)


OUTPUT = REPO_ROOT / "configurations/robot_lab/gripper_geometry_audit.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_gripper_geometry_audit()
    if args.verify:
        stored = load_strict_json(OUTPUT)
        if stored != payload:
            raise ValueError("Checked gripper geometry audit drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("Gripper geometry audit exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_gripper_geometry_audit(load_strict_json(OUTPUT))
    print(json.dumps({
        "status": status,
        "identity_sha256": payload["identity_sha256"],
        "geom_count": len(payload["gripper_geoms"]),
        "minimum_aperture_m": payload["aperture_reference"]["minimum_m"],
        "maximum_aperture_m": payload["aperture_reference"]["maximum_m"],
        "synthetic_contact_proof": payload["synthetic_contact_convention_proof"]["aggregate_valid"],
        "simulation_training_ready": payload["simulation_training_ready"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
