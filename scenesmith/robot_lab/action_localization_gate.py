"""Compose the four-model T20.11 action-error localization gate."""

from __future__ import annotations

from typing import Any

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.learned_action_localization import (
    verify_model_action_localization,
)
from scenesmith.robot_lab.model_bakeoff import MODEL_ORDER


SCHEMA_VERSION = "scenesmith.t20_11_action_localization_gate.v1"


def build_action_localization_gate(
    results: list[tuple[str, dict[str, Any], str]],
) -> dict[str, Any]:
    if [payload.get("model_id") for _path, payload, _sha in results] != list(MODEL_ORDER):
        raise ValueError("T20.11 model localization results are missing or reordered")
    summaries = []
    for path, payload, file_sha256 in results:
        verify_model_action_localization(payload)
        if not _is_sha256(file_sha256):
            raise ValueError("T20.11 model localization file hash is invalid")
        diagnostics = payload["action_error_diagnostics"]
        initial = diagnostics["initial_action_absolute_error_rad"]
        non_gripper = [initial[name] for name in JOINT_NAMES if name != "gripper"]
        rollout = payload["corrected_closed_loop"]
        summaries.append(
            {
                "model_id": payload["model_id"],
                "path": path,
                "identity_sha256": payload["identity_sha256"],
                "file_sha256": file_sha256,
                "first_action_divergence": diagnostics["first_action_divergence"],
                "initial_action_mean_absolute_error_rad": diagnostics[
                    "initial_action_mean_absolute_error_rad"
                ],
                "initial_action_maximum_absolute_error_rad": diagnostics[
                    "initial_action_maximum_absolute_error_rad"
                ],
                "initial_gripper_absolute_error_rad": diagnostics[
                    "initial_gripper_absolute_error_rad"
                ],
                "initial_non_gripper_mean_absolute_error_rad": sum(non_gripper)
                / len(non_gripper),
                "dominant_initial_error_joint": diagnostics[
                    "dominant_initial_error_joint"
                ],
                "trajectory_mean_absolute_error_rad": diagnostics[
                    "trajectory_mean_absolute_error_rad"
                ],
                "trajectory_maximum_absolute_error_rad": diagnostics[
                    "trajectory_maximum_absolute_error_rad"
                ],
                "projected_action_frame_count": rollout[
                    "projected_action_frame_count"
                ],
                "terminal_outcome": rollout["terminal_outcome"],
                "maximum_anchor_lift_m": rollout["maximum_anchor_lift_m"],
                "simulation_semantic_strict_success": rollout[
                    "simulation_semantic_strict_success"
                ],
                "rendered_keyframe_count": len(rollout["rendered_keyframes"]),
            }
        )
    hypothesis = derive_next_hypothesis(summaries)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.11",
            "model_results": summaries,
            "all_four_models_present": True,
            "all_initial_observations_identical_within_tolerance": True,
            "all_models_first_diverge_at_frame_zero": all(
                row["first_action_divergence"]["frame_index"] == 0
                for row in summaries
            ),
            "cross_model_training_loss_used_for_ranking": False,
            "next_hypothesis": hypothesis,
            "winner_model_id": None,
            "simulation_policy_accepted": False,
            "optimizer_training": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_action_localization_gate(
    payload: dict[str, Any], results: list[tuple[str, dict[str, Any], str]]
) -> None:
    verify_signed_payload(payload, label="T20.11 action-localization gate")
    if payload != build_action_localization_gate(results):
        raise ValueError("T20.11 action-localization gate drifted from model evidence")


def derive_next_hypothesis(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    by_model = {row["model_id"]: row for row in summaries}
    if set(by_model) != set(MODEL_ORDER):
        raise ValueError("T20.11 hypothesis requires all four model summaries")
    pi05 = by_model["pi05"]
    arm_threshold = 0.05
    gripper_threshold = 0.5
    arm_close = pi05["initial_non_gripper_mean_absolute_error_rad"] <= arm_threshold
    gripper_large = pi05["initial_gripper_absolute_error_rad"] >= gripper_threshold
    all_frame_zero = all(
        row["first_action_divergence"]["frame_index"] == 0
        for row in summaries
    )
    selected = arm_close and gripper_large and all_frame_zero
    return {
        "hypothesis_id": (
            "pi05_gripper_channel_semantics_or_weighting"
            if selected
            else "no_single_channel_hypothesis_selected"
        ),
        "diagnostic_model_id": "pi05" if selected else None,
        "diagnostic_model_is_not_a_winner": True,
        "measured_pi05_non_gripper_initial_mae_rad": pi05[
            "initial_non_gripper_mean_absolute_error_rad"
        ],
        "maximum_pi05_non_gripper_initial_mae_rad": arm_threshold,
        "pi05_non_gripper_margin_rad": arm_threshold
        - pi05["initial_non_gripper_mean_absolute_error_rad"],
        "measured_pi05_gripper_initial_error_rad": pi05[
            "initial_gripper_absolute_error_rad"
        ],
        "minimum_large_gripper_error_rad": gripper_threshold,
        "pi05_gripper_error_margin_rad": pi05[
            "initial_gripper_absolute_error_rad"
        ]
        - gripper_threshold,
        "all_models_first_diverge_at_frame_zero": all_frame_zero,
        "hypothesis_selected": selected,
        "next_action": (
            "audit_pi05_gripper_source_processor_normalization_and_loss_weight_before_training"
            if selected
            else "broaden_initial_action_representation_audit_before_training"
        ),
    }


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
