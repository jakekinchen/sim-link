"""Tests for the source-bound T17.4 experience compiler."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.experience_compiler import (
    compile_experience_contract,
    compile_projection,
    verify_compilation,
)
from scenesmith.robot_lab.experience_records import REPO_ROOT


CONTRACT_PATH = REPO_ROOT / "configurations/robot_lab/experience_record_contract.json"
NORMALIZATION_PATH = REPO_ROOT / "configurations/robot_lab/normalization_bundle.json"


class ExperienceCompilerTests(unittest.TestCase):
    def test_current_fixture_is_quarantined_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-compiler-") as first_dir:
            first = compile_experience_contract(
                CONTRACT_PATH, NORMALIZATION_PATH, Path(first_dir)
            )
            verify_compilation(Path(first_dir))
            with tempfile.TemporaryDirectory(prefix="scenesmith-compiler-") as second_dir:
                second = compile_experience_contract(
                    CONTRACT_PATH, NORMALIZATION_PATH, Path(second_dir)
                )
                self.assertEqual(first["manifest"], second["manifest"])
                for name in (
                    "frames.parquet",
                    "segments.parquet",
                    "quarantine_manifest.json",
                    "compiler_manifest.json",
                ):
                    self.assertEqual(
                        (Path(first_dir) / name).read_bytes(),
                        (Path(second_dir) / name).read_bytes(),
                    )
        self.assertEqual(first["manifest"]["frame_count"], 2)
        self.assertEqual(first["manifest"]["eligible_frame_count"], 0)
        self.assertEqual(first["manifest"]["segment_count"], 0)
        self.assertGreaterEqual(first["manifest"]["quarantine_count"], 2)
        self.assertFalse(first["manifest"]["training_eligible"])

    def test_quarantined_frame_cannot_bridge_two_eligible_segments(self) -> None:
        contract = load_strict_json(CONTRACT_PATH)
        projection = copy.deepcopy(contract["fixture_projection"])
        template = projection["frames"][0]
        frames = [copy.deepcopy(template) for _ in range(3)]
        for index, frame in enumerate(frames):
            frame["frame_index"] = index
            frame["frame_id"] = f"{projection['raw_rollout']['rollout_id']}-frame-{index:06d}"
            frame["timestamp_ns"] = index + 1
            frame["boundary_events"] = []
            frame["record_identity_sha256"] = f"{index + 1:064x}"
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
            for field in ("requested_gripper_pose", "achieved_gripper_pose", "effort"):
                frame[field] = {
                    "state": "observed",
                    "value": float(index),
                    "units": "unit",
                    "provenance": {"state": "observed", "source": "test"},
                    "reason": None,
                }
        frames[1]["actions"]["measured"]["state"] = "not_observed"
        projection["frames"] = frames
        result = compile_projection(
            projection,
            source_experience_identity="a" * 64,
            source_normalization_identity="b" * 64,
        )
        self.assertEqual(result["manifest"]["eligible_frame_count"], 2)
        self.assertEqual(result["manifest"]["segment_count"], 0)
        self.assertEqual(
            sum(
                "segment_too_short_after_hard_boundary" in item["reason_codes"]
                for item in result["quarantine"]
            ),
            2,
        )

    def test_complete_projection_forms_segment_and_boundary_splits(self) -> None:
        contract = load_strict_json(CONTRACT_PATH)
        projection = copy.deepcopy(contract["fixture_projection"])
        for index, frame in enumerate(projection["frames"]):
            frame["boundary_events"] = []
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
            for field in ("requested_gripper_pose", "achieved_gripper_pose", "effort"):
                frame[field] = {
                    "state": "observed",
                    "value": float(index),
                    "units": "unit",
                    "provenance": {"state": "observed", "source": "test"},
                    "reason": None,
                }
        result = compile_projection(
            projection,
            source_experience_identity="a" * 64,
            source_normalization_identity="b" * 64,
        )
        self.assertEqual(result["manifest"]["eligible_frame_count"], 2)
        self.assertEqual(result["manifest"]["segment_count"], 1)

        projection["frames"][1]["boundary_events"] = ["prompt_change"]
        split = compile_projection(
            projection,
            source_experience_identity="a" * 64,
            source_normalization_identity="b" * 64,
        )
        self.assertEqual(split["manifest"]["segment_count"], 0)
        self.assertTrue(
            any(
                "segment_too_short_after_hard_boundary" in item["reason_codes"]
                for item in split["quarantine"]
            )
        )

    def test_timestamp_gap_is_a_quarantine_boundary(self) -> None:
        contract = load_strict_json(CONTRACT_PATH)
        projection = copy.deepcopy(contract["fixture_projection"])
        for frame in projection["frames"]:
            frame["boundary_events"] = []
            frame["actions"] = {
                variant: {
                    "state": "observed",
                    "representation": "mujoco_radians",
                    "units": "radian",
                    "ordered_joint_names": ["joint"],
                    "values": [0.0],
                    "provenance": {"state": "observed", "source": "test"},
                    "reason": None,
                }
                for variant in ("requested", "proposed", "projected", "sent", "measured")
            }
            for field in ("requested_gripper_pose", "achieved_gripper_pose", "effort"):
                frame[field] = {
                    "state": "observed",
                    "value": 0.0,
                    "units": "unit",
                    "provenance": {"state": "observed", "source": "test"},
                    "reason": None,
                }
        projection["frames"][1]["timestamp_ns"] = 10_000
        result = compile_projection(
            projection,
            source_experience_identity="a" * 64,
            source_normalization_identity="b" * 64,
            max_timestamp_gap_ns=100,
        )
        self.assertEqual(result["manifest"]["segment_count"], 0)
        self.assertTrue(
            any(
                "timestamp_gap" in item["reason_codes"]
                for item in result["quarantine"]
            )
        )


if __name__ == "__main__":
    unittest.main()
