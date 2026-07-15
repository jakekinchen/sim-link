"""Model-free residual-variance localization for T20.35i."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

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
    RESULT_PATH as T20_35G_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35g_sources,
)
from scenesmith.robot_lab.t20_35h_decoded_action_bias_ceiling import (
    TIME_CONDITIONED_CLASS,
    _apply_correction,
    _matrix,
    _time_conditioned_bias,
    verify_bias_ceiling_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = Path(
    "configurations/robot_lab/t20_35i_residual_variance_localization.json"
)
SCHEMA_VERSION = "scenesmith.t20_35i_residual_variance_localization.v1"
EXPECTED_T20_35H_IDENTITY = (
    "63e1181b2f825de108a85525e38e0ae728cae2288a16b7d3763851e8109a6593"
)
SINGLE_CONCENTRATION_THRESHOLD = 0.50
TOP_TWO_CONCENTRATION_THRESHOLD = 0.75
BOUNDARY_WIDTH = 5
BOUNDARY_CONCENTRATION_THRESHOLD = 0.60
FIVE_FOURTHS_IDENTITY_TOLERANCE = 1e-15


def build_variance_localization(
    *,
    source_ceiling_identity: str,
    target_chunk: list[list[float]],
    raw_decoded_chunks: list[dict[str, Any]],
    corrected_action_chunks: list[dict[str, Any]],
    expected_corrected_hashes: list[dict[str, Any]],
) -> dict[str, Any]:
    _sha(source_ceiling_identity, "source ceiling identity")
    target = _matrix(target_chunk, "target chunk")
    raw_rows = _chunk_rows(
        raw_decoded_chunks,
        matrix_key="decoded_action_chunk",
        label="raw decoded chunks",
    )
    corrected_rows = _chunk_rows(
        corrected_action_chunks,
        matrix_key="corrected_action_chunk",
        label="corrected action chunks",
    )
    expected_hashes = _expected_hash_rows(expected_corrected_hashes)
    raw_matrices = [row["matrix"] for row in raw_rows]
    corrected_matrices = [row["matrix"] for row in corrected_rows]

    raw_means = [
        [
            sum(matrix[timestep][joint] for matrix in raw_matrices) / 5
            for joint in range(6)
        ]
        for timestep in range(50)
    ]
    for seed_index, corrected in enumerate(corrected_matrices):
        digest = hashlib.sha256(canonical_json_bytes(corrected)).hexdigest()
        if digest != expected_hashes[seed_index]["corrected_action_chunk_sha256"]:
            raise ValueError("T20.35i corrected action hash drifted")
        for timestep in range(50):
            for joint in range(6):
                expected_error = 1.25 * (
                    raw_matrices[seed_index][timestep][joint]
                    - raw_means[timestep][joint]
                )
                observed_error = corrected[timestep][joint] - target[timestep][joint]
                if not math.isclose(
                    observed_error,
                    expected_error,
                    rel_tol=0.0,
                    abs_tol=FIVE_FOURTHS_IDENTITY_TOLERANCE,
                ):
                    raise ValueError("T20.35i five-fourths identity drifted")

    spread_positions = []
    spread_lookup: dict[tuple[int, int], float] = {}
    for timestep in range(50):
        for joint, joint_name in enumerate(JOINT_NAMES):
            values = [matrix[timestep][joint] for matrix in raw_matrices]
            spread = max(values) - min(values)
            spread_lookup[(timestep, joint)] = spread
            spread_positions.append(
                {
                    "timestep": timestep,
                    "joint_index": joint,
                    "joint_name": joint_name,
                    "raw_decoded_spread_rad": spread,
                }
            )

    exceedances = []
    per_seed_counts = [0] * 5
    per_channel_counts = [0] * 6
    per_timestep_counts = [0] * 50
    per_seed_channel_counts = [[0] * 6 for _ in range(5)]
    position_failure_count: dict[tuple[int, int], int] = {}
    for seed_index, corrected in enumerate(corrected_matrices):
        for timestep in range(50):
            for joint, joint_name in enumerate(JOINT_NAMES):
                signed_error = corrected[timestep][joint] - target[timestep][joint]
                absolute_error = abs(signed_error)
                if absolute_error <= MAX_ACTION_ERROR_RAD:
                    continue
                per_seed_counts[seed_index] += 1
                per_channel_counts[joint] += 1
                per_timestep_counts[timestep] += 1
                per_seed_channel_counts[seed_index][joint] += 1
                key = (timestep, joint)
                position_failure_count[key] = position_failure_count.get(key, 0) + 1
                exceedances.append(
                    {
                        "inference_seed": INFERENCE_SEEDS[seed_index],
                        "timestep": timestep,
                        "joint_index": joint,
                        "joint_name": joint_name,
                        "target_action_rad": target[timestep][joint],
                        "corrected_action_rad": corrected[timestep][joint],
                        "signed_error_rad": signed_error,
                        "absolute_error_rad": absolute_error,
                        "raw_decoded_spread_rad": spread_lookup[key],
                    }
                )
    total = len(exceedances)
    if total <= 0:
        raise ValueError("T20.35i requires at least one residual exceedance")
    boundary_count = sum(
        count
        for timestep, count in enumerate(per_timestep_counts)
        if timestep < BOUNDARY_WIDTH or timestep >= 50 - BOUNDARY_WIDTH
    )
    classification = classify_variance(
        total_exceedances=total,
        boundary_exceedance_count=boundary_count,
        per_seed_counts=per_seed_counts,
        per_channel_counts=per_channel_counts,
    )
    spread_values = [row["raw_decoded_spread_rad"] for row in spread_positions]
    failing_position_spreads = [
        spread_lookup[key] for key in sorted(position_failure_count)
    ]
    spread_positions = [
        {
            **row,
            "held_out_failure_count": position_failure_count.get(
                (row["timestep"], row["joint_index"]), 0
            ),
        }
        for row in spread_positions
    ]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35i",
            "scope": "model_free_time_conditioned_residual_variance_localization",
            "source_t20_35h_identity_sha256": source_ceiling_identity,
            "source_correction_class": TIME_CONDITIONED_CLASS,
            "dataset_action_chunk_sha256": hashlib.sha256(
                canonical_json_bytes(target)
            ).hexdigest(),
            "inference_seeds": list(INFERENCE_SEEDS),
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "five_fourths_identity_tolerance": FIVE_FOURTHS_IDENTITY_TOLERANCE,
            "corrected_action_chunk_hashes": expected_hashes,
            "threshold_exceedance_count": total,
            "exceedance_seed_coverage_count": sum(count > 0 for count in per_seed_counts),
            "exceedances": exceedances,
            "per_seed_summary": [
                {
                    "inference_seed": seed,
                    "threshold_exceedance_count": per_seed_counts[index],
                    "threshold_exceedance_fraction": per_seed_counts[index] / total,
                }
                for index, seed in enumerate(INFERENCE_SEEDS)
            ],
            "per_channel_summary": [
                {
                    "joint_index": joint,
                    "joint_name": joint_name,
                    "threshold_exceedance_count": per_channel_counts[joint],
                    "threshold_exceedance_fraction": per_channel_counts[joint] / total,
                }
                for joint, joint_name in enumerate(JOINT_NAMES)
            ],
            "per_seed_channel_summary": [
                {
                    "inference_seed": seed,
                    "joint_index": joint,
                    "joint_name": joint_name,
                    "threshold_exceedance_count": per_seed_channel_counts[seed_index][joint],
                    "threshold_exceedance_fraction": per_seed_channel_counts[seed_index][joint] / total,
                }
                for seed_index, seed in enumerate(INFERENCE_SEEDS)
                for joint, joint_name in enumerate(JOINT_NAMES)
            ],
            "per_timestep_summary": [
                {
                    "timestep": timestep,
                    "threshold_exceedance_count": count,
                    "threshold_exceedance_fraction": count / total,
                }
                for timestep, count in enumerate(per_timestep_counts)
            ],
            "boundary_width_timesteps": BOUNDARY_WIDTH,
            "boundary_exceedance_count": boundary_count,
            "boundary_exceedance_fraction": boundary_count / total,
            "single_seed_concentration_threshold": SINGLE_CONCENTRATION_THRESHOLD,
            "top_two_seed_concentration_threshold": TOP_TWO_CONCENTRATION_THRESHOLD,
            "single_channel_concentration_threshold": SINGLE_CONCENTRATION_THRESHOLD,
            "top_two_channel_concentration_threshold": TOP_TWO_CONCENTRATION_THRESHOLD,
            "boundary_concentration_threshold": BOUNDARY_CONCENTRATION_THRESHOLD,
            **classification,
            "raw_decoded_spread_by_position": spread_positions,
            "maximum_raw_decoded_spread_rad": max(spread_values),
            "aggregate_mean_raw_decoded_spread_rad": sum(spread_values) / len(spread_values),
            "unique_failure_position_count": len(position_failure_count),
            "maximum_failure_position_raw_spread_rad": max(failing_position_spreads),
            "aggregate_mean_failure_position_raw_spread_rad": sum(failing_position_spreads) / len(failing_position_spreads),
            "minimum_raw_mean_deviation_for_loo_gate_rad": 0.8 * MAX_ACTION_ERROR_RAD,
            "post_hoc_localization_only": True,
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


def classify_variance(
    *,
    total_exceedances: int,
    boundary_exceedance_count: int,
    per_seed_counts: list[int],
    per_channel_counts: list[int],
) -> dict[str, Any]:
    _counts(total_exceedances, boundary_exceedance_count, per_seed_counts, per_channel_counts)
    ranked_seeds = sorted(
        [
            {"inference_seed": seed, "threshold_exceedance_count": per_seed_counts[index]}
            for index, seed in enumerate(INFERENCE_SEEDS)
        ],
        key=lambda row: (-row["threshold_exceedance_count"], list(INFERENCE_SEEDS).index(row["inference_seed"])),
    )
    ranked_channels = sorted(
        [
            {
                "joint_index": index,
                "joint_name": JOINT_NAMES[index],
                "threshold_exceedance_count": per_channel_counts[index],
            }
            for index in range(6)
        ],
        key=lambda row: (-row["threshold_exceedance_count"], row["joint_index"]),
    )
    boundary_fraction = boundary_exceedance_count / total_exceedances
    single_seed_fraction = ranked_seeds[0]["threshold_exceedance_count"] / total_exceedances
    top_two_seed_fraction = sum(row["threshold_exceedance_count"] for row in ranked_seeds[:2]) / total_exceedances
    single_channel_fraction = ranked_channels[0]["threshold_exceedance_count"] / total_exceedances
    top_two_channel_fraction = sum(row["threshold_exceedance_count"] for row in ranked_channels[:2]) / total_exceedances
    if boundary_fraction >= BOUNDARY_CONCENTRATION_THRESHOLD:
        classification = "chunk_boundary_variance"
        route = "inspect_sampler_time_grid_and_terminal_boundary_variance"
    elif single_seed_fraction >= SINGLE_CONCENTRATION_THRESHOLD:
        classification = "single_seed_variance"
        route = "run_separately_reviewed_inference_only_initial_noise_sensitivity_probe"
    elif top_two_seed_fraction >= TOP_TWO_CONCENTRATION_THRESHOLD:
        classification = "top_two_seed_variance"
        route = "run_separately_reviewed_inference_only_initial_noise_sensitivity_probe"
    elif single_channel_fraction >= SINGLE_CONCENTRATION_THRESHOLD:
        classification = "single_channel_variance"
        route = "localize_action_head_stochastic_channel_variance_before_model_correction"
    elif top_two_channel_fraction >= TOP_TWO_CONCENTRATION_THRESHOLD:
        classification = "top_two_channel_variance"
        route = "localize_action_head_stochastic_channel_variance_before_model_correction"
    else:
        classification = "distributed_seed_channel_variance"
        route = "run_separately_reviewed_inference_only_initial_noise_scale_discriminator"
    return {
        "ranked_seed_counts": ranked_seeds,
        "ranked_channel_counts": ranked_channels,
        "single_seed_concentration_fraction": single_seed_fraction,
        "top_two_seed_concentration_fraction": top_two_seed_fraction,
        "single_channel_concentration_fraction": single_channel_fraction,
        "top_two_channel_concentration_fraction": top_two_channel_fraction,
        "variance_classification": classification,
        "selected_next_hypothesis": route,
    }


def verify_variance_localization(
    payload: dict[str, Any],
    *,
    source_ceiling_identity: str,
    target_chunk: list[list[float]],
    raw_decoded_chunks: list[dict[str, Any]],
    corrected_action_chunks: list[dict[str, Any]],
    expected_corrected_hashes: list[dict[str, Any]],
) -> None:
    verify_signed_payload(payload, label="T20.35i residual variance localization")
    expected = build_variance_localization(
        source_ceiling_identity=source_ceiling_identity,
        target_chunk=target_chunk,
        raw_decoded_chunks=raw_decoded_chunks,
        corrected_action_chunks=corrected_action_chunks,
        expected_corrected_hashes=expected_corrected_hashes,
    )
    archived_content = {key: value for key, value in payload.items() if key != "identity_sha256"}
    expected_content = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(archived_content, expected_content, absolute_tolerance=1e-15):
        raise ValueError("T20.35i residual variance localization drifted")


def build_live_variance_localization(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    ceiling = verify_bias_ceiling_file(repo_root=root)
    if (
        ceiling.get("identity_sha256") != EXPECTED_T20_35H_IDENTITY
        or ceiling.get("analytical_ceiling_passed") is not False
        or ceiling.get(TIME_CONDITIONED_CLASS, {}).get("total_threshold_exceedance_count") != 96
        or ceiling.get("selected_next_hypothesis")
        != "bias_ceiling_improves_but_fails_route_residual_variance_localization"
    ):
        raise ValueError("T20.35i source ceiling or route drifted")
    sources = load_t20_35g_sources(repo_root=root)
    target = sources["residual_report"]["target_action_chunk"]
    source_result_path = root / T20_35G_RESULT_PATH
    if hashlib.sha256(source_result_path.read_bytes()).hexdigest() != ceiling.get(
        "source_t20_35g_result_file_sha256"
    ):
        raise ValueError("T20.35i source result file hash drifted")
    result = load_strict_json(source_result_path)
    baseline_rows = [
        row for row in result["cadence_evaluations"] if row.get("num_inference_steps") == 10
    ]
    if len(baseline_rows) != 1:
        raise ValueError("T20.35i raw baseline row is ambiguous")
    raw_chunks = baseline_rows[0]["decoded_action_chunks"]
    raw_matrices = [
        _matrix(row["decoded_action_chunk"], "T20.35i raw decoded chunk")
        for row in raw_chunks
    ]
    corrected_chunks = []
    expected_hashes = []
    source_folds = ceiling[TIME_CONDITIONED_CLASS]["folds"]
    for held_out_index, seed in enumerate(INFERENCE_SEEDS):
        calibration_indices = [index for index in range(5) if index != held_out_index]
        correction = _time_conditioned_bias(raw_matrices, target, calibration_indices)
        corrected = _apply_correction(raw_matrices[held_out_index], correction, time_conditioned=True)
        source_fold = source_folds[held_out_index]
        correction_hash = hashlib.sha256(canonical_json_bytes(correction)).hexdigest()
        corrected_hash = hashlib.sha256(canonical_json_bytes(corrected)).hexdigest()
        if (
            source_fold.get("held_out_inference_seed") != seed
            or source_fold.get("calibration_seeds") != [INFERENCE_SEEDS[index] for index in calibration_indices]
            or source_fold.get("correction_sha256") != correction_hash
            or source_fold.get("corrected_action_chunk_sha256") != corrected_hash
        ):
            raise ValueError("T20.35i source fold reconstruction drifted")
        corrected_chunks.append({"inference_seed": seed, "corrected_action_chunk": corrected})
        expected_hashes.append({"inference_seed": seed, "corrected_action_chunk_sha256": corrected_hash})
    report = build_variance_localization(
        source_ceiling_identity=ceiling["identity_sha256"],
        target_chunk=target,
        raw_decoded_chunks=raw_chunks,
        corrected_action_chunks=corrected_chunks,
        expected_corrected_hashes=expected_hashes,
    )
    if report["threshold_exceedance_count"] != 96:
        raise ValueError("T20.35i reconstructed exceedance count drifted")
    return report


def write_variance_localization(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    report = build_live_variance_localization(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / REPORT_PATH, report)
    return report


def verify_variance_localization_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected = build_live_variance_localization(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / REPORT_PATH)
    verify_signed_payload(archived, label="T20.35i archived variance localization")
    archived_content = {key: value for key, value in archived.items() if key != "identity_sha256"}
    expected_content = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(archived_content, expected_content, absolute_tolerance=1e-15):
        raise ValueError("T20.35i archived variance localization drifted from sources")
    return archived


def _chunk_rows(value: Any, *, matrix_key: str, label: str) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or len(value) != 5
        or [row.get("inference_seed") for row in value if isinstance(row, dict)] != list(INFERENCE_SEEDS)
    ):
        raise ValueError(f"T20.35i {label} seed coverage or order drifted")
    return [
        {"inference_seed": row["inference_seed"], "matrix": _matrix(row.get(matrix_key), label)}
        for row in value
    ]


def _expected_hash_rows(value: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or len(value) != 5
        or [row.get("inference_seed") for row in value if isinstance(row, dict)] != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35i expected corrected hashes drifted")
    result = []
    for row in value:
        _sha(row.get("corrected_action_chunk_sha256"), "corrected action hash")
        result.append(
            {
                "inference_seed": row["inference_seed"],
                "corrected_action_chunk_sha256": row["corrected_action_chunk_sha256"],
            }
        )
    return result


def _counts(total: Any, boundary: Any, seeds: Any, channels: Any) -> None:
    if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
        raise ValueError("T20.35i total exceedance count is invalid")
    if (
        isinstance(boundary, bool)
        or not isinstance(boundary, int)
        or not 0 <= boundary <= total
        or not isinstance(seeds, list)
        or len(seeds) != 5
        or not isinstance(channels, list)
        or len(channels) != 6
        or any(isinstance(count, bool) or not isinstance(count, int) or count < 0 for count in seeds + channels)
        or sum(seeds) != total
        or sum(channels) != total
    ):
        raise ValueError("T20.35i concentration counts are invalid")


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35i {label} must be lowercase SHA-256")
