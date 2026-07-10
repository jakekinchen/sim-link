from __future__ import annotations

import hashlib
import json
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.structural_twin_diff import (
    DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
    build_structural_twin_diff,
    verify_structural_twin_diff,
    write_structural_twin_diff,
)


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
        self.assertTrue(
            any(
                record["key"] == "site:gripperframe"
                for record in payload["categories"]["named_sites"]["mismatched"]
            )
        )
        self.assertTrue(
            any(
                record["key"] == "joint:wrist_roll"
                for record in payload["categories"]["joint_limits"]["mismatched"]
            )
        )
        self.assertTrue(payload["summary"]["mismatched_records"] > 0)

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


if __name__ == "__main__":
    unittest.main()
