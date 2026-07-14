"""Tests for MJCF/URDF/STL/BOM/bundle exporters."""

import struct
import xml.etree.ElementTree as ET

import numpy as np
import pytest

from scenesmith.calibration import default_so101_target, resolve_target, standard_kit
from scenesmith.calibration.export_bom import bom_rows, fiducial_rows
from scenesmith.calibration.export_mjcf import to_mjcf_string
from scenesmith.calibration.export_stl import write_primitive_soup
from scenesmith.calibration.export_urdf import to_urdf_string
from scenesmith.calibration.geometry import build_geometry
from scenesmith.calibration.report import build_bundle


@pytest.fixture(scope="module")
def spec():
    return default_so101_target()


@pytest.fixture(scope="module")
def geom(spec):
    return build_geometry(spec)


@pytest.fixture(scope="module")
def targets(spec, geom):
    return [resolve_target(spec, c, geometry=geom) for c in standard_kit(spec)]


@pytest.fixture(scope="module")
def offset(targets):
    return next(t for t in targets if t.config.name == "offset")


def test_mjcf_is_wellformed_with_matching_inertial(offset):
    root = ET.fromstring(to_mjcf_string(offset))
    inertial = root.find(".//inertial")
    assert inertial is not None
    mass = float(inertial.attrib["mass"])
    assert mass == pytest.approx(offset.mass_properties.mass, rel=1e-9)
    # fullinertia has six components.
    assert len(inertial.attrib["fullinertia"].split()) == 6
    # Named sites for each tag, grasp, and CoM exist.
    site_names = {s.attrib["name"] for s in root.iter("site")}
    assert {"tag_top", "tag_side_x", "tag_side_y", "grasp", "com"} <= site_names


def test_mjcf_scene_has_freejoint_and_floor(offset):
    root = ET.fromstring(to_mjcf_string(offset, include_scene=True, freejoint=True))
    assert root.find(".//freejoint") is not None
    assert any(g.attrib.get("type") == "plane" for g in root.iter("geom"))


def test_urdf_is_wellformed_with_frames(offset):
    root = ET.fromstring(to_urdf_string(offset))
    assert root.tag == "robot"
    inertia = root.find(".//link[@name='base']/inertial/inertia")
    assert inertia is not None
    link_names = {ln.attrib["name"] for ln in root.iter("link")}
    assert {"base", "tag_top", "grasp"} <= link_names


def test_binary_stl_parses_with_declared_triangle_count(tmp_path, offset):
    path = tmp_path / "preview.stl"
    n = write_primitive_soup(path, offset.all_primitives, segments=24)
    data = path.read_bytes()
    (count,) = struct.unpack("<I", data[80:84])
    assert count == n > 0
    assert len(data) == 84 + count * 50  # 50 bytes per triangle


def test_bom_rows_sum_to_total(offset):
    rows = bom_rows(offset)
    total_row = rows[-1]
    assert total_row["part"] == "TOTAL"
    part_sum = sum(r["total_mass_g"] for r in rows[:-1])
    # Rows are rounded to 0.1 mg for display; allow rounding noise, not a
    # dropped part (which would be grams off).
    assert part_sum == pytest.approx(total_row["total_mass_g"], abs=1e-2)


def test_fiducial_rows_have_unit_quaternions(geom):
    rows = fiducial_rows(geom)
    assert len(rows) == 3
    for r in rows:
        q = np.array([r["quat_w"], r["quat_x"], r["quat_y"], r["quat_z"]])
        assert np.linalg.norm(q) == pytest.approx(1.0, abs=1e-4)


def test_bundle_has_expected_structure(spec, targets):
    bundle = build_bundle(spec, targets)
    assert bundle["schema"].startswith("scenesmith.calibration/target")
    assert bundle["units"]["mass"] == "kg"
    for name in ("centered", "offset", "high_inertia"):
        cfg = bundle["configurations"][name]
        assert "inertia_com_kg_m2" in cfg
        assert "com_relative_to_frames" in cfg
        # tag->CoM vector exists for every fiducial.
        assert "tag_top" in cfg["com_relative_to_frames"]
    assert bundle["revision"] == spec.revision()
