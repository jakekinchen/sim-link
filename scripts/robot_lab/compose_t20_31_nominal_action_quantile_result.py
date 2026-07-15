#!/usr/bin/env python3
"""Compose or verify the signed T20.31 training/evaluation result gate."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

import numpy as np
from safetensors import safe_open

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    artifact_ref,
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_30_nominal_action_quantile_preflight import (
    CLEAN_STATS_PATH,
)
from scenesmith.robot_lab.t20_31_nominal_action_quantile_campaign import (  # noqa: E402
    HELD_OUT_SEEDS,
    RESULT_GATE_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    build_result_gate,
    verify_run_summary,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    gate = build_gate()
    if args.verify:
        archived = load_strict_json(REPO_ROOT / RESULT_GATE_PATH)
        verify_signed_payload(archived, label="T20.31 result gate")
        if archived != gate:
            raise ValueError("T20.31 result gate drifted from live evidence")
    else:
        dump_canonical_json(REPO_ROOT / RESULT_GATE_PATH, gate)
    print(gate["identity_sha256"], gate["decision"], gate["strict_success_count"])
    return 0


def build_gate() -> dict:
    summary_path = RUN_ROOT / RUN_SUMMARY_PATH
    summary = load_strict_json(REPO_ROOT / summary_path)
    verify_signed_payload(summary, label="T20.31 training summary")
    verify_run_summary(summary)
    checkpoint = (
        REPO_ROOT / RUN_ROOT / "training/checkpoints/last/pretrained_model"
    )
    state_path = (
        checkpoint
        / "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
    )
    clean_stats = load_strict_json(REPO_ROOT / CLEAN_STATS_PATH)["action"]
    with safe_open(state_path, framework="np") as state:
        q01 = np.asarray(state.get_tensor("action.q01"), dtype=np.float64)
        q99 = np.asarray(state.get_tensor("action.q99"), dtype=np.float64)
    quantiles_match = all(
        np.allclose(recorded, clean_stats[name], rtol=0.0, atol=2e-5)
        for recorded, name in ((q01, "q01"), (q99, "q99"))
    )
    refs = []
    rollouts = []
    for seed in HELD_OUT_SEEDS:
        relative = RUN_ROOT / f"held_out_seed_{seed}_closed_loop.json"
        evaluation = load_strict_json(REPO_ROOT / relative)
        verify_signed_payload(evaluation, label=f"T20.31 seed-{seed} evaluation")
        if evaluation.get("held_out_seed") != seed:
            raise ValueError("T20.31 evaluation wrapper seed drifted")
        refs.append(
            {
                "seed": seed,
                **artifact_ref(
                    path=relative, payload=evaluation, repo_root=REPO_ROOT
                ),
            }
        )
        rollouts.append(evaluation["closed_loop"])
    return build_result_gate(
        training_ref=artifact_ref(
            path=summary_path, payload=summary, repo_root=REPO_ROOT
        ),
        evaluation_refs=refs,
        training_summary=summary,
        evaluations=rollouts,
        checkpoint_action_quantiles_match_t20_30=quantiles_match,
    )


if __name__ == "__main__":
    raise SystemExit(main())
