#!/usr/bin/env python3
"""Write or verify the deterministic offline no-write servo-census fixture."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.readonly_servo_census import (
    verify_census_fixture_artifacts,
    write_census_fixture_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the tracked artifacts instead of rewriting them.",
    )
    args = parser.parse_args()
    if args.verify:
        bundle = verify_census_fixture_artifacts(repo_root=REPO_ROOT)
        status = "verified"
    else:
        bundle = write_census_fixture_artifacts(repo_root=REPO_ROOT)
        status = "written"

    result = bundle["result"]
    print(
        json.dumps(
            {
                "status": status,
                "contract_identity_sha256": bundle["contract"]["identity_sha256"],
                "trace_identity_sha256": bundle["trace"]["identity_sha256"],
                "result_identity_sha256": result["identity_sha256"],
                "proof_label": result["proof_label"],
                "conformance_state": result["conformance_state"],
                "servo_count": len(result["servos"]),
                "operation_counts": result["operation_counts"],
                "hardware_opened": result["hardware_opened"],
                "physical_follower_commanded": result["physical_follower_commanded"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
