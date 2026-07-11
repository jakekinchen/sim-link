"""Pure PI0.5 checkpoint training-support classification for fixture inputs."""

from __future__ import annotations

import math
import re

from bisect import bisect_right
from typing import Any


JOINT_ORDER = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]
STATE_STATISTIC_ORDER = [
    "min",
    "q01",
    "q10",
    "q50",
    "q90",
    "q99",
    "max",
    "mean",
    "std",
]
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def build_state_support_audit(
    state_stats: Any,
    *,
    state_values: list[float],
    normalized_values: list[float],
    discretized_values: list[int],
    source_contract: dict[str, Any],
) -> dict[str, Any]:
    """Build a mean/std and observed-support audit from pinned tensors."""

    if not isinstance(state_stats, dict) or set(state_stats) != {
        "count",
        *STATE_STATISTIC_ORDER,
    }:
        raise ValueError("PI0.5 fixture state statistics are incomplete")
    count_value = state_stats["count"]
    sample_count = float(
        count_value.item() if hasattr(count_value, "item") else count_value
    )
    if (
        not math.isfinite(sample_count)
        or sample_count <= 0
        or not sample_count.is_integer()
    ):
        raise ValueError("PI0.5 fixture state statistic count is invalid")
    statistics: dict[str, list[float]] = {}
    for name in STATE_STATISTIC_ORDER:
        value = state_stats[name]
        items = value.tolist() if hasattr(value, "tolist") else value
        if (
            not isinstance(items, list)
            or len(items) != len(JOINT_ORDER)
            or any(
                isinstance(item, bool)
                or not isinstance(item, (int, float))
                or not math.isfinite(float(item))
                for item in items
            )
        ):
            raise ValueError(f"PI0.5 fixture state statistic drifted: {name}")
        statistics[name] = [float(item) for item in items]
    return _compose_state_support_audit(
        sample_count=int(sample_count),
        statistics=statistics,
        state_values=state_values,
        normalized_values=normalized_values,
        discretized_values=discretized_values,
        normalizer_file_sha256=_normalizer_file_sha256(source_contract),
    )


def verify_state_support_audit(
    value: Any,
    *,
    state_values: list[float],
    discretized_values: list[int],
    source: dict[str, Any],
) -> None:
    """Recompute support classes and reject re-signed semantic drift."""

    if not isinstance(value, dict):
        raise ValueError("PI0.5 fixture state-support audit is missing")
    if (
        value.get("normalization_mode") != "MEAN_STD"
        or value.get("normalization_mode_mutated") is not False
        or value.get("clipping_applied") is not False
        or value.get("normalizer_file_sha256")
        != _normalizer_file_sha256(source)
        or value.get("statistic_order") != STATE_STATISTIC_ORDER
        or not isinstance(value.get("statistics"), dict)
        or set(value["statistics"]) != set(STATE_STATISTIC_ORDER)
        or not isinstance(value.get("normalized_values"), list)
    ):
        raise ValueError("PI0.5 fixture state-support classification drifted")
    checkpoint = source["checkpoint_processor_snapshot"]["checkpoint_config"]
    if checkpoint["normalization_mapping"]["STATE"] != "MEAN_STD":
        raise ValueError("PI0.5 fixture checkpoint state normalization drifted")
    expected = _compose_state_support_audit(
        sample_count=value.get("sample_count"),
        statistics=value["statistics"],
        state_values=state_values,
        normalized_values=value["normalized_values"],
        discretized_values=discretized_values,
        normalizer_file_sha256=_normalizer_file_sha256(source),
    )
    if value != expected:
        raise ValueError("PI0.5 fixture state-support audit drifted")


def _compose_state_support_audit(
    *,
    sample_count: int,
    statistics: dict[str, list[float]],
    state_values: list[float],
    normalized_values: list[float],
    discretized_values: list[int],
    normalizer_file_sha256: str,
) -> dict[str, Any]:
    if (
        type(sample_count) is not int
        or sample_count <= 0
        or set(statistics) != set(STATE_STATISTIC_ORDER)
        or len(state_values) != len(JOINT_ORDER)
        or len(normalized_values) != len(JOINT_ORDER)
        or len(discretized_values) != len(JOINT_ORDER)
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in [*state_values, *normalized_values]
        )
        or any(
            type(value) is not int or value < -1 or value > 255
            for value in discretized_values
        )
    ):
        raise ValueError("PI0.5 fixture state-support inputs are malformed")
    bins = [-1.0 + index / 128.0 for index in range(256)]
    for index in range(len(JOINT_ORDER)):
        ordered = [statistics[name][index] for name in STATE_STATISTIC_ORDER[:7]]
        if any(left > right for left, right in zip(ordered, ordered[1:])):
            raise ValueError("PI0.5 fixture state quantiles are not ordered")
        if statistics["std"][index] <= 0:
            raise ValueError("PI0.5 fixture state standard deviation is nonpositive")
        if not (
            statistics["min"][index]
            <= statistics["mean"][index]
            <= statistics["max"][index]
        ):
            raise ValueError("PI0.5 fixture state mean is outside observed bounds")
        expected_normalized = (
            state_values[index] - statistics["mean"][index]
        ) / statistics["std"][index]
        if not math.isclose(
            normalized_values[index],
            expected_normalized,
            rel_tol=1e-6,
            abs_tol=1e-6,
        ):
            raise ValueError("PI0.5 fixture mean/std normalization drifted")
        if discretized_values[index] != bisect_right(
            bins,
            normalized_values[index],
        ) - 1:
            raise ValueError("PI0.5 fixture state discretization drifted")

    joints = []
    outside_std = []
    outside_q01_q99 = []
    outside_min_max = []
    within_observed = []
    for index, joint_name in enumerate(JOINT_ORDER):
        value = float(state_values[index])
        normalized = float(normalized_values[index])
        minimum = statistics["min"][index]
        maximum = statistics["max"][index]
        q01 = statistics["q01"][index]
        q99 = statistics["q99"][index]
        within_std = -1.0 <= normalized <= 1.0
        within_q = q01 <= value <= q99
        within_min_max = minimum <= value <= maximum
        if not within_std:
            outside_std.append(joint_name)
        if not within_q:
            outside_q01_q99.append(joint_name)
        if not within_min_max:
            outside_min_max.append(joint_name)
            support_class = "outside_observed_training_min_max"
        elif not within_q:
            within_observed.append(joint_name)
            support_class = "within_observed_min_max_outside_q01_q99"
        else:
            within_observed.append(joint_name)
            support_class = "within_q01_q99"
        joints.append(
            {
                "joint_name": joint_name,
                "value": value,
                "normalized_mean_std_value": normalized,
                "discretized_value": discretized_values[index],
                "mean_minus_std": statistics["mean"][index]
                - statistics["std"][index],
                "mean_plus_std": statistics["mean"][index]
                + statistics["std"][index],
                "q01": q01,
                "q99": q99,
                "observed_min": minimum,
                "observed_max": maximum,
                "within_mean_plus_minus_std": within_std,
                "within_q01_q99": within_q,
                "within_observed_min_max": within_min_max,
                "support_class": support_class,
            }
        )

    return {
        "normalization_mode": "MEAN_STD",
        "normalization_mode_source": "serialized_checkpoint_config_and_preprocessor",
        "normalization_mode_mutated": False,
        "clipping_applied": False,
        "normalizer_file_sha256": normalizer_file_sha256,
        "sample_count": sample_count,
        "statistic_order": list(STATE_STATISTIC_ORDER),
        "statistics": statistics,
        "discretizer": {
            "implementation": "numpy_digitize_minus_one",
            "reference_interval": [-1.0, 1.0],
            "reference_interval_is_hard_validity_domain": False,
            "bin_count": 256,
            "last_bin_lower_edge": 0.9921875,
            "below_reference_interval_value": -1,
            "at_or_above_last_bin_value": 255,
            "clipping_applied": False,
        },
        "normalized_values": [float(value) for value in normalized_values],
        "joints": joints,
        "summary": {
            "outside_mean_plus_minus_std_joints": outside_std,
            "outside_q01_q99_joints": outside_q01_q99,
            "outside_observed_min_max_joints": outside_min_max,
            "within_observed_support_joints": within_observed,
            "actual_live_input_present": False,
            "policy_shadow_input_valid_granted": False,
            "physical_policy_actuation_eligible": False,
            "out_of_support_disposition": (
                "record_and_allow_no_actuation_shadow_analysis_only_after_"
                "independent_live_acceptance;block_policy_actuation"
            ),
        },
    }


def _normalizer_file_sha256(source: dict[str, Any]) -> str:
    files = source.get("checkpoint_processor_snapshot", {}).get("files")
    if not isinstance(files, list):
        raise ValueError("PI0.5 fixture checkpoint file evidence is missing")
    matches = [
        item
        for item in files
        if item.get("filename")
        == "policy_preprocessor_step_2_normalizer_processor.safetensors"
    ]
    if len(matches) != 1:
        raise ValueError("PI0.5 fixture normalizer file identity is ambiguous")
    digest = matches[0].get("sha256")
    if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
        raise ValueError("PI0.5 fixture normalizer file must be lowercase SHA-256")
    return digest


__all__ = ["build_state_support_audit", "verify_state_support_audit"]
