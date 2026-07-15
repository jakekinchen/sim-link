"""Fail-closed artifact contract for the T20.36 corrected-coverage campaign."""

from __future__ import annotations

import copy
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
from scenesmith.robot_lab.t20_32_closed_loop_divergence import (
    ALL_SEEDS,
    _sequence_sha,
    summarize_rows,
    verify_threshold_contract,
)
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (
    EXPECTED_DEPENDENCY_VERSIONS as X_EXPECTED_DEPENDENCY_VERSIONS,
    MAX_ACTION_ERROR_RAD,
    MAX_OBJECTIVE_RATIO,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "T20.36"
SPEC_PATH = Path(
    "configurations/robot_lab/t20_36_bounded_corrected_coverage_training_spec.json"
)
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36_runtime_dependency_preflight.json"
)
TRAINING_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36_bounded_corrected_coverage_permit.json"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_36_bounded_corrected_coverage_result.json"
)
RUN_ROOT = Path("outputs/robot_lab/t20_36_bounded_corrected_coverage_run_001")
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
CHECKPOINT_ROOT = RUN_ROOT / "checkpoint"
X_SPEC_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_training_spec.json"
)
X_RESULT_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_result.json"
)
X_RUN_ROOT = Path(
    "outputs/robot_lab/t20_35x_physical_gate_joint_weighted_run_001"
)
X_RUN_PATH = X_RUN_ROOT / "run_summary.json"
X_CHECKPOINT_ROOT = X_RUN_ROOT / "checkpoint"
X_CHECKPOINT_CONFIG_PATH = X_CHECKPOINT_ROOT / "physical_gate_joint_weighted_config.json"
X_CHECKPOINT_MODEL_PATH = X_CHECKPOINT_ROOT / "physical_gate_joint_weighted_model.safetensors"
RECOVERY_SPEC_PATH = Path(
    "configurations/robot_lab/t20_23_recovery_augmented_training_spec.json"
)
RECOVERY_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_23_recovery_augmented_dataset_manifest.json"
)
RECOVERY_DATASET_ROOT = Path("outputs/robot_lab/t20_23_recovery_augmented_dataset")
SAMPLER_AUDIT_PATH = Path(
    "configurations/robot_lab/t20_28_sampler_exposure_audit.json"
)
THRESHOLD_PATH = Path("configurations/robot_lab/t20_32_divergence_thresholds.json")
RENDERER_PATH = Path("scripts/robot_lab/render_rollout_mirror.py")

SPEC_SCHEMA_VERSION = "scenesmith.t20_36_bounded_corrected_coverage_spec.v1"
RUNTIME_PREFLIGHT_SCHEMA_VERSION = (
    "scenesmith.t20_36_runtime_dependency_preflight.v1"
)
TRAINING_PERMIT_SCHEMA_VERSION = (
    "scenesmith.t20_36_bounded_corrected_coverage_permit.v1"
)
RUN_SCHEMA_VERSION = "scenesmith.t20_36_bounded_corrected_coverage_run.v1"
TRACE_SCHEMA_VERSION = "scenesmith.t20_36_closed_loop_trace.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_36_bounded_corrected_coverage_result.v1"

EXPECTED_X_SPEC_IDENTITY = (
    "96efc6d35115126268684c91346b7388077342c573e458b7e708e98714113cfd"
)
EXPECTED_X_RUN_IDENTITY = (
    "b5cc16ef53a415a7e0a4b8519332a4197201544fc9ebe5186565562e048c054b"
)
EXPECTED_X_RESULT_IDENTITY = (
    "e79dacff684dac507295d839527fb15d4eced8fa9c83973f5534bdf7e99ec6cd"
)
EXPECTED_X_CHECKPOINT_IDENTITY = (
    "40c94f66e24f0e949c1b48c057de7643b868468cc3ee0025e15778c25b8cad50"
)
EXPECTED_RECOVERY_SPEC_IDENTITY = (
    "5ad2f407d5df49752c65180addbda033888fdcc5869fc5c9a546669bb94a58aa"
)
EXPECTED_RECOVERY_MANIFEST_IDENTITY = (
    "f12c95a3cdf3e0005fa093000a5e44e1cddd08dbfb049ab405f462e2c9e760fa"
)
EXPECTED_SAMPLER_AUDIT_IDENTITY = (
    "2445c5d0711ebd29d6f6c92ca637b80e9c6d3e6725e39d7b427eb3b215937d38"
)
EXPECTED_THRESHOLD_IDENTITY = (
    "edbbf85e56a7020cec9b16cbab6263dc3e9dbe106ff8f55b53a85d3034d7f4cb"
)
EXPECTED_DEPENDENCY_VERSIONS = {
    **X_EXPECTED_DEPENDENCY_VERSIONS,
    "mujoco": "3.3.5",
    "Pillow": "12.3.0",
}
OPTIMIZER_UPDATES = 500
MINIMUM_FREE_DISK_BYTES = 6 * 1024 * 1024 * 1024
TRAINING_SEED = 20260719
STANDARD_FLOW_SEED_BASE = 20264719
EVALUATION_SEEDS = tuple(ALL_SEEDS)
INFERENCE_SEEDS = {0: 20260716, 6: 20260714, 7: 20260715}


def build_training_spec(
    *,
    x_spec: dict[str, Any],
    x_run: dict[str, Any],
    x_result: dict[str, Any],
    x_checkpoint_config: dict[str, Any],
    recovery_spec: dict[str, Any],
    recovery_manifest: dict[str, Any],
    sampler_audit: dict[str, Any],
    threshold: dict[str, Any],
    recovery_dataset_tree: list[dict[str, Any]],
    renderer_source_sha256: str,
) -> dict[str, Any]:
    for label, payload in (
        ("X spec", x_spec),
        ("X run", x_run),
        ("X result", x_result),
        ("X checkpoint config", x_checkpoint_config),
        ("recovery spec", recovery_spec),
        ("recovery manifest", recovery_manifest),
        ("sampler audit", sampler_audit),
        ("threshold", threshold),
    ):
        verify_signed_payload(payload, label=f"T20.36 {label}")
    verify_threshold_contract(threshold)
    _sha(renderer_source_sha256, "renderer source")
    if (
        x_spec.get("identity_sha256") != EXPECTED_X_SPEC_IDENTITY
        or x_run.get("identity_sha256") != EXPECTED_X_RUN_IDENTITY
        or x_result.get("identity_sha256") != EXPECTED_X_RESULT_IDENTITY
        or x_result.get("run_identity_sha256") != x_run.get("identity_sha256")
        or x_result.get("gate_b_passed") is not True
        or x_result.get("objective_ratio_within_threshold") is not True
        or x_result.get("all_decoded_chunks_within_threshold") is not True
        or x_run.get("checkpoint_identity_sha256")
        != EXPECTED_X_CHECKPOINT_IDENTITY
        or x_checkpoint_config.get("task_id") != "T20.35x"
        or x_checkpoint_config.get("training_spec_identity_sha256")
        != x_spec.get("identity_sha256")
        or recovery_spec.get("identity_sha256")
        != EXPECTED_RECOVERY_SPEC_IDENTITY
        or recovery_manifest.get("identity_sha256")
        != EXPECTED_RECOVERY_MANIFEST_IDENTITY
        or sampler_audit.get("identity_sha256")
        != EXPECTED_SAMPLER_AUDIT_IDENTITY
        or threshold.get("identity_sha256") != EXPECTED_THRESHOLD_IDENTITY
    ):
        raise ValueError("T20.36 source identity, Gate B, or route drifted")
    dataset = recovery_manifest.get("dataset", {})
    if (
        dataset.get("repo_id")
        != recovery_spec.get("dataset_contract", {}).get("dataset_repo_id")
        or dataset.get("total_episodes") != 10
        or dataset.get("total_frames") != 2330
    ):
        raise ValueError("T20.36 frozen recovery dataset contract drifted")
    recovery = sampler_audit.get("campaigns", {}).get("recovery_augmented", {})
    sample_indices = recovery.get("sampled_indices")
    if (
        not isinstance(sample_indices, list)
        or len(sample_indices) != OPTIMIZER_UPDATES
        or len(set(sample_indices)) != OPTIMIZER_UPDATES
        or any(isinstance(index, bool) or not isinstance(index, int) for index in sample_indices)
        or any(index < 0 or index >= 2330 for index in sample_indices)
        or hashlib.sha256(canonical_json_bytes(sample_indices)).hexdigest()
        != recovery.get("sampled_indices_sha256")
    ):
        raise ValueError("T20.36 exact coverage sample schedule drifted")
    if recovery_dataset_tree != _normalize_tree(recovery_dataset_tree):
        raise ValueError("T20.36 recovery dataset tree is not canonical")
    paths = {row["path"] for row in recovery_dataset_tree}
    if paths != {
        "data/chunk-000/file-000.parquet",
        "meta/episodes/chunk-000/file-000.parquet",
        "meta/info.json",
        "meta/stats.json",
        "meta/tasks.parquet",
    }:
        raise ValueError("T20.36 recovery dataset tree coverage drifted")
    campaign = x_spec.get("campaign", {})
    correction_schedule = campaign.get("sample_index_by_update")
    if not isinstance(correction_schedule, list) or len(correction_schedule) != OPTIMIZER_UPDATES:
        raise ValueError("T20.36 correction replay schedule drifted")
    flow_seeds = [STANDARD_FLOW_SEED_BASE + index for index in range(OPTIMIZER_UPDATES)]
    return sign_payload(
        {
            "schema_version": SPEC_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "scope": "one_bounded_expert_only_corrected_coverage_campaign_then_ordered_gate_b_gate_c_and_held_out_evaluation",
            "source_gate_b": {
                "t20_35x_spec_identity_sha256": x_spec["identity_sha256"],
                "t20_35x_run_identity_sha256": x_run["identity_sha256"],
                "t20_35x_result_identity_sha256": x_result["identity_sha256"],
                "checkpoint_identity_sha256": x_run["checkpoint_identity_sha256"],
                "checkpoint_tree": copy.deepcopy(x_run["checkpoint_tree"]),
                "checkpoint_config_identity_sha256": x_checkpoint_config[
                    "identity_sha256"
                ],
            },
            "coverage_dataset": {
                "training_spec_identity_sha256": recovery_spec["identity_sha256"],
                "manifest_identity_sha256": recovery_manifest["identity_sha256"],
                "root": RECOVERY_DATASET_ROOT.as_posix(),
                "repo_id": dataset["repo_id"],
                "episode_count": 10,
                "frame_count": 2330,
                "file_tree": copy.deepcopy(recovery_dataset_tree),
                "file_tree_identity_sha256": hashlib.sha256(
                    canonical_json_bytes(recovery_dataset_tree)
                ).hexdigest(),
            },
            "processor_contract": {
                "source": "unchanged_t20_35x_processor_and_statistics",
                "dataset_stats_path": x_spec["dataset_stats_path"],
                "dataset_stats_file_sha256": x_spec["dataset_stats_file_sha256"],
                "physical_joint_weighting": copy.deepcopy(
                    x_spec["physical_joint_weighting"]
                ),
                "time_normalization": copy.deepcopy(x_spec["time_normalization"]),
                "statistics_changed": False,
            },
            "campaign": {
                "optimizer": campaign["optimizer"],
                "optimizer_update_count": OPTIMIZER_UPDATES,
                "learning_rate": campaign["learning_rate"],
                "weight_decay": campaign["weight_decay"],
                "betas": copy.deepcopy(campaign["betas"]),
                "epsilon": campaign["epsilon"],
                "amsgrad": campaign["amsgrad"],
                "gradient_clip_norm": campaign["gradient_clip_norm"],
                "training_seed": TRAINING_SEED,
                "coverage_sample_index_by_update": copy.deepcopy(sample_indices),
                "coverage_sample_indices_sha256": recovery[
                    "sampled_indices_sha256"
                ],
                "coverage_unique_sample_count": OPTIMIZER_UPDATES,
                "correction_example_index_by_update": copy.deepcopy(
                    correction_schedule
                ),
                "standard_flow_seed_by_update": flow_seeds,
                "gradient_accumulation": "one_full_coverage_standard_gradient_plus_one_t20_35x_time_and_joint_weighted_correction_gradient_before_each_step",
                "network_mode": "offline_local_cache_only",
            },
            "gate_b": {
                "source_gate_baseline_objective_mean": x_spec[
                    "source_gate_baseline_objective_mean"
                ],
                "maximum_objective_ratio": MAX_OBJECTIVE_RATIO,
                "maximum_action_error_rad": MAX_ACTION_ERROR_RAD,
                "inference_seeds": copy.deepcopy(x_spec["evaluation"]["inference_seeds"]),
                "base_noise_sha256_by_seed": copy.deepcopy(
                    x_spec["evaluation"]["base_noise_sha256_by_seed"]
                ),
                "all_inference_seeds_must_pass": True,
            },
            "ordered_closed_loop_evaluation": {
                "seeds": list(EVALUATION_SEEDS),
                "roles": ["training", "held_out", "held_out"],
                "inference_seed_by_episode_seed": {
                    str(seed): INFERENCE_SEEDS[seed] for seed in EVALUATION_SEEDS
                },
                "action_horizon": 5,
                "gate_b_required_before_any_rollout": True,
                "training_seed_strict_v2_required_before_held_out": True,
                "complete_signed_trace_required": True,
                "content_addressed_mirror_required": True,
                "threshold_contract_identity_sha256": threshold[
                    "identity_sha256"
                ],
            },
            "render_runtime": {
                "renderer_path": RENDERER_PATH.as_posix(),
                "renderer_source_sha256": renderer_source_sha256,
                "ffmpeg_version": "8.0.1",
                "mujoco_version": EXPECTED_DEPENDENCY_VERSIONS["mujoco"],
                "pillow_version": EXPECTED_DEPENDENCY_VERSIONS["Pillow"],
            },
            "required_python_major_minor": [3, 12],
            "required_dependency_versions": copy.deepcopy(
                EXPECTED_DEPENDENCY_VERSIONS
            ),
            "runtime_dependency_preflight_required": True,
            "minimum_free_disk_bytes_before_attempt": MINIMUM_FREE_DISK_BYTES,
            "one_run_permit_required": True,
            "authorized_actions": [
                "simulation_model_load",
                "simulation_model_inference",
                "simulation_optimizer_training",
                "simulation_closed_loop_rollout_if_prior_gates_pass",
                "diagnostic_mirror_render",
            ],
            "model_loaded": False,
            "model_inference": False,
            "optimizer_training": False,
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


def verify_training_spec(payload: dict[str, Any], **sources: Any) -> None:
    verify_signed_payload(payload, label="T20.36 training spec")
    if payload != build_training_spec(**sources):
        raise ValueError("T20.36 training spec drifted")


def build_runtime_preflight(
    *,
    spec: dict[str, Any],
    authority_identity: str,
    python_major_minor: list[int],
    dependency_versions: dict[str, str],
    mps_available: bool,
    lerobot_stack_identity_sha256: str,
    ffmpeg_version: str,
    render_smoke_verified: bool,
    free_disk_bytes: int,
    source_checkpoint_tree_verified: bool,
    coverage_dataset_tree_verified: bool,
    attempt_exists: bool,
    result_exists: bool,
) -> dict[str, Any]:
    verify_signed_payload(spec, label="T20.36 runtime-preflight spec")
    _sha(authority_identity, "authority identity")
    _sha(lerobot_stack_identity_sha256, "LeRobot stack identity")
    if (
        python_major_minor != spec["required_python_major_minor"]
        or dependency_versions != spec["required_dependency_versions"]
        or mps_available is not True
        or ffmpeg_version != spec["render_runtime"]["ffmpeg_version"]
        or render_smoke_verified is not True
        or isinstance(free_disk_bytes, bool)
        or not isinstance(free_disk_bytes, int)
        or free_disk_bytes < spec["minimum_free_disk_bytes_before_attempt"]
        or source_checkpoint_tree_verified is not True
        or coverage_dataset_tree_verified is not True
        or attempt_exists is not False
        or result_exists is not False
    ):
        raise ValueError("T20.36 runtime dependency preflight failed closed")
    return sign_payload(
        {
            "schema_version": RUNTIME_PREFLIGHT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "source_checkpoint_identity_sha256": spec["source_gate_b"][
                "checkpoint_identity_sha256"
            ],
            "coverage_dataset_tree_identity_sha256": spec["coverage_dataset"][
                "file_tree_identity_sha256"
            ],
            "lerobot_stack_identity_sha256": lerobot_stack_identity_sha256,
            "ffmpeg_version": ffmpeg_version,
            "render_smoke_verified": render_smoke_verified,
            "free_disk_bytes": free_disk_bytes,
            "minimum_free_disk_bytes": spec[
                "minimum_free_disk_bytes_before_attempt"
            ],
            "python_major_minor": python_major_minor,
            "dependency_versions": dependency_versions,
            "mps_available": mps_available,
            "source_checkpoint_tree_verified": source_checkpoint_tree_verified,
            "coverage_dataset_tree_verified": coverage_dataset_tree_verified,
            "attempt_exists": attempt_exists,
            "result_exists": result_exists,
            "checkpoint_tensor_read": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "closed_loop_rollout": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.36 runtime preflight")
    expected = build_runtime_preflight(
        spec=spec,
        authority_identity=authority_identity,
        python_major_minor=payload.get("python_major_minor"),
        dependency_versions=payload.get("dependency_versions"),
        mps_available=payload.get("mps_available"),
        lerobot_stack_identity_sha256=payload.get(
            "lerobot_stack_identity_sha256"
        ),
        ffmpeg_version=payload.get("ffmpeg_version"),
        render_smoke_verified=payload.get("render_smoke_verified"),
        free_disk_bytes=payload.get("free_disk_bytes"),
        source_checkpoint_tree_verified=payload.get(
            "source_checkpoint_tree_verified"
        ),
        coverage_dataset_tree_verified=payload.get(
            "coverage_dataset_tree_verified"
        ),
        attempt_exists=payload.get("attempt_exists"),
        result_exists=payload.get("result_exists"),
    )
    if payload != expected:
        raise ValueError("T20.36 runtime preflight drifted")


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
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime_preflight[
                "identity_sha256"
            ],
            "source_checkpoint_identity_sha256": spec["source_gate_b"][
                "checkpoint_identity_sha256"
            ],
            "authorized_attempt_count": 1,
            "authorized_actions": copy.deepcopy(spec["authorized_actions"]),
            "simulation_only": True,
            "ordered_gate_enforcement_required": True,
            "valid_until": "2026-07-15T23:27:47-05:00",
            "checkpoint_tensor_read": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
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
    verify_signed_payload(payload, label="T20.36 training permit")
    expected = build_training_permit(
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.36 training permit drifted")


def build_trace(
    *,
    threshold: dict[str, Any],
    seed: int,
    inference_seed: int,
    source_episode_file_sha256: str,
    source_episode_identity_sha256: str,
    run_identity_sha256: str,
    checkpoint_identity_sha256: str,
    rows: list[dict[str, Any]],
    closed_loop: dict[str, Any],
) -> dict[str, Any]:
    verify_threshold_contract(threshold)
    if seed not in EVALUATION_SEEDS or inference_seed != INFERENCE_SEEDS[seed]:
        raise ValueError("T20.36 trace seed coverage drifted")
    diagnostics = summarize_rows(rows, threshold)
    requested_sha = _sequence_sha(rows, "candidate_requested_action_rad")
    applied_sha = _sequence_sha(rows, "candidate_applied_action_rad")
    verify_signed_payload(closed_loop, label="T20.36 embedded closed loop")
    payload = sign_payload(
        {
            "schema_version": TRACE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "adapter_id": "t20_36_bounded_corrected_coverage",
            "seed": seed,
            "seed_role": "training" if seed == 0 else "held_out",
            "inference_seed": inference_seed,
            "threshold_contract_identity_sha256": threshold["identity_sha256"],
            "source_episode_file_sha256": source_episode_file_sha256,
            "source_episode_identity_sha256": source_episode_identity_sha256,
            "training_identity_sha256": run_identity_sha256,
            "checkpoint_sha256": checkpoint_identity_sha256,
            "comparisons": rows,
            "diagnostics": diagnostics,
            "closed_loop": closed_loop,
            "requested_action_sequence_sha256": requested_sha,
            "applied_action_sequence_sha256": applied_sha,
            "model_inference_executed": True,
            "optimizer_training": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    verify_trace(payload, threshold=threshold)
    return payload


def verify_trace(payload: dict[str, Any], *, threshold: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36 closed-loop trace")
    verify_threshold_contract(threshold)
    seed = payload.get("seed")
    if (
        payload.get("schema_version") != TRACE_SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("adapter_id") != "t20_36_bounded_corrected_coverage"
        or seed not in EVALUATION_SEEDS
        or payload.get("seed_role") != ("training" if seed == 0 else "held_out")
        or payload.get("inference_seed") != INFERENCE_SEEDS[seed]
        or payload.get("threshold_contract_identity_sha256")
        != threshold.get("identity_sha256")
    ):
        raise ValueError("T20.36 trace identity or order drifted")
    for field in (
        "source_episode_file_sha256",
        "source_episode_identity_sha256",
        "training_identity_sha256",
        "checkpoint_sha256",
        "requested_action_sequence_sha256",
        "applied_action_sequence_sha256",
    ):
        _sha(payload.get(field), field)
    rows = payload.get("comparisons")
    if payload.get("diagnostics") != summarize_rows(rows, threshold):
        raise ValueError("T20.36 trace diagnostics drifted")
    if payload["diagnostics"]["initial_reset_identical_within_tolerance"] is not True:
        raise ValueError("T20.36 trace reset drifted")
    rollout = payload.get("closed_loop", {})
    verify_signed_payload(rollout, label="T20.36 embedded closed loop")
    if (
        rollout.get("seed") != seed
        or rollout.get("frame_count") != 244
        or rollout.get("policy_action_sequence_sha256")
        != payload["requested_action_sequence_sha256"]
        or payload["requested_action_sequence_sha256"]
        != _sequence_sha(rows, "candidate_requested_action_rad")
        or payload["applied_action_sequence_sha256"]
        != _sequence_sha(rows, "candidate_applied_action_rad")
        or rollout.get("projected_action_frame_count") != 0
        or rollout.get("active_assist_frame_count") != 0
        or not isinstance(rollout.get("simulation_semantic_strict_success"), bool)
    ):
        raise ValueError("T20.36 trace rollout linkage or assistance drifted")
    for field in (
        "optimizer_training",
        "dataset_mutated",
        "statistics_changed",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    ):
        if payload.get(field) is not False:
            raise ValueError("T20.36 trace authority drifted")


def build_mirror_ref(
    *, trace: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    verify_signed_payload(trace, label="T20.36 mirror trace")
    verify_signed_payload(manifest, label="T20.36 mirror manifest")
    if (
        manifest.get("schema_version") != "scenesmith.rollout_mirror_render.v1"
        or manifest.get("trace_identity_sha256") != trace.get("identity_sha256")
        or manifest.get("adapter_id") != trace.get("adapter_id")
        or manifest.get("seed") != trace.get("seed")
        or manifest.get("frame_count") != 244
    ):
        raise ValueError("T20.36 mirror binding drifted")
    output_sha = manifest.get("output_sha256")
    _sha(output_sha, "mirror output")
    output = Path(str(manifest.get("output_mp4", "")))
    if output.stem != trace["identity_sha256"]:
        raise ValueError("T20.36 mirror is not content addressed by trace")
    return {
        "seed": trace["seed"],
        "trace_identity_sha256": trace["identity_sha256"],
        "manifest_identity_sha256": manifest["identity_sha256"],
        "output_mp4": output.as_posix(),
        "output_sha256": output_sha,
        "output_bytes": manifest["output_bytes"],
    }


def verify_run(
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.36 campaign run")
    _sha(authority_identity, "authority identity")
    campaign = spec["campaign"]
    if (
        payload.get("schema_version") != RUN_SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("training_spec_identity_sha256") != spec["identity_sha256"]
        or payload.get("authority_decision_identity_sha256") != authority_identity
        or payload.get("optimizer_update_count") != OPTIMIZER_UPDATES
        or payload.get("coverage_sample_index_by_update")
        != campaign["coverage_sample_index_by_update"]
        or payload.get("correction_example_index_by_update")
        != campaign["correction_example_index_by_update"]
        or payload.get("standard_flow_seed_by_update")
        != campaign["standard_flow_seed_by_update"]
        or payload.get("optimizer_training") is not True
        or payload.get("closed_loop_rollout") is not False
    ):
        raise ValueError("T20.36 campaign run contract drifted")
    for field in (
        "per_update_standard_coverage_objective",
        "per_update_time_joint_weighted_correction_objective",
        "per_update_total_objective",
        "gradient_norms_before_clip",
    ):
        values = payload.get(field)
        if not isinstance(values, list) or len(values) != OPTIMIZER_UPDATES:
            raise ValueError("T20.36 objective or gradient trace is incomplete")
        if any(not _is_finite_number(value) for value in values):
            raise ValueError("T20.36 objective or gradient trace is non-finite")
    decoded = payload.get("decoded_action_chunks")
    if not isinstance(decoded, list) or len(decoded) != 5:
        raise ValueError("T20.36 Gate B decoded coverage drifted")
    for row in decoded:
        if not _is_finite_number(row.get("maximum_absolute_error_rad")):
            raise ValueError("T20.36 Gate B decoded action is non-finite")
    final_standard = payload.get("final_standard_objective_mean")
    ratio = payload.get("final_to_source_gate_baseline_objective_ratio")
    if (
        not _is_finite_number(final_standard)
        or not _is_finite_number(ratio)
        or not math.isclose(
            float(ratio),
            float(final_standard)
            / float(spec["gate_b"]["source_gate_baseline_objective_mean"]),
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    ):
        raise ValueError("T20.36 Gate B standard-objective ratio drifted")
    objective_pass = float(ratio) <= spec["gate_b"]["maximum_objective_ratio"]
    action_pass = all(
        float(row["maximum_absolute_error_rad"])
        <= spec["gate_b"]["maximum_action_error_rad"]
        for row in decoded
    )
    if (
        payload.get("objective_ratio_within_threshold") is not objective_pass
        or payload.get("all_decoded_chunks_within_threshold") is not action_pass
        or payload.get("gate_b_passed") is not (objective_pass and action_pass)
    ):
        raise ValueError("T20.36 Gate B conjunction drifted")
    for field in (
        "checkpoint_mutated",
        "dataset_mutated",
        "statistics_changed",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    ):
        if payload.get(field) is not False:
            raise ValueError("T20.36 campaign run authority drifted")


def build_result(
    *,
    spec: dict[str, Any],
    run: dict[str, Any],
    authority_identity: str,
    traces: list[dict[str, Any]],
    mirror_refs: list[dict[str, Any]],
    threshold: dict[str, Any],
) -> dict[str, Any]:
    verify_run(run, spec=spec, authority_identity=authority_identity)
    gate_b_passed = bool(run.get("gate_b_passed"))
    expected_seeds: list[int]
    if not gate_b_passed:
        expected_seeds = []
        decision = "gate_b_regressed_stop_before_closed_loop"
    else:
        if not traces:
            raise ValueError("T20.36 Gate B pass requires training-seed Gate C evidence")
        verify_trace(traces[0], threshold=threshold)
        if traces[0]["seed"] != 0:
            raise ValueError("T20.36 Gate C training seed must run first")
        gate_c_passed = traces[0]["closed_loop"][
            "simulation_semantic_strict_success"
        ]
        if gate_c_passed:
            expected_seeds = list(EVALUATION_SEEDS)
            decision = "gate_c_passed_held_out_candidate_recorded"
        else:
            expected_seeds = [0]
            decision = "gate_c_failed_stop_before_held_out"
    if [trace.get("seed") for trace in traces] != expected_seeds:
        raise ValueError("T20.36 ordered closed-loop trace coverage drifted")
    if [ref.get("seed") for ref in mirror_refs] != expected_seeds:
        raise ValueError("T20.36 ordered mirror coverage drifted")
    for trace, ref in zip(traces, mirror_refs, strict=True):
        verify_trace(trace, threshold=threshold)
        if ref.get("trace_identity_sha256") != trace["identity_sha256"]:
            raise ValueError("T20.36 trace-to-mirror linkage drifted")
    gate_c = bool(
        traces
        and traces[0]["closed_loop"]["simulation_semantic_strict_success"]
    )
    strict_count = sum(
        trace["closed_loop"]["simulation_semantic_strict_success"]
        for trace in traces
    )
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "run_identity_sha256": run["identity_sha256"],
            "checkpoint_identity_sha256": run["checkpoint_identity_sha256"],
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "gate_b_passed": gate_b_passed,
            "gate_c_training_seed_strict_success": gate_c,
            "evaluation_seeds_reached": expected_seeds,
            "trace_identity_sha256_by_seed": {
                str(trace["seed"]): trace["identity_sha256"] for trace in traces
            },
            "mirror_refs": copy.deepcopy(mirror_refs),
            "strict_success_count": strict_count,
            "all_reached_evaluations_strict_success": bool(traces)
            and strict_count == len(traces),
            "candidate_three_seed_strict_success": expected_seeds
            == list(EVALUATION_SEEDS)
            and strict_count == len(EVALUATION_SEEDS),
            "decision": decision,
            "simulation_policy_accepted": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_result(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    run: dict[str, Any],
    authority_identity: str,
    traces: list[dict[str, Any]],
    mirror_refs: list[dict[str, Any]],
    threshold: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36 result")
    expected = build_result(
        spec=spec,
        run=run,
        authority_identity=authority_identity,
        traces=traces,
        mirror_refs=mirror_refs,
        threshold=threshold,
    )
    if payload != expected:
        raise ValueError("T20.36 result drifted")


def load_source_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    return {
        "x_spec": load_strict_json(root / X_SPEC_PATH),
        "x_run": load_strict_json(root / X_RUN_PATH),
        "x_result": load_strict_json(root / X_RESULT_PATH),
        "x_checkpoint_config": load_strict_json(root / X_CHECKPOINT_CONFIG_PATH),
        "recovery_spec": load_strict_json(root / RECOVERY_SPEC_PATH),
        "recovery_manifest": load_strict_json(root / RECOVERY_MANIFEST_PATH),
        "sampler_audit": load_strict_json(root / SAMPLER_AUDIT_PATH),
        "threshold": load_strict_json(root / THRESHOLD_PATH),
        "recovery_dataset_tree": file_tree(root / RECOVERY_DATASET_ROOT),
        "renderer_source_sha256": hashlib.sha256(
            (root / RENDERER_PATH).read_bytes()
        ).hexdigest(),
    }


def file_tree(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(item for item in Path(root).rglob("*") if item.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": digest.hexdigest(),
            }
        )
    if not rows:
        raise ValueError("T20.36 file tree is empty")
    return rows


def _normalize_tree(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "size_bytes", "sha256"}:
            raise ValueError("T20.36 file tree row drifted")
        path = row["path"]
        size = row["size_bytes"]
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or ".." in Path(path).parts
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size <= 0
        ):
            raise ValueError("T20.36 file tree path or size drifted")
        _sha(row["sha256"], "file tree digest")
        normalized.append(copy.deepcopy(row))
    return sorted(normalized, key=lambda row: row["path"])


def _sha(value: Any, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"T20.36 {label} is not a SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"T20.36 {label} is not a SHA-256") from error


def _is_finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )
