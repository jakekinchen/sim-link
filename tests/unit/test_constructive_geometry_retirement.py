"""Guard the small constructive grasp surface against search-wrapper relapse."""

from __future__ import annotations

import unittest

from pathlib import Path

from scenesmith.robot_lab.retired_grasp_diagnostics import (
    FROZEN_GRASP_DIAGNOSTICS,
    load_frozen_artifact,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ROBOT_LAB = REPO_ROOT / "scenesmith" / "robot_lab"
RETIRED_MODULES = (
    "geometry_first_grasp_search",
    "explicit_pad_proxy_search",
    "pad_midpoint_search",
    "post_yaw_settle_search",
    "principal_axis_grasp_search",
    "horizontal_axis_grasp_search",
    "best_axis_grasp_search",
    "centered_axis_grasp_search",
    "centered_contact_face_audit",
)


class ConstructiveGeometryRetirementTests(unittest.TestCase):
    def test_retired_wrapper_sources_are_absent(self) -> None:
        for module in RETIRED_MODULES:
            with self.subTest(module=module):
                self.assertFalse((ROBOT_LAB / f"{module}.py").exists())

    def test_live_primitives_have_no_halton_candidate_generator(self) -> None:
        source = (ROBOT_LAB / "geometry_derived_grasp_primitives.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("HALTON_BASES", source)
        self.assertNotIn("TRAINING_CANDIDATES", source)
        self.assertNotIn("def _candidate", source)

    def test_frozen_diagnostics_remain_hash_pinned_and_non_promoting(self) -> None:
        for name in RETIRED_MODULES:
            with self.subTest(name=name):
                self.assertIn(name, FROZEN_GRASP_DIAGNOSTICS)
                payload = load_frozen_artifact(name)
                self.assertFalse(payload.get("simulation_training_ready", False))
                self.assertFalse(payload.get("physical_follower_commanded", False))


if __name__ == "__main__":
    unittest.main()
