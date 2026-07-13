"""Immutable fixture-scoped normalization and preprocessing bundle."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import artifact_ref, load_strict_json, sign_payload, verify_artifact_ref, verify_signed_payload
from scenesmith.robot_lab.so101_processor import CONTRACT_PATH as PROCESSOR_PATH, JOINT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_PATH = Path("configurations/robot_lab/normalization_bundle.json")
PARITY_PATH = Path("configurations/robot_lab/pi05_fixture_model_ready_tensor_parity.json")
DEPENDENCY_PATH = Path("configurations/robot_lab/pi05_robotics_dependency_lock.json")
SCHEMA_VERSION = "scenesmith.normalization_bundle.v1"
STATISTIC_ORDER = ("min", "q01", "q10", "q50", "q90", "q99", "max", "mean", "std")
CAMERA_ORDER = ("observation.images.base_0_rgb", "observation.images.left_wrist_0_rgb", "observation.images.right_wrist_0_rgb")


def build_normalization_bundle(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    processor = load_strict_json(repo_root / PROCESSOR_PATH)
    parity = load_strict_json(repo_root / PARITY_PATH)
    dependency = load_strict_json(repo_root / DEPENDENCY_PATH)
    for payload, label in ((processor, "processor"), (parity, "fixture parity"), (dependency, "dependency lock")):
        verify_signed_payload(payload, label=label)
    runtime = parity["runtime_result"]
    audit = runtime["state_support_audit"]
    images = runtime["model_image_inputs"]
    tokenizer = runtime["tokenizer_output"]
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "bundle_name": "so101_pi05_fixture_normalization_v1",
        "scope": "actual_cached_processor_fixture_parity_not_production_input",
        "source_refs": {
            "canonical_processor": artifact_ref(path=PROCESSOR_PATH, payload=processor, repo_root=repo_root),
            "fixture_tensor_parity": artifact_ref(path=PARITY_PATH, payload=parity, repo_root=repo_root),
            "robotics_dependency_lock": artifact_ref(path=DEPENDENCY_PATH, payload=dependency, repo_root=repo_root),
        },
        "feature_order": list(JOINT_NAMES),
        "normalization": {
            "mode": audit["normalization_mode"],
            "mode_mutated": audit["normalization_mode_mutated"],
            "sample_count": audit["sample_count"],
            "statistic_order": list(STATISTIC_ORDER),
            "statistics": audit["statistics"],
            "normalizer_file_sha256": audit["normalizer_file_sha256"],
        },
        "preprocessing": {
            "stack_identity_sha256": runtime["runtime"]["stack_identity_sha256"],
            "checkpoint_snapshot_revision": runtime["runtime"]["checkpoint_snapshot_revision"],
            "tokenizer_snapshot_revision": runtime["runtime"]["tokenizer_snapshot_revision"],
            "processor_step_order": runtime["runtime"]["source_step_order"],
            "processor_step_classes": runtime["runtime"]["runtime_step_classes"],
            "strict_offline": runtime["runtime"]["strict_offline"],
            "tokenizer": {"max_length": tokenizer["max_length"], "padding_side": tokenizer["padding_side"], "truncation": tokenizer["truncation"]},
            "camera_order": images["ordered_keys"],
            "image_resolution": images["image_resolution"],
            "input_range": images["input_range"],
            "model_range": images["model_range"],
            "resize_mode": images["resize_mode"],
            "model_image_entries": images["entries"],
            "preprocessor_output_sha256": {key: value["sha256"] for key, value in runtime["preprocessor_outputs"].items()},
        },
        "actual_cached_processor_executed": runtime["processor_instantiated"] and runtime["tokenizer_instantiated"] and runtime["preprocessing_run"],
        "model_call_executed": runtime["model_call_contract"]["model_call_executed"],
        "fixture_normalization_bundle_valid": True,
        "production_eligible": False,
        "compiled_training_frames": False,
        "simulation_training_ready": False,
        "hardware_accessed": False,
        "authority_not_granted": ["production_normalization_valid", "compiled_training_frames", "simulation_training_ready", "optimizer_training", "physical_actuation"],
    }
    return sign_payload(bundle)


def verify_normalization_bundle(payload: dict[str, Any], *, repo_root: Path = REPO_ROOT) -> None:
    verify_signed_payload(payload, label="normalization bundle")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Normalization bundle schema is invalid")
    expected = build_normalization_bundle(repo_root=repo_root)
    for key in expected["source_refs"]:
        verify_artifact_ref(payload.get("source_refs", {}).get(key), expected["source_refs"][key], label=key)
    if payload != expected:
        raise ValueError("Normalization bundle drifted")
    normalization = payload["normalization"]
    if normalization["mode"] != "MEAN_STD" or normalization["mode_mutated"]:
        raise ValueError("Normalization mode drifted")
    if normalization["statistic_order"] != list(STATISTIC_ORDER):
        raise ValueError("Normalization statistic order drifted")
    for name in STATISTIC_ORDER:
        values = normalization["statistics"].get(name)
        if not isinstance(values, list) or len(values) != len(JOINT_NAMES) or any(isinstance(value, bool) or not math.isfinite(float(value)) for value in values):
            raise ValueError(f"Normalization {name} vector is invalid")
    if any(value <= 0 for value in normalization["statistics"]["std"]):
        raise ValueError("Normalization std must be positive")
    if payload["feature_order"] != list(JOINT_NAMES) or payload["preprocessing"]["camera_order"] != list(CAMERA_ORDER):
        raise ValueError("Normalization feature or camera order drifted")
    if not payload["actual_cached_processor_executed"] or payload["production_eligible"] or payload["simulation_training_ready"]:
        raise ValueError("Normalization bundle proof scope is invalid")
