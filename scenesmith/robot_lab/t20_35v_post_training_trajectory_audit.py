"""Post-training trajectory comparison for T20.35v."""

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
from scenesmith.robot_lab.t20_33_one_batch_memorization import INFERENCE_SEEDS
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (
    _equal_with_float_tolerance,
)
from scenesmith.robot_lab.t20_35o_flow_trajectory_consistency_audit import (
    ACTIVE_ACTION_DIMENSIONS,
    MAXIMUM_ACTION_DIMENSIONS,
    NUM_INFERENCE_STEPS,
)
from scenesmith.robot_lab.t20_35q_post_training_trajectory_audit import (
    ATTEMPT_PATH as T20_35Q_ATTEMPT_PATH,
    RESULT_PATH as T20_35Q_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35q_sources,
    verify_attempt_marker as verify_t20_35q_attempt,
    verify_result as verify_t20_35q_result,
)
from scenesmith.robot_lab.t20_35t_time_normalized_standard_replay_correction import (
    RESULT_PATH as T20_35T_RESULT_PATH,
    SPEC_PATH as T20_35T_SPEC_PATH,
    verify_result as verify_t20_35t_result,
    verify_run as verify_t20_35t_run,
)
from scenesmith.robot_lab.t20_35u_post_training_trajectory_audit import (
    ATTEMPT_PATH as T20_35U_ATTEMPT_PATH,
    PERMIT_PATH as T20_35U_PERMIT_PATH,
    SPEC_PATH as T20_35U_SPEC_PATH,
    verify_attempt_marker as verify_t20_35u_attempt,
    verify_evaluation_permit as verify_t20_35u_permit,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_35v_post_training_trajectory_spec.json")
PERMIT_PATH = Path(
    "configurations/robot_lab/t20_35v_post_training_trajectory_evaluation_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_35v_post_training_trajectory_result.json"
)
ATTEMPT_PATH = Path("outputs/robot_lab/t20_35v_post_training_trajectory/attempt.json")
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_35v_runtime_dependency_preflight.json"
)
T20_35U_FAILURE_PATH = Path(
    "configurations/robot_lab/t20_35u_runtime_dependency_failure.json"
)
SCHEMA_VERSION = "scenesmith.t20_35v_post_training_trajectory_spec.v1"
PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_35v_post_training_trajectory_evaluation_permit.v1"
)
RESULT_SCHEMA_VERSION = "scenesmith.t20_35v_post_training_trajectory_result.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_35v_evaluation_attempt.v1"
RUNTIME_PREFLIGHT_SCHEMA_VERSION = (
    "scenesmith.t20_35v_runtime_dependency_preflight.v1"
)
EXPECTED_T20_35Q_SPEC_IDENTITY = (
    "fdb2fe3e4cbc70a87d09d297ded8fa64fc8d6caa4b94818af435d94b0945f05d"
)
EXPECTED_T20_35Q_RESULT_IDENTITY = (
    "6ba4954cd850abe69cf0de838740dab3b976ca277cb08360ec2e29ec0011f40b"
)
EXPECTED_T20_35T_RUN_IDENTITY = (
    "b5da8ab3f75d6232462ccdbe08179df718737883e92b8c89d14e26739b09b810"
)
EXPECTED_T20_35T_RESULT_IDENTITY = (
    "f63ee934d44ec6993f6e589d607fc8469f1aab4681c1b229e4d5c53e9264d38c"
)
EXPECTED_T20_35U_FAILURE_IDENTITY = (
    "0abd9650caa36206e6b2b8a1dc4c89d773107ada1c062677520089beadc0d208"
)
INHERITED_AUTHORITY_IDENTITY = (
    "8387945b2c8232315668c9619096f07e086cee2368245a99c6e28ca392b084c8"
)
ACTIVE_NOISE_SCALE = 0.0
PADDED_NOISE_SCALE = 1.0
MATERIAL_RESIDUAL_WORSENING = 0.01
MATERIAL_STATE_DISPLACEMENT = 0.01
VALID_FROM = "2026-07-15T07:27:47-05:00"
VALID_UNTIL = "2026-07-15T23:27:47-05:00"


def build_evaluation_spec(
    *,
    source_spec: dict[str, Any],
    source_result: dict[str, Any],
    training_run: dict[str, Any],
    training_result: dict[str, Any],
    runtime_failure: dict[str, Any],
) -> dict[str, Any]:
    for label, payload in (
        ("source spec", source_spec),
        ("source result", source_result),
        ("training run", training_run),
        ("training result", training_result),
        ("runtime failure", runtime_failure),
    ):
        verify_signed_payload(payload, label=f"T20.35v {label}")
    if (
        source_result.get("path_interference_classification")
        != "early_mid_path_interference"
        or source_result.get("gate_b_passed") is not False
        or source_result.get("selected_next_hypothesis")
        != "design_full_path_self_consistency_correction"
        or training_result.get("run_identity_sha256")
        != training_run.get("identity_sha256")
        or training_result.get("correction_objective_ratio_within_target") is not True
        or training_result.get("objective_ratio_within_threshold") is not True
        or training_result.get("all_decoded_chunks_within_threshold") is not False
        or training_result.get("gate_b_passed") is not False
        or training_result.get("selected_next_hypothesis")
        != "balanced_objectives_pass_action_fail_route_post_training_path_audit"
        or runtime_failure.get("failure_phase")
        != "lerobot_dataset_dependency_import_before_checkpoint_access"
        or runtime_failure.get("missing_package") != "datasets"
        or runtime_failure.get("model_loaded") is not False
        or runtime_failure.get("checkpoint_read") is not False
        or runtime_failure.get("selected_next_hypothesis")
        != "route_dependency_complete_runtime_preflight_before_distinct_path_audit"
    ):
        raise ValueError("T20.35v source route drifted")
    source_rows = _seed_rows(source_result.get("new_trajectory_evaluations"))
    training_chunks = _seed_rows(training_result.get("decoded_action_chunks"))
    base_hashes = []
    source_endpoint_hashes = []
    new_endpoint_hashes = []
    for index, (source_row, new_row) in enumerate(
        zip(source_rows, training_chunks, strict=True)
    ):
        if (
            source_row.get("inference_seed") != INFERENCE_SEEDS[index]
            or new_row.get("inference_seed") != INFERENCE_SEEDS[index]
        ):
            raise ValueError("T20.35v source seed order drifted")
        _sha(source_row.get("base_noise_sha256"), "source base noise")
        _sha(source_row.get("decoded_action_chunk_sha256"), "source endpoint")
        _sha(new_row.get("decoded_action_chunk_sha256"), "training endpoint")
        base_hashes.append(source_row["base_noise_sha256"])
        source_endpoint_hashes.append(source_row["decoded_action_chunk_sha256"])
        new_endpoint_hashes.append(new_row["decoded_action_chunk_sha256"])
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35v",
            "scope": "one_inference_only_balanced_checkpoint_source_target_trajectory_comparison",
            "t20_35q_spec_identity_sha256": source_spec["identity_sha256"],
            "t20_35q_result_identity_sha256": source_result["identity_sha256"],
            "t20_35t_run_identity_sha256": training_run["identity_sha256"],
            "t20_35t_result_identity_sha256": training_result["identity_sha256"],
            "t20_35u_runtime_failure_identity_sha256": runtime_failure[
                "identity_sha256"
            ],
            "t20_35o_result_identity_sha256": source_result[
                "t20_35o_result_identity_sha256"
            ],
            "checkpoint_identity_sha256": training_run[
                "checkpoint_identity_sha256"
            ],
            "checkpoint_tree": training_run["checkpoint_tree"],
            "dataset_action_chunk_sha256": source_spec[
                "dataset_action_chunk_sha256"
            ],
            "normalized_padded_target_sha256": source_spec[
                "normalized_padded_target_sha256"
            ],
            "lerobot_stack_identity_sha256": source_spec[
                "lerobot_stack_identity_sha256"
            ],
            "sampler_source_sha256": source_spec["sampler_source_sha256"],
            "active_action_dimension_count": ACTIVE_ACTION_DIMENSIONS,
            "maximum_action_dimension_count": MAXIMUM_ACTION_DIMENSIONS,
            "active_noise_scale": ACTIVE_NOISE_SCALE,
            "padded_noise_scale": PADDED_NOISE_SCALE,
            "inference_seeds": list(INFERENCE_SEEDS),
            "num_inference_steps": NUM_INFERENCE_STEPS,
            "base_noise_sha256_by_seed": base_hashes,
            "source_decoded_action_sha256_by_seed": source_endpoint_hashes,
            "new_decoded_action_sha256_by_seed": new_endpoint_hashes,
            "material_active_target_residual_worsening_threshold": MATERIAL_RESIDUAL_WORSENING,
            "material_state_displacement_threshold": MATERIAL_STATE_DISPLACEMENT,
            "required_python_major_minor": [3, 12],
            "runtime_dependency_preflight_required": True,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
            ],
            "model_loaded": False,
            "model_inference": False,
            "optimizer_training": False,
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


def verify_evaluation_spec(
    payload: dict[str, Any], *, expected_spec: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.35v trajectory spec")
    verify_signed_payload(expected_spec, label="T20.35v expected trajectory spec")
    if payload != expected_spec:
        raise ValueError("T20.35v trajectory spec drifted")


def build_evaluation_permit(*, spec: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35v permit source spec")
    if (
        spec.get("active_noise_scale") != ACTIVE_NOISE_SCALE
        or spec.get("padded_noise_scale") != PADDED_NOISE_SCALE
        or spec.get("num_inference_steps") != NUM_INFERENCE_STEPS
        or spec.get("runtime_dependency_preflight_required") is not True
    ):
        raise ValueError("T20.35v permit source spec drifted")
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": "T20.35v",
            "scope": "one_local_mps_inference_only_post_training_trajectory_audit",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "inherited_authority_decision_identity_sha256": INHERITED_AUTHORITY_IDENTITY,
            "t20_35u_runtime_failure_identity_sha256": spec[
                "t20_35u_runtime_failure_identity_sha256"
            ],
            "runtime_dependency_preflight_required": True,
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
    verify_signed_payload(payload, label="T20.35v trajectory permit")
    if payload != build_evaluation_permit(spec=spec):
        raise ValueError("T20.35v trajectory permit drifted")


def build_runtime_preflight(
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    stack_identity: str,
    dependency_versions: dict[str, str],
) -> dict[str, Any]:
    verify_evaluation_permit(permit, spec=spec)
    required = {"datasets", "lerobot", "pyarrow", "safetensors", "torch", "transformers"}
    if (
        stack_identity != spec.get("lerobot_stack_identity_sha256")
        or set(dependency_versions) != required
        or any(not isinstance(value, str) or not value for value in dependency_versions.values())
    ):
        raise ValueError("T20.35v runtime dependency evidence drifted")
    return sign_payload(
        {
            "schema_version": RUNTIME_PREFLIGHT_SCHEMA_VERSION,
            "task_id": "T20.35v",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "t20_35u_runtime_failure_identity_sha256": spec[
                "t20_35u_runtime_failure_identity_sha256"
            ],
            "lerobot_stack_identity_sha256": stack_identity,
            "checkpoint_identity_sha256": spec["checkpoint_identity_sha256"],
            "python_major_minor": [3, 12],
            "dependency_versions": dependency_versions,
            "mps_available": True,
            "attempt_exists": False,
            "result_exists": False,
            "checkpoint_tree_verified": True,
            "model_loaded": False,
            "model_inference": False,
            "checkpoint_tensor_read": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "closed_loop_rollout": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any], *, spec: dict[str, Any], permit: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.35v runtime preflight")
    expected = build_runtime_preflight(
        spec=spec,
        permit=permit,
        stack_identity=payload.get("lerobot_stack_identity_sha256"),
        dependency_versions=payload.get("dependency_versions"),
    )
    if payload != expected:
        raise ValueError("T20.35v runtime preflight drifted")


def verify_attempt_marker(
    payload: dict[str, Any], *, spec_identity: str, permit_identity: str,
    runtime_preflight_identity: str,
) -> None:
    verify_signed_payload(payload, label="T20.35v trajectory attempt")
    if (
        payload.get("schema_version") != ATTEMPT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35v"
        or payload.get("evaluation_spec_identity_sha256") != spec_identity
        or payload.get("evaluation_permit_identity_sha256") != permit_identity
        or payload.get("runtime_preflight_identity_sha256")
        != runtime_preflight_identity
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
        raise ValueError("T20.35v trajectory attempt drifted")


def build_result(
    *,
    spec: dict[str, Any],
    permit: dict[str, Any],
    runtime_preflight: dict[str, Any],
    attempt: dict[str, Any],
    source_trajectory_result: dict[str, Any],
    training_result: dict[str, Any],
    target_chunk: list[list[float]],
    normalized_target: list[list[float]],
    new_trajectory_evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35v result spec")
    verify_signed_payload(source_trajectory_result, label="T20.35v source path")
    verify_signed_payload(training_result, label="T20.35v training result")
    verify_evaluation_permit(permit, spec=spec)
    verify_runtime_preflight(runtime_preflight, spec=spec, permit=permit)
    verify_attempt_marker(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
        runtime_preflight_identity=runtime_preflight["identity_sha256"],
    )
    if (
        source_trajectory_result["identity_sha256"]
        != spec["t20_35q_result_identity_sha256"]
        or training_result["identity_sha256"]
        != spec["t20_35t_result_identity_sha256"]
        or _matrix_sha(target_chunk) != spec["dataset_action_chunk_sha256"]
    ):
        raise ValueError("T20.35v result source lineage drifted")
    target = _finite_matrix(
        normalized_target,
        rows=50,
        columns=MAXIMUM_ACTION_DIMENSIONS,
        label="normalized target",
    )
    if _matrix_sha(target) != spec["normalized_padded_target_sha256"]:
        raise ValueError("T20.35v normalized target drifted")
    source_rows = _seed_rows(
        source_trajectory_result.get("new_trajectory_evaluations")
    )
    new_rows = _seed_rows(new_trajectory_evaluations)
    evaluated = []
    step_buckets = [
        {
            "new_active_residual": [],
            "source_active_residual": [],
            "active_state_displacement": [],
            "padded_state_displacement": [],
            "active_velocity_displacement": [],
            "padded_velocity_displacement": [],
        }
        for _ in range(NUM_INFERENCE_STEPS)
    ]
    for seed_index, (source_row, new_row) in enumerate(
        zip(source_rows, new_rows, strict=True)
    ):
        if (
            source_row.get("inference_seed") != INFERENCE_SEEDS[seed_index]
            or new_row.get("inference_seed") != INFERENCE_SEEDS[seed_index]
            or new_row.get("base_noise_sha256")
            != spec["base_noise_sha256_by_seed"][seed_index]
        ):
            raise ValueError("T20.35v new trajectory seed or noise drifted")
        decoded = _finite_matrix(
            new_row.get("decoded_action_chunk"),
            rows=50,
            columns=ACTIVE_ACTION_DIMENSIONS,
            label="decoded endpoint",
        )
        decoded_sha = _matrix_sha(decoded)
        if decoded_sha != spec["new_decoded_action_sha256_by_seed"][seed_index]:
            raise ValueError("T20.35v decoded endpoint failed exact reproduction")
        source_steps = source_row.get("steps")
        new_steps = new_row.get("steps")
        if (
            not isinstance(source_steps, list)
            or len(source_steps) != NUM_INFERENCE_STEPS
            or not isinstance(new_steps, list)
            or len(new_steps) != NUM_INFERENCE_STEPS
        ):
            raise ValueError("T20.35v trajectory step coverage drifted")
        steps = []
        for step_index, (source_step, new_step) in enumerate(
            zip(source_steps, new_steps, strict=True)
        ):
            expected_time = 1.0 - step_index / NUM_INFERENCE_STEPS
            if (
                source_step.get("step_index") != step_index
                or new_step.get("step_index") != step_index
                or _finite(source_step.get("time"), "source time") != expected_time
                or _finite(new_step.get("time"), "new time") != expected_time
            ):
                raise ValueError("T20.35v trajectory time grid drifted")
            source_state = _finite_matrix(
                source_step.get("state"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="source state",
            )
            source_velocity = _finite_matrix(
                source_step.get("learned_velocity"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="source velocity",
            )
            new_state = _finite_matrix(
                new_step.get("state"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="new state",
            )
            new_velocity = _finite_matrix(
                new_step.get("learned_velocity"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="new velocity",
            )
            source_residual = [
                [
                    source_velocity[t][j]
                    - (source_state[t][j] - target[t][j]) / expected_time
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for t in range(50)
            ]
            new_residual = [
                [
                    new_velocity[t][j]
                    - (new_state[t][j] - target[t][j]) / expected_time
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for t in range(50)
            ]
            active_source = _mean_abs(source_residual, 0, ACTIVE_ACTION_DIMENSIONS)
            active_new = _mean_abs(new_residual, 0, ACTIVE_ACTION_DIMENSIONS)
            padded_source = _mean_abs(
                source_residual, ACTIVE_ACTION_DIMENSIONS, MAXIMUM_ACTION_DIMENSIONS
            )
            padded_new = _mean_abs(
                new_residual, ACTIVE_ACTION_DIMENSIONS, MAXIMUM_ACTION_DIMENSIONS
            )
            state_displacement = _difference(new_state, source_state)
            velocity_displacement = _difference(new_velocity, source_velocity)
            active_state = _mean_abs(
                state_displacement, 0, ACTIVE_ACTION_DIMENSIONS
            )
            padded_state = _mean_abs(
                state_displacement,
                ACTIVE_ACTION_DIMENSIONS,
                MAXIMUM_ACTION_DIMENSIONS,
            )
            active_velocity = _mean_abs(
                velocity_displacement, 0, ACTIVE_ACTION_DIMENSIONS
            )
            padded_velocity = _mean_abs(
                velocity_displacement,
                ACTIVE_ACTION_DIMENSIONS,
                MAXIMUM_ACTION_DIMENSIONS,
            )
            bucket = step_buckets[step_index]
            bucket["new_active_residual"].append(active_new)
            bucket["source_active_residual"].append(active_source)
            bucket["active_state_displacement"].append(active_state)
            bucket["padded_state_displacement"].append(padded_state)
            bucket["active_velocity_displacement"].append(active_velocity)
            bucket["padded_velocity_displacement"].append(padded_velocity)
            steps.append(
                {
                    "step_index": step_index,
                    "time": expected_time,
                    "state": new_state,
                    "state_sha256": _matrix_sha(new_state),
                    "learned_velocity": new_velocity,
                    "learned_velocity_sha256": _matrix_sha(new_velocity),
                    "new_active_target_residual_mean_absolute": active_new,
                    "source_active_target_residual_mean_absolute": active_source,
                    "active_target_residual_mean_change": active_new - active_source,
                    "new_padded_target_residual_mean_absolute": padded_new,
                    "source_padded_target_residual_mean_absolute": padded_source,
                    "active_state_displacement_mean_absolute": active_state,
                    "padded_state_displacement_mean_absolute": padded_state,
                    "active_velocity_displacement_mean_absolute": active_velocity,
                    "padded_velocity_displacement_mean_absolute": padded_velocity,
                }
            )
        evaluated.append(
            {
                "inference_seed": new_row["inference_seed"],
                "base_noise_sha256": new_row["base_noise_sha256"],
                "decoded_action_chunk": decoded,
                "decoded_action_chunk_sha256": decoded_sha,
                "steps": steps,
            }
        )
    aggregate = []
    for step_index, bucket in enumerate(step_buckets):
        values = {
            key: sum(rows) / len(rows) for key, rows in bucket.items()
        }
        aggregate.append(
            {
                "step_index": step_index,
                "time": 1.0 - step_index / NUM_INFERENCE_STEPS,
                "new_active_target_residual_mean_absolute": values[
                    "new_active_residual"
                ],
                "source_active_target_residual_mean_absolute": values[
                    "source_active_residual"
                ],
                "active_target_residual_mean_change": values[
                    "new_active_residual"
                ]
                - values["source_active_residual"],
                "active_state_displacement_mean_absolute": values[
                    "active_state_displacement"
                ],
                "padded_state_displacement_mean_absolute": values[
                    "padded_state_displacement"
                ],
                "active_velocity_displacement_mean_absolute": values[
                    "active_velocity_displacement"
                ],
                "padded_velocity_displacement_mean_absolute": values[
                    "padded_velocity_displacement"
                ],
            }
        )
    residual_worsening = [
        row["step_index"]
        for row in aggregate
        if row["active_target_residual_mean_change"]
        >= MATERIAL_RESIDUAL_WORSENING
    ]
    earliest_residual = residual_worsening[0] if residual_worsening else None
    path_displacement = [
        row["step_index"]
        for row in aggregate
        if max(
            row["active_state_displacement_mean_absolute"],
            row["padded_state_displacement_mean_absolute"],
        )
        >= MATERIAL_STATE_DISPLACEMENT
    ]
    earliest_path = path_displacement[0] if path_displacement else None
    max_active_state = max(
        row["active_state_displacement_mean_absolute"] for row in aggregate
    )
    max_padded_state = max(
        row["padded_state_displacement_mean_absolute"] for row in aggregate
    )
    if (
        max_padded_state >= MATERIAL_STATE_DISPLACEMENT
        and max_padded_state > max_active_state
    ):
        classification = "padded_state_coupling"
        route = "design_padded_state_invariance_correction"
    elif (
        earliest_residual is not None and earliest_residual <= 6
    ) or (earliest_path is not None and earliest_path <= 6):
        classification = "early_mid_path_interference"
        route = "audit_balanced_checkpoint_step_coordinate_outliers"
    elif earliest_residual is not None or earliest_path is not None:
        classification = "off_trajectory_terminal_supervision"
        route = "design_on_policy_terminal_path_correction"
    else:
        classification = "distributed_path_interference"
        route = "audit_subthreshold_distributed_path_displacement"
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35v",
            "scope": "one_inference_only_balanced_checkpoint_source_target_trajectory_result",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "runtime_preflight_identity_sha256": runtime_preflight[
                "identity_sha256"
            ],
            "evaluation_attempt_identity_sha256": attempt["identity_sha256"],
            "t20_35q_result_identity_sha256": source_trajectory_result[
                "identity_sha256"
            ],
            "t20_35t_result_identity_sha256": training_result["identity_sha256"],
            "t20_35u_runtime_failure_identity_sha256": spec[
                "t20_35u_runtime_failure_identity_sha256"
            ],
            "t20_35o_result_identity_sha256": spec[
                "t20_35o_result_identity_sha256"
            ],
            "checkpoint_identity_sha256": spec["checkpoint_identity_sha256"],
            "dataset_action_chunk_sha256": spec["dataset_action_chunk_sha256"],
            "new_trajectory_evaluations": evaluated,
            "aggregate_step_comparison": aggregate,
            "earliest_material_active_target_residual_worsening_step": earliest_residual,
            "earliest_material_path_displacement_step": earliest_path,
            "maximum_active_state_displacement_mean_absolute": max_active_state,
            "maximum_padded_state_displacement_mean_absolute": max_padded_state,
            "path_interference_classification": classification,
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
    runtime_preflight: dict[str, Any],
    attempt: dict[str, Any],
    source_trajectory_result: dict[str, Any],
    training_result: dict[str, Any],
    target_chunk: list[list[float]],
    normalized_target: list[list[float]],
) -> None:
    verify_signed_payload(payload, label="T20.35v trajectory result")
    expected = build_result(
        spec=spec,
        permit=permit,
        runtime_preflight=runtime_preflight,
        attempt=attempt,
        source_trajectory_result=source_trajectory_result,
        training_result=training_result,
        target_chunk=target_chunk,
        normalized_target=normalized_target,
        new_trajectory_evaluations=payload.get("new_trajectory_evaluations"),
    )
    archived = {key: value for key, value in payload.items() if key != "identity_sha256"}
    rebuilt = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(archived, rebuilt, absolute_tolerance=1e-15):
        raise ValueError("T20.35v trajectory result drifted")


def load_source_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    prior_spec = load_strict_json(root / T20_35U_SPEC_PATH)
    prior_permit = load_strict_json(root / T20_35U_PERMIT_PATH)
    verify_t20_35u_permit(prior_permit, spec=prior_spec)
    prior_attempt = load_strict_json(root / T20_35U_ATTEMPT_PATH)
    verify_t20_35u_attempt(
        prior_attempt,
        spec_identity=prior_spec["identity_sha256"],
        permit_identity=prior_permit["identity_sha256"],
    )
    runtime_failure = load_strict_json(root / T20_35U_FAILURE_PATH)
    verify_signed_payload(runtime_failure, label="T20.35v prior runtime failure")
    if (
        runtime_failure.get("identity_sha256")
        != EXPECTED_T20_35U_FAILURE_IDENTITY
        or runtime_failure.get("evaluation_attempt_identity_sha256")
        != prior_attempt["identity_sha256"]
    ):
        raise ValueError("T20.35v prior runtime failure lineage drifted")
    source = load_t20_35q_sources(repo_root=root)
    source_spec = source["trajectory_spec"]
    source_permit = source["trajectory_permit"]
    source_attempt = load_strict_json(root / T20_35Q_ATTEMPT_PATH)
    verify_t20_35q_attempt(
        source_attempt,
        spec_identity=source_spec["identity_sha256"],
        permit_identity=source_permit["identity_sha256"],
    )
    source_result = load_strict_json(root / T20_35Q_RESULT_PATH)
    target = source["residual_report"]["target_action_chunk"]
    verify_t20_35q_result(
        source_result,
        spec=source_spec,
        permit=source_permit,
        attempt=source_attempt,
        source_trajectory_result=source["source_result"],
        training_result=source["training_result"],
        target_chunk=target,
    )
    target_result = source["source_result"]
    training_spec = load_strict_json(root / T20_35T_SPEC_PATH)
    from scripts.robot_lab.run_t20_35t_time_normalized_standard_replay_correction import (
        SUMMARY_PATH,
    )

    training_run = load_strict_json(SUMMARY_PATH)
    training_result = load_strict_json(root / T20_35T_RESULT_PATH)
    verify_t20_35t_run(
        training_run,
        spec=training_spec,
        authority_identity=training_result["authority_decision_identity_sha256"],
    )
    verify_t20_35t_result(
        training_result, spec=training_spec, run=training_run
    )
    if (
        source_spec["identity_sha256"] != EXPECTED_T20_35Q_SPEC_IDENTITY
        or source_result["identity_sha256"] != EXPECTED_T20_35Q_RESULT_IDENTITY
        or training_run["identity_sha256"] != EXPECTED_T20_35T_RUN_IDENTITY
        or training_result["identity_sha256"] != EXPECTED_T20_35T_RESULT_IDENTITY
    ):
        raise ValueError("T20.35v expected source identity drifted")
    return {
        **source,
        "source_spec": source_spec,
        "source_result": source_result,
        "target_result": target_result,
        "training_spec": training_spec,
        "training_run": training_run,
        "training_result": training_result,
        "runtime_failure": runtime_failure,
    }


def write_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    spec = build_evaluation_spec(
        source_spec=sources["source_spec"],
        source_result=sources["source_result"],
        training_run=sources["training_run"],
        training_result=sources["training_result"],
        runtime_failure=sources["runtime_failure"],
    )
    permit = build_evaluation_permit(spec=spec)
    dump_canonical_json(root / SPEC_PATH, spec)
    dump_canonical_json(root / PERMIT_PATH, permit)
    return {"trajectory_spec": spec, "trajectory_permit": permit}


def load_and_verify_evaluation_files(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    expected = build_evaluation_spec(
        source_spec=sources["source_spec"],
        source_result=sources["source_result"],
        training_run=sources["training_run"],
        training_result=sources["training_result"],
        runtime_failure=sources["runtime_failure"],
    )
    spec = load_strict_json(root / SPEC_PATH)
    verify_evaluation_spec(spec, expected_spec=expected)
    permit = load_strict_json(root / PERMIT_PATH)
    verify_evaluation_permit(permit, spec=spec)
    return {**sources, "trajectory_spec": spec, "trajectory_permit": permit}


def _seed_rows(value: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or len(value) != len(INFERENCE_SEEDS)
        or any(not isinstance(row, dict) for row in value)
    ):
        raise ValueError("T20.35v seed coverage drifted")
    return value


def _finite_matrix(
    value: Any, *, rows: int, columns: int, label: str
) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != rows:
        raise ValueError(f"T20.35v {label} row count drifted")
    matrix = []
    for row in value:
        if not isinstance(row, list) or len(row) != columns:
            raise ValueError(f"T20.35v {label} column count drifted")
        matrix.append([_finite(item, label) for item in row])
    return matrix


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.35v {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.35v {label} must be finite")
    return number


def _mean_abs(matrix: list[list[float]], start: int, stop: int) -> float:
    values = [abs(row[index]) for row in matrix for index in range(start, stop)]
    return sum(values) / len(values)


def _difference(
    left: list[list[float]], right: list[list[float]]
) -> list[list[float]]:
    return [
        [left[row][column] - right[row][column] for column in range(len(left[row]))]
        for row in range(len(left))
    ]


def _matrix_sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35v {label} must be lowercase SHA-256")
