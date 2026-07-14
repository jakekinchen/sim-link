"""Static metrology extras: the D405 depth plate and the grip-fit gauge.

These are *separate* printed parts, deliberately kept off the manipulable
body -- depth characterization wants spheres, cylinders, steps, and oblique
planes, while a graspable object wants flat faces and a flat sliding base.
The plate sits in the same fiducial frame as the body (or bolts beside it)
and is never used during dynamic manipulation.

Both generators require ``trimesh`` (with ``manifold3d`` for booleans) and are
skipped gracefully by the CLI when it is absent. Each part is emitted as a
watertight STL plus a JSON feature manifest (name, kind, parameters, pose) so a
depth-evaluation pipeline can register the CAD reference surface and score
per-feature bias, RMSE, valid-point density, and edge dropout -- reporting per
feature and incidence angle, never one collapsed "accuracy" number.
"""

from __future__ import annotations

import json

from pathlib import Path

import numpy as np

MM = 1e-3


def available() -> bool:
    """True if the trimesh-based generators can run."""
    try:
        import trimesh  # noqa: F401

        return True
    except Exception:  # pragma: no cover - optional dependency
        return False


def build_depth_plate(
    plate_xy_mm: tuple[float, float] = (100.0, 75.0),
    plate_thickness_mm: float = 6.0,
):
    """Build the D405 depth-metrology plate.

    Feature set follows open close-range RGB-D evaluation practice: a flat
    reference patch, 30 and 45 degree planes, a 10 mm step, vertical cylinders
    of two diameters, a horizontal half-cylinder, and a hemisphere -- because
    planes alone do not characterize manipulation-relevant depth behavior, and
    cylinder orientation relative to stereo epipolar geometry matters.

    Returns:
        (mesh, features): a watertight ``trimesh.Trimesh`` in meters, and the
        feature-manifest list of dicts (positions in mm, plate frame, origin at
        plate center, +z up from the plate surface).
    """
    import trimesh

    px, py = plate_xy_mm
    t = plate_thickness_mm
    parts = []
    features: list[dict] = []

    def add(mesh, name, kind, pos_mm, **params):
        mesh.apply_translation(np.asarray(pos_mm, dtype=float) * MM)
        parts.append(mesh)
        features.append({"name": name, "kind": kind, "pos_mm": list(pos_mm), **params})

    # Base plate; its top surface is z=0 in the feature frame.
    base = trimesh.creation.box(extents=[px * MM, py * MM, t * MM])
    base.apply_translation([0, 0, -t / 2 * MM])
    parts.append(base)
    features.append(
        {
            "name": "plane_0deg",
            "kind": "plane",
            "pos_mm": [-30.0, -22.0, 0.0],
            "incidence_deg": 0,
            "patch_mm": [30, 25],
            "note": "flat region of the base plate itself",
        }
    )

    def wedge(angle_deg, name, pos):
        # A tilted box whose top face presents the oblique plane.
        box = trimesh.creation.box(extents=[24 * MM, 20 * MM, 4 * MM])
        rot = trimesh.transformations.rotation_matrix(np.radians(angle_deg), [0, 1, 0])
        box.apply_transform(rot)
        # Sink so the lowest corner is below the surface (embedded on union).
        z_lift = -float(box.bounds[0][2]) - 1.5 * MM
        box.apply_translation([0, 0, z_lift])
        add(box, name, "plane", pos, incidence_deg=angle_deg, patch_mm=[24, 20])

    wedge(30, "plane_30deg", (5.0, -22.0, 0.0))
    wedge(45, "plane_45deg", (35.0, -22.0, 0.0))

    step = trimesh.creation.box(extents=[24 * MM, 20 * MM, 10 * MM])
    step.apply_translation([0, 0, 5 * MM])
    add(step, "step_10mm", "step", (-33.0, 5.0, 0.0), height_mm=10)

    for dia, name, pos in [
        (12.0, "cylinder_v12", (-8.0, 5.0, 0.0)),
        (24.0, "cylinder_v24", (18.0, 8.0, 0.0)),
    ]:
        cyl = trimesh.creation.cylinder(radius=dia / 2 * MM, height=20 * MM)
        cyl.apply_translation([0, 0, 10 * MM])
        add(cyl, name, "cylinder_vertical", pos, diameter_mm=dia, height_mm=20)

    # Horizontal half-cylinder: axis along x at the plate surface.
    half = trimesh.creation.cylinder(radius=11 * MM, height=30 * MM)
    half.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    add(
        half,
        "halfcylinder_h22",
        "cylinder_horizontal",
        (-15.0, 26.0, 0.0),
        diameter_mm=22,
        length_mm=30,
        note="lower half embedded in plate",
    )

    hemi = trimesh.creation.icosphere(radius=14 * MM, subdivisions=3)
    add(hemi, "hemisphere_28", "hemisphere", (30.0, 22.0, 0.0), diameter_mm=28)

    mesh = trimesh.boolean.union(parts)
    return mesh, features


def build_grip_gauge(
    widths_mm: tuple[float, ...] = (38.0, 40.0, 42.0),
    section_height_mm: float = 12.0,
    depth_mm: float = 20.0,
):
    """Build the stepped grip-width fit coupon.

    A cheap pre-print that answers "can the gripper actually span 40 mm?"
    empirically instead of trusting vendor CAD: stacked sections of the given
    widths; close the gripper on each and record which fit.

    Returns:
        (mesh, features) like :func:`build_depth_plate`.
    """
    import trimesh

    parts = []
    features = []
    z = 0.0
    for width in widths_mm:
        box = trimesh.creation.box(
            extents=[width * MM, depth_mm * MM, section_height_mm * MM]
        )
        box.apply_translation([0, 0, (z + section_height_mm / 2) * MM])
        parts.append(box)
        features.append(
            {
                "name": f"grip_{width:g}mm",
                "kind": "grip_section",
                "width_mm": width,
                "z_center_mm": z + section_height_mm / 2,
            }
        )
        z += section_height_mm
    mesh = trimesh.boolean.union(parts)
    return mesh, features


def export_metrology(out_dir: str | Path) -> list[str]:
    """Write the depth plate and grip gauge STLs + manifests into ``out_dir``.

    Returns the list of written filenames (empty if trimesh is missing).
    """
    if not available():
        return []
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for build, stem in [
        (build_depth_plate, "depth_plate"),
        (build_grip_gauge, "grip_gauge"),
    ]:
        mesh, features = build()
        stl_path = out / f"{stem}.stl"
        mesh.export(str(stl_path))
        manifest = out / f"{stem}_features.json"
        manifest.write_text(json.dumps(features, indent=2))
        written += [stl_path.name, manifest.name]
    return written
