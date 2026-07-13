"""Tests for centered bilateral contact-face audit."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.centered_contact_face_audit import REPO_ROOT, build_centered_contact_face_audit, verify_centered_contact_face_audit

ARTIFACT = REPO_ROOT / "configurations/robot_lab/centered_contact_face_audit.json"


class CenteredContactFaceAuditTests(unittest.TestCase):
    def test_checked_audit_is_deterministic_and_source_identical(self) -> None:
        payload = load_strict_json(ARTIFACT)
        verify_centered_contact_face_audit(payload)
        self.assertEqual(payload, build_centered_contact_face_audit())
        self.assertTrue(payload["source_candidate_metrics_identical"])
        self.assertTrue(payload["geom_order_independent"])

    def test_diagnostic_only_authority(self) -> None:
        payload = load_strict_json(ARTIFACT)
        self.assertEqual([row["candidate_index"] for row in payload["candidates"]], [2, 3])
        self.assertFalse(payload["simulation_training_ready"])
        self.assertFalse(payload["actual_mujoco_grasp_success"])


if __name__ == "__main__":
    unittest.main()
