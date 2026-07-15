"""Deterministic decoded-action residual localization for T20.35d."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    INFERENCE_SEEDS,
    MAX_ACTION_ERROR_RAD,
    SPEC_PATH as T20_33_SPEC_PATH,
)
from scenesmith.robot_lab.t20_35b_pi05_coverage_correction import CORRECTION_PATH
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (
    EXPECTED_DATASET_ACTION_CHUNK_SHA256,
    RESULT_PATH as T20_35C_RESULT_PATH,
    SPEC_PATH as T20_35C_SPEC_PATH,
    verify_run as verify_t20_35c_run,
    verify_training_spec as verify_t20_35c_spec,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_35d_residual_localization_spec.json")
PERMIT_PATH = Path("configurations/robot_lab/t20_35d_evaluation_permit.json")
REPORT_PATH = Path("configurations/robot_lab/t20_35d_residual_localization_report.json")
SOURCE_RUN_PATH = Path("outputs/robot_lab/t20_35c_expert_only_run_001/run_summary.json")
CHECKPOINT_ROOT = Path("outputs/robot_lab/t20_35c_expert_only_run_001/checkpoint")
ATTEMPT_PATH = Path("outputs/robot_lab/t20_35d_residual_localization/attempt.json")
SCHEMA_VERSION = "scenesmith.t20_35d_residual_localization_spec.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_35d_evaluation_permit.v1"
REPORT_SCHEMA_VERSION = "scenesmith.t20_35d_residual_localization_report.v1"
EXPECTED_RESULT_IDENTITY = (
    "f6f6b024c169ffec9c59be9e8a111e756aae2b70729ae30ad016b29ee402df47"
)
EXPECTED_RUN_IDENTITY = (
    "9b1af8ee0020fef65b3990b587268642c4eb1e137f8b252729e79d0d5a5ad650"
)
EXPECTED_CHECKPOINT_IDENTITY = (
    "439ae119842fe5f9639b3e3e9b76f029678fd4b4257dfd6308253f6d2832c29f"
)
INHERITED_AUTHORITY_IDENTITY = (
    "75dc9c7d860e12e2a2114be709e24f7e544ff576696a3d223dd87dd0e2f06606"
)
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T15:27:47-05:00"
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)
BOUNDARY_WIDTH = 5
JOINT_CONCENTRATION_FRACTION = 0.50
BOUNDARY_CONCENTRATION_FRACTION = 0.60


def build_evaluation_spec(
    *,
    t20_35c_spec: dict[str, Any],
    t20_35c_result: dict[str, Any],
    source_run: dict[str, Any],
    t20_33_spec: dict[str, Any],
    correction: dict[str, Any],
) -> dict[str, Any]:
    verify_t20_35c_spec(
        t20_35c_spec, t20_33_spec=t20_33_spec, correction=correction
    )
    verify_t20_35c_run(
        source_run,
        spec=t20_35c_spec,
        authority_identity=INHERITED_AUTHORITY_IDENTITY,
        t20_33_spec=t20_33_spec,
        correction=correction,
    )
    verify_signed_payload(t20_35c_result, label="T20.35d source result")
    if (
        t20_35c_result.get("identity_sha256") != EXPECTED_RESULT_IDENTITY
        or t20_35c_result.get("run_identity_sha256") != EXPECTED_RUN_IDENTITY
        or source_run.get("identity_sha256") != EXPECTED_RUN_IDENTITY
        or source_run.get("checkpoint_identity_sha256")
        != EXPECTED_CHECKPOINT_IDENTITY
        or t20_35c_result.get("objective_ratio_within_threshold") is not True
        or t20_35c_result.get("all_decoded_chunks_within_threshold") is not False
        or t20_35c_result.get("selected_next_hypothesis")
        != "gate_b_objective_pass_action_fail_route_decoded_action_residual_localization"
    ):
        raise ValueError("T20.35d source result, run, or route drifted")
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35d",
            "scope": "optimizer_free_exact_checkpoint_replay_and_residual_localization",
            "t20_35c_training_spec_identity_sha256": t20_35c_spec["identity_sha256"],
            "t20_35c_result_identity_sha256": t20_35c_result["identity_sha256"],
            "source_run_identity_sha256": source_run["identity_sha256"],
            "source_attempt_identity_sha256": source_run["attempt_identity_sha256"],
            "checkpoint_identity_sha256": source_run["checkpoint_identity_sha256"],
            "checkpoint_tree": source_run["checkpoint_tree"],
            "trainable_parameter_names_sha256": source_run[
                "trainable_parameter_names_sha256"
            ],
            "trainable_parameter_count": source_run["trainable_parameter_count"],
            "paligemma_trainable_parameter_count": source_run[
                "paligemma_trainable_parameter_count"
            ],
            "dataset_action_chunk_sha256": EXPECTED_DATASET_ACTION_CHUNK_SHA256,
            "inference_seeds": list(INFERENCE_SEEDS),
            "action_horizon": 50,
            "joint_names": list(JOINT_NAMES),
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "boundary_width_timesteps": BOUNDARY_WIDTH,
            "joint_concentration_fraction": JOINT_CONCENTRATION_FRACTION,
            "boundary_concentration_fraction": BOUNDARY_CONCENTRATION_FRACTION,
            "expected_decoded_action_chunks": t20_35c_result[
                "decoded_action_chunks"
            ],
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "model_loaded": False,
            "model_inference": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
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
    payload: dict[str, Any],
    *,
    t20_35c_spec: dict[str, Any],
    t20_35c_result: dict[str, Any],
    source_run: dict[str, Any],
    t20_33_spec: dict[str, Any],
    correction: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.35d evaluation spec")
    expected = build_evaluation_spec(
        t20_35c_spec=t20_35c_spec,
        t20_35c_result=t20_35c_result,
        source_run=source_run,
        t20_33_spec=t20_33_spec,
        correction=correction,
    )
    if payload != expected:
        raise ValueError("T20.35d evaluation spec drifted")


def build_evaluation_permit(*, spec: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35d permit source spec")
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": "T20.35d",
            "scope": "one_optimizer_free_exact_t20_35c_checkpoint_replay",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "inherited_authority_decision_identity_sha256": INHERITED_AUTHORITY_IDENTITY,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "optimizer_training_authorized": False,
            "checkpoint_mutation_authorized": False,
            "closed_loop_rollout_authorized": False,
            "exactly_one_replay_attempt_authorized": True,
            "valid_from": VALID_FROM,
            "valid_until": VALID_UNTIL,
            "physical_actuation_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
        }
    )


def verify_evaluation_permit(payload: dict[str, Any], *, spec: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.35d evaluation permit")
    if payload != build_evaluation_permit(spec=spec):
        raise ValueError("T20.35d evaluation permit drifted")


def load_and_verify_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    t20_33_spec = load_strict_json(root / T20_33_SPEC_PATH)
    correction = load_strict_json(root / CORRECTION_PATH)
    t20_35c_spec = load_strict_json(root / T20_35C_SPEC_PATH)
    result = load_strict_json(root / T20_35C_RESULT_PATH)
    run = load_strict_json(root / SOURCE_RUN_PATH)
    expected = build_evaluation_spec(
        t20_35c_spec=t20_35c_spec,
        t20_35c_result=result,
        source_run=run,
        t20_33_spec=t20_33_spec,
        correction=correction,
    )
    return {
        "t20_33_spec": t20_33_spec,
        "correction": correction,
        "t20_35c_spec": t20_35c_spec,
        "t20_35c_result": result,
        "source_run": run,
        "evaluation_spec": expected,
    }


def verify_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_and_verify_sources(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_evaluation_spec(
        spec,
        t20_35c_spec=sources["t20_35c_spec"],
        t20_35c_result=sources["t20_35c_result"],
        source_run=sources["source_run"],
        t20_33_spec=sources["t20_33_spec"],
        correction=sources["correction"],
    )
    if spec != sources["evaluation_spec"]:
        raise ValueError("T20.35d archived spec drifted from sources")
    permit = load_strict_json(root / PERMIT_PATH)
    verify_evaluation_permit(permit, spec=spec)
    return {**sources, "evaluation_spec": spec, "evaluation_permit": permit}


def build_report(
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    replay_attempt_identity: str,
    target_chunk: list[list[float]],
    replay_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35d report spec")
    verify_evaluation_permit(permit, spec=spec)
    _sha(replay_attempt_identity, "replay attempt identity")
    target = _matrix(target_chunk, "target chunk")
    if hashlib.sha256(canonical_json_bytes(target)).hexdigest() != spec[
        "dataset_action_chunk_sha256"
    ]:
        raise ValueError("T20.35d target chunk identity drifted")
    if (
        not isinstance(replay_chunks, list)
        or [row.get("inference_seed") for row in replay_chunks if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35d replay seed order drifted")
    expected = spec["expected_decoded_action_chunks"]
    localized = []
    exceedances = []
    all_errors: list[list[list[float]]] = []
    for row, prior in zip(replay_chunks, expected, strict=True):
        decoded = _matrix(row.get("decoded_action_chunk"), "decoded chunk")
        digest = hashlib.sha256(canonical_json_bytes(decoded)).hexdigest()
        if digest != prior["decoded_action_chunk_sha256"]:
            raise ValueError("T20.35d decoded chunk hash failed exact replay")
        residual = [
            [abs(decoded[t][j] - target[t][j]) for j in range(6)]
            for t in range(50)
        ]
        flat = [value for timestep in residual for value in timestep]
        mean_error = sum(flat) / len(flat)
        max_error = max(flat)
        if (
            not math.isclose(
                mean_error,
                prior["mean_absolute_error_rad"],
                rel_tol=0.0,
                abs_tol=1e-15,
            )
            or not math.isclose(
                max_error,
                prior["maximum_absolute_error_rad"],
                rel_tol=0.0,
                abs_tol=1e-15,
            )
        ):
            raise ValueError("T20.35d decoded chunk metrics failed exact replay")
        seed = row["inference_seed"]
        for timestep, values in enumerate(residual):
            for joint_index, error in enumerate(values):
                if error > MAX_ACTION_ERROR_RAD:
                    exceedances.append(
                        {
                            "inference_seed": seed,
                            "timestep": timestep,
                            "joint_index": joint_index,
                            "joint_name": JOINT_NAMES[joint_index],
                            "target_rad": target[timestep][joint_index],
                            "decoded_rad": decoded[timestep][joint_index],
                            "absolute_error_rad": error,
                        }
                    )
        localized.append(
            {
                "inference_seed": seed,
                "decoded_action_chunk_sha256": digest,
                "decoded_action_chunk": decoded,
                "absolute_residual_rad": residual,
                "mean_absolute_error_rad": mean_error,
                "maximum_absolute_error_rad": max_error,
            }
        )
        all_errors.append(residual)
    summaries = _summaries(all_errors=all_errors, exceedances=exceedances)
    classification = _classification(summaries)
    return sign_payload(
        {
            "schema_version": REPORT_SCHEMA_VERSION,
            "task_id": "T20.35d",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "replay_attempt_identity_sha256": replay_attempt_identity,
            "source_result_identity_sha256": spec[
                "t20_35c_result_identity_sha256"
            ],
            "source_run_identity_sha256": spec["source_run_identity_sha256"],
            "checkpoint_identity_sha256": spec["checkpoint_identity_sha256"],
            "target_action_chunk": target,
            "target_action_chunk_sha256": spec["dataset_action_chunk_sha256"],
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "replayed_chunks": localized,
            "all_five_decoded_hashes_reproduced": True,
            "threshold_exceedances": exceedances,
            **summaries,
            "residual_classification": classification,
            "selected_next_hypothesis": _next_hypothesis(classification),
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_report(payload: dict[str, Any], *, spec: dict[str, Any], permit: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.35d residual report")
    replay = [
        {
            "inference_seed": row.get("inference_seed"),
            "decoded_action_chunk": row.get("decoded_action_chunk"),
        }
        for row in payload.get("replayed_chunks", [])
        if isinstance(row, dict)
    ]
    expected = build_report(
        spec=spec,
        permit=permit,
        replay_attempt_identity=payload.get("replay_attempt_identity_sha256"),
        target_chunk=payload.get("target_action_chunk"),
        replay_chunks=replay,
    )
    if payload != expected:
        raise ValueError("T20.35d residual report drifted from replay evidence")


def _summaries(
    *, all_errors: list[list[list[float]]], exceedances: list[dict[str, Any]]
) -> dict[str, Any]:
    joint_summaries = []
    for joint_index, joint_name in enumerate(JOINT_NAMES):
        values = [
            all_errors[seed_index][timestep][joint_index]
            for seed_index in range(5)
            for timestep in range(50)
        ]
        joint_exceedances = [
            row for row in exceedances if row["joint_index"] == joint_index
        ]
        joint_summaries.append(
            {
                "joint_index": joint_index,
                "joint_name": joint_name,
                "mean_absolute_error_rad": sum(values) / len(values),
                "maximum_absolute_error_rad": max(values),
                "threshold_exceedance_count": len(joint_exceedances),
            }
        )
    timestep_summaries = []
    for timestep in range(50):
        values = [
            all_errors[seed_index][timestep][joint_index]
            for seed_index in range(5)
            for joint_index in range(6)
        ]
        timestep_summaries.append(
            {
                "timestep": timestep,
                "mean_absolute_error_rad": sum(values) / len(values),
                "maximum_absolute_error_rad": max(values),
                "threshold_exceedance_count": sum(
                    row["timestep"] == timestep for row in exceedances
                ),
            }
        )
    total = len(exceedances)
    max_joint_count = max(
        row["threshold_exceedance_count"] for row in joint_summaries
    )
    boundary_count = sum(
        row["timestep"] < BOUNDARY_WIDTH
        or row["timestep"] >= 50 - BOUNDARY_WIDTH
        for row in exceedances
    )
    return {
        "threshold_exceedance_count": total,
        "per_joint_summary": joint_summaries,
        "per_timestep_summary": timestep_summaries,
        "largest_joint_exceedance_count": max_joint_count,
        "largest_joint_exceedance_fraction": max_joint_count / total if total else 0.0,
        "boundary_exceedance_count": boundary_count,
        "boundary_exceedance_fraction": boundary_count / total if total else 0.0,
    }


def _classification(summaries: dict[str, Any]) -> str:
    if summaries["threshold_exceedance_count"] == 0:
        return "no_threshold_exceedance"
    joint = (
        summaries["largest_joint_exceedance_fraction"]
        >= JOINT_CONCENTRATION_FRACTION
    )
    boundary = (
        summaries["boundary_exceedance_fraction"]
        >= BOUNDARY_CONCENTRATION_FRACTION
    )
    if joint and boundary:
        return "joint_and_chunk_boundary_concentrated"
    if joint:
        return "joint_specific_residual"
    if boundary:
        return "chunk_boundary_residual"
    return "distributed_decoding_residual"


def _next_hypothesis(classification: str) -> str:
    return {
        "no_threshold_exceedance": "gate_b_action_replay_pass_reconcile_prior_result",
        "joint_and_chunk_boundary_concentrated": "inspect_joint_time_conditioning_interaction",
        "joint_specific_residual": "inspect_joint_normalization_or_output_projection",
        "chunk_boundary_residual": "inspect_chunk_boundary_cadence_or_time_conditioning",
        "distributed_decoding_residual": "inspect_decoder_sampling_or_action_gate_calibration",
    }[classification]


def _matrix(value: Any, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 50:
        raise ValueError(f"T20.35d {label} must contain 50 timesteps")
    result = []
    for row in value:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError(f"T20.35d {label} must contain six joints")
        normalized = []
        for element in row:
            if isinstance(element, bool) or not isinstance(element, (int, float)) or not math.isfinite(float(element)):
                raise ValueError(f"T20.35d {label} must be finite")
            normalized.append(float(element))
        result.append(normalized)
    return result


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"T20.35d {label} must be lowercase SHA-256")
    return value
