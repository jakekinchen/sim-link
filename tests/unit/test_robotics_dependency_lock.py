from __future__ import annotations

import hashlib
import json
import unittest

from pathlib import Path

from scenesmith.robot_lab.robotics_dependency_lock import (
    build_robotics_dependency_lock,
    verify_robotics_dependency_lock,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _resign(payload: dict) -> None:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    payload["identity_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class RoboticsDependencyLockTests(unittest.TestCase):
    def test_build_and_verify_current_repo_lock(self):
        payload = build_robotics_dependency_lock(repo_root=REPO_ROOT)

        verify_robotics_dependency_lock(payload, repo_root=REPO_ROOT)

        self.assertEqual(
            payload["dependencies"]["local_lerobot_checkout"]["resolution"],
            "split_runtime_unresolved",
        )
        self.assertEqual(
            payload["dependencies"]["openpi_semantic_reference"]["resolution"],
            "unresolved_remote_reference",
        )
        self.assertEqual(
            payload["dependencies"]["menagerie_robotstudio_so101"]["model_path"],
            "robotstudio_so101",
        )

    def test_verify_rejects_missing_dirty_patch_identity(self):
        payload = build_robotics_dependency_lock(repo_root=REPO_ROOT)
        git_payload = payload["dependencies"]["local_lerobot_checkout"]["git"]
        if not git_payload["is_dirty"]:
            self.skipTest("local lerobot checkout is unexpectedly clean")
        git_payload.pop("tracked_diff_sha256", None)
        git_payload.pop("untracked_tree_sha256", None)
        git_payload.pop("untracked_file_evidence", None)
        _resign(payload)
        with self.assertRaisesRegex(ValueError, "Git tracked diff drifted|Git untracked tree drifted"):
            verify_robotics_dependency_lock(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_license_drift(self):
        payload = build_robotics_dependency_lock(repo_root=REPO_ROOT)
        payload["dependencies"]["openpi_semantic_reference"]["license_id"] = "MIT"
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "Remote reference license drifted"):
            verify_robotics_dependency_lock(payload, repo_root=REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
