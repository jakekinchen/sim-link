"""Cross-check tests: Monte-Carlo always; trimesh and MuJoCo when available."""

import numpy as np
import pytest

from scenesmith.calibration import default_so101_target, resolve_target, standard_kit
from scenesmith.calibration.geometry import build_geometry
from scenesmith.calibration.verify import (
    verify_montecarlo,
    verify_mujoco,
    verify_trimesh,
)


@pytest.fixture(scope="module")
def target():
    spec = default_so101_target()
    geom = build_geometry(spec)
    offset = next(c for c in standard_kit(spec) if c.name == "offset")
    return resolve_target(spec, offset, geometry=geom)


def test_montecarlo_agrees_with_analytic(target):
    result = verify_montecarlo(
        target,
        n_samples=120_000,
        seed=1,
        mass_tol=0.02,
        com_tol_mm=0.5,
        inertia_tol=0.05,
    )
    assert result.available and result.passed, result.summary()


def test_trimesh_agrees_with_analytic(target):
    pytest.importorskip("trimesh")
    result = verify_trimesh(target)
    assert result.available and result.passed, result.summary()
    assert result.mass_rel_err < 1e-3
    assert result.inertia_rel_err < 1e-3


def test_mujoco_roundtrip_matches_analytic(target):
    pytest.importorskip("mujoco")
    result = verify_mujoco(target)
    assert result.available and result.passed, result.summary()
    # A parse round-trip should be numerically exact.
    assert result.mass_rel_err < 1e-6
    assert result.inertia_rel_err < 1e-6


def test_montecarlo_matches_hollow_shell_mass(target):
    # Sanity: MC mass estimate close to analytic on the same field.
    result = verify_montecarlo(target, n_samples=120_000, seed=7)
    analytic = target.mass_properties.mass
    est = analytic * (1 + result.mass_rel_err)
    assert np.isfinite(est)
    assert result.mass_rel_err < 0.02
