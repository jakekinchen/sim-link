"""STL export for the printable geometry.

Two paths, both deriving from the same primitive list so they cannot describe a
different solid than the physics model:

* :func:`write_primitive_soup` is pure-Python (numpy + stdlib) and always
  available. It writes the triangulated *positive external* solids as a preview
  proxy -- fast to open, not boolean-clean.
* :func:`write_watertight` uses trimesh + manifold3d when installed to perform
  the real union/difference and emit a single watertight mesh suitable for
  slicing. For a production print, prefer the parametric CAD (STEP) path in
  :mod:`build123d_cad`.
"""

from __future__ import annotations

import struct

from pathlib import Path

import numpy as np

from scenesmith.calibration.geometry import TargetGeometry
from scenesmith.calibration.primitives import Primitive

_INTERNAL = ("shell_cavity", "recess_", "guide_")


def _triangle_normals(tris: np.ndarray) -> np.ndarray:
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    n = np.cross(v1 - v0, v2 - v0)
    norms = np.linalg.norm(n, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return n / norms


def write_binary_stl(path: str | Path, triangles: np.ndarray) -> int:
    """Write a binary STL from an (T, 3, 3) triangle array. Returns triangle count."""
    tris = np.asarray(triangles, dtype=np.float32)
    normals = _triangle_normals(tris).astype(np.float32)
    count = len(tris)
    with open(path, "wb") as f:
        f.write(b"scenesmith calibration target".ljust(80, b" "))
        f.write(struct.pack("<I", count))
        for i in range(count):
            f.write(struct.pack("<3f", *normals[i]))
            for vertex in tris[i]:
                f.write(struct.pack("<3f", *vertex))
            f.write(struct.pack("<H", 0))
    return count


def write_primitive_soup(
    path: str | Path, primitives: list[Primitive], segments: int = 48
) -> int:
    """Write a preview STL of the positive external solids (proxy, not boolean)."""
    chunks = []
    for p in primitives:
        if p.density <= 0 or p.label.startswith(_INTERNAL):
            continue
        chunks.append(p.triangles(segments=segments))
    if not chunks:
        return 0
    return write_binary_stl(path, np.concatenate(chunks, axis=0))


def write_watertight(path: str | Path, geometry: TargetGeometry) -> bool:
    """Write a watertight shell via boolean ops if trimesh+manifold3d exist.

    Returns True on success, False if the optional dependencies are missing.
    """
    try:
        import trimesh
    except Exception:  # pragma: no cover - optional dependency
        return False

    from scenesmith.calibration.verify import primitive_to_trimesh

    segments = geometry.spec.triangulation_segments
    # Guide tubes stand *inside* the cavity void, so they must be unioned back
    # AFTER the cavity is subtracted -- otherwise the cavity cut deletes them.
    base, guides, negatives = [], [], []
    for p in geometry.shell_primitives:
        mesh = primitive_to_trimesh(p, segments=segments)
        if p.density < 0:
            negatives.append(mesh)
        elif p.label.startswith("guide_"):
            guides.append(mesh)
        else:
            base.append(mesh)

    solid = trimesh.boolean.union(base)
    if negatives:
        solid = trimesh.boolean.difference([solid, trimesh.boolean.union(negatives)])
    if guides:
        solid = trimesh.boolean.union([solid] + guides)
    # Coupons are separate bodies; append as-is for a printable preview.
    parts = [solid]
    for p in geometry.coupon_primitives:
        parts.append(
            primitive_to_trimesh(p, segments=geometry.spec.triangulation_segments)
        )
    combined = trimesh.util.concatenate(parts)
    combined.export(str(path))
    return True
