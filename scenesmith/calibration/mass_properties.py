"""Exact rigid-body mass-property algebra.

A calibration target is modeled as a superposition of *signed* rigid bodies:
solid plastic minus cavities (negative mass) plus steel cartridges. Every gram
is a labeled, traceable contribution. This module implements the exact algebra
that turns such a superposition into a single body's mass, center of mass, and
inertia tensor -- with no mesh engine required.

Conventions (SI):
    * mass in kilograms (may be negative for a subtracted region),
    * lengths / centroids in meters,
    * inertia in kg * m**2.

Inertia is always tracked as a full 3x3 tensor expressed *about the reference
frame origin* in that frame's axes. Composition is then a plain sum, and the
inertia about the center of mass is recovered once via the parallel-axis
theorem. This ordering (accumulate about the origin, shift to the CoM at the
end) is what keeps signed superposition exact.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

_I3 = np.eye(3)


def parallel_axis(
    inertia_about_centroid: np.ndarray, mass: float, offset: np.ndarray
) -> np.ndarray:
    """Shift an inertia tensor from a body's centroid to a displaced frame.

    Uses the parallel-axis (Huygens-Steiner) theorem in tensor form::

        I_offset = I_centroid + mass * (|d|**2 * I3 - d d^T)

    where ``d`` is the vector from the new reference point to the centroid.
    Works unchanged for negative ``mass`` (subtracted regions).

    Args:
        inertia_about_centroid: 3x3 inertia tensor about the body's own centroid.
        mass: Signed mass in kg.
        offset: Vector (m) from the target reference point to the centroid.

    Returns:
        3x3 inertia tensor about the target reference point.
    """
    d = np.asarray(offset, dtype=float)
    steiner = mass * (float(d @ d) * _I3 - np.outer(d, d))
    return np.asarray(inertia_about_centroid, dtype=float) + steiner


@dataclass(frozen=True)
class MassProperties:
    """Mass, center of mass, and inertia of a (possibly signed) rigid body.

    The inertia tensor is stored about the *reference-frame origin*, not the
    center of mass. This makes :meth:`combine` a simple additive operation.
    Use :attr:`inertia_com` for the center-of-mass tensor that URDF/MJCF/SDF
    expect.

    Attributes:
        mass: Signed mass in kg.
        first_moment: Mass-weighted first moment ``mass * com`` (kg * m). Stored
            rather than the CoM directly so that combining bodies stays linear
            and remains well defined even when a subset sums to zero mass.
        inertia_origin: 3x3 inertia tensor (kg * m**2) about the frame origin.
    """

    mass: float
    first_moment: np.ndarray
    inertia_origin: np.ndarray

    @property
    def com(self) -> np.ndarray:
        """Center of mass (m) in the reference frame."""
        if abs(self.mass) < 1e-15:
            return np.zeros(3)
        return self.first_moment / self.mass

    @property
    def inertia_com(self) -> np.ndarray:
        """3x3 inertia tensor (kg * m**2) about the center of mass."""
        # Shift from origin to CoM: I_com = I_origin - m (|c|^2 I - c c^T).
        return parallel_axis(self.inertia_origin, -self.mass, self.com)

    @classmethod
    def zero(cls) -> "MassProperties":
        """The additive identity: zero mass, zero moment, zero inertia."""
        return cls(0.0, np.zeros(3), np.zeros((3, 3)))

    @classmethod
    def from_centroid(
        cls, mass: float, centroid: np.ndarray, inertia_centroid: np.ndarray
    ) -> "MassProperties":
        """Build from a primitive given about its own centroid.

        Args:
            mass: Signed mass in kg.
            centroid: Centroid position (m) in the reference frame.
            inertia_centroid: 3x3 inertia tensor about the centroid.

        Returns:
            A :class:`MassProperties` referenced to the frame origin.
        """
        c = np.asarray(centroid, dtype=float)
        inertia_origin = parallel_axis(inertia_centroid, mass, c)
        return cls(mass, mass * c, inertia_origin)

    def combine(self, other: "MassProperties") -> "MassProperties":
        """Superpose two bodies expressed in the same reference frame."""
        return MassProperties(
            self.mass + other.mass,
            self.first_moment + other.first_moment,
            self.inertia_origin + other.inertia_origin,
        )

    def __add__(self, other: "MassProperties") -> "MassProperties":
        return self.combine(other)

    def principal_axes(self) -> "PrincipalInertia":
        """Diagonalize the center-of-mass inertia tensor.

        Returns:
            A :class:`PrincipalInertia` with sorted principal moments and the
            rotation (columns are principal axes in the body frame).
        """
        eigvals, eigvecs = np.linalg.eigh(self.inertia_com)
        order = np.argsort(eigvals)
        eigvals = eigvals[order]
        eigvecs = eigvecs[:, order]
        # Force a right-handed frame (det = +1) so it is a valid rotation.
        if np.linalg.det(eigvecs) < 0:
            eigvecs[:, 0] = -eigvecs[:, 0]
        return PrincipalInertia(moments=eigvals, rotation=eigvecs)

    def is_physically_valid(self, rel_tol: float = 1e-6) -> bool:
        """Check positive-definiteness and the inertia triangle inequality.

        A real solid's principal moments are positive and obey
        ``I_i + I_j >= I_k`` for every permutation. A composed target that
        violates this signals a modeling error (e.g. a cavity larger than its
        parent), so the check is a cheap correctness guard.

        Args:
            rel_tol: Relative slack applied to the triangle inequality to absorb
                floating-point noise.

        Returns:
            True if the body could be a physically realizable rigid body.
        """
        if self.mass <= 0:
            return False
        moments = self.principal_axes().moments
        if np.any(moments <= 0):
            return False
        i1, i2, i3 = moments
        scale = i3 * (1.0 + rel_tol)
        return (i1 + i2) >= i3 - rel_tol * scale


@dataclass(frozen=True)
class PrincipalInertia:
    """Principal moments of inertia and their body-frame orientation.

    Attributes:
        moments: Sorted principal moments ``[I1, I2, I3]`` with ``I1 <= I2 <= I3``
            (kg * m**2).
        rotation: 3x3 rotation whose columns are the principal axes expressed in
            the body frame (det = +1).
    """

    moments: np.ndarray
    rotation: np.ndarray = field(default_factory=lambda: np.eye(3))


def combine_all(bodies) -> MassProperties:
    """Superpose an iterable of :class:`MassProperties` in a shared frame."""
    total = MassProperties.zero()
    for body in bodies:
        total = total.combine(body)
    return total


def inertia_to_sixtuple(inertia: np.ndarray) -> dict:
    """Extract the 6 unique symmetric components (URDF/SDF/MJCF ordering).

    Returns:
        Dict with keys ``ixx, iyy, izz, ixy, ixz, iyz``.
    """
    i = np.asarray(inertia, dtype=float)
    return {
        "ixx": float(i[0, 0]),
        "iyy": float(i[1, 1]),
        "izz": float(i[2, 2]),
        "ixy": float(i[0, 1]),
        "ixz": float(i[0, 2]),
        "iyz": float(i[1, 2]),
    }
