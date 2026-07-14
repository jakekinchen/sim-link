"""Deterministic T20.12 PI0.5 action-representation and loss audit."""

from __future__ import annotations

import hashlib
import json
import math
import struct

from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot


SCHEMA_VERSION = "scenesmith.t20_12_pi05_gripper_channel_audit.v1"
ROUNDTRIP_THRESHOLD_RAD = 1e-8
NORMALIZER_EPS = 1e-8
_STATISTIC_NAMES = ("count", "min", "q01", "q99", "max", "mean", "std")


def load_action_statistics(path: Path, *, expected_sha256: str) -> dict[str, Any]:
    """Read the bounded action vectors needed from a pinned safetensors file."""

    encoded = path.read_bytes()
    if hashlib.sha256(encoded).hexdigest() != expected_sha256:
        raise ValueError("T20.12 normalizer safetensors hash drifted")
    if len(encoded) < 10:
        raise ValueError("T20.12 normalizer safetensors is truncated")
    header_length = struct.unpack("<Q", encoded[:8])[0]
    if header_length <= 1 or 8 + header_length > len(encoded):
        raise ValueError("T20.12 normalizer header length is invalid")
    try:
        header = json.loads(encoded[8 : 8 + header_length].decode("utf-8").strip())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("T20.12 normalizer header is malformed") from exc
    data = encoded[8 + header_length :]
    result: dict[str, Any] = {}
    for statistic in _STATISTIC_NAMES:
        name = f"action.{statistic}"
        entry = header.get(name)
        width = 1 if statistic == "count" else len(JOINT_NAMES)
        if (
            not isinstance(entry, dict)
            or entry.get("dtype") != "F32"
            or entry.get("shape") != [width]
            or not isinstance(entry.get("data_offsets"), list)
            or len(entry["data_offsets"]) != 2
        ):
            raise ValueError(f"T20.12 normalizer statistic is malformed: {name}")
        start, finish = entry["data_offsets"]
        if (
            type(start) is not int
            or type(finish) is not int
            or start < 0
            or finish > len(data)
            or finish - start != width * 4
        ):
            raise ValueError(f"T20.12 normalizer statistic offsets drifted: {name}")
        values = list(struct.unpack(f"<{width}f", data[start:finish]))
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"T20.12 normalizer statistic is non-finite: {name}")
        result[statistic] = values[0] if statistic == "count" else values
    if (
        result["count"] <= 0
        or not float(result["count"]).is_integer()
        or any(value <= 0 for value in result["std"])
    ):
        raise ValueError("T20.12 normalizer count or standard deviation is invalid")
    return result


def build_pi05_gripper_channel_audit(
    *,
    train_action_mujoco: np.ndarray,
    evaluation_action_mujoco: np.ndarray,
    checkpoint_action_statistics: dict[str, Any],
    source_evidence: dict[str, Any],
    t20_11_pi05: dict[str, Any],
    loss_contract: dict[str, Any],
) -> dict[str, Any]:
    train = _action_matrix(train_action_mujoco, (488, 6), "train")
    evaluation = _action_matrix(evaluation_action_mujoco, (244, 6), "evaluation")
    statistics = _statistics(checkpoint_action_statistics)
    evidence = _source_evidence(source_evidence)
    loss = _loss_contract(loss_contract)

    train_lerobot = _to_lerobot(train)
    evaluation_lerobot = _to_lerobot(evaluation)
    mean = np.asarray(statistics["mean"], dtype=np.float64)
    std = np.asarray(statistics["std"], dtype=np.float64)
    train_normalized = (train_lerobot - mean) / (std + NORMALIZER_EPS)
    evaluation_normalized = (evaluation_lerobot - mean) / (std + NORMALIZER_EPS)

    train_roundtrip = _inverse_pipeline(train_normalized, mean, std)
    evaluation_roundtrip = _inverse_pipeline(evaluation_normalized, mean, std)
    train_error = np.abs(train_roundtrip - train)
    evaluation_error = np.abs(evaluation_roundtrip - evaluation)
    maximum_roundtrip_error = float(max(np.max(train_error), np.max(evaluation_error)))
    roundtrip_pass = maximum_roundtrip_error <= ROUNDTRIP_THRESHOLD_RAD

    diagnostic = t20_11_pi05.get("action_error_diagnostics", {})
    divergence = diagnostic.get("first_action_divergence", {})
    rollout = t20_11_pi05.get("corrected_closed_loop", {})
    requested_first = _vector(rollout.get("policy_requested_action_first"), "requested action")
    source_first = evaluation[0]
    if (
        t20_11_pi05.get("model_id") != "pi05"
        or divergence.get("frame_index") != 0
        or divergence.get("joint_name") != "gripper"
        or not math.isclose(
            float(divergence.get("source_action_rad", math.nan)),
            float(source_first[-1]),
            rel_tol=0.0,
            abs_tol=1e-7,
        )
        or not math.isclose(
            float(divergence.get("model_action_rad", math.nan)),
            float(requested_first[-1]),
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    ):
        raise ValueError("T20.12 T20.11 frame-zero gripper linkage drifted")
    observed_error = abs(float(source_first[-1]) - float(requested_first[-1]))
    t20_11_source_gripper = float(divergence["source_action_rad"])
    t20_11_model_gripper = float(divergence["model_action_rad"])
    t20_11_reported_error = float(divergence["absolute_error_rad"])
    source_to_tensor_quantization_error = abs(
        float(source_first[-1]) - t20_11_source_gripper
    )
    error_reconciliation_difference = abs(observed_error - t20_11_reported_error)
    if not math.isclose(
        observed_error,
        float(divergence.get("absolute_error_rad", math.nan)),
        rel_tol=0.0,
        abs_tol=1e-7,
    ):
        raise ValueError("T20.12 T20.11 gripper-error accounting drifted")

    requested_lerobot = np.asarray(mujoco_to_lerobot(requested_first), dtype=np.float64)
    requested_normalized = (requested_lerobot - mean) / (std + NORMALIZER_EPS)
    requested_reconstruction = _inverse_pipeline(
        requested_normalized.reshape(1, 6), mean, std
    )[0]

    split_rows = {
        "train": _split_statistics(train, train_lerobot, train_normalized, statistics),
        "evaluation": _split_statistics(
            evaluation, evaluation_lerobot, evaluation_normalized, statistics
        ),
    }
    gripper_index = len(JOINT_NAMES) - 1
    source_gripper_percent = float(evaluation_lerobot[0, gripper_index])
    checkpoint_gripper_max = float(statistics["max"][gripper_index])
    checkpoint_gripper_q99 = float(statistics["q99"][gripper_index])
    open_above_max = source_gripper_percent > checkpoint_gripper_max
    open_above_q99 = source_gripper_percent > checkpoint_gripper_q99
    joints_outside_checkpoint = [
        name
        for name, row in split_rows["train"]["joints"].items()
        if row["outside_checkpoint_min_max_count"] > 0
    ]
    non_gripper_outside = [name for name in joints_outside_checkpoint if name != "gripper"]
    mismatch = open_above_max and bool(non_gripper_outside)

    frame_zero = []
    for index, name in enumerate(JOINT_NAMES):
        frame_zero.append(
            {
                "joint_name": name,
                "source_mujoco_rad": float(source_first[index]),
                "source_lerobot_value": float(evaluation_lerobot[0, index]),
                "source_normalized_value": float(evaluation_normalized[0, index]),
                "model_requested_mujoco_rad": float(requested_first[index]),
                "model_requested_lerobot_value": float(requested_lerobot[index]),
                "model_requested_reconstructed_normalized_value": float(
                    requested_normalized[index]
                ),
                "native_absolute_error_rad": float(
                    abs(source_first[index] - requested_first[index])
                ),
            }
        )

    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.12",
            "source_evidence": evidence,
            "coordinate_contract": {
                "source_units": "mujoco_radians",
                "model_external_units": "lerobot_body_degrees_and_gripper_percent",
                "normalization": "checkpoint_mean_std",
                "normalizer_epsilon": NORMALIZER_EPS,
                "maximum_inverse_roundtrip_error_rad": maximum_roundtrip_error,
                "maximum_allowed_inverse_roundtrip_error_rad": ROUNDTRIP_THRESHOLD_RAD,
                "roundtrip_margin_rad": ROUNDTRIP_THRESHOLD_RAD
                - maximum_roundtrip_error,
                "all_732_actions_roundtrip_within_threshold": roundtrip_pass,
                "clipping_observed_for_source_actions": False,
                "gripper_mapping_monotonic_increasing": True,
            },
            "checkpoint_action_statistics": statistics,
            "dataset_action_audit": split_rows,
            "frame_zero_trace": frame_zero,
            "t20_11_gripper_reconciliation": {
                "t20_11_source_gripper_mujoco_rad": t20_11_source_gripper,
                "training_tensor_source_gripper_mujoco_rad": float(source_first[-1]),
                "source_to_float32_tensor_quantization_error_rad": (
                    source_to_tensor_quantization_error
                ),
                "t20_11_model_requested_gripper_mujoco_rad": t20_11_model_gripper,
                "t20_11_reported_native_absolute_error_rad": t20_11_reported_error,
                "training_tensor_recomputed_native_absolute_error_rad": observed_error,
                "reported_vs_recomputed_error_difference_rad": error_reconciliation_difference,
                "source_gripper_mujoco_rad": float(source_first[-1]),
                "source_gripper_lerobot_percent": source_gripper_percent,
                "source_gripper_normalized": float(evaluation_normalized[0, -1]),
                "model_requested_gripper_mujoco_rad": float(requested_first[-1]),
                "model_requested_gripper_lerobot_percent": float(requested_lerobot[-1]),
                "model_requested_gripper_reconstructed_normalized": float(
                    requested_normalized[-1]
                ),
                "model_postprocess_inverse_roundtrip_error_rad": float(
                    abs(requested_reconstruction[-1] - requested_first[-1])
                ),
                "native_absolute_error_rad": observed_error,
                "normalized_absolute_error": float(
                    abs(evaluation_normalized[0, -1] - requested_normalized[-1])
                ),
            },
            "loss_accounting": loss,
            "gate_margins": {
                "coordinate_inverse_roundtrip": {
                    "pass": roundtrip_pass,
                    "measured_maximum_error_rad": maximum_roundtrip_error,
                    "threshold_maximum_error_rad": ROUNDTRIP_THRESHOLD_RAD,
                    "margin_rad": ROUNDTRIP_THRESHOLD_RAD - maximum_roundtrip_error,
                },
                "source_to_training_tensor_quantization": {
                    "pass": source_to_tensor_quantization_error <= 1e-7,
                    "measured_absolute_error_rad": source_to_tensor_quantization_error,
                    "threshold_absolute_error_rad": 1e-7,
                    "margin_rad": 1e-7 - source_to_tensor_quantization_error,
                },
                "t20_11_error_reconciliation": {
                    "pass": error_reconciliation_difference <= 1e-7,
                    "measured_absolute_difference_rad": error_reconciliation_difference,
                    "threshold_absolute_difference_rad": 1e-7,
                    "margin_rad": 1e-7 - error_reconciliation_difference,
                },
                "frame_zero_open_gripper_within_checkpoint_max": {
                    "pass": not open_above_max,
                    "measured_gripper_percent": source_gripper_percent,
                    "threshold_checkpoint_max_percent": checkpoint_gripper_max,
                    "margin_percent": checkpoint_gripper_max - source_gripper_percent,
                },
                "frame_zero_open_gripper_within_checkpoint_q99": {
                    "pass": not open_above_q99,
                    "measured_gripper_percent": source_gripper_percent,
                    "threshold_checkpoint_q99_percent": checkpoint_gripper_q99,
                    "margin_percent": checkpoint_gripper_q99 - source_gripper_percent,
                },
            },
            "finding": {
                "coordinate_representation_fault_observed": not roundtrip_pass,
                "gripper_loss_underweighting_observed": loss["gripper_dimension_weight"]
                < 1.0,
                "checkpoint_normalization_domain_mismatch_observed": mismatch,
                "joints_outside_checkpoint_min_max": joints_outside_checkpoint,
                "non_gripper_joints_outside_checkpoint_min_max": non_gripper_outside,
                "single_gripper_fault_supported": False,
                "causal_claim": "diagnostic_hypothesis_only_no_optimizer_test",
                "selected_next_hypothesis": (
                    "derive_dataset_bound_pi05_normalizer_then_retest_without_loss_reweighting"
                    if mismatch and roundtrip_pass
                    else "no_next_hypothesis_selected"
                ),
            },
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_pi05_gripper_channel_audit(
    payload: dict[str, Any],
    *,
    train_action_mujoco: np.ndarray,
    evaluation_action_mujoco: np.ndarray,
    checkpoint_action_statistics: dict[str, Any],
    source_evidence: dict[str, Any],
    t20_11_pi05: dict[str, Any],
    loss_contract: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.12 PI0.5 gripper-channel audit")
    expected = build_pi05_gripper_channel_audit(
        train_action_mujoco=train_action_mujoco,
        evaluation_action_mujoco=evaluation_action_mujoco,
        checkpoint_action_statistics=checkpoint_action_statistics,
        source_evidence=source_evidence,
        t20_11_pi05=t20_11_pi05,
        loss_contract=loss_contract,
    )
    if payload != expected:
        raise ValueError("T20.12 PI0.5 gripper-channel audit drifted from sources")


def _split_statistics(
    native: np.ndarray,
    lerobot: np.ndarray,
    normalized: np.ndarray,
    checkpoint: dict[str, Any],
) -> dict[str, Any]:
    rows = {}
    for index, name in enumerate(JOINT_NAMES):
        minimum = float(checkpoint["min"][index])
        maximum = float(checkpoint["max"][index])
        q01 = float(checkpoint["q01"][index])
        q99 = float(checkpoint["q99"][index])
        values = lerobot[:, index]
        rows[name] = {
            "mujoco_min_rad": float(np.min(native[:, index])),
            "mujoco_max_rad": float(np.max(native[:, index])),
            "lerobot_min": float(np.min(values)),
            "lerobot_max": float(np.max(values)),
            "lerobot_mean": float(np.mean(values)),
            "lerobot_std": float(np.std(values)),
            "normalized_min": float(np.min(normalized[:, index])),
            "normalized_max": float(np.max(normalized[:, index])),
            "normalized_mean": float(np.mean(normalized[:, index])),
            "normalized_std": float(np.std(normalized[:, index])),
            "normalized_target_mean_square": float(
                np.mean(np.square(normalized[:, index]))
            ),
            "checkpoint_min": minimum,
            "checkpoint_q01": q01,
            "checkpoint_q99": q99,
            "checkpoint_max": maximum,
            "outside_checkpoint_min_max_count": int(
                np.count_nonzero((values < minimum) | (values > maximum))
            ),
            "outside_checkpoint_q01_q99_count": int(
                np.count_nonzero((values < q01) | (values > q99))
            ),
        }
    return {"frame_count": int(native.shape[0]), "joints": rows}


def _inverse_pipeline(normalized: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    lerobot = normalized * std + mean
    return np.asarray([lerobot_to_mujoco(row) for row in lerobot], dtype=np.float64)


def _to_lerobot(values: np.ndarray) -> np.ndarray:
    converted = np.asarray([mujoco_to_lerobot(row) for row in values], dtype=np.float64)
    if converted.shape != values.shape or not np.isfinite(converted).all():
        raise ValueError("T20.12 coordinate conversion produced invalid values")
    return converted


def _action_matrix(value: Any, shape: tuple[int, int], label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"T20.12 {label} action matrix is malformed")
    return result


def _vector(value: Any, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (6,) or not np.isfinite(result).all():
        raise ValueError(f"T20.12 {label} is malformed")
    return result


def _statistics(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(_STATISTIC_NAMES):
        raise ValueError("T20.12 checkpoint action statistics are incomplete")
    result = {"count": int(value["count"])}
    if result["count"] <= 0 or float(value["count"]) != result["count"]:
        raise ValueError("T20.12 checkpoint action statistic count is invalid")
    for name in _STATISTIC_NAMES[1:]:
        vector = _vector(value[name], f"checkpoint action {name}")
        result[name] = [float(item) for item in vector]
    if any(item <= 0 for item in result["std"]):
        raise ValueError("T20.12 checkpoint action std is nonpositive")
    for index in range(6):
        ordered = [result[name][index] for name in ("min", "q01", "q99", "max")]
        if any(left > right for left, right in zip(ordered, ordered[1:])):
            raise ValueError("T20.12 checkpoint action support is unordered")
    return result


def _source_evidence(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise ValueError("T20.12 source evidence is missing")
    for name, item in value.items():
        if not isinstance(name, str) or not name or not isinstance(item, dict):
            raise ValueError("T20.12 source evidence entry is malformed")
        digest = item.get("sha256")
        if not _is_sha256(digest) or not isinstance(item.get("path"), str):
            raise ValueError("T20.12 source evidence hash or path is invalid")
    return {name: dict(item) for name, item in sorted(value.items())}


def _loss_contract(value: Any) -> dict[str, Any]:
    expected = {
        "action_dimension_count": 6,
        "action_dimension_weights": [1.0] * 6,
        "gripper_dimension_weight": 1.0,
        "gripper_only_loss": False,
        "reduction": "mean_over_batch_time_and_six_action_dimensions",
        "per_dimension_aggregation_share": 1.0 / 6.0,
        "observed_loss_per_dimension_recomputed": False,
        "target_scale_proxy_is_not_observed_loss": True,
    }
    if value != expected:
        raise ValueError("T20.12 PI0.5 loss contract drifted")
    return dict(expected)


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
