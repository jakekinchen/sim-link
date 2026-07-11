from __future__ import annotations

import json
import math
import os
import sys
import types
import unittest

from pathlib import Path
from unittest import mock

from scenesmith.robot_lab.lerobot_stack import (
    activate_lerobot_stack,
    build_stack_identity,
    process_saved_sample,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE = REPO_ROOT / "tests/fixtures/robot_lab/lerobot_stack/sample.json"


class LeRobotStackTests(unittest.TestCase):
    def test_current_checkout_matches_tracked_executable_identity(self):
        identity = build_stack_identity(repo_root=REPO_ROOT)
        self.assertEqual(identity["base_revision"], "e40b58a8dfa9e7b86918c374791599d070518d11")
        self.assertEqual(identity["roles"], ["collection", "training", "finalization", "inference", "lelab"])
        self.assertEqual(len(identity["identity_sha256"]), 64)

    def test_rejects_critical_environment_drift(self):
        with mock.patch.dict(os.environ, {"SCENESMITH_GRIPPER_LOSS_WEIGHT": "2"}):
            with self.assertRaisesRegex(ValueError, "environment drifted"):
                build_stack_identity(repo_root=REPO_ROOT)

    def test_collection_training_and_inference_sample_conformance(self):
        sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
        results = {
            stage: process_saved_sample(sample, repo_root=REPO_ROOT, stage=stage)
            for stage in ("collection", "training", "inference")
        }
        comparable = {
            stage: {key: value for key, value in result.items() if key != "stage"}
            for stage, result in results.items()
        }
        self.assertEqual(comparable["collection"], comparable["training"])
        self.assertEqual(comparable["training"], comparable["inference"])
        for expected, actual in zip(sample["action"], results["inference"]["decoded_action_radians"], strict=True):
            self.assertTrue(math.isclose(expected, actual, rel_tol=0.0, abs_tol=1e-12))

    def test_activate_rejects_unknown_stage(self):
        with self.assertRaisesRegex(ValueError, "Unsupported LeRobot stage"):
            activate_lerobot_stack(repo_root=REPO_ROOT, stage="promotion")

    def test_activate_rejects_already_imported_package_from_other_runtime(self):
        foreign = types.ModuleType("lerobot")
        foreign.__file__ = "/tmp/foreign-runtime/lerobot/__init__.py"
        with mock.patch.dict(sys.modules, {"lerobot": foreign}):
            with self.assertRaisesRegex(RuntimeError, "outside the unified stack"):
                activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")


if __name__ == "__main__":
    unittest.main()
