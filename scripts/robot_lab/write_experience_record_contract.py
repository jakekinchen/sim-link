#!/usr/bin/env python3
"""Write or verify the immutable M17 experience-record contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.experience_records import (
    CONTRACT_PATH,
    build_experience_record_contract,
    verify_experience_record_contract,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    output = REPO_ROOT / CONTRACT_PATH
    payload = build_experience_record_contract(repo_root=REPO_ROOT)
    if args.verify:
        if load_strict_json(output) != payload:
            raise ValueError("Checked experience-record contract drifted")
        status = "verified"
    else:
        if output.exists() or output.is_symlink():
            raise ValueError("Experience-record contract exists; use --verify")
        dump_canonical_json(output, payload)
        status = "written"
    verify_experience_record_contract(load_strict_json(output), repo_root=REPO_ROOT)
    fixture = payload["fixture_projection"]
    print(
        json.dumps(
            {
                "status": status,
                "identity_sha256": payload["identity_sha256"],
                "rollout_id": fixture["raw_rollout"]["rollout_id"],
                "frame_count": len(fixture["frames"]),
                "training_eligible": fixture["training_eligible"],
                "quarantine_reason_count": len(fixture["quarantine_reasons"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
