#!/usr/bin/env python3
"""Load and step a generated SceneSmith robot-lab MuJoCo scene."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, required=True, help="Generated MuJoCo XML.")
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional path for MuJoCo load summary.",
    )
    args = parser.parse_args()

    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "mujoco is not installed in this Python environment; install mujoco "
            "or run this script from the SceneSmith .mujoco_venv after setup"
        ) from exc

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)
    for _ in range(240):
        mujoco.mj_step(model, data)

    joint_names = _object_names(mujoco, model, mujoco.mjtObj.mjOBJ_JOINT, model.njnt)
    body_names = _object_names(mujoco, model, mujoco.mjtObj.mjOBJ_BODY, model.nbody)
    geom_names = _object_names(mujoco, model, mujoco.mjtObj.mjOBJ_GEOM, model.ngeom)
    actuator_names = _object_names(
        mujoco, model, mujoco.mjtObj.mjOBJ_ACTUATOR, model.nu
    )
    site_names = _object_names(mujoco, model, mujoco.mjtObj.mjOBJ_SITE, model.nsite)
    camera_names = _object_names(mujoco, model, mujoco.mjtObj.mjOBJ_CAMERA, model.ncam)
    required_joints = [
        "shoulder_pan",
        "shoulder_lift",
        "elbow_flex",
        "wrist_flex",
        "wrist_roll",
        "gripper",
    ]
    required_sites = [
        "gripperframe",
        "side_camera_anchor",
        "wrist_camera_anchor",
        "sort_workspace_center",
        "red_tray_zone",
        "blue_tray_zone",
    ]
    required_cameras = ["cam0_side", "cam1_overhead", "cam2_wrist"]
    required_fiducial_geoms = [
        "apriltag_0_white",
        "apriltag_0_cell_0_0",
        "apriltag_0_cell_7_7",
    ]
    required_wrist_camera_geoms = [
        "wrist_camera_body",
        "wrist_camera_mount",
        "wrist_camera_mount_foot",
        "wrist_camera_lens",
    ]
    summary = {
        "status": "pass",
        "xml": str(args.xml),
        "mujoco_version": mujoco.mj_version(),
        "nbody": int(model.nbody),
        "ngeom": int(model.ngeom),
        "nsite": int(model.nsite),
        "njnt": int(model.njnt),
        "nq": int(model.nq),
        "nv": int(model.nv),
        "nu": int(model.nu),
        "sim_time_s": float(data.time),
        "joint_names": joint_names,
        "body_names": body_names,
        "geom_names": geom_names,
        "actuator_names": actuator_names,
        "site_names": site_names,
        "camera_names": camera_names,
        "checks": {
            "has_robot_controls": int(model.nu) == 6,
            "has_real_so101_joints": all(name in joint_names for name in required_joints),
            "has_real_so101_actuators": all(
                name in actuator_names for name in required_joints
            ),
            "has_cube_free_joints": sum(
                name.endswith("_free") for name in joint_names
            )
            == 4,
            "has_camera_and_target_sites": all(name in site_names for name in required_sites),
            "has_side_overhead_and_wrist_cameras": all(
                name in camera_names for name in required_cameras
            ),
            "has_apriltag_fiducial": "apriltag_0" in body_names
            and "apriltag_0_pose" in site_names
            and all(name in geom_names for name in required_fiducial_geoms),
            "has_visible_wrist_camera_body": "wrist_camera" in body_names
            and all(name in geom_names for name in required_wrist_camera_geoms),
        },
    }
    summary["status"] = (
        "pass" if all(summary["checks"].values()) else "fail"
    )
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


def _object_names(mujoco, model, obj_type, count: int) -> list[str]:
    return [
        name
        for index in range(int(count))
        if (name := mujoco.mj_id2name(model, obj_type, index))
    ]


if __name__ == "__main__":
    raise SystemExit(main())
