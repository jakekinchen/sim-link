"""WCW-1: the Workcell Calibration Witness, a ball-cartridge target design.

WCW-1 supersedes the slug-based "calbrick" as the recommended physical design.
It adopts the metrology-driven decisions from the workcell design review:

* **Precision bearing balls, not slugs.** A 20 mm G25 AISI 52100 chrome-steel
  ball has certified diameter, orientation-independent inertia, self-locates in
  a printed cradle, and its *measured* mass (not the nominal ~32.7 g) enters the
  ground-truth model via the receipt.
* **Flat, parallel grasp faces with a tag-free contact band** instead of a
  grasp rib: the gripper contacts bare reference PLA on a central 18 mm band;
  fiducials sit above the band and on the other faces. No tag on the sliding
  bottom face.
* **Keyed cartridges C0-C4.** One printed carrier per configuration holds the
  balls at spec'd y-offsets. C1 vs C2 changes *only* the center of mass
  (same total mass); C3 vs C4 changes *only* the rotational inertia (same
  total mass AND same center of mass) -- each pair isolates one term.
* **Solid printing standard.** The shell is an explicit CAD solid printed with
  full walls (``nominal_infill=1.0``), not slicer sparse infill, so
  geometry-based inertia is meaningful; the weigh-back loop absorbs the
  remaining as-printed deviation.

Modeling notes (idealizations the receipt absorbs):

* Each ball seat is modeled as a full spherical void of exactly the ball
  diameter inside the carrier, with the steel ball filling it -- exact for mass
  algebra. The physical carrier uses a three-point cradle plus retainer; the
  small plastic difference is captured by weighing the printed carrier.
* The flush top lid is modeled as part of the closed shell; weigh body and lid
  together (or record separately in the receipt).
* External 2 mm edge chamfers and the 1 mm orientation notch are not modeled;
  they are symmetric/negligible and covered by the measured-mass feedback.
"""

from __future__ import annotations

import hashlib
import json
import math

from dataclasses import asdict, dataclass, field, replace

import numpy as np

from scenesmith.calibration import primitives as prim
from scenesmith.calibration.configurations import Cartridge, PartRow, ResolvedTarget
from scenesmith.calibration.geometry import TargetGeometry, _fiducial
from scenesmith.calibration.mass_properties import combine_all
from scenesmith.calibration.materials import effective_density_from_mass, get_material
from scenesmith.calibration.primitives import Axis, Primitive
from scenesmith.calibration.spec import MM, FiducialFace, G, Tolerances


@dataclass(frozen=True)
class BallCarrier:
    """The printed cartridge carrier that seats the bearing balls.

    One carrier is printed per configuration; all carriers share these
    dimensions so their modeled plastic mass differs only by seat count.
    """

    x_mm: float = 26.0
    y_mm: float = 54.0
    z_mm: float = 24.0
    seat_min_wall_mm: float = 1.5


@dataclass(frozen=True)
class Wcw1Spec:
    """Parametric description of a WCW-1 body (all lengths in mm).

    Axes: x is the 40 mm grasp thickness (gripper closes along x), y the 60 mm
    width (ball offsets run along y), z the 65 mm height. Origin at the outer
    box centroid; the bottom sliding face is -z.
    """

    name: str = "so101_wcw1"
    version: str = "0.1.0"

    length_mm: float = 40.0  # grasp thickness (between gripper contact faces)
    width_mm: float = 60.0
    height_mm: float = 65.0
    wall_mm: float = 2.4

    shell_material: str = "pla"
    shell_effective_density: float | None = None
    # Reference manufacturing standard: explicit CAD solid, full walls, no
    # sparse infill -- so the nominal print is solid plastic.
    nominal_infill: float = 1.0

    ball_material: str = "chrome_steel_52100"
    ball_diameter_mm: float = 20.0  # ISO 3290-1 G25 nominal
    ball_measured_mass_g: float | None = None  # mean of the selected matched set

    carrier: BallCarrier = field(default_factory=BallCarrier)
    carrier_measured_mass_g: float | None = None  # per-carrier weigh-back

    contact_band_height_mm: float = 18.0

    fiducials: tuple[FiducialFace, ...] = field(
        default_factory=lambda: (
            FiducialFace("top", "+z", tag_id=0, tag_size_mm=24.0, quiet_zone_mm=2.5),
            FiducialFace("side_py", "+y", tag_id=1, tag_size_mm=24.0),
            FiducialFace("side_ny", "-y", tag_id=2, tag_size_mm=24.0),
            # Grasp-face tags sit above the tag-free contact band.
            FiducialFace(
                "grasp_px", "+x", tag_id=3, tag_size_mm=16.0, offset_mm=(0.0, 20.0)
            ),
            FiducialFace(
                "grasp_nx", "-x", tag_id=4, tag_size_mm=16.0, offset_mm=(0.0, 20.0)
            ),
        )
    )
    # WCW-1 deliberately has no rib and no bonded coupons: the printed PLA
    # grasp/bottom faces are the standardized half of each contact pair.
    grasp: None = None
    coupons: tuple = ()

    tolerances: Tolerances = field(default_factory=Tolerances)
    triangulation_segments: int = 48

    # ----- derived quantities ------------------------------------------- #

    def shell_density(self) -> float:
        """Effective printed-plastic density (kg/m**3) for the model."""
        if self.shell_effective_density is not None:
            return self.shell_effective_density
        return get_material(self.shell_material).density * self.nominal_infill

    def cavity_extents_mm(self) -> tuple[float, float, float]:
        t2 = 2.0 * self.wall_mm
        return (self.length_mm - t2, self.width_mm - t2, self.height_mm - t2)

    def ball_mass_kg(self) -> float:
        """Ground-truth mass of one ball (kg); measured value wins."""
        if self.ball_measured_mass_g is not None:
            return self.ball_measured_mass_g * G
        r = self.ball_diameter_mm * MM / 2.0
        return 4.0 / 3.0 * math.pi * r**3 * get_material(self.ball_material).density

    def ball_density(self) -> float:
        """Effective ball density so the modeled sphere matches ground truth."""
        r = self.ball_diameter_mm * MM / 2.0
        return self.ball_mass_kg() / (4.0 / 3.0 * math.pi * r**3)

    def cartridge_line(self) -> str:
        """One-line cartridge description for the acceptance sheet."""
        return (
            f"- **Cartridge insert:** {self.ball_material} bearing ball, "
            f"d{self.ball_diameter_mm:.3f} mm (G25 / ISO 3290-1), "
            f"{self.ball_mass_kg() * 1e3:.3f} g each (model)"
        )

    def with_measured_shell_mass(
        self, measured_mass_g: float, shell_solid_volume_m3: float
    ) -> "Wcw1Spec":
        """Fix the effective shell density from the weighed body+lid."""
        density = effective_density_from_mass(
            measured_mass_g * G, shell_solid_volume_m3
        )
        return replace(self, shell_effective_density=density)

    def with_measured_ball_mass(self, grams: float) -> "Wcw1Spec":
        """Use the measured mean mass of the selected matched ball set."""
        return replace(self, ball_measured_mass_g=grams)

    def with_measured_slug_mass(self, grams: float) -> "Wcw1Spec":
        """Alias so generic tooling can feed back the cartridge-insert mass."""
        return self.with_measured_ball_mass(grams)

    def validate(self) -> list[str]:
        """Geometry invariants; empty list means the spec is sound."""
        warnings: list[str] = []
        cav = self.cavity_extents_mm()
        if min(cav) <= 0:
            warnings.append(f"wall_mm={self.wall_mm} too thick; cavity {cav}")
        c = self.carrier
        if c.x_mm > cav[0] or c.y_mm > cav[1] or c.z_mm > cav[2]:
            warnings.append(
                f"carrier ({c.x_mm}x{c.y_mm}x{c.z_mm}) exceeds cavity "
                f"({cav[0]:.1f}x{cav[1]:.1f}x{cav[2]:.1f})"
            )
        d = self.ball_diameter_mm
        if d + 2 * c.seat_min_wall_mm > min(c.x_mm, c.z_mm):
            warnings.append(
                f"ball d{d} + walls does not fit carrier section "
                f"({c.x_mm}x{c.z_mm})"
            )
        half = {
            "x": self.length_mm / 2,
            "y": self.width_mm / 2,
            "z": self.height_mm / 2,
        }
        for fid in self.fiducials:
            if fid.recess_depth_mm >= self.wall_mm:
                warnings.append(
                    f"fiducial '{fid.name}' recess {fid.recess_depth_mm} mm >= "
                    f"wall {self.wall_mm} mm"
                )
            pocket_half = (fid.tag_size_mm + 2 * fid.quiet_zone_mm) / 2.0
            axis = fid.face[1]
            in_plane = [a for a in ("x", "y", "z") if a != axis]
            for dim, off in zip(in_plane, fid.offset_mm):
                if abs(off) + pocket_half > half[dim]:
                    warnings.append(
                        f"fiducial '{fid.name}' pocket exceeds the {dim} extent "
                        f"of face {fid.face}"
                    )
            # Grasp-face tags must clear the tag-free contact band.
            if fid.face[1] == "x":
                band_top = self.contact_band_height_mm / 2.0
                if fid.offset_mm[1] - pocket_half < band_top:
                    warnings.append(
                        f"fiducial '{fid.name}' intrudes into the contact band "
                        f"(clear z > {band_top} mm)"
                    )
        return warnings

    def to_dict(self) -> dict:
        return asdict(self)

    def content_hash(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, default=list)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]

    def revision(self) -> str:
        return f"{self.name}-v{self.version}-{self.content_hash()}"


def default_wcw1_target() -> Wcw1Spec:
    """The WCW-1 v1 reference design for the SO-101 workcell."""
    return Wcw1Spec()


@dataclass(frozen=True)
class Wcw1Configuration:
    """A keyed cartridge loadout: ball seats at fixed y-offsets (mm)."""

    name: str
    description: str
    seats_y_mm: tuple[float, ...] = ()
    include_carrier: bool = True

    def total_slugs(self) -> int:  # keep the Configuration interface
        return len(self.seats_y_mm)

    @property
    def cartridges(self) -> tuple[Cartridge, ...]:
        """Report-compatible view: one 'cartridge' per seated ball."""
        return tuple(
            Cartridge((0, i), 1, "chrome_steel_52100")
            for i in range(len(self.seats_y_mm))
        )


def wcw1_kit(spec: Wcw1Spec, slugs: int = 0) -> list[Wcw1Configuration]:
    """The canonical C0-C4 cartridge set.

    ``slugs`` is accepted for CLI interface parity and ignored -- WCW-1 loadouts
    are fixed by design so the C1/C2 and C3/C4 pairs stay mass-matched.
    """
    del slugs
    return [
        Wcw1Configuration(
            "C0",
            "Bare body: printed shell, perception and light-payload baseline.",
            (),
            include_carrier=False,
        ),
        Wcw1Configuration(
            "C1", "One ball centered (y=0): known centered payload.", (0.0,)
        ),
        Wcw1Configuration(
            "C2",
            "Same single ball moved to y=+15 mm: CoM shift at constant mass.",
            (15.0,),
        ),
        Wcw1Configuration(
            "C3",
            "Two balls at y=+/-11 mm: centered mass, lower rotational inertia.",
            (-11.0, 11.0),
        ),
        Wcw1Configuration(
            "C4",
            "Two balls at y=+/-15 mm: same mass AND CoM as C3, higher inertia.",
            (-15.0, 15.0),
        ),
    ]


def build_wcw1_geometry(spec: Wcw1Spec) -> TargetGeometry:
    """Resolve the WCW-1 shell (body + lid + tag recesses) into primitives."""
    rho = spec.shell_density()
    L, W, H = (v * MM for v in (spec.length_mm, spec.width_mm, spec.height_mm))
    ci_x, ci_y, ci_z = (v * MM for v in spec.cavity_extents_mm())

    shell: list[Primitive] = [
        prim.box((0, 0, 0), L, W, H, rho, "shell_outer"),
        prim.box((0, 0, 0), ci_x, ci_y, ci_z, -rho, "shell_cavity"),
    ]

    tag_frames: dict[str, dict] = {}
    for fid in spec.fiducials:
        frame, recess = _fiducial(spec, fid, (L, W, H), rho)
        shell.append(recess)
        tag_frames[fid.name] = frame

    # Grasp frame: jaws close along body x on the contact band at the body
    # center; approach from above (tool z = -body z).
    grasp = np.eye(4)
    grasp[:3, 0] = [1.0, 0.0, 0.0]
    grasp[:3, 1] = [0.0, -1.0, 0.0]
    grasp[:3, 2] = [0.0, 0.0, -1.0]

    cavity_floor_z = -H / 2 + spec.wall_mm * MM
    return TargetGeometry(
        spec=spec,
        shell_primitives=shell,
        coupon_primitives=[],
        tag_frames=tag_frames,
        grasp_frame=grasp,
        socket_floor_z=cavity_floor_z,
        socket_axis=Axis.Y,
        socket_positions={},
    )


def _cartridge_primitives(
    spec: Wcw1Spec, geom: TargetGeometry, config: Wcw1Configuration
) -> list[Primitive]:
    """Model one keyed cartridge: carrier box, seat voids, and steel balls."""
    if not config.include_carrier:
        return []
    c = spec.carrier
    rho_p = spec.shell_density()
    if spec.carrier_measured_mass_g is not None:
        # Weigh-back: scale carrier plastic density so the modeled net carrier
        # (box minus seat voids) matches the scale reading.
        d = spec.ball_diameter_mm * MM
        box_vol = c.x_mm * c.y_mm * c.z_mm * MM**3
        void_vol = len(config.seats_y_mm) * math.pi / 6.0 * d**3
        rho_p = (spec.carrier_measured_mass_g * G) / (box_vol - void_vol)
    r_ball = spec.ball_diameter_mm * MM / 2.0
    center_z = geom.socket_floor_z + c.z_mm * MM / 2.0

    out: list[Primitive] = [
        prim.box(
            (0.0, 0.0, center_z),
            c.x_mm * MM,
            c.y_mm * MM,
            c.z_mm * MM,
            rho_p,
            f"carrier_{config.name}",
        )
    ]
    for k, y_mm in enumerate(config.seats_y_mm):
        center = (0.0, y_mm * MM, center_z)
        out.append(prim.sphere(center, r_ball, -rho_p, f"void_seat_{k}"))
        out.append(prim.sphere(center, r_ball, spec.ball_density(), f"ball_{k}"))
    return out


def resolve_wcw1(
    spec: Wcw1Spec,
    config: Wcw1Configuration,
    geometry: TargetGeometry | None = None,
) -> ResolvedTarget:
    """Compose the shell + one cartridge into a target with exact properties."""
    geom = geometry or build_wcw1_geometry(spec)
    cartridges = _cartridge_primitives(spec, geom, config)
    all_prims = list(geom.shell_primitives) + cartridges
    mp = combine_all(p.mass_properties() for p in all_prims)

    parts: list[PartRow] = []
    shell_mp = combine_all(p.mass_properties() for p in geom.shell_primitives)
    shell_mass = sum(p.mass for p in geom.shell_primitives)
    parts.append(
        PartRow(
            "printed_shell_net",
            "plastic_shell",
            1,
            shell_mass,
            shell_mass,
            tuple(shell_mp.com),
        )
    )
    if cartridges:
        plastic = [p for p in cartridges if p.label.startswith(("carrier", "void_"))]
        balls = [p for p in cartridges if p.label.startswith("ball_")]
        carrier_mp = combine_all(p.mass_properties() for p in plastic)
        carrier_mass = sum(p.mass for p in plastic)
        parts.append(
            PartRow(
                f"carrier_{config.name}",
                spec.shell_material,
                1,
                carrier_mass,
                carrier_mass,
                tuple(carrier_mp.com),
            )
        )
        if balls:
            ball_mp = combine_all(p.mass_properties() for p in balls)
            parts.append(
                PartRow(
                    f"balls_d{spec.ball_diameter_mm:g}mm",
                    spec.ball_material,
                    len(balls),
                    balls[0].mass,
                    sum(p.mass for p in balls),
                    tuple(ball_mp.com),
                )
            )

    return ResolvedTarget(
        spec=spec,
        geometry=geom,
        config=config,
        cartridge_primitives=cartridges,
        all_primitives=all_prims,
        mass_properties=mp,
        parts=parts,
    )
