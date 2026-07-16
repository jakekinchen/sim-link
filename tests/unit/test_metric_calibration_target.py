from __future__ import annotations

import copy
import io
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload

try:
    from pypdf import PdfReader

    from scenesmith.robot_lab.metric_calibration_target import (
        BOARD_HEIGHT_MM,
        BOARD_WIDTH_MM,
        INNER_CORNERS,
        PDF_PATH,
        SPEC_PATH,
        SQUARE_SIZE_MM,
        build_metric_checkerboard_pdf_bytes,
        build_metric_checkerboard_spec,
        verify_metric_checkerboard_artifacts,
    )

    PDF_DEPENDENCIES_AVAILABLE = True
except ModuleNotFoundError:
    PDF_DEPENDENCIES_AVAILABLE = False


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(
    PDF_DEPENDENCIES_AVAILABLE,
    "metric target tests require the bundled PDF runtime",
)
class MetricCalibrationTargetTests(unittest.TestCase):
    def test_pdf_generation_is_deterministic_and_exact_letter_size(self) -> None:
        left = build_metric_checkerboard_pdf_bytes()
        right = build_metric_checkerboard_pdf_bytes()
        self.assertEqual(left, right)
        reader = PdfReader(io.BytesIO(left))
        self.assertEqual(len(reader.pages), 1)
        self.assertEqual(float(reader.pages[0].mediabox.width), 612.0)
        self.assertEqual(float(reader.pages[0].mediabox.height), 792.0)

    def test_geometry_is_exact_and_print_scale_is_unambiguous(self) -> None:
        spec = build_metric_checkerboard_spec(repo_root=ROOT)
        self.assertEqual(INNER_CORNERS, (9, 6))
        self.assertEqual(SQUARE_SIZE_MM, 20.0)
        self.assertEqual(BOARD_WIDTH_MM, 200.0)
        self.assertEqual(BOARD_HEIGHT_MM, 140.0)
        self.assertEqual(spec["print_contract"]["scale_percent"], 100)
        self.assertFalse(spec["print_contract"]["fit_to_page"])
        self.assertEqual(spec["checkerboard"]["top_left_square"], "black")

    def test_checked_in_artifacts_verify_from_generator(self) -> None:
        spec = load_strict_json(ROOT / SPEC_PATH)
        verify_metric_checkerboard_artifacts(spec, repo_root=ROOT)
        self.assertTrue((ROOT / PDF_PATH).is_file())

    def test_resigned_geometry_drift_is_rejected(self) -> None:
        spec = build_metric_checkerboard_spec(repo_root=ROOT)
        forged = copy.deepcopy(spec)
        forged["checkerboard"]["square_size_mm"] = 19.9
        forged = sign_payload(
            {key: value for key, value in forged.items() if key != "identity_sha256"}
        )
        with self.assertRaisesRegex(ValueError, "spec drifted"):
            verify_metric_checkerboard_artifacts(forged, repo_root=ROOT)


if __name__ == "__main__":
    unittest.main()
