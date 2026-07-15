#!/usr/bin/env python3
"""Compose or verify the signed T20.32 divergence-localization report."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json  # noqa: E402
from scenesmith.robot_lab.t20_32_closed_loop_divergence import (  # noqa: E402
    ADAPTER_IDS,
    ALL_SEEDS,
    build_localization_report,
    verify_localization_report,
    verify_threshold_contract,
)
from scripts.robot_lab.materialize_t20_32_divergence_thresholds import (  # noqa: E402
    OUTPUT_PATH as THRESHOLD_PATH,
)
from scripts.robot_lab.run_t20_32_closed_loop_divergence import (  # noqa: E402
    OUTPUT_ROOT,
)


OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t20_32_divergence_localization_report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    threshold = load_strict_json(THRESHOLD_PATH)
    verify_threshold_contract(threshold)
    traces = [
        load_strict_json(OUTPUT_ROOT / f"{adapter}_seed_{seed}.json")
        for adapter in ADAPTER_IDS
        for seed in ALL_SEEDS
    ]
    if args.verify:
        verify_localization_report(
            load_strict_json(OUTPUT_PATH), threshold=threshold, traces=traces
        )
        print("T20.32 divergence-localization report verified")
        return 0
    if OUTPUT_PATH.exists():
        raise FileExistsError("T20.32 report already exists; use --verify")
    report = build_localization_report(threshold=threshold, traces=traces)
    dump_canonical_json(OUTPUT_PATH, report)
    print(
        report["identity_sha256"],
        report["lowest_unmet_capability_gate"],
        report["selected_next_gate_hypothesis"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
