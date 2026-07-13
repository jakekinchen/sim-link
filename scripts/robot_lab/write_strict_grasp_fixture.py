#!/usr/bin/env python3
"""Write or verify the deterministic strict anchor-grasp evaluator fixture."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.strict_grasp import (
    build_strict_grasp_fixture,
    verify_strict_grasp_fixture,
)


OUTPUT = REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator.fixture.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = build_strict_grasp_fixture()
    if args.verify:
        stored = load_strict_json(OUTPUT)
        if stored != payload:
            raise ValueError("Checked strict grasp fixture drifted")
        status = "verified"
    else:
        if OUTPUT.exists() or OUTPUT.is_symlink():
            raise ValueError("Strict grasp fixture exists; use --verify")
        dump_canonical_json(OUTPUT, payload)
        status = "written"
    verify_strict_grasp_fixture(load_strict_json(OUTPUT))
    print(
        json.dumps(
            {
                "status": status,
                "identity_sha256": payload["identity_sha256"],
                "negative_count": len(payload["adversarial_negatives"]),
                "positive_strict_grasp_success": payload["positive"]["evaluation"][
                    "strict_grasp_success"
                ],
                "all_negatives_rejected": payload[
                    "all_negatives_rejected_for_expected_reason"
                ],
                "physical_twin_qualified": payload["physical_twin_qualified"],
                "simulation_training_ready": payload["simulation_training_ready"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
