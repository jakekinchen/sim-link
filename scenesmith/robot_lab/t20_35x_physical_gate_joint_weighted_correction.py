"""Exact-state physical-gate joint-weighted correction for T20.35x."""

from __future__ import annotations

import copy
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
    MAX_OBJECTIVE_RATIO,
)
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (
    ADAPTATION_MODE,
    TRAINABLE_PREFIXES,
)
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (
    _equal_with_float_tolerance,
)
from scenesmith.robot_lab.so101_coordinates import (
    GRIPPER_RANGE_RAD,
    coordinate_contract,
)
from scenesmith.robot_lab.so101_processor import JOINT_NAMES
from scenesmith.robot_lab.t20_17_clean_base_preflight import DATASET_MANIFEST_PATH
from scenesmith.robot_lab.t20_35o_flow_trajectory_consistency_audit import (
    ACTIVE_ACTION_DIMENSIONS,
    MAXIMUM_ACTION_DIMENSIONS,
)
from scenesmith.robot_lab.t20_35v_post_training_trajectory_audit import (
    RESULT_PATH as T20_35V_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35v_sources,
)
from scenesmith.robot_lab.t20_35w_step_coordinate_action_outlier_audit import (
    AUDIT_PATH as T20_35W_AUDIT_PATH,
    load_source_artifacts as load_t20_35w_sources,
    verify_audit as verify_t20_35w_audit,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_training_spec.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_result.json"
)
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_35x_runtime_dependency_preflight.json"
)
TRAINING_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_permit.json"
)
DATASET_STATS_PATH = Path(
    "outputs/robot_lab/t20_17_lerobot_training_dataset/meta/stats.json"
)
SCHEMA_VERSION = "scenesmith.t20_35x_physical_gate_joint_weighted_training_spec.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_35x_physical_gate_joint_weighted_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_35x_physical_gate_joint_weighted_result.v1"
RUNTIME_PREFLIGHT_SCHEMA_VERSION = "scenesmith.t20_35x_runtime_dependency_preflight.v1"
TRAINING_PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_35x_physical_gate_joint_weighted_permit.v1"
)
EXPECTED_T20_35T_SPEC_IDENTITY = (
    "34881e21e02b7567133a51a101fafc673ae52fe9bb7bf6e603384811e4747335"
)
EXPECTED_T20_35T_RUN_IDENTITY = (
    "b5da8ab3f75d6232462ccdbe08179df718737883e92b8c89d14e26739b09b810"
)
EXPECTED_T20_35T_RESULT_IDENTITY = (
    "f63ee934d44ec6993f6e589d607fc8469f1aab4681c1b229e4d5c53e9264d38c"
)
EXPECTED_T20_35V_SPEC_IDENTITY = (
    "a0b5c211312ab488fd07b3b237a50e49f50a4b05ec012faf3120ed55603f66d8"
)
EXPECTED_T20_35V_RESULT_IDENTITY = (
    "aad8a14809fdcd079651bc90ca4bbdcd753831044c025591e21da391f02e3f3d"
)
EXPECTED_T20_35O_RESULT_IDENTITY = (
    "5c5b41b99d83b1e5116195bab551277d3b65126066717823342030b23391a582"
)
EXPECTED_T20_35W_AUDIT_IDENTITY = (
    "e52d6d08fb0b2ab0b8308f880e98156aa7b20db7e7eb203efd08a7424a288901"
)
EXPECTED_DATASET_STATS_SHA256 = (
    "9c013fde21c80e2dd0d184ac3122f1ce4fd75e662dedef97fd5f6b651376cf4c"
)
EXPECTED_DEPENDENCY_VERSIONS = {
    "datasets": "4.8.5",
    "lerobot": "0.6.1",
    "pyarrow": "25.0.0",
    "safetensors": "0.8.0",
    "torch": "2.11.0",
    "transformers": "5.5.4",
}
EXPECTED_RUNTIME_PREFLIGHT_IDENTITY = (
    "292a5b10c66b208bf87947840639be5b4ea5e7cb575e91d5c3331df7e1c041b9"
)
EXPECTED_TRAINING_PERMIT_IDENTITY = (
    "c497dbed89c5d5ae3b0a512b6e4d0237d4271d721b4326dc938f7a9ce0523e24"
)
CORRECTION_STEP_INDICES = tuple(range(10))
CORRECTION_EXAMPLE_COUNT = len(INFERENCE_SEEDS) * len(CORRECTION_STEP_INDICES)
OPTIMIZER_UPDATES = 500
LEARNING_RATE = 2.5e-5
TRAINING_SEED = 20260718
STANDARD_REPLAY_SEED_BASE = 20262718
GRADIENT_CLIP_NORM = 1.0
RECONSTRUCTION_TOLERANCE = 2e-12


def build_correction_examples(
    trajectory_result: dict[str, Any],
    target_result: dict[str, Any],
    coefficient_by_dimension: list[float],
) -> list[dict[str, Any]]:
    verify_signed_payload(trajectory_result, label="T20.35x trajectory source")
    verify_signed_payload(target_result, label="T20.35x normalized-target source")
    if (
        trajectory_result.get("identity_sha256") != EXPECTED_T20_35V_RESULT_IDENTITY
        or trajectory_result.get("path_interference_classification")
        != "early_mid_path_interference"
        or trajectory_result.get("selected_next_hypothesis")
        != "audit_balanced_checkpoint_step_coordinate_outliers"
        or trajectory_result.get("gate_b_passed") is not False
        or target_result.get("identity_sha256") != EXPECTED_T20_35O_RESULT_IDENTITY
        or trajectory_result.get("t20_35o_result_identity_sha256")
        != target_result.get("identity_sha256")
    ):
        raise ValueError("T20.35x trajectory route drifted")
    coefficients = [
        _finite(value, "joint coefficient") for value in coefficient_by_dimension
    ]
    if len(coefficients) != MAXIMUM_ACTION_DIMENSIONS or any(
        value <= 0.0 for value in coefficients
    ):
        raise ValueError("T20.35x joint coefficient coverage drifted")
    target = _finite_matrix(
        target_result.get("normalized_padded_target"),
        rows=50,
        columns=MAXIMUM_ACTION_DIMENSIONS,
        label="normalized padded target",
    )
    if _matrix_sha(target) != target_result.get("normalized_padded_target_sha256"):
        raise ValueError("T20.35x normalized target hash drifted")
    rows = trajectory_result.get("new_trajectory_evaluations")
    if (
        not isinstance(rows, list)
        or len(rows) != len(INFERENCE_SEEDS)
        or [row.get("inference_seed") for row in rows if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35x trajectory seed coverage drifted")
    examples: list[dict[str, Any]] = []
    for row in rows:
        steps = row.get("steps")
        if not isinstance(steps, list) or len(steps) != 10:
            raise ValueError("T20.35x trajectory step coverage drifted")
        for step_index in CORRECTION_STEP_INDICES:
            step = steps[step_index]
            if step.get("step_index") != step_index:
                raise ValueError("T20.35x correction step order drifted")
            time = _finite(step.get("time"), "correction time")
            expected_time = 1.0 - step_index / 10
            if time != expected_time or time <= 0.0:
                raise ValueError("T20.35x correction time drifted")
            state = _finite_matrix(
                step.get("state"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="correction state",
            )
            if _matrix_sha(state) != step.get("state_sha256"):
                raise ValueError("T20.35x correction state hash drifted")
            learned_velocity = _finite_matrix(
                step.get("learned_velocity"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="learned velocity",
            )
            if _matrix_sha(learned_velocity) != step.get("learned_velocity_sha256"):
                raise ValueError("T20.35x learned velocity hash drifted")
            reference = [
                [
                    (state[t][j] - target[t][j]) / time
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for t in range(50)
            ]
            derived_noise = [
                [
                    (state[t][j] - (1.0 - time) * target[t][j]) / time
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for t in range(50)
            ]
            reconstructed_state = [
                [
                    time * derived_noise[t][j] + (1.0 - time) * target[t][j]
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for t in range(50)
            ]
            reconstructed_velocity = [
                [
                    derived_noise[t][j] - target[t][j]
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for t in range(50)
            ]
            state_error = max(
                abs(reconstructed_state[t][j] - state[t][j])
                for t in range(50)
                for j in range(MAXIMUM_ACTION_DIMENSIONS)
            )
            velocity_error = max(
                abs(reconstructed_velocity[t][j] - reference[t][j])
                for t in range(50)
                for j in range(MAXIMUM_ACTION_DIMENSIONS)
            )
            if (
                state_error > RECONSTRUCTION_TOLERANCE
                or velocity_error > RECONSTRUCTION_TOLERANCE
            ):
                raise ValueError(
                    "T20.35x exact-state reconstruction exceeded tolerance"
                )
            squared_error = [
                [
                    (learned_velocity[t][j] - reference[t][j]) ** 2
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for t in range(50)
            ]
            baseline_raw = _finite(
                sum(
                    squared_error[t][j]
                    for t in range(50)
                    for j in range(ACTIVE_ACTION_DIMENSIONS)
                )
                / (50 * ACTIVE_ACTION_DIMENSIONS),
                "baseline raw correction objective",
            )
            baseline_joint_weighted = _finite(
                sum(
                    squared_error[t][j] * coefficients[j]
                    for t in range(50)
                    for j in range(MAXIMUM_ACTION_DIMENSIONS)
                )
                / (50 * MAXIMUM_ACTION_DIMENSIONS),
                "baseline joint-weighted correction objective",
            )
            if baseline_raw <= 0.0 or baseline_joint_weighted <= 0.0:
                raise ValueError(
                    "T20.35x baseline correction objective must be positive"
                )
            examples.append(
                {
                    "correction_example_index": len(examples),
                    "inference_seed": row["inference_seed"],
                    "step_index": step_index,
                    "time": time,
                    "state_sha256": step["state_sha256"],
                    "target_velocity_sha256": _matrix_sha(reference),
                    "derived_noise_sha256": _matrix_sha(derived_noise),
                    "learned_velocity_sha256": step["learned_velocity_sha256"],
                    "baseline_raw_correction_objective": baseline_raw,
                    "baseline_joint_weighted_correction_objective": baseline_joint_weighted,
                    "state_reconstruction_maximum_error": state_error,
                    "velocity_reconstruction_maximum_error": velocity_error,
                }
            )
    if len(examples) != CORRECTION_EXAMPLE_COUNT:
        raise ValueError("T20.35x correction example count drifted")
    return examples


def materialize_correction_tensors(
    trajectory_result: dict[str, Any],
    target_result: dict[str, Any],
    coefficient_by_dimension: list[float],
) -> list[dict[str, Any]]:
    """Return verified raw tensors for the reviewed runner."""
    manifest = build_correction_examples(
        trajectory_result, target_result, coefficient_by_dimension
    )
    target = target_result["normalized_padded_target"]
    output = []
    for manifest_row, trajectory in zip(
        manifest,
        [
            (row, step)
            for row in trajectory_result["new_trajectory_evaluations"]
            for step in CORRECTION_STEP_INDICES
        ],
        strict=True,
    ):
        row, step_index = trajectory
        state = row["steps"][step_index]["state"]
        time = manifest_row["time"]
        noise = [
            [
                (state[t][j] - (1.0 - time) * target[t][j]) / time
                for j in range(MAXIMUM_ACTION_DIMENSIONS)
            ]
            for t in range(50)
        ]
        if _matrix_sha(noise) != manifest_row["derived_noise_sha256"]:
            raise ValueError("T20.35x materialized correction noise drifted")
        output.append({**manifest_row, "derived_noise": noise})
    return output


def build_training_spec(
    *,
    source_spec: dict[str, Any],
    source_run: dict[str, Any],
    source_result: dict[str, Any],
    trajectory_spec: dict[str, Any],
    trajectory_result: dict[str, Any],
    target_result: dict[str, Any],
    outlier_audit: dict[str, Any],
    dataset_manifest: dict[str, Any],
    dataset_stats: dict[str, Any],
    dataset_stats_file_sha256: str,
) -> dict[str, Any]:
    for label, payload in (
        ("source spec", source_spec),
        ("source run", source_run),
        ("source result", source_result),
        ("trajectory spec", trajectory_spec),
        ("trajectory result", trajectory_result),
        ("target result", target_result),
        ("outlier audit", outlier_audit),
        ("dataset manifest", dataset_manifest),
    ):
        verify_signed_payload(payload, label=f"T20.35x {label}")
    if (
        source_spec.get("identity_sha256") != EXPECTED_T20_35T_SPEC_IDENTITY
        or source_spec.get("model", {}).get("adaptation_mode") != ADAPTATION_MODE
        or source_run.get("identity_sha256") != EXPECTED_T20_35T_RUN_IDENTITY
        or source_result.get("identity_sha256") != EXPECTED_T20_35T_RESULT_IDENTITY
        or source_result.get("objective_ratio_within_threshold") is not True
        or source_result.get("correction_objective_ratio_within_target") is not True
        or source_result.get("all_decoded_chunks_within_threshold") is not False
        or source_result.get("gate_b_passed") is not False
        or source_result.get("run_identity_sha256") != source_run.get("identity_sha256")
        or trajectory_spec.get("identity_sha256") != EXPECTED_T20_35V_SPEC_IDENTITY
        or trajectory_result.get("identity_sha256") != EXPECTED_T20_35V_RESULT_IDENTITY
        or trajectory_result.get("evaluation_spec_identity_sha256")
        != trajectory_spec.get("identity_sha256")
        or trajectory_spec.get("checkpoint_identity_sha256")
        != source_run.get("checkpoint_identity_sha256")
        or target_result.get("identity_sha256") != EXPECTED_T20_35O_RESULT_IDENTITY
        or outlier_audit.get("identity_sha256") != EXPECTED_T20_35W_AUDIT_IDENTITY
        or outlier_audit.get("action_outlier_classification")
        != "physical_gate_joint_dominance_without_normalized_state_dominance"
        or outlier_audit.get("selected_next_hypothesis")
        != "design_physical_gate_aligned_joint_weighted_standard_replay_correction"
        or outlier_audit.get("gate_b_passed") is not False
        or dataset_stats_file_sha256 != EXPECTED_DATASET_STATS_SHA256
    ):
        raise ValueError("T20.35x source identity or route drifted")
    metadata_files = (
        dataset_manifest.get("dataset", {}).get("metadata_tree", {}).get("files")
    )
    if not isinstance(metadata_files, list) or not any(
        row.get("path") == "meta/stats.json"
        and row.get("sha256") == EXPECTED_DATASET_STATS_SHA256
        for row in metadata_files
        if isinstance(row, dict)
    ):
        raise ValueError("T20.35x dataset stats provenance drifted")
    weighting = derive_joint_weighting(dataset_stats)
    coefficients = weighting["coefficient_by_dimension"]
    examples = build_correction_examples(trajectory_result, target_result, coefficients)
    sample_order = [
        index % CORRECTION_EXAMPLE_COUNT for index in range(OPTIMIZER_UPDATES)
    ]
    if [sample_order.count(index) for index in range(CORRECTION_EXAMPLE_COUNT)] != [
        10
    ] * CORRECTION_EXAMPLE_COUNT:
        raise ValueError("T20.35x correction schedule is not balanced")
    time_weights, baseline_by_step = _derive_time_weights(examples)
    standard_seeds = [
        STANDARD_REPLAY_SEED_BASE + update for update in range(OPTIMIZER_UPDATES)
    ]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35x",
            "scope": "one_bounded_expert_only_current_path_physical_gate_joint_weighted_correction_with_standard_replay",
            "t20_35t_training_spec_identity_sha256": source_spec["identity_sha256"],
            "t20_35t_run_identity_sha256": source_run["identity_sha256"],
            "t20_35t_result_identity_sha256": source_result["identity_sha256"],
            "t20_35v_spec_identity_sha256": trajectory_spec["identity_sha256"],
            "t20_35v_result_identity_sha256": trajectory_result["identity_sha256"],
            "t20_35o_result_identity_sha256": target_result["identity_sha256"],
            "t20_35w_audit_identity_sha256": outlier_audit["identity_sha256"],
            "dataset_manifest_identity_sha256": dataset_manifest["identity_sha256"],
            "dataset_stats_path": DATASET_STATS_PATH.as_posix(),
            "dataset_stats_file_sha256": dataset_stats_file_sha256,
            "source_checkpoint_identity_sha256": source_run[
                "checkpoint_identity_sha256"
            ],
            "source_checkpoint_tree": source_run["checkpoint_tree"],
            "source_checkpoint_mutated": False,
            "source_gate_baseline_objective_mean": source_spec[
                "source_gate_baseline_objective_mean"
            ],
            "source_checkpoint_standard_objective_mean": source_result[
                "final_standard_objective_mean"
            ],
            "dataset_action_chunk_sha256": trajectory_spec[
                "dataset_action_chunk_sha256"
            ],
            "normalized_padded_target_sha256": target_result[
                "normalized_padded_target_sha256"
            ],
            "lerobot_stack_identity_sha256": trajectory_spec[
                "lerobot_stack_identity_sha256"
            ],
            "sampler_source_sha256": trajectory_spec["sampler_source_sha256"],
            "model": copy.deepcopy(source_spec["model"]),
            "physical_joint_weighting": weighting,
            "correction_step_indices": list(CORRECTION_STEP_INDICES),
            "correction_examples": examples,
            "correction_examples_sha256": hashlib.sha256(
                canonical_json_bytes(examples)
            ).hexdigest(),
            "time_normalization": {
                "formula": "global_initial_joint_weighted_mean_divided_by_step_initial_joint_weighted_mean",
                "initial_joint_weighted_objective_by_step": baseline_by_step,
                "source_initial_joint_weighted_objective_mean": sum(baseline_by_step)
                / len(CORRECTION_STEP_INDICES),
                "weight_by_step": time_weights,
                "joint_weighted_correction_loss_coefficient": 1.0,
                "standard_replay_loss_coefficient": 1.0,
            },
            "campaign": {
                "optimizer": "AdamW",
                "optimizer_update_count": OPTIMIZER_UPDATES,
                "learning_rate": LEARNING_RATE,
                "weight_decay": 0.0,
                "betas": [0.9, 0.999],
                "epsilon": 1e-8,
                "amsgrad": False,
                "gradient_clip_norm": GRADIENT_CLIP_NORM,
                "training_seed": TRAINING_SEED,
                "correction_example_count": CORRECTION_EXAMPLE_COUNT,
                "sample_order": "seed_major_steps_0_through_9_repeated_10_times",
                "sample_index_by_update": sample_order,
                "standard_replay_seed_by_update": standard_seeds,
                "standard_replay_update_count": OPTIMIZER_UPDATES,
                "gradient_accumulation": "one_time_and_joint_weighted_correction_plus_one_unique_standard_replay_before_each_step",
                "network_mode": "offline_local_cache_only",
            },
            "evaluation": {
                "inference_seeds": list(INFERENCE_SEEDS),
                "active_noise_scale": 0.0,
                "padded_noise_scale": 1.0,
                "num_inference_steps": 10,
                "base_noise_sha256_by_seed": trajectory_spec[
                    "base_noise_sha256_by_seed"
                ],
                "source_decoded_action_sha256_by_seed": trajectory_spec[
                    "new_decoded_action_sha256_by_seed"
                ],
            },
            "gate": {
                "maximum_final_to_source_gate_baseline_objective_ratio": MAX_OBJECTIVE_RATIO,
                "target_maximum_final_to_baseline_correction_objective_ratio": MAX_OBJECTIVE_RATIO,
                "maximum_decoded_action_error_rad": MAX_ACTION_ERROR_RAD,
                "all_inference_seeds_must_pass": True,
            },
            "required_python_major_minor": [3, 12],
            "required_dependency_versions": copy.deepcopy(EXPECTED_DEPENDENCY_VERSIONS),
            "runtime_dependency_preflight_required": True,
            "one_run_permit_required": True,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
                "simulation_optimizer_training",
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


def verify_training_spec(
    payload: dict[str, Any],
    *,
    source_spec: dict[str, Any],
    source_run: dict[str, Any],
    source_result: dict[str, Any],
    trajectory_spec: dict[str, Any],
    trajectory_result: dict[str, Any],
    target_result: dict[str, Any],
    outlier_audit: dict[str, Any],
    dataset_manifest: dict[str, Any],
    dataset_stats: dict[str, Any],
    dataset_stats_file_sha256: str,
) -> None:
    verify_signed_payload(payload, label="T20.35x training spec")
    expected = build_training_spec(
        source_spec=source_spec,
        source_run=source_run,
        source_result=source_result,
        trajectory_spec=trajectory_spec,
        trajectory_result=trajectory_result,
        target_result=target_result,
        outlier_audit=outlier_audit,
        dataset_manifest=dataset_manifest,
        dataset_stats=dataset_stats,
        dataset_stats_file_sha256=dataset_stats_file_sha256,
    )
    archived_examples_hash = hashlib.sha256(
        canonical_json_bytes(payload.get("correction_examples"))
    ).hexdigest()
    if archived_examples_hash != payload.get("correction_examples_sha256"):
        raise ValueError("T20.35x archived correction example hash drifted")
    ignored_rebuild_keys = {"identity_sha256", "correction_examples_sha256"}
    archived = {
        key: value for key, value in payload.items() if key not in ignored_rebuild_keys
    }
    rebuilt = {
        key: value for key, value in expected.items() if key not in ignored_rebuild_keys
    }
    # Historical dataset reduction order can move derived float leaves by a
    # few ulps after an otherwise exact dependency restore. The signed archive
    # remains byte-exact; rebuild verification therefore uses the same bounded
    # tolerance approach as the T20.35x result verifier.
    if not _equal_with_float_tolerance(
        archived, rebuilt, absolute_tolerance=5e-14
    ):
        raise ValueError("T20.35x training spec drifted")


def build_runtime_preflight(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    python_major_minor: list[int],
    dependency_versions: dict[str, str],
    mps_available: bool,
    lerobot_stack_identity_sha256: str,
    checkpoint_tree_verified: bool,
    attempt_exists: bool,
    result_exists: bool,
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35x runtime-preflight spec")
    _sha(authority_identity, "runtime-preflight authority identity")
    _sha(lerobot_stack_identity_sha256, "runtime-preflight LeRobot stack identity")
    if (
        python_major_minor != spec["required_python_major_minor"]
        or dependency_versions != spec["required_dependency_versions"]
        or mps_available is not True
        or lerobot_stack_identity_sha256 != spec["lerobot_stack_identity_sha256"]
        or checkpoint_tree_verified is not True
        or attempt_exists is not False
        or result_exists is not False
    ):
        raise ValueError("T20.35x runtime dependency preflight failed closed")
    return sign_payload(
        {
            "schema_version": RUNTIME_PREFLIGHT_SCHEMA_VERSION,
            "task_id": "T20.35x",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "checkpoint_identity_sha256": spec["source_checkpoint_identity_sha256"],
            "lerobot_stack_identity_sha256": lerobot_stack_identity_sha256,
            "python_major_minor": python_major_minor,
            "dependency_versions": dependency_versions,
            "mps_available": mps_available,
            "checkpoint_tree_verified": checkpoint_tree_verified,
            "attempt_exists": attempt_exists,
            "result_exists": result_exists,
            "checkpoint_tensor_read": False,
            "model_loaded": False,
            "model_inference": False,
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
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35x runtime preflight")
    expected = build_runtime_preflight(
        spec=spec,
        authority_identity=authority_identity,
        python_major_minor=payload.get("python_major_minor"),
        dependency_versions=payload.get("dependency_versions"),
        mps_available=payload.get("mps_available"),
        lerobot_stack_identity_sha256=payload.get("lerobot_stack_identity_sha256"),
        checkpoint_tree_verified=payload.get("checkpoint_tree_verified"),
        attempt_exists=payload.get("attempt_exists"),
        result_exists=payload.get("result_exists"),
    )
    if payload != expected:
        raise ValueError("T20.35x runtime preflight drifted")


def build_training_permit(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> dict[str, Any]:
    verify_runtime_preflight(
        runtime_preflight, spec=spec, authority_identity=authority_identity
    )
    return sign_payload(
        {
            "schema_version": TRAINING_PERMIT_SCHEMA_VERSION,
            "task_id": "T20.35x",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime_preflight["identity_sha256"],
            "source_checkpoint_identity_sha256": spec[
                "source_checkpoint_identity_sha256"
            ],
            "authorized_attempt_count": 1,
            "authorized_actions": list(spec["authorized_actions"]),
            "simulation_only": True,
            "valid_until": "2026-07-15T23:27:47-05:00",
            "checkpoint_tensor_read": False,
            "model_loaded": False,
            "model_inference": False,
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


def verify_training_permit(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    authority_identity: str,
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.35x training permit")
    expected = build_training_permit(
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.35x training permit drifted")


def verify_run(
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35x run")
    _sha(authority_identity, "authority identity")
    campaign = spec["campaign"]
    if (
        payload.get("schema_version") != RUN_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35x"
        or payload.get("training_spec_identity_sha256") != spec["identity_sha256"]
        or payload.get("authority_decision_identity_sha256") != authority_identity
        or payload.get("runtime_preflight_identity_sha256")
        != EXPECTED_RUNTIME_PREFLIGHT_IDENTITY
        or payload.get("training_permit_identity_sha256")
        != EXPECTED_TRAINING_PERMIT_IDENTITY
        or payload.get("source_checkpoint_identity_sha256")
        != spec["source_checkpoint_identity_sha256"]
        or payload.get("optimizer_update_count") != OPTIMIZER_UPDATES
        or payload.get("learning_rate") != LEARNING_RATE
        or payload.get("optimizer_config")
        != {
            "optimizer": campaign["optimizer"],
            "betas": campaign["betas"],
            "epsilon": campaign["epsilon"],
            "weight_decay": campaign["weight_decay"],
            "amsgrad": campaign["amsgrad"],
            "gradient_clip_norm": campaign["gradient_clip_norm"],
        }
        or payload.get("correction_example_count") != CORRECTION_EXAMPLE_COUNT
        or payload.get("sample_index_by_update") != campaign["sample_index_by_update"]
        or payload.get("example_use_count") != [10] * CORRECTION_EXAMPLE_COUNT
        or payload.get("joint_weight_coefficient_by_dimension")
        != spec["physical_joint_weighting"]["coefficient_by_dimension"]
        or payload.get("time_normalization_weight_by_step")
        != spec["time_normalization"]["weight_by_step"]
        or payload.get("standard_replay_seed_by_update")
        != campaign["standard_replay_seed_by_update"]
        or payload.get("standard_replay_update_count") != OPTIMIZER_UPDATES
        or payload.get("adaptation_mode") != ADAPTATION_MODE
        or payload.get("trainable_prefixes") != list(TRAINABLE_PREFIXES)
        or payload.get("paligemma_trainable_parameter_count") != 0
        or payload.get("source_checkpoint_tree_unchanged") is not True
        or payload.get("optimizer_training") is not True
    ):
        raise ValueError("T20.35x run campaign or lineage drifted")
    for field in (
        "authority_decision_identity_sha256",
        "runtime_preflight_identity_sha256",
        "training_permit_identity_sha256",
        "attempt_identity_sha256",
        "source_checkpoint_identity_sha256",
        "checkpoint_identity_sha256",
        "trainable_parameter_names_sha256",
    ):
        _sha(payload.get(field), field)
    update_fields = (
        "per_update_objective",
        "per_update_raw_correction_objective",
        "per_update_joint_weighted_correction_objective",
        "per_update_time_joint_weighted_correction_objective",
        "per_update_standard_replay_objective",
        "gradient_norms_before_clip",
    )
    example_fields = (
        "baseline_raw_objective_by_example",
        "final_raw_objective_by_example",
        "baseline_joint_weighted_objective_by_example",
        "final_joint_weighted_objective_by_example",
        "baseline_time_joint_weighted_objective_by_example",
        "final_time_joint_weighted_objective_by_example",
    )
    seed_fields = (
        "baseline_standard_objective_by_seed",
        "final_standard_objective_by_seed",
    )
    traces: dict[str, list[float]] = {}
    for field, count in (
        *((field, OPTIMIZER_UPDATES) for field in update_fields),
        *((field, CORRECTION_EXAMPLE_COUNT) for field in example_fields),
        *((field, len(INFERENCE_SEEDS)) for field in seed_fields),
    ):
        values = payload.get(field)
        if not isinstance(values, list) or len(values) != count:
            raise ValueError("T20.35x objective or gradient trace is incomplete")
        traces[field] = [_finite(value, field) for value in values]
    mean_fields = (
        "baseline_raw_correction_objective_mean",
        "final_raw_correction_objective_mean",
        "baseline_joint_weighted_correction_objective_mean",
        "final_joint_weighted_correction_objective_mean",
        "baseline_time_joint_weighted_correction_objective_mean",
        "final_time_joint_weighted_correction_objective_mean",
        "baseline_standard_objective_mean",
        "final_standard_objective_mean",
    )
    for field in mean_fields:
        if _finite(payload.get(field), field) <= 0.0:
            raise ValueError("T20.35x objective means must be positive")
    weights = spec["time_normalization"]["weight_by_step"]
    for update, example_index in enumerate(campaign["sample_index_by_update"]):
        expected_time_joint = (
            traces["per_update_joint_weighted_correction_objective"][update]
            * weights[example_index % 10]
        )
        if (
            abs(
                traces["per_update_time_joint_weighted_correction_objective"][update]
                - expected_time_joint
            )
            > 1e-6
            or abs(
                traces["per_update_objective"][update]
                - traces["per_update_time_joint_weighted_correction_objective"][update]
                - traces["per_update_standard_replay_objective"][update]
            )
            > 1e-6
        ):
            raise ValueError("T20.35x paired update objective drifted")
    for index in range(CORRECTION_EXAMPLE_COUNT):
        weight = weights[index % 10]
        if (
            abs(
                traces["baseline_time_joint_weighted_objective_by_example"][index]
                - traces["baseline_joint_weighted_objective_by_example"][index] * weight
            )
            > 1e-6
            or abs(
                traces["final_time_joint_weighted_objective_by_example"][index]
                - traces["final_joint_weighted_objective_by_example"][index] * weight
            )
            > 1e-6
            or abs(
                traces["baseline_raw_objective_by_example"][index]
                - spec["correction_examples"][index][
                    "baseline_raw_correction_objective"
                ]
            )
            > 1e-5
            or abs(
                traces["baseline_joint_weighted_objective_by_example"][index]
                - spec["correction_examples"][index][
                    "baseline_joint_weighted_correction_objective"
                ]
            )
            > 1e-5
        ):
            raise ValueError("T20.35x weighted correction evidence drifted")
    mean_sources = {
        "baseline_raw_correction_objective_mean": "baseline_raw_objective_by_example",
        "final_raw_correction_objective_mean": "final_raw_objective_by_example",
        "baseline_joint_weighted_correction_objective_mean": "baseline_joint_weighted_objective_by_example",
        "final_joint_weighted_correction_objective_mean": "final_joint_weighted_objective_by_example",
        "baseline_time_joint_weighted_correction_objective_mean": "baseline_time_joint_weighted_objective_by_example",
        "final_time_joint_weighted_correction_objective_mean": "final_time_joint_weighted_objective_by_example",
        "baseline_standard_objective_mean": "baseline_standard_objective_by_seed",
        "final_standard_objective_mean": "final_standard_objective_by_seed",
    }
    for mean_field, trace_field in mean_sources.items():
        if (
            abs(
                sum(traces[trace_field]) / len(traces[trace_field])
                - payload[mean_field]
            )
            > 1e-12
        ):
            raise ValueError("T20.35x correction objective mean drifted")
    if (
        abs(
            payload["baseline_standard_objective_mean"]
            - spec["source_checkpoint_standard_objective_mean"]
        )
        > 1e-6
    ):
        raise ValueError("T20.35x source checkpoint standard objective drifted")
    for field in ("trainable_parameter_count", "paligemma_parameter_count"):
        if (
            isinstance(payload.get(field), bool)
            or not isinstance(payload.get(field), int)
            or payload[field] <= 0
        ):
            raise ValueError(f"T20.35x {field} is invalid")
    chunks = payload.get("decoded_action_chunks")
    if not isinstance(chunks, list) or [
        row.get("inference_seed") for row in chunks if isinstance(row, dict)
    ] != list(INFERENCE_SEEDS):
        raise ValueError("T20.35x decoded seed coverage drifted")
    for row in chunks:
        _sha(row.get("decoded_action_chunk_sha256"), "decoded action hash")
        if (
            _finite(row.get("mean_absolute_error_rad"), "decoded mean error") < 0.0
            or _finite(row.get("maximum_absolute_error_rad"), "decoded maximum error")
            < 0.0
        ):
            raise ValueError("T20.35x decoded action errors must be nonnegative")
    tree = payload.get("checkpoint_tree")
    if not isinstance(tree, list) or len(tree) < 2:
        raise ValueError("T20.35x checkpoint tree is incomplete")
    if (
        hashlib.sha256(canonical_json_bytes(tree)).hexdigest()
        != payload["checkpoint_identity_sha256"]
    ):
        raise ValueError("T20.35x checkpoint identity drifted")
    required_false = (
        "checkpoint_mutated",
        "dataset_mutated",
        "statistics_changed",
        "sampler_mutated",
        "closed_loop_rollout",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if any(payload.get(field) is not False for field in required_false):
        raise ValueError("T20.35x run authority fields drifted")


def build_result(
    *, spec: dict[str, Any], authority_identity: str, run: dict[str, Any]
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35x result spec")
    verify_run(run, spec=spec, authority_identity=authority_identity)
    objectives = {}
    for name in ("raw", "joint_weighted", "time_joint_weighted"):
        baseline = _finite(
            run[f"baseline_{name}_correction_objective_mean"],
            f"baseline {name} correction objective",
        )
        final = _finite(
            run[f"final_{name}_correction_objective_mean"],
            f"final {name} correction objective",
        )
        objectives[name] = {
            "baseline": baseline,
            "final": final,
            "ratio": _finite(final / baseline, f"{name} correction objective ratio"),
        }
    standard_ratio = _finite(
        run["final_standard_objective_mean"]
        / spec["source_gate_baseline_objective_mean"],
        "standard objective ratio",
    )
    action_pass = all(
        row["maximum_absolute_error_rad"] <= MAX_ACTION_ERROR_RAD
        for row in run["decoded_action_chunks"]
    )
    correction_objective_pass = all(
        row["ratio"] <= MAX_OBJECTIVE_RATIO for row in objectives.values()
    )
    objective_pass = standard_ratio <= MAX_OBJECTIVE_RATIO
    gate_b_passed = action_pass and objective_pass
    if gate_b_passed:
        route = "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction"
    elif objective_pass and correction_objective_pass:
        route = (
            "joint_weighted_objectives_pass_action_fail_route_post_training_path_audit"
        )
    elif objective_pass:
        route = "standard_objective_pass_joint_weighted_correction_fail_route_gradient_compatibility_audit"
    elif action_pass:
        route = "action_pass_standard_objective_fail_route_objective_floor_audit"
    else:
        route = "joint_weighted_correction_and_gate_b_fail_route_gradient_compatibility_audit"
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35x",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "run_identity_sha256": run["identity_sha256"],
            "t20_35v_result_identity_sha256": spec["t20_35v_result_identity_sha256"],
            "t20_35o_result_identity_sha256": spec["t20_35o_result_identity_sha256"],
            "t20_35w_audit_identity_sha256": spec["t20_35w_audit_identity_sha256"],
            "source_checkpoint_identity_sha256": spec[
                "source_checkpoint_identity_sha256"
            ],
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "correction_example_count": CORRECTION_EXAMPLE_COUNT,
            "baseline_raw_correction_objective_mean": objectives["raw"]["baseline"],
            "final_raw_correction_objective_mean": objectives["raw"]["final"],
            "final_to_baseline_raw_correction_objective_ratio": objectives["raw"][
                "ratio"
            ],
            "baseline_joint_weighted_correction_objective_mean": objectives[
                "joint_weighted"
            ]["baseline"],
            "final_joint_weighted_correction_objective_mean": objectives[
                "joint_weighted"
            ]["final"],
            "final_to_baseline_joint_weighted_correction_objective_ratio": objectives[
                "joint_weighted"
            ]["ratio"],
            "baseline_time_joint_weighted_correction_objective_mean": objectives[
                "time_joint_weighted"
            ]["baseline"],
            "final_time_joint_weighted_correction_objective_mean": objectives[
                "time_joint_weighted"
            ]["final"],
            "final_to_baseline_time_joint_weighted_correction_objective_ratio": objectives[
                "time_joint_weighted"
            ]["ratio"],
            "baseline_standard_objective_mean": run["baseline_standard_objective_mean"],
            "final_standard_objective_mean": run["final_standard_objective_mean"],
            "final_to_source_gate_baseline_objective_ratio": standard_ratio,
            "maximum_allowed_objective_ratio": MAX_OBJECTIVE_RATIO,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "decoded_action_chunks": run["decoded_action_chunks"],
            "all_correction_objective_ratios_within_target": correction_objective_pass,
            "objective_ratio_within_threshold": objective_pass,
            "all_decoded_chunks_within_threshold": action_pass,
            "gate_b_passed": gate_b_passed,
            "selected_next_hypothesis": route,
            "optimizer_training": True,
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
    payload: dict[str, Any], *, spec: dict[str, Any], run: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.35x result")
    expected = build_result(
        spec=spec,
        authority_identity=payload.get("authority_decision_identity_sha256"),
        run=run,
    )
    archived = {
        key: value for key, value in payload.items() if key != "identity_sha256"
    }
    rebuilt = {
        key: value for key, value in expected.items() if key != "identity_sha256"
    }
    if not _equal_with_float_tolerance(archived, rebuilt, absolute_tolerance=1e-15):
        raise ValueError("T20.35x result drifted")


def load_source_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    trajectory_sources = load_t20_35v_sources(repo_root=root)
    trajectory_spec = trajectory_sources["trajectory_spec"]
    audit_sources = load_t20_35w_sources(repo_root=root)
    trajectory_result = load_strict_json(root / T20_35V_RESULT_PATH)
    outlier_audit = load_strict_json(root / T20_35W_AUDIT_PATH)
    verify_t20_35w_audit(outlier_audit, **audit_sources)
    if trajectory_result != audit_sources["trajectory_result"]:
        raise ValueError("T20.35x V trajectory source drifted")
    dataset_manifest = load_strict_json(root / DATASET_MANIFEST_PATH)
    verify_signed_payload(dataset_manifest, label="T20.35x dataset manifest")
    stats_path = root / DATASET_STATS_PATH
    stats_bytes = stats_path.read_bytes()
    dataset_stats_file_sha256 = hashlib.sha256(stats_bytes).hexdigest()
    dataset_stats = load_strict_json(stats_path)
    return {
        **trajectory_sources,
        "base_source_run": trajectory_sources["source_run"],
        "source_spec": trajectory_sources["training_spec"],
        "source_run": trajectory_sources["training_run"],
        "source_result": trajectory_sources["training_result"],
        "trajectory_spec": trajectory_spec,
        "trajectory_result": trajectory_result,
        "target_result": trajectory_sources["target_result"],
        "outlier_audit": outlier_audit,
        "dataset_manifest": dataset_manifest,
        "dataset_stats": dataset_stats,
        "dataset_stats_file_sha256": dataset_stats_file_sha256,
    }


def write_training_spec(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    spec = build_training_spec(
        source_spec=sources["source_spec"],
        source_run=sources["source_run"],
        source_result=sources["source_result"],
        trajectory_spec=sources["trajectory_spec"],
        trajectory_result=sources["trajectory_result"],
        target_result=sources["target_result"],
        outlier_audit=sources["outlier_audit"],
        dataset_manifest=sources["dataset_manifest"],
        dataset_stats=sources["dataset_stats"],
        dataset_stats_file_sha256=sources["dataset_stats_file_sha256"],
    )
    dump_canonical_json(root / SPEC_PATH, spec)
    return spec


def verify_training_spec_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    archived = load_strict_json(root / SPEC_PATH)
    verify_training_spec(
        archived,
        source_spec=sources["source_spec"],
        source_run=sources["source_run"],
        source_result=sources["source_result"],
        trajectory_spec=sources["trajectory_spec"],
        trajectory_result=sources["trajectory_result"],
        target_result=sources["target_result"],
        outlier_audit=sources["outlier_audit"],
        dataset_manifest=sources["dataset_manifest"],
        dataset_stats=sources["dataset_stats"],
        dataset_stats_file_sha256=sources["dataset_stats_file_sha256"],
    )
    return archived


def _finite_matrix(
    value: Any, *, rows: int, columns: int, label: str
) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != rows:
        raise ValueError(f"T20.35x {label} row count drifted")
    matrix = []
    for row in value:
        if not isinstance(row, list) or len(row) != columns:
            raise ValueError(f"T20.35x {label} column count drifted")
        matrix.append([_finite(item, label) for item in row])
    return matrix


def derive_joint_weighting(dataset_stats: dict[str, Any]) -> dict[str, Any]:
    action = dataset_stats.get("action")
    if not isinstance(action, dict):
        raise ValueError("T20.35x dataset action statistics are absent")
    standard_deviation = action.get("std")
    if not isinstance(standard_deviation, list) or len(standard_deviation) != len(
        JOINT_NAMES
    ):
        raise ValueError("T20.35x action standard-deviation coverage drifted")
    standard_deviation = [
        _finite(value, "action standard deviation") for value in standard_deviation
    ]
    if any(value <= 0.0 for value in standard_deviation):
        raise ValueError("T20.35x action standard deviations must be positive")
    gripper_span = GRIPPER_RANGE_RAD[1] - GRIPPER_RANGE_RAD[0]
    physical_jacobian = [
        _finite(value * math.pi / 180.0, "body physical Jacobian")
        for value in standard_deviation[:5]
    ] + [
        _finite(
            standard_deviation[5] * gripper_span / 100.0,
            "gripper physical Jacobian",
        )
    ]
    squared = [
        _finite(value * value, "squared physical Jacobian")
        for value in physical_jacobian
    ]
    mean_squared = _finite(sum(squared) / len(squared), "mean squared Jacobian")
    active_coefficients = [
        _finite(value / mean_squared, "active joint coefficient") for value in squared
    ]
    if abs(sum(active_coefficients) / len(active_coefficients) - 1.0) > 1e-15:
        raise ValueError("T20.35x active joint weights failed mean-one normalization")
    coefficients = [
        *active_coefficients,
        *([1.0] * (MAXIMUM_ACTION_DIMENSIONS - ACTIVE_ACTION_DIMENSIONS)),
    ]
    contract = coordinate_contract()
    return {
        "formula": "square(normalized_unit_to_physical_radian_jacobian)_then_normalize_active_mean_to_one",
        "active_joint_names": list(JOINT_NAMES),
        "dataset_action_normalization_mode": "MEAN_STD",
        "dataset_action_standard_deviation_lerobot_units": standard_deviation,
        "dataset_action_standard_deviation_sha256": hashlib.sha256(
            canonical_json_bytes(standard_deviation)
        ).hexdigest(),
        "coordinate_contract": contract,
        "coordinate_contract_sha256": hashlib.sha256(
            canonical_json_bytes(contract)
        ).hexdigest(),
        "normalized_unit_to_physical_radian_jacobian": physical_jacobian,
        "active_joint_coefficient": active_coefficients,
        "active_joint_coefficient_mean": sum(active_coefficients)
        / len(active_coefficients),
        "padded_dimension_coefficient": 1.0,
        "coefficient_by_dimension": coefficients,
    }


def _derive_time_weights(
    examples: list[dict[str, Any]],
) -> tuple[list[float], list[float]]:
    if len(examples) != CORRECTION_EXAMPLE_COUNT or [
        row.get("correction_example_index") for row in examples
    ] != list(range(CORRECTION_EXAMPLE_COUNT)):
        raise ValueError("T20.35x correction-example coverage drifted")
    means = []
    for step_index in CORRECTION_STEP_INDICES:
        values = [
            _finite(
                row.get("baseline_joint_weighted_correction_objective"),
                "step joint-weighted baseline objective",
            )
            for row in examples
            if row.get("step_index") == step_index
        ]
        if len(values) != len(INFERENCE_SEEDS):
            raise ValueError("T20.35x step objective coverage drifted")
        means.append(sum(values) / len(values))
    if any(value <= 0.0 for value in means):
        raise ValueError("T20.35x step baseline objective must be positive")
    global_mean = sum(means) / len(means)
    weights = [
        _finite(global_mean / value, "time normalization weight") for value in means
    ]
    if any(
        abs(weight * value - global_mean) > 1e-12
        for weight, value in zip(weights, means, strict=True)
    ):
        raise ValueError("T20.35x time normalization failed exact balance")
    return weights, means


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.35x {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.35x {label} must be finite")
    return number


def _matrix_sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35x {label} must be lowercase SHA-256")
