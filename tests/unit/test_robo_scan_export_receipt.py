from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from scenesmith.robot_lab.authority_composer import (
    FORBIDDEN_COMPONENT_FIELDS,
    build_composition_request,
    compose_authority,
)
from scenesmith.robot_lab.robo_scan_export_receipt import (
    DEFAULT_LOCK_PATH,
    RoboScanExportError,
    build_twin_candidate,
    validate_robo_scan_export,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "tests/fixtures/robot_lab/robo_scan_export_reference_only"
LOCK_PATH = REPO_ROOT / DEFAULT_LOCK_PATH
SCRIPT_PATH = REPO_ROOT / "scripts/robot_lab/verify_robo_scan_export.py"


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _seal_receipt(payload: dict) -> None:
    payload.pop("receiptSha256", None)
    payload["receiptSha256"] = hashlib.sha256(_canonical(payload)).hexdigest()


class RoboScanExportReceiptTests(unittest.TestCase):
    def _copied_fixture(self, parent: Path) -> Path:
        target = parent / "copied-export"
        shutil.copytree(FIXTURE_ROOT, target)
        # Git text patches carry one final LF; producer canonical JSON does not.
        for relative in ("export-receipt.json", "layered-scene-manifest.json"):
            path = target / relative
            raw = path.read_bytes()
            self.assertTrue(raw.endswith(b"\n"))
            self.assertFalse(raw.endswith(b"\n\n"))
            path.write_bytes(raw[:-1])
        return target

    @staticmethod
    def _write_receipt(root: Path, receipt: dict) -> None:
        _seal_receipt(receipt)
        (root / "export-receipt.json").write_bytes(_canonical(receipt))

    def test_copied_fixture_validates_and_materializes_non_authorizing_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copied_fixture(Path(temporary))
            verified = validate_robo_scan_export(export_root=root, lock_path=LOCK_PATH)
            candidate = build_twin_candidate(export_root=root, lock_path=LOCK_PATH)

        self.assertEqual(verified["receipt"]["exportId"], "reference_scene_export_fixture")
        self.assertEqual(candidate["candidateClass"], "reference_only_visual_context")
        self.assertFalse(candidate["simulationAssetCompilation"]["eligible"])
        self.assertEqual(candidate["coordinateSystem"]["units"], "relative")
        self.assertEqual(candidate["nodeBindings"][2]["uncertainty"], {"state": "not_provided"})
        self.assertEqual(candidate["producer"]["commit"], "72eb02efe7e69981a5afab41a2733cd31ec03d4e")

    def test_runtime_rejects_checkout_root(self) -> None:
        with self.assertRaisesRegex(RoboScanExportError, "outside a live checkout"):
            validate_robo_scan_export(export_root=FIXTURE_ROOT, lock_path=LOCK_PATH)

    def test_asset_extra_and_symlink_mutations_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copied_fixture(Path(temporary))
            (root / "extra.txt").write_text("unbound", encoding="utf-8")
            with self.assertRaisesRegex(RoboScanExportError, "unbound"):
                validate_robo_scan_export(export_root=root, lock_path=LOCK_PATH)
        if hasattr(os, "symlink"):
            with tempfile.TemporaryDirectory() as temporary:
                root = self._copied_fixture(Path(temporary))
                os.symlink(root / "layers/reference-only/fixture.txt", root / "linked.txt")
                with self.assertRaisesRegex(RoboScanExportError, "symlinks"):
                    validate_robo_scan_export(export_root=root, lock_path=LOCK_PATH)

    def test_missing_declared_asset_and_noncanonical_json_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copied_fixture(Path(temporary))
            (root / "layers/reference-only/fixture.txt").unlink()
            with self.assertRaisesRegex(RoboScanExportError, "unbound or missing"):
                validate_robo_scan_export(export_root=root, lock_path=LOCK_PATH)
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copied_fixture(Path(temporary))
            (root / "export-receipt.json").write_bytes((root / "export-receipt.json").read_bytes() + b"\n")
            with self.assertRaisesRegex(RoboScanExportError, "canonical"):
                validate_robo_scan_export(export_root=root, lock_path=LOCK_PATH)

    def test_receipt_authority_privacy_metric_evidence_and_uncertainty_mutations_fail(self) -> None:
        mutations = {
            "disposition": lambda receipt: receipt["disposition"].update({"promotionEligible": True}),
            "privacy": lambda receipt: receipt["privacy"].update({"rawObservationPublished": True}),
            "metric evidence": lambda receipt: receipt.update({"metricEvidence": {"captureCalibrationVerified": True, "evidence": []}}),
            "uncertainty": lambda receipt: receipt["nodeBindings"][0].update({"uncertainty": {"state": "unknown"}}),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = self._copied_fixture(Path(temporary))
                receipt = json.loads((root / "export-receipt.json").read_text(encoding="utf-8"))
                mutate(receipt)
                self._write_receipt(root, receipt)
                with self.assertRaises(RoboScanExportError):
                    validate_robo_scan_export(export_root=root, lock_path=LOCK_PATH)

    def test_identity_provenance_units_transform_and_manifest_mutations_fail(self) -> None:
        cases = {
            "identity": lambda receipt: receipt["scene"].update({"manifestSha256": "0" * 64}),
            "provenance": lambda receipt: receipt["scene"]["provenance"].update({"sourceClassification": "other"}),
            "units": lambda receipt: receipt["scene"]["coordinateSystem"].update({"units": "meters"}),
            "transform": lambda receipt: receipt["nodeBindings"][0]["localTransform"][0].__setitem__(0, 2.0),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = self._copied_fixture(Path(temporary))
                receipt = json.loads((root / "export-receipt.json").read_text(encoding="utf-8"))
                mutate(receipt)
                self._write_receipt(root, receipt)
                with self.assertRaises(RoboScanExportError):
                    validate_robo_scan_export(export_root=root, lock_path=LOCK_PATH)
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copied_fixture(Path(temporary))
            manifest = json.loads((root / "layered-scene-manifest.json").read_text(encoding="utf-8"))
            manifest["manifestSha256"] = "0" * 64
            (root / "layered-scene-manifest.json").write_bytes(_canonical(manifest))
            with self.assertRaisesRegex(RoboScanExportError, "manifest bytes"):
                validate_robo_scan_export(export_root=root, lock_path=LOCK_PATH)

    def test_candidate_has_no_global_authority_surface_and_composer_still_denies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = build_twin_candidate(export_root=self._copied_fixture(Path(temporary)), lock_path=LOCK_PATH)
        serialized = json.dumps(candidate, sort_keys=True)
        for forbidden in FORBIDDEN_COMPONENT_FIELDS:
            self.assertNotIn(f'"{forbidden}"', serialized)
        request = build_composition_request(
            subject_id="pi05_so101_sorting_system",
            scope_id="pi05_so101_authority",
            evaluation_time="2026-07-14T14:50:00-05:00",
            claims=[],
        )
        decision = compose_authority(request)
        self.assertEqual(decision["authority_granted"], [])
        self.assertTrue(all(not item["granted"] for item in decision["global_decisions"]))

    def test_cli_uses_explicit_copied_root_and_never_a_producer_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copied_fixture(Path(temporary))
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "verify", "--export-root", str(root), "--lock", str(LOCK_PATH)],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["exportId"], "reference_scene_export_fixture")


if __name__ == "__main__":
    unittest.main()
