"""Tests for immutable T18.4 snapshot branch-and-correct mechanics."""

from __future__ import annotations

import copy
import hashlib
import subprocess
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.snapshot_branch_corrections import (
    REPO_ROOT,
    build_correction_event,
    build_snapshot_branch_manifest,
    restore_snapshot,
    validate_correction_event,
    validate_correction_events,
    verify_snapshot_branch_manifest,
)


class SnapshotBranchCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = build_snapshot_branch_manifest()

    def test_manifest_is_deterministic_and_restores_exact_source_sequences(self) -> None:
        verify_snapshot_branch_manifest(self.manifest)
        self.assertEqual(self.manifest["snapshot_count"], 192)
        self.assertEqual(self.manifest["base_branch_count"], 192)
        self.assertEqual(self.manifest["correction_event_count"], 0)
        self.assertFalse(self.manifest["source_correction_evidence_present"])
        snapshot = self.manifest["snapshots"][0]
        restored = restore_snapshot(self.manifest, snapshot["snapshot_id"])
        self.assertEqual(restored["window_id"], snapshot["window_id"])
        self.assertEqual(
            restored["component_record_ids"],
            [frame["component_record_id"] for frame in snapshot["frames"]],
        )

    def test_snapshot_source_and_cross_window_drift_are_rejected(self) -> None:
        source_drift = copy.deepcopy(self.manifest)
        source_drift["source_exact_state_file_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            verify_snapshot_branch_manifest(sign_payload(source_drift))

        altered = copy.deepcopy(self.manifest)
        altered["snapshots"][0]["frames"][0]["frame_id"] = "tampered"
        with self.assertRaisesRegex(ValueError, "Snapshot identity"):
            verify_snapshot_branch_manifest(sign_payload(altered))

        duplicate = copy.deepcopy(self.manifest)
        duplicate["snapshots"].append(copy.deepcopy(duplicate["snapshots"][0]))
        duplicate["snapshot_count"] += 1
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verify_snapshot_branch_manifest(sign_payload(duplicate))

        cross_window = copy.deepcopy(self.manifest)
        cross_window["base_branches"][0]["window_id"] = cross_window["snapshots"][1]["window_id"]
        self._refresh_branch_identity(cross_window["base_branches"][0])
        with self.assertRaisesRegex(ValueError, "source binding"):
            verify_snapshot_branch_manifest(sign_payload(cross_window))

    def test_fixture_event_requires_distinct_immutable_branches_and_stays_out_of_source(self) -> None:
        snapshots = self.manifest["snapshots"]
        event = build_correction_event(
            snapshots,
            failure_snapshot_id=snapshots[0]["snapshot_id"],
            correction_snapshot_id=snapshots[1]["snapshot_id"],
            evidence_class="fixture_only",
        )
        validate_correction_event(event, snapshots=snapshots)
        self.assertEqual(event["evidence_class"], "fixture_only")
        self.assertNotEqual(event["failure_branch"]["branch_id"], event["correction_branch"]["branch_id"])
        with self.assertRaisesRegex(ValueError, "reused event ID"):
            validate_correction_events([event, copy.deepcopy(event)], snapshots=snapshots)

        second_event = build_correction_event(
            snapshots,
            failure_snapshot_id=snapshots[0]["snapshot_id"],
            correction_snapshot_id=snapshots[2]["snapshot_id"],
            evidence_class="fixture_only",
        )
        with self.assertRaisesRegex(ValueError, "reuses an immutable branch"):
            validate_correction_events([event, second_event], snapshots=snapshots)

        with self.assertRaisesRegex(ValueError, "distinct"):
            build_correction_event(
                snapshots,
                failure_snapshot_id=snapshots[0]["snapshot_id"],
                correction_snapshot_id=snapshots[0]["snapshot_id"],
                evidence_class="fixture_only",
            )

        with self.assertRaisesRegex(ValueError, "evidence class"):
            build_correction_event(
                snapshots,
                failure_snapshot_id=snapshots[0]["snapshot_id"],
                correction_snapshot_id=snapshots[1]["snapshot_id"],
                evidence_class="source_bound",
            )

        absent = copy.deepcopy(event)
        absent["failure_branch"]["snapshot_id"] = "0" * 64
        self._refresh_branch_identity(absent["failure_branch"])
        self._refresh_event_identity(absent)
        with self.assertRaisesRegex(ValueError, "absent|binding"):
            validate_correction_event(absent, snapshots=snapshots)

        mixed = copy.deepcopy(self.manifest)
        mixed["correction_events"] = [event]
        mixed["correction_event_count"] = 1
        mixed["correction_event_ids_sha256"] = hashlib.sha256(
            canonical_json_bytes([event["correction_event_id"]])
        ).hexdigest()
        with self.assertRaisesRegex(ValueError, "zero correction events"):
            verify_snapshot_branch_manifest(sign_payload(mixed))

    def test_authority_escalation_raw_rewrite_buffer_mutation_and_rewrite_are_rejected(self) -> None:
        for field in ("optimizer_training", "raw_bytes_rewritten", "buffer_mutated"):
            elevated = copy.deepcopy(self.manifest)
            elevated[field] = True
            with self.assertRaisesRegex(ValueError, "authority flag"):
                verify_snapshot_branch_manifest(sign_payload(elevated))
        result = subprocess.run(
            [
                str(REPO_ROOT / ".mujoco_venv/bin/python"),
                str(REPO_ROOT / "scripts/robot_lab/write_snapshot_branch_corrections.py"),
                "--rewrite",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("immutable", result.stderr)

    @staticmethod
    def _refresh_branch_identity(branch: dict) -> None:
        unsigned = {key: value for key, value in branch.items() if key != "branch_id"}
        branch["branch_id"] = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()

    @staticmethod
    def _refresh_event_identity(event: dict) -> None:
        unsigned = {key: value for key, value in event.items() if key != "correction_event_id"}
        event["correction_event_id"] = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


if __name__ == "__main__":
    unittest.main()
