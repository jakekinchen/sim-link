"""Analytic mass properties and triangulations for primitive solids.

Every geometric feature of the calibration target reduces to an axis-aligned
box, a cylinder along a principal axis, an annular tube, or a sphere. For each
we know the closed-form mass, centroid inertia, an exact point-membership test
(used by the Monte-Carlo verifier), and a surface triangulation (used by the
STL exporter). Keeping all four in one place guarantees the physics model, the
independent check, and the printed mesh describe the *same* solid.

Axes are indexed 0=x, 1=y, 2=z. All inputs are SI (meters, kg/m**3).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from scenesmith.calibration.mass_properties import MassProperties


class Axis(Enum):
    """Principal axis a cylinder/tube is extruded along."""

    X = 0
    Y = 1
    Z = 2


@dataclass(frozen=True)
class Primitive:
    """A signed primitive solid placed in the body frame.

    Attributes:
        kind: One of ``box``, ``cylinder``, ``tube``, ``sphere``.
        center: Centroid position (m) in the body frame.
        params: Shape parameters (see the factory functions below).
        density: Material density (kg/m**3). Negative densities are used to
            carve cavities out of a parent solid via superposition.
        label: Human-readable name used in the BOM and traceability report.
    """

    kind: str
    center: np.ndarray
    params: dict
    density: float
    label: str = ""

    @property
    def volume(self) -> float:
        """Signed volume (m**3); negative for a subtracted region."""
        p = self.params
        sign = -1.0 if self.density < 0 else 1.0
        if self.kind == "box":
            vol = p["dx"] * p["dy"] * p["dz"]
        elif self.kind == "cylinder":
            vol = np.pi * p["radius"] ** 2 * p["length"]
        elif self.kind == "tube":
            vol = np.pi * (p["radius"] ** 2 - p["inner_radius"] ** 2) * p["length"]
        elif self.kind == "sphere":
            vol = 4.0 / 3.0 * np.pi * p["radius"] ** 3
        else:  # pragma: no cover - guarded by factories
            raise ValueError(f"unknown primitive kind: {self.kind}")
        return sign * vol

    @property
    def mass(self) -> float:
        """Signed mass (kg). ``density`` already carries the sign."""
        return abs(self.volume) * self.density

    def mass_properties(self) -> MassProperties:
        """Exact :class:`MassProperties` about the body-frame origin."""
        m = self.mass
        inertia_c = self._inertia_centroid(m)
        return MassProperties.from_centroid(m, self.center, inertia_c)

    def _inertia_centroid(self, mass: float) -> np.ndarray:
        p = self.params
        if self.kind == "box":
            a, b, c = p["dx"], p["dy"], p["dz"]
            ixx = mass / 12.0 * (b * b + c * c)
            iyy = mass / 12.0 * (a * a + c * c)
            izz = mass / 12.0 * (a * a + b * b)
            return np.diag([ixx, iyy, izz])
        if self.kind in ("cylinder", "tube"):
            r_out = p["radius"]
            r_in = p.get("inner_radius", 0.0)
            h = p["length"]
            axial = 0.5 * mass * (r_out * r_out + r_in * r_in)
            trans = mass / 12.0 * (3.0 * (r_out * r_out + r_in * r_in) + h * h)
            axis = p["axis"]
            diag = [trans, trans, trans]
            diag[axis] = axial
            return np.diag(diag)
        if self.kind == "sphere":
            r = p["radius"]
            i = 0.4 * mass * r * r
            return np.diag([i, i, i])
        raise ValueError(f"unknown primitive kind: {self.kind}")  # pragma: no cover

    def contains(self, points: np.ndarray) -> np.ndarray:
        """Vectorized point-membership test in the primitive's solid region.

        Args:
            points: (N, 3) array of body-frame points (m).

        Returns:
            (N,) boolean array, True where a point lies inside the (unsigned)
            solid region -- the sign of ``density`` is applied by the caller.
        """
        pts = np.asarray(points, dtype=float) - self.center
        p = self.params
        if self.kind == "box":
            half = np.array([p["dx"], p["dy"], p["dz"]]) / 2.0
            return np.all(np.abs(pts) <= half, axis=1)
        if self.kind in ("cylinder", "tube"):
            axis = p["axis"]
            radial = np.delete(pts, axis, axis=1)
            r2 = np.sum(radial * radial, axis=1)
            within_len = np.abs(pts[:, axis]) <= p["length"] / 2.0
            r_in = p.get("inner_radius", 0.0)
            within_r = (r2 <= p["radius"] ** 2) & (r2 >= r_in * r_in)
            return within_len & within_r
        if self.kind == "sphere":
            return np.sum(pts * pts, axis=1) <= p["radius"] ** 2
        raise ValueError(f"unknown primitive kind: {self.kind}")  # pragma: no cover

    def triangles(self, segments: int = 48) -> np.ndarray:
        """Surface triangulation for STL/preview export.

        Args:
            segments: Angular resolution for round primitives.

        Returns:
            (T, 3, 3) array of triangle vertices in the body frame.
        """
        if self.kind == "box":
            return _box_triangles(self.center, self.params)
        if self.kind in ("cylinder", "tube"):
            return _cylinder_triangles(self.center, self.params, segments)
        if self.kind == "sphere":
            return _sphere_triangles(self.center, self.params, segments)
        raise ValueError(f"unknown primitive kind: {self.kind}")  # pragma: no cover


def box(center, dx: float, dy: float, dz: float, density: float, label: str = ""):
    """Axis-aligned box of full extents (dx, dy, dz)."""
    return Primitive(
        "box", np.asarray(center, float), {"dx": dx, "dy": dy, "dz": dz}, density, label
    )


def cylinder(center, radius, length, axis: Axis, density, label: str = ""):
    """Solid cylinder of the given radius/length extruded along ``axis``."""
    return Primitive(
        "cylinder",
        np.asarray(center, float),
        {"radius": radius, "length": length, "axis": axis.value},
        density,
        label,
    )


def tube(center, radius, inner_radius, length, axis: Axis, density, label: str = ""):
    """Annular tube (hollow cylinder) extruded along ``axis``."""
    return Primitive(
        "tube",
        np.asarray(center, float),
        {
            "radius": radius,
            "inner_radius": inner_radius,
            "length": length,
            "axis": axis.value,
        },
        density,
        label,
    )


def sphere(center, radius, density, label: str = ""):
    """Solid sphere."""
    return Primitive(
        "sphere", np.asarray(center, float), {"radius": radius}, density, label
    )


# --------------------------------------------------------------------------- #
# Triangulation helpers (body-frame vertices).
# --------------------------------------------------------------------------- #

_BOX_FACES = [
    # (fixed axis, sign, in-plane axes) -> two triangles per face.
    (0, +1, (1, 2)),
    (0, -1, (1, 2)),
    (1, +1, (0, 2)),
    (1, -1, (0, 2)),
    (2, +1, (0, 1)),
    (2, -1, (0, 1)),
]


def _box_triangles(center, p) -> np.ndarray:
    half = np.array([p["dx"], p["dy"], p["dz"]]) / 2.0
    tris = []
    for fixed, sign, (u, v) in _BOX_FACES:
        base = np.zeros(3)
        base[fixed] = sign * half[fixed]
        corners = []
        for su, sv in [(-1, -1), (+1, -1), (+1, +1), (-1, +1)]:
            corner = base.copy()
            corner[u] = su * half[u]
            corner[v] = sv * half[v]
            corners.append(corner)
        c0, c1, c2, c3 = corners
        # Wind so the normal points outward (+sign along the fixed axis).
        if sign > 0:
            tris.append([c0, c1, c2])
            tris.append([c0, c2, c3])
        else:
            tris.append([c0, c2, c1])
            tris.append([c0, c3, c2])
    return np.asarray(tris) + center


def _cylinder_triangles(center, p, segments) -> np.ndarray:
    axis = p["axis"]
    r_out = p["radius"]
    r_in = p.get("inner_radius", 0.0)
    h = p["length"]
    u, v = [a for a in range(3) if a != axis]
    theta = np.linspace(0.0, 2.0 * np.pi, segments, endpoint=False)
    tris = []

    def pt(radius, ang, along):
        q = np.zeros(3)
        q[u] = radius * np.cos(ang)
        q[v] = radius * np.sin(ang)
        q[axis] = along
        return q

    for i in range(segments):
        a0, a1 = theta[i], theta[(i + 1) % segments]
        top, bot = h / 2.0, -h / 2.0
        # Outer wall.
        o00, o10 = pt(r_out, a0, bot), pt(r_out, a1, bot)
        o01, o11 = pt(r_out, a0, top), pt(r_out, a1, top)
        tris += [[o00, o10, o11], [o00, o11, o01]]
        if r_in > 0.0:
            i00, i10 = pt(r_in, a0, bot), pt(r_in, a1, bot)
            i01, i11 = pt(r_in, a0, top), pt(r_in, a1, top)
            # Inner wall (reversed winding).
            tris += [[i00, i11, i10], [i00, i01, i11]]
            # Annular caps.
            tris += [[o01, o11, i11], [o01, i11, i01]]  # top
            tris += [[o00, i10, o10], [o00, i00, i10]]  # bottom
        else:
            cap_top, cap_bot = pt(0.0, 0.0, top), pt(0.0, 0.0, bot)
            tris += [[o01, o11, cap_top]]
            tris += [[o10, o00, cap_bot]]
    return np.asarray(tris) + center


def _sphere_triangles(center, p, segments) -> np.ndarray:
    r = p["radius"]
    n_lat = max(4, segments // 2)
    lat = np.linspace(0.0, np.pi, n_lat + 1)
    lon = np.linspace(0.0, 2.0 * np.pi, segments, endpoint=False)
    tris = []

    def pt(theta, phi):
        return np.array(
            [
                r * np.sin(theta) * np.cos(phi),
                r * np.sin(theta) * np.sin(phi),
                r * np.cos(theta),
            ]
        )

    for i in range(n_lat):
        for j in range(segments):
            t0, t1 = lat[i], lat[i + 1]
            p0, p1 = lon[j], lon[(j + 1) % segments]
            a, b, c, d = pt(t0, p0), pt(t0, p1), pt(t1, p1), pt(t1, p0)
            tris += [[a, b, c], [a, c, d]]
    return np.asarray(tris) + center
