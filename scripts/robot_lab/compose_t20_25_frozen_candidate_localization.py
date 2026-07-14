#!/usr/bin/env python3
"""Compose or verify the signed T20.25 frozen-candidate localization gate."""

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
from scenesmith.robot_lab.t20_25_frozen_candidate_localization import (  # noqa: E402
    CANDIDATE_IDS,
    HELD_OUT_SEEDS,
    build_localization_gate,
    verify_localization_gate,
)
from scripts.robot_lab.run_t20_25_frozen_candidate_localization import OUTPUT_ROOT  # noqa: E402


OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t20_25_frozen_candidate_localization_gate.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    traces = [
        load_strict_json(OUTPUT_ROOT / f"{candidate}_seed_{seed}.json")
        for candidate in CANDIDATE_IDS
        for seed in HELD_OUT_SEEDS
    ]
    if args.verify:
        verify_localization_gate(load_strict_json(OUTPUT_PATH), traces)
        print("T20.25 localization gate verified")
        return 0
    if OUTPUT_PATH.exists():
        raise FileExistsError("T20.25 localization gate already exists; use --verify")
    gate = build_localization_gate(traces)
    dump_canonical_json(OUTPUT_PATH, gate)
    print(
        gate["identity_sha256"],
        gate["recovery_relative_effect"],
        gate["selected_next_hypothesis"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
