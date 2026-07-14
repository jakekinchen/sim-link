"""Unit tests for the parametric spec, geometry, and cartridge configurations."""

import numpy as np
import pytest

from scenesmith.calibration import default_so101_target, resolve_target, standard_kit
from scenesmith.calibration.geometry import build_geometry


@pytest.fixture(scope="module")
def spec():
    return default_so101_target()


@pytest.fixture(scope="module")
def geom(spec):
    return build_geometry(spec)


def _by_name(spec, geom):
    return {c.name: resolve_target(spec, c, geometry=geom) for c in standard_kit(spec)}


def test_default_spec_validates_clean(spec):
    assert spec.validate() == []


def test_content_hash_is_deterministic_and_sensitive(spec):
    from dataclasses import replace

    assert spec.content_hash() == spec.content_hash()
    other = replace(spec, wall_mm=spec.wall_mm + 0.1)
    assert other.content_hash() != spec.content_hash()


def test_centered_and_high_inertia_are_mass_matched(spec, geom):
    t = _by_name(spec, geom)
    assert t["centered"].mass_properties.mass == pytest.approx(
        t["high_inertia"].mass_properties.mass, rel=1e-12
    )


def test_high_inertia_has_larger_principal_moments(spec, geom):
    t = _by_name(spec, geom)
    centered = np.sort(t["centered"].mass_properties.principal_axes().moments)
    spread = np.sort(t["high_inertia"].mass_properties.principal_axes().moments)
    # Same mass, weight moved outward -> every principal moment grows.
    assert np.all(spread > centered)


def test_offset_shifts_com_along_x(spec, geom):
    t = _by_name(spec, geom)
    centered_com = t["centered"].mass_properties.com
    offset_com = t["offset"].mass_properties.com
    assert offset_com[0] - centered_com[0] > 2e-3  # > 2 mm shift
    assert abs(offset_com[1] - centered_com[1]) < 1e-4  # y unchanged


def test_all_configs_physically_valid(spec, geom):
    for target in _by_name(spec, geom).values():
        assert target.mass_properties.is_physically_valid()


def test_bom_total_matches_composite_mass(spec, geom):
    target = _by_name(spec, geom)["offset"]
    part_sum = sum(p.total_mass_kg for p in target.parts)
    assert part_sum == pytest.approx(target.mass_properties.mass, rel=1e-9)


def test_measured_shell_mass_updates_effective_density(spec, geom):
    solid_vol = geom.shell_solid_volume()
    updated = spec.with_measured_shell_mass(50.0, solid_vol)
    assert updated.shell_density() == pytest.approx(0.050 / solid_vol, rel=1e-12)
    # And it changes the ground-truth shell mass accordingly.
    new_geom = build_geometry(updated)
    new_mass = new_geom.shell_solid_volume() * updated.shell_density()
    assert new_mass == pytest.approx(0.050, rel=1e-9)


def test_slug_measured_mass_overrides_density(spec):
    updated = spec.with_measured_slug_mass(3.5)
    assert updated.slug_mass_kg() == pytest.approx(3.5e-3, rel=1e-12)


def test_three_orthogonal_fiducials(geom):
    faces = {info["face"] for info in geom.tag_frames.values()}
    assert faces == {"+z", "+x", "+y"}
