"""Exact-state full-path flow-consistency correction for T20.35r."""

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
from scenesmith.robot_lab.t20_35o_flow_trajectory_consistency_audit import (
    ACTIVE_ACTION_DIMENSIONS,
    MAXIMUM_ACTION_DIMENSIONS,
)
from scenesmith.robot_lab.t20_35q_post_training_trajectory_audit import (
    ATTEMPT_PATH as T20_35Q_ATTEMPT_PATH,
    RESULT_PATH as T20_35Q_RESULT_PATH,
    load_and_verify_evaluation_files as load_t20_35q_sources,
    verify_attempt_marker as verify_t20_35q_attempt,
    verify_result as verify_t20_35q_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(
    "configurations/robot_lab/t20_35r_full_path_flow_consistency_training_spec.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_35r_full_path_flow_consistency_result.json"
)
SCHEMA_VERSION = "scenesmith.t20_35r_full_path_flow_consistency_training_spec.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_35r_full_path_flow_consistency_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_35r_full_path_flow_consistency_result.v1"
EXPECTED_T20_35P_SPEC_IDENTITY = (
    "fd4f75f68b9031d0089b402d3fda6ec8b467c3e8ef177f8d02aec418045a6476"
)
EXPECTED_T20_35P_RUN_IDENTITY = (
    "283c57453474863a7154c4a71adfac2d80c2196d4c47ad4bc04f900e81a4d7f6"
)
EXPECTED_T20_35P_RESULT_IDENTITY = (
    "cde1347f4afcb878a5cc0ebada2a14a197ba82ba6b45e7f40a574d841c64166b"
)
EXPECTED_T20_35Q_SPEC_IDENTITY = (
    "fdb2fe3e4cbc70a87d09d297ded8fa64fc8d6caa4b94818af435d94b0945f05d"
)
EXPECTED_T20_35Q_RESULT_IDENTITY = (
    "6ba4954cd850abe69cf0de838740dab3b976ca277cb08360ec2e29ec0011f40b"
)
EXPECTED_T20_35O_RESULT_IDENTITY = (
    "5c5b41b99d83b1e5116195bab551277d3b65126066717823342030b23391a582"
)
CORRECTION_STEP_INDICES = tuple(range(10))
CORRECTION_EXAMPLE_COUNT = len(INFERENCE_SEEDS) * len(CORRECTION_STEP_INDICES)
OPTIMIZER_UPDATES = 500
LEARNING_RATE = 2.5e-5
TRAINING_SEED = 20260717
GRADIENT_CLIP_NORM = 1.0
RECONSTRUCTION_TOLERANCE = 2e-12


def build_correction_examples(
    trajectory_result: dict[str, Any],
    target_result: dict[str, Any],
) -> list[dict[str, Any]]:
    verify_signed_payload(trajectory_result, label="T20.35r trajectory source")
    verify_signed_payload(target_result, label="T20.35r normalized-target source")
    if (
        trajectory_result.get("identity_sha256")
        != EXPECTED_T20_35Q_RESULT_IDENTITY
        or trajectory_result.get("path_interference_classification")
        != "early_mid_path_interference"
        or trajectory_result.get("selected_next_hypothesis")
        != "design_full_path_self_consistency_correction"
        or trajectory_result.get("gate_b_passed") is not False
        or target_result.get("identity_sha256")
        != EXPECTED_T20_35O_RESULT_IDENTITY
        or trajectory_result.get("t20_35o_result_identity_sha256")
        != target_result.get("identity_sha256")
    ):
        raise ValueError("T20.35r trajectory route drifted")
    target = _finite_matrix(
        target_result.get("normalized_padded_target"),
        rows=50,
        columns=MAXIMUM_ACTION_DIMENSIONS,
        label="normalized padded target",
    )
    if _matrix_sha(target) != target_result.get(
        "normalized_padded_target_sha256"
    ):
        raise ValueError("T20.35r normalized target hash drifted")
    rows = trajectory_result.get("new_trajectory_evaluations")
    if (
        not isinstance(rows, list)
        or len(rows) != len(INFERENCE_SEEDS)
        or [row.get("inference_seed") for row in rows if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35r trajectory seed coverage drifted")
    examples: list[dict[str, Any]] = []
    for row in rows:
        steps = row.get("steps")
        if not isinstance(steps, list) or len(steps) != 10:
            raise ValueError("T20.35r trajectory step coverage drifted")
        for step_index in CORRECTION_STEP_INDICES:
            step = steps[step_index]
            if step.get("step_index") != step_index:
                raise ValueError("T20.35r correction step order drifted")
            time = _finite(step.get("time"), "correction time")
            expected_time = 1.0 - step_index / 10
            if time != expected_time or time <= 0.0:
                raise ValueError("T20.35r correction time drifted")
            state = _finite_matrix(
                step.get("state"),
                rows=50,
                columns=MAXIMUM_ACTION_DIMENSIONS,
                label="correction state",
            )
            if _matrix_sha(state) != step.get("state_sha256"):
                raise ValueError("T20.35r correction state hash drifted")
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
                [derived_noise[t][j] - target[t][j] for j in range(MAXIMUM_ACTION_DIMENSIONS)]
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
                raise ValueError("T20.35r exact-state reconstruction exceeded tolerance")
            examples.append(
                {
                    "correction_example_index": len(examples),
                    "inference_seed": row["inference_seed"],
                    "step_index": step_index,
                    "time": time,
                    "state_sha256": step["state_sha256"],
                    "target_velocity_sha256": _matrix_sha(reference),
                    "derived_noise_sha256": _matrix_sha(derived_noise),
                    "state_reconstruction_maximum_error": state_error,
                    "velocity_reconstruction_maximum_error": velocity_error,
                }
            )
    if len(examples) != CORRECTION_EXAMPLE_COUNT:
        raise ValueError("T20.35r correction example count drifted")
    return examples


def materialize_correction_tensors(
    trajectory_result: dict[str, Any],
    target_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return verified raw tensors for the reviewed runner."""
    manifest = build_correction_examples(trajectory_result, target_result)
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
            raise ValueError("T20.35r materialized correction noise drifted")
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
) -> dict[str, Any]:
    for label, payload in (
        ("source spec", source_spec),
        ("source run", source_run),
        ("source result", source_result),
        ("trajectory spec", trajectory_spec),
        ("trajectory result", trajectory_result),
        ("target result", target_result),
    ):
        verify_signed_payload(payload, label=f"T20.35r {label}")
    if (
        source_spec.get("identity_sha256") != EXPECTED_T20_35P_SPEC_IDENTITY
        or source_spec.get("model", {}).get("adaptation_mode") != ADAPTATION_MODE
        or source_run.get("identity_sha256") != EXPECTED_T20_35P_RUN_IDENTITY
        or source_result.get("identity_sha256") != EXPECTED_T20_35P_RESULT_IDENTITY
        or source_result.get("objective_ratio_within_threshold") is not True
        or source_result.get("gate_b_passed") is not False
        or source_result.get("run_identity_sha256") != source_run.get("identity_sha256")
        or trajectory_spec.get("identity_sha256") != EXPECTED_T20_35Q_SPEC_IDENTITY
        or trajectory_result.get("identity_sha256") != EXPECTED_T20_35Q_RESULT_IDENTITY
        or trajectory_result.get("evaluation_spec_identity_sha256")
        != trajectory_spec.get("identity_sha256")
        or trajectory_spec.get("checkpoint_identity_sha256")
        != source_run.get("checkpoint_identity_sha256")
        or target_result.get("identity_sha256") != EXPECTED_T20_35O_RESULT_IDENTITY
    ):
        raise ValueError("T20.35r source identity or route drifted")
    examples = build_correction_examples(trajectory_result, target_result)
    sample_order = [index % CORRECTION_EXAMPLE_COUNT for index in range(OPTIMIZER_UPDATES)]
    if [sample_order.count(index) for index in range(CORRECTION_EXAMPLE_COUNT)] != [
        10
    ] * CORRECTION_EXAMPLE_COUNT:
        raise ValueError("T20.35r correction schedule is not balanced")
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35r",
            "scope": "one_bounded_expert_only_exact_full_path_state_flow_consistency_correction",
            "t20_35p_training_spec_identity_sha256": source_spec["identity_sha256"],
            "t20_35p_run_identity_sha256": source_run["identity_sha256"],
            "t20_35p_result_identity_sha256": source_result["identity_sha256"],
            "t20_35q_spec_identity_sha256": trajectory_spec["identity_sha256"],
            "t20_35q_result_identity_sha256": trajectory_result["identity_sha256"],
            "t20_35o_result_identity_sha256": target_result["identity_sha256"],
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
            "correction_step_indices": list(CORRECTION_STEP_INDICES),
            "correction_examples": examples,
            "correction_examples_sha256": hashlib.sha256(
                canonical_json_bytes(examples)
            ).hexdigest(),
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
) -> None:
    verify_signed_payload(payload, label="T20.35r training spec")
    expected = build_training_spec(
        source_spec=source_spec,
        source_run=source_run,
        source_result=source_result,
        trajectory_spec=trajectory_spec,
        trajectory_result=trajectory_result,
        target_result=target_result,
    )
    if payload != expected:
        raise ValueError("T20.35r training spec drifted")


def verify_run(
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35r run")
    _sha(authority_identity, "authority identity")
    campaign = spec["campaign"]
    if (
        payload.get("schema_version") != RUN_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35r"
        or payload.get("training_spec_identity_sha256") != spec["identity_sha256"]
        or payload.get("authority_decision_identity_sha256") != authority_identity
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
        or payload.get("sample_index_by_update")
        != campaign["sample_index_by_update"]
        or payload.get("example_use_count") != [10] * CORRECTION_EXAMPLE_COUNT
        or payload.get("adaptation_mode") != ADAPTATION_MODE
        or payload.get("trainable_prefixes") != list(TRAINABLE_PREFIXES)
        or payload.get("paligemma_trainable_parameter_count") != 0
        or payload.get("source_checkpoint_tree_unchanged") is not True
        or payload.get("optimizer_training") is not True
    ):
        raise ValueError("T20.35r run campaign or lineage drifted")
    for field in (
        "authority_decision_identity_sha256",
        "attempt_identity_sha256",
        "source_checkpoint_identity_sha256",
        "checkpoint_identity_sha256",
        "trainable_parameter_names_sha256",
    ):
        _sha(payload.get(field), field)
    losses = payload.get("per_update_objective")
    gradients = payload.get("gradient_norms_before_clip")
    baseline_by_example = payload.get("baseline_objective_by_example")
    final_by_example = payload.get("final_objective_by_example")
    baseline_standard_by_seed = payload.get("baseline_standard_objective_by_seed")
    final_standard_by_seed = payload.get("final_standard_objective_by_seed")
    if (
        not isinstance(losses, list)
        or len(losses) != OPTIMIZER_UPDATES
        or not isinstance(gradients, list)
        or len(gradients) != OPTIMIZER_UPDATES
        or not isinstance(baseline_by_example, list)
        or len(baseline_by_example) != CORRECTION_EXAMPLE_COUNT
        or not isinstance(final_by_example, list)
        or len(final_by_example) != CORRECTION_EXAMPLE_COUNT
        or not isinstance(baseline_standard_by_seed, list)
        or len(baseline_standard_by_seed) != len(INFERENCE_SEEDS)
        or not isinstance(final_standard_by_seed, list)
        or len(final_standard_by_seed) != len(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35r objective or gradient trace is incomplete")
    for value in (
        payload.get("baseline_correction_objective_mean"),
        payload.get("final_correction_objective_mean"),
        *losses,
        *gradients,
        *baseline_by_example,
        *final_by_example,
        *baseline_standard_by_seed,
        *final_standard_by_seed,
    ):
        _finite(value, "run numeric evidence")
    if payload["baseline_correction_objective_mean"] <= 0.0:
        raise ValueError("T20.35r baseline correction objective must be positive")
    if (
        abs(
            sum(baseline_by_example) / CORRECTION_EXAMPLE_COUNT
            - payload["baseline_correction_objective_mean"]
        )
        > 1e-12
        or abs(
            sum(final_by_example) / CORRECTION_EXAMPLE_COUNT
            - payload["final_correction_objective_mean"]
        )
        > 1e-12
        or abs(
            sum(baseline_standard_by_seed) / len(INFERENCE_SEEDS)
            - payload["baseline_standard_objective_mean"]
        )
        > 1e-12
        or abs(
            sum(final_standard_by_seed) / len(INFERENCE_SEEDS)
            - payload["final_standard_objective_mean"]
        )
        > 1e-12
    ):
        raise ValueError("T20.35r correction objective mean drifted")
    if (
        abs(
            payload["baseline_standard_objective_mean"]
            - spec["source_checkpoint_standard_objective_mean"]
        )
        > 1e-6
    ):
        raise ValueError("T20.35r source checkpoint standard objective drifted")
    for field in ("trainable_parameter_count", "paligemma_parameter_count"):
        if (
            isinstance(payload.get(field), bool)
            or not isinstance(payload.get(field), int)
            or payload[field] <= 0
        ):
            raise ValueError(f"T20.35r {field} is invalid")
    chunks = payload.get("decoded_action_chunks")
    if (
        not isinstance(chunks, list)
        or [row.get("inference_seed") for row in chunks if isinstance(row, dict)]
        != list(INFERENCE_SEEDS)
    ):
        raise ValueError("T20.35r decoded seed coverage drifted")
    for row in chunks:
        _sha(row.get("decoded_action_chunk_sha256"), "decoded action hash")
        _finite(row.get("mean_absolute_error_rad"), "decoded mean error")
        _finite(row.get("maximum_absolute_error_rad"), "decoded maximum error")
    tree = payload.get("checkpoint_tree")
    if not isinstance(tree, list) or len(tree) < 2:
        raise ValueError("T20.35r checkpoint tree is incomplete")
    if hashlib.sha256(canonical_json_bytes(tree)).hexdigest() != payload[
        "checkpoint_identity_sha256"
    ]:
        raise ValueError("T20.35r checkpoint identity drifted")
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
        raise ValueError("T20.35r run authority fields drifted")


def build_result(
    *, spec: dict[str, Any], authority_identity: str, run: dict[str, Any]
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.35r result spec")
    verify_run(run, spec=spec, authority_identity=authority_identity)
    baseline = _finite(
        run["baseline_correction_objective_mean"], "baseline correction objective"
    )
    final = _finite(
        run["final_correction_objective_mean"], "final correction objective"
    )
    ratio = final / baseline
    standard_ratio = (
        run["final_standard_objective_mean"]
        / spec["source_gate_baseline_objective_mean"]
    )
    action_pass = all(
        row["maximum_absolute_error_rad"] <= MAX_ACTION_ERROR_RAD
        for row in run["decoded_action_chunks"]
    )
    correction_objective_pass = ratio <= MAX_OBJECTIVE_RATIO
    objective_pass = standard_ratio <= MAX_OBJECTIVE_RATIO
    gate_b_passed = action_pass and objective_pass
    if gate_b_passed:
        route = "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction"
    elif objective_pass and correction_objective_pass:
        route = "full_path_objective_pass_action_fail_route_iterated_self_consistency_audit"
    elif objective_pass:
        route = "standard_objective_pass_correction_objective_fail_route_correction_attainability_audit"
    elif action_pass:
        route = "action_pass_full_path_objective_fail_route_objective_floor_audit"
    else:
        route = "full_path_correction_both_fail_route_capacity_or_interference_audit"
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.35r",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "run_identity_sha256": run["identity_sha256"],
            "t20_35q_result_identity_sha256": spec["t20_35q_result_identity_sha256"],
            "t20_35o_result_identity_sha256": spec["t20_35o_result_identity_sha256"],
            "source_checkpoint_identity_sha256": spec[
                "source_checkpoint_identity_sha256"
            ],
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "correction_example_count": CORRECTION_EXAMPLE_COUNT,
            "baseline_correction_objective_mean": baseline,
            "final_correction_objective_mean": final,
            "final_to_baseline_correction_objective_ratio": ratio,
            "baseline_standard_objective_mean": run[
                "baseline_standard_objective_mean"
            ],
            "final_standard_objective_mean": run["final_standard_objective_mean"],
            "final_to_source_gate_baseline_objective_ratio": standard_ratio,
            "maximum_allowed_objective_ratio": MAX_OBJECTIVE_RATIO,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "decoded_action_chunks": run["decoded_action_chunks"],
            "correction_objective_ratio_within_target": correction_objective_pass,
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
    verify_signed_payload(payload, label="T20.35r result")
    expected = build_result(
        spec=spec,
        authority_identity=payload.get("authority_decision_identity_sha256"),
        run=run,
    )
    archived = {key: value for key, value in payload.items() if key != "identity_sha256"}
    rebuilt = {key: value for key, value in expected.items() if key != "identity_sha256"}
    if not _equal_with_float_tolerance(archived, rebuilt, absolute_tolerance=1e-15):
        raise ValueError("T20.35r result drifted")


def load_source_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    trajectory_sources = load_t20_35q_sources(repo_root=root)
    trajectory_spec = trajectory_sources["trajectory_spec"]
    trajectory_permit = trajectory_sources["trajectory_permit"]
    trajectory_attempt = load_strict_json(root / T20_35Q_ATTEMPT_PATH)
    verify_t20_35q_attempt(
        trajectory_attempt,
        spec_identity=trajectory_spec["identity_sha256"],
        permit_identity=trajectory_permit["identity_sha256"],
    )
    trajectory_result = load_strict_json(root / T20_35Q_RESULT_PATH)
    verify_t20_35q_result(
        trajectory_result,
        spec=trajectory_spec,
        permit=trajectory_permit,
        attempt=trajectory_attempt,
        source_trajectory_result=trajectory_sources["source_result"],
        training_result=trajectory_sources["training_result"],
        target_chunk=trajectory_sources["residual_report"]["target_action_chunk"],
    )
    return {
        **trajectory_sources,
        "base_source_run": trajectory_sources["source_run"],
        "source_spec": trajectory_sources["training_spec"],
        "source_run": trajectory_sources["training_run"],
        "source_result": trajectory_sources["training_result"],
        "trajectory_spec": trajectory_spec,
        "trajectory_result": trajectory_result,
        "target_result": trajectory_sources["source_result"],
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
    )
    return archived


def _finite_matrix(
    value: Any, *, rows: int, columns: int, label: str
) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != rows:
        raise ValueError(f"T20.35r {label} row count drifted")
    matrix = []
    for row in value:
        if not isinstance(row, list) or len(row) != columns:
            raise ValueError(f"T20.35r {label} column count drifted")
        matrix.append([_finite(item, label) for item in row])
    return matrix


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.35r {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.35r {label} must be finite")
    return number


def _matrix_sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35r {label} must be lowercase SHA-256")
