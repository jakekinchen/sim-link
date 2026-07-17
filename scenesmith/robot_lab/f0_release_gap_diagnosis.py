"""Deterministic, model-free diagnosis of the T20.43c-R2 release gap."""

from __future__ import annotations

import argparse
import bisect
import hashlib
import math
import statistics

from collections import Counter
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.so101_coordinates import GRIPPER_RANGE_RAD


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = Path("configurations/robot_lab/f0_release_gap_diagnosis.json")
SCHEMA_VERSION = "scenesmith.f0_release_gap_diagnosis.v1"
SOURCE_BOUNDARY_COMMIT = "545bba080c1af4033423e595f66b6c15fdf11a1f"
BRIEF_ACTIVATION_COMMIT = "12129ba2b0e4628d3ba5c4da840567448538f21d"

MIXTURE_PATH = Path(
    "configurations/robot_lab/t20_42_r0_dataset_mixture_manifest.json"
)
STATISTICS_PATH = Path("configurations/robot_lab/t20_42_r0_dataset_statistics.json")
R0_RETENTION_PATH = Path("configurations/robot_lab/t20_42_r0_retention_receipt.json")
R2_RETENTION_PATH = Path(
    "configurations/robot_lab/t20_43c_r2_act_retention_receipt.json"
)
R2_FINAL_PATH = Path("configurations/robot_lab/t20_43c_r2_act_final_receipt.json")
R2_ROLLOUT_PATH = Path(
    "outputs/robot_lab/t20_43c_r2_act_replacement_run_001/rollouts/"
    "step_10000_chunk_50.json"
)

RUNNER_PATH = Path("scenesmith/robot_lab/t20_43b_r1_act_runner.py")
CONTRACT_PATH = Path("scenesmith/robot_lab/t20_43b_r1_act_contracts.py")
COORDINATE_PATH = Path("scenesmith/robot_lab/so101_coordinates.py")
PHASE_PLAN_PATH = Path("scenesmith/robot_lab/act_grasp_closed_loop.py")
SAMPLER_PATH = Path("external/lerobot/src/lerobot/datasets/sampler.py")
DATASET_READER_PATH = Path(
    "external/lerobot/src/lerobot/datasets/dataset_reader.py"
)
ACT_MODEL_PATH = Path("external/lerobot/src/lerobot/policies/act/modeling_act.py")

EXPECTED_MIXTURE_IDENTITY = (
    "37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df"
)
EXPECTED_STATISTICS_IDENTITY = (
    "02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae"
)
EXPECTED_R0_RETENTION_IDENTITY = (
    "19d19fbaa315511fa0e7df736d3895089827da8f0b8a2aecd15a2a75885bd495"
)
EXPECTED_R2_RETENTION_IDENTITY = (
    "e565e17a5d4f8a52c4d894d3d61f03cf4b38beaf1df0bec3b83ade7f05afc023"
)
EXPECTED_R2_FINAL_IDENTITY = (
    "be11a258b6662baa10341acac13fe09055cd4ded7c2eaba4236d466977dfac5e"
)
EXPECTED_R2_RUN_IDENTITY = (
    "82a0608386375f029a56be8ca9f972bc0e83939d30ad286164db828aa22dc851"
)

TRAINING_SEED = 20260801
BATCH_SIZE = 8
OPTIMIZER_UPDATES = 10_000
CHUNK_SIZE = 50
ROLLOUT_FRAMES = 244
FINAL_CHUNK_START = 200
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
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
LATE_PHASES = ("release", "release_settle", "retreat")


def reconstruct_sampler_batches(
    episode_lengths: list[int],
    *,
    seed: int = TRAINING_SEED,
    batch_size: int = BATCH_SIZE,
    update_count: int = OPTIMIZER_UPDATES,
) -> tuple[list[list[int]], int]:
    """Reproduce EpisodeAwareSampler plus DataLoader batching exactly."""

    lengths = _episode_lengths(episode_lengths)
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("F0 sampler seed is invalid")
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("F0 batch size is invalid")
    if isinstance(update_count, bool) or not isinstance(update_count, int) or update_count <= 0:
        raise ValueError("F0 update count is invalid")

    import numpy as np
    import torch

    frame_count = sum(lengths)
    batches: list[list[int]] = []
    epoch = 0
    while len(batches) < update_count:
        epoch_seed = int(
            np.random.SeedSequence([seed, epoch]).generate_state(
                1, dtype=np.uint64
            )[0]
        )
        order = torch.randperm(
            frame_count, generator=torch.Generator().manual_seed(epoch_seed)
        ).tolist()
        for offset in range(0, frame_count, batch_size):
            batches.append(order[offset : offset + batch_size])
            if len(batches) == update_count:
                break
        epoch += 1
    return batches, epoch


def analyze_sampler(
    episode_lengths: list[int], batches: list[list[int]]
) -> dict[str, Any]:
    lengths = _episode_lengths(episode_lengths)
    if not isinstance(batches, list) or not batches:
        raise ValueError("F0 sampler batches are absent")
    starts = []
    ends = []
    cursor = 0
    for length in lengths:
        starts.append(cursor)
        cursor += length
        ends.append(cursor)

    phase_start_count = Counter({name: 0 for name in PHASE_NAMES})
    phase_loss_mass = Counter({name: 0.0 for name in PHASE_NAMES})
    target_exposure = [0] * ROLLOUT_FRAMES
    exact_frame_200_exposures = 0
    valid_target_count = 0
    batch_size_histogram: Counter[int] = Counter()
    sampled_start_count = 0

    for batch in batches:
        if not isinstance(batch, list) or not batch:
            raise ValueError("F0 sampler batch is empty")
        batch_size_histogram[len(batch)] += 1
        batch_phase_targets = Counter({name: 0 for name in PHASE_NAMES})
        batch_valid_targets = 0
        for absolute_index in batch:
            if (
                isinstance(absolute_index, bool)
                or not isinstance(absolute_index, int)
                or not 0 <= absolute_index < cursor
            ):
                raise ValueError("F0 sampler index is invalid")
            episode_index = bisect.bisect_right(ends, absolute_index)
            local_index = absolute_index - starts[episode_index]
            episode_length = lengths[episode_index]
            phase_start_count[phase_for_frame(local_index)] += 1
            sampled_start_count += 1
            if local_index == FINAL_CHUNK_START:
                exact_frame_200_exposures += 1
            for target_index in range(
                local_index, min(local_index + CHUNK_SIZE, episode_length)
            ):
                target_exposure[target_index] += 1
                batch_phase_targets[phase_for_frame(target_index)] += 1
                batch_valid_targets += 1
                valid_target_count += 1
        if batch_valid_targets <= 0:
            raise ValueError("F0 sampler batch has no valid targets")
        for phase in PHASE_NAMES:
            phase_loss_mass[phase] += (
                batch_phase_targets[phase] / batch_valid_targets
            )

    update_count = len(batches)
    normalized_loss_mass = {
        phase: phase_loss_mass[phase] / update_count for phase in PHASE_NAMES
    }
    median_interior_exposure = float(statistics.median(target_exposure[50:200]))
    minimum_late_exposure = min(target_exposure[200:244])
    minimum_late_to_interior_ratio = minimum_late_exposure / median_interior_exposure
    late_loss_mass = sum(normalized_loss_mass[phase] for phase in LATE_PHASES)
    late_valid_frame_count = sum(
        max(0, min(length, ROLLOUT_FRAMES) - FINAL_CHUNK_START)
        for length in lengths
    )
    late_valid_frame_geometric_share = late_valid_frame_count / sum(lengths)
    late_loss_mass_to_geometric_share_ratio = (
        late_loss_mass / late_valid_frame_geometric_share
    )
    eligible_frame_200_episode_count = sum(
        length > FINAL_CHUNK_START for length in lengths
    )
    observed_frame_200_start_share = exact_frame_200_exposures / sampled_start_count
    expected_uniform_frame_200_start_share = (
        eligible_frame_200_episode_count / sum(lengths)
    )
    frame_200_exposure_to_uniform_ratio = (
        observed_frame_200_start_share / expected_uniform_frame_200_start_share
    )
    valid_lengths = Counter(
        min(CHUNK_SIZE, length - FINAL_CHUNK_START)
        for length in lengths
        if length > FINAL_CHUNK_START
    )
    tail_coverage_defect = (
        minimum_late_to_interior_ratio < 0.9
        or late_loss_mass_to_geometric_share_ratio < 0.9
    )
    return {
        "episode_count": len(lengths),
        "episode_length_histogram": {
            str(key): value for key, value in sorted(Counter(lengths).items())
        },
        "training_frame_count": sum(lengths),
        "optimizer_update_count": update_count,
        "sampled_start_count": sampled_start_count,
        "batch_size_histogram": {
            str(key): value for key, value in sorted(batch_size_histogram.items())
        },
        "phase_start_count": dict(phase_start_count),
        "phase_start_share": {
            phase: phase_start_count[phase] / sampled_start_count
            for phase in PHASE_NAMES
        },
        "phase_valid_loss_mass_share": normalized_loss_mass,
        "valid_target_count": valid_target_count,
        "target_exposure_by_frame": target_exposure,
        "median_target_exposure_frames_50_199": median_interior_exposure,
        "minimum_target_exposure_frames_200_243": minimum_late_exposure,
        "minimum_late_to_interior_target_exposure_ratio": (
            minimum_late_to_interior_ratio
        ),
        "late_phase_valid_loss_mass_share": late_loss_mass,
        "late_phase_valid_frame_geometric_share": late_valid_frame_geometric_share,
        "late_loss_mass_to_geometric_share_ratio": (
            late_loss_mass_to_geometric_share_ratio
        ),
        "eligible_frame_200_episode_count": eligible_frame_200_episode_count,
        "exact_frame_200_start_exposure_count": exact_frame_200_exposures,
        "observed_frame_200_start_share": observed_frame_200_start_share,
        "expected_uniform_frame_200_start_share": (
            expected_uniform_frame_200_start_share
        ),
        "frame_200_exposure_to_uniform_ratio": frame_200_exposure_to_uniform_ratio,
        "frame_200_valid_length_histogram": {
            str(key): value for key, value in sorted(valid_lengths.items())
        },
        "tail_padding_active": True,
        "tail_coverage_defect": tail_coverage_defect,
    }


def analyze_unpadded_horizon_50(
    start_histogram: dict[str, int]
) -> dict[str, Any]:
    if not isinstance(start_histogram, dict) or not start_histogram:
        raise ValueError("F0 unpadded horizon-50 histogram is absent")
    normalized: dict[str, int] = {}
    for raw_start, raw_count in start_histogram.items():
        try:
            start = int(raw_start)
        except (TypeError, ValueError) as error:
            raise ValueError("F0 unpadded start is invalid") from error
        if str(start) != raw_start or start < 0:
            raise ValueError("F0 unpadded start is invalid")
        if isinstance(raw_count, bool) or not isinstance(raw_count, int) or raw_count <= 0:
            raise ValueError("F0 unpadded start count is invalid")
        normalized[raw_start] = raw_count
    starts = [int(value) for value in normalized]
    return {
        "start_frame_histogram": {
            key: normalized[key]
            for key in sorted(normalized, key=lambda value: int(value))
        },
        "window_count": sum(normalized.values()),
        "start_frame_minimum": min(starts),
        "start_frame_maximum": max(starts),
        "end_frame_maximum": max(starts) + CHUNK_SIZE - 1,
        "window_count_starting_at_or_after_release": sum(
            count
            for start, count in ((int(key), value) for key, value in normalized.items())
            if start >= FINAL_CHUNK_START
        ),
        "window_count_covering_release_or_later": sum(
            count
            for start, count in ((int(key), value) for key, value in normalized.items())
            if start + CHUNK_SIZE - 1 >= FINAL_CHUNK_START
        ),
        "consumed_by_r2_act_runner": False,
    }


def analyze_normalization(
    action_statistics: dict[str, list[float]],
    late_rollout_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    stats = _action_statistics(action_statistics)
    rows = _late_rows(late_rollout_evidence)
    low, high = GRIPPER_RANGE_RAD
    source_percent = [
        100.0 * (row["source_gripper_rad"] - low) / (high - low) for row in rows
    ]
    required_open = max(source_percent)
    gripper_minimum = stats["min"][5]
    gripper_maximum = stats["max"][5]
    gripper_mean = stats["mean"][5]
    gripper_std = stats["std"][5]
    z_score = (required_open - gripper_mean) / gripper_std
    tolerance = 1e-4
    inside = (
        required_open >= gripper_minimum - tolerance
        and required_open <= gripper_maximum + tolerance
    )
    defect = not inside or abs(z_score) > 3.0
    return {
        "normalization": "MEAN_STD",
        "required_open_gripper_lerobot_percent": required_open,
        "r0_gripper_minimum_percent": gripper_minimum,
        "r0_gripper_maximum_percent": gripper_maximum,
        "r0_gripper_mean_percent": gripper_mean,
        "r0_gripper_standard_deviation_percent": gripper_std,
        "required_open_z_score": z_score,
        "float_envelope_tolerance_percent": tolerance,
        "required_open_inside_r0_envelope": inside,
        "required_open_within_three_standard_deviations": abs(z_score) <= 3.0,
        "normalization_defect": defect,
    }


def derive_physical_l1_weights(
    action_standard_deviation: list[float],
) -> dict[str, Any]:
    if not isinstance(action_standard_deviation, list) or len(action_standard_deviation) != 6:
        raise ValueError("F0 action standard deviation coverage drifted")
    std = [_positive_finite(value, "action standard deviation") for value in action_standard_deviation]
    gripper_span = GRIPPER_RANGE_RAD[1] - GRIPPER_RANGE_RAD[0]
    jacobian = [value * math.pi / 180.0 for value in std[:5]] + [
        std[5] * gripper_span / 100.0
    ]
    mean = sum(jacobian) / len(jacobian)
    coefficients = [value / mean for value in jacobian]
    return {
        "objective": "ACT normalized-space L1",
        "formula": "absolute_normalized_unit_to_physical_radian_jacobian_then_active_mean_one",
        "joint_names": list(JOINT_NAMES),
        "action_standard_deviation_lerobot_units": std,
        "normalized_unit_to_physical_radian_jacobian": jacobian,
        "active_joint_coefficient": coefficients,
        "active_joint_coefficient_mean": sum(coefficients) / len(coefficients),
        "gripper_coefficient": coefficients[5],
        "gripper_weighting_mechanism_eligible": coefficients[5] >= 1.5,
    }


def analyze_late_rollout(
    late_rollout_evidence: list[dict[str, Any]], failed_gate_names: list[str]
) -> dict[str, Any]:
    rows = _late_rows(late_rollout_evidence)
    if failed_gate_names != ["release_final_contact_clear"]:
        raise ValueError("F0 retained best rollout failure boundary drifted")
    release_rows = [row for row in rows if row["phase"] == "release"]
    source_pattern = [row["source_gripper_rad"] for row in release_rows]
    candidate = [row["candidate_gripper_rad"] for row in rows]
    shift_scores = []
    for shift in range(len(candidate) - len(source_pattern) + 1):
        score = sum(
            abs(left - right)
            for left, right in zip(
                candidate[shift : shift + len(source_pattern)],
                source_pattern,
                strict=True,
            )
        ) / len(source_pattern)
        shift_scores.append((score, shift))
    best_score, best_shift = min(shift_scores)
    zero_shift_score = shift_scores[0][0]
    improvement_ratio = (
        None if best_score == 0.0 else zero_shift_score / best_score
    )
    by_phase = {}
    for phase in LATE_PHASES:
        phase_rows = [row for row in rows if row["phase"] == phase]
        errors = [
            row["candidate_gripper_rad"] - row["source_gripper_rad"]
            for row in phase_rows
        ]
        by_phase[phase] = {
            "frame_count": len(phase_rows),
            "mean_signed_error_rad": sum(errors) / len(errors),
            "mean_absolute_error_rad": sum(abs(value) for value in errors)
            / len(errors),
            "maximum_under_open_error_rad": max(-value for value in errors),
            "candidate_strict_contact_frame_count": sum(
                row["candidate_strict_contact"] for row in phase_rows
            ),
        }
    contact_relevant = (
        by_phase["release"]["mean_signed_error_rad"] < -0.1
        and by_phase["release"]["candidate_strict_contact_frame_count"]
        == by_phase["release"]["frame_count"]
        and by_phase["release_settle"]["candidate_strict_contact_frame_count"]
        == by_phase["release_settle"]["frame_count"]
    )
    delay_counterexample = (
        best_shift == 20
        and best_score <= 0.1
        and (
            (improvement_ratio is None and zero_shift_score > 0.0)
            or (improvement_ratio is not None and improvement_ratio >= 5.0)
        )
    )
    return {
        "failed_gate_names": list(failed_gate_names),
        "late_phase_gripper_error": by_phase,
        "source_release_pattern_frame_count": len(source_pattern),
        "zero_shift_release_pattern_mae_rad": zero_shift_score,
        "best_release_pattern_shift_frames": best_shift,
        "best_shift_release_pattern_mae_rad": best_score,
        "zero_to_best_shift_mae_ratio": improvement_ratio,
        "same_direction_contact_relevant_gripper_error": contact_relevant,
        "twenty_frame_release_sequence_delay_counterexample": delay_counterexample,
    }


def build_release_gap_diagnosis(
    *,
    source_refs: list[dict[str, Any]],
    source_semantics: dict[str, bool],
    episode_lengths: list[int],
    unpadded_horizon_50_start_histogram: dict[str, int],
    action_statistics: dict[str, list[float]],
    late_rollout_evidence: list[dict[str, Any]],
    failed_gate_names: list[str],
) -> dict[str, Any]:
    refs = _source_refs(source_refs)
    semantics = _source_semantics(source_semantics)
    lengths = _episode_lengths(episode_lengths)
    rows = _late_rows(late_rollout_evidence)
    stats = _action_statistics(action_statistics)
    batches, epochs_touched = reconstruct_sampler_batches(lengths)
    sampler = analyze_sampler(lengths, batches)
    unpadded = analyze_unpadded_horizon_50(unpadded_horizon_50_start_histogram)
    normalization = analyze_normalization(stats, rows)
    weighting = derive_physical_l1_weights(stats["std"])
    rollout = analyze_late_rollout(rows, failed_gate_names)
    import numpy as np
    import torch

    tail_defect = sampler["tail_coverage_defect"]
    normalization_defect = normalization["normalization_defect"]
    release_mixture_defect = (
        sampler["late_loss_mass_to_geometric_share_ratio"] < 0.9
    )
    gripper_supported = (
        weighting["gripper_weighting_mechanism_eligible"]
        and rollout["same_direction_contact_relevant_gripper_error"]
    )
    if tail_defect or normalization_defect:
        route = "propose_one_fresh_10000_update_release_fixed_data_rung"
        corrective_training_selected = True
    elif release_mixture_defect and gripper_supported:
        route = "propose_one_short_release_oversampled_physical_l1_weighted_continuation"
        corrective_training_selected = True
    elif rollout["twenty_frame_release_sequence_delay_counterexample"]:
        route = "open_fresh_model_free_chunk_timing_and_phase_observability_audit"
        corrective_training_selected = False
    else:
        route = "close_f0_without_corrective_training"
        corrective_training_selected = False

    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "F0",
            "scope": "model_free_r0_act_release_gap_diagnosis",
            "source_boundary_commit": SOURCE_BOUNDARY_COMMIT,
            "brief_activation_commit": BRIEF_ACTIVATION_COMMIT,
            "source_refs": refs,
            "source_semantics": semantics,
            "input_evidence": {
                "episode_lengths": lengths,
                "sampler_recipe": {
                    "seed": TRAINING_SEED,
                    "batch_size": BATCH_SIZE,
                    "optimizer_update_count": OPTIMIZER_UPDATES,
                    "chunk_size": CHUNK_SIZE,
                    "epochs_touched": epochs_touched,
                    "runtime_versions": {
                        "numpy": np.__version__,
                        "torch": torch.__version__,
                    },
                },
                "unpadded_horizon_50_start_histogram": (
                    unpadded["start_frame_histogram"]
                ),
                "action_statistics": stats,
                "late_rollout_evidence": rows,
                "failed_gate_names": list(failed_gate_names),
            },
            "sampler_analysis": sampler,
            "standalone_unpadded_window_analysis": unpadded,
            "normalization_analysis": normalization,
            "physical_l1_weighting_analysis": weighting,
            "retained_rollout_analysis": rollout,
            "findings": {
                "tail_coverage_defect": tail_defect,
                "normalization_defect": normalization_defect,
                "release_mixture_underweight_defect": release_mixture_defect,
                "gripper_physical_l1_underweight_supported": gripper_supported,
                "twenty_frame_release_sequence_delay_counterexample": rollout[
                    "twenty_frame_release_sequence_delay_counterexample"
                ],
            },
            "selected_route": route,
            "corrective_training_selected": corrective_training_selected,
            "single_corrective_rung_consumed": False,
            "training_lock": "closed",
            "retained_prior_model_inference_evidence_read": True,
            "retained_prior_rollout_evidence_read": True,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "closed_loop_rollout_executed": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "hardware_accessed": False,
            "physical_actuation": False,
            "gate_c_executed": False,
            "simulation_policy_accepted": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
            "freeze_tag_authorized": False,
        }
    )


def verify_release_gap_diagnosis(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="F0 release-gap diagnosis")
    inputs = payload.get("input_evidence")
    if not isinstance(inputs, dict):
        raise ValueError("F0 input evidence is absent")
    expected = build_release_gap_diagnosis(
        source_refs=payload.get("source_refs"),
        source_semantics=payload.get("source_semantics"),
        episode_lengths=inputs.get("episode_lengths"),
        unpadded_horizon_50_start_histogram=inputs.get(
            "unpadded_horizon_50_start_histogram"
        ),
        action_statistics=inputs.get("action_statistics"),
        late_rollout_evidence=inputs.get("late_rollout_evidence"),
        failed_gate_names=inputs.get("failed_gate_names"),
    )
    if payload != expected:
        raise ValueError("F0 release-gap diagnosis drifted")


def build_live_release_gap_diagnosis(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root)
    mixture = load_strict_json(root / MIXTURE_PATH)
    statistics = load_strict_json(root / STATISTICS_PATH)
    r0_retention = load_strict_json(root / R0_RETENTION_PATH)
    r2_retention = load_strict_json(root / R2_RETENTION_PATH)
    r2_final = load_strict_json(root / R2_FINAL_PATH)
    for label, payload, expected_identity in (
        ("R0 mixture", mixture, EXPECTED_MIXTURE_IDENTITY),
        ("R0 statistics", statistics, EXPECTED_STATISTICS_IDENTITY),
        ("R0 retention", r0_retention, EXPECTED_R0_RETENTION_IDENTITY),
        ("R2 retention", r2_retention, EXPECTED_R2_RETENTION_IDENTITY),
        ("R2 final", r2_final, EXPECTED_R2_FINAL_IDENTITY),
    ):
        verify_signed_payload(payload, label=label)
        if payload.get("identity_sha256") != expected_identity:
            raise ValueError(f"F0 {label} identity drifted")
    if r2_retention.get("run_identity_sha256") != EXPECTED_R2_RUN_IDENTITY:
        raise ValueError("F0 R2 run identity drifted")
    if r2_final.get("retention_receipt_identity_sha256") != EXPECTED_R2_RETENTION_IDENTITY:
        raise ValueError("F0 R2 final/retention binding drifted")

    r0_dataset = r0_retention["local_output_trees"]["lerobot_dataset"]
    r0_windows = r0_retention["local_output_trees"]["windows"]
    episode_ref = _retained_ref(
        r0_dataset, "meta/episodes/chunk-000/file-000.parquet"
    )
    meta_stats_ref = _retained_ref(r0_dataset, "meta/stats.json")
    window_ref = _retained_ref(r0_windows, "window_index.parquet")
    rollout_ref = _retained_ref(
        r2_retention["local_output_trees"]["rollouts"],
        "step_10000_chunk_50.json",
    )
    episode_path = root / r0_dataset["root"] / episode_ref["path"]
    meta_stats_path = root / r0_dataset["root"] / meta_stats_ref["path"]
    window_path = root / r0_windows["root"] / window_ref["path"]
    rollout_path = root / R2_ROLLOUT_PATH
    for path, ref in (
        (episode_path, episode_ref),
        (meta_stats_path, meta_stats_ref),
        (window_path, window_ref),
        (rollout_path, rollout_ref),
    ):
        _verify_file(path, ref)

    import pyarrow.parquet as pq

    episode_rows = pq.read_table(
        episode_path, columns=["episode_index", "length"]
    ).to_pylist()
    if [row["episode_index"] for row in episode_rows] != list(range(129)):
        raise ValueError("F0 R0 episode order drifted")
    episode_lengths = [int(row["length"]) for row in episode_rows]
    window_rows = pq.read_table(
        window_path, columns=["horizon", "start_frame_index", "rollout_id"]
    ).to_pylist()
    horizon_50 = [row for row in window_rows if row["horizon"] == CHUNK_SIZE]
    start_histogram = Counter(int(row["start_frame_index"]) for row in horizon_50)
    if len({row["rollout_id"] for row in horizon_50}) != 128:
        raise ValueError("F0 unpadded horizon-50 rollout coverage drifted")

    meta_stats = load_strict_json(meta_stats_path)
    action_stats = meta_stats.get("action")
    tracked_action = statistics.get("features", {}).get("action")
    if (
        not isinstance(action_stats, dict)
        or not isinstance(tracked_action, dict)
        or action_stats.get("mean") != tracked_action.get("mean")
        or action_stats.get("std") != tracked_action.get("std")
        or action_stats.get("count") != [int(tracked_action.get("count", [0])[0])]
    ):
        raise ValueError("F0 R0 tracked/meta action statistics drifted")

    rollout = load_strict_json(rollout_path)
    verify_signed_payload(rollout, label="F0 retained R2 rollout")
    comparisons = rollout.get("comparisons")
    if not isinstance(comparisons, list) or len(comparisons) != ROLLOUT_FRAMES:
        raise ValueError("F0 retained R2 comparisons drifted")
    late_rows = [
        {
            "frame_index": row["frame_index"],
            "phase": row["phase"],
            "source_gripper_rad": row["source_requested_action_rad"][5],
            "candidate_gripper_rad": row["candidate_requested_action_rad"][5],
            "candidate_strict_contact": row["candidate_strict_contact"],
        }
        for row in comparisons[FINAL_CHUNK_START:ROLLOUT_FRAMES]
    ]
    failed_gate_names = [
        row["gate"] for row in rollout["closed_loop"]["failed_gate_margins"]
    ]
    source_semantics = _live_source_semantics(root)
    source_refs = _live_source_refs(
        root,
        mixture=mixture,
        statistics=statistics,
        r0_retention=r0_retention,
        r2_retention=r2_retention,
        r2_final=r2_final,
        episode_path=episode_path,
        episode_ref=episode_ref,
        meta_stats_path=meta_stats_path,
        meta_stats_ref=meta_stats_ref,
        window_path=window_path,
        window_ref=window_ref,
        rollout_path=rollout_path,
        rollout_ref=rollout_ref,
        rollout=rollout,
    )
    result = build_release_gap_diagnosis(
        source_refs=source_refs,
        source_semantics=source_semantics,
        episode_lengths=episode_lengths,
        unpadded_horizon_50_start_histogram={
            str(key): value for key, value in sorted(start_histogram.items())
        },
        action_statistics={
            key: action_stats[key] for key in ("min", "max", "mean", "std")
        },
        late_rollout_evidence=late_rows,
        failed_gate_names=failed_gate_names,
    )
    verify_release_gap_diagnosis(result)
    return result


def write_result(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = build_live_release_gap_diagnosis(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / RESULT_PATH, result)
    return result


def verify_result_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    archived = load_strict_json(root / RESULT_PATH)
    verify_release_gap_diagnosis(archived)
    expected = build_live_release_gap_diagnosis(repo_root=root)
    if archived != expected:
        raise ValueError("F0 archived release-gap diagnosis drifted from live sources")
    return archived


def phase_for_frame(frame_index: int) -> str:
    if (
        isinstance(frame_index, bool)
        or not isinstance(frame_index, int)
        or not 0 <= frame_index < ROLLOUT_FRAMES
    ):
        raise ValueError("F0 frame index is outside the phase plan")
    cursor = 0
    for phase, count in PHASE_PLAN:
        cursor += count
        if frame_index < cursor:
            return phase
    raise AssertionError("unreachable")


def _episode_lengths(value: Any) -> list[int]:
    if not isinstance(value, list) or not value:
        raise ValueError("F0 episode lengths are absent")
    lengths = []
    for item in value:
        if (
            isinstance(item, bool)
            or not isinstance(item, int)
            or not 0 < item <= ROLLOUT_FRAMES
        ):
            raise ValueError("F0 episode length is invalid")
        lengths.append(item)
    return lengths


def _action_statistics(value: Any) -> dict[str, list[float]]:
    if not isinstance(value, dict) or set(value) != {"min", "max", "mean", "std"}:
        raise ValueError("F0 action statistics schema drifted")
    result = {}
    for field in ("min", "max", "mean", "std"):
        row = value[field]
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError(f"F0 action {field} coverage drifted")
        result[field] = [_finite(item, f"action {field}") for item in row]
    if any(item <= 0 for item in result["std"]):
        raise ValueError("F0 action standard deviation must be positive")
    if any(low > high for low, high in zip(result["min"], result["max"], strict=True)):
        raise ValueError("F0 action min/max order drifted")
    return result


def _late_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != ROLLOUT_FRAMES - FINAL_CHUNK_START:
        raise ValueError("F0 late rollout evidence coverage drifted")
    rows = []
    for offset, source in enumerate(value):
        frame_index = FINAL_CHUNK_START + offset
        if not isinstance(source, dict) or set(source) != {
            "frame_index",
            "phase",
            "source_gripper_rad",
            "candidate_gripper_rad",
            "candidate_strict_contact",
        }:
            raise ValueError("F0 late rollout evidence schema drifted")
        if source["frame_index"] != frame_index or source["phase"] != phase_for_frame(frame_index):
            raise ValueError("F0 late rollout order or phase drifted")
        if not isinstance(source["candidate_strict_contact"], bool):
            raise ValueError("F0 late rollout contact flag drifted")
        rows.append(
            {
                "frame_index": frame_index,
                "phase": source["phase"],
                "source_gripper_rad": _finite(
                    source["source_gripper_rad"], "source gripper"
                ),
                "candidate_gripper_rad": _finite(
                    source["candidate_gripper_rad"], "candidate gripper"
                ),
                "candidate_strict_contact": source["candidate_strict_contact"],
            }
        )
    return rows


def _source_refs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("F0 source references are absent")
    normalized = []
    labels = []
    for row in value:
        if not isinstance(row, dict) or set(row) not in (
            {"label", "path", "file_sha256", "size_bytes"},
            {"label", "path", "file_sha256", "size_bytes", "identity_sha256"},
        ):
            raise ValueError("F0 source reference schema drifted")
        label = row["label"]
        path = row["path"]
        size = row["size_bytes"]
        if not isinstance(label, str) or not label or label in labels:
            raise ValueError("F0 source reference label drifted")
        if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError("F0 source reference path drifted")
        _sha(row["file_sha256"], "source file")
        if "identity_sha256" in row:
            _sha(row["identity_sha256"], "source identity")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError("F0 source reference size drifted")
        labels.append(label)
        normalized.append(dict(row))
    if labels != sorted(labels):
        raise ValueError("F0 source reference order drifted")
    return normalized


def _source_semantics(value: Any) -> dict[str, bool]:
    expected = {
        "act_loss_masks_action_is_pad",
        "dataset_reader_clamps_and_marks_tail_padding",
        "episode_aware_sampler_covers_all_episode_frames",
        "phase_plan_matches_frozen_244_frames",
        "r2_runner_uses_delta_timestamps_0_through_49",
        "r2_runner_uses_episode_aware_sampler",
        "r2_spec_has_no_sample_weighting",
        "standalone_unpadded_index_not_consumed_by_runner",
    }
    if not isinstance(value, dict) or set(value) != expected or any(item is not True for item in value.values()):
        raise ValueError("F0 source semantics drifted")
    return {key: True for key in sorted(expected)}


def _live_source_semantics(root: Path) -> dict[str, bool]:
    runner = (root / RUNNER_PATH).read_text()
    contract = (root / CONTRACT_PATH).read_text()
    reader = (root / DATASET_READER_PATH).read_text()
    sampler = (root / SAMPLER_PATH).read_text()
    act = (root / ACT_MODEL_PATH).read_text()
    from scenesmith.robot_lab.act_grasp_closed_loop import (
        PHASE_PLAN as live_phase_plan,
    )

    semantics = {
        "act_loss_masks_action_is_pad": 'valid_mask = ~batch["action_is_pad"].unsqueeze(-1)' in act,
        "dataset_reader_clamps_and_marks_tail_padding": "abs_idx + delta >= ep_end" in reader and 'f"{key}_is_pad"' in reader,
        "episode_aware_sampler_covers_all_episode_frames": "self._num_frames = int(self._cum_lengths[-1])" in sampler and "drop_n_last_frames: int = 0" in sampler,
        "phase_plan_matches_frozen_244_frames": tuple(live_phase_plan) == PHASE_PLAN,
        "r2_runner_uses_delta_timestamps_0_through_49": '"action": [index / metadata.fps for index in range(CHUNK_SIZE)]' in runner,
        "r2_runner_uses_episode_aware_sampler": "sampler = EpisodeAwareSampler(" in runner,
        "r2_spec_has_no_sample_weighting": '"sample_weighting": None' in contract,
        "standalone_unpadded_index_not_consumed_by_runner": "unpadded_window_index" not in runner,
    }
    return _source_semantics(semantics)


def _live_source_refs(
    root: Path,
    *,
    mixture: dict[str, Any],
    statistics: dict[str, Any],
    r0_retention: dict[str, Any],
    r2_retention: dict[str, Any],
    r2_final: dict[str, Any],
    episode_path: Path,
    episode_ref: dict[str, Any],
    meta_stats_path: Path,
    meta_stats_ref: dict[str, Any],
    window_path: Path,
    window_ref: dict[str, Any],
    rollout_path: Path,
    rollout_ref: dict[str, Any],
    rollout: dict[str, Any],
) -> list[dict[str, Any]]:
    refs = []
    for label, path, payload in (
        ("r0_mixture", MIXTURE_PATH, mixture),
        ("r0_retention", R0_RETENTION_PATH, r0_retention),
        ("r0_statistics", STATISTICS_PATH, statistics),
        ("r2_final", R2_FINAL_PATH, r2_final),
        ("r2_retention", R2_RETENTION_PATH, r2_retention),
    ):
        refs.append(_file_ref(root, label, root / path, payload["identity_sha256"]))
    for label, path, ref, identity in (
        ("r0_episode_metadata", episode_path, episode_ref, None),
        ("r0_meta_statistics", meta_stats_path, meta_stats_ref, None),
        ("r0_unpadded_window_index", window_path, window_ref, None),
        ("r2_best_chunk_50_rollout", rollout_path, rollout_ref, rollout["identity_sha256"]),
    ):
        row = {
            "label": label,
            "path": path.relative_to(root).as_posix(),
            "file_sha256": ref["sha256"],
            "size_bytes": ref["size_bytes"],
        }
        if identity is not None:
            row["identity_sha256"] = identity
        refs.append(row)
    for label, path in (
        ("act_model_source", ACT_MODEL_PATH),
        ("coordinate_source", COORDINATE_PATH),
        ("dataset_reader_source", DATASET_READER_PATH),
        ("phase_plan_source", PHASE_PLAN_PATH),
        ("r2_contract_source", CONTRACT_PATH),
        ("r2_runner_source", RUNNER_PATH),
        ("sampler_source", SAMPLER_PATH),
    ):
        refs.append(_file_ref(root, label, root / path))
    return _source_refs(sorted(refs, key=lambda row: row["label"]))


def _retained_ref(tree: dict[str, Any] | list[dict[str, Any]], path: str) -> dict[str, Any]:
    rows = tree.get("files") if isinstance(tree, dict) else tree
    if not isinstance(rows, list):
        raise ValueError("F0 retained file list is absent")
    matches = [row for row in rows if row.get("path") == path]
    if len(matches) != 1:
        raise ValueError(f"F0 retained source {path} is absent or ambiguous")
    return matches[0]


def _verify_file(path: Path, ref: dict[str, Any]) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != ref.get("size_bytes") or _sha_file(path) != ref.get("sha256"):
        raise ValueError(f"F0 retained file {path} drifted")


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


def _positive_finite(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number <= 0:
        raise ValueError(f"F0 {label} must be positive")
    return number


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"F0 {label} is invalid")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"F0 {label} is non-finite")
    return number


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"F0 {label} must be lowercase SHA-256")


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
