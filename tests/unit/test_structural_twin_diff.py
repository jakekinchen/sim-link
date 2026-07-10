from __future__ import annotations

import hashlib
import json
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.structural_twin_diff import (
    DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
    MUJOCO_OPTION_DEFAULTS,
    _compare_category,
    build_structural_twin_diff,
    verify_structural_twin_diff,
    write_structural_twin_diff,
)
from scenesmith.robot_lab.twin_contract import DEFAULT_TWIN_PROFILE_PATH


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CATEGORIES = {
    "inertials",
    "joint_frames",
    "joint_limits",
    "actuators",
    "arm_collisions",
    "gripper_collisions",
    "cameras",
    "solver_settings",
    "friction",
    "backlash",
    "named_sites",
}


def _resign(payload: dict) -> None:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    payload["identity_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class StructuralTwinDiffTests(unittest.TestCase):
    def test_build_and_verify_current_repo_diff(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)

        verify_structural_twin_diff(payload, repo_root=REPO_ROOT)

        self.assertEqual(set(payload["categories"]), REQUIRED_CATEGORIES)
        for category_name, category in payload["categories"].items():
            self.assertEqual(
                set(category),
                {"matched", "mismatched", "missing", "extra", "unknown"},
                category_name,
            )
        self.assertEqual(
            payload["sources"]["runtime"]["path"],
            "external/SO-ARM100/Simulation/SO101/so101_new_calib.xml",
        )
        self.assertEqual(
            payload["sources"]["menagerie"]["path"],
            "third_party/mujoco_menagerie/robotstudio_so101/so101.xml",
        )
        self.assertEqual(
            payload["twin_profile_ref"]["path"],
            "configurations/robot_lab/pi05_twin_profile.simulation_only.json",
        )
        expected_profile = json.loads((REPO_ROOT / DEFAULT_TWIN_PROFILE_PATH).read_text(encoding="utf-8"))
        self.assertEqual(
            payload["twin_profile_ref"]["identity_sha256"],
            expected_profile["identity_sha256"],
        )
        gripperframe = next(
            record
            for record in payload["categories"]["named_sites"]["mismatched"]
            if record["key"] == "site:gripperframe"
        )
        self.assertNotIn("quat", gripperframe["numeric_deltas"])
        self.assertEqual(
            gripperframe["compared_values"],
            {
                "runtime": {"quat": [0.707106781, -0.0, 0.707106781, -0.0]},
                "menagerie": {"quat": [0.707106781, 0.0, 0.707106781, 0.0]},
            },
        )
        solver_mismatches = payload["categories"]["solver_settings"]["mismatched"]
        self.assertTrue(
            any(
                record["key"] == "option:global"
                and record["runtime"]["integrator"] == MUJOCO_OPTION_DEFAULTS["integrator"]
                and record["menagerie"]["integrator"] == "implicitfast"
                for record in solver_mismatches
            )
        )
        self.assertFalse(payload["categories"]["solver_settings"]["missing"])
        self.assertTrue(
            any(
                record["key"] == "joint:wrist_roll"
                for record in payload["categories"]["joint_limits"]["mismatched"]
            )
        )
        self.assertTrue(payload["summary"]["mismatched_records"] > 0)

    def test_compare_category_matches_equivalent_quaternions(self):
        category = _compare_category(
            "named_sites",
            {
                "site:gripperframe": {
                    "quat": [0.707107, 0.0, 0.707107, 0.0],
                }
            },
            {
                "site:gripperframe": {
                    "quat": [1.0, 0.0, 1.0, 0.0],
                }
            },
        )

        self.assertEqual(len(category["matched"]), 1)
        self.assertFalse(category["mismatched"])

    def test_compare_category_records_canonical_quaternion_values_for_true_mismatch(self):
        category = _compare_category(
            "named_sites",
            {
                "site:tool": {
                    "quat": [0.0, 0.0, 0.707107, 0.707107],
                }
            },
            {
                "site:tool": {
                    "quat": [0.0, 0.0, 1.0, 0.0],
                }
            },
        )

        mismatch = category["mismatched"][0]
        self.assertEqual(
            mismatch["compared_values"],
            {
                "runtime": {"quat": [0.0, 0.0, 0.707106781, 0.707106781]},
                "menagerie": {"quat": [0.0, 0.0, 1.0, 0.0]},
            },
        )

    def test_compare_category_uses_effective_solver_defaults_when_option_is_omitted(self):
        category = _compare_category(
            "solver_settings",
            {"option:global": dict(MUJOCO_OPTION_DEFAULTS)},
            {
                "option:global": {
                    **MUJOCO_OPTION_DEFAULTS,
                    "integrator": "implicitfast",
                    "iterations": 10.0,
                    "ls_iterations": 20.0,
                    "impratio": 10.0,
                    "cone": "elliptic",
                    "timestep": 0.005,
                }
            },
        )

        self.assertFalse(category["missing"])
        self.assertFalse(category["extra"])
        mismatch = category["mismatched"][0]
        self.assertEqual(mismatch["key"], "option:global")
        self.assertEqual(mismatch["runtime"]["integrator"], "euler")
        self.assertEqual(
            mismatch["numeric_deltas"],
            {
                "impratio": -9.0,
                "iterations": 90.0,
                "ls_iterations": 30.0,
                "timestep": -0.003,
            },
        )

    def test_write_current_repo_artifact_is_deterministic(self):
        expected = build_structural_twin_diff(repo_root=REPO_ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / DEFAULT_STRUCTURAL_TWIN_DIFF_PATH.name
            written = write_structural_twin_diff(repo_root=REPO_ROOT, output_path=artifact_path)
            verified = json.loads(artifact_path.read_text(encoding="utf-8"))

        self.assertEqual(written, expected)
        self.assertEqual(verified, expected)

    def test_verify_rejects_artifact_identity_tamper(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)
        payload["summary"]["mismatched_records"] += 1

        with self.assertRaisesRegex(ValueError, "identity hash is invalid"):
            verify_structural_twin_diff(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_source_hash_tamper(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)
        payload["sources"]["menagerie"]["sha256"] = "0" * 64
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "Menagerie source hash drifted"):
            verify_structural_twin_diff(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_missing_category(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)
        payload["categories"].pop("cameras")
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "Missing structural diff categories"):
            verify_structural_twin_diff(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_twin_profile_identity_tamper(self):
        payload = build_structural_twin_diff(repo_root=REPO_ROOT)
        payload["twin_profile_ref"]["identity_sha256"] = "0" * 64
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "Twin profile identity drifted"):
            verify_structural_twin_diff(payload, repo_root=REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
