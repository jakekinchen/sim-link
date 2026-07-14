"""Tests that hash outputs from the actual pinned LeRobot PI0.5 processor."""

from __future__ import annotations

import copy
import tempfile
import unittest

from pathlib import Path

try:
    import numpy as np
    import torch
    from lerobot.datasets import LeRobotDataset
except ModuleNotFoundError:
    np = None
    torch = None
    LeRobotDataset = None

from scenesmith.robot_lab.lerobot_actual_processor_observation import (
    build_lerobot_processor_observation,
    verify_lerobot_processor_observation,
)
from scenesmith.robot_lab.lerobot_native_episode_manifest import (
    build_lerobot_episode_manifest,
)


_PROCESSOR_ROOT = (
    Path.home()
    / ".cache/huggingface/hub/models--Cache-SCA--pi05_teleop_sort_block/snapshots"
    / "84b551af1303e92d97d6752d43cc3c9f1a090778"
)
_TOKENIZER_ROOT = (
    Path.home()
    / ".cache/huggingface/hub/models--google--paligemma-3b-pt-224/snapshots"
    / "35e4f46485b4d07967e7e9935bc3786aad50687c"
)


@unittest.skipUnless(
    np is not None
    and torch is not None
    and LeRobotDataset is not None
    and _PROCESSOR_ROOT.is_dir()
    and _TOKENIZER_ROOT.is_dir(),
    "requires the pinned LeRobot training runtime and local PI0.5 processor snapshot",
)
class LeRobotActualProcessorObservationTests(unittest.TestCase):
    def test_actual_processor_output_is_deterministic_and_source_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = self._build_dataset(Path(temporary) / "dataset")
            annotations = [
                {
                    "episode_index": 0,
                    "raw_rollout_identity_sha256": "a" * 64,
                    "eligible": True,
                    "quarantine_reason": None,
                }
            ]
            manifest = build_lerobot_episode_manifest(
                dataset,
                dataset_label="fixture/processor",
                episode_annotations=annotations,
            )

            first = build_lerobot_processor_observation(
                dataset,
                episode_manifest=manifest,
                dataset_label="fixture/processor",
                episode_annotations=annotations,
                frame_index=0,
                processor_root=_PROCESSOR_ROOT,
                tokenizer_root=_TOKENIZER_ROOT,
            )
            second = build_lerobot_processor_observation(
                dataset,
                episode_manifest=manifest,
                dataset_label="fixture/processor",
                episode_annotations=annotations,
                frame_index=0,
                processor_root=_PROCESSOR_ROOT,
                tokenizer_root=_TOKENIZER_ROOT,
            )

            self.assertEqual(first, second)
            self.assertEqual(
                first["pipeline"]["step_classes"],
                [
                    "RenameObservationsProcessorStep",
                    "AddBatchDimensionProcessorStep",
                    "NormalizerProcessorStep",
                    "Pi05PrepareStateTokenizerProcessorStep",
                    "TokenizerProcessorStep",
                    "DeviceProcessorStep",
                ],
            )
            self.assertTrue(first["processor_executed"])
            self.assertFalse(first["normalization_reimplemented"])
            self.assertFalse(first["model_instantiated"])
            self.assertFalse(first["policy_inference_executed"])
            self.assertIn("observation.state", first["output"]["entries"])
            verify_lerobot_processor_observation(
                first,
                dataset,
                episode_manifest=manifest,
                dataset_label="fixture/processor",
                episode_annotations=annotations,
                frame_index=0,
                processor_root=_PROCESSOR_ROOT,
                tokenizer_root=_TOKENIZER_ROOT,
            )

            altered = copy.deepcopy(first)
            altered["processor_executed"] = False
            with self.assertRaises(ValueError):
                verify_lerobot_processor_observation(
                    altered,
                    dataset,
                    episode_manifest=manifest,
                    dataset_label="fixture/processor",
                    episode_annotations=annotations,
                    frame_index=0,
                    processor_root=_PROCESSOR_ROOT,
                    tokenizer_root=_TOKENIZER_ROOT,
                )

    @staticmethod
    def _build_dataset(root: Path):
        features = {
            "observation.images.top": {
                "dtype": "image",
                "shape": (3, 224, 224),
                "names": ["channel", "height", "width"],
            },
            "observation.images.wrist": {
                "dtype": "image",
                "shape": (3, 224, 224),
                "names": ["channel", "height", "width"],
            },
            "observation.state": {
                "dtype": "float32",
                "shape": (6,),
                "names": [f"joint_{index}" for index in range(6)],
            },
            "action": {
                "dtype": "float32",
                "shape": (6,),
                "names": [f"joint_{index}" for index in range(6)],
            },
        }
        dataset = LeRobotDataset.create(
            repo_id="scenesmith/processor-fixture",
            root=root,
            fps=30,
            robot_type="fixture",
            features=features,
            use_videos=False,
        )
        for frame in range(2):
            dataset.add_frame(
                {
                    "observation.images.top": np.full(
                        (3, 224, 224), frame / 255.0, dtype=np.float32
                    ),
                    "observation.images.wrist": np.full(
                        (3, 224, 224), (frame + 1) / 255.0, dtype=np.float32
                    ),
                    "observation.state": torch.tensor(
                        [float(index + frame) for index in range(6)], dtype=torch.float32
                    ),
                    "action": torch.tensor(
                        [float(frame - index) for index in range(6)], dtype=torch.float32
                    ),
                    "task": "pick up the fixture anchor",
                }
            )
        dataset.save_episode()
        dataset.finalize()
        return LeRobotDataset(
            "scenesmith/processor-fixture",
            root=root,
            return_uint8=True,
            download_videos=False,
        )
