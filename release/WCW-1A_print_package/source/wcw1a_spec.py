"""Frozen parametric contract for the WCW-1A AprilTag calibration cube.

All geometry is expressed in millimetres.  The printable CAD generator, tag
artwork generator, validation report, and documentation import this module so
the release package cannot silently drift across those surfaces.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math


@dataclass(frozen=True)
class TagPlacement:
    name: str
    face: str
    tag_id: int
    black_square_mm: float
    full_label_mm: float
    face_up_direction: str
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0
    center_z_mm: float = 0.0

    @property
    def module_mm(self) -> float:
        """Module pitch for the full 10 x 10 tag36h11 raster."""
        return self.full_label_mm / 10.0

    @property
    def white_border_mm(self) -> float:
        """Required one-module white border on each edge."""
        return (self.full_label_mm - self.black_square_mm) / 2.0


@dataclass(frozen=True)
class Wcw1aSpec:
    revision: str = "WCW-1A-R1"
    units: str = "mm"

    body_x_mm: float = 40.0
    body_y_mm: float = 60.0
    body_z_mm: float = 65.0
    body_wall_mm: float = 2.4
    body_roof_mm: float = 2.8
    body_edge_chamfer_mm: float = 2.0
    grasp_band_height_mm: float = 18.0

    ball_nominal_diameter_mm: float = 20.0
    ball_expected_min_mm: float = 19.8
    ball_expected_max_mm: float = 20.2
    ball_fit_allowance_diametral_mm: float = 0.8
    ball_density_g_cm3: float = 7.81

    carrier_x_min_mm: float = -17.0
    carrier_x_max_mm: float = 14.0
    carrier_y_mm: float = 54.4
    carrier_z_mm: float = 25.0
    retainer_x_max_mm: float = 16.5
    retainer_plate_thickness_mm: float = 1.6
    retainer_slide_total_clearance_mm: float = 0.2
    ball_retainer_preload_mm: float = 0.2

    body_cavity_x_mm: float = 35.2
    body_cavity_y_mm: float = 55.2
    lid_flange_x_mm: float = 39.4
    lid_flange_y_mm: float = 59.4
    lid_flange_thickness_mm: float = 2.6
    lid_plug_x_mm: float = 34.5
    lid_plug_y_mm: float = 54.5
    lid_plug_height_mm: float = 2.4
    lid_detent_interference_each_side_mm: float = 0.15
    lid_crush_rib_interference_mm: float = 0.3

    cartridge_assembly_z_mm: float = -14.2
    cartridge_frame_y_offset_mm: float = 0.0
    lid_assembly_z_mm: float = -31.2

    fit_coupon_pocket_diameters_mm: tuple[float, ...] = (20.4, 20.6, 20.8)
    pla_density_g_cm3: float = 1.24

    configuration_seats_y_mm: dict[str, tuple[float, ...]] = field(
        default_factory=lambda: {
            "C0": (),
            "C1": (0.0,),
            "C2": (15.0,),
            "C3": (-11.0, 11.0),
            "C4": (-15.0, 15.0),
        }
    )
    tags: tuple[TagPlacement, ...] = field(
        default_factory=lambda: (
            TagPlacement("top", "+z", 0, 24.0, 30.0, "+y"),
            TagPlacement("side_py", "+y", 1, 24.0, 30.0, "+z"),
            TagPlacement("side_ny", "-y", 2, 24.0, 30.0, "+z"),
            TagPlacement("grasp_px", "+x", 3, 16.0, 20.0, "+z", center_z_mm=21.5),
            TagPlacement("grasp_nx", "-x", 4, 16.0, 20.0, "+z", center_z_mm=21.5),
        )
    )

    @property
    def body_dimensions_mm(self) -> tuple[float, float, float]:
        return (self.body_x_mm, self.body_y_mm, self.body_z_mm)

    @property
    def coordinate_convention(self) -> dict[str, str]:
        return {
            "origin": "outer_body_centroid",
            "x": "grasp_thickness_40mm",
            "y": "non_grasp_width_60mm",
            "z": "height_65mm_up",
        }

    @property
    def ball_expected_range_mm(self) -> tuple[float, float]:
        return (self.ball_expected_min_mm, self.ball_expected_max_mm)

    @property
    def ball_pocket_diameter_mm(self) -> float:
        return self.ball_nominal_diameter_mm + self.ball_fit_allowance_diametral_mm

    @property
    def ball_pocket_diametral_clearance_nominal_mm(self) -> float:
        return self.ball_pocket_diameter_mm - self.ball_nominal_diameter_mm

    @property
    def ball_pocket_diametral_clearance_at_max_ball_mm(self) -> float:
        return self.ball_pocket_diameter_mm - self.ball_expected_max_mm

    @property
    def total_balls_for_all_cartridges(self) -> int:
        return sum(len(seats) for seats in self.configuration_seats_y_mm.values())

    @property
    def ball_nominal_mass_g(self) -> float:
        radius_cm = self.ball_nominal_diameter_mm / 20.0
        return 4.0 / 3.0 * math.pi * radius_cm**3 * self.ball_density_g_cm3

    @property
    def minimum_ball_wall_mm(self) -> float:
        pocket_radius = self.ball_pocket_diameter_mm / 2.0
        outer_y_wall = self.carrier_y_mm / 2.0 - 15.0 - pocket_radius
        outer_z_wall = self.carrier_z_mm / 2.0 - pocket_radius
        c3_web = 22.0 - self.ball_pocket_diameter_mm
        return min(outer_y_wall, outer_z_wall, c3_web)

    @property
    def cartridge_to_body_clearance_mm(self) -> dict[str, float]:
        cavity_half_x = self.body_cavity_x_mm / 2.0
        return {
            "x_minus": self.carrier_x_min_mm - (-cavity_half_x),
            "x_plus": cavity_half_x - self.retainer_x_max_mm,
            "y_each_side": (self.body_cavity_y_mm - self.carrier_y_mm) / 2.0,
        }

    @property
    def lid_plug_clearance_each_side_mm(self) -> float:
        return min(
            (self.body_cavity_x_mm - self.lid_plug_x_mm) / 2.0,
            (self.body_cavity_y_mm - self.lid_plug_y_mm) / 2.0,
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.units != "mm":
            errors.append("CAD units must be millimetres")
        if self.body_dimensions_mm != (40.0, 60.0, 65.0):
            errors.append("frozen body dimensions drifted")
        if self.ball_expected_max_mm >= self.ball_pocket_diameter_mm:
            errors.append("maximum ordinary ball does not clear the pocket")
        if self.minimum_ball_wall_mm < 1.2 - 1e-9:
            errors.append("local material between/around ball pockets is below 1.2 mm")
        if self.total_balls_for_all_cartridges > 10:
            errors.append("kit needs more than the ten owner-supplied balls")
        if len({tag.tag_id for tag in self.tags}) != len(self.tags):
            errors.append("AprilTag IDs are not unique")
        for tag in self.tags:
            if abs(tag.white_border_mm - tag.module_mm) > 1e-9:
                errors.append(f"{tag.name} does not have a one-module white border")
            if tag.face in {"+x", "-x"}:
                label_bottom = tag.center_z_mm - tag.full_label_mm / 2.0
                if label_bottom <= self.grasp_band_height_mm / 2.0:
                    errors.append(f"{tag.name} overlaps the grasp band")
        return errors

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["derived"] = {
            "ball_pocket_diameter_mm": self.ball_pocket_diameter_mm,
            "ball_nominal_mass_g": self.ball_nominal_mass_g,
            "minimum_ball_wall_mm": self.minimum_ball_wall_mm,
            "total_balls_for_all_cartridges": self.total_balls_for_all_cartridges,
        }
        return payload

    def identity_sha256(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
