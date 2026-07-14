#!/usr/bin/env python3
"""Write or verify the deterministic T18.1 episode-first window sample."""

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
from scenesmith.robot_lab.episode_first_window_sampling import (  # noqa: E402
    build_episode_first_window_sample,
    verify_episode_first_window_sample,
)


OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t18_1_episode_first_window_sample.json"


def _write() -> dict:
    if OUTPUT_PATH.exists():
        raise ValueError("T18.1 episode-first sample already exists; use --verify")
    manifest = build_episode_first_window_sample()
    verify_episode_first_window_sample(manifest)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(OUTPUT_PATH, manifest)
    return manifest


def _verify() -> dict:
    if not OUTPUT_PATH.is_file():
        raise ValueError("T18.1 episode-first sample is absent")
    stored = load_strict_json(OUTPUT_PATH)
    verify_episode_first_window_sample(stored)
    regenerated = build_episode_first_window_sample()
    if canonical_json_bytes(stored) != canonical_json_bytes(regenerated):
        raise ValueError("T18.1 episode-first sample bytes drifted")
    return stored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument(
        "--rewrite",
        action="store_true",
        help="Rejected: source windows are immutable and this is a new selection view.",
    )
    args = parser.parse_args()
    if args.rewrite:
        raise ValueError("T18.1 source windows are immutable; write a new reviewed selection")
    manifest = _verify() if args.verify else _write()
    print(
        json.dumps(
            {
                "status": "verified" if args.verify else "written",
                "sampling_seed": manifest["sampling_seed"],
                "configured_bucket_count": manifest["configured_bucket_count"],
                "realized_window_count": manifest["realized_window_count"],
                "unique_window_ratio": manifest["unique_window_ratio"],
                "training_eligible": manifest["training_eligible"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
