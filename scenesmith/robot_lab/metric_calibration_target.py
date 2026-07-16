"""Deterministic printable metric checkerboard for T19.2 camera calibration."""

from __future__ import annotations

import hashlib
import io

from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload


SCHEMA_VERSION = "scenesmith.metric_calibration_target.v1"
PDF_PATH = Path("output/pdf/pi05_t19_2_metric_checkerboard.pdf")
SPEC_PATH = Path("configurations/robot_lab/t19_2_metric_checkerboard_spec.json")
PAGE_WIDTH_PT, PAGE_HEIGHT_PT = letter
COLUMNS = 10
ROWS = 7
INNER_CORNERS = (9, 6)
SQUARE_SIZE_MM = 20.0
BOARD_WIDTH_MM = COLUMNS * SQUARE_SIZE_MM
BOARD_HEIGHT_MM = ROWS * SQUARE_SIZE_MM
BOARD_ORIGIN_MM = ((PAGE_WIDTH_PT / mm - BOARD_WIDTH_MM) / 2.0, 82.0)
AUTHORITY_NOT_GRANTED = (
    "target_printed_at_scale",
    "target_physically_observed",
    "camera_access",
    "serial_access",
    "register_write",
    "torque_change",
    "motion",
    "calibration_update",
    "twin_update",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "policy_actuation",
    "external_compute",
    "brev_compute",
)


def build_metric_checkerboard_pdf_bytes() -> bytes:
    stream = io.BytesIO()
    pdf = canvas.Canvas(
        stream,
        pagesize=letter,
        invariant=1,
        pageCompression=0,
    )
    pdf.setTitle("SceneSmith T19.2 Metric Calibration Checkerboard")
    pdf.setAuthor("SceneSmith")
    pdf.setSubject("9 x 6 inner-corner checkerboard, 20.00 mm squares")
    pdf.setCreator("SceneSmith deterministic target generator")
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(
        PAGE_WIDTH_PT / 2,
        PAGE_HEIGHT_PT - 20 * mm,
        "SceneSmith T19.2 Metric Calibration Target",
    )
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(
        PAGE_WIDTH_PT / 2,
        PAGE_HEIGHT_PT - 27 * mm,
        "Print at 100% / Actual Size. Disable Fit, Shrink, and Scale.",
    )
    pdf.drawCentredString(
        PAGE_WIDTH_PT / 2,
        PAGE_HEIGHT_PT - 33 * mm,
        "Checkerboard: 9 x 6 inner corners - 20.00 mm squares - active area 200.00 x 140.00 mm",
    )

    origin_x = BOARD_ORIGIN_MM[0] * mm
    origin_y = BOARD_ORIGIN_MM[1] * mm
    square = SQUARE_SIZE_MM * mm
    pdf.setFillColorRGB(0, 0, 0)
    for row_from_top in range(ROWS):
        for column in range(COLUMNS):
            if (row_from_top + column) % 2 == 0:
                y = origin_y + (ROWS - 1 - row_from_top) * square
                pdf.rect(
                    origin_x + column * square,
                    y,
                    square,
                    square,
                    stroke=0,
                    fill=1,
                )

    pdf.setStrokeColorRGB(0, 0, 0)
    pdf.setLineWidth(0.25)
    pdf.rect(
        origin_x,
        origin_y,
        BOARD_WIDTH_MM * mm,
        BOARD_HEIGHT_MM * mm,
        stroke=1,
        fill=0,
    )
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(origin_x, origin_y + BOARD_HEIGHT_MM * mm + 3 * mm, "TOP - BLACK ORIGIN SQUARE")
    pdf.drawString(origin_x, origin_y - 5 * mm, "LEFT / ORIGIN SIDE")

    bar_x = (PAGE_WIDTH_PT - 100 * mm) / 2
    bar_y = 48 * mm
    pdf.setLineWidth(0.5)
    pdf.rect(bar_x, bar_y, 100 * mm, 4 * mm, stroke=1, fill=0)
    for tick_mm in range(0, 101, 10):
        height = 4 * mm if tick_mm in {0, 50, 100} else 2 * mm
        pdf.line(bar_x + tick_mm * mm, bar_y, bar_x + tick_mm * mm, bar_y + height)
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(PAGE_WIDTH_PT / 2, bar_y - 5 * mm, "Verification bar: 100.00 mm")
    pdf.drawCentredString(PAGE_WIDTH_PT / 2, 30 * mm, "Measure the bar and five adjacent squares: both must equal 100.00 mm.")
    pdf.drawCentredString(PAGE_WIDTH_PT / 2, 25 * mm, "Reject the print if either differs by more than 0.20 mm.")
    pdf.drawCentredString(PAGE_WIDTH_PT / 2, 18 * mm, "Target ID: pi05_t19_2_metric_checkerboard_v1")
    pdf.showPage()
    pdf.save()
    return stream.getvalue()


def build_metric_checkerboard_spec(*, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    module_path = Path(__file__).resolve()
    module_relative = module_path.relative_to(root)
    pdf_bytes = build_metric_checkerboard_pdf_bytes()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    page = reader.pages[0]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "target_id": "pi05_t19_2_metric_checkerboard_v1",
            "target_kind": "planar_checkerboard",
            "page": {
                "media": "US Letter portrait",
                "width_points": float(page.mediabox.width),
                "height_points": float(page.mediabox.height),
                "width_mm": PAGE_WIDTH_PT / mm,
                "height_mm": PAGE_HEIGHT_PT / mm,
                "page_count": len(reader.pages),
            },
            "checkerboard": {
                "columns": COLUMNS,
                "rows": ROWS,
                "inner_corners_columns": INNER_CORNERS[0],
                "inner_corners_rows": INNER_CORNERS[1],
                "square_size_mm": SQUARE_SIZE_MM,
                "active_width_mm": BOARD_WIDTH_MM,
                "active_height_mm": BOARD_HEIGHT_MM,
                "board_origin_from_page_bottom_left_mm": list(BOARD_ORIGIN_MM),
                "top_left_square": "black",
                "corner_coordinate_convention": "origin_at_top_left_inner_corner_x_right_y_down",
            },
            "print_contract": {
                "scale_percent": 100,
                "printer_mode": "actual_size",
                "fit_to_page": False,
                "shrink_oversized_pages": False,
                "verification_bar_mm": 100.0,
                "maximum_scale_error_mm": 0.2,
            },
            "pdf": {
                "path": PDF_PATH.as_posix(),
                "sha256": hashlib.sha256(pdf_bytes).hexdigest(),
                "size_bytes": len(pdf_bytes),
                "vector_geometry": True,
            },
            "generator": {
                "path": module_relative.as_posix(),
                "sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
                "size_bytes": module_path.stat().st_size,
                "deterministic_invariant_pdf": True,
            },
            "local_capabilities": ["printable_metric_calibration_target_artifact_valid"],
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "authority_not_granted": list(AUTHORITY_NOT_GRANTED),
        }
    )


def verify_metric_checkerboard_artifacts(
    spec: dict[str, Any],
    *,
    repo_root: Path,
) -> None:
    verify_signed_payload(spec, label="metric calibration target spec")
    root = Path(repo_root).resolve()
    pdf_path = (root / PDF_PATH).resolve()
    if not pdf_path.is_relative_to(root) or not pdf_path.is_file():
        raise ValueError("Metric calibration target PDF is missing or escaped")
    expected_bytes = build_metric_checkerboard_pdf_bytes()
    if pdf_path.read_bytes() != expected_bytes:
        raise ValueError("Metric calibration target PDF bytes drifted")
    expected = build_metric_checkerboard_spec(repo_root=root)
    if spec != expected:
        raise ValueError("Metric calibration target spec drifted from generator")
