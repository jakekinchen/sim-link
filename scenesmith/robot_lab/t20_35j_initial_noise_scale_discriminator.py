"""Inference-only initial-noise-scale discriminator for T20.35j."""

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
from scenesmith.robot_lab.t20_35g_denoising_cadence_discriminator import (
    ATTEMPT_002_PATH as T20_35G_ATTEMPT_PATH,
    RESULT_PATH as T20_35G_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35g_sources,
    verify_attempt_marker as verify_t20_35g_attempt,
    verify_result as verify_t20_35g_result,
)
from scenesmith.robot_lab.t20_35i_residual_variance_localization import (
    verify_variance_localization_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(
    "configurations/robot_lab/t20_35j_initial_noise_scale_spec.json"
)
PERMIT_PATH = Path(
    "configurations/robot_lab/t20_35j_initial_noise_scale_evaluation_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_35j_initial_noise_scale_result.json"
)
ATTEMPT_PATH = Path(
    "outputs/robot_lab/t20_35j_initial_noise_scale/attempt.json"
)
SAMPLER_SOURCE_PATH = Path(
    "external/leLab/.venv/lib/python3.12/site-packages/lerobot/policies/pi05/modeling_pi05.py"
)
SCHEMA_VERSION = "scenesmith.t20_35j_initial_noise_scale_spec.v1"
PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_35j_initial_noise_scale_evaluation_permit.v1"
)
RESULT_SCHEMA_VERSION = "scenesmith.t20_35j_initial_noise_scale_result.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_35j_evaluation_attempt.v1"
INITIAL_NOISE_SCALES = (1.0, 0.5, 0.0)
NUM_INFERENCE_STEPS = 10
EXPECTED_VARIANCE_IDENTITY = (
    "ac87de7b21c7698fe5b02d1e57b06cab009bc6a92257bbcc52c27111cc04a6f0"
)
EXPECTED_CADENCE_RESULT_IDENTITY = (
    "57f1f0dd5190fa1e0dc2b84cf25546b8f4e520bb75d2a15616797c5f311b2ea2"
)
INHERITED_AUTHORITY_IDENTITY = (
    "75dc9c7d860e12e2a2114be709e24f7e544ff576696a3d223dd87dd0e2f06606"
)
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T23:27:47-05:00"


def build_evaluation_spec(
    *,
    variance_report: dict[str, Any],
    cadence_spec: dict[str, Any],
    cadence_result: dict[str, Any],
    sampler_source_sha256: str,
    lerobot_stack_identity_sha256: str | None = None,
) -> dict[str, Any]:
    for label, payload in (
        ("variance report", variance_report),
        ("cadence spec", cadence_spec),
        ("cadence result", cadence_result),
    ):
        verify_signed_payload(payload, label=f"T20.35j source {label}")
    _sha(sampler_source_sha256, "sampler source hash")
    stack_identity = (
        lerobot_stack_identity_sha256
        if lerobot_stack_identity_sha256 is not None
        else cadence_spec.get("lerobot_stack_identity_sha256")
    )
    _sha(stack_identity, "LeRobot stack identity")
    if (
        variance_report.get("variance_classification")
        != "distributed_seed_channel_variance"
        or variance_report.get("selected_next_hypothesis")
        != "run_separately_reviewed_inference_only_initial_noise_scale_discriminator"
        or variance_report.get("gate_b_passed") is not False
        or cadence_result.get("baseline_reproduced_exactly") is not True
        or cadence_result.get("gate_b_passed") is not False
        or cadence_spec.get("inference_seeds") != list(INFERENCE_SEEDS)
        or cadence_spec.get("source_objective_ratio_within_threshold") is not True
    ):
        raise ValueError("T20.35j source route or lineage drifted")
    baseline_rows = [
        row
        for row in cadence_result.get("cadence_evaluations", [])
        if isinstance(row, dict) and row.get("num_inference_steps") == NUM_INFERENCE_STEPS
    ]
    if len(baseline_rows) != 1:
        raise ValueError("T20.35j source baseline is ambiguous")
    baseline_chunks = _source_baseline_hashes(
        baseline_rows[0].get("decoded_action_chunks")
    )
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35j",
            "scope": "one_inference_only_pi05_initial_noise_scale_discriminator",
            "t20_35i_variance_identity_sha256": variance_report["identity_sha256"],
            "t20_35g_spec_identity_sha256": cadence_spec["identity_sha256"],
            "t20_35g_result_identity_sha256": cadence_result["identity_sha256"],
            "checkpoint_identity_sha256": cadence_spec["checkpoint_identity_sha256"],
            "checkpoint_tree": cadence_spec["checkpoint_tree"],
            "trainable_parameter_names_sha256": cadence_spec[
                "trainable_parameter_names_sha256"
            ],
            "trainable_parameter_count": cadence_spec["trainable_parameter_count"],
            "paligemma_trainable_parameter_count": cadence_spec[
                "paligemma_trainable_parameter_count"
            ],
            "dataset_action_chunk_sha256": cadence_spec[
                "dataset_action_chunk_sha256"
            ],
            "lerobot_stack_identity_sha256": stack_identity,
            "sampler_source_path": str(SAMPLER_SOURCE_PATH),
            "sampler_source_sha256": sampler_source_sha256,
            "sampler_noise_distribution": "standard_normal_scaled_after_sampling",
            "same_base_noise_required_across_scales_per_seed": True,
            "inference_seeds": list(INFERENCE_SEEDS),
            "num_inference_steps": NUM_INFERENCE_STEPS,
            "initial_noise_scales": list(INITIAL_NOISE_SCALES),
            "expected_baseline_decoded_action_chunks": baseline_chunks,
            "source_final_to_baseline_objective_ratio": cadence_spec[
                "source_final_to_baseline_objective_ratio"
            ],
            "source_objective_ratio_within_threshold": True,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "passing_selection_rule": "largest_passing_candidate_scale",
            "directional_improvement_rule": (
                "candidate_worst_seed_maximum_aggregate_mean_and_aggregate_raw_"
                "spread_all_strictly_below_scale_1"
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
    verify_signed_payload(payload, label="T20.35j noise-scale spec")
    verify_signed_payload(expected_spec, label="T20.35j expected noise-scale spec")
    if payload != expected_spec:
        raise ValueError("T20.35j noise-scale spec drifted")


def build_evaluation_permit(*, spec: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35j permit source spec")
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": "T20.35j",
            "scope": "one_local_mps_inference_only_initial_noise_scale_evaluation",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "inherited_authority_decision_identity_sha256": INHERITED_AUTHORITY_IDENTITY,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "initial_noise_scales": list(INITIAL_NOISE_SCALES),
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
    verify_signed_payload(payload, label="T20.35j noise-scale permit")
    if payload != build_evaluation_permit(spec=spec):
        raise ValueError("T20.35j noise-scale permit drifted")


def verify_attempt_marker(
    payload: dict[str, Any], *, spec_identity: str, permit_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35j noise-scale attempt")
    if (
        payload.get("schema_version") != ATTEMPT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35j"
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
        raise ValueError("T20.35j noise-scale attempt drifted")


def build_result(
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    attempt: dict[str, Any],
    target_chunk: list[list[float]],
    scale_evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35j result spec")
    verify_evaluation_permit(permit, spec=spec)
    verify_attempt_marker(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
    )
    target = _matrix(target_chunk, "result target")
    if hashlib.sha256(canonical_json_bytes(target)).hexdigest() != spec[
        "dataset_action_chunk_sha256"
    ]:
        raise ValueError("T20.35j result target drifted")
    if (
        not isinstance(scale_evaluations, list)
        or [
            row.get("initial_noise_scale")
            for row in scale_evaluations
            if isinstance(row, dict)
        ]
        != list(INITIAL_NOISE_SCALES)
    ):
        raise ValueError("T20.35j scale set or order drifted")
    evaluated = []
    for row in scale_evaluations:
        scale = _finite_scale(row["initial_noise_scale"])
        chunks = _evaluate_chunks(row.get("decoded_action_chunks"), target=target)
        if scale == 1.0:
            expected_hashes = [
                item["decoded_action_chunk_sha256"]
                for item in spec["expected_baseline_decoded_action_chunks"]
            ]
            if [item["decoded_action_chunk_sha256"] for item in chunks] != expected_hashes:
                raise ValueError("T20.35j scale-1 baseline failed exact reproduction")
        spread = _aggregate_raw_spread(chunks)
        evaluated.append(
            {
                "initial_noise_scale": scale,
                "decoded_action_chunks": chunks,
                "all_decoded_chunks_within_threshold": all(
                    item["maximum_absolute_error_rad"] <= MAX_ACTION_ERROR_RAD
                    for item in chunks
                ),
                "worst_seed_maximum_error_rad": max(
                    item["maximum_absolute_error_rad"] for item in chunks
                ),
                "aggregate_mean_absolute_error_rad": sum(
                    item["mean_absolute_error_rad"] for item in chunks
                )
                / len(chunks),
                "aggregate_mean_raw_decoded_spread_rad": spread,
            }
        )
    baseline = evaluated[0]
    candidates = evaluated[1:]
    baseline_noise_hashes = [
        row["base_noise_sha256"] for row in baseline["decoded_action_chunks"]
    ]
    for row in candidates:
        if [
            chunk["base_noise_sha256"] for chunk in row["decoded_action_chunks"]
        ] != baseline_noise_hashes:
            raise ValueError("T20.35j base noise changed across scales")
    for row in candidates:
        row["improves_baseline_worst_seed_maximum"] = (
            row["worst_seed_maximum_error_rad"]
            < baseline["worst_seed_maximum_error_rad"]
        )
        row["improves_baseline_aggregate_mean"] = (
            row["aggregate_mean_absolute_error_rad"]
            < baseline["aggregate_mean_absolute_error_rad"]
        )
        row["improves_baseline_aggregate_raw_spread"] = (
            row["aggregate_mean_raw_decoded_spread_rad"]
            < baseline["aggregate_mean_raw_decoded_spread_rad"]
        )
        row["directionally_improves_all_metrics"] = (
            row["improves_baseline_worst_seed_maximum"]
            and row["improves_baseline_aggregate_mean"]
            and row["improves_baseline_aggregate_raw_spread"]
        )
    passing = [row for row in candidates if row["all_decoded_chunks_within_threshold"]]
    positive = [row for row in candidates if row["directionally_improves_all_metrics"]]
    if passing:
        selected = max(passing, key=lambda row: row["initial_noise_scale"])
        selected_scale = selected["initial_noise_scale"]
        gate_b_passed = True
        scale_effect_positive = True
        route = "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction"
    elif positive:
        selected = min(
            positive,
            key=lambda row: (
                row["worst_seed_maximum_error_rad"],
                row["aggregate_mean_absolute_error_rad"],
                -row["initial_noise_scale"],
            ),
        )
        selected_scale = selected["initial_noise_scale"]
        gate_b_passed = False
        scale_effect_positive = True
        route = "initial_noise_scale_positive_but_gate_b_closed_route_sampler_distribution_audit"
    else:
        selected_scale = None
        gate_b_passed = False
        scale_effect_positive = False
        route = "initial_noise_scale_rejected_route_model_robustness_correction"
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35j",
            "scope": "one_inference_only_pi05_initial_noise_scale_result",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "evaluation_attempt_identity_sha256": attempt["identity_sha256"],
            "checkpoint_identity_sha256": spec["checkpoint_identity_sha256"],
            "dataset_action_chunk_sha256": spec["dataset_action_chunk_sha256"],
            "source_final_to_baseline_objective_ratio": spec[
                "source_final_to_baseline_objective_ratio"
            ],
            "source_objective_ratio_within_threshold": True,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "scale_evaluations": evaluated,
            "baseline_reproduced_exactly": True,
            "initial_noise_scale_effect_positive": scale_effect_positive,
            "selected_initial_noise_scale": selected_scale,
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
    target_chunk: list[list[float]],
) -> None:
    verify_signed_payload(payload, label="T20.35j noise-scale result")
    expected = build_result(
        spec=spec,
        permit=permit,
        attempt=attempt,
        target_chunk=target_chunk,
        scale_evaluations=payload.get("scale_evaluations"),
    )
    archived_content = {key: value for key, value in payload.items() if key != "identity_sha256"}
    expected_content = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(archived_content, expected_content, absolute_tolerance=1e-15):
        raise ValueError("T20.35j noise-scale result drifted")


def load_and_verify_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    variance_report = verify_variance_localization_file(repo_root=root)
    cadence_sources = load_t20_35g_sources(repo_root=root)
    cadence_spec = cadence_sources["cadence_spec"]
    cadence_permit = cadence_sources["cadence_permit"]
    target = cadence_sources["residual_report"]["target_action_chunk"]
    cadence_attempt = load_strict_json(root / T20_35G_ATTEMPT_PATH)
    verify_t20_35g_attempt(
        cadence_attempt,
        spec_identity=cadence_spec["identity_sha256"],
        permit_identity=cadence_permit["identity_sha256"],
    )
    cadence_result = load_strict_json(root / T20_35G_RESULT_PATH)
    verify_t20_35g_result(
        cadence_result,
        spec=cadence_spec,
        permit=cadence_permit,
        attempt=cadence_attempt,
        target_chunk=target,
    )
    if (
        variance_report["identity_sha256"] != EXPECTED_VARIANCE_IDENTITY
        or cadence_result["identity_sha256"] != EXPECTED_CADENCE_RESULT_IDENTITY
    ):
        raise ValueError("T20.35j expected source identity drifted")
    sampler_path = root / SAMPLER_SOURCE_PATH
    sampler_sha = hashlib.sha256(sampler_path.read_bytes()).hexdigest()
    expected = build_evaluation_spec(
        variance_report=variance_report,
        cadence_spec=cadence_spec,
        cadence_result=cadence_result,
        sampler_source_sha256=sampler_sha,
        lerobot_stack_identity_sha256=cadence_sources["t20_35c_spec"][
            "lerobot_stack_identity_sha256"
        ],
    )
    spec = load_strict_json(root / SPEC_PATH)
    verify_evaluation_spec(spec, expected_spec=expected)
    permit = load_strict_json(root / PERMIT_PATH)
    verify_evaluation_permit(permit, spec=spec)
    return {
        **cadence_sources,
        "variance_report": variance_report,
        "cadence_result": cadence_result,
        "noise_scale_spec": spec,
        "noise_scale_permit": permit,
    }


def write_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    variance_report = verify_variance_localization_file(repo_root=root)
    cadence_sources = load_t20_35g_sources(repo_root=root)
    cadence_spec = cadence_sources["cadence_spec"]
    cadence_permit = cadence_sources["cadence_permit"]
    target = cadence_sources["residual_report"]["target_action_chunk"]
    cadence_attempt = load_strict_json(root / T20_35G_ATTEMPT_PATH)
    cadence_result = load_strict_json(root / T20_35G_RESULT_PATH)
    verify_t20_35g_result(
        cadence_result,
        spec=cadence_spec,
        permit=cadence_permit,
        attempt=cadence_attempt,
        target_chunk=target,
    )
    sampler_sha = hashlib.sha256((root / SAMPLER_SOURCE_PATH).read_bytes()).hexdigest()
    spec = build_evaluation_spec(
        variance_report=variance_report,
        cadence_spec=cadence_spec,
        cadence_result=cadence_result,
        sampler_source_sha256=sampler_sha,
        lerobot_stack_identity_sha256=cadence_sources["t20_35c_spec"][
            "lerobot_stack_identity_sha256"
        ],
    )
    permit = build_evaluation_permit(spec=spec)
    dump_canonical_json(root / SPEC_PATH, spec)
    dump_canonical_json(root / PERMIT_PATH, permit)
    return {"spec": spec, "permit": permit}


def _source_baseline_hashes(value: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or len(value) != 5
        or [row.get("inference_seed") for row in value if isinstance(row, dict)] != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35j source baseline seed coverage drifted")
    result = []
    for row in value:
        matrix = _matrix(row.get("decoded_action_chunk"), "source baseline chunk")
        digest = hashlib.sha256(canonical_json_bytes(matrix)).hexdigest()
        if row.get("decoded_action_chunk_sha256") not in (None, digest):
            raise ValueError("T20.35j source baseline hash drifted")
        result.append(
            {
                "inference_seed": row["inference_seed"],
                "decoded_action_chunk_sha256": digest,
            }
        )
    return result


def _evaluate_chunks(value: Any, *, target: list[list[float]]) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or len(value) != 5
        or [row.get("inference_seed") for row in value if isinstance(row, dict)] != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35j result seed coverage drifted")
    result = []
    for row in value:
        _sha(row.get("base_noise_sha256"), "base noise hash")
        matrix = _matrix(row.get("decoded_action_chunk"), "result decoded chunk")
        errors = [
            abs(matrix[timestep][joint] - target[timestep][joint])
            for timestep in range(50)
            for joint in range(6)
        ]
        result.append(
            {
                "inference_seed": row["inference_seed"],
                "base_noise_sha256": row["base_noise_sha256"],
                "decoded_action_chunk_sha256": hashlib.sha256(
                    canonical_json_bytes(matrix)
                ).hexdigest(),
                "decoded_action_chunk": matrix,
                "mean_absolute_error_rad": sum(errors) / len(errors),
                "maximum_absolute_error_rad": max(errors),
            }
        )
    return result


def _aggregate_raw_spread(chunks: list[dict[str, Any]]) -> float:
    matrices = [row["decoded_action_chunk"] for row in chunks]
    spreads = [
        max(matrix[timestep][joint] for matrix in matrices)
        - min(matrix[timestep][joint] for matrix in matrices)
        for timestep in range(50)
        for joint in range(6)
    ]
    return sum(spreads) / len(spreads)


def _matrix(value: Any, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 50:
        raise ValueError(f"T20.35j {label} must have 50 rows")
    result = []
    for row in value:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError(f"T20.35j {label} must have six columns")
        converted = []
        for item in row:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError(f"T20.35j {label} must be finite")
            number = float(item)
            if not math.isfinite(number):
                raise ValueError(f"T20.35j {label} must be finite")
            converted.append(number)
        result.append(converted)
    return result


def _finite_scale(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("T20.35j initial noise scale must be finite")
    number = float(value)
    if not math.isfinite(number) or number not in INITIAL_NOISE_SCALES:
        raise ValueError("T20.35j initial noise scale drifted")
    return number


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35j {label} must be lowercase SHA-256")
