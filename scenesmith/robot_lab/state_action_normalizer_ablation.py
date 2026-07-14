"""Analyze the T20.15 PI0.5 state/action normalizer 2x2 ablation."""

from __future__ import annotations

import hashlib
import math

from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES


SCHEMA_VERSION = "scenesmith.t20_15_state_action_normalizer_ablation.v1"
CELL_ORDER = [
    "checkpoint_state_checkpoint_action",
    "checkpoint_state_dataset_action",
    "dataset_state_checkpoint_action",
    "dataset_state_dataset_action",
]


def build_state_action_normalizer_ablation(
    *,
    sources: dict[str, Any],
    cells: list[dict[str, Any]],
    oracle_action_rad: list[float],
    processor_evidence: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    oracle = _vector(oracle_action_rad, "oracle action")
    by_id = _validate_cells(cells, oracle)
    _validate_processor_evidence(processor_evidence)
    _validate_runtime(runtime)

    old_old = _action(by_id[CELL_ORDER[0]])
    old_new = _action(by_id[CELL_ORDER[1]])
    new_old = _action(by_id[CELL_ORDER[2]])
    new_new = _action(by_id[CELL_ORDER[3]])
    state_effect = new_old - old_old
    action_effect = old_new - old_old
    interaction = new_new - old_old - state_effect - action_effect
    decomposed = state_effect + action_effect + interaction
    residual = new_new - old_old - decomposed

    summaries = [_summarize_cell(by_id[cell_id], oracle) for cell_id in CELL_ORDER]
    by_summary = {row["cell_id"]: row for row in summaries}
    state_arm_delta = (
        by_summary[CELL_ORDER[2]]["initial_non_gripper_mae_rad"]
        - by_summary[CELL_ORDER[0]]["initial_non_gripper_mae_rad"]
    )
    action_arm_delta = (
        by_summary[CELL_ORDER[1]]["initial_non_gripper_mae_rad"]
        - by_summary[CELL_ORDER[0]]["initial_non_gripper_mae_rad"]
    )
    selected = _select_hypothesis(state_effect, action_effect, interaction)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.15",
            "sources": sources,
            "processor_evidence": processor_evidence,
            "oracle_action_rad": oracle.tolist(),
            "cells": summaries,
            "determinism": {
                "checkpoint_state_normalized_outputs_identical": (
                    by_id[CELL_ORDER[0]]["normalized_output_sha256"]
                    == by_id[CELL_ORDER[1]]["normalized_output_sha256"]
                ),
                "dataset_state_normalized_outputs_identical": (
                    by_id[CELL_ORDER[2]]["normalized_output_sha256"]
                    == by_id[CELL_ORDER[3]]["normalized_output_sha256"]
                ),
                "common_inference_seed": runtime["inference_seed"],
                "same_source_observation": True,
                "same_checkpoint": True,
            },
            "effect_decomposition_rad": {
                "state_preprocessor_effect": state_effect.tolist(),
                "action_postprocessor_effect": action_effect.tolist(),
                "interaction_effect": interaction.tolist(),
                "closure_residual_max_abs": float(np.max(np.abs(residual))),
                "state_effect_non_gripper_mae": float(np.mean(np.abs(state_effect[:5]))),
                "action_effect_non_gripper_mae": float(np.mean(np.abs(action_effect[:5]))),
                "interaction_effect_non_gripper_mae": float(
                    np.mean(np.abs(interaction[:5]))
                ),
                "state_effect_gripper_abs": float(abs(state_effect[5])),
                "action_effect_gripper_abs": float(abs(action_effect[5])),
                "interaction_effect_gripper_abs": float(abs(interaction[5])),
                "state_only_non_gripper_error_delta_rad": state_arm_delta,
                "action_only_non_gripper_error_delta_rad": action_arm_delta,
            },
            "finding": selected,
            "runtime": runtime,
            "model_inference_executed": True,
            "optimizer_training": False,
            "closed_loop_evaluation_executed": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_state_action_normalizer_ablation(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.15 state/action normalizer ablation")
    expected = build_state_action_normalizer_ablation(
        sources=payload.get("sources", {}),
        cells=payload.get("cells", []),
        oracle_action_rad=payload.get("oracle_action_rad"),
        processor_evidence=payload.get("processor_evidence", {}),
        runtime=payload.get("runtime", {}),
    )
    if payload != expected:
        raise ValueError("T20.15 ablation drifted from measured cells")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != "T20.15"
        or [row.get("cell_id") for row in payload.get("cells", [])] != CELL_ORDER
        or payload.get("determinism", {}).get(
            "checkpoint_state_normalized_outputs_identical"
        )
        is not True
        or payload.get("determinism", {}).get(
            "dataset_state_normalized_outputs_identical"
        )
        is not True
        or payload.get("effect_decomposition_rad", {}).get(
            "closure_residual_max_abs"
        )
        > 1e-12
        or payload.get("model_inference_executed") is not True
        or payload.get("optimizer_training") is not False
        or payload.get("closed_loop_evaluation_executed") is not False
        or payload.get("simulation_policy_accepted") is not False
        or payload.get("physical_actuation") is not False
        or payload.get("external_compute_started") is not False
        or payload.get("brev_compute_started") is not False
    ):
        raise ValueError("T20.15 ablation contract drifted")


def _validate_cells(
    cells: list[dict[str, Any]], oracle: np.ndarray
) -> dict[str, dict[str, Any]]:
    if [row.get("cell_id") for row in cells] != CELL_ORDER:
        raise ValueError("T20.15 ablation cells are missing or reordered")
    result = {}
    for row in cells:
        action = _action(row)
        normalized = _vector(row.get("normalized_model_output"), "normalized output")
        expected_error = np.abs(action - oracle)
        recorded_error = _vector(row.get("oracle_absolute_error_rad"), "oracle error")
        if not np.array_equal(expected_error, recorded_error):
            raise ValueError("T20.15 recorded oracle error drifted")
        if not _is_sha256(row.get("normalized_output_sha256")):
            raise ValueError("T20.15 normalized output hash is invalid")
        normalized_sha256 = hashlib.sha256(
            normalized.astype(np.float32).tobytes()
        ).hexdigest()
        if normalized_sha256 != row["normalized_output_sha256"]:
            raise ValueError("T20.15 normalized output hash drifted")
        if not np.isfinite(normalized).all():
            raise ValueError("T20.15 normalized output is non-finite")
        result[row["cell_id"]] = row
    for left, right in ((CELL_ORDER[0], CELL_ORDER[1]), (CELL_ORDER[2], CELL_ORDER[3])):
        if not np.array_equal(
            _vector(result[left]["normalized_model_output"], "left normalized"),
            _vector(result[right]["normalized_model_output"], "right normalized"),
        ):
            raise ValueError("T20.15 common-state normalized outputs are not identical")
    return result


def _summarize_cell(row: dict[str, Any], oracle: np.ndarray) -> dict[str, Any]:
    action = _action(row)
    error = np.abs(action - oracle)
    return {
        **row,
        "initial_action_mae_rad": float(np.mean(error)),
        "initial_action_max_error_rad": float(np.max(error)),
        "initial_non_gripper_mae_rad": float(np.mean(error[:5])),
        "initial_gripper_absolute_error_rad": float(error[5]),
        "dominant_initial_error_joint": JOINT_NAMES[int(np.argmax(error))],
    }


def _select_hypothesis(
    state_effect: np.ndarray,
    action_effect: np.ndarray,
    interaction: np.ndarray,
) -> dict[str, Any]:
    magnitudes = {
        "state_preprocessor": float(np.mean(np.abs(state_effect[:5]))),
        "action_postprocessor": float(np.mean(np.abs(action_effect[:5]))),
        "interaction": float(np.mean(np.abs(interaction[:5]))),
    }
    ordered = sorted(magnitudes.items(), key=lambda row: (-row[1], row[0]))
    dominant, dominant_value = ordered[0]
    runner_up_value = ordered[1][1]
    ratio = math.inf if runner_up_value == 0.0 else dominant_value / runner_up_value
    isolated = dominant_value > 1e-6 and ratio >= 2.0
    hypothesis_ids = {
        "state_preprocessor": "dataset_state_token_distribution_shift_dominates",
        "action_postprocessor": "dataset_action_unnormalization_dominates",
        "interaction": "state_action_normalizer_interaction_dominates",
    }
    return {
        "effect_non_gripper_mae_rad": magnitudes,
        "dominant_effect": dominant,
        "dominant_to_runner_up_ratio": ratio,
        "single_effect_isolated": isolated,
        "selected_next_hypothesis": (
            hypothesis_ids[dominant]
            if isolated
            else "mixed_normalizer_effect_requires_compatible_processor_training"
        ),
        "capability_claimed": False,
        "more_optimizer_updates_authorized": False,
    }


def _validate_processor_evidence(value: dict[str, Any]) -> None:
    required_true = (
        "checkpoint_pipeline_loaded_from_pinned_snapshot",
        "only_state_statistics_replaced_in_dataset_state_preprocessor",
        "only_action_statistics_replaced_in_dataset_action_postprocessor",
        "all_other_preprocessor_statistics_identical",
        "all_other_postprocessor_statistics_identical",
    )
    if any(value.get(name) is not True for name in required_true):
        raise ValueError("T20.15 processor isolation evidence drifted")
    for name in (
        "checkpoint_state_statistics_sha256",
        "dataset_state_statistics_sha256",
        "checkpoint_action_statistics_sha256",
        "dataset_action_statistics_sha256",
    ):
        if not _is_sha256(value.get(name)):
            raise ValueError("T20.15 processor statistics hash is invalid")


def _validate_runtime(value: dict[str, Any]) -> None:
    if (
        value.get("device") != "mps"
        or value.get("offline") is not True
        or value.get("model_inference_call_count") != 4
        or value.get("optimizer_step_count") != 0
        or value.get("simulation_step_count") != 0
    ):
        raise ValueError("T20.15 runtime contract drifted")


def _action(row: dict[str, Any]) -> np.ndarray:
    return _vector(row.get("canonical_action_mujoco_rad"), "canonical action")


def _vector(value: Any, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (6,) or not np.isfinite(result).all():
        raise ValueError(f"T20.15 {label} is malformed or non-finite")
    return result


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
