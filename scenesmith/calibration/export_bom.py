"""Bill of materials and fiducial coordinate tables.

The BOM lists every traceable mass contribution (net printed shell, each coupon,
each cartridge stack) so an as-built target can be reconciled part by part. The
fiducial table gives each AprilTag's exact pose in the body frame -- the input a
perception stack needs to turn a tag detection into a body pose.
"""

from __future__ import annotations

import csv

from pathlib import Path

import numpy as np

from scenesmith.calibration.configurations import ResolvedTarget
from scenesmith.calibration.frames import rotation_to_quaternion
from scenesmith.calibration.geometry import TargetGeometry

_G = 1e3  # kg -> g
_MM = 1e3  # m -> mm


def bom_rows(target: ResolvedTarget) -> list[dict]:
    """Return BOM rows (masses in grams, positions in mm)."""
    rows = []
    for part in target.parts:
        cx, cy, cz = (v * _MM for v in part.centroid_m)
        rows.append(
            {
                "part": part.label,
                "material": part.material,
                "quantity": part.quantity,
                "unit_mass_g": round(part.unit_mass_kg * _G, 4),
                "total_mass_g": round(part.total_mass_kg * _G, 4),
                "cx_mm": round(cx, 3),
                "cy_mm": round(cy, 3),
                "cz_mm": round(cz, 3),
            }
        )
    total = target.mass_properties.mass * _G
    com = target.com_mm
    rows.append(
        {
            "part": "TOTAL",
            "material": "-",
            "quantity": "",
            "unit_mass_g": "",
            "total_mass_g": round(total, 4),
            "cx_mm": round(float(com[0]), 3),
            "cy_mm": round(float(com[1]), 3),
            "cz_mm": round(float(com[2]), 3),
        }
    )
    return rows


def write_bom_csv(path: str | Path, target: ResolvedTarget) -> None:
    """Write the BOM to a CSV file."""
    rows = bom_rows(target)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fiducial_rows(geometry: TargetGeometry) -> list[dict]:
    """Return fiducial pose rows (position mm, quaternion w,x,y,z)."""
    rows = []
    for name, info in geometry.tag_frames.items():
        T = np.asarray(info["transform"])
        q = rotation_to_quaternion(T[:3, :3])
        pos = T[:3, 3] * _MM
        rows.append(
            {
                "name": name,
                "tag_id": info["tag_id"],
                "family": info["family"],
                "face": info["face"],
                "tag_size_mm": info["tag_size_mm"],
                "pos_x_mm": round(float(pos[0]), 3),
                "pos_y_mm": round(float(pos[1]), 3),
                "pos_z_mm": round(float(pos[2]), 3),
                "quat_w": round(float(q[0]), 6),
                "quat_x": round(float(q[1]), 6),
                "quat_y": round(float(q[2]), 6),
                "quat_z": round(float(q[3]), 6),
            }
        )
    return rows


def write_fiducial_csv(path: str | Path, geometry: TargetGeometry) -> None:
    """Write the fiducial coordinate table to a CSV file."""
    rows = fiducial_rows(geometry)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
