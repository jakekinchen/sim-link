"""Inference-only PI0.5 denoising cadence discriminator for T20.35g."""

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
    REPORT_PATH as T20_35D_REPORT_PATH,
    verify_evaluation_files as verify_t20_35d_evaluation_files,
    verify_report as verify_t20_35d_report,
)
from scenesmith.robot_lab.t20_35f_normalized_residual_saturation_audit import (
    AUDIT_PATH as T20_35F_AUDIT_PATH,
    verify_audit_file as verify_t20_35f_audit_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_35g_denoising_cadence_spec.json")
PERMIT_PATH = Path(
    "configurations/robot_lab/t20_35g_denoising_cadence_evaluation_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_35g_denoising_cadence_result.json"
)
ATTEMPT_PATH = Path("outputs/robot_lab/t20_35g_denoising_cadence/attempt.json")
SCHEMA_VERSION = "scenesmith.t20_35g_denoising_cadence_spec.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_35g_denoising_cadence_evaluation_permit.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_35g_denoising_cadence_result.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_35g_evaluation_attempt.v1"
EXPECTED_AUDIT_IDENTITY = (
    "85c24c5cd9a08c1a8153361bbdebaab0cedde28c5c1ec1a79bd1544924354432"
)
EXPECTED_REPORT_IDENTITY = (
    "13b08e70a805a8b176b9f9a7c0e37843f7267d7918f82aeb523551e2dadf1fbe"
)
EXPECTED_CHECKPOINT_IDENTITY = (
    "439ae119842fe5f9639b3e3e9b76f029678fd4b4257dfd6308253f6d2832c29f"
)
INHERITED_AUTHORITY_IDENTITY = (
    "75dc9c7d860e12e2a2114be709e24f7e544ff576696a3d223dd87dd0e2f06606"
)
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T15:27:47-05:00"
CADENCE_NUM_INFERENCE_STEPS = (10, 20, 50)
BASELINE_NUM_INFERENCE_STEPS = 10


def build_evaluation_spec(
    *,
    audit: dict[str, Any],
    residual_spec: dict[str, Any],
    residual_report: dict[str, Any],
    source_run: dict[str, Any],
    source_result: dict[str, Any],
) -> dict[str, Any]:
    for label, payload in (
        ("T20.35f audit", audit),
        ("T20.35d spec", residual_spec),
        ("T20.35d report", residual_report),
        ("T20.35c run", source_run),
        ("T20.35c result", source_result),
    ):
        verify_signed_payload(payload, label=f"T20.35g source {label}")
    if (
        audit.get("selected_next_hypothesis")
        != "gate_b_inference_denoising_cadence_discriminator"
        or audit.get("hard_saturation_detected") is not False
        or audit.get("all_selected_channels_systematic_bias_dominant") is not True
        or audit.get("source_contract", {}).get(
            "t20_35d_report_identity_sha256"
        )
        != residual_report.get("identity_sha256")
        or residual_spec.get("checkpoint_identity_sha256")
        != source_run.get("checkpoint_identity_sha256")
        or residual_spec.get("checkpoint_tree") != source_run.get("checkpoint_tree")
        or source_result.get("run_identity_sha256")
        != source_run.get("identity_sha256")
        or source_result.get("objective_ratio_within_threshold") is not True
        or source_result.get("all_decoded_chunks_within_threshold") is not False
    ):
        raise ValueError("T20.35g source route or lineage drifted")
    target = _matrix(residual_report.get("target_action_chunk"), "source target")
    target_hash = hashlib.sha256(canonical_json_bytes(target)).hexdigest()
    if target_hash != residual_spec.get("dataset_action_chunk_sha256"):
        raise ValueError("T20.35g source target identity drifted")
    baseline = _source_baseline(residual_report)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35g",
            "scope": "one_inference_only_pi05_denoising_cadence_discriminator",
            "t20_35f_audit_identity_sha256": audit["identity_sha256"],
            "t20_35d_spec_identity_sha256": residual_spec["identity_sha256"],
            "t20_35d_report_identity_sha256": residual_report["identity_sha256"],
            "source_run_identity_sha256": source_run["identity_sha256"],
            "source_result_identity_sha256": source_result["identity_sha256"],
            "checkpoint_identity_sha256": source_run[
                "checkpoint_identity_sha256"
            ],
            "checkpoint_tree": source_run["checkpoint_tree"],
            "trainable_parameter_names_sha256": source_run[
                "trainable_parameter_names_sha256"
            ],
            "trainable_parameter_count": source_run["trainable_parameter_count"],
            "paligemma_trainable_parameter_count": source_run[
                "paligemma_trainable_parameter_count"
            ],
            "dataset_action_chunk_sha256": target_hash,
            "inference_seeds": list(INFERENCE_SEEDS),
            "action_horizon": 50,
            "baseline_num_inference_steps": BASELINE_NUM_INFERENCE_STEPS,
            "cadence_num_inference_steps": list(CADENCE_NUM_INFERENCE_STEPS),
            "expected_baseline_decoded_action_chunks": baseline,
            "source_final_to_baseline_objective_ratio": source_result[
                "final_to_baseline_objective_ratio"
            ],
            "source_objective_ratio_within_threshold": True,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "selection_rule": (
                "smallest_all_seed_action_gate_pass_else_lowest_worst_seed_maximum_"
                "then_aggregate_mean_then_steps"
            ),
            "directional_improvement_rule": (
                "candidate_worst_seed_maximum_and_aggregate_mean_both_strictly_"
                "below_baseline"
            ),
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
    payload: dict[str, Any], *, source_spec: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.35g cadence spec")
    verify_signed_payload(source_spec, label="T20.35g expected cadence spec")
    if payload != source_spec:
        raise ValueError("T20.35g cadence spec drifted")


def build_evaluation_permit(*, spec: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35g permit source spec")
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": "T20.35g",
            "scope": "one_local_mps_inference_only_denoising_cadence_evaluation",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "inherited_authority_decision_identity_sha256": INHERITED_AUTHORITY_IDENTITY,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "cadence_num_inference_steps": list(CADENCE_NUM_INFERENCE_STEPS),
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
    verify_signed_payload(payload, label="T20.35g cadence permit")
    if payload != build_evaluation_permit(spec=spec):
        raise ValueError("T20.35g cadence permit drifted")


def build_result(
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    attempt: dict[str, Any],
    target_chunk: list[list[float]],
    cadence_evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35g result spec")
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
        raise ValueError("T20.35g result target drifted")
    if (
        not isinstance(cadence_evaluations, list)
        or [row.get("num_inference_steps") for row in cadence_evaluations if isinstance(row, dict)]
        != list(CADENCE_NUM_INFERENCE_STEPS)
    ):
        raise ValueError("T20.35g cadence set or order drifted")

    evaluated = []
    for row in cadence_evaluations:
        step_count = row["num_inference_steps"]
        chunks = _evaluate_chunks(row.get("decoded_action_chunks"), target=target)
        if step_count == BASELINE_NUM_INFERENCE_STEPS:
            expected_hashes = [
                item["decoded_action_chunk_sha256"]
                for item in spec["expected_baseline_decoded_action_chunks"]
            ]
            if [item["decoded_action_chunk_sha256"] for item in chunks] != expected_hashes:
                raise ValueError("T20.35g 10-step baseline failed exact reproduction")
        evaluated.append(
            {
                "num_inference_steps": step_count,
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
            }
        )

    baseline = evaluated[0]
    candidates = evaluated[1:]
    for row in candidates:
        row["improves_baseline_worst_seed_maximum"] = (
            row["worst_seed_maximum_error_rad"]
            < baseline["worst_seed_maximum_error_rad"]
        )
        row["improves_baseline_aggregate_mean"] = (
            row["aggregate_mean_absolute_error_rad"]
            < baseline["aggregate_mean_absolute_error_rad"]
        )
        row["directionally_improves_both_metrics"] = (
            row["improves_baseline_worst_seed_maximum"]
            and row["improves_baseline_aggregate_mean"]
        )

    passing = [row for row in candidates if row["all_decoded_chunks_within_threshold"]]
    best = min(
        candidates,
        key=lambda row: (
            row["worst_seed_maximum_error_rad"],
            row["aggregate_mean_absolute_error_rad"],
            row["num_inference_steps"],
        ),
    )
    if passing:
        selected_steps = min(row["num_inference_steps"] for row in passing)
        gate_b_passed = True
        cadence_positive = True
        route = "gate_b_pass_route_gate_c_closed_loop_reproduction"
    elif best["directionally_improves_both_metrics"]:
        selected_steps = best["num_inference_steps"]
        gate_b_passed = False
        cadence_positive = True
        route = "cadence_effect_positive_but_gate_b_still_closed"
    else:
        selected_steps = None
        gate_b_passed = False
        cadence_positive = False
        route = "denoising_cadence_rejected_route_output_bias_correction"

    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35g",
            "scope": "one_inference_only_pi05_denoising_cadence_result",
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
            "cadence_evaluations": evaluated,
            "baseline_reproduced_exactly": True,
            "cadence_effect_positive": cadence_positive,
            "selected_num_inference_steps": selected_steps,
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
    verify_signed_payload(payload, label="T20.35g cadence result")
    expected = build_result(
        spec=spec,
        permit=permit,
        attempt=attempt,
        target_chunk=target_chunk,
        cadence_evaluations=payload.get("cadence_evaluations"),
    )
    if payload != expected:
        raise ValueError("T20.35g cadence result drifted")


def verify_attempt_marker(
    payload: dict[str, Any], *, spec_identity: str, permit_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35g cadence attempt")
    if (
        payload.get("schema_version") != ATTEMPT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35g"
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
        raise ValueError("T20.35g cadence attempt drifted")


def load_and_verify_evaluation_files(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root)
    residual_sources = verify_t20_35d_evaluation_files(repo_root=root)
    residual_report = load_strict_json(root / T20_35D_REPORT_PATH)
    verify_t20_35d_report(
        residual_report,
        spec=residual_sources["evaluation_spec"],
        permit=residual_sources["evaluation_permit"],
    )
    audit = verify_t20_35f_audit_file(repo_root=root)
    expected = build_evaluation_spec(
        audit=audit,
        residual_spec=residual_sources["evaluation_spec"],
        residual_report=residual_report,
        source_run=residual_sources["source_run"],
        source_result=residual_sources["t20_35c_result"],
    )
    spec = load_strict_json(root / SPEC_PATH)
    verify_evaluation_spec(spec, source_spec=expected)
    permit = load_strict_json(root / PERMIT_PATH)
    verify_evaluation_permit(permit, spec=spec)
    return {
        **residual_sources,
        "residual_report": residual_report,
        "t20_35f_audit": audit,
        "cadence_spec": spec,
        "cadence_permit": permit,
    }


def write_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    residual_sources = verify_t20_35d_evaluation_files(repo_root=root)
    residual_report = load_strict_json(root / T20_35D_REPORT_PATH)
    verify_t20_35d_report(
        residual_report,
        spec=residual_sources["evaluation_spec"],
        permit=residual_sources["evaluation_permit"],
    )
    audit = verify_t20_35f_audit_file(repo_root=root)
    spec = build_evaluation_spec(
        audit=audit,
        residual_spec=residual_sources["evaluation_spec"],
        residual_report=residual_report,
        source_run=residual_sources["source_run"],
        source_result=residual_sources["t20_35c_result"],
    )
    permit = build_evaluation_permit(spec=spec)
    dump_canonical_json(root / SPEC_PATH, spec)
    dump_canonical_json(root / PERMIT_PATH, permit)
    return {"spec": spec, "permit": permit}


def _source_baseline(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("replayed_chunks")
    if (
        not isinstance(rows, list)
        or len(rows) != 5
        or [row.get("inference_seed") for row in rows if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35g baseline seed coverage drifted")
    baseline = []
    for row in rows:
        matrix = _matrix(row.get("decoded_action_chunk"), "baseline decoded chunk")
        digest = hashlib.sha256(canonical_json_bytes(matrix)).hexdigest()
        if digest != row.get("decoded_action_chunk_sha256"):
            raise ValueError("T20.35g baseline decoded hash drifted")
        baseline.append(
            {
                "inference_seed": row["inference_seed"],
                "decoded_action_chunk_sha256": digest,
            }
        )
    return baseline


def _evaluate_chunks(
    value: Any, *, target: list[list[float]]
) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or len(value) != 5
        or [row.get("inference_seed") for row in value if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35g result seed coverage drifted")
    result = []
    for row in value:
        matrix = _matrix(row.get("decoded_action_chunk"), "result decoded chunk")
        errors = [
            abs(matrix[timestep][joint] - target[timestep][joint])
            for timestep in range(50)
            for joint in range(6)
        ]
        result.append(
            {
                "inference_seed": row["inference_seed"],
                "decoded_action_chunk_sha256": hashlib.sha256(
                    canonical_json_bytes(matrix)
                ).hexdigest(),
                "decoded_action_chunk": matrix,
                "mean_absolute_error_rad": sum(errors) / len(errors),
                "maximum_absolute_error_rad": max(errors),
            }
        )
    return result


def _matrix(value: Any, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 50:
        raise ValueError(f"T20.35g {label} must have 50 rows")
    result = []
    for row in value:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError(f"T20.35g {label} must have six columns")
        converted = []
        for item in row:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError(f"T20.35g {label} must be finite")
            number = float(item)
            if not math.isfinite(number):
                raise ValueError(f"T20.35g {label} must be finite")
            converted.append(number)
        result.append(converted)
    return result
