"""Optimizer-free signed-evidence interference audit for T20.36a."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = Path(
    "configurations/robot_lab/t20_36a_objective_interference_audit.json"
)
SOURCE_SPEC_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_training_spec.json"
)
SOURCE_RESULT_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_result.json"
)
SOURCE_RUN_PATH = Path(
    "outputs/robot_lab/t20_35x_physical_gate_joint_weighted_run_001/run_summary.json"
)
CAMPAIGN_SPEC_PATH = Path(
    "configurations/robot_lab/t20_36_bounded_corrected_coverage_training_spec.json"
)
CAMPAIGN_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36_bounded_corrected_coverage_result.json"
)
CAMPAIGN_RUN_PATH = Path(
    "outputs/robot_lab/t20_36_bounded_corrected_coverage_run_001/run_summary.json"
)
THRESHOLD_PATH = Path("configurations/robot_lab/t20_32_divergence_thresholds.json")
SCHEMA_VERSION = "scenesmith.t20_36a_objective_interference_audit.v1"
TASK_ID = "T20.36a"
EXPECTED_X_SPEC_IDENTITY = (
    "96efc6d35115126268684c91346b7388077342c573e458b7e708e98714113cfd"
)
EXPECTED_X_RUN_IDENTITY = (
    "b5cc16ef53a415a7e0a4b8519332a4197201544fc9ebe5186565562e048c054b"
)
EXPECTED_X_RESULT_IDENTITY = (
    "e79dacff684dac507295d839527fb15d4eced8fa9c83973f5534bdf7e99ec6cd"
)
EXPECTED_X_CHECKPOINT_IDENTITY = (
    "40c94f66e24f0e949c1b48c057de7643b868468cc3ee0025e15778c25b8cad50"
)
EXPECTED_THRESHOLD_IDENTITY = (
    "edbbf85e56a7020cec9b16cbab6263dc3e9dbe106ff8f55b53a85d3034d7f4cb"
)
EXPECTED_CAMPAIGN_SPEC_IDENTITY = (
    "522a1e5a871613640eb24ba8334f24dad98c027f13a9e52b861ca56afdb19cfb"
)
EXPECTED_CAMPAIGN_RUN_IDENTITY = (
    "88daae0d8239239d064227b9e9561a01b7bf634d849dc4e61237b1713462410e"
)
EXPECTED_CAMPAIGN_RESULT_IDENTITY = (
    "02b543be829220f89e0bfe2d16b042507127f488f73a9de0149442e89bc3a638"
)
EXPECTED_INPUT_FILE_SHA256 = {
    "source_spec": "a404128fedd56529b039ec98031aee09073ba156e8cc6f89d3d9b075d5d77e77",
    "source_run": "b05fd6c68ea13f2e140861249f16b42a95f517d1b9ab24e36b6995c954a8f02d",
    "source_result": "981082fd51f15b3067af6e1a4724d46b5941f3016b8212dc9af385c3167501e4",
    "campaign_spec": "8d0b826ab48b9528870747ec1297362f6bf319a53548ff04214a0df96eef211f",
    "campaign_run": "19010302db1e7f41cc6a089914fa7260030eaa57498bea76737a03fb9862e830",
    "campaign_result": "7927aaafa7d7a403487ac228b8cfe7e058b3414ac0a2a6a56993d77b17ba8ee8",
    "threshold": "e91632dcefc104d6ed5596140f9fc1d33080580ab2b16c3f74744b23ce0d7c12",
}
HISTORY_UPDATE_COUNT = 500
HISTORY_WINDOW_SIZE = 25
ABSOLUTE_TOLERANCE = 1e-12


def classify_interference(
    *,
    weighted_ratio: float,
    raw_ratio: float,
    every_decoded_seed_maximum_worsened: bool,
) -> tuple[str, str]:
    """Classify only the mutually exclusive predicates declared by Brief 192."""
    weighted = _finite(weighted_ratio, "weighted correction ratio")
    raw = _finite(raw_ratio, "raw correction ratio")
    if weighted < 1.0 and raw > 1.0 and every_decoded_seed_maximum_worsened:
        return (
            "weighted_objective_physical_gate_aliasing_under_coverage",
            "design_gate_equivalent_retention_guard_before_any_training_proposal",
        )
    if weighted > 1.0 and raw > 1.0:
        return (
            "broad_correction_objective_regression_under_coverage",
            "audit_gradient_objective_scale_compatibility_before_any_training_proposal",
        )
    return (
        "insufficient_recorded_evidence_for_interference_classification",
        "preserve_gate_b_closed_and_request_one_separately_reviewed_diagnostic",
    )


def build_audit(
    *,
    source_spec: dict[str, Any],
    source_run: dict[str, Any],
    source_result: dict[str, Any],
    campaign_spec: dict[str, Any],
    campaign_run: dict[str, Any],
    campaign_result: dict[str, Any],
    threshold: dict[str, Any],
    input_file_sha256: dict[str, str],
) -> dict[str, Any]:
    _verify_sources(
        source_spec=source_spec,
        source_run=source_run,
        source_result=source_result,
        campaign_spec=campaign_spec,
        campaign_run=campaign_run,
        campaign_result=campaign_result,
        threshold=threshold,
        input_file_sha256=input_file_sha256,
    )

    gate = campaign_spec["gate_b"]
    maximum_objective_ratio = _finite(
        gate.get("maximum_objective_ratio"), "maximum objective ratio"
    )
    maximum_action_error = _finite(
        gate.get("maximum_action_error_rad"), "maximum action error"
    )
    if maximum_objective_ratio != 0.1 or maximum_action_error != 0.05:
        raise ValueError("T20.36a Gate B thresholds drifted")

    source_standard = _positive(
        source_result.get("final_standard_objective_mean"),
        "source standard objective",
    )
    campaign_standard = _positive(
        campaign_run.get("final_standard_objective_mean"),
        "campaign standard objective",
    )
    campaign_standard_by_seed = _finite_vector(
        campaign_run.get("final_standard_objective_by_seed"),
        5,
        "campaign standard objective by seed",
        nonnegative=True,
    )
    if not math.isclose(
        sum(campaign_standard_by_seed) / len(campaign_standard_by_seed),
        campaign_standard,
        rel_tol=0.0,
        abs_tol=ABSOLUTE_TOLERANCE,
    ):
        raise ValueError("T20.36a campaign standard-objective mean drifted")

    source_raw = _positive(
        source_result.get("final_raw_correction_objective_mean"),
        "source raw correction objective",
    )
    campaign_baseline_raw = _positive(
        campaign_run.get("baseline_raw_correction_objective_mean"),
        "campaign baseline raw correction objective",
    )
    campaign_raw = _positive(
        campaign_run.get("final_raw_correction_objective_mean"),
        "campaign raw correction objective",
    )
    source_weighted = _positive(
        source_result.get("final_joint_weighted_correction_objective_mean"),
        "source joint-weighted correction objective",
    )
    campaign_baseline_weighted = _positive(
        campaign_run.get("baseline_joint_weighted_correction_objective_mean"),
        "campaign baseline joint-weighted correction objective",
    )
    campaign_weighted = _positive(
        campaign_run.get("final_joint_weighted_correction_objective_mean"),
        "campaign joint-weighted correction objective",
    )
    for source, baseline, label in (
        (source_raw, campaign_baseline_raw, "raw correction"),
        (source_weighted, campaign_baseline_weighted, "joint-weighted correction"),
    ):
        if not math.isclose(
            source,
            baseline,
            rel_tol=0.0,
            abs_tol=ABSOLUTE_TOLERANCE,
        ):
            raise ValueError(f"T20.36a X-to-campaign {label} handoff drifted")

    decoded_change = _decoded_change(
        source_result=source_result,
        campaign_run=campaign_run,
        maximum_action_error=maximum_action_error,
    )
    source_worst = max(row["source_maximum_absolute_error_rad"] for row in decoded_change)
    campaign_worst = max(
        row["campaign_maximum_absolute_error_rad"] for row in decoded_change
    )
    every_max_worsened = all(row["maximum_error_worsened"] for row in decoded_change)
    if (
        source_result.get("gate_b_passed") is not True
        or campaign_run.get("gate_b_passed") is not False
        or campaign_result.get("gate_b_passed") is not False
        or campaign_result.get("decision")
        != "gate_b_regressed_stop_before_closed_loop"
        or campaign_result.get("evaluation_seeds_reached") != []
    ):
        raise ValueError("T20.36a Gate B source or stop route drifted")

    weighted_ratio = campaign_weighted / source_weighted
    raw_ratio = campaign_raw / source_raw
    classification, route = classify_interference(
        weighted_ratio=weighted_ratio,
        raw_ratio=raw_ratio,
        every_decoded_seed_maximum_worsened=every_max_worsened,
    )

    standard_history = _finite_vector(
        campaign_run.get("per_update_standard_coverage_objective"),
        HISTORY_UPDATE_COUNT,
        "standard coverage history",
        nonnegative=True,
    )
    correction_history = _finite_vector(
        campaign_run.get("per_update_time_joint_weighted_correction_objective"),
        HISTORY_UPDATE_COUNT,
        "weighted correction history",
        nonnegative=True,
    )
    total_history = _finite_vector(
        campaign_run.get("per_update_total_objective"),
        HISTORY_UPDATE_COUNT,
        "total objective history",
        nonnegative=True,
    )
    gradient_history = _finite_vector(
        campaign_run.get("gradient_norms_before_clip"),
        HISTORY_UPDATE_COUNT,
        "gradient norm history",
        nonnegative=True,
    )
    for standard, correction, total in zip(
        standard_history, correction_history, total_history, strict=True
    ):
        if not math.isclose(
            standard + correction,
            total,
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            raise ValueError("T20.36a paired objective history drifted")
    gradient_clip_norm = _positive(
        campaign_run.get("optimizer_config", {}).get("gradient_clip_norm"),
        "gradient clip norm",
    )
    history_windows = _history_windows(
        standard_history=standard_history,
        correction_history=correction_history,
        total_history=total_history,
        gradient_history=gradient_history,
        gradient_clip_norm=gradient_clip_norm,
    )

    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "scope": "one_optimizer_free_signed_evidence_objective_interference_audit",
            "source_spec_identity_sha256": source_spec["identity_sha256"],
            "source_run_identity_sha256": source_run["identity_sha256"],
            "source_result_identity_sha256": source_result["identity_sha256"],
            "source_checkpoint_identity_sha256": source_run[
                "checkpoint_identity_sha256"
            ],
            "campaign_spec_identity_sha256": campaign_spec["identity_sha256"],
            "campaign_run_identity_sha256": campaign_run["identity_sha256"],
            "campaign_result_identity_sha256": campaign_result["identity_sha256"],
            "campaign_checkpoint_identity_sha256": campaign_run[
                "checkpoint_identity_sha256"
            ],
            "threshold_identity_sha256": threshold["identity_sha256"],
            "input_file_sha256": dict(input_file_sha256),
            "maximum_allowed_objective_ratio": maximum_objective_ratio,
            "maximum_allowed_action_error_rad": maximum_action_error,
            "source_standard_objective_mean": source_standard,
            "campaign_standard_objective_mean": campaign_standard,
            "campaign_to_source_standard_objective_ratio": campaign_standard
            / source_standard,
            "source_raw_correction_objective_mean": source_raw,
            "campaign_raw_correction_objective_mean": campaign_raw,
            "campaign_to_source_raw_correction_ratio": raw_ratio,
            "source_joint_weighted_correction_objective_mean": source_weighted,
            "campaign_joint_weighted_correction_objective_mean": campaign_weighted,
            "campaign_to_source_joint_weighted_correction_ratio": weighted_ratio,
            "source_worst_action_error_rad": source_worst,
            "campaign_worst_action_error_rad": campaign_worst,
            "campaign_to_source_worst_action_error_ratio": campaign_worst
            / source_worst,
            "decoded_action_change_by_seed": decoded_change,
            "source_gate_b_passed": True,
            "campaign_gate_b_passed": False,
            "joint_weighted_correction_improved": weighted_ratio < 1.0,
            "raw_correction_worsened": raw_ratio > 1.0,
            "every_decoded_seed_maximum_worsened": every_max_worsened,
            "history_update_count": HISTORY_UPDATE_COUNT,
            "history_window_size": HISTORY_WINDOW_SIZE,
            "gradient_clip_norm": gradient_clip_norm,
            "history_windows": history_windows,
            "standard_coverage_history_summary": _series_summary(standard_history),
            "weighted_correction_history_summary": _series_summary(
                correction_history
            ),
            "total_objective_history_summary": _series_summary(total_history),
            "gradient_norm_history_summary": {
                **_series_summary(gradient_history),
                "above_clip_count": sum(
                    value > gradient_clip_norm for value in gradient_history
                ),
            },
            "interference_classification": classification,
            "classification_limitation": "records_non_equivalence_of_the_weighted_mean_and_physical_maximum_gate_in_this_campaign_not_gradient_level_causality",
            "selected_next_hypothesis": route,
            "checkpoint_read": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "gate_b_threshold_changed": False,
            "second_campaign_authorized": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_audit(payload: dict[str, Any], **sources: Any) -> None:
    verify_signed_payload(payload, label="T20.36a objective interference audit")
    expected = build_audit(**sources)
    if payload != expected:
        raise ValueError("T20.36a objective interference audit drifted")


def load_source_artifacts(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    paths = {
        "source_spec": root / SOURCE_SPEC_PATH,
        "source_run": root / SOURCE_RUN_PATH,
        "source_result": root / SOURCE_RESULT_PATH,
        "campaign_spec": root / CAMPAIGN_SPEC_PATH,
        "campaign_run": root / CAMPAIGN_RUN_PATH,
        "campaign_result": root / CAMPAIGN_RESULT_PATH,
        "threshold": root / THRESHOLD_PATH,
    }
    return {
        **{label: load_strict_json(path) for label, path in paths.items()},
        "input_file_sha256": {
            label: hashlib.sha256(path.read_bytes()).hexdigest()
            for label, path in paths.items()
        },
    }


def write_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    audit = build_audit(**sources)
    dump_canonical_json(root / AUDIT_PATH, audit)
    return audit


def verify_audit_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_source_artifacts(repo_root=root)
    audit = load_strict_json(root / AUDIT_PATH)
    verify_audit(audit, **sources)
    return audit


def _verify_sources(
    *,
    source_spec: dict[str, Any],
    source_run: dict[str, Any],
    source_result: dict[str, Any],
    campaign_spec: dict[str, Any],
    campaign_run: dict[str, Any],
    campaign_result: dict[str, Any],
    threshold: dict[str, Any],
    input_file_sha256: dict[str, str],
) -> None:
    if input_file_sha256 != EXPECTED_INPUT_FILE_SHA256:
        raise ValueError("T20.36a input file identity drifted")
    for label, payload in (
        ("source spec", source_spec),
        ("source run", source_run),
        ("source result", source_result),
        ("campaign spec", campaign_spec),
        ("campaign run", campaign_run),
        ("campaign result", campaign_result),
        ("threshold", threshold),
    ):
        verify_signed_payload(payload, label=f"T20.36a {label}")
    if (
        source_spec.get("identity_sha256") != EXPECTED_X_SPEC_IDENTITY
        or source_run.get("identity_sha256") != EXPECTED_X_RUN_IDENTITY
        or source_result.get("identity_sha256") != EXPECTED_X_RESULT_IDENTITY
        or source_run.get("checkpoint_identity_sha256")
        != EXPECTED_X_CHECKPOINT_IDENTITY
        or campaign_spec.get("identity_sha256")
        != EXPECTED_CAMPAIGN_SPEC_IDENTITY
        or campaign_run.get("identity_sha256")
        != EXPECTED_CAMPAIGN_RUN_IDENTITY
        or campaign_result.get("identity_sha256")
        != EXPECTED_CAMPAIGN_RESULT_IDENTITY
        or threshold.get("identity_sha256") != EXPECTED_THRESHOLD_IDENTITY
    ):
        raise ValueError("T20.36a signed source identity drifted")
    source_authority = source_result.get("authority_decision_identity_sha256")
    campaign_authority = campaign_result.get("authority_decision_identity_sha256")
    if (
        source_result.get("training_spec_identity_sha256")
        != source_spec["identity_sha256"]
        or source_result.get("run_identity_sha256") != source_run["identity_sha256"]
        or source_run.get("training_spec_identity_sha256")
        != source_spec["identity_sha256"]
        or source_run.get("authority_decision_identity_sha256") != source_authority
        or source_result.get("gate_b_passed") is not True
        or source_run.get("optimizer_training") is not True
        or campaign_result.get("training_spec_identity_sha256")
        != campaign_spec["identity_sha256"]
        or campaign_result.get("run_identity_sha256")
        != campaign_run["identity_sha256"]
        or campaign_run.get("training_spec_identity_sha256")
        != campaign_spec["identity_sha256"]
        or campaign_run.get("authority_decision_identity_sha256")
        != campaign_authority
        or campaign_result.get("gate_b_passed") is not False
        or campaign_run.get("gate_b_passed") is not False
        or campaign_run.get("optimizer_training") is not True
    ):
        raise ValueError("T20.36a signed source lineage or result drifted")


def _decoded_change(
    *,
    source_result: dict[str, Any],
    campaign_run: dict[str, Any],
    maximum_action_error: float,
) -> list[dict[str, Any]]:
    source_rows = source_result.get("decoded_action_chunks")
    campaign_rows = campaign_run.get("decoded_action_chunks")
    if not isinstance(source_rows, list) or not isinstance(campaign_rows, list):
        raise ValueError("T20.36a decoded action evidence is missing")
    if len(source_rows) != 5 or len(campaign_rows) != 5:
        raise ValueError("T20.36a decoded action seed coverage drifted")
    output = []
    for source, campaign in zip(source_rows, campaign_rows, strict=True):
        if (
            not isinstance(source, dict)
            or not isinstance(campaign, dict)
            or source.get("inference_seed") != campaign.get("inference_seed")
        ):
            raise ValueError("T20.36a decoded action seed order drifted")
        source_max = _nonnegative(
            source.get("maximum_absolute_error_rad"), "source decoded maximum"
        )
        campaign_max = _nonnegative(
            campaign.get("maximum_absolute_error_rad"),
            "campaign decoded maximum",
        )
        source_mean = _nonnegative(
            source.get("mean_absolute_error_rad"), "source decoded mean"
        )
        campaign_mean = _nonnegative(
            campaign.get("mean_absolute_error_rad"), "campaign decoded mean"
        )
        if source_max > maximum_action_error or campaign_max <= maximum_action_error:
            raise ValueError("T20.36a decoded Gate B pass-to-fail transition drifted")
        output.append(
            {
                "inference_seed": source["inference_seed"],
                "source_decoded_action_chunk_sha256": source[
                    "decoded_action_chunk_sha256"
                ],
                "campaign_decoded_action_chunk_sha256": campaign[
                    "decoded_action_chunk_sha256"
                ],
                "source_maximum_absolute_error_rad": source_max,
                "campaign_maximum_absolute_error_rad": campaign_max,
                "maximum_error_ratio": campaign_max / source_max,
                "maximum_error_worsened": campaign_max > source_max,
                "source_mean_absolute_error_rad": source_mean,
                "campaign_mean_absolute_error_rad": campaign_mean,
                "mean_error_ratio": campaign_mean / source_mean,
                "mean_error_worsened": campaign_mean > source_mean,
            }
        )
    return output


def _history_windows(
    *,
    standard_history: list[float],
    correction_history: list[float],
    total_history: list[float],
    gradient_history: list[float],
    gradient_clip_norm: float,
) -> list[dict[str, Any]]:
    windows = []
    for start in range(0, HISTORY_UPDATE_COUNT, HISTORY_WINDOW_SIZE):
        stop = start + HISTORY_WINDOW_SIZE
        standard = standard_history[start:stop]
        correction = correction_history[start:stop]
        total = total_history[start:stop]
        gradient = gradient_history[start:stop]
        standard_sum = sum(standard)
        correction_sum = sum(correction)
        total_sum = sum(total)
        if not math.isclose(
            standard_sum + correction_sum,
            total_sum,
            rel_tol=0.0,
            abs_tol=1e-8,
        ):
            raise ValueError("T20.36a history-window objective mass drifted")
        windows.append(
            {
                "window_index": start // HISTORY_WINDOW_SIZE,
                "update_start": start + 1,
                "update_end": stop,
                "standard_coverage_objective_mean": standard_sum
                / HISTORY_WINDOW_SIZE,
                "weighted_correction_objective_mean": correction_sum
                / HISTORY_WINDOW_SIZE,
                "total_objective_mean": total_sum / HISTORY_WINDOW_SIZE,
                "standard_objective_mass_fraction": standard_sum / total_sum,
                "weighted_correction_objective_mass_fraction": correction_sum
                / total_sum,
                "gradient_norm_mean_before_clip": sum(gradient)
                / HISTORY_WINDOW_SIZE,
                "gradient_norm_maximum_before_clip": max(gradient),
                "gradient_norm_above_clip_count": sum(
                    value > gradient_clip_norm for value in gradient
                ),
            }
        )
    return windows


def _series_summary(values: list[float]) -> dict[str, float]:
    return {
        "first": values[0],
        "last": values[-1],
        "minimum": min(values),
        "maximum": max(values),
        "mean": sum(values) / len(values),
        "first_window_mean": sum(values[:HISTORY_WINDOW_SIZE])
        / HISTORY_WINDOW_SIZE,
        "last_window_mean": sum(values[-HISTORY_WINDOW_SIZE:])
        / HISTORY_WINDOW_SIZE,
    }


def _finite_vector(
    value: Any,
    count: int,
    label: str,
    *,
    nonnegative: bool = False,
) -> list[float]:
    if not isinstance(value, list) or len(value) != count:
        raise ValueError(f"T20.36a {label} coverage drifted")
    values = [_finite(item, label) for item in value]
    if nonnegative and any(item < 0.0 for item in values):
        raise ValueError(f"T20.36a {label} must be nonnegative")
    return values


def _positive(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number <= 0.0:
        raise ValueError(f"T20.36a {label} must be positive")
    return number


def _nonnegative(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number < 0.0:
        raise ValueError(f"T20.36a {label} must be nonnegative")
    return number


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.36a {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.36a {label} must be finite")
    return number
