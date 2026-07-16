"""Model-free correction manifest and optimizer specification for T20.36o."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (
    RESULT_PATH as SOURCE_RESULT_PATH,
    SPEC_PATH as SOURCE_SPEC_PATH,
)
from scenesmith.robot_lab.t20_36o_baseline_capture import (
    BASELINE_PERMIT_PATH,
    RESULT_PATH as BASELINE_RESULT_PATH,
    TENSOR_PATH,
    TRACKED_ATTEMPT_PATH,
    TRAJECTORY_PATH,
    decode_trajectory_matrix,
    verify_tracked_result,
)
from scenesmith.robot_lab.t20_36o_episode_bridge_design import (
    SPEC_PATH as BRIDGE_SPEC_PATH,
    verify_bridge_spec_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(
    "configurations/robot_lab/t20_36o_bounded_optimizer_spec.json"
)
RETENTION_RECEIPT_PATH = Path(
    "configurations/robot_lab/t20_36o_baseline_capture_retention_receipt.json"
)
SCHEMA_VERSION = "scenesmith.t20_36o_bounded_optimizer_spec.v1"
EXPECTED_BRIDGE_IDENTITY = (
    "8294c63be101dbb1ea3536d2b2da1447d23ca9aa71d2145eb501452547c30c0c"
)
EXPECTED_BASELINE_RESULT_IDENTITY = (
    "e653742885cc086219cb08a36b84606dbc066941b8751fcc890bf8897c0b2e97"
)
EXPECTED_TRAJECTORY_IDENTITY = (
    "202ace386bdb05a8888d887a31b83e6335c836e30da145a0d444a813365b680b"
)
EXPECTED_RETENTION_RECEIPT_IDENTITY = (
    "1154d5244fbe65f90d30c6e2ad0e39b677f2010dd7051157579fa7bfd93765e7"
)
TARGET_HORIZON = 50
ACTIVE_ACTION_DIMENSIONS = 6
MAXIMUM_ACTION_DIMENSIONS = 32
CORRECTION_EXAMPLE_COUNT = 250


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    bridge = verify_bridge_spec_file(repo_root=root)
    permit = load_strict_json(root / BASELINE_PERMIT_PATH)
    attempt = load_strict_json(root / TRACKED_ATTEMPT_PATH)
    tensors = load_strict_json(root / TENSOR_PATH)
    trajectories = load_strict_json(root / TRAJECTORY_PATH)
    baseline_result = load_strict_json(root / BASELINE_RESULT_PATH)
    source_result = load_strict_json(root / SOURCE_RESULT_PATH)
    source_spec = load_strict_json(root / SOURCE_SPEC_PATH)
    receipt = load_strict_json(root / RETENTION_RECEIPT_PATH)
    verify_tracked_result(
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensors,
        trajectory_artifact=trajectories,
        result=baseline_result,
        bridge_spec=bridge,
        source_result=source_result,
    )
    verify_signed_payload(source_spec, label="T20.36o optimizer source spec")
    verify_signed_payload(receipt, label="T20.36o optimizer retention receipt")
    if (
        bridge.get("identity_sha256") != EXPECTED_BRIDGE_IDENTITY
        or baseline_result.get("identity_sha256")
        != EXPECTED_BASELINE_RESULT_IDENTITY
        or trajectories.get("identity_sha256") != EXPECTED_TRAJECTORY_IDENTITY
        or receipt.get("identity_sha256") != EXPECTED_RETENTION_RECEIPT_IDENTITY
        or baseline_result.get("amended_bridge_gate_passed") is not False
        or baseline_result.get("decision")
        != "retain_trajectories_compose_separate_optimizer_authority"
        or receipt.get("result_identity_sha256")
        != baseline_result.get("identity_sha256")
        or receipt.get("ignored_run_summary_required_for_rescore") is not False
    ):
        raise ValueError("T20.36o optimizer route source drifted")
    _verify_retention_receipt(receipt, repo_root=root)
    stats_path = root / source_spec["dataset_stats_path"]
    if (
        hashlib.sha256(stats_path.read_bytes()).hexdigest()
        != source_spec["dataset_stats_file_sha256"]
    ):
        raise ValueError("T20.36o optimizer dataset statistics drifted")
    stats = load_strict_json(stats_path)
    return {
        "bridge_spec": bridge,
        "baseline_permit": permit,
        "baseline_attempt": attempt,
        "baseline_tensors": tensors,
        "baseline_trajectories": trajectories,
        "baseline_result": baseline_result,
        "source_result": source_result,
        "source_spec": source_spec,
        "retention_receipt": receipt,
        "dataset_stats": stats,
        "dataset_stats_path": source_spec["dataset_stats_path"],
    }


def build_normalized_targets(
    *, bridge_spec: dict[str, Any], dataset_stats: dict[str, Any]
) -> list[dict[str, Any]]:
    verify_signed_payload(bridge_spec, label="T20.36o target bridge spec")
    action_stats = dataset_stats.get("action")
    if not isinstance(action_stats, dict):
        raise ValueError("T20.36o action statistics are missing")
    q01 = _float32_vector(action_stats.get("q01"), label="action q01")
    q99 = _float32_vector(action_stats.get("q99"), label="action q99")
    denom = q99 - q01
    if np.any(denom == np.float32(0.0)):
        raise ValueError("T20.36o action quantile range is zero")
    rows = []
    for window in bridge_spec.get("source_windows", []):
        raw = np.asarray(
            window.get("padded_target_action_lerobot_deg"), dtype=np.float32
        )
        if raw.shape != (TARGET_HORIZON, ACTIVE_ACTION_DIMENSIONS):
            raise ValueError("T20.36o padded target action shape drifted")
        normalized_active = (
            np.float32(2.0) * (raw - q01) / denom - np.float32(1.0)
        )
        normalized = np.pad(
            normalized_active,
            ((0, 0), (0, MAXIMUM_ACTION_DIMENSIONS - ACTIVE_ACTION_DIMENSIONS)),
            constant_values=np.float32(0.0),
        ).astype(np.float32)
        values = normalized.astype(float).tolist()
        rows.append(
            {
                "start_frame": window["start_frame"],
                "executed_length": window["executed_length"],
                "normalized_padded_target_sha256": _canonical_sha(values),
                "normalized_padded_target": values,
            }
        )
    if [row["start_frame"] for row in rows] != [0, 50, 100, 150, 200]:
        raise ValueError("T20.36o normalized target start coverage drifted")
    return rows


def build_optimizer_spec(*, sources: dict[str, Any]) -> dict[str, Any]:
    bridge = sources["bridge_spec"]
    trajectories = sources["baseline_trajectories"]
    normalized_targets = build_normalized_targets(
        bridge_spec=bridge,
        dataset_stats=sources["dataset_stats"],
    )
    if (
        normalized_targets[0]["normalized_padded_target_sha256"]
        != sources["source_spec"]["normalized_padded_target_sha256"]
    ):
        raise ValueError("T20.36o start-zero target normalization drifted")
    examples = _build_correction_examples(
        bridge_spec=bridge,
        trajectories=trajectories,
        normalized_targets=normalized_targets,
    )
    schedule = bridge["correction_schedule"]
    schedule_order = schedule["example_order"]
    observed_order = [
        {
            "example_index": row["correction_example_index"],
            "chunk_start_frame": row["start_frame"],
            "inference_seed": row["inference_seed"],
            "denoise_step_index": row["step_index"],
            "time": row["time"],
        }
        for row in examples
    ]
    if (
        observed_order != schedule_order
        or _canonical_sha(observed_order) != schedule["example_order_sha256"]
        or len(examples) != CORRECTION_EXAMPLE_COUNT
    ):
        raise ValueError("T20.36o correction example order drifted")
    target_summary = [
        {key: row[key] for key in row if key != "normalized_padded_target"}
        for row in normalized_targets
    ]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.36o",
            "scope": "one_bounded_retained_path_correction_with_paired_standard_replay",
            "bridge_spec_identity_sha256": bridge["identity_sha256"],
            "baseline_result_identity_sha256": sources["baseline_result"][
                "identity_sha256"
            ],
            "baseline_trajectory_identity_sha256": trajectories[
                "identity_sha256"
            ],
            "retention_receipt_identity_sha256": sources[
                "retention_receipt"
            ]["identity_sha256"],
            "source_checkpoint_identity_sha256": bridge[
                "source_checkpoint_identity_sha256"
            ],
            "source_training_spec_identity_sha256": sources["source_spec"][
                "identity_sha256"
            ],
            "dataset_stats_path": sources["dataset_stats_path"],
            "dataset_stats_file_sha256": sources["source_spec"][
                "dataset_stats_file_sha256"
            ],
            "target_normalization": {
                "mode": "QUANTILES",
                "formula": "2*(action-q01)/(q99-q01)-1_then_zero_pad_to_32",
                "float_dtype": "float32",
                "start_zero_parity_sha256": normalized_targets[0][
                    "normalized_padded_target_sha256"
                ],
                "targets": target_summary,
            },
            "correction_example_count": len(examples),
            "correction_examples_sha256": _canonical_sha(examples),
            "correction_examples": examples,
            "correction_schedule": schedule,
            "baseline_probe_update_count": 0,
            "optimizer_update_count_ceiling": schedule[
                "optimizer_update_count_ceiling"
            ],
            "optimizer_creation_requires_separate_permit": True,
            "first_complete_confirmed_pass_stops_training": True,
            "negative_at_ceiling_stops_without_retry": True,
            "gate_c_requires_separate_authority_after_pass": True,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "threshold_changed": False,
            "gate_c_authorized": False,
            "gate_c_executed": False,
            "policy_track_selected": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_optimizer_spec(
    payload: dict[str, Any], *, sources: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36o optimizer spec")
    if payload != build_optimizer_spec(sources=sources):
        raise ValueError("T20.36o optimizer spec drifted")


def materialize_correction_examples(
    *, spec: dict[str, Any], sources: dict[str, Any]
) -> list[dict[str, Any]]:
    verify_optimizer_spec(spec, sources=sources)
    targets = {
        row["start_frame"]: row["normalized_padded_target"]
        for row in build_normalized_targets(
            bridge_spec=sources["bridge_spec"],
            dataset_stats=sources["dataset_stats"],
        )
    }
    trajectory_rows = {
        (row["start_frame"], row["inference_seed"]): row
        for row in sources["baseline_trajectories"]["rows"]
        if row["repeat_index"] == 0
    }
    output = []
    for manifest in spec["correction_examples"]:
        trajectory = trajectory_rows[
            (manifest["start_frame"], manifest["inference_seed"])
        ]
        state = decode_trajectory_matrix(
            trajectory["steps"][manifest["step_index"]], field="state"
        )
        target = targets[manifest["start_frame"]]
        time = manifest["time"]
        noise = [
            [
                (state[timestep][dimension] - (1.0 - time) * target[timestep][dimension])
                / time
                for dimension in range(MAXIMUM_ACTION_DIMENSIONS)
            ]
            for timestep in range(TARGET_HORIZON)
        ]
        if _canonical_sha(noise) != manifest["derived_noise_sha256"]:
            raise ValueError("T20.36o materialized correction noise drifted")
        output.append(
            {
                **manifest,
                "derived_noise": noise,
                "normalized_padded_target": target,
            }
        )
    return output


def _build_correction_examples(
    *,
    bridge_spec: dict[str, Any],
    trajectories: dict[str, Any],
    normalized_targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target_by_start = {row["start_frame"]: row for row in normalized_targets}
    window_by_start = {
        row["start_frame"]: row for row in bridge_spec["source_windows"]
    }
    trajectory_rows = [
        row for row in trajectories.get("rows", []) if row.get("repeat_index") == 0
    ]
    if len(trajectory_rows) != 25:
        raise ValueError("T20.36o unique trajectory coverage drifted")
    coefficients = bridge_spec["correction_schedule"][
        "physical_joint_weighting"
    ]["coefficient_by_dimension"]
    if len(coefficients) != MAXIMUM_ACTION_DIMENSIONS:
        raise ValueError("T20.36o correction coefficient coverage drifted")
    examples = []
    for trajectory in trajectory_rows:
        start = trajectory["start_frame"]
        target_row = target_by_start[start]
        target = target_row["normalized_padded_target"]
        mask = window_by_start[start]["executed_mask"]
        executed_length = sum(mask)
        if executed_length != trajectory["executed_length"]:
            raise ValueError("T20.36o correction mask coverage drifted")
        for step_index, step in enumerate(trajectory["steps"]):
            time = _finite(step.get("time"), label="correction time")
            expected_time = 1.0 - step_index / 10
            if time != expected_time or time <= 0.0:
                raise ValueError("T20.36o correction time grid drifted")
            state = decode_trajectory_matrix(step, field="state")
            learned_velocity = decode_trajectory_matrix(
                step, field="learned_velocity"
            )
            reference = [
                [
                    (state[timestep][dimension] - target[timestep][dimension])
                    / time
                    for dimension in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for timestep in range(TARGET_HORIZON)
            ]
            noise = [
                [
                    (
                        state[timestep][dimension]
                        - (1.0 - time) * target[timestep][dimension]
                    )
                    / time
                    for dimension in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for timestep in range(TARGET_HORIZON)
            ]
            squared = [
                [
                    (learned_velocity[timestep][dimension] - reference[timestep][dimension])
                    ** 2
                    for dimension in range(MAXIMUM_ACTION_DIMENSIONS)
                ]
                for timestep in range(TARGET_HORIZON)
            ]
            raw = sum(
                squared[timestep][dimension]
                for timestep in range(TARGET_HORIZON)
                if mask[timestep]
                for dimension in range(ACTIVE_ACTION_DIMENSIONS)
            ) / (executed_length * ACTIVE_ACTION_DIMENSIONS)
            weighted = sum(
                squared[timestep][dimension] * coefficients[dimension]
                for timestep in range(TARGET_HORIZON)
                if mask[timestep]
                for dimension in range(MAXIMUM_ACTION_DIMENSIONS)
            ) / (executed_length * MAXIMUM_ACTION_DIMENSIONS)
            examples.append(
                {
                    "correction_example_index": len(examples),
                    "start_frame": start,
                    "executed_length": executed_length,
                    "inference_seed": trajectory["inference_seed"],
                    "step_index": step_index,
                    "time": time,
                    "source_trajectory_index": trajectory["trajectory_index"],
                    "source_denoise_path_sha256": trajectory[
                        "denoise_path_sha256"
                    ],
                    "state_f32le_sha256": step["state_f32le_sha256"],
                    "learned_velocity_f32le_sha256": step[
                        "learned_velocity_f32le_sha256"
                    ],
                    "normalized_padded_target_sha256": target_row[
                        "normalized_padded_target_sha256"
                    ],
                    "executed_mask_sha256": window_by_start[start][
                        "executed_mask_sha256"
                    ],
                    "derived_noise_sha256": _canonical_sha(noise),
                    "target_velocity_sha256": _canonical_sha(reference),
                    "baseline_raw_correction_objective": _finite_nonnegative(
                        raw, label="baseline raw correction objective"
                    ),
                    "baseline_joint_weighted_correction_objective": _finite_nonnegative(
                        weighted,
                        label="baseline joint-weighted correction objective",
                    ),
                    "time_normalization_weight": bridge_spec[
                        "correction_schedule"
                    ]["time_normalization"]["weight_by_step"][step_index],
                }
            )
    return examples


def _verify_retention_receipt(
    receipt: dict[str, Any], *, repo_root: Path
) -> None:
    for row in receipt.get("artifacts", []):
        path = repo_root / row["path"]
        data = path.read_bytes()
        payload = load_strict_json(path)
        verify_signed_payload(payload, label=f"T20.36o retained {path}")
        if (
            len(data) != row["size_bytes"]
            or hashlib.sha256(data).hexdigest() != row["file_sha256"]
            or payload.get("identity_sha256") != row["identity_sha256"]
            or payload.get("schema_version") != row["schema_version"]
        ):
            raise ValueError("T20.36o retention receipt artifact drifted")


def _float32_vector(value: Any, *, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32)
    if array.shape != (ACTIVE_ACTION_DIMENSIONS,) or not np.isfinite(array).all():
        raise ValueError(f"T20.36o {label} must be finite length 6")
    return array


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _finite(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"T20.36o {label} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"T20.36o {label} must be finite")
    return number


def _finite_nonnegative(value: Any, *, label: str) -> float:
    number = _finite(value, label=label)
    if number < 0.0:
        raise ValueError(f"T20.36o {label} must be nonnegative")
    return number
