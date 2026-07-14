"""Pad-midpoint search with a passive post-yaw table-settle baseline."""

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
from scenesmith.robot_lab.grasp_pose_solver import APPROACH_MOTION_LIMIT_M


SCHEMA_VERSION = "scenesmith.post_yaw_settle_grasp_search.v1"
SOURCE = REPO_ROOT / "configurations/robot_lab/pad_midpoint_search.json"
POST_YAW_SETTLE_SECONDS = 0.25
PINNED_MODEL_TIMESTEP_SECONDS = 0.002
EXPECTED_SETTLE_STEP_COUNT = round(
    POST_YAW_SETTLE_SECONDS / PINNED_MODEL_TIMESTEP_SECONDS
)


def build_post_yaw_settle_search() -> dict[str, Any]:
    source = load_strict_json(SOURCE)
    verify_signed_payload(source, label="source pad-midpoint search")
    candidates = [
        _settled_candidate(index, holdout=False)
        for index in range(1, TRAINING_CANDIDATES + 1)
    ]
    eligible = [row for row in candidates if row["geometry_eligible"]]
    selected = min(eligible, key=_rank) if eligible else None
    holdout = _settled_candidate(TRAINING_CANDIDATES + 1, holdout=True)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "identical_search_post_yaw_passive_settle_baseline",
            "source_pad_midpoint_search_identity_sha256": source["identity_sha256"],
            "candidate_design_identical_to_source": True,
            "contact_physics_unchanged": True,
            "post_yaw_settle_seconds": POST_YAW_SETTLE_SECONDS,
            "approach_motion_limit_m": APPROACH_MOTION_LIMIT_M,
            "ranges": {key: list(value) for key, value in RANGES.items()},
            "training_candidate_count": len(candidates),
            "bilateral_contact_candidate_count": sum(
                row.get("close_pad_contact_frame_count", 0) > 0
                for row in candidates
            ),
            "approach_motion_valid_candidate_count": sum(
                row.get("approach_object_motion_valid", False)
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


def _settled_candidate(index: int, *, holdout: bool) -> dict[str, Any]:
    row = _candidate(
        index,
        holdout=holdout,
        explicit_pad_proxy_only=True,
        pad_midpoint_targeting=True,
        post_yaw_settle_seconds=POST_YAW_SETTLE_SECONDS,
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


def verify_post_yaw_settle_search(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="post-yaw-settle search")
    candidates = payload.get("candidates", [])
    if payload.get("training_candidate_count") != len(candidates):
        raise ValueError("Post-yaw-settle candidate count drifted")
    if (
        not payload.get("candidate_design_identical_to_source")
        or not payload.get("contact_physics_unchanged")
    ):
        raise ValueError("Post-yaw-settle isolation drifted")
    if payload.get("post_yaw_settle_seconds") != POST_YAW_SETTLE_SECONDS:
        raise ValueError("Post-yaw-settle duration drifted")
    if payload.get("geometry_eligible_count") != sum(
        row["geometry_eligible"] for row in candidates
    ):
        raise ValueError("Post-yaw-settle eligibility drifted")
    for candidate in candidates:
        if candidate.get("setup_valid") and candidate.get(
            "post_yaw_settle_step_count"
        ) != EXPECTED_SETTLE_STEP_COUNT:
            raise ValueError("Post-yaw settle step count drifted")
