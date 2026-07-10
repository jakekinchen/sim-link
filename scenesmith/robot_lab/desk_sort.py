"""Build and export SceneSmith-owned SO-101 desk sorting scenes."""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.spec import (
    ColorName,
    RobotLabCube,
    RobotLabDesk,
    RobotLabFiducial,
    RobotLabPolicy,
    RobotLabRobot,
    RobotLabRoom,
    RobotLabScene,
    RobotLabTray,
)
from scenesmith.robot_lab.lerobot_bridge import (
    build_lelab_manifest,
    build_lerobot_policy_request,
)
from scenesmith.robot_lab.mujoco_export import (
    prepare_mujoco_so101_assets,
    prepare_viewer_so101_urdf_assets,
    render_mujoco_xml,
)
from scenesmith.robot_lab.scoring import (
    cube_states_from_scene,
    oracle_sorted_cube_states,
    score_cube_sort,
)
from scenesmith.robot_lab.threejs_export import render_threejs_viewer

SUPPORTED_COLORS: tuple[ColorName, ...] = (
    "red",
    "blue",
    "green",
    "yellow",
    "purple",
    "orange",
)


def build_so101_desk_sort_scene(
    description: str,
    *,
    scene_id: str = "scenesmith_so101_desk_cube_sort",
) -> RobotLabScene:
    """Convert a natural-language task/room description into a lab scene.

    This is deterministic by design: it gives SceneSmith a concrete sim contract
    even when the full LLM/Drake/SAM3D paper pipeline is unavailable locally.
    """

    normalized = description.lower()
    colors = _extract_colors(normalized)
    cube_count = _extract_cube_count(normalized)
    red_like, blue_like = colors[0], colors[1]
    desk = RobotLabDesk()
    table_top_z = desk.center_m[2] + desk.size_m[2] / 2
    tray_center_z = table_top_z + RobotLabTray(
        name="height_probe",
        color=red_like,
        center_m=(0.0, 0.0, 0.0),
    ).size_m[2] / 2
    cube_center_z = table_top_z + RobotLabCube(
        name="height_probe",
        color=red_like,
        initial_position_m=(0.0, 0.0, 0.0),
    ).side_length_m / 2
    trays = (
        RobotLabTray(
            name=f"{red_like}_tray",
            color=red_like,
            center_m=(0.34, 0.15, tray_center_z),
        ),
        RobotLabTray(
            name=f"{blue_like}_tray",
            color=blue_like,
            center_m=(0.34, -0.15, tray_center_z),
        ),
    )
    cubes = tuple(
        _create_cubes_for_color(red_like, 0.105, cube_count, cube_center_z)
        + _create_cubes_for_color(blue_like, -0.105, cube_count, cube_center_z)
    )
    fiducials = (
        RobotLabFiducial(
            position_m=(
                0.08,
                desk.center_m[1] + desk.size_m[1] / 2 - 0.045,
                table_top_z + 0.003,
            ),
            attached_to=f"{desk.name}_top",
        ),
    )
    policy_task = (
        f"Sort each cube into the same-colored tray: {red_like} cubes into the "
        f"{red_like} tray and {blue_like} cubes into the {blue_like} tray."
    )

    return RobotLabScene(
        schema_version="scenesmith.robot_lab.v1",
        scene_id=scene_id,
        description=description,
        room=RobotLabRoom(),
        desk=desk,
        robot=RobotLabRobot(),
        trays=trays,
        cubes=cubes,
        policy=RobotLabPolicy(task=policy_task),
        fiducials=fiducials,
        source={
            "generator": "scenesmith.robot_lab.desk_sort",
            "description_parser": "deterministic_color_and_count_parser",
            "sim_backend": "mujoco_xml",
            "viewer_backend": "threejs",
            "policy_bridge": "lerobot_lelab_manifest_plus_action_server_request",
        },
    )


def export_so101_desk_sort_scene(
    scene: RobotLabScene,
    output_dir: Path,
    *,
    action_server_url: str | None = None,
) -> dict[str, Any]:
    """Export the scene into SceneSmith, MuJoCo, Three.js, and LeRobot assets."""

    output_dir.mkdir(parents=True, exist_ok=True)
    mujoco_dir = output_dir / "mujoco"
    viewer_dir = output_dir / "viewer"
    lerobot_dir = output_dir / "lerobot"
    for directory in (mujoco_dir, viewer_dir, lerobot_dir):
        directory.mkdir(parents=True, exist_ok=True)

    scene_json = output_dir / "scene.json"
    scene_state_json = output_dir / "scene_state.json"
    sim_bridge_json = output_dir / "sim_bridge_contract.json"
    fiducial_report_json = output_dir / "fiducials" / "apriltag_calibration_report.json"
    mujoco_xml = mujoco_dir / "scene.xml"
    viewer_html = viewer_dir / "index.html"
    policy_request_json = lerobot_dir / "policy_request.json"
    lelab_manifest_json = lerobot_dir / "lelab_manifest.json"
    policy_status_json = lerobot_dir / "policy_action_server_status.json"
    proof_json = output_dir / "proof_summary.json"

    robot_mjcf = prepare_mujoco_so101_assets(mujoco_dir, scene.robot.base_position_m)
    robot_urdf_bundle = prepare_viewer_so101_urdf_assets(viewer_dir)
    scene_state = build_scene_state(scene)
    sim_bridge = build_sim_bridge_contract(
        scene,
        mujoco_xml,
        viewer_html,
        robot_mjcf=robot_mjcf,
        robot_urdf_bundle=robot_urdf_bundle,
    )
    policy_request = build_lerobot_policy_request(scene, scene_state)
    fiducial_report = build_fiducial_calibration_report(scene)
    lelab_manifest = build_lelab_manifest(
        scene=scene,
        scene_json=scene_json,
        scene_state_json=scene_state_json,
        mujoco_xml=mujoco_xml,
        viewer_html=viewer_html,
        policy_request_json=policy_request_json,
    )
    initial_states = cube_states_from_scene(scene)
    oracle_states = oracle_sorted_cube_states(scene)
    initial_score = score_cube_sort(initial_states, scene.trays)
    oracle_score = score_cube_sort(oracle_states, scene.trays)

    write_json(scene_json, scene.to_dict())
    write_json(scene_state_json, scene_state)
    write_json(sim_bridge_json, sim_bridge)
    write_json(fiducial_report_json, fiducial_report)
    mujoco_xml.write_text(
        render_mujoco_xml(scene, robot_include=robot_mjcf.name),
        encoding="utf-8",
    )
    viewer_html.write_text(render_threejs_viewer(scene), encoding="utf-8")
    write_json(policy_request_json, policy_request)
    write_json(lelab_manifest_json, lelab_manifest)
    policy_status = maybe_post_action_server(policy_request, action_server_url)
    write_json(policy_status_json, policy_status)

    proof_summary = {
        "status": "pass" if oracle_score["success"] else "fail",
        "scene_id": scene.scene_id,
        "description": scene.description,
        "initial_score": initial_score,
        "oracle_score": oracle_score,
        "artifacts": {
            "scene_json": str(scene_json),
            "scene_state_json": str(scene_state_json),
            "sim_bridge_contract": str(sim_bridge_json),
            "fiducial_calibration_report": str(fiducial_report_json),
            "mujoco_xml": str(mujoco_xml),
            "robot_mjcf": str(robot_mjcf),
            "robot_urdf": str(robot_urdf_bundle / "urdf" / "so101_new_calib.urdf"),
            "viewer_html": str(viewer_html),
            "policy_request": str(policy_request_json),
            "lelab_manifest": str(lelab_manifest_json),
            "policy_status": str(policy_status_json),
        },
        "robot_asset_provenance": {
            "mujoco_source": scene.robot.source_mjcf,
            "urdf_source": scene.robot.source_urdf,
            "joint_names": list(scene.robot.joint_names),
            "urdf_joint_names": list(scene.robot.urdf_joint_names),
        },
        "policy_bridge": {
            "provider": scene.policy.provider,
            "repo_id": scene.policy.repo_id,
            "action_server_url": action_server_url,
            "action_server_status": policy_status,
        },
    }
    write_json(proof_json, proof_summary)
    proof_summary["artifacts"]["proof_summary"] = str(proof_json)
    write_json(proof_json, proof_summary)
    return proof_summary


def build_scene_state(scene: RobotLabScene) -> dict[str, Any]:
    """SceneSmith object state for robot task binding and later eval."""

    objects: dict[str, Any] = {}
    desk_min = [-scene.desk.size_m[0] / 2, -scene.desk.size_m[1] / 2, -scene.desk.size_m[2] / 2]
    desk_max = [scene.desk.size_m[0] / 2, scene.desk.size_m[1] / 2, scene.desk.size_m[2] / 2]
    objects[scene.desk.name] = {
        "name": "work desk",
        "object_type": "furniture",
        "category": "desk",
        "transform": _transform(scene.desk.center_m),
        "bbox_min": desk_min,
        "bbox_max": desk_max,
    }

    for tray in scene.trays:
        objects[tray.name] = {
            "name": f"{tray.color} sorting tray",
            "object_type": "fixture",
            "category": "tray",
            "color": tray.color,
            "transform": _transform(tray.center_m),
            "bbox_min": [-tray.size_m[0] / 2, -tray.size_m[1] / 2, -tray.size_m[2] / 2],
            "bbox_max": [tray.size_m[0] / 2, tray.size_m[1] / 2, tray.size_m[2] / 2],
            "metadata": {"accepts_cube_color": tray.color},
        }

    for cube in scene.cubes:
        half = cube.side_length_m / 2
        objects[cube.name] = {
            "name": f"{cube.color} cube",
            "object_type": "manipuland",
            "category": "cube",
            "color": cube.color,
            "transform": _transform(cube.initial_position_m),
            "bbox_min": [-half, -half, -half],
            "bbox_max": [half, half, half],
            "metadata": {"target_tray_color": cube.color, "mass_kg": cube.mass_kg},
        }

    for fiducial in scene.fiducials:
        half = fiducial.size_m / 2
        objects[fiducial.name] = {
            "name": f"{fiducial.family} id {fiducial.tag_id}",
            "object_type": "fiducial",
            "category": "apriltag",
            "transform": _transform(fiducial.position_m, fiducial.euler_deg),
            "bbox_min": [-half, -half, -0.001],
            "bbox_max": [half, half, 0.001],
            "metadata": {
                "family": fiducial.family,
                "tag_id": fiducial.tag_id,
                "size_m": fiducial.size_m,
                "attached_to": fiducial.attached_to,
                "role": fiducial.role,
                "grid": list(fiducial.grid),
            },
        }

    objects[scene.robot.name] = {
        "name": scene.robot.model,
        "object_type": "robot",
        "category": "robot_arm",
        "transform": _transform(scene.robot.base_position_m),
        "metadata": {
            "joint_names": list(scene.robot.joint_names),
            "urdf_joint_names": list(scene.robot.urdf_joint_names),
            "joint_name_map": dict(scene.robot.joint_name_map),
            "source_mjcf": scene.robot.source_mjcf,
            "source_urdf": scene.robot.source_urdf,
        },
    }

    return {
        "schema_version": "scenesmith.scene_state.v1",
        "scene_id": scene.scene_id,
        "description": scene.description,
        "objects": objects,
        "task": {
            "description": scene.policy.task,
            "success_metric": scene.success_metric,
        },
    }


def build_sim_bridge_contract(
    scene: RobotLabScene,
    mujoco_xml: Path,
    viewer_html: Path,
    *,
    robot_mjcf: Path,
    robot_urdf_bundle: Path,
) -> dict[str, Any]:
    """Contract that lets a robot digital twin operate in the generated scene."""

    return {
        "schema_version": "scenesmith.robot_sim_bridge.v1",
        "scene_id": scene.scene_id,
        "backend": "mujoco",
        "mujoco_xml": str(mujoco_xml),
        "viewer_html": str(viewer_html),
        "robot": {
            "name": scene.robot.name,
            "model": scene.robot.model,
            "joint_names": list(scene.robot.joint_names),
            "urdf_joint_names": list(scene.robot.urdf_joint_names),
            "joint_name_map": dict(scene.robot.joint_name_map),
            "source_mjcf": str(robot_mjcf),
            "source_urdf": str(robot_urdf_bundle / "urdf" / "so101_new_calib.urdf"),
            "action_space": {
                "type": "joint_position_targets",
                "size": len(scene.robot.joint_names),
                "units": list(scene.robot.joint_position_units),
            },
        },
        "bodies": {
            "cubes": [cube.name for cube in scene.cubes],
            "trays": [tray.name for tray in scene.trays],
            "desk": scene.desk.name,
            "fiducials": [fiducial.name for fiducial in scene.fiducials],
        },
        "sites": {
            "camera": ["gripperframe", "side_camera_anchor", "wrist_camera_anchor"],
            "targets": [f"{tray.color}_tray_zone" for tray in scene.trays],
            "workspace": "sort_workspace_center",
        },
        "cameras": {
            "cam0": {
                "mujoco_name": "cam0_side",
                "role": "base_side",
                "mount": "fixed_world",
                "image_key": "observation.images.base_0_rgb",
            },
            "cam1": {
                "mujoco_name": "cam1_overhead",
                "role": "overhead",
                "mount": "fixed_world",
                "image_key": "observation.images.right_wrist_0_rgb",
            },
            "cam2": {
                "mujoco_name": "cam2_wrist",
                "role": "wrist",
                "mount": "gripper",
                "anchor_site": "wrist_camera_anchor",
                "image_key": "observation.images.left_wrist_0_rgb",
            },
        },
        "observation": {
            "state": list(scene.robot.joint_names),
            "scene": ["cube_poses", "tray_poses", "camera_anchors"],
            "images": ["cam0_side", "cam1_overhead", "cam2_wrist"],
            "legacy_images": ["cam0", "cam1"],
        },
        "policy": {
            "provider": scene.policy.provider,
            "repo_id": scene.policy.repo_id,
            "task": scene.policy.task,
        },
        "fiducials": [
            {
                "name": fiducial.name,
                "family": fiducial.family,
                "tag_id": fiducial.tag_id,
                "size_m": fiducial.size_m,
                "position_m": list(fiducial.position_m),
                "euler_deg": list(fiducial.euler_deg),
                "attached_to": fiducial.attached_to,
                "role": fiducial.role,
                "grid": list(fiducial.grid),
            }
            for fiducial in scene.fiducials
        ],
    }


def build_fiducial_calibration_report(scene: RobotLabScene) -> dict[str, Any]:
    """Ground-truth fiducial contract for future camera/world reconstruction."""

    return {
        "schema_version": "scenesmith.fiducial_calibration.v1",
        "scene_id": scene.scene_id,
        "status": "pass" if scene.fiducials else "no_fiducials",
        "coordinate_frame": "mujoco_world_meters",
        "policy_dependency": "none",
        "notes": (
            "The fiducial is an optional calibration anchor. Policy execution and "
            "task scoring must not require tag detection."
        ),
        "camera_visibility_expectations": {
            "cam0_side": "visible when unobstructed by the arm",
            "cam1_overhead": "primary calibration view",
            "cam2_wrist": "visible near the rear desk edge during many approach poses",
        },
        "fiducials": [
            {
                "name": fiducial.name,
                "family": fiducial.family,
                "tag_id": fiducial.tag_id,
                "size_m": fiducial.size_m,
                "position_m": list(fiducial.position_m),
                "euler_deg": list(fiducial.euler_deg),
                "attached_to": fiducial.attached_to,
                "role": fiducial.role,
                "grid": list(fiducial.grid),
                "grid_encoding": "1=black,0=white",
                "grid_size": len(fiducial.grid),
                "ground_truth_pose_source": "SceneSmith scene spec",
            }
            for fiducial in scene.fiducials
        ],
    }


def maybe_post_action_server(
    policy_request: dict[str, Any], action_server_url: str | None
) -> dict[str, Any]:
    if not action_server_url:
        return {
            "attempted": False,
            "reason": "No action server URL supplied.",
        }

    payload = json.dumps(policy_request).encode("utf-8")
    request = urllib.request.Request(
        action_server_url,
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "attempted": True,
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "response": _safe_json(body) or body[:2000],
            }
    except urllib.error.URLError as exc:
        return {"attempted": True, "ok": False, "error": str(exc)}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def encode_file_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _extract_colors(description: str) -> tuple[ColorName, ColorName]:
    colors = [color for color in SUPPORTED_COLORS if re.search(rf"\b{color}\b", description)]
    if len(colors) < 2:
        return ("red", "blue")
    return (colors[0], colors[1])


def _extract_cube_count(description: str) -> int:
    match = re.search(r"(\d+)\s+(?:cubes|blocks)", description)
    if match:
        total = max(2, min(12, int(match.group(1))))
        return max(1, total // 2)
    return 2


def _create_cubes_for_color(
    color: ColorName, y_center: float, count: int, z: float
) -> list[RobotLabCube]:
    offsets = _cube_offsets(count)
    return [
        RobotLabCube(
            name=f"{color}_cube_{index}",
            color=color,
            initial_position_m=(0.19 + offset[0], y_center + offset[1], z),
        )
        for index, offset in enumerate(offsets)
    ]


def _cube_offsets(count: int) -> list[tuple[float, float]]:
    if count == 1:
        return [(0.0, 0.0)]
    if count == 2:
        return [(-0.025, 0.012), (0.035, 0.012)]
    return [((index % 3) - 1, index // 3) for index in range(count)]


def _transform(
    translation: tuple[float, float, float],
    euler_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> dict[str, Any]:
    return {
        "translation": list(translation),
        "rotation_euler_deg": list(euler_deg),
        "rotation_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def _safe_json(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
