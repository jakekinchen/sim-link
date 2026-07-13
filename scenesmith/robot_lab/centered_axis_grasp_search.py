"""Best-axis grasp search centered only along the selected closing axis."""

from __future__ import annotations

from typing import Any

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload, verify_signed_payload
from scenesmith.robot_lab.geometry_first_grasp_search import REPO_ROOT, RANGES, TRAINING_CANDIDATES, _candidate, _rank
from scenesmith.robot_lab.post_yaw_settle_search import APPROACH_MOTION_LIMIT_M, POST_YAW_SETTLE_SECONDS

SCHEMA_VERSION = "scenesmith.centered_axis_grasp_search.v1"
SOURCE = REPO_ROOT / "configurations/robot_lab/best_axis_grasp_search.json"


def build_centered_axis_grasp_search() -> dict[str, Any]:
    source = load_strict_json(SOURCE)
    verify_signed_payload(source, label="source best-axis search")
    candidates = [_centered_candidate(index, holdout=False) for index in range(1, TRAINING_CANDIDATES + 1)]
    eligible = [row for row in candidates if row["geometry_eligible"]]
    selected = min(eligible, key=_rank) if eligible else None
    holdout = _centered_candidate(TRAINING_CANDIDATES + 1, holdout=True)
    return sign_payload({
        "schema_version": SCHEMA_VERSION,
        "evidence_mode": "deterministic_selected_axis_centered_target_search",
        "source_best_axis_search_identity_sha256": source["identity_sha256"],
        "only_selected_axis_offset_removed": True,
        "contact_physics_unchanged": True,
        "post_yaw_settle_seconds": POST_YAW_SETTLE_SECONDS,
        "approach_motion_limit_m": APPROACH_MOTION_LIMIT_M,
        "ranges": {key: list(value) for key, value in RANGES.items()},
        "training_candidate_count": len(candidates),
        "centered_candidate_count": sum(row.get("setup_valid", False) for row in candidates),
        "bilateral_contact_candidate_count": sum(row.get("close_pad_contact_frame_count", 0) > 0 for row in candidates),
        "geometry_eligible_count": len(eligible),
        "candidates": candidates,
        "selected_candidate": selected,
        "holdout": {"excluded_from_selection": True, "candidate": holdout},
        "actual_mujoco_grasp_success": False,
        "simulation_training_ready": False,
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "authority_not_granted": ["unassisted_mujoco_grasp_success", "simulation_training_ready", "physical_actuation"],
    })


def _centered_candidate(index: int, *, holdout: bool) -> dict[str, Any]:
    row = _candidate(index, holdout=holdout, explicit_pad_proxy_only=True, pad_midpoint_targeting=True, post_yaw_settle_seconds=POST_YAW_SETTLE_SECONDS, center_selected_axis_offset=True)
    if not row.get("setup_valid"):
        return row
    row["base_contact_geometry_eligible"] = row["geometry_eligible"]
    row["approach_object_motion_valid"] = row["preclose_object_displacement_m"] <= APPROACH_MOTION_LIMIT_M
    row["nonpad_contact_valid"] = row["nonpad_robot_object_contact_frame_count"] == 0
    row["geometry_eligible"] = bool(row["base_contact_geometry_eligible"] and row["approach_object_motion_valid"] and row["nonpad_contact_valid"])
    return row


def verify_centered_axis_grasp_search(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="centered-axis grasp search")
    candidates = payload.get("candidates", [])
    if payload.get("training_candidate_count") != len(candidates):
        raise ValueError("Centered-axis candidate count drifted")
    if not payload.get("only_selected_axis_offset_removed") or not payload.get("contact_physics_unchanged"):
        raise ValueError("Centered-axis isolation drifted")
    if payload.get("centered_candidate_count") != sum(row.get("setup_valid", False) for row in candidates):
        raise ValueError("Centered-axis setup count drifted")
    if payload.get("geometry_eligible_count") != sum(row["geometry_eligible"] for row in candidates):
        raise ValueError("Centered-axis eligibility drifted")
