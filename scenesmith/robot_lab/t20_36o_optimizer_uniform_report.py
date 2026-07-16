"""Model-free strict-uniform report supplement for T20.36o."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36o_baseline_capture import score_action_tensor
from scenesmith.robot_lab.t20_36o_bounded_optimizer_run import (
    verify_probe_artifact,
    verify_result,
)


REPORT_PATH = Path(
    "configurations/robot_lab/t20_36o_optimizer_uniform_report.json"
)
SCHEMA_VERSION = "scenesmith.t20_36o_optimizer_uniform_report.v1"
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)


def build_uniform_report(
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    optimizer_spec: dict[str, Any],
    bridge_spec: dict[str, Any],
    probe_artifact: dict[str, Any],
    result: dict[str, Any],
    source_gate_baseline_objective_mean: float,
) -> dict[str, Any]:
    verify_probe_artifact(
        probe_artifact,
        attempt=attempt,
        permit=permit,
        optimizer_spec=optimizer_spec,
        bridge_spec=bridge_spec,
        source_gate_baseline_objective_mean=source_gate_baseline_objective_mean,
    )
    verify_result(
        result,
        attempt=attempt,
        permit=permit,
        optimizer_spec=optimizer_spec,
        probe_artifact=probe_artifact,
    )
    threshold = bridge_spec["acceptance"][
        "strict_uniform_maximum_absolute_error_rad_report_only"
    ]
    if threshold != 0.05:
        raise ValueError("T20.36o strict uniform report threshold drifted")
    thresholds = {
        phase: {joint: threshold for joint in JOINT_NAMES}
        for phase in ("reach", "grasp")
    }
    windows = {row["start_frame"]: row for row in bridge_spec["source_windows"]}
    probe_reports = []
    for probe in probe_artifact["probes"]:
        rows = []
        for tensor_row in probe["rows"]:
            if tensor_row["repeat_index"] != 0:
                continue
            window = windows[tensor_row["start_frame"]]
            score = score_action_tensor(
                tensor=tensor_row["decoded_action_chunk"],
                target=window["padded_target_action_mujoco_rad"],
                executed_mask=window["executed_mask"],
                thresholds=thresholds,
            )
            rows.append(
                {
                    "start_frame": tensor_row["start_frame"],
                    "executed_length": tensor_row["executed_length"],
                    "inference_seed": tensor_row["inference_seed"],
                    "decoded_action_chunk_sha256": tensor_row[
                        "decoded_action_chunk_sha256"
                    ],
                    **score,
                }
            )
        probe_reports.append(
            {
                "update_count": probe["update_count"],
                "strict_uniform_report_only_passed": all(
                    row["passed"] for row in rows
                ),
                "passing_probe_count": sum(row["passed"] for row in rows),
                "total_violation_count": sum(
                    row["violation_count"] for row in rows
                ),
                "maximum_absolute_error_rad": max(
                    row["maximum_absolute_error_rad"] for row in rows
                ),
                "rows": rows,
            }
        )
    selected = probe_reports[-1]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.36o",
            "scope": "report_only_strict_uniform_metric_supplement",
            "attempt_identity_sha256": attempt["identity_sha256"],
            "training_permit_identity_sha256": permit["identity_sha256"],
            "optimizer_spec_identity_sha256": optimizer_spec["identity_sha256"],
            "bridge_spec_identity_sha256": bridge_spec["identity_sha256"],
            "probe_artifact_identity_sha256": probe_artifact["identity_sha256"],
            "optimizer_result_identity_sha256": result["identity_sha256"],
            "strict_uniform_maximum_absolute_error_rad": threshold,
            "probe_reports": probe_reports,
            "selected_update_count": selected["update_count"],
            "selected_strict_uniform_report_only_passed": selected[
                "strict_uniform_report_only_passed"
            ],
            "selected_passing_probe_count": selected["passing_probe_count"],
            "selected_total_violation_count": selected["total_violation_count"],
            "selected_maximum_absolute_error_rad": selected[
                "maximum_absolute_error_rad"
            ],
            "unexecuted_tail_scored": False,
            "amended_gate_decision_changed": False,
            "threshold_changed": False,
            "retry_authorized": False,
            "gate_c_authorized": False,
            "gate_c_executed": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_uniform_report(
    payload: dict[str, Any],
    *,
    attempt: dict[str, Any],
    permit: dict[str, Any],
    optimizer_spec: dict[str, Any],
    bridge_spec: dict[str, Any],
    probe_artifact: dict[str, Any],
    result: dict[str, Any],
    source_gate_baseline_objective_mean: float,
) -> None:
    verify_signed_payload(payload, label="T20.36o strict uniform report")
    expected = build_uniform_report(
        attempt=attempt,
        permit=permit,
        optimizer_spec=optimizer_spec,
        bridge_spec=bridge_spec,
        probe_artifact=probe_artifact,
        result=result,
        source_gate_baseline_objective_mean=source_gate_baseline_objective_mean,
    )
    if payload != expected:
        raise ValueError("T20.36o strict uniform report drifted")
