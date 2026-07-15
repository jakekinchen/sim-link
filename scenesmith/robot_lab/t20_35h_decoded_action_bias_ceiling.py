"""Model-free leave-one-seed-out decoded-action bias ceiling for T20.35h."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any, Callable

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    INFERENCE_SEEDS,
    MAX_ACTION_ERROR_RAD,
)
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (
    JOINT_NAMES,
    _equal_with_float_tolerance,
)
from scenesmith.robot_lab.t20_35g_denoising_cadence_discriminator import (
    ATTEMPT_002_PATH,
    RESULT_PATH as T20_35G_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35g_sources,
    verify_attempt_marker,
    verify_result as verify_t20_35g_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CEILING_PATH = Path(
    "configurations/robot_lab/t20_35h_decoded_action_bias_ceiling.json"
)
SCHEMA_VERSION = "scenesmith.t20_35h_decoded_action_bias_ceiling.v1"
EXPECTED_T20_35G_RESULT_IDENTITY = (
    "57f1f0dd5190fa1e0dc2b84cf25546b8f4e520bb75d2a15616797c5f311b2ea2"
)
GLOBAL_CLASS = "global_output_channel_bias"
TIME_CONDITIONED_CLASS = "time_conditioned_output_channel_bias"


def build_bias_ceiling(
    *,
    source_result_identity: str,
    source_result_file_sha256: str,
    target_chunk: list[list[float]],
    baseline_decoded_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build both predeclared LOO correction ceilings from immutable chunks."""
    _sha(source_result_identity, "source result identity")
    _sha(source_result_file_sha256, "source result file hash")
    target = _matrix(target_chunk, "target chunk")
    baseline = _baseline_rows(baseline_decoded_chunks, target=target)
    baseline_worst = max(row["maximum_absolute_error_rad"] for row in baseline)
    baseline_mean = sum(
        row["mean_absolute_error_rad"] for row in baseline
    ) / len(baseline)
    matrices = [
        _matrix(row["decoded_action_chunk"], "baseline decoded chunk")
        for row in baseline_decoded_chunks
    ]

    global_result = _evaluate_correction_class(
        correction_class=GLOBAL_CLASS,
        matrices=matrices,
        target=target,
        correction_builder=_global_channel_bias,
        baseline_worst=baseline_worst,
        baseline_mean=baseline_mean,
    )
    time_conditioned_result = _evaluate_correction_class(
        correction_class=TIME_CONDITIONED_CLASS,
        matrices=matrices,
        target=target,
        correction_builder=_time_conditioned_bias,
        baseline_worst=baseline_worst,
        baseline_mean=baseline_mean,
    )
    if global_result["ceiling_passed"]:
        preferred = GLOBAL_CLASS
        route = (
            "global_decoded_action_bias_ceiling_passes_route_model_internal_"
            "output_bias_correction"
        )
    elif time_conditioned_result["ceiling_passed"]:
        preferred = TIME_CONDITIONED_CLASS
        route = (
            "time_conditioned_decoded_action_bias_ceiling_passes_route_action_"
            "head_time_conditioning_correction"
        )
    elif (
        time_conditioned_result["improves_baseline_worst_fold_maximum"]
        and time_conditioned_result["improves_baseline_aggregate_mean"]
    ):
        preferred = None
        route = "bias_ceiling_improves_but_fails_route_residual_variance_localization"
    else:
        preferred = None
        route = (
            "bias_only_correction_rejected_route_representation_action_head_"
            "localization"
        )

    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35h",
            "scope": "model_free_leave_one_seed_out_decoded_action_bias_ceiling",
            "source_t20_35g_result_identity_sha256": source_result_identity,
            "source_t20_35g_result_file_sha256": source_result_file_sha256,
            "source_num_inference_steps": 10,
            "dataset_action_chunk_sha256": hashlib.sha256(
                canonical_json_bytes(target)
            ).hexdigest(),
            "inference_seeds": list(INFERENCE_SEEDS),
            "leave_one_seed_out": True,
            "calibration_seed_count_per_fold": 4,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "baseline_decoded_action_chunks": [
                {
                    key: row[key]
                    for key in (
                        "inference_seed",
                        "decoded_action_chunk_sha256",
                        "mean_absolute_error_rad",
                        "maximum_absolute_error_rad",
                    )
                }
                for row in baseline
            ],
            "baseline_worst_fold_maximum_error_rad": baseline_worst,
            "baseline_aggregate_mean_absolute_error_rad": baseline_mean,
            GLOBAL_CLASS: global_result,
            TIME_CONDITIONED_CLASS: time_conditioned_result,
            "analytical_ceiling_passed": (
                global_result["ceiling_passed"]
                or time_conditioned_result["ceiling_passed"]
            ),
            "preferred_ceiling_class": preferred,
            "selected_next_hypothesis": route,
            "post_hoc_ceiling_only": True,
            "gate_b_passed": False,
            "action_correction_selected": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_read": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_bias_ceiling(
    payload: dict[str, Any],
    *,
    source_result_identity: str,
    source_result_file_sha256: str,
    target_chunk: list[list[float]],
    baseline_decoded_chunks: list[dict[str, Any]],
) -> None:
    verify_signed_payload(payload, label="T20.35h decoded-action bias ceiling")
    expected = build_bias_ceiling(
        source_result_identity=source_result_identity,
        source_result_file_sha256=source_result_file_sha256,
        target_chunk=target_chunk,
        baseline_decoded_chunks=baseline_decoded_chunks,
    )
    archived_content = {
        key: value for key, value in payload.items() if key != "identity_sha256"
    }
    expected_content = {
        key: value for key, value in expected.items() if key != "identity_sha256"
    }
    if not _equal_with_float_tolerance(
        archived_content, expected_content, absolute_tolerance=1e-15
    ):
        raise ValueError("T20.35h decoded-action bias ceiling drifted")


def build_live_bias_ceiling(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35g_sources(repo_root=root)
    spec = sources["cadence_spec"]
    permit = sources["cadence_permit"]
    target = sources["residual_report"]["target_action_chunk"]
    attempt = load_strict_json(root / ATTEMPT_002_PATH)
    verify_attempt_marker(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
    )
    result_path = root / T20_35G_RESULT_PATH
    result = load_strict_json(result_path)
    verify_t20_35g_result(
        result,
        spec=spec,
        permit=permit,
        attempt=attempt,
        target_chunk=target,
    )
    if (
        result.get("identity_sha256") != EXPECTED_T20_35G_RESULT_IDENTITY
        or result.get("baseline_reproduced_exactly") is not True
        or result.get("gate_b_passed") is not False
        or result.get("cadence_effect_positive") is not False
        or result.get("selected_next_hypothesis")
        != "denoising_cadence_rejected_route_output_bias_correction"
    ):
        raise ValueError("T20.35h source result or route drifted")
    baseline_rows = [
        row
        for row in result["cadence_evaluations"]
        if row.get("num_inference_steps") == 10
    ]
    if len(baseline_rows) != 1:
        raise ValueError("T20.35h source baseline row is ambiguous")
    source_file_sha256 = hashlib.sha256(result_path.read_bytes()).hexdigest()
    ceiling = build_bias_ceiling(
        source_result_identity=result["identity_sha256"],
        source_result_file_sha256=source_file_sha256,
        target_chunk=target,
        baseline_decoded_chunks=baseline_rows[0]["decoded_action_chunks"],
    )
    verify_bias_ceiling(
        ceiling,
        source_result_identity=result["identity_sha256"],
        source_result_file_sha256=source_file_sha256,
        target_chunk=target,
        baseline_decoded_chunks=baseline_rows[0]["decoded_action_chunks"],
    )
    return ceiling


def write_bias_ceiling(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    ceiling = build_live_bias_ceiling(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / CEILING_PATH, ceiling)
    return ceiling


def verify_bias_ceiling_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected = build_live_bias_ceiling(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / CEILING_PATH)
    verify_signed_payload(archived, label="T20.35h archived bias ceiling")
    archived_content = {
        key: value for key, value in archived.items() if key != "identity_sha256"
    }
    expected_content = {
        key: value for key, value in expected.items() if key != "identity_sha256"
    }
    if not _equal_with_float_tolerance(
        archived_content, expected_content, absolute_tolerance=1e-15
    ):
        raise ValueError("T20.35h archived bias ceiling drifted from sources")
    return archived


def _evaluate_correction_class(
    *,
    correction_class: str,
    matrices: list[list[list[float]]],
    target: list[list[float]],
    correction_builder: Callable[
        [list[list[list[float]]], list[list[float]], list[int]], Any
    ],
    baseline_worst: float,
    baseline_mean: float,
) -> dict[str, Any]:
    folds = []
    for held_out_index, held_out_seed in enumerate(INFERENCE_SEEDS):
        calibration_indices = [
            index for index in range(len(INFERENCE_SEEDS)) if index != held_out_index
        ]
        correction = correction_builder(matrices, target, calibration_indices)
        corrected = _apply_correction(
            matrices[held_out_index],
            correction,
            time_conditioned=correction_class == TIME_CONDITIONED_CLASS,
        )
        fold_metrics = _chunk_metrics(corrected, target=target)
        folds.append(
            {
                "held_out_inference_seed": held_out_seed,
                "calibration_seeds": [
                    INFERENCE_SEEDS[index] for index in calibration_indices
                ],
                "correction_shape": (
                    [50, 6] if correction_class == TIME_CONDITIONED_CLASS else [6]
                ),
                "correction_sha256": hashlib.sha256(
                    canonical_json_bytes(correction)
                ).hexdigest(),
                "corrected_action_chunk_sha256": hashlib.sha256(
                    canonical_json_bytes(corrected)
                ).hexdigest(),
                **fold_metrics,
            }
        )
    worst = max(row["maximum_absolute_error_rad"] for row in folds)
    aggregate_mean = sum(
        row["mean_absolute_error_rad"] for row in folds
    ) / len(folds)
    return {
        "correction_class": correction_class,
        "folds": folds,
        "all_held_out_chunks_within_threshold": all(
            row["maximum_absolute_error_rad"] <= MAX_ACTION_ERROR_RAD
            for row in folds
        ),
        "worst_fold_maximum_error_rad": worst,
        "aggregate_mean_absolute_error_rad": aggregate_mean,
        "total_threshold_exceedance_count": sum(
            row["threshold_exceedance_count"] for row in folds
        ),
        "improves_baseline_worst_fold_maximum": worst < baseline_worst,
        "improves_baseline_aggregate_mean": aggregate_mean < baseline_mean,
        "ceiling_passed": all(
            row["maximum_absolute_error_rad"] <= MAX_ACTION_ERROR_RAD
            for row in folds
        ),
    }


def _global_channel_bias(
    matrices: list[list[list[float]]],
    target: list[list[float]],
    calibration_indices: list[int],
) -> list[float]:
    denominator = len(calibration_indices) * 50
    return [
        math.fsum(
            target[timestep][joint] - matrices[index][timestep][joint]
            for index in calibration_indices
            for timestep in range(50)
        )
        / denominator
        for joint in range(6)
    ]


def _time_conditioned_bias(
    matrices: list[list[list[float]]],
    target: list[list[float]],
    calibration_indices: list[int],
) -> list[list[float]]:
    return [
        [
            math.fsum(
                target[timestep][joint] - matrices[index][timestep][joint]
                for index in calibration_indices
            )
            / len(calibration_indices)
            for joint in range(6)
        ]
        for timestep in range(50)
    ]


def _apply_correction(
    matrix: list[list[float]], correction: Any, *, time_conditioned: bool
) -> list[list[float]]:
    return [
        [
            matrix[timestep][joint]
            + (
                correction[timestep][joint]
                if time_conditioned
                else correction[joint]
            )
            for joint in range(6)
        ]
        for timestep in range(50)
    ]


def _baseline_rows(
    value: Any, *, target: list[list[float]]
) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or len(value) != len(INFERENCE_SEEDS)
        or [row.get("inference_seed") for row in value if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35h baseline seed coverage or order drifted")
    rows = []
    for source in value:
        matrix = _matrix(source.get("decoded_action_chunk"), "baseline decoded chunk")
        digest = hashlib.sha256(canonical_json_bytes(matrix)).hexdigest()
        source_digest = source.get("decoded_action_chunk_sha256")
        if source_digest is not None and source_digest != digest:
            raise ValueError("T20.35h baseline decoded action hash drifted")
        rows.append(
            {
                "inference_seed": source["inference_seed"],
                "decoded_action_chunk_sha256": digest,
                **{
                    key: value
                    for key, value in _chunk_metrics(matrix, target=target).items()
                    if key
                    in ("mean_absolute_error_rad", "maximum_absolute_error_rad")
                },
            }
        )
    return rows


def _chunk_metrics(
    matrix: list[list[float]], *, target: list[list[float]]
) -> dict[str, Any]:
    per_channel = []
    all_errors = []
    for joint, joint_name in enumerate(JOINT_NAMES):
        errors = [
            abs(matrix[timestep][joint] - target[timestep][joint])
            for timestep in range(50)
        ]
        all_errors.extend(errors)
        per_channel.append(
            {
                "joint_index": joint,
                "joint_name": joint_name,
                "mean_absolute_error_rad": sum(errors) / len(errors),
                "maximum_absolute_error_rad": max(errors),
                "threshold_exceedance_count": sum(
                    error > MAX_ACTION_ERROR_RAD for error in errors
                ),
            }
        )
    return {
        "per_channel_summary": per_channel,
        "threshold_exceedance_count": sum(
            error > MAX_ACTION_ERROR_RAD for error in all_errors
        ),
        "mean_absolute_error_rad": sum(all_errors) / len(all_errors),
        "maximum_absolute_error_rad": max(all_errors),
    }


def _matrix(value: Any, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 50:
        raise ValueError(f"T20.35h {label} must have 50 rows")
    result = []
    for row in value:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError(f"T20.35h {label} must have six columns")
        converted = []
        for item in row:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError(f"T20.35h {label} must be finite")
            number = float(item)
            if not math.isfinite(number):
                raise ValueError(f"T20.35h {label} must be finite")
            converted.append(number)
        result.append(converted)
    return result


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35h {label} must be lowercase SHA-256")
