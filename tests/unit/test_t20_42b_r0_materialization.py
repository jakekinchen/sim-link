from __future__ import annotations

import copy
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    validate_bounded_episode_spec,
)
from scenesmith.robot_lab.t20_42a_r0_generation_authority import (
    DECISION_PATH,
    OWNER_GRANT_PATH,
    PERMIT_PATH,
    REQUEST_PATH,
    RUNTIME_PREFLIGHT_PATH,
    fixture_runtime_snapshot,
    load_verified_sources,
)
from scenesmith.robot_lab.t20_42b_r0_materialization import (
    AUTHORITY_PATHS,
    build_materialization_bundle,
    verify_materialization_bundle,
    write_authority_bundle,
)


class T2042bR0MaterializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_verified_sources()
        cls.commit = "c" * 40
        cls.runtime = fixture_runtime_snapshot(source_commit=cls.commit)
        cls.bundle = build_materialization_bundle(
            sources=cls.sources,
            required_source_commit=cls.commit,
            valid_from="2026-07-16T12:35:56-05:00",
            valid_until="2026-07-16T20:35:56-05:00",
            runtime_snapshot=cls.runtime,
        )

    def test_bundle_is_exact_five_artifact_one_use_boundary(self) -> None:
        verify_materialization_bundle(self.bundle, sources=self.sources)
        self.assertEqual(
            list(self.bundle), [path.as_posix() for path in AUTHORITY_PATHS]
        )
        self.assertEqual(
            self.bundle[DECISION_PATH.as_posix()]["authority_granted"],
            ["simulation_training_ready"],
        )
        permit = self.bundle[PERMIT_PATH.as_posix()]
        self.assertEqual(permit["authorized_attempt_count"], 1)
        self.assertEqual(len(permit["training_candidate_ids"]), 119)
        self.assertEqual(len(permit["fresh_held_out_candidate_ids"]), 9)
        self.assertFalse(permit["retry_authorized"])

    def test_bundle_rejects_resigned_owner_request_and_permit_drift(self) -> None:
        for path, field, value in (
            (OWNER_GRANT_PATH, "authorized_attempt_count", 2),
            (REQUEST_PATH, "composition_mode", "fixture"),
            (PERMIT_PATH, "retry_authorized", True),
        ):
            with self.subTest(path=path):
                drift = copy.deepcopy(self.bundle)
                drift[path.as_posix()][field] = value
                drift[path.as_posix()] = sign_payload(drift[path.as_posix()])
                with self.assertRaises(ValueError):
                    verify_materialization_bundle(drift, sources=self.sources)

    def test_exclusive_writer_persists_exact_bundle_and_rejects_repeat(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            written = write_authority_bundle(
                self.bundle, sources=self.sources, repo_root=root
            )
            self.assertEqual(written, self.bundle)
            for path in AUTHORITY_PATHS:
                self.assertTrue((root / path).is_file())
            with self.assertRaises(FileExistsError):
                write_authority_bundle(
                    self.bundle, sources=self.sources, repo_root=root
                )

    def test_preexisting_later_target_prevents_any_partial_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / RUNTIME_PREFLIGHT_PATH
            target.parent.mkdir(parents=True)
            target.write_text("occupied", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_authority_bundle(
                    self.bundle, sources=self.sources, repo_root=root
                )
            self.assertFalse((root / OWNER_GRANT_PATH).exists())

    def test_symlinked_authority_parent_fails_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            elsewhere = root / "elsewhere"
            elsewhere.mkdir()
            (root / "configurations").symlink_to(elsewhere, target_is_directory=True)
            with self.assertRaises(ValueError):
                write_authority_bundle(
                    self.bundle, sources=self.sources, repo_root=root
                )
            self.assertEqual(list(elsewhere.iterdir()), [])

    def test_bounded_source_entrypoint_validator_does_not_widen_envelope(self) -> None:
        valid = {
            "seed": 42000,
            "planar_offset_m": [0.001, -0.001],
            "yaw_offset_rad": 0.03,
        }
        validate_bounded_episode_spec(valid)
        for mutation in (
            {**valid, "yaw_offset_rad": 0.0300001},
            {**valid, "planar_offset_m": [0.0011, 0.0]},
            {**valid, "physics": "changed"},
            {**valid, "seed": True},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    validate_bounded_episode_spec(mutation)


if __name__ == "__main__":
    unittest.main()
