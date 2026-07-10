"""Deterministic, validity-preserving randomization for robot-lab scenes."""

from __future__ import annotations

import json
import math
import random
import xml.etree.ElementTree as ET

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.spec import RobotLabCube, RobotLabScene, RobotLabTray


@dataclass(frozen=True)
class DomainRandomizationConfig:
    """Bounds chosen for the SO-101 desk-sort reachable workspace."""

    tray_xy_jitter_m: tuple[float, float] = (0.025, 0.020)
    cube_xy_jitter_m: tuple[float, float] = (0.040, 0.040)
    cube_mass_scale: tuple[float, float] = (0.82, 1.18)
    cube_size_scale: tuple[float, float] = (0.94, 1.06)
    friction_scale: tuple[float, float] = (0.85, 1.20)
    light_intensity_scale: tuple[float, float] = (0.86, 1.14)
    side_camera_jitter_m: float = 0.010
    overhead_camera_jitter_m: float = 0.008
    room_color_jitter: float = 0.055
    desk_color_jitter: float = 0.050
    minimum_object_clearance_m: float = 0.012
    maximum_sampling_attempts: int = 120


DEFAULT_CONFIG = DomainRandomizationConfig()


def randomize_scene(
    scene: RobotLabScene,
    seed: int,
    *,
    config: DomainRandomizationConfig = DEFAULT_CONFIG,
) -> tuple[RobotLabScene, dict[str, Any]]:
    """Return one deterministic, collision-aware scene variant and manifest."""

    rng = random.Random(seed)
    room = replace(
        scene.room,
        wall_rgba=_jitter_rgba(rng, scene.room.wall_rgba, config.room_color_jitter),
        floor_rgba=_jitter_rgba(rng, scene.room.floor_rgba, config.room_color_jitter * 0.82),
    )
    desk = replace(scene.desk, rgba=_jitter_rgba(rng, scene.desk.rgba, config.desk_color_jitter))
    trays = _sample_trays(rng, scene, config)
    cubes = _sample_cubes(rng, scene, trays, config)

    randomized = replace(
        scene,
        scene_id=f"{scene.scene_id}_seed_{seed}",
        room=room,
        desk=desk,
        trays=trays,
        cubes=cubes,
        source={
            **scene.source,
            "domain_randomization": "scenesmith.robot_lab.domain_randomization.v2",
            "domain_randomization_seed": str(seed),
        },
    )
    manifest = build_domain_randomization_manifest(scene, randomized, seed, rng, config)
    validate_randomized_scene(randomized, config=config)
    return randomized, manifest


def build_domain_randomization_manifest(
    base_scene: RobotLabScene,
    randomized_scene: RobotLabScene,
    seed: int,
    rng: random.Random,
    config: DomainRandomizationConfig,
) -> dict[str, Any]:
    side_offset = [
        round(rng.uniform(-config.side_camera_jitter_m, config.side_camera_jitter_m), 6)
        for _ in range(3)
    ]
    overhead_offset = [
        round(rng.uniform(-config.overhead_camera_jitter_m, config.overhead_camera_jitter_m), 6)
        for _ in range(3)
    ]
    return {
        "schema_version": "scenesmith.domain_randomization.v2",
        "seed": seed,
        "base_scene_id": base_scene.scene_id,
        "scene_id": randomized_scene.scene_id,
        "config": _jsonable_config(config),
        "randomized_fields": {
            "room.wall_rgba": list(randomized_scene.room.wall_rgba),
            "room.floor_rgba": list(randomized_scene.room.floor_rgba),
            "desk.rgba": list(randomized_scene.desk.rgba),
            "trays": {
                tray.name: {"center_m": list(tray.center_m)} for tray in randomized_scene.trays
            },
            "cubes": {
                cube.name: {
                    "initial_position_m": list(cube.initial_position_m),
                    "side_length_m": cube.side_length_m,
                    "mass_kg": cube.mass_kg,
                }
                for cube in randomized_scene.cubes
            },
        },
        "mujoco": {
            "light_intensity_scale": round(rng.uniform(*config.light_intensity_scale), 6),
            "friction_scale": round(rng.uniform(*config.friction_scale), 6),
            "camera_position_offsets_m": {
                "cam0_side": side_offset,
                "cam1_overhead": overhead_offset,
            },
        },
        "observation_augmentation": {
            "camera_noise_std": round(rng.uniform(0.0035, 0.0110), 6),
            "brightness_scale": round(rng.uniform(0.92, 1.08), 6),
        },
        "fixed_fields": {
            "robot_base_position_m": list(randomized_scene.robot.base_position_m),
            "fiducials": {
                fiducial.name: {
                    "family": fiducial.family,
                    "tag_id": fiducial.tag_id,
                    "position_m": list(fiducial.position_m),
                    "euler_deg": list(fiducial.euler_deg),
                    "size_m": fiducial.size_m,
                }
                for fiducial in randomized_scene.fiducials
            },
            "apriltag_visibility": "expected_visible_not_policy_required",
            "wrist_camera_extrinsics": "fixed_to_physical_mount_contract",
        },
    }


def apply_mujoco_randomization(xml_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Apply manifest dynamics and sensor samples to an exported MuJoCo XML."""

    root = ET.parse(xml_path).getroot()
    settings = manifest["mujoco"]
    applied: dict[str, Any] = {"xml_path": str(xml_path), "cameras": {}}

    light = root.find("./worldbody/light[@name='key']")
    if light is None:
        raise ValueError(f"Missing key light in {xml_path}")
    light_scale = float(settings["light_intensity_scale"])
    diffuse = [round(min(1.0, 0.72 * light_scale), 6)] * 3
    light.set("diffuse", _numbers(diffuse))
    applied["key_light_diffuse"] = diffuse

    friction_default = root.find("./default/geom")
    if friction_default is None:
        raise ValueError(f"Missing default geom friction in {xml_path}")
    base_friction = [float(value) for value in friction_default.get("friction", "1 0.02 0.002").split()]
    friction_scale = float(settings["friction_scale"])
    friction = [round(value * friction_scale, 6) for value in base_friction]
    friction_default.set("friction", _numbers(friction))
    applied["default_geom_friction"] = friction

    for camera_name, offset in settings["camera_position_offsets_m"].items():
        camera = root.find(f"./worldbody/camera[@name='{camera_name}']")
        if camera is None:
            raise ValueError(f"Missing camera {camera_name} in {xml_path}")
        base_position = [float(value) for value in camera.attrib["pos"].split()]
        position = [round(value + float(delta), 6) for value, delta in zip(base_position, offset)]
        camera.set("pos", _numbers(position))
        applied["cameras"][camera_name] = {"offset_m": offset, "position_m": position}

    ET.indent(root, space="  ")
    ET.ElementTree(root).write(xml_path, encoding="unicode")
    xml_path.write_text(xml_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    applied["status"] = "applied"
    manifest["mujoco_applied"] = applied
    return applied


def validate_randomized_scene(
    scene: RobotLabScene,
    *,
    config: DomainRandomizationConfig = DEFAULT_CONFIG,
) -> None:
    """Raise when a reset would begin with overlapping or off-desk objects."""

    desk_min_x, desk_max_x, desk_min_y, desk_max_y = _desk_bounds(scene)
    for tray in scene.trays:
        half_x, half_y = tray.size_m[0] / 2, tray.size_m[1] / 2
        if not (
            desk_min_x <= tray.center_m[0] - half_x
            and tray.center_m[0] + half_x <= desk_max_x
            and desk_min_y <= tray.center_m[1] - half_y
            and tray.center_m[1] + half_y <= desk_max_y
        ):
            raise ValueError(f"Tray {tray.name} is outside the desk bounds")

    for index, left in enumerate(scene.trays):
        for right in scene.trays[index + 1 :]:
            if _rectangles_overlap(
                left.center_m,
                left.size_m[0] / 2 + config.minimum_object_clearance_m,
                left.size_m[1] / 2 + config.minimum_object_clearance_m,
                right.center_m,
                right.size_m[0] / 2,
                right.size_m[1] / 2,
            ):
                raise ValueError(f"Trays overlap: {left.name}, {right.name}")

    for index, cube in enumerate(scene.cubes):
        half = cube.side_length_m / 2
        if not (
            desk_min_x <= cube.initial_position_m[0] - half
            and cube.initial_position_m[0] + half <= desk_max_x
            and desk_min_y <= cube.initial_position_m[1] - half
            and cube.initial_position_m[1] + half <= desk_max_y
        ):
            raise ValueError(f"Cube {cube.name} is outside the desk bounds")
        for tray in scene.trays:
            if _rectangles_overlap(
                cube.initial_position_m,
                half + config.minimum_object_clearance_m,
                half + config.minimum_object_clearance_m,
                tray.center_m,
                tray.size_m[0] / 2,
                tray.size_m[1] / 2,
            ):
                raise ValueError(f"Cube {cube.name} overlaps tray {tray.name}")
        for other in scene.cubes[index + 1 :]:
            clearance = half + other.side_length_m / 2 + config.minimum_object_clearance_m
            dx = cube.initial_position_m[0] - other.initial_position_m[0]
            dy = cube.initial_position_m[1] - other.initial_position_m[1]
            if math.hypot(dx, dy) < clearance:
                raise ValueError(f"Cubes overlap: {cube.name}, {other.name}")


def _sample_trays(
    rng: random.Random,
    scene: RobotLabScene,
    config: DomainRandomizationConfig,
) -> tuple[RobotLabTray, ...]:
    sampled: list[RobotLabTray] = []
    for tray in scene.trays:
        for _ in range(config.maximum_sampling_attempts):
            center = (
                tray.center_m[0] + rng.uniform(-config.tray_xy_jitter_m[0], config.tray_xy_jitter_m[0]),
                tray.center_m[1] + rng.uniform(-config.tray_xy_jitter_m[1], config.tray_xy_jitter_m[1]),
                tray.center_m[2],
            )
            candidate = replace(tray, center_m=_round3(center))
            tentative = replace(scene, trays=tuple([*sampled, candidate]), cubes=())
            try:
                validate_randomized_scene(tentative, config=config)
            except ValueError:
                continue
            sampled.append(candidate)
            break
        else:
            raise RuntimeError(f"Could not sample a valid pose for tray {tray.name}")
    return tuple(sampled)


def _sample_cubes(
    rng: random.Random,
    scene: RobotLabScene,
    trays: tuple[RobotLabTray, ...],
    config: DomainRandomizationConfig,
) -> tuple[RobotLabCube, ...]:
    for _ in range(config.maximum_sampling_attempts):
        sampled: list[RobotLabCube] = []
        for cube in scene.cubes:
            candidate = _sample_cube_candidate(rng, scene, cube, config)
            tentative = replace(scene, trays=trays, cubes=tuple([*sampled, candidate]))
            try:
                validate_randomized_scene(tentative, config=config)
            except ValueError:
                break
            sampled.append(candidate)
        if len(sampled) == len(scene.cubes):
            return tuple(sampled)
    raise RuntimeError("Could not sample a collision-free set of cubes")


def _sample_cube_candidate(
    rng: random.Random,
    scene: RobotLabScene,
    cube: RobotLabCube,
    config: DomainRandomizationConfig,
) -> RobotLabCube:
    size_scale = rng.uniform(*config.cube_size_scale)
    side = round(cube.side_length_m * size_scale, 6)
    center = (
        cube.initial_position_m[0]
        + rng.uniform(-config.cube_xy_jitter_m[0], config.cube_xy_jitter_m[0]),
        cube.initial_position_m[1]
        + rng.uniform(-config.cube_xy_jitter_m[1], config.cube_xy_jitter_m[1]),
        scene.desk.center_m[2] + scene.desk.size_m[2] / 2 + side / 2,
    )
    return replace(
        cube,
        initial_position_m=_round3(center),
        side_length_m=side,
        mass_kg=round(cube.mass_kg * rng.uniform(*config.cube_mass_scale), 6),
    )


def _desk_bounds(scene: RobotLabScene) -> tuple[float, float, float, float]:
    margin = 0.012
    return (
        scene.desk.center_m[0] - scene.desk.size_m[0] / 2 + margin,
        scene.desk.center_m[0] + scene.desk.size_m[0] / 2 - margin,
        scene.desk.center_m[1] - scene.desk.size_m[1] / 2 + margin,
        scene.desk.center_m[1] + scene.desk.size_m[1] / 2 - margin,
    )


def _rectangles_overlap(
    left_center: tuple[float, float, float],
    left_half_x: float,
    left_half_y: float,
    right_center: tuple[float, float, float],
    right_half_x: float,
    right_half_y: float,
) -> bool:
    return (
        abs(left_center[0] - right_center[0]) < left_half_x + right_half_x
        and abs(left_center[1] - right_center[1]) < left_half_y + right_half_y
    )


def _jitter_rgba(
    rng: random.Random,
    rgba: tuple[float, float, float, float],
    amount: float,
) -> tuple[float, float, float, float]:
    return (
        _clamp(rgba[0] + rng.uniform(-amount, amount), 0.02, 0.98),
        _clamp(rgba[1] + rng.uniform(-amount, amount), 0.02, 0.98),
        _clamp(rgba[2] + rng.uniform(-amount, amount), 0.02, 0.98),
        rgba[3],
    )


def _jsonable_config(config: DomainRandomizationConfig) -> dict[str, Any]:
    return json.loads(json.dumps(asdict(config)))


def _round3(values: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(round(value, 6) for value in values)  # type: ignore[return-value]


def _numbers(values: list[float]) -> str:
    return " ".join(str(value) for value in values)


def _clamp(value: float, low: float, high: float) -> float:
    return round(min(high, max(low, value)), 6)
