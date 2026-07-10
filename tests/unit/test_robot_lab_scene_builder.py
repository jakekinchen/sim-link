"""Tests for SceneSmith robot-lab scene generation.

These tests use only the Python standard library so they remain runnable on
Mac-native machines where the full Drake/SAM3D paper stack is unavailable.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scenesmith.robot_lab import (
    build_so101_desk_sort_scene,
    export_so101_desk_sort_scene,
    randomize_scene,
    scene_from_dict,
)
from scenesmith.robot_lab.scoring import (
    cube_states_from_scene,
    oracle_sorted_cube_states,
    score_cube_sort,
)


class RobotLabSceneBuilderTests(unittest.TestCase):
    def test_description_builds_scene_contract(self):
        scene = build_so101_desk_sort_scene(
            "Put an SO-101 arm on a desk with red and blue trays and 4 cubes."
        )

        self.assertEqual(scene.schema_version, "scenesmith.robot_lab.v1")
        self.assertEqual(scene.robot.model, "SO-101")
        self.assertEqual(
            list(scene.robot.joint_names),
            [
                "shoulder_pan",
                "shoulder_lift",
                "elbow_flex",
                "wrist_flex",
                "wrist_roll",
                "gripper",
            ],
        )
        self.assertEqual([tray.color for tray in scene.trays], ["red", "blue"])
        self.assertEqual([tray.center_m[0] for tray in scene.trays], [0.34, 0.34])
        self.assertEqual(len(scene.cubes), 4)
        self.assertEqual(len(scene.fiducials), 1)
        self.assertEqual(scene.fiducials[0].family, "tag36h11")
        self.assertEqual(scene.fiducials[0].tag_id, 0)
        self.assertEqual(
            scene.fiducials[0].grid,
            (
                "0000000000",
                "0111111110",
                "0100101010",
                "0110001010",
                "0110011110",
                "0101011110",
                "0110100110",
                "0111101110",
                "0111111110",
                "0000000000",
            ),
        )
        self.assertIn("red cubes", scene.policy.task)
        self.assertIn("blue cubes", scene.policy.task)

    def test_scoring_separates_initial_and_oracle_state(self):
        scene = build_so101_desk_sort_scene(
            "SO-101 desk sorting setup with red and blue trays."
        )
        initial = score_cube_sort(cube_states_from_scene(scene), scene.trays)
        oracle = score_cube_sort(oracle_sorted_cube_states(scene), scene.trays)

        self.assertFalse(initial["success"])
        self.assertEqual(initial["outside_count"], 4)
        self.assertTrue(oracle["success"])
        self.assertEqual(oracle["sorted_count"], 4)

    def test_export_writes_mujoco_viewer_and_lerobot_contracts(self):
        scene = build_so101_desk_sort_scene(
            "Set up an SO-101 arm on a desk with red and blue trays and cubes."
        )
        with tempfile.TemporaryDirectory() as tmp:
            proof = export_so101_desk_sort_scene(scene, Path(tmp))

            self.assertEqual(proof["status"], "pass")
            for key in [
                "scene_json",
                "scene_state_json",
                "sim_bridge_contract",
                "fiducial_calibration_report",
                "mujoco_xml",
                "viewer_html",
                "policy_request",
                "lelab_manifest",
                "proof_summary",
            ]:
                self.assertTrue(Path(proof["artifacts"][key]).exists(), key)

            xml_root = ET.parse(proof["artifacts"]["mujoco_xml"]).getroot()
            self.assertEqual(xml_root.tag, "mujoco")
            self.assertEqual(xml_root.attrib["model"], scene.scene_id)
            self.assertEqual(xml_root.find("include").attrib["file"], "so101_new_calib.xml")
            camera_names = [
                camera.attrib["name"] for camera in xml_root.findall(".//camera")
            ]
            self.assertIn("cam0_side", camera_names)
            self.assertIn("cam1_overhead", camera_names)
            self.assertIn("apriltag_0", [body.attrib["name"] for body in xml_root.findall(".//body")])
            self.assertIn(
                "apriltag_0_white",
                [
                    geom.attrib["name"]
                    for geom in xml_root.findall(".//geom")
                    if "name" in geom.attrib
                ],
            )
            self.assertEqual(
                xml_root.find(".//site[@name='apriltag_0_pose']").attrib["rgba"],
                "0 0 0 0",
            )
            self.assertEqual(len(xml_root.findall(".//freejoint")), 4)
            grasp_assists = xml_root.findall("./equality/weld")
            self.assertEqual(len(grasp_assists), 4)
            self.assertEqual(
                {weld.attrib["body2"] for weld in grasp_assists},
                {cube.name for cube in scene.cubes},
            )
            self.assertTrue(
                all(
                    weld.attrib["body1"] == "gripper"
                    and weld.attrib["active"] == "false"
                    for weld in grasp_assists
                )
            )
            robot_xml = Path(proof["artifacts"]["mujoco_xml"]).with_name("so101_new_calib.xml")
            self.assertTrue(robot_xml.exists())
            self.assertTrue(robot_xml.with_name("assets").joinpath("base_so101_v2.stl").exists())
            robot_root = ET.parse(robot_xml).getroot()
            robot_camera_names = [
                camera.attrib["name"] for camera in robot_root.findall(".//camera")
            ]
            robot_body_names = [body.attrib["name"] for body in robot_root.findall(".//body")]
            robot_geom_names = [
                geom.attrib["name"]
                for geom in robot_root.findall(".//geom")
                if "name" in geom.attrib
            ]
            robot_site_names = [site.attrib["name"] for site in robot_root.findall(".//site")]
            self.assertIn("wrist_camera", robot_body_names)
            self.assertIn("wrist_camera_body", robot_geom_names)
            self.assertIn("wrist_camera_mount", robot_geom_names)
            self.assertIn("wrist_camera_mount_foot", robot_geom_names)
            self.assertIn("wrist_camera_lens", robot_geom_names)
            self.assertIn("cam2_wrist", robot_camera_names)
            self.assertIn("wrist_camera_anchor", robot_site_names)
            wrist_camera = robot_root.find(".//camera[@name='cam2_wrist']")
            self.assertEqual(wrist_camera.attrib["pos"], "0 0 0")
            self.assertEqual(wrist_camera.attrib["xyaxes"], "0 1 0 -0.868 0 0.496")
            self.assertEqual(len(robot_root.findall(".//actuator/position")), 6)
            actuator_names = [
                actuator.attrib["name"]
                for actuator in robot_root.findall(".//actuator/position")
            ]
            self.assertEqual(actuator_names, list(scene.robot.joint_names))

            policy_request = json.loads(
                Path(proof["artifacts"]["policy_request"]).read_text()
            )
            self.assertEqual(
                policy_request["repo_id"], "lerobot/MolmoAct2-SO100_101-LeRobot"
            )
            self.assertEqual(policy_request["observation"]["state_order"], list(scene.robot.joint_names))
            self.assertEqual(policy_request["observation"]["scene"]["scene_id"], scene.scene_id)
            self.assertIn("cam2_wrist", policy_request["observation"]["images"])
            self.assertIn("apriltag_0", policy_request["observation"]["scene"]["fiducials"])
            self.assertEqual(
                policy_request["observation"]["cameras"]["cam2"]["role"], "wrist"
            )

            sim_bridge = json.loads(
                Path(proof["artifacts"]["sim_bridge_contract"]).read_text()
            )
            self.assertEqual(sim_bridge["cameras"]["cam2"]["mujoco_name"], "cam2_wrist")
            self.assertEqual(sim_bridge["cameras"]["cam2"]["mount"], "gripper")
            self.assertIn("cam2_wrist", sim_bridge["observation"]["images"])
            self.assertEqual(sim_bridge["fiducials"][0]["name"], "apriltag_0")

            fiducial_report = json.loads(
                Path(proof["artifacts"]["fiducial_calibration_report"]).read_text()
            )
            self.assertEqual(fiducial_report["status"], "pass")
            self.assertEqual(fiducial_report["policy_dependency"], "none")

            lelab_manifest = json.loads(
                Path(proof["artifacts"]["lelab_manifest"]).read_text()
            )
            self.assertEqual(lelab_manifest["schema_version"], "scenesmith.lelab_manifest.v1")
            self.assertEqual(lelab_manifest["lerobot"]["policy_repo_id"], scene.policy.repo_id)
            self.assertEqual(lelab_manifest["robot"]["lerobot_robot_type"], "so101_follower")
            self.assertEqual(lelab_manifest["fiducials"][0]["family"], "tag36h11")

            rehydrated = scene_from_dict(json.loads(Path(proof["artifacts"]["scene_json"]).read_text()))
            self.assertEqual(rehydrated.fiducials[0].name, scene.fiducials[0].name)

    def test_domain_randomization_is_deterministic_and_preserves_fiducial_pose(self):
        scene = build_so101_desk_sort_scene(
            "Set up an SO-101 arm on a desk with red and blue trays and cubes."
        )

        variant_a, manifest_a = randomize_scene(scene, 1234)
        variant_b, manifest_b = randomize_scene(scene, 1234)
        variant_c, manifest_c = randomize_scene(scene, 1235)

        self.assertEqual(variant_a.to_dict(), variant_b.to_dict())
        self.assertEqual(manifest_a, manifest_b)
        self.assertNotEqual(variant_a.cubes[0].initial_position_m, variant_c.cubes[0].initial_position_m)
        self.assertNotEqual(manifest_a["seed"], manifest_c["seed"])
        self.assertEqual(variant_a.fiducials[0].position_m, scene.fiducials[0].position_m)
        self.assertEqual(
            manifest_a["fixed_fields"]["apriltag_visibility"],
            "expected_visible_not_policy_required",
        )
        self.assertIn("friction_scale", manifest_a["mujoco"])
        self.assertIn("camera_position_offsets_m", manifest_a["mujoco"])


if __name__ == "__main__":
    unittest.main()
