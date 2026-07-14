"""Geometry-derived unilateral-jaw unassisted MuJoCo grasp proof."""

from __future__ import annotations

import math
from typing import Any

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload, verify_signed_payload
from scenesmith.robot_lab.geometry_first_grasp_search import REPO_ROOT, _candidate
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes
from scenesmith.robot_lab.gripper_contact_semantics import PAD_HALF_SIZE_M
from scenesmith.robot_lab.mujoco_anchor_grasp import ANCHOR_DIMENSIONS_M
from scenesmith.robot_lab.post_yaw_settle_search import APPROACH_MOTION_LIMIT_M, POST_YAW_SETTLE_SECONDS

SCHEMA_VERSION = "scenesmith.geometry_derived_unilateral_grasp.v1"
GEOMETRY_AUDIT = REPO_ROOT / "configurations/robot_lab/gripper_geometry_audit.json"
CONTACT_AUDIT = REPO_ROOT / "configurations/robot_lab/centered_contact_face_audit.json"
SOURCE_CANDIDATE_INDEX = 3
SELECTED_OBJECT_WIDTH_M = ANCHOR_DIMENSIONS_M[1]
PAD_NORMAL_HALF_THICKNESS_M = PAD_HALF_SIZE_M[0]
TARGET_APERTURE_M = SELECTED_OBJECT_WIDTH_M + 2.0 * PAD_NORMAL_HALF_THICKNESS_M
FIXED_JAW_CLEARANCE_M = -2.0 * PAD_NORMAL_HALF_THICKNESS_M


def build_geometry_derived_unilateral_grasp() -> dict[str, Any]:
    geometry = load_strict_json(GEOMETRY_AUDIT)
    contact_audit = load_strict_json(CONTACT_AUDIT)
    verify_signed_payload(geometry, label="source gripper geometry audit")
    verify_signed_payload(contact_audit, label="source centered contact-face audit")
    close_target = _invert_aperture_curve(geometry["aperture_reference"]["samples"], TARGET_APERTURE_M)
    first = _run(close_target)
    second = _run(close_target)
    if first != second:
        raise ValueError("Geometry-derived grasp replay is not deterministic")
    cycle = first["full_lift_cycle"]
    counts = cycle["phase_frame_counts"]
    strict = cycle["strict_v2_valid_frame_counts"]
    lift_z = cycle["object_z_m"]["unassisted_lift"]
    hold_z = cycle["object_z_m"]["unsupported_lift_hold"]
    selected_axis = first["object_x_axis_world"]
    closing_axis = first["predicted_closing_axis_world"]
    fixed_to_moving_axis_dot_selected_axis = sum(
        selected * closing
        for selected, closing in zip(selected_axis, closing_axis, strict=True)
    )
    clearance_opposes_fixed_to_moving_axis = (
        FIXED_JAW_CLEARANCE_M * fixed_to_moving_axis_dot_selected_axis < 0.0
    )
    success = bool(
        first["setup_valid"]
        and first["preclose_object_displacement_m"] <= APPROACH_MOTION_LIMIT_M
        and first["nonpad_robot_object_contact_frame_count"] == 0
        and clearance_opposes_fixed_to_moving_axis
        and strict["grasp_hold"] == counts["grasp_hold"] == 8
        and strict["unassisted_lift"] == counts["unassisted_lift"] == 24
        and strict["unsupported_lift_hold"] == counts["unsupported_lift_hold"] == 12
        and strict["lower"] == counts["lower"] == 24
        and cycle["unsupported_lift_hold_frame_count"] == 12
        and cycle["active_assist_frame_count"] == 0
        and max(lift_z + hold_z) - min(cycle["object_z_m"]["grasp_hold"]) >= 0.035
        and cycle["retreat_final_contact_clear"]
    )
    return sign_payload({
        "schema_version": SCHEMA_VERSION,
        "evidence_mode": "two_pass_geometry_derived_unassisted_mujoco_grasp_cycle",
        "source_gripper_geometry_audit_identity_sha256": geometry["identity_sha256"],
        "source_contact_face_audit_identity_sha256": contact_audit["identity_sha256"],
        "source_candidate_index": SOURCE_CANDIDATE_INDEX,
        "geometry_derived_controls": True,
        "derivation": {
            "selected_object_axis": "y",
            "selected_object_width_m": SELECTED_OBJECT_WIDTH_M,
            "pad_normal_half_thickness_m": PAD_NORMAL_HALF_THICKNESS_M,
            "target_aperture_m": TARGET_APERTURE_M,
            "derived_close_target_rad": close_target,
            "pad_midpoint_vertical_offset_m": 0.0,
            "fixed_jaw_clearance_m": FIXED_JAW_CLEARANCE_M,
            "fixed_to_moving_axis_dot_selected_axis": fixed_to_moving_axis_dot_selected_axis,
            "clearance_opposes_fixed_to_moving_axis": clearance_opposes_fixed_to_moving_axis,
            "aperture_interpolation": "piecewise_linear_checked_curve",
        },
        "two_pass_exact_determinism": True,
        "trajectory": first,
        "unassisted_mujoco_grasp_success": success,
        "actual_mujoco_grasp_success": success,
        "simulation_training_ready": False,
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "authority_not_granted": ["simulation_training_ready", "physical_twin_qualified", "physical_actuation"],
    })


def _run(close_target: float) -> dict[str, Any]:
    row = _candidate(
        SOURCE_CANDIDATE_INDEX,
        holdout=False,
        explicit_pad_proxy_only=True,
        pad_midpoint_targeting=True,
        post_yaw_settle_seconds=POST_YAW_SETTLE_SECONDS,
        center_selected_axis_offset=True,
        close_target_override_rad=close_target,
        vertical_target_override_m=0.0,
        selected_axis_clearance_m=FIXED_JAW_CLEARANCE_M,
        execute_full_lift_cycle=True,
    )
    if not row.get("setup_valid"):
        raise ValueError(f"Geometry-derived grasp setup failed: {row}")
    return row


def _invert_aperture_curve(samples: list[dict[str, Any]], target_m: float) -> float:
    if len(samples) < 2 or not math.isfinite(target_m):
        raise ValueError("Aperture inversion requires two samples and a finite target")
    ordered = sorted(samples, key=lambda row: row["separation_m"])
    if any(
        not math.isfinite(row["separation_m"])
        or not math.isfinite(row["gripper_qpos_rad"])
        for row in ordered
    ):
        raise ValueError("Aperture curve contains a non-finite value")
    if any(
        lower["separation_m"] >= upper["separation_m"]
        for lower, upper in zip(ordered, ordered[1:], strict=False)
    ):
        raise ValueError("Aperture curve must have unique increasing separations")
    if target_m < ordered[0]["separation_m"] or target_m > ordered[-1]["separation_m"]:
        raise ValueError("Target aperture lies outside checked curve")
    for lower, upper in zip(ordered, ordered[1:], strict=False):
        if lower["separation_m"] <= target_m <= upper["separation_m"]:
            fraction = (target_m - lower["separation_m"]) / (upper["separation_m"] - lower["separation_m"])
            return lower["gripper_qpos_rad"] + fraction * (upper["gripper_qpos_rad"] - lower["gripper_qpos_rad"])
    raise ValueError("Target aperture interpolation interval is missing")


def verify_geometry_derived_unilateral_grasp(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="geometry-derived unilateral grasp")
    if not payload.get("two_pass_exact_determinism") or not payload.get("geometry_derived_controls"):
        raise ValueError("Geometry-derived grasp proof is incomplete")
    validate_rendered_keyframes(payload.get("trajectory", {}).get("rendered_keyframes"))
    if payload != build_geometry_derived_unilateral_grasp():
        raise ValueError("Geometry-derived grasp proof drifted")
