from __future__ import annotations

import json
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.simulation_training_spec import (
    EVALUATION_SEEDS,
    TRAIN_SEEDS,
    build_training_spec,
    verify_training_spec,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class SimulationTrainingSpecTests(unittest.TestCase):
    def test_three_episode_spec_is_source_bound_and_deterministic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tensor = Path(tmpdir) / "t20_1_tensor_view.npz"
            payload = build_training_spec(repo_root=REPO_ROOT, tensor_view_path=tensor)
            verify_training_spec(payload, repo_root=REPO_ROOT, tensor_view_path=tensor)

            self.assertEqual(payload["train_seeds"], list(TRAIN_SEEDS))
            self.assertEqual(payload["evaluation_seeds"], list(EVALUATION_SEEDS))
            self.assertEqual(payload["split_frame_counts"], {"train": 488, "evaluation": 244})
            self.assertTrue(payload["simulation_only"])
            self.assertTrue(tensor.is_file())
            self.assertFalse(payload["simulation_training_ready"])
            self.assertFalse(payload["optimizer_training"])
            self.assertFalse(payload["physical_actuation"])

    def test_changed_authority_or_selected_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tensor = Path(tmpdir) / "t20_1_tensor_view.npz"
            payload = build_training_spec(repo_root=REPO_ROOT, tensor_view_path=tensor)
            for key, value in (("optimizer_training", True), ("simulation_training_ready", True)):
                changed = json.loads(json.dumps(payload))
                changed[key] = value
                with self.subTest(key=key):
                    with self.assertRaisesRegex(ValueError, "drifted"):
                        verify_training_spec(sign_payload(changed), repo_root=REPO_ROOT, tensor_view_path=tensor)
            changed = json.loads(json.dumps(payload))
            changed["selected_episodes"][0]["episode_file_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "drifted"):
                verify_training_spec(sign_payload(changed), repo_root=REPO_ROOT, tensor_view_path=tensor)

    def test_existing_tensor_view_with_different_bytes_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tensor = Path(tmpdir) / "t20_1_tensor_view.npz"
            tensor.write_bytes(b"not a source-bound tensor view")
            with self.assertRaisesRegex(ValueError, "different bytes"):
                build_training_spec(repo_root=REPO_ROOT, tensor_view_path=tensor)
