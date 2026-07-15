"""Compact arrangement-spec intake for declarative robot-lab workcells.

Turns a small owner-authored JSON arrangement (cubes, trays, task prompt)
into a complete :class:`RobotLabScene` using the nominal verified room, desk,
and SO-101 robot defaults. The intake fails closed on unknown fields, bad
colors, non-finite or off-desk positions, duplicate names, and overlapping
manipulands. Physical plausibility beyond these static checks is owned by the
builder's settle test, not by this module.

A built workcell is a labelled simulation fixture. It grants no metric,
calibration, training, transfer, or promotion authority.
"""

from __future__ import annotations

import math

from typing import Any, get_args

from scenesmith.robot_lab.spec import (
    ColorName,
    RobotLabCube,
    RobotLabDesk,
    RobotLabPolicy,
    RobotLabRobot,
    RobotLabRoom,
    RobotLabScene,
    RobotLabTray,
    tuple3,
)

SPEC_SCHEMA_VERSION = "scenesmith.workcell_arrangement_spec.v1"
SCENE_SCHEMA_VERSION = "scenesmith.robot_lab.v1"
ALLOWED_COLORS = frozenset(get_args(ColorName))
ALLOWED_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "scene_id",
        "description",
        "task_prompt",
        "success_metric",
        "cubes",
        "trays",
    }
)
ALLOWED_CUBE_FIELDS = frozenset(
    {"name", "color", "position_m", "side_length_m", "mass_kg"}
)
ALLOWED_TRAY_FIELDS = frozenset({"name", "color", "center_m", "size_m"})
DESK_MARGIN_M = 0.01
MAX_CUBES = 8
MAX_TRAYS = 4


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _finite_vec3(values: Any, field_name: str) -> tuple[float, float, float]:
    vector = tuple3(values, field_name)
    _require(
        all(math.isfinite(value) for value in vector),
        f"{field_name} must be finite",
    )
    return vector


def _check_on_desk(
    position: tuple[float, float, float], desk: RobotLabDesk, label: str
) -> None:
    center = desk.center_m
    size = desk.size_m
    half_x = size[0] / 2.0 - DESK_MARGIN_M
    half_y = size[1] / 2.0 - DESK_MARGIN_M
    desk_top = center[2] + size[2] / 2.0
    _require(
        abs(position[0] - center[0]) <= half_x
        and abs(position[1] - center[1]) <= half_y,
        f"{label} lies outside the desk footprint",
    )
    _require(
        desk_top - 0.005 <= position[2] <= desk_top + 0.12,
        f"{label} height is not on or just above the desk top",
    )


def scene_from_arrangement_spec(payload: dict[str, Any]) -> RobotLabScene:
    """Validate a compact arrangement spec and build the full scene."""

    _require(isinstance(payload, dict), "Arrangement spec must be an object")
    unknown = set(payload) - ALLOWED_TOP_LEVEL_FIELDS
    _require(not unknown, f"Unknown arrangement fields: {sorted(unknown)}")
    _require(
        payload.get("schema_version") == SPEC_SCHEMA_VERSION,
        f"schema_version must be {SPEC_SCHEMA_VERSION!r}",
    )
    scene_id = str(payload.get("scene_id", ""))
    _require(
        scene_id
        and scene_id.replace("_", "").replace("-", "").isalnum()
        and len(scene_id) <= 80,
        "scene_id must be a short alphanumeric/underscore/hyphen slug",
    )

    desk = RobotLabDesk()
    room = RobotLabRoom()
    robot = RobotLabRobot()

    raw_trays = payload.get("trays", [])
    raw_cubes = payload.get("cubes", [])
    _require(
        isinstance(raw_trays, list) and 1 <= len(raw_trays) <= MAX_TRAYS,
        f"trays must contain 1-{MAX_TRAYS} entries",
    )
    _require(
        isinstance(raw_cubes, list) and 1 <= len(raw_cubes) <= MAX_CUBES,
        f"cubes must contain 1-{MAX_CUBES} entries",
    )

    trays: list[RobotLabTray] = []
    for index, entry in enumerate(raw_trays):
        label = f"trays[{index}]"
        _require(isinstance(entry, dict), f"{label} must be an object")
        unknown = set(entry) - ALLOWED_TRAY_FIELDS
        _require(not unknown, f"{label} has unknown fields: {sorted(unknown)}")
        color = entry.get("color")
        _require(color in ALLOWED_COLORS, f"{label}.color must be one of {sorted(ALLOWED_COLORS)}")
        center = _finite_vec3(entry["center_m"], f"{label}.center_m")
        _check_on_desk(center, desk, label)
        size = (
            _finite_vec3(entry["size_m"], f"{label}.size_m")
            if "size_m" in entry
            else RobotLabTray.size_m
        )
        _require(all(value > 0 for value in size), f"{label}.size_m must be positive")
        trays.append(
            RobotLabTray(
                name=str(entry["name"]), color=color, center_m=center, size_m=size
            )
        )

    cubes: list[RobotLabCube] = []
    for index, entry in enumerate(raw_cubes):
        label = f"cubes[{index}]"
        _require(isinstance(entry, dict), f"{label} must be an object")
        unknown = set(entry) - ALLOWED_CUBE_FIELDS
        _require(not unknown, f"{label} has unknown fields: {sorted(unknown)}")
        color = entry.get("color")
        _require(color in ALLOWED_COLORS, f"{label}.color must be one of {sorted(ALLOWED_COLORS)}")
        position = _finite_vec3(entry["position_m"], f"{label}.position_m")
        _check_on_desk(position, desk, label)
        side = float(entry.get("side_length_m", RobotLabCube.side_length_m))
        mass = float(entry.get("mass_kg", RobotLabCube.mass_kg))
        _require(0.01 <= side <= 0.08, f"{label}.side_length_m must be within [0.01, 0.08]")
        _require(0.005 <= mass <= 0.5, f"{label}.mass_kg must be within [0.005, 0.5]")
        cubes.append(
            RobotLabCube(
                name=str(entry["name"]),
                color=color,
                initial_position_m=position,
                side_length_m=side,
                mass_kg=mass,
            )
        )

    names = [item.name for item in trays] + [item.name for item in cubes]
    _require(all(names), "Every cube and tray needs a non-empty name")
    _require(len(names) == len(set(names)), "Cube and tray names must be unique")

    for first_index in range(len(cubes)):
        for second_index in range(first_index + 1, len(cubes)):
            first, second = cubes[first_index], cubes[second_index]
            minimum = (first.side_length_m + second.side_length_m) / 2.0
            distance = math.hypot(
                first.initial_position_m[0] - second.initial_position_m[0],
                first.initial_position_m[1] - second.initial_position_m[1],
            )
            _require(
                distance >= minimum,
                f"Cubes {first.name!r} and {second.name!r} overlap at start",
            )

    task_prompt = str(payload.get("task_prompt", RobotLabPolicy.task))
    _require(task_prompt.strip(), "task_prompt must not be empty")

    return RobotLabScene(
        schema_version=SCENE_SCHEMA_VERSION,
        scene_id=scene_id,
        description=str(payload.get("description", f"Declared workcell {scene_id}")),
        room=room,
        desk=desk,
        robot=robot,
        trays=tuple(trays),
        cubes=tuple(cubes),
        policy=RobotLabPolicy(task=task_prompt),
        success_metric=str(
            payload.get("success_metric", "all_cubes_inside_matching_color_trays")
        ),
        source={"arrangement_schema_version": SPEC_SCHEMA_VERSION},
    )
