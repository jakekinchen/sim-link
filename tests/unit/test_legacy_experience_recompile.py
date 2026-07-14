"""Tests for the bounded, no-migration T17.6 legacy evidence audit."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    sign_payload,
)
from scenesmith.robot_lab.experience_compiler import compile_projections, verify_compilation
from scenesmith.robot_lab.legacy_experience_recompile import (
    CANDIDATE_SPECS,
    LegacyCandidateSpec,
    REPO_ROOT,
    build_legacy_inventory_manifest,
    compile_legacy_inventory,
    verify_legacy_inventory_manifest,
)


class LegacyExperienceRecompileTests(unittest.TestCase):
    def test_current_canary_is_reasoned_quarantine_and_deterministic(self) -> None:
        first = build_legacy_inventory_manifest()
        second = build_legacy_inventory_manifest()
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))
        verify_legacy_inventory_manifest(first)
        self.assertEqual(first["configured_candidate_count"], 3)
        self.assertEqual(first["accepted_candidate_count"], 0)
        self.assertEqual(first["quarantined_candidate_count"], 3)
        by_id = {candidate["candidate_id"]: candidate for candidate in first["candidates"]}
        self.assertEqual(by_id["m10_observation_frames"]["record_count"], 3219)
        self.assertIn(
            "missing_current_action_variant_lineage",
            by_id["m10_observation_frames"]["quarantine_reason_codes"],
        )
        self.assertEqual(by_id["m10_training_dataset_metadata"]["source_facts"]["declared_episode_count"], 12)

    def test_empty_compiler_view_is_source_bound_and_byte_deterministic(self) -> None:
        manifest = build_legacy_inventory_manifest()
        with tempfile.TemporaryDirectory(
            prefix="scenesmith-legacy-", dir=REPO_ROOT
        ) as first_dir:
            first_root = Path(first_dir)
            manifest_path = first_root / "inventory.json"
            dump_canonical_json(manifest_path, manifest)
            first = compile_legacy_inventory(
                manifest,
                first_root / "compile",
                inventory_manifest_sha256=_sha256(manifest_path),
            )
            verify_compilation(first_root / "compile")
            self.assertEqual(first["manifest"]["frame_count"], 0)
            self.assertEqual(first["manifest"]["segment_count"], 0)
            self.assertEqual(first["manifest"]["quarantine_count"], 0)
            self.assertIn("source_legacy_inventory_manifest_sha256", first["manifest"])

    def test_root_escape_duplicates_and_malformed_records_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="scenesmith-legacy-", dir=REPO_ROOT
        ) as directory:
            root = Path(directory)
            self._write_candidate_files(root, malformed_observation=True)
            with self.assertRaisesRegex(ValueError, "Malformed legacy JSONL"):
                build_legacy_inventory_manifest(root)

            self._write_candidate_files(root, malformed_observation=False)
            duplicate = CANDIDATE_SPECS + (CANDIDATE_SPECS[0],)
            with self.assertRaisesRegex(ValueError, "identifiers must be unique"):
                build_legacy_inventory_manifest(root, specs=duplicate)
            escaped = (
                LegacyCandidateSpec("escaped", Path("../escape.jsonl"), "legacy_jsonl_frame_stream"),
            )
            with self.assertRaisesRegex(ValueError, "escapes"):
                build_legacy_inventory_manifest(root, specs=escaped)

    def test_source_hash_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="scenesmith-legacy-", dir=REPO_ROOT
        ) as directory:
            root = Path(directory)
            self._write_candidate_files(root)
            manifest = build_legacy_inventory_manifest(root)
            observation = root / CANDIDATE_SPECS[0].relative_path
            observation.write_text(observation.read_text() + "\n")
            with self.assertRaisesRegex(ValueError, "drifted"):
                verify_legacy_inventory_manifest(manifest, root)

    def test_authority_escalation_and_raw_rewrite_are_rejected(self) -> None:
        manifest = build_legacy_inventory_manifest()
        elevated = dict(manifest)
        elevated["training_eligible"] = True
        elevated = sign_payload(elevated)
        with self.assertRaisesRegex(ValueError, "authority flag"):
            verify_legacy_inventory_manifest(elevated)
        command = [
            str(REPO_ROOT / ".mujoco_venv/bin/python"),
            str(REPO_ROOT / "scripts/robot_lab/write_legacy_experience_recompile.py"),
            "--rewrite",
        ]
        result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("immutable", result.stderr)

    def test_empty_projection_requires_a_bound_legacy_inventory_hash(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one source projection"):
            compile_projections(
                [],
                source_experience_identity="a" * 64,
                source_normalization_identity="b" * 64,
            )
        with self.assertRaisesRegex(ValueError, "legacy-inventory manifest hash"):
            compile_projections(
                [],
                source_experience_identity="a" * 64,
                source_normalization_identity="b" * 64,
                source_legacy_inventory_manifest_sha256="not-a-hash",
            )

    @staticmethod
    def _write_candidate_files(root: Path, *, malformed_observation: bool = False) -> None:
        observation = root / CANDIDATE_SPECS[0].relative_path
        sidecar = root / CANDIDATE_SPECS[1].relative_path
        metadata = root / CANDIDATE_SPECS[2].relative_path
        for path in (observation, sidecar, metadata):
            path.parent.mkdir(parents=True, exist_ok=True)
        observation.write_text("{bad json}\n" if malformed_observation else json.dumps({"time_s": 0.0, "executed_action": [0.0]}) + "\n")
        sidecar.write_text(json.dumps({"time_s": 0.0, "observation_images": {"top": "/tmp/top.png"}}) + "\n")
        metadata.write_text(
            json.dumps(
                {
                    "total_episodes": 12,
                    "total_frames": 11316,
                    "features": {"action": {"dtype": "float32", "shape": [6]}},
                }
            )
        )


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
