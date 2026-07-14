"""Fail-closed T20.7 closed-loop evidence and comparison gate."""

from __future__ import annotations

import base64
import hashlib
import io
import math

from pathlib import Path
from typing import Any

from PIL import Image

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload
from scenesmith.robot_lab.model_bakeoff import MODEL_ORDER


SCHEMA_VERSION = "scenesmith.t20_7_model_closed_loop.v1"
GATE_SCHEMA_VERSION = "scenesmith.t20_7_model_evaluation_gate.v1"
GATE_NAMES = {
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
}


def verify_model_closed_loop_result(
    payload: dict[str, Any],
    plan: dict[str, Any],
    training_result: dict[str, Any],
    *,
    training_result_file_sha256: str,
) -> None:
    """Verify one observed rollout while retaining truthful negative outcomes."""

    verify_signed_payload(payload, label="T20.7 model closed-loop result")
    model_id = payload.get("model_id")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "task_id": "T20.7",
        "model_id": training_result["model_id"],
        "policy_label": training_result["model_id"],
        "evidence_mode": "held_out_seed_equal_sample_four_model_bakeoff_mujoco",
        "source_plan_identity_sha256": plan["identity_sha256"],
        "source_training_result_identity_sha256": training_result[
            "identity_sha256"
        ],
        "training_run_summary_sha256": training_result_file_sha256,
        "seed": plan["evaluation_contract"]["held_out_episode_seed"],
        "frame_count": plan["evaluation_contract"]["frame_count"],
    }
    if model_id not in MODEL_ORDER or any(
        payload.get(key) != value for key, value in expected.items()
    ):
        raise ValueError("T20.7 closed-loop source or evaluation linkage drifted")
    checkpoint_hashes = {
        value["sha256"] for value in training_result["checkpoint_files"].values()
    }
    if payload.get("checkpoint_sha256") not in checkpoint_hashes:
        raise ValueError("T20.7 closed-loop checkpoint linkage drifted")
    if not _is_sha256(payload.get("policy_action_sequence_sha256")):
        raise ValueError("T20.7 closed-loop action-sequence hash is invalid")
    for key in (
        "policy_requested_action_first",
        "policy_requested_action_last",
        "applied_action_first",
        "applied_action_last",
    ):
        values = payload.get(key)
        if (
            not isinstance(values, list)
            or len(values) != 6
            or not all(_finite_number(value) for value in values)
        ):
            raise ValueError("T20.7 closed-loop first or last action is invalid")
    if not _finite_number(payload.get("maximum_anchor_lift_m")):
        raise ValueError("T20.7 closed-loop lift measurement is non-finite")

    runtime = payload.get("policy_runtime", {})
    expected_steps = None if model_id == "act" else 10
    runtime_expected = {
        "device": "mps",
        "dtype": "float32",
        "offline": True,
        "inference_seed": plan["evaluation_contract"]["inference_seed"],
        "action_horizon": plan["evaluation_contract"]["executed_action_horizon"],
        "maximum_open_loop_duration_frames": plan["evaluation_contract"][
            "executed_action_horizon"
        ],
        "initial_policy_reset_count": 1,
        "inference_replan_count": 49,
        "queue_refill_count": 49,
        "denoising_steps_where_applicable": expected_steps,
    }
    if any(runtime.get(key) != value for key, value in runtime_expected.items()):
        raise ValueError("T20.7 closed-loop runtime contract drifted")
    if not _is_sha256(runtime.get("lerobot_stack_identity_sha256")):
        raise ValueError("T20.7 closed-loop LeRobot runtime identity is invalid")

    keyframes = payload.get("rendered_keyframes")
    if (
        not isinstance(keyframes, list)
        or len(keyframes) != plan["evaluation_contract"]["rendered_keyframe_count"]
        or len({frame.get("frame_index") for frame in keyframes}) != len(keyframes)
        or not all(
            isinstance(frame.get("frame_index"), int)
            and not isinstance(frame.get("frame_index"), bool)
            and 0 <= frame["frame_index"] < payload["frame_count"]
            for frame in keyframes
        )
    ):
        raise ValueError("T20.7 closed-loop keyframe count or indices drifted")
    for frame in keyframes:
        if set(frame.get("images", {})) != {"top", "wrist"}:
            raise ValueError("T20.7 closed-loop keyframe camera set drifted")
        for image in frame["images"].values():
            _verify_rendered_image(
                image,
                expected_size=plan["evaluation_contract"]["rendered_keyframe_size_px"],
            )

    margins = payload.get("gate_margins")
    if not isinstance(margins, dict) or set(margins) != GATE_NAMES:
        raise ValueError("T20.7 closed-loop gate-margin set drifted")
    failed = {}
    for name, value in margins.items():
        _verify_margin(value)
        if not value["passed"]:
            failed[name] = value
    failed_rows = payload.get("failed_gate_margins")
    if (
        not isinstance(failed_rows, list)
        or len(failed_rows) != len(failed)
        or {
            row.get("gate"): {
                key: value for key, value in row.items() if key != "gate"
            }
            for row in failed_rows
        }
        != failed
    ):
        raise ValueError("T20.7 closed-loop failed-gate margins drifted")
    strict_success = all(value["passed"] for value in margins.values())
    if payload.get("simulation_semantic_strict_success") is not strict_success:
        raise ValueError("T20.7 closed-loop strict-success derivation drifted")

    projected = payload.get("projected_action_frame_indices")
    if (
        not isinstance(projected, list)
        or len(projected) != payload.get("projected_action_frame_count")
        or len(set(projected)) != len(projected)
        or not all(
            isinstance(index, int)
            and not isinstance(index, bool)
            and 0 <= index < payload["frame_count"]
            for index in projected
        )
    ):
        raise ValueError("T20.7 closed-loop projection accounting drifted")
    counts = payload.get("strict_v2_valid_frame_counts")
    if not isinstance(counts, dict) or not counts or not all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in counts.values()
    ):
        raise ValueError("T20.7 closed-loop strict-frame counts are invalid")
    required_true = ("model_inference_executed", "policy_controls_owned_all_frames")
    required_false = (
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if any(payload.get(key) is not True for key in required_true) or any(
        payload.get(key) is not False for key in required_false
    ):
        raise ValueError("T20.7 closed-loop authority fields drifted")
    if payload.get("active_assist_frame_count") != 0:
        raise ValueError("T20.7 closed-loop assistance is forbidden")


def build_model_evaluation_gate(
    plan: dict[str, Any],
    training_gate: dict[str, Any],
    results: list[tuple[str, dict[str, Any], str, dict[str, Any], str]],
) -> dict[str, Any]:
    """Compose all observed behavior without manufacturing a winner."""

    verify_signed_payload(training_gate, label="T20.7 model training gate")
    if training_gate.get("source_plan_identity_sha256") != plan["identity_sha256"]:
        raise ValueError("T20.7 evaluation source training gate drifted")
    if [payload.get("model_id") for _, payload, _, _, _ in results] != list(
        MODEL_ORDER
    ):
        raise ValueError("T20.7 closed-loop results are incomplete or out of order")
    entries = []
    disqualifications = []
    strict_models = []
    for path, payload, file_sha256, training_result, training_file_sha256 in results:
        verify_model_closed_loop_result(
            payload,
            plan,
            training_result,
            training_result_file_sha256=training_file_sha256,
        )
        if not _is_sha256(file_sha256):
            raise ValueError("T20.7 closed-loop result file hash is invalid")
        projection_count = payload["projected_action_frame_count"]
        eligible = projection_count == 0
        if not eligible:
            disqualifications.append(
                {
                    "model_id": payload["model_id"],
                    "reason": "action_projection_forbidden_by_plan",
                    "measured": projection_count,
                    "threshold": 0,
                    "margin": -float(projection_count),
                }
            )
        if payload["simulation_semantic_strict_success"]:
            strict_models.append(payload["model_id"])
        entries.append(
            {
                "model_id": payload["model_id"],
                "path": path,
                "identity_sha256": payload["identity_sha256"],
                "file_sha256": file_sha256,
                "comparison_eligible": eligible,
                "terminal_outcome": payload["terminal_outcome"],
                "simulation_semantic_strict_success": payload[
                    "simulation_semantic_strict_success"
                ],
                "maximum_anchor_lift_m": payload["maximum_anchor_lift_m"],
                "strict_v2_valid_frame_counts": payload[
                    "strict_v2_valid_frame_counts"
                ],
                "projected_action_frame_count": projection_count,
                "active_assist_frame_count": payload["active_assist_frame_count"],
                "rendered_keyframe_count": len(payload["rendered_keyframes"]),
                "failed_gate_margins": payload["failed_gate_margins"],
                "policy_action_sequence_sha256": payload[
                    "policy_action_sequence_sha256"
                ],
            }
        )
    return sign_payload(
        {
            "schema_version": GATE_SCHEMA_VERSION,
            "task_id": "T20.7",
            "source_plan_identity_sha256": plan["identity_sha256"],
            "source_training_gate_identity_sha256": training_gate["identity_sha256"],
            "ranking_surface": plan["ranking_surface"],
            "model_results": entries,
            "all_four_evaluations_present": True,
            "same_closed_loop_contract_verified": True,
            "all_keyframe_requirements_verified": True,
            "all_gate_margins_reported": True,
            "comparison_disqualifications": disqualifications,
            "all_four_models_comparison_eligible": not disqualifications,
            "strict_success_models": strict_models,
            "strict_success_count": len(strict_models),
            "winner_model_id": strict_models[0] if len(strict_models) == 1 else None,
            "no_winner_reason": (
                None
                if len(strict_models) == 1
                else "no_model_met_all_strict_v2_gates"
                if not strict_models
                else "multiple_models_met_strict_v2; no tie_breaker_authorized"
            ),
            "t20_7_verified_negative": not strict_models,
            "optimizer_training": True,
            "model_inference_executed": True,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_model_evaluation_gate(
    payload: dict[str, Any],
    plan: dict[str, Any],
    training_gate: dict[str, Any],
    results: list[tuple[str, dict[str, Any], str, dict[str, Any], str]],
) -> None:
    verify_signed_payload(payload, label="T20.7 model evaluation gate")
    if payload != build_model_evaluation_gate(plan, training_gate, results):
        raise ValueError("T20.7 model evaluation gate drifted from observed results")


def _verify_rendered_image(image: dict[str, Any], *, expected_size: int) -> None:
    if (
        image.get("encoding") != "png"
        or image.get("channels") != 3
        or image.get("width") != expected_size
        or image.get("height") != expected_size
        or not _is_sha256(image.get("image_sha256"))
    ):
        raise ValueError("T20.7 rendered keyframe metadata drifted")
    try:
        raw = base64.b64decode(image["png_base64"], validate=True)
        with Image.open(io.BytesIO(raw)) as decoded:
            decoded.verify()
        with Image.open(io.BytesIO(raw)) as decoded:
            if decoded.size != (expected_size, expected_size) or decoded.mode != "RGB":
                raise ValueError("T20.7 rendered keyframe image dimensions drifted")
    except Exception as error:
        raise ValueError("T20.7 rendered keyframe PNG is invalid") from error
    if hashlib.sha256(raw).hexdigest() != image["image_sha256"]:
        raise ValueError("T20.7 rendered keyframe PNG hash drifted")


def _verify_margin(value: dict[str, Any]) -> None:
    measured = value.get("measured")
    threshold = value.get("threshold")
    comparison = value.get("comparison")
    if not _finite_number(threshold) or comparison not in {">=", "=="}:
        raise ValueError("T20.7 gate-margin threshold or comparison is invalid")
    if measured is None:
        expected_margin, expected_passed = None, False
    elif not _finite_number(measured):
        raise ValueError("T20.7 gate-margin measurement is non-finite")
    elif comparison == ">=":
        expected_margin = float(measured) - float(threshold)
        expected_passed = expected_margin >= 0
    else:
        expected_margin = -abs(float(measured) - float(threshold))
        expected_passed = measured == threshold
    if value.get("margin") != expected_margin or value.get("passed") is not expected_passed:
        raise ValueError("T20.7 gate-margin derivation drifted")


def _finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
