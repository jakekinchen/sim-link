"""Identical geometry search with composite jaw contacts disabled."""

from __future__ import annotations

from typing import Any

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload, verify_signed_payload
from scenesmith.robot_lab.geometry_first_grasp_search import (
    REPO_ROOT,
    RANGES,
    TRAINING_CANDIDATES,
    _candidate,
    _rank,
)


SCHEMA_VERSION = "scenesmith.explicit_pad_proxy_search.v1"
SOURCE_SEARCH = REPO_ROOT / "configurations/robot_lab/geometry_first_grasp_search.json"


def build_explicit_pad_proxy_search() -> dict[str, Any]:
    source = load_strict_json(SOURCE_SEARCH)
    verify_signed_payload(source, label="source geometry-first search")
    candidates = [
        _proxy_candidate(index, holdout=False)
        for index in range(1, TRAINING_CANDIDATES + 1)
    ]
    eligible = [row for row in candidates if row["geometry_eligible"]]
    selected = min(eligible, key=_rank) if eligible else None
    holdout = _proxy_candidate(TRAINING_CANDIDATES + 1, holdout=True)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "identical_geometry_search_explicit_pad_proxy_only",
            "source_search_identity_sha256": source["identity_sha256"],
            "semantic_model_version": "scenesmith.so101_explicit_pad_proxy_contact.v2",
            "composite_jaw_geometry_retained": True,
            "composite_jaw_contact_masks_disabled": True,
            "ranges": {name: list(bounds) for name, bounds in RANGES.items()},
            "candidate_design_identical_to_source": True,
            "friction_compliance_mass_and_time_constants_unchanged": True,
            "training_candidate_count": len(candidates),
            "geometry_eligible_count": len(eligible),
            "explicit_pad_contact_candidate_count": sum(
                row.get("raw_pad_contact_count", 0) > 0 for row in candidates
            ),
            "bilateral_representative_contact_candidate_count": sum(
                row.get("close_pad_contact_frame_count", 0) > 0
                for row in candidates
            ),
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


def verify_explicit_pad_proxy_search(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="explicit pad proxy search")
    candidates = payload.get("candidates", [])
    if payload.get("training_candidate_count") != len(candidates):
        raise ValueError("Explicit-pad candidate count drifted")
    if not payload.get("candidate_design_identical_to_source"):
        raise ValueError("Explicit-pad search design drifted")
    if not payload.get("friction_compliance_mass_and_time_constants_unchanged"):
        raise ValueError("Explicit-pad correction changed contact properties")
    if payload.get("geometry_eligible_count") != sum(
        row["geometry_eligible"] for row in candidates
    ):
        raise ValueError("Explicit-pad eligibility count drifted")


def _proxy_candidate(index: int, *, holdout: bool) -> dict[str, Any]:
    row = _candidate(
        index,
        holdout=holdout,
        explicit_pad_proxy_only=True,
    )
    if not row.get("setup_valid"):
        return row
    row["base_contact_geometry_eligible"] = row["geometry_eligible"]
    row["approach_object_motion_valid"] = (
        row["preclose_object_displacement_m"] <= 0.0001
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
