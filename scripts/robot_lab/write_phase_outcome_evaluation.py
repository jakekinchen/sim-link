#!/usr/bin/env python3
"""Write the deterministic T20.6 outcome-versus-strict fixture."""

from __future__ import annotations

import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.phase_outcome_evaluation import (
    build_phase_outcome_fixture,
    verify_phase_outcome_fixture,
)


SOURCE_PATH = (
    REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json"
)
OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t20_6_phase_outcome_evaluation.json"


def main() -> int:
    source = load_strict_json(SOURCE_PATH)
    payload = build_phase_outcome_fixture(source)
    verify_phase_outcome_fixture(payload, source)
    dump_canonical_json(OUTPUT_PATH, payload)
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} {payload['identity_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
