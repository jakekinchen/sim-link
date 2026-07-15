"""Active-versus-padded PI0.5 initial-noise mask discriminator for T20.35l."""

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
from scenesmith.robot_lab.t20_35j_initial_noise_scale_discriminator import (
    ATTEMPT_PATH as T20_35J_ATTEMPT_PATH,
    RESULT_PATH as T20_35J_RESULT_PATH,
    _aggregate_raw_spread,
    _evaluate_chunks,
    load_and_verify_evaluation_files as load_t20_35j_sources,
    verify_attempt_marker as verify_t20_35j_attempt,
    verify_result as verify_t20_35j_result,
)
from scenesmith.robot_lab.t20_35k_sampler_noise_distribution_audit import (
    verify_audit_file as verify_t20_35k_audit_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(
    "configurations/robot_lab/t20_35l_active_padded_noise_mask_spec.json"
)
PERMIT_PATH = Path(
    "configurations/robot_lab/t20_35l_active_padded_noise_mask_evaluation_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_35l_active_padded_noise_mask_result.json"
)
ATTEMPT_PATH = Path(
    "outputs/robot_lab/t20_35l_active_padded_noise_mask/attempt.json"
)
SCHEMA_VERSION = "scenesmith.t20_35l_active_padded_noise_mask_spec.v1"
PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_35l_active_padded_noise_mask_evaluation_permit.v1"
)
RESULT_SCHEMA_VERSION = "scenesmith.t20_35l_active_padded_noise_mask_result.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_35l_evaluation_attempt.v1"
ACTIVE_ACTION_DIMENSIONS = 6
MAXIMUM_ACTION_DIMENSIONS = 32
PADDED_ACTION_DIMENSIONS = 26
NUM_INFERENCE_STEPS = 10
MIXED_NOISE_CONDITIONS = (
    "active_normal_padded_zero",
    "active_zero_padded_normal",
)
ALL_NOISE_CONDITIONS = (
    "active_normal_padded_normal",
    *MIXED_NOISE_CONDITIONS,
    "active_zero_padded_zero",
)
EXPECTED_T20_35J_RESULT_IDENTITY = (
    "e9bbff84864a838f64e67c72a4996fd4eefe13739294becc43a371268f3da75a"
)
EXPECTED_T20_35K_AUDIT_IDENTITY = (
    "bc9f08458b2339757c1dc7a8266df34332df911209bab1154b5d1ce9a1a4ad60"
)
INHERITED_AUTHORITY_IDENTITY = (
    "75dc9c7d860e12e2a2114be709e24f7e544ff576696a3d223dd87dd0e2f06606"
)
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T23:27:47-05:00"


def noise_mask_for_condition(
    condition: str, *, active_dimensions: int, maximum_dimensions: int
) -> list[float]:
    if condition not in MIXED_NOISE_CONDITIONS:
        raise ValueError("T20.35l unknown mixed-noise condition")
    if (
        isinstance(active_dimensions, bool)
        or not isinstance(active_dimensions, int)
        or isinstance(maximum_dimensions, bool)
        or not isinstance(maximum_dimensions, int)
        or not 0 < active_dimensions < maximum_dimensions
    ):
        raise ValueError("T20.35l invalid active/padded dimensions")
    active_value = 1.0 if condition == "active_normal_padded_zero" else 0.0
    padded_value = 1.0 - active_value
    return [active_value] * active_dimensions + [padded_value] * (
        maximum_dimensions - active_dimensions
    )


def build_evaluation_spec(
    *,
    sampler_audit: dict[str, Any],
    source_spec: dict[str, Any],
    source_result: dict[str, Any],
) -> dict[str, Any]:
    for label, payload in (
        ("sampler audit", sampler_audit),
        ("source spec", source_spec),
        ("source result", source_result),
    ):
        verify_signed_payload(payload, label=f"T20.35l {label}")
    if (
        sampler_audit.get("t20_35j_result_identity_sha256")
        != source_result.get("identity_sha256")
        or sampler_audit.get("sampler_classification")
        != "matched_standard_normal_sampler_with_unsupervised_padded_noise_exposure"
        or sampler_audit.get("selected_next_hypothesis")
        != "run_separately_reviewed_active_vs_padded_noise_mask_discriminator"
        or sampler_audit.get("supervised_action_dimension_count")
        != ACTIVE_ACTION_DIMENSIONS
        or sampler_audit.get("maximum_action_dimension_count")
        != MAXIMUM_ACTION_DIMENSIONS
        or sampler_audit.get("padded_action_dimension_count")
        != PADDED_ACTION_DIMENSIONS
        or sampler_audit.get("gate_b_passed") is not False
        or source_result.get("initial_noise_scale_effect_positive") is not True
        or source_result.get("selected_initial_noise_scale") != 0.0
        or source_result.get("gate_b_passed") is not False
        or source_spec.get("source_objective_ratio_within_threshold") is not True
    ):
        raise ValueError("T20.35l source route or dimensions drifted")
    all_normal = _source_endpoint(source_result, 1.0)
    all_zero = _source_endpoint(source_result, 0.0)
    normal_hashes, base_noise_hashes = _endpoint_hashes(all_normal)
    zero_hashes, zero_base_hashes = _endpoint_hashes(all_zero)
    if zero_base_hashes != base_noise_hashes:
        raise ValueError("T20.35l inherited endpoint base-noise hashes drifted")
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35l",
            "scope": "one_inference_only_active_six_vs_padded_twenty_six_noise_mask_discriminator",
            "t20_35j_spec_identity_sha256": source_spec["identity_sha256"],
            "t20_35j_result_identity_sha256": source_result["identity_sha256"],
            "t20_35k_audit_identity_sha256": sampler_audit["identity_sha256"],
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
            "padded_action_dimension_count": PADDED_ACTION_DIMENSIONS,
            "inference_seeds": list(INFERENCE_SEEDS),
            "num_inference_steps": NUM_INFERENCE_STEPS,
            "inherited_noise_conditions": [
                "active_normal_padded_normal",
                "active_zero_padded_zero",
            ],
            "evaluated_noise_conditions": list(MIXED_NOISE_CONDITIONS),
            "all_noise_conditions": list(ALL_NOISE_CONDITIONS),
            "base_noise_sha256_by_seed": base_noise_hashes,
            "source_all_normal_decoded_action_sha256_by_seed": normal_hashes,
            "source_all_zero_decoded_action_sha256_by_seed": zero_hashes,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "directional_improvement_rule": (
                "mixed_condition_worst_seed_maximum_aggregate_mean_and_aggregate_"
                "raw_spread_all_strictly_below_all_normal"
            ),
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
    verify_signed_payload(payload, label="T20.35l noise-mask spec")
    verify_signed_payload(expected_spec, label="T20.35l expected noise-mask spec")
    if payload != expected_spec:
        raise ValueError("T20.35l noise-mask spec drifted")


def build_evaluation_permit(*, spec: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35l permit source spec")
    if (
        spec.get("evaluated_noise_conditions") != list(MIXED_NOISE_CONDITIONS)
        or spec.get("active_action_dimension_count") != ACTIVE_ACTION_DIMENSIONS
        or spec.get("padded_action_dimension_count") != PADDED_ACTION_DIMENSIONS
    ):
        raise ValueError("T20.35l permit source spec drifted")
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": "T20.35l",
            "scope": "one_local_mps_inference_only_active_padded_noise_mask_evaluation",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "inherited_authority_decision_identity_sha256": INHERITED_AUTHORITY_IDENTITY,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "evaluated_noise_conditions": list(MIXED_NOISE_CONDITIONS),
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
    verify_signed_payload(payload, label="T20.35l noise-mask permit")
    if payload != build_evaluation_permit(spec=spec):
        raise ValueError("T20.35l noise-mask permit drifted")


def verify_attempt_marker(
    payload: dict[str, Any], *, spec_identity: str, permit_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35l noise-mask attempt")
    if (
        payload.get("schema_version") != ATTEMPT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35l"
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
        raise ValueError("T20.35l noise-mask attempt drifted")


def build_result(
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    attempt: dict[str, Any],
    source_result: dict[str, Any],
    target_chunk: list[list[float]],
    mixed_condition_evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35l result spec")
    verify_signed_payload(source_result, label="T20.35l result source")
    verify_evaluation_permit(permit, spec=spec)
    verify_attempt_marker(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
    )
    if source_result["identity_sha256"] != spec["t20_35j_result_identity_sha256"]:
        raise ValueError("T20.35l source result identity drifted")
    if hashlib.sha256(canonical_json_bytes(target_chunk)).hexdigest() != spec[
        "dataset_action_chunk_sha256"
    ]:
        raise ValueError("T20.35l target action chunk drifted")
    if (
        not isinstance(mixed_condition_evaluations, list)
        or [
            row.get("noise_condition")
            for row in mixed_condition_evaluations
            if isinstance(row, dict)
        ]
        != list(MIXED_NOISE_CONDITIONS)
    ):
        raise ValueError("T20.35l mixed-noise condition set or order drifted")

    all_normal = _condition_from_source(
        "active_normal_padded_normal", _source_endpoint(source_result, 1.0), target_chunk
    )
    all_zero = _condition_from_source(
        "active_zero_padded_zero", _source_endpoint(source_result, 0.0), target_chunk
    )
    mixed = [
        _condition_from_chunks(
            row["noise_condition"], row.get("decoded_action_chunks"), target_chunk
        )
        for row in mixed_condition_evaluations
    ]
    expected_noise_hashes = spec["base_noise_sha256_by_seed"]
    for row in mixed:
        hashes = [
            item["base_noise_sha256"] for item in row["decoded_action_chunks"]
        ]
        if hashes != expected_noise_hashes:
            raise ValueError("T20.35l mixed-condition base noise changed")
    conditions = [all_normal, mixed[0], mixed[1], all_zero]
    for row in mixed:
        row["improves_all_normal_worst_seed_maximum"] = (
            row["worst_seed_maximum_error_rad"]
            < all_normal["worst_seed_maximum_error_rad"]
        )
        row["improves_all_normal_aggregate_mean"] = (
            row["aggregate_mean_absolute_error_rad"]
            < all_normal["aggregate_mean_absolute_error_rad"]
        )
        row["improves_all_normal_aggregate_raw_spread"] = (
            row["aggregate_mean_raw_decoded_spread_rad"]
            < all_normal["aggregate_mean_raw_decoded_spread_rad"]
        )
        row["directionally_improves_all_metrics"] = all(
            (
                row["improves_all_normal_worst_seed_maximum"],
                row["improves_all_normal_aggregate_mean"],
                row["improves_all_normal_aggregate_raw_spread"],
            )
        )
    passing = [row for row in mixed if row["all_decoded_chunks_within_threshold"]]
    padded_positive = mixed[0]["directionally_improves_all_metrics"]
    active_positive = mixed[1]["directionally_improves_all_metrics"]
    if passing:
        selected = min(
            passing,
            key=lambda row: (
                row["worst_seed_maximum_error_rad"],
                row["aggregate_mean_absolute_error_rad"],
                MIXED_NOISE_CONDITIONS.index(row["noise_condition"]),
            ),
        )
        selected_condition = selected["noise_condition"]
        gate_b_passed = True
        classification = "mixed_noise_mask_gate_b_pass"
        route = "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction"
    elif padded_positive and not active_positive:
        selected_condition = mixed[0]["noise_condition"]
        gate_b_passed = False
        classification = "padded_noise_sensitivity_isolated"
        route = "audit_padded_noise_handling_and_trainable_invariance"
    elif active_positive and not padded_positive:
        selected_condition = mixed[1]["noise_condition"]
        gate_b_passed = False
        classification = "active_action_noise_sensitivity_isolated"
        route = "audit_active_action_flow_consistency"
    elif padded_positive and active_positive:
        selected_condition = min(
            mixed,
            key=lambda row: (
                row["worst_seed_maximum_error_rad"],
                row["aggregate_mean_absolute_error_rad"],
            ),
        )["noise_condition"]
        gate_b_passed = False
        classification = "joint_active_and_padded_noise_sensitivity"
        route = "audit_joint_active_padded_flow_robustness"
    else:
        selected_condition = None
        gate_b_passed = False
        classification = "mixed_noise_masks_rejected"
        route = "route_general_model_robustness_correction"
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35l",
            "scope": "one_inference_only_active_six_vs_padded_twenty_six_noise_mask_result",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "evaluation_attempt_identity_sha256": attempt["identity_sha256"],
            "t20_35j_result_identity_sha256": source_result["identity_sha256"],
            "t20_35k_audit_identity_sha256": spec[
                "t20_35k_audit_identity_sha256"
            ],
            "checkpoint_identity_sha256": spec["checkpoint_identity_sha256"],
            "dataset_action_chunk_sha256": spec["dataset_action_chunk_sha256"],
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "active_action_dimension_count": ACTIVE_ACTION_DIMENSIONS,
            "maximum_action_dimension_count": MAXIMUM_ACTION_DIMENSIONS,
            "padded_action_dimension_count": PADDED_ACTION_DIMENSIONS,
            "condition_evaluations": conditions,
            "padded_noise_sensitivity_positive": padded_positive,
            "active_action_noise_sensitivity_positive": active_positive,
            "selected_noise_condition": selected_condition,
            "noise_mask_classification": classification,
            "gate_b_passed": gate_b_passed,
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
    verify_signed_payload(payload, label="T20.35l noise-mask result")
    mixed_rows = [
        {
            "noise_condition": row.get("noise_condition"),
            "decoded_action_chunks": row.get("decoded_action_chunks"),
        }
        for row in payload.get("condition_evaluations", [])
        if isinstance(row, dict) and row.get("noise_condition") in MIXED_NOISE_CONDITIONS
    ]
    expected = build_result(
        spec=spec,
        permit=permit,
        attempt=attempt,
        source_result=source_result,
        target_chunk=target_chunk,
        mixed_condition_evaluations=mixed_rows,
    )
    archived_content = {key: value for key, value in payload.items() if key != "identity_sha256"}
    expected_content = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(
        archived_content, expected_content, absolute_tolerance=1e-15
    ):
        raise ValueError("T20.35l noise-mask result drifted")


def load_and_verify_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35j_sources(repo_root=root)
    source_spec = sources["noise_scale_spec"]
    source_permit = sources["noise_scale_permit"]
    source_attempt = load_strict_json(root / T20_35J_ATTEMPT_PATH)
    verify_t20_35j_attempt(
        source_attempt,
        spec_identity=source_spec["identity_sha256"],
        permit_identity=source_permit["identity_sha256"],
    )
    source_result = load_strict_json(root / T20_35J_RESULT_PATH)
    target = sources["residual_report"]["target_action_chunk"]
    verify_t20_35j_result(
        source_result,
        spec=source_spec,
        permit=source_permit,
        attempt=source_attempt,
        target_chunk=target,
    )
    sampler_audit = verify_t20_35k_audit_file(repo_root=root)
    if (
        source_result["identity_sha256"] != EXPECTED_T20_35J_RESULT_IDENTITY
        or sampler_audit["identity_sha256"] != EXPECTED_T20_35K_AUDIT_IDENTITY
    ):
        raise ValueError("T20.35l expected source identity drifted")
    expected = build_evaluation_spec(
        sampler_audit=sampler_audit,
        source_spec=source_spec,
        source_result=source_result,
    )
    spec = load_strict_json(root / SPEC_PATH)
    verify_evaluation_spec(spec, expected_spec=expected)
    permit = load_strict_json(root / PERMIT_PATH)
    verify_evaluation_permit(permit, spec=spec)
    return {
        **sources,
        "source_result": source_result,
        "sampler_audit": sampler_audit,
        "noise_mask_spec": spec,
        "noise_mask_permit": permit,
    }


def write_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35j_sources(repo_root=root)
    source_spec = sources["noise_scale_spec"]
    source_permit = sources["noise_scale_permit"]
    source_attempt = load_strict_json(root / T20_35J_ATTEMPT_PATH)
    source_result = load_strict_json(root / T20_35J_RESULT_PATH)
    target = sources["residual_report"]["target_action_chunk"]
    verify_t20_35j_attempt(
        source_attempt,
        spec_identity=source_spec["identity_sha256"],
        permit_identity=source_permit["identity_sha256"],
    )
    verify_t20_35j_result(
        source_result,
        spec=source_spec,
        permit=source_permit,
        attempt=source_attempt,
        target_chunk=target,
    )
    sampler_audit = verify_t20_35k_audit_file(repo_root=root)
    spec = build_evaluation_spec(
        sampler_audit=sampler_audit,
        source_spec=source_spec,
        source_result=source_result,
    )
    permit = build_evaluation_permit(spec=spec)
    dump_canonical_json(root / SPEC_PATH, spec)
    dump_canonical_json(root / PERMIT_PATH, permit)
    return {"noise_mask_spec": spec, "noise_mask_permit": permit}


def _source_endpoint(source_result: dict[str, Any], scale: float) -> dict[str, Any]:
    matches = [
        row
        for row in source_result.get("scale_evaluations", [])
        if isinstance(row, dict) and row.get("initial_noise_scale") == scale
    ]
    if len(matches) != 1:
        raise ValueError("T20.35l inherited endpoint is ambiguous")
    return matches[0]


def _endpoint_hashes(endpoint: dict[str, Any]) -> tuple[list[str], list[str]]:
    rows = endpoint.get("decoded_action_chunks")
    if (
        not isinstance(rows, list)
        or len(rows) != len(INFERENCE_SEEDS)
        or [row.get("inference_seed") for row in rows if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35l inherited endpoint seed coverage drifted")
    action_hashes = []
    noise_hashes = []
    for row in rows:
        digest = hashlib.sha256(
            canonical_json_bytes(row.get("decoded_action_chunk"))
        ).hexdigest()
        if row.get("decoded_action_chunk_sha256") != digest:
            raise ValueError("T20.35l inherited endpoint action hash drifted")
        _sha(row.get("base_noise_sha256"), "base-noise hash")
        action_hashes.append(digest)
        noise_hashes.append(row["base_noise_sha256"])
    return action_hashes, noise_hashes


def _condition_from_source(
    condition: str, endpoint: dict[str, Any], target: list[list[float]]
) -> dict[str, Any]:
    return _condition_from_chunks(condition, endpoint.get("decoded_action_chunks"), target)


def _condition_from_chunks(
    condition: str, chunks: Any, target: list[list[float]]
) -> dict[str, Any]:
    if condition not in ALL_NOISE_CONDITIONS:
        raise ValueError("T20.35l noise condition drifted")
    evaluated = _evaluate_chunks(chunks, target=target)
    return {
        "noise_condition": condition,
        "decoded_action_chunks": evaluated,
        "all_decoded_chunks_within_threshold": all(
            row["maximum_absolute_error_rad"] <= MAX_ACTION_ERROR_RAD
            for row in evaluated
        ),
        "worst_seed_maximum_error_rad": max(
            row["maximum_absolute_error_rad"] for row in evaluated
        ),
        "aggregate_mean_absolute_error_rad": sum(
            row["mean_absolute_error_rad"] for row in evaluated
        )
        / len(evaluated),
        "aggregate_mean_raw_decoded_spread_rad": _aggregate_raw_spread(evaluated),
    }


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35l {label} must be lowercase SHA-256")
