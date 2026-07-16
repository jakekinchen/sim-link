"""Fail-closed contracts for the T20.44/R2 SmolVLA standard rung.

This module is model-free.  It binds the reviewed R0 dataset, exact standard
SmolVLA recipe, Gate A evidence, central authority, runtime preflight, one-use
permit, marker, and pre-run acceptance.  It never constructs a policy or
optimizer and never executes a rollout.
"""

from __future__ import annotations

import hashlib
import math

from datetime import datetime
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.authority_composer import (
    DEFAULT_AUTHORITY_SCOPE_ID,
    DEFAULT_AUTHORITY_SUBJECT_ID,
    build_authority_contract,
    build_capability_claim,
    build_composition_request,
    build_evidence_ref,
    compose_authority,
    require_global_decision,
    verify_authority_decision,
)
from scenesmith.robot_lab.quantitative_strict_v2_receipt import (
    load_verified_sources as load_t20_38_sources,
    verify_quantitative_receipt,
)
from scenesmith.robot_lab.t20_36l_frozen_consequence_gate import (
    verify_spec as verify_frozen_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "T20.44"
BRANCH = "codex/pi05-autolearn-loop"
SOURCE_RESULT_COMMIT = "2e6a3e34406e0b251b9af4b7a6b83100e18af785"
LEROBOT_SOURCE_COMMIT = "e40b58a8dfa9e7b86918c374791599d070518d11"
TRAINING_SEED = 20260831
MAXIMUM_OPTIMIZER_UPDATES = 5_000
BATCH_SIZE = 8
CHECKPOINT_SCHEDULE = (0, 500, 1000, 2500, 5000)
CHUNK_SIZE = 50
EVALUATION_ACTION_STEPS = (50, 10)
GATE_C_SEED = 0
SAMPLE_INDICES = (
    0,
    2091,
    4182,
    6273,
    8364,
    10455,
    12546,
    14637,
    16728,
    18819,
    20910,
    23001,
    25092,
    27183,
    29274,
    31365,
)

SPEC_PATH = Path("configurations/robot_lab/t20_44_r2_smolvla_standard_spec.json")
GATE_A_PATH = Path("configurations/robot_lab/t20_44_r2_smolvla_gate_a.json")
OWNER_GRANT_PATH = Path(
    "configurations/robot_lab/t20_44_r2_smolvla_owner_authorization.json"
)
REQUEST_PATH = Path("configurations/robot_lab/t20_44_r2_smolvla_authority_request.json")
DECISION_PATH = Path(
    "configurations/robot_lab/t20_44_r2_smolvla_authority_decision.json"
)
RUNTIME_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_44_r2_smolvla_runtime_preflight.json"
)
PERMIT_PATH = Path("configurations/robot_lab/t20_44_r2_smolvla_permit.json")
PRE_RUN_ACCEPTANCE_PATH = Path(
    "configurations/robot_lab/t20_44_r2_smolvla_pre_run_acceptance.json"
)
ATTEMPT_PATH = Path("configurations/robot_lab/t20_44_r2_smolvla_attempt.json")
RESULT_PATH = Path("configurations/robot_lab/t20_44_r2_smolvla_result.json")
FAILURE_PATH = Path("configurations/robot_lab/t20_44_r2_smolvla_terminal_failure.json")
RETENTION_PATH = Path(
    "configurations/robot_lab/t20_44_r2_smolvla_retention_receipt.json"
)
SCORECARD_PATH = Path("configurations/robot_lab/t20_44_r2_smolvla_scorecard.json")
RUN_ROOT = Path("outputs/robot_lab/t20_44_r2_smolvla_run_001")
CHECKPOINT_ROOT = RUN_ROOT / "checkpoints"
ROLLOUT_ROOT = RUN_ROOT / "rollouts"
VIDEO_ROOT = RUN_ROOT / "mirrors"
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
RENDERER_SMOKE_ROOT = Path("outputs/robot_lab/t20_44_r2_renderer_smoke_001")
RENDERER_SMOKE_VIDEO_PATH = RENDERER_SMOKE_ROOT / "checkpoint_0_chunk_50.mp4"
RENDERER_SMOKE_MANIFEST_PATH = RENDERER_SMOKE_VIDEO_PATH.with_suffix(".manifest.json")
RENDERER_SMOKE_RECEIPT_PATH = Path(
    "configurations/robot_lab/t20_44_r2_renderer_smoke.json"
)

R0_RESULT_PATH = Path("configurations/robot_lab/t20_42_r0_generation_result.json")
R0_MIXTURE_PATH = Path(
    "configurations/robot_lab/t20_42_r0_dataset_mixture_manifest.json"
)
R0_STATISTICS_PATH = Path("configurations/robot_lab/t20_42_r0_dataset_statistics.json")
R0_RETENTION_PATH = Path("configurations/robot_lab/t20_42_r0_retention_receipt.json")
R0_DATASET_MANIFEST_PATH = Path(
    "outputs/robot_lab/t20_42_r0_generation_run_001/lerobot_dataset_manifest.json"
)
R0_DATASET_ROOT = Path("outputs/robot_lab/t20_42_r0_generation_run_001/lerobot_dataset")
R0_DATASET_REPO_ID = "scenesmith/t20-42-r0-anchor-grasp-train"
FROZEN_GATE_PATH = Path("configurations/robot_lab/t20_36l_frozen_consequence_gate.json")
T20_38_RECEIPT_PATH = Path(
    "configurations/robot_lab/t20_38_strict_v2_quantitative_receipt.simulation_only.json"
)
INHERITED_REQUEST_PATH = Path(
    "configurations/robot_lab/t20_23_simulation_training_authority_request.json"
)
INHERITED_DECISION_PATH = Path(
    "configurations/robot_lab/t20_23_simulation_training_authority_decision.json"
)
T20_43_FAILURE_PATH = Path(
    "configurations/robot_lab/t20_43_r1_act_terminal_failure.json"
)
T20_36I_CLOSURE_PATH = Path(
    "configurations/robot_lab/t20_36i_smolvla_dependency_closure.json"
)
T20_36J_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36j_corrected_environment_preflight.json"
)
T20_36J_INSTALLED_CLOSURE_PATH = Path(
    "configurations/robot_lab/t20_36j_installed_dependency_closure.json"
)
T20_36J_PROCESSOR_SMOKE_PATH = Path(
    "configurations/robot_lab/t20_36j_offline_auto_processor_smoke.json"
)
T20_36J_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36j_exact_smolvla_gate_b_result.json"
)
POLICY_REVISION = "c83c3163b8ca9b7e67c509fffd9121e66cb96205"
VLM_REVISION = "7b375e1b73b11138ff12fe22c8f2822d8fe03467"
POLICY_SNAPSHOT_PATH = (
    Path.home()
    / ".cache/huggingface/hub/models--lerobot--smolvla_base/snapshots"
    / POLICY_REVISION
)
VLM_SNAPSHOT_PATH = (
    Path.home()
    / ".cache/huggingface/hub/models--HuggingFaceTB--SmolVLM2-500M-Video-Instruct/snapshots"
    / VLM_REVISION
)
POLICY_WEIGHTS_SHA256 = (
    "7cd549ac2351fb069c0ddb3c34ad2d09cfc92b56a15dccdfc2e41467aaca01eb"
)
POLICY_WEIGHTS_BYTES = 906_712_520
VLM_WEIGHTS_SHA256 = "b9bfd456c9472c0acd5719d6e514c4b859891af205ee1a736552fd3497b8b0c3"
VLM_WEIGHTS_BYTES = 2_029_990_624
MUJOCO_SUPPORT_SITE_PACKAGES = Path(
    "/Users/kelly/.cache/uv/archive-v0/jImpGSbFmnkCImQkijLNh/"
    "lib/python3.12/site-packages"
)
RENDERER_SMOKE_TRACE_PATH = Path(
    "outputs/robot_lab/t20_43_r1_act_run_001/rollouts/step_00000_chunk_50.json"
)
RENDERER_SMOKE_TRACE_IDENTITY = (
    "6133ce582936d6f2057cff2877df1a7d66b7cb2397fbcc1032286fbf16a59507"
)

SPEC_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_standard_spec.v1"
GATE_A_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_gate_a.v1"
OWNER_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_owner_authorization.v1"
RUNTIME_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_runtime_preflight.v1"
PERMIT_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_permit.v1"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_attempt.v1"
ACCEPTANCE_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_pre_run_acceptance.v1"
MAXIMUM_AUTHORITY_SECONDS = 8 * 60 * 60
MINIMUM_FREE_DISK_BYTES = 10 * 1024**3
EXPECTED_DEPENDENCIES = {
    "python": "3.12.12",
    "torch": "2.11.0",
    "torchvision": "0.26.0",
    "transformers": "5.5.4",
    "safetensors": "0.8.0",
    "accelerate": "1.14.0",
    "num2words": "0.5.14",
    "docopt": "0.6.2",
    "psutil": "7.2.2",
    "datasets": "4.8.5",
    "mujoco": "3.3.5",
    "numpy": "2.2.6",
    "pillow": "12.3.0",
    "pyarrow": "25.0.0",
    "lerobot": "0.6.1",
}

EXPECTED_SOURCE_IDENTITIES = {
    "r0_result": "d238379bce62d884833da0a449535e3dc24f988b8da573513ae684bbb19a5969",
    "r0_mixture": "37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df",
    "r0_statistics": "02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae",
    "r0_retention": "19d19fbaa315511fa0e7df736d3895089827da8f0b8a2aecd15a2a75885bd495",
    "r0_dataset_manifest": "bd36b7c491ba3c3e08ae3efd87febdbbb1f52f917cb258399484ba4f5311a184",
    "frozen_gate": "463477dc91e3fb36b0550b88d461a788709a7258f9825ad6644f98bf0c77e48f",
    "t20_38_receipt": "042bf0bee9dcca28449311a39f5e884106deabf604febc05b53b026ecaf71b4e",
    "t20_43_failure": "b64ec6d07296526c9931ccb061c005c037b59e828b392ceaa7dacc0e46b26a0c",
    "t20_36i_closure": "0804fd4fda9b255509428f70c50f24672bf99ea91f9a2c6166410d5b6a45cee8",
    "t20_36j_preflight": "3c9b5af93848b28e6454451b56bbce0740820b9e6741274d1db91638f24d9de4",
    "t20_36j_installed_closure": "ac8abed17c87b46cd0aa1dbead3ed6d675be0a1fa4cae0d5c07a55bbe685d0af",
    "t20_36j_processor_smoke": "5223d8f06f215e188e0b044ff2a078e0b1997da9120f93b9edd1be6cf14a75c3",
    "t20_36j_result": "08ef923d1ebcffde26055834db271e92bb068e0eb09f75c60078f2d8b548c4a1",
}

SMOLVLA_SOURCE_PATHS = (
    Path("external/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py"),
    Path("external/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py"),
    Path("external/lerobot/src/lerobot/policies/smolvla/processor_smolvla.py"),
    Path("external/lerobot/src/lerobot/policies/smolvla/smolvlm_with_expert.py"),
    Path("external/lerobot/src/lerobot/policies/pretrained.py"),
    Path("external/lerobot/src/lerobot/processor/batch_processor.py"),
    Path("external/lerobot/src/lerobot/processor/normalize_processor.py"),
    Path("external/lerobot/src/lerobot/processor/tokenizer_processor.py"),
    Path("external/lerobot/src/lerobot/datasets/lerobot_dataset.py"),
    Path("external/lerobot/src/lerobot/datasets/sampler.py"),
    Path("external/lerobot/src/lerobot/optim/factory.py"),
    Path("external/lerobot/src/lerobot/optim/schedulers.py"),
    Path("scenesmith/robot_lab/act_grasp_closed_loop.py"),
    Path("scenesmith/robot_lab/so101_coordinates.py"),
    Path("scenesmith/robot_lab/strict_grasp.py"),
    Path("scripts/robot_lab/render_rollout_mirror.py"),
)

AUTHORITY_PATHS = (
    RENDERER_SMOKE_RECEIPT_PATH,
    GATE_A_PATH,
    OWNER_GRANT_PATH,
    REQUEST_PATH,
    DECISION_PATH,
    RUNTIME_PREFLIGHT_PATH,
    PERMIT_PATH,
)
OUTPUT_PATHS = (
    PRE_RUN_ACCEPTANCE_PATH,
    ATTEMPT_PATH,
    RESULT_PATH,
    FAILURE_PATH,
    RETENTION_PATH,
    SCORECARD_PATH,
    RUN_ROOT,
    CHECKPOINT_ROOT,
    ROLLOUT_ROOT,
    VIDEO_ROOT,
    RUN_SUMMARY_PATH,
)

FALSE_AUTHORITY_FIELDS = (
    "hardware_accessed",
    "camera_accessed",
    "serial_accessed",
    "physical_motion",
    "physical_actuation",
    "network_accessed",
    "external_compute_started",
    "brev_compute_started",
    "physical_transfer_ready",
    "promotion_eligible",
    "t20_45_activated",
)


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    paths = {
        "r0_result": R0_RESULT_PATH,
        "r0_mixture": R0_MIXTURE_PATH,
        "r0_statistics": R0_STATISTICS_PATH,
        "r0_retention": R0_RETENTION_PATH,
        "r0_dataset_manifest": R0_DATASET_MANIFEST_PATH,
        "frozen_gate": FROZEN_GATE_PATH,
        "t20_38_receipt": T20_38_RECEIPT_PATH,
        "t20_43_failure": T20_43_FAILURE_PATH,
        "t20_36i_closure": T20_36I_CLOSURE_PATH,
        "t20_36j_preflight": T20_36J_PREFLIGHT_PATH,
        "t20_36j_installed_closure": T20_36J_INSTALLED_CLOSURE_PATH,
        "t20_36j_processor_smoke": T20_36J_PROCESSOR_SMOKE_PATH,
        "t20_36j_result": T20_36J_RESULT_PATH,
    }
    sources = {name: load_strict_json(root / path) for name, path in paths.items()}
    for name, expected in EXPECTED_SOURCE_IDENTITIES.items():
        verify_signed_payload(sources[name], label=f"T20.44 {name}")
        if sources[name].get("identity_sha256") != expected:
            raise ValueError(f"T20.44 reviewed source drifted: {name}")
    verify_frozen_gate(sources["frozen_gate"], repo_root=root)
    verify_quantitative_receipt(
        sources["t20_38_receipt"], sources=load_t20_38_sources(repo_root=root)
    )
    result = sources["r0_result"]
    mixture = sources["r0_mixture"]
    statistics = sources["r0_statistics"]
    manifest = sources["r0_dataset_manifest"]
    if (
        result.get("status") != "verified_success"
        or result.get("new_training_strict_success_count") != 119
        or result.get("fresh_held_out_strict_success_count") != 9
        or result.get("retry_authorized") is not False
        or mixture.get("base_included_exactly_once") is not True
        or mixture.get("base_episode_count") != 10
        or mixture.get("training_episode_count") != 129
        or mixture.get("training_frame_count") != 31366
        or mixture.get("fresh_held_out_training_rows") != 0
        or mixture.get("existing_held_out_training_rows") != 0
        or statistics.get("held_out_values_contributed_to_fit") is not False
        or manifest.get("dataset", {}).get("total_episodes") != 129
        or manifest.get("dataset", {}).get("total_frames") != 31366
    ):
        raise ValueError("T20.44 R0 training/held-out boundary drifted")
    inherited_request = load_strict_json(root / INHERITED_REQUEST_PATH)
    inherited_decision = load_strict_json(root / INHERITED_DECISION_PATH)
    verify_authority_decision(inherited_decision, request=inherited_request)
    require_global_decision(
        inherited_decision,
        request=inherited_request,
        decision_id="simulation_training_ready",
    )
    if inherited_decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.44 inherited authority exceeded simulation scope")
    if (
        sources["t20_43_failure"].get("retry_authorized") is not False
        or sources["t20_43_failure"].get("execution", {}).get("optimizer_update_count")
        != 0
        or sources["t20_36j_result"].get("optimizer_update_count") != 2000
        or sources["t20_36j_result"].get("gate_b_passed") is not False
        or sources["t20_36j_processor_smoke"].get("constructed") is not True
        or sources["t20_36j_processor_smoke"].get("network_attempted") is not False
    ):
        raise ValueError("T20.44 inherited SmolVLA/T20.43 boundary drifted")
    sources["inherited_request"] = inherited_request
    sources["inherited_decision"] = inherited_decision
    sources["source_refs"] = {
        name: artifact_ref(path=path, payload=sources[name], repo_root=root)
        for name, path in paths.items()
    }
    sources["source_refs"]["inherited_decision"] = artifact_ref(
        path=INHERITED_DECISION_PATH,
        payload=inherited_decision,
        repo_root=root,
    )
    sources["smolvla_source_files"] = [
        {
            "path": path.as_posix(),
            "file_sha256": _sha_file(root / path),
            "size_bytes": (root / path).stat().st_size,
        }
        for path in SMOLVLA_SOURCE_PATHS
    ]
    return sources


def build_spec(*, sources: dict[str, Any]) -> dict[str, Any]:
    _verify_sources(sources)
    payload = {
        "schema_version": SPEC_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "scope": "one_cached_base_smolvla_standard_recipe_r2_with_rollout_primary_evaluation",
        "source_result_commit": SOURCE_RESULT_COMMIT,
        "source_refs": dict(sources["source_refs"]),
        "lerobot_source_commit": LEROBOT_SOURCE_COMMIT,
        "smolvla_source_files": list(sources["smolvla_source_files"]),
        "dataset": {
            "root": R0_DATASET_ROOT.as_posix(),
            "repo_id": R0_DATASET_REPO_ID,
            "episode_count": 129,
            "frame_count": 31366,
            "sample_indices": list(SAMPLE_INDICES),
            "image_features": [
                "observation.images.base_0_rgb",
                "observation.images.left_wrist_0_rgb",
            ],
            "joint_names": [
                "shoulder_pan",
                "shoulder_lift",
                "elbow_flex",
                "wrist_flex",
                "wrist_roll",
                "gripper",
            ],
            "fresh_held_out_training_rows": 0,
            "existing_held_out_training_rows": 0,
            "normalization": "MEAN_STD",
            "statistics_source": "frozen_training_split_only",
        },
        "cached_base": {
            "policy_repo_id": "lerobot/smolvla_base",
            "policy_revision": POLICY_REVISION,
            "policy_snapshot_path": str(POLICY_SNAPSHOT_PATH),
            "policy_weights_sha256": POLICY_WEIGHTS_SHA256,
            "policy_weights_size_bytes": POLICY_WEIGHTS_BYTES,
            "vlm_repo_id": "HuggingFaceTB/SmolVLM2-500M-Video-Instruct",
            "vlm_revision": VLM_REVISION,
            "vlm_snapshot_path": str(VLM_SNAPSHOT_PATH),
            "vlm_weights_sha256": VLM_WEIGHTS_SHA256,
            "vlm_weights_size_bytes": VLM_WEIGHTS_BYTES,
            "retained_t20_36j_finetuned_checkpoint_allowed": False,
            "network_fallback_allowed": False,
        },
        "stable_runtime": {
            "python_interpreter": (
                "/Users/kelly/Developer/sim-link/external/lerobot/.venv/bin/python"
            ),
            "mujoco_support_site_packages": str(MUJOCO_SUPPORT_SITE_PACKAGES),
            "temporary_uv_build_interpreter_allowed": False,
            "package_installation_allowed": False,
        },
        "smolvla_config": {
            "policy_type": "smolvla",
            "initialization": "exact_cached_smolvla_base",
            "device": "mps",
            "dtype": "float32",
            "compile_model": False,
            "use_amp": False,
            "n_obs_steps": 1,
            "chunk_size": CHUNK_SIZE,
            "n_action_steps": CHUNK_SIZE,
            "normalization_mapping": {
                "VISUAL": "IDENTITY",
                "STATE": "MEAN_STD",
                "ACTION": "MEAN_STD",
            },
            "max_state_dim": 32,
            "max_action_dim": 32,
            "resize_imgs_with_padding": [512, 512],
            "empty_cameras": 0,
            "adapt_to_pi_aloha": False,
            "use_delta_joint_actions_aloha": False,
            "tokenizer_max_length": 48,
            "num_steps": 10,
            "use_cache": True,
            "freeze_vision_encoder": True,
            "train_expert_only": True,
            "train_state_proj": True,
            "full_vlm_training": False,
            "peft": False,
            "load_vlm_weights": True,
            "vlm_model_name": str(VLM_SNAPSHOT_PATH),
            "add_image_special_tokens": False,
            "attention_mode": "cross_attn",
            "prefix_length": 0,
            "pad_language_to": "max_length",
            "num_expert_layers": 0,
            "num_vlm_layers": 16,
            "self_attn_every_n_layers": 2,
            "expert_width_multiplier": 0.75,
        },
        "campaign": {
            "training_seed": TRAINING_SEED,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "batch_size": BATCH_SIZE,
            "sampler": "lerobot.datasets.EpisodeAwareSampler",
            "sampler_shuffle": True,
            "num_workers": 0,
            "optimizer": "AdamW",
            "learning_rate": 1e-4,
            "betas": [0.9, 0.95],
            "epsilon": 1e-8,
            "weight_decay": 1e-10,
            "gradient_clip_norm": 10.0,
            "scheduler": "CosineDecayWithWarmup",
            "scheduler_warmup_steps": 1000,
            "scheduler_decay_steps": 30000,
            "scheduler_decay_lr": 2.5e-6,
            "scheduler_effective_warmup_steps_at_5000": 166,
            "scheduler_effective_decay_steps_at_5000": 5000,
            "scheduler_auto_scaling_is_official_implementation": True,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "continue_to_maximum_after_gate_c_pass": True,
            "one_attempt_only": True,
            "retry_or_sweep_allowed": False,
            "sample_weighting": None,
            "correction_objective": None,
        },
        "gate_a": {
            "must_pass_before_marker": True,
            "model_construction": False,
            "optimizer_creation": False,
            "checks": [
                "r0_artifact_and_local_tree_identity",
                "dataset_count_feature_and_order",
                "training_only_statistics_match",
                "fixed_sample_tensor_hashes",
                "smolvla_processor_shapes_tokens_and_training_stats",
                "action_postprocessor_inverse_parity",
                "dataset_mujoco_coordinate_round_trip",
                "held_out_exclusion",
                "installed_smolvla_dependency_closure",
            ],
            "open_loop_gate_blocks_rollout": False,
        },
        "evaluation": {
            "oracle": "strict_v2_only",
            "seed": GATE_C_SEED,
            "frame_count": 244,
            "decode_noise_seed_formula": (
                "20260901 + checkpoint_update*100 + n_action_steps*10 + "
                "decode_start_frame"
            ),
            "evaluation_does_not_reseed_training_rng": True,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "variants": [
                {
                    "variant_id": "chunk_50",
                    "n_action_steps": 50,
                    "queue_reset_count": 1,
                    "decode_starts": [0, 50, 100, 150, 200],
                    "executed_lengths": [50, 50, 50, 50, 44],
                    "unexecuted_tail_actions": 6,
                },
                {
                    "variant_id": "receding_10",
                    "n_action_steps": 10,
                    "queue_reset_count": 1,
                    "decode_starts": list(range(0, 244, 10)),
                    "executed_lengths": [*[10] * 24, 4],
                    "unexecuted_tail_actions_per_decode_excluded": True,
                },
            ],
            "gate_c": (
                "first_scheduled_checkpoint_with_unassisted_episode_0_"
                "strict_v2_pass_under_either_variant"
            ),
            "same_checkpoint_tie_breaker": "chunk_50",
            "first_pass_cannot_be_replaced": True,
            "required_evidence": [
                "complete_trace",
                "first_source_divergence",
                "strict_v2_margins",
                "t20_38_bound_quantitative_margins",
                "frozen_amended_gate_report",
                "uniform_0_05_rad_report",
                "decode_and_action_hashes",
                "mirror_mp4_and_manifest",
            ],
        },
        "attempt_contract": {
            "authorized_attempt_count": 1,
            "marker_path": ATTEMPT_PATH.as_posix(),
            "marker_follows_renderer_and_dependency_smoke": True,
            "marker_precedes_policy_or_vlm_tensor_read_model_inference_optimizer": True,
            "retry_authorized": False,
        },
        "renderer_smoke": {
            "required_before_marker": True,
            "trace_path": RENDERER_SMOKE_TRACE_PATH.as_posix(),
            "trace_identity_sha256": RENDERER_SMOKE_TRACE_IDENTITY,
            "entrypoint": "scripts/robot_lab/render_rollout_mirror.py",
            "interpreter_must_equal_runner_interpreter": True,
            "mujoco_version": "3.3.5",
            "output_video_path": RENDERER_SMOKE_VIDEO_PATH.as_posix(),
            "output_manifest_path": RENDERER_SMOKE_MANIFEST_PATH.as_posix(),
            "receipt_path": RENDERER_SMOKE_RECEIPT_PATH.as_posix(),
            "exit_code": 0,
            "nonempty_mp4_required": True,
            "signed_manifest_required": True,
            "network_allowed": False,
            "model_weight_read": False,
        },
        "checkpoint_retention": {
            "local_tree_only": True,
            "tree_identity_required": True,
            "multi_gigabyte_git_tracking": False,
            "compact_evidence_git_tracking": True,
        },
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
        "learned_policy_rollout": False,
        "gate_c_executed": False,
        "r2_activated": False,
        "simulation_policy_accepted": False,
        **_false_authority_fields(),
    }
    return sign_payload(payload)


def verify_spec(payload: dict[str, Any], *, sources: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.44 standard spec")
    expected = build_spec(sources=sources)
    if payload != expected:
        raise ValueError("T20.44 standard spec drifted")


def build_gate_a(*, spec: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    _verify_gate_a_evidence(evidence)
    payload = {
        "schema_version": GATE_A_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "spec_identity_sha256": spec["identity_sha256"],
        "status": "pass",
        "evidence": evidence,
        "open_loop_entry_barrier": False,
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
        "learned_policy_rollout": False,
        "gate_c_executed": False,
        "simulation_policy_accepted": False,
        **_false_authority_fields(),
    }
    return sign_payload(payload)


def verify_gate_a(payload: dict[str, Any], *, spec: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.44 Gate A")
    if payload != build_gate_a(spec=spec, evidence=payload.get("evidence")):
        raise ValueError("T20.44 Gate A drifted")


def build_renderer_smoke(
    *, spec: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    required = {
        "trace_file_sha256",
        "runner_interpreter",
        "interpreter_version",
        "command",
        "exit_code",
        "stdout_sha256",
        "stderr_sha256",
        "mujoco_version",
        "video_file_sha256",
        "video_size_bytes",
        "manifest_identity_sha256",
        "manifest_file_sha256",
    }
    if not isinstance(evidence, dict) or set(evidence) != required:
        raise ValueError("T20.44 renderer smoke evidence fields drifted")
    for key in (
        "trace_file_sha256",
        "stdout_sha256",
        "stderr_sha256",
        "video_file_sha256",
        "manifest_identity_sha256",
        "manifest_file_sha256",
    ):
        _sha(evidence[key])
    if (
        not isinstance(evidence["runner_interpreter"], str)
        or not evidence["runner_interpreter"]
        or evidence["interpreter_version"] != "3.12.12"
        or evidence["exit_code"] != 0
        or evidence["mujoco_version"] != "3.3.5"
        or not isinstance(evidence["command"], list)
        or evidence["command"][0] != evidence["runner_interpreter"]
        or not any(
            str(part).endswith("scripts/robot_lab/render_rollout_mirror.py")
            for part in evidence["command"]
        )
        or evidence["video_size_bytes"] <= 0
    ):
        raise ValueError("T20.44 renderer smoke failed closed")
    return sign_payload(
        {
            "schema_version": "scenesmith.t20_44_r2_renderer_smoke.v1",
            "task_id": TASK_ID,
            "spec_identity_sha256": spec["identity_sha256"],
            "trace_path": RENDERER_SMOKE_TRACE_PATH.as_posix(),
            "trace_identity_sha256": RENDERER_SMOKE_TRACE_IDENTITY,
            "output_video_path": RENDERER_SMOKE_VIDEO_PATH.as_posix(),
            "output_manifest_path": RENDERER_SMOKE_MANIFEST_PATH.as_posix(),
            "interpreter_matches_runner": True,
            "model_or_weight_action_executed": False,
            "network_accessed": False,
            **evidence,
            **_false_authority_fields(),
        }
    )


def verify_renderer_smoke(payload: dict[str, Any], *, spec: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.44 renderer smoke")
    evidence = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "schema_version",
            "task_id",
            "spec_identity_sha256",
            "trace_path",
            "trace_identity_sha256",
            "output_video_path",
            "output_manifest_path",
            "interpreter_matches_runner",
            "model_or_weight_action_executed",
            "network_accessed",
            "identity_sha256",
            *FALSE_AUTHORITY_FIELDS,
        }
    }
    if payload != build_renderer_smoke(spec=spec, evidence=evidence):
        raise ValueError("T20.44 renderer smoke drifted")


def build_owner_grant(
    *,
    spec: dict[str, Any],
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
) -> dict[str, Any]:
    start, stop = _authority_window(valid_from, valid_until)
    return sign_payload(
        {
            "schema_version": OWNER_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "authorization_id": "t20_44_one_cached_base_smolvla_standard_r2_attempt",
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "spec_identity_sha256": spec["identity_sha256"],
            "required_source_commit": _commit(required_source_commit),
            "authorized_actions": [
                "verify_exact_runner_interpreter_renderer_smoke",
                "load_cached_smolvla_base_and_pinned_vlm",
                "construct_smolvla_policy",
                "run_smolvla_model_inference",
                "create_official_adamw_optimizer_and_cosine_scheduler",
                "execute_exactly_5000_simulation_training_updates",
                "save_fixed_schedule_checkpoints",
                "run_fixed_schedule_dual_semantics_mujoco_evaluations",
                "render_and_retain_signed_mirror_mp4",
            ],
            "authorized_attempt_count": 1,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "retry_or_sweep_authorized": False,
            "correction_objective_authorized": False,
            "threshold_change_authorized": False,
            "gate_b_entry_barrier_authorized": False,
            "simulation_only": True,
            "issued_at": start.isoformat(),
            "valid_from": start.isoformat(),
            "valid_until": stop.isoformat(),
            "maximum_authority_seconds": MAXIMUM_AUTHORITY_SECONDS,
            **_prohibited_authority_grants(),
        }
    )


def verify_owner_grant(payload: dict[str, Any], *, spec: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.44 owner grant")
    expected = build_owner_grant(
        spec=spec,
        required_source_commit=payload.get("required_source_commit"),
        valid_from=payload.get("valid_from"),
        valid_until=payload.get("valid_until"),
    )
    if payload != expected:
        raise ValueError("T20.44 owner grant drifted")


def build_central_authority(
    *,
    sources: dict[str, Any],
    spec: dict[str, Any],
    gate_a: dict[str, Any],
    owner_grant: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    verify_spec(spec, sources=sources)
    verify_gate_a(gate_a, spec=spec)
    verify_owner_grant(owner_grant, spec=spec)
    refs = {
        "owner": _prospective_ref(OWNER_GRANT_PATH, owner_grant),
        "spec": artifact_ref(path=SPEC_PATH, payload=spec, repo_root=REPO_ROOT),
        "gate_a": _prospective_ref(GATE_A_PATH, gate_a),
        "r0_result": dict(sources["source_refs"]["r0_result"]),
        "r0_mixture": dict(sources["source_refs"]["r0_mixture"]),
        "r0_statistics": dict(sources["source_refs"]["r0_statistics"]),
        "r0_dataset": dict(sources["source_refs"]["r0_dataset_manifest"]),
        "inherited_decision": dict(sources["source_refs"]["inherited_decision"]),
    }
    evidence = {
        "required_training_authority_present": [refs["owner"]],
        "structural_contract_valid": [refs["spec"], refs["r0_result"]],
        "executable_stack_valid": [refs["gate_a"], refs["spec"]],
        "coordinate_contract_valid": [refs["gate_a"], refs["r0_dataset"]],
        "normalization_contract_valid": [refs["gate_a"], refs["r0_statistics"]],
        "experience_compiler_valid": [refs["r0_mixture"], refs["r0_dataset"]],
        "required_simulation_properties_available": [
            refs["inherited_decision"],
            refs["gate_a"],
        ],
    }
    requirements = {
        row["prerequisite_id"]: row
        for row in build_authority_contract()["prerequisites"]
    }
    start = owner_grant["valid_from"]
    stop = owner_grant["valid_until"]
    claims = []
    for prerequisite_id, evidence_refs in sorted(evidence.items()):
        requirement = requirements[prerequisite_id]
        provenance = requirement["allowed_provenance_classes"][0]
        claims.append(
            build_capability_claim(
                claim_id=f"t20_44_{prerequisite_id}",
                capability_id=prerequisite_id,
                value=True,
                subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                provenance_class=provenance,
                issuer=requirement["authorized_issuers"][0],
                validity={
                    "observed_at": start,
                    "valid_from": start,
                    "valid_until": stop,
                    "max_age_seconds": MAXIMUM_AUTHORITY_SECONDS,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind="t20_44_r2_smolvla_evidence",
                        artifact_schema_version=ref["schema_version"],
                        artifact_identity_sha256=ref["identity_sha256"],
                        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                        provenance_class=provenance,
                    )
                    for ref in evidence_refs
                ],
            )
        )
    request = build_composition_request(
        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
        evaluation_time=start,
        claims=claims,
        composition_mode="production",
    )
    decision = compose_authority(request)
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.44 central authority exceeded simulation training")
    return request, decision


def build_runtime_preflight(
    *,
    spec: dict[str, Any],
    gate_a: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_snapshot: dict[str, Any],
) -> dict[str, Any]:
    verify_gate_a(gate_a, spec=spec)
    verify_owner_grant(owner_grant, spec=spec)
    verify_authority_decision(decision, request=request)
    _verify_runtime_snapshot(runtime_snapshot, owner_grant=owner_grant)
    return sign_payload(
        {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "spec_identity_sha256": spec["identity_sha256"],
            "gate_a_identity_sha256": gate_a["identity_sha256"],
            "owner_grant_identity_sha256": owner_grant["identity_sha256"],
            "authority_request_identity_sha256": request["identity_sha256"],
            "authority_decision_identity_sha256": decision["identity_sha256"],
            **runtime_snapshot,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "learned_policy_rollout": False,
            "gate_c_executed": False,
            **_false_authority_fields(),
        }
    )


def verify_runtime_preflight(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    gate_a: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.44 runtime preflight")
    runtime = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "schema_version",
            "task_id",
            "spec_identity_sha256",
            "gate_a_identity_sha256",
            "owner_grant_identity_sha256",
            "authority_request_identity_sha256",
            "authority_decision_identity_sha256",
            "identity_sha256",
            "model_constructed",
            "model_loaded",
            "model_inference",
            "optimizer_created",
            "optimizer_training",
            "learned_policy_rollout",
            "gate_c_executed",
            *FALSE_AUTHORITY_FIELDS,
        }
    }
    expected = build_runtime_preflight(
        spec=spec,
        gate_a=gate_a,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
        runtime_snapshot=runtime,
    )
    if payload != expected:
        raise ValueError("T20.44 runtime preflight drifted")


def build_permit(
    *,
    spec: dict[str, Any],
    gate_a: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_preflight: dict[str, Any],
) -> dict[str, Any]:
    verify_runtime_preflight(
        runtime_preflight,
        spec=spec,
        gate_a=gate_a,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
    )
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "spec_identity_sha256": spec["identity_sha256"],
            "gate_a_identity_sha256": gate_a["identity_sha256"],
            "owner_grant_identity_sha256": owner_grant["identity_sha256"],
            "authority_decision_identity_sha256": decision["identity_sha256"],
            "runtime_preflight_identity_sha256": runtime_preflight["identity_sha256"],
            "required_source_commit": owner_grant["required_source_commit"],
            "authorized_attempt_count": 1,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "evaluation_action_steps": list(EVALUATION_ACTION_STEPS),
            "attempt_marker_path": ATTEMPT_PATH.as_posix(),
            "renderer_smoke_identity_sha256": runtime_preflight[
                "renderer_smoke_identity_sha256"
            ],
            "marker_follows_renderer_and_dependency_smoke": True,
            "marker_precedes_policy_or_vlm_tensor_read_model_inference_optimizer": True,
            "retry_or_sweep_authorized": False,
            "correction_objective_authorized": False,
            "threshold_change_authorized": False,
            "hardware_authorized": False,
            "network_authorized": False,
            "external_compute_authorized": False,
            "brev_compute_authorized": False,
            "physical_transfer_authorized": False,
            "promotion_authorized": False,
            "r2_authorized": True,
            "t20_45_authorized": False,
        }
    )


def verify_permit(
    payload: dict[str, Any],
    *,
    spec: dict[str, Any],
    gate_a: dict[str, Any],
    owner_grant: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    runtime_preflight: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.44 permit")
    expected = build_permit(
        spec=spec,
        gate_a=gate_a,
        owner_grant=owner_grant,
        request=request,
        decision=decision,
        runtime_preflight=runtime_preflight,
    )
    if payload != expected:
        raise ValueError("T20.44 permit drifted")


def build_attempt_marker(
    *, permit: dict[str, Any], source_commit: str, started_at: str
) -> dict[str, Any]:
    started = _aware_time(started_at, label="attempt start")
    if permit.get("authorized_attempt_count") != 1:
        raise ValueError("T20.44 permit attempt count drifted")
    return sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "permit_identity_sha256": permit["identity_sha256"],
            "attempt_ordinal": 1,
            "source_commit": _commit(source_commit),
            "started_at": started.isoformat(),
            "renderer_and_dependency_smoke_completed": True,
            "created_before_policy_or_vlm_tensor_read": True,
            "created_before_model_construction": True,
            "created_before_model_inference": True,
            "created_before_optimizer_creation": True,
            "permit_consumed": True,
            "retry_authorized": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "learned_policy_rollout": False,
            "gate_c_executed": False,
            **_false_authority_fields(),
        }
    )


def verify_attempt_marker(payload: dict[str, Any], *, permit: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.44 attempt marker")
    expected = build_attempt_marker(
        permit=permit,
        source_commit=payload.get("source_commit"),
        started_at=payload.get("started_at"),
    )
    if payload != expected:
        raise ValueError("T20.44 attempt marker drifted")


def build_pre_run_acceptance(
    *,
    authority_commit: str,
    reviewer_decision_id: str,
    reviewer_path: str,
    reviewer_file_sha256: str,
    permit: dict[str, Any],
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": ACCEPTANCE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "decision": "ACCEPT_ONE_T20_44_R2_SMOLVLA_STANDARD_ATTEMPT",
            "authority_commit": _commit(authority_commit),
            "reviewer_decision_id": str(reviewer_decision_id),
            "reviewer_path": reviewer_path,
            "reviewer_file_sha256": _sha(reviewer_file_sha256),
            "permit_identity_sha256": permit["identity_sha256"],
            "attempt_marker_exists": False,
            "model_or_optimizer_action_executed": False,
            "retry_authorized": False,
            **_false_authority_fields(),
        }
    )


def verify_pre_run_acceptance(
    payload: dict[str, Any], *, permit: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.44 pre-run acceptance")
    expected = build_pre_run_acceptance(
        authority_commit=payload.get("authority_commit"),
        reviewer_decision_id=payload.get("reviewer_decision_id"),
        reviewer_path=payload.get("reviewer_path"),
        reviewer_file_sha256=payload.get("reviewer_file_sha256"),
        permit=permit,
    )
    if payload != expected:
        raise ValueError("T20.44 pre-run acceptance drifted")


def _verify_sources(sources: dict[str, Any]) -> None:
    if not isinstance(sources, dict) or set(EXPECTED_SOURCE_IDENTITIES) - set(sources):
        raise ValueError("T20.44 source bundle is incomplete")
    for name, expected in EXPECTED_SOURCE_IDENTITIES.items():
        if sources[name].get("identity_sha256") != expected:
            raise ValueError(f"T20.44 source identity drifted: {name}")
    if not isinstance(sources.get("source_refs"), dict) or not isinstance(
        sources.get("smolvla_source_files"), list
    ):
        raise ValueError("T20.44 source refs are incomplete")


def _verify_gate_a_evidence(evidence: Any) -> None:
    if not isinstance(evidence, dict):
        raise ValueError("T20.44 Gate A evidence must be an object")
    exact = {
        "dataset_episode_count": 129,
        "dataset_frame_count": 31366,
        "sample_indices": list(SAMPLE_INDICES),
        "sample_count": len(SAMPLE_INDICES),
        "action_shape": [50, 6],
        "state_shape": [6],
        "image_shapes": {
            "observation.images.base_0_rgb": [3, 256, 256],
            "observation.images.left_wrist_0_rgb": [3, 256, 256],
        },
        "fresh_held_out_training_rows": 0,
        "existing_held_out_training_rows": 0,
        "all_values_finite": True,
        "dataset_stats_match_compact_statistics": True,
        "processor_matches_manual_mean_std": True,
        "postprocessor_inverse_matches_actions": True,
        "coordinate_round_trip_passed": True,
    }
    for key, expected in exact.items():
        if evidence.get(key) != expected:
            raise ValueError(f"T20.44 Gate A evidence drifted: {key}")
    for key in (
        "dataset_tree_identity_sha256",
        "dataset_manifest_identity_sha256",
        "dataset_info_file_sha256",
        "dataset_stats_file_sha256",
        "sample_tensor_identity_sha256",
        "normalized_tensor_identity_sha256",
        "postprocessed_action_identity_sha256",
    ):
        _sha(evidence.get(key))
    for key in (
        "maximum_processor_manual_error",
        "maximum_postprocessor_inverse_error",
        "maximum_coordinate_round_trip_error_rad",
    ):
        value = _finite(evidence.get(key), label=key)
        if "postprocessor" in key:
            tolerance = 1e-5
        else:
            tolerance = 1e-6 if "coordinate" not in key else 1e-8
        if value > tolerance:
            raise ValueError(f"T20.44 Gate A tolerance failed: {key}")


def _verify_runtime_snapshot(snapshot: Any, *, owner_grant: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise ValueError("T20.44 runtime snapshot must be an object")
    required = {
        "source_commit",
        "branch",
        "origin_contains_source_commit",
        "scoped_dirty_paths",
        "dependencies",
        "mps_available",
        "free_disk_bytes",
        "network_enabled",
        "dependency_fallback_enabled",
        "policy_weights_file_sha256",
        "policy_weights_size_bytes",
        "vlm_weights_file_sha256",
        "vlm_weights_size_bytes",
        "policy_snapshot_tree_identity_sha256",
        "vlm_snapshot_tree_identity_sha256",
        "installed_dependency_closure_identity_sha256",
        "processor_smoke_identity_sha256",
        "renderer_smoke_identity_sha256",
        "renderer_interpreter",
        "mujoco_support_site_packages",
        "mujoco_support_tree_identity_sha256",
        "renderer_interpreter_matches_runner",
        "renderer_smoke_exit_code",
        "output_path_state",
        "authority_artifacts_materialized",
        "attempt_marker_exists",
    }
    if set(snapshot) != required:
        raise ValueError("T20.44 runtime snapshot field set drifted")
    if (
        snapshot["source_commit"] != owner_grant["required_source_commit"]
        or snapshot["branch"] != BRANCH
        or snapshot["origin_contains_source_commit"] is not True
        or snapshot["scoped_dirty_paths"] != []
        or snapshot["mps_available"] is not True
        or snapshot["free_disk_bytes"] < MINIMUM_FREE_DISK_BYTES
        or snapshot["network_enabled"] is not False
        or snapshot["dependency_fallback_enabled"] is not False
        or snapshot["policy_weights_file_sha256"] != POLICY_WEIGHTS_SHA256
        or snapshot["policy_weights_size_bytes"] != POLICY_WEIGHTS_BYTES
        or snapshot["vlm_weights_file_sha256"] != VLM_WEIGHTS_SHA256
        or snapshot["vlm_weights_size_bytes"] != VLM_WEIGHTS_BYTES
        or snapshot["installed_dependency_closure_identity_sha256"]
        != EXPECTED_SOURCE_IDENTITIES["t20_36j_installed_closure"]
        or snapshot["processor_smoke_identity_sha256"]
        != EXPECTED_SOURCE_IDENTITIES["t20_36j_processor_smoke"]
        or not isinstance(snapshot["policy_snapshot_tree_identity_sha256"], str)
        or len(snapshot["policy_snapshot_tree_identity_sha256"]) != 64
        or not isinstance(snapshot["vlm_snapshot_tree_identity_sha256"], str)
        or len(snapshot["vlm_snapshot_tree_identity_sha256"]) != 64
        or not isinstance(snapshot["renderer_smoke_identity_sha256"], str)
        or len(snapshot["renderer_smoke_identity_sha256"]) != 64
        or not isinstance(snapshot["renderer_interpreter"], str)
        or snapshot["mujoco_support_site_packages"] != str(MUJOCO_SUPPORT_SITE_PACKAGES)
        or not isinstance(snapshot["mujoco_support_tree_identity_sha256"], str)
        or len(snapshot["mujoco_support_tree_identity_sha256"]) != 64
        or snapshot["renderer_interpreter_matches_runner"] is not True
        or snapshot["renderer_smoke_exit_code"] != 0
        or snapshot["authority_artifacts_materialized"] is not False
        or snapshot["attempt_marker_exists"] is not False
    ):
        raise ValueError("T20.44 runtime facts failed closed")
    dependencies = snapshot["dependencies"]
    if dependencies != EXPECTED_DEPENDENCIES:
        raise ValueError("T20.44 dependency versions drifted")
    output_state = snapshot["output_path_state"]
    expected_paths = {path.as_posix() for path in OUTPUT_PATHS}
    if set(output_state) != expected_paths or any(
        row != {"exists": False, "is_symlink": False} for row in output_state.values()
    ):
        raise ValueError("T20.44 output paths are not absent and unaliased")


def _authority_window(valid_from: str, valid_until: str) -> tuple[datetime, datetime]:
    start = _aware_time(valid_from, label="authority start")
    stop = _aware_time(valid_until, label="authority stop")
    seconds = (stop - start).total_seconds()
    if seconds <= 0 or seconds > MAXIMUM_AUTHORITY_SECONDS:
        raise ValueError("T20.44 authority window is invalid")
    return start, stop


def _aware_time(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"T20.44 {label} must be ISO text")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"T20.44 {label} must carry a UTC offset")
    return parsed


def _prospective_ref(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(_canonical_file_bytes(payload)).hexdigest(),
    }


def _canonical_file_bytes(payload: dict[str, Any]) -> bytes:
    import json

    return (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def _false_authority_fields() -> dict[str, bool]:
    return {field: False for field in FALSE_AUTHORITY_FIELDS}


def _prohibited_authority_grants() -> dict[str, bool]:
    return {
        "hardware_authorized": False,
        "camera_authorized": False,
        "serial_authorized": False,
        "physical_motion_authorized": False,
        "network_authorized": False,
        "external_compute_authorized": False,
        "brev_compute_authorized": False,
        "physical_transfer_authorized": False,
        "promotion_authorized": False,
        "r2_authorized": True,
        "t20_45_authorized": False,
    }


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("T20.44 expected a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("T20.44 expected a SHA-256 hex digest") from error
    return value


def _commit(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise ValueError("T20.44 expected a full Git commit")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("T20.44 expected a full Git commit") from error
    return value


def _finite(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.44 {label} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"T20.44 {label} must be finite and nonnegative")
    return number


__all__ = [
    "ACCEPTANCE_SCHEMA_VERSION",
    "SMOLVLA_SOURCE_PATHS",
    "ATTEMPT_PATH",
    "AUTHORITY_PATHS",
    "BATCH_SIZE",
    "BRANCH",
    "CHECKPOINT_ROOT",
    "CHECKPOINT_SCHEDULE",
    "CHUNK_SIZE",
    "DECISION_PATH",
    "EVALUATION_ACTION_STEPS",
    "FAILURE_PATH",
    "GATE_A_PATH",
    "MAXIMUM_OPTIMIZER_UPDATES",
    "MUJOCO_SUPPORT_SITE_PACKAGES",
    "OUTPUT_PATHS",
    "OWNER_GRANT_PATH",
    "PERMIT_PATH",
    "PRE_RUN_ACCEPTANCE_PATH",
    "REQUEST_PATH",
    "POLICY_SNAPSHOT_PATH",
    "VLM_SNAPSHOT_PATH",
    "POLICY_WEIGHTS_SHA256",
    "VLM_WEIGHTS_SHA256",
    "RENDERER_SMOKE_RECEIPT_PATH",
    "RENDERER_SMOKE_ROOT",
    "RENDERER_SMOKE_TRACE_PATH",
    "RENDERER_SMOKE_VIDEO_PATH",
    "RESULT_PATH",
    "RETENTION_PATH",
    "ROLLOUT_ROOT",
    "R0_DATASET_REPO_ID",
    "R0_DATASET_ROOT",
    "RUN_ROOT",
    "RUN_SUMMARY_PATH",
    "RUNTIME_PREFLIGHT_PATH",
    "SAMPLE_INDICES",
    "SCORECARD_PATH",
    "SPEC_PATH",
    "TRAINING_SEED",
    "VIDEO_ROOT",
    "build_attempt_marker",
    "build_central_authority",
    "build_gate_a",
    "build_owner_grant",
    "build_permit",
    "build_pre_run_acceptance",
    "build_runtime_preflight",
    "build_spec",
    "load_verified_sources",
    "verify_attempt_marker",
    "verify_gate_a",
    "verify_owner_grant",
    "verify_permit",
    "verify_pre_run_acceptance",
    "verify_runtime_preflight",
    "verify_spec",
]
