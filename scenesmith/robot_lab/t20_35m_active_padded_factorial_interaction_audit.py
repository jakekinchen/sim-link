"""Model-free 2x2 active/padded noise interaction audit for T20.35m."""

from __future__ import annotations

import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_35l_active_padded_noise_mask_discriminator import (
    ATTEMPT_PATH as T20_35L_ATTEMPT_PATH,
    RESULT_PATH as T20_35L_RESULT_PATH,
    ALL_NOISE_CONDITIONS,
    load_and_verify_evaluation_files as load_t20_35l_sources,
    verify_attempt_marker as verify_t20_35l_attempt,
    verify_result as verify_t20_35l_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = Path(
    "configurations/robot_lab/t20_35m_active_padded_factorial_interaction_audit.json"
)
SCHEMA_VERSION = (
    "scenesmith.t20_35m_active_padded_factorial_interaction_audit.v1"
)
EXPECTED_T20_35L_RESULT_IDENTITY = (
    "b4fc6060c56431ab2bf52dd74d8efa58b1808a10a827521db076f9d10234dbea"
)
METRICS = (
    "worst_seed_maximum_error_rad",
    "aggregate_mean_absolute_error_rad",
    "aggregate_mean_raw_decoded_spread_rad",
)


def build_factorial_interaction_audit(
    *,
    t20_35l_result_identity: str,
    condition_metrics: list[dict[str, Any]],
    source_gate_b_passed: bool,
) -> dict[str, Any]:
    _sha(t20_35l_result_identity, "T20.35l result identity")
    if source_gate_b_passed is not False:
        raise ValueError("T20.35m source Gate B route drifted")
    conditions = _normalize_conditions(condition_metrics)
    by_name = {row["noise_condition"]: row for row in conditions}
    all_normal = by_name["active_normal_padded_normal"]
    active_normal_padded_zero = by_name["active_normal_padded_zero"]
    active_zero_padded_normal = by_name["active_zero_padded_normal"]
    all_zero = by_name["active_zero_padded_zero"]
    contrasts = []
    for metric in METRICS:
        y11 = all_normal[metric]
        y10 = active_normal_padded_zero[metric]
        y01 = active_zero_padded_normal[metric]
        y00 = all_zero[metric]
        contrasts.append(
            {
                "metric": metric,
                "active_noise_effect_with_padded_zero": y10 - y00,
                "active_noise_effect_with_padded_normal": y11 - y01,
                "padded_noise_effect_with_active_zero": y01 - y00,
                "padded_noise_effect_with_active_normal": y11 - y10,
                "active_padded_interaction": y11 - y10 - y01 + y00,
            }
        )
    active_harmful = all(
        row["active_noise_effect_with_padded_zero"] > 0
        and row["active_noise_effect_with_padded_normal"] > 0
        for row in contrasts
    )
    accuracy_contrasts = contrasts[:2]
    padded_accuracy_sign_change = all(
        row["padded_noise_effect_with_active_zero"] < 0
        and row["padded_noise_effect_with_active_normal"] > 0
        for row in accuracy_contrasts
    )
    best = min(
        conditions,
        key=lambda row: (
            row["worst_seed_maximum_error_rad"],
            row["aggregate_mean_absolute_error_rad"],
            ALL_NOISE_CONDITIONS.index(row["noise_condition"]),
        ),
    )["noise_condition"]
    if (
        active_harmful
        and padded_accuracy_sign_change
        and best == "active_zero_padded_normal"
    ):
        classification = (
            "active_noise_dominant_with_context_dependent_padded_interaction"
        )
        route = (
            "run_separately_reviewed_near_zero_active_noise_scale_discriminator_"
            "with_padded_normal"
        )
    else:
        classification = "factorial_effects_require_general_flow_consistency_audit"
        route = "audit_smallest_factor_from_factorial_contrasts"
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35m",
            "scope": "model_free_active_padded_noise_two_by_two_factorial_interaction_audit",
            "t20_35l_result_identity_sha256": t20_35l_result_identity,
            "condition_metrics": conditions,
            "metric_contrasts": contrasts,
            "active_noise_harmful_at_both_padded_settings_all_metrics": active_harmful,
            "padded_noise_accuracy_effect_changes_sign_by_active_setting": (
                padded_accuracy_sign_change
            ),
            "best_noise_condition": best,
            "interaction_classification": classification,
            "selected_next_hypothesis": route,
            "gate_b_passed": False,
            "action_correction_selected": False,
            "model_imported": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_read": False,
            "checkpoint_mutated": False,
            "dataset_read": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "sampler_mutated": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_factorial_interaction_audit(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.35m factorial interaction audit")
    expected = build_factorial_interaction_audit(
        t20_35l_result_identity=payload.get("t20_35l_result_identity_sha256"),
        condition_metrics=payload.get("condition_metrics"),
        source_gate_b_passed=payload.get("gate_b_passed"),
    )
    if payload != expected:
        raise ValueError("T20.35m factorial interaction audit drifted")


def build_live_factorial_interaction_audit(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root)
    sources = load_t20_35l_sources(repo_root=root)
    spec = sources["noise_mask_spec"]
    permit = sources["noise_mask_permit"]
    attempt = load_strict_json(root / T20_35L_ATTEMPT_PATH)
    verify_t20_35l_attempt(
        attempt,
        spec_identity=spec["identity_sha256"],
        permit_identity=permit["identity_sha256"],
    )
    result = load_strict_json(root / T20_35L_RESULT_PATH)
    target = sources["residual_report"]["target_action_chunk"]
    verify_t20_35l_result(
        result,
        spec=spec,
        permit=permit,
        attempt=attempt,
        source_result=sources["source_result"],
        target_chunk=target,
    )
    if result["identity_sha256"] != EXPECTED_T20_35L_RESULT_IDENTITY:
        raise ValueError("T20.35m expected T20.35l result identity drifted")
    metrics = [
        {
            "noise_condition": row["noise_condition"],
            **{metric: row[metric] for metric in METRICS},
            "all_decoded_chunks_within_threshold": row[
                "all_decoded_chunks_within_threshold"
            ],
        }
        for row in result["condition_evaluations"]
    ]
    audit = build_factorial_interaction_audit(
        t20_35l_result_identity=result["identity_sha256"],
        condition_metrics=metrics,
        source_gate_b_passed=result["gate_b_passed"],
    )
    verify_factorial_interaction_audit(audit)
    return audit


def write_audit(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    audit = build_live_factorial_interaction_audit(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / AUDIT_PATH, audit)
    return audit


def verify_audit_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected = build_live_factorial_interaction_audit(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / AUDIT_PATH)
    verify_factorial_interaction_audit(archived)
    if archived != expected:
        raise ValueError("T20.35m archived audit drifted from T20.35l")
    return archived


def _normalize_conditions(value: Any) -> list[dict[str, Any]]:
    expected_keys = {"noise_condition", *METRICS, "all_decoded_chunks_within_threshold"}
    if (
        not isinstance(value, list)
        or [row.get("noise_condition") for row in value if isinstance(row, dict)]
        != list(ALL_NOISE_CONDITIONS)
    ):
        raise ValueError("T20.35m condition order or coverage drifted")
    normalized = []
    for source in value:
        if not isinstance(source, dict) or set(source) != expected_keys:
            raise ValueError("T20.35m condition metric schema drifted")
        if source["all_decoded_chunks_within_threshold"] is not False:
            raise ValueError("T20.35m source unexpectedly passes Gate B")
        row = {
            "noise_condition": source["noise_condition"],
            "all_decoded_chunks_within_threshold": False,
        }
        for metric in METRICS:
            item = source[metric]
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError(f"T20.35m {metric} is invalid")
            number = float(item)
            if not math.isfinite(number) or number < 0:
                raise ValueError(f"T20.35m {metric} is invalid")
            row[metric] = number
        normalized.append(row)
    return normalized


def _sha(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"T20.35m {label} must be lowercase SHA-256")
