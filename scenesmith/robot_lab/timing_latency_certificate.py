"""Derived offline timing and latency certificates for T20.22."""

from __future__ import annotations

import copy

from pathlib import Path
from typing import Any, Callable

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.paired_trace_runner import verify_paired_trace_runner_fixture


CONTRACT_SCHEMA_VERSION = "scenesmith.timing_latency_contract.v1"
CERTIFICATE_SCHEMA_VERSION = "scenesmith.timing_latency_certificate.v1"
RESULT_SCHEMA_VERSION = "scenesmith.timing_latency_evaluation.v1"
FIXTURE_SCHEMA_VERSION = "scenesmith.timing_latency_fixture.v1"
PAIRED_PATH = Path("configurations/robot_lab/t20_21_paired_trace_runner.json")
REPO_ROOT = Path(__file__).resolve().parents[2]
CLOCK_KEYS = (
    "sensor_a",
    "sensor_b",
    "observation_assembly",
    "inference",
    "action_transport",
    "control_loop",
)
CERTIFICATE_FIELDS = {
    "schema_version",
    "certificate_id",
    "evidence_source",
    "source_paired_trace_contract_identity_sha256",
    "source_simulator_trace_identity_sha256",
    "source_observable_trace_identity_sha256",
    "source_paired_result_identity_sha256",
    "clock_sources",
    "samples",
    "identity_sha256",
}
SAMPLE_FIELDS = {
    "cycle_index",
    "control_cycle_timestamp_ns",
    "sensor_frame_timestamps_ns",
    "observation_assembled_timestamp_ns",
    "inference_start_timestamp_ns",
    "inference_end_timestamp_ns",
    "action_proposed_timestamp_ns",
    "action_issued_timestamp_ns",
    "action_applied_timestamp_ns",
    "action_hold_until_timestamp_ns",
    "deadline_timestamp_ns",
    "observation_dropped",
}
TIMING_MISMATCH_CATEGORIES = (
    "clock_domain_mismatch",
    "frame_age_exceeded",
    "frame_skew_exceeded",
    "observation_assembly_exceeded",
    "action_transport_exceeded",
    "action_hold_out_of_bounds",
    "control_period_out_of_bounds",
    "control_jitter_exceeded",
    "inference_latency_exceeded",
    "observation_drop_detected",
    "deadline_miss_detected",
)


def build_timing_latency_contract(
    paired_fixture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the signed source bindings, metric definitions, and thresholds."""

    paired_fixture = paired_fixture or load_strict_json(REPO_ROOT / PAIRED_PATH)
    verify_paired_trace_runner_fixture(paired_fixture)
    return sign_payload(
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "source_paired_trace_fixture_identity_sha256": paired_fixture[
                "identity_sha256"
            ],
            "source_paired_trace_contract_identity_sha256": paired_fixture[
                "contract"
            ]["identity_sha256"],
            "source_simulator_trace_identity_sha256": paired_fixture["traces"][
                "simulator"
            ]["identity_sha256"],
            "source_observable_trace_identity_sha256": paired_fixture["traces"][
                "observable"
            ]["identity_sha256"],
            "source_paired_result_identity_sha256": paired_fixture["matched_result"][
                "identity_sha256"
            ],
            "clock_source_keys": list(CLOCK_KEYS),
            "certificate_fields": sorted(CERTIFICATE_FIELDS),
            "sample_fields": sorted(SAMPLE_FIELDS),
            "mismatch_categories": list(TIMING_MISMATCH_CATEGORIES),
            "thresholds": {
                "maximum_frame_age_ns": 50_000_000,
                "maximum_frame_skew_ns": 20_000_000,
                "maximum_observation_assembly_ns": 10_000_000,
                "maximum_action_transport_ns": 20_000_000,
                "minimum_action_hold_ns": 20_000_000,
                "maximum_action_hold_ns": 100_000_000,
                "expected_control_period_ns": 100_000_000,
                "control_period_tolerance_ns": 10_000_000,
                "maximum_control_jitter_ns": 5_000_000,
                "maximum_inference_latency_ns": 50_000_000,
            },
            "allowed_evidence_sources": [
                "synthetic_timing_fixture",
                "offline_recorded_timing",
            ],
            "metric_policy": "derive_from_cycle_samples_never_trust_aggregates",
            "clock_policy": "cross_stream_metrics_require_one_declared_clock_domain",
            "dynamics_attribution_policy": (
                "any_timing_mismatch_blocks_dynamics_error_attribution"
            ),
            "live_probe_supported": False,
            "calibration_or_twin_update_supported": False,
            "physical_qualification_supported": False,
        }
    )


def evaluate_timing_certificate(
    contract: dict[str, Any], certificate: dict[str, Any]
) -> dict[str, Any]:
    """Derive timing metrics and block dynamics attribution on any mismatch."""

    _validate_contract(contract)
    _validate_certificate(contract, certificate)
    samples = certificate["samples"]
    clock_values = list(certificate["clock_sources"].values())
    clock_aligned = len(set(clock_values)) == 1
    thresholds = contract["thresholds"]

    drops = sum(1 for sample in samples if sample["observation_dropped"])
    categories: list[str] = []
    if not clock_aligned:
        categories.append("clock_domain_mismatch")

    maximum_frame_age: int | None = None
    maximum_frame_skew: int | None = None
    maximum_assembly: int | None = None
    maximum_transport: int | None = None
    minimum_hold: int | None = None
    maximum_hold: int | None = None
    mean_period: float | None = None
    maximum_jitter: float | None = None
    maximum_inference: int | None = None
    deadline_misses: int | None = None

    if clock_aligned:
        frame_ages = [
            sample["control_cycle_timestamp_ns"] - timestamp
            for sample in samples
            for timestamp in sample["sensor_frame_timestamps_ns"].values()
        ]
        frame_skews = [
            max(sample["sensor_frame_timestamps_ns"].values())
            - min(sample["sensor_frame_timestamps_ns"].values())
            for sample in samples
        ]
        assemblies = [
            sample["observation_assembled_timestamp_ns"]
            - sample["control_cycle_timestamp_ns"]
            for sample in samples
        ]
        transports = [
            sample["action_applied_timestamp_ns"]
            - sample["action_issued_timestamp_ns"]
            for sample in samples
        ]
        holds = [
            sample["action_hold_until_timestamp_ns"]
            - sample["action_applied_timestamp_ns"]
            for sample in samples
        ]
        periods = [
            right["control_cycle_timestamp_ns"] - left["control_cycle_timestamp_ns"]
            for left, right in zip(samples, samples[1:])
        ]
        inference_latencies = [
            sample["inference_end_timestamp_ns"]
            - sample["inference_start_timestamp_ns"]
            for sample in samples
            if sample["inference_start_timestamp_ns"] is not None
        ]
        maximum_frame_age = max(frame_ages)
        maximum_frame_skew = max(frame_skews)
        maximum_assembly = max(assemblies)
        maximum_transport = max(transports)
        minimum_hold = min(holds)
        maximum_hold = max(holds)
        mean_period = sum(periods) / len(periods)
        maximum_jitter = max(abs(period - mean_period) for period in periods)
        maximum_inference = max(inference_latencies) if inference_latencies else 0
        deadline_misses = sum(
            1
            for sample in samples
            if sample["action_applied_timestamp_ns"] > sample["deadline_timestamp_ns"]
        )

        if maximum_frame_age > thresholds["maximum_frame_age_ns"]:
            categories.append("frame_age_exceeded")
        if maximum_frame_skew > thresholds["maximum_frame_skew_ns"]:
            categories.append("frame_skew_exceeded")
        if maximum_assembly > thresholds["maximum_observation_assembly_ns"]:
            categories.append("observation_assembly_exceeded")
        if maximum_transport > thresholds["maximum_action_transport_ns"]:
            categories.append("action_transport_exceeded")
        if (
            minimum_hold < thresholds["minimum_action_hold_ns"]
            or maximum_hold > thresholds["maximum_action_hold_ns"]
        ):
            categories.append("action_hold_out_of_bounds")
        if (
            abs(mean_period - thresholds["expected_control_period_ns"])
            > thresholds["control_period_tolerance_ns"]
        ):
            categories.append("control_period_out_of_bounds")
        if maximum_jitter > thresholds["maximum_control_jitter_ns"]:
            categories.append("control_jitter_exceeded")
        if maximum_inference > thresholds["maximum_inference_latency_ns"]:
            categories.append("inference_latency_exceeded")
        if deadline_misses:
            categories.append("deadline_miss_detected")
    if drops:
        categories.append("observation_drop_detected")

    categories = [
        category for category in TIMING_MISMATCH_CATEGORIES if category in categories
    ]
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "contract_identity_sha256": contract["identity_sha256"],
            "certificate_identity_sha256": certificate["identity_sha256"],
            "evidence_source": certificate["evidence_source"],
            "sample_count": len(samples),
            "clock_sources": dict(certificate["clock_sources"]),
            "cross_stream_metrics_available": clock_aligned,
            "maximum_frame_age_ns": maximum_frame_age,
            "maximum_frame_skew_ns": maximum_frame_skew,
            "maximum_observation_assembly_ns": maximum_assembly,
            "maximum_action_transport_ns": maximum_transport,
            "minimum_action_hold_ns": minimum_hold,
            "maximum_action_hold_ns": maximum_hold,
            "mean_control_period_ns": mean_period,
            "maximum_control_jitter_ns": maximum_jitter,
            "maximum_inference_latency_ns": maximum_inference,
            "observation_drop_count": drops,
            "deadline_miss_count": deadline_misses,
            "timing_mismatch_categories": categories,
            "timing_valid": not categories,
            "dynamics_error_attribution_blocked_by_timing": bool(categories),
            "dynamics_error_proven": False,
            "clock_synchronization_proven": False,
            "calibration_update_selected": False,
            "twin_update_selected": False,
            "physical_qualification": False,
            "authority_granted": [],
        }
    )


def build_timing_latency_fixture(
    paired_fixture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a passing certificate and fixed one-factor timing diagnostics."""

    paired_fixture = paired_fixture or load_strict_json(REPO_ROOT / PAIRED_PATH)
    contract = build_timing_latency_contract(paired_fixture)
    passing = _base_certificate(contract)
    passing_result = evaluate_timing_certificate(contract, passing)
    mutations: dict[str, Callable[[dict[str, Any]], None]] = {
        "clock_domain_mismatch": lambda value: value["clock_sources"].__setitem__(
            "sensor_b", "synthetic_monotonic_ns_alt"
        ),
        "frame_age_exceeded": _exceed_frame_age,
        "frame_skew_exceeded": _exceed_frame_skew,
        "observation_assembly_exceeded": _exceed_assembly,
        "action_transport_exceeded": _exceed_transport,
        "action_hold_out_of_bounds": _exceed_hold,
        "control_period_out_of_bounds": _exceed_control_period,
        "control_jitter_exceeded": _exceed_control_jitter,
        "inference_latency_exceeded": _exceed_inference,
        "observation_drop_detected": lambda value: value["samples"][0].__setitem__(
            "observation_dropped", True
        ),
        "deadline_miss_detected": _miss_deadline,
    }
    diagnostics: dict[str, dict[str, Any]] = {}
    for category in TIMING_MISMATCH_CATEGORIES:
        changed = copy.deepcopy(passing)
        mutations[category](changed)
        changed.pop("identity_sha256")
        changed = sign_payload(changed)
        diagnostics[category] = {
            "expected_mismatch_category": category,
            "certificate_identity_sha256": changed["identity_sha256"],
            "result": evaluate_timing_certificate(contract, changed),
        }
    return sign_payload(
        {
            "schema_version": FIXTURE_SCHEMA_VERSION,
            "source_paired_trace_fixture_identity_sha256": paired_fixture[
                "identity_sha256"
            ],
            "contract": contract,
            "passing_certificate": passing,
            "passing_result": passing_result,
            "diagnostic_cases": diagnostics,
            "all_timing_mismatches_routed": all(
                category
                in diagnostics[category]["result"]["timing_mismatch_categories"]
                for category in TIMING_MISMATCH_CATEGORIES
            ),
            "all_timing_mismatches_block_dynamics_attribution": all(
                diagnostics[category]["result"][
                    "dynamics_error_attribution_blocked_by_timing"
                ]
                for category in TIMING_MISMATCH_CATEGORIES
            ),
            "evidence_scope": "synthetic_offline_timing_fixture_only",
            "hardware_observation_performed": False,
            "live_probe_executed": False,
            "camera_accessed": False,
            "clock_synchronization_proven": False,
            "calibration_updated": False,
            "twin_updated": False,
            "dynamics_error_proven": False,
            "physical_qualification_granted": False,
            "simulation_policy_accepted": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "optimizer_training": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "authority_granted": ["offline_timing_latency_fixture_conformant"],
            "authority_not_granted": [
                "hardware_observation",
                "live_probe_execution",
                "camera_access",
                "clock_synchronization",
                "dynamics_calibration",
                "calibration_update",
                "twin_update",
                "dynamics_error_proven",
                "physical_qualification",
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
        }
    )


def verify_timing_latency_fixture(
    payload: dict[str, Any], paired_fixture: dict[str, Any] | None = None
) -> None:
    """Reject signed drift from the deterministic paired-trace-bound fixture."""

    paired_fixture = paired_fixture or load_strict_json(REPO_ROOT / PAIRED_PATH)
    verify_signed_payload(payload, label="timing latency fixture")
    if payload != build_timing_latency_fixture(paired_fixture):
        raise ValueError("Timing latency fixture drifted")


def _validate_contract(contract: dict[str, Any]) -> None:
    verify_signed_payload(contract, label="timing latency contract")
    if contract != build_timing_latency_contract():
        raise ValueError("Timing latency contract drifted")


def _validate_certificate(contract: dict[str, Any], certificate: dict[str, Any]) -> None:
    if not isinstance(certificate, dict):
        raise ValueError("Timing certificate must be an object")
    unknown = set(certificate).difference(CERTIFICATE_FIELDS)
    if unknown:
        raise ValueError(
            "undeclared certificate field: " + ", ".join(sorted(unknown))
        )
    missing = CERTIFICATE_FIELDS.difference(certificate)
    if missing:
        raise ValueError("missing certificate field: " + ", ".join(sorted(missing)))
    if certificate["schema_version"] != CERTIFICATE_SCHEMA_VERSION:
        raise ValueError("Timing certificate schema is invalid")
    _require_nonblank(certificate["certificate_id"], "certificate_id")
    if certificate["evidence_source"] not in contract["allowed_evidence_sources"]:
        raise ValueError("Timing certificate evidence source is not allowed")
    for key in (
        "source_paired_trace_contract_identity_sha256",
        "source_simulator_trace_identity_sha256",
        "source_observable_trace_identity_sha256",
        "source_paired_result_identity_sha256",
    ):
        if certificate[key] != contract[key]:
            raise ValueError(f"Timing certificate source binding drifted: {key}")
    clock_sources = certificate["clock_sources"]
    if not isinstance(clock_sources, dict) or set(clock_sources) != set(CLOCK_KEYS):
        raise ValueError("Timing certificate clock source keys are invalid")
    for value in clock_sources.values():
        _require_nonblank(value, "clock source")

    samples = certificate["samples"]
    if not isinstance(samples, list) or len(samples) < 3:
        raise ValueError("Timing certificate requires at least three samples")
    prior_control: int | None = None
    for expected_index, sample in enumerate(samples):
        _validate_sample(sample, expected_index, prior_control)
        prior_control = sample["control_cycle_timestamp_ns"]
    verify_signed_payload(certificate, label="timing certificate")


def _validate_sample(
    sample: Any, expected_index: int, prior_control: int | None
) -> None:
    if not isinstance(sample, dict):
        raise ValueError("Timing sample must be an object")
    unknown = set(sample).difference(SAMPLE_FIELDS)
    if unknown:
        raise ValueError("undeclared timing sample field: " + ", ".join(sorted(unknown)))
    missing = SAMPLE_FIELDS.difference(sample)
    if missing:
        raise ValueError("missing timing sample field: " + ", ".join(sorted(missing)))
    index = sample["cycle_index"]
    if isinstance(index, bool) or not isinstance(index, int) or index != expected_index:
        raise ValueError("Timing sample cycle indices must be contiguous")
    if not isinstance(sample["observation_dropped"], bool):
        raise ValueError("observation_dropped must be boolean")
    sensor_times = sample["sensor_frame_timestamps_ns"]
    if not isinstance(sensor_times, dict) or set(sensor_times) != {"sensor_a", "sensor_b"}:
        raise ValueError("sensor frame timestamp keys are invalid")
    for label, value in sensor_times.items():
        _timestamp(value, f"{label} timestamp")
    timestamp_fields = (
        "control_cycle_timestamp_ns",
        "observation_assembled_timestamp_ns",
        "action_proposed_timestamp_ns",
        "action_issued_timestamp_ns",
        "action_applied_timestamp_ns",
        "action_hold_until_timestamp_ns",
        "deadline_timestamp_ns",
    )
    for field in timestamp_fields:
        _timestamp(sample[field], field)
    start = sample["inference_start_timestamp_ns"]
    end = sample["inference_end_timestamp_ns"]
    if (start is None) != (end is None):
        raise ValueError("Inference timestamps must be both present or both null")
    if start is not None:
        _timestamp(start, "inference_start_timestamp_ns")
        _timestamp(end, "inference_end_timestamp_ns")

    control = sample["control_cycle_timestamp_ns"]
    if prior_control is not None and control <= prior_control:
        raise ValueError("Control cycle timestamps must be strictly increasing")
    if any(value > control for value in sensor_times.values()):
        raise ValueError("Timing sample contains a future sensor frame")
    assembly = sample["observation_assembled_timestamp_ns"]
    proposed = sample["action_proposed_timestamp_ns"]
    issued = sample["action_issued_timestamp_ns"]
    applied = sample["action_applied_timestamp_ns"]
    hold_until = sample["action_hold_until_timestamp_ns"]
    ordered = [control, assembly]
    if start is not None:
        ordered.extend([start, end])
    ordered.extend([proposed, issued, applied, hold_until])
    if any(right < left for left, right in zip(ordered, ordered[1:])):
        raise ValueError("Timing sample timestamps violate causal order")


def _timestamp(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must use non-negative integer nanoseconds")
    return value


def _require_nonblank(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank")
    return value


def _base_certificate(contract: dict[str, Any]) -> dict[str, Any]:
    samples = []
    for index in range(4):
        control = (index + 1) * 100_000_000
        samples.append(
            {
                "cycle_index": index,
                "control_cycle_timestamp_ns": control,
                "sensor_frame_timestamps_ns": {
                    "sensor_a": control - 10_000_000,
                    "sensor_b": control - 8_000_000,
                },
                "observation_assembled_timestamp_ns": control + 5_000_000,
                "inference_start_timestamp_ns": control + 5_000_000,
                "inference_end_timestamp_ns": control + 25_000_000,
                "action_proposed_timestamp_ns": control + 25_000_000,
                "action_issued_timestamp_ns": control + 26_000_000,
                "action_applied_timestamp_ns": control + 31_000_000,
                "action_hold_until_timestamp_ns": control + 81_000_000,
                "deadline_timestamp_ns": control + 200_000_000,
                "observation_dropped": False,
            }
        )
    return sign_payload(
        {
            "schema_version": CERTIFICATE_SCHEMA_VERSION,
            "certificate_id": "t20_22_synthetic_passing_timing_fixture",
            "evidence_source": "synthetic_timing_fixture",
            "source_paired_trace_contract_identity_sha256": contract[
                "source_paired_trace_contract_identity_sha256"
            ],
            "source_simulator_trace_identity_sha256": contract[
                "source_simulator_trace_identity_sha256"
            ],
            "source_observable_trace_identity_sha256": contract[
                "source_observable_trace_identity_sha256"
            ],
            "source_paired_result_identity_sha256": contract[
                "source_paired_result_identity_sha256"
            ],
            "clock_sources": {
                key: "synthetic_monotonic_ns" for key in CLOCK_KEYS
            },
            "samples": samples,
        }
    )


def _exceed_frame_age(value: dict[str, Any]) -> None:
    sample = value["samples"][0]
    control = sample["control_cycle_timestamp_ns"]
    sample["sensor_frame_timestamps_ns"] = {
        "sensor_a": control - 60_000_000,
        "sensor_b": control - 58_000_000,
    }


def _exceed_frame_skew(value: dict[str, Any]) -> None:
    sample = value["samples"][0]
    control = sample["control_cycle_timestamp_ns"]
    sample["sensor_frame_timestamps_ns"] = {
        "sensor_a": control - 30_000_000,
        "sensor_b": control - 8_000_000,
    }


def _shift_timestamp_suffix(sample: dict[str, Any], delta: int, fields: tuple[str, ...]) -> None:
    for field in fields:
        if sample[field] is not None:
            sample[field] += delta


def _exceed_assembly(value: dict[str, Any]) -> None:
    sample = value["samples"][0]
    _shift_timestamp_suffix(
        sample,
        15_000_000,
        (
            "observation_assembled_timestamp_ns",
            "inference_start_timestamp_ns",
            "inference_end_timestamp_ns",
            "action_proposed_timestamp_ns",
            "action_issued_timestamp_ns",
            "action_applied_timestamp_ns",
            "action_hold_until_timestamp_ns",
        ),
    )


def _exceed_transport(value: dict[str, Any]) -> None:
    sample = value["samples"][0]
    sample["action_applied_timestamp_ns"] = sample["action_issued_timestamp_ns"] + 25_000_000
    sample["action_hold_until_timestamp_ns"] = sample["action_applied_timestamp_ns"] + 50_000_000


def _exceed_hold(value: dict[str, Any]) -> None:
    sample = value["samples"][0]
    sample["action_hold_until_timestamp_ns"] = sample["action_applied_timestamp_ns"] + 120_000_000


def _shift_cycle(sample: dict[str, Any], delta: int) -> None:
    sample["control_cycle_timestamp_ns"] += delta
    for key in sample["sensor_frame_timestamps_ns"]:
        sample["sensor_frame_timestamps_ns"][key] += delta
    for field in SAMPLE_FIELDS.difference(
        {"cycle_index", "sensor_frame_timestamps_ns", "observation_dropped"}
    ):
        if field != "control_cycle_timestamp_ns" and sample[field] is not None:
            sample[field] += delta


def _exceed_control_period(value: dict[str, Any]) -> None:
    for index, sample in enumerate(value["samples"]):
        _shift_cycle(sample, index * 20_000_000)


def _exceed_control_jitter(value: dict[str, Any]) -> None:
    _shift_cycle(value["samples"][1], 8_000_000)


def _exceed_inference(value: dict[str, Any]) -> None:
    sample = value["samples"][0]
    sample["inference_end_timestamp_ns"] = sample["inference_start_timestamp_ns"] + 60_000_000
    _shift_timestamp_suffix(
        sample,
        40_000_000,
        (
            "action_proposed_timestamp_ns",
            "action_issued_timestamp_ns",
            "action_applied_timestamp_ns",
            "action_hold_until_timestamp_ns",
        ),
    )


def _miss_deadline(value: dict[str, Any]) -> None:
    sample = value["samples"][0]
    sample["deadline_timestamp_ns"] = sample["action_applied_timestamp_ns"] - 1
