from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.robotics_dependency_lock import (
    OPENPI_REVISION,
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
            "exact_base_plus_tracked_patchset",
        )
        self.assertEqual(
            payload["dependencies"]["lelab_runtime"]["effective_lerobot_runtime"][
                "stack_identity_sha256"
            ],
            payload["dependencies"]["local_lerobot_checkout"]["executable_stack"][
                "identity_sha256"
            ],
        )
        self.assertEqual(
            payload["dependencies"]["openpi_semantic_reference"]["revision"],
            OPENPI_REVISION,
        )
        self.assertEqual(
            payload["dependencies"]["menagerie_robotstudio_so101"]["model_path"],
            "robotstudio_so101",
        )
        self.assertIn(
            "robotstudio_so101/so101.xml",
            {
                entry["path"]
                for entry in payload["dependencies"]["menagerie_robotstudio_so101"][
                    "reference_files"
                ]
            },
        )
        self.assertEqual(
            payload["dependencies"]["menagerie_robotstudio_so101"]["vendored_root"],
            "third_party/mujoco_menagerie/robotstudio_so101",
        )
        self.assertNotIn("repo_root", payload)

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

    def test_verify_rejects_short_remote_revision(self):
        payload = build_robotics_dependency_lock(repo_root=REPO_ROOT)
        payload["dependencies"]["openpi_semantic_reference"]["revision"] = OPENPI_REVISION[:12]
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "40-character commit SHA"):
            verify_robotics_dependency_lock(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_wrong_remote_reference_path(self):
        payload = build_robotics_dependency_lock(repo_root=REPO_ROOT)
        payload["dependencies"]["menagerie_robotstudio_so101"]["reference_files"][2]["path"] = (
            "robotstudio_so101/wrong.xml"
        )
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "Remote reference file pin drifted"):
            verify_robotics_dependency_lock(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_missing_vendored_model_evidence(self):
        payload = build_robotics_dependency_lock(repo_root=REPO_ROOT)
        payload["dependencies"]["menagerie_robotstudio_so101"]["vendored_files"] = []
        _resign(payload)

        with self.assertRaisesRegex(ValueError, "vendored file set drifted"):
            verify_robotics_dependency_lock(payload, repo_root=REPO_ROOT)

    def test_verify_rejects_modified_signed_fields(self):
        payload = build_robotics_dependency_lock(repo_root=REPO_ROOT)
        payload["dependencies"]["openpi_semantic_reference"]["reference_files"][0]["sha256"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "identity hash is invalid"):
            verify_robotics_dependency_lock(payload, repo_root=REPO_ROOT)

    def test_build_is_portable_across_equivalent_roots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_a = Path(temp_dir) / "root-a"
            root_b = Path(temp_dir) / "root-b"
            self._write_portable_fixture(root_a)
            self._write_portable_fixture(root_b)

            payload_a = build_robotics_dependency_lock(repo_root=root_a)
            payload_b = build_robotics_dependency_lock(repo_root=root_b)

            self.assertEqual(payload_a, payload_b)
            verify_robotics_dependency_lock(payload_a, repo_root=root_a)
            verify_robotics_dependency_lock(payload_b, repo_root=root_b)

    def _write_portable_fixture(self, root: Path) -> None:
        files = {
            "scenesmith/robot_lab/spec.py": "spec fixture\n",
            "scenesmith/robot_lab/so101_coordinates.py": "coords fixture\n",
            "scenesmith/robot_lab/mujoco_export.py": "export fixture\n",
            "external/SO-ARM100/LICENSE": "robotstudio license\n",
            "external/SO-ARM100/Simulation/SO101/so101_new_calib.xml": "<mujoco/>\n",
            "external/leLab/LICENSE": "lelab license\n",
            "external/leLab/pyproject.toml": """
[project]
name = "LeLab"
version = "0.1.0"
license = "Apache-2.0"
dependencies = [
  "lerobot[core_scripts,feetech,training] @ git+https://github.com/huggingface/lerobot.git@v0.6.0",
]

[project.urls]
source = "https://github.com/huggingface/leLab.git"
""".strip()
            + "\n",
            "external/leLab/frontend/public/so-101-urdf/urdf/so101_new_calib.urdf": "<robot/>\n",
            "external/lerobot/LICENSE": "lerobot license\n",
            "external/lerobot/pyproject.toml": """
[project]
name = "lerobot"
version = "0.6.1"
license = "Apache-2.0"

[project.urls]
source = "https://github.com/huggingface/lerobot"
""".strip()
            + "\n",
            "external/lerobot/uv.lock": "fixture lock\n",
            "external/lerobot/docs/source/policy_pi05_README.md": "pi05 readme\n",
            "external/lerobot/src/lerobot/policies/pi05/configuration_pi05.py": "cfg = 1\n",
            "external/lerobot/src/lerobot/policies/pi05/modeling_pi05.py": "model = 1\n",
            "external/lerobot/src/lerobot/policies/pi05/processor_pi05.py": "processor = 1\n",
            "external/lerobot/src/lerobot/processor/relative_action_processor.py": "processor = 2\n",
            "external/lerobot/src/lerobot/scripts/lerobot_train.py": "train = 1\n",
            "external/lerobot/tests/policies/pi0_pi05/utils/openpi_parity.py": "parity = 1\n",
        }
        for relative, contents in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")

        shutil.copytree(
            REPO_ROOT / "third_party/mujoco_menagerie/robotstudio_so101",
            root / "third_party/mujoco_menagerie/robotstudio_so101",
        )

        self._init_repo(
            root / "external/leLab",
            remote_url="https://github.com/huggingface/leLab.git",
        )
        self._init_repo(
            root / "external/lerobot",
            remote_url="https://github.com/huggingface/lerobot.git",
        )
        self._init_repo(
            root / "external/SO-ARM100",
            remote_url="https://github.com/TheRobotStudio/SO-ARM100.git",
        )
        lerobot_root = root / "external/lerobot"
        base_revision = self._git(lerobot_root, "rev-parse", "HEAD").strip()
        (lerobot_root / "src/lerobot/policies/pi05/modeling_pi05.py").write_text(
            "model = 2\n", encoding="utf-8"
        )
        patch_path = root / "scripts/robot_lab/patches/fixture.patch"
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(self._git(lerobot_root, "diff", "--binary", "HEAD", "--"), encoding="utf-8")
        runtime_config = {
            "schema_version": "scenesmith.lerobot_runtime.v1",
            "base_revision": base_revision,
            "source_root": "external/lerobot/src",
            "environment_lock": "external/lerobot/uv.lock",
            "patches": ["scripts/robot_lab/patches/fixture.patch"],
            "critical_environment": {},
            "processor_contract": {
                "joint_names": [
                    "shoulder_pan",
                    "shoulder_lift",
                    "elbow_flex",
                    "wrist_flex",
                    "wrist_roll",
                    "gripper",
                ],
                "input_units": "radians",
                "lerobot_units": "degrees",
                "tensor_width": 32,
                "padding_value": 0.0,
            },
            "roles": ["collection", "training", "finalization", "inference", "lelab"],
        }
        config_path = root / "configurations/robot_lab/pi05_lerobot_runtime.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(runtime_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _init_repo(self, path: Path, *, remote_url: str) -> None:
        self._git(path, "init")
        self._git(path, "config", "user.name", "Fixture User")
        self._git(path, "config", "user.email", "fixture@example.com")
        self._git(path, "remote", "add", "origin", remote_url)
        self._git(path, "add", ".")
        self._git(path, "commit", "-m", "fixture")

    def _git(self, path: Path, *args: str) -> str:
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = "2026-01-01T00:00:00+00:00"
        env["GIT_COMMITTER_DATE"] = "2026-01-01T00:00:00+00:00"
        result = subprocess.run(
            ["git", *args],
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        return result.stdout


if __name__ == "__main__":
    unittest.main()
