#!/usr/bin/env python3
"""Write or verify the deterministic T18.3 exact-state component manifest."""

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
from scenesmith.robot_lab.exact_state_components import (  # noqa: E402
    build_exact_state_components,
    verify_exact_state_components,
)


OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t18_3_exact_state_components.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--rewrite", action="store_true")
    args = parser.parse_args()
    if args.rewrite:
        raise ValueError("T18.3 exact-state components are immutable; write a reviewed successor")
    if args.verify:
        if not OUTPUT_PATH.is_file():
            raise ValueError("T18.3 exact-state component manifest is absent")
        manifest = load_strict_json(OUTPUT_PATH)
        verify_exact_state_components(manifest)
        if canonical_json_bytes(manifest) != canonical_json_bytes(build_exact_state_components()):
            raise ValueError("T18.3 exact-state component manifest bytes drifted")
        status = "verified"
    else:
        if OUTPUT_PATH.exists():
            raise ValueError("T18.3 exact-state component manifest exists; use --verify")
        manifest = build_exact_state_components()
        verify_exact_state_components(manifest)
        dump_canonical_json(OUTPUT_PATH, manifest)
        status = "written"
    print(
        json.dumps(
            {
                "status": status,
                "logical_cycle_window_count": manifest["logical_cycle_window_count"],
                "unique_frame_count": manifest["unique_frame_count"],
                "privileged_fields_available_to_actor": manifest[
                    "privileged_fields_available_to_actor"
                ],
                "training_eligible": manifest["training_eligible"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
