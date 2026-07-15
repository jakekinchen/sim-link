"""Pure pre-run design for the exact T20.36d ACT Gate B control."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    MAX_ACTION_ERROR_RAD,
    MAX_OBJECTIVE_RATIO,
    verify_training_spec as verify_t20_33_spec,
)
from scenesmith.robot_lab.t20_36c_local_policy_track_preflight import (
    LEROBOT_HEAD,
    SOURCE_SHA256,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(
    "configurations/robot_lab/t20_36d_exact_act_gate_b_control_spec.json"
)
LOCAL_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36c_local_policy_track_preflight.json"
)
GATE_B_SPEC_PATH = Path(
    "configurations/robot_lab/t20_33_one_batch_training_spec.json"
)
DATASET_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_23_recovery_augmented_dataset_manifest.json"
)
DATASET_ROOT = Path("outputs/robot_lab/t20_23_recovery_augmented_dataset")
DATASET_INFO_PATH = DATASET_ROOT / "meta/info.json"
DATASET_STATS_PATH = DATASET_ROOT / "meta/stats.json"
COORDINATE_SOURCE_PATH = Path("scenesmith/robot_lab/so101_coordinates.py")
SCHEMA_VERSION = "scenesmith.t20_36d_exact_act_gate_b_control_spec.v1"
TASK_ID = "T20.36d"
EXECUTION_TASK_ID = "T20.36e"
EXPECTED_IDENTITY = {
    "local_preflight": (
        "61fcf124ab23d2e27672f8335ade0e74df10254ca58d4aec5a77b606ef328bcb"
    ),
    "gate_b_spec": (
        "3fa3098c816b228a6687e952cb8444c77344e49877b17cfc5d1afdc32e6e685a"
    ),
    "dataset_manifest": (
        "f12c95a3cdf3e0005fa093000a5e44e1cddd08dbfb049ab405f462e2c9e760fa"
    ),
}
EXPECTED_FILE_SHA256 = {
    "local_preflight": (
        "358abe964aba2613838ca2c6a159bcd630e88e139af720778e0093767b3c0626"
    ),
    "gate_b_spec": (
        "e084e17015bef33f15023bab868ef88f38601e99bd3b7f20163395476967a358"
    ),
    "dataset_manifest": (
        "df6e63d86cd053937c9e4d4c267f057b76aaf418761e7dc3356a9ae08c06fea5"
    ),
    "dataset_info": (
        "789ab860cae39d100f1d28e0e547e2229b860cdcacc2916c230074ff5e7ed9fc"
    ),
    "dataset_stats": (
        "aae49a26834aa3684d17bede1da1407f2664c61d0bb9f33a650b269af6123bc1"
    ),
    "coordinate_source": (
        "9382e02106741906380eed572959f991382c285cedd08c8d652d0a3375cf843a"
    ),
}
JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]
IMAGE_FEATURE_KEYS = [
    "observation.images.base_0_rgb",
    "observation.images.left_wrist_0_rgb",
]
NORMALIZATION_MAPPING = {
    "ACTION": "MEAN_STD",
    "STATE": "MEAN_STD",
    "VISUAL": "IDENTITY",
}
TRAINING_SEED = 20260731
MAXIMUM_OPTIMIZER_UPDATES = 2000
EVALUATION_UPDATE_SCHEDULE = [0, 100, 250, 500, 1000, 2000]
EVALUATION_REPETITIONS = 5
LEARNING_RATE = 1e-4
ATTEMPT_MARKER_PATH = Path(
    "outputs/robot_lab/t20_36e_exact_act_gate_b_control_run_001/attempt.json"
)
AUTHORITY_FIELDS = (
    "network_accessed",
    "weights_downloaded",
    "checkpoint_tensor_read",
    "model_constructed",
    "model_loaded",
    "model_inference",
    "optimizer_created",
    "optimizer_training",
    "attempt_marker_created",
    "act_control_run_authorized",
    "act_control_run_executed",
    "policy_track_selected",
    "smolvla_entry_authorized",
    "gate_b_threshold_changed",
    "gate_c_authorized",
    "closed_loop_rollout",
    "simulation_policy_accepted",
    "physical_actuation",
    "external_compute_started",
    "brev_compute_started",
    "physical_transfer_ready",
    "promotion_eligible",
)


def load_design_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    paths = {
        "local_preflight": LOCAL_PREFLIGHT_PATH,
        "gate_b_spec": GATE_B_SPEC_PATH,
        "dataset_manifest": DATASET_MANIFEST_PATH,
        "dataset_info": DATASET_INFO_PATH,
        "dataset_stats": DATASET_STATS_PATH,
        "coordinate_source": COORDINATE_SOURCE_PATH,
    }
    return {
        "local_preflight": load_strict_json(root / LOCAL_PREFLIGHT_PATH),
        "gate_b_spec": load_strict_json(root / GATE_B_SPEC_PATH),
        "dataset_manifest": load_strict_json(root / DATASET_MANIFEST_PATH),
        "dataset_info": load_strict_json(root / DATASET_INFO_PATH),
        "dataset_stats": load_strict_json(root / DATASET_STATS_PATH),
        "source_file_sha256": {
            label: _file_sha256(root / path) for label, path in paths.items()
        },
    }


def build_spec(*, sources: dict[str, Any]) -> dict[str, Any]:
    _validate_sources(sources)
    preflight = _dict(sources.get("local_preflight"), "local preflight")
    gate_b = _dict(sources.get("gate_b_spec"), "Gate B source spec")
    manifest = _dict(sources.get("dataset_manifest"), "dataset manifest")
    info = _dict(sources.get("dataset_info"), "dataset info")
    stats = _dict(sources.get("dataset_stats"), "dataset statistics")
    feature_contract = _feature_contract(info)
    statistics = _normalization_statistics(stats)
    episode_zero = _episode_zero(manifest)
    source_batch = _dict(gate_b.get("source_batch"), "source batch")
    if (
        episode_zero["raw_rollout_identity_sha256"]
        != source_batch.get("source_episode_identity_sha256")
    ):
        raise ValueError("T20.36d canonical episode zero is not the Gate B source")
    act_sources = [
        row
        for row in preflight["lerobot_source"]["source_files"]
        if row["path"]
        in {
            "src/lerobot/configs/policies.py",
            "src/lerobot/policies/act/configuration_act.py",
            "src/lerobot/policies/act/modeling_act.py",
            "src/lerobot/policies/act/processor_act.py",
            "src/lerobot/policies/factory.py",
        }
    ]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "execution_task_id": EXECUTION_TASK_ID,
        "scope": "design_only_exact_act_one_batch_gate_b_diagnostic_control",
        "source_refs": {
            "local_preflight": _artifact_ref(
                LOCAL_PREFLIGHT_PATH,
                preflight,
                sources["source_file_sha256"]["local_preflight"],
            ),
            "gate_b_source_spec": _artifact_ref(
                GATE_B_SPEC_PATH,
                gate_b,
                sources["source_file_sha256"]["gate_b_spec"],
            ),
            "canonical_dataset_manifest": _artifact_ref(
                DATASET_MANIFEST_PATH,
                manifest,
                sources["source_file_sha256"]["dataset_manifest"],
            ),
        },
        "lerobot_source": {
            "head": LEROBOT_HEAD,
            "act_source_files": act_sources,
        },
        "source_batch": {
            "source_spec_dataset_root": source_batch["dataset_root"],
            "canonical_dataset_root": str(DATASET_ROOT),
            "canonical_dataset_episode_index": 0,
            "source_seed": source_batch["source_seed"],
            "frame_index": source_batch["frame_index"],
            "action_horizon": source_batch["action_horizon"],
            "action_variant": source_batch["action_variant"],
            "action_units": source_batch["action_units"],
            "source_episode_file_sha256": source_batch[
                "source_episode_file_sha256"
            ],
            "source_episode_identity_sha256": source_batch[
                "source_episode_identity_sha256"
            ],
            "measured_action_chunk_sha256": source_batch[
                "measured_action_chunk_sha256"
            ],
            "initial_observation_state_sha256": source_batch[
                "initial_observation_state_sha256"
            ],
            "initial_image_sha256": source_batch["initial_image_sha256"],
            "image_role_to_dataset_feature": {
                "top": IMAGE_FEATURE_KEYS[0],
                "wrist": IMAGE_FEATURE_KEYS[1],
            },
            "padding_or_inferred_actions": False,
        },
        "canonical_dataset": {
            "root": str(DATASET_ROOT),
            "repo_id": manifest["dataset"]["repo_id"],
            "revision": manifest["dataset"]["revision"],
            "manifest_identity_sha256": manifest["identity_sha256"],
            "episode_zero_raw_rollout_identity_sha256": episode_zero[
                "raw_rollout_identity_sha256"
            ],
            "episode_zero_content_sha256": episode_zero[
                "episode_content_sha256"
            ],
            "episode_zero_frame_count": episode_zero["frame_count"],
            "total_episode_count": manifest["dataset"]["total_episodes"],
            "total_frame_count": manifest["dataset"]["total_frames"],
            "metadata_file_sha256": {
                "info": sources["source_file_sha256"]["dataset_info"],
                "stats": sources["source_file_sha256"]["dataset_stats"],
            },
            **feature_contract,
        },
        "normalization": {
            "mapping": NORMALIZATION_MAPPING,
            "statistics_source_path": str(DATASET_STATS_PATH),
            "statistics_source_sha256": sources["source_file_sha256"][
                "dataset_stats"
            ],
            "statistics_frame_count": 2330,
            "statistics": statistics,
            "action_normalization_matches_t20_35x_correction_mode": True,
            "policy_specific_processor_implementation": "lerobot.policies.act.processor_act.make_act_pre_post_processors",
            "shared_contract_claim_limited_to_dataset_statistics_and_physical_round_trip": True,
        },
        "coordinate_round_trip": {
            "source_path": str(COORDINATE_SOURCE_PATH),
            "source_sha256": sources["source_file_sha256"]["coordinate_source"],
            "dataset_to_physical_function": "lerobot_to_mujoco",
            "physical_to_dataset_function": "mujoco_to_lerobot",
            "maximum_runtime_source_target_error_rad": 1e-5,
            "maximum_round_trip_error_rad": 1e-8,
            "must_pass_before_model_construction": True,
        },
        "act_config": {
            "policy_type": "act",
            "input_features": {
                IMAGE_FEATURE_KEYS[0]: {"type": "VISUAL", "shape": [3, 256, 256]},
                IMAGE_FEATURE_KEYS[1]: {"type": "VISUAL", "shape": [3, 256, 256]},
                "observation.state": {"type": "STATE", "shape": [6]},
            },
            "output_features": {"action": {"type": "ACTION", "shape": [6]}},
            "normalization_mapping": NORMALIZATION_MAPPING,
            "n_obs_steps": 1,
            "chunk_size": 50,
            "n_action_steps": 50,
            "vision_backbone": "resnet18",
            "pretrained_backbone_weights": None,
            "replace_final_stride_with_dilation": False,
            "pre_norm": False,
            "dim_model": 64,
            "n_heads": 4,
            "dim_feedforward": 128,
            "feedforward_activation": "relu",
            "n_encoder_layers": 1,
            "n_decoder_layers": 1,
            "use_vae": False,
            "temporal_ensemble_coeff": None,
            "dropout": 0.0,
            "device": "mps",
            "dtype": "float32",
            "use_amp": False,
            "compile_model": False,
        },
        "model_initialization": {
            "mode": "fresh_seeded_act_parameters",
            "training_seed": TRAINING_SEED,
            "cached_checkpoint_used": False,
            "pretrained_backbone_used": False,
            "network_fallback_allowed": False,
        },
        "campaign": {
            "optimizer": "AdamW",
            "learning_rate": LEARNING_RATE,
            "betas": [0.9, 0.999],
            "epsilon": 1e-8,
            "weight_decay": 0.0,
            "gradient_clip_norm": 1.0,
            "scheduler": None,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "evaluation_update_schedule": EVALUATION_UPDATE_SCHEDULE,
            "batch_size": 1,
            "fixed_batch_repeated": True,
            "training_seed": TRAINING_SEED,
            "per_update_seed_formula": "training_seed_plus_zero_based_update_index",
            "network_mode": "offline_no_download",
            "device": "mps",
            "one_attempt_only": True,
            "retry_or_sweep_allowed": False,
            "attempt_marker_path": str(ATTEMPT_MARKER_PATH),
            "attempt_marker_must_precede_model_construction": True,
            "stop_at_first_post_baseline_gate_b_pass": True,
            "otherwise_stop_after_maximum_updates": True,
        },
        "attempt_contract": {
            "schema_version": "scenesmith.t20_36e_exact_act_gate_b_control_attempt.v1",
            "path": str(ATTEMPT_MARKER_PATH),
            "immutable_create_once": True,
            "must_precede_model_construction": True,
            "required_fields": [
                "schema_version",
                "task_id",
                "training_spec_identity_sha256",
                "authority_decision_identity_sha256",
                "source_commit",
                "training_seed",
                "created_before_model_construction",
            ],
            "training_spec_identity_bound_at_runtime": True,
            "central_authority_identity_bound_at_runtime": True,
            "model_constructed_at_design_time": False,
        },
        "evaluation": {
            "mode": "deterministic_open_loop_same_observation_action_chunk",
            "repetition_count_per_checkpoint": EVALUATION_REPETITIONS,
            "model_eval_mode": True,
            "vae_disabled": True,
            "dropout_disabled": True,
            "decode": "reset_once_then_select_action_50_times_from_one_processed_observation",
            "expected_model_forward_count_per_repetition": 1,
            "all_repetition_action_hashes_must_match": True,
            "physical_error_basis": "decoded_lerobot_action_converted_to_mujoco_radian_vs_exact_source_measured_chunk",
            "supervised_objective_basis": "mean_absolute_normalized_action_error_over_unpadded_horizon_50",
            "closed_loop": False,
        },
        "gate": {
            "maximum_physical_action_error_rad": MAX_ACTION_ERROR_RAD,
            "maximum_final_to_baseline_supervised_objective_ratio": MAX_OBJECTIVE_RATIO,
            "all_action_dimensions_and_timesteps_must_pass": True,
            "all_deterministic_repetitions_must_pass": True,
            "unchanged_t20_33_conjunction": True,
            "proxy_metric_substitution_allowed": False,
            "uniform_physical_metric_reported_without_amendment": True,
        },
        "result_routing": {
            "pass": "shared_batch_and_normalization_control_pass_then_design_smolvla_entry",
            "pass_claim_limit": "one_batch_shared_dataset_statistics_and_physical_round_trip_exonerated_not_pi05_decode_or_product_policy",
            "fail": "shared_pipeline_not_exonerated_diagnose_before_smolvla_entry",
            "fail_claim_limit": "does_not_prove_dataset_fault_without_separating_act_implementation_and_optimization",
            "act_is_product_policy": False,
            "pi05_gate_b_changed": False,
            "gate_c_unlocked_by_control": False,
        },
        "pre_run_remote_preservation_required": True,
        "separate_central_training_authority_required": True,
        "separate_execution_review_required": True,
    }
    payload.update({field: False for field in AUTHORITY_FIELDS})
    return sign_payload(payload)


def verify_spec(payload: dict[str, Any], *, sources: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36d exact ACT Gate B control spec")
    expected = build_spec(sources=sources)
    if payload != expected:
        raise ValueError("T20.36d exact ACT Gate B control spec drifted")


def write_spec(
    *, repo_root: Path = REPO_ROOT, output_path: Path = SPEC_PATH
) -> dict[str, Any]:
    sources = load_design_sources(repo_root=repo_root)
    spec = build_spec(sources=sources)
    destination = output_path if output_path.is_absolute() else repo_root / output_path
    dump_canonical_json(destination, spec)
    verify_spec_file(
        repo_root=repo_root,
        output_path=output_path,
        sources=sources,
    )
    return spec


def verify_spec_file(
    *,
    repo_root: Path = REPO_ROOT,
    output_path: Path = SPEC_PATH,
    sources: dict[str, Any] | None = None,
) -> dict[str, Any]:
    destination = output_path if output_path.is_absolute() else repo_root / output_path
    payload = load_strict_json(destination)
    verify_spec(
        payload,
        sources=sources or load_design_sources(repo_root=repo_root),
    )
    return payload


def _validate_sources(sources: dict[str, Any]) -> None:
    preflight = _dict(sources.get("local_preflight"), "local preflight")
    gate_b = _dict(sources.get("gate_b_spec"), "Gate B source spec")
    manifest = _dict(sources.get("dataset_manifest"), "dataset manifest")
    hashes = sources.get("source_file_sha256")
    if hashes != EXPECTED_FILE_SHA256:
        raise ValueError("T20.36d source file identities drifted")
    for label, payload in (
        ("local_preflight", preflight),
        ("gate_b_spec", gate_b),
        ("dataset_manifest", manifest),
    ):
        verify_signed_payload(payload, label=f"T20.36d {label}")
        if payload.get("identity_sha256") != EXPECTED_IDENTITY[label]:
            raise ValueError(f"T20.36d {label} identity drifted")
    verify_t20_33_spec(gate_b)
    if (
        gate_b["gate"].get("maximum_decoded_action_error_rad")
        != MAX_ACTION_ERROR_RAD
        or gate_b["gate"].get("maximum_final_to_baseline_objective_ratio")
        != MAX_OBJECTIVE_RATIO
        or preflight.get("selected_next_hypothesis")
        != "design_exact_act_gate_b_control_before_smolvla_entry"
        or preflight.get("policy_track_selected") is not False
        or preflight["lerobot_source"].get("head") != LEROBOT_HEAD
    ):
        raise ValueError("T20.36d route, Gate B, or source boundary drifted")
    observed_sources = {
        row.get("path"): row.get("sha256")
        for row in preflight["lerobot_source"].get("source_files", [])
        if isinstance(row, dict)
    }
    if observed_sources != SOURCE_SHA256:
        raise ValueError("T20.36d LeRobot source evidence drifted")
    dataset = _dict(manifest.get("dataset"), "manifest dataset")
    if (
        dataset.get("repo_id")
        != "scenesmith/t20-23-anchor-grasp-recovery-train"
        or dataset.get("revision") != "v3.0"
        or dataset.get("total_episodes") != 10
        or dataset.get("total_frames") != 2330
    ):
        raise ValueError("T20.36d canonical dataset boundary drifted")


def _feature_contract(info: dict[str, Any]) -> dict[str, Any]:
    if info.get("total_episodes") != 10 or info.get("total_frames") != 2330:
        raise ValueError("T20.36d dataset counts drifted")
    features = _dict(info.get("features"), "dataset features")
    state = _dict(features.get("observation.state"), "state feature")
    action = _dict(features.get("action"), "action feature")
    image_keys = sorted(
        key
        for key, value in features.items()
        if isinstance(value, dict) and value.get("dtype") == "image"
    )
    if (
        image_keys != IMAGE_FEATURE_KEYS
        or state.get("shape") != [6]
        or action.get("shape") != [6]
        or state.get("names") != JOINT_NAMES
        or action.get("names") != JOINT_NAMES
        or any(features[key].get("shape") != [3, 256, 256] for key in image_keys)
    ):
        raise ValueError("T20.36d dataset feature contract drifted")
    return {
        "state_dimension": 6,
        "action_dimension": 6,
        "joint_names": JOINT_NAMES,
        "image_feature_keys": image_keys,
        "image_shape": [3, 256, 256],
    }


def _normalization_statistics(stats: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ("action", "observation.state"):
        source = _dict(stats.get(key), f"{key} statistics")
        mean = _six_finite(source.get("mean"), f"{key} mean")
        std = _six_finite(source.get("std"), f"{key} standard deviation")
        if any(value <= 0.0 for value in std) or source.get("count") != [2330]:
            raise ValueError(f"T20.36d {key} statistics are invalid")
        result[key] = {"mean": mean, "std": std, "count": [2330]}
    return result


def _episode_zero(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = manifest.get("episodes")
    if not isinstance(rows, list):
        raise ValueError("T20.36d dataset episode evidence is missing")
    matches = [row for row in rows if isinstance(row, dict) and row.get("episode_index") == 0]
    if len(matches) != 1:
        raise ValueError("T20.36d dataset episode zero is missing or duplicated")
    row = matches[0]
    if row.get("eligible") is not True or row.get("frame_count") != 244:
        raise ValueError("T20.36d dataset episode zero is not eligible and complete")
    for key in ("raw_rollout_identity_sha256", "episode_content_sha256"):
        _sha(row.get(key), f"episode zero {key}")
    return row


def _artifact_ref(path: Path, payload: dict[str, Any], file_sha256: str) -> dict[str, Any]:
    return {
        "path": str(path),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": file_sha256,
    }


def _six_finite(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError(f"T20.36d {label} must contain six values")
    result = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"T20.36d {label} must be finite")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError(f"T20.36d {label} must be finite")
        result.append(number)
    return result


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.36d {label} is not a lowercase SHA-256")
    return value


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"T20.36d {label} is invalid")
    return value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
