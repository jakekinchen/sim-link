"""Flow-trajectory consistency audit for T20.35o."""

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
    _equal_with_float_tolerance,
)
from scenesmith.robot_lab.t20_35n_near_zero_active_noise_scale_discriminator import (
    ACTIVE_ACTION_DIMENSIONS,
    ATTEMPT_PATH as T20_35N_ATTEMPT_PATH,
    MAXIMUM_ACTION_DIMENSIONS,
    NUM_INFERENCE_STEPS,
    PADDED_NOISE_SCALE,
    RESULT_PATH as T20_35N_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35n_sources,
    verify_attempt_marker as verify_t20_35n_attempt,
    verify_result as verify_t20_35n_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_35o_flow_trajectory_consistency_spec.json")
PERMIT_PATH = Path(
    "configurations/robot_lab/t20_35o_flow_trajectory_consistency_evaluation_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_35o_flow_trajectory_consistency_result.json"
)
ATTEMPT_PATH = Path("outputs/robot_lab/t20_35o_flow_trajectory_consistency/attempt.json")
SCHEMA_VERSION = "scenesmith.t20_35o_flow_trajectory_consistency_spec.v1"
PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_35o_flow_trajectory_consistency_evaluation_permit.v1"
)
RESULT_SCHEMA_VERSION = "scenesmith.t20_35o_flow_trajectory_consistency_result.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_35o_evaluation_attempt.v1"
EXPECTED_T20_35N_RESULT_IDENTITY = (
    "d3e6e5d96f9ddc462c0840c5baa72f864fb7b6c1ddc2ec00bce0ded03394fe7b"
)
INHERITED_AUTHORITY_IDENTITY = (
    "75dc9c7d860e12e2a2114be709e24f7e544ff576696a3d223dd87dd0e2f06606"
)
ACTIVE_NOISE_SCALE = 0.0
LATE_STEP_START_INDEX = 7
CONCENTRATION_THRESHOLD = 0.5
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T23:27:47-05:00"


def build_evaluation_spec(
    *, source_spec: dict[str, Any], source_result: dict[str, Any]
) -> dict[str, Any]:
    verify_signed_payload(source_spec, label="T20.35o source spec")
    verify_signed_payload(source_result, label="T20.35o source result")
    if (
        source_result.get("selected_active_noise_scale") != ACTIVE_NOISE_SCALE
        or source_result.get("gate_b_passed") is not False
        or source_result.get("selected_next_hypothesis")
        != "active_zero_endpoint_optimum_route_model_flow_consistency_correction"
        or source_spec.get("source_objective_ratio_within_threshold") is not True
    ):
        raise ValueError("T20.35o source route drifted")
    endpoint = _active_zero_evaluation(source_result)
    action_hashes: list[str] = []
    noise_hashes: list[str] = []
    for index, row in enumerate(_seed_rows(endpoint.get("decoded_action_chunks"))):
        digest = _matrix_sha(row.get("decoded_action_chunk"))
        if row.get("decoded_action_chunk_sha256") != digest:
            raise ValueError("T20.35o source decoded endpoint hash drifted")
        if row.get("inference_seed") != INFERENCE_SEEDS[index]:
            raise ValueError("T20.35o source inference seed drifted")
        _sha(row.get("base_noise_sha256"), "source base-noise hash")
        action_hashes.append(digest)
        noise_hashes.append(row["base_noise_sha256"])
    if source_spec.get("base_noise_sha256_by_seed") != noise_hashes:
        raise ValueError("T20.35o source base-noise lineage drifted")
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35o",
            "scope": "one_inference_only_active_zero_padded_normal_flow_trajectory_consistency_audit",
            "t20_35n_spec_identity_sha256": source_spec["identity_sha256"],
            "t20_35n_result_identity_sha256": source_result["identity_sha256"],
            "checkpoint_identity_sha256": source_spec["checkpoint_identity_sha256"],
            "checkpoint_tree": source_spec["checkpoint_tree"],
            "trainable_parameter_names_sha256": source_spec[
                "trainable_parameter_names_sha256"
            ],
            "trainable_parameter_count": source_spec["trainable_parameter_count"],
            "paligemma_trainable_parameter_count": source_spec[
                "paligemma_trainable_parameter_count"
            ],
            "dataset_action_chunk_sha256": source_spec[
                "dataset_action_chunk_sha256"
            ],
            "lerobot_stack_identity_sha256": source_spec[
                "lerobot_stack_identity_sha256"
            ],
            "sampler_source_sha256": source_spec["sampler_source_sha256"],
            "source_final_to_baseline_objective_ratio": source_spec[
                "source_final_to_baseline_objective_ratio"
            ],
            "source_objective_ratio_within_threshold": True,
            "active_action_dimension_count": ACTIVE_ACTION_DIMENSIONS,
            "maximum_action_dimension_count": MAXIMUM_ACTION_DIMENSIONS,
            "active_noise_scale": ACTIVE_NOISE_SCALE,
            "padded_noise_scale": PADDED_NOISE_SCALE,
            "inference_seeds": list(INFERENCE_SEEDS),
            "num_inference_steps": NUM_INFERENCE_STEPS,
            "base_noise_sha256_by_seed": noise_hashes,
            "source_decoded_action_sha256_by_seed": action_hashes,
            "reference_velocity_definition": "(pre_update_state-normalized_padded_target)/time",
            "late_step_indices": list(range(LATE_STEP_START_INDEX, NUM_INFERENCE_STEPS)),
            "concentration_threshold": CONCENTRATION_THRESHOLD,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "required_python_major_minor": [3, 12],
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "model_loaded": False,
            "model_inference": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_evaluation_spec(
    payload: dict[str, Any], *, expected_spec: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.35o trajectory spec")
    verify_signed_payload(expected_spec, label="T20.35o expected trajectory spec")
    if payload != expected_spec:
        raise ValueError("T20.35o trajectory spec drifted")


def build_evaluation_permit(*, spec: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35o permit source spec")
    if (
        spec.get("active_noise_scale") != ACTIVE_NOISE_SCALE
        or spec.get("padded_noise_scale") != PADDED_NOISE_SCALE
        or spec.get("num_inference_steps") != NUM_INFERENCE_STEPS
    ):
        raise ValueError("T20.35o permit source spec drifted")
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": "T20.35o",
            "scope": "one_local_mps_inference_only_flow_trajectory_consistency_audit",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "inherited_authority_decision_identity_sha256": INHERITED_AUTHORITY_IDENTITY,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "active_noise_scale": ACTIVE_NOISE_SCALE,
            "padded_noise_scale": PADDED_NOISE_SCALE,
            "inference_seeds": list(INFERENCE_SEEDS),
            "num_inference_steps": NUM_INFERENCE_STEPS,
            "optimizer_training_authorized": False,
            "checkpoint_mutation_authorized": False,
            "dataset_mutation_authorized": False,
            "closed_loop_rollout_authorized": False,
            "exactly_one_evaluation_attempt_authorized": True,
            "valid_from": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "physical_actuation_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
        }
    )


def verify_evaluation_permit(
    payload: dict[str, Any], *, spec: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.35o trajectory permit")
    if payload != build_evaluation_permit(spec=spec):
        raise ValueError("T20.35o trajectory permit drifted")


def verify_attempt_marker(
    payload: dict[str, Any], *, spec_identity: str, permit_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35o trajectory attempt")
    if (
        payload.get("schema_version") != ATTEMPT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35o"
        or payload.get("evaluation_spec_identity_sha256") != spec_identity
        or payload.get("evaluation_permit_identity_sha256") != permit_identity
        or not isinstance(payload.get("started_at"), str)
        or not payload["started_at"]
        or payload.get("one_evaluation_permit_consumed") is not True
        or payload.get("checkpoint_tree_verified") is not True
        or payload.get("model_loaded_at_marker") is not False
        or payload.get("model_inference_at_marker") is not False
        or payload.get("optimizer_created_at_marker") is not False
        or payload.get("optimizer_training") is not False
        or payload.get("checkpoint_mutated") is not False
        or payload.get("closed_loop_rollout") is not False
        or payload.get("physical_actuation") is not False
        or payload.get("external_compute_started") is not False
        or payload.get("brev_compute_started") is not False
    ):
        raise ValueError("T20.35o trajectory attempt drifted")


def build_result(
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    attempt: dict[str, Any],
    source_result: dict[str, Any],
    target_chunk: list[list[float]],
    normalized_padded_target: list[list[float]],
    trajectory_evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35o result spec")
    verify_signed_payload(source_result, label="T20.35o result source")
    verify_evaluation_permit(permit, spec=spec)
    verify_attempt_marker(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
    )
    if source_result.get("identity_sha256") != spec.get(
        "t20_35n_result_identity_sha256"
    ):
        raise ValueError("T20.35o source result identity drifted")
    if _matrix_sha(target_chunk) != spec.get("dataset_action_chunk_sha256"):
        raise ValueError("T20.35o target action chunk drifted")
    _finite_matrix(
        target_chunk,
        rows=50,
        columns=ACTIVE_ACTION_DIMENSIONS,
        label="target action chunk",
    )
    normalized = _finite_matrix(
        normalized_padded_target,
        rows=50,
        columns=MAXIMUM_ACTION_DIMENSIONS,
        label="normalized padded target",
    )
    if any(
        value != 0.0
        for row in normalized
        for value in row[ACTIVE_ACTION_DIMENSIONS:]
    ):
        raise ValueError("T20.35o normalized padded target has nonzero padding")

    source_rows = _seed_rows(
        _active_zero_evaluation(source_result).get("decoded_action_chunks")
    )
    rows = _seed_rows(trajectory_evaluations)
    evaluated: list[dict[str, Any]] = []
    all_step_active_means: list[list[float]] = []
    channel_totals = [0.0] * ACTIVE_ACTION_DIMENSIONS
    total_active_absolute = 0.0
    late_active_absolute = 0.0
    for seed_index, (row, source_row) in enumerate(zip(rows, source_rows, strict=True)):
        if row.get("inference_seed") != INFERENCE_SEEDS[seed_index]:
            raise ValueError("T20.35o trajectory inference seed drifted")
        if row.get("base_noise_sha256") != spec["base_noise_sha256_by_seed"][seed_index]:
            raise ValueError("T20.35o trajectory base-noise hash drifted")
        decoded = _finite_matrix(
            row.get("decoded_action_chunk"),
            rows=50,
            columns=ACTIVE_ACTION_DIMENSIONS,
            label="decoded endpoint",
        )
        decoded_sha = _matrix_sha(decoded)
        if (
            decoded_sha != spec["source_decoded_action_sha256_by_seed"][seed_index]
            or decoded_sha != source_row.get("decoded_action_chunk_sha256")
        ):
            raise ValueError("T20.35o decoded endpoint failed exact reproduction")
        raw_steps = row.get("steps")
        if not isinstance(raw_steps, list) or len(raw_steps) != NUM_INFERENCE_STEPS:
            raise ValueError("T20.35o trajectory step coverage drifted")
        steps: list[dict[str, Any]] = []
        seed_step_means: list[float] = []
        for step_index, step in enumerate(raw_steps):
            if not isinstance(step, dict) or step.get("step_index") != step_index:
                raise ValueError("T20.35o trajectory step order drifted")
            expected_time = 1.0 - step_index / NUM_INFERENCE_STEPS
            time = _finite_number(step.get("time"), "trajectory time")
            if abs(time - expected_time) > 1e-12 or time <= 0.0:
                raise ValueError("T20.35o trajectory time drifted")
            state = _finite_matrix(
                step.get("state"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="trajectory state",
            )
            velocity = _finite_matrix(
                step.get("learned_velocity"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="learned velocity",
            )
            if step_index == 0 and any(
                value != 0.0
                for state_row in state
                for value in state_row[:ACTIVE_ACTION_DIMENSIONS]
            ):
                raise ValueError("T20.35o initial active state is not zero")
            residual = [
                [
                    velocity[t][j] - (state[t][j] - normalized[t][j]) / time
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for t in range(50)
            ]
            active_values = [
                abs(residual[t][j])
                for t in range(50)
                for j in range(ACTIVE_ACTION_DIMENSIONS)
            ]
            padded_values = [
                abs(residual[t][j])
                for t in range(50)
                for j in range(ACTIVE_ACTION_DIMENSIONS, MAXIMUM_ACTION_DIMENSIONS)
            ]
            by_channel = [
                sum(abs(residual[t][j]) for t in range(50)) / 50
                for j in range(ACTIVE_ACTION_DIMENSIONS)
            ]
            active_sum = sum(active_values)
            total_active_absolute += active_sum
            if step_index >= LATE_STEP_START_INDEX:
                late_active_absolute += active_sum
            for channel, value in enumerate(by_channel):
                channel_totals[channel] += value
            active_mean = active_sum / len(active_values)
            seed_step_means.append(active_mean)
            steps.append(
                {
                    "step_index": step_index,
                    "time": time,
                    "state": state,
                    "state_sha256": _matrix_sha(state),
                    "learned_velocity": velocity,
                    "learned_velocity_sha256": _matrix_sha(velocity),
                    "active_velocity_residual_matrix_sha256": _matrix_sha(
                        [values[:ACTIVE_ACTION_DIMENSIONS] for values in residual]
                    ),
                    "padded_velocity_residual_matrix_sha256": _matrix_sha(
                        [values[ACTIVE_ACTION_DIMENSIONS:] for values in residual]
                    ),
                    "active_velocity_residual_maximum": max(active_values),
                    "active_velocity_residual_mean_absolute": active_mean,
                    "active_velocity_residual_mean_absolute_by_channel": by_channel,
                    "padded_velocity_residual_maximum": max(padded_values),
                    "padded_velocity_residual_mean_absolute": sum(padded_values)
                    / len(padded_values),
                }
            )
        all_step_active_means.append(seed_step_means)
        evaluated.append(
            {
                "inference_seed": row["inference_seed"],
                "base_noise_sha256": row["base_noise_sha256"],
                "decoded_action_chunk": decoded,
                "decoded_action_chunk_sha256": decoded_sha,
                "steps": steps,
            }
        )

    last_three_fraction = (
        late_active_absolute / total_active_absolute
        if total_active_absolute > 0.0
        else 0.0
    )
    channel_total = sum(channel_totals)
    channel_fractions = (
        [value / channel_total for value in channel_totals]
        if channel_total > 0.0
        else [0.0] * ACTIVE_ACTION_DIMENSIONS
    )
    dominant_channel = max(
        range(ACTIVE_ACTION_DIMENSIONS), key=lambda index: channel_fractions[index]
    )
    if last_three_fraction >= CONCENTRATION_THRESHOLD:
        classification = "late_step_active_flow_residual_concentrated"
        route = "design_terminal_time_flow_consistency_training_correction"
    elif channel_fractions[dominant_channel] >= CONCENTRATION_THRESHOLD:
        classification = "active_channel_flow_residual_concentrated"
        route = "audit_dominant_active_channel_training_semantics"
    else:
        classification = "distributed_active_flow_residual"
        route = "design_full_path_flow_consistency_training_correction"
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35o",
            "scope": "one_inference_only_active_zero_padded_normal_flow_trajectory_consistency_result",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "evaluation_attempt_identity_sha256": attempt["identity_sha256"],
            "t20_35n_result_identity_sha256": source_result["identity_sha256"],
            "checkpoint_identity_sha256": spec["checkpoint_identity_sha256"],
            "dataset_action_chunk_sha256": spec["dataset_action_chunk_sha256"],
            "normalized_padded_target": normalized,
            "normalized_padded_target_sha256": _matrix_sha(normalized),
            "active_noise_scale": ACTIVE_NOISE_SCALE,
            "padded_noise_scale": PADDED_NOISE_SCALE,
            "num_inference_steps": NUM_INFERENCE_STEPS,
            "trajectory_evaluations": evaluated,
            "aggregate_active_velocity_residual_mean_absolute_by_step": [
                sum(values[step] for values in all_step_active_means)
                / len(all_step_active_means)
                for step in range(NUM_INFERENCE_STEPS)
            ],
            "aggregate_active_velocity_residual_mean_absolute_by_channel": [
                value / (len(INFERENCE_SEEDS) * NUM_INFERENCE_STEPS)
                for value in channel_totals
            ],
            "last_three_step_active_residual_fraction": last_three_fraction,
            "dominant_active_channel_index": dominant_channel,
            "dominant_active_channel_residual_fraction": channel_fractions[
                dominant_channel
            ],
            "flow_residual_classification": classification,
            "gate_b_passed": False,
            "selected_next_hypothesis": route,
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_read": True,
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


def verify_result(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    attempt: dict[str, Any],
    source_result: dict[str, Any],
    target_chunk: list[list[float]],
) -> None:
    verify_signed_payload(payload, label="T20.35o trajectory result")
    expected = build_result(
        spec=spec,
        permit=permit,
        attempt=attempt,
        source_result=source_result,
        target_chunk=target_chunk,
        normalized_padded_target=payload.get("normalized_padded_target"),
        trajectory_evaluations=payload.get("trajectory_evaluations"),
    )
    archived = {key: value for key, value in payload.items() if key != "identity_sha256"}
    rebuilt = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(archived, rebuilt, absolute_tolerance=1e-15):
        raise ValueError("T20.35o trajectory result drifted")


def load_and_verify_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35n_sources(repo_root=root)
    source_spec = sources["active_scale_spec"]
    source_permit = sources["active_scale_permit"]
    source_attempt = load_strict_json(root / T20_35N_ATTEMPT_PATH)
    verify_t20_35n_attempt(
        source_attempt,
        spec_identity=source_spec["identity_sha256"],
        permit_identity=source_permit["identity_sha256"],
    )
    source_result = load_strict_json(root / T20_35N_RESULT_PATH)
    target = sources["residual_report"]["target_action_chunk"]
    verify_t20_35n_result(
        source_result,
        spec=source_spec,
        permit=source_permit,
        attempt=source_attempt,
        source_result=sources["source_result"],
        target_chunk=target,
    )
    if source_result["identity_sha256"] != EXPECTED_T20_35N_RESULT_IDENTITY:
        raise ValueError("T20.35o expected source result identity drifted")
    expected = build_evaluation_spec(
        source_spec=source_spec, source_result=source_result
    )
    spec = load_strict_json(root / SPEC_PATH)
    verify_evaluation_spec(spec, expected_spec=expected)
    permit = load_strict_json(root / PERMIT_PATH)
    verify_evaluation_permit(permit, spec=spec)
    return {
        **sources,
        "source_spec": source_spec,
        "source_result": source_result,
        "trajectory_spec": spec,
        "trajectory_permit": permit,
    }


def write_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35n_sources(repo_root=root)
    source_spec = sources["active_scale_spec"]
    source_permit = sources["active_scale_permit"]
    source_attempt = load_strict_json(root / T20_35N_ATTEMPT_PATH)
    verify_t20_35n_attempt(
        source_attempt,
        spec_identity=source_spec["identity_sha256"],
        permit_identity=source_permit["identity_sha256"],
    )
    source_result = load_strict_json(root / T20_35N_RESULT_PATH)
    target = sources["residual_report"]["target_action_chunk"]
    verify_t20_35n_result(
        source_result,
        spec=source_spec,
        permit=source_permit,
        attempt=source_attempt,
        source_result=sources["source_result"],
        target_chunk=target,
    )
    spec = build_evaluation_spec(source_spec=source_spec, source_result=source_result)
    permit = build_evaluation_permit(spec=spec)
    dump_canonical_json(root / SPEC_PATH, spec)
    dump_canonical_json(root / PERMIT_PATH, permit)
    return {"trajectory_spec": spec, "trajectory_permit": permit}


def _active_zero_evaluation(source_result: dict[str, Any]) -> dict[str, Any]:
    matches = [
        row
        for row in source_result.get("active_scale_evaluations", [])
        if isinstance(row, dict) and row.get("active_noise_scale") == ACTIVE_NOISE_SCALE
    ]
    if len(matches) != 1 or matches[0].get("padded_noise_scale") != PADDED_NOISE_SCALE:
        raise ValueError("T20.35o active-zero/padded-normal source is ambiguous")
    return matches[0]


def _seed_rows(value: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or len(value) != len(INFERENCE_SEEDS)
        or any(not isinstance(row, dict) for row in value)
    ):
        raise ValueError("T20.35o seed coverage drifted")
    return value


def _finite_matrix(
    value: Any, *, rows: int, columns: int, label: str
) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != rows:
        raise ValueError(f"T20.35o {label} row count drifted")
    matrix: list[list[float]] = []
    for row in value:
        if not isinstance(row, list) or len(row) != columns:
            raise ValueError(f"T20.35o {label} column count drifted")
        matrix.append([_finite_number(item, label) for item in row])
    return matrix


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.35o {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.35o {label} must be finite")
    return number


def _matrix_sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35o {label} must be lowercase SHA-256")
