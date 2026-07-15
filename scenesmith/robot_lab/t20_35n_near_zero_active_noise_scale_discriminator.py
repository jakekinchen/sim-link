"""Near-zero active-noise scale discriminator for T20.35n."""

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
    _aggregate_raw_spread,
    _evaluate_chunks,
)
from scenesmith.robot_lab.t20_35l_active_padded_noise_mask_discriminator import (
    ATTEMPT_PATH as T20_35L_ATTEMPT_PATH,
    RESULT_PATH as T20_35L_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35l_sources,
    verify_attempt_marker as verify_t20_35l_attempt,
    verify_result as verify_t20_35l_result,
)
from scenesmith.robot_lab.t20_35m_active_padded_factorial_interaction_audit import (
    verify_audit_file as verify_t20_35m_audit_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(
    "configurations/robot_lab/t20_35n_near_zero_active_noise_scale_spec.json"
)
PERMIT_PATH = Path(
    "configurations/robot_lab/t20_35n_near_zero_active_noise_scale_evaluation_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_35n_near_zero_active_noise_scale_result.json"
)
ATTEMPT_PATH = Path(
    "outputs/robot_lab/t20_35n_near_zero_active_noise_scale/attempt.json"
)
SCHEMA_VERSION = "scenesmith.t20_35n_near_zero_active_noise_scale_spec.v1"
PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_35n_near_zero_active_noise_scale_evaluation_permit.v1"
)
RESULT_SCHEMA_VERSION = "scenesmith.t20_35n_near_zero_active_noise_scale_result.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_35n_evaluation_attempt.v1"
ACTIVE_ACTION_DIMENSIONS = 6
MAXIMUM_ACTION_DIMENSIONS = 32
PADDED_NOISE_SCALE = 1.0
INHERITED_ACTIVE_NOISE_SCALES = (0.0, 1.0)
EVALUATED_ACTIVE_NOISE_SCALES = (0.25, 0.5)
ALL_ACTIVE_NOISE_SCALES = (0.0, 0.25, 0.5, 1.0)
NUM_INFERENCE_STEPS = 10
EXPECTED_T20_35L_RESULT_IDENTITY = (
    "b4fc6060c56431ab2bf52dd74d8efa58b1808a10a827521db076f9d10234dbea"
)
EXPECTED_T20_35M_AUDIT_IDENTITY = (
    "83105424d6faf668d8a41a70999e25a82338bb2537c802f5a4a60803df3cedb0"
)
INHERITED_AUTHORITY_IDENTITY = (
    "75dc9c7d860e12e2a2114be709e24f7e544ff576696a3d223dd87dd0e2f06606"
)
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T23:27:47-05:00"


def active_noise_mask(
    active_scale: float, *, active_dimensions: int, maximum_dimensions: int
) -> list[float]:
    scale = _active_scale(active_scale, allowed=EVALUATED_ACTIVE_NOISE_SCALES)
    if (
        isinstance(active_dimensions, bool)
        or not isinstance(active_dimensions, int)
        or isinstance(maximum_dimensions, bool)
        or not isinstance(maximum_dimensions, int)
        or not 0 < active_dimensions < maximum_dimensions
    ):
        raise ValueError("T20.35n invalid active/padded dimensions")
    return [scale] * active_dimensions + [PADDED_NOISE_SCALE] * (
        maximum_dimensions - active_dimensions
    )


def build_evaluation_spec(
    *,
    factorial_audit: dict[str, Any],
    source_spec: dict[str, Any],
    source_result: dict[str, Any],
) -> dict[str, Any]:
    for label, payload in (
        ("factorial audit", factorial_audit),
        ("source spec", source_spec),
        ("source result", source_result),
    ):
        verify_signed_payload(payload, label=f"T20.35n {label}")
    if (
        factorial_audit.get("t20_35l_result_identity_sha256")
        != source_result.get("identity_sha256")
        or factorial_audit.get("interaction_classification")
        != "active_noise_dominant_with_context_dependent_padded_interaction"
        or factorial_audit.get("selected_next_hypothesis")
        != "run_separately_reviewed_near_zero_active_noise_scale_discriminator_with_padded_normal"
        or factorial_audit.get("best_noise_condition")
        != "active_zero_padded_normal"
        or factorial_audit.get(
            "active_noise_harmful_at_both_padded_settings_all_metrics"
        )
        is not True
        or factorial_audit.get("gate_b_passed") is not False
        or source_result.get("noise_mask_classification")
        != "joint_active_and_padded_noise_sensitivity"
        or source_result.get("gate_b_passed") is not False
        or source_spec.get("source_objective_ratio_within_threshold") is not True
    ):
        raise ValueError("T20.35n source route drifted")
    active_zero = _source_condition(source_result, "active_zero_padded_normal")
    active_one = _source_condition(source_result, "active_normal_padded_normal")
    zero_hashes, zero_noise_hashes = _condition_hashes(active_zero)
    one_hashes, one_noise_hashes = _condition_hashes(active_one)
    if zero_noise_hashes != one_noise_hashes:
        raise ValueError("T20.35n inherited base-noise hashes drifted")
    if source_spec.get("base_noise_sha256_by_seed") != zero_noise_hashes:
        raise ValueError("T20.35n source spec base-noise hashes drifted")
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35n",
            "scope": "one_inference_only_near_zero_active_noise_scale_discriminator_with_padded_normal",
            "t20_35l_spec_identity_sha256": source_spec["identity_sha256"],
            "t20_35l_result_identity_sha256": source_result["identity_sha256"],
            "t20_35m_audit_identity_sha256": factorial_audit["identity_sha256"],
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
            "padded_noise_scale": PADDED_NOISE_SCALE,
            "inherited_active_noise_scales": list(INHERITED_ACTIVE_NOISE_SCALES),
            "evaluated_active_noise_scales": list(EVALUATED_ACTIVE_NOISE_SCALES),
            "all_active_noise_scales": list(ALL_ACTIVE_NOISE_SCALES),
            "inference_seeds": list(INFERENCE_SEEDS),
            "num_inference_steps": NUM_INFERENCE_STEPS,
            "base_noise_sha256_by_seed": zero_noise_hashes,
            "source_active_zero_decoded_action_sha256_by_seed": zero_hashes,
            "source_active_one_decoded_action_sha256_by_seed": one_hashes,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "passing_selection_rule": "largest_passing_active_noise_scale",
            "nonpassing_selection_rule": (
                "lowest_worst_error_then_lowest_mean_then_largest_active_scale"
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
    verify_signed_payload(payload, label="T20.35n active-scale spec")
    verify_signed_payload(expected_spec, label="T20.35n expected active-scale spec")
    if payload != expected_spec:
        raise ValueError("T20.35n active-scale spec drifted")


def build_evaluation_permit(*, spec: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35n permit source spec")
    if (
        spec.get("evaluated_active_noise_scales")
        != list(EVALUATED_ACTIVE_NOISE_SCALES)
        or spec.get("padded_noise_scale") != PADDED_NOISE_SCALE
    ):
        raise ValueError("T20.35n permit source spec drifted")
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": "T20.35n",
            "scope": "one_local_mps_inference_only_near_zero_active_noise_scale_evaluation",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "inherited_authority_decision_identity_sha256": INHERITED_AUTHORITY_IDENTITY,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "evaluated_active_noise_scales": list(EVALUATED_ACTIVE_NOISE_SCALES),
            "padded_noise_scale": PADDED_NOISE_SCALE,
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
    verify_signed_payload(payload, label="T20.35n active-scale permit")
    if payload != build_evaluation_permit(spec=spec):
        raise ValueError("T20.35n active-scale permit drifted")


def verify_attempt_marker(
    payload: dict[str, Any], *, spec_identity: str, permit_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35n active-scale attempt")
    if (
        payload.get("schema_version") != ATTEMPT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35n"
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
        raise ValueError("T20.35n active-scale attempt drifted")


def build_result(
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    attempt: dict[str, Any],
    source_result: dict[str, Any],
    target_chunk: list[list[float]],
    evaluated_active_scales: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35n result spec")
    verify_signed_payload(source_result, label="T20.35n result source")
    verify_evaluation_permit(permit, spec=spec)
    verify_attempt_marker(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
    )
    if source_result["identity_sha256"] != spec["t20_35l_result_identity_sha256"]:
        raise ValueError("T20.35n source result identity drifted")
    if hashlib.sha256(canonical_json_bytes(target_chunk)).hexdigest() != spec[
        "dataset_action_chunk_sha256"
    ]:
        raise ValueError("T20.35n target action chunk drifted")
    if (
        not isinstance(evaluated_active_scales, list)
        or [
            row.get("active_noise_scale")
            for row in evaluated_active_scales
            if isinstance(row, dict)
        ]
        != list(EVALUATED_ACTIVE_NOISE_SCALES)
    ):
        raise ValueError("T20.35n evaluated active-scale set or order drifted")
    active_zero = _scale_from_source(
        0.0, _source_condition(source_result, "active_zero_padded_normal"), target_chunk
    )
    active_one = _scale_from_source(
        1.0, _source_condition(source_result, "active_normal_padded_normal"), target_chunk
    )
    interior = [
        _scale_from_chunks(
            _active_scale(row["active_noise_scale"], allowed=EVALUATED_ACTIVE_NOISE_SCALES),
            row.get("decoded_action_chunks"),
            target_chunk,
        )
        for row in evaluated_active_scales
    ]
    expected_noise_hashes = spec["base_noise_sha256_by_seed"]
    for row in interior:
        if [
            item["base_noise_sha256"] for item in row["decoded_action_chunks"]
        ] != expected_noise_hashes:
            raise ValueError("T20.35n evaluated base noise changed")
    evaluations = [active_zero, interior[0], interior[1], active_one]
    passing = [row for row in evaluations if row["all_decoded_chunks_within_threshold"]]
    if passing:
        selected = max(passing, key=lambda row: row["active_noise_scale"])
        selected_scale = selected["active_noise_scale"]
        gate_b_passed = True
        route = "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction"
    else:
        selected = min(
            evaluations,
            key=lambda row: (
                row["worst_seed_maximum_error_rad"],
                row["aggregate_mean_absolute_error_rad"],
                -row["active_noise_scale"],
            ),
        )
        selected_scale = selected["active_noise_scale"]
        gate_b_passed = False
        if selected_scale in EVALUATED_ACTIVE_NOISE_SCALES:
            route = "refine_active_noise_scale_around_selected_interior"
        elif selected_scale == 0.0:
            route = "active_zero_endpoint_optimum_route_model_flow_consistency_correction"
        else:
            route = "active_one_endpoint_optimum_route_general_model_robustness"
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35n",
            "scope": "one_inference_only_near_zero_active_noise_scale_result_with_padded_normal",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "evaluation_attempt_identity_sha256": attempt["identity_sha256"],
            "t20_35l_result_identity_sha256": source_result["identity_sha256"],
            "t20_35m_audit_identity_sha256": spec["t20_35m_audit_identity_sha256"],
            "checkpoint_identity_sha256": spec["checkpoint_identity_sha256"],
            "dataset_action_chunk_sha256": spec["dataset_action_chunk_sha256"],
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "active_action_dimension_count": ACTIVE_ACTION_DIMENSIONS,
            "maximum_action_dimension_count": MAXIMUM_ACTION_DIMENSIONS,
            "padded_noise_scale": PADDED_NOISE_SCALE,
            "active_scale_evaluations": evaluations,
            "selected_active_noise_scale": selected_scale,
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
    verify_signed_payload(payload, label="T20.35n active-scale result")
    interior = [
        {
            "active_noise_scale": row.get("active_noise_scale"),
            "decoded_action_chunks": row.get("decoded_action_chunks"),
        }
        for row in payload.get("active_scale_evaluations", [])
        if isinstance(row, dict)
        and row.get("active_noise_scale") in EVALUATED_ACTIVE_NOISE_SCALES
    ]
    expected = build_result(
        spec=spec,
        permit=permit,
        attempt=attempt,
        source_result=source_result,
        target_chunk=target_chunk,
        evaluated_active_scales=interior,
    )
    archived_content = {key: value for key, value in payload.items() if key != "identity_sha256"}
    expected_content = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(
        archived_content, expected_content, absolute_tolerance=1e-15
    ):
        raise ValueError("T20.35n active-scale result drifted")


def load_and_verify_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35l_sources(repo_root=root)
    source_spec = sources["noise_mask_spec"]
    source_permit = sources["noise_mask_permit"]
    source_attempt = load_strict_json(root / T20_35L_ATTEMPT_PATH)
    verify_t20_35l_attempt(
        source_attempt,
        spec_identity=source_spec["identity_sha256"],
        permit_identity=source_permit["identity_sha256"],
    )
    source_result = load_strict_json(root / T20_35L_RESULT_PATH)
    target = sources["residual_report"]["target_action_chunk"]
    verify_t20_35l_result(
        source_result,
        spec=source_spec,
        permit=source_permit,
        attempt=source_attempt,
        source_result=sources["source_result"],
        target_chunk=target,
    )
    factorial_audit = verify_t20_35m_audit_file(repo_root=root)
    if (
        source_result["identity_sha256"] != EXPECTED_T20_35L_RESULT_IDENTITY
        or factorial_audit["identity_sha256"] != EXPECTED_T20_35M_AUDIT_IDENTITY
    ):
        raise ValueError("T20.35n expected source identity drifted")
    expected = build_evaluation_spec(
        factorial_audit=factorial_audit,
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
        "factorial_audit": factorial_audit,
        "active_scale_spec": spec,
        "active_scale_permit": permit,
    }


def write_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35l_sources(repo_root=root)
    source_spec = sources["noise_mask_spec"]
    source_permit = sources["noise_mask_permit"]
    source_attempt = load_strict_json(root / T20_35L_ATTEMPT_PATH)
    source_result = load_strict_json(root / T20_35L_RESULT_PATH)
    target = sources["residual_report"]["target_action_chunk"]
    verify_t20_35l_attempt(
        source_attempt,
        spec_identity=source_spec["identity_sha256"],
        permit_identity=source_permit["identity_sha256"],
    )
    verify_t20_35l_result(
        source_result,
        spec=source_spec,
        permit=source_permit,
        attempt=source_attempt,
        source_result=sources["source_result"],
        target_chunk=target,
    )
    factorial_audit = verify_t20_35m_audit_file(repo_root=root)
    spec = build_evaluation_spec(
        factorial_audit=factorial_audit,
        source_spec=source_spec,
        source_result=source_result,
    )
    permit = build_evaluation_permit(spec=spec)
    dump_canonical_json(root / SPEC_PATH, spec)
    dump_canonical_json(root / PERMIT_PATH, permit)
    return {"active_scale_spec": spec, "active_scale_permit": permit}


def _source_condition(source_result: dict[str, Any], condition: str) -> dict[str, Any]:
    matches = [
        row
        for row in source_result.get("condition_evaluations", [])
        if isinstance(row, dict) and row.get("noise_condition") == condition
    ]
    if len(matches) != 1:
        raise ValueError("T20.35n inherited source condition is ambiguous")
    return matches[0]


def _condition_hashes(condition: dict[str, Any]) -> tuple[list[str], list[str]]:
    rows = condition.get("decoded_action_chunks")
    if (
        not isinstance(rows, list)
        or len(rows) != len(INFERENCE_SEEDS)
        or [row.get("inference_seed") for row in rows if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35n inherited seed coverage drifted")
    action_hashes = []
    noise_hashes = []
    for row in rows:
        digest = hashlib.sha256(
            canonical_json_bytes(row.get("decoded_action_chunk"))
        ).hexdigest()
        if row.get("decoded_action_chunk_sha256") != digest:
            raise ValueError("T20.35n inherited action hash drifted")
        _sha(row.get("base_noise_sha256"), "base-noise hash")
        action_hashes.append(digest)
        noise_hashes.append(row["base_noise_sha256"])
    return action_hashes, noise_hashes


def _scale_from_source(
    scale: float, condition: dict[str, Any], target: list[list[float]]
) -> dict[str, Any]:
    return _scale_from_chunks(scale, condition.get("decoded_action_chunks"), target)


def _scale_from_chunks(
    scale: float, chunks: Any, target: list[list[float]]
) -> dict[str, Any]:
    evaluated = _evaluate_chunks(chunks, target=target)
    return {
        "active_noise_scale": scale,
        "padded_noise_scale": PADDED_NOISE_SCALE,
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


def _active_scale(value: Any, *, allowed: tuple[float, ...]) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("T20.35n active noise scale must be finite")
    number = float(value)
    if not math.isfinite(number) or number not in allowed:
        raise ValueError("T20.35n active noise scale drifted")
    return number


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35n {label} must be lowercase SHA-256")
