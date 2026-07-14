"""Tests for deterministic, episode-first T18.1 valid-window selection."""

from __future__ import annotations

import copy
import json
import subprocess
import unittest

import pyarrow.parquet as pq

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.episode_first_window_sampling import (
    COMPILER_DIR,
    HORIZONS,
    REPO_ROOT,
    SAMPLING_SEED,
    WINDOW_DIR,
    _bucket_key,
    _describe_window,
    _unique_map,
    build_episode_first_window_sample,
    select_episode_first,
    verify_episode_first_window_sample,
)


class EpisodeFirstWindowSamplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = build_episode_first_window_sample()
        frame_rows = pq.read_table(COMPILER_DIR / "frames.parquet").to_pylist()
        segment_rows = pq.read_table(COMPILER_DIR / "segments.parquet").to_pylist()
        cls.frames = _unique_map(frame_rows, "frame_id", label="compiler frame")
        cls.segments = _unique_map(segment_rows, "segment_id", label="compiler segment")
        cls.window_rows = pq.read_table(WINDOW_DIR / "window_index.parquet").to_pylist()

    def test_sample_is_deterministic_episode_first_and_unique(self) -> None:
        verify_episode_first_window_sample(self.manifest)
        self.assertEqual(self.manifest["sampling_seed"], SAMPLING_SEED)
        self.assertEqual(self.manifest["source_episode_count"], 8)
        self.assertEqual(self.manifest["configured_bucket_count"], 24)
        self.assertEqual(self.manifest["realized_window_count"], 192)
        self.assertEqual(self.manifest["unique_window_ratio"], 1.0)
        self.assertFalse(self.manifest["training_eligible"])
        self.assertFalse(self.manifest["buffer_mutated"])
        by_bucket = {}
        for row in self.manifest["selected_windows"]:
            bucket = (row["source_class"], row["task_phase"], row["control_mode"], row["horizon"])
            by_bucket.setdefault(bucket, set()).add(row["rollout_id"])
        self.assertEqual(len(by_bucket), 24)
        self.assertTrue(all(len(rollouts) == 8 for rollouts in by_bucket.values()))

    def test_selector_is_order_independent_and_rejects_duplicate_or_short_buckets(self) -> None:
        compiler_manifest = load_strict_json(COMPILER_DIR / "compiler_manifest.json")
        descriptors = [
            _describe_window(
                row,
                frames=self.frames,
                segments=self.segments,
                compiler_manifest=compiler_manifest,
            )
            for row in self.window_rows
        ]
        first, first_summary = select_episode_first(descriptors)
        second, second_summary = select_episode_first(list(reversed(descriptors)))
        self.assertEqual(first, second)
        self.assertEqual(first_summary, second_summary)
        with self.assertRaisesRegex(ValueError, "duplicate window ID"):
            select_episode_first(descriptors + [copy.deepcopy(descriptors[0])])
        target_bucket = _bucket_key(descriptors[0])
        target_rollout = descriptors[0]["rollout_id"]
        short_bucket = [
            descriptor
            for descriptor in descriptors
            if not (
                _bucket_key(descriptor) == target_bucket
                and descriptor["rollout_id"] == target_rollout
            )
        ]
        with self.assertRaisesRegex(ValueError, "lacks realized episodes"):
            select_episode_first(short_bucket)

    def test_phase_spanning_window_and_authority_escalation_are_rejected(self) -> None:
        window = next(row for row in self.window_rows if row["horizon"] == 5)
        frame_ids = json.loads(window["frame_ids_json"])
        changed_frames = dict(self.frames)
        changed = dict(changed_frames[frame_ids[1]])
        changed["task_phase"] = "different_phase"
        changed_frames[frame_ids[1]] = changed
        with self.assertRaisesRegex(ValueError, "spans task phases"):
            _describe_window(
                window,
                frames=changed_frames,
                segments=self.segments,
                compiler_manifest=load_strict_json(COMPILER_DIR / "compiler_manifest.json"),
            )
        elevated = dict(self.manifest)
        elevated["model_loaded"] = True
        with self.assertRaisesRegex(ValueError, "identity"):
            verify_episode_first_window_sample(elevated)
        with self.assertRaisesRegex(ValueError, "authority flag"):
            verify_episode_first_window_sample(sign_payload(elevated))

    def test_raw_rewrite_is_rejected(self) -> None:
        result = subprocess.run(
            [
                str(REPO_ROOT / ".mujoco_venv/bin/python"),
                str(REPO_ROOT / "scripts/robot_lab/write_episode_first_window_sample.py"),
                "--rewrite",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("immutable", result.stderr)


if __name__ == "__main__":
    unittest.main()
