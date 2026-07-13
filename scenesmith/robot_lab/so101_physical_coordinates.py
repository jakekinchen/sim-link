"""Candidate SO-101 physical-pose coordinates for offline diagnostics."""

from __future__ import annotations

import math

from collections.abc import Sequence
from typing import Any

from scenesmith.robot_lab.so101_coordinates import (
    GRIPPER_RANGE_RAD,
    MUJOCO_BODY_LIMITS_RAD,
)


MIDPOINT_DIRECT_CANDIDATE_SCHEMA_VERSION = (
    "scenesmith.so101_midpoint_direct_candidate.v1"
)
MIDPOINT_DIRECT_BODY_JOINT_SIGNS = (1.0, 1.0, 1.0, 1.0, 1.0)
MIDPOINT_DIRECT_BODY_JOINT_OFFSETS_DEG = (0.0, 0.0, 0.0, 0.0, 0.0)
BODY_JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
)


def midpoint_direct_candidate_contract() -> dict[str, Any]:
    """Describe the fail-closed direct mapping used only for offline diagnosis."""

    return {
        "schema_version": MIDPOINT_DIRECT_CANDIDATE_SCHEMA_VERSION,
        "status": "offline_diagnostic_candidate",
        "qualification_scope": "physical_pose_and_proposal_replay_diagnostic_only",
        "body_joint_signs": list(MIDPOINT_DIRECT_BODY_JOINT_SIGNS),
        "body_joint_offsets_deg": list(MIDPOINT_DIRECT_BODY_JOINT_OFFSETS_DEG),
        "gripper_range_rad": list(GRIPPER_RANGE_RAD),
        "lerobot_zero_semantics": "calibrated_range_midpoint",
        "mujoco_zero_semantics": "new_calib_virtual_joint_range_midpoint",
        "direction_semantics": "direct_positive_candidate_requires_session_review",
        "default_limit_handling": "reject_without_projection",
        "physical_twin_qualified": False,
        "authority_not_granted": [
            "matched_mujoco_replay_accepted",
            "physical_actuation",
            "physical_twin_qualified",
            "simulation_training_ready",
        ],
    }


def lerobot_to_midpoint_mujoco_candidate(
    values: Sequence[float],
    *,
    allow_limit_projection: bool = False,
    round_digits: int | None = None,
) -> list[float]:
    """Map midpoint LeRobot values into the pinned new-calib model."""

    normalized = _finite_six(values, label="LeRobot midpoint candidate")
    unbounded = [math.radians(value) for value in normalized[:5]]
    low, high = GRIPPER_RANGE_RAD
    unbounded.append(low + (normalized[5] / 100.0) * (high - low))
    result = _apply_limits(
        unbounded,
        (*MUJOCO_BODY_LIMITS_RAD, GRIPPER_RANGE_RAD),
        (*BODY_JOINT_NAMES, "gripper"),
        allow_projection=allow_limit_projection,
        label="midpoint-direct LeRobot to MuJoCo",
    )
    if round_digits is not None:
        return [round(value, round_digits) for value in result]
    return result


def midpoint_mujoco_candidate_to_lerobot(
    values: Sequence[float],
    *,
    allow_limit_projection: bool = False,
    round_digits: int | None = None,
) -> list[float]:
    """Map the pinned new-calib model into midpoint LeRobot values."""

    bounded = _apply_limits(
        _finite_six(values, label="MuJoCo midpoint candidate"),
        (*MUJOCO_BODY_LIMITS_RAD, GRIPPER_RANGE_RAD),
        (*BODY_JOINT_NAMES, "gripper"),
        allow_projection=allow_limit_projection,
        label="midpoint-direct MuJoCo to LeRobot",
    )
    low, high = GRIPPER_RANGE_RAD
    result = [
        *(math.degrees(value) for value in bounded[:5]),
        100.0 * (bounded[5] - low) / (high - low),
    ]
    if round_digits is not None:
        return [round(value, round_digits) for value in result]
    return result


def _finite_six(values: Sequence[float], *, label: str) -> list[float]:
    if len(values) != 6:
        raise ValueError(f"{label} must contain exactly six joints")
    normalized = [float(value) for value in values]
    if not all(math.isfinite(value) for value in normalized):
        raise ValueError(f"{label} must contain only finite values")
    return normalized


def _apply_limits(
    values: Sequence[float],
    limits: Sequence[tuple[float, float]],
    names: Sequence[str],
    *,
    allow_projection: bool,
    label: str,
) -> list[float]:
    result = []
    for value, (low, high), name in zip(values, limits, names, strict=True):
        if low <= value <= high:
            result.append(value)
        elif allow_projection:
            result.append(min(high, max(low, value)))
        else:
            raise ValueError(
                f"{label} {name}={value} is outside [{low}, {high}]; "
                "implicit projection is forbidden"
            )
    return result
