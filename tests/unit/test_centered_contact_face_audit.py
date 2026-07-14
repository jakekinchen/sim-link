"""Tests for centered bilateral contact-face audit."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.retired_grasp_diagnostics import load_frozen_artifact


class CenteredContactFaceAuditTests(unittest.TestCase):
    def test_checked_audit_is_deterministic_and_source_identical(self) -> None:
        payload = load_frozen_artifact("centered_contact_face_audit")
        self.assertTrue(payload["source_candidate_metrics_identical"])
        self.assertTrue(payload["geom_order_independent"])

    def test_diagnostic_only_authority(self) -> None:
        payload = load_frozen_artifact("centered_contact_face_audit")
        self.assertEqual([row["candidate_index"] for row in payload["candidates"]], [2, 3])
        self.assertFalse(payload["simulation_training_ready"])
        self.assertFalse(payload["actual_mujoco_grasp_success"])


if __name__ == "__main__":
    unittest.main()
