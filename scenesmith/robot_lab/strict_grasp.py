"""Strict grasp semantics and deterministic analytic adversarial traces."""

from __future__ import annotations

import copy
import math

from typing import Any

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload


STRICT_GRASP_SPEC_SCHEMA_VERSION = "scenesmith.strict_grasp_spec.v1"
STRICT_GRASP_FIXTURE_SCHEMA_VERSION = "scenesmith.strict_grasp_fixture.v1"
STRICT_GRASP_PHASES = (
    "approach",
    "pregrasp",
    "close",
    "grasp_confirmed",
    "lift",
    "stable_hold",
    "lower",
    "release",
    "retreat",
)
PHYSICAL_ANCHOR_FRAME_SHA256 = (
    "165815e34f85d74b216080ddb17eb84feb9b0e8690db6c4f73e9cb240e6803f6"
)


def strict_grasp_spec() -> dict[str, Any]:
    """Return the declared analytic-simulation evaluator contract."""

    return sign_payload(
        {
            "schema_version": STRICT_GRASP_SPEC_SCHEMA_VERSION,
            "object_id": "analytic_turquoise_anchor_cousin_v1",
            "ordered_phases": list(STRICT_GRASP_PHASES),
            "table_top_z_m": 0.31,
            "object_half_height_m": 0.015,
            "required_lift_clearance_m": 0.025,
            "minimum_fingertip_contacts": 2,
            "minimum_stable_hold_frames": 2,
            "maximum_hold_object_speed_m_s": 0.02,
            "maximum_object_gripper_relative_drift_m": 0.01,
            "maximum_object_speed_m_s": 0.25,
            "maximum_impact_force_n": 5.0,
            "maximum_actuator_current_ma": 600.0,
            "minimum_release_aperture_m": 0.025,
            "minimum_retreat_distance_m": 0.08,
            "prohibited_actor_observation_fields": [
                "contact_force_exact",
                "evaluator.grasp_confirmed",
                "privileged.object_pose",
                "strict_grasp_success",
            ],
            "source_mode": "analytic_simulation_fixture",
            "physical_measurement_claimed": False,
        }
    )


def analytic_grasp_trajectory(
    spec: dict[str, Any],
    *,
    controller_owner: str = "analytic_grasp_expert",
    control_mode: str = "analytic_expert",
) -> list[dict[str, Any]]:
    """Create one ordered object-relative analytic grasp trace."""

    verify_signed_payload(spec, label="strict grasp spec")
    object_id = spec["object_id"]
    rest = [0.22, 0.0, 0.325]
    lifted = [0.22, 0.0, 0.365]
    actor_fields = ["observation.images.base_0_rgb", "observation.state"]
    rows = [
        ("approach", rest, [0.22, 0.0, 0.42], 0, True, 0.0, 0.0, 40.0, "free_motion", 0.03),
        ("pregrasp", rest, [0.22, 0.0, 0.37], 0, True, 0.0, 0.0, 55.0, "free_motion", 0.03),
        ("close", rest, [0.22, 0.0, 0.345], 2, True, 0.0, 1.2, 350.0, "grasp_contact", 0.012),
        (
            "grasp_confirmed",
            rest,
            [0.22, 0.0, 0.345],
            2,
            True,
            0.0,
            0.4,
            330.0,
            "grasp_contact",
            0.012,
        ),
        (
            "lift",
            lifted,
            [0.22, 0.0, 0.385],
            2,
            False,
            0.12,
            0.2,
            360.0,
            "grasped_transport",
            0.012,
        ),
        (
            "stable_hold",
            lifted,
            [0.22, 0.0, 0.385],
            2,
            False,
            0.006,
            0.1,
            325.0,
            "grasped_transport",
            0.012,
        ),
        (
            "stable_hold",
            lifted,
            [0.22, 0.0, 0.385],
            2,
            False,
            0.004,
            0.1,
            320.0,
            "grasped_transport",
            0.012,
        ),
        ("lower", rest, [0.22, 0.0, 0.345], 2, True, 0.10, 0.4, 340.0, "grasped_transport", 0.012),
        ("release", rest, [0.22, 0.0, 0.345], 0, True, 0.0, 0.1, 80.0, "release", 0.03),
        ("retreat", rest, [0.22, 0.0, 0.43], 0, True, 0.0, 0.0, 45.0, "free_motion", 0.03),
    ]
    return [
        {
            "timestamp_ns": (index + 1) * 100_000_000,
            "phase": phase,
            "object_id": object_id,
            "controller_owner": controller_owner,
            "control_mode": control_mode,
            "object_position_m": object_position,
            "gripper_position_m": gripper_position,
            "fingertip_contacts": contacts,
            "object_table_contact": table_contact,
            "object_speed_m_s": speed,
            "impact_force_n": impact,
            "actuator_current_ma_max": current,
            "mechanism": mechanism,
            "gripper_aperture_m": aperture,
            "forbidden_collision": False,
            "scripted_object_motion": False,
            "teleport_detected": False,
            "actor_observation_fields": list(actor_fields),
        }
        for index, (
            phase,
            object_position,
            gripper_position,
            contacts,
            table_contact,
            speed,
            impact,
            current,
            mechanism,
            aperture,
        ) in enumerate(rows)
    ]


def evaluate_strict_grasp(
    spec: dict[str, Any],
    trajectory: list[dict[str, Any]],
    *,
    claimed_proof_mode: str,
) -> dict[str, Any]:
    """Evaluate one trace while keeping semantic and pure-policy proof distinct."""

    verify_signed_payload(spec, label="strict grasp spec")
    if not trajectory:
        raise ValueError("Strict grasp trajectory cannot be empty")
    _validate_frames(trajectory)
    reasons: list[str] = []
    observed_phases = _compressed_phases(trajectory)
    if observed_phases != spec["ordered_phases"]:
        reasons.append("phase_order_invalid")
    if any(frame["object_id"] != spec["object_id"] for frame in trajectory):
        reasons.append("wrong_object")

    mechanisms = {frame["mechanism"] for frame in trajectory}
    if mechanisms & {"push", "slide"}:
        reasons.append("pushing_or_sliding_without_grasp")
    if mechanisms & {"hook", "table_pin"}:
        reasons.append("hooking_or_table_pinning")
    if mechanisms & {"throw", "ballistic"}:
        reasons.append("throwing_or_ballistic_motion")
    if any(frame["teleport_detected"] for frame in trajectory):
        reasons.append("teleport_detected")
    if any(frame["scripted_object_motion"] for frame in trajectory):
        reasons.append("scripted_object_motion")
    if any(frame["forbidden_collision"] for frame in trajectory):
        reasons.append("forbidden_collision")

    prohibited_fields = set(spec["prohibited_actor_observation_fields"])
    if any(
        prohibited_fields.intersection(frame["actor_observation_fields"])
        for frame in trajectory
    ):
        reasons.append("evaluator_state_leaked_to_actor")
    if any(frame["object_speed_m_s"] > spec["maximum_object_speed_m_s"] for frame in trajectory):
        reasons.append("object_speed_limit_exceeded")
    if any(frame["impact_force_n"] > spec["maximum_impact_force_n"] for frame in trajectory):
        reasons.append("impact_limit_exceeded")
    if any(
        frame["actuator_current_ma_max"] > spec["maximum_actuator_current_ma"]
        for frame in trajectory
    ):
        reasons.append("current_limit_exceeded")

    confirmed = _phase_rows(trajectory, "grasp_confirmed")
    if not confirmed or confirmed[0]["fingertip_contacts"] < spec["minimum_fingertip_contacts"]:
        reasons.append("valid_grasp_contact_missing")
    lift = _phase_rows(trajectory, "lift")
    required_z = (
        spec["table_top_z_m"]
        + spec["object_half_height_m"]
        + spec["required_lift_clearance_m"]
    )
    if not lift or lift[0]["object_position_m"][2] < required_z or lift[0]["object_table_contact"]:
        reasons.append("object_not_clear_of_table")
    hold = _phase_rows(trajectory, "stable_hold")
    if len(hold) < spec["minimum_stable_hold_frames"]:
        reasons.append("stable_hold_too_short")
    elif any(
        frame["object_speed_m_s"] > spec["maximum_hold_object_speed_m_s"]
        or frame["object_table_contact"]
        or frame["fingertip_contacts"] < spec["minimum_fingertip_contacts"]
        for frame in hold
    ):
        reasons.append("stable_hold_invalid")
    if confirmed:
        reference = _relative_position(confirmed[0])
        grasped = [
            frame
            for frame in trajectory
            if frame["phase"] in {"lift", "stable_hold", "lower"}
        ]
        if any(
            _distance(_relative_position(frame), reference)
            > spec["maximum_object_gripper_relative_drift_m"]
            for frame in grasped
        ):
            reasons.append("object_to_gripper_drift_exceeded")

    release = _phase_rows(trajectory, "release")
    if (
        not release
        or release[0]["fingertip_contacts"] != 0
        or release[0]["gripper_aperture_m"] < spec["minimum_release_aperture_m"]
    ):
        reasons.append("release_invalid")
    retreat = _phase_rows(trajectory, "retreat")
    if (
        not retreat
        or retreat[0]["fingertip_contacts"] != 0
        or _distance(
            retreat[0]["gripper_position_m"], retreat[0]["object_position_m"]
        )
        < spec["minimum_retreat_distance_m"]
    ):
        reasons.append("retreat_invalid")

    pure_trace = all(
        frame["controller_owner"] == "policy" and frame["control_mode"] == "policy"
        for frame in trajectory
    )
    if claimed_proof_mode == "strict_policy" and not pure_trace:
        reasons.append("controller_assistance_relabelled_as_policy")
    elif claimed_proof_mode not in {"strict_policy", "analytic_expert"}:
        reasons.append("unsupported_proof_mode")
    reasons = list(dict.fromkeys(reasons))
    success = not reasons
    proof_mode = claimed_proof_mode if success else "invalid"
    return {
        "strict_grasp_success": success,
        "pure_policy_success": success and pure_trace,
        "proof_mode": proof_mode,
        "observed_phase_order": observed_phases,
        "failure_reasons": reasons,
    }


def build_strict_grasp_fixture() -> dict[str, Any]:
    """Build one positive and adversarial negatives through the same evaluator."""

    spec = strict_grasp_spec()
    positive_trace = analytic_grasp_trajectory(spec)
    positive = {
        "trajectory": positive_trace,
        "evaluation": evaluate_strict_grasp(
            spec, positive_trace, claimed_proof_mode="analytic_expert"
        ),
    }
    negatives = []
    for case_id, expected, claimed, mutation in _negative_cases():
        trajectory = copy.deepcopy(positive_trace)
        _apply_negative_mutation(trajectory, mutation)
        negatives.append(
            {
                "case_id": case_id,
                "expected_failure_reason": expected,
                "claimed_proof_mode": claimed,
                "trajectory": trajectory,
                "evaluation": evaluate_strict_grasp(
                    spec,
                    trajectory,
                    claimed_proof_mode=claimed,
                ),
            }
        )
    return sign_payload(
        {
            "schema_version": STRICT_GRASP_FIXTURE_SCHEMA_VERSION,
            "evidence_mode": "analytic_simulation_strict_grasp_fixture",
            "qualification_scope": "evaluator_semantics_not_mujoco_or_physical_success",
            "physical_anchor_observation": {
                "candidate_object_id": "visible_turquoise_rectangular_anchor_candidate_01",
                "session_id": "t16-5c-20260713-0958-cdt",
                "external_frame_sha256": PHYSICAL_ANCHOR_FRAME_SHA256,
                "visible_description": "small_lightweight_turquoise_rectangular_object",
                "dimensions_m": None,
                "mass_kg": None,
                "com_assumption": None,
                "material": None,
                "friction": None,
                "pose_transform": None,
                "measurements_complete": False,
            },
            "simulation_anchor_cousin": {
                "object_id": spec["object_id"],
                "source_mode": "declared_nominal_analytic_simulation_fixture",
                "dimensions_m": [0.05, 0.035, 0.03],
                "mass_kg": 0.025,
                "physical_measurement_claimed": False,
            },
            "task_spec": {"ordered_phases": list(STRICT_GRASP_PHASES)},
            "evaluator_spec": spec,
            "positive": positive,
            "adversarial_negatives": negatives,
            "all_negatives_rejected_for_expected_reason": all(
                not case["evaluation"]["strict_grasp_success"]
                and case["expected_failure_reason"]
                in case["evaluation"]["failure_reasons"]
                for case in negatives
            ),
            "physical_twin_qualified": False,
            "simulation_training_ready": False,
            "hardware_accessed": False,
            "physical_follower_commanded": False,
            "local_capabilities": ["strict_grasp_evaluator_fixture_conformant"],
            "proof_labels": [],
            "authority_not_granted": [
                "mujoco_grasp_trajectory_valid",
                "physical_anchor_profile_complete",
                "strict_policy_grasp_success",
                "physical_twin_qualified",
                "simulation_training_ready",
                "physical_actuation",
            ],
        }
    )


def verify_strict_grasp_fixture(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="strict grasp fixture")
    if payload != build_strict_grasp_fixture():
        raise ValueError("Strict grasp fixture drifted from deterministic sources")


def _negative_cases() -> list[tuple[str, str, str, dict[str, Any]]]:
    return [
        (
            "wrong_object",
            "wrong_object",
            "analytic_expert",
            {"kind": "set_all", "field": "object_id", "value": "wrong"},
        ),
        (
            "missing_pregrasp",
            "phase_order_invalid",
            "analytic_expert",
            {"kind": "remove", "index": 1},
        ),
        (
            "reordered_close",
            "phase_order_invalid",
            "analytic_expert",
            {"kind": "set", "index": 1, "field": "phase", "value": "close"},
        ),
        (
            "planar_slide",
            "pushing_or_sliding_without_grasp",
            "analytic_expert",
            {"kind": "set", "index": 4, "field": "mechanism", "value": "slide"},
        ),
        (
            "hook",
            "hooking_or_table_pinning",
            "analytic_expert",
            {"kind": "set", "index": 4, "field": "mechanism", "value": "hook"},
        ),
        (
            "throw",
            "throwing_or_ballistic_motion",
            "analytic_expert",
            {"kind": "set", "index": 4, "field": "mechanism", "value": "throw"},
        ),
        (
            "teleport",
            "teleport_detected",
            "analytic_expert",
            {"kind": "set", "index": 4, "field": "teleport_detected", "value": True},
        ),
        (
            "scripted_motion",
            "scripted_object_motion",
            "analytic_expert",
            {
                "kind": "set",
                "index": 4,
                "field": "scripted_object_motion",
                "value": True,
            },
        ),
        (
            "momentary_contact",
            "stable_hold_too_short",
            "analytic_expert",
            {"kind": "remove", "index": 6},
        ),
        (
            "assistance_relabel",
            "controller_assistance_relabelled_as_policy",
            "strict_policy",
            {"kind": "none"},
        ),
        (
            "evaluator_leakage",
            "evaluator_state_leaked_to_actor",
            "analytic_expert",
            {
                "kind": "append",
                "index": 0,
                "field": "actor_observation_fields",
                "value": "privileged.object_pose",
            },
        ),
        (
            "invalid_release",
            "release_invalid",
            "analytic_expert",
            {
                "kind": "set",
                "index": -2,
                "field": "fingertip_contacts",
                "value": 2,
            },
        ),
    ]


def _apply_negative_mutation(
    trajectory: list[dict[str, Any]], mutation: dict[str, Any]
) -> None:
    kind = mutation["kind"]
    if kind == "none":
        return
    if kind == "remove":
        trajectory.pop(mutation["index"])
        return
    if kind == "set_all":
        for frame in trajectory:
            frame[mutation["field"]] = mutation["value"]
        return
    frame = trajectory[mutation["index"]]
    if kind == "set":
        frame[mutation["field"]] = mutation["value"]
        return
    if kind == "append":
        frame[mutation["field"]].append(mutation["value"])
        return
    raise ValueError(f"Unknown strict grasp negative mutation: {kind}")


def _validate_frames(trajectory: list[dict[str, Any]]) -> None:
    previous_timestamp = -1
    numeric_fields = (
        "object_speed_m_s",
        "impact_force_n",
        "actuator_current_ma_max",
        "gripper_aperture_m",
    )
    boolean_fields = (
        "object_table_contact",
        "forbidden_collision",
        "scripted_object_motion",
        "teleport_detected",
    )
    string_fields = (
        "phase",
        "object_id",
        "controller_owner",
        "control_mode",
        "mechanism",
    )
    for frame in trajectory:
        timestamp = frame.get("timestamp_ns")
        if (
            isinstance(timestamp, bool)
            or not isinstance(timestamp, int)
            or timestamp <= previous_timestamp
        ):
            raise ValueError("Strict grasp timestamps must be increasing integers")
        previous_timestamp = timestamp
        for name in numeric_fields:
            value = _finite(frame.get(name), label=name)
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative")
        contacts = frame.get("fingertip_contacts")
        if isinstance(contacts, bool) or not isinstance(contacts, int) or contacts < 0:
            raise ValueError("fingertip_contacts must be a non-negative integer")
        for name in boolean_fields:
            if not isinstance(frame.get(name), bool):
                raise ValueError(f"{name} must be boolean")
        for name in string_fields:
            if not isinstance(frame.get(name), str) or not frame[name]:
                raise ValueError(f"{name} must be a non-empty string")
        for name in ("object_position_m", "gripper_position_m"):
            values = frame.get(name)
            if not isinstance(values, list) or len(values) != 3:
                raise ValueError(f"{name} must contain three values")
            for value in values:
                _finite(value, label=name)
        actor_fields = frame.get("actor_observation_fields")
        if not isinstance(actor_fields, list) or not all(
            isinstance(value, str) and value for value in actor_fields
        ):
            raise ValueError("actor_observation_fields must be a list of strings")


def _finite(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{label} must be finite")
    return normalized


def _compressed_phases(trajectory: list[dict[str, Any]]) -> list[str]:
    phases = []
    for frame in trajectory:
        phase = str(frame.get("phase"))
        if not phases or phases[-1] != phase:
            phases.append(phase)
    return phases


def _phase_rows(trajectory: list[dict[str, Any]], phase: str) -> list[dict[str, Any]]:
    return [frame for frame in trajectory if frame["phase"] == phase]


def _relative_position(frame: dict[str, Any]) -> list[float]:
    return [
        float(object_value) - float(gripper_value)
        for object_value, gripper_value in zip(
            frame["object_position_m"], frame["gripper_position_m"], strict=True
        )
    ]


def _distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)))
