#!/usr/bin/env python3
"""Write or verify T20.42/R0 pre-generation contract artifacts only."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_42_r0_dataset_construction import (  # noqa: E402
    verify_artifacts,
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing compact artifacts without rewriting them.",
    )
    args = parser.parse_args()
    result = (
        verify_artifacts(repo_root=REPO_ROOT)
        if args.verify
        else write_artifacts(repo_root=REPO_ROOT)
    )
    spec = result["construction_spec"]
    fixture = result["admission_fixture"]
    preflight = result["preflight"]
    print(
        json.dumps(
            {
                "status": "verified" if args.verify else "written",
                "construction_spec_identity_sha256": spec["identity_sha256"],
                "training_candidate_count": spec["construction"][
                    "training_candidate_count"
                ],
                "fresh_held_out_candidate_count": spec["construction"][
                    "fresh_held_out_candidate_count"
                ],
                "admission_fixture_identity_sha256": fixture["identity_sha256"],
                "preflight_identity_sha256": preflight["identity_sha256"],
                "generation_ready": preflight["generation_ready"],
                "r0_episode_generation_executed": preflight[
                    "r0_episode_generation_executed"
                ],
                "optimizer_training": preflight["optimizer_training"],
                "hardware_accessed": preflight["hardware_accessed"],
                "network_accessed": preflight["network_accessed"],
                "external_compute_started": preflight["external_compute_started"],
                "brev_compute_started": preflight["brev_compute_started"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
