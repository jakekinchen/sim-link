#!/usr/bin/env python3
"""Write the deterministic T20.7 four-model bake-off plan."""

from __future__ import annotations

import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.model_bakeoff import (
    build_model_bakeoff_plan,
    verify_model_bakeoff_plan,
)


TRAINING_SPEC_PATH = REPO_ROOT / "configurations/robot_lab/t20_1_simulation_training_spec.json"
SEMANTIC_PATH = REPO_ROOT / "configurations/robot_lab/t20_6_phase_outcome_evaluation.json"
STRICT_V2_PATH = REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json"
OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"


def main() -> int:
    training_spec = load_strict_json(TRAINING_SPEC_PATH)
    semantic = load_strict_json(SEMANTIC_PATH)
    strict_v2 = load_strict_json(STRICT_V2_PATH)
    payload = build_model_bakeoff_plan(
        training_spec, semantic, strict_v2, repo_root=REPO_ROOT
    )
    verify_model_bakeoff_plan(
        payload, training_spec, semantic, strict_v2, repo_root=REPO_ROOT
    )
    dump_canonical_json(OUTPUT_PATH, payload)
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} {payload['identity_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
