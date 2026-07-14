"""Interchangeable cartridge loadouts for one printed shell.

A single shell supports a *family* of ground-truth targets by loading steel
slugs into different sockets. The standard kit provides the three regimes a
self-calibrating arm needs to excite:

* ``centered``     -- mass packed at the center: planar CoM on the axis, low
                      rotational inertia (the baseline).
* ``offset``       -- mass on one side: a known off-axis center of mass.
* ``high_inertia`` -- the *same total mass* moved to the corners: unchanged
                      centered CoM but markedly larger inertia, isolating the
                      inertia term from the mass term.

Because every loadout reuses the identical weighed slugs and shell, the three
targets are mutually consistent and individually traceable.
"""

from __future__ import annotations

import math

from dataclasses import dataclass

import numpy as np

from scenesmith.calibration import primitives as prim
from scenesmith.calibration.geometry import TargetGeometry, build_geometry
from scenesmith.calibration.mass_properties import MassProperties, combine_all
from scenesmith.calibration.materials import get_coupon, get_material
from scenesmith.calibration.primitives import Axis, Primitive
from scenesmith.calibration.spec import MM, CalibrationTargetSpec


@dataclass(frozen=True)
class Cartridge:
    """A stack of ``n_slugs`` identical slugs seated in one socket."""

    socket: tuple[int, int]
    n_slugs: int
    material: str | None = None  # None -> spec.cartridge_material


@dataclass(frozen=True)
class Configuration:
    """A named cartridge loadout applied to a shell."""

    name: str
    description: str
    cartridges: tuple[Cartridge, ...] = ()

    def total_slugs(self) -> int:
        return sum(c.n_slugs for c in self.cartridges)


@dataclass(frozen=True)
class PartRow:
    """One line of the bill of materials / traceability report."""

    label: str
    material: str
    quantity: int
    unit_mass_kg: float
    total_mass_kg: float
    centroid_m: tuple[float, float, float]


@dataclass
class ResolvedTarget:
    """A fully-composed target: geometry + loadout + exact mass properties."""

    spec: CalibrationTargetSpec
    geometry: TargetGeometry
    config: Configuration
    cartridge_primitives: list[Primitive]
    all_primitives: list[Primitive]
    mass_properties: MassProperties
    parts: list[PartRow]

    @property
    def mass_g(self) -> float:
        return self.mass_properties.mass * 1e3

    @property
    def com_mm(self) -> np.ndarray:
        return self.mass_properties.com * 1e3


def _slug_density(spec: CalibrationTargetSpec, material: str | None) -> float:
    """Effective density so a modeled slug matches its ground-truth mass."""
    r = (spec.slug_diameter_mm * MM) / 2.0
    h = spec.slug_length_mm * MM
    volume = math.pi * r * r * h
    use_default = material is None or material == spec.cartridge_material
    if use_default and spec.slug_measured_mass_g is not None:
        # Honor the weighed mass; keep geometric radius/length for inertia.
        return spec.slug_mass_kg() / volume
    name = material or spec.cartridge_material
    return get_material(name).density


def _cartridge_primitives(
    spec: CalibrationTargetSpec, geom: TargetGeometry, config: Configuration
) -> list[Primitive]:
    """Place slug cylinders for a loadout, stacking upward from each socket."""
    r = (spec.slug_diameter_mm * MM) / 2.0
    h = spec.slug_length_mm * MM
    out: list[Primitive] = []
    for cart in config.cartridges:
        if cart.socket not in geom.socket_positions:
            raise KeyError(f"socket {cart.socket} not in grid")
        base = geom.socket_positions[cart.socket]
        rho = _slug_density(spec, cart.material)
        mat = cart.material or spec.cartridge_material
        for k in range(cart.n_slugs):
            z = geom.socket_floor_z + (k + 0.5) * h
            center = (base[0], base[1], z)
            out.append(
                prim.cylinder(
                    center,
                    r,
                    h,
                    Axis.Z,
                    rho,
                    f"slug_{cart.socket[0]}{cart.socket[1]}_{k}_{mat}",
                )
            )
    return out


def _bill_of_materials(
    shell: list[Primitive], coupons: list[Primitive], cartridges: list[Primitive]
) -> list[PartRow]:
    """Group primitives into human-readable BOM rows.

    Shell primitives collapse into a single net plastic row (signed volume nets
    out the cavity and recesses); coupons and cartridges are grouped by label
    stem so a stack of identical slugs reports as one line with a quantity.
    """
    rows: list[PartRow] = []

    shell_mass = sum(p.mass for p in shell)
    shell_material = "plastic_shell"
    shell_mp = combine_all(p.mass_properties() for p in shell)
    rows.append(
        PartRow(
            "printed_shell_net",
            shell_material,
            1,
            shell_mass,
            shell_mass,
            tuple(shell_mp.com),
        )
    )

    # Coupons: recover the coupon key (label minus its trailing face token) and
    # report the coupon's real bulk material from the registry.
    coupon_groups: dict[str, list[Primitive]] = {}
    for p in coupons:
        key = "_".join(p.label.split("_")[:-1])
        coupon_groups.setdefault(key, []).append(p)
    for key, group in coupon_groups.items():
        mp = combine_all(g.mass_properties() for g in group)
        rows.append(
            PartRow(
                key,
                get_coupon(key).material,
                len(group),
                group[0].mass,
                sum(g.mass for g in group),
                tuple(mp.com),
            )
        )
    if cartridges:
        # Group all slugs of a socket+material together (drop the k index).
        by_key: dict[str, list[Primitive]] = {}
        for p in cartridges:
            parts = p.label.split("_")  # slug_<ij>_<k>_<mat>
            key = f"slug_{parts[1]}_{parts[3]}"
            by_key.setdefault(key, []).append(p)
        for key, group in by_key.items():
            mp = combine_all(g.mass_properties() for g in group)
            rows.append(
                PartRow(
                    key,
                    f"cartridge:{key.split('_')[-1]}",
                    len(group),
                    group[0].mass,
                    sum(g.mass for g in group),
                    tuple(mp.com),
                )
            )
    return rows


def resolve_target(
    spec: CalibrationTargetSpec,
    config: Configuration,
    geometry: TargetGeometry | None = None,
) -> ResolvedTarget:
    """Compose a shell + loadout into a target with exact mass properties."""
    geom = geometry or build_geometry(spec)
    cartridges = _cartridge_primitives(spec, geom, config)
    all_prims = list(geom.shell_primitives) + list(geom.coupon_primitives) + cartridges
    mp = combine_all(p.mass_properties() for p in all_prims)
    parts = _bill_of_materials(
        geom.shell_primitives, geom.coupon_primitives, cartridges
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


# --------------------------------------------------------------------------- #
# Standard kit.
# --------------------------------------------------------------------------- #


def standard_kit(spec: CalibrationTargetSpec, slugs: int = 4) -> list[Configuration]:
    """The canonical calibration configurations for a 3x3 socket grid.

    Args:
        spec: Target spec (used to sanity-check the grid size).
        slugs: Number of slugs used by the mass-matched centered/high-inertia
            pair. Must be even so the corner spread is symmetric.

    Returns:
        ``[bare, centered, offset, high_inertia]``. ``centered`` and
        ``high_inertia`` carry identical total mass by construction.
    """
    nx, ny = spec.sockets.nx, spec.sockets.ny
    cx, cy = (nx - 1) // 2, (ny - 1) // 2
    x_hi = nx - 1
    corners = [(0, 0), (0, ny - 1), (x_hi, 0), (x_hi, ny - 1)]
    if slugs % 4 != 0:
        # Keep the corner spread symmetric; round up to a multiple of 4.
        slugs = ((slugs + 3) // 4) * 4
    per_corner = slugs // 4

    bare = Configuration("bare", "Empty shell (for weighing effective density).")
    centered = Configuration(
        "centered",
        "Mass packed in the center socket: axial CoM, low rotational inertia.",
        (Cartridge((cx, cy), slugs),),
    )
    offset = Configuration(
        "offset",
        "Mass at the +x edge socket: a known off-axis center of mass.",
        (Cartridge((x_hi, cy), slugs),),
    )
    high_inertia = Configuration(
        "high_inertia",
        "Same total mass moved to the four corners: centered CoM, high inertia.",
        tuple(Cartridge(c, per_corner) for c in corners),
    )
    return [bare, centered, offset, high_inertia]
