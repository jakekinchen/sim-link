"""Deterministic, model-free audit of ACT tail cadence and observability."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.so101_coordinates import mujoco_to_lerobot


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = Path("configurations/robot_lab/f0a_chunk_phase_observability.json")
SCHEMA_VERSION = "scenesmith.f0a_chunk_phase_observability.v1"
SOURCE_BOUNDARY_COMMIT = "c433177b36baea3e7eea048ce743b509b61e3799"
BRIEF_ACTIVATION_COMMIT = "a6efa4b64b8a6e56aa090df8b7fd43006ec40c55"

F0_RESULT_PATH = Path("configurations/robot_lab/f0_release_gap_diagnosis.json")
R0_RETENTION_PATH = Path("configurations/robot_lab/t20_42_r0_retention_receipt.json")
R0_STATISTICS_PATH = Path("configurations/robot_lab/t20_42_r0_dataset_statistics.json")
R2_RETENTION_PATH = Path(
    "configurations/robot_lab/t20_43c_r2_act_retention_receipt.json"
)
R2_ROLLOUT_PATH = Path(
    "outputs/robot_lab/t20_43c_r2_act_replacement_run_001/rollouts/"
    "step_10000_chunk_50.json"
)
RUNNER_PATH = Path("scenesmith/robot_lab/t20_43b_r1_act_runner.py")
COORDINATE_PATH = Path("scenesmith/robot_lab/so101_coordinates.py")
PHASE_PLAN_PATH = Path("scenesmith/robot_lab/act_grasp_closed_loop.py")
ACT_MODEL_PATH = Path("external/lerobot/src/lerobot/policies/act/modeling_act.py")

EXPECTED_F0_IDENTITY = (
    "807d3da7e21bbf3ec846454bb13aa6a2cb92eac4f6dffe8d86becb0ad777e5f9"
)
EXPECTED_R0_RETENTION_IDENTITY = (
    "19d19fbaa315511fa0e7df736d3895089827da8f0b8a2aecd15a2a75885bd495"
)
EXPECTED_R0_STATISTICS_IDENTITY = (
    "02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae"
)
EXPECTED_R2_RETENTION_IDENTITY = (
    "e565e17a5d4f8a52c4d894d3d61f03cf4b38beaf1df0bec3b83ade7f05afc023"
)
EXPECTED_R2_ROLLOUT_IDENTITY = (
    "77bf82ce917c2a30cc3bfc915b887f0e6af98c8c8a397f022b633ccf23c7d19c"
)
EXPECTED_SOURCE_FILE_SHA256 = (
    "586a3e67034a577bf046381837aebe68d3d5febdce6b1c51dbcb6f0be4968b54"
)
EXPECTED_SOURCE_ROLLOUT_IDENTITY = (
    "9e186088c9ca82fa9c58cb6e3870f322a9c2a84405d5ea23152b822fb9d4abdb"
)

ROLLOUT_FRAMES = 244
DECODE_STARTS = (0, 50, 100, 150, 200)
EXECUTED_LENGTHS = (50, 50, 50, 50, 44)
LIFT_FRAMES = tuple(range(76, 100))
LOWER_FRAMES = tuple(range(176, 200))
RELEASE_START = 200
RELEASE_GATE_FRAME = 219
ALIAS_COUNT_THRESHOLD = 12
IMAGE_THRESHOLD_MULTIPLIER = 2.0
VELOCITY_COSINE_THRESHOLD = -0.8
TARGET_COSINE_THRESHOLD = -0.8
TARGET_NORM_MINIMUM_RAD = 0.01
GRIPPER_CONFLICT_RAD = 0.5
LAG_ALIGNMENT_TOLERANCE_FRAMES = 5
POLICY_INPUT_KEYS = (
    "observation.images.base_0_rgb",
    "observation.images.left_wrist_0_rgb",
    "observation.state",
)
EXPECTED_RAW_ACTOR_FIELDS = (
    "observation.joint_position",
    "observation.joint_velocity",
    "observation.top_rgb",
    "observation.wrist_rgb",
)
PHASE_PLAN = (
    ("approach", 14),
    ("pregrasp", 18),
    ("close", 36),
    ("grasp_hold", 8),
    ("unassisted_lift", 24),
    ("unsupported_lift_hold", 12),
    ("recording_stable_hold", 64),
    ("lower", 24),
    ("release", 12),
    ("release_settle", 8),
    ("retreat", 24),
)
PHASE_NAMES = tuple(name for name, _ in PHASE_PLAN)
FALSE_AUTHORITY_FIELDS = (
    "new_rendering_executed",
    "simulator_state_created",
    "checkpoint_tensor_read",
    "model_constructed",
    "model_loaded",
    "model_inference",
    "optimizer_created",
    "optimizer_training",
    "closed_loop_rollout_executed",
    "dataset_mutated",
    "statistics_changed",
    "gate_or_threshold_changed",
    "network_accessed",
    "external_compute_started",
    "brev_compute_started",
    "hardware_accessed",
    "physical_actuation",
    "gate_c_executed",
    "simulation_policy_accepted",
    "physical_transfer_ready",
    "promotion_eligible",
    "freeze_tag_authorized",
)


def analyze_observation_contract(
    *,
    dataset_feature_keys: list[str],
    raw_actor_input_fields: list[str],
    source_semantics: dict[str, bool],
) -> dict[str, Any]:
    semantics = _source_semantics(source_semantics)
    if not isinstance(dataset_feature_keys, list) or not all(
        isinstance(item, str) and item for item in dataset_feature_keys
    ):
        raise ValueError("F0a dataset feature keys are invalid")
    if len(dataset_feature_keys) != len(set(dataset_feature_keys)):
        raise ValueError("F0a dataset feature keys are duplicated")
    if not isinstance(raw_actor_input_fields, list) or not all(
        isinstance(item, str) and item for item in raw_actor_input_fields
    ):
        raise ValueError("F0a raw actor input fields are invalid")
    dataset_keys = sorted(dataset_feature_keys)
    raw_fields = sorted(raw_actor_input_fields)
    if raw_fields != list(EXPECTED_RAW_ACTOR_FIELDS):
        raise ValueError("F0a raw actor input field coverage drifted")
    for required in (*POLICY_INPUT_KEYS, "timestamp", "action"):
        if required not in dataset_keys:
            raise ValueError(f"F0a required dataset feature {required} is absent")
    omitted = {
        "joint_velocity": "observation.joint_velocity" not in POLICY_INPUT_KEYS,
        "phase": not any("phase" in item for item in POLICY_INPUT_KEYS),
        "progress": not any("progress" in item for item in POLICY_INPUT_KEYS),
        "timestamp": "timestamp" not in POLICY_INPUT_KEYS,
        "environment_state": not any("environment" in item for item in POLICY_INPUT_KEYS),
    }
    if not all(omitted.values()):
        raise ValueError("F0a consumed observation omission contract drifted")
    return {
        "dataset_feature_keys": dataset_keys,
        "raw_actor_input_fields": raw_fields,
        "consumed_policy_input_keys": list(POLICY_INPUT_KEYS),
        "dataset_has_timestamp_column": "timestamp" in dataset_keys,
        "raw_has_joint_velocity": "observation.joint_velocity" in raw_fields,
        "consumed_field_omissions": omitted,
        "source_semantics": semantics,
        "direction_disambiguating_fields_omitted": (
            omitted["joint_velocity"] and omitted["phase"] and omitted["progress"]
        ),
    }


def analyze_decode_progress(
    *,
    comparisons: list[dict[str, Any]],
    state_standard_deviation: list[float],
    decode_starts: list[int],
    f0_release_shift_frames: int,
) -> dict[str, Any]:
    rows = _comparison_rows(comparisons)
    std = _positive_vector(state_standard_deviation, "state standard deviation")
    starts = _decode_starts(decode_starts)
    if (
        isinstance(f0_release_shift_frames, bool)
        or not isinstance(f0_release_shift_frames, int)
        or f0_release_shift_frames < 0
    ):
        raise ValueError("F0a F0 release shift is invalid")
    source = [mujoco_to_lerobot(row["source_qpos_rad"]) for row in rows]
    candidate = [mujoco_to_lerobot(row["candidate_qpos_rad"]) for row in rows]
    progress_rows = []
    for start in starts:
        distances = [normalized_l2(candidate[start], value, std) for value in source]
        nearest_overall = _nearest_row(distances, range(ROLLOUT_FRAMES), rows)
        nearest_by_phase = {
            phase: _nearest_row(
                distances,
                (index for index, row in enumerate(rows) if row["phase"] == phase),
                rows,
            )
            for phase in PHASE_NAMES
        }
        progress_rows.append(
            {
                "decode_start_frame": start,
                "nearest_source_overall": nearest_overall,
                "nearest_source_by_phase": nearest_by_phase,
            }
        )
    final = next(row for row in progress_rows if row["decode_start_frame"] == RELEASE_START)
    nearest_lower = final["nearest_source_by_phase"]["lower"]
    nearest_lift = final["nearest_source_by_phase"]["unassisted_lift"]
    lag = RELEASE_START - nearest_lower["frame_index"]
    lag_alignment = (
        nearest_lower["frame_index"] < RELEASE_START
        and abs(lag - f0_release_shift_frames) <= LAG_ALIGNMENT_TOLERANCE_FRAMES
    )
    return {
        "normalization": "R0_observation_state_standard_deviation",
        "state_standard_deviation_lerobot_units": std,
        "decode_starts": starts,
        "decode_progress_rows": progress_rows,
        "frame_200_nearest_lower": nearest_lower,
        "frame_200_nearest_lift": nearest_lift,
        "frame_200_lower_state_lag_frames": lag,
        "f0_release_pattern_shift_frames": f0_release_shift_frames,
        "lag_alignment_tolerance_frames": LAG_ALIGNMENT_TOLERANCE_FRAMES,
        "lag_alignment_supported": lag_alignment,
    }


def analyze_reversal_alias(
    *,
    source_frames: list[dict[str, Any]],
    state_standard_deviation: list[float],
) -> dict[str, Any]:
    frames = _source_frames(source_frames)
    std = _positive_vector(state_standard_deviation, "state standard deviation")
    states = [mujoco_to_lerobot(row["qpos_rad"]) for row in frames]
    adjacent_indices = [*range(76, 99), *range(176, 199)]
    image_cache: dict[tuple[int, str], Any] = {}
    adjacent_state = [
        normalized_l2(states[index], states[index + 1], std)
        for index in adjacent_indices
    ]
    adjacent_image = [
        _image_pair_mae_rows(frames, index, index + 1, cache=image_cache)["mean"]
        for index in adjacent_indices
    ]
    state_p95 = nearest_rank_percentile(adjacent_state, 0.95)
    image_p95 = nearest_rank_percentile(adjacent_image, 0.95)
    image_threshold = IMAGE_THRESHOLD_MULTIPLIER * image_p95
    pair_rows = []
    for lower_index in LOWER_FRAMES:
        state_distances = {
            lift_index: normalized_l2(
                states[lower_index], states[lift_index], std
            )
            for lift_index in LIFT_FRAMES
        }
        lift_index = min(state_distances, key=lambda index: (state_distances[index], index))
        state_distance = state_distances[lift_index]
        images = _image_pair_mae_rows(
            frames, lower_index, lift_index, cache=image_cache
        )
        velocity_cosine = cosine(
            frames[lower_index]["qvel_rad_s"], frames[lift_index]["qvel_rad_s"]
        )
        lower_arm = _future_arm_displacement(frames, lower_index)
        lift_arm = _future_arm_displacement(frames, lift_index)
        lower_norm = vector_norm(lower_arm)
        lift_norm = vector_norm(lift_arm)
        arm_cosine = (
            cosine(lower_arm, lift_arm)
            if lower_norm >= TARGET_NORM_MINIMUM_RAD
            and lift_norm >= TARGET_NORM_MINIMUM_RAD
            else None
        )
        gripper_difference = max(
            abs(
                frames[lower_index + offset]["action_rad"][5]
                - frames[lift_index + offset]["action_rad"][5]
            )
            for offset in range(20)
        )
        state_near = state_distance <= state_p95
        image_near = images["mean"] <= image_threshold
        velocity_conflict = (
            velocity_cosine is not None
            and velocity_cosine <= VELOCITY_COSINE_THRESHOLD
        )
        arm_target_conflict = (
            arm_cosine is not None and arm_cosine <= TARGET_COSINE_THRESHOLD
        )
        gripper_target_conflict = gripper_difference >= GRIPPER_CONFLICT_RAD
        target_conflict = arm_target_conflict or gripper_target_conflict
        alias_pass = state_near and image_near and velocity_conflict and target_conflict
        pair_rows.append(
            {
                "lower_frame": lower_index,
                "lift_frame": lift_index,
                "normalized_state_l2": state_distance,
                "two_camera_image_mae": images["mean"],
                "image_mae_by_camera": images["by_camera"],
                "image_sha256_by_camera": {
                    camera: {
                        "lower": frames[lower_index]["images"][camera]["image_sha256"],
                        "lift": frames[lift_index]["images"][camera]["image_sha256"],
                    }
                    for camera in ("top", "wrist")
                },
                "joint_velocity_cosine": velocity_cosine,
                "next_ten_arm_displacement_lower_rad": lower_arm,
                "next_ten_arm_displacement_lift_rad": lift_arm,
                "next_ten_arm_displacement_lower_norm_rad": lower_norm,
                "next_ten_arm_displacement_lift_norm_rad": lift_norm,
                "next_ten_arm_displacement_cosine": arm_cosine,
                "next_twenty_gripper_maximum_difference_rad": gripper_difference,
                "state_near": state_near,
                "image_near": image_near,
                "hidden_velocity_direction_conflict": velocity_conflict,
                "arm_target_direction_conflict": arm_target_conflict,
                "gripper_target_conflict": gripper_target_conflict,
                "future_target_conflict": target_conflict,
                "alias_pass": alias_pass,
            }
        )
    alias_count = sum(row["alias_pass"] for row in pair_rows)
    return {
        "lift_frame_range_inclusive": [LIFT_FRAMES[0], LIFT_FRAMES[-1]],
        "lower_frame_range_inclusive": [LOWER_FRAMES[0], LOWER_FRAMES[-1]],
        "nearest_rank_percentile_method": True,
        "adjacent_reference_pair_count": len(adjacent_indices),
        "adjacent_normalized_state_l2": adjacent_state,
        "adjacent_two_camera_image_mae": adjacent_image,
        "adjacent_state_l2_p95": state_p95,
        "adjacent_image_mae_p95": image_p95,
        "image_threshold_multiplier": IMAGE_THRESHOLD_MULTIPLIER,
        "state_near_threshold": state_p95,
        "image_near_threshold": image_threshold,
        "velocity_cosine_threshold": VELOCITY_COSINE_THRESHOLD,
        "target_cosine_threshold": TARGET_COSINE_THRESHOLD,
        "target_norm_minimum_rad": TARGET_NORM_MINIMUM_RAD,
        "gripper_conflict_threshold_rad": GRIPPER_CONFLICT_RAD,
        "pair_rows": pair_rows,
        "alias_pass_count": alias_count,
        "alias_pair_count": len(pair_rows),
        "alias_count_threshold": ALIAS_COUNT_THRESHOLD,
        "source_corridor_alias_supported": alias_count >= ALIAS_COUNT_THRESHOLD,
    }


def analyze_cadence_coupling(
    *,
    decode_progress: dict[str, Any],
    decode_starts: list[int],
    release_gate_passed: bool,
    retreat_final_clear_passed: bool,
) -> dict[str, Any]:
    starts = _decode_starts(decode_starts)
    if not isinstance(release_gate_passed, bool) or not isinstance(
        retreat_final_clear_passed, bool
    ):
        raise ValueError("F0a cadence gate flags are invalid")
    shift = decode_progress.get("f0_release_pattern_shift_frames")
    if isinstance(shift, bool) or not isinstance(shift, int) or shift < 0:
        raise ValueError("F0a cadence shift is invalid")
    aligned_onset = RELEASE_START + shift
    observations_between = [
        frame for frame in starts if RELEASE_START < frame <= aligned_onset
    ]
    supported = (
        decode_progress.get("lag_alignment_supported") is True
        and aligned_onset > RELEASE_GATE_FRAME
        and not observations_between
        and not release_gate_passed
        and retreat_final_clear_passed
    )
    return {
        "release_start_frame": RELEASE_START,
        "release_settle_final_gate_frame": RELEASE_GATE_FRAME,
        "aligned_candidate_release_onset_frame": aligned_onset,
        "decode_starts": starts,
        "policy_observation_frames_after_200_through_aligned_onset": observations_between,
        "release_final_contact_clear_passed": release_gate_passed,
        "retreat_final_contact_clear_passed": retreat_final_clear_passed,
        "lag_alignment_supported": decode_progress.get("lag_alignment_supported"),
        "tail_cadence_gate_coupling_supported": supported,
    }


def build_f0a_result(
    *,
    source_refs: list[dict[str, Any]],
    source_semantics: dict[str, bool],
    observation_contract: dict[str, Any],
    decode_progress: dict[str, Any],
    reversal_alias: dict[str, Any],
    cadence_coupling: dict[str, Any],
) -> dict[str, Any]:
    refs = _source_refs(source_refs)
    semantics = _source_semantics(source_semantics)
    contract = _verify_observation_contract(observation_contract, semantics)
    progress = _verify_decode_progress(decode_progress)
    alias = _verify_reversal_alias(reversal_alias)
    cadence = _verify_cadence(cadence_coupling, progress)
    reversal_defect = (
        alias["source_corridor_alias_supported"]
        and contract["direction_disambiguating_fields_omitted"]
    )
    cadence_supported = cadence["tail_cadence_gate_coupling_supported"]
    if cadence_supported:
        route = "open_separately_reviewed_f0b_hybrid_tail_cadence_evaluation"
    elif reversal_defect:
        route = "propose_velocity_augmented_act_schema_without_training"
    else:
        route = "close_f0_family_without_corrective_training"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": "F0a",
        "scope": "model_free_chunk_timing_and_phase_observability_audit",
        "source_boundary_commit": SOURCE_BOUNDARY_COMMIT,
        "brief_activation_commit": BRIEF_ACTIVATION_COMMIT,
        "source_refs": refs,
        "source_semantics": semantics,
        "observation_contract": contract,
        "decode_progress_analysis": progress,
        "reversal_alias_analysis": alias,
        "cadence_coupling_analysis": cadence,
        "findings": {
            "reversal_observability_defect_supported": reversal_defect,
            "tail_cadence_gate_coupling_supported": cadence_supported,
            "wall_clock_phase_token_licensed": False,
        },
        "selected_route": route,
        "f0b_hybrid_schedule": {
            "decode_starts": [0, 50, 100, 150, 176, 186, 196, 206, 216, 226, 236],
            "executed_lengths": [50, 50, 50, 26, 10, 10, 10, 10, 10, 10, 8],
            "tail_transition_frame": 176,
            "frozen_gate_c_unchanged": True,
            "optimizer_training": False,
        },
        "corrective_training_selected": False,
        "single_corrective_rung_consumed": False,
        "training_lock": "closed",
        "retained_prior_model_inference_evidence_read": True,
        "retained_prior_rollout_evidence_read": True,
    }
    payload.update({field: False for field in FALSE_AUTHORITY_FIELDS})
    return sign_payload(payload)


def verify_f0a_result(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="F0a chunk/phase observability")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != "F0a"
        or payload.get("source_boundary_commit") != SOURCE_BOUNDARY_COMMIT
        or payload.get("brief_activation_commit") != BRIEF_ACTIVATION_COMMIT
    ):
        raise ValueError("F0a result header drifted")
    expected = build_f0a_result(
        source_refs=payload.get("source_refs"),
        source_semantics=payload.get("source_semantics"),
        observation_contract=payload.get("observation_contract"),
        decode_progress=payload.get("decode_progress_analysis"),
        reversal_alias=payload.get("reversal_alias_analysis"),
        cadence_coupling=payload.get("cadence_coupling_analysis"),
    )
    if payload != expected:
        raise ValueError("F0a chunk/phase observability result drifted")


def build_live_f0a_result(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    f0 = load_strict_json(root / F0_RESULT_PATH)
    r0_retention = load_strict_json(root / R0_RETENTION_PATH)
    r0_statistics = load_strict_json(root / R0_STATISTICS_PATH)
    r2_retention = load_strict_json(root / R2_RETENTION_PATH)
    rollout = load_strict_json(root / R2_ROLLOUT_PATH)
    for label, payload, expected_identity in (
        ("F0 result", f0, EXPECTED_F0_IDENTITY),
        ("R0 retention", r0_retention, EXPECTED_R0_RETENTION_IDENTITY),
        ("R0 statistics", r0_statistics, EXPECTED_R0_STATISTICS_IDENTITY),
        ("R2 retention", r2_retention, EXPECTED_R2_RETENTION_IDENTITY),
        ("R2 rollout", rollout, EXPECTED_R2_ROLLOUT_IDENTITY),
    ):
        verify_signed_payload(payload, label=label)
        if payload.get("identity_sha256") != expected_identity:
            raise ValueError(f"F0a {label} identity drifted")

    dataset_tree = r0_retention["local_output_trees"]["lerobot_dataset"]
    info_ref = _retained_ref(dataset_tree, "meta/info.json")
    stats_ref = _retained_ref(dataset_tree, "meta/stats.json")
    info_path = root / dataset_tree["root"] / info_ref["path"]
    stats_path = root / dataset_tree["root"] / stats_ref["path"]
    rollout_ref = _retained_ref(
        r2_retention["local_output_trees"]["rollouts"],
        "step_10000_chunk_50.json",
    )
    _verify_file(info_path, info_ref)
    _verify_file(stats_path, stats_ref)
    _verify_file(root / R2_ROLLOUT_PATH, rollout_ref)

    source_ref = rollout.get("source_episode_ref")
    if not isinstance(source_ref, dict):
        raise ValueError("F0a source episode reference is absent")
    source_path = root / source_ref.get("path", "")
    if (
        source_ref.get("file_sha256") != EXPECTED_SOURCE_FILE_SHA256
        or source_ref.get("raw_rollout_identity_sha256")
        != EXPECTED_SOURCE_ROLLOUT_IDENTITY
    ):
        raise ValueError("F0a source episode identity drifted")
    if _sha_file(source_path) != EXPECTED_SOURCE_FILE_SHA256:
        raise ValueError("F0a source episode file drifted")

    info = load_strict_json(info_path)
    meta_stats = load_strict_json(stats_path)
    raw = load_strict_json(source_path)
    if (
        raw.get("raw_rollout", {}).get("record_identity_sha256")
        != EXPECTED_SOURCE_ROLLOUT_IDENTITY
    ):
        raise ValueError("F0a source raw rollout drifted")
    raw_frames = _live_source_frames(raw.get("frames"))
    comparisons = rollout.get("comparisons")
    comparison_rows = _comparison_rows(comparisons)
    maximum_source_qpos_error = max(
        abs(left - right)
        for raw_row, trace_row in zip(raw_frames, comparison_rows, strict=True)
        for left, right in zip(
            raw_row["qpos_rad"], trace_row["source_qpos_rad"], strict=True
        )
    )
    if maximum_source_qpos_error != 0.0:
        raise ValueError("F0a raw/trace source qpos binding drifted")

    tracked_state = r0_statistics.get("features", {}).get("observation.state")
    meta_state = meta_stats.get("observation.state")
    if (
        not isinstance(tracked_state, dict)
        or not isinstance(meta_state, dict)
        or tracked_state.get("mean") != meta_state.get("mean")
        or tracked_state.get("std") != meta_state.get("std")
    ):
        raise ValueError("F0a tracked/meta observation statistics drifted")
    state_std = tracked_state["std"]
    semantics = _live_source_semantics(root, info)
    actor_fields = raw.get("frames", [{}])[0].get("actor_input_field_names")
    contract = analyze_observation_contract(
        dataset_feature_keys=list(info.get("features", {})),
        raw_actor_input_fields=actor_fields,
        source_semantics=semantics,
    )
    shift = f0.get("retained_rollout_analysis", {}).get(
        "best_release_pattern_shift_frames"
    )
    progress = analyze_decode_progress(
        comparisons=comparisons,
        state_standard_deviation=state_std,
        decode_starts=rollout.get("decode_start_frames"),
        f0_release_shift_frames=shift,
    )
    alias = analyze_reversal_alias(
        source_frames=raw_frames,
        state_standard_deviation=state_std,
    )
    gates = rollout.get("closed_loop", {}).get("gate_margins", {})
    cadence = analyze_cadence_coupling(
        decode_progress=progress,
        decode_starts=rollout.get("decode_start_frames"),
        release_gate_passed=gates.get("release_final_contact_clear", {}).get(
            "passed"
        ),
        retreat_final_clear_passed=gates.get(
            "retreat_final_contact_clear", {}
        ).get("passed"),
    )
    refs = _live_source_refs(
        root,
        f0=f0,
        r0_retention=r0_retention,
        r0_statistics=r0_statistics,
        r2_retention=r2_retention,
        rollout=rollout,
        info_path=info_path,
        info_ref=info_ref,
        stats_path=stats_path,
        stats_ref=stats_ref,
        source_path=source_path,
    )
    result = build_f0a_result(
        source_refs=refs,
        source_semantics=semantics,
        observation_contract=contract,
        decode_progress=progress,
        reversal_alias=alias,
        cadence_coupling=cadence,
    )
    verify_f0a_result(result)
    return result


def write_result(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = build_live_f0a_result(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / RESULT_PATH, result)
    return result


def verify_result_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    archived = load_strict_json(root / RESULT_PATH)
    verify_f0a_result(archived)
    expected = build_live_f0a_result(repo_root=root)
    if archived != expected:
        raise ValueError("F0a archived result drifted from live sources")
    return archived


def normalized_l2(left: list[float], right: list[float], scale: list[float]) -> float:
    if not len(left) == len(right) == len(scale) or not left:
        raise ValueError("F0a normalized L2 vector coverage drifted")
    values = [
        (_finite(a, "normalized L2 value") - _finite(b, "normalized L2 value"))
        / _positive_finite(s, "normalized L2 scale")
        for a, b, s in zip(left, right, scale, strict=True)
    ]
    return math.sqrt(sum(value * value for value in values))


def vector_norm(value: list[float]) -> float:
    vector = [_finite(item, "vector value") for item in value]
    return math.sqrt(sum(item * item for item in vector))


def cosine(left: list[float], right: list[float]) -> float | None:
    if not len(left) == len(right) or not left:
        raise ValueError("F0a cosine vector coverage drifted")
    a = [_finite(item, "cosine value") for item in left]
    b = [_finite(item, "cosine value") for item in right]
    denominator = vector_norm(a) * vector_norm(b)
    if denominator <= 1e-12:
        return None
    return sum(x * y for x, y in zip(a, b, strict=True)) / denominator


def nearest_rank_percentile(values: list[float], probability: float) -> float:
    numbers = sorted(_finite(item, "percentile value") for item in values)
    if not numbers:
        raise ValueError("F0a percentile values are absent")
    if not 0.0 < probability <= 1.0:
        raise ValueError("F0a percentile probability is invalid")
    rank = max(1, math.ceil(probability * len(numbers)))
    return numbers[rank - 1]


def image_pair_mae(
    frames: list[dict[str, Any]],
    left_index: int,
    right_index: int,
    *,
    cache: dict[tuple[int, str], Any] | None = None,
) -> dict[str, Any]:
    rows = _source_frames(frames)
    return _image_pair_mae_rows(
        rows, left_index, right_index, cache={} if cache is None else cache
    )


def _image_pair_mae_rows(
    rows: list[dict[str, Any]],
    left_index: int,
    right_index: int,
    *,
    cache: dict[tuple[int, str], Any],
) -> dict[str, Any]:
    import numpy as np

    if not 0 <= left_index < len(rows) or not 0 <= right_index < len(rows):
        raise ValueError("F0a image pair index is invalid")
    by_camera = {}
    total_absolute_difference = 0
    total_values = 0
    for camera in ("top", "wrist"):
        arrays = []
        for index in (left_index, right_index):
            key = (index, camera)
            if key not in cache:
                cache[key] = _decode_image(rows[index]["images"][camera])
            arrays.append(cache[key])
        left, right = arrays
        if left.shape != right.shape or left.shape != (256, 256, 3):
            raise ValueError("F0a image shape drifted")
        absolute = np.abs(left.astype(np.int16) - right.astype(np.int16))
        camera_sum = int(absolute.sum(dtype=np.int64))
        camera_values = int(absolute.size)
        by_camera[camera] = camera_sum / (camera_values * 255)
        total_absolute_difference += camera_sum
        total_values += camera_values
    return {
        "by_camera": by_camera,
        "mean": total_absolute_difference / (total_values * 255),
    }


def phase_for_frame(frame_index: int) -> str:
    if (
        isinstance(frame_index, bool)
        or not isinstance(frame_index, int)
        or not 0 <= frame_index < ROLLOUT_FRAMES
    ):
        raise ValueError("F0a frame index is outside the phase plan")
    cursor = 0
    for phase, count in PHASE_PLAN:
        cursor += count
        if frame_index < cursor:
            return phase
    raise AssertionError("unreachable")


def _future_arm_displacement(
    frames: list[dict[str, Any]], frame_index: int
) -> list[float]:
    end = frame_index + 9
    if end >= len(frames):
        raise ValueError("F0a future arm displacement exceeds source")
    return [
        frames[end]["action_rad"][joint] - frames[frame_index]["action_rad"][joint]
        for joint in range(5)
    ]


def _nearest_row(
    distances: list[float], indices: Any, rows: list[dict[str, Any]]
) -> dict[str, Any]:
    candidates = list(indices)
    if not candidates:
        raise ValueError("F0a nearest-source candidate set is empty")
    index = min(candidates, key=lambda value: (distances[value], value))
    return {
        "frame_index": index,
        "phase": rows[index]["phase"],
        "normalized_state_l2": distances[index],
    }


def _decode_starts(value: Any) -> list[int]:
    if value != list(DECODE_STARTS):
        raise ValueError("F0a decode starts drifted")
    return list(DECODE_STARTS)


def _comparison_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != ROLLOUT_FRAMES:
        raise ValueError("F0a comparison coverage drifted")
    rows = []
    for index, row in enumerate(value):
        if not isinstance(row, dict) or row.get("frame_index") != index:
            raise ValueError("F0a comparison order drifted")
        phase = row.get("phase")
        if phase != phase_for_frame(index):
            raise ValueError("F0a comparison phase drifted")
        rows.append(
            {
                "frame_index": index,
                "phase": phase,
                "source_qpos_rad": _vector(row.get("source_qpos_rad"), "source qpos"),
                "candidate_qpos_rad": _vector(
                    row.get("candidate_qpos_rad"), "candidate qpos"
                ),
            }
        )
    return rows


def _source_frames(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != ROLLOUT_FRAMES:
        raise ValueError("F0a source frame coverage drifted")
    rows = []
    for index, row in enumerate(value):
        if not isinstance(row, dict) or row.get("frame_index") != index:
            raise ValueError("F0a source frame order drifted")
        phase = row.get("phase")
        if phase != phase_for_frame(index):
            raise ValueError("F0a source frame phase drifted")
        images = row.get("images")
        if not isinstance(images, dict) or set(images) != {"top", "wrist"}:
            raise ValueError("F0a source image coverage drifted")
        normalized_images = {
            camera: _image_payload(images[camera]) for camera in ("top", "wrist")
        }
        rows.append(
            {
                "frame_index": index,
                "phase": phase,
                "qpos_rad": _vector(row.get("qpos_rad"), "source qpos"),
                "qvel_rad_s": _vector(row.get("qvel_rad_s"), "source qvel"),
                "action_rad": _vector(row.get("action_rad"), "source action"),
                "images": normalized_images,
            }
        )
    return rows


def _live_source_frames(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != ROLLOUT_FRAMES:
        raise ValueError("F0a live source frames are absent")
    rows = []
    for index, row in enumerate(value):
        observations = row.get("observations", {})
        actions = row.get("actions", {}).get("requested", {})
        rows.append(
            {
                "frame_index": row.get("frame_index"),
                "phase": row.get("source_phase"),
                "qpos_rad": observations.get("joint_position_mujoco_rad"),
                "qvel_rad_s": observations.get("joint_velocity_mujoco_rad_s"),
                "action_rad": actions.get("values"),
                "images": {
                    "top": observations.get("top"),
                    "wrist": observations.get("wrist"),
                },
            }
        )
    return _source_frames(rows)


def _image_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("F0a image payload is absent")
    expected = {
        "channels": 3,
        "encoding": "png",
        "height": 256,
        "width": 256,
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            raise ValueError("F0a image metadata drifted")
    _sha(value.get("image_sha256"), "image")
    encoded = value.get("png_base64")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("F0a image bytes are absent")
    return {
        **expected,
        "image_sha256": value["image_sha256"],
        "png_base64": encoded,
    }


def _decode_image(value: dict[str, Any]):
    import numpy as np
    from PIL import Image

    payload = _image_payload(value)
    try:
        png = base64.b64decode(payload["png_base64"], validate=True)
    except ValueError as error:
        raise ValueError("F0a image base64 is invalid") from error
    if hashlib.sha256(png).hexdigest() != payload["image_sha256"]:
        raise ValueError("F0a image SHA-256 drifted")
    with Image.open(io.BytesIO(png)) as image:
        if image.size != (256, 256):
            raise ValueError("F0a decoded image dimensions drifted")
        return np.asarray(image.convert("RGB"), dtype=np.uint8).copy()


def _verify_observation_contract(
    value: Any, semantics: dict[str, bool]
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("F0a observation contract is absent")
    expected = analyze_observation_contract(
        dataset_feature_keys=value.get("dataset_feature_keys"),
        raw_actor_input_fields=value.get("raw_actor_input_fields"),
        source_semantics=semantics,
    )
    if value != expected:
        raise ValueError("F0a observation contract drifted")
    return expected


def _verify_decode_progress(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("F0a decode progress is absent")
    std = _positive_vector(
        value.get("state_standard_deviation_lerobot_units"),
        "state standard deviation",
    )
    starts = _decode_starts(value.get("decode_starts"))
    rows = value.get("decode_progress_rows")
    if not isinstance(rows, list) or len(rows) != len(starts):
        raise ValueError("F0a decode progress row coverage drifted")
    for start, row in zip(starts, rows, strict=True):
        if not isinstance(row, dict) or row.get("decode_start_frame") != start:
            raise ValueError("F0a decode progress row order drifted")
        _nearest_source_entry(row.get("nearest_source_overall"))
        by_phase = row.get("nearest_source_by_phase")
        if not isinstance(by_phase, dict) or set(by_phase) != set(PHASE_NAMES):
            raise ValueError("F0a decode phase-nearest coverage drifted")
        for phase, entry in by_phase.items():
            normalized = _nearest_source_entry(entry)
            if normalized["phase"] != phase:
                raise ValueError("F0a decode phase-nearest identity drifted")
    final = next(row for row in rows if row["decode_start_frame"] == RELEASE_START)
    lower = _nearest_source_entry(final["nearest_source_by_phase"]["lower"])
    lift = _nearest_source_entry(
        final["nearest_source_by_phase"]["unassisted_lift"]
    )
    lag = RELEASE_START - lower["frame_index"]
    shift = value.get("f0_release_pattern_shift_frames")
    if isinstance(shift, bool) or not isinstance(shift, int) or shift < 0:
        raise ValueError("F0a release shift drifted")
    supported = (
        lower["frame_index"] < RELEASE_START
        and abs(lag - shift) <= LAG_ALIGNMENT_TOLERANCE_FRAMES
    )
    expected = {
        "normalization": "R0_observation_state_standard_deviation",
        "state_standard_deviation_lerobot_units": std,
        "decode_starts": starts,
        "decode_progress_rows": rows,
        "frame_200_nearest_lower": lower,
        "frame_200_nearest_lift": lift,
        "frame_200_lower_state_lag_frames": lag,
        "f0_release_pattern_shift_frames": shift,
        "lag_alignment_tolerance_frames": LAG_ALIGNMENT_TOLERANCE_FRAMES,
        "lag_alignment_supported": supported,
    }
    if value != expected:
        raise ValueError("F0a decode progress analysis drifted")
    return expected


def _nearest_source_entry(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "frame_index",
        "phase",
        "normalized_state_l2",
    }:
        raise ValueError("F0a nearest-source entry drifted")
    frame = value["frame_index"]
    if isinstance(frame, bool) or not isinstance(frame, int) or not 0 <= frame < ROLLOUT_FRAMES:
        raise ValueError("F0a nearest-source frame drifted")
    if value["phase"] != phase_for_frame(frame):
        raise ValueError("F0a nearest-source phase drifted")
    return {
        "frame_index": frame,
        "phase": value["phase"],
        "normalized_state_l2": _finite(
            value["normalized_state_l2"], "nearest-source distance"
        ),
    }


def _verify_reversal_alias(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("F0a reversal alias analysis is absent")
    adjacent_state = _finite_list(
        value.get("adjacent_normalized_state_l2"), "adjacent state"
    )
    adjacent_image = _finite_list(
        value.get("adjacent_two_camera_image_mae"), "adjacent image"
    )
    if len(adjacent_state) != 46 or len(adjacent_image) != 46:
        raise ValueError("F0a adjacent reference coverage drifted")
    state_p95 = nearest_rank_percentile(adjacent_state, 0.95)
    image_p95 = nearest_rank_percentile(adjacent_image, 0.95)
    image_threshold = IMAGE_THRESHOLD_MULTIPLIER * image_p95
    pair_rows = value.get("pair_rows")
    if not isinstance(pair_rows, list) or len(pair_rows) != len(LOWER_FRAMES):
        raise ValueError("F0a reversal pair coverage drifted")
    normalized_rows = []
    for lower_index, row in zip(LOWER_FRAMES, pair_rows, strict=True):
        normalized_rows.append(
            _verify_alias_pair(
                row,
                lower_index=lower_index,
                state_threshold=state_p95,
                image_threshold=image_threshold,
            )
        )
    alias_count = sum(row["alias_pass"] for row in normalized_rows)
    expected = {
        "lift_frame_range_inclusive": [LIFT_FRAMES[0], LIFT_FRAMES[-1]],
        "lower_frame_range_inclusive": [LOWER_FRAMES[0], LOWER_FRAMES[-1]],
        "nearest_rank_percentile_method": True,
        "adjacent_reference_pair_count": 46,
        "adjacent_normalized_state_l2": adjacent_state,
        "adjacent_two_camera_image_mae": adjacent_image,
        "adjacent_state_l2_p95": state_p95,
        "adjacent_image_mae_p95": image_p95,
        "image_threshold_multiplier": IMAGE_THRESHOLD_MULTIPLIER,
        "state_near_threshold": state_p95,
        "image_near_threshold": image_threshold,
        "velocity_cosine_threshold": VELOCITY_COSINE_THRESHOLD,
        "target_cosine_threshold": TARGET_COSINE_THRESHOLD,
        "target_norm_minimum_rad": TARGET_NORM_MINIMUM_RAD,
        "gripper_conflict_threshold_rad": GRIPPER_CONFLICT_RAD,
        "pair_rows": normalized_rows,
        "alias_pass_count": alias_count,
        "alias_pair_count": len(normalized_rows),
        "alias_count_threshold": ALIAS_COUNT_THRESHOLD,
        "source_corridor_alias_supported": alias_count >= ALIAS_COUNT_THRESHOLD,
    }
    if value != expected:
        raise ValueError("F0a reversal alias analysis drifted")
    return expected


def _verify_alias_pair(
    value: Any,
    *,
    lower_index: int,
    state_threshold: float,
    image_threshold: float,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("F0a alias pair is absent")
    expected_keys = {
        "lower_frame",
        "lift_frame",
        "normalized_state_l2",
        "two_camera_image_mae",
        "image_mae_by_camera",
        "image_sha256_by_camera",
        "joint_velocity_cosine",
        "next_ten_arm_displacement_lower_rad",
        "next_ten_arm_displacement_lift_rad",
        "next_ten_arm_displacement_lower_norm_rad",
        "next_ten_arm_displacement_lift_norm_rad",
        "next_ten_arm_displacement_cosine",
        "next_twenty_gripper_maximum_difference_rad",
        "state_near",
        "image_near",
        "hidden_velocity_direction_conflict",
        "arm_target_direction_conflict",
        "gripper_target_conflict",
        "future_target_conflict",
        "alias_pass",
    }
    if set(value) != expected_keys:
        raise ValueError("F0a alias pair schema drifted")
    if value.get("lower_frame") != lower_index or value.get("lift_frame") not in LIFT_FRAMES:
        raise ValueError("F0a alias pair frame identity drifted")
    state_distance = _finite(value.get("normalized_state_l2"), "pair state distance")
    image_mae = _finite(value.get("two_camera_image_mae"), "pair image MAE")
    image_by_camera = value.get("image_mae_by_camera")
    if not isinstance(image_by_camera, dict) or set(image_by_camera) != {"top", "wrist"}:
        raise ValueError("F0a alias pair image metric coverage drifted")
    normalized_image_by_camera = {
        camera: _finite(image_by_camera[camera], "pair camera image MAE")
        for camera in ("top", "wrist")
    }
    if not math.isclose(
        image_mae,
        sum(normalized_image_by_camera.values()) / 2.0,
        rel_tol=0.0,
        abs_tol=1e-15,
    ):
        raise ValueError("F0a alias pair image mean drifted")
    image_sha = value.get("image_sha256_by_camera")
    if not isinstance(image_sha, dict) or set(image_sha) != {"top", "wrist"}:
        raise ValueError("F0a alias pair image SHA coverage drifted")
    normalized_image_sha = {}
    for camera in ("top", "wrist"):
        row = image_sha[camera]
        if not isinstance(row, dict) or set(row) != {"lower", "lift"}:
            raise ValueError("F0a alias pair image SHA schema drifted")
        _sha(row["lower"], "pair lower image")
        _sha(row["lift"], "pair lift image")
        normalized_image_sha[camera] = dict(row)
    velocity_cosine = _optional_finite(
        value.get("joint_velocity_cosine"), "pair velocity cosine"
    )
    lower_arm = _vector5(
        value.get("next_ten_arm_displacement_lower_rad"), "lower arm displacement"
    )
    lift_arm = _vector5(
        value.get("next_ten_arm_displacement_lift_rad"), "lift arm displacement"
    )
    lower_norm = vector_norm(lower_arm)
    lift_norm = vector_norm(lift_arm)
    arm_cosine = (
        cosine(lower_arm, lift_arm)
        if lower_norm >= TARGET_NORM_MINIMUM_RAD
        and lift_norm >= TARGET_NORM_MINIMUM_RAD
        else None
    )
    gripper_difference = _finite(
        value.get("next_twenty_gripper_maximum_difference_rad"),
        "pair gripper difference",
    )
    state_near = state_distance <= state_threshold
    image_near = image_mae <= image_threshold
    velocity_conflict = (
        velocity_cosine is not None and velocity_cosine <= VELOCITY_COSINE_THRESHOLD
    )
    arm_conflict = arm_cosine is not None and arm_cosine <= TARGET_COSINE_THRESHOLD
    gripper_conflict = gripper_difference >= GRIPPER_CONFLICT_RAD
    target_conflict = arm_conflict or gripper_conflict
    alias_pass = state_near and image_near and velocity_conflict and target_conflict
    expected = dict(value)
    expected.update(
        {
            "normalized_state_l2": state_distance,
            "two_camera_image_mae": image_mae,
            "image_mae_by_camera": normalized_image_by_camera,
            "image_sha256_by_camera": normalized_image_sha,
            "joint_velocity_cosine": velocity_cosine,
            "next_ten_arm_displacement_lower_rad": lower_arm,
            "next_ten_arm_displacement_lift_rad": lift_arm,
            "next_ten_arm_displacement_lower_norm_rad": lower_norm,
            "next_ten_arm_displacement_lift_norm_rad": lift_norm,
            "next_ten_arm_displacement_cosine": arm_cosine,
            "next_twenty_gripper_maximum_difference_rad": gripper_difference,
            "state_near": state_near,
            "image_near": image_near,
            "hidden_velocity_direction_conflict": velocity_conflict,
            "arm_target_direction_conflict": arm_conflict,
            "gripper_target_conflict": gripper_conflict,
            "future_target_conflict": target_conflict,
            "alias_pass": alias_pass,
        }
    )
    if value != expected:
        raise ValueError("F0a alias pair decision drifted")
    return expected


def _verify_cadence(value: Any, progress: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("F0a cadence coupling analysis is absent")
    expected = analyze_cadence_coupling(
        decode_progress=progress,
        decode_starts=value.get("decode_starts"),
        release_gate_passed=value.get("release_final_contact_clear_passed"),
        retreat_final_clear_passed=value.get("retreat_final_contact_clear_passed"),
    )
    if value != expected:
        raise ValueError("F0a cadence coupling analysis drifted")
    return expected


def _source_semantics(value: Any) -> dict[str, bool]:
    expected = {
        "act_config_has_exactly_two_images_and_six_state_inputs",
        "act_runner_decodes_only_at_queue_empty",
        "act_runner_feeds_qpos_only_state_slice",
        "dataset_state_feature_has_six_positions",
        "dataset_timestamp_not_policy_input",
        "phase_plan_matches_frozen_244_frames",
        "raw_actor_fields_include_joint_velocity",
    }
    if (
        not isinstance(value, dict)
        or set(value) != expected
        or any(item is not True for item in value.values())
    ):
        raise ValueError("F0a source semantics drifted")
    return {key: True for key in sorted(expected)}


def _live_source_semantics(root: Path, info: dict[str, Any]) -> dict[str, bool]:
    runner = (root / RUNNER_PATH).read_text()
    model = (root / ACT_MODEL_PATH).read_text()
    from scenesmith.robot_lab.act_grasp_closed_loop import (
        PHASE_PLAN as live_phase_plan,
    )

    features = info.get("features", {})
    semantics = {
        "act_config_has_exactly_two_images_and_six_state_inputs": all(
            token in runner
            for token in (
                '"observation.images.base_0_rgb": PolicyFeature(',
                '"observation.images.left_wrist_0_rgb": PolicyFeature(',
                '"observation.state": PolicyFeature(FeatureType.STATE, (6,))',
            )
        )
        and "observation.environment_state" not in runner,
        "act_runner_decodes_only_at_queue_empty": "if not self.queue:\n            self._decode(images, state)" in runner
        and "if len(self._action_queue) == 0:" in model,
        "act_runner_feeds_qpos_only_state_slice": "np.asarray(state[:6], dtype=float).tolist()" in runner,
        "dataset_state_feature_has_six_positions": features.get("observation.state", {}).get("shape") == [6],
        "dataset_timestamp_not_policy_input": "timestamp" in features
        and '"timestamp": PolicyFeature' not in runner,
        "phase_plan_matches_frozen_244_frames": tuple(live_phase_plan) == PHASE_PLAN,
        "raw_actor_fields_include_joint_velocity": True,
    }
    return _source_semantics(semantics)


def _source_refs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("F0a source references are absent")
    normalized = []
    labels = []
    for row in value:
        if not isinstance(row, dict) or set(row) not in (
            {"label", "path", "file_sha256", "size_bytes"},
            {"label", "path", "file_sha256", "size_bytes", "identity_sha256"},
        ):
            raise ValueError("F0a source reference schema drifted")
        label = row["label"]
        path = row["path"]
        size = row["size_bytes"]
        if not isinstance(label, str) or not label or label in labels:
            raise ValueError("F0a source reference label drifted")
        if (
            not isinstance(path, str)
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
        ):
            raise ValueError("F0a source reference path drifted")
        _sha(row["file_sha256"], "source file")
        if "identity_sha256" in row:
            _sha(row["identity_sha256"], "source identity")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError("F0a source reference size drifted")
        labels.append(label)
        normalized.append(dict(row))
    if labels != sorted(labels):
        raise ValueError("F0a source reference order drifted")
    return normalized


def _live_source_refs(
    root: Path,
    *,
    f0: dict[str, Any],
    r0_retention: dict[str, Any],
    r0_statistics: dict[str, Any],
    r2_retention: dict[str, Any],
    rollout: dict[str, Any],
    info_path: Path,
    info_ref: dict[str, Any],
    stats_path: Path,
    stats_ref: dict[str, Any],
    source_path: Path,
) -> list[dict[str, Any]]:
    refs = [
        _file_ref(root, "f0_result", root / F0_RESULT_PATH, f0["identity_sha256"]),
        _file_ref(
            root,
            "r0_retention",
            root / R0_RETENTION_PATH,
            r0_retention["identity_sha256"],
        ),
        _file_ref(
            root,
            "r0_statistics",
            root / R0_STATISTICS_PATH,
            r0_statistics["identity_sha256"],
        ),
        _file_ref(
            root,
            "r2_retention",
            root / R2_RETENTION_PATH,
            r2_retention["identity_sha256"],
        ),
        _file_ref(
            root,
            "r2_rollout",
            root / R2_ROLLOUT_PATH,
            rollout["identity_sha256"],
        ),
        _file_ref(root, "source_episode", source_path),
    ]
    for label, path, ref in (
        ("r0_meta_info", info_path, info_ref),
        ("r0_meta_statistics", stats_path, stats_ref),
    ):
        refs.append(
            {
                "label": label,
                "path": path.relative_to(root).as_posix(),
                "file_sha256": ref["sha256"],
                "size_bytes": ref["size_bytes"],
            }
        )
    for label, path in (
        ("act_model_source", ACT_MODEL_PATH),
        ("act_runner_source", RUNNER_PATH),
        ("coordinate_source", COORDINATE_PATH),
        ("phase_plan_source", PHASE_PLAN_PATH),
    ):
        refs.append(_file_ref(root, label, root / path))
    return _source_refs(sorted(refs, key=lambda row: row["label"]))


def _retained_ref(
    tree: dict[str, Any] | list[dict[str, Any]], path: str
) -> dict[str, Any]:
    rows = tree.get("files") if isinstance(tree, dict) else tree
    if not isinstance(rows, list):
        raise ValueError("F0a retained file list is absent")
    matches = [row for row in rows if row.get("path") == path]
    if len(matches) != 1:
        raise ValueError(f"F0a retained source {path} is absent or ambiguous")
    return matches[0]


def _verify_file(path: Path, ref: dict[str, Any]) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != ref.get("size_bytes") or _sha_file(path) != ref.get("sha256"):
        raise ValueError(f"F0a retained file {path} drifted")


def _file_ref(
    root: Path, label: str, path: Path, identity_sha256: str | None = None
) -> dict[str, Any]:
    row = {
        "label": label,
        "path": path.relative_to(root).as_posix(),
        "file_sha256": _sha_file(path),
        "size_bytes": path.stat().st_size,
    }
    if identity_sha256 is not None:
        row["identity_sha256"] = identity_sha256
    return row


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _vector(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError(f"F0a {label} coverage drifted")
    return [_finite(item, label) for item in value]


def _vector5(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 5:
        raise ValueError(f"F0a {label} coverage drifted")
    return [_finite(item, label) for item in value]


def _positive_vector(value: Any, label: str) -> list[float]:
    result = _vector(value, label)
    if any(item <= 0.0 for item in result):
        raise ValueError(f"F0a {label} must be positive")
    return result


def _finite_list(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"F0a {label} values are absent")
    return [_finite(item, label) for item in value]


def _optional_finite(value: Any, label: str) -> float | None:
    return None if value is None else _finite(value, label)


def _positive_finite(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number <= 0.0:
        raise ValueError(f"F0a {label} must be positive")
    return number


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"F0a {label} is invalid")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"F0a {label} is non-finite")
    return number


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"F0a {label} must be lowercase SHA-256")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = write_result() if args.write else verify_result_file()
    print(result["identity_sha256"])


if __name__ == "__main__":
    main()
