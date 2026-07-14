"""Immutable offline joint/action/event trace comparison for T20.21."""

from __future__ import annotations

import copy
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.observer_role_evaluator import (
    verify_observer_role_evaluator_fixture,
)


CONTRACT_SCHEMA_VERSION = "scenesmith.paired_trace_runner_contract.v1"
TRACE_SCHEMA_VERSION = "scenesmith.paired_joint_action_event_trace.v1"
RESULT_SCHEMA_VERSION = "scenesmith.paired_trace_comparison.v1"
FIXTURE_SCHEMA_VERSION = "scenesmith.paired_trace_runner_fixture.v1"
OBSERVER_PATH = Path("configurations/robot_lab/t20_20_observer_role_evaluator.json")
REPO_ROOT = Path(__file__).resolve().parents[2]
ROLES = ("simulator_privileged", "hardware_observable")
TRACE_FIELDS = {
    "schema_version",
    "trace_id",
    "observer_role",
    "evidence_source",
    "clock_source",
    "q0_rad",
    "frames",
    "identity_sha256",
}
FRAME_FIELDS = {
    "frame_index",
    "timestamp_ns",
    "joint_position_rad",
    "proposed_action_rad",
    "issued_action_rad",
    "measured_action_rad",
    "events",
}
PRIVILEGED_TRACE_FIELDS = {
    "contact_force_exact",
    "contact_geometry_witness",
    "object_position_m",
    "privileged.object_pose",
    "simulator_privileged_state",
    "strict_evaluator_result",
}
EVENT_TYPES = (
    "grasp_contact",
    "object_lift_clear",
    "stable_hold",
    "release_complete",
    "retreat_complete",
)
MISMATCH_CATEGORIES = (
    "common_q0_mismatch",
    "trace_length_mismatch",
    "proposed_command_mismatch",
    "clock_source_mismatch",
    "issued_action_mismatch",
    "measured_action_mismatch",
    "joint_tracking_mismatch",
    "event_presence_mismatch",
    "event_time_mismatch",
)


def build_paired_trace_runner_contract(
    observer_fixture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the signed trace schemas and fixed diagnostic thresholds."""

    observer_fixture = observer_fixture or load_strict_json(REPO_ROOT / OBSERVER_PATH)
    verify_observer_role_evaluator_fixture(observer_fixture)
    return sign_payload(
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "source_observer_fixture_identity_sha256": observer_fixture[
                "identity_sha256"
            ],
            "trace_schema_version": TRACE_SCHEMA_VERSION,
            "result_schema_version": RESULT_SCHEMA_VERSION,
            "roles": list(ROLES),
            "joint_count": 6,
            "trace_fields": sorted(TRACE_FIELDS),
            "frame_fields": sorted(FRAME_FIELDS),
            "event_types": list(EVENT_TYPES),
            "mismatch_categories": list(MISMATCH_CATEGORIES),
            "thresholds": {
                "joint_max_abs_error_rad": 0.01,
                "issued_action_max_abs_error_rad": 0.01,
                "measured_action_max_abs_error_rad": 0.01,
                "event_elapsed_time_abs_error_ns": 20_000_000,
            },
            "allowed_evidence_sources": {
                "simulator_privileged": [
                    "synthetic_simulator_fixture",
                    "simulator_trace",
                ],
                "hardware_observable": [
                    "synthetic_observable_fixture",
                    "physical_instrumentation",
                ],
            },
            "common_q0_policy": "exact_before_diagnostic_comparison",
            "proposed_command_policy": "exact_sequence_before_causal_interpretation",
            "action_variant_policy": "proposed_issued_measured_remain_distinct",
            "timestamp_policy": "integer_nanoseconds_strictly_increasing_per_trace",
            "clock_policy": "identity_preserved_synchronization_not_inferred",
            "pixel_comparison_supported": False,
            "calibration_or_twin_update_supported": False,
            "physical_qualification_supported": False,
        }
    )


def compare_paired_traces(
    contract: dict[str, Any],
    simulator_trace: dict[str, Any],
    observable_trace: dict[str, Any],
) -> dict[str, Any]:
    """Validate and compare two signed traces without mutating either input."""

    _validate_contract(contract)
    _validate_trace(contract, simulator_trace, expected_role="simulator_privileged")
    _validate_trace(contract, observable_trace, expected_role="hardware_observable")
    if simulator_trace["trace_id"] == observable_trace["trace_id"]:
        raise ValueError("Paired traces must have distinct trace_id values")

    sim_frames = simulator_trace["frames"]
    obs_frames = observable_trace["frames"]
    paired_count = min(len(sim_frames), len(obs_frames))
    common_q0 = simulator_trace["q0_rad"] == observable_trace["q0_rad"]
    length_identical = len(sim_frames) == len(obs_frames)
    proposed_identical = (
        length_identical
        and [row["proposed_action_rad"] for row in sim_frames]
        == [row["proposed_action_rad"] for row in obs_frames]
    )
    clock_identical = (
        simulator_trace["clock_source"] == observable_trace["clock_source"]
    )
    downstream_eligible = common_q0 and length_identical and proposed_identical

    joint_errors = (
        _paired_vector_errors(sim_frames, obs_frames, "joint_position_rad", paired_count)
        if downstream_eligible
        else []
    )
    issued_errors = (
        _paired_vector_errors(sim_frames, obs_frames, "issued_action_rad", paired_count)
        if downstream_eligible
        else []
    )
    measured_errors = (
        _paired_vector_errors(sim_frames, obs_frames, "measured_action_rad", paired_count)
        if downstream_eligible
        else []
    )
    joint_max = max(joint_errors, default=0.0)
    issued_max = max(issued_errors, default=0.0)
    measured_max = max(measured_errors, default=0.0)
    joint_rmse = math.sqrt(
        sum(value * value for value in joint_errors) / len(joint_errors)
    ) if joint_errors else 0.0

    sim_events = _event_elapsed_times(sim_frames) if downstream_eligible else {}
    obs_events = _event_elapsed_times(obs_frames) if downstream_eligible else {}
    sim_event_names = set(sim_events)
    obs_event_names = set(obs_events)
    event_presence_identical = sim_event_names == obs_event_names
    event_time_eligible = downstream_eligible and clock_identical
    event_deltas = {
        event: obs_events[event] - sim_events[event]
        for event in sorted(sim_event_names.intersection(obs_event_names))
    } if event_time_eligible else {}
    max_event_delta = max((abs(value) for value in event_deltas.values()), default=0)

    thresholds = contract["thresholds"]
    categories: list[str] = []
    if not common_q0:
        categories.append("common_q0_mismatch")
    if not length_identical:
        categories.append("trace_length_mismatch")
    if not proposed_identical:
        categories.append("proposed_command_mismatch")
    if not clock_identical:
        categories.append("clock_source_mismatch")
    if issued_max > thresholds["issued_action_max_abs_error_rad"]:
        categories.append("issued_action_mismatch")
    if measured_max > thresholds["measured_action_max_abs_error_rad"]:
        categories.append("measured_action_mismatch")
    if joint_max > thresholds["joint_max_abs_error_rad"]:
        categories.append("joint_tracking_mismatch")
    if not event_presence_identical:
        categories.append("event_presence_mismatch")
    if max_event_delta > thresholds["event_elapsed_time_abs_error_ns"]:
        categories.append("event_time_mismatch")

    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "contract_identity_sha256": contract["identity_sha256"],
            "simulator_trace_identity_sha256": simulator_trace["identity_sha256"],
            "observable_trace_identity_sha256": observable_trace["identity_sha256"],
            "simulator_evidence_source": simulator_trace["evidence_source"],
            "observable_evidence_source": observable_trace["evidence_source"],
            "simulator_clock_source": simulator_trace["clock_source"],
            "observable_clock_source": observable_trace["clock_source"],
            "simulator_frame_count": len(sim_frames),
            "observable_frame_count": len(obs_frames),
            "paired_frame_count": paired_count,
            "common_q0_identical": common_q0,
            "proposed_command_sequence_identical": proposed_identical,
            "downstream_comparison_eligible": downstream_eligible,
            "joint_max_abs_error_rad": joint_max,
            "joint_rmse_rad": joint_rmse,
            "issued_action_max_abs_error_rad": issued_max,
            "measured_action_max_abs_error_rad": measured_max,
            "event_presence_identical": event_presence_identical,
            "event_time_comparison_eligible": event_time_eligible,
            "event_elapsed_time_delta_ns": event_deltas,
            "maximum_event_elapsed_time_abs_error_ns": max_event_delta,
            "mismatch_categories": categories,
            "matched": not categories,
            "pixel_comparison_performed": False,
            "clock_synchronization_inferred": False,
            "calibration_update_selected": False,
            "twin_update_selected": False,
            "physical_qualification": False,
            "authority_granted": [],
        }
    )


def build_paired_trace_runner_fixture(
    observer_fixture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build matched and one-factor diagnostic synthetic trace cases."""

    observer_fixture = observer_fixture or load_strict_json(REPO_ROOT / OBSERVER_PATH)
    contract = build_paired_trace_runner_contract(observer_fixture)
    simulator = _base_trace("simulator_privileged")
    observable = _base_trace("hardware_observable")
    matched = compare_paired_traces(contract, simulator, observable)

    mutations = {
        "common_q0_mismatch": _shift_q0,
        "trace_length_mismatch": lambda trace: trace["frames"].pop(),
        "proposed_command_mismatch": lambda trace: trace["frames"][1][
            "proposed_action_rad"
        ].__setitem__(0, 0.22),
        "clock_source_mismatch": lambda trace: trace.__setitem__(
            "clock_source", "synthetic_monotonic_ns_alt"
        ),
        "issued_action_mismatch": lambda trace: trace["frames"][1][
            "issued_action_rad"
        ].__setitem__(0, 0.22),
        "measured_action_mismatch": lambda trace: trace["frames"][1][
            "measured_action_rad"
        ].__setitem__(0, 0.22),
        "joint_tracking_mismatch": lambda trace: trace["frames"][1][
            "joint_position_rad"
        ].__setitem__(0, 0.12),
        "event_presence_mismatch": lambda trace: trace["frames"][3][
            "events"
        ].remove("release_complete"),
        "event_time_mismatch": _shift_grasp_event,
    }
    diagnostics: dict[str, dict[str, Any]] = {}
    for category in MISMATCH_CATEGORIES:
        changed = copy.deepcopy(observable)
        mutations[category](changed)
        changed.pop("identity_sha256")
        changed = sign_payload(changed)
        diagnostics[category] = {
            "expected_mismatch_category": category,
            "observable_trace_identity_sha256": changed["identity_sha256"],
            "result": compare_paired_traces(contract, simulator, changed),
        }

    return sign_payload(
        {
            "schema_version": FIXTURE_SCHEMA_VERSION,
            "source_observer_fixture_identity_sha256": observer_fixture[
                "identity_sha256"
            ],
            "contract": contract,
            "traces": {
                "simulator": simulator,
                "observable": observable,
            },
            "matched_result": matched,
            "diagnostic_cases": diagnostics,
            "all_mismatch_categories_routed": all(
                category in diagnostics[category]["result"]["mismatch_categories"]
                for category in MISMATCH_CATEGORIES
            ),
            "evidence_scope": "synthetic_offline_trace_fixture_only",
            "hardware_observation_performed": False,
            "live_robot_executed": False,
            "camera_accessed": False,
            "pixel_comparison_performed": False,
            "clock_synchronization_proven": False,
            "calibration_updated": False,
            "twin_updated": False,
            "physical_qualification_granted": False,
            "simulation_policy_accepted": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "optimizer_training": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "authority_granted": ["offline_paired_trace_runner_fixture_conformant"],
            "authority_not_granted": [
                "hardware_observation",
                "live_robot_execution",
                "camera_access",
                "clock_synchronization",
                "calibration_update",
                "twin_update",
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


def verify_paired_trace_runner_fixture(
    payload: dict[str, Any], observer_fixture: dict[str, Any] | None = None
) -> None:
    """Reject signed drift from the deterministic observer-bound fixture."""

    observer_fixture = observer_fixture or load_strict_json(REPO_ROOT / OBSERVER_PATH)
    verify_signed_payload(payload, label="paired trace runner fixture")
    if payload != build_paired_trace_runner_fixture(observer_fixture):
        raise ValueError("Paired trace runner fixture drifted")


def _validate_contract(contract: dict[str, Any]) -> None:
    verify_signed_payload(contract, label="paired trace runner contract")
    if contract != build_paired_trace_runner_contract():
        raise ValueError("Paired trace runner contract drifted")


def _validate_trace(
    contract: dict[str, Any], trace: dict[str, Any], *, expected_role: str
) -> None:
    if not isinstance(trace, dict):
        raise ValueError("Paired trace must be an object")
    unknown = set(trace).difference(TRACE_FIELDS)
    if unknown:
        raise ValueError("undeclared trace field: " + ", ".join(sorted(unknown)))
    missing = TRACE_FIELDS.difference(trace)
    if missing:
        raise ValueError("missing trace field: " + ", ".join(sorted(missing)))
    if trace["schema_version"] != TRACE_SCHEMA_VERSION:
        raise ValueError("Paired trace schema is invalid")
    if trace["observer_role"] != expected_role:
        raise ValueError(f"Expected {expected_role} trace")
    _require_identifier(trace["trace_id"], "trace_id")
    _require_nonblank(trace["clock_source"], "clock_source")
    if trace["evidence_source"] not in contract["allowed_evidence_sources"][expected_role]:
        raise ValueError("Trace evidence source is not allowed for its role")
    _finite_vector(trace["q0_rad"], contract["joint_count"], "q0_rad")

    frames = trace["frames"]
    if not isinstance(frames, list) or len(frames) < 2:
        raise ValueError("Paired trace must contain at least two frames")
    prior_timestamp: int | None = None
    observed_events: set[str] = set()
    for expected_index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError("Paired trace frame must be an object")
        frame_fields = set(frame)
        if expected_role == "hardware_observable":
            leaked = frame_fields.intersection(PRIVILEGED_TRACE_FIELDS)
            if leaked:
                raise ValueError("Observable trace role leakage: " + ", ".join(sorted(leaked)))
        unknown_frame = frame_fields.difference(FRAME_FIELDS)
        if unknown_frame:
            raise ValueError(
                "undeclared frame field: " + ", ".join(sorted(unknown_frame))
            )
        missing_frame = FRAME_FIELDS.difference(frame_fields)
        if missing_frame:
            raise ValueError("missing frame field: " + ", ".join(sorted(missing_frame)))
        if (
            isinstance(frame["frame_index"], bool)
            or not isinstance(frame["frame_index"], int)
            or frame["frame_index"] != expected_index
        ):
            raise ValueError("Paired trace frame indices must be contiguous")
        timestamp = frame["timestamp_ns"]
        if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp < 0:
            raise ValueError("timestamp_ns must be a non-negative integer")
        if prior_timestamp is not None and timestamp <= prior_timestamp:
            raise ValueError("Paired trace timestamps must be strictly increasing")
        prior_timestamp = timestamp
        for field in (
            "joint_position_rad",
            "proposed_action_rad",
            "issued_action_rad",
            "measured_action_rad",
        ):
            _finite_vector(frame[field], contract["joint_count"], field)
        events = frame["events"]
        if not isinstance(events, list) or not all(event in EVENT_TYPES for event in events):
            raise ValueError("Paired trace events are invalid")
        if len(events) != len(set(events)):
            raise ValueError("Paired trace frame contains a duplicate event")
        for event in events:
            if event in observed_events:
                raise ValueError("Paired trace contains a duplicate event")
            observed_events.add(event)
    if frames[0]["joint_position_rad"] != trace["q0_rad"]:
        raise ValueError("Paired trace first joint position must equal declared q0")
    verify_signed_payload(trace, label=f"{expected_role} paired trace")


def _finite_vector(value: Any, width: int, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != width:
        raise ValueError(f"{label} must contain six values")
    result: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{label} must contain finite values")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError(f"{label} must contain finite values")
        result.append(number)
    return result


def _require_nonblank(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank")
    return value


def _require_identifier(value: Any, label: str) -> str:
    identifier = _require_nonblank(value, label)
    if identifier in {".", ".."} or "/" in identifier or "\\" in identifier:
        raise ValueError(f"{label} must not contain a path alias")
    return identifier


def _paired_vector_errors(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    field: str,
    count: int,
) -> list[float]:
    return [
        abs(float(left[index][field][joint]) - float(right[index][field][joint]))
        for index in range(count)
        for joint in range(6)
    ]


def _event_elapsed_times(frames: list[dict[str, Any]]) -> dict[str, int]:
    origin = frames[0]["timestamp_ns"]
    return {
        event: frame["timestamp_ns"] - origin
        for frame in frames
        for event in frame["events"]
    }


def _base_trace(role: str) -> dict[str, Any]:
    q0 = [0.0] * 6
    targets = (0.0, 0.1, 0.2, 0.3)
    events = ((), ("grasp_contact",), ("stable_hold",), ("release_complete",))
    frames = []
    for index, target in enumerate(targets):
        vector = [target, 0.0, 0.0, 0.0, 0.0, 0.0]
        frames.append(
            {
                "frame_index": index,
                "timestamp_ns": index * 100_000_000,
                "joint_position_rad": list(vector),
                "proposed_action_rad": list(vector),
                "issued_action_rad": list(vector),
                "measured_action_rad": list(vector),
                "events": list(events[index]),
            }
        )
    source = (
        "synthetic_simulator_fixture"
        if role == "simulator_privileged"
        else "synthetic_observable_fixture"
    )
    return sign_payload(
        {
            "schema_version": TRACE_SCHEMA_VERSION,
            "trace_id": f"t20_21_{role}_matched_fixture",
            "observer_role": role,
            "evidence_source": source,
            "clock_source": "synthetic_monotonic_ns",
            "q0_rad": q0,
            "frames": frames,
        }
    )


def _shift_grasp_event(trace: dict[str, Any]) -> None:
    trace["frames"][1]["events"].remove("grasp_contact")
    trace["frames"][2]["events"].append("grasp_contact")


def _shift_q0(trace: dict[str, Any]) -> None:
    trace["q0_rad"][0] = 0.02
    trace["frames"][0]["joint_position_rad"][0] = 0.02
