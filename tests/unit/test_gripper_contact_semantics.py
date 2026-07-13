"""Tests for compiled gripper geometry and pad-qualified contacts."""

from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.gripper_contact_semantics import (
    FIXED_PAD_GEOM,
    FIXED_JAW_COMPOSITE_GEOM,
    MOVING_PAD_GEOM,
    MOVING_JAW_COMPOSITE_GEOM,
    REPO_ROOT,
    SHELL_GEOM,
    aggregate_pad_contacts,
    apply_gripper_contact_identities,
    build_gripper_geometry_audit,
    synthetic_contact_convention_proof,
    verify_gripper_geometry_audit,
)


ARTIFACT = REPO_ROOT / "configurations/robot_lab/gripper_geometry_audit.json"
SOURCE = REPO_ROOT / "external/SO-ARM100/Simulation/SO101/so101_new_calib.xml"


class GripperContactSemanticsTests(unittest.TestCase):
    def test_semantic_patch_names_exact_collision_geoms_without_geometry_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "robot.xml"
            target.write_bytes(SOURCE.read_bytes())
            change = apply_gripper_contact_identities(target)
            root = ET.parse(target).getroot()
            names = {geom.get("name") for geom in root.iter("geom")}
            self.assertTrue(change["original_collision_geometry_preserved"])
            self.assertEqual(change["collision_geometry_digest_before"], change["collision_geometry_digest_after"])
            self.assertTrue(
                {
                    FIXED_PAD_GEOM,
                    MOVING_PAD_GEOM,
                    FIXED_JAW_COMPOSITE_GEOM,
                    MOVING_JAW_COMPOSITE_GEOM,
                    SHELL_GEOM,
                }.issubset(names)
            )

    def test_synthetic_contact_normals_are_object_inward_and_order_independent(self) -> None:
        proof = synthetic_contact_convention_proof()
        self.assertTrue(proof["geom_order_independent"])
        self.assertTrue(proof["aggregate_valid"])
        for case in proof["order_cases"]:
            aggregate = case["aggregate"]
            self.assertAlmostEqual(aggregate["normal_dot"], -1.0)
            self.assertAlmostEqual(aggregate["fixed_normal_span_alignment"], 1.0)
            self.assertAlmostEqual(aggregate["moving_normal_span_alignment"], 1.0)

    def test_non_pad_or_nonpositive_contacts_do_not_form_a_witness(self) -> None:
        contact = {
            "pad_role": "fixed_fingertip_pad",
            "normal_force_n": 1.0,
            "contact_point_object_m": [-0.02, 0.0, 0.0],
            "contact_normal_object_inward": [1.0, 0.0, 0.0],
        }
        self.assertIsNone(aggregate_pad_contacts([contact], [1.0, 0.0, 0.0]))

        moving = dict(contact)
        moving.update({
            "pad_role": "moving_fingertip_pad",
            "normal_force_n": 0.0,
            "contact_point_object_m": [0.02, 0.0, 0.0],
            "contact_normal_object_inward": [-1.0, 0.0, 0.0],
        })
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            aggregate_pad_contacts([contact, moving], [1.0, 0.0, 0.0])

    def test_checked_audit_is_deterministic_and_bounded(self) -> None:
        stored = load_strict_json(ARTIFACT)
        verify_gripper_geometry_audit(stored)
        self.assertEqual(stored, build_gripper_geometry_audit())
        aperture = stored["aperture_reference"]
        self.assertGreater(aperture["maximum_m"], aperture["minimum_m"])
        self.assertFalse(aperture["physical_calibration_claimed"])
        self.assertFalse(stored["actual_mujoco_grasp_success"])
        self.assertFalse(stored["simulation_training_ready"])
        self.assertEqual(
            set(stored["fixed_fingertip_pad_geom_names"] + stored["moving_fingertip_pad_geom_names"]),
            {FIXED_PAD_GEOM, MOVING_PAD_GEOM},
        )


if __name__ == "__main__":
    unittest.main()
