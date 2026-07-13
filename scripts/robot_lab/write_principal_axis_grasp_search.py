#!/usr/bin/env python3
"""Write or verify the principal-axis-aligned grasp search."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.principal_axis_grasp_search import (
    build_principal_axis_grasp_search,
    verify_principal_axis_grasp_search,
)


OUTPUT = REPO_ROOT / "configurations/robot_lab/principal_axis_grasp_search.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_principal_axis_grasp_search()
    if args.verify:
        if load_strict_json(OUTPUT) != payload:
            raise ValueError("Checked principal-axis search drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("Principal-axis search exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_principal_axis_grasp_search(load_strict_json(OUTPUT))
    print(
        json.dumps(
            {
                "status": status,
                "identity_sha256": payload["identity_sha256"],
                "candidate_count": payload["training_candidate_count"],
                "aligned_candidates": payload["aligned_candidate_count"],
                "bilateral_contact_candidates": payload[
                    "bilateral_contact_candidate_count"
                ],
                "eligible_count": payload["geometry_eligible_count"],
                "holdout_eligible": payload["holdout"]["candidate"][
                    "geometry_eligible"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
