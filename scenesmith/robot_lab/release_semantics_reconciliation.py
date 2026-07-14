"""Fail-closed T20.10 force-bearing release-semantics decision."""

from __future__ import annotations

from typing import Any

from scenesmith.robot_lab.act_grasp_closed_loop import (
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
)
from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes
from scenesmith.robot_lab.model_bakeoff_evaluation import GATE_NAMES


SCHEMA_VERSION = "scenesmith.t20_10_release_semantics_reconciliation.v1"
ROLLOUT_SCHEMA_VERSION = "scenesmith.t20_10_release_semantics_oracle_rollout.v1"
EVIDENCE_MODE = "source_expert_oracle_force_bearing_release_semantics"


def build_release_semantics_reconciliation(
    *,
    source_t20_9_ref: dict[str, Any],
    source_refs: dict[str, Any],
    t20_7_evaluation_ref: dict[str, Any],
    oracle_rollout: dict[str, Any],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    payload = sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.10",
            "evidence_mode": EVIDENCE_MODE,
            "source_t20_9_ref": source_t20_9_ref,
            "source_refs": source_refs,
            "t20_7_evaluation_ref": t20_7_evaluation_ref,
            "corrected_oracle_rollout": oracle_rollout,
            "diagnostics": diagnostics,
            "release_semantics": {
                "release_clearance_basis": FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
                "release_settle_final_geometry_clear": diagnostics.get(
                    "release_settle_final_geometry_clear"
                ),
                "release_settle_final_force_bearing_contact_clear": diagnostics.get(
                    "release_settle_final_force_bearing_contact_clear"
                ),
                "retreat_final_geometry_clear": diagnostics.get(
                    "retreat_final_contact_clear"
                ),
                "release_gate_margin": oracle_rollout.get("gate_margins", {}).get(
                    "release_final_contact_clear"
                ),
                "retreat_gate_margin": oracle_rollout.get("gate_margins", {}).get(
                    "retreat_final_contact_clear"
                ),
            },
            "terminal_diagnostic_outcome": "source_oracle_passes_reconciled_release_semantics",
            "historical_evidence_reinterpreted": False,
            "model_loaded": False,
            "model_inference_executed": False,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    verify_release_semantics_reconciliation(payload)
    return payload


def verify_release_semantics_reconciliation(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.10 release-semantics reconciliation")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != "T20.10"
        or payload.get("evidence_mode") != EVIDENCE_MODE
    ):
        raise ValueError("T20.10 release-semantics identity drifted")
    rollout = payload.get("corrected_oracle_rollout", {})
    verify_signed_payload(rollout, label="T20.10 corrected source oracle rollout")
    expected_rollout = {
        "schema_version": ROLLOUT_SCHEMA_VERSION,
        "task_id": "T20.10",
        "evidence_mode": EVIDENCE_MODE,
        "policy_label": "source_expert_oracle",
        "seed": 2,
        "frame_count": 244,
        "release_clearance_basis": FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        "terminal_outcome": "strict_success",
        "simulation_semantic_strict_success": True,
        "policy_controls_owned_all_frames": True,
        "projected_action_frame_count": 0,
        "active_assist_frame_count": 0,
    }
    if any(rollout.get(name) != value for name, value in expected_rollout.items()):
        raise ValueError("T20.10 corrected oracle rollout drifted")
    validate_rendered_keyframes(rollout.get("rendered_keyframes"))
    margins = rollout.get("gate_margins", {})
    if (
        set(margins) != GATE_NAMES
        or any(row.get("passed") is not True for row in margins.values())
        or rollout.get("failed_gate_margins") != []
        or rollout.get("maximum_anchor_lift_m", 0.0) < 0.035
    ):
        raise ValueError("T20.10 corrected strict gates did not all pass")
    diagnostics = payload.get("diagnostics", {})
    if (
        diagnostics.get("frame_count") != 244
        or diagnostics.get("first_execution_divergence") is not None
        or diagnostics.get("execution_adapter_reproduced_source_trajectory") is not True
        or diagnostics.get("source_declared_strict_success") is not True
        or diagnostics.get("oracle_strict_success") is not True
        or diagnostics.get("source_vs_acceptance_semantic_mismatch") is not False
        or diagnostics.get("release_clearance_basis")
        != FORCE_BEARING_RELEASE_CLEARANCE_BASIS
        or diagnostics.get("release_settle_final_geometry_clear") is not False
        or diagnostics.get("release_settle_final_force_bearing_contact_clear") is not True
        or diagnostics.get("retreat_final_contact_clear") is not True
    ):
        raise ValueError("T20.10 corrected source-oracle diagnostics drifted")
    release = payload.get("release_semantics", {})
    expected_release = {
        "release_clearance_basis": FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        "release_settle_final_geometry_clear": False,
        "release_settle_final_force_bearing_contact_clear": True,
        "retreat_final_geometry_clear": True,
        "release_gate_margin": {
            "measured": 1,
            "threshold": 1,
            "comparison": "==",
            "margin": 0.0,
            "passed": True,
        },
        "retreat_gate_margin": {
            "measured": 1,
            "threshold": 1,
            "comparison": "==",
            "margin": 0.0,
            "passed": True,
        },
    }
    if release != expected_release:
        raise ValueError("T20.10 release/retreat semantic decision drifted")
    source_t20_9 = payload.get("source_t20_9_ref", {})
    source_episode = payload.get("source_refs", {}).get("episode", {})
    if (
        not _is_sha256(source_t20_9.get("identity_sha256"))
        or not _is_sha256(source_t20_9.get("file_sha256"))
        or source_episode.get("source_action_sequence_sha256")
        != rollout.get("policy_action_sequence_sha256")
        or payload.get("t20_7_evaluation_ref", {}).get("strict_success_count") != 0
    ):
        raise ValueError("T20.10 source evidence linkage drifted")
    required_false = (
        "historical_evidence_reinterpreted",
        "model_loaded",
        "model_inference_executed",
        "optimizer_training",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if any(payload.get(name) is not False for name in required_false):
        raise ValueError("T20.10 authority or historical-evidence field drifted")
    if (
        payload.get("terminal_diagnostic_outcome")
        != "source_oracle_passes_reconciled_release_semantics"
    ):
        raise ValueError("T20.10 terminal diagnostic outcome drifted")


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
