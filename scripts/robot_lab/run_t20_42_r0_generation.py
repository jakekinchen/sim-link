#!/usr/bin/env python3
"""Consume the sole permit and run the fixed T20.42/R0 manifest."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_42b_r0_runner import (  # noqa: E402
    run_fixed_manifest,
    verify_r0_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--started-at")
    args = parser.parse_args()
    if args.run:
        if not args.started_at:
            parser.error("--run requires --started-at")
        outputs = run_fixed_manifest(started_at=args.started_at, repo_root=REPO_ROOT)
    else:
        outputs = verify_r0_outputs(repo_root=REPO_ROOT)
    result = outputs["result"]
    print(
        json.dumps(
            {
                "status": result["status"],
                "result_identity_sha256": result["identity_sha256"],
                "configured_candidate_count": result["configured_candidate_count"],
                "completed_episode_count": result["completed_episode_count"],
                "new_training_strict_success_count": result[
                    "new_training_strict_success_count"
                ],
                "fresh_held_out_strict_success_count": result[
                    "fresh_held_out_strict_success_count"
                ],
                "dataset_materialized": result["dataset_materialized"],
                "attempt_count": result["attempt_count"],
                "retry_authorized": result["retry_authorized"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "verified_success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
