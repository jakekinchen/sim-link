#!/usr/bin/env python3
"""Compose or verify the offline T20.29 action-quantile counterfactual."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path

import numpy as np
from safetensors import safe_open

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_26_frame_zero_variability import (  # noqa: E402
    verify_batch,
)
from scenesmith.robot_lab.t20_29_quantile_counterfactual import (  # noqa: E402
    build_counterfactual,
    verify_counterfactual,
)


OUTPUT_ROOT = REPO_ROOT / "outputs/robot_lab/t20_25_frozen_candidate_localization"
T20_27_GATE = (
    REPO_ROOT / "configurations/robot_lab/t20_27_paired_source_action_gate.json"
)
FORMULA_SOURCE = (
    REPO_ROOT / "external/lerobot/src/lerobot/processor/normalize_processor.py"
)
OUTPUT_PATH = (
    REPO_ROOT
    / "configurations/robot_lab/t20_29_quantile_postprocessor_counterfactual.json"
)
CHECKPOINTS = {
    "clean_base": REPO_ROOT
    / "outputs/robot_lab/t20_17_clean_base_run_002/training/checkpoints/000250/"
    "pretrained_model",
    "recovery_augmented": REPO_ROOT
    / "outputs/robot_lab/t20_24_recovery_augmented_run_002/training/checkpoints/000500/"
    "pretrained_model",
}
STATS_PATHS = {
    "clean_base": REPO_ROOT
    / "outputs/robot_lab/t20_17_lerobot_training_dataset/meta/stats.json",
    "recovery_augmented": REPO_ROOT
    / "outputs/robot_lab/t20_23_recovery_augmented_dataset/meta/stats.json",
}
CONFIG_NAME = "policy_postprocessor.json"
STATE_NAME = "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
STATE_MATCH_ATOL = 2e-5


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    expected, batches, stats = _compose()
    if args.verify:
        recorded = load_strict_json(OUTPUT_PATH)
        verify_counterfactual(
            recorded,
            batches=batches,
            source_action_rad=expected["source_action_rad"],
            clean_stats=stats["clean_base"],
            recovery_stats=stats["recovery_augmented"],
            clean_stats_sha256=expected["clean_stats_sha256"],
            recovery_stats_sha256=expected["recovery_stats_sha256"],
            clean_postprocessor_config_sha256=expected[
                "clean_postprocessor_config_sha256"
            ],
            recovery_postprocessor_config_sha256=expected[
                "recovery_postprocessor_config_sha256"
            ],
            clean_postprocessor_state_sha256=expected[
                "clean_postprocessor_state_sha256"
            ],
            recovery_postprocessor_state_sha256=expected[
                "recovery_postprocessor_state_sha256"
            ],
            formula_source_sha256=expected["formula_source_sha256"],
            t20_27_gate_identity_sha256=expected[
                "t20_27_gate_identity_sha256"
            ],
            observed_recovery_minus_clean_mae_rad=expected[
                "observed_recovery_minus_clean_mae_rad"
            ],
        )
        if recorded != expected:
            raise ValueError("T20.29 recorded counterfactual drifted from evidence")
        print("T20.29 quantile counterfactual verified")
        return 0
    if OUTPUT_PATH.exists():
        raise FileExistsError("T20.29 artifact already exists; use --verify")
    dump_canonical_json(OUTPUT_PATH, expected)
    print(
        expected["identity_sha256"],
        expected["aggregates"],
        expected["accounting_residual_rad"],
        expected["result"],
    )
    return 0


def _compose() -> tuple[dict, dict[str, dict], dict[str, dict]]:
    batches = {
        candidate: load_strict_json(
            OUTPUT_ROOT / f"{candidate}_frame_zero_batch_1.json"
        )
        for candidate in CHECKPOINTS
    }
    for candidate, batch in batches.items():
        verify_batch(batch)
        if batch["candidate_id"] != candidate or batch["batch_id"] != 1:
            raise ValueError("T20.29 batch identity substitution detected")
    gate = load_strict_json(T20_27_GATE)
    verify_signed_payload(gate, label="T20.27 paired source-action gate")
    if gate.get("task_id") != "T20.27":
        raise ValueError("T20.29 T20.27 gate identity drifted")

    stats = {}
    stats_hashes = {}
    config_hashes = {}
    state_hashes = {}
    for candidate, checkpoint in CHECKPOINTS.items():
        stats_path = STATS_PATHS[candidate]
        config_path = checkpoint / CONFIG_NAME
        state_path = checkpoint / STATE_NAME
        stats_document = load_strict_json(stats_path)
        action_stats = stats_document["action"]
        config = load_strict_json(config_path)
        _verify_quantile_postprocessor(config, state_path, action_stats)
        stats[candidate] = action_stats
        stats_hashes[candidate] = _hash(stats_path)
        config_hashes[candidate] = _hash(config_path)
        state_hashes[candidate] = _hash(state_path)

    payload = build_counterfactual(
        batches=batches,
        source_action_rad=gate["source_action_rad"],
        clean_stats=stats["clean_base"],
        recovery_stats=stats["recovery_augmented"],
        clean_stats_sha256=stats_hashes["clean_base"],
        recovery_stats_sha256=stats_hashes["recovery_augmented"],
        clean_postprocessor_config_sha256=config_hashes["clean_base"],
        recovery_postprocessor_config_sha256=config_hashes["recovery_augmented"],
        clean_postprocessor_state_sha256=state_hashes["clean_base"],
        recovery_postprocessor_state_sha256=state_hashes["recovery_augmented"],
        formula_source_sha256=_hash(FORMULA_SOURCE),
        t20_27_gate_identity_sha256=gate["identity_sha256"],
        observed_recovery_minus_clean_mae_rad=gate["aggregate"][
            "recovery_minus_clean_mae_rad"
        ],
    )
    return payload, batches, stats


def _verify_quantile_postprocessor(
    config: dict, state_path: Path, action_stats: dict
) -> None:
    steps = config.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("T20.29 postprocessor steps are malformed")
    step = steps[0]
    step_config = step.get("config", {})
    if (
        step.get("registry_name") != "unnormalizer_processor"
        or step_config.get("norm_map", {}).get("ACTION") != "QUANTILES"
        or step_config.get("features", {}).get("action", {}).get("shape") != [6]
        or step.get("state_file") != STATE_NAME
    ):
        raise ValueError("T20.29 action-quantile postprocessor contract drifted")
    with safe_open(state_path, framework="np") as state:
        q01 = np.asarray(state.get_tensor("action.q01"), dtype=np.float64)
        q99 = np.asarray(state.get_tensor("action.q99"), dtype=np.float64)
    for recorded, expected, label in (
        (q01, action_stats.get("q01"), "q01"),
        (q99, action_stats.get("q99"), "q99"),
    ):
        expected_array = np.asarray(expected, dtype=np.float64)
        if recorded.shape != (6,) or not np.allclose(
            recorded, expected_array, rtol=0.0, atol=STATE_MATCH_ATOL
        ):
            raise ValueError(f"T20.29 checkpoint action {label} drifted from stats")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
