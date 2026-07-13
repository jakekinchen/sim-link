"""Named canonical SO-101 processor with separated transform and safety steps."""

from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path
from typing import Any, Sequence

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_artifact_ref,
    verify_signed_payload,
)
from scenesmith.robot_lab.so101_coordinates import (
    BODY_JOINT_OFFSETS_DEG,
    BODY_JOINT_SIGNS,
    GRIPPER_RANGE_RAD,
    MUJOCO_BODY_LIMITS_RAD,
    coordinate_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("configurations/robot_lab/so101_canonical_processor_contract.json")
EXPERIENCE_CONTRACT_PATH = Path("configurations/robot_lab/experience_record_contract.json")
SCHEMA_VERSION = "scenesmith.so101_canonical_processor_contract.v1"
PROCESSOR_NAME = "scenesmith_so101_canonical_processor_v1"
MUJOCO_REPRESENTATION = "absolute_joint_radians_plus_gripper_radians"
CANONICAL_REPRESENTATION = "absolute_joint_degrees_plus_gripper_percent"
ACTION_MODE = "absolute"
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)


class CanonicalSO101Processor:
    """Pure coordinate transform plus explicit validation and limiting."""

    name = PROCESSOR_NAME

    def transform(
        self,
        values: Sequence[float],
        *,
        source_representation: str,
        target_representation: str,
        ordered_joint_names: Sequence[str] = JOINT_NAMES,
        action_mode: str = ACTION_MODE,
    ) -> list[float]:
        prepared = self._prepare(values, ordered_joint_names, action_mode)
        self._require_representation(source_representation)
        self._require_representation(target_representation)
        if source_representation == target_representation:
            return prepared
        if source_representation == MUJOCO_REPRESENTATION:
            body_degrees = [math.degrees(value) for value in prepared[:5]]
            body = [
                (value - offset) / sign
                for value, sign, offset in zip(
                    body_degrees,
                    BODY_JOINT_SIGNS,
                    BODY_JOINT_OFFSETS_DEG,
                    strict=True,
                )
            ]
            low, high = GRIPPER_RANGE_RAD
            gripper = 100.0 * (prepared[5] - low) / (high - low)
            return [*body, gripper]
        body_degrees = [
            value * sign + offset
            for value, sign, offset in zip(
                prepared[:5],
                BODY_JOINT_SIGNS,
                BODY_JOINT_OFFSETS_DEG,
                strict=True,
            )
        ]
        low, high = GRIPPER_RANGE_RAD
        gripper = low + (prepared[5] / 100.0) * (high - low)
        return [*(math.radians(value) for value in body_degrees), gripper]

    def validate(
        self,
        values: Sequence[float],
        *,
        representation: str,
        ordered_joint_names: Sequence[str] = JOINT_NAMES,
        action_mode: str = ACTION_MODE,
    ) -> list[float]:
        prepared = self._prepare(values, ordered_joint_names, action_mode)
        limits = self.limits(representation)
        for name, value, (low, high) in zip(
            JOINT_NAMES, prepared, limits, strict=True
        ):
            if not low <= value <= high:
                raise ValueError(
                    f"{name} is outside {representation} bounds [{low}, {high}]"
                )
        return prepared

    def limit(
        self,
        values: Sequence[float],
        *,
        representation: str,
        ordered_joint_names: Sequence[str] = JOINT_NAMES,
        action_mode: str = ACTION_MODE,
    ) -> dict[str, Any]:
        requested = self._prepare(values, ordered_joint_names, action_mode)
        limits = self.limits(representation)
        executed = [
            min(high, max(low, value))
            for value, (low, high) in zip(requested, limits, strict=True)
        ]
        clipped_indices = [
            index
            for index, (before, after) in enumerate(
                zip(requested, executed, strict=True)
            )
            if before != after
        ]
        return {
            "processor_name": self.name,
            "operation": "safety_limit",
            "representation": representation,
            "action_mode": action_mode,
            "ordered_joint_names": list(JOINT_NAMES),
            "requested_values": requested,
            "executed_values": executed,
            "clipped_indices": clipped_indices,
            "clipped_joint_names": [JOINT_NAMES[index] for index in clipped_indices],
            "safety_limited": bool(clipped_indices),
        }

    @staticmethod
    def limits(representation: str) -> tuple[tuple[float, float], ...]:
        if representation == MUJOCO_REPRESENTATION:
            return (*MUJOCO_BODY_LIMITS_RAD, GRIPPER_RANGE_RAD)
        if representation == CANONICAL_REPRESENTATION:
            body = []
            for (low, high), sign, offset in zip(
                MUJOCO_BODY_LIMITS_RAD,
                BODY_JOINT_SIGNS,
                BODY_JOINT_OFFSETS_DEG,
                strict=True,
            ):
                transformed = (
                    (math.degrees(low) - offset) / sign,
                    (math.degrees(high) - offset) / sign,
                )
                body.append((min(transformed), max(transformed)))
            return (*body, (0.0, 100.0))
        raise ValueError(f"Unsupported SO-101 representation: {representation}")

    @staticmethod
    def _prepare(
        values: Sequence[float],
        ordered_joint_names: Sequence[str],
        action_mode: str,
    ) -> list[float]:
        try:
            names = tuple(ordered_joint_names)
        except TypeError as exc:
            raise ValueError(
                "SO-101 ordered joint names are missing, extra, or permuted"
            ) from exc
        if names != JOINT_NAMES:
            raise ValueError("SO-101 ordered joint names are missing, extra, or permuted")
        if action_mode != ACTION_MODE:
            raise ValueError("SO-101 processor supports explicit absolute action mode only")
        try:
            value_count = len(values)
        except TypeError as exc:
            raise ValueError("SO-101 action must contain exactly six ordered values") from exc
        if isinstance(values, (str, bytes, dict)) or value_count != len(JOINT_NAMES):
            raise ValueError("SO-101 action must contain exactly six ordered values")
        prepared = []
        for value in values:
            if isinstance(value, bool):
                raise ValueError("SO-101 action values must be finite numbers")
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("SO-101 action values must be finite numbers") from exc
            if not math.isfinite(number):
                raise ValueError("SO-101 action values must be finite numbers")
            prepared.append(number)
        return prepared

    @staticmethod
    def _require_representation(representation: str) -> None:
        if representation not in {MUJOCO_REPRESENTATION, CANONICAL_REPRESENTATION}:
            raise ValueError(f"Unsupported SO-101 representation: {representation}")


def build_so101_processor_contract(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    experience = load_strict_json(repo_root / EXPERIENCE_CONTRACT_PATH)
    verify_signed_payload(experience, label="source experience record contract")
    experience_ref = artifact_ref(
        path=EXPERIENCE_CONTRACT_PATH, payload=experience, repo_root=repo_root
    )
    coordinates = coordinate_contract()
    coordinate_ref = {
        "schema_version": coordinates["schema_version"],
        "identity_sha256": hashlib.sha256(canonical_json_bytes(coordinates)).hexdigest(),
    }
    processor = CanonicalSO101Processor()
    generator = random.Random(1702)
    maximum_round_trip_error = 0.0
    for _ in range(128):
        sample = [
            generator.uniform(low, high)
            for low, high in processor.limits(MUJOCO_REPRESENTATION)
        ]
        canonical = processor.transform(
            sample,
            source_representation=MUJOCO_REPRESENTATION,
            target_representation=CANONICAL_REPRESENTATION,
        )
        replay = processor.transform(
            canonical,
            source_representation=CANONICAL_REPRESENTATION,
            target_representation=MUJOCO_REPRESENTATION,
        )
        maximum_round_trip_error = max(
            maximum_round_trip_error,
            *(abs(before - after) for before, after in zip(sample, replay, strict=True)),
        )
    golden_mujoco = [0.0, -0.55, 1.05, -0.48, 0.0, 0.35]
    golden_canonical = processor.transform(
        golden_mujoco,
        source_representation=MUJOCO_REPRESENTATION,
        target_representation=CANONICAL_REPRESENTATION,
    )
    out_of_range = [*golden_canonical[:5], 120.0]
    pure_out = processor.transform(
        out_of_range,
        source_representation=CANONICAL_REPRESENTATION,
        target_representation=MUJOCO_REPRESENTATION,
    )
    limited = processor.limit(
        out_of_range, representation=CANONICAL_REPRESENTATION
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "processor_name": PROCESSOR_NAME,
        "source_experience_record_contract_ref": experience_ref,
        "coordinate_contract_ref": coordinate_ref,
        "ordered_joint_names": list(JOINT_NAMES),
        "action_mode": ACTION_MODE,
        "representations": {
            "canonical": CANONICAL_REPRESENTATION,
            "mujoco": MUJOCO_REPRESENTATION,
        },
        "operations": {
            "transform": "pure_unclamped_coordinate_conversion",
            "validate": "fail_closed_representation_range_validation",
            "limit": "explicit_safety_limit_with_requested_and_executed_values",
        },
        "limits": {
            CANONICAL_REPRESENTATION: [
                list(bounds) for bounds in processor.limits(CANONICAL_REPRESENTATION)
            ],
            MUJOCO_REPRESENTATION: [
                list(bounds) for bounds in processor.limits(MUJOCO_REPRESENTATION)
            ],
        },
        "verification": {
            "random_seed": 1702,
            "random_round_trip_count": 128,
            "maximum_round_trip_error": maximum_round_trip_error,
            "golden_mujoco_values": golden_mujoco,
            "golden_canonical_values": golden_canonical,
            "pure_transform_out_of_range_gripper_rad": pure_out[5],
            "limited_out_of_range_example": limited,
            "gripper_monotonic_canonical_percent": [
                processor.transform(
                    [0.0, 0.0, 0.0, 0.0, 0.0, value],
                    source_representation=MUJOCO_REPRESENTATION,
                    target_representation=CANONICAL_REPRESENTATION,
                )[5]
                for value in GRIPPER_RANGE_RAD
            ],
        },
        "normalization_bundle_valid": False,
        "compiled_training_frames": False,
        "simulation_training_ready": False,
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "authority_not_granted": [
            "normalization_bundle_valid",
            "compiled_training_frames",
            "simulation_training_ready",
            "optimizer_training",
            "physical_actuation",
        ],
    }
    return sign_payload(payload)


def verify_so101_processor_contract(
    payload: dict[str, Any], *, repo_root: Path = REPO_ROOT
) -> None:
    verify_signed_payload(payload, label="SO-101 canonical processor contract")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("SO-101 processor contract schema is invalid")
    experience = load_strict_json(repo_root / EXPERIENCE_CONTRACT_PATH)
    verify_signed_payload(experience, label="source experience record contract")
    expected_ref = artifact_ref(
        path=EXPERIENCE_CONTRACT_PATH, payload=experience, repo_root=repo_root
    )
    verify_artifact_ref(
        payload.get("source_experience_record_contract_ref"),
        expected_ref,
        label="source experience record contract",
    )
    if payload != build_so101_processor_contract(repo_root=repo_root):
        raise ValueError("SO-101 processor contract drifted")
    if payload.get("simulation_training_ready") or payload.get("compiled_training_frames"):
        raise ValueError("SO-101 processor contract escalates training authority")
