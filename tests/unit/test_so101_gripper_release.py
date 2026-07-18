"""Regression checks for the printer-ready SO-101 compliant-gripper release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release/SO101_R1_AD5X_compliant_gripper"
PACKAGE = ROOT / "release/SO101_R1_AD5X_Compliant_Gripper_Print_Package.zip"
CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SO101GripperReleaseTests(unittest.TestCase):
    def test_final_validation_is_two_material_jobs_and_three_components(self) -> None:
        validation = json.loads((RELEASE / "validation/PRINT_VALIDATION.json").read_text())
        self.assertEqual([component["triangle_count"] for component in validation["components"]], [39690, 18714, 3480])
        self.assertEqual([plate["object_count"] for plate in validation["plates"]], [2, 1])
        self.assertEqual([plate["material"] for plate in validation["plates"]], ["PLA or PLA+", "TPU 95A"])
        self.assertTrue(validation["gates"]["all_source_components_finite_nondegenerate_watertight_manifold"])
        self.assertTrue(validation["gates"]["pla_and_tpu_separated_into_exactly_two_jobs"])
        self.assertFalse(validation["gates"]["physical_fit_verified"])
        self.assertFalse(validation["gates"]["robot_calibration_updated"])
        for plate in validation["plates"]:
            for obj in plate["objects"]:
                minimum = obj["plate_bounds_mm"]["min"]
                maximum = obj["plate_bounds_mm"]["max"]
                self.assertTrue(all(low <= high for low, high in zip(minimum, maximum)))
                self.assertEqual(minimum[2], 0.0)

    def test_standard_3mf_files_are_millimetre_geometry_only_projects(self) -> None:
        paths = sorted((RELEASE / "plates").glob("*.3mf"))
        self.assertEqual(len(paths), 2)
        counts = []
        for path in paths:
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(sorted(archive.namelist()), ["3D/3dmodel.model", "[Content_Types].xml", "_rels/.rels"])
                model = ET.fromstring(archive.read("3D/3dmodel.model"))
            self.assertEqual(model.attrib["unit"], "millimeter")
            objects = model.findall(f".//{{{CORE_NS}}}object")
            items = model.findall(f".//{{{CORE_NS}}}build/{{{CORE_NS}}}item")
            self.assertEqual(len(objects), len(items))
            counts.append(len(objects))
            for item in items:
                transform = [float(value) for value in item.attrib["transform"].split()]
                self.assertEqual(transform[:9], [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])
                self.assertEqual(transform[11], 0.0)
        self.assertEqual(counts, [2, 1])

    def test_manifest_hashes_and_zip_contents_verify(self) -> None:
        manifest = json.loads((RELEASE / "MANIFEST.json").read_text())
        for entry in manifest["files"]:
            path = RELEASE / entry["file"]
            self.assertTrue(path.is_file(), entry["file"])
            self.assertEqual(path.stat().st_size, entry["size_bytes"])
            self.assertEqual(sha256(path), entry["sha256"])
        with zipfile.ZipFile(PACKAGE) as archive:
            self.assertIsNone(archive.testzip())
            names = set(archive.namelist())
            for entry in manifest["files"]:
                self.assertIn(f"SO101_R1_AD5X_compliant_gripper/{entry['file']}", names)
            embedded = json.loads(archive.read("SO101_R1_AD5X_compliant_gripper/MANIFEST.json"))
            self.assertEqual(embedded, manifest)


if __name__ == "__main__":
    unittest.main()
