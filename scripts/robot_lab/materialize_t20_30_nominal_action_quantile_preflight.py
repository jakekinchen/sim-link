#!/usr/bin/env python3
"""Materialize or verify the T20.30 nominal-action-quantile preflight."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    from scenesmith.robot_lab.t20_30_nominal_action_quantile_preflight import (
        materialize_preflight,
        verify_preflight,
    )

    result = (
        verify_preflight(repo_root=REPO_ROOT)
        if args.verify
        else materialize_preflight(repo_root=REPO_ROOT)
    )
    print(
        json.dumps(
            {
                "manifest_identity_sha256": result["manifest"]["identity_sha256"],
                "training_spec_identity_sha256": result["training_spec"][
                    "identity_sha256"
                ],
                "optimizer_training": False,
                "physical_actuation": False,
                "external_compute_started": False,
                "brev_compute_started": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
