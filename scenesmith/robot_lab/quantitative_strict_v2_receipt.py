"""Policy-independent quantitative receipts for strict-v2 grasp evaluation."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.strict_grasp import (
    evaluate_antipodal_contact_witness,
    evaluate_strict_grasp,
    verify_strict_grasp_v2_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FIXTURE_PATH = Path(
    "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json"
)
EVALUATOR_SOURCE_PATH = Path("scenesmith/robot_lab/strict_grasp.py")
RECEIPT_PATH = Path(
    "configurations/robot_lab/t20_38_strict_v2_quantitative_receipt.simulation_only.json"
)
SCHEMA_VERSION = "scenesmith.quantitative_strict_v2_receipt.v1"
EXPECTED_FIXTURE_IDENTITY = (
    "950e7568025f4fe09b9e51633da71b3ee90212ee5ea9c86be8194863cea2e640"
)
EXPECTED_EVALUATOR_SOURCE_SHA256 = (
    "8dd97c798c1fb8e6824351e9a21e17b56f7e7a0c1bf87da1bd16d7e1dffc50a5"
)
COMPARATORS = ("gte", "lte", "range", "eq")


def build_quantitative_margin(
    *,
    predicate_id: str,
    observed_value: Any,
    comparator: str,
    threshold: Any,
    normalization_scale: float,
    units: str,
    actor_valid: bool = True,
    evidence_valid: bool = True,
    evidence_detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(predicate_id, str) or not predicate_id:
        raise ValueError("Strict-v2 predicate id must be non-empty")
    if comparator not in COMPARATORS:
        raise ValueError("Strict-v2 comparator is unsupported")
    scale = _finite(normalization_scale, label="normalization scale")
    if scale <= 0.0:
        raise ValueError("Strict-v2 normalization scale must be positive")
    if not isinstance(units, str) or not units:
        raise ValueError("Strict-v2 units must be non-empty")
    if not isinstance(actor_valid, bool) or not isinstance(evidence_valid, bool):
        raise ValueError("Strict-v2 guards must be boolean")
    if evidence_detail is not None and not isinstance(evidence_detail, dict):
        raise ValueError("Strict-v2 evidence detail must be an object")

    if comparator == "gte":
        observed = _finite(observed_value, label="observed value")
        boundary = _finite(threshold, label="lower threshold")
        raw_margin = observed - boundary
        comparator_passed = raw_margin >= 0.0
    elif comparator == "lte":
        observed = _finite(observed_value, label="observed value")
        boundary = _finite(threshold, label="upper threshold")
        raw_margin = boundary - observed
        comparator_passed = raw_margin >= 0.0
    elif comparator == "range":
        observed = _finite(observed_value, label="observed value")
        if not isinstance(threshold, list) or len(threshold) != 2:
            raise ValueError("Strict-v2 range threshold must contain two values")
        lower = _finite(threshold[0], label="range lower threshold")
        upper = _finite(threshold[1], label="range upper threshold")
        if lower > upper:
            raise ValueError("Strict-v2 range threshold is inverted")
        boundary = [lower, upper]
        raw_margin = min(observed - lower, upper - observed)
        comparator_passed = raw_margin >= 0.0
    else:
        _finite_tree(observed_value, label="observed equality value")
        _finite_tree(threshold, label="expected equality value")
        boundary = threshold
        comparator_passed = observed_value == threshold
        raw_margin = scale if comparator_passed else -scale

    normalized_margin = raw_margin / scale
    effective_passed = comparator_passed and actor_valid and evidence_valid
    blocking_reasons = []
    if not comparator_passed:
        blocking_reasons.append("predicate_failed")
    if not actor_valid:
        blocking_reasons.append("actor_guard_failed")
    if not evidence_valid:
        blocking_reasons.append("evidence_guard_failed")
    return {
        "predicate_id": predicate_id,
        "observed_value": observed_value,
        "comparator": comparator,
        "threshold": boundary,
        "normalization_scale": scale,
        "units": units,
        "signed_raw_margin": raw_margin,
        "normalized_signed_margin": normalized_margin,
        "comparator_passed": comparator_passed,
        "actor_valid": actor_valid,
        "evidence_valid": evidence_valid,
        "effective_passed": effective_passed,
        "blocking_reasons": blocking_reasons,
        "evidence_detail": evidence_detail or {},
    }


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    fixture_path = root / SOURCE_FIXTURE_PATH
    evaluator_path = root / EVALUATOR_SOURCE_PATH
    fixture = load_strict_json(fixture_path)
    verify_strict_grasp_v2_fixture(fixture)
    evaluator_sha = hashlib.sha256(evaluator_path.read_bytes()).hexdigest()
    fixture_file_sha = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    if (
        fixture.get("identity_sha256") != EXPECTED_FIXTURE_IDENTITY
        or evaluator_sha != EXPECTED_EVALUATOR_SOURCE_SHA256
        or fixture.get("evidence_mode")
        != "analytic_antipodal_contact_evaluator_fixture"
        or fixture.get("actual_mujoco_grasp_success") is not False
        or fixture.get("physical_twin_qualified") is not False
    ):
        raise ValueError("T20.38 strict-v2 source binding drifted")
    return {
        "fixture": fixture,
        "fixture_file_sha256": fixture_file_sha,
        "fixture_size_bytes": fixture_path.stat().st_size,
        "evaluator_source_sha256": evaluator_sha,
        "evaluator_source_size_bytes": evaluator_path.stat().st_size,
    }


def build_quantitative_receipt(*, sources: dict[str, Any]) -> dict[str, Any]:
    fixture = sources["fixture"]
    verify_strict_grasp_v2_fixture(fixture)
    spec = fixture["evaluator_spec"]
    positive = fixture["positive"]
    trajectory = positive["trajectory"]
    stored_evaluation = positive["evaluation"]
    evaluation = evaluate_strict_grasp(
        spec,
        trajectory,
        claimed_proof_mode="analytic_expert",
    )
    if evaluation != stored_evaluation:
        raise ValueError("T20.38 source evaluation drifted")
    predicates = _compile_predicates(spec=spec, trajectory=trajectory)
    hard_conjunction = all(row["effective_passed"] for row in predicates)
    if hard_conjunction != evaluation["strict_grasp_success"]:
        raise ValueError("T20.38 receipt/evaluator conjunction disagrees")
    bottleneck_index = min(
        range(len(predicates)),
        key=lambda index: predicates[index]["normalized_signed_margin"],
    )
    bottleneck = predicates[bottleneck_index]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.38",
            "scope": "policy_independent_quantitative_strict_v2_receipt",
            "source_fixture_ref": {
                "path": SOURCE_FIXTURE_PATH.as_posix(),
                "schema_version": fixture["schema_version"],
                "identity_sha256": fixture["identity_sha256"],
                "file_sha256": sources["fixture_file_sha256"],
                "size_bytes": sources["fixture_size_bytes"],
            },
            "evaluator_source_ref": {
                "path": EVALUATOR_SOURCE_PATH.as_posix(),
                "file_sha256": sources["evaluator_source_sha256"],
                "size_bytes": sources["evaluator_source_size_bytes"],
                "entrypoint": "evaluate_strict_grasp",
            },
            "evaluator_spec_identity_sha256": spec["identity_sha256"],
            "source_trajectory_sha256": hashlib.sha256(
                canonical_json_bytes(trajectory)
            ).hexdigest(),
            "evidence_provenance": "analytic_simulation_fixture",
            "proof_mode": evaluation["proof_mode"],
            "predicate_count": len(predicates),
            "predicates": predicates,
            "hard_conjunction_passed": hard_conjunction,
            "source_strict_grasp_success": evaluation["strict_grasp_success"],
            "source_strict_success_agrees": True,
            "bottleneck_predicate_id": bottleneck["predicate_id"],
            "bottleneck_normalized_signed_margin": bottleneck[
                "normalized_signed_margin"
            ],
            "average_or_compensating_pass_allowed": False,
            "pure_policy_success": evaluation["pure_policy_success"],
            "actual_mujoco_grasp_success": False,
            "physical_proof": False,
            "simulation_training_ready": False,
            "model_constructed": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "rollout_executed": False,
            "historical_artifact_mutated": False,
            "gate_changed": False,
            "threshold_changed": False,
            "policy_selected": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "promotion_eligible": False,
        }
    )


def verify_quantitative_receipt(
    payload: dict[str, Any], *, sources: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.38 quantitative strict-v2 receipt")
    expected = build_quantitative_receipt(sources=sources)
    if payload != expected:
        raise ValueError("T20.38 quantitative strict-v2 receipt drifted")


def _compile_predicates(
    *, spec: dict[str, Any], trajectory: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    phases = []
    for frame in trajectory:
        if not phases or phases[-1] != frame["phase"]:
            phases.append(frame["phase"])
    mechanisms = {frame["mechanism"] for frame in trajectory}
    actor_fields = {
        field for frame in trajectory for field in frame["actor_observation_fields"]
    }
    confirmed = [row for row in trajectory if row["phase"] == "grasp_confirmed"]
    lift = [row for row in trajectory if row["phase"] == "lift"]
    hold = [row for row in trajectory if row["phase"] == "stable_hold"]
    release = [row for row in trajectory if row["phase"] == "release"]
    retreat = [row for row in trajectory if row["phase"] == "retreat"]
    antipodal_requirement = spec["antipodal_contact_requirement"]
    witness_rows = [*confirmed, *hold]
    witness_scores = [
        evaluate_antipodal_contact_witness(
            row.get("contact_geometry_witness"),
            antipodal_requirement,
        )
        for row in witness_rows
    ]
    required_z = (
        spec["table_top_z_m"]
        + spec["object_half_height_m"]
        + spec["required_lift_clearance_m"]
    )
    reference = _relative_position(confirmed[0]) if confirmed else [math.inf] * 3
    grasped = [
        row
        for row in trajectory
        if row["phase"] in {"lift", "stable_hold", "lower"}
    ]
    max_drift = max(
        (_distance(_relative_position(row), reference) for row in grasped),
        default=math.inf,
    )
    pure_analytic_owner = all(
        row["controller_owner"] == "analytic_grasp_expert"
        and row["control_mode"] == "analytic_expert"
        for row in trajectory
    )
    rows = []

    def add(
        predicate_id: str,
        observed: Any,
        comparator: str,
        threshold: Any,
        scale: float,
        units: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        rows.append(
            build_quantitative_margin(
                predicate_id=predicate_id,
                observed_value=observed,
                comparator=comparator,
                threshold=threshold,
                normalization_scale=scale,
                units=units,
                evidence_detail=detail,
            )
        )

    add("phase_order", phases, "eq", spec["ordered_phases"], 1.0, "boolean")
    add(
        "object_identity",
        all(row["object_id"] == spec["object_id"] for row in trajectory),
        "eq",
        True,
        1.0,
        "boolean",
    )
    add(
        "mechanism_exclusions",
        not bool(mechanisms & {"push", "slide", "hook", "table_pin", "throw", "ballistic"}),
        "eq",
        True,
        1.0,
        "boolean",
        {"observed_mechanisms": sorted(mechanisms)},
    )
    for field in ("teleport_detected", "scripted_object_motion", "forbidden_collision"):
        add(
            field,
            not any(row[field] for row in trajectory),
            "eq",
            True,
            1.0,
            "boolean",
        )
    add(
        "actor_observation_fields_allowed",
        not bool(actor_fields & set(spec["prohibited_actor_observation_fields"])),
        "eq",
        True,
        1.0,
        "boolean",
        {"actor_observation_fields": sorted(actor_fields)},
    )
    add(
        "maximum_object_speed",
        max(row["object_speed_m_s"] for row in trajectory),
        "lte",
        spec["maximum_object_speed_m_s"],
        spec["maximum_object_speed_m_s"],
        "m_s",
    )
    add(
        "maximum_impact_force",
        max(row["impact_force_n"] for row in trajectory),
        "lte",
        spec["maximum_impact_force_n"],
        spec["maximum_impact_force_n"],
        "N",
    )
    currents = [row["actuator_current_ma_max"] for row in trajectory]
    add("actuator_current_present", all(value is not None for value in currents), "eq", True, 1.0, "boolean")
    add(
        "maximum_actuator_current",
        max(value for value in currents if value is not None),
        "lte",
        spec["maximum_actuator_current_ma"],
        spec["maximum_actuator_current_ma"],
        "mA",
    )
    apertures = [row["gripper_aperture_m"] for row in trajectory]
    add("gripper_aperture_present", all(value is not None for value in apertures), "eq", True, 1.0, "boolean")
    add("grasp_confirmed_present", bool(confirmed), "eq", True, 1.0, "boolean")
    add(
        "grasp_confirmed_contacts",
        confirmed[0]["fingertip_contacts"] if confirmed else 0,
        "gte",
        spec["minimum_fingertip_contacts"],
        spec["minimum_fingertip_contacts"],
        "count",
    )
    add("antipodal_witnesses_valid", bool(witness_scores) and all(row["valid"] for row in witness_scores), "eq", True, 1.0, "boolean")
    add(
        "minimum_contact_span",
        min(row["contact_span_m"] for row in witness_scores if row["contact_span_m"] is not None),
        "gte",
        antipodal_requirement["minimum_contact_span_m"],
        antipodal_requirement["minimum_contact_span_m"],
        "m",
    )
    add(
        "maximum_opposing_normal_dot",
        max(row["normal_dot"] for row in witness_scores if row["normal_dot"] is not None),
        "lte",
        antipodal_requirement["maximum_opposing_normal_dot"],
        abs(antipodal_requirement["maximum_opposing_normal_dot"]),
        "unitless",
    )
    add(
        "minimum_contact_axis_alignment",
        min(row["minimum_axis_alignment"] for row in witness_scores if row["minimum_axis_alignment"] is not None),
        "gte",
        antipodal_requirement["minimum_contact_axis_alignment"],
        antipodal_requirement["minimum_contact_axis_alignment"],
        "unitless",
    )
    add("lift_present", bool(lift), "eq", True, 1.0, "boolean")
    add(
        "lift_clearance",
        lift[0]["object_position_m"][2] if lift else -math.inf,
        "gte",
        required_z,
        spec["required_lift_clearance_m"],
        "m",
    )
    add("lift_table_clear", bool(lift) and not lift[0]["object_table_contact"], "eq", True, 1.0, "boolean")
    add(
        "stable_hold_frame_count",
        len(hold),
        "gte",
        spec["minimum_stable_hold_frames"],
        spec["minimum_stable_hold_frames"],
        "count",
    )
    add(
        "stable_hold_maximum_speed",
        max((row["object_speed_m_s"] for row in hold), default=math.inf),
        "lte",
        spec["maximum_hold_object_speed_m_s"],
        spec["maximum_hold_object_speed_m_s"],
        "m_s",
    )
    add("stable_hold_table_clear", bool(hold) and not any(row["object_table_contact"] for row in hold), "eq", True, 1.0, "boolean")
    add(
        "stable_hold_minimum_contacts",
        min((row["fingertip_contacts"] for row in hold), default=0),
        "gte",
        spec["minimum_fingertip_contacts"],
        spec["minimum_fingertip_contacts"],
        "count",
    )
    add(
        "maximum_object_gripper_relative_drift",
        max_drift,
        "lte",
        spec["maximum_object_gripper_relative_drift_m"],
        spec["maximum_object_gripper_relative_drift_m"],
        "m",
    )
    add("release_present", bool(release), "eq", True, 1.0, "boolean")
    add("release_contacts_clear", release[0]["fingertip_contacts"] if release else -1, "eq", 0, 1.0, "count")
    add(
        "release_aperture",
        release[0]["gripper_aperture_m"] if release and release[0]["gripper_aperture_m"] is not None else -math.inf,
        "gte",
        spec["minimum_release_aperture_m"],
        spec["minimum_release_aperture_m"],
        "m",
    )
    add("retreat_present", bool(retreat), "eq", True, 1.0, "boolean")
    add("retreat_contacts_clear", retreat[0]["fingertip_contacts"] if retreat else -1, "eq", 0, 1.0, "count")
    retreat_distance = (
        _distance(retreat[0]["gripper_position_m"], retreat[0]["object_position_m"])
        if retreat
        else -math.inf
    )
    add(
        "minimum_retreat_distance",
        retreat_distance,
        "gte",
        spec["minimum_retreat_distance_m"],
        spec["minimum_retreat_distance_m"],
        "m",
    )
    add("analytic_expert_actor_contract", pure_analytic_owner, "eq", True, 1.0, "boolean")
    return rows


def _relative_position(frame: dict[str, Any]) -> list[float]:
    return [
        float(object_value) - float(gripper_value)
        for object_value, gripper_value in zip(
            frame["object_position_m"], frame["gripper_position_m"], strict=True
        )
    ]


def _distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)))


def _finite(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Strict-v2 {label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Strict-v2 {label} must be finite")
    return number


def _finite_tree(value: Any, *, label: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Strict-v2 {label} must be finite")
    if isinstance(value, list):
        for item in value:
            _finite_tree(item, label=label)
    elif isinstance(value, dict):
        for item in value.values():
            _finite_tree(item, label=label)
