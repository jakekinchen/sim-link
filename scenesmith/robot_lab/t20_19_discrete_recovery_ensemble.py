"""Fixed, uncalibrated T20.19 discrete recovery-controller ensemble contract."""

from __future__ import annotations

import hashlib
import math
from typing import Any

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload, verify_signed_payload


SCHEMA_VERSION = "scenesmith.t20_19_discrete_recovery_ensemble.v1"
SCORECARD_SCHEMA_VERSION = "scenesmith.t20_19_discrete_recovery_scorecard.v1"
TASK_ID = "T20.19"
_CELL_SPECS = (
    ("nominal", "nominal", 0.0),
    ("cube_x_low", "cube_x_offset_m", -0.004),
    ("cube_x_high", "cube_x_offset_m", 0.004),
    ("cube_y_low", "cube_y_offset_m", -0.004),
    ("cube_y_high", "cube_y_offset_m", 0.004),
    ("friction_low", "object_friction_multiplier", 0.8),
    ("friction_high", "object_friction_multiplier", 1.2),
    ("command_delay_1", "command_delay_frames", 1),
    ("command_delay_2", "command_delay_frames", 2),
    ("action_hold_2", "action_hold_frames", 2),
    ("gripper_scale_low", "gripper_command_scale", 0.95),
    ("gripper_scale_high", "gripper_command_scale", 1.05),
)
_FALSE_AUTHORITY_FIELDS = (
    "posterior_calibrated",
    "optimizer_training",
    "dataset_mixture_frozen",
    "simulation_training_ready",
    "simulation_policy_accepted",
    "physical_transfer_ready",
    "promotion_eligible",
    "physical_actuation",
    "external_compute_started",
    "brev_compute_started",
)


def build_cell_manifest(
    *,
    recovery_manifest_identity_sha256: str,
    recovery_package_identity_sha256: str,
    source_branch_id: str,
) -> dict[str, Any]:
    cells = [
        {
            "cell_index": index,
            "cell_id": cell_id,
            "factor": factor,
            "value": value,
            "one_factor_only": True,
        }
        for index, (cell_id, factor, value) in enumerate(_CELL_SPECS)
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "ensemble_scope": "fixed_discrete_uncalibrated_one_factor_recovery_falsification",
        "recovery_manifest_identity_sha256": _sha_value(
            recovery_manifest_identity_sha256, "recovery manifest identity"
        ),
        "recovery_package_identity_sha256": _sha_value(
            recovery_package_identity_sha256, "recovery package identity"
        ),
        "source_branch_id": _sha_value(source_branch_id, "source branch ID"),
        "seed": 6,
        "cell_count": len(cells),
        "cell_ids_sha256": _sha([row["cell_id"] for row in cells]),
        "cells": cells,
        **{field: False for field in _FALSE_AUTHORITY_FIELDS},
    }
    manifest = sign_payload(payload)
    verify_cell_manifest(manifest)
    return manifest


def verify_cell_manifest(manifest: dict[str, Any]) -> None:
    verify_signed_payload(manifest, label="T20.19 cell manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("task_id") != TASK_ID:
        raise ValueError("T20.19 cell manifest schema or task drifted")
    for field in _FALSE_AUTHORITY_FIELDS:
        if manifest.get(field) is not False:
            raise ValueError(f"T20.19 authority flag drifted: {field}")
    if manifest.get("ensemble_scope") != "fixed_discrete_uncalibrated_one_factor_recovery_falsification":
        raise ValueError("T20.19 ensemble scope drifted")
    for field in (
        "recovery_manifest_identity_sha256",
        "recovery_package_identity_sha256",
        "source_branch_id",
    ):
        _sha_value(manifest.get(field), field)
    if manifest.get("seed") != 6:
        raise ValueError("T20.19 seed drifted")
    cells = manifest.get("cells")
    if not isinstance(cells, list) or len(cells) != len(_CELL_SPECS):
        raise ValueError("T20.19 cell count drifted")
    expected = []
    seen: set[str] = set()
    for index, (cell_id, factor, value) in enumerate(_CELL_SPECS):
        cell = cells[index]
        if not isinstance(cell, dict) or cell.get("cell_index") != index:
            raise ValueError("T20.19 cell order drifted")
        if cell.get("cell_id") != cell_id or cell_id in seen:
            raise ValueError("T20.19 cell identity is duplicate or drifted")
        seen.add(cell_id)
        if cell.get("factor") != factor or cell.get("one_factor_only") is not True:
            raise ValueError("T20.19 one-factor cell drifted")
        _validate_factor_value(factor, cell.get("value"))
        if cell.get("value") != value:
            raise ValueError("T20.19 cell value drifted from its fixed bound")
        expected.append(cell_id)
    if manifest.get("cell_count") != len(cells) or manifest.get("cell_ids_sha256") != _sha(expected):
        raise ValueError("T20.19 cell manifest digest drifted")


def transform_actions(
    actions: list[list[float]], cell: dict[str, Any], initial_action: list[float]
) -> tuple[list[list[float]], str]:
    clean = [_vector(row, 6, "source action") for row in actions]
    initial = _vector(initial_action, 6, "initial action")
    if not clean:
        raise ValueError("T20.19 source actions are absent")
    factor = cell.get("factor")
    value = cell.get("value")
    _validate_factor_value(factor, value)
    if factor in {"nominal", "cube_x_offset_m", "cube_y_offset_m", "object_friction_multiplier"}:
        return clean, "measured_source"
    if factor == "command_delay_frames":
        delay = int(value)
        return [initial.copy() for _ in range(delay)] + clean[:-delay], "deterministic_command_delay"
    if factor == "action_hold_frames":
        hold = int(value)
        return [clean[(index // hold) * hold].copy() for index in range(len(clean))], "deterministic_action_hold"
    if factor == "gripper_command_scale":
        output = [row.copy() for row in clean]
        for row in output:
            row[5] *= float(value)
        return output, "deterministic_gripper_scale"
    raise ValueError("T20.19 action transform factor is unsupported")


def build_scorecard(manifest: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    verify_cell_manifest(manifest)
    clean = _validate_results(results, manifest)
    success_count = sum(row["simulation_semantic_strict_success"] for row in clean)
    nominal = clean[0]
    worst = min(
        clean,
        key=lambda row: (
            int(row["simulation_semantic_strict_success"]),
            row["strict_contact_frame_count"],
            row["maximum_anchor_lift_m"],
            -row["cell_index"],
        ),
    )
    payload = {
        "schema_version": SCORECARD_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "cell_manifest_identity_sha256": manifest["identity_sha256"],
        "ensemble_scope": manifest["ensemble_scope"],
        "cell_count": len(clean),
        "success_count": success_count,
        "success_rate": success_count / len(clean),
        "nominal_strict_success": nominal["simulation_semantic_strict_success"],
        "nominal_terminal_outcome": nominal["terminal_outcome"],
        "worst_cell_id": worst["cell_id"],
        "worst_cell_terminal_outcome": worst["terminal_outcome"],
        "results": clean,
        **{field: False for field in _FALSE_AUTHORITY_FIELDS},
    }
    scorecard = sign_payload(payload)
    verify_scorecard(scorecard, manifest)
    return scorecard


def verify_scorecard(scorecard: dict[str, Any], manifest: dict[str, Any]) -> None:
    verify_signed_payload(scorecard, label="T20.19 scorecard")
    verify_cell_manifest(manifest)
    if scorecard.get("schema_version") != SCORECARD_SCHEMA_VERSION or scorecard.get("task_id") != TASK_ID:
        raise ValueError("T20.19 scorecard schema or task drifted")
    for field in _FALSE_AUTHORITY_FIELDS:
        if scorecard.get(field) is not False:
            raise ValueError(f"T20.19 scorecard authority flag drifted: {field}")
    if scorecard.get("cell_manifest_identity_sha256") != manifest["identity_sha256"]:
        raise ValueError("T20.19 scorecard manifest binding drifted")
    expected = build_scorecard_unsigned(manifest, scorecard.get("results"))
    for key, value in expected.items():
        if scorecard.get(key) != value:
            raise ValueError(f"T20.19 scorecard derived field drifted: {key}")


def build_scorecard_unsigned(manifest: dict[str, Any], results: Any) -> dict[str, Any]:
    clean = _validate_results(results, manifest)
    count = sum(row["simulation_semantic_strict_success"] for row in clean)
    worst = min(
        clean,
        key=lambda row: (
            int(row["simulation_semantic_strict_success"]),
            row["strict_contact_frame_count"],
            row["maximum_anchor_lift_m"],
            -row["cell_index"],
        ),
    )
    return {
        "ensemble_scope": manifest["ensemble_scope"],
        "cell_count": len(clean),
        "success_count": count,
        "success_rate": count / len(clean),
        "nominal_strict_success": clean[0]["simulation_semantic_strict_success"],
        "nominal_terminal_outcome": clean[0]["terminal_outcome"],
        "worst_cell_id": worst["cell_id"],
        "worst_cell_terminal_outcome": worst["terminal_outcome"],
    }


def _validate_results(results: Any, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(results, list) or len(results) != len(manifest["cells"]):
        raise ValueError("T20.19 result count drifted")
    clean = []
    for index, (result, cell) in enumerate(zip(results, manifest["cells"], strict=True)):
        if not isinstance(result, dict) or result.get("cell_id") != cell["cell_id"]:
            raise ValueError("T20.19 result cell order drifted")
        first = _sha_value(result.get("first_trace_sha256"), "first replay trace")
        second = _sha_value(result.get("second_trace_sha256"), "second replay trace")
        if first != second:
            raise ValueError("T20.19 cell replay drifted")
        success = result.get("simulation_semantic_strict_success")
        contacts = result.get("strict_contact_frame_count")
        if not isinstance(success, bool) or not isinstance(contacts, int) or isinstance(contacts, bool) or contacts < 0:
            raise ValueError("T20.19 result semantics are invalid")
        lift = _number(result.get("maximum_anchor_lift_m"), "maximum lift")
        terminal = result.get("terminal_outcome")
        if not isinstance(terminal, str) or not terminal:
            raise ValueError("T20.19 terminal outcome is invalid")
        clean.append(
            {
                "cell_index": index,
                "cell_id": cell["cell_id"],
                "first_trace_sha256": first,
                "second_trace_sha256": second,
                "simulation_semantic_strict_success": success,
                "strict_contact_frame_count": contacts,
                "maximum_anchor_lift_m": lift,
                "terminal_outcome": terminal,
            }
        )
    return clean


def _validate_factor_value(factor: Any, value: Any) -> None:
    bounds = {
        "nominal": {0.0},
        "cube_x_offset_m": {-0.004, 0.004},
        "cube_y_offset_m": {-0.004, 0.004},
        "object_friction_multiplier": {0.8, 1.2},
        "command_delay_frames": {1, 2},
        "action_hold_frames": {2},
        "gripper_command_scale": {0.95, 1.05},
    }
    if factor not in bounds or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("T20.19 factor or value is invalid and must be finite")
    if value not in bounds[factor]:
        raise ValueError("T20.19 factor value exceeds or drifts from its bound")


def _vector(value: Any, length: int, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{label} has an invalid shape")
    return [_number(item, label) for item in value]


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _sha_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return value


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
