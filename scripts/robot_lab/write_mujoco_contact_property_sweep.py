#!/usr/bin/env python3
"""Write or verify the nominal MuJoCo contact-span/property sweep."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.mujoco_contact_property_sweep import (
    build_mujoco_contact_property_sweep,
    verify_mujoco_contact_property_sweep,
)


OUTPUT = REPO_ROOT / "configurations/robot_lab/mujoco_contact_property_sweep.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_mujoco_contact_property_sweep()
    if args.verify:
        stored = load_strict_json(OUTPUT)
        if stored != payload:
            raise ValueError("Checked MuJoCo contact property sweep drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("MuJoCo contact property sweep exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_mujoco_contact_property_sweep(load_strict_json(OUTPUT))
    print(
        json.dumps(
            {
                "status": status,
                "identity_sha256": payload["identity_sha256"],
                "contact_span_range_m": payload["contact_span_range_m"],
                "training_candidate_count": payload["training_grid"][
                    "candidate_count"
                ],
                "training_success_count": payload["training_success_count"],
                "selected_training_candidate": payload[
                    "selected_training_candidate"
                ],
                "holdout_success": payload["holdout"]["result"][
                    "unassisted_lift_clearance_maintained"
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
