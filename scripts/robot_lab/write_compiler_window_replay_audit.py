#!/usr/bin/env python3
"""Write or verify the deterministic T17.7 replay-audit manifest."""

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
from scenesmith.robot_lab.compiler_window_replay_audit import (  # noqa: E402
    build_replay_audit,
    verify_replay_audit,
)


OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t17_7_compiler_window_replay_audit.json"


def _write() -> dict:
    if OUTPUT_PATH.exists():
        raise ValueError("T17.7 replay audit already exists; use --verify")
    manifest = build_replay_audit()
    verify_replay_audit(manifest)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(OUTPUT_PATH, manifest)
    return manifest


def _verify() -> dict:
    if not OUTPUT_PATH.is_file():
        raise ValueError("T17.7 replay audit is absent")
    stored = load_strict_json(OUTPUT_PATH)
    verify_replay_audit(stored)
    regenerated = build_replay_audit()
    if canonical_json_bytes(stored) != canonical_json_bytes(regenerated):
        raise ValueError("T17.7 replay audit bytes drifted")
    return stored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument(
        "--rewrite",
        action="store_true",
        help="Rejected: T17.7 is a new read-only audit; raw evidence is immutable.",
    )
    args = parser.parse_args()
    if args.rewrite:
        raise ValueError("T17.7 raw evidence is immutable; write a new reviewed audit")
    manifest = _verify() if args.verify else _write()
    print(
        json.dumps(
            {
                "status": "verified" if args.verify else "written",
                "selected_window_count": manifest["selected_window_count"],
                "selected_window_count_by_horizon": manifest[
                    "selected_window_count_by_horizon"
                ],
                "model_loaded": manifest["model_loaded"],
                "model_inference_executed": manifest["model_inference_executed"],
                "training_eligible": manifest["training_eligible"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
