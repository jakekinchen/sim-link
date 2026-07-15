"""Model-free top-two-channel semantic correction for T20.35e."""

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
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (
    PERMIT_PATH,
    REPORT_PATH,
    SPEC_PATH,
    verify_evaluation_permit,
    verify_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CORRECTION_PATH = Path(
    "configurations/robot_lab/t20_35e_top_two_channel_correction.json"
)
SCHEMA_VERSION = "scenesmith.t20_35e_top_two_channel_correction.v1"
EXPECTED_REPORT_IDENTITY = (
    "13b08e70a805a8b176b9f9a7c0e37843f7267d7918f82aeb523551e2dadf1fbe"
)
TOP_TWO_CONCENTRATION_THRESHOLD = 0.75
SINGLE_JOINT_THRESHOLD = 0.50
BOUNDARY_THRESHOLD = 0.60


def build_correction(
    *,
    source_report_identity: str,
    threshold_exceedance_count: int,
    per_joint_summary: list[dict[str, Any]],
    boundary_exceedance_fraction: float,
    original_classification: str,
    original_selected_next_hypothesis: str,
) -> dict[str, Any]:
    _sha(source_report_identity, "source report identity")
    if isinstance(threshold_exceedance_count, bool) or not isinstance(threshold_exceedance_count, int) or threshold_exceedance_count <= 0:
        raise ValueError("T20.35e threshold exceedance count is invalid")
    boundary = _fraction(boundary_exceedance_fraction, "boundary fraction")
    if not isinstance(per_joint_summary, list) or len(per_joint_summary) != 6:
        raise ValueError("T20.35e per-joint summary is incomplete")
    rows = []
    for index, row in enumerate(per_joint_summary):
        if (
            not isinstance(row, dict)
            or row.get("joint_index") != index
            or not isinstance(row.get("joint_name"), str)
            or isinstance(row.get("threshold_exceedance_count"), bool)
            or not isinstance(row.get("threshold_exceedance_count"), int)
            or row["threshold_exceedance_count"] < 0
        ):
            raise ValueError("T20.35e per-joint count row drifted")
        rows.append(
            {
                "joint_index": index,
                "joint_name": row["joint_name"],
                "threshold_exceedance_count": row[
                    "threshold_exceedance_count"
                ],
            }
        )
    if sum(row["threshold_exceedance_count"] for row in rows) != threshold_exceedance_count:
        raise ValueError("T20.35e per-joint counts do not sum to total")
    ranked = sorted(
        rows,
        key=lambda row: (-row["threshold_exceedance_count"], row["joint_index"]),
    )
    top_one_count = ranked[0]["threshold_exceedance_count"]
    top_two_count = top_one_count + ranked[1]["threshold_exceedance_count"]
    top_one_fraction = top_one_count / threshold_exceedance_count
    top_two_fraction = top_two_count / threshold_exceedance_count
    if boundary >= BOUNDARY_THRESHOLD:
        corrected = "chunk_boundary_residual"
    elif top_one_fraction >= SINGLE_JOINT_THRESHOLD:
        corrected = "joint_specific_residual"
    elif top_two_fraction >= TOP_TWO_CONCENTRATION_THRESHOLD:
        corrected = "multi_joint_output_channel_concentrated"
    else:
        corrected = "distributed_decoding_residual"
    route = {
        "chunk_boundary_residual": "inspect_chunk_boundary_cadence_or_time_conditioning",
        "joint_specific_residual": "audit_normalized_space_residual_and_target_saturation_for_top_channels",
        "multi_joint_output_channel_concentrated": "audit_normalized_space_residual_and_target_saturation_for_top_channels",
        "distributed_decoding_residual": "inspect_decoder_sampling_or_action_gate_calibration",
    }[corrected]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.35e",
            "scope": "model_free_top_two_channel_residual_semantic_correction",
            "source_t20_35d_report_identity_sha256": source_report_identity,
            "threshold_exceedance_count": threshold_exceedance_count,
            "per_joint_exceedance_counts": rows,
            "ranked_joint_exceedance_counts": ranked,
            "boundary_exceedance_fraction": boundary,
            "single_joint_concentration_threshold": SINGLE_JOINT_THRESHOLD,
            "top_two_channel_concentration_threshold": TOP_TWO_CONCENTRATION_THRESHOLD,
            "boundary_concentration_threshold": BOUNDARY_THRESHOLD,
            "top_one_channel": ranked[0],
            "top_one_channel_fraction": top_one_fraction,
            "top_two_channels": ranked[:2],
            "top_two_channel_exceedance_count": top_two_count,
            "top_two_channel_exceedance_fraction": top_two_fraction,
            "original_residual_classification": original_classification,
            "original_selected_next_hypothesis": original_selected_next_hypothesis,
            "corrected_residual_classification": corrected,
            "selected_next_hypothesis": route,
            "source_report_mutated": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_training": False,
            "checkpoint_read": False,
            "checkpoint_mutated": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_correction(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.35e top-two correction")
    expected = build_correction(
        source_report_identity=payload.get("source_t20_35d_report_identity_sha256"),
        threshold_exceedance_count=payload.get("threshold_exceedance_count"),
        per_joint_summary=payload.get("per_joint_exceedance_counts"),
        boundary_exceedance_fraction=payload.get("boundary_exceedance_fraction"),
        original_classification=payload.get("original_residual_classification"),
        original_selected_next_hypothesis=payload.get(
            "original_selected_next_hypothesis"
        ),
    )
    if payload != expected:
        raise ValueError("T20.35e top-two correction drifted")


def build_live_correction(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    spec = load_strict_json(root / SPEC_PATH)
    permit = load_strict_json(root / PERMIT_PATH)
    verify_evaluation_permit(permit, spec=spec)
    report = load_strict_json(root / REPORT_PATH)
    verify_report(report, spec=spec, permit=permit)
    if report["identity_sha256"] != EXPECTED_REPORT_IDENTITY:
        raise ValueError("T20.35e source report identity drifted")
    correction = build_correction(
        source_report_identity=report["identity_sha256"],
        threshold_exceedance_count=report["threshold_exceedance_count"],
        per_joint_summary=report["per_joint_summary"],
        boundary_exceedance_fraction=report["boundary_exceedance_fraction"],
        original_classification=report["residual_classification"],
        original_selected_next_hypothesis=report["selected_next_hypothesis"],
    )
    verify_correction(correction)
    return correction


def write_correction(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    correction = build_live_correction(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / CORRECTION_PATH, correction)
    return correction


def verify_correction_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected = build_live_correction(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / CORRECTION_PATH)
    verify_correction(archived)
    if archived != expected:
        raise ValueError("T20.35e archived correction drifted from report")
    return archived


def _fraction(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"T20.35e {label} must be a finite fraction")
    return float(value)


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"T20.35e {label} must be lowercase SHA-256")
