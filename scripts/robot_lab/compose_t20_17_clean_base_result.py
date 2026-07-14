#!/usr/bin/env python3
"""Compose the signed T20.17 clean-base training/evaluation result gate."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import artifact_ref, dump_canonical_json, load_strict_json, verify_signed_payload
from scenesmith.robot_lab.t20_17_clean_base_campaign import (
    RESULT_GATE_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    build_result_gate,
    verify_run_summary,
)


def main() -> int:
    summary_path = RUN_ROOT / RUN_SUMMARY_PATH
    evaluation_path = RUN_ROOT / "held_out_seed_6_closed_loop.json"
    summary = load_strict_json(REPO_ROOT / summary_path)
    evaluation = load_strict_json(REPO_ROOT / evaluation_path)
    verify_signed_payload(summary, label="T20.17 training summary")
    verify_run_summary(summary)
    verify_signed_payload(evaluation, label="T20.17 held-out evaluation")
    rollout = evaluation.get("closed_loop")
    if not isinstance(rollout, dict):
        raise ValueError("T20.17 held-out closed loop is missing")
    gate = build_result_gate(
        training_ref=artifact_ref(path=summary_path, payload=summary, repo_root=REPO_ROOT),
        evaluation_ref=artifact_ref(path=evaluation_path, payload=evaluation, repo_root=REPO_ROOT),
        training_summary=summary,
        rollout=rollout,
    )
    dump_canonical_json(REPO_ROOT / RESULT_GATE_PATH, gate)
    print(gate["identity_sha256"], gate["decision"], gate["maximum_anchor_lift_m"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
