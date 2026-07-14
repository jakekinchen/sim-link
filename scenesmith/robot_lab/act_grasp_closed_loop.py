"""Strict, bounded closed-loop ACT evaluation on the held-out grasp scene."""

from __future__ import annotations

import hashlib
import json
import math
import tempfile

from pathlib import Path
from typing import Any, Callable

import numpy as np

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.causal_sort_expert import CausalSortExpert, CausalSortExpertConfig, SIMULATION_HOME
from scenesmith.robot_lab.geometry_first_grasp_search import (
    _all_robot_object_contact_geoms,
    _nonpad_contacts,
    _valid_contact,
)
from scenesmith.robot_lab.grasp_evidence import finalize_rendered_keyframes, retain_rendered_keyframe
from scenesmith.robot_lab.grasp_pose_solver import apply_and_read_object_yaw
from scenesmith.robot_lab.gripper_contact_semantics import (
    FIXED_PAD_SITE,
    MOVING_PAD_SITE,
    aggregate_pad_contacts,
    apply_explicit_pad_proxy_contact_model,
    compiled_pad_geom_roles,
    extract_pad_contacts,
)
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID, _bind_anchor_geometry, _raw_frame, _scene
from scenesmith.robot_lab.mujoco_export import prepare_mujoco_so101_assets, render_mujoco_xml
from scenesmith.robot_lab.scripted_grasp_episode_generation import BASE_ANCHOR_POSITION_M, EPISODE_SPECS
from scenesmith.robot_lab.strict_grasp import strict_grasp_spec_v2


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "scenesmith.t20_2_act_closed_loop.v1"
GRASP_PATH = REPO_ROOT / "configurations/robot_lab/geometry_derived_unilateral_grasp.json"
PHASE_PLAN = (
    ("approach", 14),
    ("pregrasp", 18),
    ("close", 36),
    ("grasp_hold", 8),
    ("unassisted_lift", 24),
    ("unsupported_lift_hold", 12),
    ("recording_stable_hold", 64),
    ("lower", 24),
    ("release", 12),
    ("release_settle", 8),
    ("retreat", 24),
)
ROLLOUT_FRAMES = sum(count for _, count in PHASE_PLAN)
Policy = Callable[[dict[str, np.ndarray], np.ndarray], np.ndarray]
FrameObserver = Callable[[dict[str, Any]], None]


def phase_for_frame(frame_index: int) -> str:
    if isinstance(frame_index, bool) or not 0 <= frame_index < ROLLOUT_FRAMES:
        raise ValueError("Closed-loop frame index is outside the bounded phase plan")
    cursor = 0
    for phase, count in PHASE_PLAN:
        cursor += count
        if frame_index < cursor:
            return phase
    raise AssertionError("unreachable")


def run_act_grasp_closed_loop(
    policy: Policy,
    *,
    checkpoint_sha256: str,
    training_run_summary_sha256: str,
    seed: int = 2,
) -> dict[str, Any]:
    """Run exactly one held-out ACT rollout with policy-owned controls."""

    return run_policy_grasp_closed_loop(
        policy,
        checkpoint_sha256=checkpoint_sha256,
        training_run_summary_sha256=training_run_summary_sha256,
        seed=seed,
        schema_version=SCHEMA_VERSION,
        task_id="T20.2",
        evidence_mode="held_out_seed_closed_loop_act_mujoco",
        policy_label="ACT",
    )


def run_policy_grasp_closed_loop(
    policy: Policy,
    *,
    checkpoint_sha256: str,
    training_run_summary_sha256: str,
    seed: int,
    schema_version: str,
    task_id: str,
    evidence_mode: str,
    policy_label: str,
    frame_observer: FrameObserver | None = None,
) -> dict[str, Any]:
    """Run one bounded held-out rollout for a named policy evidence contract."""

    for name, value in {
        "schema_version": schema_version,
        "task_id": task_id,
        "evidence_mode": evidence_mode,
        "policy_label": policy_label,
    }.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Closed-loop {name} must be a non-empty string")

    spec = next((dict(item) for item in EPISODE_SPECS if item["seed"] == seed), None)
    if spec is None:
        raise ValueError("Closed-loop seed is not in the fixed episode design")
    grasp = load_strict_json(GRASP_PATH)
    request = dict(grasp["trajectory"]["request"])
    request["object_yaw_rad"] += spec["yaw_offset_rad"]
    offset_x, offset_y = spec["planar_offset_m"]
    initial_position = (
        BASE_ANCHOR_POSITION_M[0] + offset_x,
        BASE_ANCHOR_POSITION_M[1] + offset_y,
        BASE_ANCHOR_POSITION_M[2],
    )
    scene = _scene(initial_position_m=initial_position)
    frames: list[dict[str, Any]] = []
    rendered: dict[str, dict[str, Any]] = {}
    requested_actions: list[list[float]] = []
    applied_actions: list[list[float]] = []
    projected_frames: list[int] = []
    pending_requested: np.ndarray | None = None

    with tempfile.TemporaryDirectory(prefix="scenesmith-policy-grasp-") as directory:
        root = Path(directory)
        robot_xml = prepare_mujoco_so101_assets(root, scene.robot.base_position_m)
        apply_explicit_pad_proxy_contact_model(robot_xml)
        scene_xml = root / "scene.xml"
        scene_xml.write_text(render_mujoco_xml(scene), encoding="utf-8")
        _bind_anchor_geometry(scene_xml)
        expert: CausalSortExpert | None = None
        pad_roles: dict[int, str] = {}
        fixed_site = moving_site = object_body = -1

        def retain(frame: dict[str, Any], images: dict[str, np.ndarray]) -> None:
            assert expert is not None and pending_requested is not None
            row = _raw_frame(expert, frame)
            contacts = extract_pad_contacts(
                expert.mujoco,
                expert.model,
                expert.data,
                object_body_id=object_body,
                pad_geom_roles=pad_roles,
            )
            rotation = np.asarray(expert.data.xmat[object_body]).reshape(3, 3)
            closing_world = expert.data.site_xpos[moving_site] - expert.data.site_xpos[fixed_site]
            closing_object = rotation.T @ closing_world
            row["pad_contacts"] = contacts
            row["pad_contact_aggregate"] = aggregate_pad_contacts(contacts, closing_object.tolist()) if contacts else None
            row["nonpad_robot_object_contacts"] = _nonpad_contacts(expert, object_body, set(pad_roles))
            row["all_robot_object_contact_geoms"] = _all_robot_object_contact_geoms(expert, object_body)
            row["policy_requested_action"] = pending_requested.astype(float).tolist()
            frames.append(row)
            if frame_observer is not None:
                frame_observer(json.loads(json.dumps(row)))
            retain_rendered_keyframe(rendered, frame, images)

        expert = CausalSortExpert(
            scene,
            scene_xml,
            seed=1701 + seed,
            frame_sink=retain,
            config=CausalSortExpertConfig(image_size=256, capture_images=True),
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
            apply_and_read_object_yaw(
                expert.mujoco,
                expert.model,
                expert.data,
                object_joint_name=f"{OBJECT_ID}_free",
                object_body_name=OBJECT_ID,
                yaw_rad=request["object_yaw_rad"],
            )
            settle_seconds = float(grasp["trajectory"]["post_yaw_settle_seconds"])
            for _ in range(round(settle_seconds / expert.model.opt.timestep)):
                expert.mujoco.mj_step(expert.model, expert.data)
            anchor_start = expert.data.xpos[object_body].copy()
            ctrl_min = expert.model.actuator_ctrlrange[: expert.model.nu, 0]
            ctrl_max = expert.model.actuator_ctrlrange[: expert.model.nu, 1]
            for frame_index in range(ROLLOUT_FRAMES):
                images = {
                    "top": expert._capture("cam1_overhead", 0),
                    "wrist": expert._capture("cam2_wrist", 1),
                }
                state = np.concatenate(
                    [
                        expert.data.qpos[: expert.model.nu],
                        expert.data.qvel[: expert.model.nu],
                    ]
                ).astype(np.float32)
                pending_requested = np.asarray(policy(images, state), dtype=np.float64)
                if pending_requested.shape != (expert.model.nu,) or not np.isfinite(pending_requested).all():
                    raise ValueError(f"{policy_label} policy emitted a non-finite or wrong-shaped action")
                applied = np.clip(pending_requested, ctrl_min, ctrl_max)
                if not np.array_equal(applied, pending_requested):
                    projected_frames.append(frame_index)
                requested_actions.append(pending_requested.astype(float).tolist())
                applied_actions.append(applied.astype(float).tolist())
                expert._record_and_step(phase_for_frame(frame_index), applied)
            anchor_final = expert.data.xpos[object_body].copy()
        finally:
            expert.close()

    evidence = _evaluate(frames, anchor_start=anchor_start, anchor_final=anchor_final, projected_frames=projected_frames)
    action_bytes = json.dumps(requested_actions, separators=(",", ":"), allow_nan=False).encode()
    return sign_payload(
        {
            "schema_version": schema_version,
            "task_id": task_id,
            "evidence_mode": evidence_mode,
            "policy_label": policy_label,
            "seed": seed,
            "source_episode_spec": spec,
            "source_grasp_identity_sha256": grasp["identity_sha256"],
            "checkpoint_sha256": checkpoint_sha256,
            "training_run_summary_sha256": training_run_summary_sha256,
            "frame_count": len(frames),
            "phase_frame_counts": {phase: count for phase, count in PHASE_PLAN},
            "phase_schedule_source": "held_out_scripted_episode_horizon_only_not_semantic_success",
            "policy_action_sequence_sha256": hashlib.sha256(action_bytes).hexdigest(),
            "policy_requested_action_first": requested_actions[0],
            "policy_requested_action_last": requested_actions[-1],
            "applied_action_first": applied_actions[0],
            "applied_action_last": applied_actions[-1],
            "projected_action_frame_count": len(projected_frames),
            "projected_action_frame_indices": projected_frames,
            "rendered_keyframes": finalize_rendered_keyframes(rendered),
            **evidence,
            "policy_controls_owned_all_frames": True,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "simulation_policy_accepted": False,
        }
    )


def _evaluate(
    frames: list[dict[str, Any]],
    *,
    anchor_start: np.ndarray,
    anchor_final: np.ndarray,
    projected_frames: list[int],
) -> dict[str, Any]:
    requirement = strict_grasp_spec_v2()["antipodal_contact_requirement"]
    by_phase = {phase: [row for row in frames if row["phase"] == phase] for phase, _ in PHASE_PLAN}
    valid_counts = {
        phase: sum(_valid_contact(row, requirement) for row in rows)
        for phase, rows in by_phase.items()
    }
    all_aggregates = [row["pad_contact_aggregate"] for row in frames if row["pad_contact_aggregate"]]
    best_alignment = max(
        (
            min(value["fixed_normal_span_alignment"], value["moving_normal_span_alignment"])
            for value in all_aggregates
        ),
        default=None,
    )
    min_span = min((value["euclidean_span_m"] for value in all_aggregates), default=None)
    maximum_z = max(row["cube_positions_m"][OBJECT_ID][2] for row in frames)
    support_free_hold = sum(not row["anchor_support_contacts"] for row in by_phase["unsupported_lift_hold"])
    nonpad_count = sum(bool(row["nonpad_robot_object_contacts"]) for row in frames)
    active_assist_count = sum(bool(row["grasp_assists_active"]) for row in frames)
    release_clear = bool(by_phase["release_settle"]) and not by_phase["release_settle"][-1]["all_robot_object_contact_geoms"]
    retreat_clear = bool(by_phase["retreat"]) and not by_phase["retreat"][-1]["all_robot_object_contact_geoms"]
    measurements = {
        "grasp_hold_strict_v2": (valid_counts["grasp_hold"], 8, ">="),
        "unassisted_lift_strict_v2": (valid_counts["unassisted_lift"], 24, ">="),
        "unsupported_lift_hold_strict_v2": (valid_counts["unsupported_lift_hold"], 12, ">="),
        "recording_stable_hold_strict_v2": (valid_counts["recording_stable_hold"], 64, ">="),
        "lower_strict_v2": (valid_counts["lower"], 24, ">="),
        "unsupported_lift_support_free": (support_free_hold, 12, ">="),
        "representative_span_m": (min_span, requirement["minimum_contact_span_m"], ">="),
        "normal_alignment": (best_alignment, requirement["minimum_contact_axis_alignment"], ">="),
        "lift_displacement_m": (maximum_z - float(anchor_start[2]), 0.025, ">="),
        "projected_action_frames": (len(projected_frames), 0, "=="),
        "active_assist_frames": (active_assist_count, 0, "=="),
        "nonpad_contact_frames": (nonpad_count, 0, "=="),
        "release_final_contact_clear": (int(release_clear), 1, "=="),
        "retreat_final_contact_clear": (int(retreat_clear), 1, "=="),
    }
    margins = {name: _margin(*values) for name, values in measurements.items()}
    strict_success = all(item["passed"] for item in margins.values())
    if strict_success:
        terminal = "strict_success"
    elif maximum_z - float(anchor_start[2]) >= 0.025:
        terminal = "lifted_without_strict_cycle"
    elif any(valid_counts.values()):
        terminal = "contact_without_strict_lift"
    else:
        terminal = "no_strict_grasp_contact"
    return {
        "terminal_outcome": terminal,
        "simulation_semantic_strict_success": strict_success,
        "strict_v2_valid_frame_counts": valid_counts,
        "gate_margins": margins,
        "failed_gate_margins": [
            {"gate": name, **value} for name, value in margins.items() if not value["passed"]
        ],
        "anchor_start_position_m": np.asarray(anchor_start).astype(float).tolist(),
        "anchor_final_position_m": np.asarray(anchor_final).astype(float).tolist(),
        "maximum_anchor_lift_m": maximum_z - float(anchor_start[2]),
        "active_assist_frame_count": active_assist_count,
    }


def _margin(measured: Any, threshold: float | int, comparison: str) -> dict[str, Any]:
    if measured is None or isinstance(measured, float) and not math.isfinite(measured):
        return {"measured": measured, "threshold": threshold, "comparison": comparison, "margin": None, "passed": False}
    if comparison == ">=":
        margin = float(measured) - float(threshold)
        passed = margin >= 0.0
    elif comparison == "==":
        margin = -abs(float(measured) - float(threshold))
        passed = measured == threshold
    else:
        raise ValueError("Unsupported gate comparison")
    if margin == 0:
        margin = 0.0
    return {"measured": measured, "threshold": threshold, "comparison": comparison, "margin": margin, "passed": passed}
