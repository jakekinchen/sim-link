from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest

from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "reconstruction-kit/scripts/regenerate_r0.py"
SPEC = importlib.util.spec_from_file_location(
    "reconstruction_regenerate_r0", SCRIPT_PATH
)
assert SPEC and SPEC.loader
r0 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r0)


class RegenerateR0ContractTest(unittest.TestCase):
    def test_exact_legacy_boundary_is_immutable(self) -> None:
        self.assertEqual(r0.EXPECTED["new_training_strict_success_count"], 119)
        self.assertEqual(r0.EXPECTED["fresh_held_out_strict_success_count"], 9)
        self.assertEqual(r0.EXPECTED["training_episode_count"], 129)
        self.assertEqual(r0.EXPECTED["training_frame_count"], 31366)
        self.assertEqual(r0.EXPECTED["window_count"], 59904)
        self.assertEqual(
            r0.EXPECTED["mixture_identity_sha256"],
            "37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df",
        )
        self.assertEqual(
            r0.EXPECTED["statistics_identity_sha256"],
            "02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae",
        )

    def test_non_live_template_preserves_labels_and_tier_boundary(self) -> None:
        template = r0._verify_template()
        self.assertTrue(template["non_live_template"])
        self.assertFalse(template["live_authority"])
        self.assertTrue(template["historical_authority_is_inert_evidence_only"])
        self.assertEqual(
            template["evidence_labels_preserved"], ["fixture", "simulation", "replay"]
        )
        self.assertEqual(
            template["dataset_tiers"],
            {
                "compatibility": "exact_existing_full_r0_recreation",
                "future_fast_rl": "light_state_only_parquet_follow_on_not_part_of_w2",
            },
        )
        self.assertEqual(
            template["full_audiovisual_lerobot_dataset_role"], "vla_and_demo_only"
        )
        self.assertEqual(
            template["short_60_frame_success_terminated_state_tasks"],
            "fork_birth_follow_on_not_part_of_w2",
        )

    def test_local_epoch_is_fresh_signed_and_non_authorizing(self) -> None:
        template = r0._verify_template()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template_path = root / "docs/reconstruction/R0_LOCAL_EPOCH_TEMPLATE.json"
            template_path.parent.mkdir(parents=True)
            template_path.write_text(json.dumps(template), encoding="utf-8")
            manifest = r0._sign(
                {
                    "schema_version": "test.source_manifest.v1",
                    "source_commit": "a" * 40,
                }
            )
            manifest_path = root / "docs/reconstruction/SOURCE_MANIFEST.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with (
                mock.patch.object(r0, "REPO_ROOT", root),
                mock.patch.object(r0, "TEMPLATE_PATH", template_path),
                mock.patch.object(r0, "SOURCE_MANIFEST_PATH", manifest_path),
            ):
                relative, epoch = r0._materialize_epoch(
                    template,
                    epoch_id="1" * 32,
                    created_at="2026-07-16T23:00:00-05:00",
                )
            self.assertEqual(epoch["identity_sha256"], r0._payload_identity(epoch))
            self.assertEqual(relative.name, "LOCAL_EPOCH.json")
            self.assertFalse(epoch["current_live_authority"])
            self.assertFalse(epoch["historical_permit_reused_as_authority"])
            self.assertFalse(epoch["training_authorized"])
            self.assertFalse(epoch["hardware_accessed"])
            self.assertFalse(epoch["network_accessed"])
            self.assertFalse(epoch["external_compute_started"])
            self.assertFalse(epoch["brev_compute_started"])

    def test_every_gate_mismatch_fails_closed_as_new_dataset(self) -> None:
        self.assertEqual(r0._mismatches(dict(r0.EXPECTED)), {})
        for key in (
            "new_training_strict_success_count",
            "fresh_held_out_strict_success_count",
            "training_episode_count",
            "training_frame_count",
            "window_count",
            "mixture_identity_sha256",
            "statistics_identity_sha256",
        ):
            with self.subTest(key=key):
                observed = dict(r0.EXPECTED)
                observed[key] = "drift"
                mismatch = r0._mismatches(observed)
                self.assertEqual(set(mismatch), {key})
                error = r0.R0MismatchError(mismatch)
                receipt = r0._failure_receipt(
                    started_at="2026-07-16T23:00:00-05:00",
                    elapsed_seconds=1.0,
                    stage="test",
                    error=error,
                    epoch_path=None,
                    epoch=None,
                )
                self.assertEqual(receipt["status"], "new_dataset_not_recreation")
                self.assertEqual(receipt["message"], "new dataset, not a recreation")
                self.assertIn(key, receipt["mismatches"])
                self.assertTrue(
                    all(receipt[field] is False for field in r0.FALSE_AUTHORITY_FIELDS)
                )

    def test_parallel_metadata_key_order_is_normalized_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "meta/stats.json"
            path.parent.mkdir(parents=True)
            payload = {
                key: {"count": [index]}
                for index, key in enumerate(reversed(r0.LEGACY_META_STATS_KEY_ORDER))
            }
            path.write_text(json.dumps(payload, indent=4), encoding="utf-8")
            ordered = {key: payload[key] for key in r0.LEGACY_META_STATS_KEY_ORDER}
            expected_bytes = json.dumps(ordered, indent=4, allow_nan=False).encode()
            expected_hash = hashlib.sha256(expected_bytes).hexdigest()
            with mock.patch.object(
                r0,
                "EXPECTED_DATASET_META_STATS_FILE_SHA256",
                expected_hash,
            ):
                r0._normalize_legacy_meta_stats(root)
            self.assertEqual(path.read_bytes(), expected_bytes)
            self.assertEqual(
                list(json.loads(path.read_text(encoding="utf-8"))),
                list(r0.LEGACY_META_STATS_KEY_ORDER),
            )

    def test_run_receipt_is_handoff_evidence_and_future_rl_is_deferred(self) -> None:
        tiers = r0._dataset_tiers()
        self.assertTrue(tiers["compatibility"]["w2_hard_gate"])
        self.assertEqual(
            tiers["future_fast_rl"]["status"],
            "deferred_fork_birth_follow_on_not_part_of_w2",
        )
        self.assertFalse(tiers["future_fast_rl"]["may_alter_w2_gate"])
        self.assertEqual(
            tiers["full_audiovisual_lerobot_dataset"]["role"], "VLA/demo-only"
        )

    def test_historical_permit_file_is_never_loaded_as_authority(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("t20_42a_r0_generation_permit.json", source)
        self.assertIn("inert_compatibility_projection_only", source)


if __name__ == "__main__":
    unittest.main()
