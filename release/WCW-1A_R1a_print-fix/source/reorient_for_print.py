#!/usr/bin/env python3
"""Bake the documented print orientations into the WCW-1A STLs (R1 -> R1a).

Root cause of R1's orientation bug: ``wcw1a_cad.py`` exports every part in
body-frame coordinates and only the *filename* records the intended print
orientation ("exterior-face-down", "top-down", ...). The rotation was never
applied to the mesh, and the 3MF plates ship identity transforms too -- so
parts load standing on edge (see Zane's 2026-07-17 report and screenshot in
``docs/wcw-1a-print-correspondence/``).

This script is the missing export step. For each R1 STL it applies the
orientation its own filename and README_PRINTING.md declare, drops the part to
z=0, centers it in XY, and writes the result as an ``R1a`` STL. The transform
is a rigid rotation + translation: triangle count and volume are preserved
exactly, so every R1 validation of geometry still holds for R1a.

Documented orientations (verified against the R1 geometry by cross-section:
the retainer's flat face is +x with spring bosses at -x, the carrier's closed
face is -x, the body's closed tag face is +z, the lid's flat outer face is -z):

* body_top-down            -> rotate 180 deg about X (+z tag face to the bed;
                              open bottom up; avoids bridging the cavity roof)
* carrier_..-x-face-down   -> rotate -90 deg about Y (-x closed face to the
                              bed; ball wells and rails become vertical)
* ball-retainer_exterior.. -> rotate +90 deg about Y (+x flat exterior face to
                              the bed; spring bosses up)
* bottom-lid_outer-face..  -> identity (outer face is already -z)
* ball-fit-coupon          -> identity (already flat, labels up)

Requires numpy + trimesh only. Run from anywhere:

    python reorient_for_print.py [--src <R1 stl dir>] [--out <R1a stl dir>]
"""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

import numpy as np
import trimesh

_DEFAULT_SRC = Path(__file__).resolve().parents[2] / "WCW-1A_print_package" / "stl"
_DEFAULT_OUT = Path(__file__).resolve().parents[1] / "stl"

_COS_OVERHANG = np.cos(np.radians(45.0))
_BED_EPS_MM = 0.3


def _rot_x(deg: float) -> np.ndarray:
    transform = trimesh.transformations.rotation_matrix(np.radians(deg), [1, 0, 0])
    return transform


def _rot_y(deg: float) -> np.ndarray:
    return trimesh.transformations.rotation_matrix(np.radians(deg), [0, 1, 0])


def print_transform_for(filename: str) -> np.ndarray:
    """Return the 4x4 print transform a WCW-1A part's filename declares."""
    if "body_top-down" in filename:
        return _rot_x(180.0)
    if "carrier_print-minus-x-face-down" in filename:
        return _rot_y(-90.0)
    if "ball-retainer_exterior-face-down" in filename:
        return _rot_y(90.0)
    if "bottom-lid_outer-face-down" in filename or "ball-fit-coupon" in filename:
        return np.eye(4)
    raise ValueError(f"no documented print orientation for: {filename}")


def overhang_report(mesh: trimesh.Trimesh) -> tuple[float, float]:
    """Return (bed contact area mm^2, unsupported >45deg downward area mm^2)."""
    normals = mesh.face_normals
    areas = mesh.area_faces
    centers = mesh.triangles_center
    down = normals[:, 2] < -_COS_OVERHANG
    on_bed = centers[:, 2] < (mesh.bounds[0][2] + _BED_EPS_MM)
    bed_area = float(areas[down & on_bed].sum())
    overhang_area = float(areas[down & ~on_bed].sum())
    return bed_area, overhang_area


def reorient(src: Path, out: Path) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    for path in sorted(src.glob("*.stl")):
        mesh = trimesh.load(path, force="mesh")
        original_volume = float(mesh.volume)
        original_faces = len(mesh.faces)

        mesh.apply_transform(print_transform_for(path.name))
        # Bed placement: z=0, XY centered.
        minimum, maximum = mesh.bounds
        center = (minimum + maximum) / 2.0
        mesh.apply_translation([-center[0], -center[1], -minimum[2]])

        if not mesh.is_watertight:
            raise RuntimeError(f"{path.name}: not watertight after transform")
        if len(mesh.faces) != original_faces:
            raise RuntimeError(f"{path.name}: triangle count changed")
        if abs(float(mesh.volume) - original_volume) > 1e-6 * abs(original_volume):
            raise RuntimeError(f"{path.name}: volume changed")

        bed_area, overhang_area = overhang_report(mesh)
        out_name = path.name.replace("_R1_", "_R1a_")
        mesh.export(str(out / out_name))
        extents = np.round(mesh.extents, 2).tolist()
        reports.append(
            {
                "file": out_name,
                "extents_mm": extents,
                "bed_contact_mm2": round(bed_area, 1),
                "overhang45_mm2": round(overhang_area, 1),
            }
        )
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=_DEFAULT_SRC)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()

    reports = reorient(args.src, args.out)
    width = max(len(r["file"]) for r in reports)
    for r in reports:
        print(
            f"{r['file']:{width}s}  ext={r['extents_mm']}  "
            f"bed={r['bed_contact_mm2']:8.1f} mm^2  "
            f"overhang>45={r['overhang45_mm2']:7.1f} mm^2"
        )
    print(f"\n{len(reports)} STLs written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
