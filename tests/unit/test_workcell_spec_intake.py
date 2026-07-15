"""Fail-closed tests for the compact workcell arrangement intake."""

from __future__ import annotations

import json
import unittest

from pathlib import Path

from scenesmith.robot_lab.workcell_spec_intake import (
    SPEC_SCHEMA_VERSION,
    scene_from_arrangement_spec,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_SPEC = REPO_ROOT / "configurations/robot_lab/workcell_spec_example.json"


def _valid_spec() -> dict:
    return {
        "schema_version": SPEC_SCHEMA_VERSION,
        "scene_id": "unit_test_cell",
        "trays": [
            {"name": "red_tray", "color": "red", "center_m": [0.32, -0.12, 0.316]}
        ],
        "cubes": [
            {"name": "red_cube", "color": "red", "position_m": [0.2, 0.0, 0.325]}
        ],
    }


class WorkcellSpecIntakeTest(unittest.TestCase):
    def test_valid_spec_builds_scene(self) -> None:
        scene = scene_from_arrangement_spec(_valid_spec())
        self.assertEqual(scene.scene_id, "unit_test_cell")
        self.assertEqual(len(scene.cubes), 1)
        self.assertEqual(len(scene.trays), 1)
        self.assertEqual(scene.cubes[0].color, "red")
        self.assertTrue(scene.policy.task.strip())
        self.assertEqual(
            scene.source["arrangement_schema_version"], SPEC_SCHEMA_VERSION
        )

    def test_example_spec_parses(self) -> None:
        payload = json.loads(EXAMPLE_SPEC.read_text(encoding="utf-8"))
        scene = scene_from_arrangement_spec(payload)
        self.assertEqual(scene.scene_id, "sorting_demo_two_cube")
        self.assertEqual(len(scene.cubes), 2)
        self.assertEqual(len(scene.trays), 2)

    def test_unknown_top_level_field_rejects(self) -> None:
        spec = _valid_spec()
        spec["metric_authority"] = True
        with self.assertRaises(ValueError):
            scene_from_arrangement_spec(spec)

    def test_bad_color_rejects(self) -> None:
        spec = _valid_spec()
        spec["cubes"][0]["color"] = "turquoise"
        with self.assertRaises(ValueError):
            scene_from_arrangement_spec(spec)

    def test_off_desk_position_rejects(self) -> None:
        spec = _valid_spec()
        spec["cubes"][0]["position_m"] = [2.0, 0.0, 0.325]
        with self.assertRaises(ValueError):
            scene_from_arrangement_spec(spec)

    def test_non_finite_position_rejects(self) -> None:
        spec = _valid_spec()
        spec["cubes"][0]["position_m"] = [float("nan"), 0.0, 0.325]
        with self.assertRaises(ValueError):
            scene_from_arrangement_spec(spec)

    def test_overlapping_cubes_reject(self) -> None:
        spec = _valid_spec()
        spec["cubes"].append(
            {"name": "blue_cube", "color": "blue", "position_m": [0.21, 0.0, 0.325]}
        )
        with self.assertRaises(ValueError):
            scene_from_arrangement_spec(spec)

    def test_duplicate_names_reject(self) -> None:
        spec = _valid_spec()
        spec["cubes"].append(
            {"name": "red_tray", "color": "blue", "position_m": [0.26, 0.08, 0.325]}
        )
        with self.assertRaises(ValueError):
            scene_from_arrangement_spec(spec)

    def test_wrong_schema_version_rejects(self) -> None:
        spec = _valid_spec()
        spec["schema_version"] = "scenesmith.workcell_arrangement_spec.v0"
        with self.assertRaises(ValueError):
            scene_from_arrangement_spec(spec)


if __name__ == "__main__":
    unittest.main()
