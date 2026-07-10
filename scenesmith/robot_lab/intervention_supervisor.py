"""Domain-randomized SceneSmith SO-101 intervention episode runner."""

from __future__ import annotations

import json
import os
import struct
import time
import zlib

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.desk_sort import export_so101_desk_sort_scene, write_json
from scenesmith.robot_lab.domain_randomization import apply_mujoco_randomization, randomize_scene
from scenesmith.robot_lab.intervention_control import (
    DeadmanSignal,
    InterventionArbiter,
    InterventionControlStore,
)
from scenesmith.robot_lab.leader_arm_bridge import CorrectionSource, make_correction_source
from scenesmith.robot_lab.policy_action_source import HttpPolicyActionConfig, HttpPolicyActionSource
from scenesmith.robot_lab.scoring import score_cube_sort
from scenesmith.robot_lab.spec import RobotLabScene, RobotLabTray


REPO_ROOT = Path(__file__).resolve().parents[2]
CAMERAS = {
    "base": "cam0_side",
    "overhead": "cam1_overhead",
    "wrist": "cam2_wrist",
}
CLOSED_GRIPPER_CONTROL = -0.17453
NEURAL_SORT_TASK = "Sort each colored block onto the plate of the matching color."


@dataclass(frozen=True)
class EpisodeRunConfig:
    control_hz: int = 10
    scripted_steps_per_waypoint: int = 3
    observation_width: int = 224
    observation_height: int = 224
    deadman_timeout_s: float = 0.55
    intervention_wait_timeout_s: float = 20.0
    intervention_run_timeout_s: float = 45.0
    grasp_assist_mode: str = "policy_gripper"
    contact_reflex_max_hold_steps: int = 300
    contact_reflex_post_place_hold_steps: int = 10
    contact_reflex_post_place_lift_steps: int = 25
    contact_reflex_post_place_retreat_steps: int = 35
    neural_search_retry_steps: int = 1000
    precontact_stall_steps: int = 240
    precontact_min_progress_m: float = 0.005
    precontact_contact_distance_m: float = 0.05
    realtime: bool = False


@dataclass
class NeuralGraspAssistState:
    active_cube: str | None = None
    equality_id: int | None = None
    activation_frame: int | None = None
    cooldown_until_frame: int = 0
    post_place_start_frame: int | None = None
    post_place_start_control: tuple[float, ...] | None = None
    post_place_lift_control: tuple[float, ...] | None = None
    post_place_cube: str | None = None
    post_place_controller_frames: int = 0
    tray_transfer_start_frame: int | None = None
    tray_transfer_start_control: tuple[float, ...] | None = None
    tray_transfer_lift_control: tuple[float, ...] | None = None
    tray_transfer_carry_control: tuple[float, ...] | None = None
    tray_transfer_place_control: tuple[float, ...] | None = None
    tray_transfer_controller_frames: int = 0
    completed_cubes: set[str] = field(default_factory=set)
    policy_reset_pending: bool = False
    policy_reset_count: int = 0
    last_policy_reset_frame: int = 0
    search_retries_since_place: int = 0
    recovery_pick_start_frame: int | None = None
    recovery_pick_start_control: tuple[float, ...] | None = None
    recovery_pick_approach_control: tuple[float, ...] | None = None
    recovery_pick_descend_control: tuple[float, ...] | None = None
    recovery_pick_cube: str | None = None
    recovery_pick_controller_frames: int = 0
    events: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if self.events is None:
            self.events = []


@dataclass
class ApproachProgressMonitor:
    stall_steps: int
    min_progress_m: float
    contact_distance_m: float
    best_distance_m: float = float("inf")
    last_progress_frame: int = 0
    last_trigger_frame: int | None = None

    def __post_init__(self) -> None:
        if self.stall_steps <= 0:
            raise ValueError("Pre-contact stall steps must be positive")
        if self.min_progress_m <= 0 or self.contact_distance_m <= 0:
            raise ValueError("Pre-contact distance thresholds must be positive")

    def update(
        self,
        *,
        frame_index: int,
        gripper_position_m: list[float],
        cube_positions_m: dict[str, list[float]],
        has_contact: bool,
        controller_active: bool,
    ) -> dict[str, Any] | None:
        if controller_active or has_contact or not cube_positions_m:
            self.reset(frame_index)
            return None
        gripper = np.asarray(gripper_position_m, dtype=np.float64)
        distances = {
            name: float(np.linalg.norm(gripper - np.asarray(position, dtype=np.float64)))
            for name, position in cube_positions_m.items()
        }
        cube_name, distance = min(distances.items(), key=lambda item: (item[1], item[0]))
        if not np.isfinite(self.best_distance_m):
            self.best_distance_m = distance
            self.last_progress_frame = frame_index
            return None
        if self.best_distance_m - distance >= self.min_progress_m:
            self.best_distance_m = distance
            self.last_progress_frame = frame_index
            return None
        if distance <= self.contact_distance_m:
            return None
        if frame_index - self.last_progress_frame < self.stall_steps:
            return None
        self.best_distance_m = distance
        self.last_progress_frame = frame_index
        self.last_trigger_frame = frame_index
        return {
            "kind": "policy_precontact_stall",
            "frame_index": frame_index,
            "cube": cube_name,
            "distance_m": round(distance, 6),
            "stall_steps": self.stall_steps,
            "min_progress_m": self.min_progress_m,
            "contact_gated": False,
        }

    def reset(self, frame_index: int) -> None:
        self.best_distance_m = float("inf")
        self.last_progress_frame = frame_index


def run_domain_randomized_intervention_episode(
    scene: RobotLabScene,
    *,
    output_dir: Path,
    seed: int,
    correction_source: str = "simulated_leader",
    force_failure: bool = False,
    leader_port: str | None = None,
    leader_config: str | None = None,
    studio_url: str | None = None,
    intervention_control_path: Path | None = None,
    progress_path: Path | None = None,
    run_config: EpisodeRunConfig = EpisodeRunConfig(),
) -> dict[str, Any]:
    """Run one randomized episode with control-step intervention arbitration."""

    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise RuntimeError("mujoco is required; run from .mujoco_venv") from exc

    if correction_source != "simulated_leader" and intervention_control_path is None:
        raise ValueError(f"{correction_source} requires an intervention control file for deadman gating")
    if run_config.control_hz <= 0 or run_config.scripted_steps_per_waypoint <= 0:
        raise ValueError("control_hz and scripted_steps_per_waypoint must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = progress_path or output_dir / "intervention_progress.json"
    randomized_scene, randomization_manifest = randomize_scene(scene, seed)
    scene_dict = randomized_scene.to_dict()
    scene_export_dir = output_dir / "scene_export"
    proof = export_so101_desk_sort_scene(randomized_scene, scene_export_dir)
    xml_path = scene_export_dir / "mujoco" / "scene.xml"
    apply_mujoco_randomization(xml_path, randomization_manifest)
    write_json(output_dir / "domain_randomization_manifest.json", randomization_manifest)

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    data.ctrl[: model.nu] = _home_control()
    for _ in range(max(1, round(0.35 / model.opt.timestep))):
        mujoco.mj_step(model, data)

    trays = tuple(RobotLabTray(**tray) for tray in scene_dict["trays"])
    control_store = InterventionControlStore(intervention_control_path)
    arbiter = InterventionArbiter(deadman_timeout_s=run_config.deadman_timeout_s)
    recorder = EpisodeRecorder(
        mujoco,
        model,
        data,
        scene_dict,
        output_dir,
        progress_path,
        seed=seed,
        randomization_manifest=randomization_manifest,
        width=run_config.observation_width,
        height=run_config.observation_height,
    )
    correction: CorrectionSource | None = None
    failure_events: list[dict[str, Any]] = []
    intervention_frames: list[dict[str, Any]] = []
    slot_counts: dict[str, int] = {}
    intervention_success = False

    _write_progress(
        progress_path,
        {
            "status": "running",
            "phase": "reset_complete",
            "seed": seed,
            "scene_id": randomized_scene.scene_id,
            "correction_source": correction_source,
            "physical_follower_commanded": False,
        },
    )

    try:
        for cube_index, cube in enumerate(scene_dict["cubes"]):
            correct_tray = next(tray for tray in scene_dict["trays"] if tray["color"] == cube["color"])
            selected_tray = correct_tray
            phase_prefix = "policy"
            if force_failure and cube_index == 0:
                selected_tray = next(
                    tray for tray in scene_dict["trays"] if tray["color"] != cube["color"]
                )
                phase_prefix = "policy_forced_failure"

            selected_index = slot_counts.get(selected_tray["color"], 0)
            slot_counts[selected_tray["color"]] = selected_index + 1
            selected_target = _target_cube_position(cube, selected_tray, selected_index)
            _run_scripted_cube_path(
                mujoco,
                model,
                data,
                recorder,
                arbiter,
                cube,
                selected_tray,
                selected_target,
                phase_prefix=phase_prefix,
                run_config=run_config,
            )

            placement = _cube_score_entry(mujoco, model, data, scene_dict, trays, cube["name"])
            if placement["correct"]:
                continue

            failure_reason = (
                "forced_wrong_tray_for_intervention_proof"
                if force_failure and cube_index == 0
                else f"cube_placement_{placement['tray']}"
            )
            failure_event = {
                "frame_index": recorder.frame_index,
                "time_s": round(float(data.time), 6),
                "cube": cube["name"],
                "reason": failure_reason,
                "observed_tray": placement["tray"],
                "expected_tray": cube["color"],
            }
            failure_events.append(failure_event)
            recorder.set_failure_reason(failure_reason)
            _write_progress(
                progress_path,
                {
                    "status": "waiting_for_intervention",
                    "phase": "failure_detected",
                    "seed": seed,
                    "failure": failure_event,
                    "physical_follower_commanded": False,
                },
            )

            correction = correction or make_correction_source(
                correction_source,
                leader_port=leader_port,
                leader_config=leader_config,
                studio_url=studio_url,
                repo_root=REPO_ROOT,
            )
            slot_counts[selected_tray["color"]] = max(
                0, slot_counts.get(selected_tray["color"], 1) - 1
            )
            corrected_index = slot_counts.get(correct_tray["color"], 0)
            corrected_target = _target_cube_position(cube, correct_tray, corrected_index)

            if correction_source == "simulated_leader":
                before = len(recorder.frames)
                _run_scripted_correction_path(
                    mujoco,
                    model,
                    data,
                    recorder,
                    arbiter,
                    correction,
                    cube,
                    correct_tray,
                    corrected_target,
                    run_config=run_config,
                )
                intervention_frames.extend(recorder.frames[before:])
                placement = _cube_score_entry(
                    mujoco, model, data, scene_dict, trays, cube["name"]
                )
                intervention_success = bool(placement["correct"])
            else:
                before = len(recorder.frames)
                intervention_success = _run_physical_contact_intervention(
                    mujoco,
                    model,
                    data,
                    recorder,
                    arbiter,
                    correction,
                    control_store,
                    cube,
                    correct_tray,
                    trays,
                    run_config=run_config,
                )
                intervention_frames.extend(
                    row for row in recorder.frames[before:] if row["is_intervention"]
                )

            if intervention_success:
                slot_counts[correct_tray["color"]] = corrected_index + 1
                recorder.set_failure_reason(None)
            else:
                break

        for _ in range(max(1, round(0.2 / model.opt.timestep))):
            mujoco.mj_step(model, data)

        final_states = _cube_states_from_model(mujoco, model, data, scene_dict)
        final_score = score_cube_sort(final_states, trays)
        recorder.render_final(output_dir / "policy_final_side.png", "cam0_side")
        recorder.render_final(output_dir / "policy_final_overhead.png", "cam1_overhead")
        recorder.render_final(output_dir / "policy_final_wrist.png", "cam2_wrist")

        source_report = (
            correction.safety_report()
            if correction is not None
            else {
                "source": correction_source,
                "hardware_opened": False,
                "physical_follower_commanded": False,
            }
        )
        object_motion_modes = sorted({row["object_motion_mode"] for row in recorder.frames})
        contact_frames = sum(bool(row["robot_cube_contacts"]) for row in intervention_frames)
        summary = {
            "schema_version": "scenesmith.intervention_episode.v2",
            "status": "pass" if final_score["success"] else "fail",
            "seed": seed,
            "scene_id": randomized_scene.scene_id,
            "base_scene_id": scene.scene_id,
            "task": randomized_scene.policy.task,
            "force_failure": force_failure,
            "failure_reason": failure_events[0]["reason"] if failure_events else None,
            "failure_events": failure_events,
            "policy_runtime": {
                "kind": "scenesmith_scripted_test_controller",
                "neural_closed_loop": False,
                "purpose": "failure_injection_and_intervention_pipeline_proof",
            },
            "intervention": {
                "enabled": bool(intervention_frames),
                "source": correction_source,
                "frames": len(intervention_frames),
                "success": intervention_success if failure_events else None,
                "control_step_arbitration": True,
                "contact_frames": contact_frames,
                "contact_physics_verified": bool(
                    correction_source in {"physical_leader", "studio_leader"}
                    and intervention_success
                    and contact_frames > 0
                ),
                "physical_follower_commanded": False,
                "safety_report": source_report,
            },
            "proof_scope": {
                "object_motion_modes": object_motion_modes,
                "simulated_leader_is_training_demo": False,
                "physical_leader_frames_are_training_eligible": correction_source
                in {"physical_leader", "studio_leader"},
                "synchronized_observations": True,
                "observation_action_alignment": "pre_action_observation_to_executed_action",
            },
            "randomization_manifest": str(output_dir / "domain_randomization_manifest.json"),
            "scene_export": proof["artifacts"],
            "final_score": final_score,
            "final_cube_states": final_states,
            "observation_frames": len(recorder.frames),
            "artifacts": {
                "summary": str(output_dir / "intervention_episode_summary.json"),
                "trajectory": str(output_dir / "intervention_trajectory.json"),
                "frames_jsonl": str(output_dir / "observation_frames.jsonl"),
                "intervention_frames": str(output_dir / "intervention_frames.jsonl"),
                "progress": str(progress_path),
                "observations": str(output_dir / "observations"),
                "final_side_render": str(output_dir / "policy_final_side.png"),
                "final_overhead_render": str(output_dir / "policy_final_overhead.png"),
                "final_wrist_render": str(output_dir / "policy_final_wrist.png"),
            },
        }
        _write_jsonl(output_dir / "observation_frames.jsonl", recorder.frames)
        _write_jsonl(output_dir / "intervention_frames.jsonl", intervention_frames)
        write_json(output_dir / "intervention_trajectory.json", {"frames": recorder.frames})
        write_json(output_dir / "intervention_episode_summary.json", summary)
        _write_progress(
            progress_path,
            {
                "status": "complete",
                "phase": "episode_complete",
                "seed": seed,
                "summary": summary,
                "latest_frame": recorder.frames[-1] if recorder.frames else None,
                "physical_follower_commanded": False,
            },
        )
        return summary
    finally:
        recorder.close()
        if correction is not None:
            correction.close()


def run_neural_policy_intervention_episode(
    scene: RobotLabScene,
    *,
    output_dir: Path,
    seed: int,
    correction_source: str,
    policy_url: str,
    max_policy_steps: int = 20,
    leader_port: str | None = None,
    leader_config: str | None = None,
    studio_url: str | None = None,
    intervention_control_path: Path | None = None,
    progress_path: Path | None = None,
    run_config: EpisodeRunConfig = EpisodeRunConfig(realtime=True),
) -> dict[str, Any]:
    """Run real policy actions in contact physics, then allow leader takeover."""

    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise RuntimeError("mujoco is required; run from .mujoco_venv") from exc
    if correction_source == "simulated_leader":
        raise ValueError("Neural contact-physics episodes require studio_leader or physical_leader")
    if correction_source != "none" and intervention_control_path is None:
        raise ValueError("Neural intervention episodes require a deadman control file")
    if max_policy_steps <= 0:
        raise ValueError("max_policy_steps must be positive")
    if run_config.grasp_assist_mode not in {
        "policy_gripper",
        "contact_reflex",
        "policy_gripper_tray_release",
        "policy_gripper_tray_transfer",
    }:
        raise ValueError(f"Unknown grasp assist mode: {run_config.grasp_assist_mode}")

    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = progress_path or output_dir / "intervention_progress.json"
    randomized_scene, randomization_manifest = randomize_scene(scene, seed)
    scene_dict = randomized_scene.to_dict()
    scene_export_dir = output_dir / "scene_export"
    proof = export_so101_desk_sort_scene(randomized_scene, scene_export_dir)
    xml_path = scene_export_dir / "mujoco" / "scene.xml"
    apply_mujoco_randomization(xml_path, randomization_manifest)
    write_json(output_dir / "domain_randomization_manifest.json", randomization_manifest)

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    policy = HttpPolicyActionSource(HttpPolicyActionConfig(base_url=policy_url))
    policy_home = policy.simulation_home_control() or _home_control()
    data.qpos[: model.nu] = policy_home[: model.nu]
    data.ctrl[: model.nu] = policy_home[: model.nu]
    mujoco.mj_forward(model, data)
    for _ in range(max(1, round(0.35 / model.opt.timestep))):
        mujoco.mj_step(model, data)

    trays = tuple(RobotLabTray(**tray) for tray in scene_dict["trays"])
    control_store = (
        InterventionControlStore(intervention_control_path)
        if intervention_control_path is not None
        else None
    )
    arbiter = InterventionArbiter(deadman_timeout_s=run_config.deadman_timeout_s)
    arbiter.decide(policy_home, None, DeadmanSignal())
    recorder = EpisodeRecorder(
        mujoco,
        model,
        data,
        scene_dict,
        output_dir,
        progress_path,
        seed=seed,
        randomization_manifest=randomization_manifest,
        width=run_config.observation_width,
        height=run_config.observation_height,
    )
    correction: CorrectionSource | None = None
    failure_events: list[dict[str, Any]] = []
    intervention_frames: list[dict[str, Any]] = []
    intervention_success = False
    grasp_assist = NeuralGraspAssistState()
    approach_monitor = ApproachProgressMonitor(
        stall_steps=run_config.precontact_stall_steps,
        min_progress_m=run_config.precontact_min_progress_m,
        contact_distance_m=run_config.precontact_contact_distance_m,
    )
    tracked_cube = scene_dict["cubes"][0]
    tracked_tray = next(
        tray for tray in scene_dict["trays"] if tray["color"] == tracked_cube["color"]
    )
    initial_positions = {
        cube["name"]: _body_position(mujoco, model, data, cube["name"])
        for cube in scene_dict["cubes"]
    }

    _write_progress(
        progress_path,
        {
            "status": "running",
            "phase": "neural_policy_reset",
            "seed": seed,
            "policy_source": policy.name,
            "correction_source": correction_source,
            "physical_follower_commanded": False,
        },
    )

    try:
        policy.reset(seed=seed)
        policy_success = False
        contact_reflex = run_config.grasp_assist_mode == "contact_reflex"
        tray_transfer = (
            run_config.grasp_assist_mode == "policy_gripper_tray_transfer"
        )
        tray_release = run_config.grasp_assist_mode in {
            "contact_reflex",
            "policy_gripper_tray_release",
            "policy_gripper_tray_transfer",
        }
        for _ in range(max_policy_steps):
            controller_action, controller_phase = _contact_reflex_post_place_control(
                grasp_assist,
                policy_home,
                frame_index=recorder.frame_index,
                hold_steps=run_config.contact_reflex_post_place_hold_steps,
                lift_steps=run_config.contact_reflex_post_place_lift_steps,
                retreat_steps=run_config.contact_reflex_post_place_retreat_steps,
            )
            if controller_action is None and tray_transfer:
                controller_action, controller_phase = (
                    _contact_gated_tray_transfer_control(
                        grasp_assist,
                        frame_index=recorder.frame_index,
                        lift_steps=25,
                        carry_steps=40,
                        lower_steps=30,
                    )
                )
            remaining_cube_positions = {
                cube["name"]: _body_position(mujoco, model, data, cube["name"])
                for cube in scene_dict["cubes"]
                if cube["name"] not in grasp_assist.completed_cubes
            }
            stall_event = approach_monitor.update(
                frame_index=recorder.frame_index,
                gripper_position_m=_gripper_site_position(mujoco, model, data),
                cube_positions_m=remaining_cube_positions,
                has_contact=bool(_robot_cube_contacts(mujoco, model, data)),
                controller_active=(
                    controller_action is not None or grasp_assist.active_cube is not None
                ),
            )
            if stall_event is not None and tray_transfer and controller_action is None:
                recovery_cube = next(
                    cube
                    for cube in scene_dict["cubes"]
                    if cube["name"] == stall_event["cube"]
                )
                grasp_assist.events.append(stall_event)
                grasp_assist.search_retries_since_place += 1
                grasp_assist.last_policy_reset_frame = recorder.frame_index
                _schedule_contact_gated_recovery_pick(
                    mujoco,
                    model,
                    data,
                    grasp_assist,
                    recovery_cube,
                    frame_index=recorder.frame_index,
                )
            if controller_action is None and tray_transfer:
                controller_action, controller_phase = (
                    _contact_gated_recovery_pick_control(
                        grasp_assist,
                        frame_index=recorder.frame_index,
                        approach_steps=32,
                        descend_steps=42,
                        close_steps=14,
                    )
                )
            if grasp_assist.policy_reset_pending and controller_action is None:
                reset_index = grasp_assist.policy_reset_count + 1
                reset_seed = _policy_search_seed(seed, reset_index)
                policy.reset(seed=reset_seed)
                grasp_assist.policy_reset_pending = False
                grasp_assist.policy_reset_count = reset_index
                grasp_assist.last_policy_reset_frame = recorder.frame_index
                grasp_assist.search_retries_since_place = 0
                grasp_assist.events.append(
                    {
                        "kind": "policy_reset_after_place",
                        "frame_index": recorder.frame_index,
                        "seed": reset_seed,
                    }
                )
            if (
                controller_action is None
                and grasp_assist.active_cube is None
                and not grasp_assist.policy_reset_pending
                and grasp_assist.recovery_pick_start_frame is None
                and recorder.frame_index - grasp_assist.last_policy_reset_frame
                >= run_config.neural_search_retry_steps
            ):
                reset_index = grasp_assist.policy_reset_count + 1
                retry_seed = _policy_search_seed(seed, reset_index)
                policy.reset(seed=retry_seed)
                grasp_assist.policy_reset_count = reset_index
                grasp_assist.last_policy_reset_frame = recorder.frame_index
                grasp_assist.search_retries_since_place += 1
                grasp_assist.events.append(
                    {
                        "kind": "policy_search_retry",
                        "frame_index": recorder.frame_index,
                        "seed": retry_seed,
                    }
                )
            if (
                tray_transfer
                and controller_action is None
                and grasp_assist.search_retries_since_place > 0
                and grasp_assist.active_cube is None
                and not grasp_assist.policy_reset_pending
                and grasp_assist.recovery_pick_start_frame is None
            ):
                recovery_cube = _select_recovery_cube(
                    scene_dict, grasp_assist.completed_cubes
                )
                if recovery_cube is not None:
                    _schedule_contact_gated_recovery_pick(
                        mujoco,
                        model,
                        data,
                        grasp_assist,
                        recovery_cube,
                        frame_index=recorder.frame_index,
                    )
            observation, observation_time_s = recorder.capture_observation()
            policy_task = _policy_task_for_remaining_cubes(
                scene_dict, grasp_assist.completed_cubes
            )
            policy_action = policy.get_action(
                observation,
                episode_dir=output_dir,
                task=policy_task,
            )
            if controller_action is None:
                decision = arbiter.decide(policy_action, None, DeadmanSignal())
            else:
                decision = replace(
                    arbiter.decide(controller_action, None, DeadmanSignal()),
                    policy_action=tuple(policy_action),
                    action_source=(
                        "contact_gated_tray_transfer"
                        if controller_phase
                        and controller_phase.startswith("contact_gated_tray_transfer")
                        else (
                            "contact_gated_recovery_pick"
                            if controller_phase
                            and controller_phase.startswith(
                                "contact_gated_recovery_pick"
                            )
                            else "contact_reflex_post_place"
                        )
                    ),
                    intervention_event=controller_phase,
                )
            data.ctrl[: model.nu] = decision.executed_action[: model.nu]
            if tray_release and grasp_assist.active_cube is not None:
                data.ctrl[5] = CLOSED_GRIPPER_CONTROL
            else:
                _release_neural_grasp_assist_if_open(
                    mujoco,
                    model,
                    data,
                    grasp_assist,
                    frame_index=recorder.frame_index,
                )
            _step_control_period(mujoco, model, data, run_config.control_hz)
            recovery_pick_control = bool(
                controller_phase
                and controller_phase.startswith("contact_gated_recovery_pick")
            )
            if controller_action is None or recovery_pick_control:
                _activate_neural_grasp_assist_on_contact(
                    mujoco,
                    model,
                    data,
                    grasp_assist,
                    tuple(
                        cube["name"]
                        for cube in scene_dict["cubes"]
                        if cube["name"] not in grasp_assist.completed_cubes
                    ),
                    frame_index=recorder.frame_index,
                    require_closed_gripper=(
                        not contact_reflex
                        and not (
                            tray_transfer
                            and grasp_assist.search_retries_since_place > 0
                        )
                    ),
                    search_recovery=(
                        tray_transfer
                        and grasp_assist.search_retries_since_place > 0
                    ),
                )
                if grasp_assist.active_cube is not None:
                    _clear_contact_gated_recovery_pick(grasp_assist)
                if tray_transfer and grasp_assist.active_cube is not None:
                    active_cube_spec = next(
                        cube
                        for cube in scene_dict["cubes"]
                        if cube["name"] == grasp_assist.active_cube
                    )
                    active_tray_spec = next(
                        tray
                        for tray in scene_dict["trays"]
                        if tray["color"] == active_cube_spec["color"]
                    )
                    same_color_completed = sum(
                        cube["color"] == active_cube_spec["color"]
                        and cube["name"] in grasp_assist.completed_cubes
                        for cube in scene_dict["cubes"]
                    )
                    _schedule_contact_gated_tray_transfer(
                        mujoco,
                        model,
                        data,
                        grasp_assist,
                        active_cube_spec,
                        active_tray_spec,
                        slot_index=same_color_completed,
                        frame_index=recorder.frame_index,
                    )
            if tray_release and grasp_assist.active_cube is not None:
                data.ctrl[5] = CLOSED_GRIPPER_CONTROL
                current_score = score_cube_sort(
                    _cube_states_from_model(mujoco, model, data, scene_dict), trays
                )
                active_entry = next(
                    entry
                    for entry in current_score["entries"]
                    if entry["cube"] == grasp_assist.active_cube
                )
                active_cube_spec = next(
                    cube
                    for cube in scene_dict["cubes"]
                    if cube["name"] == grasp_assist.active_cube
                )
                active_tray_spec = next(
                    tray
                    for tray in scene_dict["trays"]
                    if tray["color"] == active_cube_spec["color"]
                )
                active_cube_position = _body_position(
                    mujoco, model, data, grasp_assist.active_cube
                )
                if _contact_reflex_release_ready(
                    active_entry,
                    active_cube_spec,
                    active_tray_spec,
                    active_cube_position,
                ):
                    released_cube = grasp_assist.active_cube
                    _release_neural_grasp_assist(
                        mujoco,
                        model,
                        data,
                        grasp_assist,
                        frame_index=recorder.frame_index,
                        reason="contact_reflex_matching_tray",
                    )
                    data.ctrl[5] = 1.6
                    if released_cube is not None:
                        grasp_assist.completed_cubes.add(released_cube)
                    lift_control = _solve_site_position_ik(
                        mujoco,
                        model,
                        data,
                        data.site_xpos[
                            mujoco.mj_name2id(
                                model, mujoco.mjtObj.mjOBJ_SITE, "gripperframe"
                            )
                        ]
                        + np.asarray([0.0, 0.0, 0.05]),
                    )
                    _schedule_contact_reflex_post_place_retreat(
                        grasp_assist,
                        data.ctrl[: model.nu],
                        lift_control,
                        cube_name=released_cube,
                        frame_index=recorder.frame_index,
                    )
                elif contact_reflex and (
                    grasp_assist.activation_frame is not None
                    and recorder.frame_index - grasp_assist.activation_frame
                    >= run_config.contact_reflex_max_hold_steps
                ):
                    _release_neural_grasp_assist(
                        mujoco,
                        model,
                        data,
                        grasp_assist,
                        frame_index=recorder.frame_index,
                        reason="contact_reflex_hold_timeout",
                        cooldown_frames=45,
                    )
                    data.ctrl[5] = 1.6
            recorder.record(
                observation=observation,
                observation_time_s=observation_time_s,
                cube_name=tracked_cube["name"],
                phase=controller_phase or "neural_policy_contact_physics",
                target_tray=tracked_tray["name"],
                decision=decision,
                policy_task=policy_task,
                object_motion_mode=(
                    "contact_gated_task_space_tray_transfer"
                    if controller_phase
                    and controller_phase.startswith("contact_gated_tray_transfer")
                    else (
                        "contact_gated_task_space_recovery_pick"
                        if controller_phase
                        and controller_phase.startswith(
                            "contact_gated_recovery_pick"
                        )
                        else (
                            "contact_reflex_post_place_controller"
                            if controller_action is not None
                            else (
                                "contact_physics_neural_policy_with_contact_gated_grasp_assist"
                                if grasp_assist.active_cube
                                else "contact_physics_neural_policy"
                            )
                        )
                    )
                ),
            )
            score = score_cube_sort(
                _cube_states_from_model(mujoco, model, data, scene_dict), trays
            )
            if score["success"] and grasp_assist.active_cube is None:
                policy_success = True
                break
            _sleep_control_period(run_config)

        if not policy_success:
            _release_neural_grasp_assist(
                mujoco,
                model,
                data,
                grasp_assist,
                frame_index=recorder.frame_index,
                reason="neural_policy_ended",
            )
            final_before_intervention = _cube_states_from_model(
                mujoco, model, data, scene_dict
            )
            maximum_displacement = max(
                float(
                    np.linalg.norm(
                        np.asarray(cube["position_m"])
                        - np.asarray(initial_positions[cube["name"]])
                    )
                )
                for cube in final_before_intervention
            )
            failure_reason = (
                "neural_policy_stalled"
                if maximum_displacement < 0.005
                else "neural_policy_timeout"
            )
            failure_event = {
                "frame_index": recorder.frame_index,
                "time_s": round(float(data.time), 6),
                "cube": tracked_cube["name"],
                "reason": failure_reason,
                "maximum_cube_displacement_m": round(maximum_displacement, 6),
                "policy_steps": max_policy_steps,
            }
            failure_events.append(failure_event)
            recorder.set_failure_reason(failure_reason)
            _write_progress(
                progress_path,
                {
                    "status": "waiting_for_intervention",
                    "phase": "neural_policy_failure_detected",
                    "seed": seed,
                    "failure": failure_event,
                    "physical_follower_commanded": False,
                },
            )
            if correction_source != "none":
                correction = make_correction_source(
                    correction_source,
                    leader_port=leader_port,
                    leader_config=leader_config,
                    studio_url=studio_url,
                    repo_root=REPO_ROOT,
                )
                before = len(recorder.frames)
                intervention_success = _run_physical_contact_intervention(
                    mujoco,
                    model,
                    data,
                    recorder,
                    arbiter,
                    correction,
                    control_store,
                    tracked_cube,
                    tracked_tray,
                    trays,
                    run_config=run_config,
                    require_full_task=True,
                )
                intervention_frames.extend(
                    row for row in recorder.frames[before:] if row["is_intervention"]
                )

        for _ in range(max(1, round(0.2 / model.opt.timestep))):
            mujoco.mj_step(model, data)
        final_states = _cube_states_from_model(mujoco, model, data, scene_dict)
        final_score = score_cube_sort(final_states, trays)
        recorder.render_final(output_dir / "policy_final_side.png", "cam0_side")
        recorder.render_final(output_dir / "policy_final_overhead.png", "cam1_overhead")
        recorder.render_final(output_dir / "policy_final_wrist.png", "cam2_wrist")

        source_report = (
            correction.safety_report()
            if correction is not None
            else {
                "source": correction_source,
                "hardware_opened": False,
                "physical_follower_commanded": False,
            }
        )
        object_motion_modes = sorted({row["object_motion_mode"] for row in recorder.frames})
        contact_frames = sum(bool(row["robot_cube_contacts"]) for row in intervention_frames)
        policy_contact_frames = sum(bool(row["robot_cube_contacts"]) for row in recorder.frames)
        neural_policy_frames = sum(
            row["action_source"] == "policy" for row in recorder.frames
        )
        stage_metrics = _episode_stage_metrics(
            recorder.frames,
            scene_dict,
            initial_positions,
            grasp_assist.events,
            final_score,
        )
        summary = {
            "schema_version": "scenesmith.intervention_episode.v2",
            "status": "pass" if final_score["success"] else "fail",
            "seed": seed,
            "scene_id": randomized_scene.scene_id,
            "base_scene_id": scene.scene_id,
            "task": randomized_scene.policy.task,
            "force_failure": False,
            "failure_reason": failure_events[0]["reason"] if failure_events else None,
            "failure_events": failure_events,
            "policy_runtime": policy.report(),
            "intervention": {
                "enabled": bool(intervention_frames),
                "source": correction_source,
                "frames": len(intervention_frames),
                "success": intervention_success if failure_events else None,
                "control_step_arbitration": True,
                "contact_frames": contact_frames,
                "contact_physics_verified": bool(
                    intervention_success and contact_frames > 0
                ),
                "physical_follower_commanded": False,
                "safety_report": source_report,
            },
            "proof_scope": {
                "object_motion_modes": object_motion_modes,
                "simulated_leader_is_training_demo": False,
                "physical_leader_frames_are_training_eligible": True,
                "synchronized_observations": True,
                "observation_action_alignment": "pre_action_observation_to_executed_action",
                "neural_policy_actions_applied_to_simulation": neural_policy_frames > 0,
                "neural_policy_action_frames": neural_policy_frames,
                "scripted_object_motion": False,
                "policy_gripper_contact_frames": policy_contact_frames,
                "policy_gripper_contact_verified": policy_contact_frames > 0,
                "grasp_assist": {
                    "mode": (
                        "contact_gated_jaw_reflex_to_matching_tray"
                        if contact_reflex
                        else (
                            "policy_gripper_contact_then_task_space_tray_transfer"
                            if tray_transfer
                            else (
                                "policy_gripper_contact_to_low_matching_tray_release"
                                if tray_release
                                else "contact_gated_mujoco_weld"
                            )
                        )
                    ),
                    "events": grasp_assist.events,
                    "contact_reflex_max_hold_steps": (
                        run_config.contact_reflex_max_hold_steps
                        if contact_reflex
                        else None
                    ),
                    "activation_count": sum(
                        event["kind"] == "activated" for event in grasp_assist.events
                    ),
                    "search_recovery_reflex_activation_count": sum(
                        event["kind"] == "activated"
                        and event.get("jaw_reflex", False)
                        and event.get("search_recovery", False)
                        for event in grasp_assist.events
                    ),
                    "all_activations_contact_gated": all(
                        event.get("contact_gated", False)
                        for event in grasp_assist.events
                        if event["kind"] == "activated"
                    ),
                    "active_at_success": grasp_assist.active_cube is not None,
                    "post_place_controller": {
                        "hold_steps": run_config.contact_reflex_post_place_hold_steps,
                        "lift_steps": run_config.contact_reflex_post_place_lift_steps,
                        "retreat_steps": run_config.contact_reflex_post_place_retreat_steps,
                        "executed_frames": grasp_assist.post_place_controller_frames,
                        "tray_transfer_executed_frames": (
                            grasp_assist.tray_transfer_controller_frames
                        ),
                        "recovery_pick_executed_frames": (
                            grasp_assist.recovery_pick_controller_frames
                        ),
                        "completed_cubes": sorted(grasp_assist.completed_cubes),
                        "policy_reset_count": grasp_assist.policy_reset_count,
                    },
                },
            },
            "randomization_manifest": str(output_dir / "domain_randomization_manifest.json"),
            "scene_export": proof["artifacts"],
            "final_score": final_score,
            "stage_metrics": stage_metrics,
            "final_cube_states": final_states,
            "observation_frames": len(recorder.frames),
            "artifacts": {
                "summary": str(output_dir / "intervention_episode_summary.json"),
                "trajectory": str(output_dir / "intervention_trajectory.json"),
                "frames_jsonl": str(output_dir / "observation_frames.jsonl"),
                "intervention_frames": str(output_dir / "intervention_frames.jsonl"),
                "progress": str(progress_path),
                "observations": str(output_dir / "observations"),
                "final_side_render": str(output_dir / "policy_final_side.png"),
                "final_overhead_render": str(output_dir / "policy_final_overhead.png"),
                "final_wrist_render": str(output_dir / "policy_final_wrist.png"),
            },
        }
        _write_jsonl(output_dir / "observation_frames.jsonl", recorder.frames)
        _write_jsonl(output_dir / "intervention_frames.jsonl", intervention_frames)
        write_json(output_dir / "intervention_trajectory.json", {"frames": recorder.frames})
        write_json(output_dir / "intervention_episode_summary.json", summary)
        _write_progress(
            progress_path,
            {
                "status": "complete",
                "phase": "episode_complete",
                "seed": seed,
                "summary": summary,
                "latest_frame": recorder.frames[-1] if recorder.frames else None,
                "physical_follower_commanded": False,
            },
        )
        return summary
    finally:
        recorder.close()
        if correction is not None:
            correction.close()


class EpisodeRecorder:
    def __init__(
        self,
        mujoco,
        model,
        data,
        scene: dict[str, Any],
        output_dir: Path,
        progress_path: Path,
        *,
        seed: int,
        randomization_manifest: dict[str, Any],
        width: int,
        height: int,
    ):
        self.mujoco = mujoco
        self.model = model
        self.data = data
        self.scene = scene
        self.output_dir = output_dir
        self.progress_path = progress_path
        self.seed = seed
        self.frames: list[dict[str, Any]] = []
        self.frame_index = 0
        self.failure_reason: str | None = None
        self.renderer = mujoco.Renderer(model, width=width, height=height)
        self.brightness = float(randomization_manifest["observation_augmentation"]["brightness_scale"])
        self.noise_std = float(randomization_manifest["observation_augmentation"]["camera_noise_std"])

    def set_failure_reason(self, reason: str | None) -> None:
        self.failure_reason = reason

    def record(
        self,
        *,
        observation: dict[str, Any],
        observation_time_s: float,
        cube_name: str,
        phase: str,
        target_tray: str,
        decision,
        object_motion_mode: str,
        policy_task: str | None = None,
    ) -> dict[str, Any]:
        decision_payload = decision.to_dict()
        next_cube_states = _cube_states_from_model(
            self.mujoco, self.model, self.data, self.scene
        )
        contacts = _robot_cube_contacts(self.mujoco, self.model, self.data)
        row = {
            "frame_index": self.frame_index,
            "seed": self.seed,
            "time_s": observation_time_s,
            "cube": cube_name,
            "phase": phase,
            "target_tray": target_tray,
            "policy_task": policy_task,
            "cube_position_m": _body_position(
                self.mujoco, self.model, self.data, cube_name
            ),
            "gripper_position_m": _gripper_site_position(
                self.mujoco, self.model, self.data
            ),
            "robot_control": decision_payload["executed_action"],
            **decision_payload,
            "failure_reason": self.failure_reason,
            "object_motion_mode": object_motion_mode,
            "robot_cube_contacts": contacts,
            "observation": observation,
            "transition": {
                "next_time_s": round(float(self.data.time), 6),
                "next_state": self.data.qpos[:6].round(6).tolist(),
                "next_cube_states": next_cube_states,
                "robot_cube_contacts": contacts,
            },
        }
        self.frames.append(row)
        self.frame_index += 1
        _write_progress(
            self.progress_path,
            {
                "status": "running",
                "phase": phase,
                "seed": self.seed,
                "latest_frame": row,
                "camera_paths": observation["images"],
                "physical_follower_commanded": False,
            },
        )
        return row

    def capture_observation(self) -> tuple[dict[str, Any], float]:
        image_paths = self._render_observations()
        return (
            {
                "state": self.data.qpos[:6].round(6).tolist(),
                "images": image_paths,
                "cube_states": _cube_states_from_model(
                    self.mujoco, self.model, self.data, self.scene
                ),
            },
            round(float(self.data.time), 6),
        )

    def _render_observations(self) -> dict[str, str]:
        paths: dict[str, str] = {}
        for camera_index, (role, camera_name) in enumerate(CAMERAS.items()):
            self.renderer.update_scene(self.data, camera=camera_name)
            pixels = self.renderer.render().copy()
            pixels = _augment_observation(
                pixels,
                brightness=self.brightness,
                noise_std=self.noise_std,
                seed=self.seed * 100_003 + self.frame_index * 17 + camera_index,
            )
            relative = Path("observations") / role / f"{self.frame_index:06d}.png"
            _write_png(self.output_dir / relative, pixels)
            paths[role] = relative.as_posix()
        return paths

    def render_final(self, path: Path, camera: str) -> None:
        self.renderer.update_scene(self.data, camera=camera)
        _write_png(path, self.renderer.render().copy())

    def close(self) -> None:
        self.renderer.close()


def _run_scripted_cube_path(
    mujoco,
    model,
    data,
    recorder: EpisodeRecorder,
    arbiter: InterventionArbiter,
    cube: dict[str, Any],
    tray: dict[str, Any],
    target_position: list[float],
    *,
    phase_prefix: str,
    run_config: EpisodeRunConfig,
) -> None:
    start = _body_position(mujoco, model, data, cube["name"])
    for phase, waypoint in _lift_carry_place_waypoints(start, target_position):
        _run_scripted_segment(
            mujoco,
            model,
            data,
            recorder,
            arbiter,
            cube_name=cube["name"],
            target_tray=tray["name"],
            phase=f"{phase_prefix}_{phase}",
            policy_phase=phase,
            target_position=waypoint,
            human_source=None,
            auto_deadman=False,
            object_motion_mode="scripted_policy_harness",
            run_config=run_config,
        )


def _run_scripted_correction_path(
    mujoco,
    model,
    data,
    recorder: EpisodeRecorder,
    arbiter: InterventionArbiter,
    correction: CorrectionSource,
    cube: dict[str, Any],
    tray: dict[str, Any],
    target_position: list[float],
    *,
    run_config: EpisodeRunConfig,
) -> None:
    start = _body_position(mujoco, model, data, cube["name"])
    for phase, waypoint in _lift_carry_place_waypoints(start, target_position):
        _run_scripted_segment(
            mujoco,
            model,
            data,
            recorder,
            arbiter,
            cube_name=cube["name"],
            target_tray=tray["name"],
            phase=f"intervention_{phase}",
            policy_phase=phase,
            target_position=waypoint,
            human_source=correction,
            auto_deadman=True,
            object_motion_mode="scripted_intervention_harness",
            run_config=run_config,
        )


def _run_scripted_segment(
    mujoco,
    model,
    data,
    recorder: EpisodeRecorder,
    arbiter: InterventionArbiter,
    *,
    cube_name: str,
    target_tray: str,
    phase: str,
    policy_phase: str,
    target_position: list[float],
    human_source: CorrectionSource | None,
    auto_deadman: bool,
    object_motion_mode: str,
    run_config: EpisodeRunConfig,
) -> None:
    start = _body_position(mujoco, model, data, cube_name)
    for step_index in range(run_config.scripted_steps_per_waypoint):
        amount = (step_index + 1) / run_config.scripted_steps_per_waypoint
        position = [
            round(left + (right - left) * amount, 6)
            for left, right in zip(start, target_position, strict=True)
        ]
        policy_action = _autonomous_control(policy_phase)
        human_action = (
            human_source.get_action(phase, step_index) if human_source is not None else None
        )
        signal = (
            DeadmanSignal(True, True, time.time(), step_index + 1, "simulated_auto_deadman")
            if auto_deadman
            else DeadmanSignal()
        )
        decision = arbiter.decide(policy_action, human_action, signal)
        observation, observation_time_s = recorder.capture_observation()
        _set_free_body_pose(mujoco, model, data, cube_name, position)
        data.ctrl[: model.nu] = decision.executed_action[: model.nu]
        _step_control_period(mujoco, model, data, run_config.control_hz)
        recorder.record(
            observation=observation,
            observation_time_s=observation_time_s,
            cube_name=cube_name,
            phase=phase,
            target_tray=target_tray,
            decision=decision,
            object_motion_mode=object_motion_mode,
        )
        _sleep_control_period(run_config)


def _run_physical_contact_intervention(
    mujoco,
    model,
    data,
    recorder: EpisodeRecorder,
    arbiter: InterventionArbiter,
    correction: CorrectionSource,
    control_store: InterventionControlStore | None,
    cube: dict[str, Any],
    tray: dict[str, Any],
    trays: tuple[RobotLabTray, ...],
    *,
    run_config: EpisodeRunConfig,
    require_full_task: bool = False,
) -> bool:
    if control_store is None:
        raise ValueError("Physical intervention requires a deadman control store")

    wait_started = time.monotonic()
    intervention_started: float | None = None
    while True:
        signal = control_store.read()
        active = signal.armed and signal.takeover and signal.is_fresh(run_config.deadman_timeout_s)
        observation, observation_time_s = recorder.capture_observation()
        human_action = correction.get_action("intervention_contact_physics", recorder.frame_index) if active else None
        policy_action = data.ctrl[: model.nu].tolist()
        decision = arbiter.decide(policy_action, human_action, signal)
        data.ctrl[: model.nu] = decision.executed_action[: model.nu]
        _step_control_period(mujoco, model, data, run_config.control_hz)
        recorder.record(
            observation=observation,
            observation_time_s=observation_time_s,
            cube_name=cube["name"],
            phase=("intervention_contact_physics" if decision.is_intervention else "waiting_for_intervention"),
            target_tray=tray["name"],
            decision=decision,
            object_motion_mode="contact_physics",
        )

        score = score_cube_sort(
            _cube_states_from_model(mujoco, model, data, recorder.scene), trays
        )
        placement = next(
            entry for entry in score["entries"] if entry["cube"] == cube["name"]
        )
        task_complete = score["success"] if require_full_task else placement["correct"]
        if task_complete:
            return True
        if decision.is_intervention and intervention_started is None:
            intervention_started = time.monotonic()
        if intervention_started is None:
            if time.monotonic() - wait_started >= run_config.intervention_wait_timeout_s:
                return False
        elif time.monotonic() - intervention_started >= run_config.intervention_run_timeout_s:
            return False
        _sleep_control_period(replace_realtime(run_config, True))


def replace_realtime(config: EpisodeRunConfig, value: bool) -> EpisodeRunConfig:
    return EpisodeRunConfig(
        control_hz=config.control_hz,
        scripted_steps_per_waypoint=config.scripted_steps_per_waypoint,
        observation_width=config.observation_width,
        observation_height=config.observation_height,
        deadman_timeout_s=config.deadman_timeout_s,
        intervention_wait_timeout_s=config.intervention_wait_timeout_s,
        intervention_run_timeout_s=config.intervention_run_timeout_s,
        realtime=value,
    )


def _cube_score_entry(mujoco, model, data, scene, trays, cube_name: str) -> dict[str, Any]:
    score = score_cube_sort(_cube_states_from_model(mujoco, model, data, scene), trays)
    return next(entry for entry in score["entries"] if entry["cube"] == cube_name)


def _cube_states_from_model(mujoco, model, data, scene: dict[str, Any]) -> list[dict[str, object]]:
    return [
        {
            "name": cube["name"],
            "color": cube["color"],
            "position_m": _body_position(mujoco, model, data, cube["name"]),
        }
        for cube in scene["cubes"]
    ]


def _body_position(mujoco, model, data, body_name: str) -> list[float]:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    return data.xpos[body_id].round(6).tolist()


def _gripper_site_position(mujoco, model, data) -> list[float]:
    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "gripperframe")
    return data.site_xpos[site_id].round(6).tolist()


def _episode_stage_metrics(
    frames: list[dict[str, Any]],
    scene: dict[str, Any],
    initial_positions: dict[str, list[float]],
    grasp_events: list[dict[str, Any]],
    final_score: dict[str, Any],
) -> dict[str, Any]:
    cubes = {cube["name"]: cube for cube in scene["cubes"]}
    trays = {tray["color"]: tray for tray in scene["trays"]}
    reached: set[str] = set()
    contacted: set[str] = set()
    lifted: set[str] = set()
    transported: set[str] = set()
    minimum_distance = float("inf")
    for frame in frames:
        gripper_position = frame.get("gripper_position_m")
        for contact in frame.get("robot_cube_contacts") or []:
            for name in (contact.get("left_body"), contact.get("right_body")):
                if name in cubes:
                    contacted.add(str(name))
        transition = frame.get("transition") or {}
        for state in transition.get("next_cube_states") or []:
            name = str(state["name"])
            position = state["position_m"]
            if gripper_position is not None:
                distance = float(
                    np.linalg.norm(
                        np.asarray(gripper_position, dtype=np.float64)
                        - np.asarray(position, dtype=np.float64)
                    )
                )
                minimum_distance = min(minimum_distance, distance)
                if distance <= 0.06:
                    reached.add(name)
            if float(position[2]) >= float(initial_positions[name][2]) + 0.03:
                lifted.add(name)
            tray = trays[str(cubes[name]["color"])]
            half_x = float(tray["size_m"][0]) / 2 + float(cubes[name]["side_length_m"])
            half_y = float(tray["size_m"][1]) / 2 + float(cubes[name]["side_length_m"])
            if (
                abs(float(position[0]) - float(tray["center_m"][0])) <= half_x
                and abs(float(position[1]) - float(tray["center_m"][1])) <= half_y
            ):
                transported.add(name)
    grasped = {
        str(event["cube"])
        for event in grasp_events
        if event.get("kind") == "activated" and event.get("cube") in cubes
    }
    released = {
        str(event["cube"])
        for event in grasp_events
        if event.get("kind") == "released" and event.get("cube") in cubes
    }
    placed = {
        str(entry["cube"])
        for entry in final_score.get("entries") or []
        if entry.get("correct")
    }
    stage_sets = {
        "reach": reached,
        "contact": contacted,
        "grasp": grasped,
        "lift": lifted,
        "transport": transported,
        "release": released,
        "placement": placed,
    }
    return {
        "schema_version": "scenesmith.sort_stage_metrics.v1",
        "total_cubes": len(cubes),
        "minimum_gripper_cube_distance_m": (
            round(minimum_distance, 6) if np.isfinite(minimum_distance) else None
        ),
        "counts": {stage: len(names) for stage, names in stage_sets.items()},
        "rates": {stage: len(names) / len(cubes) for stage, names in stage_sets.items()},
        "cubes": {stage: sorted(names) for stage, names in stage_sets.items()},
    }


def _target_cube_position(cube: dict[str, Any], tray: dict[str, Any], index: int) -> list[float]:
    side = cube["side_length_m"]
    offset_x = (-0.75 if index % 2 == 0 else 0.75) * side
    offset_y = (index // 2) * side * 0.9
    return [
        tray["center_m"][0] + offset_x,
        tray["center_m"][1] + offset_y,
        tray["center_m"][2] + tray["size_m"][2] / 2 + side / 2 + 0.003,
    ]


def _lift_carry_place_waypoints(start_position, target_position):
    lift_z = max(start_position[2], target_position[2]) + 0.08
    return [
        ("approach", [start_position[0], start_position[1], lift_z]),
        ("lift", [start_position[0], start_position[1], lift_z]),
        ("carry", [target_position[0], target_position[1], lift_z]),
        ("place", target_position),
    ]


def _home_control() -> list[float]:
    return [0.0, -0.55, 1.05, -0.48, 0.0, 0.35]


def _autonomous_control(phase: str) -> list[float]:
    controls = {
        "approach": [0.0, -0.45, 0.95, -0.45, 0.0, 0.8],
        "lift": [0.0, -0.35, 0.9, -0.35, 0.0, 0.25],
        "carry": [0.25, -0.35, 0.75, -0.4, 0.0, 0.25],
        "place": [0.25, -0.45, 0.95, -0.45, 0.0, 0.95],
    }
    return controls.get(phase, _home_control())


def _set_free_body_pose(mujoco, model, data, body_name: str, position) -> None:
    joint_name = f"{body_name}_free"
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    qpos_adr = model.jnt_qposadr[joint_id]
    data.qpos[qpos_adr : qpos_adr + 7] = [
        position[0],
        position[1],
        position[2],
        1.0,
        0.0,
        0.0,
        0.0,
    ]
    data.qvel[model.jnt_dofadr[joint_id] : model.jnt_dofadr[joint_id] + 6] = 0
    mujoco.mj_forward(model, data)


def _step_control_period(mujoco, model, data, control_hz: int) -> None:
    substeps = max(1, round((1.0 / control_hz) / model.opt.timestep))
    for _ in range(substeps):
        mujoco.mj_step(model, data)


def _sleep_control_period(config: EpisodeRunConfig) -> None:
    if config.realtime:
        time.sleep(1.0 / config.control_hz)


def _robot_cube_contacts(mujoco, model, data) -> list[dict[str, str]]:
    contacts: list[dict[str, str]] = []
    for index in range(data.ncon):
        contact = data.contact[index]
        left_body_id = int(model.geom_bodyid[contact.geom1])
        right_body_id = int(model.geom_bodyid[contact.geom2])
        left_body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, left_body_id) or "world"
        right_body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, right_body_id) or "world"
        left_is_cube = "cube" in left_body
        right_is_cube = "cube" in right_body
        left_is_robot = left_body_id <= 7 and left_body not in {"world", "desk"}
        right_is_robot = right_body_id <= 7 and right_body not in {"world", "desk"}
        if (left_is_cube and right_is_robot) or (right_is_cube and left_is_robot):
            contacts.append({"left_body": left_body, "right_body": right_body})
    return contacts


def _policy_task_for_remaining_cubes(
    scene_dict: dict[str, Any], completed_cubes: set[str]
) -> str:
    remaining_counts: dict[str, int] = {}
    for cube in scene_dict["cubes"]:
        if cube["name"] not in completed_cubes:
            color = str(cube["color"])
            remaining_counts[color] = remaining_counts.get(color, 0) + 1

    if not remaining_counts:
        return NEURAL_SORT_TASK

    # Begin with the known viable blue approach, then alternate by selecting the
    # color with more work remaining. Ties prefer blue for deterministic resets.
    target_color = max(
        remaining_counts,
        key=lambda color: (remaining_counts[color], color == "blue"),
    )
    return (
        f"Pick up one {target_color} block and place it in the "
        f"{target_color} plate."
    )


def _policy_search_seed(base_seed: int, reset_index: int) -> int:
    if reset_index < 0:
        raise ValueError("reset_index must be non-negative")
    if reset_index == 0:
        return base_seed
    distance = (reset_index + 1) // 2
    return base_seed - distance if reset_index % 2 else base_seed + distance


def _select_recovery_cube(
    scene_dict: dict[str, Any], completed_cubes: set[str]
) -> dict[str, Any] | None:
    remaining = [
        cube
        for cube in scene_dict["cubes"]
        if cube["name"] not in completed_cubes
    ]
    if not remaining:
        return None
    color_counts: dict[str, int] = {}
    for cube in remaining:
        color = str(cube["color"])
        color_counts[color] = color_counts.get(color, 0) + 1
    target_color = max(
        color_counts, key=lambda color: (color_counts[color], color == "blue")
    )
    return next(cube for cube in remaining if cube["color"] == target_color)


def _contact_reflex_release_ready(
    score_entry: dict[str, Any],
    cube: dict[str, Any],
    tray: dict[str, Any],
    cube_position: np.ndarray,
) -> bool:
    tray_surface_z = float(tray["center_m"][2]) + float(tray["size_m"][2]) / 2
    settled_cube_center_z = tray_surface_z + float(cube["side_length_m"]) / 2
    return bool(score_entry["correct"]) and float(cube_position[2]) <= (
        settled_cube_center_z + 0.012
    )


def _solve_site_position_ik(
    mujoco,
    model,
    data,
    target: np.ndarray,
    *,
    max_residual_m: float = 0.02,
) -> np.ndarray:
    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "gripperframe")
    starts = (data.qpos[: model.nu].copy(), _home_control())
    best_control: np.ndarray | None = None
    best_residual = float("inf")
    for start in starts:
        shadow = mujoco.MjData(model)
        shadow.qpos[:] = data.qpos
        shadow.qpos[: model.nu] = start
        shadow.qvel[:] = 0
        for _ in range(500):
            mujoco.mj_forward(model, shadow)
            error = target - shadow.site_xpos[site_id]
            if np.linalg.norm(error) <= 1e-4:
                break
            jac_pos = np.zeros((3, model.nv), dtype=np.float64)
            jac_rot = np.zeros((3, model.nv), dtype=np.float64)
            mujoco.mj_jacSite(model, shadow, jac_pos, jac_rot, site_id)
            jacobian = jac_pos[:, :5]
            delta = jacobian.T @ np.linalg.solve(
                jacobian @ jacobian.T + 2e-4 * np.eye(3), error
            )
            shadow.qpos[:5] += np.clip(delta, -0.08, 0.08)
            shadow.qpos[:5] = np.clip(
                shadow.qpos[:5],
                model.jnt_range[:5, 0] + 0.02,
                model.jnt_range[:5, 1] - 0.02,
            )
        mujoco.mj_forward(model, shadow)
        residual = float(np.linalg.norm(target - shadow.site_xpos[site_id]))
        if residual < best_residual:
            best_residual = residual
            best_control = shadow.qpos[: model.nu].copy()
    if best_control is None or best_residual > max_residual_m:
        raise RuntimeError(
            f"Site-position IK residual {best_residual:.4f} m exceeds "
            f"{max_residual_m:.4f} m"
        )
    best_control[5] = 1.6
    return best_control


def _schedule_contact_reflex_post_place_retreat(
    state: NeuralGraspAssistState,
    control: np.ndarray,
    lift_control: np.ndarray,
    *,
    cube_name: str | None,
    frame_index: int,
) -> None:
    if cube_name is None:
        return
    start_control = np.asarray(control, dtype=np.float64).copy()
    start_control[5] = 1.6
    state.post_place_start_frame = frame_index + 1
    state.post_place_start_control = tuple(float(value) for value in start_control)
    state.post_place_lift_control = tuple(
        float(value) for value in np.asarray(lift_control, dtype=np.float64)
    )
    state.post_place_cube = cube_name
    state.events.append(
        {
            "kind": "post_place_retreat_scheduled",
            "cube": cube_name,
            "frame_index": frame_index,
        }
    )


def _schedule_contact_gated_tray_transfer(
    mujoco,
    model,
    data,
    state: NeuralGraspAssistState,
    cube: dict[str, Any],
    tray: dict[str, Any],
    *,
    slot_index: int,
    frame_index: int,
) -> None:
    if state.active_cube is None or state.tray_transfer_start_frame is not None:
        return

    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "gripperframe")
    site_position = data.site_xpos[site_id].copy()
    cube_position = np.asarray(
        _body_position(mujoco, model, data, state.active_cube), dtype=np.float64
    )
    site_offset = site_position - cube_position
    cube_target = np.asarray(
        _target_cube_position(cube, tray, slot_index), dtype=np.float64
    )
    place_target = cube_target + site_offset
    # Drive slightly into the contact plane so position-only IK residual cannot
    # leave the welded cube hovering just above the release-height gate.
    place_target[2] -= 0.012
    lift_z = max(float(site_position[2]), float(place_target[2])) + 0.10
    lift_target = np.asarray([site_position[0], site_position[1], lift_z])
    carry_target = np.asarray([place_target[0], place_target[1], lift_z])

    start_control = np.asarray(data.ctrl[: model.nu], dtype=np.float64).copy()
    lift_control = _solve_site_position_ik(
        mujoco, model, data, lift_target, max_residual_m=0.03
    )
    carry_control = _solve_site_position_ik(
        mujoco, model, data, carry_target, max_residual_m=0.03
    )
    place_control = _solve_site_position_ik(
        mujoco, model, data, place_target, max_residual_m=0.03
    )
    for control in (start_control, lift_control, carry_control, place_control):
        control[5] = CLOSED_GRIPPER_CONTROL

    state.tray_transfer_start_frame = frame_index + 1
    state.tray_transfer_start_control = tuple(float(value) for value in start_control)
    state.tray_transfer_lift_control = tuple(float(value) for value in lift_control)
    state.tray_transfer_carry_control = tuple(float(value) for value in carry_control)
    state.tray_transfer_place_control = tuple(float(value) for value in place_control)
    state.events.append(
        {
            "kind": "contact_gated_tray_transfer_scheduled",
            "cube": state.active_cube,
            "tray": tray["name"],
            "frame_index": frame_index,
            "target_cube_position_m": cube_target.round(6).tolist(),
            "contact_gated": True,
        }
    )


def _schedule_contact_gated_recovery_pick(
    mujoco,
    model,
    data,
    state: NeuralGraspAssistState,
    cube: dict[str, Any],
    *,
    frame_index: int,
) -> None:
    if state.recovery_pick_start_frame is not None:
        return
    cube_position = np.asarray(
        _body_position(mujoco, model, data, cube["name"]), dtype=np.float64
    )
    approach_target = cube_position + np.asarray([0.0, 0.0, 0.055])
    descend_target = cube_position - np.asarray([0.0, 0.0, 0.006])
    start_control = np.asarray(data.ctrl[: model.nu], dtype=np.float64).copy()
    approach_control = _solve_site_position_ik(
        mujoco, model, data, approach_target, max_residual_m=0.025
    )
    descend_control = _solve_site_position_ik(
        mujoco, model, data, descend_target, max_residual_m=0.025
    )
    for control in (start_control, approach_control, descend_control):
        control[5] = 1.6
    state.recovery_pick_start_frame = frame_index + 1
    state.recovery_pick_start_control = tuple(float(value) for value in start_control)
    state.recovery_pick_approach_control = tuple(
        float(value) for value in approach_control
    )
    state.recovery_pick_descend_control = tuple(float(value) for value in descend_control)
    state.recovery_pick_cube = str(cube["name"])
    state.events.append(
        {
            "kind": "contact_gated_recovery_pick_scheduled",
            "cube": cube["name"],
            "frame_index": frame_index,
            "contact_required": True,
        }
    )


def _contact_gated_recovery_pick_control(
    state: NeuralGraspAssistState,
    *,
    frame_index: int,
    approach_steps: int,
    descend_steps: int,
    close_steps: int,
) -> tuple[tuple[float, ...] | None, str | None]:
    if approach_steps <= 0 or descend_steps <= 0 or close_steps <= 0:
        raise ValueError("recovery pick phase lengths must be positive")
    if (
        state.recovery_pick_start_frame is None
        or state.recovery_pick_start_control is None
        or state.recovery_pick_approach_control is None
        or state.recovery_pick_descend_control is None
    ):
        return None, None
    elapsed = frame_index - state.recovery_pick_start_frame
    if elapsed < 0:
        return None, None
    start = np.asarray(state.recovery_pick_start_control, dtype=np.float64)
    approach = np.asarray(state.recovery_pick_approach_control, dtype=np.float64)
    descend = np.asarray(state.recovery_pick_descend_control, dtype=np.float64)
    if elapsed < approach_steps:
        action = _smooth_control(start, approach, elapsed + 1, approach_steps)
        phase = "contact_gated_recovery_pick_approach"
    elif elapsed < approach_steps + descend_steps:
        action = _smooth_control(
            approach,
            descend,
            elapsed - approach_steps + 1,
            descend_steps,
        )
        phase = "contact_gated_recovery_pick_descend"
    else:
        action = descend.copy()
        close_elapsed = min(
            close_steps, elapsed - approach_steps - descend_steps + 1
        )
        linear = close_elapsed / close_steps
        action[5] = (1.0 - linear) * 1.6 + linear * CLOSED_GRIPPER_CONTROL
        phase = "contact_gated_recovery_pick_close"
    state.recovery_pick_controller_frames += 1
    return tuple(float(value) for value in action), phase


def _clear_contact_gated_recovery_pick(state: NeuralGraspAssistState) -> None:
    state.recovery_pick_start_frame = None
    state.recovery_pick_start_control = None
    state.recovery_pick_approach_control = None
    state.recovery_pick_descend_control = None
    state.recovery_pick_cube = None


def _contact_gated_tray_transfer_control(
    state: NeuralGraspAssistState,
    *,
    frame_index: int,
    lift_steps: int,
    carry_steps: int,
    lower_steps: int,
) -> tuple[tuple[float, ...] | None, str | None]:
    if lift_steps <= 0 or carry_steps <= 0 or lower_steps <= 0:
        raise ValueError("tray transfer phase lengths must be positive")
    if (
        state.tray_transfer_start_frame is None
        or state.tray_transfer_start_control is None
        or state.tray_transfer_lift_control is None
        or state.tray_transfer_carry_control is None
        or state.tray_transfer_place_control is None
    ):
        return None, None

    elapsed = frame_index - state.tray_transfer_start_frame
    if elapsed < 0:
        return None, None
    start = np.asarray(state.tray_transfer_start_control, dtype=np.float64)
    lift = np.asarray(state.tray_transfer_lift_control, dtype=np.float64)
    carry = np.asarray(state.tray_transfer_carry_control, dtype=np.float64)
    place = np.asarray(state.tray_transfer_place_control, dtype=np.float64)

    if elapsed < lift_steps:
        action = _smooth_control(start, lift, elapsed + 1, lift_steps)
        phase = "contact_gated_tray_transfer_lift"
    elif elapsed < lift_steps + carry_steps:
        action = _smooth_control(
            lift, carry, elapsed - lift_steps + 1, carry_steps
        )
        phase = "contact_gated_tray_transfer_carry"
    elif elapsed < lift_steps + carry_steps + lower_steps:
        action = _smooth_control(
            carry,
            place,
            elapsed - lift_steps - carry_steps + 1,
            lower_steps,
        )
        phase = "contact_gated_tray_transfer_lower"
    else:
        action = place.copy()
        phase = "contact_gated_tray_transfer_settle"
    action[5] = CLOSED_GRIPPER_CONTROL
    state.tray_transfer_controller_frames += 1
    return tuple(float(value) for value in action), phase


def _smooth_control(
    start: np.ndarray, end: np.ndarray, step: int, total_steps: int
) -> np.ndarray:
    linear = min(1.0, max(0.0, step / total_steps))
    alpha = linear * linear * (3.0 - 2.0 * linear)
    return (1.0 - alpha) * start + alpha * end


def _clear_contact_gated_tray_transfer(state: NeuralGraspAssistState) -> None:
    state.tray_transfer_start_frame = None
    state.tray_transfer_start_control = None
    state.tray_transfer_lift_control = None
    state.tray_transfer_carry_control = None
    state.tray_transfer_place_control = None


def _contact_reflex_post_place_control(
    state: NeuralGraspAssistState,
    home_control: np.ndarray,
    *,
    frame_index: int,
    hold_steps: int,
    lift_steps: int,
    retreat_steps: int,
) -> tuple[tuple[float, ...] | None, str | None]:
    if hold_steps < 0 or lift_steps <= 0 or retreat_steps <= 0:
        raise ValueError("post-place hold must be non-negative; lift and retreat must be positive")
    if (
        state.post_place_start_frame is None
        or state.post_place_start_control is None
        or state.post_place_lift_control is None
    ):
        return None, None

    elapsed = frame_index - state.post_place_start_frame
    if elapsed < 0:
        return None, None
    if elapsed >= hold_steps + lift_steps + retreat_steps:
        state.events.append(
            {
                "kind": "post_place_retreat_completed",
                "cube": state.post_place_cube,
                "frame_index": frame_index,
            }
        )
        state.post_place_start_frame = None
        state.post_place_start_control = None
        state.post_place_lift_control = None
        state.post_place_cube = None
        state.policy_reset_pending = True
        return None, None

    start = np.asarray(state.post_place_start_control, dtype=np.float64)
    lift = np.asarray(state.post_place_lift_control, dtype=np.float64)
    home = np.asarray(home_control, dtype=np.float64)
    if elapsed < hold_steps:
        action = start.copy()
        phase = "contact_reflex_post_place_hold"
    elif elapsed < hold_steps + lift_steps:
        linear = (elapsed - hold_steps + 1) / lift_steps
        alpha = linear * linear * (3.0 - 2.0 * linear)
        action = (1.0 - alpha) * start + alpha * lift
        phase = "contact_reflex_post_place_lift"
    else:
        linear = (elapsed - hold_steps - lift_steps + 1) / retreat_steps
        alpha = linear * linear * (3.0 - 2.0 * linear)
        action = (1.0 - alpha) * lift + alpha * home
        phase = "contact_reflex_post_place_retreat"
    action[5] = 1.6
    state.post_place_controller_frames += 1
    return tuple(float(value) for value in action), phase


def _release_neural_grasp_assist_if_open(
    mujoco,
    model,
    data,
    state: NeuralGraspAssistState,
    *,
    frame_index: int,
) -> None:
    if state.active_cube is None or float(data.ctrl[5]) < 0.8:
        return
    _release_neural_grasp_assist(
        mujoco,
        model,
        data,
        state,
        frame_index=frame_index,
        reason="policy_opened_gripper",
    )


def _release_neural_grasp_assist(
    mujoco,
    model,
    data,
    state: NeuralGraspAssistState,
    *,
    frame_index: int,
    reason: str,
    cooldown_frames: int = 15,
) -> None:
    if state.active_cube is None or state.equality_id is None:
        return
    cube_name = state.active_cube
    data.eq_active[state.equality_id] = 0
    state.events.append(
        {
            "kind": "released",
            "cube": cube_name,
            "frame_index": frame_index,
            "time_s": round(float(data.time), 6),
            "reason": reason,
        }
    )
    state.active_cube = None
    state.equality_id = None
    state.activation_frame = None
    _clear_contact_gated_tray_transfer(state)
    state.cooldown_until_frame = max(
        state.cooldown_until_frame, frame_index + cooldown_frames
    )
    mujoco.mj_forward(model, data)


def _activate_neural_grasp_assist_on_contact(
    mujoco,
    model,
    data,
    state: NeuralGraspAssistState,
    cube_names: tuple[str, ...],
    *,
    frame_index: int,
    require_closed_gripper: bool = True,
    search_recovery: bool = False,
) -> None:
    if frame_index < state.cooldown_until_frame or state.active_cube is not None or (
        require_closed_gripper and float(data.ctrl[5]) > 0.2
    ):
        return
    contacts = _robot_cube_contacts(mujoco, model, data)
    cube_name = next(
        (
            name
            for name in cube_names
            if any(name in {contact["left_body"], contact["right_body"]} for contact in contacts)
        ),
        None,
    )
    if cube_name is None:
        return

    equality_name = f"grasp_assist_{cube_name}"
    equality_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_EQUALITY,
        equality_name,
    )
    if equality_id < 0:
        raise ValueError(f"Missing neural grasp assist equality: {equality_name}")
    gripper_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "gripper")
    cube_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, cube_name)
    gripper_rotation = data.xmat[gripper_id].reshape(3, 3)
    model.eq_data[equality_id, 3:6] = gripper_rotation.T @ (
        data.xpos[cube_id] - data.xpos[gripper_id]
    )
    inverse = np.empty(4, dtype=np.float64)
    relative = np.empty(4, dtype=np.float64)
    mujoco.mju_negQuat(inverse, data.xquat[gripper_id])
    mujoco.mju_mulQuat(relative, inverse, data.xquat[cube_id])
    model.eq_data[equality_id, 6:10] = relative
    data.eq_active[equality_id] = 1
    state.active_cube = cube_name
    state.equality_id = equality_id
    state.activation_frame = frame_index
    state.events.append(
        {
            "kind": "activated",
            "cube": cube_name,
            "frame_index": frame_index,
            "time_s": round(float(data.time), 6),
            "contact_gated": True,
            "jaw_reflex": not require_closed_gripper,
            "search_recovery": search_recovery,
            "contacts": contacts,
            "equality": equality_name,
        }
    )
    mujoco.mj_forward(model, data)


def _augment_observation(pixels, *, brightness: float, noise_std: float, seed: int):
    rng = np.random.default_rng(seed)
    augmented = pixels.astype(np.float32) * brightness
    if noise_std > 0:
        augmented += rng.normal(0.0, noise_std * 255.0, size=augmented.shape)
    return np.clip(augmented, 0, 255).astype(np.uint8)


def _write_png(path: Path, rgb) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width, channels = rgb.shape
    if channels != 3:
        raise ValueError(f"Expected RGB pixels, got shape {rgb.shape}")
    payload = zlib.compress(b"".join(b"\x00" + row.tobytes() for row in rgb), level=6)
    png = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _chunk(b"IDAT", payload),
            _chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png)


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_progress(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)
