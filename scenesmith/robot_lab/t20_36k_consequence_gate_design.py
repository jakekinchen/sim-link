"""Model-free task-consequence calibration for a non-authorizing Gate B design."""

from __future__ import annotations

import hashlib
import math

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from scenesmith.robot_lab.act_grasp_closed_loop import (
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    ROLLOUT_FRAMES,
    phase_for_frame,
    run_policy_grasp_closed_loop,
)
from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_artifact_ref,
    verify_signed_payload,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.strict_grasp import strict_grasp_spec_v2


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "scenesmith.t20_36k_consequence_gate_design.v1"
RESULT_PATH = Path("configurations/robot_lab/t20_36k_consequence_gate_design.json")
ACT_RESULT_PATH = Path("configurations/robot_lab/t20_36e_exact_act_gate_b_control_result.json")
ACT_LOCALIZATION_PATH = Path("configurations/robot_lab/t20_36f_act_decode_localization_result.json")
SMOLVLA_RESULT_PATH = Path("configurations/robot_lab/t20_36j_exact_smolvla_gate_b_result.json")
SOURCE_MANIFEST_PATH = Path("configurations/robot_lab/t17_5b_episode_generation_manifest.json")
HISTORICAL_GATE_B_SPEC_PATH = Path(
    "configurations/robot_lab/t20_36d_exact_act_gate_b_control_spec.json"
)
SOURCE_SEED = 0
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)
PHASE_GROUPS = {
    "reach": ("approach", "pregrasp"),
    "grasp": ("close", "grasp_hold"),
    "lift": ("unassisted_lift", "unsupported_lift_hold"),
    "hold": ("recording_stable_hold",),
    "lower": ("lower",),
    "release": ("release", "release_settle"),
    "retreat": ("retreat",),
}
PERTURBATION_MAGNITUDES_RAD = (0.01, 0.025, 0.05, 0.1, 0.2, 0.4)
STRICT_UNIFORM_THRESHOLD_RAD = 0.05
RESOLUTION_FLOOR_RAD = PERTURBATION_MAGNITUDES_RAD[0]
_GATE_MEASUREMENTS = (
    "grasp_hold_strict_v2",
    "unassisted_lift_strict_v2",
    "unsupported_lift_hold_strict_v2",
    "recording_stable_hold_strict_v2",
    "lower_strict_v2",
    "unsupported_lift_support_free",
    "representative_span_m",
    "normal_alignment",
    "lift_displacement_m",
    "projected_action_frames",
    "active_assist_frames",
    "nonpad_contact_frames",
    "release_final_contact_clear",
    "retreat_final_contact_clear",
)


def phase_group_for_frame(frame_index: int) -> str:
    phase = phase_for_frame(frame_index)
    matches = [group for group, phases in PHASE_GROUPS.items() if phase in phases]
    if len(matches) != 1:
        raise ValueError("Strict-v2 phase must map to exactly one consequence group")
    return matches[0]


def build_perturbed_actions(
    nominal_actions: np.ndarray,
    *,
    joint_name: str,
    phase_group: str,
    signed_delta_rad: float,
) -> np.ndarray:
    actions = np.asarray(nominal_actions, dtype=np.float64)
    if actions.shape != (ROLLOUT_FRAMES, len(JOINT_NAMES)) or not np.isfinite(actions).all():
        raise ValueError("Nominal action trajectory must be finite and exactly 244x6")
    if joint_name not in JOINT_NAMES:
        raise ValueError("Perturbed joint is not canonical")
    if phase_group not in PHASE_GROUPS:
        raise ValueError("Perturbed phase group is not pre-registered")
    if isinstance(signed_delta_rad, bool) or not math.isfinite(float(signed_delta_rad)):
        raise ValueError("Perturbation delta must be finite")
    magnitude = abs(float(signed_delta_rad))
    if signed_delta_rad == 0 or magnitude not in PERTURBATION_MAGNITUDES_RAD:
        raise ValueError("Perturbation delta must belong to the pre-registered grid")
    perturbed = actions.copy()
    joint_index = JOINT_NAMES.index(joint_name)
    for frame_index in range(ROLLOUT_FRAMES):
        if phase_group_for_frame(frame_index) == phase_group:
            perturbed[frame_index, joint_index] += float(signed_delta_rad)
    return perturbed


def derive_threshold_rows(
    symmetric_pairs: Iterable[dict[str, Any]],
    *,
    require_complete_matrix: bool = True,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[float, bool]] = defaultdict(dict)
    for pair in symmetric_pairs:
        joint = pair.get("joint_name")
        group = pair.get("phase_group")
        magnitude = pair.get("magnitude_rad")
        passed = pair.get("both_signs_consequence_passed")
        if joint not in JOINT_NAMES or group not in PHASE_GROUPS:
            raise ValueError("Consequence pair has a non-canonical joint or phase group")
        if isinstance(magnitude, bool) or float(magnitude) not in PERTURBATION_MAGNITUDES_RAD:
            raise ValueError("Consequence pair is outside the pre-registered grid")
        if not isinstance(passed, bool):
            raise ValueError("Consequence pair pass state must be boolean")
        key = (str(joint), str(group))
        numeric = float(magnitude)
        if numeric in grouped[key]:
            raise ValueError("Consequence pair grid contains a duplicate")
        grouped[key][numeric] = passed

    expected_grid = set(PERTURBATION_MAGNITUDES_RAD)
    expected_keys = {(joint, group) for joint in JOINT_NAMES for group in PHASE_GROUPS}
    if require_complete_matrix and set(grouped) != expected_keys:
        raise ValueError("Threshold derivation requires the complete perturbation grid")
    rows: list[dict[str, Any]] = []
    for joint, group in sorted(
        grouped,
        key=lambda item: (JOINT_NAMES.index(item[0]), tuple(PHASE_GROUPS).index(item[1])),
    ):
        observed = grouped[(joint, group)]
        if set(observed) != expected_grid:
            raise ValueError("Threshold derivation requires the complete perturbation grid")
        ordered_passes = [observed[magnitude] for magnitude in PERTURBATION_MAGNITUDES_RAD]
        failure_index = next(
            (index for index, passed in enumerate(ordered_passes) if not passed),
            None,
        )
        first_failure = (
            None if failure_index is None else PERTURBATION_MAGNITUDES_RAD[failure_index]
        )
        safe_ceiling = (
            PERTURBATION_MAGNITUDES_RAD[-1]
            if failure_index is None
            else 0.0
            if failure_index == 0
            else PERTURBATION_MAGNITUDES_RAD[failure_index - 1]
        )
        non_monotonic = bool(
            failure_index is not None and any(ordered_passes[failure_index + 1 :])
        )
        sensitivity_class = _sensitivity_class(first_failure)
        amendment_ceiling = _amendment_ceiling(
            first_failure=first_failure,
            safe_ceiling=safe_ceiling,
        )
        rows.append(
            {
                "joint_name": joint,
                "phase_group": group,
                "first_observed_consequence_delta_rad": first_failure,
                "largest_evidenced_safe_symmetric_delta_rad": safe_ceiling,
                "non_monotonic_outcome_observed": non_monotonic,
                "sensitivity_class": sensitivity_class,
                "amendment_ceiling_rad": amendment_ceiling,
                "critical_joint_waiver_allowed": False,
            }
        )
    return rows


def _sensitivity_class(first_failure: float | None) -> str:
    if first_failure is None:
        return "insensitive_through_bounded_grid"
    if first_failure <= 0.01:
        return "critical_at_resolution_floor"
    if first_failure <= 0.05:
        return "task_critical"
    if first_failure <= 0.1:
        return "consequence_sensitive"
    if first_failure <= 0.2:
        return "bounded_tolerance"
    return "high_tolerance"


def _amendment_ceiling(*, first_failure: float | None, safe_ceiling: float) -> float:
    if first_failure is None:
        return PERTURBATION_MAGNITUDES_RAD[-1]
    if safe_ceiling <= 0.0:
        return RESOLUTION_FLOOR_RAD
    return min(safe_ceiling, first_failure)


def run_design(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = _load_sources(repo_root)
    source_entry = _source_episode_entry(sources["manifest"])
    nominal = _load_nominal_actions(sources["manifest"], repo_root)
    baseline_rollout = _run_action_sequence(nominal, label="nominal")
    baseline = _summarize_rollout(baseline_rollout)
    if not baseline["simulation_semantic_strict_success"]:
        raise ValueError("Canonical source action replay failed the current strict-v2 evaluator")

    pairs: list[dict[str, Any]] = []
    for joint_name in JOINT_NAMES:
        for phase_group in PHASE_GROUPS:
            for magnitude in PERTURBATION_MAGNITUDES_RAD:
                signs: dict[str, dict[str, Any]] = {}
                for sign_name, sign in (("negative", -1.0), ("positive", 1.0)):
                    actions = build_perturbed_actions(
                        nominal,
                        joint_name=joint_name,
                        phase_group=phase_group,
                        signed_delta_rad=sign * magnitude,
                    )
                    rollout = _run_action_sequence(
                        actions,
                        label=f"{joint_name}:{phase_group}:{sign_name}:{magnitude:g}",
                    )
                    signs[sign_name] = _summarize_rollout(
                        rollout,
                        baseline_measurements=baseline["gate_measurements"],
                    )
                pairs.append(
                    {
                        "joint_name": joint_name,
                        "phase_group": phase_group,
                        "magnitude_rad": magnitude,
                        "requested_pair_rad": [-magnitude, magnitude],
                        "negative": signs["negative"],
                        "positive": signs["positive"],
                        "both_signs_consequence_passed": all(
                            signs[name]["simulation_semantic_strict_success"]
                            for name in ("negative", "positive")
                        ),
                    }
                )

    threshold_rows = derive_threshold_rows(pairs)
    joint_safeguards = {
        joint: min(
            row["amendment_ceiling_rad"]
            for row in threshold_rows
            if row["joint_name"] == joint
        )
        for joint in JOINT_NAMES
    }
    strict_v2_spec = strict_grasp_spec_v2()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": "T20.36k",
        "decision": "consequence_calibration_complete_non_authorizing",
        "source_refs": sources["refs"],
        "candidate_evidence_context_only": {
            "used_for_threshold_derivation": False,
            "act_result_identity_sha256": sources["act_result"]["identity_sha256"],
            "act_localization_identity_sha256": sources["act_localization"]["identity_sha256"],
            "smolvla_result_identity_sha256": sources["smolvla_result"]["identity_sha256"],
            "act_final_to_baseline_supervised_objective_ratio": sources[
                "act_result"
            ]["final_to_baseline_supervised_objective_ratio"],
            "act_final_maximum_absolute_error_rad": sources["act_result"][
                "final_maximum_absolute_error_rad"
            ],
            "smolvla_final_to_baseline_supervised_objective_ratio": sources[
                "smolvla_result"
            ]["final_to_baseline_supervised_objective_ratio"],
            "smolvla_final_maximum_absolute_error_rad": sources["smolvla_result"][
                "final_maximum_absolute_error_rad"
            ],
        },
        "perturbation_spec": {
            "source": "pre_registered_historical_uniform_gate_multiples_not_candidate_errors",
            "joint_names": list(JOINT_NAMES),
            "phase_groups": {name: list(phases) for name, phases in PHASE_GROUPS.items()},
            "magnitudes_rad": list(PERTURBATION_MAGNITUDES_RAD),
            "signs": [-1, 1],
            "pair_count": len(pairs),
            "simulation_seed": SOURCE_SEED,
            "source_episode_file_sha256": source_entry["episode_file_sha256"],
            "source_raw_rollout_record_identity_sha256": source_entry[
                "raw_rollout_record_identity_sha256"
            ],
            "strict_v2_spec_sha256": hashlib.sha256(
                canonical_json_bytes(strict_v2_spec)
            ).hexdigest(),
            "image_capture_enabled": False,
            "release_clearance_basis": FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        },
        "nominal_replay": baseline,
        "symmetric_perturbation_pairs": pairs,
        "derived_phase_joint_threshold_design": threshold_rows,
        "threshold_derivation_contract": {
            "candidate_outputs_are_inputs": False,
            "prefix_safe_rule": "after_first_paired_consequence_failure_all_larger_magnitudes_remain_unsafe_even_if_non_monotonic",
            "resolution_floor_rad": RESOLUTION_FLOOR_RAD,
            "joint_minimum_phase_ceiling_rad": joint_safeguards,
            "phase_specific_ceiling_required": True,
            "task_critical_joint_waiver_allowed": False,
            "immediate_gate_amendment_authorized": False,
        },
        "strict_uniform_gate_report_only": {
            "maximum_absolute_error_rad": STRICT_UNIFORM_THRESHOLD_RAD,
            "maximum_final_to_baseline_supervised_objective_ratio": 0.1,
            "all_dimensions_timesteps_and_fixed_repetitions_reported": True,
            "status": "retained_visible_non_gating_in_proposed_amendment",
        },
        "eventual_gate_c_arbiter": {
            "required": True,
            "scope": "one_training_episode_closed_loop_reproduction",
            "consequence_metric_pass_alone_accepts_policy": False,
            "executed_by_this_artifact": False,
        },
        "gate_b_threshold_changed": False,
        "gate_c_authorized": False,
        "closed_loop_policy_evaluation": False,
        "model_constructed": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "simulation_policy_accepted": False,
        "promotion_eligible": False,
        "physical_transfer_ready": False,
    }
    result = sign_payload(payload)
    verify_design(result, repo_root=repo_root)
    return result


def verify_design(payload: dict[str, Any], *, repo_root: Path = REPO_ROOT) -> None:
    verify_signed_payload(payload, label="T20.36k consequence design")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("T20.36k consequence design schema drifted")
    sources = _load_sources(repo_root)
    for name, expected in sources["refs"].items():
        verify_artifact_ref(payload.get("source_refs", {}).get(name), expected, label=name)
    context = payload.get("candidate_evidence_context_only", {})
    expected_context = {
        "used_for_threshold_derivation": False,
        "act_result_identity_sha256": sources["act_result"]["identity_sha256"],
        "act_localization_identity_sha256": sources["act_localization"][
            "identity_sha256"
        ],
        "smolvla_result_identity_sha256": sources["smolvla_result"][
            "identity_sha256"
        ],
        "act_final_to_baseline_supervised_objective_ratio": sources["act_result"][
            "final_to_baseline_supervised_objective_ratio"
        ],
        "act_final_maximum_absolute_error_rad": sources["act_result"][
            "final_maximum_absolute_error_rad"
        ],
        "smolvla_final_to_baseline_supervised_objective_ratio": sources[
            "smolvla_result"
        ]["final_to_baseline_supervised_objective_ratio"],
        "smolvla_final_maximum_absolute_error_rad": sources["smolvla_result"][
            "final_maximum_absolute_error_rad"
        ],
    }
    if context != expected_context:
        raise ValueError("Candidate evidence must not derive consequence thresholds")
    perturbation = payload.get("perturbation_spec", {})
    if perturbation.get("magnitudes_rad") != list(PERTURBATION_MAGNITUDES_RAD):
        raise ValueError("T20.36k perturbation grid drifted")
    if (
        perturbation.get("joint_names") != list(JOINT_NAMES)
        or perturbation.get("phase_groups")
        != {name: list(phases) for name, phases in PHASE_GROUPS.items()}
        or perturbation.get("signs") != [-1, 1]
        or perturbation.get("pair_count")
        != len(JOINT_NAMES) * len(PHASE_GROUPS) * len(PERTURBATION_MAGNITUDES_RAD)
        or perturbation.get("simulation_seed") != SOURCE_SEED
        or perturbation.get("image_capture_enabled") is not False
        or perturbation.get("release_clearance_basis")
        != FORCE_BEARING_RELEASE_CLEARANCE_BASIS
    ):
        raise ValueError("T20.36k perturbation contract drifted")
    source_entry = _source_episode_entry(sources["manifest"])
    if perturbation.get("source_episode_file_sha256") != source_entry.get(
        "episode_file_sha256"
    ) or perturbation.get(
        "source_raw_rollout_record_identity_sha256"
    ) != source_entry.get(
        "raw_rollout_record_identity_sha256"
    ):
        raise ValueError("T20.36k canonical action chunk binding drifted")
    expected_strict_v2 = hashlib.sha256(
        canonical_json_bytes(strict_grasp_spec_v2())
    ).hexdigest()
    if perturbation.get("strict_v2_spec_sha256") != expected_strict_v2:
        raise ValueError("T20.36k strict-v2 evaluator binding drifted")
    pairs = payload.get("symmetric_perturbation_pairs")
    if not isinstance(pairs, list):
        raise ValueError("T20.36k consequence pairs are missing")
    baseline = payload.get("nominal_replay", {})
    _verify_pair_records(pairs, baseline)
    derived = derive_threshold_rows(pairs)
    if payload.get("derived_phase_joint_threshold_design") != derived:
        raise ValueError("T20.36k threshold derivation drifted")
    expected_safeguards = {
        joint: min(
            row["amendment_ceiling_rad"]
            for row in derived
            if row["joint_name"] == joint
        )
        for joint in JOINT_NAMES
    }
    contract = payload.get("threshold_derivation_contract", {})
    if (
        contract.get("candidate_outputs_are_inputs") is not False
        or contract.get("joint_minimum_phase_ceiling_rad") != expected_safeguards
        or contract.get("task_critical_joint_waiver_allowed") is not False
        or contract.get("immediate_gate_amendment_authorized") is not False
    ):
        raise ValueError("T20.36k threshold derivation contract drifted")
    historical_gate = sources["historical_gate_b_spec"].get("gate", {})
    report_only = payload.get("strict_uniform_gate_report_only", {})
    if report_only.get("maximum_absolute_error_rad") != historical_gate.get(
        "maximum_physical_action_error_rad"
    ) or report_only.get(
        "maximum_final_to_baseline_supervised_objective_ratio"
    ) != historical_gate.get(
        "maximum_final_to_baseline_supervised_objective_ratio"
    ):
        raise ValueError("T20.36k historical Gate B report-only binding drifted")
    if baseline.get("simulation_semantic_strict_success") is not True:
        raise ValueError("T20.36k nominal replay must pass strict-v2")
    for key in (
        "gate_b_threshold_changed",
        "gate_c_authorized",
        "closed_loop_policy_evaluation",
        "model_constructed",
        "model_inference",
        "optimizer_created",
        "optimizer_training",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "simulation_policy_accepted",
        "promotion_eligible",
        "physical_transfer_ready",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"T20.36k must keep {key} false")
    arbiter = payload.get("eventual_gate_c_arbiter", {})
    if arbiter.get("required") is not True or arbiter.get(
        "consequence_metric_pass_alone_accepts_policy"
    ) is not False:
        raise ValueError("T20.36k must keep Gate C as the behavioral arbiter")


def _load_sources(repo_root: Path) -> dict[str, Any]:
    paths = {
        "act_result": ACT_RESULT_PATH,
        "act_localization": ACT_LOCALIZATION_PATH,
        "smolvla_result": SMOLVLA_RESULT_PATH,
        "source_manifest": SOURCE_MANIFEST_PATH,
        "historical_gate_b_spec": HISTORICAL_GATE_B_SPEC_PATH,
    }
    loaded = {name: load_strict_json(repo_root / path) for name, path in paths.items()}
    for name, payload in loaded.items():
        verify_signed_payload(payload, label=f"T20.36k {name}")
    verify_episode_store(loaded["source_manifest"], default_store_root(repo_root=repo_root))
    refs = {
        name: artifact_ref(path=path, payload=loaded[name], repo_root=repo_root)
        for name, path in paths.items()
    }
    return {**loaded, "manifest": loaded["source_manifest"], "refs": refs}


def _load_nominal_actions(manifest: dict[str, Any], repo_root: Path) -> np.ndarray:
    entry = _source_episode_entry(manifest)
    episode_path = default_store_root(repo_root=repo_root) / entry["relative_path"]
    if hashlib.sha256(episode_path.read_bytes()).hexdigest() != entry["episode_file_sha256"]:
        raise ValueError("T20.36k source episode file hash drifted")
    episode = load_strict_json(episode_path)
    frames = episode.get("frames")
    if not isinstance(frames, list) or len(frames) != ROLLOUT_FRAMES:
        raise ValueError("T20.36k source episode horizon drifted")
    actions = np.asarray(
        [row["actions"]["requested"]["values"] for row in frames],
        dtype=np.float64,
    )
    if actions.shape != (ROLLOUT_FRAMES, len(JOINT_NAMES)) or not np.isfinite(actions).all():
        raise ValueError("T20.36k source actions are invalid")
    return actions


def _source_episode_entry(manifest: dict[str, Any]) -> dict[str, Any]:
    entries = [
        row for row in manifest.get("episodes", []) if row.get("seed") == SOURCE_SEED
    ]
    if len(entries) != 1 or entries[0].get("outcome", {}).get("strict_success") is not True:
        raise ValueError("T20.36k requires one strict-success seed-0 source episode")
    return entries[0]


def _run_action_sequence(actions: np.ndarray, *, label: str) -> dict[str, Any]:
    index = 0

    def policy(_images: dict[str, np.ndarray], _state: np.ndarray) -> np.ndarray:
        nonlocal index
        if index >= len(actions):
            raise ValueError("T20.36k action sequence exhausted")
        action = actions[index].copy()
        index += 1
        return action

    rollout = run_policy_grasp_closed_loop(
        policy,
        checkpoint_sha256="0" * 64,
        training_run_summary_sha256="0" * 64,
        seed=SOURCE_SEED,
        schema_version="scenesmith.t20_36k_model_free_perturbation.v1",
        task_id="T20.36k",
        evidence_mode="model_free_canonical_action_consequence_sensitivity",
        policy_label=label,
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        capture_images=False,
    )
    if index != ROLLOUT_FRAMES:
        raise ValueError("T20.36k action sequence was not consumed exactly once")
    return rollout


def _summarize_rollout(
    rollout: dict[str, Any],
    *,
    baseline_measurements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    margins = rollout.get("gate_margins", {})
    measurements = {name: margins[name]["measured"] for name in _GATE_MEASUREMENTS}
    summary: dict[str, Any] = {
        "rollout_identity_sha256": rollout["identity_sha256"],
        "policy_action_sequence_sha256": rollout["policy_action_sequence_sha256"],
        "terminal_outcome": rollout["terminal_outcome"],
        "simulation_semantic_strict_success": rollout[
            "simulation_semantic_strict_success"
        ],
        "failed_gate_names": [row["gate"] for row in rollout["failed_gate_margins"]],
        "gate_measurements": measurements,
        "strict_v2_valid_frame_counts": rollout["strict_v2_valid_frame_counts"],
        "maximum_anchor_lift_m": rollout["maximum_anchor_lift_m"],
        "projected_action_frame_count": rollout["projected_action_frame_count"],
        "active_assist_frame_count": rollout["active_assist_frame_count"],
    }
    if baseline_measurements is not None:
        summary["gate_measurement_delta_from_nominal"] = {
            name: _numeric_delta(measurements[name], baseline_measurements[name])
            for name in _GATE_MEASUREMENTS
        }
    return summary


def _numeric_delta(value: Any, baseline: Any) -> float | None:
    if isinstance(value, bool) or isinstance(baseline, bool):
        return None
    if not isinstance(value, (int, float)) or not isinstance(baseline, (int, float)):
        return None
    delta = float(value) - float(baseline)
    return 0.0 if delta == 0 else delta


def _verify_pair_records(
    pairs: list[dict[str, Any]], baseline: dict[str, Any]
) -> None:
    baseline_measurements = baseline.get("gate_measurements")
    if not isinstance(baseline_measurements, dict) or set(baseline_measurements) != set(
        _GATE_MEASUREMENTS
    ):
        raise ValueError("T20.36k nominal gate measurements drifted")
    for pair in pairs:
        magnitude = pair.get("magnitude_rad")
        if pair.get("requested_pair_rad") != [-magnitude, magnitude]:
            raise ValueError("T20.36k requested symmetric pair drifted")
        sign_successes = []
        for sign_name in ("negative", "positive"):
            summary = pair.get(sign_name)
            if not isinstance(summary, dict):
                raise ValueError("T20.36k signed consequence summary is missing")
            measurements = summary.get("gate_measurements")
            if not isinstance(measurements, dict) or set(measurements) != set(
                _GATE_MEASUREMENTS
            ):
                raise ValueError("T20.36k signed gate measurements drifted")
            expected_deltas = {
                name: _numeric_delta(measurements[name], baseline_measurements[name])
                for name in _GATE_MEASUREMENTS
            }
            if summary.get("gate_measurement_delta_from_nominal") != expected_deltas:
                raise ValueError("T20.36k consequence delta drifted")
            success = summary.get("simulation_semantic_strict_success")
            if not isinstance(success, bool):
                raise ValueError("T20.36k signed consequence pass state drifted")
            sign_successes.append(success)
        if pair.get("both_signs_consequence_passed") is not all(sign_successes):
            raise ValueError("T20.36k paired consequence pass state drifted")
