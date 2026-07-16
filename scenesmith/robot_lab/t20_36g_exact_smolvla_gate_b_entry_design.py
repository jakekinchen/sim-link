"""Design-only exact SmolVLA Gate B entry contract for T20.36g."""

from __future__ import annotations

import hashlib
import json

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36d_exact_act_gate_b_control_design import (
    IMAGE_FEATURE_KEYS,
    JOINT_NAMES,
    NORMALIZATION_MAPPING,
    verify_spec_file as verify_act_spec_file,
)
from scenesmith.robot_lab.t20_36f_act_decode_localization import (
    RESULT_PATH as ACT_LOCALIZATION_PATH,
    verify_result as verify_act_localization_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36c_local_policy_track_preflight.json"
)
SOURCE_ATTEMPT_PATH = Path(
    "outputs/robot_lab/t20_36f_act_decode_localization_run_001/attempt.json"
)
SOURCE_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36f_act_decode_localization_permit.json"
)
SPEC_PATH = Path(
    "configurations/robot_lab/t20_36g_exact_smolvla_gate_b_entry_spec.json"
)
SMOLVLA_SOURCE_PATHS = [
    Path("external/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py"),
    Path("external/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py"),
    Path("external/lerobot/src/lerobot/policies/smolvla/processor_smolvla.py"),
    Path("external/lerobot/src/lerobot/policies/smolvla/smolvlm_with_expert.py"),
    Path("external/lerobot/src/lerobot/policies/pretrained.py"),
    Path("external/lerobot/src/lerobot/processor/batch_processor.py"),
    Path("external/lerobot/src/lerobot/processor/normalize_processor.py"),
    Path("external/lerobot/src/lerobot/processor/tokenizer_processor.py"),
]
SMOLVLA_SNAPSHOT = (
    Path.home()
    / ".cache/huggingface/hub/models--lerobot--smolvla_base/snapshots"
    / "c83c3163b8ca9b7e67c509fffd9121e66cb96205"
)
VLM_SNAPSHOT = (
    Path.home()
    / ".cache/huggingface/hub/models--HuggingFaceTB--SmolVLM2-500M-Video-Instruct/snapshots"
    / "7b375e1b73b11138ff12fe22c8f2822d8fe03467"
)
ATTEMPT_PATH = Path(
    "outputs/robot_lab/t20_36h_exact_smolvla_gate_b_run_001/attempt.json"
)
RESULT_PATH = Path(
    "outputs/robot_lab/t20_36h_exact_smolvla_gate_b_run_001/result.json"
)
SCHEMA_VERSION = "scenesmith.t20_36g_exact_smolvla_gate_b_entry_spec.v1"
TASK_ID = "T20.36g"
EXECUTION_TASK_ID = "T20.36h"
EXPECTED_LOCAL_PREFLIGHT_IDENTITY = (
    "61fcf124ab23d2e27672f8335ade0e74df10254ca58d4aec5a77b606ef328bcb"
)
EXPECTED_LOCALIZATION_IDENTITY = (
    "472e5ec5aabf36d9f280d2daf3f90b40988ccbc6d236b27cf3b3289755681ffb"
)
EXPECTED_ACT_SPEC_IDENTITY = (
    "45c90dc05578546e589cbde28ac3f072e0a8b87c2dd1001f343a8d7f4d586a4b"
)
EXPECTED_BASE_CONFIG_SHA256 = (
    "650584b56c104720f7a3c91d1ec6bec9e8de8ac11e60c92ba2fa82d93eda147d"
)
EXPECTED_SOURCE_SHA256 = {
    "configuration_smolvla.py": (
        "2fb637cb428fa2fdf1d114646dcffaf4728216bfe5b7039d5d0cac4857ffc4e0"
    ),
    "modeling_smolvla.py": (
        "5daaa297954acf9ae89397b571322f07bf30798e72f566e61a09393342cb1f99"
    ),
    "processor_smolvla.py": (
        "d34594291b2ecf7801f8c27a940a998c52a7e308cbc89f2403c9cbecfb368f22"
    ),
    "smolvlm_with_expert.py": (
        "f7542fa2bf904f9ef64d26843809f913a5e93c4dfa538dda06db0b288391ab4d"
    ),
    "pretrained.py": (
        "39e30b8ff6216d71c59a1a798b5693cbb356659d9fc23597d83232c76eaf0e36"
    ),
    "batch_processor.py": (
        "3e5c1d21468b6852bfe5df6c0ab03a81731f580dc4f69623c0aa458c52ae88f6"
    ),
    "normalize_processor.py": (
        "e9c4745d44f6f3808a84ed7ee9bc23b99ad930cc14222030e9167d4999da1012"
    ),
    "tokenizer_processor.py": (
        "7ba06e58a833a013421e67f74ffa992e6237df838c2b787711bf0c3156895b72"
    ),
}
TRAINING_SEED = 20260801
INFERENCE_SEEDS = [20260811, 20260812, 20260813, 20260814, 20260815]
OBJECTIVE_SEEDS = [20260821, 20260822, 20260823, 20260824, 20260825]
MAXIMUM_OPTIMIZER_UPDATES = 2000
EVALUATION_UPDATE_SCHEDULE = [0, 100, 250, 500, 1000, 2000]
LEARNING_RATE = 1e-4


def load_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    from scenesmith.robot_lab.t20_36f_act_decode_localization import (
        load_verified_sources as load_act_audit_sources,
    )

    act_audit_sources = load_act_audit_sources(repo_root=root)
    permit = load_strict_json(root / SOURCE_PERMIT_PATH)
    attempt = load_strict_json(root / SOURCE_ATTEMPT_PATH)
    localization = load_strict_json(root / ACT_LOCALIZATION_PATH)
    verify_act_localization_result(
        localization, permit=permit, attempt=attempt
    )
    return {
        "local_preflight": load_strict_json(root / LOCAL_PREFLIGHT_PATH),
        "act_spec": verify_act_spec_file(repo_root=root),
        "act_localization": localization,
        "act_audit_source_result": act_audit_sources["source_result"],
        "base_config": json.loads(
            (SMOLVLA_SNAPSHOT / "config.json").read_text(encoding="utf-8")
        ),
        "base_config_sha256": _file_sha256(SMOLVLA_SNAPSHOT / "config.json"),
        "source_file_sha256": {
            path.name: _file_sha256(root / path) for path in SMOLVLA_SOURCE_PATHS
        },
    }


def build_spec(*, sources: dict[str, Any]) -> dict[str, Any]:
    _verify_sources(sources)
    preflight = sources["local_preflight"]
    act_spec = sources["act_spec"]
    localization = sources["act_localization"]
    base = sources["base_config"]
    canonical_inputs = act_spec["act_config"]["input_features"]
    input_features = {
        key: canonical_inputs[key]
        for key in [*IMAGE_FEATURE_KEYS, "observation.state"]
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "execution_task_id": EXECUTION_TASK_ID,
        "scope": "design_only_exact_local_smolvla_one_batch_gate_b_entry",
        "source_identities": {
            "local_policy_preflight": preflight["identity_sha256"],
            "canonical_batch_spec": act_spec["identity_sha256"],
            "act_gate_b_control_result": sources["act_audit_source_result"][
                "identity_sha256"
            ],
            "act_decode_localization": localization["identity_sha256"],
            "lerobot_head": preflight["lerobot_source"]["head"],
        },
        "source_files": [
            {
                "path": str(path),
                "sha256": sources["source_file_sha256"][path.name],
            }
            for path in SMOLVLA_SOURCE_PATHS
        ],
        "local_cache": {
            "policy_repo_id": "lerobot/smolvla_base",
            "policy_revision": preflight["cache_inventory"]["smolvla_base"][
                "revision"
            ],
            "policy_snapshot": str(SMOLVLA_SNAPSHOT),
            "policy_files": preflight["cache_inventory"]["smolvla_base"][
                "files"
            ],
            "policy_config_sha256": sources["base_config_sha256"],
            "vlm_repo_id": base["vlm_model_name"],
            "vlm_revision": preflight["cache_inventory"]["smolvlm_base"][
                "revision"
            ],
            "vlm_snapshot": str(VLM_SNAPSHOT),
            "vlm_files": preflight["cache_inventory"]["smolvlm_base"]["files"],
            "tensor_content_read_at_design": False,
            "checkpoint_integrity_requires_execution_preflight": True,
            "network_fallback_allowed": False,
        },
        "canonical_batch": {
            **act_spec["source_batch"],
            "batch_evidence_required": {
                "physical_action_chunk_sha256": (
                    "5698babc07b2eebc8a3a96d33b28f03bbb33f1bec9b83a97d4e4f8a325c36b7e"
                ),
                "physical_state_sha256": (
                    "efd3788785f8c60ac67d91fcb2e754c9b3c13d62798469fbf811a968c8941ec4"
                ),
                "base_image_tensor_sha256": (
                    "5ed2cbd3740a3a377bf705eb6fb0bad4b1d0c9d40a8ef91ed0eaadac65e3fa87"
                ),
                "wrist_image_tensor_sha256": (
                    "10362eecfea21ed2cda3b0fe4f4b7246700b0dea13237b9575af323c2d9a649d"
                ),
            },
            "joint_names": JOINT_NAMES,
            "task": (
                "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."
            ),
        },
        "normalization": {
            **act_spec["normalization"],
            "policy_specific_processor_implementation": (
                "lerobot.policies.smolvla.processor_smolvla."
                "make_smolvla_pre_post_processors"
            ),
            "shared_contract_claim_limited_to_dataset_statistics_and_physical_round_trip": True,
        },
        "coordinate_round_trip": act_spec["coordinate_round_trip"],
        "camera_override": {
            "cached_features": list(base["input_features"]),
            "canonical_features": IMAGE_FEATURE_KEYS,
            "override_mode": "replace_cached_image_feature_map_before_model_construction",
            "empty_cameras": 0,
            "missing_camera_padding_allowed": False,
            "duplicate_camera_allowed": False,
            "synthetic_camera_allowed": False,
            "silent_camera_drop_allowed": False,
            "processor_uses_configured_feature_keys": True,
        },
        "smolvla_config": {
            **{
                key: base[key]
                for key in (
                    "adapt_to_pi_aloha",
                    "add_image_special_tokens",
                    "attention_mode",
                    "chunk_size",
                    "expert_width_multiplier",
                    "freeze_vision_encoder",
                    "load_vlm_weights",
                    "max_action_dim",
                    "max_state_dim",
                    "n_action_steps",
                    "n_obs_steps",
                    "num_expert_layers",
                    "num_steps",
                    "num_vlm_layers",
                    "pad_language_to",
                    "prefix_length",
                    "resize_imgs_with_padding",
                    "self_attn_every_n_layers",
                    "tokenizer_max_length",
                    "train_expert_only",
                    "train_state_proj",
                    "use_amp",
                    "use_cache",
                    "use_delta_joint_actions_aloha",
                )
            },
            "device": "mps",
            "compile_model": False,
            "input_features": input_features,
            "output_features": act_spec["act_config"]["output_features"],
            "normalization_mapping": NORMALIZATION_MAPPING,
            "empty_cameras": 0,
            "vlm_model_name": str(VLM_SNAPSHOT),
        },
        "batch_construction": {
            "dataset_item_is_unbatched": True,
            "construction": "torch.utils.data.default_collate([dataset_item])",
            "reason": (
                "AddBatchDimensionProcessorStep does not add a batch axis to a "
                "rank-2 horizon action chunk"
            ),
            "preprocessor_must_not_change_existing_batch_axes": True,
            "processed_action_shape": [1, 50, 6],
            "processed_state_shape": [1, 6],
            "processed_image_shape_by_key": {
                key: [1, 3, 256, 256] for key in IMAGE_FEATURE_KEYS
            },
            "token_batch_size": 1,
            "token_sequence_length": base["tokenizer_max_length"],
        },
        "runtime_contract": {
            "policy_constructor": "SmolVLAPolicy.from_pretrained",
            "policy_checkpoint_path": str(SMOLVLA_SNAPSHOT),
            "vlm_source_repo_id": base["vlm_model_name"],
            "vlm_checkpoint_path": str(VLM_SNAPSHOT),
            "policy_config_passed_explicitly": True,
            "local_files_only": True,
            "huggingface_hub_offline": True,
            "transformers_offline": True,
            "network_access_allowed": False,
            "requested_device": "mps",
            "cpu_fallback_allowed": False,
            "compile_model": False,
            "vlm_constructor_requested_dtype_from_source": "bfloat16",
            "observed_parameter_dtype_inventory_required": True,
            "observed_buffer_dtype_inventory_required": True,
            "torch_transformers_safetensors_versions_required": True,
            "model_train_mode_required_before_optimizer": True,
        },
        "trainable_scope": {
            "mode": "pretrained_policy_expert_only_plus_state_projection",
            "freeze_vision_encoder": True,
            "train_expert_only": True,
            "train_state_proj": True,
            "full_vlm_training": False,
            "peft": False,
            "runtime_trainable_parameter_inventory_required": True,
        },
        "campaign": {
            "optimizer": "AdamW",
            "learning_rate": LEARNING_RATE,
            "betas": [0.9, 0.95],
            "epsilon": 1e-8,
            "weight_decay": 1e-10,
            "gradient_clip_norm": 10.0,
            "scheduler": None,
            "scheduler_warmup_steps": 0,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "evaluation_update_schedule": EVALUATION_UPDATE_SCHEDULE,
            "training_seed": TRAINING_SEED,
            "objective_seeds": OBJECTIVE_SEEDS,
            "inference_seeds": INFERENCE_SEEDS,
            "batch_size": 1,
            "fixed_batch_repeated": True,
            "network_mode": "offline_local_cache_only",
            "device": "mps",
            "one_attempt_only": True,
            "retry_or_sweep_allowed": False,
            "stop_at_first_post_baseline_gate_b_pass": True,
            "otherwise_stop_after_maximum_updates": True,
            "attempt_marker_path": str(ATTEMPT_PATH),
        },
        "finite_evidence": {
            "baseline_objective": True,
            "every_training_loss": True,
            "every_gradient_norm": True,
            "every_scheduled_objective": True,
            "every_decoded_action_element": True,
            "every_physical_error_element": True,
            "non_finite_value_fails_closed": True,
        },
        "checkpoint_contract": {
            "format": "lerobot_save_pretrained_single_model_safetensors",
            "scheduled_evaluations_are_in_memory": True,
            "save_only_selected_pass_or_terminal_checkpoint": True,
            "model_file": "model.safetensors",
            "config_file": "config.json",
            "preprocessor_and_postprocessor_saved": True,
            "all_saved_file_sha256_required": True,
            "optimizer_state_saved": False,
        },
        "result_contract": {
            "path": str(RESULT_PATH),
            "signed_canonical_json": True,
            "source_spec_authority_permit_attempt_and_checkpoint_bound": True,
            "evaluation_schedule_complete_through_selected_update": True,
        },
        "evaluation": {
            "flow_decode_steps": base["num_steps"],
            "fixed_noise_seed_count": 5,
            "all_action_hashes_must_be_deterministic_per_seed": True,
            "physical_error_basis": (
                "decoded_lerobot_action_converted_to_mujoco_radian_"
                "vs_exact_source_measured_chunk"
            ),
            "report_per_joint_and_time_region": True,
            "closed_loop": False,
        },
        "gate": {
            "maximum_final_to_baseline_supervised_objective_ratio": 0.10,
            "maximum_physical_action_error_rad": 0.05,
            "all_action_dimensions_and_timesteps_must_pass": True,
            "all_inference_seeds_must_pass": True,
            "gate_b_threshold_changed": False,
            "task_consequence_metrics_report_only": True,
        },
        "result_routing": {
            "pass": "design_separate_smolvla_gate_c_training_episode_reproduction",
            "fail": "localize_smolvla_architecture_optimizer_and_boundary_error",
            "policy_track_selected_by_result_claim": False,
            "gate_c_authorized_by_spec": False,
        },
        "required_execution_preflight": {
            "full_policy_and_vlm_checkpoint_hashes": True,
            "offline_exact_snapshot_resolution": True,
            "mps_backend_available": True,
            "mps_model_construction_smoke": True,
            "mps_forward_backward_smoke": True,
            "finite_loss_and_gradient_smoke": True,
            "no_cpu_parameter_or_buffer_fallback": True,
            "runtime_dtype_inventory": True,
            "runtime_trainable_parameter_inventory": True,
            "two_camera_processor_shapes_and_tokens": True,
            "default_collated_action_shape": [1, 50, 6],
            "free_disk_bytes_minimum": 6 * 1024 * 1024 * 1024,
            "remote_source_commit_match": True,
            "task_specific_central_authority": True,
            "attempt_marker_precedes_model_construction": True,
        },
        "model_constructed": False,
        "checkpoint_tensor_read": False,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
        "policy_track_selected": False,
        "smolvla_entry_authorized": False,
        "gate_b_threshold_changed": False,
        "gate_c_authorized": False,
        "closed_loop_rollout": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    return sign_payload(payload)


def verify_spec(payload: dict[str, Any], *, sources: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36g SmolVLA entry spec")
    expected = build_spec(sources=sources)
    if payload != expected:
        raise ValueError("T20.36g SmolVLA entry spec drifted")


def write_spec(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = load_sources(repo_root=repo_root)
    spec = build_spec(sources=sources)
    dump_canonical_json(Path(repo_root) / SPEC_PATH, spec)
    return spec


def verify_spec_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = load_sources(repo_root=repo_root)
    spec = load_strict_json(Path(repo_root) / SPEC_PATH)
    verify_spec(spec, sources=sources)
    return spec


def _verify_sources(sources: dict[str, Any]) -> None:
    preflight = sources.get("local_preflight")
    act_spec = sources.get("act_spec")
    localization = sources.get("act_localization")
    base = sources.get("base_config")
    if not all(isinstance(value, dict) for value in (preflight, act_spec, localization, base)):
        raise ValueError("T20.36g source bundle is incomplete")
    verify_signed_payload(preflight, label="T20.36g local preflight")
    verify_signed_payload(act_spec, label="T20.36g ACT batch spec")
    verify_signed_payload(localization, label="T20.36g ACT localization")
    if (
        preflight["identity_sha256"] != EXPECTED_LOCAL_PREFLIGHT_IDENTITY
        or act_spec["identity_sha256"] != EXPECTED_ACT_SPEC_IDENTITY
        or localization["identity_sha256"] != EXPECTED_LOCALIZATION_IDENTITY
        or sources.get("base_config_sha256") != EXPECTED_BASE_CONFIG_SHA256
        or sources.get("source_file_sha256") != EXPECTED_SOURCE_SHA256
        or base.get("type") != "smolvla"
        or base.get("chunk_size") != 50
        or base.get("n_action_steps") != 50
        or set(base.get("input_features", {}))
        != {
            "observation.images.camera1",
            "observation.images.camera2",
            "observation.images.camera3",
            "observation.state",
        }
    ):
        raise ValueError("T20.36g frozen source identity drifted")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
