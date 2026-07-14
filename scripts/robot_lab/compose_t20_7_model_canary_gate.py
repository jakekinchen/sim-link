#!/usr/bin/env python3
"""Compose four T20.7 per-model canaries into one immutable gate."""

from __future__ import annotations

import hashlib
import argparse
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.model_bakeoff import (
    MODEL_ORDER,
    build_model_canary_gate,
    verify_model_canary_gate,
)


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    run_root = args.run_root if args.run_root.is_absolute() else REPO_ROOT / args.run_root
    output_path = run_root / "run_summary.json"
    if output_path.exists():
        raise ValueError("T20.7 canary gate output is immutable")
    plan = load_strict_json(PLAN_PATH)
    results = []
    for model_id in MODEL_ORDER:
        path = run_root / f"{model_id}.json"
        payload = load_strict_json(path)
        results.append(
            (
                str(path.relative_to(REPO_ROOT)),
                payload,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    gate = build_model_canary_gate(plan, results)
    verify_model_canary_gate(gate, plan, results)
    dump_canonical_json(output_path, gate)
    print(f"wrote {output_path.relative_to(REPO_ROOT)} {gate['identity_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
