"""Finite low-impact two-jaw contact search for the nominal anchor cousin."""

from __future__ import annotations

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


SCHEMA_VERSION = "scenesmith.mujoco_grasp_contact_search.v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ATTEMPT = REPO_ROOT / "configurations/robot_lab/mujoco_anchor_grasp_attempt.json"
WRIST_ROLL_GRID_RAD = (-1.5, -1.0, 1.0, 1.5, 2.0)
PREGRASP_HEIGHT_GRID_M = (0.018, 0.022, 0.026, 0.03)
CLOSE_TARGET_RAD = -0.17
IMPACT_LIMIT_N = 5.0


def build_mujoco_grasp_contact_search() -> dict[str, Any]:
    """Run the finite grid and selected unassisted lift twice exactly."""

    result = _run_search()
    source_attempt = load_strict_json(SOURCE_ATTEMPT)
    verify_signed_payload(source_attempt, label="source MuJoCo anchor grasp attempt")
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "evidence_mode": "finite_mujoco_two_jaw_contact_search",
            "object_id": OBJECT_ID,
            "source_anchor_attempt_identity_sha256": source_attempt["identity_sha256"],
            "pinned_mjcf": source_attempt["pinned_mjcf"],
            "anchor_dimensions_m": source_attempt["anchor_dimensions_m"],
            "anchor_mass_kg": source_attempt["anchor_mass_kg"],
            "physical_measurement_claimed": False,
            "wrist_roll_grid_rad": list(WRIST_ROLL_GRID_RAD),
            "pregrasp_height_grid_m": list(PREGRASP_HEIGHT_GRID_M),
            "close_target_rad": CLOSE_TARGET_RAD,
            "impact_limit_n": IMPACT_LIMIT_N,
            "selected_validation_two_pass_exact_determinism": True,
            "candidate_count": len(result["candidates"]),
            "candidates": result["candidates"],
            "selected_candidate": result["selected_candidate"],
            "selected_unassisted_validation": result[
                "selected_unassisted_validation"
            ],
            "metric_gripper_aperture_profile_complete": False,
            "unassisted_mujoco_grasp_success": False,
            "strict_grasp_success": False,
            "physical_twin_qualified": False,
            "simulation_training_ready": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "local_capabilities": [
                "low_impact_two_jaw_mujoco_contact_candidate_observed"
            ],
            "authority_not_granted": [
                "unassisted_mujoco_grasp_success",
                "strict_policy_grasp_success",
                "metric_gripper_aperture_profile_complete",
                "physical_twin_qualified",
                "simulation_training_ready",
                "physical_actuation",
            ],
        }
    )


def verify_mujoco_grasp_contact_search(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="MuJoCo grasp contact search")
    if payload.get("candidate_count") != len(payload.get("candidates", [])):
        raise ValueError("MuJoCo grasp contact search candidate count drifted")
    if not payload.get("selected_validation_two_pass_exact_determinism"):
        raise ValueError("Selected MuJoCo grasp validation is not deterministic")


def _run_search() -> dict[str, Any]:
    candidates = [
        _run_probe(roll, height, include_lift=False)["summary"]
        for roll in WRIST_ROLL_GRID_RAD
        for height in PREGRASP_HEIGHT_GRID_M
    ]
    eligible = [
        candidate
        for candidate in candidates
        if candidate["maximum_contact_force_n"] <= IMPACT_LIMIT_N
        and candidate["close_two_jaw_frames"] > 0
        and candidate["hold_two_jaw_frames"] > 0
    ]
    if not eligible:
        raise ValueError("Finite MuJoCo grid found no low-impact two-jaw candidate")
    selected = min(
        eligible,
        key=lambda candidate: (
            -candidate["hold_two_jaw_frames"],
            -candidate["close_two_jaw_frames"],
            candidate["maximum_contact_force_n"],
            candidate["wrist_roll_rad"],
            candidate["pregrasp_height_m"],
        ),
    )
    validation = _run_probe(
        selected["wrist_roll_rad"],
        selected["pregrasp_height_m"],
        include_lift=True,
    )
    validation_replay = _run_probe(
        selected["wrist_roll_rad"],
        selected["pregrasp_height_m"],
        include_lift=True,
    )
    if validation != validation_replay:
        raise ValueError("Selected MuJoCo grasp validation is not deterministic")
    return {
        "candidates": candidates,
        "selected_candidate": selected,
        "selected_unassisted_validation": validation,
    }


def _run_probe(
    wrist_roll_rad: float,
    pregrasp_height_m: float,
    *,
    include_lift: bool,
) -> dict[str, Any]:
    scene = _scene()
    raw_frames: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="scenesmith-contact-search-") as directory:
        root = Path(directory)
        prepare_mujoco_so101_assets(root, scene.robot.base_position_m)
        xml_path = root / "scene.xml"
        xml_path.write_text(render_mujoco_xml(scene), encoding="utf-8")
        _bind_anchor_geometry(xml_path)
        expert: CausalSortExpert | None = None

        def retain(frame: dict[str, Any], _images: dict[str, np.ndarray]) -> None:
            if expert is None:
                raise RuntimeError("MuJoCo contact probe was not initialized")
            raw_frames.append(_raw_frame(expert, frame))

        expert = CausalSortExpert(
            scene,
            xml_path,
            seed=901,
            frame_sink=retain,
            config=CausalSortExpertConfig(image_size=16, capture_images=False),
        )
        try:
            home = np.asarray(SIMULATION_HOME, dtype=np.float64).copy()
            home[4] = wrist_roll_rad
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
                anchor + np.asarray([0.0, 0.0, pregrasp_height_m]),
                24,
                1.6,
            )
            expert._hold("pregrasp_hold", 4)
            expert._move_gripper("close", CLOSE_TARGET_RAD, 40)
            expert._hold("grasp_hold", 8)
            if include_lift:
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
    summary = _summarize_probe(
        raw_frames,
        wrist_roll_rad=wrist_roll_rad,
        pregrasp_height_m=pregrasp_height_m,
    )
    return {
        "summary": summary,
        "raw_frame_count": len(raw_frames),
        "raw_frames": raw_frames if include_lift else [],
        "contact_gated_assist_ever_active": any(
            frame["grasp_assists_active"] for frame in raw_frames
        ),
    }


def _summarize_probe(
    raw_frames: list[dict[str, Any]],
    *,
    wrist_roll_rad: float,
    pregrasp_height_m: float,
) -> dict[str, Any]:
    close = [frame for frame in raw_frames if frame["phase"] == "close"]
    hold = [frame for frame in raw_frames if frame["phase"] == "grasp_hold"]
    lift = [frame for frame in raw_frames if frame["phase"] == "unassisted_lift"]
    lift_hold = [
        frame for frame in raw_frames if frame["phase"] == "unassisted_lift_hold"
    ]
    two_jaw = [frame for frame in raw_frames if _has_two_jaw_contact(frame)]
    contact_values = [
        frame["state"][-1]
        for frame in two_jaw
        if frame["phase"] in {"close", "grasp_hold"}
    ]
    object_z = [frame["cube_positions_m"][OBJECT_ID][2] for frame in raw_frames]
    return {
        "wrist_roll_rad": wrist_roll_rad,
        "pregrasp_height_m": pregrasp_height_m,
        "maximum_contact_force_n": max(
            frame["robot_anchor_contact_force_n_max"] for frame in raw_frames
        ),
        "close_two_jaw_frames": sum(_has_two_jaw_contact(frame) for frame in close),
        "hold_two_jaw_frames": sum(_has_two_jaw_contact(frame) for frame in hold),
        "lift_two_jaw_frames": sum(_has_two_jaw_contact(frame) for frame in lift),
        "lift_hold_two_jaw_frames": sum(
            _has_two_jaw_contact(frame) for frame in lift_hold
        ),
        "two_jaw_contact_gripper_percent_range": (
            [min(contact_values), max(contact_values)] if contact_values else None
        ),
        "maximum_object_z_m": max(object_z),
        "final_object_z_m": object_z[-1],
        "unassisted_lift_clearance_maintained": bool(lift_hold)
        and lift_hold[-1]["cube_positions_m"][OBJECT_ID][2] >= 0.35,
    }


def _has_two_jaw_contact(frame: dict[str, Any]) -> bool:
    bodies = {
        contact["body1"] if contact["body1"] != OBJECT_ID else contact["body2"]
        for contact in frame["robot_cube_contacts"]
    }
    return {"gripper", "moving_jaw_so101_v1"}.issubset(bodies)
