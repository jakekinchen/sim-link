#!/usr/bin/env python3
"""Compose the four observed T20.7 policy rollouts into a signed gate."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.model_bakeoff import MODEL_ORDER
from scenesmith.robot_lab.model_bakeoff_evaluation import (
    build_model_evaluation_gate,
    verify_model_evaluation_gate,
)


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    run_root = _resolve(args.run_root)
    output = run_root / "evaluation_summary.json"
    if output.exists():
        raise ValueError("T20.7 model evaluation gate is immutable")
    plan = load_strict_json(PLAN_PATH)
    training_gate = load_strict_json(run_root / "run_summary.json")
    results = []
    for model_id in MODEL_ORDER:
        training_path = run_root / model_id / "run_summary.json"
        evaluation_path = run_root / "closed_loop" / f"{model_id}.json"
        training = load_strict_json(training_path)
        evaluation = load_strict_json(evaluation_path)
        results.append(
            (
                str(evaluation_path.relative_to(REPO_ROOT)),
                evaluation,
                _sha(evaluation_path),
                training,
                _sha(training_path),
            )
        )
    gate = build_model_evaluation_gate(plan, training_gate, results)
    verify_model_evaluation_gate(gate, plan, training_gate, results)
    dump_canonical_json(output, gate)
    print(output.relative_to(REPO_ROOT), gate["identity_sha256"])
    return 0


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
