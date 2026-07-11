from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET

from pathlib import Path

from scenesmith.robot_lab.structural_twin_diff import (
    DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
    MUJOCO_OPTION_DEFAULTS,
    QUATERNION_SEMANTIC_CATEGORIES,
    _compare_category,
    _compare_extracted_category,
    _extract_model,
    build_structural_twin_diff,
    verify_structural_twin_diff,
    write_structural_twin_diff,
)
from scenesmith.robot_lab.twin_contract import DEFAULT_TWIN_PROFILE_PATH


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CATEGORIES = {
    "inertials",
    "joint_frames",
    "joint_limits",
    "actuators",
    "arm_collisions",
    "gripper_collisions",
    "cameras",
    "solver_settings",
    "friction",
    "backlash",
    "named_sites",
}


def _resign(payload: dict) -> None:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    payload["identity_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _model_from_xml(xml_text: str) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        xml_path = Path(temp_dir) / "model.xml"
        xml_path.write_text(ET.tostring(ET.fromstring(xml_text), encoding="unicode"), encoding="utf-8")
        return _extract_model(xml_path)


class StructuralTwinDiffTests(unittest.TestCase):
    def test_build_and_verify_current_repo_diff(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)

        verify_structural_twin_diff(payload, repo_root=REPO_ROOT)

        self.assertEqual(set(payload["categories"]), REQUIRED_CATEGORIES)
        for category_name, category in payload["categories"].items():
            self.assertEqual(
                set(category),
                {"matched", "mismatched", "missing", "extra", "unknown"},
                category_name,
            )
        self.assertEqual(
            payload["sources"]["runtime"]["path"],
            "external/SO-ARM100/Simulation/SO101/so101_new_calib.xml",
        )
        self.assertEqual(
            payload["sources"]["menagerie"]["path"],
            "third_party/mujoco_menagerie/robotstudio_so101/so101.xml",
        )
        self.assertEqual(
            payload["twin_profile_ref"]["path"],
            "configurations/robot_lab/pi05_twin_profile.simulation_only.json",
        )
        expected_profile = json.loads((REPO_ROOT / DEFAULT_TWIN_PROFILE_PATH).read_text(encoding="utf-8"))
        self.assertEqual(
            payload["twin_profile_ref"]["identity_sha256"],
            expected_profile["identity_sha256"],
        )
        gripperframe = next(
            record
            for record in payload["categories"]["named_sites"]["mismatched"]
            if record["key"] == "site:gripperframe"
        )
        self.assertNotIn("quat", gripperframe["numeric_deltas"])
        self.assertEqual(
            gripperframe["compared_values"],
            {
                "runtime": {"quat": [0.707106781, -0.0, 0.707106781, -0.0]},
                "menagerie": {"quat": [0.707106781, 0.0, 0.707106781, 0.0]},
            },
        )
        solver_mismatches = payload["categories"]["solver_settings"]["mismatched"]
        self.assertTrue(
            any(
                record["key"] == "option:global"
                and record["runtime"]["integrator"] == MUJOCO_OPTION_DEFAULTS["integrator"]
                and record["menagerie"]["integrator"] == "implicitfast"
                for record in solver_mismatches
            )
        )
        self.assertFalse(payload["categories"]["solver_settings"]["missing"])
        self.assertTrue(
            any(
                record["key"] == "joint:wrist_roll"
                for record in payload["categories"]["joint_limits"]["mismatched"]
            )
        )
        self.assertTrue(payload["summary"]["mismatched_records"] > 0)

    def test_build_repo_diff_surfaces_camera_mount_inertial_as_unknown(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)

        unknown = payload["categories"]["inertials"]["unknown"]
        camera_mount = next(
            record
            for record in unknown
            if record["key"] == "body:base/shoulder/upper_arm/lower_arm/wrist/gripper/camera_mount"
        )

        self.assertEqual(camera_mount["side"], "menagerie")
        self.assertEqual(camera_mount["kind"], "inferred_body_inertia")
        self.assertEqual(camera_mount["decision"], "adapt")
        self.assertEqual(camera_mount["evidence"]["geoms"][0]["mass"], 0.012)

    def test_compare_extracted_category_keeps_declaration_only_friction_unknown(self):
        runtime_model = _model_from_xml(
            """
            <mujoco>
              <default>
                <default class="ghost_contact">
                  <geom friction="1 0.1 0.01" priority="1"/>
                </default>
                <default class="live_contact">
                  <geom condim="3"/>
                </default>
              </default>
              <worldbody>
                <body name="base">
                  <geom name="live" class="live_contact" type="box" size="0.1 0.1 0.1"/>
                </body>
              </worldbody>
            </mujoco>
            """
        )
        menagerie_model = _model_from_xml(
            """
            <mujoco>
              <default>
                <default class="live_contact">
                  <geom condim="3"/>
                </default>
              </default>
              <worldbody>
                <body name="base">
                  <geom name="live" class="live_contact" type="box" size="0.1 0.1 0.1"/>
                </body>
              </worldbody>
            </mujoco>
            """
        )

        category = _compare_extracted_category(
            "friction",
            runtime_model["categories"]["friction"],
            menagerie_model["categories"]["friction"],
        )

        self.assertEqual(len(category["matched"]), 1)
        self.assertFalse(category["missing"])
        self.assertFalse(category["extra"])
        self.assertFalse(category["mismatched"])
        self.assertEqual(
            category["unknown"],
            [
                {
                    "decision": "retain",
                    "evidence": {"friction": [1.0, 0.1, 0.01], "priority": 1.0},
                    "key": "declaration:geom:ghost_contact",
                    "kind": "declaration_only_default",
                    "rationale": "Declaration-only contact defaults stay explicit, but they are not compared as effective attachment behavior until they are actually attached in the source model.",
                    "reason": "This default class carries contact-related settings but is not attached to a compared joint or geom, so it remains declaration-only evidence rather than effective runtime behavior.",
                    "side": "runtime",
                }
            ],
        )

    def test_compare_extracted_category_surfaces_effective_friction_attachment_delta(self):
        runtime_model = _model_from_xml(
            """
            <mujoco>
              <default>
                <default class="pad">
                  <geom friction="1 0.1 0.01" priority="1"/>
                </default>
              </default>
              <worldbody>
                <body name="base">
                  <geom name="finger_pad" class="pad" type="box" size="0.1 0.1 0.1"/>
                </body>
              </worldbody>
            </mujoco>
            """
        )
        menagerie_model = _model_from_xml(
            """
            <mujoco>
              <default>
                <default class="pad">
                  <geom friction="2 0.1 0.01" priority="1"/>
                </default>
              </default>
              <worldbody>
                <body name="base">
                  <geom name="finger_pad" class="pad" type="box" size="0.1 0.1 0.1"/>
                </body>
              </worldbody>
            </mujoco>
            """
        )

        category = _compare_extracted_category(
            "friction",
            runtime_model["categories"]["friction"],
            menagerie_model["categories"]["friction"],
        )

        self.assertFalse(category["matched"])
        self.assertFalse(category["unknown"])
        mismatch = category["mismatched"][0]
        self.assertEqual(mismatch["key"], "geom:base:finger_pad")
        self.assertEqual(mismatch["numeric_deltas"], {"friction": [-1.0, 0.0, 0.0]})

    def test_compare_category_matches_equivalent_quaternions(self):
        category = _compare_category(
            "named_sites",
            {
                "site:gripperframe": {
                    "quat": [0.707107, 0.0, 0.707107, 0.0],
                }
            },
            {
                "site:gripperframe": {
                    "quat": [1.0, 0.0, 1.0, 0.0],
                }
            },
        )

        self.assertEqual(len(category["matched"]), 1)
        self.assertFalse(category["mismatched"])

    def test_compare_category_matches_equivalent_collision_quaternions(self):
        category = _compare_category(
            "arm_collisions",
            {
                "geom:arm:guard": {
                    "quat": [0.5, 0.5, 0.5, -0.5],
                }
            },
            {
                "geom:arm:guard": {
                    "quat": [-1.0, -1.0, -1.0, 1.0],
                }
            },
        )

        self.assertEqual(len(category["matched"]), 1)
        self.assertFalse(category["mismatched"])

    def test_compare_category_uses_identity_quaternion_default_for_transform_categories(self):
        for category_name in QUATERNION_SEMANTIC_CATEGORIES:
            with self.subTest(category_name=category_name):
                category = _compare_category(
                    category_name,
                    {"record": {"quat": []}},
                    {"record": {"quat": [1.0, 0.0, 0.0, 0.0]}},
                )

                self.assertEqual(len(category["matched"]), 1)
                self.assertFalse(category["mismatched"])

    def test_compare_category_records_canonical_quaternion_values_for_true_mismatch(self):
        category = _compare_category(
            "named_sites",
            {
                "site:tool": {
                    "quat": [0.0, 0.0, 0.707107, 0.707107],
                }
            },
            {
                "site:tool": {
                    "quat": [0.0, 0.0, 1.0, 0.0],
                }
            },
        )

        mismatch = category["mismatched"][0]
        self.assertEqual(
            mismatch["compared_values"],
            {
                "runtime": {"quat": [0.0, 0.0, 0.707106781, 0.707106781]},
                "menagerie": {"quat": [0.0, 0.0, 1.0, 0.0]},
            },
        )

    def test_compare_category_tolerates_small_canonical_quaternion_noise(self):
        category = _compare_category(
            "joint_frames",
            {
                "body:wrist": {
                    "quat": [0.707106781, 0.707106781, -0.000000019, 0.000000019],
                }
            },
            {
                "body:wrist": {
                    "quat": [0.707106781, 0.707106781, 0.0, 0.0],
                }
            },
        )

        self.assertEqual(len(category["matched"]), 1)
        self.assertFalse(category["mismatched"])

    def test_compare_category_uses_effective_solver_defaults_when_option_is_omitted(self):
        category = _compare_category(
            "solver_settings",
            {"option:global": dict(MUJOCO_OPTION_DEFAULTS)},
            {
                "option:global": {
                    **MUJOCO_OPTION_DEFAULTS,
                    "integrator": "implicitfast",
                    "iterations": 10.0,
                    "ls_iterations": 20.0,
                    "impratio": 10.0,
                    "cone": "elliptic",
                    "timestep": 0.005,
                }
            },
        )

        self.assertFalse(category["missing"])
        self.assertFalse(category["extra"])
        mismatch = category["mismatched"][0]
        self.assertEqual(mismatch["key"], "option:global")
        self.assertEqual(mismatch["runtime"]["integrator"], "euler")
        self.assertEqual(
            mismatch["numeric_deltas"],
            {
                "impratio": -9.0,
                "iterations": 90.0,
                "ls_iterations": 30.0,
                "timestep": -0.003,
            },
        )

    def test_write_current_repo_artifact_is_deterministic(self):
        expected = build_structural_twin_diff(repo_root=REPO_ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / DEFAULT_STRUCTURAL_TWIN_DIFF_PATH.name
            written = write_structural_twin_diff(repo_root=REPO_ROOT, output_path=artifact_path)
            verified = json.loads(artifact_path.read_text(encoding="utf-8"))

        self.assertEqual(written, expected)
        self.assertEqual(verified, expected)

    def test_verify_rejects_artifact_identity_tamper(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)
        payload["summary"]["mismatched_records"] += 1

        with self.assertRaisesRegex(ValueError, "identity hash is invalid"):
            verify_structural_twin_diff(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_source_hash_tamper(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)
        payload["sources"]["menagerie"]["sha256"] = "0" * 64
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "Menagerie source hash drifted"):
            verify_structural_twin_diff(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_missing_category(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)
        payload["categories"].pop("cameras")
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "Missing structural diff categories"):
            verify_structural_twin_diff(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_twin_profile_identity_tamper(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)
        payload["twin_profile_ref"]["identity_sha256"] = "0" * 64
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "Twin profile identity drifted"):
            verify_structural_twin_diff(payload, repo_root=REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
