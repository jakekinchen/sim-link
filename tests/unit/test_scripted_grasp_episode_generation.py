"""Focused evidence and fail-closed tests for T17.5b scripted episodes."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.experience_compiler import verify_compilation
from scenesmith.robot_lab.experience_window_index import (
    compile_window_index,
    verify_window_index,
    write_window_index,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    EPISODE_SPECS,
    _build_store_manifest,
    _resolve_store_path,
    _validate_episode_spec,
    _write_episode_payload,
    compile_episode_store,
    generate_episode_payload,
    verify_episode_store,
)


class ScriptedGraspEpisodeGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seed_zero_payload = generate_episode_payload(dict(EPISODE_SPECS[0]))

    def test_seed_zero_records_complete_unassisted_evidence(self) -> None:
        payload = self.seed_zero_payload
        self.assertEqual(len(payload["frames"]), 244)
        self.assertTrue(payload["outcome"]["strict_success"])
        self.assertEqual(len(payload["rendered_keyframes"]), 5)
        self.assertEqual(
            payload["outcome"]["strict_v2_valid_frame_counts"],
            {
                "grasp_hold": 8,
                "unassisted_lift": 24,
                "unsupported_lift_hold": 12,
                "lower": 24,
                "release_settle": 0,
                "retreat": 0,
            },
        )
        self.assertEqual(
            payload["outcome"]["recording_stable_hold"]["strict_v2_valid_frame_count"],
            64,
        )
        first_actions = payload["frames"][0]["actions"]
        self.assertEqual(first_actions["requested"]["state"], "observed")
        for variant in ("proposed", "projected", "sent", "measured"):
            self.assertEqual(first_actions[variant]["state"], "derived")
            self.assertTrue(first_actions[variant]["provenance"]["derivation"])

    def test_store_verifier_rejects_tampered_path_hash_and_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scenesmith-t17-5b-test-") as directory:
            store = Path(directory)
            entry = _write_episode_payload(self.seed_zero_payload, store)
            failures = [
                {
                    "seed": spec["seed"],
                    "spec": spec,
                    "terminal_outcome": "runtime_failure",
                    "strict_success": False,
                    "error": "synthetic test accounting only",
                }
                for spec in EPISODE_SPECS[1:]
            ]
            manifest = _build_store_manifest([entry], failures)
            verify_episode_store(manifest, store)
            with tempfile.TemporaryDirectory(prefix="scenesmith-t17-5b-compile-") as output:
                written = compile_episode_store(
                    manifest,
                    store,
                    Path(output),
                    manifest_file_sha256="a" * 64,
                )
                verify_compilation(Path(output))
                self.assertGreater(written["manifest"]["eligible_frame_count"], 0)
                self.assertGreater(written["manifest"]["segment_count"], 0)
                window = Path(output) / "window"
                write_window_index(compile_window_index(Path(output)), window)
                verify_window_index(window, Path(output))
                self.assertGreater(
                    compile_window_index(Path(output))["manifest"]["window_count_by_horizon"]["50"],
                    0,
                )

            escaped = copy.deepcopy(manifest)
            escaped["episodes"][0]["relative_path"] = "../escaped.json"
            with self.assertRaisesRegex(ValueError, "escapes"):
                verify_episode_store(sign_payload(escaped), store)

            authority = copy.deepcopy(manifest)
            authority["training_eligible"] = True
            with self.assertRaisesRegex(ValueError, "authority flag"):
                verify_episode_store(sign_payload(authority), store)

    def test_only_fixed_seed_specs_and_in_root_paths_are_valid(self) -> None:
        _validate_episode_spec(dict(EPISODE_SPECS[0]))
        altered = dict(EPISODE_SPECS[0])
        altered["planar_offset_m"] = [0.001, 0.0]
        with self.assertRaisesRegex(ValueError, "fixed seeds"):
            _validate_episode_spec(altered)
        with tempfile.TemporaryDirectory(prefix="scenesmith-t17-5b-root-") as directory:
            with self.assertRaisesRegex(ValueError, "escapes"):
                _resolve_store_path(Path(directory), "../escape.json")


if __name__ == "__main__":
    unittest.main()
