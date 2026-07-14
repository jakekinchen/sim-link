"""Train-only dataset-bound PI0.5 normalizer preflight."""

from __future__ import annotations

import math

from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot


SCHEMA_VERSION = "scenesmith.t20_13_dataset_bound_pi05_normalizer.v1"
NORMALIZER_EPS = 1e-8
MINIMUM_STD = 1e-6
TRAIN_NORMALIZATION_TOLERANCE = 1e-6
INVERSE_TOLERANCE_RAD = 1e-8


def build_dataset_bound_pi05_normalizer(
    *,
    train_state_mujoco: np.ndarray,
    train_action_mujoco: np.ndarray,
    evaluation_state_mujoco: np.ndarray,
    evaluation_action_mujoco: np.ndarray,
    source_evidence: dict[str, Any],
    t20_12_audit: dict[str, Any],
) -> dict[str, Any]:
    inputs = {
        "state": (
            _matrix(train_state_mujoco, (488, 12), "train state")[:, :6],
            _matrix(evaluation_state_mujoco, (244, 12), "evaluation state")[:, :6],
        ),
        "action": (
            _matrix(train_action_mujoco, (488, 6), "train action"),
            _matrix(evaluation_action_mujoco, (244, 6), "evaluation action"),
        ),
    }
    evidence = _source_evidence(source_evidence)
    if (
        t20_12_audit.get("schema_version")
        != "scenesmith.t20_12_pi05_gripper_channel_audit.v1"
        or t20_12_audit.get("finding", {}).get(
            "selected_next_hypothesis"
        )
        != "derive_dataset_bound_pi05_normalizer_then_retest_without_loss_reweighting"
    ):
        raise ValueError("T20.13 source T20.12 hypothesis drifted")

    fitted = {}
    feature_audits = {}
    converted = {}
    for feature, (train_native, evaluation_native) in inputs.items():
        train_lerobot = _convert(train_native)
        evaluation_lerobot = _convert(evaluation_native)
        mean = np.mean(train_lerobot, axis=0)
        std = np.std(train_lerobot, axis=0, ddof=0)
        if not np.isfinite(mean).all() or not np.isfinite(std).all() or np.any(
            std <= MINIMUM_STD
        ):
            raise ValueError("T20.13 fitted statistics are non-finite or near-zero")
        train_normalized = (train_lerobot - mean) / (std + NORMALIZER_EPS)
        evaluation_normalized = (evaluation_lerobot - mean) / (std + NORMALIZER_EPS)
        train_inverse = _inverse(train_normalized, mean, std)
        evaluation_inverse = _inverse(evaluation_normalized, mean, std)
        fitted[feature] = {
            "count": 488,
            "mean": [float(value) for value in mean],
            "std": [float(value) for value in std],
        }
        feature_audits[feature] = _feature_audit(
            train_native=train_native,
            evaluation_native=evaluation_native,
            train_lerobot=train_lerobot,
            evaluation_lerobot=evaluation_lerobot,
            train_normalized=train_normalized,
            evaluation_normalized=evaluation_normalized,
            train_inverse=train_inverse,
            evaluation_inverse=evaluation_inverse,
            std=std,
        )
        converted[feature] = {
            "train_normalized": train_normalized,
            "evaluation_normalized": evaluation_normalized,
        }

    old_rows = t20_12_audit.get("dataset_action_audit", {}).get("train", {}).get(
        "joints", {}
    )
    if set(old_rows) != set(JOINT_NAMES):
        raise ValueError("T20.13 source T20.12 per-joint audit is incomplete")
    target_scale = {}
    for index, joint_name in enumerate(JOINT_NAMES):
        old = float(old_rows[joint_name]["normalized_target_mean_square"])
        new = float(
            np.mean(np.square(converted["action"]["train_normalized"][:, index]))
        )
        if not math.isfinite(old) or old < 0 or not math.isfinite(new) or new < 0:
            raise ValueError("T20.13 target-scale comparison is non-finite")
        target_scale[joint_name] = {
            "checkpoint_normalizer_target_mean_square": old,
            "dataset_normalizer_target_mean_square": new,
            "checkpoint_to_dataset_scale_ratio": old / new if new > 0 else None,
        }
    dominant_old = max(
        JOINT_NAMES,
        key=lambda name: target_scale[name]["checkpoint_normalizer_target_mean_square"],
    )
    frame_zero_gripper = {
        "checkpoint_normalized": float(
            t20_12_audit["t20_11_gripper_reconciliation"][
                "source_gripper_normalized"
            ]
        ),
        "dataset_normalized": float(
            converted["action"]["evaluation_normalized"][0, -1]
        ),
    }
    frame_zero_gripper["absolute_scale_reduction"] = abs(
        frame_zero_gripper["checkpoint_normalized"]
    ) - abs(frame_zero_gripper["dataset_normalized"])

    all_train_normalized = all(
        value["train_normalization_gate"]["pass"] for value in feature_audits.values()
    )
    all_inverse = all(
        value["inverse_gate"]["pass"] for value in feature_audits.values()
    )
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.13",
            "source_evidence": evidence,
            "fit_contract": {
                "fit_split": "train_only",
                "fit_frame_count": 488,
                "held_out_frame_count": 244,
                "held_out_values_contributed_to_fit": False,
                "standard_deviation_estimator": "population_ddof_0",
                "normalization_mode": "MEAN_STD",
                "normalizer_epsilon": NORMALIZER_EPS,
                "clipping": False,
                "coordinate_units": "lerobot_body_degrees_and_gripper_percent",
                "state_projection": (
                    "first_six_joint_positions_only_matching_t20_7_vla_batch;"
                    "six_velocity_columns_excluded"
                ),
            },
            "fitted_statistics": fitted,
            "feature_audits": feature_audits,
            "target_scale_comparison": {
                "metric": "normalized_target_mean_square_not_observed_model_loss",
                "joints": target_scale,
                "dominant_checkpoint_scaled_joint": dominant_old,
                "dominant_checkpoint_scaled_value": target_scale[dominant_old][
                    "checkpoint_normalizer_target_mean_square"
                ],
                "same_equal_six_way_loss_weights_required_for_next_test": True,
            },
            "frame_zero_gripper_comparison": frame_zero_gripper,
            "gate_summary": {
                "all_train_means_zero_and_stds_one_within_tolerance": all_train_normalized,
                "all_state_and_action_inverse_transforms_within_tolerance": all_inverse,
                "minimum_fitted_std": min(
                    min(value["std"]) for value in fitted.values()
                ),
                "minimum_allowed_fitted_std": MINIMUM_STD,
                "minimum_std_margin": min(
                    min(value["std"]) for value in fitted.values()
                )
                - MINIMUM_STD,
            },
            "finding": {
                "dataset_bound_normalizer_preflight_passed": all_train_normalized
                and all_inverse,
                "causal_training_improvement_claimed": False,
                "selected_next_hypothesis": (
                    "bounded_pi05_retrain_with_dataset_normalizer_and_equal_loss_weights"
                    if all_train_normalized and all_inverse
                    else "no_optimizer_hypothesis_selected"
                ),
            },
            "model_loaded": False,
            "model_inference_executed": False,
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


def verify_dataset_bound_pi05_normalizer(
    payload: dict[str, Any],
    *,
    train_state_mujoco: np.ndarray,
    train_action_mujoco: np.ndarray,
    evaluation_state_mujoco: np.ndarray,
    evaluation_action_mujoco: np.ndarray,
    source_evidence: dict[str, Any],
    t20_12_audit: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.13 dataset-bound PI0.5 normalizer")
    expected = build_dataset_bound_pi05_normalizer(
        train_state_mujoco=train_state_mujoco,
        train_action_mujoco=train_action_mujoco,
        evaluation_state_mujoco=evaluation_state_mujoco,
        evaluation_action_mujoco=evaluation_action_mujoco,
        source_evidence=source_evidence,
        t20_12_audit=t20_12_audit,
    )
    if payload != expected:
        raise ValueError("T20.13 dataset-bound normalizer drifted from sources")


def _feature_audit(
    *,
    train_native: np.ndarray,
    evaluation_native: np.ndarray,
    train_lerobot: np.ndarray,
    evaluation_lerobot: np.ndarray,
    train_normalized: np.ndarray,
    evaluation_normalized: np.ndarray,
    train_inverse: np.ndarray,
    evaluation_inverse: np.ndarray,
    std: np.ndarray,
) -> dict[str, Any]:
    train_mean_error = float(np.max(np.abs(np.mean(train_normalized, axis=0))))
    train_std_error = float(np.max(np.abs(np.std(train_normalized, axis=0) - 1.0)))
    inverse_error = float(
        max(
            np.max(np.abs(train_inverse - train_native)),
            np.max(np.abs(evaluation_inverse - evaluation_native)),
        )
    )
    joints = {}
    for index, joint_name in enumerate(JOINT_NAMES):
        joints[joint_name] = {
            "train_lerobot_min": float(np.min(train_lerobot[:, index])),
            "train_lerobot_max": float(np.max(train_lerobot[:, index])),
            "train_normalized_mean": float(np.mean(train_normalized[:, index])),
            "train_normalized_std": float(np.std(train_normalized[:, index])),
            "train_normalized_min": float(np.min(train_normalized[:, index])),
            "train_normalized_max": float(np.max(train_normalized[:, index])),
            "evaluation_lerobot_min": float(np.min(evaluation_lerobot[:, index])),
            "evaluation_lerobot_max": float(np.max(evaluation_lerobot[:, index])),
            "evaluation_normalized_mean": float(
                np.mean(evaluation_normalized[:, index])
            ),
            "evaluation_normalized_std": float(
                np.std(evaluation_normalized[:, index])
            ),
            "evaluation_normalized_min": float(
                np.min(evaluation_normalized[:, index])
            ),
            "evaluation_normalized_max": float(
                np.max(evaluation_normalized[:, index])
            ),
            "fitted_std": float(std[index]),
        }
    return {
        "train_frame_count": 488,
        "evaluation_frame_count": 244,
        "joints": joints,
        "train_normalization_gate": {
            "pass": train_mean_error <= TRAIN_NORMALIZATION_TOLERANCE
            and train_std_error <= TRAIN_NORMALIZATION_TOLERANCE,
            "measured_max_abs_mean": train_mean_error,
            "measured_max_abs_std_error_from_one": train_std_error,
            "threshold": TRAIN_NORMALIZATION_TOLERANCE,
            "mean_margin": TRAIN_NORMALIZATION_TOLERANCE - train_mean_error,
            "std_margin": TRAIN_NORMALIZATION_TOLERANCE - train_std_error,
        },
        "inverse_gate": {
            "pass": inverse_error <= INVERSE_TOLERANCE_RAD,
            "measured_maximum_error_rad": inverse_error,
            "threshold_maximum_error_rad": INVERSE_TOLERANCE_RAD,
            "margin_rad": INVERSE_TOLERANCE_RAD - inverse_error,
        },
    }


def _convert(native: np.ndarray) -> np.ndarray:
    result = np.asarray([mujoco_to_lerobot(row) for row in native], dtype=np.float64)
    if result.shape != native.shape or not np.isfinite(result).all():
        raise ValueError("T20.13 coordinate conversion produced invalid values")
    return result


def _inverse(normalized: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    lerobot = normalized * std + mean
    result = np.asarray([lerobot_to_mujoco(row) for row in lerobot], dtype=np.float64)
    if result.shape != normalized.shape or not np.isfinite(result).all():
        raise ValueError("T20.13 inverse conversion produced invalid values")
    return result


def _matrix(value: Any, shape: tuple[int, int], label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"T20.13 {label} matrix is malformed")
    return result


def _source_evidence(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise ValueError("T20.13 source evidence is missing")
    for name, item in value.items():
        digest = item.get("sha256") if isinstance(item, dict) else None
        if (
            not isinstance(name, str)
            or not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError("T20.13 source evidence is malformed")
    return {name: dict(item) for name, item in sorted(value.items())}
