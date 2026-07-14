#!/usr/bin/env python3
"""Compose or verify the T20.14 dataset-normalized PI0.5 result gate."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.dataset_normalized_pi05_gate import (
    build_dataset_normalized_pi05_gate,
    verify_dataset_normalized_pi05_gate,
)


ROOT = REPO_ROOT / "outputs/robot_lab/t20_14_dataset_normalized_pi05_run_001"
TRAINING = ROOT / "run_summary.json"
CLOSED_LOOP = ROOT / "closed_loop.json"
BASELINE = REPO_ROOT / "outputs/robot_lab/t20_11_action_localization/pi05.json"
OUTPUT = ROOT / "evaluation_summary.json"


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs():
    return (
        _relative(TRAINING),
        load_strict_json(TRAINING),
        _sha(TRAINING),
        _relative(CLOSED_LOOP),
        load_strict_json(CLOSED_LOOP),
        _sha(CLOSED_LOOP),
        _relative(BASELINE),
        load_strict_json(BASELINE),
        _sha(BASELINE),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    inputs = _inputs()
    if args.check:
        stored = load_strict_json(OUTPUT)
        verify_dataset_normalized_pi05_gate(stored, *inputs)
        print("verified", _relative(OUTPUT), stored["identity_sha256"])
        return 0
    if OUTPUT.exists():
        raise ValueError("T20.14 evaluation summary exists; use --check")
    payload = build_dataset_normalized_pi05_gate(*inputs)
    dump_canonical_json(OUTPUT, payload)
    print("wrote", _relative(OUTPUT), payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
