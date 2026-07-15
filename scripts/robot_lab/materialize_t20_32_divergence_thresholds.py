#!/usr/bin/env python3
"""Materialize or verify the signed T20.32 divergence thresholds."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json  # noqa: E402
from scenesmith.robot_lab.t20_32_closed_loop_divergence import (  # noqa: E402
    build_threshold_contract,
    verify_threshold_contract,
)


OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t20_32_divergence_thresholds.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify_threshold_contract(load_strict_json(OUTPUT_PATH))
        print("T20.32 divergence thresholds verified")
        return 0
    if OUTPUT_PATH.exists():
        raise FileExistsError("T20.32 divergence thresholds already exist; use --verify")
    payload = build_threshold_contract()
    dump_canonical_json(OUTPUT_PATH, payload)
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
