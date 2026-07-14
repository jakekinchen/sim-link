#!/usr/bin/env python3
"""Compose or verify the T20.16 hybrid gripper rollout gate."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.hybrid_gripper_postprocessor_gate import (
    build_hybrid_gripper_postprocessor_gate,
    verify_hybrid_gripper_postprocessor_gate,
)


RESULT = REPO_ROOT / "outputs/robot_lab/t20_16_hybrid_gripper_postprocessor_rollout.json"
OUTPUT = REPO_ROOT / "outputs/robot_lab/t20_16_hybrid_gripper_postprocessor_gate.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = str(RESULT.relative_to(REPO_ROOT))
    result = load_strict_json(RESULT)
    file_sha256 = hashlib.sha256(RESULT.read_bytes()).hexdigest()
    if args.check:
        stored = load_strict_json(OUTPUT)
        verify_hybrid_gripper_postprocessor_gate(
            stored, path, result, file_sha256
        )
        print("verified", OUTPUT.relative_to(REPO_ROOT), stored["identity_sha256"])
        return 0
    if OUTPUT.exists():
        raise ValueError("T20.16 gate already exists; use --check")
    payload = build_hybrid_gripper_postprocessor_gate(path, result, file_sha256)
    dump_canonical_json(OUTPUT, payload)
    print("wrote", OUTPUT.relative_to(REPO_ROOT), payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
