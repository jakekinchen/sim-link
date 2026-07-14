"""Tests for the deterministic, model-free T17.7 replay audit."""

from __future__ import annotations

import copy
import subprocess
import unittest

import pyarrow.parquet as pq

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.compiler_window_replay_audit import (
    COMPILER_DIR,
    EPISODE_MANIFEST_PATH,
    HORIZONS,
    REPO_ROOT,
    SELECTION_PER_HORIZON,
    WINDOW_DIR,
    _actor_input_descriptor,
    _audit_window,
    _load_raw_frames,
    _unique_map,
    _validate_raw_compiler_frame,
    build_replay_audit,
    select_replay_windows,
    verify_replay_audit,
)


class CompilerWindowReplayAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = build_replay_audit()
        cls.window_rows = pq.read_table(WINDOW_DIR / "window_index.parquet").to_pylist()

    def test_audit_is_stratified_source_bound_and_model_free(self) -> None:
        audit = self.audit
        verify_replay_audit(audit)
        self.assertEqual(audit["selected_window_count"], 100)
        self.assertEqual(
            audit["selected_window_count_by_horizon"],
            {str(horizon): SELECTION_PER_HORIZON for horizon in HORIZONS},
        )
        self.assertFalse(audit["model_loaded"])
        self.assertFalse(audit["model_inference_executed"])
        self.assertFalse(audit["training_eligible"])
        self.assertEqual(len({window["window_id"] for window in audit["selected_windows"]}), 100)
        for horizon in HORIZONS:
            rollouts = {
                window["rollout_id"]
                for window in audit["selected_windows"]
                if window["horizon"] == horizon
            }
            self.assertEqual(len(rollouts), 8)
        frame = audit["selected_windows"][0]["frames"][0]
        self.assertEqual(
            frame["raw_frame_record_identity_sha256"],
            frame["compiler_frame_record_identity_sha256"],
        )

    def test_selection_is_deterministic_and_rejects_duplicates_or_horizon_skew(self) -> None:
        first = select_replay_windows(self.window_rows)
        second = select_replay_windows(list(reversed(self.window_rows)))
        self.assertEqual(
            [(rank, row["window_id"]) for rank, row in first],
            [(rank, row["window_id"]) for rank, row in second],
        )
        duplicate = list(self.window_rows) + [copy.deepcopy(self.window_rows[0])]
        with self.assertRaisesRegex(ValueError, "duplicate window ID"):
            select_replay_windows(duplicate)
        only_short = [row for row in self.window_rows if row["horizon"] != 50]
        with self.assertRaisesRegex(ValueError, "cannot supply"):
            select_replay_windows(only_short)

    def test_actor_input_descriptor_rejects_leakage_and_image_hash_drift(self) -> None:
        source_frame = self._source_raw_frame()
        leaked = copy.deepcopy(source_frame)
        leaked["actor_input_field_names"].append("reward.value")
        with self.assertRaisesRegex(ValueError, "actor input fields"):
            _actor_input_descriptor(leaked, leaked["actor_input_field_names"], label="test")
        image_drift = copy.deepcopy(source_frame)
        image_drift["observations"]["top"]["image_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "byte hash"):
            _actor_input_descriptor(
                image_drift, image_drift["actor_input_field_names"], label="test"
            )

    def test_raw_compiler_mismatch_and_internal_boundary_are_rejected(self) -> None:
        from scenesmith.robot_lab.artifact_contract import load_strict_json
        from scenesmith.robot_lab.scripted_grasp_episode_generation import default_store_root

        raw_frames = _load_raw_frames(
            load_strict_json(EPISODE_MANIFEST_PATH), default_store_root()
        )
        compiler_rows = pq.read_table(COMPILER_DIR / "frames.parquet").to_pylist()
        compiler_frames = _unique_map(compiler_rows, "frame_id", label="compiler frame")
        source_raw = next(iter(raw_frames.values()))
        mismatched = copy.deepcopy(compiler_frames[source_raw["frame_id"]])
        mismatched["record_identity_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "record identity"):
            _validate_raw_compiler_frame(source_raw, mismatched)

        audit_window = next(
            window for window in self.audit["selected_windows"] if window["horizon"] == 5
        )
        window_row = next(
            row for row in self.window_rows if row["window_id"] == audit_window["window_id"]
        )
        segments = _unique_map(
            pq.read_table(COMPILER_DIR / "segments.parquet").to_pylist(),
            "segment_id",
            label="compiler segment",
        )
        boundary_frames = dict(compiler_frames)
        internal_id = audit_window["frames"][1]["frame_id"]
        internal = dict(boundary_frames[internal_id])
        internal["boundary_events_json"] = '["reset"]'
        boundary_frames[internal_id] = internal
        with self.assertRaisesRegex(ValueError, "internal hard boundary"):
            _audit_window(
                window_row,
                selection_rank=1,
                raw_frames=raw_frames,
                compiler_frames=boundary_frames,
                segments=segments,
                compiler_manifest=load_strict_json(COMPILER_DIR / "compiler_manifest.json"),
            )

    def test_manifest_drift_and_raw_rewrite_are_rejected(self) -> None:
        changed = dict(self.audit)
        changed["model_loaded"] = True
        with self.assertRaisesRegex(ValueError, "identity"):
            verify_replay_audit(changed)
        elevated = sign_payload(changed)
        with self.assertRaisesRegex(ValueError, "authority flag"):
            verify_replay_audit(elevated)
        result = subprocess.run(
            [
                str(REPO_ROOT / ".mujoco_venv/bin/python"),
                str(REPO_ROOT / "scripts/robot_lab/write_compiler_window_replay_audit.py"),
                "--rewrite",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("immutable", result.stderr)

    @staticmethod
    def _source_raw_frame() -> dict:
        from scenesmith.robot_lab.compiler_window_replay_audit import (
            _load_raw_frames,
        )
        from scenesmith.robot_lab.artifact_contract import load_strict_json
        from scenesmith.robot_lab.scripted_grasp_episode_generation import (
            default_store_root,
        )

        frames = _load_raw_frames(load_strict_json(EPISODE_MANIFEST_PATH), default_store_root())
        return next(iter(frames.values()))


if __name__ == "__main__":
    unittest.main()
