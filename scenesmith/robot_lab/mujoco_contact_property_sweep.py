"""Simulation-only jaw contact-span and friction/compliance sweep."""

from __future__ import annotations

import math
import tempfile

from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.causal_sort_expert import (
    SIMULATION_HOME,
    CausalSortExpert,
    CausalSortExpertConfig,
)
from scenesmith.robot_lab.grasp_evidence import (
    KEYFRAME_IMAGE_SIZE,
    finalize_rendered_keyframes,
    retain_rendered_keyframe,
    validate_rendered_keyframes,
)
from scenesmith.robot_lab.mujoco_anchor_grasp import (
    OBJECT_ID,
    _add_anchor_speeds,
    _bind_anchor_geometry,
    _raw_frame,
    _scene,
)
from scenesmith.robot_lab.mujoco_export import (
    prepare_mujoco_so101_assets,
    render_mujoco_xml,
)


SCHEMA_VERSION = "scenesmith.mujoco_contact_property_sweep.v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_SEARCH = REPO_ROOT / "configurations/robot_lab/mujoco_grasp_contact_search.json"
FRICTION_GRID = (1.1, 2.0, 3.0, 5.0)
CONTACT_TIMECONST_GRID_S = (0.004, 0.008, 0.012)
HOLDOUT = (4.0, 0.01)
WRIST_ROLL_RAD = -1.5
PREGRASP_HEIGHT_M = 0.018
CLOSE_TARGET_RAD = -0.17
IMPACT_LIMIT_N = 5.0
REQUIRED_CLEARANCE_Z_M = 0.35


def build_mujoco_contact_property_sweep() -> dict[str, Any]:
    source = load_strict_json(SOURCE_SEARCH)
    verify_signed_payload(source, label="source MuJoCo grasp contact search")
    baseline = _run_variant(None, None)
    baseline_replay = _run_variant(None, None)
    if baseline != baseline_replay:
        raise ValueError("Baseline jaw contact-span replay is not deterministic")
    training = [
        _run_variant(friction, timeconst)["summary"]
        for friction in FRICTION_GRID
        for timeconst in CONTACT_TIMECONST_GRID_S
    ]
    successful = [candidate for candidate in training if _candidate_passes(candidate)]
    selected = (
        min(
            successful,
            key=lambda candidate: (
                candidate["maximum_contact_force_n"],
                -candidate["lift_hold_two_jaw_frames"],
                candidate["friction"],
                candidate["contact_timeconst_s"],
            ),
        )
        if successful
        else None
    )
    holdout = _run_variant(*HOLDOUT)["summary"]
    profile = baseline["contact_span_profile"]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "simulation_only_contact_span_and_property_sweep",
            "source_contact_search_identity_sha256": source["identity_sha256"],
            "pinned_mjcf": source["pinned_mjcf"],
            "object_id": OBJECT_ID,
            "anchor_dimensions_m": source["anchor_dimensions_m"],
            "anchor_mass_kg": source["anchor_mass_kg"],
            "physical_measurement_claimed": False,
            "fixed_pose": {
                "wrist_roll_rad": WRIST_ROLL_RAD,
                "pregrasp_height_m": PREGRASP_HEIGHT_M,
                "close_target_rad": CLOSE_TARGET_RAD,
            },
            "baseline_two_pass_exact_determinism": True,
            "baseline_summary": baseline["summary"],
            "contact_span_profile": profile,
            "contact_span_range_m": [
                min(row["jaw_contact_point_span_m"] for row in profile),
                max(row["jaw_contact_point_span_m"] for row in profile),
            ],
            "metric_profile_scope": "mujoco_contact_point_span_not_physical_aperture",
            "training_grid": {
                "friction": list(FRICTION_GRID),
                "contact_timeconst_s": list(CONTACT_TIMECONST_GRID_S),
                "candidate_count": len(training),
            },
            "training_candidates": training,
            "training_success_count": len(successful),
            "selected_training_candidate": selected,
            "holdout": {
                "friction": HOLDOUT[0],
                "contact_timeconst_s": HOLDOUT[1],
                "excluded_from_selection": True,
                "result": holdout,
            },
            "unassisted_mujoco_grasp_success": bool(selected)
            and _candidate_passes(holdout),
            "metric_physical_gripper_aperture_profile_complete": False,
            "physical_twin_qualified": False,
            "simulation_training_ready": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "local_capabilities": [
                "mujoco_contact_span_profile_observed",
                "bounded_contact_property_sweep_observed",
            ],
            "authority_not_granted": [
                "unassisted_mujoco_grasp_success",
                "strict_policy_grasp_success",
                "physical_gripper_aperture_calibrated",
                "physical_twin_qualified",
                "simulation_training_ready",
                "physical_actuation",
            ],
        }
    )


def verify_mujoco_contact_property_sweep(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="MuJoCo contact property sweep")
    grid = payload.get("training_grid", {})
    if grid.get("candidate_count") != len(payload.get("training_candidates", [])):
        raise ValueError("MuJoCo contact property sweep candidate count drifted")
    if not payload.get("baseline_two_pass_exact_determinism"):
        raise ValueError("MuJoCo contact property baseline is not deterministic")
    if not payload.get("holdout", {}).get("excluded_from_selection"):
        raise ValueError("MuJoCo contact property holdout leaked into selection")
    keyframe_phases = (
        "pregrasp",
        "close",
        "grasp_hold",
        "unassisted_lift_hold",
    )
    validate_rendered_keyframes(
        payload.get("baseline_summary", {}).get("rendered_keyframes"),
        phases=keyframe_phases,
    )
    for candidate in payload.get("training_candidates", []):
        validate_rendered_keyframes(
            candidate.get("rendered_keyframes"), phases=keyframe_phases
        )
    validate_rendered_keyframes(
        payload.get("holdout", {}).get("result", {}).get("rendered_keyframes"),
        phases=keyframe_phases,
    )


def _run_variant(
    friction: float | None,
    contact_timeconst_s: float | None,
) -> dict[str, Any]:
    scene = _scene()
    raw_frames: list[dict[str, Any]] = []
    rendered_keyframes: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="scenesmith-contact-property-") as directory:
        root = Path(directory)
        prepare_mujoco_so101_assets(root, scene.robot.base_position_m)
        xml_path = root / "scene.xml"
        xml_path.write_text(render_mujoco_xml(scene), encoding="utf-8")
        _bind_anchor_geometry(xml_path)
        expert: CausalSortExpert | None = None

        def retain(frame: dict[str, Any], _images: dict[str, np.ndarray]) -> None:
            if expert is None:
                raise RuntimeError("MuJoCo contact-property probe was not initialized")
            retained = _raw_frame(expert, frame)
            retained["jaw_contact_geometry"] = _jaw_contact_geometry(expert)
            raw_frames.append(retained)
            retain_rendered_keyframe(
                rendered_keyframes,
                frame,
                _images,
                phases=(
                    "pregrasp",
                    "close",
                    "grasp_hold",
                    "unassisted_lift_hold",
                ),
                image_size=KEYFRAME_IMAGE_SIZE,
            )

        expert = CausalSortExpert(
            scene,
            xml_path,
            seed=901,
            frame_sink=retain,
            config=CausalSortExpertConfig(
                image_size=KEYFRAME_IMAGE_SIZE,
                capture_images=True,
            ),
        )
        if friction is not None and contact_timeconst_s is not None:
            _apply_contact_properties(expert, friction, contact_timeconst_s)
        try:
            home = np.asarray(SIMULATION_HOME, dtype=np.float64).copy()
            home[4] = WRIST_ROLL_RAD
            expert.data.qpos[: expert.model.nu] = home
            expert.data.ctrl[: expert.model.nu] = home
            expert.mujoco.mj_forward(expert.model, expert.data)
            for _ in range(max(1, round(0.35 / expert.model.opt.timestep))):
                expert.mujoco.mj_step(expert.model, expert.data)
            expert._hold("settle", 4)
            anchor = expert._body_position(OBJECT_ID)
            expert._move_site(
                "approach",
                anchor + np.asarray([0.0, 0.0, 0.06]),
                16,
                1.6,
            )
            expert._move_site(
                "pregrasp",
                anchor + np.asarray([0.0, 0.0, PREGRASP_HEIGHT_M]),
                24,
                1.6,
            )
            expert._hold("pregrasp_hold", 4)
            expert._move_gripper("close", CLOSE_TARGET_RAD, 40)
            expert._hold("grasp_hold", 8)
            target = expert.data.site_xpos[expert.gripper_site_id].copy()
            expert._move_site(
                "unassisted_lift",
                target + np.asarray([0.0, 0.0, 0.05]),
                40,
                CLOSE_TARGET_RAD,
            )
            expert._hold("unassisted_lift_hold", 12)
        finally:
            expert.close()
    _add_anchor_speeds(raw_frames)
    summary = _summary(raw_frames, friction, contact_timeconst_s)
    summary["rendered_keyframes"] = finalize_rendered_keyframes(
        rendered_keyframes,
        phases=("pregrasp", "close", "grasp_hold", "unassisted_lift_hold"),
    )
    return {
        "summary": summary,
        "contact_span_profile": _contact_span_profile(raw_frames),
    }


def _apply_contact_properties(
    expert: CausalSortExpert,
    friction: float,
    contact_timeconst_s: float,
) -> None:
    moving_jaw = expert._id(expert.mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
    bodies = {
        expert.cube_body_ids[OBJECT_ID],
        expert.gripper_body_id,
        moving_jaw,
    }
    for geom_id, body_id in enumerate(expert.model.geom_bodyid):
        if int(body_id) not in bodies:
            continue
        expert.model.geom_friction[geom_id] = [friction, 0.02, 0.002]
        expert.model.geom_solref[geom_id] = [contact_timeconst_s, 1.0]


def _jaw_contact_geometry(expert: CausalSortExpert) -> list[dict[str, Any]]:
    data = expert.data
    model = expert.model
    cube_id = expert.cube_body_ids[OBJECT_ID]
    moving_jaw = expert._id(
        expert.mujoco.mjtObj.mjOBJ_BODY,
        "moving_jaw_so101_v1",
    )
    allowed = {expert.gripper_body_id, moving_jaw}
    rows = []
    for index in range(data.ncon):
        contact = data.contact[index]
        body1 = int(model.geom_bodyid[contact.geom1])
        body2 = int(model.geom_bodyid[contact.geom2])
        if cube_id not in {body1, body2}:
            continue
        other = body2 if body1 == cube_id else body1
        if other not in allowed:
            continue
        rows.append(
            {
                "jaw_body": expert._body_name(other),
                "position_m": [round(float(value), 9) for value in contact.pos],
                "normal": [round(float(value), 9) for value in contact.frame[:3]],
            }
        )
    return rows


def _contact_span_profile(raw_frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for frame in raw_frames:
        fixed = [
            row["position_m"]
            for row in frame["jaw_contact_geometry"]
            if row["jaw_body"] == "gripper"
        ]
        moving = [
            row["position_m"]
            for row in frame["jaw_contact_geometry"]
            if row["jaw_body"] == "moving_jaw_so101_v1"
        ]
        if not fixed or not moving or frame["phase"] not in {"close", "grasp_hold"}:
            continue
        span = min(_distance(left, right) for left in fixed for right in moving)
        rows.append(
            {
                "frame_index": frame["frame_index"],
                "phase": frame["phase"],
                "gripper_percent": frame["state"][-1],
                "jaw_contact_point_span_m": round(span, 9),
                "contact_force_n_max": frame["robot_anchor_contact_force_n_max"],
            }
        )
    if not rows:
        raise ValueError("Baseline produced no simultaneous jaw contact span")
    return rows


def _summary(
    raw_frames: list[dict[str, Any]],
    friction: float | None,
    contact_timeconst_s: float | None,
) -> dict[str, Any]:
    lift_hold = [frame for frame in raw_frames if frame["phase"] == "unassisted_lift_hold"]
    object_z = [frame["cube_positions_m"][OBJECT_ID][2] for frame in raw_frames]
    return {
        "friction": friction,
        "contact_timeconst_s": contact_timeconst_s,
        "maximum_contact_force_n": max(
            frame["robot_anchor_contact_force_n_max"] for frame in raw_frames
        ),
        "lift_hold_two_jaw_frames": sum(_has_two_jaw_contact(frame) for frame in lift_hold),
        "maximum_object_z_m": max(object_z),
        "final_object_z_m": object_z[-1],
        "unassisted_lift_clearance_maintained": lift_hold[-1][
            "cube_positions_m"
        ][OBJECT_ID][2]
        >= REQUIRED_CLEARANCE_Z_M,
        "contact_gated_assist_ever_active": any(
            frame["grasp_assists_active"] for frame in raw_frames
        ),
    }


def _candidate_passes(candidate: dict[str, Any]) -> bool:
    return (
        candidate["maximum_contact_force_n"] <= IMPACT_LIMIT_N
        and candidate["lift_hold_two_jaw_frames"] == 12
        and candidate["unassisted_lift_clearance_maintained"]
        and not candidate["contact_gated_assist_ever_active"]
    )


def _has_two_jaw_contact(frame: dict[str, Any]) -> bool:
    bodies = {row["jaw_body"] for row in frame["jaw_contact_geometry"]}
    return {"gripper", "moving_jaw_so101_v1"}.issubset(bodies)


def _distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)))
