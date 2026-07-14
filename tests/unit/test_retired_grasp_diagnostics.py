"""Stored-hash verification for retired grasp diagnostics."""

from __future__ import annotations

import unittest

from scenesmith.robot_lab.retired_grasp_diagnostics import (
    FROZEN_GRASP_DIAGNOSTICS,
    load_frozen_artifact,
)


class RetiredGraspDiagnosticTests(unittest.TestCase):
    def test_every_frozen_artifact_is_signed_and_file_hash_pinned(self) -> None:
        self.assertGreaterEqual(len(FROZEN_GRASP_DIAGNOSTICS), 10)
        for name in FROZEN_GRASP_DIAGNOSTICS:
            with self.subTest(name=name):
                payload = load_frozen_artifact(name)
                self.assertFalse(payload.get("simulation_training_ready", False))
                self.assertFalse(payload.get("physical_follower_commanded", False))

    def test_unknown_artifact_fails_closed(self) -> None:
        with self.assertRaises(KeyError):
            load_frozen_artifact("not-a-real-diagnostic")


if __name__ == "__main__":
    unittest.main()
