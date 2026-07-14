#!/usr/bin/env python3
"""Compose or verify the signed T20.26 frame-zero variability gate."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.t20_25_frozen_candidate_localization import CANDIDATE_IDS  # noqa: E402
from scenesmith.robot_lab.t20_26_frame_zero_variability import (  # noqa: E402
    BATCH_IDS,
    build_gate,
    verify_gate,
)
from scripts.robot_lab.run_t20_25_frozen_candidate_localization import OUTPUT_ROOT  # noqa: E402


OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t20_26_frame_zero_variability_gate.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    batches = [
        load_strict_json(OUTPUT_ROOT / f"{candidate}_frame_zero_batch_{batch}.json")
        for candidate in CANDIDATE_IDS
        for batch in BATCH_IDS
    ]
    if args.verify:
        verify_gate(load_strict_json(OUTPUT_PATH), batches)
        print("T20.26 frame-zero variability gate verified")
        return 0
    if OUTPUT_PATH.exists():
        raise FileExistsError("T20.26 gate already exists; use --verify")
    gate = build_gate(batches)
    dump_canonical_json(OUTPUT_PATH, gate)
    print(
        gate["identity_sha256"],
        gate["candidate_summaries"],
        gate["selected_next_hypothesis"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
