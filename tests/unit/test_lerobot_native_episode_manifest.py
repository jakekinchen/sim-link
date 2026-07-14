"""Tests for the thin signed provenance view over a real LeRobotDataset."""

from __future__ import annotations

import copy
import tempfile
import unittest

from pathlib import Path

try:
    import torch
    from lerobot.datasets import LeRobotDataset
except ModuleNotFoundError:
    torch = None
    LeRobotDataset = None

from scenesmith.robot_lab.lerobot_native_episode_manifest import (
    build_lerobot_episode_manifest,
    verify_lerobot_episode_manifest,
)


@unittest.skipUnless(
    torch is not None and LeRobotDataset is not None,
    "requires the pinned LeRobot training runtime",
)
class LeRobotNativeEpisodeManifestTests(unittest.TestCase):
    def test_real_dataset_manifest_is_deterministic_and_quarantines_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = self._build_dataset(Path(temporary) / "dataset")
            annotations = [
                {
                    "episode_index": 0,
                    "raw_rollout_identity_sha256": "a" * 64,
                    "eligible": True,
                    "quarantine_reason": None,
                },
                {
                    "episode_index": 1,
                    "raw_rollout_identity_sha256": "b" * 64,
                    "eligible": False,
                    "quarantine_reason": "fixture_episode_is_not_training_eligible",
                },
            ]

            first = build_lerobot_episode_manifest(
                dataset,
                dataset_label="fixture/two-episode",
                episode_annotations=annotations,
            )
            second = build_lerobot_episode_manifest(
                dataset,
                dataset_label="fixture/two-episode",
                episode_annotations=annotations,
            )

            self.assertEqual(first, second)
            self.assertEqual(first["dataset"]["total_episodes"], 2)
            self.assertEqual(first["dataset"]["total_frames"], 4)
            self.assertEqual(first["eligible_episode_count"], 1)
            self.assertEqual(first["quarantined_episode_count"], 1)
            self.assertEqual(first["new_storage_rows_created"], 0)
            self.assertFalse(first["simulation_training_ready"])
            verify_lerobot_episode_manifest(
                first,
                dataset,
                dataset_label="fixture/two-episode",
                episode_annotations=annotations,
            )

            changed_annotations = copy.deepcopy(annotations)
            changed_annotations[0]["eligible"] = False
            changed_annotations[0]["quarantine_reason"] = "changed"
            with self.assertRaisesRegex(ValueError, "drifted"):
                verify_lerobot_episode_manifest(
                    first,
                    dataset,
                    dataset_label="fixture/two-episode",
                    episode_annotations=changed_annotations,
                )

    def test_manifest_rejects_missing_or_invalid_episode_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = self._build_dataset(Path(temporary) / "dataset")
            annotation = {
                "episode_index": 0,
                "raw_rollout_identity_sha256": "a" * 64,
                "eligible": True,
                "quarantine_reason": None,
            }
            with self.assertRaisesRegex(ValueError, "every LeRobot episode"):
                build_lerobot_episode_manifest(
                    dataset,
                    dataset_label="fixture/two-episode",
                    episode_annotations=[annotation],
                )

            invalid = [
                annotation,
                {**annotation, "episode_index": 1, "eligible": False},
            ]
            with self.assertRaisesRegex(ValueError, "quarantine reason"):
                build_lerobot_episode_manifest(
                    dataset,
                    dataset_label="fixture/two-episode",
                    episode_annotations=invalid,
                )

    @staticmethod
    def _build_dataset(root: Path):
        features = {
            "observation.state": {
                "dtype": "float32",
                "shape": (2,),
                "names": ["joint_a", "joint_b"],
            },
            "action": {
                "dtype": "float32",
                "shape": (2,),
                "names": ["joint_a", "joint_b"],
            },
        }
        dataset = LeRobotDataset.create(
            repo_id="scenesmith/manifest-fixture",
            root=root,
            fps=30,
            robot_type="fixture",
            features=features,
            use_videos=False,
        )
        for episode in range(2):
            for frame in range(2):
                dataset.add_frame(
                    {
                        "observation.state": torch.tensor(
                            [float(episode), float(frame)], dtype=torch.float32
                        ),
                        "action": torch.tensor(
                            [float(frame), float(episode)], dtype=torch.float32
                        ),
                        "task": "fixture grasp",
                    }
                )
            dataset.save_episode()
        dataset.finalize()
        return LeRobotDataset(
            "scenesmith/manifest-fixture",
            root=root,
            return_uint8=True,
            download_videos=False,
        )
