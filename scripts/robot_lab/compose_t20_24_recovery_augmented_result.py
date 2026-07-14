#!/usr/bin/env python3
"""Compose the signed T20.24 two-seed training/evaluation result gate."""

from __future__ import annotations

import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_24_recovery_augmented_campaign import (
    HELD_OUT_SEEDS,
    RESULT_GATE_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    build_result_gate,
    verify_run_summary,
)


def main() -> int:
    summary_path = RUN_ROOT / RUN_SUMMARY_PATH
    summary = load_strict_json(REPO_ROOT / summary_path)
    verify_signed_payload(summary, label="T20.24 training summary")
    verify_run_summary(summary)
    refs = []
    rollouts = []
    for seed in HELD_OUT_SEEDS:
        relative = RUN_ROOT / f"held_out_seed_{seed}_closed_loop.json"
        evaluation = load_strict_json(REPO_ROOT / relative)
        verify_signed_payload(evaluation, label=f"T20.24 seed-{seed} evaluation")
        if evaluation.get("held_out_seed") != seed:
            raise ValueError("T20.24 evaluation seed wrapper drifted")
        rollout = evaluation.get("closed_loop")
        if not isinstance(rollout, dict):
            raise ValueError("T20.24 held-out closed loop is missing")
        refs.append(
            {
                "seed": seed,
                **artifact_ref(path=relative, payload=evaluation, repo_root=REPO_ROOT),
            }
        )
        rollouts.append(rollout)
    gate = build_result_gate(
        training_ref=artifact_ref(
            path=summary_path, payload=summary, repo_root=REPO_ROOT
        ),
        evaluation_refs=refs,
        training_summary=summary,
        evaluations=rollouts,
    )
    dump_canonical_json(REPO_ROOT / RESULT_GATE_PATH, gate)
    print(
        gate["identity_sha256"],
        gate["decision"],
        gate["strict_success_count"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
