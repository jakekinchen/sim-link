"""Physically causal SO-101 sorting demonstrations for SceneSmith workcells."""

from __future__ import annotations

import random

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

from scenesmith.robot_lab.scoring import score_cube_sort
from scenesmith.robot_lab.so101_coordinates import (
    BODY_JOINT_OFFSETS_DEG,
    BODY_JOINT_SIGNS,
    GRIPPER_RANGE_RAD,
    mujoco_to_lerobot,
)
from scenesmith.robot_lab.spec import RobotLabScene, RobotLabTray


JOINT_NAMES = (
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
)
TASK = "Sort each colored block onto the plate of the matching color."
SIMULATION_HOME = (0.050438, -1.697719, 1.549157, 1.059675, -0.053182, 1.6)


@dataclass(frozen=True)
class CausalSortExpertConfig:
    control_hz: int = 30
    image_size: int = 224
    settle_frames: int = 8
    approach_frames: int = 32
    descend_frames: int = 42
    close_frames: int = 14
    lift_frames: int = 34
    carry_frames: int = 46
    place_frames: int = 40
    place_settle_frames: int = 15
    release_settle_frames: int = 8
    release_frames: int = 12
    post_release_settle_frames: int = 8
    retreat_frames: int = 24
    lift_clearance_m: float = 0.05
    damping: float = 2e-4
    ik_tolerance_m: float = 1e-4
    # Randomized far-tray carries can sit just beyond the arm's exact Cartesian
    # envelope. Keep the accepted miss tightly bounded while allowing the
    # physics-scored episode to decide whether the resulting placement is valid.
    ik_max_residual_m: float = 0.020
    capture_images: bool = True


FrameSink = Callable[[dict[str, Any], dict[str, np.ndarray]], None]


class CausalSortExpert:
    """Joint-space expert with contact-gated grasp assistance.

    The assist weld is inactive during approach and closing. It is activated only
    after MuJoCo reports robot-cube contact, and it is released before the gripper
    opens. This prevents the old dataset's non-causal object teleports while making
    stable low-cost grasp demonstrations possible with the upstream SO-101 meshes.
    """

    def __init__(
        self,
        scene: RobotLabScene,
        xml_path: Path,
        *,
        seed: int,
        frame_sink: FrameSink,
        config: CausalSortExpertConfig = CausalSortExpertConfig(),
        brightness: float = 1.0,
        noise_std: float = 0.0,
    ) -> None:
        try:
            import mujoco
        except ModuleNotFoundError as exc:
            raise RuntimeError("mujoco is required to run the causal sorting expert") from exc

        if config.control_hz <= 0 or config.image_size <= 0:
            raise ValueError("control_hz and image_size must be positive")
        self.mujoco = mujoco
        self.scene = scene
        self.scene_dict = scene.to_dict()
        self.seed = seed
        self.frame_sink = frame_sink
        self.config = config
        self.brightness = brightness
        self.noise_std = noise_std
        self.model = mujoco.MjModel.from_xml_path(str(xml_path))
        self.data = mujoco.MjData(self.model)
        self.renderer = (
            mujoco.Renderer(
                self.model,
                height=config.image_size,
                width=config.image_size,
            )
            if config.capture_images
            else None
        )
        self.gripper_site_id = self._id(mujoco.mjtObj.mjOBJ_SITE, "gripperframe")
        self.gripper_body_id = self._id(mujoco.mjtObj.mjOBJ_BODY, "gripper")
        base_body_id = self._id(mujoco.mjtObj.mjOBJ_BODY, "base")
        self.robot_body_ids = {
            body_id
            for body_id in range(self.model.nbody)
            if self._is_descendant_of(body_id, base_body_id)
        }
        self.cube_body_ids = {
            cube.name: self._id(mujoco.mjtObj.mjOBJ_BODY, cube.name)
            for cube in scene.cubes
        }
        self.first_cube_body_id = min(self.cube_body_ids.values())
        self.frame_index = 0
        self.phase_counts: dict[str, int] = {}
        self.grasp_events: list[dict[str, Any]] = []
        self.last_images: dict[str, np.ndarray] = {}

    def close(self) -> None:
        if self.renderer is not None:
            self.renderer.close()
        self.frame_sink = lambda _frame, _images: None

    def run(self) -> dict[str, Any]:
        mujoco = self.mujoco
        home = np.asarray(SIMULATION_HOME, dtype=np.float64)
        self.data.qpos[: self.model.nu] = home
        self.data.ctrl[: self.model.nu] = home
        mujoco.mj_forward(self.model, self.data)
        for _ in range(max(1, round(0.35 / self.model.opt.timestep))):
            mujoco.mj_step(self.model, self.data)

        self._hold("reset_settle", self.config.settle_frames)
        target_counts: dict[str, int] = {}
        cube_order = list(self.scene.cubes)
        random.Random(self.seed).shuffle(cube_order)
        for cube in cube_order:
            tray = next(tray for tray in self.scene.trays if tray.color == cube.color)
            slot = target_counts.get(cube.color, 0)
            target_counts[cube.color] = slot + 1
            self._sort_cube(cube.name, cube.side_length_m, tray, slot)

        self._hold("final_settle", self.config.settle_frames)
        cube_states = self._cube_states()
        score = score_cube_sort(cube_states, self.scene.trays)
        return {
            "status": "pass" if score["success"] else "fail",
            "seed": self.seed,
            "task": TASK,
            "frames": self.frame_index,
            "phase_counts": self.phase_counts,
            "cube_order": [cube.name for cube in cube_order],
            "grasp_events": self.grasp_events,
            "all_grasps_contact_gated": bool(self.grasp_events)
            and all(event["contact_before_assist"] for event in self.grasp_events),
            "object_motion_mode": "mujoco_contact_plus_contact_gated_weld_assist",
            "final_cube_states": cube_states,
            "final_score": score,
        }

    def render(self, camera: str) -> np.ndarray:
        if self.renderer is None:
            raise RuntimeError("Image capture is disabled for this expert")
        self.renderer.update_scene(self.data, camera=camera)
        return self.renderer.render().copy()

    def _sort_cube(
        self,
        cube_name: str,
        cube_side_m: float,
        tray: RobotLabTray,
        slot: int,
    ) -> None:
        cube_start = self._body_position(cube_name)
        high_start = cube_start + np.array([0.0, 0.0, self.config.lift_clearance_m])
        self._move_site(f"{cube_name}_approach", high_start, self.config.approach_frames, 1.6)
        self._move_site(
            f"{cube_name}_descend",
            cube_start - np.array([0.0, 0.0, 0.006]),
            self.config.descend_frames,
            1.6,
        )
        self._hold(f"{cube_name}_grasp_settle", 6)
        self._move_gripper(f"{cube_name}_close", -0.17, self.config.close_frames)

        contacts = self._robot_cube_contacts(cube_name)
        if not contacts:
            contacts = self._reacquire_grasp(cube_name)
        if not contacts:
            raise RuntimeError(f"No robot contact before grasp assist for {cube_name}")
        assist_id = self._activate_grasp_assist(cube_name)
        cube_attached = self._body_position(cube_name)
        site_to_cube = self.data.site_xpos[self.gripper_site_id].copy() - cube_attached
        event = {
            "cube": cube_name,
            "frame_index": self.frame_index,
            "time_s": round(float(self.data.time), 6),
            "contact_before_assist": True,
            "contacts": contacts,
            "assist_name": f"grasp_assist_{cube_name}",
        }
        self.grasp_events.append(event)

        target_cube = self._tray_target(tray, cube_side_m, slot)
        self._move_site(
            f"{cube_name}_lift",
            cube_attached + site_to_cube + np.array([0.0, 0.0, self.config.lift_clearance_m]),
            self.config.lift_frames,
            -0.17,
        )
        self._move_site(
            f"{cube_name}_carry",
            target_cube + site_to_cube + np.array([0.0, 0.0, self.config.lift_clearance_m]),
            self.config.carry_frames,
            -0.17,
        )
        self._move_site(
            f"{cube_name}_place",
            target_cube + site_to_cube,
            self.config.place_frames,
            -0.17,
        )
        self._hold(f"{cube_name}_place_settle", self.config.place_settle_frames)
        self.data.eq_active[assist_id] = 0
        self._hold(f"{cube_name}_release_settle", self.config.release_settle_frames)
        self._move_gripper(f"{cube_name}_release", 1.6, self.config.release_frames)
        self._hold(
            f"{cube_name}_post_release_settle",
            self.config.post_release_settle_frames,
        )
        self._move_site(
            f"{cube_name}_retreat",
            target_cube + site_to_cube + np.array([0.0, 0.0, self.config.lift_clearance_m]),
            self.config.retreat_frames,
            1.6,
        )
        self._move_site(
            f"{cube_name}_safe_traverse",
            np.asarray([0.18, 0.0, 0.42], dtype=np.float64),
            self.config.retreat_frames,
            1.6,
        )
        self._move_control(
            f"{cube_name}_return_home",
            np.asarray(SIMULATION_HOME, dtype=np.float64),
            self.config.retreat_frames,
        )
        event["released_frame_index"] = self.frame_index
        event["released_cube_position_m"] = self._body_position(cube_name).round(6).tolist()

    def _move_site(self, phase: str, target: np.ndarray, frames: int, gripper: float) -> None:
        target_control = self._solve_ik(target)
        target_control[5] = gripper
        self._move_control(phase, target_control, frames)

    def _move_gripper(self, phase: str, target: float, frames: int) -> None:
        target_control = self.data.ctrl[: self.model.nu].copy()
        target_control[5] = target
        self._move_control(phase, target_control, frames)

    def _hold(self, phase: str, frames: int) -> None:
        self._move_control(phase, self.data.ctrl[: self.model.nu].copy(), frames)

    def _move_control(self, phase: str, target_control: np.ndarray, frames: int) -> None:
        if frames <= 0:
            return
        start = self.data.ctrl[: self.model.nu].copy()
        for index in range(frames):
            linear = (index + 1) / frames
            alpha = linear * linear * (3.0 - 2.0 * linear)
            action = (1.0 - alpha) * start + alpha * target_control
            self._record_and_step(phase, action)

    def _record_and_step(self, phase: str, action: np.ndarray) -> None:
        images = (
            {
                "top": self._capture("cam1_overhead", 0),
                "wrist": self._capture("cam2_wrist", 1),
            }
            if self.config.capture_images
            else {}
        )
        state = self._mujoco_to_lerobot(self.data.qpos[: self.model.nu])
        policy_action = self._mujoco_to_lerobot(action)
        contacts = self._all_robot_cube_contacts()
        active_assists = [
            self.mujoco.mj_id2name(
                self.model,
                self.mujoco.mjtObj.mjOBJ_EQUALITY,
                index,
            )
            for index, active in enumerate(self.data.eq_active)
            if active
        ]
        frame = {
            "frame_index": self.frame_index,
            "time_s": round(float(self.data.time), 6),
            "phase": phase,
            "state": state,
            "action": policy_action,
            "mujoco_qpos": self.data.qpos[: self.model.nu].astype(float).tolist(),
            "mujoco_qvel": self.data.qvel[: self.model.nu].astype(float).tolist(),
            "mujoco_requested_action": np.asarray(action, dtype=np.float64).tolist(),
            "mujoco_actuator_effort": self.data.qfrc_actuator[: self.model.nu]
            .astype(float)
            .tolist(),
            "robot_cube_contacts": contacts,
            "grasp_assists_active": active_assists,
            "cube_positions_m": {
                name: self._body_position(name).round(6).tolist()
                for name in self.cube_body_ids
            },
        }
        self.frame_sink(frame, images)
        self.last_images = images
        self.data.ctrl[: self.model.nu] = action
        self._step_control_period()
        self.phase_counts[phase] = self.phase_counts.get(phase, 0) + 1
        self.frame_index += 1

    def _capture(self, camera: str, camera_index: int) -> np.ndarray:
        if self.renderer is None:
            raise RuntimeError("Image capture is disabled for this expert")
        self.renderer.update_scene(self.data, camera=camera)
        pixels = self.renderer.render().copy()
        if self.brightness == 1.0 and self.noise_std <= 0:
            return pixels
        rng = np.random.default_rng(
            self.seed * 100_003 + self.frame_index * 17 + camera_index
        )
        augmented = pixels.astype(np.float32) * self.brightness
        if self.noise_std > 0:
            augmented += rng.normal(0.0, self.noise_std * 255.0, pixels.shape)
        return np.clip(augmented, 0, 255).astype(np.uint8)

    def _solve_ik(self, target: np.ndarray) -> np.ndarray:
        starts = [
            self.data.qpos[: self.model.nu].copy(),
            np.asarray(SIMULATION_HOME, dtype=np.float64),
        ]
        best_control: np.ndarray | None = None
        best_residual = float("inf")
        for start in starts:
            shadow = self.mujoco.MjData(self.model)
            shadow.qpos[:] = self.data.qpos
            shadow.qpos[: self.model.nu] = start
            shadow.qvel[:] = 0
            for _ in range(500):
                self.mujoco.mj_forward(self.model, shadow)
                error = target - shadow.site_xpos[self.gripper_site_id]
                if np.linalg.norm(error) <= self.config.ik_tolerance_m:
                    break
                jac_pos = np.zeros((3, self.model.nv), dtype=np.float64)
                jac_rot = np.zeros((3, self.model.nv), dtype=np.float64)
                self.mujoco.mj_jacSite(
                    self.model,
                    shadow,
                    jac_pos,
                    jac_rot,
                    self.gripper_site_id,
                )
                jacobian = jac_pos[:, :5]
                delta = jacobian.T @ np.linalg.solve(
                    jacobian @ jacobian.T + self.config.damping * np.eye(3),
                    error,
                )
                shadow.qpos[:5] += np.clip(delta, -0.08, 0.08)
                shadow.qpos[:5] = np.clip(
                    shadow.qpos[:5],
                    self.model.jnt_range[:5, 0] + 0.02,
                    self.model.jnt_range[:5, 1] - 0.02,
                )
            self.mujoco.mj_forward(self.model, shadow)
            residual = float(
                np.linalg.norm(target - shadow.site_xpos[self.gripper_site_id])
            )
            if residual < best_residual:
                best_residual = residual
                best_control = shadow.qpos[: self.model.nu].copy()
            if residual <= self.config.ik_tolerance_m:
                break
        if best_control is None or best_residual > self.config.ik_max_residual_m:
            raise RuntimeError(
                f"IK residual {best_residual:.4f} m exceeds limit for target {target}"
            )
        return best_control

    def _activate_grasp_assist(self, cube_name: str) -> int:
        mujoco = self.mujoco
        assist_id = self._id(
            mujoco.mjtObj.mjOBJ_EQUALITY,
            f"grasp_assist_{cube_name}",
        )
        cube_body_id = self.cube_body_ids[cube_name]
        gripper_rotation = self.data.xmat[self.gripper_body_id].reshape(3, 3)
        self.model.eq_data[assist_id, 3:6] = gripper_rotation.T @ (
            self.data.xpos[cube_body_id] - self.data.xpos[self.gripper_body_id]
        )
        inverse = np.empty(4, dtype=np.float64)
        relative = np.empty(4, dtype=np.float64)
        mujoco.mju_negQuat(inverse, self.data.xquat[self.gripper_body_id])
        mujoco.mju_mulQuat(relative, inverse, self.data.xquat[cube_body_id])
        self.model.eq_data[assist_id, 6:10] = relative
        self.data.eq_active[assist_id] = 1
        mujoco.mj_forward(self.model, self.data)
        return assist_id

    def _reacquire_grasp(self, cube_name: str) -> list[dict[str, Any]]:
        offsets = (
            np.array([0.0, 0.0, -0.010]),
            np.array([0.005, 0.0, -0.012]),
            np.array([-0.005, 0.0, -0.012]),
        )
        for attempt, offset in enumerate(offsets, start=1):
            self._move_gripper(f"{cube_name}_reopen_{attempt}", 1.6, 6)
            current = self._body_position(cube_name)
            self._move_site(
                f"{cube_name}_reacquire_{attempt}",
                current + offset,
                12,
                1.6,
            )
            self._move_gripper(f"{cube_name}_reclose_{attempt}", -0.17, 8)
            contacts = self._robot_cube_contacts(cube_name)
            if contacts:
                return contacts
        return []

    def _robot_cube_contacts(self, cube_name: str) -> list[dict[str, Any]]:
        cube_body_id = self.cube_body_ids[cube_name]
        return [
            contact
            for contact in self._all_robot_cube_contacts()
            if cube_name in {contact["body1"], contact["body2"]}
            and cube_body_id in {contact["body1_id"], contact["body2_id"]}
        ]

    def _all_robot_cube_contacts(self) -> list[dict[str, Any]]:
        contacts: list[dict[str, Any]] = []
        cube_ids = set(self.cube_body_ids.values())
        for index in range(self.data.ncon):
            contact = self.data.contact[index]
            body1 = int(self.model.geom_bodyid[contact.geom1])
            body2 = int(self.model.geom_bodyid[contact.geom2])
            cube_id = body1 if body1 in cube_ids else body2 if body2 in cube_ids else None
            other_id = body2 if cube_id == body1 else body1
            if cube_id is None or other_id not in self.robot_body_ids:
                continue
            contacts.append(
                {
                    "body1": self._body_name(body1),
                    "body2": self._body_name(body2),
                    "body1_id": body1,
                    "body2_id": body2,
                    "distance_m": round(float(contact.dist), 6),
                }
            )
        return contacts

    def _step_control_period(self) -> None:
        substeps = max(
            1,
            round((1.0 / self.config.control_hz) / self.model.opt.timestep),
        )
        for _ in range(substeps):
            self.mujoco.mj_step(self.model, self.data)

    def _cube_states(self) -> list[dict[str, Any]]:
        return [
            {
                "name": cube.name,
                "color": cube.color,
                "position_m": self._body_position(cube.name).round(6).tolist(),
            }
            for cube in self.scene.cubes
        ]

    def _body_position(self, name: str) -> np.ndarray:
        return self.data.xpos[self.cube_body_ids[name]].copy()

    def _body_name(self, body_id: int) -> str:
        return (
            self.mujoco.mj_id2name(
                self.model,
                self.mujoco.mjtObj.mjOBJ_BODY,
                body_id,
            )
            or "world"
        )

    def _is_descendant_of(self, body_id: int, ancestor_id: int) -> bool:
        current = body_id
        while current > 0:
            if current == ancestor_id:
                return True
            current = int(self.model.body_parentid[current])
        return False

    def _id(self, object_type, name: str) -> int:
        object_id = self.mujoco.mj_name2id(self.model, object_type, name)
        if object_id < 0:
            raise ValueError(f"MuJoCo object not found: {name}")
        return object_id

    @staticmethod
    def _tray_target(tray: RobotLabTray, cube_side_m: float, slot: int) -> np.ndarray:
        toward_center = -1.0 if tray.center_m[1] > 0 else 1.0
        return np.asarray(
            [
                tray.center_m[0] + (-1.6 if slot % 2 == 0 else 0.4) * cube_side_m,
                tray.center_m[1] + toward_center * 0.75 * cube_side_m,
                tray.center_m[2]
                + tray.size_m[2] / 2
                + cube_side_m / 2
                + 0.003,
            ],
            dtype=np.float64,
        )

    @staticmethod
    def _mujoco_to_lerobot(values: np.ndarray) -> list[float]:
        return mujoco_to_lerobot(values, round_digits=6)
