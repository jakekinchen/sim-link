"""Model-free decoded-action outlier audit for T20.35w."""

from __future__ import annotations

import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.so101_processor import JOINT_NAMES
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    INFERENCE_SEEDS,
    MAX_ACTION_ERROR_RAD,
)
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (
    _equal_with_float_tolerance,
)
from scenesmith.robot_lab.t20_35v_post_training_trajectory_audit import (
    ATTEMPT_PATH as T20_35V_ATTEMPT_PATH,
    RESULT_PATH as T20_35V_RESULT_PATH,
    RUNTIME_PREFLIGHT_PATH as T20_35V_RUNTIME_PREFLIGHT_PATH,
    load_and_verify_evaluation_files as load_t20_35v_sources,
    verify_attempt_marker as verify_t20_35v_attempt,
    verify_result as verify_t20_35v_result,
    verify_runtime_preflight as verify_t20_35v_runtime_preflight,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = Path(
    "configurations/robot_lab/t20_35w_step_coordinate_action_outlier_audit.json"
)
SCHEMA_VERSION = "scenesmith.t20_35w_step_coordinate_action_outlier_audit.v1"
EXPECTED_T20_35V_SPEC_IDENTITY = (
    "a0b5c211312ab488fd07b3b237a50e49f50a4b05ec012faf3120ed55603f66d8"
)
EXPECTED_T20_35V_PERMIT_IDENTITY = (
    "304b956b59587e036a52f61d977a431f2600c1bae03d4aade4bd072ed9051dbc"
)
EXPECTED_T20_35V_RUNTIME_PREFLIGHT_IDENTITY = (
    "59ecc86c8caab7659a77f537a79d0d881c4fb147c1099fc8a85c5f152f2bd279"
)
EXPECTED_T20_35V_RESULT_IDENTITY = (
    "aad8a14809fdcd079651bc90ca4bbdcd753831044c025591e21da391f02e3f3d"
)
ACTION_COUNT = 50
JOINT_COUNT = len(JOINT_NAMES)
CELL_COUNT = len(INFERENCE_SEEDS) * ACTION_COUNT * JOINT_COUNT
TIME_BAND_WIDTH = 10
TIME_BAND_COUNT = ACTION_COUNT // TIME_BAND_WIDTH
SPARSE_EXCEEDANCE_FRACTION_MAX = 0.10
SPARSE_TOP_FIVE_PERCENT_SQUARED_MASS_MIN = 0.50
JOINT_SQUARED_MASS_DOMINANCE_MIN = 0.50
TIME_BAND_SQUARED_MASS_DOMINANCE_MIN = 0.50
NORMALIZED_JOINT_SQUARED_MASS_DOMINANCE_MIN = 0.50


def build_audit(
    *,
    trajectory_spec: dict[str, Any],
    trajectory_permit: dict[str, Any],
    runtime_preflight: dict[str, Any],
    trajectory_attempt: dict[str, Any],
    trajectory_result: dict[str, Any],
    source_trajectory_result: dict[str, Any],
    training_result: dict[str, Any],
    target_result: dict[str, Any],
    target_action_chunk: list[list[float]],
) -> dict[str, Any]:
    for label, payload in (
        ("trajectory spec", trajectory_spec),
        ("trajectory permit", trajectory_permit),
        ("runtime preflight", runtime_preflight),
        ("trajectory attempt", trajectory_attempt),
        ("trajectory result", trajectory_result),
        ("source trajectory result", source_trajectory_result),
        ("training result", training_result),
        ("target result", target_result),
    ):
        verify_signed_payload(payload, label=f"T20.35w {label}")
    verify_t20_35v_runtime_preflight(
        runtime_preflight,
        spec=trajectory_spec,
        permit=trajectory_permit,
    )
    verify_t20_35v_attempt(
        trajectory_attempt,
        spec_identity=trajectory_spec["identity_sha256"],
        permit_identity=trajectory_permit["identity_sha256"],
        runtime_preflight_identity=runtime_preflight["identity_sha256"],
    )
    verify_t20_35v_result(
        trajectory_result,
        spec=trajectory_spec,
        permit=trajectory_permit,
        runtime_preflight=runtime_preflight,
        attempt=trajectory_attempt,
        source_trajectory_result=source_trajectory_result,
        training_result=training_result,
        target_chunk=target_action_chunk,
        normalized_target=target_result["normalized_padded_target"],
    )
    if (
        trajectory_spec.get("identity_sha256")
        != EXPECTED_T20_35V_SPEC_IDENTITY
        or trajectory_permit.get("identity_sha256")
        != EXPECTED_T20_35V_PERMIT_IDENTITY
        or runtime_preflight.get("identity_sha256")
        != EXPECTED_T20_35V_RUNTIME_PREFLIGHT_IDENTITY
        or trajectory_result.get("identity_sha256")
        != EXPECTED_T20_35V_RESULT_IDENTITY
        or trajectory_result.get("path_interference_classification")
        != "early_mid_path_interference"
        or trajectory_result.get("selected_next_hypothesis")
        != "audit_balanced_checkpoint_step_coordinate_outliers"
        or trajectory_result.get("gate_b_passed") is not False
    ):
        raise ValueError("T20.35w source identity or route drifted")

    target = _finite_matrix(
        target_action_chunk,
        rows=ACTION_COUNT,
        columns=JOINT_COUNT,
        label="target action chunk",
    )
    normalized_target = _finite_matrix(
        target_result.get("normalized_padded_target"),
        rows=ACTION_COUNT,
        columns=32,
        label="normalized target",
    )
    rows = trajectory_result.get("new_trajectory_evaluations")
    if (
        not isinstance(rows, list)
        or len(rows) != len(INFERENCE_SEEDS)
        or [row.get("inference_seed") for row in rows if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35w trajectory seed coverage drifted")

    cells: list[dict[str, Any]] = []
    normalized_cells: list[dict[str, Any]] = []
    for seed_index, row in enumerate(rows):
        decoded = _finite_matrix(
            row.get("decoded_action_chunk"),
            rows=ACTION_COUNT,
            columns=JOINT_COUNT,
            label="decoded action chunk",
        )
        steps = row.get("steps")
        if not isinstance(steps, list) or len(steps) != 10:
            raise ValueError("T20.35w trajectory step coverage drifted")
        last = steps[-1]
        if (
            last.get("step_index") != 9
            or _finite(last.get("time"), "last time") != 1.0 - 9 / 10
        ):
            raise ValueError("T20.35w last-captured time drifted")
        last_state = _finite_matrix(
            last.get("state"),
            rows=ACTION_COUNT,
            columns=32,
            label="last captured normalized state",
        )
        for action_index in range(ACTION_COUNT):
            for joint_index, joint_name in enumerate(JOINT_NAMES):
                error = abs(
                    decoded[action_index][joint_index]
                    - target[action_index][joint_index]
                )
                normalized_error = abs(
                    last_state[action_index][joint_index]
                    - normalized_target[action_index][joint_index]
                )
                cells.append(
                    {
                        "inference_seed": INFERENCE_SEEDS[seed_index],
                        "action_index": action_index,
                        "joint_index": joint_index,
                        "joint_name": joint_name,
                        "absolute_error_rad": error,
                        "squared_error_rad2": error * error,
                        "exceeds_threshold": error > MAX_ACTION_ERROR_RAD,
                    }
                )
                normalized_cells.append(
                    {
                        "inference_seed": INFERENCE_SEEDS[seed_index],
                        "action_index": action_index,
                        "joint_index": joint_index,
                        "absolute_error": normalized_error,
                        "squared_error": normalized_error * normalized_error,
                    }
                )
    if len(cells) != CELL_COUNT or len(normalized_cells) != CELL_COUNT:
        raise ValueError("T20.35w action-error coverage drifted")
    total_squared = sum(row["squared_error_rad2"] for row in cells)
    normalized_total_squared = sum(row["squared_error"] for row in normalized_cells)
    if total_squared <= 0.0 or normalized_total_squared <= 0.0:
        raise ValueError("T20.35w error mass must be positive")

    by_seed = _summaries(
        cells,
        groups=[("inference_seed", seed) for seed in INFERENCE_SEEDS],
        total_squared=total_squared,
    )
    by_joint = _summaries(
        cells,
        groups=[("joint_index", index) for index in range(JOINT_COUNT)],
        total_squared=total_squared,
    )
    for row in by_joint:
        row["joint_name"] = JOINT_NAMES[row["joint_index"]]
    by_action_index = _summaries(
        cells,
        groups=[("action_index", index) for index in range(ACTION_COUNT)],
        total_squared=total_squared,
    )
    by_time_band = []
    for band_index in range(TIME_BAND_COUNT):
        start = band_index * TIME_BAND_WIDTH
        selected = [
            row for row in cells if start <= row["action_index"] < start + TIME_BAND_WIDTH
        ]
        summary = _summary(selected, total_squared=total_squared)
        summary.update(
            {
                "band_index": band_index,
                "start_action_index": start,
                "end_action_index_inclusive": start + TIME_BAND_WIDTH - 1,
            }
        )
        by_time_band.append(summary)
    normalized_by_joint = []
    for joint_index, joint_name in enumerate(JOINT_NAMES):
        selected = [
            row for row in normalized_cells if row["joint_index"] == joint_index
        ]
        squared = sum(row["squared_error"] for row in selected)
        normalized_by_joint.append(
            {
                "joint_index": joint_index,
                "joint_name": joint_name,
                "cell_count": len(selected),
                "maximum_absolute_error": max(row["absolute_error"] for row in selected),
                "mean_absolute_error": sum(row["absolute_error"] for row in selected)
                / len(selected),
                "squared_error_mass_fraction": squared / normalized_total_squared,
            }
        )

    ordered = sorted(
        cells,
        key=lambda row: (
            -row["absolute_error_rad"],
            row["inference_seed"],
            row["action_index"],
            row["joint_index"],
        ),
    )
    exceedance_count = sum(row["exceeds_threshold"] for row in cells)
    exceedance_fraction = exceedance_count / CELL_COUNT
    top_five_percent_count = math.ceil(CELL_COUNT * 0.05)
    top_five_percent_mass = sum(
        row["squared_error_rad2"] for row in ordered[:top_five_percent_count]
    ) / total_squared
    dominant_joint = max(by_joint, key=lambda row: row["squared_error_mass_fraction"])
    dominant_band = max(
        by_time_band, key=lambda row: row["squared_error_mass_fraction"]
    )
    normalized_dominant_joint = max(
        normalized_by_joint, key=lambda row: row["squared_error_mass_fraction"]
    )
    sparse = (
        exceedance_fraction <= SPARSE_EXCEEDANCE_FRACTION_MAX
        and top_five_percent_mass >= SPARSE_TOP_FIVE_PERCENT_SQUARED_MASS_MIN
    )
    joint_dominant = (
        dominant_joint["squared_error_mass_fraction"]
        >= JOINT_SQUARED_MASS_DOMINANCE_MIN
    )
    time_band_dominant = (
        dominant_band["squared_error_mass_fraction"]
        >= TIME_BAND_SQUARED_MASS_DOMINANCE_MIN
    )
    normalized_joint_dominant = (
        normalized_dominant_joint["squared_error_mass_fraction"]
        >= NORMALIZED_JOINT_SQUARED_MASS_DOMINANCE_MIN
    )
    if joint_dominant and not normalized_joint_dominant:
        classification = (
            "physical_gate_joint_dominance_without_normalized_state_dominance"
        )
        route = "design_physical_gate_aligned_joint_weighted_standard_replay_correction"
    elif joint_dominant:
        classification = "joint_dominant_action_error"
        route = "design_joint_weighted_standard_replay_correction"
    elif time_band_dominant:
        classification = "time_band_dominant_action_error"
        route = "design_action_time_band_weighted_standard_replay_correction"
    elif sparse:
        classification = "sparse_step_coordinate_action_outliers"
        route = "design_sparse_action_outlier_replay_correction"
    else:
        classification = "distributed_action_error"
        route = "audit_decoded_action_objective_alignment"

    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35w",
            "scope": "one_model_free_decoded_action_step_coordinate_outlier_audit",
            "t20_35v_spec_identity_sha256": trajectory_spec["identity_sha256"],
            "t20_35v_permit_identity_sha256": trajectory_permit["identity_sha256"],
            "t20_35v_runtime_preflight_identity_sha256": runtime_preflight[
                "identity_sha256"
            ],
            "t20_35v_attempt_identity_sha256": trajectory_attempt["identity_sha256"],
            "t20_35v_result_identity_sha256": trajectory_result["identity_sha256"],
            "target_result_identity_sha256": target_result["identity_sha256"],
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "action_error_cell_count": CELL_COUNT,
            "action_error_cells": cells,
            "action_error_by_seed": by_seed,
            "action_error_by_joint": by_joint,
            "action_error_by_action_index": by_action_index,
            "action_error_by_time_band": by_time_band,
            "last_captured_normalized_error_by_joint": normalized_by_joint,
            "exceeding_cell_count": exceedance_count,
            "exceeding_cell_fraction": exceedance_fraction,
            "top_five_percent_cell_count": top_five_percent_count,
            "top_five_percent_squared_error_mass_fraction": top_five_percent_mass,
            "top_error_cells": ordered[:25],
            "sparse_exceedance_fraction_max": SPARSE_EXCEEDANCE_FRACTION_MAX,
            "sparse_top_five_percent_squared_mass_min": SPARSE_TOP_FIVE_PERCENT_SQUARED_MASS_MIN,
            "joint_squared_error_mass_dominance_min": JOINT_SQUARED_MASS_DOMINANCE_MIN,
            "time_band_squared_error_mass_dominance_min": TIME_BAND_SQUARED_MASS_DOMINANCE_MIN,
            "normalized_joint_squared_error_mass_dominance_min": NORMALIZED_JOINT_SQUARED_MASS_DOMINANCE_MIN,
            "sparse_outliers": sparse,
            "joint_dominant": joint_dominant,
            "time_band_dominant": time_band_dominant,
            "normalized_joint_dominant": normalized_joint_dominant,
            "dominant_joint_index": dominant_joint["joint_index"],
            "dominant_joint_name": dominant_joint["joint_name"],
            "dominant_joint_squared_error_mass_fraction": dominant_joint[
                "squared_error_mass_fraction"
            ],
            "dominant_time_band_index": dominant_band["band_index"],
            "dominant_time_band_squared_error_mass_fraction": dominant_band[
                "squared_error_mass_fraction"
            ],
            "normalized_dominant_joint_name": normalized_dominant_joint[
                "joint_name"
            ],
            "normalized_dominant_joint_squared_error_mass_fraction": normalized_dominant_joint[
                "squared_error_mass_fraction"
            ],
            "action_outlier_classification": classification,
            "gate_b_passed": False,
            "selected_next_hypothesis": route,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_read": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "sampler_mutated": False,
            "action_correction_selected": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_audit(payload: dict[str, Any], **sources: Any) -> None:
    verify_signed_payload(payload, label="T20.35w action outlier audit")
    expected = build_audit(**sources)
    archived = {key: value for key, value in payload.items() if key != "identity_sha256"}
    rebuilt = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(archived, rebuilt, absolute_tolerance=1e-15):
        raise ValueError("T20.35w action outlier audit drifted")


def load_source_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35v_sources(repo_root=root)
    spec = sources["trajectory_spec"]
    permit = sources["trajectory_permit"]
    runtime = load_strict_json(root / T20_35V_RUNTIME_PREFLIGHT_PATH)
    verify_t20_35v_runtime_preflight(runtime, spec=spec, permit=permit)
    attempt = load_strict_json(root / T20_35V_ATTEMPT_PATH)
    verify_t20_35v_attempt(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
        runtime_preflight_identity=runtime["identity_sha256"],
    )
    result = load_strict_json(root / T20_35V_RESULT_PATH)
    verify_t20_35v_result(
        result,
        spec=spec,
        permit=permit,
        runtime_preflight=runtime,
        attempt=attempt,
        source_trajectory_result=sources["source_result"],
        training_result=sources["training_result"],
        target_chunk=sources["residual_report"]["target_action_chunk"],
        normalized_target=sources["target_result"]["normalized_padded_target"],
    )
    return {
        "trajectory_spec": spec,
        "trajectory_permit": permit,
        "runtime_preflight": runtime,
        "trajectory_attempt": attempt,
        "trajectory_result": result,
        "source_trajectory_result": sources["source_result"],
        "training_result": sources["training_result"],
        "target_result": sources["target_result"],
        "target_action_chunk": sources["residual_report"]["target_action_chunk"],
    }


def write_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    if (root / AUDIT_PATH).exists():
        raise FileExistsError("T20.35w immutable audit already exists")
    audit = build_audit(**load_source_artifacts(repo_root=root))
    dump_canonical_json(root / AUDIT_PATH, audit)
    return audit


def verify_audit_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    audit = load_strict_json(root / AUDIT_PATH)
    verify_audit(audit, **sources)
    return audit


def _summaries(
    rows: list[dict[str, Any]],
    *,
    groups: list[tuple[str, Any]],
    total_squared: float,
) -> list[dict[str, Any]]:
    result = []
    for field, value in groups:
        selected = [row for row in rows if row[field] == value]
        summary = _summary(selected, total_squared=total_squared)
        summary[field] = value
        result.append(summary)
    return result


def _summary(rows: list[dict[str, Any]], *, total_squared: float) -> dict[str, Any]:
    if not rows:
        raise ValueError("T20.35w summary group is empty")
    squared = sum(row["squared_error_rad2"] for row in rows)
    return {
        "cell_count": len(rows),
        "exceeding_cell_count": sum(row["exceeds_threshold"] for row in rows),
        "maximum_absolute_error_rad": max(row["absolute_error_rad"] for row in rows),
        "mean_absolute_error_rad": sum(row["absolute_error_rad"] for row in rows)
        / len(rows),
        "squared_error_mass_fraction": squared / total_squared,
    }


def _finite_matrix(
    value: Any, *, rows: int, columns: int, label: str
) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != rows:
        raise ValueError(f"T20.35w {label} row count drifted")
    result = []
    for row in value:
        if not isinstance(row, list) or len(row) != columns:
            raise ValueError(f"T20.35w {label} column count drifted")
        result.append([_finite(item, label) for item in row])
    return result


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.35w {label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"T20.35w {label} must be finite")
    return result
