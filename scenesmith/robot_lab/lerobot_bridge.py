"""LeRobot/LeLab-facing exports for generated SceneSmith robot scenes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.spec import RobotLabScene


def build_lerobot_policy_request(
    scene: RobotLabScene, scene_state: dict[str, Any]
) -> dict[str, Any]:
    """Build a MolmoAct2/LeRobot-style action request.

    The image fields are intentionally placeholders at generation time. The
    viewer verification step can provide screenshots, and a runtime bridge can
    replace these with real camera frames.
    """

    return {
        "repo_id": scene.policy.repo_id,
        "task": scene.policy.task,
        "observation": {
            "state": [0.0 for _ in scene.robot.joint_names],
            "state_order": list(scene.robot.joint_names),
            "urdf_state_order": list(scene.robot.urdf_joint_names),
            "images": {
                "cam0": "",
                "cam1": "",
                "cam2": "",
                "cam0_side": "",
                "cam1_overhead": "",
                "cam2_wrist": "",
            },
            "cameras": {
                "cam0": {"mujoco_name": "cam0_side", "role": "base_side"},
                "cam1": {"mujoco_name": "cam1_overhead", "role": "overhead"},
                "cam2": {
                    "mujoco_name": "cam2_wrist",
                    "role": "wrist",
                    "mount": "gripper",
                    "anchor_site": "wrist_camera_anchor",
                },
            },
            "scene": {
                "scene_id": scene.scene_id,
                "cube_poses": {
                    cube.name: {
                        "color": cube.color,
                        "position_m": list(cube.initial_position_m),
                    }
                    for cube in scene.cubes
                },
                "tray_poses": {
                    tray.name: {
                        "color": tray.color,
                        "center_m": list(tray.center_m),
                        "size_m": list(tray.size_m),
                    }
                    for tray in scene.trays
                },
                "fiducials": {
                    fiducial.name: {
                        "family": fiducial.family,
                        "tag_id": fiducial.tag_id,
                        "size_m": fiducial.size_m,
                        "position_m": list(fiducial.position_m),
                        "euler_deg": list(fiducial.euler_deg),
                        "attached_to": fiducial.attached_to,
                        "role": fiducial.role,
                    }
                    for fiducial in scene.fiducials
                },
                "scene_state_schema": scene_state["schema_version"],
            },
        },
        "metadata": {
            "generated_by": "SceneSmith robot_lab",
            "action_server_env": scene.policy.action_server_env,
            "sim_backend": "mujoco",
            "robot_model": scene.robot.model,
            "robot_type": "so101_follower",
            "teleop_type": "so101_leader",
            "joint_name_map": dict(scene.robot.joint_name_map),
        },
    }


def build_lelab_manifest(
    *,
    scene: RobotLabScene,
    scene_json: Path,
    scene_state_json: Path,
    mujoco_xml: Path,
    viewer_html: Path,
    policy_request_json: Path,
) -> dict[str, Any]:
    """Build a manifest that a LeRobot/LeLab adapter can import."""

    return {
        "schema_version": "scenesmith.lelab_manifest.v1",
        "name": scene.scene_id,
        "task": scene.policy.task,
        "robot": {
            "family": "LeRobot SO arm",
            "model": scene.robot.model,
            "lerobot_robot_type": "so101_follower",
            "lerobot_teleop_type": "so101_leader",
            "joint_names": list(scene.robot.joint_names),
            "urdf_joint_names": list(scene.robot.urdf_joint_names),
            "joint_name_map": dict(scene.robot.joint_name_map),
            "source_mjcf": scene.robot.source_mjcf,
            "source_urdf": scene.robot.source_urdf,
        },
        "lelab": {
            "upstream": "https://github.com/huggingface/leLab",
            "docs": "https://huggingface.co/docs/lerobot/en/lelab",
            "compatibility_note": (
                "LeLab is treated as the workflow/UI shell. SceneSmith owns the "
                "generated sim scene and exports this manifest plus LeRobot action "
                "request for adapter import."
            ),
        },
        "lerobot": {
            "policy_repo_id": scene.policy.repo_id,
            "provider": scene.policy.provider,
            "action_server_env": scene.policy.action_server_env,
            "request_json": str(policy_request_json),
            "rendered_request_json": str(
                policy_request_json.with_name("policy_request.rendered.json")
            ),
        },
        "scene_assets": {
            "scene_json": str(scene_json),
            "scene_state_json": str(scene_state_json),
            "mujoco_xml": str(mujoco_xml),
            "viewer_html": str(viewer_html),
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
            }
            for fiducial in scene.fiducials
        ],
        "expected_capabilities": [
            "load generated MuJoCo scene",
            "render inspectable Three.js scene",
            "preserve optional AprilTag fiducial calibration metadata",
            "provide robot joint state",
            "provide cam0 side, cam1 overhead, and cam2 wrist observation images",
            "send policy request to LeRobot action server",
        ],
    }
