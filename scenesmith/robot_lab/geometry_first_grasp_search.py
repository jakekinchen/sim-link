"""Bounded geometry-first grasp search through explicit fingertip pads."""

from __future__ import annotations

import math
import tempfile

from pathlib import Path
from typing import Any, Callable

import numpy as np

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload, verify_signed_payload
from scenesmith.robot_lab.causal_sort_expert import CausalSortExpert, CausalSortExpertConfig, SIMULATION_HOME
from scenesmith.robot_lab.grasp_pose_solver import apply_and_read_object_yaw, solve_grasp_pose
from scenesmith.robot_lab.grasp_pose_solver import (
    APPROACH_MOTION_LIMIT_M,
    POSITION_TOLERANCE_M,
)
from scenesmith.robot_lab.grasp_evidence import (
    KEYFRAME_IMAGE_SIZE,
    finalize_rendered_keyframes,
    retain_rendered_keyframe,
    validate_rendered_keyframes,
)
from scenesmith.robot_lab.gripper_contact_semantics import (
    FIXED_PAD_SITE,
    MOVING_PAD_SITE,
    aggregate_pad_contacts,
    apply_gripper_contact_identities,
    apply_explicit_pad_proxy_contact_model,
    compiled_pad_geom_roles,
    extract_pad_contacts,
)
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID, _bind_anchor_geometry, _raw_frame, _scene
from scenesmith.robot_lab.mujoco_export import prepare_mujoco_so101_assets, render_mujoco_xml
from scenesmith.robot_lab.strict_grasp import evaluate_antipodal_contact_witness, strict_grasp_spec_v2


SCHEMA_VERSION = "scenesmith.geometry_first_grasp_search.v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
GEOMETRY_AUDIT = REPO_ROOT / "configurations/robot_lab/gripper_geometry_audit.json"
POSE_FIXTURE = REPO_ROOT / "configurations/robot_lab/grasp_pose_solver.fixture.json"
# Retired design: 12 Halton samples under-sample the largest base (17), and
# vertical_m=(0.014, 0.034) was proven to search dead space above the object.
HALTON_BASES = (2, 3, 5, 7, 11, 13, 17)
TRAINING_CANDIDATES = 12
MINIMUM_REUSE_CANDIDATE_COUNT = 5 * max(HALTON_BASES)
DEGENERATE_SEARCH_NOTICE = (
    "retired: 12-sample Halton design under-samples base 17 and its vertical "
    "band searches dead space above the object"
)
RANGES = {
    "wrist_flex_rad": (-0.65, 0.65),
    "wrist_roll_rad": (-1.6, 1.6),
    "object_yaw_rad": (-0.7, 0.7),
    "lateral_x_m": (-0.012, 0.012),
    "lateral_y_m": (-0.012, 0.012),
    "vertical_m": (0.014, 0.034),
    "close_target_rad": (-0.17, 0.12),
}
PRINCIPAL_AXIS_ALIGNMENT_MINIMUM = 0.8


class GraspGateFailure(ValueError):
    """A rejected candidate with structured measured-vs-threshold evidence."""

    def __init__(self, message: str, *, gate_margins: dict[str, dict[str, Any]]) -> None:
        super().__init__(message)
        self.gate_margins = gate_margins


def build_geometry_first_grasp_search() -> dict[str, Any]:
    audit = load_strict_json(GEOMETRY_AUDIT)
    pose = load_strict_json(POSE_FIXTURE)
    verify_signed_payload(audit, label="source gripper geometry audit")
    verify_signed_payload(pose, label="source grasp pose fixture")
    candidates = [_candidate(index, holdout=False) for index in range(1, TRAINING_CANDIDATES + 1)]
    eligible = [row for row in candidates if row["geometry_eligible"]]
    selected = min(eligible, key=_rank) if eligible else None
    holdout = _candidate(TRAINING_CANDIDATES + 1, holdout=True)
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "deterministic_geometry_first_mujoco_search",
            "source_gripper_geometry_audit_identity_sha256": audit["identity_sha256"],
            "source_grasp_pose_solver_identity_sha256": pose["identity_sha256"],
            "range_derivation": {
                "wrist": "bounded interior of compiled joint ranges and verified pose fixture",
                "object_yaw": "bounded symmetric anchor orientations",
                "lateral_offsets": "less than half the nominal 30-50 mm object extents",
                "vertical_offset": "table clearance and nominal 30 mm object height",
                "close_target": "compiled gripper range near closed end; aperture audit remains simulation-only",
            },
            "ranges": {name: list(bounds) for name, bounds in RANGES.items()},
            "design": "seven_dimensional_halton_bases_2_3_5_7_11_13_17",
            "search_status": "retired_degenerate_design",
            "retirement_notice": DEGENERATE_SEARCH_NOTICE,
            "reuse_requirements": {
                "minimum_candidate_count": MINIMUM_REUSE_CANDIDATE_COUNT,
                "largest_halton_base": max(HALTON_BASES),
                "vertical_band_must_be_rederived": True,
            },
            "friction_or_compliance_tuned": False,
            "training_candidate_count": len(candidates),
            "geometry_eligible_count": len(eligible),
            "candidates": candidates,
            "selected_candidate": selected,
            "holdout": {"excluded_from_selection": True, "candidate": holdout},
            "local_refinement_executed": bool(selected),
            "actual_mujoco_grasp_success": False,
            "simulation_training_ready": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "authority_not_granted": ["unassisted_mujoco_grasp_success", "simulation_training_ready", "physical_actuation"],
        }
    )


def verify_geometry_first_grasp_search(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="geometry-first grasp search")
    candidates = payload.get("candidates", [])
    if payload.get("training_candidate_count") != len(candidates):
        raise ValueError("Geometry search candidate count drifted")
    if not payload.get("holdout", {}).get("excluded_from_selection"):
        raise ValueError("Geometry holdout leaked into selection")
    if payload.get("friction_or_compliance_tuned") is not False:
        raise ValueError("Geometry search changed contact properties")
    if payload.get("geometry_eligible_count") != sum(row["geometry_eligible"] for row in candidates):
        raise ValueError("Geometry eligibility count drifted")
    if payload.get("search_status") != "retired_degenerate_design":
        raise ValueError("Degenerate geometry search was not retired")
    if payload.get("retirement_notice") != DEGENERATE_SEARCH_NOTICE:
        raise ValueError("Degenerate geometry search notice drifted")
    reuse = payload.get("reuse_requirements")
    if not isinstance(reuse, dict) or reuse.get("minimum_candidate_count") < MINIMUM_REUSE_CANDIDATE_COUNT:
        raise ValueError("Geometry search reuse candidate floor is missing")
    if reuse.get("largest_halton_base") != max(HALTON_BASES) or reuse.get("vertical_band_must_be_rederived") is not True:
        raise ValueError("Geometry search reuse warning is incomplete")
    for row in candidates:
        if "gate_margins" in row:
            if not isinstance(row.get("failed_gate_margins"), list):
                raise ValueError("Geometry search rejection lacks failed gate margins")
            expected_failed = {
                name
                for name, margin in row["gate_margins"].items()
                if not margin.get("passed")
            }
            observed_failed = {
                margin.get("gate") for margin in row["failed_gate_margins"]
            }
            if observed_failed != expected_failed:
                raise ValueError("Geometry search failed gate margins drifted")
        if row.get("setup_valid"):
            if "gate_margins" not in row:
                raise ValueError("Geometry search candidate lacks gate margins")
            validate_rendered_keyframes(row.get("rendered_keyframes"))


def _candidate(
    index: int,
    *,
    holdout: bool,
    explicit_pad_proxy_only: bool = False,
    pad_midpoint_targeting: bool = False,
    post_yaw_settle_seconds: float = 0.0,
    principal_axis_alignment: bool = False,
    joint_wrist_axis_alignment: bool = False,
    best_principal_axis_alignment: bool = False,
    center_selected_axis_offset: bool = False,
    retain_contact_diagnostics: bool = False,
    close_target_override_rad: float | None = None,
    vertical_target_override_m: float | None = None,
    selected_axis_clearance_m: float = 0.0,
    execute_full_lift_cycle: bool = False,
    capture_keyframes: bool = True,
) -> dict[str, Any]:
    values = _halton(index)
    request = {name: _scale(value, RANGES[name]) for name, value in zip(RANGES, values, strict=True)}
    try:
        result = _run_candidate(
            request,
            explicit_pad_proxy_only=explicit_pad_proxy_only,
            pad_midpoint_targeting=pad_midpoint_targeting,
            post_yaw_settle_seconds=post_yaw_settle_seconds,
            principal_axis_alignment=principal_axis_alignment,
            joint_wrist_axis_alignment=joint_wrist_axis_alignment,
            best_principal_axis_alignment=best_principal_axis_alignment,
            center_selected_axis_offset=center_selected_axis_offset,
            retain_contact_diagnostics=retain_contact_diagnostics,
            close_target_override_rad=close_target_override_rad,
            vertical_target_override_m=vertical_target_override_m,
            selected_axis_clearance_m=selected_axis_clearance_m,
            execute_full_lift_cycle=execute_full_lift_cycle,
            capture_keyframes=capture_keyframes,
        )
    except GraspGateFailure as exc:
        failed_gate_margins = [
            {"gate": name, **margin}
            for name, margin in exc.gate_margins.items()
            if not margin["passed"]
        ]
        return {
            "candidate_index": index,
            "holdout": holdout,
            "request": request,
            "setup_valid": False,
            "rejection_reason": str(exc),
            "geometry_eligible": False,
            "gate_margins": exc.gate_margins,
            "failed_gate_margins": failed_gate_margins,
        }
    except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
        return {"candidate_index": index, "holdout": holdout, "request": request, "setup_valid": False, "rejection_reason": str(exc), "geometry_eligible": False}
    return {"candidate_index": index, "holdout": holdout, "request": request, **result}


def _run_candidate(
    request: dict[str, float],
    *,
    explicit_pad_proxy_only: bool = False,
    pad_midpoint_targeting: bool = False,
    post_yaw_settle_seconds: float = 0.0,
    principal_axis_alignment: bool = False,
    joint_wrist_axis_alignment: bool = False,
    best_principal_axis_alignment: bool = False,
    center_selected_axis_offset: bool = False,
    retain_contact_diagnostics: bool = False,
    close_target_override_rad: float | None = None,
    vertical_target_override_m: float | None = None,
    selected_axis_clearance_m: float = 0.0,
    execute_full_lift_cycle: bool = False,
    capture_keyframes: bool = False,
    recording_stable_hold_frames: int = 0,
    scene_initial_position_m: tuple[float, float, float] | None = None,
    recording_sink: Callable[[dict[str, Any], dict[str, np.ndarray]], None] | None = None,
) -> dict[str, Any]:
    if isinstance(recording_stable_hold_frames, bool) or recording_stable_hold_frames < 0:
        raise ValueError("Recording stable-hold frame count must be nonnegative")
    scene = _scene(initial_position_m=scene_initial_position_m)
    raw_frames: list[dict[str, Any]] = []
    rendered_keyframes: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="scenesmith-geometry-search-") as directory:
        root = Path(directory)
        robot_xml = prepare_mujoco_so101_assets(root, scene.robot.base_position_m)
        if explicit_pad_proxy_only:
            apply_explicit_pad_proxy_contact_model(robot_xml)
        else:
            apply_gripper_contact_identities(robot_xml)
        scene_xml = root / "scene.xml"
        scene_xml.write_text(render_mujoco_xml(scene), encoding="utf-8")
        _bind_anchor_geometry(scene_xml)
        expert: CausalSortExpert | None = None
        pad_roles: dict[int, str] = {}
        fixed_site = moving_site = object_body = -1

        def retain(frame: dict[str, Any], _images: dict[str, np.ndarray]) -> None:
            assert expert is not None
            retained = _raw_frame(expert, frame)
            contacts = extract_pad_contacts(expert.mujoco, expert.model, expert.data, object_body_id=object_body, pad_geom_roles=pad_roles)
            object_rotation = np.asarray(expert.data.xmat[object_body]).reshape(3, 3)
            closing_world = expert.data.site_xpos[moving_site] - expert.data.site_xpos[fixed_site]
            closing_object = object_rotation.T @ closing_world
            aggregate = aggregate_pad_contacts(contacts, closing_object.tolist()) if contacts else None
            retained["pad_contacts"] = contacts
            retained["pad_contact_aggregate"] = aggregate
            retained["nonpad_robot_object_contacts"] = _nonpad_contacts(expert, object_body, set(pad_roles))
            if explicit_pad_proxy_only:
                retained["all_robot_object_contact_geoms"] = _all_robot_object_contact_geoms(
                    expert,
                    object_body,
                )
                retained["raw_pad_normal_forces_n"] = _raw_pad_normal_forces(
                    expert,
                    object_body,
                    set(pad_roles),
                )
            raw_frames.append(retained)
            if recording_sink is not None:
                recording_sink(retained, _images)
            if capture_keyframes:
                retain_rendered_keyframe(
                    rendered_keyframes,
                    frame,
                    _images,
                    image_size=KEYFRAME_IMAGE_SIZE,
                )

        expert = CausalSortExpert(
            scene,
            scene_xml,
            seed=1701 + index_hash(request),
            frame_sink=retain,
            config=CausalSortExpertConfig(
                image_size=KEYFRAME_IMAGE_SIZE if capture_keyframes else 16,
                capture_images=capture_keyframes,
            ),
        )
        try:
            pad_roles = compiled_pad_geom_roles(expert.mujoco, expert.model)
            fixed_site = expert._id(expert.mujoco.mjtObj.mjOBJ_SITE, FIXED_PAD_SITE)
            moving_site = expert._id(expert.mujoco.mjtObj.mjOBJ_SITE, MOVING_PAD_SITE)
            object_body = expert.cube_body_ids[OBJECT_ID]
            expert.data.qpos[: expert.model.nu] = np.asarray(SIMULATION_HOME)
            expert.data.ctrl[: expert.model.nu] = np.asarray(SIMULATION_HOME)
            expert.mujoco.mj_forward(expert.model, expert.data)
            for _ in range(round(0.25 / expert.model.opt.timestep)):
                expert.mujoco.mj_step(expert.model, expert.data)
            achieved_yaw = apply_and_read_object_yaw(expert.mujoco, expert.model, expert.data, object_joint_name=f"{OBJECT_ID}_free", object_body_name=OBJECT_ID, yaw_rad=request["object_yaw_rad"])
            if post_yaw_settle_seconds < 0.0 or not math.isfinite(post_yaw_settle_seconds):
                raise ValueError("Post-yaw settle duration must be finite and nonnegative")
            pre_settle_position = expert.data.xpos[object_body].copy()
            if post_yaw_settle_seconds:
                settle_steps = max(
                    1,
                    round(post_yaw_settle_seconds / expert.model.opt.timestep),
                )
                for _ in range(settle_steps):
                    expert.mujoco.mj_step(expert.model, expert.data)
            else:
                settle_steps = 0
            settled_yaw = math.atan2(
                float(expert.data.xmat[object_body][3]),
                float(expert.data.xmat[object_body][0]),
            )
            passive_settle_displacement = float(
                np.linalg.norm(expert.data.xpos[object_body] - pre_settle_position)
            )
            passive_settle_yaw_drift = math.atan2(
                math.sin(settled_yaw - achieved_yaw),
                math.cos(settled_yaw - achieved_yaw),
            )
            effective_base_request = dict(request)
            if close_target_override_rad is not None:
                effective_base_request["close_target_rad"] = close_target_override_rad
            target_vertical = request["vertical_m"] if vertical_target_override_m is None else vertical_target_override_m
            anchor_start = expert.data.xpos[object_body].copy()
            target = anchor_start + np.asarray([request["lateral_x_m"], request["lateral_y_m"], target_vertical])
            approach = target + np.asarray([0.0, 0.0, 0.04])
            effective_request = effective_base_request
            axis_alignment: dict[str, Any] | None = None
            if best_principal_axis_alignment or center_selected_axis_offset:
                object_rotation = np.asarray(expert.data.xmat[object_body]).reshape(3, 3)
                axis_alignment = _select_best_horizontal_principal_axis_wrist_pose(
                    expert,
                    desired_midpoint=target,
                    request=effective_base_request,
                    fixed_site=fixed_site,
                    moving_site=moving_site,
                    object_rotation_world=object_rotation,
                )
                if center_selected_axis_offset:
                    selected_axis = np.asarray(
                        axis_alignment["object_x_axis_world"], dtype=np.float64
                    )
                    selected_axis[2] = 0.0
                    selected_axis /= np.linalg.norm(selected_axis)
                    original_lateral = np.asarray(
                        [request["lateral_x_m"], request["lateral_y_m"], 0.0]
                    )
                    removed_projection = float(
                        np.dot(original_lateral, selected_axis)
                    )
                    retained_lateral = original_lateral - removed_projection * selected_axis + selected_axis_clearance_m * selected_axis
                    target = (
                        anchor_start
                        + retained_lateral
                        + np.asarray([0.0, 0.0, target_vertical])
                    )
                    approach = target + np.asarray([0.0, 0.0, 0.04])
                    selected_label = axis_alignment[
                        "selected_object_principal_axis"
                    ]
                    final_alignment = _select_horizontal_principal_axis_wrist_pose(
                        expert,
                        desired_midpoint=target,
                        request=effective_base_request,
                        fixed_site=fixed_site,
                        moving_site=moving_site,
                        object_axis_world=selected_axis,
                    )
                    final_alignment.update(
                        {
                            "selected_object_principal_axis": selected_label,
                            "original_horizontal_target_offset_world_m": original_lateral.tolist(),
                            "removed_selected_axis_offset_m": removed_projection,
                            "retained_horizontal_target_offset_world_m": retained_lateral.tolist(),
                        }
                    )
                    if selected_axis_clearance_m:
                        final_alignment["selected_axis_clearance_m"] = selected_axis_clearance_m
                    if vertical_target_override_m is not None:
                        final_alignment["target_vertical_offset_m"] = target_vertical
                    axis_alignment = final_alignment
                effective_request = {
                    **effective_base_request,
                    "wrist_flex_rad": axis_alignment["selected_wrist_flex_rad"],
                    "wrist_roll_rad": axis_alignment["selected_wrist_roll_rad"],
                }
            elif joint_wrist_axis_alignment:
                object_rotation = np.asarray(expert.data.xmat[object_body]).reshape(3, 3)
                axis_alignment = _select_horizontal_principal_axis_wrist_pose(
                    expert,
                    desired_midpoint=target,
                    request=effective_base_request,
                    fixed_site=fixed_site,
                    moving_site=moving_site,
                    object_axis_world=object_rotation[:, 0],
                )
                effective_request = {
                    **effective_base_request,
                    "wrist_flex_rad": axis_alignment["selected_wrist_flex_rad"],
                    "wrist_roll_rad": axis_alignment["selected_wrist_roll_rad"],
                }
            elif principal_axis_alignment:
                object_rotation = np.asarray(expert.data.xmat[object_body]).reshape(3, 3)
                axis_alignment = _select_principal_axis_wrist_roll(
                    expert,
                    desired_midpoint=target,
                    request=effective_base_request,
                    fixed_site=fixed_site,
                    moving_site=moving_site,
                    object_axis_world=object_rotation[:, 0],
                )
                effective_request = {
                    **effective_base_request,
                    "wrist_roll_rad": axis_alignment["selected_wrist_roll_rad"],
                }
            if pad_midpoint_targeting:
                approach_solution = _solve_pad_midpoint_target(
                    expert,
                    desired_midpoint=approach,
                    request=effective_request,
                    fixed_site=fixed_site,
                    moving_site=moving_site,
                )
            else:
                approach_solution = solve_grasp_pose(expert.mujoco, expert.model, expert.data, gripper_site_id=expert.gripper_site_id, target_position_m=approach.tolist(), wrist_flex_rad=effective_request["wrist_flex_rad"], wrist_roll_rad=effective_request["wrist_roll_rad"])
            expert._move_control("approach", approach_solution["qpos"][: expert.model.nu], 14)
            if pad_midpoint_targeting:
                pregrasp_solution = _solve_pad_midpoint_target(
                    expert,
                    desired_midpoint=target,
                    request=effective_request,
                    fixed_site=fixed_site,
                    moving_site=moving_site,
                )
            else:
                pregrasp_solution = solve_grasp_pose(expert.mujoco, expert.model, expert.data, gripper_site_id=expert.gripper_site_id, target_position_m=target.tolist(), wrist_flex_rad=effective_request["wrist_flex_rad"], wrist_roll_rad=effective_request["wrist_roll_rad"])
            expert._move_control("pregrasp", pregrasp_solution["qpos"][: expert.model.nu], 18)
            preclose_displacement = float(np.linalg.norm(expert.data.xpos[object_body] - anchor_start))
            expert._move_gripper("close", effective_request["close_target_rad"], 36)
            expert._hold("grasp_hold", 8)
            if execute_full_lift_cycle:
                lift_solution = _solve_pad_midpoint_target(
                    expert,
                    desired_midpoint=target + np.asarray([0.0, 0.0, 0.04]),
                    request=effective_request,
                    fixed_site=fixed_site,
                    moving_site=moving_site,
                )
                gripper_address = int(
                    expert.model.jnt_qposadr[
                        expert._id(expert.mujoco.mjtObj.mjOBJ_JOINT, "gripper")
                    ]
                )
                lift_control = lift_solution["qpos"][: expert.model.nu].copy()
                lift_control[gripper_address] = effective_request["close_target_rad"]
                expert._move_control("unassisted_lift", lift_control, 24)
                expert._hold("unsupported_lift_hold", 12)
                if recording_stable_hold_frames:
                    expert._hold("recording_stable_hold", recording_stable_hold_frames)
                lower_control = pregrasp_solution["qpos"][: expert.model.nu].copy()
                lower_control[gripper_address] = effective_request["close_target_rad"]
                expert._move_control("lower", lower_control, 24)
                expert._move_gripper("release", 1.6, 12)
                expert._hold("release_settle", 8)
                retreat_control = approach_solution["qpos"][: expert.model.nu].copy()
                retreat_control[gripper_address] = 1.6
                expert._move_control("retreat", retreat_control, 24)
        finally:
            expert.close()
    close = [row for row in raw_frames if row["phase"] == "close"]
    hold = [row for row in raw_frames if row["phase"] == "grasp_hold"]
    spec = strict_grasp_spec_v2()["antipodal_contact_requirement"]
    confirmation = _valid_contact(close[-1], spec) if close else False
    hold_valid = [_valid_contact(row, spec) for row in hold]
    aggregates = [row["pad_contact_aggregate"] for row in close + hold if row["pad_contact_aggregate"]]
    geometry_eligible = confirmation and len(hold_valid) == 8 and all(hold_valid)
    result = {
        "setup_valid": True,
        "achieved_object_yaw_rad": achieved_yaw,
        "approach_position_residual_m": approach_solution["position_residual_m"],
        "pregrasp_position_residual_m": pregrasp_solution["position_residual_m"],
        "preclose_object_displacement_m": preclose_displacement,
        "maximum_contact_force_n": max(row["robot_anchor_contact_force_n_max"] for row in raw_frames),
        "nonpad_robot_object_contact_frame_count": sum(bool(row["nonpad_robot_object_contacts"]) for row in raw_frames),
        "close_pad_contact_frame_count": sum(row["pad_contact_aggregate"] is not None for row in close),
        "hold_pad_contact_frame_count": sum(row["pad_contact_aggregate"] is not None for row in hold),
        "hold_strict_v2_valid_frame_count": sum(hold_valid),
        "minimum_representative_span_m": min((row["euclidean_span_m"] for row in aggregates), default=None),
        "maximum_representative_span_m": max((row["euclidean_span_m"] for row in aggregates), default=None),
        "best_normal_alignment": max((min(row["fixed_normal_span_alignment"], row["moving_normal_span_alignment"]) for row in aggregates), default=None),
        "geometry_eligible": geometry_eligible,
    }
    result["gate_margins"] = _gate_margins(
        result,
        minimum_hold_frames=8,
        minimum_span_m=spec["minimum_contact_span_m"],
        minimum_normal_alignment=0.8,
        approach_motion_limit_m=APPROACH_MOTION_LIMIT_M,
        position_tolerance_m=POSITION_TOLERANCE_M,
    )
    result["failed_gate_margins"] = [
        {"gate": name, **margin}
        for name, margin in result["gate_margins"].items()
        if not margin["passed"]
    ]
    if capture_keyframes:
        result["rendered_keyframes"] = finalize_rendered_keyframes(rendered_keyframes)
    if post_yaw_settle_seconds:
        result.update(
            {
                "settled_object_yaw_rad": settled_yaw,
                "post_yaw_settle_seconds": post_yaw_settle_seconds,
                "post_yaw_settle_step_count": settle_steps,
                "passive_settle_displacement_m": passive_settle_displacement,
                "passive_settle_yaw_drift_rad": passive_settle_yaw_drift,
            }
        )
    if close_target_override_rad is not None:
        result["effective_close_target_rad"] = close_target_override_rad
    if vertical_target_override_m is not None:
        result["effective_vertical_target_offset_m"] = vertical_target_override_m
    if explicit_pad_proxy_only:
        result["observed_robot_object_contact_geoms"] = sorted(
            {
                name
                for row in raw_frames
                for name in row.get("all_robot_object_contact_geoms", [])
            }
        )
        raw_pad_forces = [
            force
            for row in raw_frames
            for force in row.get("raw_pad_normal_forces_n", [])
        ]
        result["raw_pad_contact_count"] = len(raw_pad_forces)
        result["raw_pad_normal_force_range_n"] = (
            [min(raw_pad_forces), max(raw_pad_forces)] if raw_pad_forces else None
        )
    if pad_midpoint_targeting:
        result["approach_predicted_pad_midpoint_residual_m"] = approach_solution[
            "predicted_pad_midpoint_residual_m"
        ]
        result["pregrasp_predicted_pad_midpoint_residual_m"] = pregrasp_solution[
            "predicted_pad_midpoint_residual_m"
        ]
    if retain_contact_diagnostics:
        result["pad_contact_phase_diagnostics"] = [
            {
                "phase": row["phase"],
                "phase_frame_index": index,
                "aggregate": row["pad_contact_aggregate"],
            }
            for phase in ("close", "grasp_hold")
            for index, row in enumerate(
                frame for frame in raw_frames if frame["phase"] == phase
            )
            if row["pad_contact_aggregate"] is not None
        ]
    if execute_full_lift_cycle:
        phase_names = ("grasp_hold", "unassisted_lift", "unsupported_lift_hold", "lower", "release_settle", "retreat")
        phase_rows = {phase: [row for row in raw_frames if row["phase"] == phase] for phase in phase_names}
        result["full_lift_cycle"] = {
            "phase_frame_counts": {phase: len(rows) for phase, rows in phase_rows.items()},
            "strict_v2_valid_frame_counts": {phase: sum(_valid_contact(row, spec) for row in rows) for phase, rows in phase_rows.items()},
            "unsupported_lift_hold_frame_count": sum(not row["anchor_support_contacts"] for row in phase_rows["unsupported_lift_hold"]),
            "active_assist_frame_count": sum(bool(row["grasp_assists_active"]) for row in raw_frames),
            "object_z_m": {phase: [row["cube_positions_m"][OBJECT_ID][2] for row in rows] for phase, rows in phase_rows.items()},
            "robot_object_contact_geoms": {phase: [row.get("all_robot_object_contact_geoms", []) for row in rows] for phase, rows in phase_rows.items()},
            "release_settle_contact_clear": all(not row.get("all_robot_object_contact_geoms", []) for row in phase_rows["release_settle"]),
            "retreat_contact_clear": all(not row.get("all_robot_object_contact_geoms", []) for row in phase_rows["retreat"]),
            "release_settle_final_contact_clear": bool(phase_rows["release_settle"]) and not phase_rows["release_settle"][-1].get("all_robot_object_contact_geoms", []),
            "retreat_final_contact_clear": bool(phase_rows["retreat"]) and not phase_rows["retreat"][-1].get("all_robot_object_contact_geoms", []),
        }
        if recording_stable_hold_frames:
            recording_hold_rows = [
                row for row in raw_frames if row["phase"] == "recording_stable_hold"
            ]
            result["recording_stable_hold"] = {
                "frame_count": len(recording_hold_rows),
                "strict_v2_valid_frame_count": sum(
                    _valid_contact(row, spec) for row in recording_hold_rows
                ),
                "anchor_support_free_frame_count": sum(
                    not row["anchor_support_contacts"] for row in recording_hold_rows
                ),
            }
    if (
        principal_axis_alignment
        or joint_wrist_axis_alignment
        or best_principal_axis_alignment
        or center_selected_axis_offset
    ):
        assert axis_alignment is not None
        result.update(axis_alignment)
    return result


def _solve_pad_midpoint_target(
    expert: CausalSortExpert,
    *,
    desired_midpoint: np.ndarray,
    request: dict[str, float],
    fixed_site: int,
    moving_site: int,
) -> dict[str, Any]:
    site_target = desired_midpoint.copy()
    best: tuple[float, dict[str, Any]] | None = None
    for _ in range(10):
        solved = solve_grasp_pose(
            expert.mujoco,
            expert.model,
            expert.data,
            gripper_site_id=expert.gripper_site_id,
            target_position_m=site_target.tolist(),
            wrist_flex_rad=request["wrist_flex_rad"],
            wrist_roll_rad=request["wrist_roll_rad"],
        )
        predicted = expert.mujoco.MjData(expert.model)
        predicted.qpos[:] = solved["qpos"]
        predicted.qpos[
            int(
                expert.model.jnt_qposadr[
                    expert._id(expert.mujoco.mjtObj.mjOBJ_JOINT, "gripper")
                ]
            )
        ] = request["close_target_rad"]
        expert.mujoco.mj_forward(expert.model, predicted)
        midpoint = 0.5 * (
            predicted.site_xpos[fixed_site] + predicted.site_xpos[moving_site]
        )
        error = desired_midpoint - midpoint
        residual = float(np.linalg.norm(error))
        if best is None or residual < best[0]:
            best = (residual, solved)
        if residual <= 0.0005:
            break
        site_target += error
    if best is None or best[0] > 0.001:
        raise ValueError(f"Predicted pad midpoint residual exceeds limit: {best}")
    output = best[1]
    output["qpos"][
        int(
            expert.model.jnt_qposadr[
                expert._id(expert.mujoco.mjtObj.mjOBJ_JOINT, "gripper")
            ]
        )
    ] = 1.6
    output["predicted_pad_midpoint_residual_m"] = best[0]
    return output


def _select_principal_axis_wrist_roll(
    expert: CausalSortExpert,
    *,
    desired_midpoint: np.ndarray,
    request: dict[str, float],
    fixed_site: int,
    moving_site: int,
    object_axis_world: np.ndarray,
) -> dict[str, Any]:
    original_roll = request["wrist_roll_rad"]
    roll_min, roll_max = RANGES["wrist_roll_rad"]
    roll_grid = sorted(
        {
            original_roll,
            *(float(value) for value in np.linspace(roll_min, roll_max, 33)),
        }
    )
    object_axis = np.asarray(object_axis_world, dtype=np.float64)
    object_axis /= np.linalg.norm(object_axis)
    best: tuple[tuple[float, float, float], dict[str, Any]] | None = None
    for roll in roll_grid:
        trial_request = {**request, "wrist_roll_rad": roll}
        try:
            solved = _solve_pad_midpoint_target(
                expert,
                desired_midpoint=desired_midpoint,
                request=trial_request,
                fixed_site=fixed_site,
                moving_site=moving_site,
            )
        except (RuntimeError, ValueError, np.linalg.LinAlgError):
            continue
        predicted = expert.mujoco.MjData(expert.model)
        predicted.qpos[:] = solved["qpos"]
        predicted.qpos[
            int(
                expert.model.jnt_qposadr[
                    expert._id(expert.mujoco.mjtObj.mjOBJ_JOINT, "gripper")
                ]
            )
        ] = request["close_target_rad"]
        expert.mujoco.mj_forward(expert.model, predicted)
        closing_axis = (
            predicted.site_xpos[moving_site] - predicted.site_xpos[fixed_site]
        )
        closing_axis /= np.linalg.norm(closing_axis)
        alignment = abs(float(np.dot(closing_axis, object_axis)))
        score = (alignment, -abs(roll - original_roll), -roll)
        evidence = {
            "sampled_wrist_roll_rad": original_roll,
            "selected_wrist_roll_rad": roll,
            "object_x_axis_world": object_axis.tolist(),
            "predicted_closing_axis_world": closing_axis.tolist(),
            "predicted_principal_axis_alignment": alignment,
            "wrist_roll_grid_count": len(roll_grid),
        }
        if best is None or score > best[0]:
            best = (score, evidence)
    measured = (
        None if best is None else best[1]["predicted_principal_axis_alignment"]
    )
    if measured is None or measured < PRINCIPAL_AXIS_ALIGNMENT_MINIMUM:
        raise GraspGateFailure(
            f"No principal-axis-aligned wrist roll found: {best}",
            gate_margins={
                "principal_axis_alignment": _margin(
                    measured, PRINCIPAL_AXIS_ALIGNMENT_MINIMUM, ">="
                )
            },
        )
    return best[1]


def _select_horizontal_principal_axis_wrist_pose(
    expert: CausalSortExpert,
    *,
    desired_midpoint: np.ndarray,
    request: dict[str, float],
    fixed_site: int,
    moving_site: int,
    object_axis_world: np.ndarray,
) -> dict[str, Any]:
    flex_min, flex_max = RANGES["wrist_flex_rad"]
    roll_min, roll_max = RANGES["wrist_roll_rad"]
    flex_values = sorted(
        {
            request["wrist_flex_rad"],
            *(float(value) for value in np.linspace(flex_min, flex_max, 5)),
        }
    )
    roll_values = sorted(
        {
            request["wrist_roll_rad"],
            *(float(value) for value in np.linspace(roll_min, roll_max, 9)),
        }
    )
    object_axis = np.asarray(object_axis_world, dtype=np.float64)
    object_axis /= np.linalg.norm(object_axis)
    evaluated: dict[tuple[float, float], dict[str, Any]] = {}

    def evaluate(flex: float, roll: float) -> dict[str, Any] | None:
        key = (flex, roll)
        if key in evaluated:
            return evaluated[key]
        trial_request = {
            **request,
            "wrist_flex_rad": flex,
            "wrist_roll_rad": roll,
        }
        try:
            solved = _solve_pad_midpoint_target(
                expert,
                desired_midpoint=desired_midpoint,
                request=trial_request,
                fixed_site=fixed_site,
                moving_site=moving_site,
            )
        except (RuntimeError, ValueError, np.linalg.LinAlgError):
            return None
        predicted = expert.mujoco.MjData(expert.model)
        predicted.qpos[:] = solved["qpos"]
        predicted.qpos[
            int(
                expert.model.jnt_qposadr[
                    expert._id(expert.mujoco.mjtObj.mjOBJ_JOINT, "gripper")
                ]
            )
        ] = request["close_target_rad"]
        expert.mujoco.mj_forward(expert.model, predicted)
        closing_axis = (
            predicted.site_xpos[moving_site] - predicted.site_xpos[fixed_site]
        )
        closing_axis /= np.linalg.norm(closing_axis)
        alignment = abs(float(np.dot(closing_axis, object_axis)))
        vertical = abs(float(closing_axis[2]))
        evidence = {
            "selected_wrist_flex_rad": flex,
            "selected_wrist_roll_rad": roll,
            "object_x_axis_world": object_axis.tolist(),
            "predicted_closing_axis_world": closing_axis.tolist(),
            "predicted_principal_axis_alignment": alignment,
            "predicted_closing_axis_vertical_abs": vertical,
            "orientation_error": (1.0 - alignment) ** 2 + vertical**2,
        }
        evaluated[key] = evidence
        return evidence

    best: dict[str, Any] | None = None
    for flex in flex_values:
        for roll in roll_values:
            candidate = evaluate(flex, roll)
            if candidate is not None and (
                best is None or candidate["orientation_error"] < best["orientation_error"]
            ):
                best = candidate
    flex_step = (flex_max - flex_min) / 4.0
    roll_step = (roll_max - roll_min) / 8.0
    for _ in range(3):
        if best is None:
            break
        flex_step /= 2.0
        roll_step /= 2.0
        center_flex = best["selected_wrist_flex_rad"]
        center_roll = best["selected_wrist_roll_rad"]
        for flex in (center_flex - flex_step, center_flex, center_flex + flex_step):
            for roll in (center_roll - roll_step, center_roll, center_roll + roll_step):
                if not (flex_min <= flex <= flex_max and roll_min <= roll <= roll_max):
                    continue
                candidate = evaluate(flex, roll)
                if candidate is not None and candidate["orientation_error"] < best["orientation_error"]:
                    best = candidate
    alignment = (
        None if best is None else best["predicted_principal_axis_alignment"]
    )
    vertical = (
        None if best is None else best["predicted_closing_axis_vertical_abs"]
    )
    if alignment is None or alignment < 0.95 or vertical is None or vertical > 0.1:
        raise GraspGateFailure(
            f"No horizontal principal-axis wrist pose found: {best}",
            gate_margins={
                "principal_axis_alignment": _margin(alignment, 0.95, ">="),
                "closing_axis_vertical_abs": _margin(vertical, 0.1, "<="),
            },
        )
    best.update(
        {
            "sampled_wrist_flex_rad": request["wrist_flex_rad"],
            "sampled_wrist_roll_rad": request["wrist_roll_rad"],
            "wrist_orientation_evaluation_count": len(evaluated),
        }
    )
    return best


def _select_best_horizontal_principal_axis_wrist_pose(
    expert: CausalSortExpert,
    *,
    desired_midpoint: np.ndarray,
    request: dict[str, float],
    fixed_site: int,
    moving_site: int,
    object_rotation_world: np.ndarray,
) -> dict[str, Any]:
    valid: list[dict[str, Any]] = []
    failures: dict[str, str] = {}
    for axis_label, column in (("x", 0), ("y", 1)):
        try:
            evidence = _select_horizontal_principal_axis_wrist_pose(
                expert,
                desired_midpoint=desired_midpoint,
                request=request,
                fixed_site=fixed_site,
                moving_site=moving_site,
                object_axis_world=object_rotation_world[:, column],
            )
        except ValueError as exc:
            failures[axis_label] = str(exc)
            continue
        evidence["selected_object_principal_axis"] = axis_label
        valid.append(evidence)
    if not valid:
        raise ValueError(f"No horizontal anchor principal axis found: {failures}")
    selected = min(
        valid,
        key=lambda row: (
            row["orientation_error"],
            row["selected_object_principal_axis"],
        ),
    )
    selected["rejected_principal_axis_failures"] = failures
    return selected


def _valid_contact(frame: dict[str, Any], requirement: dict[str, Any]) -> bool:
    aggregate = frame["pad_contact_aggregate"]
    return bool(aggregate) and evaluate_antipodal_contact_witness(aggregate["strict_v2_witness"], requirement)["valid"]


def _gate_margins(
    result: dict[str, Any],
    *,
    minimum_hold_frames: int,
    minimum_span_m: float,
    minimum_normal_alignment: float,
    approach_motion_limit_m: float,
    position_tolerance_m: float,
) -> dict[str, dict[str, Any]]:
    """Report measured value, threshold, and signed margin for each gate."""

    return {
        "strict_hold_frame_count": _margin(
            result["hold_strict_v2_valid_frame_count"], minimum_hold_frames, ">="
        ),
        "representative_span_m": _margin(
            result["minimum_representative_span_m"], minimum_span_m, ">="
        ),
        "normal_alignment": _margin(
            result["best_normal_alignment"], minimum_normal_alignment, ">="
        ),
        "preclose_object_displacement_m": _margin(
            result["preclose_object_displacement_m"], approach_motion_limit_m, "<="
        ),
        "approach_position_residual_m": _margin(
            result["approach_position_residual_m"], position_tolerance_m, "<="
        ),
        "pregrasp_position_residual_m": _margin(
            result["pregrasp_position_residual_m"], position_tolerance_m, "<="
        ),
        "nonpad_contact_frame_count": _margin(
            result["nonpad_robot_object_contact_frame_count"], 0, "<="
        ),
    }


def _margin(measured: Any, threshold: float | int, comparison: str) -> dict[str, Any]:
    if measured is None:
        return {
            "measured": None,
            "threshold": threshold,
            "comparison": comparison,
            "margin": None,
            "passed": False,
        }
    if comparison == ">=":
        margin = float(measured) - float(threshold)
        passed = measured >= threshold
    else:
        margin = float(threshold) - float(measured)
        passed = measured <= threshold
    return {
        "measured": measured,
        "threshold": threshold,
        "comparison": comparison,
        "margin": margin,
        "passed": bool(passed),
    }


def _nonpad_contacts(expert: CausalSortExpert, object_body: int, pad_geoms: set[int]) -> list[str]:
    rows = []
    for index in range(expert.data.ncon):
        contact = expert.data.contact[index]
        geoms = (int(contact.geom1), int(contact.geom2))
        bodies = tuple(int(expert.model.geom_bodyid[geom]) for geom in geoms)
        if object_body not in bodies:
            continue
        other = geoms[1] if bodies[0] == object_body else geoms[0]
        other_body = int(expert.model.geom_bodyid[other])
        if other_body in expert.robot_body_ids and other not in pad_geoms:
            rows.append(expert.mujoco.mj_id2name(expert.model, expert.mujoco.mjtObj.mjOBJ_GEOM, other) or f"geom:{other}")
    return sorted(set(rows))


def _all_robot_object_contact_geoms(
    expert: CausalSortExpert,
    object_body: int,
) -> list[str]:
    rows = []
    for index in range(expert.data.ncon):
        contact = expert.data.contact[index]
        geoms = (int(contact.geom1), int(contact.geom2))
        bodies = tuple(int(expert.model.geom_bodyid[geom]) for geom in geoms)
        if object_body not in bodies:
            continue
        other = geoms[1] if bodies[0] == object_body else geoms[0]
        if int(expert.model.geom_bodyid[other]) in expert.robot_body_ids:
            rows.append(
                expert.mujoco.mj_id2name(
                    expert.model,
                    expert.mujoco.mjtObj.mjOBJ_GEOM,
                    other,
                )
                or f"geom:{other}"
            )
    return sorted(set(rows))


def _raw_pad_normal_forces(
    expert: CausalSortExpert,
    object_body: int,
    pad_geoms: set[int],
) -> list[float]:
    rows = []
    force = np.zeros(6, dtype=np.float64)
    for index in range(expert.data.ncon):
        contact = expert.data.contact[index]
        geoms = (int(contact.geom1), int(contact.geom2))
        bodies = tuple(int(expert.model.geom_bodyid[geom]) for geom in geoms)
        if object_body not in bodies:
            continue
        other = geoms[1] if bodies[0] == object_body else geoms[0]
        if other in pad_geoms:
            expert.mujoco.mj_contactForce(expert.model, expert.data, index, force)
            rows.append(round(float(force[0]), 9))
    return rows


def _rank(row: dict[str, Any]) -> tuple[Any, ...]:
    return (-row["hold_strict_v2_valid_frame_count"], -(row["minimum_representative_span_m"] or 0.0), -(row["best_normal_alignment"] or -1.0), row["maximum_contact_force_n"], row["preclose_object_displacement_m"], row["pregrasp_position_residual_m"])


def _halton(index: int) -> list[float]:
    return [_radical_inverse(index, base) for base in HALTON_BASES]


def _radical_inverse(index: int, base: int) -> float:
    value = 0.0
    factor = 1.0 / base
    while index:
        value += factor * (index % base)
        index //= base
        factor /= base
    return value


def _scale(value: float, bounds: tuple[float, float]) -> float:
    return bounds[0] + value * (bounds[1] - bounds[0])


def index_hash(request: dict[str, float]) -> int:
    return sum(round(abs(value) * 1000) for value in request.values()) % 1000
