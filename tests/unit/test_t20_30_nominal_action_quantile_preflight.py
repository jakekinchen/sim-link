from __future__ import annotations

import copy
import os
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_17_clean_base_preflight import EXPECTED_MODEL_REVISION
from scenesmith.robot_lab.t20_30_nominal_action_quantile_preflight import (
    build_ablation_stats,
    build_manifest,
    build_training_spec,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_30_simulation_training_authority import (
    AUTHORIZED_ACTIONS,
    build_owner_grant,
    verify_owner_grant,
)


class T2030NominalActionQuantilePreflightTests(unittest.TestCase):
    def test_replaces_only_action_q01_q99(self) -> None:
        clean = self._stats(1.0, 3.0, marker=10.0)
        recovery = self._stats(2.0, 5.0, marker=20.0)
        result = build_ablation_stats(clean, recovery)
        expected = copy.deepcopy(recovery)
        expected["action"]["q01"] = [1.0] * 6
        expected["action"]["q99"] = [3.0] * 6
        self.assertEqual(result, expected)

    def test_rejects_nonfinite_and_zero_span(self) -> None:
        clean = self._stats(1.0, 3.0, marker=10.0)
        clean["action"]["q01"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            build_ablation_stats(clean, self._stats(2.0, 5.0, marker=20.0))
        clean = self._stats(3.0, 3.0, marker=10.0)
        with self.assertRaisesRegex(ValueError, "span"):
            build_ablation_stats(clean, self._stats(2.0, 5.0, marker=20.0))

    def test_manifest_rejects_non_stat_drift_and_inode_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            derived = root / "derived"
            for directory in (source, derived):
                (directory / "meta").mkdir(parents=True)
                (directory / "data").mkdir()
                (directory / "data/file.parquet").write_bytes(b"same")
            clean = self._stats(1.0, 3.0, marker=10.0)
            recovery = self._stats(2.0, 5.0, marker=20.0)
            self._write_json(source / "meta/stats.json", recovery)
            self._write_json(
                derived / "meta/stats.json",
                build_ablation_stats(clean, recovery),
            )
            manifest = build_manifest(
                source_root=source,
                derived_root=derived,
                clean_stats=clean,
                recovery_stats=recovery,
                episode_count=10,
                frame_count=2330,
            )
            self.assertEqual(manifest["changed_statistic_paths"], [
                "action.q01",
                "action.q99",
            ])
            (derived / "data/file.parquet").write_bytes(b"drift")
            with self.assertRaisesRegex(ValueError, "byte drifted"):
                build_manifest(
                    source_root=source,
                    derived_root=derived,
                    clean_stats=clean,
                    recovery_stats=recovery,
                    episode_count=10,
                    frame_count=2330,
                )
            (derived / "data/file.parquet").unlink()
            os.link(source / "data/file.parquet", derived / "data/file.parquet")
            with self.assertRaisesRegex(ValueError, "inode alias"):
                build_manifest(
                    source_root=source,
                    derived_root=derived,
                    clean_stats=clean,
                    recovery_stats=recovery,
                    episode_count=10,
                    frame_count=2330,
                )

    def test_training_spec_freezes_campaign_and_false_execution(self) -> None:
        spec = build_training_spec(
            manifest_ref=self._ref("manifest", "1"),
            source_spec_ref=self._ref("source", "2"),
            t20_29_ref=self._ref("counterfactual", "3"),
            model_revision=EXPECTED_MODEL_REVISION,
        )
        verify_training_spec(spec)
        self.assertEqual(spec["campaign"]["optimizer_update_count"], 500)
        self.assertEqual(spec["campaign"]["training_seed"], 20260714)
        self.assertFalse(spec["optimizer_training"])
        drift = copy.deepcopy(spec)
        drift["campaign"]["training_seed"] += 1
        with self.assertRaisesRegex(ValueError, "campaign"):
            verify_training_spec(sign_payload(drift))
        drift = copy.deepcopy(spec)
        drift["optimizer_training"] = True
        with self.assertRaisesRegex(ValueError, "execution|authority"):
            verify_training_spec(sign_payload(drift))

    def test_owner_grant_is_spec_bound_and_simulation_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = root / (
                "configurations/robot_lab/"
                "t20_30_nominal_action_quantile_training_spec.json"
            )
            spec_path.parent.mkdir(parents=True)
            spec = {
                "schema_version": "example.v1",
                "identity_sha256": "a" * 64,
            }
            self._write_json(spec_path, spec)
            grant = build_owner_grant(training_spec=spec, repo_root=root)
            verify_owner_grant(grant, training_spec=spec, repo_root=root)
            self.assertEqual(grant["authorized_actions"], list(AUTHORIZED_ACTIONS))
            self.assertFalse(grant["physical_transfer_authorized"])
            drift = copy.deepcopy(grant)
            drift["authorized_actions"].append("physical_actuation")
            with self.assertRaisesRegex(ValueError, "drifted"):
                verify_owner_grant(
                    sign_payload(drift), training_spec=spec, repo_root=root
                )
    @staticmethod
    def _stats(low: float, high: float, *, marker: float) -> dict:
        return {
            "action": {
                "q01": [low] * 6,
                "q99": [high] * 6,
                "mean": [marker] * 6,
            },
            "observation.state": {"mean": [marker + 1.0] * 6},
        }

    @staticmethod
    def _ref(name: str, digit: str) -> dict:
        return {
            "path": f"configurations/robot_lab/{name}.json",
            "schema_version": f"scenesmith.{name}.v1",
            "identity_sha256": digit * 64,
            "file_sha256": str(int(digit) + 4) * 64,
        }

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        import json

        path.write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
