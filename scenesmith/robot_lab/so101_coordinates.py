"""Canonical SO-101 coordinate contract for SceneSmith robot-lab data."""

from __future__ import annotations

import math

from collections.abc import Sequence
from typing import Any


COORDINATE_SCHEMA_VERSION = "scenesmith.so101_coordinates.v1"
BODY_JOINT_SIGNS = (1.0, 1.0, 1.0, 1.0, 1.0)
BODY_JOINT_OFFSETS_DEG = (0.0, -105.85, 89.58, 0.0, 0.0)
GRIPPER_RANGE_RAD = (-0.17453, 1.74533)
MUJOCO_BODY_LIMITS_RAD = (
    (-1.91986, 1.91986),
    (-1.74533, 1.74533),
    (-1.69, 1.69),
    (-1.65806, 1.65806),
    (-2.74385, 2.84121),
)


def coordinate_contract(
    *,
    signs: Sequence[float] = BODY_JOINT_SIGNS,
    offsets_deg: Sequence[float] = BODY_JOINT_OFFSETS_DEG,
) -> dict[str, Any]:
    """Return JSON-compatible metadata that identifies the coordinate mapping."""

    normalized_signs, normalized_offsets = _validate_calibration(signs, offsets_deg)
    return {
        "schema_version": COORDINATE_SCHEMA_VERSION,
        "body_joint_signs": list(normalized_signs),
        "body_joint_offsets_deg": list(normalized_offsets),
        "gripper_range_rad": list(GRIPPER_RANGE_RAD),
        "mujoco_to_lerobot_formula": "lerobot_deg=(mujoco_deg-offset_deg)/sign",
        "lerobot_to_mujoco_formula": "mujoco_deg=lerobot_deg*sign+offset_deg",
    }


def mujoco_to_lerobot(
    values: Sequence[float],
    signs: Sequence[float] = BODY_JOINT_SIGNS,
    offsets_deg: Sequence[float] = BODY_JOINT_OFFSETS_DEG,
    *,
    round_digits: int | None = None,
) -> list[float]:
    """Convert six MuJoCo radians to calibrated LeRobot degrees/percent."""

    if len(values) < 6:
        raise ValueError("MuJoCo state/action must contain six joints")
    normalized_signs, normalized_offsets = _validate_calibration(signs, offsets_deg)
    body_degrees = [math.degrees(float(value)) for value in values[:5]]
    calibrated = [
        (value - offset) / sign
        for value, sign, offset in zip(
            body_degrees, normalized_signs, normalized_offsets, strict=True
        )
    ]
    low, high = GRIPPER_RANGE_RAD
    gripper = 100.0 * (float(values[5]) - low) / (high - low)
    result = [*calibrated, min(100.0, max(0.0, gripper))]
    if round_digits is not None:
        return [round(value, round_digits) for value in result]
    return result


def lerobot_to_mujoco(
    values: Sequence[float],
    signs: Sequence[float] = BODY_JOINT_SIGNS,
    offsets_deg: Sequence[float] = BODY_JOINT_OFFSETS_DEG,
    *,
    round_digits: int | None = None,
) -> list[float]:
    """Convert calibrated LeRobot degrees/percent to bounded MuJoCo radians."""

    if len(values) < 6:
        raise ValueError("LeRobot state/action must contain six joints")
    normalized_signs, normalized_offsets = _validate_calibration(signs, offsets_deg)
    body_degrees = [
        float(value) * sign + offset
        for value, sign, offset in zip(
            values[:5], normalized_signs, normalized_offsets, strict=True
        )
    ]
    body_radians = [
        min(high, max(low, math.radians(value)))
        for value, (low, high) in zip(body_degrees, MUJOCO_BODY_LIMITS_RAD, strict=True)
    ]
    low, high = GRIPPER_RANGE_RAD
    gripper_percent = min(100.0, max(0.0, float(values[5])))
    result = [*body_radians, low + (gripper_percent / 100.0) * (high - low)]
    if round_digits is not None:
        return [round(value, round_digits) for value in result]
    return result


def _validate_calibration(
    signs: Sequence[float], offsets_deg: Sequence[float]
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if len(signs) != 5 or len(offsets_deg) != 5:
        raise ValueError("SO-101 body calibration requires five signs and five offsets")
    normalized_signs = tuple(float(value) for value in signs)
    if any(value == 0.0 for value in normalized_signs):
        raise ValueError("SO-101 body joint signs must be non-zero")
    return normalized_signs, tuple(float(value) for value in offsets_deg)
