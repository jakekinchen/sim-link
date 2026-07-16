"""Contract tests for the WCW-1A Bambu batched plate definitions."""

from scenesmith.robot_lab.wcw1a_batched_plates import (
    PARTS,
    PLATES,
    PRODUCTION_PART_KEYS,
    orient_point,
    validate_plate_contract,
)


def test_primary_256mm_route_is_coupon_then_one_complete_production_plate():
    primary = next(plate for plate in PLATES if plate.key == "bambu_256_full_kit")
    coupon = next(plate for plate in PLATES if plate.key == "universal_coupon")
    assert [placement.part_key for placement in coupon.placements] == ["coupon"]
    assert tuple(placement.part_key for placement in primary.placements) == PRODUCTION_PART_KEYS
    assert len(primary.placements) == 12
    assert primary.bed_x_mm == primary.bed_y_mm == 256.0


def test_fallback_180mm_route_contains_every_part_exactly_once_in_four_jobs():
    plates = [plate for plate in PLATES if plate.route in {"universal_preflight", "fallback_180mm"}]
    assert len(plates) == 4
    keys = [placement.part_key for plate in plates for placement in plate.placements]
    assert keys.count("coupon") == 1
    for key in PRODUCTION_PART_KEYS:
        assert keys.count(key) == 1
    assert all(plate.bed_x_mm == plate.bed_y_mm == 180.0 for plate in plates)


def test_orientations_put_the_documented_face_toward_negative_build_z():
    point = (2.0, 3.0, 5.0)
    assert orient_point(point, "minus_z_face_down") == (2.0, 3.0, 5.0)
    assert orient_point(point, "top_face_down") == (2.0, -3.0, -5.0)
    assert orient_point(point, "minus_x_face_down") == (-5.0, 3.0, 2.0)
    assert orient_point(point, "plus_x_face_down") == (5.0, 3.0, -2.0)


def test_part_registry_and_plate_contract_are_complete():
    assert set(PARTS) == set(PRODUCTION_PART_KEYS) | {"coupon"}
    assert validate_plate_contract() == []
