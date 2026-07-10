#!/usr/bin/env python3
"""Validate physical placement for a generated SceneSmith SO-101 workcell."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-json", type=Path, required=True)
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "mujoco is not installed in this Python environment; run from .mujoco_venv"
        ) from exc

    scene = json.loads(args.scene_json.read_text(encoding="utf-8"))
    desk = scene["desk"]
    robot = scene["robot"]
    trays = scene["trays"]
    cubes = scene["cubes"]

    desk_center = desk["center_m"]
    desk_size = desk["size_m"]
    desk_top_z = desk_center[2] + desk_size[2] / 2
    checks: dict[str, bool] = {}
    details: dict[str, object] = {
        "desk_top_z": desk_top_z,
        "table_bounds_xy": {
            "x": [desk_center[0] - desk_size[0] / 2, desk_center[0] + desk_size[0] / 2],
            "y": [desk_center[1] - desk_size[1] / 2, desk_center[1] + desk_size[1] / 2],
        },
    }

    base_z_offset = robot["base_position_m"][2] - desk_top_z
    checks["robot_base_mounted_on_desk"] = 0.0 <= base_z_offset <= 0.05
    details["robot_base_z_offset_from_desktop_m"] = base_z_offset

    checks["trays_seated_on_desktop"] = all(
        abs((tray["center_m"][2] - tray["size_m"][2] / 2) - desk_top_z) <= 1e-6
        for tray in trays
    )
    checks["cubes_spawn_on_desktop"] = all(
        abs((cube["initial_position_m"][2] - cube["side_length_m"] / 2) - desk_top_z)
        <= 1e-6
        for cube in cubes
    )
    checks["objects_inside_table_footprint"] = all(
        _box_inside_table(obj["center_m"], obj["size_m"], desk_center, desk_size)
        for obj in trays
    ) and all(
        _box_inside_table(
            cube["initial_position_m"],
            [cube["side_length_m"]] * 3,
            desk_center,
            desk_size,
        )
        for cube in cubes
    )

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)
    for _ in range(1000):
        mujoco.mj_step(model, data)

    cube_contacts = {cube["name"]: False for cube in cubes}
    min_contact_dist = 0.0
    contacts = []
    for index in range(data.ncon):
        contact = data.contact[index]
        geom1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, contact.geom1)
        geom2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, contact.geom2)
        min_contact_dist = min(min_contact_dist, float(contact.dist))
        contacts.append({"geom1": geom1, "geom2": geom2, "dist": float(contact.dist)})
        for cube_name in cube_contacts:
            cube_geom = f"{cube_name}_geom"
            if {geom1, geom2} == {"desk_top", cube_geom}:
                cube_contacts[cube_name] = True

    settled_cubes = {}
    for cube in cubes:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, cube["name"])
        settled_cubes[cube["name"]] = data.xpos[body_id].round(6).tolist()

    checks["cubes_settle_on_desktop"] = all(cube_contacts.values())
    checks["contact_penetration_bounded"] = min_contact_dist >= -0.002
    checks["robot_and_objects_inside_room"] = _bodies_inside_room(
        mujoco,
        model,
        data,
        scene["room"]["size_m"],
        [
            "base",
            "shoulder",
            "upper_arm",
            "lower_arm",
            "wrist",
            "gripper",
            *[cube["name"] for cube in cubes],
            *[tray["name"] for tray in trays],
        ],
    )

    details.update(
        {
            "settled_cube_positions_m": settled_cubes,
            "cube_desk_contacts": cube_contacts,
            "min_contact_dist_m": min_contact_dist,
            "contact_count": int(data.ncon),
            "contacts": contacts[:40],
        }
    )
    summary = {
        "status": "pass" if all(checks.values()) else "fail",
        "scene_json": str(args.scene_json),
        "xml": str(args.xml),
        "checks": checks,
        "details": details,
    }

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


def _box_inside_table(center, size, desk_center, desk_size) -> bool:
    return (
        center[0] - size[0] / 2 >= desk_center[0] - desk_size[0] / 2
        and center[0] + size[0] / 2 <= desk_center[0] + desk_size[0] / 2
        and center[1] - size[1] / 2 >= desk_center[1] - desk_size[1] / 2
        and center[1] + size[1] / 2 <= desk_center[1] + desk_size[1] / 2
    )


def _bodies_inside_room(mujoco, model, data, room_size, body_names) -> bool:
    half_x = room_size[0] / 2
    half_y = room_size[1] / 2
    height = room_size[2]
    for body_name in body_names:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if body_id < 0:
            return False
        x, y, z = data.xpos[body_id]
        if not (-half_x <= x <= half_x and -half_y <= y <= half_y and 0 <= z <= height):
            return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
