"""Post-settle search with jointly aligned wrist flex and roll."""

from __future__ import annotations

from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.geometry_first_grasp_search import (
    REPO_ROOT,
    RANGES,
    TRAINING_CANDIDATES,
    _candidate,
    _rank,
)
from scenesmith.robot_lab.post_yaw_settle_search import (
    APPROACH_MOTION_LIMIT_M,
    POST_YAW_SETTLE_SECONDS,
)


SCHEMA_VERSION = "scenesmith.horizontal_axis_grasp_search.v1"
SOURCE = REPO_ROOT / "configurations/robot_lab/principal_axis_grasp_search.json"
ALIGNMENT_MINIMUM = 0.95
VERTICAL_MAXIMUM = 0.1


def build_horizontal_axis_grasp_search() -> dict[str, Any]:
    source = load_strict_json(SOURCE)
    verify_signed_payload(source, label="source principal-axis search")
    candidates = [
        _aligned_candidate(index, holdout=False)
        for index in range(1, TRAINING_CANDIDATES + 1)
    ]
    eligible = [row for row in candidates if row["geometry_eligible"]]
    selected = min(eligible, key=_rank) if eligible else None
    holdout = _aligned_candidate(TRAINING_CANDIDATES + 1, holdout=True)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "deterministic_joint_wrist_horizontal_object_x_axis_alignment",
            "source_principal_axis_search_identity_sha256": source["identity_sha256"],
            "candidate_inputs_except_wrist_pose_unchanged": True,
            "contact_physics_unchanged": True,
            "principal_axis_alignment_minimum": ALIGNMENT_MINIMUM,
            "closing_axis_vertical_maximum": VERTICAL_MAXIMUM,
            "post_yaw_settle_seconds": POST_YAW_SETTLE_SECONDS,
            "approach_motion_limit_m": APPROACH_MOTION_LIMIT_M,
            "ranges": {key: list(value) for key, value in RANGES.items()},
            "training_candidate_count": len(candidates),
            "aligned_candidate_count": sum(
                row.get("predicted_principal_axis_alignment", 0.0)
                >= ALIGNMENT_MINIMUM
                and row.get("predicted_closing_axis_vertical_abs", 1.0)
                <= VERTICAL_MAXIMUM
                for row in candidates
            ),
            "bilateral_contact_candidate_count": sum(
                row.get("close_pad_contact_frame_count", 0) > 0
                for row in candidates
            ),
            "geometry_eligible_count": len(eligible),
            "candidates": candidates,
            "selected_candidate": selected,
            "holdout": {"excluded_from_selection": True, "candidate": holdout},
            "actual_mujoco_grasp_success": False,
            "simulation_training_ready": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "authority_not_granted": [
                "unassisted_mujoco_grasp_success",
                "simulation_training_ready",
                "physical_actuation",
            ],
        }
    )


def _aligned_candidate(index: int, *, holdout: bool) -> dict[str, Any]:
    row = _candidate(
        index,
        holdout=holdout,
        explicit_pad_proxy_only=True,
        pad_midpoint_targeting=True,
        post_yaw_settle_seconds=POST_YAW_SETTLE_SECONDS,
        joint_wrist_axis_alignment=True,
    )
    if not row.get("setup_valid"):
        return row
    row["base_contact_geometry_eligible"] = row["geometry_eligible"]
    row["approach_object_motion_valid"] = (
        row["preclose_object_displacement_m"] <= APPROACH_MOTION_LIMIT_M
    )
    row["nonpad_contact_valid"] = (
        row["nonpad_robot_object_contact_frame_count"] == 0
    )
    row["geometry_eligible"] = bool(
        row["base_contact_geometry_eligible"]
        and row["approach_object_motion_valid"]
        and row["nonpad_contact_valid"]
    )
    return row


def verify_horizontal_axis_grasp_search(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="horizontal-axis grasp search")
    candidates = payload.get("candidates", [])
    if payload.get("training_candidate_count") != len(candidates):
        raise ValueError("Horizontal-axis candidate count drifted")
    if (
        not payload.get("candidate_inputs_except_wrist_pose_unchanged")
        or not payload.get("contact_physics_unchanged")
    ):
        raise ValueError("Horizontal-axis isolation drifted")
    if payload.get("aligned_candidate_count") != sum(
        row.get("predicted_principal_axis_alignment", 0.0) >= ALIGNMENT_MINIMUM
        and row.get("predicted_closing_axis_vertical_abs", 1.0)
        <= VERTICAL_MAXIMUM
        for row in candidates
    ):
        raise ValueError("Horizontal-axis alignment count drifted")
    if payload.get("geometry_eligible_count") != sum(
        row["geometry_eligible"] for row in candidates
    ):
        raise ValueError("Horizontal-axis eligibility drifted")
