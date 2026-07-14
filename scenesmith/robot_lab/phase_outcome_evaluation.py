"""Phase-level terminal-outcome versus strict-grasp semantic evaluation."""

from __future__ import annotations

import copy

from typing import Any

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.strict_grasp import (
    evaluate_strict_grasp,
    verify_strict_grasp_v2_fixture,
)


PHASE_OUTCOME_SCHEMA_VERSION = "scenesmith.phase_outcome_evaluation.v1"
CAPABILITY_STAGES = (
    "approach",
    "contact",
    "grasp",
    "lift",
    "transport",
    "placement",
    "release",
    "retreat",
)
_STAGE_SOURCE_PHASES = {
    "approach": ("approach", "pregrasp"),
    "contact": ("close",),
    "grasp": ("grasp_confirmed",),
    "lift": ("lift",),
    "transport": ("stable_hold",),
    "placement": ("lower",),
    "release": ("release",),
    "retreat": ("retreat",),
}
_REQUIRED_CASE_IDS = (
    "putt_without_grasp",
    "planar_slide_without_lift",
    "ballistic_throw_after_momentary_contact",
    "terminal_occupancy_without_verified_release",
    "scripted_object_motion",
    "assistance_relabelled_as_policy",
    "stage_witness_drift",
    "actor_privilege_leakage",
)


def target_contract() -> dict[str, Any]:
    """Return the deterministic analytic target used only by this fixture."""

    return sign_payload(
        {
            "schema_version": "scenesmith.phase_outcome_target.v1",
            "target_id": "analytic_one_cube_target_v1",
            "center_m": [0.232, 0.0, 0.325],
            "xy_half_extent_m": [0.01, 0.02],
            "z_tolerance_m": 0.002,
            "minimum_stable_frames": 2,
            "maximum_stable_object_speed_m_s": 0.02,
            "source_mode": "declared_analytic_semantic_fixture",
            "physical_measurement_claimed": False,
        }
    )


def build_phase_outcome_fixture(strict_v2_fixture: dict[str, Any]) -> dict[str, Any]:
    """Build the deterministic T20.6 positive and required adversarial cases."""

    verify_strict_grasp_v2_fixture(strict_v2_fixture)
    spec = strict_v2_fixture["evaluator_spec"]
    target = target_contract()
    positive_trajectory = _target_transport_trajectory(
        strict_v2_fixture["positive"]["trajectory"]
    )
    positive = _evaluate_case(
        trajectory=positive_trajectory,
        spec=spec,
        target=target,
        claimed_proof_mode="analytic_expert",
    )
    adversarial_cases = []
    for case_id, expected_reason, claimed_mode, mutator in _adversarial_definitions():
        trajectory = copy.deepcopy(positive_trajectory)
        mutator(trajectory)
        case = _evaluate_case(
            trajectory=trajectory,
            spec=spec,
            target=target,
            claimed_proof_mode=claimed_mode,
        )
        case.update(
            {
                "case_id": case_id,
                "expected_failure_reason": expected_reason,
                "claimed_proof_mode": claimed_mode,
            }
        )
        adversarial_cases.append(case)

    expected_ids = list(_REQUIRED_CASE_IDS)
    all_rejected = (
        [case["case_id"] for case in adversarial_cases] == expected_ids
        and all(
            case["terminal_outcome"]["object_reached_target"]
            and case["terminal_outcome"]["stable_target_occupancy"]
            and not case["strict_evaluation"]["strict_grasp_success"]
            and case["expected_failure_reason"]
            in case["strict_evaluation"]["failure_reasons"]
            for case in adversarial_cases
        )
    )
    return sign_payload(
        {
            "schema_version": PHASE_OUTCOME_SCHEMA_VERSION,
            "evidence_mode": "deterministic_analytic_outcome_semantics_fixture",
            "qualification_scope": (
                "evaluator_semantics_not_mujoco_policy_or_physical_success"
            ),
            "source_strict_v2_identity_sha256": strict_v2_fixture[
                "identity_sha256"
            ],
            "source_strict_v2_schema_version": strict_v2_fixture["schema_version"],
            "target_contract": target,
            "capability_stages": list(CAPABILITY_STAGES),
            "positive": positive,
            "adversarial_cases": adversarial_cases,
            "all_required_adversarial_cases_rejected": all_rejected,
            "terminal_outcome_recorded_independently": True,
            "terminal_occupancy_sufficient_for_strict_success": False,
            "actual_mujoco_policy_success": False,
            "simulation_policy_accepted": False,
            "physical_transfer_eligible": False,
            "hardware_accessed": False,
            "optimizer_training": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "local_capabilities": [
                "phase_outcome_vs_strict_semantics_fixture_conformant"
            ],
            "authority_not_granted": [
                "actual_mujoco_policy_success",
                "simulation_policy_accepted",
                "physical_transfer_ready",
                "promotion_eligible",
                "physical_actuation",
                "external_compute",
                "brev_compute",
            ],
        }
    )


def verify_phase_outcome_fixture(
    payload: dict[str, Any], strict_v2_fixture: dict[str, Any]
) -> None:
    """Fail closed on identity, source, semantic, or deterministic drift."""

    verify_signed_payload(payload, label="T20.6 phase outcome fixture")
    verify_strict_grasp_v2_fixture(strict_v2_fixture)
    if payload != build_phase_outcome_fixture(strict_v2_fixture):
        raise ValueError("T20.6 phase outcome fixture drifted from deterministic sources")


def _target_transport_trajectory(
    source_trajectory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    trajectory = copy.deepcopy(source_trajectory)
    for frame in trajectory:
        if frame["phase"] in {
            "lift",
            "stable_hold",
            "lower",
            "release",
            "retreat",
        }:
            frame["object_position_m"][0] = 0.232
            frame["gripper_position_m"][0] = 0.232
    return trajectory


def _evaluate_case(
    *,
    trajectory: list[dict[str, Any]],
    spec: dict[str, Any],
    target: dict[str, Any],
    claimed_proof_mode: str,
) -> dict[str, Any]:
    return {
        "trajectory": trajectory,
        "capability_stage_witness": _capability_stage_witness(trajectory),
        "terminal_outcome": _terminal_outcome(trajectory, target),
        "strict_evaluation": evaluate_strict_grasp(
            spec,
            trajectory,
            claimed_proof_mode=claimed_proof_mode,
        ),
    }


def _capability_stage_witness(
    trajectory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    witness = []
    for stage in CAPABILITY_STAGES:
        expected_phases = _STAGE_SOURCE_PHASES[stage]
        frames = [frame for frame in trajectory if frame["phase"] in expected_phases]
        observed_phases = list(dict.fromkeys(frame["phase"] for frame in frames))
        witness.append(
            {
                "stage": stage,
                "expected_source_phases": list(expected_phases),
                "observed_source_phases": observed_phases,
                "source_timestamps_ns": [frame["timestamp_ns"] for frame in frames],
                "evidence_frame_count": len(frames),
                "witness_complete": observed_phases == list(expected_phases),
            }
        )
    return witness


def _terminal_outcome(
    trajectory: list[dict[str, Any]], target: dict[str, Any]
) -> dict[str, Any]:
    stable_count = target["minimum_stable_frames"]
    terminal_frames = trajectory[-stable_count:]
    in_target = [_frame_in_target(frame, target) for frame in terminal_frames]
    stable = [
        frame["object_table_contact"]
        and frame["object_speed_m_s"]
        <= target["maximum_stable_object_speed_m_s"]
        for frame in terminal_frames
    ]
    return {
        "target_id": target["target_id"],
        "object_reached_target": bool(terminal_frames) and in_target[-1],
        "stable_target_occupancy": (
            len(terminal_frames) == stable_count and all(in_target) and all(stable)
        ),
        "terminal_frame_count": len(terminal_frames),
        "terminal_timestamps_ns": [frame["timestamp_ns"] for frame in terminal_frames],
        "terminal_object_positions_m": [
            frame["object_position_m"] for frame in terminal_frames
        ],
    }


def _frame_in_target(frame: dict[str, Any], target: dict[str, Any]) -> bool:
    position = frame["object_position_m"]
    center = target["center_m"]
    half_extent = target["xy_half_extent_m"]
    return (
        abs(position[0] - center[0]) <= half_extent[0]
        and abs(position[1] - center[1]) <= half_extent[1]
        and abs(position[2] - center[2]) <= target["z_tolerance_m"]
    )


def _adversarial_definitions() -> list[tuple[str, str, str, Any]]:
    return [
        (
            "putt_without_grasp",
            "pushing_or_sliding_without_grasp",
            "analytic_expert",
            _mutate_putt,
        ),
        (
            "planar_slide_without_lift",
            "pushing_or_sliding_without_grasp",
            "analytic_expert",
            _mutate_slide,
        ),
        (
            "ballistic_throw_after_momentary_contact",
            "throwing_or_ballistic_motion",
            "analytic_expert",
            _mutate_throw,
        ),
        (
            "terminal_occupancy_without_verified_release",
            "release_invalid",
            "analytic_expert",
            _mutate_invalid_release,
        ),
        (
            "scripted_object_motion",
            "scripted_object_motion",
            "analytic_expert",
            _mutate_scripted_motion,
        ),
        (
            "assistance_relabelled_as_policy",
            "controller_assistance_relabelled_as_policy",
            "strict_policy",
            lambda trajectory: None,
        ),
        (
            "stage_witness_drift",
            "phase_order_invalid",
            "analytic_expert",
            lambda trajectory: trajectory.pop(1),
        ),
        (
            "actor_privilege_leakage",
            "evaluator_state_leaked_to_actor",
            "analytic_expert",
            _mutate_actor_privilege,
        ),
    ]


def _mutate_putt(trajectory: list[dict[str, Any]]) -> None:
    for frame in trajectory:
        if frame["phase"] in {"grasp_confirmed", "lift", "stable_hold", "lower"}:
            frame["fingertip_contacts"] = 0
    lift = next(frame for frame in trajectory if frame["phase"] == "lift")
    lift["mechanism"] = "push"
    lift["impact_force_n"] = 8.0


def _mutate_slide(trajectory: list[dict[str, Any]]) -> None:
    for frame in trajectory:
        if frame["phase"] in {"grasp_confirmed", "lift", "stable_hold", "lower"}:
            frame["fingertip_contacts"] = 0
        if frame["phase"] in {"lift", "stable_hold", "lower"}:
            frame["object_position_m"][2] = 0.325
            frame["object_table_contact"] = True
    lift = next(frame for frame in trajectory if frame["phase"] == "lift")
    lift["mechanism"] = "slide"


def _mutate_throw(trajectory: list[dict[str, Any]]) -> None:
    lift = next(frame for frame in trajectory if frame["phase"] == "lift")
    lift["mechanism"] = "throw"
    first_hold = next(
        index for index, frame in enumerate(trajectory) if frame["phase"] == "stable_hold"
    )
    trajectory.pop(first_hold + 1)


def _mutate_invalid_release(trajectory: list[dict[str, Any]]) -> None:
    release = next(frame for frame in trajectory if frame["phase"] == "release")
    release["fingertip_contacts"] = 2


def _mutate_scripted_motion(trajectory: list[dict[str, Any]]) -> None:
    lift = next(frame for frame in trajectory if frame["phase"] == "lift")
    lift["scripted_object_motion"] = True


def _mutate_actor_privilege(trajectory: list[dict[str, Any]]) -> None:
    trajectory[0]["actor_observation_fields"].append("strict_grasp_success")
