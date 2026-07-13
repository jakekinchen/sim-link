#!/usr/bin/env python3
"""Write or verify the canonical SO-101 processor contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.so101_processor import (
    CONTRACT_PATH,
    build_so101_processor_contract,
    verify_so101_processor_contract,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    output = REPO_ROOT / CONTRACT_PATH
    payload = build_so101_processor_contract(repo_root=REPO_ROOT)
    if args.verify:
        if load_strict_json(output) != payload:
            raise ValueError("Checked SO-101 processor contract drifted")
        status = "verified"
    else:
        if output.exists() or output.is_symlink():
            raise ValueError("SO-101 processor contract exists; use --verify")
        dump_canonical_json(output, payload)
        status = "written"
    verify_so101_processor_contract(load_strict_json(output), repo_root=REPO_ROOT)
    print(
        json.dumps(
            {
                "status": status,
                "identity_sha256": payload["identity_sha256"],
                "processor_name": payload["processor_name"],
                "random_round_trip_count": payload["verification"]["random_round_trip_count"],
                "maximum_round_trip_error": payload["verification"]["maximum_round_trip_error"],
                "simulation_training_ready": payload["simulation_training_ready"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
