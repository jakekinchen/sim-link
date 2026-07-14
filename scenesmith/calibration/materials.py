"""Material and friction registries for the calibration target.

Two distinct kinds of physical property live here, and the distinction is
deliberate:

* **Bulk density** is a property of a material *body* and is what turns geometry
  into mass. Printed plastic is the subtle case: the as-printed part is never
  fully dense, so we track an *effective* density that is meant to be
  back-calculated from the weighed shell (see
  :func:`effective_density_from_mass`).
* **Friction** is a property of a *contacting pair and surface condition*, never
  a scalar owned by the object. It therefore lives on replaceable surface
  *coupons*, keyed by the pair of surfaces in contact.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    """A bulk material used for a printed shell or a metal cartridge.

    Attributes:
        name: Registry key.
        density: Nominal *solid* density in kg/m**3.
        note: Provenance / measurement guidance.
        is_printed: True for FDM/SLA plastics whose as-built density differs
            from the solid value and must be measured.
    """

    name: str
    density: float
    note: str = ""
    is_printed: bool = False


# Nominal solid densities (kg/m**3). Printed plastics list the *solid* value;
# the as-printed effective density is lower and must be measured per print.
MATERIALS: dict[str, Material] = {
    m.name: m
    for m in [
        Material("pla", 1240.0, "Solid PLA; measure printed shell.", is_printed=True),
        Material("petg", 1270.0, "Solid PETG; measure printed shell.", is_printed=True),
        Material("abs", 1040.0, "Solid ABS; measure printed shell.", is_printed=True),
        Material("pa12", 1010.0, "SLS Nylon PA12.", is_printed=True),
        Material("resin", 1180.0, "Standard SLA resin.", is_printed=True),
        Material("steel", 7850.0, "AISI low-carbon steel dowel/slug."),
        Material(
            "chrome_steel_52100",
            7810.0,
            "AISI 52100 chrome bearing steel (ISO 3290-1 precision balls).",
        ),
        Material("stainless", 7900.0, "304/316 stainless slug or ball."),
        Material("brass", 8500.0, "Brass slug."),
        Material("tungsten", 19250.0, "Tungsten slug (high density, small size)."),
        Material("aluminum", 2700.0, "6061 aluminum slug."),
    ]
}


def get_material(name: str) -> Material:
    """Look up a material by name, raising a clear error if unknown."""
    try:
        return MATERIALS[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(
            f"unknown material '{name}'; known: {sorted(MATERIALS)}"
        ) from exc


def effective_density_from_mass(
    measured_mass_kg: float, solid_volume_m3: float
) -> float:
    """Back-calculate the as-printed effective density from a weighed shell.

    This closes the print-density loop the design depends on: print the bare
    shell, weigh it, and feed the mass back so the ground-truth model uses the
    real density instead of a nominal one.

    Args:
        measured_mass_kg: Scale reading for the bare printed shell (kg).
        solid_volume_m3: Solid volume of the shell from the parametric model
            (m**3), i.e. outer minus all cavities.

    Returns:
        Effective density in kg/m**3.
    """
    if solid_volume_m3 <= 0:
        raise ValueError("solid_volume_m3 must be positive")
    return measured_mass_kg / solid_volume_m3


@dataclass(frozen=True)
class FrictionCoupon:
    """A replaceable contact surface and its measured friction *pairing*.

    Friction is reported against a named counter-surface because it only has
    meaning as a pair. ``mu_static`` / ``mu_kinetic`` are placeholders to be
    filled from a tribometer or a controlled push test on the workcell.

    Attributes:
        name: Registry key (also the printed/engraved coupon id).
        material: Coupon bulk material (for its own small mass contribution).
        thickness_mm: Plate thickness.
        counter_surface: The surface it was characterized against.
        mu_static: Measured static coefficient (None until characterized).
        mu_kinetic: Measured kinetic coefficient (None until characterized).
    """

    name: str
    material: str
    thickness_mm: float
    counter_surface: str = "unknown"
    mu_static: float | None = None
    mu_kinetic: float | None = None


# Catalogue of swappable coupons. Coefficients start ``None`` on purpose: they
# are measured per workcell, not asserted by the design.
FRICTION_COUPONS: dict[str, FrictionCoupon] = {
    c.name: c
    for c in [
        FrictionCoupon("coupon_pla_smooth", "pla", 2.0, "steel_tabletop"),
        FrictionCoupon("coupon_tpu_grip", "pa12", 2.0, "steel_tabletop"),
        FrictionCoupon("coupon_pla_knurled", "pla", 2.5, "steel_tabletop"),
        FrictionCoupon("coupon_ptfe", "abs", 2.0, "steel_tabletop"),
    ]
}


def get_coupon(name: str) -> FrictionCoupon:
    """Look up a friction coupon by name."""
    try:
        return FRICTION_COUPONS[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(
            f"unknown coupon '{name}'; known: {sorted(FRICTION_COUPONS)}"
        ) from exc
