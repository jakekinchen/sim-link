"""Tests for source-bound, actor-safe T18.3 exact-state components."""

from __future__ import annotations

import copy
import hashlib
import subprocess
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.exact_state_components import (
    REPO_ROOT,
    build_exact_state_components,
    verify_exact_state_components,
)


class ExactStateComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = build_exact_state_components()

    def test_manifest_is_deterministic_complete_and_actor_safe(self) -> None:
        verify_exact_state_components(self.manifest)
        self.assertEqual(self.manifest["logical_cycle_window_count"], 192)
        self.assertGreater(self.manifest["unique_frame_count"], 0)
        self.assertFalse(self.manifest["privileged_fields_available_to_actor"])
        self.assertTrue(
            all(
                record["reward"]["source_value"]["value"]
                == record["reward"]["exact_state_predicate"]["expected_value"]
                for record in self.manifest["component_records"]
            )
        )

    def test_source_cycle_hash_phase_and_duplicate_frame_drift_are_rejected(self) -> None:
        source_hash_drift = copy.deepcopy(self.manifest)
        source_hash_drift["source_window_index_file_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            verify_exact_state_components(sign_payload(source_hash_drift))

        cycle_drift = copy.deepcopy(self.manifest)
        cycle_drift["logical_cycle_window_ids_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "logical cycle window digest"):
            verify_exact_state_components(sign_payload(cycle_drift))

        phase_drift = copy.deepcopy(self.manifest)
        phase_drift["component_records"][0]["phase"]["task_phase"]["value"] = "tampered"
        with self.assertRaisesRegex(ValueError, "identity drifted"):
            verify_exact_state_components(sign_payload(phase_drift))

        duplicate = copy.deepcopy(self.manifest)
        duplicate["component_records"].append(copy.deepcopy(duplicate["component_records"][0]))
        duplicate["unique_frame_count"] += 1
        duplicate["component_record_ids_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "duplicate frame"):
            verify_exact_state_components(sign_payload(duplicate))

    def test_missing_provenance_privilege_leak_and_authority_escalation_are_rejected(self) -> None:
        missing_provenance = copy.deepcopy(self.manifest)
        del missing_provenance["component_records"][0]["progress"]["source_value"]["provenance"]
        self._refresh_component_identity(missing_provenance, 0)
        with self.assertRaisesRegex(ValueError, "provenance"):
            verify_exact_state_components(sign_payload(missing_provenance))

        leak = copy.deepcopy(self.manifest)
        leak["component_records"][0]["actor_input_schema"].append("reward")
        self._refresh_component_identity(leak, 0)
        with self.assertRaisesRegex(ValueError, "privilege"):
            verify_exact_state_components(sign_payload(leak))

        elevated = copy.deepcopy(self.manifest)
        elevated["optimizer_training"] = True
        with self.assertRaisesRegex(ValueError, "authority flag"):
            verify_exact_state_components(sign_payload(elevated))

        raw_rewrite = copy.deepcopy(self.manifest)
        raw_rewrite["raw_bytes_rewritten"] = True
        with self.assertRaisesRegex(ValueError, "authority flag"):
            verify_exact_state_components(sign_payload(raw_rewrite))

        buffer_mutation = copy.deepcopy(self.manifest)
        buffer_mutation["buffer_mutated"] = True
        with self.assertRaisesRegex(ValueError, "authority flag"):
            verify_exact_state_components(sign_payload(buffer_mutation))

        nonfinite = copy.deepcopy(self.manifest)
        nonfinite["component_records"][0]["progress"]["source_value"]["value"] = float("nan")
        with self.assertRaises(ValueError):
            sign_payload(nonfinite)

    def test_rewrite_is_refused(self) -> None:
        result = subprocess.run(
            [
                str(REPO_ROOT / ".mujoco_venv/bin/python"),
                str(REPO_ROOT / "scripts/robot_lab/write_exact_state_components.py"),
                "--rewrite",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("immutable", result.stderr)

    @staticmethod
    def _refresh_component_identity(manifest: dict, index: int) -> None:
        record = manifest["component_records"][index]
        unsigned = {key: value for key, value in record.items() if key != "component_record_id"}
        record["component_record_id"] = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


if __name__ == "__main__":
    unittest.main()
