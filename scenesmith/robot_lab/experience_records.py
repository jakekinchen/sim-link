"""Immutable raw-rollout and frame-record contracts for M17."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    load_strict_json,
    require_finite_number,
    require_nonblank,
    sign_payload,
    validate_content_addressed_evidence,
    validate_unique_ids,
    verify_artifact_ref,
    verify_signed_payload,
)
from scenesmith.robot_lab.so101_coordinates import coordinate_contract


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("configurations/robot_lab/experience_record_contract.json")
GRASP_PATH = Path("configurations/robot_lab/geometry_derived_unilateral_grasp.json")
TWIN_PROFILE_PATH = Path("configurations/robot_lab/pi05_twin_profile.simulation_only.json")
CONTRACT_SCHEMA_VERSION = "scenesmith.experience_record_contract.v1"
RAW_ROLLOUT_SCHEMA_VERSION = "scenesmith.raw_rollout_record.v1"
FRAME_SCHEMA_VERSION = "scenesmith.frame_record.v1"
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)
SOURCE_CLASSES = (
    "analytic_expert",
    "mujoco_expert",
    "retargeted_simulation",
    "physical_demonstration",
    "correction",
    "autonomous_policy",
)
PROOF_MODES = (
    "analytic_fixture",
    "simulation_unassisted",
    "simulation_assisted",
    "physical_scripted",
    "physical_policy",
)
TASK_PHASES = (
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
CONTROL_MODES = (
    "analytic_expert",
    "scripted_mujoco_expert",
    "retargeted_simulation",
    "scripted_physical",
    "teleoperated_physical",
    "autonomous_policy",
    "policy_projected_assisted",
    "recovery",
)
CONTROLLER_OWNERS = (
    "analytic_grasp_expert",
    "geometry_derived_mujoco_expert",
    "retargeting_controller",
    "human_operator",
    "autonomous_policy",
    "safety_projector",
)
ACTION_VARIANTS = ("requested", "proposed", "projected", "sent", "measured")
AVAILABILITY_STATES = ("observed", "derived", "not_observed", "not_applicable")
HARD_BOUNDARY_EVENTS = (
    "rollout_start",
    "rollout_end",
    "phase_change",
    "reset",
    "teleport",
    "scene_change",
    "prompt_change",
    "controller_owner_change",
    "control_mode_change",
    "coordinate_contract_change",
    "dropped_observation",
    "timestamp_gap",
)
PRIVILEGED_ACTOR_ROOTS = {
    "reward",
    "progress",
    "future_state",
    "simulator_privileged_state",
    "strict_evaluator_result",
}


def build_experience_record_contract(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    grasp_path = repo_root / GRASP_PATH
    twin_path = repo_root / TWIN_PROFILE_PATH
    grasp = load_strict_json(grasp_path)
    twin = load_strict_json(twin_path)
    verify_signed_payload(grasp, label="source geometry-derived grasp")
    verify_signed_payload(twin, label="source simulation twin profile")
    grasp_ref = artifact_ref(path=GRASP_PATH, payload=grasp, repo_root=repo_root)
    twin_ref = artifact_ref(path=TWIN_PROFILE_PATH, payload=twin, repo_root=repo_root)
    coordinates = coordinate_contract()
    coordinate_ref = {
        "schema_version": coordinates["schema_version"],
        "identity_sha256": _sha256(coordinates),
    }
    fixture = _build_fixture_projection(
        grasp=grasp,
        grasp_ref=grasp_ref,
        twin_ref=twin_ref,
        coordinate_ref=coordinate_ref,
    )
    payload = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "contract_name": "so101_immutable_grasp_experience_records",
        "source_grasp_artifact_ref": grasp_ref,
        "twin_profile_ref": twin_ref,
        "coordinate_contract_ref": coordinate_ref,
        "record_schema_versions": {
            "raw_rollout": RAW_ROLLOUT_SCHEMA_VERSION,
            "frame": FRAME_SCHEMA_VERSION,
        },
        "provenance_dictionaries": {
            "source_classes": list(SOURCE_CLASSES),
            "proof_modes": list(PROOF_MODES),
            "task_phases": list(TASK_PHASES),
            "control_modes": list(CONTROL_MODES),
            "controller_owners": list(CONTROLLER_OWNERS),
            "action_variants": list(ACTION_VARIANTS),
            "availability_states": list(AVAILABILITY_STATES),
            "hard_boundary_events": list(HARD_BOUNDARY_EVENTS),
        },
        "invariants": {
            "raw_payload_append_only": True,
            "raw_payload_identity_is_canonical_sha256": True,
            "frame_record_identity_is_canonical_sha256": True,
            "timestamps_are_integer_nanoseconds_and_strictly_increasing": True,
            "actions_remain_variant_separated": True,
            "unavailable_values_are_null_with_reason": True,
            "reward_progress_and_privileged_state_are_not_actor_inputs": True,
            "unknown_semantics_require_quarantine": True,
            "recovery_is_control_mode_not_task_phase": True,
            "raw_bytes_are_never_rewritten_by_compilation": True,
        },
        "required_raw_rollout_fields": [
            "rollout_id",
            "source_class",
            "proof_mode",
            "controller_owner",
            "control_mode",
            "prompt",
            "object_identity",
            "workcell_identity",
            "environment_identity",
            "coordinate_contract_ref",
            "twin_profile_ref",
            "preprocessing_identity",
            "source_artifact_ref",
            "start_timestamp_ns",
            "end_timestamp_ns",
            "frame_count",
            "raw_payload",
            "raw_payload_sha256",
        ],
        "required_frame_fields": [
            "frame_id",
            "rollout_id",
            "frame_index",
            "timestamp_ns",
            "task_phase",
            "source_phase",
            "source_class",
            "proof_mode",
            "controller_owner",
            "control_mode",
            "actions",
            "requested_gripper_pose",
            "achieved_gripper_pose",
            "contact_geometry_witness",
            "aperture",
            "effort",
            "reward",
            "progress",
            "strict_evaluator_result",
            "boundary_events",
            "actor_input_field_names",
        ],
        "fixture_projection": fixture,
        "compiled_training_frames": False,
        "simulation_training_ready": False,
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "authority_not_granted": [
            "compiled_training_frames",
            "simulation_training_ready",
            "optimizer_training",
            "physical_actuation",
        ],
    }
    return sign_payload(payload)


def verify_experience_record_contract(
    payload: dict[str, Any], *, repo_root: Path = REPO_ROOT
) -> None:
    verify_signed_payload(payload, label="experience record contract")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ValueError("Experience record contract schema is invalid")
    grasp = load_strict_json(repo_root / GRASP_PATH)
    twin = load_strict_json(repo_root / TWIN_PROFILE_PATH)
    verify_signed_payload(grasp, label="source geometry-derived grasp")
    verify_signed_payload(twin, label="source simulation twin profile")
    expected_grasp_ref = artifact_ref(
        path=GRASP_PATH, payload=grasp, repo_root=repo_root
    )
    expected_twin_ref = artifact_ref(
        path=TWIN_PROFILE_PATH, payload=twin, repo_root=repo_root
    )
    verify_artifact_ref(
        payload.get("source_grasp_artifact_ref"),
        expected_grasp_ref,
        label="source grasp artifact",
    )
    verify_artifact_ref(
        payload.get("twin_profile_ref"), expected_twin_ref, label="twin profile"
    )
    expected_coordinate_ref = {
        "schema_version": coordinate_contract()["schema_version"],
        "identity_sha256": _sha256(coordinate_contract()),
    }
    if payload.get("coordinate_contract_ref") != expected_coordinate_ref:
        raise ValueError("Coordinate contract linkage drifted")
    expected_dictionaries = {
        "source_classes": list(SOURCE_CLASSES),
        "proof_modes": list(PROOF_MODES),
        "task_phases": list(TASK_PHASES),
        "control_modes": list(CONTROL_MODES),
        "controller_owners": list(CONTROLLER_OWNERS),
        "action_variants": list(ACTION_VARIANTS),
        "availability_states": list(AVAILABILITY_STATES),
        "hard_boundary_events": list(HARD_BOUNDARY_EVENTS),
    }
    if payload.get("provenance_dictionaries") != expected_dictionaries:
        raise ValueError("Experience provenance dictionaries drifted")
    fixture = payload.get("fixture_projection")
    if not isinstance(fixture, dict):
        raise ValueError("Experience record fixture projection is missing")
    raw = fixture.get("raw_rollout")
    frames = fixture.get("frames")
    validate_raw_rollout_record(raw, expected_grasp_ref)
    verify_artifact_ref(
        raw.get("twin_profile_ref"), expected_twin_ref, label="raw rollout twin profile"
    )
    if raw.get("coordinate_contract_ref") != expected_coordinate_ref:
        raise ValueError("Raw rollout coordinate contract linkage drifted")
    validate_frame_records(frames, raw)
    if fixture.get("training_eligible") is not False:
        raise ValueError("Source projection fixture must not be training eligible")
    reasons = fixture.get("quarantine_reasons")
    if not isinstance(reasons, list) or not reasons:
        raise ValueError("Source projection fixture requires quarantine reasons")
    if payload.get("compiled_training_frames") or payload.get("simulation_training_ready"):
        raise ValueError("Experience record contract escalates training authority")
    if payload.get("hardware_accessed") or payload.get("physical_follower_commanded"):
        raise ValueError("Experience record contract claims hardware access")
    if payload != build_experience_record_contract(repo_root=repo_root):
        raise ValueError("Experience record contract drifted")


def validate_raw_rollout_record(
    record: Any, expected_source_ref: dict[str, Any]
) -> None:
    if not isinstance(record, dict):
        raise ValueError("Raw rollout record must be an object")
    if record.get("schema_version") != RAW_ROLLOUT_SCHEMA_VERSION:
        raise ValueError("Raw rollout schema is invalid")
    _verify_record_identity(record, label="raw rollout")
    require_nonblank(record.get("rollout_id"), label="rollout_id")
    _require_enum(record, "source_class", SOURCE_CLASSES)
    _require_enum(record, "proof_mode", PROOF_MODES)
    _require_enum(record, "controller_owner", CONTROLLER_OWNERS)
    _require_enum(record, "control_mode", CONTROL_MODES)
    for field in (
        "object_identity",
        "workcell_identity",
        "environment_identity",
        "preprocessing_identity",
    ):
        require_nonblank(record.get(field), label=field)
    prompt = record.get("prompt")
    if not isinstance(prompt, dict):
        raise ValueError("prompt is required")
    prompt_text = require_nonblank(prompt.get("text"), label="prompt text")
    if prompt.get("identity_sha256") != _sha256(prompt_text):
        raise ValueError("Prompt identity drifted")
    verify_artifact_ref(
        record.get("source_artifact_ref"),
        expected_source_ref,
        label="raw rollout source artifact",
    )
    coordinate_ref = record.get("coordinate_contract_ref")
    if not isinstance(coordinate_ref, dict):
        raise ValueError("coordinate contract reference is required")
    require_nonblank(
        coordinate_ref.get("schema_version"), label="coordinate contract schema"
    )
    _require_sha256(
        coordinate_ref.get("identity_sha256"), label="coordinate contract identity"
    )
    start = _require_nonnegative_integer(record.get("start_timestamp_ns"), "start_timestamp_ns")
    end = _require_nonnegative_integer(record.get("end_timestamp_ns"), "end_timestamp_ns")
    if end < start:
        raise ValueError("Raw rollout timestamps are reversed")
    frame_count = record.get("frame_count")
    if isinstance(frame_count, bool) or not isinstance(frame_count, int) or frame_count <= 0:
        raise ValueError("Raw rollout frame_count must be positive")
    if record.get("raw_payload_append_only") is not True:
        raise ValueError("Raw rollout append-only flag is missing")
    raw_payload = record.get("raw_payload")
    if not isinstance(raw_payload, dict):
        raise ValueError("Raw rollout raw_payload is missing")
    expected_raw_sha = _sha256(raw_payload)
    if record.get("raw_payload_sha256") != expected_raw_sha:
        raise ValueError("Raw rollout raw payload hash drifted")
    if record["rollout_id"] != f"rollout-{expected_raw_sha[:24]}":
        raise ValueError("Raw rollout_id is not bound to raw payload")
    twin_ref = record.get("twin_profile_ref")
    if not isinstance(twin_ref, dict):
        raise ValueError("Raw rollout twin profile reference is required")
    for field in ("path", "schema_version"):
        require_nonblank(twin_ref.get(field), label=f"raw rollout twin profile {field}")
    for field in ("identity_sha256", "file_sha256"):
        _require_sha256(twin_ref.get(field), label=f"raw rollout twin profile {field}")
    validate_content_addressed_evidence(
        record.get("evidence"), label="raw rollout"
    )


def sign_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a record with a canonical content identity."""

    signed = dict(record)
    signed["record_identity_sha256"] = _record_identity(signed)
    return signed


def validate_frame_records(frames: Any, raw_rollout: dict[str, Any]) -> None:
    if not isinstance(frames, list) or not frames:
        raise ValueError("Frame records are required")
    if any(not isinstance(frame, dict) for frame in frames):
        raise ValueError("Frame record must be an object")
    validate_unique_ids(frames, field="frame_id", label="frame")
    frame_indices = [frame.get("frame_index") for frame in frames]
    if any(isinstance(index, bool) or not isinstance(index, int) for index in frame_indices):
        raise ValueError("Frame frame_index must be an integer")
    if len(frame_indices) != len(set(frame_indices)):
        raise ValueError("Duplicate frame frame_index")
    if len(frames) != raw_rollout.get("frame_count"):
        raise ValueError("Frame count does not match raw rollout")
    prior_timestamp: int | None = None
    for expected_index, frame in enumerate(frames):
        if frame.get("schema_version") != FRAME_SCHEMA_VERSION:
            raise ValueError("Frame schema is invalid")
        _verify_record_identity(frame, label="frame")
        if frame.get("frame_index") != expected_index:
            raise ValueError("Frame indices must be contiguous and ordered")
        expected_frame_id = f"{raw_rollout['rollout_id']}-frame-{expected_index:06d}"
        if frame.get("frame_id") != expected_frame_id:
            raise ValueError("Frame_id is not stable for rollout and index")
        if frame.get("rollout_id") != raw_rollout.get("rollout_id"):
            raise ValueError("Frame rollout_id drifted")
        timestamp = _require_nonnegative_integer(frame.get("timestamp_ns"), "timestamp_ns")
        if prior_timestamp is not None and timestamp <= prior_timestamp:
            raise ValueError("Frame timestamps must increase strictly")
        prior_timestamp = timestamp
        if not raw_rollout["start_timestamp_ns"] <= timestamp <= raw_rollout["end_timestamp_ns"]:
            raise ValueError("Frame timestamp lies outside rollout")
        _require_enum(frame, "source_class", SOURCE_CLASSES)
        _require_enum(frame, "proof_mode", PROOF_MODES)
        _require_enum(frame, "task_phase", TASK_PHASES)
        require_nonblank(frame.get("source_phase"), label="source_phase")
        _require_enum(frame, "control_mode", CONTROL_MODES)
        _require_enum(frame, "controller_owner", CONTROLLER_OWNERS)
        for field in ("source_class", "proof_mode", "control_mode", "controller_owner"):
            if frame[field] != raw_rollout[field]:
                raise ValueError(f"Frame {field} drifted from raw rollout")
        actions = frame.get("actions")
        if not isinstance(actions, dict) or set(actions) != set(ACTION_VARIANTS):
            raise ValueError("Frame action variants are incomplete")
        for variant, action in actions.items():
            _validate_action(action, label=f"{variant} action")
        for field in (
            "requested_gripper_pose",
            "achieved_gripper_pose",
            "contact_geometry_witness",
            "aperture",
            "effort",
        ):
            _validate_sourced_value(frame.get(field), label=field)
        _validate_reward_or_progress(frame.get("reward"), label="reward")
        _validate_reward_or_progress(frame.get("progress"), label="progress")
        strict_result = frame.get("strict_evaluator_result")
        if not isinstance(strict_result, dict) or not isinstance(strict_result.get("valid"), bool):
            raise ValueError("strict evaluator result is invalid")
        _validate_provenance(strict_result.get("provenance"), label="strict evaluator")
        boundary_events = frame.get("boundary_events")
        if not isinstance(boundary_events, list) or any(
            event not in HARD_BOUNDARY_EVENTS for event in boundary_events
        ):
            raise ValueError("Frame boundary events are invalid")
        if len(boundary_events) != len(set(boundary_events)):
            raise ValueError("Frame boundary events contain duplicates")
        actor_inputs = frame.get("actor_input_field_names")
        if not isinstance(actor_inputs, list) or any(
            not isinstance(field, str) for field in actor_inputs
        ):
            raise ValueError("Actor input field declaration is invalid")
        leaked = {
            field
            for field in actor_inputs
            if field.split(".", 1)[0] in PRIVILEGED_ACTOR_ROOTS
        }
        if leaked:
            raise ValueError(f"Frame actor input leaks privileged field: {sorted(leaked)}")


def _build_fixture_projection(
    *,
    grasp: dict[str, Any],
    grasp_ref: dict[str, Any],
    twin_ref: dict[str, Any],
    coordinate_ref: dict[str, Any],
) -> dict[str, Any]:
    prompt_text = "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."
    raw_payload = {
        "source_artifact_identity_sha256": grasp["identity_sha256"],
        "source_candidate_index": grasp["source_candidate_index"],
        "proof_mode": "simulation_unassisted",
        "phase_frame_counts": grasp["trajectory"]["full_lift_cycle"]["phase_frame_counts"],
        "strict_v2_valid_frame_counts": grasp["trajectory"]["full_lift_cycle"]["strict_v2_valid_frame_counts"],
        "unassisted_mujoco_grasp_success": grasp["unassisted_mujoco_grasp_success"],
    }
    raw_sha = _sha256(raw_payload)
    rollout_id = f"rollout-{raw_sha[:24]}"
    raw = {
        "schema_version": RAW_ROLLOUT_SCHEMA_VERSION,
        "rollout_id": rollout_id,
        "source_class": "mujoco_expert",
        "proof_mode": "simulation_unassisted",
        "controller_owner": "geometry_derived_mujoco_expert",
        "control_mode": "scripted_mujoco_expert",
        "prompt": {"text": prompt_text, "identity_sha256": _sha256(prompt_text)},
        "object_identity": "simulation_anchor_50x35x30mm",
        "workcell_identity": "scenesmith_mujoco_anchor_fixture",
        "environment_identity": "geometry_derived_unilateral_grasp_v1",
        "coordinate_contract_ref": coordinate_ref,
        "preprocessing_identity": "not_applicable_simulator_state_projection",
        "twin_profile_ref": twin_ref,
        "source_artifact_ref": grasp_ref,
        "start_timestamp_ns": 0,
        "end_timestamp_ns": 1_000_000,
        "frame_count": 2,
        "raw_payload_append_only": True,
        "raw_payload": raw_payload,
        "raw_payload_sha256": raw_sha,
        "evidence": [
            {
                "kind": "signed_simulation_artifact",
                "ref": grasp_ref["path"],
                "sha256": grasp_ref["file_sha256"],
            }
        ],
    }
    raw["record_identity_sha256"] = _record_identity(raw)
    frames = [
        _fixture_frame(
            raw=raw,
            index=0,
            timestamp_ns=0,
            phase="grasp_confirmed",
            source_phase="grasp_hold",
            source_pointer="/trajectory/full_lift_cycle/strict_v2_valid_frame_counts/grasp_hold",
            boundary_events=["rollout_start", "phase_change"],
            grasp_ref=grasp_ref,
            grasp=grasp,
        ),
        _fixture_frame(
            raw=raw,
            index=1,
            timestamp_ns=1_000_000,
            phase="stable_hold",
            source_phase="unsupported_lift_hold",
            source_pointer="/trajectory/full_lift_cycle/strict_v2_valid_frame_counts/unsupported_lift_hold",
            boundary_events=["phase_change", "rollout_end"],
            grasp_ref=grasp_ref,
            grasp=grasp,
        ),
    ]
    return {
        "fixture_role": "source_projection_contract_fixture_not_training_data",
        "raw_rollout": raw,
        "frames": frames,
        "training_eligible": False,
        "quarantine_reasons": [
            "source_artifact_does_not_retain_per_frame_requested_proposed_projected_sent_measured_actions",
            "source_artifact_does_not_retain_per_frame_requested_and_achieved_gripper_pose",
            "source_artifact_does_not_retain_simulation_actuator_effort",
            "hard_boundary_segments_and_unpadded_action_windows_not_compiled",
            "normalization_and_preprocessing_bundle_not_compiled",
        ],
    }


def _fixture_frame(
    *,
    raw: dict[str, Any],
    index: int,
    timestamp_ns: int,
    phase: str,
    source_phase: str,
    source_pointer: str,
    boundary_events: list[str],
    grasp_ref: dict[str, Any],
    grasp: dict[str, Any],
) -> dict[str, Any]:
    source_provenance = {
        "state": "derived",
        "source_ref": grasp_ref,
        "source_pointer": source_pointer,
        "derivation": "phase strict-v2 valid count equals the complete phase frame count",
    }
    unavailable_actions = {
        variant: {
            "state": "not_observed",
            "representation": None,
            "units": None,
            "ordered_joint_names": None,
            "values": None,
            "provenance": None,
            "reason": "source artifact does not retain this per-frame action variant",
        }
        for variant in ACTION_VARIANTS
    }
    frame = {
        "schema_version": FRAME_SCHEMA_VERSION,
        "frame_id": f"{raw['rollout_id']}-frame-{index:06d}",
        "rollout_id": raw["rollout_id"],
        "frame_index": index,
        "timestamp_ns": timestamp_ns,
        "task_phase": phase,
        "source_phase": source_phase,
        "source_class": raw["source_class"],
        "proof_mode": raw["proof_mode"],
        "controller_owner": raw["controller_owner"],
        "control_mode": raw["control_mode"],
        "actions": unavailable_actions,
        "requested_gripper_pose": _unavailable_value(
            "source artifact does not retain per-frame requested gripper pose"
        ),
        "achieved_gripper_pose": _unavailable_value(
            "source artifact does not retain per-frame achieved gripper pose"
        ),
        "contact_geometry_witness": {
            "state": "observed",
            "value": {"strict_v2_valid": True},
            "units": "boolean",
            "provenance": source_provenance,
            "reason": None,
        },
        "aperture": {
            "state": "derived",
            "value": grasp["derivation"]["target_aperture_m"],
            "units": "meter",
            "provenance": {
                "state": "derived",
                "source_ref": grasp_ref,
                "source_pointer": "/derivation/target_aperture_m",
                "derivation": "selected object width plus two pad normal half-thicknesses",
            },
            "reason": None,
        },
        "effort": _unavailable_value(
            "source artifact does not retain per-frame actuator effort"
        ),
        "reward": _unavailable_reward_or_progress(
            "source artifact does not retain reward components"
        ),
        "progress": _unavailable_reward_or_progress(
            "source artifact does not retain progress provenance"
        ),
        "strict_evaluator_result": {
            "valid": True,
            "evaluator": "strict_anchor_grasp_evaluator_v2",
            "provenance": source_provenance,
        },
        "boundary_events": boundary_events,
        "actor_input_field_names": [],
    }
    frame["record_identity_sha256"] = _record_identity(frame)
    return frame


def _validate_action(action: Any, *, label: str) -> None:
    if not isinstance(action, dict):
        raise ValueError(f"{label} must be an object")
    state = action.get("state")
    if state not in AVAILABILITY_STATES:
        raise ValueError(f"{label} state is invalid")
    if state in {"observed", "derived"}:
        require_nonblank(action.get("representation"), label=f"{label} representation")
        require_nonblank(action.get("units"), label=f"{label} units")
        if action.get("ordered_joint_names") != list(JOINT_NAMES):
            raise ValueError(f"{label} ordered joint names are invalid")
        values = action.get("values")
        if not isinstance(values, list) or len(values) != len(JOINT_NAMES):
            raise ValueError(f"{label} values are invalid")
        for value in values:
            require_finite_number(value, label=f"{label} value")
        _validate_provenance(action.get("provenance"), label=label)
        if action.get("reason") is not None:
            raise ValueError(f"{label} observed action must not carry a missing reason")
    else:
        if any(
            action.get(field) is not None
            for field in ("representation", "units", "ordered_joint_names", "values", "provenance")
        ):
            raise ValueError(f"{label} unavailable action must not carry values")
        require_nonblank(action.get("reason"), label=f"{label} unavailable reason")


def _validate_sourced_value(value: Any, *, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    state = value.get("state")
    if state not in AVAILABILITY_STATES:
        raise ValueError(f"{label} state is invalid")
    if state in {"observed", "derived"}:
        if value.get("value") is None:
            raise ValueError(f"{label} observed value is missing")
        require_nonblank(value.get("units"), label=f"{label} units")
        _validate_provenance(value.get("provenance"), label=label)
        if value.get("reason") is not None:
            raise ValueError(f"{label} observed value carries a missing reason")
    else:
        if any(value.get(field) is not None for field in ("value", "units", "provenance")):
            raise ValueError(f"{label} unavailable value must be null")
        require_nonblank(value.get("reason"), label=f"{label} unavailable reason")


def _validate_reward_or_progress(value: Any, *, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    state = value.get("state")
    if state not in AVAILABILITY_STATES:
        raise ValueError(f"{label} state is invalid")
    if state in {"observed", "derived"}:
        require_finite_number(value.get("value"), label=f"{label} value")
        if not isinstance(value.get("components"), list):
            raise ValueError(f"{label} components are invalid")
        _validate_provenance(value.get("provenance"), label=label)
        if value.get("reason") is not None:
            raise ValueError(f"{label} observed value carries a missing reason")
    else:
        if value.get("value") is not None or value.get("components") != [] or value.get("provenance") is not None:
            raise ValueError(f"{label} unavailable value must be null")
        require_nonblank(value.get("reason"), label=f"{label} unavailable reason")


def _validate_provenance(value: Any, *, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} provenance is required")
    if value.get("state") not in {"observed", "derived"}:
        raise ValueError(f"{label} provenance state is invalid")
    source_ref = value.get("source_ref")
    if not isinstance(source_ref, dict):
        raise ValueError(f"{label} provenance source reference is required")
    for field in ("path", "schema_version", "identity_sha256", "file_sha256"):
        require_nonblank(source_ref.get(field), label=f"{label} provenance {field}")
    for field in ("identity_sha256", "file_sha256"):
        _require_sha256(source_ref.get(field), label=f"{label} provenance {field}")
    require_nonblank(value.get("source_pointer"), label=f"{label} provenance source pointer")
    if value["state"] == "derived":
        require_nonblank(value.get("derivation"), label=f"{label} provenance derivation")
    elif value.get("derivation") is not None:
        raise ValueError(f"{label} observed provenance must not carry derivation")


def _unavailable_value(reason: str) -> dict[str, Any]:
    return {
        "state": "not_observed",
        "value": None,
        "units": None,
        "provenance": None,
        "reason": reason,
    }


def _unavailable_reward_or_progress(reason: str) -> dict[str, Any]:
    return {
        "state": "not_observed",
        "value": None,
        "components": [],
        "provenance": None,
        "reason": reason,
    }


def _require_enum(record: dict[str, Any], field: str, allowed: tuple[str, ...]) -> None:
    if record.get(field) not in allowed:
        raise ValueError(f"{field} is invalid")


def _require_nonnegative_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _require_sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest


def _record_identity(record: dict[str, Any]) -> str:
    unsigned = {
        key: value for key, value in record.items() if key != "record_identity_sha256"
    }
    return _sha256(unsigned)


def _verify_record_identity(record: dict[str, Any], *, label: str) -> None:
    if record.get("record_identity_sha256") != _record_identity(record):
        raise ValueError(f"{label} record identity drifted")


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
