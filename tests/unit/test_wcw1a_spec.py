"""Deterministic contract tests for the WCW-1A printer package."""

import math

from scenesmith.robot_lab.wcw1a_spec import Wcw1aSpec


def test_wcw1a_frozen_geometry_and_coordinate_contract():
    spec = Wcw1aSpec()
    assert spec.body_dimensions_mm == (40.0, 60.0, 65.0)
    assert spec.coordinate_convention == {
        "origin": "outer_body_centroid",
        "x": "grasp_thickness_40mm",
        "y": "non_grasp_width_60mm",
        "z": "height_65mm_up",
    }
    assert spec.cartridge_frame_y_offset_mm == 0.0
    assert spec.configuration_seats_y_mm == {
        "C0": (),
        "C1": (0.0,),
        "C2": (15.0,),
        "C3": (-11.0, 11.0),
        "C4": (-15.0, 15.0),
    }


def test_wcw1a_uses_six_ordinary_nominal_20mm_balls():
    spec = Wcw1aSpec()
    assert spec.ball_nominal_diameter_mm == 20.0
    assert spec.ball_expected_range_mm == (19.8, 20.2)
    assert spec.ball_fit_allowance_diametral_mm == 0.8
    assert spec.ball_pocket_diameter_mm == 20.8
    assert math.isclose(spec.ball_pocket_diametral_clearance_nominal_mm, 0.8)
    assert math.isclose(spec.ball_pocket_diametral_clearance_at_max_ball_mm, 0.6)
    assert spec.total_balls_for_all_cartridges == 6


def test_wcw1a_printable_wall_and_assembly_clearances():
    spec = Wcw1aSpec()
    assert spec.body_wall_mm >= 2.4
    assert spec.body_roof_mm >= 2.8
    assert spec.minimum_ball_wall_mm >= 1.2 - 1e-9
    assert spec.cartridge_to_body_clearance_mm["x_minus"] >= 0.6
    assert spec.cartridge_to_body_clearance_mm["x_plus"] >= 1.0
    assert spec.cartridge_to_body_clearance_mm["y_each_side"] >= 0.4
    assert math.isclose(spec.lid_plug_clearance_each_side_mm, 0.35)
    assert spec.ball_retainer_preload_mm == 0.2
    assert spec.lid_crush_rib_interference_mm == 0.3
    assert spec.validate() == []


def test_wcw1a_tag_ids_sizes_and_grasp_clearance_are_unique_and_frozen():
    spec = Wcw1aSpec()
    assert [tag.tag_id for tag in spec.tags] == [0, 1, 2, 3, 4]
    assert len({tag.tag_id for tag in spec.tags}) == 5
    assert {tag.face for tag in spec.tags} == {"+z", "+y", "-y", "+x", "-x"}
    for tag in spec.tags:
        if tag.face in {"+x", "-x"}:
            assert tag.black_square_mm == 16.0
            assert tag.full_label_mm == 20.0
            assert tag.center_z_mm == 21.5
            assert tag.center_z_mm - tag.full_label_mm / 2.0 > spec.grasp_band_height_mm / 2.0
        else:
            assert tag.black_square_mm == 24.0
            assert tag.full_label_mm == 30.0


def test_wcw1a_pairwise_mass_experiment_intent_is_preserved():
    spec = Wcw1aSpec()
    seats = spec.configuration_seats_y_mm
    assert len(seats["C1"]) == len(seats["C2"]) == 1
    assert len(seats["C3"]) == len(seats["C4"]) == 2
    assert sum(seats["C3"]) == sum(seats["C4"]) == 0.0
    assert sum(y * y for y in seats["C4"]) > sum(y * y for y in seats["C3"])
