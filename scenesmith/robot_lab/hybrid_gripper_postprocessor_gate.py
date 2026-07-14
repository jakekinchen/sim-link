"""Compose the T20.16 hybrid gripper postprocessor rollout gate."""

from __future__ import annotations

from typing import Any

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes


SCHEMA_VERSION = "scenesmith.t20_16_hybrid_gripper_postprocessor_gate.v1"


def build_hybrid_gripper_postprocessor_gate(
    rollout_path: str,
    result: dict[str, Any],
    result_file_sha256: str,
) -> dict[str, Any]:
    _verify_result(result)
    rollout = result["closed_loop"]
    diagnostics = result["action_error_diagnostics"]
    preflight = result["frame_zero_preflight"]
    conversion = result["coordinate_conversion"]
    keyframes = rollout["rendered_keyframes"]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.16",
            "source": {
                "path": rollout_path,
                "identity_sha256": result["identity_sha256"],
                "file_sha256": result_file_sha256,
            },
            "frame_zero_effect": {
                "non_gripper_mae_rad": preflight[
                    "measured_non_gripper_mae_rad"
                ],
                "gripper_absolute_error_rad": preflight[
                    "measured_gripper_error_rad"
                ],
                "prediction_passed": preflight["passed"],
            },
            "trajectory_effect": {
                "mean_absolute_error_rad": diagnostics[
                    "trajectory_mean_absolute_error_rad"
                ],
                "maximum_absolute_error_rad": diagnostics[
                    "trajectory_maximum_absolute_error_rad"
                ],
                "dominant_initial_error_joint": diagnostics[
                    "dominant_initial_error_joint"
                ],
            },
            "strict_closed_loop": {
                "frame_count": rollout["frame_count"],
                "strict_v2_valid_frame_counts": rollout[
                    "strict_v2_valid_frame_counts"
                ],
                "maximum_anchor_lift_m": rollout["maximum_anchor_lift_m"],
                "terminal_outcome": rollout["terminal_outcome"],
                "failed_gate_margins": rollout["failed_gate_margins"],
                "projected_action_frame_count": rollout[
                    "projected_action_frame_count"
                ],
                "active_assist_frame_count": rollout["active_assist_frame_count"],
                "simulation_semantic_strict_success": rollout[
                    "simulation_semantic_strict_success"
                ],
            },
            "coordinate_conversion": conversion,
            "rendered_grasp_evidence": {
                "keyframe_count": len(keyframes),
                "image_count": sum(len(row["images"]) for row in keyframes),
                "phases": [row["phase"] for row in keyframes],
                "visual_finding": (
                    "arm_and_gripper_remain_far_below_left_of_cube_and_wrist_"
                    "view_loses_object_through_close_hold_lift_and_retreat"
                ),
                "visible_contact_or_lift": False,
            },
            "finding": derive_hybrid_finding(conversion, rollout),
            "model_inference_executed": True,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def derive_hybrid_finding(
    conversion: dict[str, Any], rollout: dict[str, Any]
) -> dict[str, Any]:
    clipped = conversion.get("clipped_or_projected_call_count", 0) > 0
    strict_success = rollout.get("simulation_semantic_strict_success") is True
    if strict_success:
        next_hypothesis = "repeat_strict_success_across_required_acceptance_seeds"
        retired = False
    elif clipped:
        next_hypothesis = "resolve_coordinate_conversion_clipping_before_model_change"
        retired = False
    else:
        next_hypothesis = (
            "clean_pi05_base_with_dataset_statistics_from_initialization_"
            "and_realistic_data_update_budget"
        )
        retired = True
    return {
        "frame_zero_channel_hybrid_verified": True,
        "closed_loop_capability_gain_demonstrated": strict_success,
        "coordinate_clipping_caused_failure": clipped,
        "hybrid_gripper_postprocessor_retired": retired,
        "selected_next_hypothesis": next_hypothesis,
        "reason": (
            "the hybrid fixes frame-zero scaling without clipping but rapidly "
            "diverges over the trajectory; checkpoint lineage and underpowered "
            "adaptation remain confounded"
            if retired
            else "the measured strict or conversion outcome requires its own gate"
        ),
    }


def verify_hybrid_gripper_postprocessor_gate(
    payload: dict[str, Any],
    rollout_path: str,
    result: dict[str, Any],
    result_file_sha256: str,
) -> None:
    verify_signed_payload(payload, label="T20.16 hybrid gripper gate")
    expected = build_hybrid_gripper_postprocessor_gate(
        rollout_path, result, result_file_sha256
    )
    if payload != expected:
        raise ValueError("T20.16 hybrid gripper gate drifted from rollout evidence")


def _verify_result(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.16 hybrid gripper result")
    rollout = payload.get("closed_loop", {})
    verify_signed_payload(rollout, label="T20.16 nested rollout")
    validate_rendered_keyframes(rollout.get("rendered_keyframes"))
    conversion = payload.get("coordinate_conversion", {})
    if (
        payload.get("schema_version")
        != "scenesmith.t20_16_hybrid_gripper_postprocessor_rollout.v1"
        or payload.get("task_id") != "T20.16"
        or payload.get("frame_zero_preflight", {}).get("passed") is not True
        or rollout.get("frame_count") != 244
        or rollout.get("simulation_semantic_strict_success") is not False
        or rollout.get("projected_action_frame_count") != 0
        or rollout.get("active_assist_frame_count") != 0
        or conversion.get("clipped_or_projected_call_count") != 0
        or conversion.get("maximum_lerobot_roundtrip_error", 1.0) > 1e-8
        or payload.get("optimizer_training") is not False
        or payload.get("simulation_policy_accepted") is not False
        or payload.get("physical_actuation") is not False
        or payload.get("external_compute_started") is not False
        or payload.get("brev_compute_started") is not False
    ):
        raise ValueError("T20.16 hybrid gripper result contract drifted")
