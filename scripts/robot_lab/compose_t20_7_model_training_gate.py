#!/usr/bin/env python3
"""Compose four T20.7 exact-sample optimizer results into one immutable gate."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.model_bakeoff import (
    MODEL_ORDER,
    build_model_training_gate,
    verify_model_training_gate,
)


PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    run_root = (
        args.run_root if args.run_root.is_absolute() else REPO_ROOT / args.run_root
    )
    output_path = run_root / "run_summary.json"
    if output_path.exists():
        raise ValueError("T20.7 model training gate output is immutable")
    plan = load_strict_json(PLAN_PATH)
    results = []
    for model_id in MODEL_ORDER:
        model_root = run_root / model_id
        path = model_root / "run_summary.json"
        payload = load_strict_json(path)
        _verify_checkpoint_files(model_root, payload["checkpoint_files"])
        results.append(
            (
                str(path.relative_to(REPO_ROOT)),
                payload,
                _sha(path),
            )
        )
    gate = build_model_training_gate(plan, results)
    verify_model_training_gate(gate, plan, results)
    dump_canonical_json(output_path, gate)
    print(f"wrote {output_path.relative_to(REPO_ROOT)} {gate['identity_sha256']}")
    return 0


def _verify_checkpoint_files(model_root: Path, files: dict) -> None:
    root = model_root.resolve()
    for relative_path, expected in files.items():
        path = (model_root / relative_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("T20.7 checkpoint path is unavailable or escapes its run")
        if _sha(path) != expected["sha256"] or path.stat().st_size != expected[
            "size_bytes"
        ]:
            raise ValueError("T20.7 checkpoint bytes drifted from the signed result")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
