#!/usr/bin/env python3
"""Write or verify the immutable T18.4 snapshot branch manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.snapshot_branch_corrections import (  # noqa: E402
    build_snapshot_branch_manifest,
    verify_snapshot_branch_manifest,
)


OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t18_4_snapshot_branch_corrections.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--rewrite", action="store_true")
    args = parser.parse_args()
    if args.rewrite:
        raise ValueError("T18.4 snapshots are immutable; write a reviewed successor")
    if args.verify:
        if not OUTPUT_PATH.is_file():
            raise ValueError("T18.4 snapshot branch manifest is absent")
        manifest = load_strict_json(OUTPUT_PATH)
        verify_snapshot_branch_manifest(manifest)
        if canonical_json_bytes(manifest) != canonical_json_bytes(build_snapshot_branch_manifest()):
            raise ValueError("T18.4 snapshot branch manifest bytes drifted")
        status = "verified"
    else:
        if OUTPUT_PATH.exists():
            raise ValueError("T18.4 snapshot branch manifest exists; use --verify")
        manifest = build_snapshot_branch_manifest()
        verify_snapshot_branch_manifest(manifest)
        dump_canonical_json(OUTPUT_PATH, manifest)
        status = "written"
    print(
        json.dumps(
            {
                "status": status,
                "snapshot_count": manifest["snapshot_count"],
                "base_branch_count": manifest["base_branch_count"],
                "correction_event_count": manifest["correction_event_count"],
                "training_eligible": manifest["training_eligible"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
