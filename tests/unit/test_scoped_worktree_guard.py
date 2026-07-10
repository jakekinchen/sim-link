from __future__ import annotations

import json
import subprocess
import tempfile
import unittest

from pathlib import Path

from scripts.robot_lab.scoped_worktree_guard import (
    GuardError,
    snapshot_baseline,
    verify_baseline,
)


class ScopedWorktreeGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.baseline_temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self._git("init", "-b", "test-branch")
        self._git("config", "user.email", "robot-lab@example.invalid")
        self._git("config", "user.name", "Robot Lab Test")
        (self.root / "scenesmith/robot_lab").mkdir(parents=True)
        (self.root / "scenesmith/robot_lab/owned.py").write_text("owned = True\n")
        (self.root / "user.txt").write_text("original\n")
        self.scope_path = self.root / "scope.json"
        self.scope_path.write_text(
            json.dumps(
                {
                    "schema_version": "scenesmith.scoped_worktree.v1",
                    "expected_branch": "test-branch",
                    "governed_path_prefixes": ["scenesmith/robot_lab/"],
                    "explicitly_protected_paths": ["user.txt"],
                }
            )
        )
        self._git("add", ".")
        self._git("commit", "-m", "fixture")
        (self.root / "user.txt").write_text("user work\n")
        self.baseline = Path(self.baseline_temporary.name) / "baseline.json"

    def tearDown(self):
        self.baseline_temporary.cleanup()
        self.temporary.cleanup()

    def test_snapshot_and_verify_preserve_unrelated_dirty_file(self):
        snapshot = snapshot_baseline(self.root, self.scope_path, self.baseline)
        result = verify_baseline(self.root, self.scope_path, self.baseline)

        self.assertEqual(set(snapshot["protected_entries"]), {"user.txt"})
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["protected_paths"], 1)

    def test_protected_content_drift_is_rejected(self):
        snapshot_baseline(self.root, self.scope_path, self.baseline)
        (self.root / "user.txt").write_text("goal loop touched user work\n")

        with self.assertRaisesRegex(GuardError, "Protected path content/status drifted"):
            verify_baseline(self.root, self.scope_path, self.baseline)

    def test_governed_path_must_start_and_end_clean(self):
        snapshot_baseline(self.root, self.scope_path, self.baseline)
        (self.root / "scenesmith/robot_lab/owned.py").write_text("owned = False\n")

        with self.assertRaisesRegex(GuardError, "governed paths are dirty"):
            verify_baseline(self.root, self.scope_path, self.baseline)

    def test_new_out_of_scope_dirty_path_is_rejected(self):
        snapshot_baseline(self.root, self.scope_path, self.baseline)
        (self.root / "new-user-file.txt").write_text("new\n")

        with self.assertRaisesRegex(GuardError, "dirty-path set changed"):
            verify_baseline(self.root, self.scope_path, self.baseline)

    def _git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
