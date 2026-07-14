"""The single parametric source of truth for a calibration target.

Everything downstream -- CAD, mass properties, MuJoCo/URDF assets, the bill of
materials, the fiducial coordinate table, and the acceptance sheet -- is derived
from a :class:`CalibrationTargetSpec`. Change one number here and every artifact
regenerates consistently. The spec is content-hashed so a printed part can be
traced back to the exact parameters it came from.

Dimensions are authored in millimeters (natural for CAD and slicers) and
converted to SI once, at the geometry boundary. The body frame origin sits at
the centroid of the outer bounding box; +x is length, +y is width, +z is
height, so the base face is the -z plane.
"""

from __future__ import annotations

import hashlib
import json

from dataclasses import asdict, dataclass, field, replace

from scenesmith.calibration.materials import get_material

MM: float = 1e-3  # millimeters -> meters
G: float = 1e-3  # grams -> kilograms


@dataclass(frozen=True)
class SocketGrid:
    """Grid of cartridge bores inside the shell cavity.

    Sockets are addressed by integer (i, j) with the grid centered on the body
    axis, so a symmetric fill yields a centered planar center of mass. Guide
    tubes (thin plastic walls around each bore) both locate the cartridges and
    contribute a small, exactly-known plastic mass.
    """

    nx: int = 3
    ny: int = 3
    pitch_x_mm: float = 22.0
    pitch_y_mm: float = 16.0
    bore_diameter_mm: float = 8.2
    guide_wall_mm: float = 1.2
    floor_clearance_mm: float = 1.0
    depth_mm: float = 34.0

    def positions_mm(self) -> list[tuple[int, int, float, float]]:
        """Return ``(i, j, x_mm, y_mm)`` for every socket, grid-centered."""
        out = []
        for i in range(self.nx):
            for j in range(self.ny):
                x = (i - (self.nx - 1) / 2.0) * self.pitch_x_mm
                y = (j - (self.ny - 1) / 2.0) * self.pitch_y_mm
                out.append((i, j, x, y))
        return out


@dataclass(frozen=True)
class FiducialFace:
    """An AprilTag recess on one face of the body.

    The tag frame is derived in :mod:`geometry`: origin at the recess center on
    the outer surface, +z along the outward face normal, +x along the body axis
    that stays in-plane. Emitting the tag-to-CoM transform is what lets a camera
    localize the (invisible) center of mass.
    """

    name: str
    face: str  # one of +x,-x,+y,-y,+z,-z
    tag_id: int
    tag_size_mm: float = 24.0
    recess_depth_mm: float = 1.2
    quiet_zone_mm: float = 3.0
    family: str = "tag36h11"


@dataclass(frozen=True)
class GraspFeature:
    """A standardized grasp rib sized to the gripper jaw opening.

    The rib gives the parallel-jaw gripper a repeatable, well-defined line of
    contact. ``width_mm`` is the jaw spacing when closed on the rib; the top
    fiducial rides on the rib's outer surface, so the rib footprint must be
    large enough to contain that tag's recess.
    """

    width_mm: float = 32.0
    length_mm: float = 34.0
    height_mm: float = 16.0
    face: str = "+z"


@dataclass(frozen=True)
class CouponMount:
    """A replaceable friction coupon bonded to a contact face."""

    coupon: str  # key into materials.FRICTION_COUPONS
    face: str
    size_mm: tuple[float, float] = (30.0, 30.0)


@dataclass(frozen=True)
class Tolerances:
    """Acceptance tolerances for the as-built vs. modeled comparison."""

    mass_g: float = 2.0
    com_mm: float = 1.0
    inertia_rel: float = 0.05


@dataclass(frozen=True)
class CalibrationTargetSpec:
    """Full parametric description of a calibration target family.

    A single spec describes one printed *shell*; the interchangeable cartridge
    loadouts (configurations) are applied on top of it in
    :mod:`configurations`.
    """

    name: str = "so101_calbrick"
    version: str = "0.1.0"

    length_mm: float = 84.0
    width_mm: float = 60.0
    height_mm: float = 46.0
    wall_mm: float = 2.4

    shell_material: str = "pla"
    # As-printed effective density (kg/m**3). None -> nominal solid density,
    # scaled by ``nominal_infill`` as a first estimate until the shell is weighed.
    shell_effective_density: float | None = None
    nominal_infill: float = 0.6

    cartridge_material: str = "steel"
    slug_diameter_mm: float = 7.9
    slug_length_mm: float = 8.0
    # Optional per-slug measured mass (g). Preferred over geometry x density for
    # ground truth once slugs are weighed on a scale.
    slug_measured_mass_g: float | None = None

    sockets: SocketGrid = field(default_factory=SocketGrid)
    fiducials: tuple[FiducialFace, ...] = field(
        default_factory=lambda: (
            FiducialFace("top", "+z", tag_id=0, tag_size_mm=24.0, quiet_zone_mm=2.5),
            FiducialFace("side_x", "+x", tag_id=1, tag_size_mm=24.0),
            FiducialFace("side_y", "+y", tag_id=2, tag_size_mm=24.0),
        )
    )
    grasp: GraspFeature = field(default_factory=GraspFeature)
    coupons: tuple[CouponMount, ...] = field(
        default_factory=lambda: (
            CouponMount("coupon_pla_smooth", "-z", (34.0, 34.0)),
            CouponMount("coupon_tpu_grip", "+x", (28.0, 28.0)),
        )
    )

    tolerances: Tolerances = field(default_factory=Tolerances)
    triangulation_segments: int = 48

    # ----- derived quantities ------------------------------------------- #

    def shell_density(self) -> float:
        """Effective shell density (kg/m**3) used for the ground-truth model."""
        if self.shell_effective_density is not None:
            return self.shell_effective_density
        return get_material(self.shell_material).density * self.nominal_infill

    def cavity_extents_mm(self) -> tuple[float, float, float]:
        """Inner cavity extents (mm)."""
        t2 = 2.0 * self.wall_mm
        return (
            self.length_mm - t2,
            self.width_mm - t2,
            self.height_mm - t2,
        )

    def outer_extents_m(self) -> tuple[float, float, float]:
        return (self.length_mm * MM, self.width_mm * MM, self.height_mm * MM)

    def slug_mass_kg(self) -> float:
        """Ground-truth mass of one cartridge slug (kg)."""
        if self.slug_measured_mass_g is not None:
            return self.slug_measured_mass_g * G
        import math

        r = (self.slug_diameter_mm * MM) / 2.0
        h = self.slug_length_mm * MM
        vol = math.pi * r * r * h
        return vol * get_material(self.cartridge_material).density

    def with_measured_shell_mass(
        self, measured_mass_g: float, shell_solid_volume_m3: float
    ) -> "CalibrationTargetSpec":
        """Return a copy whose shell density is fixed from a weighed shell.

        Args:
            measured_mass_g: Scale reading of the bare printed shell (grams).
            shell_solid_volume_m3: Solid plastic volume from
                :func:`geometry.shell_solid_volume`.
        """
        from scenesmith.calibration.materials import effective_density_from_mass

        density = effective_density_from_mass(
            measured_mass_g * G, shell_solid_volume_m3
        )
        return replace(self, shell_effective_density=density)

    def with_measured_slug_mass(self, grams: float) -> "CalibrationTargetSpec":
        """Return a copy that uses a weighed per-slug mass for ground truth."""
        return replace(self, slug_measured_mass_g=grams)

    def validate(self) -> list[str]:
        """Return a list of geometry warnings; empty means the spec is sound.

        Guards the invariants the exact mass model relies on -- most importantly
        that every carved recess stays inside solid plastic, so no subtracted
        primitive ever produces negative net density.
        """
        warnings: list[str] = []
        cav = self.cavity_extents_mm()
        if min(cav) <= 0:
            warnings.append(
                f"wall_mm={self.wall_mm} too thick for envelope; cavity {cav}"
            )
        if self.slug_diameter_mm >= self.sockets.bore_diameter_mm:
            warnings.append(
                f"slug_diameter_mm={self.slug_diameter_mm} >= "
                f"bore_diameter_mm={self.sockets.bore_diameter_mm}"
            )
        # Socket grid must fit inside the cavity footprint (incl. guide walls).
        sg = self.sockets
        span_x = (
            (sg.nx - 1) * sg.pitch_x_mm + sg.bore_diameter_mm + 2 * sg.guide_wall_mm
        )
        span_y = (
            (sg.ny - 1) * sg.pitch_y_mm + sg.bore_diameter_mm + 2 * sg.guide_wall_mm
        )
        if span_x > cav[0] or span_y > cav[1]:
            warnings.append(
                f"socket grid span ({span_x:.1f},{span_y:.1f}) mm exceeds cavity "
                f"({cav[0]:.1f},{cav[1]:.1f}) mm"
            )
        if sg.depth_mm > cav[2]:
            warnings.append(
                f"socket depth {sg.depth_mm} mm exceeds cavity height {cav[2]:.1f} mm"
            )
        for fid in self.fiducials:
            if fid.recess_depth_mm >= self.wall_mm and fid.face != self.grasp.face:
                warnings.append(
                    f"fiducial '{fid.name}' recess {fid.recess_depth_mm} mm >= "
                    f"wall {self.wall_mm} mm (would breach the wall)"
                )
            pocket = fid.tag_size_mm + 2 * fid.quiet_zone_mm
            if fid.face == self.grasp.face:
                # Tag recess must stay within the grasp-rib footprint.
                if pocket > self.grasp.length_mm or pocket > self.grasp.width_mm:
                    warnings.append(
                        f"fiducial '{fid.name}' pocket {pocket:.1f} mm exceeds grasp "
                        f"rib footprint ({self.grasp.length_mm}x{self.grasp.width_mm})"
                    )
                if fid.recess_depth_mm >= self.grasp.height_mm:
                    warnings.append(
                        f"fiducial '{fid.name}' recess deeper than grasp rib height"
                    )
        return warnings

    def to_dict(self) -> dict:
        """Canonical, JSON-serializable representation."""
        return asdict(self)

    def content_hash(self) -> str:
        """Stable 12-char hash of the spec for versioning and traceability."""
        blob = json.dumps(self.to_dict(), sort_keys=True, default=list)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]

    def revision(self) -> str:
        """Human-facing revision string: ``<name>-v<version>-<hash>``."""
        return f"{self.name}-v{self.version}-{self.content_hash()}"


def default_so101_target() -> CalibrationTargetSpec:
    """A ready-to-print target scaled for the SO-101 arm and gripper."""
    return CalibrationTargetSpec()
