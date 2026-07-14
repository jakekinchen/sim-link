"""Unit tests for the exact mass-property algebra and analytic primitives."""

import numpy as np
import pytest

from scenesmith.calibration import primitives as prim
from scenesmith.calibration.mass_properties import (
    MassProperties,
    combine_all,
    parallel_axis,
)
from scenesmith.calibration.primitives import Axis


def test_solid_box_inertia_matches_closed_form():
    a, b, c, rho = 0.10, 0.06, 0.046, 1200.0
    box = prim.box((0, 0, 0), a, b, c, rho, "b")
    mp = box.mass_properties()
    m = rho * a * b * c
    assert mp.mass == pytest.approx(m, rel=1e-12)
    expected = np.diag(
        [
            m / 12 * (b * b + c * c),
            m / 12 * (a * a + c * c),
            m / 12 * (a * a + b * b),
        ]
    )
    np.testing.assert_allclose(mp.inertia_com, expected, rtol=1e-12)


def test_parallel_axis_adds_steiner_term():
    a = b = c = 0.05
    rho = 1000.0
    m = rho * a * b * c
    d = np.array([0.02, 0.0, 0.0])
    box = prim.box(d, a, b, c, rho, "b")
    mp = box.mass_properties()
    # Izz about the origin gains m*d^2 relative to the centroidal value.
    izz_c = m / 12 * (a * a + b * b)
    assert mp.inertia_origin[2, 2] == pytest.approx(izz_c + m * d[0] ** 2, rel=1e-12)
    # And inertia_com recovers the centroidal tensor.
    np.testing.assert_allclose(
        mp.inertia_com, np.diag([izz_c, izz_c, izz_c]), rtol=1e-12
    )


def test_parallel_axis_sign_symmetry():
    inertia = np.diag([1.0, 2.0, 3.0])
    shifted = parallel_axis(inertia, 5.0, np.array([0.1, -0.2, 0.3]))
    back = parallel_axis(shifted, -5.0, np.array([0.1, -0.2, 0.3]))
    np.testing.assert_allclose(back, inertia, atol=1e-12)


def test_hollow_box_via_negative_mass_superposition():
    # A hollow box equals a solid box plus a negative-mass inner box.
    rho = 1300.0
    outer = prim.box((0, 0, 0), 0.08, 0.06, 0.05, rho, "o")
    inner = prim.box((0, 0, 0), 0.07, 0.05, 0.04, -rho, "i")
    hollow = combine_all([outer.mass_properties(), inner.mass_properties()])
    m_expected = rho * (0.08 * 0.06 * 0.05 - 0.07 * 0.05 * 0.04)
    assert hollow.mass == pytest.approx(m_expected, rel=1e-12)
    # Centered and symmetric -> CoM at origin, valid rigid body.
    np.testing.assert_allclose(hollow.com, np.zeros(3), atol=1e-12)
    assert hollow.is_physically_valid()


def test_cylinder_axial_vs_transverse_inertia():
    r, h, rho = 0.01, 0.04, 7850.0
    cyl = prim.cylinder((0, 0, 0), r, h, Axis.Z, rho, "c")
    mp = cyl.mass_properties()
    m = mp.mass
    np.testing.assert_allclose(mp.inertia_com[2, 2], 0.5 * m * r * r, rtol=1e-12)
    trans = m / 12 * (3 * r * r + h * h)
    np.testing.assert_allclose(mp.inertia_com[0, 0], trans, rtol=1e-12)
    np.testing.assert_allclose(mp.inertia_com[1, 1], trans, rtol=1e-12)


def test_principal_axes_sorted_and_orthonormal():
    box = prim.box((0, 0, 0), 0.10, 0.06, 0.04, 1000.0, "b")
    pa = box.mass_properties().principal_axes()
    assert pa.moments[0] <= pa.moments[1] <= pa.moments[2]
    np.testing.assert_allclose(pa.rotation @ pa.rotation.T, np.eye(3), atol=1e-10)
    assert np.linalg.det(pa.rotation) == pytest.approx(1.0, abs=1e-9)


def test_is_physically_valid_rejects_triangle_violation():
    bad = MassProperties(1.0, np.zeros(3), np.diag([10.0, 1.0, 1.0]))
    # I1+I2 = 2 < I3 = 10 -> not a physical rigid body.
    assert not bad.is_physically_valid()


def test_tube_equals_outer_minus_inner_cylinder():
    r_out, r_in, h, rho = 0.012, 0.008, 0.03, 2700.0
    tube = prim.tube((0, 0, 0), r_out, r_in, h, Axis.Z, rho, "t").mass_properties()
    outer = prim.cylinder((0, 0, 0), r_out, h, Axis.Z, rho, "o").mass_properties()
    inner = prim.cylinder((0, 0, 0), r_in, h, Axis.Z, rho, "i").mass_properties()
    ref = combine_all(
        [outer, MassProperties(-inner.mass, np.zeros(3), -inner.inertia_origin)]
    )
    assert tube.mass == pytest.approx(ref.mass, rel=1e-12)
    np.testing.assert_allclose(tube.inertia_com, ref.inertia_com, rtol=1e-12)
