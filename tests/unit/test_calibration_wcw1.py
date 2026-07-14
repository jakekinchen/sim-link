"""Tests for the WCW-1 ball-cartridge design, receipt loop, and metrology."""

import numpy as np
import pytest

from scenesmith.calibration.receipt import (
    CalibrationArtifactReceipt,
    apply_receipt,
    blank_receipt,
)
from scenesmith.calibration.wcw1 import (
    build_wcw1_geometry,
    default_wcw1_target,
    resolve_wcw1,
    wcw1_kit,
)


@pytest.fixture(scope="module")
def spec():
    return default_wcw1_target()


@pytest.fixture(scope="module")
def geom(spec):
    return build_wcw1_geometry(spec)


@pytest.fixture(scope="module")
def targets(spec, geom):
    return {c.name: resolve_wcw1(spec, c, geometry=geom) for c in wcw1_kit(spec)}


def test_default_spec_validates_clean(spec):
    assert spec.validate() == []


def test_nominal_ball_mass_matches_52100_20mm(spec):
    # 20 mm AISI 52100 ball is ~32.7 g.
    assert spec.ball_mass_kg() * 1e3 == pytest.approx(32.7, abs=0.1)


def test_c1_c2_mass_matched_com_shifted(targets):
    c1, c2 = targets["C1"].mass_properties, targets["C2"].mass_properties
    assert c1.mass == pytest.approx(c2.mass, rel=1e-12)
    shift = (c2.com - c1.com) * 1e3
    # Net moved mass = ball minus its displaced seat void, so the CoM shift is
    # (m_ball - m_void) * 15mm / m_total -- about 3.7 mm, not the naive 4.4.
    assert shift[1] == pytest.approx(3.675, abs=0.05)
    assert abs(shift[0]) < 1e-9 and abs(shift[2]) < 1e-9


def test_c3_c4_isolate_pure_inertia(targets):
    c3, c4 = targets["C3"].mass_properties, targets["C4"].mass_properties
    # Same total mass AND same center of mass...
    assert c3.mass == pytest.approx(c4.mass, rel=1e-12)
    np.testing.assert_allclose(c3.com, c4.com, atol=1e-12)
    # ...but meaningfully larger inertia about the axes normal to y.
    i3 = np.sort(c3.principal_axes().moments)
    i4 = np.sort(c4.principal_axes().moments)
    assert i4[1] > 1.05 * i3[1]
    assert i4[2] > 1.05 * i3[2]


def test_all_configs_physically_valid(targets):
    for target in targets.values():
        assert target.mass_properties.is_physically_valid()


def test_grasp_face_tags_clear_contact_band(spec, geom):
    band_half = spec.contact_band_height_mm / 2.0
    for fid in spec.fiducials:
        if fid.face[1] != "x":
            continue
        pocket_half = (fid.tag_size_mm + 2 * fid.quiet_zone_mm) / 2.0
        assert fid.offset_mm[1] - pocket_half >= band_half
        # And the emitted frame reflects the offset.
        T = geom.tag_frames[fid.name]["transform"]
        assert T[2, 3] == pytest.approx(fid.offset_mm[1] * 1e-3)


def test_five_tags_none_on_bottom(geom):
    faces = [info["face"] for info in geom.tag_frames.values()]
    assert len(faces) == 5
    assert "-z" not in faces


def test_three_way_verification_passes_on_c4(targets):
    from scenesmith.calibration.verify import verify_all

    results = verify_all(targets["C4"], mc_samples=150_000)
    for result in results:
        if result.available:
            assert result.passed, result.summary()


def test_mjcf_has_sphere_geoms_and_exact_inertial(targets):
    pytest.importorskip("mujoco")
    import mujoco

    from scenesmith.calibration.export_mjcf import to_mjcf_string

    model = mujoco.MjModel.from_xml_string(to_mjcf_string(targets["C3"]))
    types = [int(t) for t in model.geom_type]
    assert types.count(int(mujoco.mjtGeom.mjGEOM_SPHERE)) == 2  # two balls
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "so101_wcw1_C3")
    assert model.body_mass[bid] == pytest.approx(
        targets["C3"].mass_properties.mass, rel=1e-9
    )


def test_receipt_roundtrip_and_apply(tmp_path, spec):
    receipt = blank_receipt(spec, "wcw1")
    receipt.body_mass_g = 40.5
    receipt.ball_measured_masses_g = [32.68, 32.71]
    path = tmp_path / "receipt.json"
    receipt.to_json(path)
    loaded = CalibrationArtifactReceipt.from_json(path)
    assert loaded.ball_grade == "G25"

    updated = apply_receipt(spec, loaded)
    geom = build_wcw1_geometry(spec)
    assert updated.shell_density() == pytest.approx(
        0.0405 / geom.shell_solid_volume(), rel=1e-9
    )
    assert updated.ball_mass_kg() * 1e3 == pytest.approx(32.695, rel=1e-9)


def test_bom_totals_match_composite(targets):
    for target in targets.values():
        part_sum = sum(p.total_mass_kg for p in target.parts)
        assert part_sum == pytest.approx(target.mass_properties.mass, rel=1e-9)


def test_metrology_parts_watertight_and_in_footprint():
    pytest.importorskip("trimesh")
    from scenesmith.calibration.metrology import build_depth_plate, build_grip_gauge

    plate, features = build_depth_plate()
    assert plate.is_watertight
    extents_mm = np.array(plate.extents) * 1e3
    assert extents_mm[0] <= 100.01 and extents_mm[1] <= 75.01
    kinds = {f["kind"] for f in features}
    assert {"plane", "step", "cylinder_vertical", "hemisphere"} <= kinds

    gauge, sections = build_grip_gauge()
    assert gauge.is_watertight
    assert [s["width_mm"] for s in sections] == [38.0, 40.0, 42.0]
