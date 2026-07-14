"""Fail-closed privileged and observable evaluator roles for T20.20."""

from __future__ import annotations

import copy
import math

from pathlib import Path
from typing import Any, Callable

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.strict_grasp import (
    STRICT_GRASP_PHASES,
    verify_strict_grasp_v2_fixture,
)


CONTRACT_SCHEMA_VERSION = "scenesmith.observer_role_evaluator_contract.v1"
FIXTURE_SCHEMA_VERSION = "scenesmith.observer_role_evaluator_fixture.v1"
TASK_PREDICATES = (
    "phase_sequence_complete",
    "antipodal_grasp_confirmed",
    "object_lift_clear",
    "stable_hold_valid",
    "object_gripper_drift_bounded",
    "release_complete",
    "retreat_complete",
    "safety_limits_respected",
)
ROLES = ("simulator_privileged", "hardware_observable")
COMMON_FIELDS = (
    "timestamp_ns",
    "evidence_source",
    "observed_phase_order",
    "actor_input_field_names",
)
OBSERVABLE_CONTEXT_FIELDS = (
    "measured_joint_positions_rad",
    "measured_joint_velocities_rad_s",
    "measured_action_rad",
    "measured_gripper_aperture_m",
    "measured_effort_ma",
)
OBSERVABLE_PREDICATE_FIELDS = (
    "grasp_event_observed",
    "lift_clear_event_observed",
    "stable_hold_event_observed",
    "drift_within_limit_event_observed",
    "release_event_observed",
    "retreat_event_observed",
    "safety_event_observed",
)
PRIVILEGED_FIELDS = (
    "bilateral_contact_count",
    "antipodal_proxy_valid",
    "object_lift_m",
    "object_table_contact_during_lift",
    "stable_hold_frame_count",
    "stable_hold_max_speed_m_s",
    "minimum_hold_contact_count",
    "maximum_object_gripper_drift_m",
    "release_contact_count",
    "release_aperture_m",
    "retreat_contact_count",
    "retreat_distance_m",
    "maximum_object_speed_m_s",
    "maximum_impact_force_n",
    "maximum_actuator_current_ma",
    "forbidden_collision_observed",
    "teleport_detected",
    "scripted_object_motion",
    "prohibited_mechanism_observed",
)
PRIVILEGED_ONLY_FIELDS = (
    *PRIVILEGED_FIELDS,
    "contact_force_exact",
    "contact_geometry_witness",
    "object_position_m",
    "object_table_contact",
    "privileged.object_pose",
    "simulator_privileged_state",
    "strict_evaluator_result",
)
PROHIBITED_ACTOR_FIELDS = {
    "observer_role_evaluator.task_success",
    "observer_role_evaluator.predicates",
    "privileged.object_pose",
    "simulator_privileged_state",
    "strict_evaluator_result",
}
STRICT_V2_PATH = Path("configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json")
REPO_ROOT = Path(__file__).resolve().parents[2]


def build_observer_role_evaluator_contract(
    strict_v2_fixture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the signed role and predicate-vocabulary contract."""

    strict_v2_fixture = strict_v2_fixture or load_strict_json(REPO_ROOT / STRICT_V2_PATH)
    verify_strict_grasp_v2_fixture(strict_v2_fixture)
    spec = strict_v2_fixture["evaluator_spec"]
    payload = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "source_strict_v2_identity_sha256": strict_v2_fixture["identity_sha256"],
        "ordered_phases": list(STRICT_GRASP_PHASES),
        "predicate_vocabulary": list(TASK_PREDICATES),
        "thresholds": {
            "minimum_fingertip_contacts": spec["minimum_fingertip_contacts"],
            "required_lift_clearance_m": spec["required_lift_clearance_m"],
            "minimum_stable_hold_frames": spec["minimum_stable_hold_frames"],
            "maximum_hold_object_speed_m_s": spec[
                "maximum_hold_object_speed_m_s"
            ],
            "maximum_object_gripper_relative_drift_m": spec[
                "maximum_object_gripper_relative_drift_m"
            ],
            "minimum_release_aperture_m": spec["minimum_release_aperture_m"],
            "minimum_retreat_distance_m": spec["minimum_retreat_distance_m"],
            "maximum_object_speed_m_s": spec["maximum_object_speed_m_s"],
            "maximum_impact_force_n": spec["maximum_impact_force_n"],
            "maximum_actuator_current_ma": spec["maximum_actuator_current_ma"],
        },
        "roles": {
            "simulator_privileged": {
                "predicate_vocabulary": list(TASK_PREDICATES),
                "allowed_fields": [*COMMON_FIELDS, *PRIVILEGED_FIELDS],
                "role_specific_fields": list(PRIVILEGED_FIELDS),
                "required_context_fields": [
                    "timestamp_ns",
                    "evidence_source",
                    "actor_input_field_names",
                ],
                "allowed_evidence_sources": ["simulator_privileged"],
                "evidence_scope": "simulator_geometry_contact_and_object_state",
            },
            "hardware_observable": {
                "predicate_vocabulary": list(TASK_PREDICATES),
                "allowed_fields": [
                    *COMMON_FIELDS,
                    *OBSERVABLE_CONTEXT_FIELDS,
                    *OBSERVABLE_PREDICATE_FIELDS,
                ],
                "role_specific_fields": [
                    *OBSERVABLE_CONTEXT_FIELDS,
                    *OBSERVABLE_PREDICATE_FIELDS,
                ],
                "required_context_fields": [
                    "timestamp_ns",
                    "evidence_source",
                    "actor_input_field_names",
                    *OBSERVABLE_CONTEXT_FIELDS,
                ],
                "privileged_only_fields": list(PRIVILEGED_ONLY_FIELDS),
                "evidence_scope": (
                    "declared_measured_robot_channels_and_external_task_events"
                ),
                "allowed_evidence_sources": [
                    "simulator_fixture_projection",
                    "physical_instrumentation",
                ],
            },
        },
        "missing_observation_policy": "predicate_false_with_not_observed_availability",
        "unknown_field_policy": "reject",
        "role_leakage_policy": "reject",
        "actor_input_policy": "evaluator_and_privileged_fields_prohibited",
        "camera_or_vlm_evidence_supported": False,
        "physical_qualification_supported": False,
    }
    return sign_payload(payload)


def evaluate_observer_role(
    contract: dict[str, Any],
    *,
    role: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate one declared role without filling missing observations."""

    verify_signed_payload(contract, label="observer role evaluator contract")
    _validate_contract(contract)
    if role not in ROLES:
        raise ValueError(f"Unknown observer role: {role!r}")
    if not isinstance(evidence, dict):
        raise ValueError("Observer evidence must be an object")

    role_contract = contract["roles"][role]
    evidence_fields = set(evidence)
    if role == "hardware_observable":
        leaked = evidence_fields.intersection(role_contract["privileged_only_fields"])
        if leaked:
            raise ValueError(
                "Observable evaluator role leakage: " + ", ".join(sorted(leaked))
            )
    unknown = evidence_fields.difference(role_contract["allowed_fields"])
    if unknown:
        raise ValueError("undeclared evidence field: " + ", ".join(sorted(unknown)))

    _validate_common_evidence(evidence)
    if (
        "evidence_source" in evidence
        and evidence["evidence_source"]
        not in role_contract["allowed_evidence_sources"]
    ):
        raise ValueError(
            f"Evidence source {evidence['evidence_source']!r} is not allowed for {role}"
        )
    if role == "hardware_observable":
        _validate_observable_evidence(evidence)
    else:
        _validate_privileged_evidence(evidence)

    evaluators = (
        _privileged_predicates(contract, evidence)
        if role == "simulator_privileged"
        else _observable_predicates(contract, evidence)
    )
    predicates: dict[str, dict[str, Any]] = {}
    for predicate_name in TASK_PREDICATES:
        required_fields, evaluator = evaluators[predicate_name]
        missing = [field for field in required_fields if field not in evidence]
        if missing:
            predicates[predicate_name] = {
                "role": role,
                "availability": "not_observed",
                "value": False,
                "reasons": [
                    f"required_observation_missing:{field}" for field in missing
                ],
            }
            continue
        value = evaluator()
        predicates[predicate_name] = {
            "role": role,
            "availability": "observed",
            "value": bool(value),
            "reasons": [] if value else [f"predicate_false:{predicate_name}"],
        }

    failures: list[str] = []
    actor_fields = evidence.get("actor_input_field_names", [])
    if any(_actor_field_is_prohibited(field) for field in actor_fields):
        failures.append("evaluator_state_leaked_to_actor")
    missing_context = [
        field
        for field in role_contract.get("required_context_fields", [])
        if field not in evidence
    ]
    failures.extend(
        f"required_context_missing:{field}" for field in missing_context
    )
    for predicate in predicates.values():
        failures.extend(predicate["reasons"])
    failures = list(dict.fromkeys(failures))
    return {
        "role": role,
        "evidence_source": evidence.get("evidence_source", "not_observed"),
        "predicate_vocabulary": list(TASK_PREDICATES),
        "predicates": predicates,
        "task_success": all(row["value"] for row in predicates.values())
        and not failures,
        "failure_reasons": failures,
        "physical_qualification": False,
        "authority_granted": [],
    }


def build_observer_role_evaluator_fixture(
    strict_v2_fixture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build fixed parity, missing-observation, and role-leakage evidence."""

    strict_v2_fixture = strict_v2_fixture or load_strict_json(REPO_ROOT / STRICT_V2_PATH)
    contract = build_observer_role_evaluator_contract(strict_v2_fixture)
    privileged_positive = _positive_privileged_evidence()
    observable_positive = _positive_observable_evidence()
    privileged_negative = copy.deepcopy(privileged_positive)
    privileged_negative["stable_hold_frame_count"] = 1
    observable_negative = copy.deepcopy(observable_positive)
    observable_negative["stable_hold_event_observed"] = False

    complete_cases = [
        _consistency_case(
            contract,
            "complete_positive",
            privileged_positive,
            observable_positive,
        ),
        _consistency_case(
            contract,
            "stable_hold_negative",
            privileged_negative,
            observable_negative,
        ),
    ]
    missing = copy.deepcopy(observable_positive)
    missing.pop("stable_hold_event_observed")
    missing_result = evaluate_observer_role(
        contract, role="hardware_observable", evidence=missing
    )
    leaked = copy.deepcopy(observable_positive)
    leaked["object_position_m"] = [0.22, 0.0, 0.365]
    spoofed = copy.deepcopy(observable_positive)
    spoofed["task_success"] = True

    report = sign_payload({
        "schema_version": "scenesmith.observer_role_simulator_consistency.v1",
        "complete_case_count": len(complete_cases),
        "complete_cases": complete_cases,
        "all_complete_cases_consistent": all(
            case["predicate_values_identical"] for case in complete_cases
        ),
        "missing_observation_rejected": (
            not missing_result["task_success"]
            and missing_result["predicates"]["stable_hold_valid"]["availability"]
            == "not_observed"
        ),
        "privileged_role_leakage_rejected": _raises_value_error(
            contract, leaked, "role leakage"
        ),
        "claimed_success_spoof_rejected": _raises_value_error(
            contract, spoofed, "undeclared evidence field"
        ),
        "scope": (
            "simulator_fixture_parity_not_hardware_observation_or_physical_qualification"
        ),
    })
    return sign_payload(
        {
            "schema_version": FIXTURE_SCHEMA_VERSION,
            "source_strict_v2_identity_sha256": strict_v2_fixture[
                "identity_sha256"
            ],
            "contract": contract,
            "cases": {
                "privileged_positive": privileged_positive,
                "observable_positive": observable_positive,
                "privileged_stable_hold_negative": privileged_negative,
                "observable_stable_hold_negative": observable_negative,
            },
            "simulator_consistency_report": report,
            "hardware_observation_performed": False,
            "camera_accessed": False,
            "physical_qualification_granted": False,
            "simulation_training_ready": False,
            "simulation_policy_accepted": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "optimizer_training": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "authority_granted": ["observer_role_evaluator_fixture_conformant"],
            "authority_not_granted": [
                "hardware_observation",
                "camera_access",
                "physical_qualification",
                "simulation_training_ready",
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
        }
    )


def verify_observer_role_evaluator_fixture(
    payload: dict[str, Any], strict_v2_fixture: dict[str, Any] | None = None
) -> None:
    """Reject signed drift from the strict-v2-bound deterministic fixture."""

    strict_v2_fixture = strict_v2_fixture or load_strict_json(REPO_ROOT / STRICT_V2_PATH)
    verify_signed_payload(payload, label="observer role evaluator fixture")
    if payload != build_observer_role_evaluator_fixture(strict_v2_fixture):
        raise ValueError("Observer role evaluator fixture drifted")


def _privileged_predicates(
    contract: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, tuple[tuple[str, ...], Callable[[], bool]]]:
    threshold = contract["thresholds"]
    return {
        "phase_sequence_complete": (
            ("observed_phase_order",),
            lambda: evidence["observed_phase_order"] == contract["ordered_phases"],
        ),
        "antipodal_grasp_confirmed": (
            ("bilateral_contact_count", "antipodal_proxy_valid"),
            lambda: evidence["bilateral_contact_count"]
            >= threshold["minimum_fingertip_contacts"]
            and evidence["antipodal_proxy_valid"],
        ),
        "object_lift_clear": (
            ("object_lift_m", "object_table_contact_during_lift"),
            lambda: evidence["object_lift_m"]
            >= threshold["required_lift_clearance_m"]
            and not evidence["object_table_contact_during_lift"],
        ),
        "stable_hold_valid": (
            (
                "stable_hold_frame_count",
                "stable_hold_max_speed_m_s",
                "minimum_hold_contact_count",
            ),
            lambda: evidence["stable_hold_frame_count"]
            >= threshold["minimum_stable_hold_frames"]
            and evidence["stable_hold_max_speed_m_s"]
            <= threshold["maximum_hold_object_speed_m_s"]
            and evidence["minimum_hold_contact_count"]
            >= threshold["minimum_fingertip_contacts"],
        ),
        "object_gripper_drift_bounded": (
            ("maximum_object_gripper_drift_m",),
            lambda: evidence["maximum_object_gripper_drift_m"]
            <= threshold["maximum_object_gripper_relative_drift_m"],
        ),
        "release_complete": (
            ("release_contact_count", "release_aperture_m"),
            lambda: evidence["release_contact_count"] == 0
            and evidence["release_aperture_m"]
            >= threshold["minimum_release_aperture_m"],
        ),
        "retreat_complete": (
            ("retreat_contact_count", "retreat_distance_m"),
            lambda: evidence["retreat_contact_count"] == 0
            and evidence["retreat_distance_m"]
            >= threshold["minimum_retreat_distance_m"],
        ),
        "safety_limits_respected": (
            (
                "maximum_object_speed_m_s",
                "maximum_impact_force_n",
                "maximum_actuator_current_ma",
                "forbidden_collision_observed",
                "teleport_detected",
                "scripted_object_motion",
                "prohibited_mechanism_observed",
            ),
            lambda: evidence["maximum_object_speed_m_s"]
            <= threshold["maximum_object_speed_m_s"]
            and evidence["maximum_impact_force_n"]
            <= threshold["maximum_impact_force_n"]
            and evidence["maximum_actuator_current_ma"]
            <= threshold["maximum_actuator_current_ma"]
            and not evidence["forbidden_collision_observed"]
            and not evidence["teleport_detected"]
            and not evidence["scripted_object_motion"]
            and not evidence["prohibited_mechanism_observed"],
        ),
    }


def _observable_predicates(
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, tuple[tuple[str, ...], Callable[[], bool]]]:
    mapping = {
        "antipodal_grasp_confirmed": "grasp_event_observed",
        "object_lift_clear": "lift_clear_event_observed",
        "stable_hold_valid": "stable_hold_event_observed",
        "object_gripper_drift_bounded": "drift_within_limit_event_observed",
        "release_complete": "release_event_observed",
        "retreat_complete": "retreat_event_observed",
        "safety_limits_respected": "safety_event_observed",
    }
    evaluators: dict[str, tuple[tuple[str, ...], Callable[[], bool]]] = {
        "phase_sequence_complete": (
            ("observed_phase_order",),
            lambda: evidence["observed_phase_order"] == contract["ordered_phases"],
        )
    }
    for predicate_name, field in mapping.items():
        evaluators[predicate_name] = ((field,), lambda field=field: evidence[field])
    return evaluators


def _validate_common_evidence(evidence: dict[str, Any]) -> None:
    if "timestamp_ns" in evidence:
        value = evidence["timestamp_ns"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("timestamp_ns must be a non-negative integer")
    if "evidence_source" in evidence and (
        not isinstance(evidence["evidence_source"], str)
        or not evidence["evidence_source"]
    ):
        raise ValueError("evidence_source must be a nonblank string")
    if "observed_phase_order" in evidence:
        phases = evidence["observed_phase_order"]
        if not isinstance(phases, list) or not all(
            isinstance(value, str) and value for value in phases
        ):
            raise ValueError("observed_phase_order must contain nonblank strings")
        if len(phases) != len(set(phases)):
            raise ValueError("observed_phase_order contains a duplicate phase")
    if "actor_input_field_names" in evidence:
        fields = evidence["actor_input_field_names"]
        if not isinstance(fields, list) or not all(
            isinstance(value, str) and value for value in fields
        ):
            raise ValueError("actor_input_field_names must contain nonblank strings")
        if len(fields) != len(set(fields)):
            raise ValueError("actor_input_field_names contains a duplicate field")


def _validate_observable_evidence(evidence: dict[str, Any]) -> None:
    for field in (
        "measured_joint_positions_rad",
        "measured_joint_velocities_rad_s",
        "measured_action_rad",
    ):
        if field in evidence:
            values = evidence[field]
            if not isinstance(values, list) or len(values) != 6:
                raise ValueError(f"{field} must contain six values")
            for value in values:
                _require_finite_number(value, field)
    for field in ("measured_gripper_aperture_m", "measured_effort_ma"):
        if field in evidence:
            _require_finite_number(evidence[field], field)
            if evidence[field] < 0:
                raise ValueError(f"{field} must be non-negative")
    for field in OBSERVABLE_PREDICATE_FIELDS:
        if field in evidence and not isinstance(evidence[field], bool):
            raise ValueError(f"{field} must be boolean")


def _validate_privileged_evidence(evidence: dict[str, Any]) -> None:
    boolean_fields = {
        "antipodal_proxy_valid",
        "object_table_contact_during_lift",
        "forbidden_collision_observed",
        "teleport_detected",
        "scripted_object_motion",
        "prohibited_mechanism_observed",
    }
    integer_fields = {
        "bilateral_contact_count",
        "stable_hold_frame_count",
        "minimum_hold_contact_count",
        "release_contact_count",
        "retreat_contact_count",
    }
    for field in boolean_fields.intersection(evidence):
        if not isinstance(evidence[field], bool):
            raise ValueError(f"{field} must be boolean")
    for field in integer_fields.intersection(evidence):
        value = evidence[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
    for field in set(PRIVILEGED_FIELDS).difference(boolean_fields, integer_fields):
        if field in evidence:
            _require_finite_number(evidence[field], field)
            if evidence[field] < 0:
                raise ValueError(f"{field} must be non-negative")


def _require_finite_number(value: Any, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{field} must be finite")


def _validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ValueError("Observer role evaluator contract schema is invalid")
    if contract.get("predicate_vocabulary") != list(TASK_PREDICATES):
        raise ValueError("Observer role evaluator predicate vocabulary is invalid")
    roles = contract.get("roles")
    if not isinstance(roles, dict) or set(roles) != set(ROLES):
        raise ValueError("Observer role evaluator roles are invalid")
    for role in ROLES:
        if roles[role].get("predicate_vocabulary") != list(TASK_PREDICATES):
            raise ValueError(f"Observer role {role} predicate vocabulary drifted")
    if contract != build_observer_role_evaluator_contract():
        raise ValueError("Observer role evaluator contract drifted from strict-v2")


def _actor_field_is_prohibited(field: str) -> bool:
    return field in PROHIBITED_ACTOR_FIELDS or field.startswith(
        (
            "observer_role_evaluator.",
            "privileged.",
            "simulator_privileged_state.",
            "strict_evaluator_result.",
        )
    )


def _positive_privileged_evidence() -> dict[str, Any]:
    return {
        "timestamp_ns": 1_000_000_000,
        "evidence_source": "simulator_privileged",
        "observed_phase_order": list(STRICT_GRASP_PHASES),
        "actor_input_field_names": ["observation.state", "task"],
        "bilateral_contact_count": 2,
        "antipodal_proxy_valid": True,
        "object_lift_m": 0.04,
        "object_table_contact_during_lift": False,
        "stable_hold_frame_count": 2,
        "stable_hold_max_speed_m_s": 0.006,
        "minimum_hold_contact_count": 2,
        "maximum_object_gripper_drift_m": 0.0,
        "release_contact_count": 0,
        "release_aperture_m": 0.03,
        "retreat_contact_count": 0,
        "retreat_distance_m": 0.085,
        "maximum_object_speed_m_s": 0.12,
        "maximum_impact_force_n": 1.2,
        "maximum_actuator_current_ma": 360.0,
        "forbidden_collision_observed": False,
        "teleport_detected": False,
        "scripted_object_motion": False,
        "prohibited_mechanism_observed": False,
    }


def _positive_observable_evidence() -> dict[str, Any]:
    return {
        "timestamp_ns": 1_000_000_000,
        "evidence_source": "simulator_fixture_projection",
        "observed_phase_order": list(STRICT_GRASP_PHASES),
        "actor_input_field_names": ["observation.state", "task"],
        "measured_joint_positions_rad": [0.0] * 6,
        "measured_joint_velocities_rad_s": [0.0] * 6,
        "measured_action_rad": [0.0] * 6,
        "measured_gripper_aperture_m": 0.03,
        "measured_effort_ma": 360.0,
        "grasp_event_observed": True,
        "lift_clear_event_observed": True,
        "stable_hold_event_observed": True,
        "drift_within_limit_event_observed": True,
        "release_event_observed": True,
        "retreat_event_observed": True,
        "safety_event_observed": True,
    }


def _consistency_case(
    contract: dict[str, Any],
    case_id: str,
    privileged: dict[str, Any],
    observable: dict[str, Any],
) -> dict[str, Any]:
    privileged_result = evaluate_observer_role(
        contract, role="simulator_privileged", evidence=privileged
    )
    observable_result = evaluate_observer_role(
        contract, role="hardware_observable", evidence=observable
    )
    privileged_values = {
        key: row["value"] for key, row in privileged_result["predicates"].items()
    }
    observable_values = {
        key: row["value"] for key, row in observable_result["predicates"].items()
    }
    return {
        "case_id": case_id,
        "privileged_result": privileged_result,
        "observable_result": observable_result,
        "predicate_values_identical": privileged_values == observable_values,
    }


def _raises_value_error(
    contract: dict[str, Any], evidence: dict[str, Any], expected_text: str
) -> bool:
    try:
        evaluate_observer_role(
            contract, role="hardware_observable", evidence=evidence
        )
    except ValueError as exc:
        return expected_text.lower() in str(exc).lower()
    return False
