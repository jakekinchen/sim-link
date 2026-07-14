"""Tests for deterministic, unpadded T17.5 action-window compilation."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scenesmith.robot_lab.artifact_contract import dump_canonical_json
from scenesmith.robot_lab.experience_compiler import (
    SEGMENT_SCHEMA,
    compile_projection,
    write_compilation,
)
from scenesmith.robot_lab.experience_records import JOINT_NAMES, REPO_ROOT
from scenesmith.robot_lab.experience_window_index import (
    HORIZONS,
    OUTPUT_NAMES,
    compile_window_index,
    verify_window_index,
    write_window_index,
)


CONTRACT_PATH = REPO_ROOT / "configurations/robot_lab/experience_record_contract.json"
SOURCE_OUTPUT_DIR = REPO_ROOT / "configurations/robot_lab/t17_4_compile"


class ExperienceWindowIndexTests(unittest.TestCase):
    def test_current_fixture_is_empty_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-window-") as first_dir:
            first = compile_window_index(SOURCE_OUTPUT_DIR)
            write_window_index(first, Path(first_dir))
            verify_window_index(Path(first_dir), SOURCE_OUTPUT_DIR)
            with tempfile.TemporaryDirectory(prefix="scenesmith-window-") as second_dir:
                second = compile_window_index(SOURCE_OUTPUT_DIR)
                write_window_index(second, Path(second_dir))
                self.assertEqual(first["manifest"], second["manifest"])
                for name in OUTPUT_NAMES:
                    self.assertEqual(
                        (Path(first_dir) / name).read_bytes(),
                        (Path(second_dir) / name).read_bytes(),
                    )

        self.assertEqual(first["manifest"]["window_count"], 0)
        self.assertEqual(
            first["manifest"]["window_count_by_horizon"],
            {str(horizon): 0 for horizon in HORIZONS},
        )
        self.assertFalse(first["manifest"]["training_eligible"])

    def test_complete_segment_compiles_exact_unpadded_windows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-window-source-") as source_dir:
            self._write_source(Path(source_dir), frame_count=52)
            result = compile_window_index(Path(source_dir))

        self.assertEqual(
            result["manifest"]["window_count_by_horizon"],
            {"5": 48, "10": 43, "15": 38, "50": 3},
        )
        self.assertEqual(result["manifest"]["window_count"], 132)
        first = result["window_rows"][0]
        self.assertEqual(first["horizon"], 5)
        self.assertEqual(first["window_frame_count"], 5)
        self.assertEqual(
            first["frame_ids_json"],
            '["fixture-frame-000000","fixture-frame-000001","fixture-frame-000002","fixture-frame-000003","fixture-frame-000004"]',
        )
        self.assertEqual(first["action_frame_ids_json"], first["frame_ids_json"])
        self.assertEqual(first["action_variants_json"], '["requested","proposed","projected","sent","measured"]')

    def test_named_derived_actions_compile_into_windows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-window-source-") as source_dir:
            self._write_source(Path(source_dir), frame_count=6, derived_action_at=2)
            result = compile_window_index(Path(source_dir))

        self.assertEqual(result["manifest"]["window_count_by_horizon"]["5"], 2)

    def test_hard_boundaries_do_not_allow_cross_segment_windows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-window-source-") as source_dir:
            self._write_source(Path(source_dir), frame_count=8, boundary_at=4)
            result = compile_window_index(Path(source_dir))

        self.assertEqual(result["manifest"]["source_segment_count"], 2)
        self.assertEqual(result["manifest"]["window_count"], 0)
        self.assertEqual(
            result["manifest"]["segments_shorter_than_horizon_count_by_horizon"]["5"],
            2,
        )

    def test_noncontiguous_or_action_incomplete_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-window-source-") as source_dir:
            self._write_source(Path(source_dir), frame_count=6, noncontiguous_at=3)
            with self.assertRaisesRegex(ValueError, "contiguous"):
                compile_window_index(Path(source_dir))

        with tempfile.TemporaryDirectory(prefix="scenesmith-window-source-") as source_dir:
            self._write_source(Path(source_dir), frame_count=6, empty_action_at=3)
            with self.assertRaisesRegex(ValueError, "action values"):
                compile_window_index(Path(source_dir))

    def test_upstream_hash_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-window-source-") as source_dir:
            source = Path(source_dir)
            self._write_source(source, frame_count=6)
            frame_path = source / "frames.parquet"
            frame_path.write_bytes(frame_path.read_bytes() + b"drift")
            with self.assertRaisesRegex(ValueError, "hash drifted"):
                compile_window_index(source)

    def test_forged_segment_reference_and_authority_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-window-source-") as source_dir:
            source = Path(source_dir)
            self._write_source(source, frame_count=6)
            segments_path = source / "segments.parquet"
            segments = pq.read_table(segments_path).to_pylist()
            segments[0]["start_frame_id"] = "unknown-source-frame"
            pq.write_table(
                pa.Table.from_pylist(segments, schema=SEGMENT_SCHEMA),
                segments_path,
                compression="NONE",
                use_dictionary=False,
                write_statistics=False,
                version="2.6",
            )
            _restamp_source_output_hash(source, "segments.parquet")
            with self.assertRaisesRegex(ValueError, "start frame identity"):
                compile_window_index(source)

        with tempfile.TemporaryDirectory(prefix="scenesmith-window-output-") as output_dir:
            output = Path(output_dir)
            result = compile_window_index(SOURCE_OUTPUT_DIR)
            write_window_index(result, output)
            manifest_path = output / "window_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["training_eligible"] = True
            dump_canonical_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "authority flag drifted"):
                verify_window_index(output, SOURCE_OUTPUT_DIR)

    def _write_source(
        self,
        output_dir: Path,
        *,
        frame_count: int,
        boundary_at: int | None = None,
        noncontiguous_at: int | None = None,
        empty_action_at: int | None = None,
        derived_action_at: int | None = None,
    ) -> None:
        projection = _complete_projection(
            frame_count,
            boundary_at=boundary_at,
            noncontiguous_at=noncontiguous_at,
            empty_action_at=empty_action_at,
            derived_action_at=derived_action_at,
        )
        result = compile_projection(
            projection,
            source_experience_identity="a" * 64,
            source_normalization_identity="b" * 64,
        )
        write_compilation(result, output_dir)


def _complete_projection(
    frame_count: int,
    *,
    boundary_at: int | None,
    noncontiguous_at: int | None,
    empty_action_at: int | None,
    derived_action_at: int | None,
) -> dict:
    import json

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    projection = copy.deepcopy(contract["fixture_projection"])
    template = projection["frames"][0]
    rollout_id = projection["raw_rollout"]["rollout_id"]
    frames = []
    for index in range(frame_count):
        frame = copy.deepcopy(template)
        frame["frame_id"] = f"fixture-frame-{index:06d}"
        frame["rollout_id"] = rollout_id
        frame["frame_index"] = index + (
            1 if noncontiguous_at is not None and index >= noncontiguous_at else 0
        )
        frame["timestamp_ns"] = 1_000_000 * index
        frame["record_identity_sha256"] = f"{index + 1:064x}"
        frame["boundary_events"] = []
        if index == 0:
            frame["boundary_events"] = ["rollout_start"]
        if boundary_at is not None and index == boundary_at:
            frame["boundary_events"] = ["phase_change"]
        if index == frame_count - 1:
            frame["boundary_events"] = ["rollout_end"]
        frame["actions"] = {
            variant: {
                "state": "observed",
                "representation": "mujoco_radians",
                "units": "radian",
                "ordered_joint_names": ["joint"],
                "values": [float(index)],
                "provenance": {"state": "observed", "source": "test"},
                "reason": None,
            }
            for variant in ("requested", "proposed", "projected", "sent", "measured")
        }
        if index == empty_action_at:
            frame["actions"]["requested"]["values"] = []
        if index == derived_action_at:
            for action in frame["actions"].values():
                action["state"] = "derived"
                action["ordered_joint_names"] = list(JOINT_NAMES)
                action["values"] = [float(index)] * len(JOINT_NAMES)
                action["provenance"] = {
                    "state": "derived",
                    "source": "test",
                    "derivation": "scripted action equals requested action",
                }
        for field in ("requested_gripper_pose", "achieved_gripper_pose", "effort"):
            frame[field] = {
                "state": "observed",
                "value": float(index),
                "units": "unit",
                "provenance": {"state": "observed", "source": "test"},
                "reason": None,
            }
        frames.append(frame)
    projection["frames"] = frames
    return projection


def _restamp_source_output_hash(source: Path, name: str) -> None:
    manifest_path = source / "compiler_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][name] = hashlib.sha256((source / name).read_bytes()).hexdigest()
    dump_canonical_json(manifest_path, manifest)


if __name__ == "__main__":
    unittest.main()
