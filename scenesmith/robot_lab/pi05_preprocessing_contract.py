"""Offline source contract for future PI0.5 physical-observation preprocessing."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import struct

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.calibration_profile import verify_calibration_profile
from scenesmith.robot_lab.robotics_dependency_lock import (
    verify_robotics_dependency_lock,
)
from scenesmith.robot_lab.static_pose_bracket import (
    verify_static_pose_bracket_contract,
)


PI05_PREPROCESSING_SOURCE_CONTRACT_SCHEMA_VERSION = (
    "scenesmith.pi05_preprocessing_source_contract.v1"
)
CHECKPOINT_REPOSITORY_ID = "Cache-SCA/pi05_teleop_sort_block"
CHECKPOINT_REVISION = "84b551af1303e92d97d6752d43cc3c9f1a090778"
TOKENIZER_REPOSITORY_ID = "google/paligemma-3b-pt-224"
TOKENIZER_REVISION = "35e4f46485b4d07967e7e9935bc3786aad50687c"

_DEPENDENCY_LOCK_PATH = Path(
    "configurations/robot_lab/pi05_robotics_dependency_lock.json"
)
_LEROBOT_RUNTIME_PATH = Path("configurations/robot_lab/pi05_lerobot_runtime.json")
_CALIBRATION_PROFILE_PATH = Path(
    "configurations/robot_lab/pi05_calibration_profile.json"
)
_STATIC_POSE_CONTRACT_PATH = Path(
    "configurations/robot_lab/pi05_static_pose_bracket_contract.json"
)
_ACCEPTED_MANIFEST_PATH = Path(
    "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
_SOURCE_PATHS = [
    "external/lerobot/src/lerobot/policies/pi05/configuration_pi05.py",
    "external/lerobot/src/lerobot/policies/pi05/modeling_pi05.py",
    "external/lerobot/src/lerobot/policies/pi05/processor_pi05.py",
    "external/lerobot/src/lerobot/processor/relative_action_processor.py",
]
_CHECKPOINT_FILES = [
    "config.json",
    "policy_preprocessor.json",
    "policy_preprocessor_step_2_normalizer_processor.safetensors",
    "policy_postprocessor.json",
    "policy_postprocessor_step_0_unnormalizer_processor.safetensors",
]
_TOKENIZER_FILES = [
    "added_tokens.json",
    "config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
]
_JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]
_INPUT_FEATURES = {
    "observation.images.base_0_rgb": {"type": "VISUAL", "shape": [3, 224, 224]},
    "observation.images.left_wrist_0_rgb": {
        "type": "VISUAL",
        "shape": [3, 224, 224],
    },
    "observation.images.right_wrist_0_rgb": {
        "type": "VISUAL",
        "shape": [3, 224, 224],
    },
    "observation.state": {"type": "STATE", "shape": [32]},
}
_NORMALIZATION_MAPPING = {
    "ACTION": "MEAN_STD",
    "STATE": "MEAN_STD",
    "VISUAL": "IDENTITY",
}
_PREPROCESSOR_STEP_ORDER = [
    "rename_observations_processor",
    "to_batch_processor",
    "normalizer_processor",
    "pi05_prepare_state_tokenizer_processor_step",
    "tokenizer_processor",
    "device_processor",
]
_POSTPROCESSOR_STEP_ORDER = [
    "unnormalizer_processor",
    "device_processor",
]
_MISSING_INPUTS = [
    "accepted_live_session_review_decision",
    "reviewed_stable_camera_role_binding",
    "reviewed_task_prompt",
]
_AUTHORITY_NOT_GRANTED = [
    "accepted_live_policy_input",
    "policy_shadow_input_valid",
    "policy_shadow",
    "model_weight_load",
    "policy_inference",
    "physical_follower_command",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]
_DTYPE_SIZES = {
    "BOOL": 1,
    "U8": 1,
    "I8": 1,
    "I16": 2,
    "U16": 2,
    "F16": 2,
    "BF16": 2,
    "I32": 4,
    "U32": 4,
    "F32": 4,
    "I64": 8,
    "U64": 8,
    "F64": 8,
}
_MAX_NORMALIZER_FILE_BYTES = 1_000_000


def build_pi05_preprocessing_source_contract(
    *,
    repo_root: Path,
    hf_cache_root: Path,
    calibration_path: Path,
) -> dict[str, Any]:
    """Build the blocked fixture contract without loading a tokenizer or model."""

    root = Path(repo_root).resolve()
    cache = Path(hf_cache_root).resolve()
    dependency_path = root / _DEPENDENCY_LOCK_PATH
    runtime_path = root / _LEROBOT_RUNTIME_PATH
    calibration_profile_path = root / _CALIBRATION_PROFILE_PATH
    static_pose_path = root / _STATIC_POSE_CONTRACT_PATH
    accepted_manifest_path = root / _ACCEPTED_MANIFEST_PATH

    dependency_lock = load_strict_json(dependency_path)
    verify_robotics_dependency_lock(dependency_lock, repo_root=root)
    verify_signed_payload(dependency_lock, label="PI0.5 dependency lock")
    runtime = load_strict_json(runtime_path)
    calibration_profile = load_strict_json(calibration_profile_path)
    static_pose_contract = load_strict_json(static_pose_path)
    verify_calibration_profile(
        calibration_profile,
        calibration_path=calibration_path,
        manifest_path=accepted_manifest_path,
    )
    verify_static_pose_bracket_contract(
        static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=accepted_manifest_path,
    )

    source_evidence, stack = _verify_executable_sources(
        dependency_lock,
        repo_root=root,
    )
    runtime_summary = _verify_runtime_contract(runtime, stack=stack)
    coordinate_contract = _verify_coordinate_contract(
        calibration_profile,
        static_pose_contract=static_pose_contract,
        stack=stack,
    )

    checkpoint = _cached_snapshot_evidence(
        cache_root=cache,
        repository_id=CHECKPOINT_REPOSITORY_ID,
        revision=CHECKPOINT_REVISION,
        filenames=_CHECKPOINT_FILES,
    )
    checkpoint_files = {
        item["filename"]: item for item in checkpoint["files"]
    }
    checkpoint_root = _snapshot_root(
        cache,
        repository_id=CHECKPOINT_REPOSITORY_ID,
        revision=CHECKPOINT_REVISION,
    )
    checkpoint_config = _load_strict_json_file(checkpoint_root / "config.json")
    _verify_file_digest(
        checkpoint_root / "config.json",
        checkpoint_files["config.json"]["sha256"],
        label="PI0.5 checkpoint config",
    )
    checkpoint_summary = _verify_checkpoint_config(checkpoint_config)
    preprocessor = _load_strict_json_file(
        checkpoint_root / "policy_preprocessor.json"
    )
    postprocessor = _load_strict_json_file(
        checkpoint_root / "policy_postprocessor.json"
    )
    _verify_file_digest(
        checkpoint_root / "policy_preprocessor.json",
        checkpoint_files["policy_preprocessor.json"]["sha256"],
        label="PI0.5 checkpoint preprocessor",
    )
    _verify_file_digest(
        checkpoint_root / "policy_postprocessor.json",
        checkpoint_files["policy_postprocessor.json"]["sha256"],
        label="PI0.5 checkpoint postprocessor",
    )
    effective_preprocessor = _verify_preprocessor(preprocessor)
    _verify_postprocessor(postprocessor)
    stats = _verify_normalizer_state(
        checkpoint_root
        / "policy_preprocessor_step_2_normalizer_processor.safetensors",
        expected_sha256=checkpoint_files[
            "policy_preprocessor_step_2_normalizer_processor.safetensors"
        ]["sha256"],
    )
    post_stats = _verify_normalizer_state(
        checkpoint_root
        / "policy_postprocessor_step_0_unnormalizer_processor.safetensors",
        expected_sha256=checkpoint_files[
            "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
        ]["sha256"],
    )
    if stats != post_stats:
        raise ValueError("PI0.5 pre/postprocessor normalizer state drifted")
    if (
        checkpoint_files[
            "policy_preprocessor_step_2_normalizer_processor.safetensors"
        ]["sha256"]
        != checkpoint_files[
            "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
        ]["sha256"]
    ):
        raise ValueError("PI0.5 pre/postprocessor state file identity drifted")

    tokenizer = _cached_snapshot_evidence(
        cache_root=cache,
        repository_id=TOKENIZER_REPOSITORY_ID,
        revision=TOKENIZER_REVISION,
        filenames=_TOKENIZER_FILES,
    )
    tokenizer_root = _snapshot_root(
        cache,
        repository_id=TOKENIZER_REPOSITORY_ID,
        revision=TOKENIZER_REVISION,
    )
    tokenizer_config = _load_strict_json_file(
        tokenizer_root / "tokenizer_config.json"
    )
    tokenizer_files = {item["filename"]: item for item in tokenizer["files"]}
    _verify_file_digest(
        tokenizer_root / "tokenizer_config.json",
        tokenizer_files["tokenizer_config.json"]["sha256"],
        label="PI0.5 tokenizer config",
    )
    tokenizer_summary = _verify_tokenizer_config(tokenizer_config)

    payload = {
        "schema_version": PI05_PREPROCESSING_SOURCE_CONTRACT_SCHEMA_VERSION,
        "contract_name": "pi05_physical_observation_preprocessing_sources",
        "qualification_scope": "fixture_pi05_preprocessing_source_contract",
        "evidence_mode": "deterministic_fixture_blocked_missing_inputs",
        "status": "blocked_missing_inputs",
        "dependency_lock": {
            **_tracked_artifact_evidence(
                dependency_path,
                repo_root=root,
                payload=dependency_lock,
            ),
            "stack_identity_sha256": stack["identity_sha256"],
            "source_files": source_evidence,
        },
        "runtime_contract": {
            **_tracked_file_evidence(runtime_path, repo_root=root),
            **runtime_summary,
        },
        "calibration_profile": _tracked_artifact_evidence(
            calibration_profile_path,
            repo_root=root,
            payload=calibration_profile,
        ),
        "static_pose_contract": _tracked_artifact_evidence(
            static_pose_path,
            repo_root=root,
            payload=static_pose_contract,
        ),
        "checkpoint_processor_snapshot": {
            **checkpoint,
            "checkpoint_config": checkpoint_summary,
            "normalizer_state": stats,
            "model_weights_read": False,
        },
        "tokenizer_snapshot": {
            **tokenizer,
            "tokenizer_config": tokenizer_summary,
            "tokenizer_instantiated": False,
            "network_accessed": False,
        },
        "effective_preprocessor": effective_preprocessor,
        "coordinate_contract": coordinate_contract,
        "camera_contract": {
            "checkpoint_source_keys": [
                "observation.images.top",
                "observation.images.wrist",
            ],
            "renamed_model_keys": [
                "observation.images.base_0_rgb",
                "observation.images.left_wrist_0_rgb",
            ],
            "model_optional_missing_key": (
                "observation.images.right_wrist_0_rgb"
            ),
            "missing_key_behavior": "zero_image_with_false_mask_in_pinned_model_source",
            "stable_camera_identity_sha256": [
                camera["stable_camera_identity_sha256"]
                for camera in static_pose_contract["cameras"]
            ],
            "stable_camera_role_binding": None,
            "role_binding_reviewed": False,
        },
        "observation_acceptance_contract": {
            "required_review_manifest_schema": (
                "scenesmith.static_pose_live_session_review_manifest.v1"
            ),
            "required_review_manifest_status": (
                "candidate_observed_pending_review"
            ),
            "required_separate_acceptance_decision": True,
            "accepted_live_review_artifact_present": False,
            "accepted_live_review_decision_present": False,
            "accepted_live_review_manifest_identity_sha256": None,
            "acceptance_decision_identity_sha256": None,
        },
        "task_contract": {
            "task_key": "task",
            "prompt_template": "Task: {cleaned_task}, State: {discretized_state};\nAction: ",
            "tokenizer_max_length": 200,
            "reviewed_task_prompt": None,
            "task_prompt_reviewed": False,
        },
        "missing_inputs": list(_MISSING_INPUTS),
        "production_preprocessing_allowed": False,
        "policy_input_built": False,
        "tokenizer_instantiated": False,
        "processor_instantiated": False,
        "model_instantiated": False,
        "model_weights_read": False,
        "preprocessing_run": False,
        "policy_shadow_run": False,
        "policy_inference_run": False,
        "mujoco_replay_run": False,
        "network_accessed": False,
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "local_capabilities": [
            "pi05_policy_input_preprocessing_source_contract_conformant"
        ],
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "motion_authority_granted": False,
        "training_authority_granted": False,
    }
    return sign_payload(payload)


def verify_pi05_preprocessing_source_contract(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    hf_cache_root: Path,
    calibration_path: Path,
) -> None:
    """Rebuild all source evidence and reject any re-signed semantic drift."""

    if not isinstance(payload, dict):
        raise ValueError("PI0.5 preprocessing source contract must be an object")
    if (
        payload.get("schema_version")
        != PI05_PREPROCESSING_SOURCE_CONTRACT_SCHEMA_VERSION
    ):
        raise ValueError("PI0.5 preprocessing source contract schema is unsupported")
    verify_signed_payload(payload, label="PI0.5 preprocessing source contract")
    expected = build_pi05_preprocessing_source_contract(
        repo_root=repo_root,
        hf_cache_root=hf_cache_root,
        calibration_path=calibration_path,
    )
    if payload != expected:
        raise ValueError("PI0.5 preprocessing source contract drifted from sources")


def _verify_executable_sources(
    dependency_lock: dict[str, Any],
    *,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if dependency_lock.get("schema_version") != "scenesmith.robotics_dependency_lock.v2":
        raise ValueError("PI0.5 dependency lock schema drifted")
    local = dependency_lock.get("dependencies", {}).get("local_lerobot_checkout")
    if not isinstance(local, dict):
        raise ValueError("PI0.5 local LeRobot dependency is missing")
    stack = local.get("executable_stack")
    relevant = local.get("relevant_sources")
    if not isinstance(stack, dict) or not isinstance(relevant, dict):
        raise ValueError("PI0.5 executable stack evidence is missing")
    _require_sha256(stack.get("identity_sha256"), label="PI0.5 stack identity")
    if (
        stack.get("schema_version") != "scenesmith.lerobot_stack_identity.v1"
        or stack.get("source_root") != "external/lerobot/src"
    ):
        raise ValueError("PI0.5 executable stack classification drifted")
    files = relevant.get("files")
    if not isinstance(files, list):
        raise ValueError("PI0.5 relevant source evidence is missing")
    by_path = {
        item.get("path"): item
        for item in files
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    output = []
    for relative in _SOURCE_PATHS:
        reference = by_path.get(relative)
        if not isinstance(reference, dict):
            raise ValueError(f"PI0.5 pinned source is missing: {relative}")
        observed = _tracked_file_evidence(repo_root / relative, repo_root=repo_root)
        if observed != reference:
            raise ValueError(f"PI0.5 pinned source drifted: {relative}")
        output.append(observed)
    return output, stack


def _verify_runtime_contract(
    runtime: dict[str, Any],
    *,
    stack: dict[str, Any],
) -> dict[str, Any]:
    processor = runtime.get("processor_contract")
    stack_processor = stack.get("processor_contract")
    if (
        runtime.get("schema_version") != "scenesmith.lerobot_runtime.v1"
        or runtime.get("base_revision") != stack.get("base_revision")
        or runtime.get("source_root") != "external/lerobot/src"
        or processor != stack_processor
        or not isinstance(processor, dict)
    ):
        raise ValueError("PI0.5 tracked runtime/stack contract drifted")
    expected = {
        "joint_names": _JOINT_NAMES,
        "input_units": "radians",
        "lerobot_units": "degrees",
        "tensor_width": 32,
        "padding_value": 0.0,
    }
    if processor != expected:
        raise ValueError("PI0.5 tracked processor contract semantics drifted")
    return {
        "stack_identity_sha256": stack["identity_sha256"],
        "processor_contract": copy.deepcopy(processor),
    }


def _verify_coordinate_contract(
    calibration_profile: dict[str, Any],
    *,
    static_pose_contract: dict[str, Any],
    stack: dict[str, Any],
) -> dict[str, Any]:
    calibration_joints = calibration_profile.get("joints")
    static_joints = static_pose_contract.get("joints")
    if (
        calibration_profile.get("schema_version")
        != "scenesmith.calibration_profile.v1"
        or static_pose_contract.get("schema_version")
        != "scenesmith.static_pose_bracket_contract.v2"
        or not isinstance(calibration_joints, list)
        or not isinstance(static_joints, list)
        or len(calibration_joints) != 6
        or len(static_joints) != 6
    ):
        raise ValueError("PI0.5 coordinate source artifacts are malformed")
    joint_contract = []
    for index, (calibration, static, name) in enumerate(
        zip(calibration_joints, static_joints, _JOINT_NAMES, strict=True),
        start=1,
    ):
        if not isinstance(calibration, dict) or not isinstance(static, dict):
            raise ValueError("PI0.5 coordinate joint evidence is malformed")
        mode = "range_0_100" if name == "gripper" else "degrees"
        calibration_units = (
            "normalized_percent" if name == "gripper" else "degrees"
        )
        static_units = "percent" if name == "gripper" else "degrees"
        normalization = calibration.get("normalization")
        if (
            calibration.get("joint_name") != name
            or calibration.get("servo_id") != index
            or not isinstance(normalization, dict)
            or normalization.get("mode") != mode
            or normalization.get("output_units") != calibration_units
            or static.get("joint_name") != name
            or static.get("servo_id") != index
            or static.get("normalization_mode") != mode
            or static.get("coordinate_units") != static_units
        ):
            raise ValueError(f"PI0.5 coordinate semantics drifted for {name}")
        joint_contract.append(
            {
                "joint_name": name,
                "servo_id": index,
                "source_units": calibration_units,
                "policy_units": static_units,
            }
        )
    if stack.get("processor_contract", {}).get("joint_names") != _JOINT_NAMES:
        raise ValueError("PI0.5 stack joint order drifted")
    return {
        "joint_order": list(_JOINT_NAMES),
        "joints": joint_contract,
        "raw_state_width": 6,
        "normalizer_state_width": 6,
        "declared_state_feature_width": 32,
        "tokenized_state_width": 6,
        "padding_applied_before_tokenization": False,
        "radians_to_degrees_conversion_applied": False,
        "conversion_disposition": (
            "physical_calibration_profile_already_emits_policy_coordinates"
        ),
    }


def _verify_checkpoint_config(value: dict[str, Any]) -> dict[str, Any]:
    if (
        value.get("type") != "pi05"
        or value.get("input_features") != _INPUT_FEATURES
        or value.get("output_features")
        != {"action": {"type": "ACTION", "shape": [6]}}
        or value.get("device") != "cuda"
        or value.get("dtype") != "bfloat16"
        or value.get("chunk_size") != 50
        or value.get("n_action_steps") != 50
        or value.get("max_state_dim") != 32
        or value.get("max_action_dim") != 32
        or value.get("use_relative_actions") is not False
        or value.get("relative_exclude_joints") != ["gripper"]
        or value.get("action_feature_names")
        != [f"{name}.pos" for name in _JOINT_NAMES]
        or value.get("image_resolution") != [224, 224]
        or value.get("tokenizer_max_length") != 200
        or value.get("normalization_mapping") != _NORMALIZATION_MAPPING
    ):
        raise ValueError("PI0.5 checkpoint configuration semantics drifted")
    return {
        "policy_type": "pi05",
        "source_device": "cuda",
        "source_dtype": "bfloat16",
        "input_features": copy.deepcopy(_INPUT_FEATURES),
        "output_action_width": 6,
        "max_state_dim": 32,
        "max_action_dim": 32,
        "chunk_size": 50,
        "n_action_steps": 50,
        "relative_actions": False,
        "normalization_mapping": copy.deepcopy(_NORMALIZATION_MAPPING),
    }


def _verify_preprocessor(value: dict[str, Any]) -> dict[str, Any]:
    steps = value.get("steps")
    if value.get("name") != "policy_preprocessor" or not isinstance(steps, list):
        raise ValueError("PI0.5 checkpoint preprocessor is malformed")
    if [step.get("registry_name") for step in steps if isinstance(step, dict)] != (
        _PREPROCESSOR_STEP_ORDER
    ):
        raise ValueError("PI0.5 checkpoint preprocessor order drifted")
    if len(steps) != len(_PREPROCESSOR_STEP_ORDER):
        raise ValueError("PI0.5 checkpoint preprocessor step count drifted")
    expected_rename = {
        "observation.images.top": "observation.images.base_0_rgb",
        "observation.images.wrist": "observation.images.left_wrist_0_rgb",
    }
    if steps[0].get("config") != {"rename_map": expected_rename}:
        raise ValueError("PI0.5 checkpoint camera rename map drifted")
    if steps[1].get("config") != {}:
        raise ValueError("PI0.5 checkpoint batch step drifted")
    normalizer = steps[2]
    normalizer_config = normalizer.get("config")
    if (
        not isinstance(normalizer_config, dict)
        or normalizer.get("state_file")
        != "policy_preprocessor_step_2_normalizer_processor.safetensors"
        or normalizer_config.get("features")
        != {**_INPUT_FEATURES, "action": {"type": "ACTION", "shape": [6]}}
        or normalizer_config.get("norm_map") != _NORMALIZATION_MAPPING
        or normalizer_config.get("eps") != 1e-8
    ):
        raise ValueError("PI0.5 checkpoint normalizer semantics drifted")
    if steps[3].get("config") != {}:
        raise ValueError("PI0.5 checkpoint state/tokenizer preparation drifted")
    tokenizer = steps[4].get("config")
    if tokenizer != {
        "max_length": 200,
        "task_key": "task",
        "padding_side": "right",
        "padding": "max_length",
        "truncation": True,
        "tokenizer_name": TOKENIZER_REPOSITORY_ID,
    }:
        raise ValueError("PI0.5 checkpoint tokenizer step drifted")
    if steps[5].get("config") != {"device": "cuda", "float_dtype": None}:
        raise ValueError("PI0.5 checkpoint preprocessing device drifted")
    effective = copy.deepcopy(value)
    effective["steps"][5]["config"]["device"] = "cpu"
    source_sha256 = _sha256_payload(value)
    effective_sha256 = _sha256_payload(effective)
    if source_sha256 == effective_sha256:
        raise ValueError("PI0.5 effective preprocessing override had no effect")
    return {
        "source_preprocessor_identity_sha256": source_sha256,
        "effective_preprocessor_identity_sha256": effective_sha256,
        "step_order": list(_PREPROCESSOR_STEP_ORDER),
        "device_override": {
            "source": "cuda",
            "effective": "cpu",
            "only_mutation": True,
        },
        "processor_instantiated": False,
    }


def _verify_postprocessor(value: dict[str, Any]) -> None:
    steps = value.get("steps")
    if (
        value.get("name") != "policy_postprocessor"
        or not isinstance(steps, list)
        or len(steps) != 2
        or [step.get("registry_name") for step in steps if isinstance(step, dict)]
        != _POSTPROCESSOR_STEP_ORDER
    ):
        raise ValueError("PI0.5 checkpoint postprocessor order drifted")
    unnormalizer = steps[0]
    config = unnormalizer.get("config")
    if (
        unnormalizer.get("state_file")
        != "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
        or not isinstance(config, dict)
        or config.get("features")
        != {"action": {"type": "ACTION", "shape": [6]}}
        or config.get("norm_map") != _NORMALIZATION_MAPPING
        or config.get("eps") != 1e-8
        or steps[1].get("config") != {"device": "cpu", "float_dtype": None}
    ):
        raise ValueError("PI0.5 checkpoint postprocessor semantics drifted")


def _verify_normalizer_state(
    path: Path,
    *,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    before = path.stat()
    size_bytes = before.st_size
    if size_bytes <= 0 or size_bytes > _MAX_NORMALIZER_FILE_BYTES:
        raise ValueError("PI0.5 normalizer safetensors file size is unbounded")
    encoded = path.read_bytes()
    after = path.stat()
    if len(encoded) != size_bytes or _stat_identity(before) != _stat_identity(after):
        raise ValueError("PI0.5 normalizer safetensors changed while reading")
    if expected_sha256 is not None and hashlib.sha256(encoded).hexdigest() != expected_sha256:
        raise ValueError("PI0.5 normalizer safetensors hash drifted while parsing")
    if len(encoded) < 10:
        raise ValueError("PI0.5 normalizer safetensors file is truncated")
    header_length = struct.unpack("<Q", encoded[:8])[0]
    if header_length <= 1 or header_length > 1_000_000 or 8 + header_length > len(encoded):
        raise ValueError("PI0.5 normalizer safetensors header length is invalid")
    try:
        header = json.loads(
            encoded[8 : 8 + header_length].decode("utf-8").strip(),
            object_pairs_hook=_reject_duplicate_json_pairs,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("PI0.5 normalizer safetensors header is malformed") from exc
    if not isinstance(header, dict):
        raise ValueError("PI0.5 normalizer safetensors header must be an object")
    data = encoded[8 + header_length :]
    intervals = []
    for name, entry in header.items():
        if name == "__metadata__":
            if not isinstance(entry, dict):
                raise ValueError("PI0.5 normalizer metadata must be an object")
            continue
        if not isinstance(entry, dict) or set(entry) != {
            "dtype",
            "shape",
            "data_offsets",
        }:
            raise ValueError("PI0.5 normalizer tensor header fields drifted")
        dtype = entry.get("dtype")
        shape = entry.get("shape")
        offsets = entry.get("data_offsets")
        if dtype not in _DTYPE_SIZES:
            raise ValueError("PI0.5 normalizer tensor dtype is unsupported")
        if (
            not isinstance(shape, list)
            or any(type(item) is not int or item < 0 for item in shape)
            or not isinstance(offsets, list)
            or len(offsets) != 2
            or any(type(item) is not int for item in offsets)
        ):
            raise ValueError("PI0.5 normalizer tensor shape or offsets are malformed")
        start, finish = offsets
        element_count = math.prod(shape)
        if (
            element_count <= 0
            or not name
            or start < 0
            or finish < start
            or finish > len(data)
            or finish - start != element_count * _DTYPE_SIZES[dtype]
        ):
            raise ValueError("PI0.5 normalizer tensor byte range is invalid")
        intervals.append((start, finish, name))
    ordered = sorted(intervals)
    if not ordered:
        raise ValueError("PI0.5 normalizer safetensors has no tensors")
    if any(current[0] < previous[1] for previous, current in zip(ordered, ordered[1:])):
        raise ValueError("PI0.5 normalizer tensor byte ranges overlap")
    if (
        ordered[0][0] != 0
        or ordered[-1][1] != len(data)
        or any(
            current[0] != previous[1]
            for previous, current in zip(ordered, ordered[1:])
        )
    ):
        raise ValueError("PI0.5 normalizer tensor ranges do not cover the file")

    required = {
        "observation.state.count": 1,
        "observation.state.mean": 6,
        "observation.state.std": 6,
        "action.count": 1,
        "action.mean": 6,
        "action.std": 6,
    }
    values = {}
    for name, width in required.items():
        entry = header.get(name)
        if (
            not isinstance(entry, dict)
            or entry.get("dtype") != "F32"
            or entry.get("shape") != [width]
        ):
            raise ValueError(f"PI0.5 normalizer tensor shape drifted: {name}")
        start, finish = entry["data_offsets"]
        unpacked = list(struct.unpack(f"<{width}f", data[start:finish]))
        if any(not math.isfinite(item) for item in unpacked):
            raise ValueError(f"PI0.5 normalizer tensor is non-finite: {name}")
        values[name] = unpacked
    state_count = values["observation.state.count"][0]
    action_count = values["action.count"][0]
    if (
        state_count <= 0
        or action_count <= 0
        or state_count != action_count
        or not state_count.is_integer()
        or not action_count.is_integer()
    ):
        raise ValueError("PI0.5 normalizer counts are invalid or contradictory")
    if any(item <= 0 for item in values["observation.state.std"]):
        raise ValueError("PI0.5 observation state standard deviation is nonpositive")
    if any(item <= 0 for item in values["action.std"]):
        raise ValueError("PI0.5 action standard deviation is nonpositive")
    return {
        "state_width": 6,
        "action_width": 6,
        "sample_count": int(state_count),
        "tensor_count": len(ordered),
        "complete_file_coverage_verified": True,
        "state_mean_sha256": _sha256_payload(values["observation.state.mean"]),
        "state_std_sha256": _sha256_payload(values["observation.state.std"]),
        "action_mean_sha256": _sha256_payload(values["action.mean"]),
        "action_std_sha256": _sha256_payload(values["action.std"]),
        "values_embedded": False,
    }


def _reject_duplicate_json_pairs(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate PI0.5 normalizer header key: {key}")
        value[key] = item
    return value


def _verify_tokenizer_config(value: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "tokenizer_class": "GemmaTokenizer",
        "bos_token": "<bos>",
        "eos_token": "<eos>",
        "pad_token": "<pad>",
        "unk_token": "<unk>",
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise ValueError("PI0.5 tokenizer configuration semantics drifted")
    return {
        **expected,
        "pipeline_max_length": 200,
        "padding_side": "right",
        "padding": "max_length",
        "truncation": True,
    }


def _cached_snapshot_evidence(
    *,
    cache_root: Path,
    repository_id: str,
    revision: str,
    filenames: list[str],
) -> dict[str, Any]:
    cache_root = Path(cache_root).resolve()
    if not cache_root.is_dir():
        raise ValueError("Hugging Face cache root is missing")
    model_root = _model_cache_root(cache_root, repository_id=repository_id)
    _require_nonaliased_directory(
        model_root,
        root=cache_root,
        label=f"Hugging Face model cache {repository_id}",
    )
    for directory_name in ("refs", "snapshots", "blobs"):
        _require_nonaliased_directory(
            model_root / directory_name,
            root=cache_root,
            label=f"Hugging Face {directory_name} directory {repository_id}",
        )
    ref = model_root / "refs" / "main"
    if ref.is_symlink() or not ref.is_file():
        raise ValueError(f"Hugging Face cache ref is missing or aliased: {repository_id}")
    observed_revision = ref.read_text(encoding="utf-8").strip()
    if observed_revision != revision:
        raise ValueError(f"Hugging Face cache revision drifted: {repository_id}")
    snapshot = _snapshot_root(
        cache_root,
        repository_id=repository_id,
        revision=revision,
    )
    _require_nonaliased_directory(
        snapshot,
        root=cache_root,
        label=f"Hugging Face snapshot {repository_id}",
    )
    files = [
        _cache_file_evidence(
            snapshot / filename,
            model_root=model_root,
            filename=filename,
        )
        for filename in filenames
    ]
    return {
        "repository_id": repository_id,
        "revision": revision,
        "files": files,
        "snapshot_identity_sha256": _sha256_payload(files),
        "absolute_cache_path_included": False,
        "network_accessed": False,
    }


def _cache_file_evidence(
    path: Path,
    *,
    model_root: Path,
    filename: str,
) -> dict[str, Any]:
    if not filename or Path(filename).name != filename:
        raise ValueError("Hugging Face cached filename is invalid")
    if not path.is_file():
        raise ValueError(f"Hugging Face cached file is missing: {filename}")
    resolved = path.resolve()
    if path.is_symlink():
        blobs = (model_root / "blobs").resolve()
        try:
            resolved.relative_to(blobs)
        except ValueError as exc:
            raise ValueError(f"Hugging Face cache symlink escaped blobs: {filename}") from exc
        storage = "cache_blob_symlink"
    else:
        if resolved != path.absolute():
            raise ValueError(f"Hugging Face snapshot file escaped: {filename}")
        storage = "snapshot_regular_file"
    size = resolved.stat().st_size
    if size <= 0:
        raise ValueError(f"Hugging Face cached file is empty: {filename}")
    return {
        "filename": filename,
        "sha256": _hash_file(resolved),
        "size_bytes": size,
        "storage": storage,
    }


def _model_cache_root(cache_root: Path, *, repository_id: str) -> Path:
    owner, name = repository_id.split("/", 1)
    return Path(cache_root) / f"models--{owner}--{name}"


def _snapshot_root(
    cache_root: Path,
    *,
    repository_id: str,
    revision: str,
) -> Path:
    return _model_cache_root(cache_root, repository_id=repository_id) / "snapshots" / revision


def _tracked_artifact_evidence(
    path: Path,
    *,
    repo_root: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    evidence = _tracked_file_evidence(path, repo_root=repo_root)
    evidence.update(
        {
            "schema_version": require_nonblank(
                payload.get("schema_version"),
                label="tracked artifact schema",
            ),
            "identity_sha256": _require_sha256(
                payload.get("identity_sha256"),
                label="tracked artifact identity",
            ),
        }
    )
    return evidence


def _tracked_file_evidence(path: Path, *, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    unresolved = Path(path)
    candidate = unresolved if unresolved.is_absolute() else root / unresolved
    relative = _require_nonaliased_file(
        candidate,
        root=root,
        label="Tracked PI0.5 source",
    )
    resolved = candidate.resolve()
    return {
        "path": relative.as_posix(),
        "sha256": _hash_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def _require_nonaliased_directory(
    path: Path,
    *,
    root: Path,
    label: str,
) -> None:
    relative = _require_lexical_containment(path, root=root, label=label)
    current = Path(root).resolve()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} is aliased")
    if not current.is_dir():
        raise ValueError(f"{label} is missing")


def _require_nonaliased_file(
    path: Path,
    *,
    root: Path,
    label: str,
) -> Path:
    relative = _require_lexical_containment(path, root=root, label=label)
    current = Path(root).resolve()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} is aliased")
    if not current.is_file():
        raise ValueError(f"{label} is missing")
    if current.resolve() != current:
        raise ValueError(f"{label} escaped its root")
    return relative


def _require_lexical_containment(
    path: Path,
    *,
    root: Path,
    label: str,
) -> Path:
    canonical_root = Path(root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = canonical_root / candidate
    try:
        relative = candidate.relative_to(canonical_root)
    except ValueError as exc:
        raise ValueError(f"{label} escaped its root") from exc
    if not relative.parts or any(part in {".", ".."} for part in relative.parts):
        raise ValueError(f"{label} has an invalid relative path")
    return relative


def _load_strict_json_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"PI0.5 JSON source is missing: {path.name}")
    return load_strict_json(path)


def _hash_file(path: Path) -> str:
    before = Path(path).stat()
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = Path(path).stat()
    if _stat_identity(before) != _stat_identity(after):
        raise ValueError("PI0.5 source changed while hashing")
    return digest.hexdigest()


def _verify_file_digest(path: Path, expected_sha256: str, *, label: str) -> None:
    if _hash_file(path.resolve()) != _require_sha256(
        expected_sha256,
        label=f"{label} expected digest",
    ):
        raise ValueError(f"{label} changed while parsing")


def _stat_identity(value: Any) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _sha256_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest
