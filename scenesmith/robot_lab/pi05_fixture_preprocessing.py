"""Deterministic fixture parity for the pinned PI0.5 model-input boundary."""

from __future__ import annotations

import binascii
import copy
import hashlib
import io
import os
import platform
import re
import shutil
import socket
import struct
import tempfile

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.pi05_preprocessing_contract import (
    CHECKPOINT_REPOSITORY_ID,
    CHECKPOINT_REVISION,
    TOKENIZER_REPOSITORY_ID,
    TOKENIZER_REVISION,
    verify_pi05_preprocessing_source_contract,
)
from scenesmith.robot_lab.pi05_reviewed_input_gate import (
    verify_pi05_reviewed_input_gate,
)
from scenesmith.robot_lab.pi05_training_support import (
    build_state_support_audit,
    verify_state_support_audit,
)
from scenesmith.robot_lab.static_pose_bracket import (
    build_fixture_static_pose_observation,
    evaluate_static_pose_bracket,
    verify_static_pose_bracket_result,
)


PI05_FIXTURE_MODEL_READY_PARITY_SCHEMA_VERSION = (
    "scenesmith.pi05_fixture_model_ready_tensor_parity.v2"
)
PI05_FIXTURE_PREPROCESSING_RUNTIME_SCHEMA_VERSION = (
    "scenesmith.pi05_fixture_preprocessing_runtime.v2"
)
PI05_FIXTURE_INPUT_SPEC_SCHEMA_VERSION = "scenesmith.pi05_fixture_input_spec.v1"

# Filled only after a real strict-offline LeLab execution of this exact source.
# The pure-Python verifier uses the golden identity to reject a re-signed opaque
# tokenizer or Torch tensor substitution in runtimes that intentionally lack Torch.
EXPECTED_RUNTIME_RESULT_IDENTITY = (
    "1642f75c3801df58a7978b3e1d6c0a255641388b11a338f3bc2987fdb584f21a"
)

_SOURCE_CONTRACT_PATH = Path(
    "configurations/robot_lab/"
    "pi05_policy_input_preprocessing.blocked_missing_inputs.json"
)
_REVIEWED_INPUT_GATE_PATH = Path(
    "configurations/robot_lab/"
    "pi05_reviewed_inputs.blocked_missing_reviewed_inputs.json"
)
_STATIC_POSE_CONTRACT_PATH = Path(
    "configurations/robot_lab/pi05_static_pose_bracket_contract.json"
)
_CHECKPOINT_PREPROCESSOR_FILES = (
    "policy_preprocessor.json",
    "policy_preprocessor_step_2_normalizer_processor.safetensors",
)
_JOINT_ORDER = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]
_CAMERA_ROLES = (
    (
        "top",
        "observation.images.top",
        "observation.images.base_0_rgb",
    ),
    (
        "wrist",
        "observation.images.wrist",
        "observation.images.left_wrist_0_rgb",
    ),
)
_MODEL_IMAGE_ORDER = [
    "observation.images.base_0_rgb",
    "observation.images.left_wrist_0_rgb",
    "observation.images.right_wrist_0_rgb",
]
_TASK_TEXT = (
    "Sort each cube into the same-colored tray: red cubes into the red tray "
    "and blue cubes into the blue tray."
)
_WIDTH = 640
_HEIGHT = 480
_CHANNELS = 3
_FRAME_COUNT_PER_CAMERA = 2
_SELECTED_FRAME_INDEX = 1
_LOCAL_CAPABILITIES = [
    "fixture_pi05_model_ready_tensor_parity_conformant",
    "fixture_pi05_training_support_audit_conformant",
]
_AUTHORITY_NOT_GRANTED = [
    "accepted_live_session_review_decision",
    "pi05_reviewed_input_bundle_valid",
    "accepted_live_policy_input",
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "model_weight_load",
    "policy_inference",
    "mujoco_replay",
    "physical_follower_command",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]
_FALSE_RUNTIME_FACTS = {
    "model_instantiated": False,
    "model_weights_named": False,
    "model_weights_read": False,
    "policy_inference_run": False,
    "policy_shadow_run": False,
    "mujoco_replay_run": False,
    "network_accessed": False,
    "hardware_accessed": False,
    "physical_follower_commanded": False,
    "motion_authority_granted": False,
    "training_authority_granted": False,
}
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def canonical_fixture_frame(*, role: str, frame_index: int) -> dict[str, Any]:
    """Return exact deterministic PNG and decoded RGB bytes for one fixture frame."""

    if role not in {item[0] for item in _CAMERA_ROLES}:
        raise ValueError("Fixture camera role is unsupported")
    if type(frame_index) is not int or frame_index not in range(_FRAME_COUNT_PER_CAMERA):
        raise ValueError("Fixture frame index is unsupported")
    png_bytes, rgb_bytes = _canonical_fixture_frame_bytes(role, frame_index)
    return {
        "role": role,
        "frame_index": frame_index,
        "width": _WIDTH,
        "height": _HEIGHT,
        "channels": _CHANNELS,
        "encoding": "png",
        "pattern_version": "scenesmith_rgb_fixture_v1",
        "png_bytes": png_bytes,
        "png_sha256": hashlib.sha256(png_bytes).hexdigest(),
        "png_size_bytes": len(png_bytes),
        "decoded_rgb_bytes": rgb_bytes,
        "decoded_rgb_sha256": hashlib.sha256(rgb_bytes).hexdigest(),
        "decoded_rgb_size_bytes": len(rgb_bytes),
    }


def build_fixture_input_spec(*, repo_root: Path) -> dict[str, Any]:
    """Rebuild the complete deterministic review-shaped static fixture."""

    root = Path(repo_root).resolve()
    static_contract = load_strict_json(root / _STATIC_POSE_CONTRACT_PATH)
    verify_signed_payload(static_contract, label="PI0.5 fixture static contract")
    cameras = static_contract.get("cameras")
    if not isinstance(cameras, list) or len(cameras) != 2:
        raise ValueError("PI0.5 fixture requires exactly two signed cameras")

    assignments = []
    frames = []
    for camera_index, (role, source_key, model_key) in enumerate(_CAMERA_ROLES):
        stable_identity = _require_sha256(
            cameras[camera_index].get("stable_camera_identity_sha256"),
            label=f"PI0.5 fixture {role} camera identity",
        )
        assignment = {
            "role": role,
            "stable_camera_identity_sha256": stable_identity,
            "source_key": source_key,
            "model_key": model_key,
        }
        assignments.append(assignment)
        for frame_index in range(_FRAME_COUNT_PER_CAMERA):
            frame = canonical_fixture_frame(role=role, frame_index=frame_index)
            frames.append(
                {
                    **assignment,
                    **{
                        key: value
                        for key, value in frame.items()
                        if key not in {"png_bytes", "decoded_rgb_bytes", "role"}
                    },
                }
            )

    observation = copy.deepcopy(build_fixture_static_pose_observation(static_contract))
    for camera_index, camera in enumerate(observation["cameras"]):
        role = _CAMERA_ROLES[camera_index][0]
        for frame in camera["frames"]:
            canonical = canonical_fixture_frame(
                role=role,
                frame_index=frame["frame_index"],
            )
            frame["frame_sha256"] = canonical["png_sha256"]
    observation = sign_payload(observation)
    result = evaluate_static_pose_bracket(
        contract=static_contract,
        observation=observation,
    )
    verify_static_pose_bracket_result(
        result,
        contract=static_contract,
        observation=observation,
    )
    if result.get("static_pose_within_tolerance") is not True:
        raise ValueError("PI0.5 fixture static pose is not within tolerance")

    joint_drift = result.get("joint_drift")
    if not isinstance(joint_drift, list) or [
        item.get("joint_name") for item in joint_drift
    ] != _JOINT_ORDER:
        raise ValueError("PI0.5 fixture joint order drifted")
    state_values = [item["coordinate_after"] for item in joint_drift]
    state_units = {
        item["joint_name"]: item["coordinate_units"] for item in joint_drift
    }
    selected_frames = [
        item for item in frames if item["frame_index"] == _SELECTED_FRAME_INDEX
    ]
    if len(selected_frames) != 2:
        raise ValueError("PI0.5 fixture selected-frame cardinality drifted")

    return sign_payload(
        {
            "schema_version": PI05_FIXTURE_INPUT_SPEC_SCHEMA_VERSION,
            "evidence_class": "deterministic_fixture",
            "review_shape": "accepted_review_shaped_fixture_not_live_acceptance",
            "production_eligible": False,
            "static_pose_contract_identity_sha256": static_contract["identity_sha256"],
            "static_pose_observation_identity_sha256": observation["identity_sha256"],
            "static_pose_result_identity_sha256": result["identity_sha256"],
            "static_pose_within_tolerance": True,
            "state_selection": "q_after",
            "joint_order": list(_JOINT_ORDER),
            "state_units": state_units,
            "state_values": state_values,
            "task_text": _TASK_TEXT,
            "task_text_sha256": hashlib.sha256(_TASK_TEXT.encode("utf-8")).hexdigest(),
            "camera_role_assignments": assignments,
            "frame_count_per_camera": _FRAME_COUNT_PER_CAMERA,
            "selected_frame_rule": "highest_complete_frame_index",
            "frames": frames,
            "selected_frames": selected_frames,
        }
    )


def execute_pi05_fixture_preprocessing(
    *,
    repo_root: Path,
    hf_cache_root: Path,
    calibration_path: Path,
) -> dict[str, Any]:
    """Run the exact cached processor and model image method without a model."""

    root = Path(repo_root).resolve()
    cache = Path(hf_cache_root).resolve()
    source_contract, reviewed_gate = _load_and_verify_sources(
        repo_root=root,
        hf_cache_root=cache,
        calibration_path=Path(calibration_path).resolve(),
    )
    fixture = build_fixture_input_spec(repo_root=root)

    # Heavy runtime dependencies stay local so the independent artifact verifier
    # remains importable in the intentionally Torch-free MuJoCo environment. The
    # offline flags must exist before Hugging Face modules cache their settings.
    network_attempts: list[str] = []
    with _strict_offline_runtime(network_attempts):
        import numpy as np
        import torch
        import transformers
        from PIL import Image

        import lerobot
        import lerobot.policies.pi05.processor_pi05  # registers the PI0.5 step
        from lerobot.policies.pi05.modeling_pi05 import PI05Policy
        from lerobot.processor.pipeline import DataProcessorPipeline
    if network_attempts:
        raise ValueError("PI0.5 fixture dependency import attempted network access")

    expected_source_root = (root / "external/lerobot/src").resolve()
    lerobot_path = Path(lerobot.__file__).resolve()
    if expected_source_root not in lerobot_path.parents:
        raise ValueError("PI0.5 fixture did not import the pinned LeRobot source")

    checkpoint_root = _snapshot_root(
        cache,
        repository_id=CHECKPOINT_REPOSITORY_ID,
        revision=CHECKPOINT_REVISION,
    )
    tokenizer_root = _snapshot_root(
        cache,
        repository_id=TOKENIZER_REPOSITORY_ID,
        revision=TOKENIZER_REVISION,
    )
    if not tokenizer_root.is_dir():
        raise ValueError("PI0.5 fixture tokenizer snapshot is missing")

    decoded_tensors: dict[str, Any] = {}
    decoded_checks = []
    for selected in fixture["selected_frames"]:
        canonical = canonical_fixture_frame(
            role=selected["role"],
            frame_index=selected["frame_index"],
        )
        with Image.open(io.BytesIO(canonical["png_bytes"])) as image:
            if image.mode != "RGB" or image.size != (_WIDTH, _HEIGHT):
                raise ValueError("PI0.5 fixture PNG decoded with wrong geometry")
            array = np.asarray(image, dtype=np.uint8)
        decoded = array.tobytes(order="C")
        if decoded != canonical["decoded_rgb_bytes"]:
            raise ValueError("PI0.5 fixture PNG decoded bytes drifted")
        decoded_checks.append(
            {
                "source_key": selected["source_key"],
                "frame_index": selected["frame_index"],
                "png_sha256": canonical["png_sha256"],
                "decoded_rgb_sha256": hashlib.sha256(decoded).hexdigest(),
                "decoded_shape": [_HEIGHT, _WIDTH, _CHANNELS],
                "decoded_dtype": "uint8",
            }
        )
        decoded_tensors[selected["source_key"]] = (
            torch.from_numpy(array.copy()).permute(2, 0, 1).to(torch.float32) / 255.0
        )

    state = torch.tensor(fixture["state_values"], dtype=torch.float32)
    batch = {
        **decoded_tensors,
        "observation.state": state,
        "task": fixture["task_text"],
    }

    with tempfile.TemporaryDirectory(prefix="scenesmith-pi05-processor-") as temp_dir:
        mirror = Path(temp_dir)
        for filename in _CHECKPOINT_PREPROCESSOR_FILES:
            source = checkpoint_root / filename
            if not source.is_file():
                raise ValueError(f"PI0.5 fixture processor source is missing: {filename}")
            shutil.copyfile(source, mirror / filename)
        with _strict_offline_runtime(network_attempts):
            processor = DataProcessorPipeline.from_pretrained(
                mirror,
                config_filename="policy_preprocessor.json",
                local_files_only=True,
                overrides={"device_processor": {"device": "cpu"}},
            )
            output = processor(batch)
    if network_attempts:
        raise ValueError("PI0.5 fixture attempted network access")

    expected_steps = source_contract["effective_preprocessor"]["step_order"]
    actual_steps = [
        getattr(step.__class__, "__name__", "") for step in processor.steps
    ]
    expected_step_classes = [
        "RenameObservationsProcessorStep",
        "AddBatchDimensionProcessorStep",
        "NormalizerProcessorStep",
        "Pi05PrepareStateTokenizerProcessorStep",
        "TokenizerProcessorStep",
        "DeviceProcessorStep",
    ]
    if actual_steps != expected_step_classes or len(expected_steps) != len(actual_steps):
        raise ValueError("PI0.5 fixture processor step order drifted")
    if getattr(processor.steps[-1], "device", None) != "cpu":
        raise ValueError("PI0.5 fixture processor device override drifted")

    prompt_values = output.get("task")
    if not isinstance(prompt_values, list) or len(prompt_values) != 1:
        raise ValueError("PI0.5 fixture prompt output is malformed")
    prompt_text = prompt_values[0]
    match = re.fullmatch(r"Task: .+, State: (-?[0-9]+(?: -?[0-9]+){5});\nAction: ", prompt_text)
    if match is None:
        raise ValueError("PI0.5 fixture prompt semantics drifted")
    discretized_state = [int(value) for value in match.group(1).split()]

    output_keys = [
        "observation.images.base_0_rgb",
        "observation.images.left_wrist_0_rgb",
        "observation.state",
        "observation.language.tokens",
        "observation.language.attention_mask",
    ]
    preprocessor_outputs = {}
    for key in output_keys:
        tensor = output.get(key)
        if not isinstance(tensor, torch.Tensor):
            raise ValueError(f"PI0.5 fixture output tensor is missing: {key}")
        preprocessor_outputs[key] = _tensor_descriptor(tensor)

    normalized_state_values = [
        float(value) for value in output["observation.state"][0].tolist()
    ]
    state_stats = getattr(processor.steps[2], "stats", {}).get(
        "observation.state"
    )
    state_support_audit = build_state_support_audit(
        state_stats,
        state_values=fixture["state_values"],
        normalized_values=normalized_state_values,
        discretized_values=discretized_state,
        source_contract=source_contract,
    )

    token_ids = output["observation.language.tokens"]
    attention = output["observation.language.attention_mask"]
    nonpadding = token_ids[attention]
    tokenizer_output = {
        "max_length": int(token_ids.shape[-1]),
        "nonpadding_length": int(attention.sum().item()),
        "nonpadding_token_ids": [int(value) for value in nonpadding.tolist()],
        "padding_side": "right",
        "truncation": True,
    }

    class _NoModelImagePreprocessShim:
        config = SimpleNamespace(
            image_features={key: None for key in _MODEL_IMAGE_ORDER},
            image_resolution=(224, 224),
        )

        @staticmethod
        def parameters() -> Iterator[Any]:
            yield torch.empty(0, dtype=torch.float32, device="cpu")

    model_images, model_masks = PI05Policy._preprocess_images(
        _NoModelImagePreprocessShim(),
        output,
    )
    if len(model_images) != 3 or len(model_masks) != 3:
        raise ValueError("PI0.5 fixture model image cardinality drifted")
    entries = []
    for index, model_key in enumerate(_MODEL_IMAGE_ORDER):
        missing = model_key == _MODEL_IMAGE_ORDER[-1]
        mask_value = bool(model_masks[index].item())
        if mask_value is missing:
            raise ValueError("PI0.5 fixture missing-camera mask drifted")
        tensor = model_images[index]
        if missing and not bool(torch.all(tensor == -1.0).item()):
            raise ValueError("PI0.5 fixture missing-camera fill drifted")
        entries.append(
            {
                "model_key": model_key,
                "source_kind": "missing_optional_camera" if missing else "selected_fixture_png",
                "mask_value": mask_value,
                "fill_value": -1.0 if missing else None,
                "tensor": _tensor_descriptor(tensor),
                "mask": _tensor_descriptor(model_masks[index]),
            }
        )

    checkpoint = source_contract["checkpoint_processor_snapshot"]["checkpoint_config"]
    action_contract = {
        "representation": "absolute_joint_positions",
        "joint_order": list(_JOINT_ORDER),
        "joint_units": ["degrees"] * 5 + ["percent"],
        "output_action_width": checkpoint["output_action_width"],
        "max_action_dim": checkpoint["max_action_dim"],
        "chunk_size": checkpoint["chunk_size"],
        "n_action_steps": checkpoint["n_action_steps"],
        "open_loop_horizon_steps": checkpoint["n_action_steps"],
        "relative_actions": checkpoint["relative_actions"],
        "reset_required_before_first_sample": True,
        "reset_semantics": "PI05Policy.reset empties _action_queue before a new sample",
        "queue_created": False,
        "queue_reset_executed": False,
        "action_proposal_created": False,
        "postprocessor_run": False,
    }

    runtime = {
        "schema_version": PI05_FIXTURE_PREPROCESSING_RUNTIME_SCHEMA_VERSION,
        "evidence_mode": "deterministic_fixture_preprocessing_runtime",
        "qualification_scope": "fixture_pi05_model_input_parity_runtime",
        "source_contract_identity_sha256": source_contract["identity_sha256"],
        "reviewed_input_gate_identity_sha256": reviewed_gate["identity_sha256"],
        "fixture_input_spec_identity_sha256": fixture["identity_sha256"],
        "runtime": {
            "python_version": platform.python_version(),
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "numpy_version": np.__version__,
            "lerobot_source": "external/lerobot/src/lerobot",
            "stack_identity_sha256": source_contract["runtime_contract"]["stack_identity_sha256"],
            "strict_offline": True,
            "network_attempt_count": 0,
            "processor_input_mirror_files": list(_CHECKPOINT_PREPROCESSOR_FILES),
            "checkpoint_snapshot_revision": CHECKPOINT_REVISION,
            "tokenizer_snapshot_revision": TOKENIZER_REVISION,
            "source_step_order": expected_steps,
            "runtime_step_classes": actual_steps,
            "source_device": "cuda",
            "effective_device": "cpu",
            "device_override_is_only_semantic_config_mutation": True,
            "model_image_method": "PI05Policy._preprocess_images_unbound_no_model_shim",
        },
        "decoded_frame_checks": decoded_checks,
        "state_input": {
            "selection": "q_after",
            "joint_order": list(_JOINT_ORDER),
            "units": ["degrees"] * 5 + ["percent"],
            "values": fixture["state_values"],
            "tensor": _tensor_descriptor(state),
        },
        "prompt_text": prompt_text,
        "prompt_utf8_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
        "discretized_state": discretized_state,
        "state_support_audit": state_support_audit,
        "preprocessor_outputs": preprocessor_outputs,
        "tokenizer_output": tokenizer_output,
        "model_image_inputs": {
            "ordered_keys": list(_MODEL_IMAGE_ORDER),
            "image_resolution": [224, 224],
            "resize_mode": "bilinear_align_corners_false_with_zero_padding",
            "input_range": [0.0, 1.0],
            "model_range": [-1.0, 1.0],
            "entries": entries,
        },
        "model_call_contract": {
            "source_method": "PI05Policy.predict_action_chunk",
            "model_method": "self.model.sample_actions",
            "positional_argument_order": ["images", "img_masks", "tokens", "masks"],
            "image_count": 3,
            "separate_state_tensor_passed_to_model": False,
            "state_semantics_embedded_in_prompt_tokens": True,
            "model_call_executed": False,
        },
        "action_contract": action_contract,
        "processor_instantiated": True,
        "tokenizer_instantiated": True,
        "preprocessing_run": True,
        **_FALSE_RUNTIME_FACTS,
        "local_capabilities": [
            "fixture_pi05_preprocessing_runtime_observed",
            "fixture_pi05_training_support_audit_runtime_observed",
        ],
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
    }
    return sign_payload(runtime)


def build_pi05_fixture_model_ready_parity(
    runtime_result: dict[str, Any],
    *,
    repo_root: Path,
    hf_cache_root: Path,
    calibration_path: Path,
) -> dict[str, Any]:
    """Compose the golden runtime result with independently rebuilt fixture sources."""

    root = Path(repo_root).resolve()
    source, gate = _load_and_verify_sources(
        repo_root=root,
        hf_cache_root=Path(hf_cache_root).resolve(),
        calibration_path=Path(calibration_path).resolve(),
    )
    fixture = build_fixture_input_spec(repo_root=root)
    _verify_runtime_result(runtime_result, source=source, gate=gate, fixture=fixture)
    if runtime_result["identity_sha256"] != EXPECTED_RUNTIME_RESULT_IDENTITY:
        raise ValueError(
            "PI0.5 fixture runtime identity is not the reviewed golden result: "
            f"observed {runtime_result['identity_sha256']}"
        )
    return sign_payload(
        {
            "schema_version": PI05_FIXTURE_MODEL_READY_PARITY_SCHEMA_VERSION,
            "artifact_name": "pi05_fixture_model_ready_tensor_parity",
            "evidence_mode": "deterministic_fixture_preprocessing",
            "qualification_scope": "fixture_pi05_model_input_parity",
            "production_eligible": False,
            "source_contract": _tracked_artifact_reference(
                root / _SOURCE_CONTRACT_PATH,
                repo_root=root,
                payload=source,
            ),
            "reviewed_input_gate": _tracked_artifact_reference(
                root / _REVIEWED_INPUT_GATE_PATH,
                repo_root=root,
                payload=gate,
            ),
            "fixture_review_shape": {
                "classification": "accepted_review_shaped_deterministic_fixture",
                "production_eligible": False,
                "real_reviewed_input_gate_status": gate["status"],
                "real_reviewed_inputs_present": False,
                "accepted_live_session": False,
                "camera_roles_fixture_bound": True,
                "task_prompt_fixture_bound": True,
            },
            "fixture_input_spec": fixture,
            "runtime_result": runtime_result,
            "model_ready_tensor_hashes_recorded": True,
            "policy_input_built_for_fixture_only": True,
            "accepted_live_policy_input": False,
            "model_instantiated": False,
            "model_weights_named": False,
            "model_weights_read": False,
            "policy_inference_run": False,
            "policy_shadow_run": False,
            "mujoco_replay_run": False,
            "network_accessed": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "local_capabilities": list(_LOCAL_CAPABILITIES),
            "proof_labels": [],
            "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        }
    )


def verify_pi05_fixture_model_ready_parity(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    hf_cache_root: Path,
    calibration_path: Path,
) -> None:
    """Rebuild every nonopaque source and require the reviewed runtime golden."""

    if not isinstance(payload, dict):
        raise ValueError("PI0.5 fixture parity artifact must be an object")
    if payload.get("schema_version") != PI05_FIXTURE_MODEL_READY_PARITY_SCHEMA_VERSION:
        raise ValueError("PI0.5 fixture parity schema is unsupported")
    verify_signed_payload(payload, label="PI0.5 fixture parity artifact")
    runtime = payload.get("runtime_result")
    if not isinstance(runtime, dict):
        raise ValueError("PI0.5 fixture runtime result is missing")
    expected = build_pi05_fixture_model_ready_parity(
        runtime,
        repo_root=repo_root,
        hf_cache_root=hf_cache_root,
        calibration_path=calibration_path,
    )
    if payload != expected:
        raise ValueError("PI0.5 fixture parity artifact drifted from sources")


def _load_and_verify_sources(
    *,
    repo_root: Path,
    hf_cache_root: Path,
    calibration_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = load_strict_json(repo_root / _SOURCE_CONTRACT_PATH)
    verify_pi05_preprocessing_source_contract(
        source,
        repo_root=repo_root,
        hf_cache_root=hf_cache_root,
        calibration_path=calibration_path,
    )
    gate = load_strict_json(repo_root / _REVIEWED_INPUT_GATE_PATH)
    verify_pi05_reviewed_input_gate(
        gate,
        repo_root=repo_root,
        hf_cache_root=hf_cache_root,
        calibration_path=calibration_path,
    )
    if (
        source.get("status") != "blocked_missing_inputs"
        or source.get("production_preprocessing_allowed") is not False
        or gate.get("status") != "blocked_missing_reviewed_inputs"
        or gate.get("production_input_issuance_allowed") is not False
        or gate.get("missing_inputs")
        != [
            "accepted_live_session_review_decision",
            "reviewed_stable_camera_role_binding",
            "reviewed_task_prompt",
        ]
    ):
        raise ValueError("PI0.5 fixture source gates no longer fail closed")
    return source, gate


def _verify_runtime_result(
    runtime: dict[str, Any],
    *,
    source: dict[str, Any],
    gate: dict[str, Any],
    fixture: dict[str, Any],
) -> None:
    if not isinstance(runtime, dict):
        raise ValueError("PI0.5 fixture runtime must be an object")
    verify_signed_payload(runtime, label="PI0.5 fixture preprocessing runtime")
    if (
        runtime.get("schema_version")
        != PI05_FIXTURE_PREPROCESSING_RUNTIME_SCHEMA_VERSION
        or runtime.get("evidence_mode")
        != "deterministic_fixture_preprocessing_runtime"
        or runtime.get("qualification_scope")
        != "fixture_pi05_model_input_parity_runtime"
        or runtime.get("source_contract_identity_sha256")
        != source.get("identity_sha256")
        or runtime.get("reviewed_input_gate_identity_sha256")
        != gate.get("identity_sha256")
        or runtime.get("fixture_input_spec_identity_sha256")
        != fixture.get("identity_sha256")
        or runtime.get("processor_instantiated") is not True
        or runtime.get("tokenizer_instantiated") is not True
        or runtime.get("preprocessing_run") is not True
        or runtime.get("local_capabilities")
        != [
            "fixture_pi05_preprocessing_runtime_observed",
            "fixture_pi05_training_support_audit_runtime_observed",
        ]
        or runtime.get("proof_labels") != []
        or runtime.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
    ):
        raise ValueError("PI0.5 fixture runtime classification drifted")
    for field, expected in _FALSE_RUNTIME_FACTS.items():
        if runtime.get(field) is not expected:
            raise ValueError(f"PI0.5 fixture runtime fact drifted: {field}")

    runtime_env = runtime.get("runtime")
    if (
        not isinstance(runtime_env, dict)
        or runtime_env.get("strict_offline") is not True
        or runtime_env.get("network_attempt_count") != 0
        or runtime_env.get("source_device") != "cuda"
        or runtime_env.get("effective_device") != "cpu"
        or runtime_env.get("device_override_is_only_semantic_config_mutation")
        is not True
        or runtime_env.get("checkpoint_snapshot_revision") != CHECKPOINT_REVISION
        or runtime_env.get("tokenizer_snapshot_revision") != TOKENIZER_REVISION
        or runtime_env.get("stack_identity_sha256")
        != source["runtime_contract"]["stack_identity_sha256"]
        or runtime_env.get("source_step_order")
        != source["effective_preprocessor"]["step_order"]
        or runtime_env.get("model_image_method")
        != "PI05Policy._preprocess_images_unbound_no_model_shim"
    ):
        raise ValueError("PI0.5 fixture runtime environment drifted")

    decoded = runtime.get("decoded_frame_checks")
    if not isinstance(decoded, list) or len(decoded) != 2:
        raise ValueError("PI0.5 fixture decoded-frame evidence is incomplete")
    for observed, expected in zip(decoded, fixture["selected_frames"]):
        if observed != {
            "source_key": expected["source_key"],
            "frame_index": expected["frame_index"],
            "png_sha256": expected["png_sha256"],
            "decoded_rgb_sha256": expected["decoded_rgb_sha256"],
            "decoded_shape": [_HEIGHT, _WIDTH, _CHANNELS],
            "decoded_dtype": "uint8",
        }:
            raise ValueError("PI0.5 fixture decoded-frame evidence drifted")

    state = runtime.get("state_input")
    if (
        not isinstance(state, dict)
        or state.get("selection") != "q_after"
        or state.get("joint_order") != _JOINT_ORDER
        or state.get("units") != ["degrees"] * 5 + ["percent"]
        or state.get("values") != fixture["state_values"]
    ):
        raise ValueError("PI0.5 fixture state input drifted")
    _verify_tensor_descriptor(state.get("tensor"), label="PI0.5 fixture raw state")

    prompt = runtime.get("prompt_text")
    if (
        not isinstance(prompt, str)
        or not prompt.startswith(f"Task: {_TASK_TEXT}, State: ")
        or not prompt.endswith(";\nAction: ")
        or runtime.get("prompt_utf8_sha256")
        != hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        or not isinstance(runtime.get("discretized_state"), list)
        or len(runtime["discretized_state"]) != 6
        or any(type(value) is not int or value < -1 or value > 255 for value in runtime["discretized_state"])
    ):
        raise ValueError("PI0.5 fixture prompt output drifted")

    verify_state_support_audit(
        runtime.get("state_support_audit"),
        state_values=fixture["state_values"],
        discretized_values=runtime["discretized_state"],
        source=source,
    )

    outputs = runtime.get("preprocessor_outputs")
    expected_output_keys = {
        "observation.images.base_0_rgb",
        "observation.images.left_wrist_0_rgb",
        "observation.state",
        "observation.language.tokens",
        "observation.language.attention_mask",
    }
    if not isinstance(outputs, dict) or set(outputs) != expected_output_keys:
        raise ValueError("PI0.5 fixture preprocessor output keys drifted")
    for key, descriptor in outputs.items():
        _verify_tensor_descriptor(descriptor, label=f"PI0.5 fixture output {key}")

    tokenizer = runtime.get("tokenizer_output")
    if (
        not isinstance(tokenizer, dict)
        or tokenizer.get("max_length") != 200
        or type(tokenizer.get("nonpadding_length")) is not int
        or tokenizer["nonpadding_length"] <= 0
        or tokenizer["nonpadding_length"] > 200
        or not isinstance(tokenizer.get("nonpadding_token_ids"), list)
        or len(tokenizer["nonpadding_token_ids"]) != tokenizer["nonpadding_length"]
        or any(type(value) is not int or value < 0 for value in tokenizer["nonpadding_token_ids"])
        or tokenizer.get("padding_side") != "right"
        or tokenizer.get("truncation") is not True
    ):
        raise ValueError("PI0.5 fixture tokenizer output drifted")

    images = runtime.get("model_image_inputs")
    if (
        not isinstance(images, dict)
        or images.get("ordered_keys") != _MODEL_IMAGE_ORDER
        or images.get("image_resolution") != [224, 224]
        or images.get("resize_mode")
        != "bilinear_align_corners_false_with_zero_padding"
        or images.get("input_range") != [0.0, 1.0]
        or images.get("model_range") != [-1.0, 1.0]
        or not isinstance(images.get("entries"), list)
        or len(images["entries"]) != 3
    ):
        raise ValueError("PI0.5 fixture model image contract drifted")
    for index, entry in enumerate(images["entries"]):
        missing = index == 2
        if (
            entry.get("model_key") != _MODEL_IMAGE_ORDER[index]
            or entry.get("source_kind")
            != ("missing_optional_camera" if missing else "selected_fixture_png")
            or entry.get("mask_value") is not (not missing)
            or entry.get("fill_value") != (-1.0 if missing else None)
        ):
            raise ValueError("PI0.5 fixture model image entry drifted")
        _verify_tensor_descriptor(entry.get("tensor"), label="PI0.5 fixture model image")
        _verify_tensor_descriptor(entry.get("mask"), label="PI0.5 fixture model mask")

    if runtime.get("model_call_contract") != {
        "source_method": "PI05Policy.predict_action_chunk",
        "model_method": "self.model.sample_actions",
        "positional_argument_order": ["images", "img_masks", "tokens", "masks"],
        "image_count": 3,
        "separate_state_tensor_passed_to_model": False,
        "state_semantics_embedded_in_prompt_tokens": True,
        "model_call_executed": False,
    }:
        raise ValueError("PI0.5 fixture model-call contract drifted")

    checkpoint = source["checkpoint_processor_snapshot"]["checkpoint_config"]
    action = runtime.get("action_contract")
    expected_action = {
        "representation": "absolute_joint_positions",
        "joint_order": list(_JOINT_ORDER),
        "joint_units": ["degrees"] * 5 + ["percent"],
        "output_action_width": checkpoint["output_action_width"],
        "max_action_dim": checkpoint["max_action_dim"],
        "chunk_size": checkpoint["chunk_size"],
        "n_action_steps": checkpoint["n_action_steps"],
        "open_loop_horizon_steps": checkpoint["n_action_steps"],
        "relative_actions": checkpoint["relative_actions"],
        "reset_required_before_first_sample": True,
        "reset_semantics": "PI05Policy.reset empties _action_queue before a new sample",
        "queue_created": False,
        "queue_reset_executed": False,
        "action_proposal_created": False,
        "postprocessor_run": False,
    }
    if action != expected_action:
        raise ValueError("PI0.5 fixture action/queue contract drifted")


def _verify_tensor_descriptor(value: Any, *, label: str) -> None:
    if not isinstance(value, dict) or set(value) != {
        "shape",
        "dtype",
        "device",
        "serialization",
        "byte_length",
        "sha256",
        "minimum",
        "maximum",
    }:
        raise ValueError(f"{label} descriptor fields drifted")
    shape = value.get("shape")
    if (
        not isinstance(shape, list)
        or any(type(item) is not int or item <= 0 for item in shape)
        or value.get("dtype") not in {"float32", "int64", "bool"}
        or value.get("device") != "cpu"
        or value.get("serialization") != "little_endian_c_order_v1"
        or type(value.get("byte_length")) is not int
        or value["byte_length"] <= 0
        or _SHA256_PATTERN.fullmatch(str(value.get("sha256"))) is None
        or isinstance(value.get("minimum"), bool)
        or isinstance(value.get("maximum"), bool)
        or not isinstance(value.get("minimum"), (int, float))
        or not isinstance(value.get("maximum"), (int, float))
        or value["minimum"] > value["maximum"]
    ):
        raise ValueError(f"{label} descriptor is invalid")


def _tensor_descriptor(tensor: Any) -> dict[str, Any]:
    import numpy as np
    import torch

    value = tensor.detach().cpu().contiguous()
    dtype = str(value.dtype).removeprefix("torch.")
    dtype_map = {
        "float32": np.dtype("<f4"),
        "int64": np.dtype("<i8"),
        "bool": np.dtype("u1"),
    }
    if dtype not in dtype_map:
        raise ValueError(f"PI0.5 fixture tensor dtype is unsupported: {dtype}")
    array = value.numpy().astype(dtype_map[dtype], copy=False)
    encoded = array.tobytes(order="C")
    minimum = value.min().item()
    maximum = value.max().item()
    return {
        "shape": list(value.shape),
        "dtype": dtype,
        "device": "cpu",
        "serialization": "little_endian_c_order_v1",
        "byte_length": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "minimum": int(minimum) if dtype in {"int64", "bool"} else float(minimum),
        "maximum": int(maximum) if dtype in {"int64", "bool"} else float(maximum),
    }


@contextmanager
def _strict_offline_runtime(network_attempts: list[str]) -> Iterator[None]:
    environment_keys = (
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "HF_DATASETS_OFFLINE",
    )
    previous = {key: os.environ.get(key) for key in environment_keys}
    original_connect = socket.socket.connect

    def blocked_connect(instance: socket.socket, address: Any) -> None:
        network_attempts.append(repr(address))
        raise RuntimeError("PI0.5 fixture runtime forbids network access")

    for key in environment_keys:
        os.environ[key] = "1"
    socket.socket.connect = blocked_connect
    try:
        yield
    finally:
        socket.socket.connect = original_connect
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@lru_cache(maxsize=4)
def _canonical_fixture_frame_bytes(role: str, frame_index: int) -> tuple[bytes, bytes]:
    role_seed = 17 if role == "top" else 83
    seed = role_seed + 29 * frame_index
    rgb = bytearray(_WIDTH * _HEIGHT * _CHANNELS)
    offset = 0
    for y in range(_HEIGHT):
        for x in range(_WIDTH):
            rgb[offset] = (x + 3 * y + seed) & 0xFF
            rgb[offset + 1] = (5 * x + y + 2 * seed) & 0xFF
            rgb[offset + 2] = ((x ^ y) + 7 * seed) & 0xFF
            offset += 3
    scanlines = bytearray()
    row_bytes = _WIDTH * _CHANNELS
    for y in range(_HEIGHT):
        scanlines.append(0)
        start = y * row_bytes
        scanlines.extend(rgb[start : start + row_bytes])
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(_png_chunk(b"IHDR", struct.pack(">IIBBBBB", _WIDTH, _HEIGHT, 8, 2, 0, 0, 0)))
    png.extend(_png_chunk(b"IDAT", _stored_zlib_stream(bytes(scanlines))))
    png.extend(_png_chunk(b"IEND", b""))
    return bytes(png), bytes(rgb)


def _stored_zlib_stream(payload: bytes) -> bytes:
    encoded = bytearray(b"\x78\x01")
    offset = 0
    while offset < len(payload):
        size = min(65_535, len(payload) - offset)
        final = offset + size == len(payload)
        encoded.append(1 if final else 0)
        encoded.extend(struct.pack("<HH", size, 0xFFFF ^ size))
        encoded.extend(payload[offset : offset + size])
        offset += size
    encoded.extend(struct.pack(">I", _adler32(payload)))
    return bytes(encoded)


def _adler32(payload: bytes) -> int:
    first = 1
    second = 0
    modulus = 65_521
    for offset in range(0, len(payload), 5_552):
        for value in payload[offset : offset + 5_552]:
            first += value
            second += first
        first %= modulus
        second %= modulus
    return (second << 16) | first


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _snapshot_root(cache: Path, *, repository_id: str, revision: str) -> Path:
    repository = "models--" + repository_id.replace("/", "--")
    root = cache / repository / "snapshots" / revision
    if not root.is_dir():
        raise ValueError(f"PI0.5 cached snapshot is missing: {repository_id}")
    return root


def _tracked_artifact_reference(
    path: Path,
    *,
    repo_root: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    resolved = path.resolve()
    relative = resolved.relative_to(repo_root).as_posix()
    encoded = resolved.read_bytes()
    return {
        "path": relative,
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "size_bytes": len(encoded),
    }


def _require_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be lowercase SHA-256")
    return value


__all__ = [
    "EXPECTED_RUNTIME_RESULT_IDENTITY",
    "PI05_FIXTURE_MODEL_READY_PARITY_SCHEMA_VERSION",
    "build_fixture_input_spec",
    "build_pi05_fixture_model_ready_parity",
    "canonical_fixture_frame",
    "execute_pi05_fixture_preprocessing",
    "verify_pi05_fixture_model_ready_parity",
]
