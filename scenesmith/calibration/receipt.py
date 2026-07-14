"""CalibrationArtifactReceipt: the as-built record that pins model to part.

The deliverable standard is *CAD plus a receipt*, not an STL. The receipt
records what was actually printed, bought, measured, and weighed -- printer,
slicer profile, filament lots, ball supplier/grade, measured dimensions and
masses -- and the simulator inertials are regenerated FROM those measurements,
never from nominal slicer density.

Workflow:
    1. ``blank_receipt(spec)`` -> fill in during the build and acceptance pass.
    2. ``apply_receipt(spec, receipt)`` -> a spec whose shell density and
       insert masses come from the scale, not from nominals.
    3. Regenerate the kit; the receipt travels with the artifact directory.
"""

from __future__ import annotations

import json

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class CalibrationArtifactReceipt:
    """As-built provenance and measurements for one physical target build.

    All masses in grams, dimensions in millimeters. ``None``/empty means
    not yet measured. Only the fields consumed by :func:`apply_receipt` affect
    the regenerated model; the rest are traceability evidence.
    """

    artifact_id: str = ""
    design: str = ""  # "wcw1" or "calbrick"
    spec_hash: str = ""
    cad_commit: str = ""

    # Reference manufacturing record.
    printer: str = ""
    printer_firmware: str = ""
    slicer: str = ""
    slicer_version: str = ""
    profile_hash: str = ""
    nozzle_mm: float | None = None
    build_plate: str = ""
    filament: str = ""
    filament_lots: list[str] = field(default_factory=list)

    # Measured geometry (key -> mm), e.g. {"grasp_thickness_top": 40.03}.
    measured_dimensions_mm: dict[str, float] = field(default_factory=dict)

    # Measured masses (grams).
    body_mass_g: float | None = None  # bare printed shell incl. lid
    lid_mass_g: float | None = None
    carrier_masses_g: dict[str, float] = field(default_factory=dict)  # per config

    # Bearing-ball provenance and measurements.
    ball_supplier: str = ""
    ball_listing: str = ""
    ball_material: str = ""
    ball_grade: str = ""
    ball_nominal_diameter_mm: float | None = None
    ball_measured_diameters_mm: list[float] = field(default_factory=list)
    ball_measured_masses_g: list[float] = field(default_factory=list)

    # Assembled per-configuration scale readings (cross-check, not input).
    configuration_masses_g: dict[str, float] = field(default_factory=dict)

    # Perception acceptance evidence.
    tag_detection_results: dict[str, dict] = field(default_factory=dict)
    reprojection_median_px: float | None = None
    photos: list[str] = field(default_factory=list)

    acceptance_result: str = ""  # "pass" / "fail" / notes

    def selected_ball_mass_g(self) -> float | None:
        """Mean measured mass of the matched ball set, if weighed."""
        if not self.ball_measured_masses_g:
            return None
        return sum(self.ball_measured_masses_g) / len(self.ball_measured_masses_g)

    def to_json(self, path: str | Path) -> None:
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def from_json(cls, path: str | Path) -> "CalibrationArtifactReceipt":
        with open(path) as f:
            data = json.load(f)
        return cls(**data)


def blank_receipt(spec, design: str) -> CalibrationArtifactReceipt:
    """A template receipt pre-filled with the spec's identity fields."""
    receipt = CalibrationArtifactReceipt(
        artifact_id=f"{spec.revision()}-serial-____",
        design=design,
        spec_hash=spec.content_hash(),
    )
    if hasattr(spec, "ball_material"):
        receipt.ball_material = spec.ball_material
        receipt.ball_grade = "G25"
        receipt.ball_nominal_diameter_mm = spec.ball_diameter_mm
    return receipt


def apply_receipt(spec, receipt: CalibrationArtifactReceipt, geometry=None):
    """Return a spec updated with the receipt's measured masses.

    Applies, when present:
      * ``body_mass_g`` (+ ``lid_mass_g`` if weighed separately) -> effective
        shell density via the modeled solid volume;
      * measured ball masses (WCW-1) or insert mass -> insert ground truth.

    Args:
        spec: A ``Wcw1Spec`` or ``CalibrationTargetSpec``.
        receipt: The filled-in as-built receipt.
        geometry: Optional pre-built geometry (avoids a rebuild).

    Returns:
        A new spec of the same type with measured values applied.
    """
    updated = spec
    if receipt.body_mass_g is not None:
        if geometry is None:
            geometry = _build_geometry_for(spec)
        total_g = receipt.body_mass_g + (receipt.lid_mass_g or 0.0)
        updated = updated.with_measured_shell_mass(
            total_g, geometry.shell_solid_volume()
        )
    ball_mass = receipt.selected_ball_mass_g()
    if ball_mass is not None and hasattr(updated, "with_measured_ball_mass"):
        updated = updated.with_measured_ball_mass(ball_mass)
    return updated


def _build_geometry_for(spec):
    """Dispatch geometry construction on the spec type."""
    if hasattr(spec, "ball_material"):
        from scenesmith.calibration.wcw1 import build_wcw1_geometry

        return build_wcw1_geometry(spec)
    from scenesmith.calibration.geometry import build_geometry

    return build_geometry(spec)
