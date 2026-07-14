"""Ground-truth bundle and acceptance sheet -- the sim <-> real link.

``calibration_target.json`` is the single machine-readable contract shared by the
physical workcell and its simulator twin: per-configuration mass, center of mass,
and inertia, plus every fiducial pose and the tag->CoM vectors that let a camera
localize the (invisible) center of mass. The acceptance sheet is its
human-readable companion: what to weigh, what to expect, and the pass/fail
tolerances for reconciling an as-built brick against the model.
"""

from __future__ import annotations

import json

from pathlib import Path

import numpy as np

from scenesmith.calibration.configurations import ResolvedTarget
from scenesmith.calibration.frames import rotation_to_quaternion
from scenesmith.calibration.geometry import TargetGeometry
from scenesmith.calibration.mass_properties import inertia_to_sixtuple
from scenesmith.calibration.materials import get_coupon
from scenesmith.calibration.spec import CalibrationTargetSpec

SCHEMA = "scenesmith.calibration/target/1"


def _com_in_frame(T: np.ndarray, com_body: np.ndarray) -> list[float]:
    """Express the body-frame CoM in a fiducial/grasp frame."""
    R, t = T[:3, :3], T[:3, 3]
    return (R.T @ (com_body - t)).tolist()


def _frames_block(geometry: TargetGeometry) -> dict:
    frames = {}
    for name, info in geometry.tag_frames.items():
        T = np.asarray(info["transform"])
        frames[f"tag_{name}"] = {
            "kind": "apriltag",
            "tag_id": info["tag_id"],
            "family": info["family"],
            "tag_size_m": info["tag_size_mm"] * 1e-3,
            "face": info["face"],
            "pos_m": T[:3, 3].tolist(),
            "quat_wxyz": rotation_to_quaternion(T[:3, :3]).tolist(),
            "transform": T.tolist(),
        }
    G = np.asarray(geometry.grasp_frame)
    frames["grasp"] = {
        "kind": "grasp",
        "pos_m": G[:3, 3].tolist(),
        "quat_wxyz": rotation_to_quaternion(G[:3, :3]).tolist(),
        "transform": G.tolist(),
    }
    return frames


def _config_block(target: ResolvedTarget, verify=None) -> dict:
    mp = target.mass_properties
    pa = mp.principal_axes()
    com = mp.com
    frames = target.geometry.tag_frames
    com_rel = {
        f"tag_{name}": _com_in_frame(np.asarray(info["transform"]), com)
        for name, info in frames.items()
    }
    com_rel["grasp"] = _com_in_frame(np.asarray(target.geometry.grasp_frame), com)

    block = {
        "description": target.config.description,
        "mass_kg": mp.mass,
        "com_m": com.tolist(),
        "inertia_com_kg_m2": mp.inertia_com.tolist(),
        "inertia_sixtuple": inertia_to_sixtuple(mp.inertia_com),
        "principal_moments_kg_m2": pa.moments.tolist(),
        "principal_axes": pa.rotation.tolist(),
        "physically_valid": bool(mp.is_physically_valid()),
        "com_relative_to_frames": com_rel,
        "cartridges": [
            {
                "socket": list(c.socket),
                "n_slugs": c.n_slugs,
                "material": c.material or target.spec.cartridge_material,
            }
            for c in target.config.cartridges
        ],
    }
    if verify is not None:
        block["verification"] = {
            r.method: {
                "available": r.available,
                "passed": r.passed,
                "mass_rel_err": r.mass_rel_err,
                "com_err_mm": r.com_err_mm,
                "inertia_rel_err": r.inertia_rel_err,
            }
            for r in verify
        }
    return block


def build_bundle(
    spec: CalibrationTargetSpec,
    targets: list[ResolvedTarget],
    verify_map: dict[str, list] | None = None,
) -> dict:
    """Assemble the ``calibration_target.json`` content."""
    geom = targets[0].geometry
    verify_map = verify_map or {}
    coupon_names = {m.coupon for m in spec.coupons}
    return {
        "schema": SCHEMA,
        "revision": spec.revision(),
        "spec_hash": spec.content_hash(),
        "units": {
            "length": "m",
            "mass": "kg",
            "inertia": "kg*m^2",
            "angle": "rad",
        },
        "spec": spec.to_dict(),
        "shell": {
            "material": spec.shell_material,
            "effective_density_kg_m3": spec.shell_density(),
            "solid_volume_m3": geom.shell_solid_volume(),
            "net_mass_kg": geom.shell_solid_volume() * spec.shell_density(),
            "note": "Weigh the bare printed shell and feed back via "
            "spec.with_measured_shell_mass() before trusting absolute mass.",
        },
        "frames": _frames_block(geom),
        "configurations": {
            t.config.name: _config_block(t, verify_map.get(t.config.name))
            for t in targets
        },
        "friction_coupons": {
            name: {
                "material": get_coupon(name).material,
                "thickness_mm": get_coupon(name).thickness_mm,
                "counter_surface": get_coupon(name).counter_surface,
                "mu_static": get_coupon(name).mu_static,
                "mu_kinetic": get_coupon(name).mu_kinetic,
                "note": "Friction is a pair property; measure per counter-surface.",
            }
            for name in sorted(coupon_names)
        },
        "tolerances": {
            "mass_g": spec.tolerances.mass_g,
            "com_mm": spec.tolerances.com_mm,
            "inertia_rel": spec.tolerances.inertia_rel,
        },
    }


def write_bundle(path: str | Path, bundle: dict) -> None:
    """Serialize the bundle as pretty JSON."""
    with open(path, "w") as f:
        json.dump(bundle, f, indent=2)


# --------------------------------------------------------------------------- #
# Human-readable acceptance sheet.
# --------------------------------------------------------------------------- #


def acceptance_markdown(
    spec: CalibrationTargetSpec,
    targets: list[ResolvedTarget],
    verify_map: dict[str, list] | None = None,
) -> str:
    """Render a printable QA / acceptance sheet."""
    verify_map = verify_map or {}
    geom = targets[0].geometry
    tol = spec.tolerances
    shell_mass_g = geom.shell_solid_volume() * spec.shell_density() * 1e3

    lines = [
        f"# Calibration Target Acceptance Sheet",
        "",
        f"- **Revision:** `{spec.revision()}`",
        f"- **Spec hash:** `{spec.content_hash()}`",
        f"- **Envelope (mm):** {spec.length_mm} x {spec.width_mm} x {spec.height_mm}"
        f", wall {spec.wall_mm}",
        f"- **Shell:** {spec.shell_material}, effective density "
        f"{spec.shell_density():.1f} kg/m^3 "
        f"(nominal infill {spec.nominal_infill:.0%})",
        f"- **Cartridge slug:** {spec.cartridge_material}, "
        f"d{spec.slug_diameter_mm} x {spec.slug_length_mm} mm, "
        f"{spec.slug_mass_kg()*1e3:.3f} g each (model)",
        "",
        "## 0. Print-density calibration (do this first)",
        "",
        f"1. Print the bare shell. Predicted net plastic mass: "
        f"**{shell_mass_g:.2f} g**.",
        "2. Weigh the bare shell (before bonding coupons) on a 0.01 g scale.",
        "3. Feed the reading back: "
        "`spec.with_measured_shell_mass(grams, shell.solid_volume_m3)` and "
        "regenerate. This replaces nominal infill density with the real value.",
        "4. Weigh each steel slug; if it differs from the model, use "
        "`spec.with_measured_slug_mass(grams)`.",
        "",
        "## 1. Configurations",
        "",
    ]

    for t in targets:
        if t.config.name == "bare":
            continue
        mp = t.mass_properties
        pa = mp.principal_axes()
        com = t.com_mm
        moments = pa.moments * 1e9  # kg*m^2 -> g*mm^2
        lines += [
            f"### `{t.config.name}` -- {t.config.description}",
            "",
            f"| Quantity | Model | Tolerance | As-built | Pass? |",
            f"|---|---|---|---|---|",
            f"| Mass (g) | {mp.mass*1e3:.3f} | +/-{tol.mass_g} | ______ | [ ] |",
            f"| CoM x (mm) | {com[0]:.3f} | +/-{tol.com_mm} | ______ | [ ] |",
            f"| CoM y (mm) | {com[1]:.3f} | +/-{tol.com_mm} | ______ | [ ] |",
            f"| CoM z (mm) | {com[2]:.3f} | +/-{tol.com_mm} | ______ | [ ] |",
            f"| I1 (g mm^2) | {moments[0]:.0f} | {tol.inertia_rel:.0%} | ______ | [ ] |",
            f"| I2 (g mm^2) | {moments[1]:.0f} | {tol.inertia_rel:.0%} | ______ | [ ] |",
            f"| I3 (g mm^2) | {moments[2]:.0f} | {tol.inertia_rel:.0%} | ______ | [ ] |",
            "",
        ]
        verify = verify_map.get(t.config.name)
        if verify:
            lines.append(
                "Cross-checks (model self-consistency): "
                + "; ".join(r.summary().strip() for r in verify if r.available)
            )
            lines.append("")

    lines += [
        "## 2. Independent verification procedures",
        "",
        "- **CoM (planar):** balance the brick on a narrow edge / suspend from "
        "two points; the plumb lines intersect at the CoM. Compare to CoM x,y.",
        "- **CoM (vertical):** suspend from a corner in two orientations; "
        "intersect the plumb lines.",
        "- **Inertia (optional):** a bifilar (two-wire) torsional pendulum gives "
        "the yaw moment I3 from the oscillation period; compare within tolerance.",
        "- **Mass:** direct scale reading equals the TOTAL row of the BOM.",
        "",
        "## 3. Fiducials",
        "",
        "| Tag | ID | Family | Face | Size (mm) |",
        "|---|---|---|---|---|",
    ]
    for name, info in geom.tag_frames.items():
        lines.append(
            f"| {name} | {info['tag_id']} | {info['family']} | {info['face']} "
            f"| {info['tag_size_mm']} |"
        )
    lines += [
        "",
        "Exact tag poses (and tag->CoM vectors for each configuration) are in "
        "`calibration_target.json` and `fiducials.csv`.",
        "",
    ]
    return "\n".join(lines)
