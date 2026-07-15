"""Action-quantile postprocessor counterfactual for T20.29."""

from __future__ import annotations

from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.experience_records import JOINT_NAMES
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot
from scenesmith.robot_lab.t20_25_frozen_candidate_localization import CANDIDATE_IDS
from scenesmith.robot_lab.t20_26_frame_zero_variability import SAMPLE_SCHEDULE


SCHEMA_VERSION = "scenesmith.t20_29_quantile_postprocessor_counterfactual.v1"
UNIQUE_SAMPLE_IDS = (
    "same_01",
    "distinct_01",
    "distinct_02",
    "distinct_03",
    "distinct_04",
)
ROUND_TRIP_TOLERANCE_RAD = 1e-8
ACCOUNTING_TOLERANCE_RAD = 0.01


def build_counterfactual(
    *,
    batches: dict[str, dict[str, Any]],
    source_action_rad: list[float],
    clean_stats: dict[str, Any],
    recovery_stats: dict[str, Any],
    clean_stats_sha256: str,
    recovery_stats_sha256: str,
    clean_postprocessor_config_sha256: str,
    recovery_postprocessor_config_sha256: str,
    clean_postprocessor_state_sha256: str,
    recovery_postprocessor_state_sha256: str,
    formula_source_sha256: str,
    t20_27_gate_identity_sha256: str,
    observed_recovery_minus_clean_mae_rad: float,
    _skip_verify: bool = False,
) -> dict[str, Any]:
    _validate_inputs(batches, source_action_rad, clean_stats, recovery_stats)
    for value, label in (
        (clean_stats_sha256, "clean stats"),
        (recovery_stats_sha256, "recovery stats"),
        (clean_postprocessor_config_sha256, "clean postprocessor config"),
        (recovery_postprocessor_config_sha256, "recovery postprocessor config"),
        (clean_postprocessor_state_sha256, "clean postprocessor state"),
        (recovery_postprocessor_state_sha256, "recovery postprocessor state"),
        (formula_source_sha256, "formula source"),
        (t20_27_gate_identity_sha256, "T20.27 gate"),
    ):
        _sha(value, label)
    observed_delta = _finite(observed_recovery_minus_clean_mae_rad, "observed delta")
    source = np.asarray(source_action_rad, dtype=np.float64)
    stats = {"clean_base": clean_stats, "recovery_augmented": recovery_stats}
    rows = []
    for candidate in CANDIDATE_IDS:
        other = "recovery_augmented" if candidate == "clean_base" else "clean_base"
        samples = {row["sample_id"]: row for row in batches[candidate]["samples"]}
        for sample_id in UNIQUE_SAMPLE_IDS:
            sample = samples[sample_id]
            actual = np.asarray(sample["requested_action_rad"], dtype=np.float64)
            own_q01, own_q99 = _quantiles(stats[candidate])
            other_q01, other_q99 = _quantiles(stats[other])
            lerobot_actual = np.asarray(mujoco_to_lerobot(actual), dtype=np.float64)
            normalized = 2.0 * (lerobot_actual - own_q01) / (own_q99 - own_q01) - 1.0
            own_decoded = (normalized + 1.0) * (own_q99 - own_q01) / 2.0 + own_q01
            other_decoded = (
                (normalized + 1.0) * (other_q99 - other_q01) / 2.0 + other_q01
            )
            own_mujoco = np.asarray(lerobot_to_mujoco(own_decoded), dtype=np.float64)
            other_mujoco = np.asarray(
                lerobot_to_mujoco(other_decoded), dtype=np.float64
            )
            round_trip = float(np.max(np.abs(own_mujoco - actual)))
            clipping = float(
                np.max(
                    np.abs(
                        np.asarray(mujoco_to_lerobot(other_mujoco), dtype=np.float64)
                        - other_decoded
                    )
                )
            )
            if round_trip > ROUND_TRIP_TOLERANCE_RAD:
                raise ValueError("T20.29 own-stat round trip exceeded tolerance")
            if clipping > ROUND_TRIP_TOLERANCE_RAD:
                raise ValueError("T20.29 cross-stat counterfactual required clipping")
            rows.append(
                {
                    "candidate_id": candidate,
                    "counterfactual_stats": other,
                    "sample_id": sample_id,
                    "inference_seed": sample["inference_seed"],
                    "actual_source_mae_rad": float(np.mean(np.abs(actual - source))),
                    "counterfactual_source_mae_rad": float(
                        np.mean(np.abs(other_mujoco - source))
                    ),
                    "counterfactual_minus_actual_mae_rad": float(
                        np.mean(np.abs(other_mujoco - source))
                        - np.mean(np.abs(actual - source))
                    ),
                    "own_stat_round_trip_max_abs_error_rad": round_trip,
                    "cross_stat_coordinate_clipping_max_abs_error": clipping,
                    "actual_per_joint_absolute_error_rad": {
                        name: float(value)
                        for name, value in zip(
                            JOINT_NAMES, np.abs(actual - source), strict=True
                        )
                    },
                    "counterfactual_per_joint_absolute_error_rad": {
                        name: float(value)
                        for name, value in zip(
                            JOINT_NAMES, np.abs(other_mujoco - source), strict=True
                        )
                    },
                }
            )
    aggregates = {}
    for candidate in CANDIDATE_IDS:
        selected = [row for row in rows if row["candidate_id"] == candidate]
        actual = np.asarray(
            [
                list(row["actual_per_joint_absolute_error_rad"].values())
                for row in selected
            ]
        )
        counterfactual = np.asarray(
            [
                list(row["counterfactual_per_joint_absolute_error_rad"].values())
                for row in selected
            ]
        )
        aggregates[candidate] = {
            "actual_source_mae_rad": float(np.mean(actual)),
            "counterfactual_source_mae_rad": float(np.mean(counterfactual)),
            "counterfactual_minus_actual_mae_rad": float(
                np.mean(counterfactual) - np.mean(actual)
            ),
            "per_joint_counterfactual_minus_actual_mae_rad": {
                name: float(value)
                for name, value in zip(
                    JOINT_NAMES,
                    np.mean(counterfactual, axis=0) - np.mean(actual, axis=0),
                    strict=True,
                )
            },
        }
    stats_only_delta = aggregates["clean_base"]["counterfactual_minus_actual_mae_rad"]
    residual = observed_delta - stats_only_delta
    result = (
        "postprocessor_quantile_shift_accounts_for_observed_regression_within_tolerance"
        if stats_only_delta > 0.0 and abs(residual) <= ACCOUNTING_TOLERANCE_RAD
        else "postprocessor_quantile_shift_does_not_account_for_observed_regression"
    )
    payload = sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.29",
            "clean_stats_sha256": clean_stats_sha256,
            "recovery_stats_sha256": recovery_stats_sha256,
            "clean_postprocessor_config_sha256": clean_postprocessor_config_sha256,
            "recovery_postprocessor_config_sha256": (
                recovery_postprocessor_config_sha256
            ),
            "clean_postprocessor_state_sha256": clean_postprocessor_state_sha256,
            "recovery_postprocessor_state_sha256": recovery_postprocessor_state_sha256,
            "formula_source_sha256": formula_source_sha256,
            "t20_27_gate_identity_sha256": t20_27_gate_identity_sha256,
            "source_action_rad": source.astype(float).tolist(),
            "quantile_formula": (
                "normalized=2*(x-q01)/(q99-q01)-1; "
                "decoded=(normalized+1)*(q99-q01)/2+q01"
            ),
            "paired_sample_count": len(UNIQUE_SAMPLE_IDS),
            "rows": rows,
            "aggregates": aggregates,
            "observed_recovery_minus_clean_mae_rad": observed_delta,
            "clean_output_recovery_stats_delta_rad": stats_only_delta,
            "accounting_residual_rad": residual,
            "accounting_tolerance_rad": ACCOUNTING_TOLERANCE_RAD,
            "result": result,
            "selected_next_hypothesis": (
                "freeze_nominal_action_quantiles_during_recovery_supervision_ablation"
                if result.startswith("postprocessor_quantile_shift_accounts")
                else "audit_state_preprocessor_and_adapter_training_effects"
            ),
            "postprocessor_only_counterfactual": True,
            "full_training_effect_isolated": False,
            "model_inference_executed": False,
            "action_applied": False,
            "closed_loop_rollout_executed": False,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    if not _skip_verify:
        verify_counterfactual(
            payload,
            batches=batches,
            source_action_rad=source_action_rad,
            clean_stats=clean_stats,
            recovery_stats=recovery_stats,
            clean_stats_sha256=clean_stats_sha256,
            recovery_stats_sha256=recovery_stats_sha256,
            clean_postprocessor_config_sha256=clean_postprocessor_config_sha256,
            recovery_postprocessor_config_sha256=(
                recovery_postprocessor_config_sha256
            ),
            clean_postprocessor_state_sha256=clean_postprocessor_state_sha256,
            recovery_postprocessor_state_sha256=recovery_postprocessor_state_sha256,
            formula_source_sha256=formula_source_sha256,
            t20_27_gate_identity_sha256=t20_27_gate_identity_sha256,
            observed_recovery_minus_clean_mae_rad=observed_delta,
        )
    return payload


def verify_counterfactual(
    payload: dict[str, Any],
    *,
    batches: dict[str, dict[str, Any]],
    source_action_rad: list[float],
    clean_stats: dict[str, Any],
    recovery_stats: dict[str, Any],
    clean_stats_sha256: str,
    recovery_stats_sha256: str,
    clean_postprocessor_config_sha256: str,
    recovery_postprocessor_config_sha256: str,
    clean_postprocessor_state_sha256: str,
    recovery_postprocessor_state_sha256: str,
    formula_source_sha256: str,
    t20_27_gate_identity_sha256: str,
    observed_recovery_minus_clean_mae_rad: float,
) -> None:
    verify_signed_payload(payload, label="T20.29 quantile counterfactual")
    expected = build_counterfactual(
        batches=batches,
        source_action_rad=source_action_rad,
        clean_stats=clean_stats,
        recovery_stats=recovery_stats,
        clean_stats_sha256=clean_stats_sha256,
        recovery_stats_sha256=recovery_stats_sha256,
        clean_postprocessor_config_sha256=clean_postprocessor_config_sha256,
        recovery_postprocessor_config_sha256=recovery_postprocessor_config_sha256,
        clean_postprocessor_state_sha256=clean_postprocessor_state_sha256,
        recovery_postprocessor_state_sha256=recovery_postprocessor_state_sha256,
        formula_source_sha256=formula_source_sha256,
        t20_27_gate_identity_sha256=t20_27_gate_identity_sha256,
        observed_recovery_minus_clean_mae_rad=(
            observed_recovery_minus_clean_mae_rad
        ),
        _skip_verify=True,
    )
    if payload != expected:
        raise ValueError("T20.29 counterfactual drifted from stats/action evidence")


def _validate_inputs(
    batches: dict[str, dict[str, Any]],
    source_action: list[float],
    clean_stats: dict[str, Any],
    recovery_stats: dict[str, Any],
) -> None:
    if set(batches) != set(CANDIDATE_IDS):
        raise ValueError("T20.29 candidate coverage drifted")
    source = np.asarray(source_action, dtype=np.float64)
    if source.shape != (6,) or not np.isfinite(source).all():
        raise ValueError("T20.29 source action is malformed")
    expected = [(row[0], row[2]) for row in SAMPLE_SCHEDULE]
    for candidate, batch in batches.items():
        actual = [(row["sample_id"], row["inference_seed"]) for row in batch["samples"]]
        if actual != expected:
            raise ValueError(f"T20.29 {candidate} sample order drifted")
        for row in batch["samples"]:
            _vector(row.get("requested_action_rad"), f"{candidate} requested action")
    _quantiles(clean_stats)
    _quantiles(recovery_stats)


def _quantiles(stats: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    q01 = np.asarray(stats.get("q01"), dtype=np.float64)
    q99 = np.asarray(stats.get("q99"), dtype=np.float64)
    if (
        q01.shape != (6,)
        or q99.shape != (6,)
        or not np.isfinite([q01, q99]).all()
    ):
        raise ValueError("T20.29 action quantiles are malformed")
    if np.any(q99 - q01 <= 0.0):
        raise ValueError("T20.29 action quantile span is non-positive")
    return q01, q99


def _finite(value: Any, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"T20.29 {label} must be finite")
    return float(value)


def _vector(value: Any, label: str) -> np.ndarray:
    vector = np.asarray(value, dtype=np.float64)
    if vector.shape != (6,) or not np.isfinite(vector).all():
        raise ValueError(f"T20.29 {label} must be a finite six-vector")
    return vector


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError(f"T20.29 {label} must be lowercase SHA-256")
    return value
