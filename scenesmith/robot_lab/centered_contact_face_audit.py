"""Audit object-frame faces and normals for centered bilateral contacts."""

from __future__ import annotations

from typing import Any

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload, verify_signed_payload
from scenesmith.robot_lab.geometry_first_grasp_search import REPO_ROOT, _candidate
from scenesmith.robot_lab.mujoco_anchor_grasp import ANCHOR_DIMENSIONS_M
from scenesmith.robot_lab.post_yaw_settle_search import APPROACH_MOTION_LIMIT_M, POST_YAW_SETTLE_SECONDS

SCHEMA_VERSION = "scenesmith.centered_contact_face_audit.v1"
SOURCE = REPO_ROOT / "configurations/robot_lab/centered_axis_grasp_search.json"
GEOMETRY_AUDIT = REPO_ROOT / "configurations/robot_lab/gripper_geometry_audit.json"
CANDIDATE_INDICES = (2, 3)


def build_centered_contact_face_audit() -> dict[str, Any]:
    source = load_strict_json(SOURCE)
    geometry = load_strict_json(GEOMETRY_AUDIT)
    verify_signed_payload(source, label="source centered-axis search")
    verify_signed_payload(geometry, label="source gripper geometry audit")
    source_rows = {row["candidate_index"]: row for row in source["candidates"]}
    candidates = []
    for index in CANDIDATE_INDICES:
        row = _candidate(index, holdout=False, explicit_pad_proxy_only=True, pad_midpoint_targeting=True, post_yaw_settle_seconds=POST_YAW_SETTLE_SECONDS, center_selected_axis_offset=True, retain_contact_diagnostics=True)
        diagnostics = row.pop("pad_contact_phase_diagnostics")
        row["base_contact_geometry_eligible"] = row["geometry_eligible"]
        row["approach_object_motion_valid"] = row["preclose_object_displacement_m"] <= APPROACH_MOTION_LIMIT_M
        row["nonpad_contact_valid"] = row["nonpad_robot_object_contact_frame_count"] == 0
        row["geometry_eligible"] = bool(row["base_contact_geometry_eligible"] and row["approach_object_motion_valid"] and row["nonpad_contact_valid"])
        if row != source_rows[index]:
            raise ValueError(f"Audited candidate {index} drifted from centered source")
        classified = []
        for diagnostic in diagnostics:
            aggregate = diagnostic["aggregate"]
            faces = {
                role: _classify_face(representative["centroid_object_m"])
                for role, representative in aggregate["representative_contacts"].items()
            }
            classified.append({**diagnostic, "representative_face_classification": faces})
        candidates.append({
            "candidate_index": index,
            "request": row["request"],
            "selected_object_principal_axis": row["selected_object_principal_axis"],
            "preclose_object_displacement_m": row["preclose_object_displacement_m"],
            "contact_phase_diagnostics": classified,
        })
    proof = geometry["synthetic_contact_convention_proof"]
    return sign_payload({
        "schema_version": SCHEMA_VERSION,
        "evidence_mode": "diagnostic_replay_of_centered_bilateral_contacts",
        "source_centered_axis_search_identity_sha256": source["identity_sha256"],
        "source_gripper_geometry_audit_identity_sha256": geometry["identity_sha256"],
        "source_candidate_metrics_identical": True,
        "contact_normal_convention": geometry["contact_normal_convention"],
        "geom_order_independent": proof["geom_order_independent"],
        "synthetic_convention_aggregate_valid": proof["aggregate_valid"],
        "anchor_half_extents_m": [dimension / 2.0 for dimension in ANCHOR_DIMENSIONS_M],
        "candidates": candidates,
        "actual_mujoco_grasp_success": False,
        "simulation_training_ready": False,
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "authority_not_granted": ["geometry_eligible_grasp_candidate", "unassisted_mujoco_grasp_success", "simulation_training_ready", "physical_actuation"],
    })


def _classify_face(point: list[float]) -> dict[str, Any]:
    half = [dimension / 2.0 for dimension in ANCHOR_DIMENSIONS_M]
    faces = {}
    for axis, coordinate, extent in zip(("x", "y", "z"), point, half, strict=True):
        faces[f"+{axis}"] = abs(coordinate - extent)
        faces[f"-{axis}"] = abs(coordinate + extent)
    face, residual = min(faces.items(), key=lambda item: (item[1], item[0]))
    return {"nearest_face": face, "face_residual_m": round(residual, 9)}


def verify_centered_contact_face_audit(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="centered contact-face audit")
    if not payload.get("source_candidate_metrics_identical"):
        raise ValueError("Contact-face audit source metrics drifted")
    if not payload.get("geom_order_independent") or not payload.get("synthetic_convention_aggregate_valid"):
        raise ValueError("Contact normal convention proof is invalid")
    if [row.get("candidate_index") for row in payload.get("candidates", [])] != list(CANDIDATE_INDICES):
        raise ValueError("Contact-face audit candidate set drifted")
    if any(not row.get("contact_phase_diagnostics") for row in payload["candidates"]):
        raise ValueError("Contact-face audit lacks bilateral diagnostics")
