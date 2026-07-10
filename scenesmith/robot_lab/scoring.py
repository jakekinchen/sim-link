"""Scoring utilities for generated robot-lab tasks."""

from __future__ import annotations

from typing import Any

from scenesmith.robot_lab.spec import RobotLabScene, RobotLabTray, Vec3


def cube_states_from_scene(scene: RobotLabScene) -> list[dict[str, Any]]:
    return [
        {
            "name": cube.name,
            "color": cube.color,
            "position_m": list(cube.initial_position_m),
        }
        for cube in scene.cubes
    ]


def oracle_sorted_cube_states(scene: RobotLabScene) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    states: list[dict[str, Any]] = []
    for cube in scene.cubes:
        tray = next(tray for tray in scene.trays if tray.color == cube.color)
        count = counts.get(cube.color, 0)
        counts[cube.color] = count + 1
        offset_x = (-0.75 if count % 2 == 0 else 0.75) * cube.side_length_m
        row_offset_y = (count // 2) * cube.side_length_m * 0.9
        states.append(
            {
                "name": cube.name,
                "color": cube.color,
                "position_m": [
                    round(tray.center_m[0] + offset_x, 6),
                    round(tray.center_m[1] + row_offset_y, 6),
                    round(tray.center_m[2] + tray.size_m[2] / 2 + cube.side_length_m / 2 + 0.003, 6),
                ],
            }
        )
    return states


def score_cube_sort(
    cube_states: list[dict[str, Any]],
    trays: tuple[RobotLabTray, ...],
    *,
    tolerance_m: float = 0.015,
) -> dict[str, Any]:
    entries = []
    for cube in cube_states:
        position = tuple(cube["position_m"])
        containing_tray = next(
            (tray for tray in trays if _inside_tray(position, tray, tolerance_m)),
            None,
        )
        tray_color = containing_tray.color if containing_tray else "outside"
        entries.append(
            {
                "cube": cube["name"],
                "color": cube["color"],
                "tray": tray_color,
                "correct": tray_color == cube["color"],
            }
        )

    sorted_count = sum(1 for entry in entries if entry["correct"])
    misplaced_count = sum(
        1 for entry in entries if entry["tray"] != "outside" and not entry["correct"]
    )
    outside_count = sum(1 for entry in entries if entry["tray"] == "outside")
    return {
        "total_count": len(cube_states),
        "sorted_count": sorted_count,
        "misplaced_count": misplaced_count,
        "outside_count": outside_count,
        "success": sorted_count == len(cube_states) and misplaced_count == 0,
        "entries": entries,
    }


def _inside_tray(position: Vec3, tray: RobotLabTray, tolerance_m: float) -> bool:
    return (
        abs(position[0] - tray.center_m[0]) <= tray.size_m[0] / 2 + tolerance_m
        and abs(position[1] - tray.center_m[1]) <= tray.size_m[1] / 2 + tolerance_m
    )
