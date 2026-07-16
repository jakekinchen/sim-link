"""One-use runner and full evidence verifier for T20.44/R2 SmolVLA."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import subprocess
import sys

from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.act_grasp_closed_loop import (
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    PHASE_PLAN,
    ROLLOUT_FRAMES,
    run_policy_grasp_closed_loop,
)
from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.geometry_derived_grasp_primitives import (
    has_valid_antipodal_contact,
)
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    default_store_root,
)
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot
from scenesmith.robot_lab.strict_grasp import strict_grasp_spec_v2
from scenesmith.robot_lab.t20_36l_frozen_consequence_gate import (
    REACH_STOP_EXCLUSIVE,
    UNIFORM_REPORT_ONLY_THRESHOLD_RAD,
)
from scenesmith.robot_lab.t20_44_r2_smolvla_contracts import (
    ATTEMPT_PATH,
    BATCH_SIZE,
    BRANCH,
    CHECKPOINT_ROOT,
    CHECKPOINT_SCHEDULE,
    CHUNK_SIZE,
    DECISION_PATH,
    EVALUATION_ACTION_STEPS,
    FAILURE_PATH,
    GATE_A_PATH,
    MAXIMUM_OPTIMIZER_UPDATES,
    MUJOCO_SUPPORT_SITE_PACKAGES,
    OWNER_GRANT_PATH,
    PERMIT_PATH,
    POLICY_SNAPSHOT_PATH,
    PRE_RUN_ACCEPTANCE_PATH,
    REQUEST_PATH,
    RESULT_PATH,
    RETENTION_PATH,
    ROLLOUT_ROOT,
    R0_DATASET_REPO_ID,
    R0_DATASET_ROOT,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    RUNTIME_PREFLIGHT_PATH,
    SCORECARD_PATH,
    SPEC_PATH,
    TRAINING_SEED,
    VLM_SNAPSHOT_PATH,
    VIDEO_ROOT,
    build_attempt_marker,
    load_verified_sources,
    verify_attempt_marker,
    verify_pre_run_acceptance,
    verify_spec,
)
from scenesmith.robot_lab.t20_44_r2_smolvla_materialization import (
    IMPLEMENTATION_SCOPED_PATHS,
    verify_materialized_authority,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_PATH = RUN_ROOT / "progress.json"
TRACE_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_closed_loop_trace.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_run.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_result.v1"
RETENTION_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_retention_receipt.v1"
SCORECARD_SCHEMA_VERSION = "scenesmith.t20_44_r2_smolvla_scorecard.v1"
T20_38_RECEIPT_IDENTITY = (
    "042bf0bee9dcca28449311a39f5e884106deabf604febc05b53b026ecaf71b4e"
)
FROZEN_GATE_IDENTITY = (
    "463477dc91e3fb36b0550b88d461a788709a7258f9825ad6644f98bf0c77e48f"
)
VARIANT_ORDER = ("chunk_50", "receding_10")
FALSE_TERMINAL_FIELDS = (
    "hardware_accessed",
    "camera_accessed",
    "serial_accessed",
    "physical_motion",
    "physical_actuation",
    "network_accessed",
    "external_compute_started",
    "brev_compute_started",
    "physical_transfer_ready",
    "promotion_eligible",
    "t20_45_activated",
)


class SmolVLARolloutAdapter:
    """Exact queue consumer with observable decode boundaries."""

    def __init__(
        self,
        *,
        policy: Any,
        preprocessor: Any,
        postprocessor: Any,
        torch: Any,
        source_frames: list[dict[str, Any]],
        n_action_steps: int,
        checkpoint_update: int,
        thresholds: dict[str, dict[str, float]],
    ) -> None:
        if n_action_steps not in EVALUATION_ACTION_STEPS:
            raise ValueError("T20.44 unsupported action-consumption variant")
        self.policy = policy
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor
        self.torch = torch
        self.source_frames = source_frames
        self.n_action_steps = n_action_steps
        self.checkpoint_update = checkpoint_update
        self.thresholds = thresholds
        self.queue: deque[np.ndarray] = deque()
        self.frame_index = 0
        self.decode_rows: list[dict[str, Any]] = []
        self.reset_count = 1

    def __call__(self, images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        if not self.queue:
            self._decode(images, state)
        action = self.queue.popleft()
        self.frame_index += 1
        return action.copy()

    def _decode(self, images: dict[str, np.ndarray], state: np.ndarray) -> None:
        torch = self.torch
        observation = {
            "observation.images.base_0_rgb": torch.as_tensor(
                np.asarray(images["top"], dtype=np.uint8).copy()
            )
            .permute(2, 0, 1)
            .float()
            .div(255.0),
            "observation.images.left_wrist_0_rgb": torch.as_tensor(
                np.asarray(images["wrist"], dtype=np.uint8).copy()
            )
            .permute(2, 0, 1)
            .float()
            .div(255.0),
            "observation.state": torch.as_tensor(
                mujoco_to_lerobot(np.asarray(state[:6], dtype=float).tolist()),
                dtype=torch.float32,
            ),
            "task": (
                "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, "
                "and retreat."
            ),
        }
        processed = self.preprocessor(observation)
        noise_seed = (
            20260901
            + self.checkpoint_update * 100
            + self.n_action_steps * 10
            + self.frame_index
        )
        generator = torch.Generator(device="cpu").manual_seed(noise_seed)
        noise_cpu = torch.randn(
            (1, CHUNK_SIZE, 32), generator=generator, dtype=torch.float32
        )
        noise = noise_cpu.to("mps")
        with torch.no_grad():
            normalized = self.policy.predict_action_chunk(
                processed, noise=noise
            ).squeeze(0)
            canonical = self.postprocessor(normalized)
        canonical_np = canonical.detach().cpu().float().numpy()
        if canonical_np.shape != (CHUNK_SIZE, 6) or not np.isfinite(canonical_np).all():
            raise ValueError("T20.44 SmolVLA emitted an invalid action chunk")
        physical = np.asarray(
            [lerobot_to_mujoco(row.tolist()) for row in canonical_np],
            dtype=np.float64,
        )
        executed_length = min(self.n_action_steps, ROLLOUT_FRAMES - self.frame_index)
        if executed_length <= 0:
            raise ValueError("T20.44 decode occurred beyond the rollout")
        self.queue.extend(row.copy() for row in physical[:executed_length])
        available = min(CHUNK_SIZE, ROLLOUT_FRAMES - self.frame_index)
        source = np.asarray(
            [
                row["actions"]["requested"]["values"]
                for row in self.source_frames[
                    self.frame_index : self.frame_index + available
                ]
            ],
            dtype=np.float64,
        )
        errors = np.abs(physical[:available] - source)
        violations = []
        joint_names = (
            "shoulder_pan",
            "shoulder_lift",
            "elbow_flex",
            "wrist_flex",
            "wrist_roll",
            "gripper",
        )
        for timestep in range(available):
            phase_group = "reach" if timestep < REACH_STOP_EXCLUSIVE else "grasp"
            for joint_index, joint_name in enumerate(joint_names):
                threshold = self.thresholds[phase_group][joint_name]
                error = float(errors[timestep, joint_index])
                if error > threshold:
                    violations.append(
                        {
                            "timestep": timestep,
                            "joint_name": joint_name,
                            "phase_group": phase_group,
                            "absolute_error_rad": error,
                            "threshold_rad": threshold,
                            "excess_rad": error - threshold,
                        }
                    )
        self.decode_rows.append(
            {
                "decode_start_frame": self.frame_index,
                "checkpoint_update": self.checkpoint_update,
                "noise_seed": noise_seed,
                "base_noise_sha256": hashlib.sha256(
                    canonical_json_bytes(noise_cpu.numpy().astype(float).tolist())
                ).hexdigest(),
                "n_action_steps": self.n_action_steps,
                "predicted_chunk_length": CHUNK_SIZE,
                "source_comparison_length": available,
                "executed_length": executed_length,
                "unexecuted_tail_count": CHUNK_SIZE - executed_length,
                "physical_action_chunk_sha256": hashlib.sha256(
                    canonical_json_bytes(physical.astype(float).tolist())
                ).hexdigest(),
                "executed_action_sha256": hashlib.sha256(
                    canonical_json_bytes(
                        physical[:executed_length].astype(float).tolist()
                    )
                ).hexdigest(),
                "uniform_report_only_threshold_rad": UNIFORM_REPORT_ONLY_THRESHOLD_RAD,
                "uniform_report_only_maximum_error_rad": float(np.max(errors)),
                "uniform_report_only_passed": bool(
                    np.max(errors) <= UNIFORM_REPORT_ONLY_THRESHOLD_RAD
                ),
                "frozen_gate_identity_sha256": FROZEN_GATE_IDENTITY,
                "frozen_amended_gate_passed": not violations,
                "frozen_amended_gate_violation_count": len(violations),
                "frozen_amended_gate_violations": violations,
            }
        )


def build_comparison_rows(
    *,
    source_frames: list[dict[str, Any]],
    candidate_frames: list[dict[str, Any]],
    n_action_steps: int,
) -> list[dict[str, Any]]:
    if (
        n_action_steps not in EVALUATION_ACTION_STEPS
        or len(source_frames) != ROLLOUT_FRAMES
        or len(candidate_frames) != ROLLOUT_FRAMES
    ):
        raise ValueError("T20.44 complete trace inputs drifted")
    rows = []
    for index, (source, candidate) in enumerate(
        zip(source_frames, candidate_frames, strict=True)
    ):
        if source.get("source_phase") != candidate.get("phase"):
            raise ValueError("T20.44 source/candidate phase drifted")
        rows.append(
            {
                "frame_index": index,
                "phase": source["source_phase"],
                "chunk_index": index // n_action_steps,
                "chunk_offset": index % n_action_steps,
                "source_requested_action_rad": _vector(
                    source["actions"]["requested"]["values"]
                ),
                "source_applied_action_rad": _vector(
                    source["actions"]["sent"]["values"]
                ),
                "candidate_requested_action_rad": _vector(
                    candidate["policy_requested_action"]
                ),
                "candidate_applied_action_rad": _vector(
                    candidate["policy_applied_action"]
                ),
                "source_qpos_rad": _vector(
                    source["observations"]["joint_position_mujoco_rad"]
                ),
                "candidate_qpos_rad": _vector(candidate["mujoco_qpos"]),
                "source_qvel_rad_s": _vector(
                    source["observations"]["joint_velocity_mujoco_rad_s"]
                ),
                "candidate_qvel_rad_s": _vector(candidate["mujoco_qvel"]),
                "candidate_anchor_position_m": _position(
                    candidate["cube_positions_m"][OBJECT_ID]
                ),
                "candidate_strict_contact": bool(candidate["t20_44_strict_contact"]),
            }
        )
    _verify_comparison_rows(rows, n_action_steps=n_action_steps)
    return rows


def build_trace(
    *,
    update: int,
    variant_id: str,
    n_action_steps: int,
    checkpoint_identity_sha256: str,
    source_ref: dict[str, Any],
    rows: list[dict[str, Any]],
    decode_rows: list[dict[str, Any]],
    closed_loop: dict[str, Any],
) -> dict[str, Any]:
    _scheduled_update(update)
    expected_variant = _variant_id(n_action_steps)
    if variant_id != expected_variant:
        raise ValueError("T20.44 trace variant drifted")
    _verify_comparison_rows(rows, n_action_steps=n_action_steps)
    _verify_decode_rows(
        decode_rows,
        n_action_steps=n_action_steps,
        checkpoint_update=update,
    )
    verify_signed_payload(closed_loop, label="T20.44 embedded rollout")
    requested_sha = _sequence_sha(rows, "candidate_requested_action_rad")
    applied_sha = _sequence_sha(rows, "candidate_applied_action_rad")
    if (
        closed_loop.get("frame_count") != ROLLOUT_FRAMES
        or closed_loop.get("seed") != 0
        or closed_loop.get("policy_action_sequence_sha256") != requested_sha
        or closed_loop.get("projected_action_frame_count") != 0
        or closed_loop.get("active_assist_frame_count") != 0
    ):
        raise ValueError("T20.44 rollout linkage drifted")
    diagnostics = _trace_diagnostics(rows, n_action_steps=n_action_steps)
    t20_38 = _t20_38_runtime_receipt(closed_loop)
    payload = sign_payload(
        {
            "schema_version": TRACE_SCHEMA_VERSION,
            "task_id": "T20.44",
            "adapter_id": variant_id,
            "seed": 0,
            "seed_role": "training",
            "optimizer_update_count": update,
            "n_action_steps": n_action_steps,
            "checkpoint_identity_sha256": _sha(checkpoint_identity_sha256),
            "source_episode_ref": source_ref,
            "comparisons": rows,
            "diagnostics": diagnostics,
            "decode_rows": decode_rows,
            "decode_start_frames": [row["decode_start_frame"] for row in decode_rows],
            "executed_lengths": [row["executed_length"] for row in decode_rows],
            "queue_reset_count": 1,
            "unexecuted_tail_actions_excluded": True,
            "requested_action_sequence_sha256": requested_sha,
            "applied_action_sequence_sha256": applied_sha,
            "closed_loop": closed_loop,
            "t20_38_runtime_receipt": t20_38,
            "frozen_amended_gate_identity_sha256": FROZEN_GATE_IDENTITY,
            "frozen_amended_gate_report_only": True,
            "uniform_0_05_rad_report_only": True,
            "strict_v2_oracle_unchanged": True,
            "model_inference_executed": True,
            "optimizer_training_preceded_this_checkpoint": update > 0,
            "simulation_policy_accepted": False,
            **_false_terminal_fields(),
        }
    )
    verify_trace(payload)
    return payload


def verify_trace(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.44 trace")
    if (
        payload.get("schema_version") != TRACE_SCHEMA_VERSION
        or payload.get("task_id") != "T20.44"
        or payload.get("seed") != 0
        or payload.get("seed_role") != "training"
        or payload.get("queue_reset_count") != 1
        or payload.get("unexecuted_tail_actions_excluded") is not True
        or payload.get("strict_v2_oracle_unchanged") is not True
        or payload.get("simulation_policy_accepted") is not False
    ):
        raise ValueError("T20.44 trace identity or authority drifted")
    update = _scheduled_update(payload.get("optimizer_update_count"))
    n_action_steps = payload.get("n_action_steps")
    source_ref = payload.get("source_episode_ref")
    if (
        not isinstance(source_ref, dict)
        or not isinstance(source_ref.get("path"), str)
        or Path(source_ref["path"]).is_absolute()
        or ".." in Path(source_ref["path"]).parts
    ):
        raise ValueError("T20.44 source episode reference is unsafe")
    _sha(source_ref.get("file_sha256"))
    _sha(source_ref.get("raw_rollout_identity_sha256"))
    if payload.get("adapter_id") != _variant_id(n_action_steps):
        raise ValueError("T20.44 trace variant identity drifted")
    rows = payload.get("comparisons")
    _verify_comparison_rows(rows, n_action_steps=n_action_steps)
    decode_rows = payload.get("decode_rows")
    _verify_decode_rows(
        decode_rows,
        n_action_steps=n_action_steps,
        checkpoint_update=update,
    )
    if (
        payload.get("decode_start_frames")
        != [row["decode_start_frame"] for row in decode_rows]
        or payload.get("executed_lengths")
        != [row["executed_length"] for row in decode_rows]
        or payload.get("requested_action_sequence_sha256")
        != _sequence_sha(rows, "candidate_requested_action_rad")
        or payload.get("applied_action_sequence_sha256")
        != _sequence_sha(rows, "candidate_applied_action_rad")
        or payload.get("diagnostics")
        != _trace_diagnostics(rows, n_action_steps=n_action_steps)
        or payload.get("optimizer_training_preceded_this_checkpoint")
        is not (update > 0)
    ):
        raise ValueError("T20.44 trace derived evidence drifted")
    rollout = payload.get("closed_loop")
    verify_signed_payload(rollout, label="T20.44 embedded rollout")
    if (
        rollout.get("seed") != 0
        or rollout.get("frame_count") != ROLLOUT_FRAMES
        or rollout.get("policy_action_sequence_sha256")
        != payload["requested_action_sequence_sha256"]
        or rollout.get("projected_action_frame_count") != 0
        or rollout.get("active_assist_frame_count") != 0
    ):
        raise ValueError("T20.44 embedded rollout linkage drifted")
    if payload.get("t20_38_runtime_receipt") != _t20_38_runtime_receipt(rollout):
        raise ValueError("T20.44 T20.38 runtime margins drifted")
    if payload.get("model_inference_executed") is not True or any(
        payload.get(field) is not False for field in FALSE_TERMINAL_FIELDS
    ):
        raise ValueError("T20.44 trace terminal authority drifted")


def build_run_summary(
    *,
    attempt: dict[str, Any],
    spec: dict[str, Any],
    optimizer_update_count: int,
    losses: list[float],
    gradient_norms: list[float],
    learning_rates: list[float],
    checkpoints: list[dict[str, Any]],
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    if optimizer_update_count != MAXIMUM_OPTIMIZER_UPDATES:
        raise ValueError("T20.44 run did not complete the fixed update budget")
    _finite_series(losses, expected=MAXIMUM_OPTIMIZER_UPDATES, label="loss")
    _finite_series(gradient_norms, expected=MAXIMUM_OPTIMIZER_UPDATES, label="gradient")
    _finite_series(learning_rates, expected=MAXIMUM_OPTIMIZER_UPDATES, label="lr")
    _verify_checkpoint_rows(checkpoints)
    _verify_evaluation_rows(evaluations)
    gate_c = _first_gate_c(evaluations)
    return sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": "T20.44",
            "attempt_identity_sha256": attempt["identity_sha256"],
            "spec_identity_sha256": spec["identity_sha256"],
            "optimizer_update_count": optimizer_update_count,
            "maximum_optimizer_updates": MAXIMUM_OPTIMIZER_UPDATES,
            "batch_size": BATCH_SIZE,
            "checkpoint_schedule": list(CHECKPOINT_SCHEDULE),
            "losses": losses,
            "gradient_norms_before_clip": gradient_norms,
            "learning_rates": learning_rates,
            "all_losses_and_gradients_finite": True,
            "checkpoints": checkpoints,
            "evaluations": evaluations,
            "first_gate_c_pass": gate_c,
            "gate_c_passed": gate_c is not None,
            "retry_authorized": False,
            "model_constructed": True,
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": True,
            "optimizer_training": True,
            "learned_policy_rollout": True,
            "gate_c_executed": True,
            "simulation_policy_accepted": gate_c is not None,
            **_false_terminal_fields(),
        }
    )


def verify_run_summary(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.44 run summary")
    if payload.get("schema_version") != RUN_SCHEMA_VERSION:
        raise ValueError("T20.44 run schema drifted")
    expected = build_run_summary(
        attempt={"identity_sha256": payload.get("attempt_identity_sha256")},
        spec={"identity_sha256": payload.get("spec_identity_sha256")},
        optimizer_update_count=payload.get("optimizer_update_count"),
        losses=payload.get("losses"),
        gradient_norms=payload.get("gradient_norms_before_clip"),
        learning_rates=payload.get("learning_rates"),
        checkpoints=payload.get("checkpoints"),
        evaluations=payload.get("evaluations"),
    )
    if payload != expected:
        raise ValueError("T20.44 run summary drifted")


def build_result(*, run: dict[str, Any]) -> dict[str, Any]:
    verify_run_summary(run)
    gate_c = run["first_gate_c_pass"]
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.44",
            "status": (
                "verified_gate_c_success" if gate_c else "verified_terminal_negative"
            ),
            "run_identity_sha256": run["identity_sha256"],
            "attempt_count": 1,
            "optimizer_update_count": run["optimizer_update_count"],
            "checkpoint_count": len(run["checkpoints"]),
            "rollout_count": len(run["evaluations"]) * len(VARIANT_ORDER),
            "first_gate_c_pass": gate_c,
            "gate_c_passed": gate_c is not None,
            "retry_authorized": False,
            "model_constructed": True,
            "model_loaded": True,
            "model_inference": True,
            "optimizer_created": True,
            "optimizer_training": True,
            "learned_policy_rollout": True,
            "gate_c_executed": True,
            "simulation_policy_accepted": gate_c is not None,
            **_false_terminal_fields(),
        }
    )


def verify_result(payload: dict[str, Any], *, run: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.44 result")
    if payload != build_result(run=run):
        raise ValueError("T20.44 result drifted")


def build_scorecard(*, result: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    verify_result(result, run=run)
    return sign_payload(
        {
            "schema_version": SCORECARD_SCHEMA_VERSION,
            "task_id": "T20.44",
            "r0_dataset": {
                "verified": True,
                "episode_count": 129,
                "frame_count": 31366,
            },
            "learning_plumbing": {
                "gate_a_passed": True,
                "updates_completed": MAXIMUM_OPTIMIZER_UPDATES,
                "all_finite": True,
            },
            "policy_behavior": {
                "rollout_primary": True,
                "strict_v2_gate_c_passed": result["gate_c_passed"],
                "first_gate_c_pass": result["first_gate_c_pass"],
                "evaluated_variants": list(VARIANT_ORDER),
            },
            "metric_twin": {"real_robo_scan_i5_verified": False},
            "physical_canary": {"learned_policy_canary_verified": False},
            "demo_ready_simulation_learning_mvp": result["gate_c_passed"],
            "full_scenesmith_mvp": False,
            "hardware_accessed": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def build_retention(
    *, result: dict[str, Any], run: dict[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    verify_result(result, run=run)
    root = Path(repo_root).resolve()
    trees = {
        "checkpoints": _file_tree(root / CHECKPOINT_ROOT),
        "rollouts": _file_tree(root / ROLLOUT_ROOT),
        "mirrors": _file_tree(root / VIDEO_ROOT),
    }
    return sign_payload(
        {
            "schema_version": RETENTION_SCHEMA_VERSION,
            "task_id": "T20.44",
            "result_identity_sha256": result["identity_sha256"],
            "run_identity_sha256": run["identity_sha256"],
            "local_output_trees": trees,
            "large_outputs_tracked_in_git": False,
            "compact_evidence_tracked_in_git": True,
            "raw_outputs_rewritten": False,
            "retry_authorized": False,
            "model_inference": True,
            "optimizer_training": True,
            "learned_policy_rollout": True,
            "gate_c_executed": True,
            "simulation_policy_accepted": result["gate_c_passed"],
            **_false_terminal_fields(),
        }
    )


def verify_all_outputs(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = load_verified_sources(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_spec(spec, sources=sources)
    bundle = verify_materialized_authority(repo_root=root)
    permit = bundle[PERMIT_PATH.as_posix()]
    acceptance = load_strict_json(root / PRE_RUN_ACCEPTANCE_PATH)
    verify_pre_run_acceptance(acceptance, permit=permit)
    attempt = load_strict_json(root / ATTEMPT_PATH)
    verify_attempt_marker(attempt, permit=permit)
    if (root / FAILURE_PATH).is_file():
        if any(
            (root / path).exists()
            for path in (RUN_SUMMARY_PATH, RESULT_PATH, SCORECARD_PATH, RETENTION_PATH)
        ):
            raise ValueError("T20.44 failure and full result coexist")
        failure = load_strict_json(root / FAILURE_PATH)
        verify_signed_payload(failure, label="T20.44 terminal failure")
        if (
            failure.get("status") != "verified_terminal_runtime_failure"
            or failure.get("attempt_identity_sha256") != attempt["identity_sha256"]
            or failure.get("attempt_count") != 1
            or failure.get("retry_authorized") is not False
            or failure.get("gate_c_passed") is not False
            or failure.get("first_gate_c_pass") is not None
            or failure.get("r2_activated") is not True
            or failure.get("t20_45_activated") is not False
        ):
            raise ValueError("T20.44 terminal failure boundary drifted")
        if (root / RUN_ROOT).is_dir() and _file_tree(root / RUN_ROOT) != failure.get(
            "partial_run_tree"
        ):
            raise ValueError("T20.44 terminal partial output tree drifted")
        return failure
    run = load_strict_json(root / RUN_SUMMARY_PATH)
    verify_run_summary(run)
    for checkpoint in run["checkpoints"]:
        if _file_tree(root / checkpoint["path"]) != checkpoint["tree"]:
            raise ValueError("T20.44 checkpoint tree drifted")
    for evaluation in run["evaluations"]:
        for variant in evaluation["variants"]:
            trace = load_strict_json(root / variant["trace_path"])
            verify_trace(trace)
            if trace["identity_sha256"] != variant["trace_identity_sha256"]:
                raise ValueError("T20.44 trace identity drifted")
            video = root / variant["video_path"]
            manifest = load_strict_json(root / variant["video_manifest_path"])
            verify_signed_payload(manifest, label="T20.44 mirror manifest")
            if (
                not video.is_file()
                or video.is_symlink()
                or _sha_file(video) != variant["video_file_sha256"]
                or manifest.get("trace_identity_sha256") != trace["identity_sha256"]
                or manifest.get("output_sha256") != variant["video_file_sha256"]
            ):
                raise ValueError("T20.44 mirror evidence drifted")
    result = load_strict_json(root / RESULT_PATH)
    verify_result(result, run=run)
    scorecard = load_strict_json(root / SCORECARD_PATH)
    if scorecard != build_scorecard(result=result, run=run):
        raise ValueError("T20.44 scorecard drifted")
    retention = load_strict_json(root / RETENTION_PATH)
    if retention != build_retention(result=result, run=run, repo_root=root):
        raise ValueError("T20.44 retention drifted")
    return result


def run_authorized_attempt(
    *, started_at: str, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    try:
        return _run_authorized_attempt(started_at=started_at, repo_root=root)
    except Exception as error:
        if (root / ATTEMPT_PATH).is_file() and not (root / FAILURE_PATH).exists():
            attempt = load_strict_json(root / ATTEMPT_PATH)
            progress = (
                load_strict_json(root / PROGRESS_PATH)
                if (root / PROGRESS_PATH).is_file()
                else {
                    "stage": "unknown_after_marker",
                    "optimizer_update_count": 0,
                    "model_constructed": False,
                    "model_loaded": False,
                    "model_inference": False,
                    "optimizer_created": False,
                    "optimizer_training": False,
                }
            )
            partial_tree = (
                _file_tree(root / RUN_ROOT) if (root / RUN_ROOT).is_dir() else []
            )
            failure = sign_payload(
                {
                    "schema_version": "scenesmith.t20_44_r2_smolvla_terminal_failure.v1",
                    "task_id": "T20.44",
                    "status": "verified_terminal_runtime_failure",
                    "attempt_identity_sha256": attempt["identity_sha256"],
                    "attempt_count": 1,
                    "optimizer_update_count": progress["optimizer_update_count"],
                    "checkpoint_count": len(
                        [
                            path
                            for path in (root / CHECKPOINT_ROOT).glob("step_*")
                            if path.is_dir()
                        ]
                    ),
                    "rollout_count": len(list((root / ROLLOUT_ROOT).glob("*.json"))),
                    "gate_c_passed": False,
                    "first_gate_c_pass": None,
                    "failure_stage": progress["stage"],
                    "error_type": type(error).__name__,
                    "error_message": (str(error) or repr(error))[:2000],
                    "execution_state": progress,
                    "partial_run_tree": partial_tree,
                    "retry_authorized": False,
                    "r2_activated": True,
                    "t20_45_activated": False,
                    "hardware_accessed": False,
                    "camera_accessed": False,
                    "serial_accessed": False,
                    "physical_motion": False,
                    "physical_actuation": False,
                    "network_accessed": False,
                    "external_compute_started": False,
                    "brev_compute_started": False,
                    "physical_transfer_ready": False,
                    "promotion_eligible": False,
                }
            )
            dump_canonical_json(root / FAILURE_PATH, failure)
        raise


def _run_authorized_attempt(
    *, started_at: str, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = load_verified_sources(repo_root=root)
    spec = load_strict_json(root / SPEC_PATH)
    verify_spec(spec, sources=sources)
    bundle = verify_materialized_authority(repo_root=root)
    permit = bundle[PERMIT_PATH.as_posix()]
    runtime_preflight = bundle[RUNTIME_PREFLIGHT_PATH.as_posix()]
    acceptance = load_strict_json(root / PRE_RUN_ACCEPTANCE_PATH)
    verify_pre_run_acceptance(acceptance, permit=permit)
    _require_active_time(bundle[OWNER_GRANT_PATH.as_posix()], started_at)
    if runtime_preflight.get("renderer_interpreter") != sys.executable:
        raise ValueError("T20.44 runner interpreter drifted from renderer smoke")
    if str(MUJOCO_SUPPORT_SITE_PACKAGES) not in sys.path:
        raise ValueError("T20.44 stable MuJoCo support path is absent")
    _require_remote_preservation(permit, acceptance, repo_root=root)
    if any(
        os.path.lexists(root / path) for path in (ATTEMPT_PATH, RUN_ROOT, RESULT_PATH)
    ):
        raise FileExistsError("T20.44 immutable attempt/output already exists")
    attempt = build_attempt_marker(
        permit=permit,
        source_commit=_git(root, "rev-parse", "HEAD"),
        started_at=started_at,
    )
    dump_canonical_json(root / ATTEMPT_PATH, attempt)
    verify_attempt_marker(attempt, permit=permit)
    (root / CHECKPOINT_ROOT).mkdir(parents=True, exist_ok=False)
    (root / ROLLOUT_ROOT).mkdir(parents=True, exist_ok=False)
    (root / VIDEO_ROOT).mkdir(parents=True, exist_ok=False)
    progress = {
        "stage": "model_import",
        "optimizer_update_count": 0,
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
    }
    dump_canonical_json(root / PROGRESS_PATH, progress)

    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "0",
        }
    )
    import torch

    from lerobot.configs.types import FeatureType, NormalizationMode, PolicyFeature
    from lerobot.datasets import EpisodeAwareSampler, LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    from lerobot.policies.smolvla.processor_smolvla import (
        make_smolvla_pre_post_processors,
    )

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.44 requires MPS")
    _seed_all(TRAINING_SEED, torch)
    config = _smolvla_config(
        SmolVLAConfig=SmolVLAConfig,
        FeatureType=FeatureType,
        NormalizationMode=NormalizationMode,
        PolicyFeature=PolicyFeature,
    )
    metadata = LeRobotDatasetMetadata(R0_DATASET_REPO_ID, root=root / R0_DATASET_ROOT)
    dataset = LeRobotDataset(
        R0_DATASET_REPO_ID,
        root=root / R0_DATASET_ROOT,
        delta_timestamps={
            "action": [index / metadata.fps for index in range(CHUNK_SIZE)]
        },
        return_uint8=False,
    )
    sampler = EpisodeAwareSampler(
        dataset.meta.episodes["dataset_from_index"],
        dataset.meta.episodes["dataset_to_index"],
        episode_indices_to_use=dataset.episodes,
        shuffle=True,
        seed=TRAINING_SEED,
        absolute_to_relative_idx=dataset.absolute_to_relative_idx,
    )
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        sampler=sampler,
        shuffle=False,
        num_workers=0,
        drop_last=False,
    )
    iterator = _cycle(dataloader)
    progress["stage"] = "model_construction"
    progress["model_constructed"] = True
    dump_canonical_json(root / PROGRESS_PATH, progress)
    policy = SmolVLAPolicy.from_pretrained(
        POLICY_SNAPSHOT_PATH,
        config=config,
        local_files_only=True,
        strict=True,
    ).to("mps")
    progress["model_loaded"] = True
    preprocessor, postprocessor = make_smolvla_pre_post_processors(
        config, dataset_stats=dataset.meta.stats
    )
    trainable = _verify_trainable_scope(policy)
    optimizer = config.get_optimizer_preset().build(trainable)
    scheduler = config.get_scheduler_preset().build(
        optimizer, MAXIMUM_OPTIMIZER_UPDATES
    )
    progress["optimizer_created"] = True
    progress["stage"] = "checkpoint_0_evaluation"
    dump_canonical_json(root / PROGRESS_PATH, progress)
    source_ref, source_frames = _source_episode_zero(root)
    thresholds = sources["frozen_gate"]["amended_gate_b_conjunction"]
    thresholds = thresholds["phase_joint_maximum_error_rad"]
    losses: list[float] = []
    gradient_norms: list[float] = []
    learning_rates: list[float] = []
    checkpoints: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []

    def checkpoint_and_evaluate(update: int) -> None:
        checkpoint_path = CHECKPOINT_ROOT / f"step_{update:05d}"
        policy.save_pretrained(root / checkpoint_path, safe_serialization=True)
        preprocessor.save_pretrained(root / checkpoint_path)
        postprocessor.save_pretrained(root / checkpoint_path)
        tree = _file_tree(root / checkpoint_path)
        checkpoint_identity = hashlib.sha256(canonical_json_bytes(tree)).hexdigest()
        checkpoint_row = {
            "optimizer_update_count": update,
            "path": checkpoint_path.as_posix(),
            "tree": tree,
            "identity_sha256": checkpoint_identity,
        }
        checkpoints.append(checkpoint_row)
        variants = []
        for n_action_steps in EVALUATION_ACTION_STEPS:
            variant_id = _variant_id(n_action_steps)
            policy.reset()
            observed: list[dict[str, Any]] = []
            adapter = SmolVLARolloutAdapter(
                policy=policy,
                preprocessor=preprocessor,
                postprocessor=postprocessor,
                torch=torch,
                source_frames=source_frames,
                n_action_steps=n_action_steps,
                checkpoint_update=update,
                thresholds=thresholds,
            )
            rollout = run_policy_grasp_closed_loop(
                adapter,
                checkpoint_sha256=checkpoint_identity,
                training_run_summary_sha256=spec["identity_sha256"],
                seed=0,
                schema_version="scenesmith.t20_44_r2_smolvla_rollout.v1",
                task_id="T20.44",
                evidence_mode=f"step_{update}_{variant_id}",
                policy_label="SMOLVLA_R2_STANDARD",
                frame_observer=observed.append,
                release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
                capture_images=True,
            )
            progress["model_inference"] = True
            dump_canonical_json(root / PROGRESS_PATH, progress)
            requirement = strict_grasp_spec_v2()["antipodal_contact_requirement"]
            for row in observed:
                row["t20_44_strict_contact"] = has_valid_antipodal_contact(
                    row, requirement
                )
            rows = build_comparison_rows(
                source_frames=source_frames,
                candidate_frames=observed,
                n_action_steps=n_action_steps,
            )
            trace = build_trace(
                update=update,
                variant_id=variant_id,
                n_action_steps=n_action_steps,
                checkpoint_identity_sha256=checkpoint_identity,
                source_ref=source_ref,
                rows=rows,
                decode_rows=adapter.decode_rows,
                closed_loop=rollout,
            )
            trace_path = ROLLOUT_ROOT / f"step_{update:05d}_{variant_id}.json"
            dump_canonical_json(root / trace_path, trace)
            video_path = VIDEO_ROOT / f"step_{update:05d}_{variant_id}.mp4"
            _render_mirror(trace_path=trace_path, video_path=video_path, repo_root=root)
            manifest_path = video_path.with_suffix(".manifest.json")
            manifest = load_strict_json(root / manifest_path)
            variants.append(
                {
                    "variant_id": variant_id,
                    "n_action_steps": n_action_steps,
                    "strict_v2_passed": rollout["simulation_semantic_strict_success"],
                    "terminal_outcome": rollout["terminal_outcome"],
                    "trace_path": trace_path.as_posix(),
                    "trace_identity_sha256": trace["identity_sha256"],
                    "video_path": video_path.as_posix(),
                    "video_file_sha256": _sha_file(root / video_path),
                    "video_manifest_path": manifest_path.as_posix(),
                    "video_manifest_identity_sha256": manifest["identity_sha256"],
                }
            )
        evaluations.append({"optimizer_update_count": update, "variants": variants})
        print(
            "evaluation",
            update,
            [(row["variant_id"], row["strict_v2_passed"]) for row in variants],
            flush=True,
        )

    checkpoint_and_evaluate(0)
    for update in range(1, MAXIMUM_OPTIMIZER_UPDATES + 1):
        progress["stage"] = "optimizer_training"
        progress["optimizer_training"] = True
        policy.train()
        batch = next(iterator)
        batch = preprocessor(batch)
        optimizer.zero_grad(set_to_none=True)
        loss, _ = policy(batch)
        if not torch.isfinite(loss):
            raise ValueError(f"T20.44 non-finite loss at update {update}")
        loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in trainable
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.44 non-finite gradient at update {update}")
        norm = torch.nn.utils.clip_grad_norm_(trainable, 10.0)
        if not torch.isfinite(norm):
            raise ValueError(f"T20.44 non-finite gradient norm at update {update}")
        optimizer.step()
        scheduler.step()
        torch.mps.synchronize()
        losses.append(float(loss.detach().cpu()))
        gradient_norms.append(float(norm.detach().cpu()))
        learning_rates.append(float(optimizer.param_groups[0]["lr"]))
        progress["optimizer_update_count"] = update
        dump_canonical_json(root / PROGRESS_PATH, progress)
        if update % 100 == 0:
            print("update", update, losses[-1], flush=True)
        if update in CHECKPOINT_SCHEDULE[1:]:
            progress["stage"] = f"checkpoint_{update}_evaluation"
            dump_canonical_json(root / PROGRESS_PATH, progress)
            checkpoint_and_evaluate(update)
    run = build_run_summary(
        attempt=attempt,
        spec=spec,
        optimizer_update_count=MAXIMUM_OPTIMIZER_UPDATES,
        losses=losses,
        gradient_norms=gradient_norms,
        learning_rates=learning_rates,
        checkpoints=checkpoints,
        evaluations=evaluations,
    )
    dump_canonical_json(root / RUN_SUMMARY_PATH, run)
    result = build_result(run=run)
    dump_canonical_json(root / RESULT_PATH, result)
    scorecard = build_scorecard(result=result, run=run)
    dump_canonical_json(root / SCORECARD_PATH, scorecard)
    retention = build_retention(result=result, run=run, repo_root=root)
    dump_canonical_json(root / RETENTION_PATH, retention)
    return verify_all_outputs(repo_root=root)


def _verify_checkpoint_rows(rows: Any) -> None:
    if not isinstance(rows, list) or [
        row.get("optimizer_update_count") for row in rows
    ] != list(CHECKPOINT_SCHEDULE):
        raise ValueError("T20.44 checkpoint schedule drifted")
    for row in rows:
        _sha(row.get("identity_sha256"))
        tree = row.get("tree")
        if not isinstance(tree, list) or not tree:
            raise ValueError("T20.44 checkpoint tree is empty")
        if (
            hashlib.sha256(canonical_json_bytes(tree)).hexdigest()
            != row["identity_sha256"]
        ):
            raise ValueError("T20.44 checkpoint identity drifted")


def _verify_evaluation_rows(rows: Any) -> None:
    if not isinstance(rows, list) or [
        row.get("optimizer_update_count") for row in rows
    ] != list(CHECKPOINT_SCHEDULE):
        raise ValueError("T20.44 evaluation schedule drifted")
    for row in rows:
        variants = row.get("variants")
        if not isinstance(variants, list) or [
            v.get("variant_id") for v in variants
        ] != list(VARIANT_ORDER):
            raise ValueError("T20.44 evaluation variant order drifted")
        for variant, action_steps in zip(
            variants, EVALUATION_ACTION_STEPS, strict=True
        ):
            if (
                variant.get("n_action_steps") != action_steps
                or not isinstance(variant.get("strict_v2_passed"), bool)
                or not isinstance(variant.get("terminal_outcome"), str)
            ):
                raise ValueError("T20.44 evaluation variant semantics drifted")
            for key in (
                "trace_identity_sha256",
                "video_file_sha256",
                "video_manifest_identity_sha256",
            ):
                _sha(variant.get(key))


def _first_gate_c(evaluations: list[dict[str, Any]]) -> dict[str, Any] | None:
    _verify_evaluation_rows(evaluations)
    for evaluation in evaluations:
        for variant in evaluation["variants"]:
            if variant["strict_v2_passed"]:
                return {
                    "optimizer_update_count": evaluation["optimizer_update_count"],
                    "variant_id": variant["variant_id"],
                    "trace_identity_sha256": variant["trace_identity_sha256"],
                    "video_file_sha256": variant["video_file_sha256"],
                }
    return None


def _verify_decode_rows(
    rows: Any, *, n_action_steps: int, checkpoint_update: int
) -> None:
    expected_starts = list(range(0, ROLLOUT_FRAMES, n_action_steps))
    expected_lengths = [
        min(n_action_steps, ROLLOUT_FRAMES - start) for start in expected_starts
    ]
    if (
        not isinstance(rows, list)
        or [row.get("decode_start_frame") for row in rows] != expected_starts
        or [row.get("executed_length") for row in rows] != expected_lengths
    ):
        raise ValueError("T20.44 decode starts or executed lengths drifted")
    for row, start, length in zip(rows, expected_starts, expected_lengths, strict=True):
        if (
            row.get("n_action_steps") != n_action_steps
            or row.get("checkpoint_update") != checkpoint_update
            or row.get("predicted_chunk_length") != CHUNK_SIZE
            or row.get("source_comparison_length")
            != min(CHUNK_SIZE, ROLLOUT_FRAMES - start)
            or row.get("unexecuted_tail_count") != CHUNK_SIZE - length
            or row.get("frozen_gate_identity_sha256") != FROZEN_GATE_IDENTITY
            or not isinstance(row.get("frozen_amended_gate_passed"), bool)
            or row.get("frozen_amended_gate_violation_count")
            != len(row.get("frozen_amended_gate_violations", []))
        ):
            raise ValueError("T20.44 decode evidence drifted")
        _sha(row.get("physical_action_chunk_sha256"))
        _sha(row.get("executed_action_sha256"))
        _sha(row.get("base_noise_sha256"))
        expected_seed = (
            20260901
            + row.get("checkpoint_update") * 100
            + row.get("n_action_steps") * 10
            + row.get("decode_start_frame")
        )
        if row.get("noise_seed") != expected_seed:
            raise ValueError("T20.44 decode noise seed drifted")


def _verify_comparison_rows(rows: Any, *, n_action_steps: int) -> None:
    if not isinstance(rows, list) or len(rows) != ROLLOUT_FRAMES:
        raise ValueError("T20.44 trace must contain 244 frames")
    phases = [phase for phase, count in PHASE_PLAN for _ in range(count)]
    for index, (row, phase) in enumerate(zip(rows, phases, strict=True)):
        if (
            row.get("frame_index") != index
            or row.get("phase") != phase
            or row.get("chunk_index") != index // n_action_steps
            or row.get("chunk_offset") != index % n_action_steps
        ):
            raise ValueError("T20.44 trace frame/chunk order drifted")
        for field in (
            "source_requested_action_rad",
            "source_applied_action_rad",
            "candidate_requested_action_rad",
            "candidate_applied_action_rad",
            "source_qpos_rad",
            "candidate_qpos_rad",
            "source_qvel_rad_s",
            "candidate_qvel_rad_s",
        ):
            _vector(row.get(field))
        _position(row.get("candidate_anchor_position_m"))
        if not isinstance(row.get("candidate_strict_contact"), bool):
            raise ValueError("T20.44 strict contact trace drifted")


def _trace_diagnostics(
    rows: list[dict[str, Any]], *, n_action_steps: int
) -> dict[str, Any]:
    _verify_comparison_rows(rows, n_action_steps=n_action_steps)
    source_action = np.asarray(
        [row["source_requested_action_rad"] for row in rows], dtype=np.float64
    )
    candidate_action = np.asarray(
        [row["candidate_requested_action_rad"] for row in rows], dtype=np.float64
    )
    source_qpos = np.asarray([row["source_qpos_rad"] for row in rows])
    candidate_qpos = np.asarray([row["candidate_qpos_rad"] for row in rows])
    action_error = np.abs(candidate_action - source_action)
    state_error = np.abs(candidate_qpos - source_qpos)
    return {
        "frame_count": ROLLOUT_FRAMES,
        "first_action_divergence": _first_divergence(
            rows, action_error, threshold=0.05
        ),
        "first_state_divergence": _first_divergence(rows, state_error, threshold=0.01),
        "trajectory_action_mean_absolute_error_rad": float(np.mean(action_error)),
        "trajectory_action_maximum_absolute_error_rad": float(np.max(action_error)),
        "trajectory_state_mean_absolute_error_rad": float(np.mean(state_error)),
        "initial_reset_maximum_state_error_rad": float(np.max(state_error[0])),
        "initial_reset_identical_within_1e_6": bool(np.max(state_error[0]) <= 1e-6),
        "strict_contact_frame_count": sum(
            row["candidate_strict_contact"] for row in rows
        ),
    }


def _first_divergence(
    rows: list[dict[str, Any]], errors: np.ndarray, *, threshold: float
) -> dict[str, Any] | None:
    names = (
        "shoulder_pan",
        "shoulder_lift",
        "elbow_flex",
        "wrist_flex",
        "wrist_roll",
        "gripper",
    )
    for index, row in enumerate(rows):
        joint = int(np.argmax(errors[index]))
        value = float(errors[index, joint])
        if value > threshold:
            return {
                "frame_index": index,
                "phase": row["phase"],
                "chunk_index": row["chunk_index"],
                "chunk_offset": row["chunk_offset"],
                "joint_name": names[joint],
                "absolute_error_rad": value,
                "threshold_rad": threshold,
            }
    return None


def _t20_38_runtime_receipt(closed_loop: dict[str, Any]) -> dict[str, Any]:
    margins = closed_loop.get("gate_margins")
    if not isinstance(margins, dict) or not margins:
        raise ValueError("T20.44 rollout lacks strict-v2 margins")
    if not all(isinstance(row.get("passed"), bool) for row in margins.values()):
        raise ValueError("T20.44 strict-v2 margin rows drifted")
    strict_success = closed_loop.get("simulation_semantic_strict_success")
    if strict_success is not all(row["passed"] for row in margins.values()):
        raise ValueError("T20.44 strict-v2 conjunction drifted")
    return sign_payload(
        {
            "schema_version": "scenesmith.t20_44_t20_38_runtime_margins.v1",
            "source_t20_38_receipt_identity_sha256": T20_38_RECEIPT_IDENTITY,
            "policy_independent_margin_vocabulary": True,
            "strict_v2_margins": margins,
            "strict_v2_passed": strict_success,
            "average_or_compensating_pass_allowed": False,
            "physical_proof": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def _source_episode_zero(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    for path in sorted(default_store_root(repo_root=root).glob("*.json")):
        payload = load_strict_json(path)
        if payload.get("episode_spec", {}).get("seed") == 0:
            frames = sorted(payload["frames"], key=lambda row: row["frame_index"])
            if len(frames) != ROLLOUT_FRAMES:
                raise ValueError("T20.44 source episode zero is incomplete")
            return (
                {
                    "path": path.relative_to(root).as_posix(),
                    "file_sha256": _sha_file(path),
                    "raw_rollout_identity_sha256": payload["raw_rollout"][
                        "record_identity_sha256"
                    ],
                },
                frames,
            )
    raise FileNotFoundError("T20.44 source episode zero is absent")


def _smolvla_config(*, SmolVLAConfig, FeatureType, NormalizationMode, PolicyFeature):
    return SmolVLAConfig(
        input_features={
            "observation.images.base_0_rgb": PolicyFeature(
                FeatureType.VISUAL, (3, 256, 256)
            ),
            "observation.images.left_wrist_0_rgb": PolicyFeature(
                FeatureType.VISUAL, (3, 256, 256)
            ),
            "observation.state": PolicyFeature(FeatureType.STATE, (6,)),
        },
        output_features={"action": PolicyFeature(FeatureType.ACTION, (6,))},
        device="mps",
        use_amp=False,
        chunk_size=50,
        n_action_steps=50,
        normalization_mapping={
            "VISUAL": NormalizationMode.IDENTITY,
            "STATE": NormalizationMode.MEAN_STD,
            "ACTION": NormalizationMode.MEAN_STD,
        },
        max_state_dim=32,
        max_action_dim=32,
        resize_imgs_with_padding=(512, 512),
        empty_cameras=0,
        adapt_to_pi_aloha=False,
        use_delta_joint_actions_aloha=False,
        tokenizer_max_length=48,
        num_steps=10,
        use_cache=True,
        freeze_vision_encoder=True,
        train_expert_only=True,
        train_state_proj=True,
        optimizer_lr=1e-4,
        optimizer_betas=(0.9, 0.95),
        optimizer_eps=1e-8,
        optimizer_weight_decay=1e-10,
        optimizer_grad_clip_norm=10.0,
        scheduler_warmup_steps=1000,
        scheduler_decay_steps=30000,
        scheduler_decay_lr=2.5e-6,
        vlm_model_name=str(VLM_SNAPSHOT_PATH),
        load_vlm_weights=True,
        add_image_special_tokens=False,
        attention_mode="cross_attn",
        prefix_length=0,
        pad_language_to="max_length",
        num_expert_layers=0,
        num_vlm_layers=16,
        self_attn_every_n_layers=2,
        expert_width_multiplier=0.75,
    )


def _render_mirror(*, trace_path: Path, video_path: Path, repo_root: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/robot_lab/render_rollout_mirror.py"),
            "--trace",
            trace_path.as_posix(),
            "--output-mp4",
            video_path.as_posix(),
            "--fps",
            "25",
        ],
        cwd=repo_root,
        check=True,
        env={
            **os.environ,
            "PYTHONPATH": (
                f"{repo_root / 'external/lerobot/src'}:"
                f"{repo_root / 'external/lerobot/.venv/lib/python3.12/site-packages'}:"
                f"{MUJOCO_SUPPORT_SITE_PACKAGES}"
            ),
        },
    )


def _require_active_time(owner: dict[str, Any], started_at: str) -> None:
    current = datetime.fromisoformat(started_at)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("T20.44 start time lacks UTC offset")
    if not (
        datetime.fromisoformat(owner["valid_from"])
        <= current
        <= datetime.fromisoformat(owner["valid_until"])
    ):
        raise ValueError("T20.44 owner authority is inactive")


def _require_remote_preservation(
    permit: dict[str, Any], acceptance: dict[str, Any], *, repo_root: Path
) -> None:
    if _git(repo_root, "branch", "--show-current") != BRANCH:
        raise ValueError("T20.44 run is on the wrong branch")
    head = _git(repo_root, "rev-parse", "HEAD")
    upstream = _git(repo_root, "rev-parse", "@{u}")
    if head != upstream:
        raise ValueError("T20.44 HEAD is not origin-confirmed")
    for ancestor in (
        permit["required_source_commit"],
        acceptance["authority_commit"],
    ):
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, head],
            cwd=repo_root,
            check=True,
        )
    dirty = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *[path.as_posix() for path in IMPLEMENTATION_SCOPED_PATHS],
            OWNER_GRANT_PATH.as_posix(),
            GATE_A_PATH.as_posix(),
            REQUEST_PATH.as_posix(),
            DECISION_PATH.as_posix(),
            RUNTIME_PREFLIGHT_PATH.as_posix(),
            PERMIT_PATH.as_posix(),
            SPEC_PATH.as_posix(),
            PRE_RUN_ACCEPTANCE_PATH.as_posix(),
            acceptance["reviewer_path"],
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if dirty.strip():
        raise ValueError("T20.44 scoped pre-run boundary is dirty")
    reviewer = repo_root / acceptance["reviewer_path"]
    if (
        not reviewer.is_file()
        or reviewer.is_symlink()
        or _sha_file(reviewer) != acceptance["reviewer_file_sha256"]
    ):
        raise ValueError("T20.44 reviewer decision bytes drifted")


def _file_tree(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"T20.44 output tree is absent or aliased: {root}")
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"T20.44 output tree contains a symlink: {path}")
        if path.is_file():
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha_file(path),
                }
            )
    if not rows:
        raise ValueError(f"T20.44 output tree is empty: {root}")
    return rows


def _cycle(loader):
    while True:
        yield from loader


def _verify_trainable_scope(policy: Any) -> list[Any]:
    allowed = (
        "model.vlm_with_expert.lm_expert.",
        "model.state_proj.",
        "model.action_in_proj.",
        "model.action_out_proj.",
        "model.action_time_mlp_in.",
        "model.action_time_mlp_out.",
    )
    rows = [
        (name, parameter)
        for name, parameter in policy.named_parameters()
        if parameter.requires_grad
    ]
    if not rows or any(
        not name.startswith(allowed) or str(parameter.device) != "mps:0"
        for name, parameter in rows
    ):
        raise ValueError("T20.44 SmolVLA trainable scope or device drifted")
    if any(not any(name.startswith(prefix) for name, _ in rows) for prefix in allowed):
        raise ValueError("T20.44 SmolVLA required trainable pathway is missing")
    if any(str(parameter.device) != "mps:0" for parameter in policy.parameters()):
        raise ValueError("T20.44 SmolVLA parameter CPU fallback detected")
    if any(str(buffer.device) != "mps:0" for buffer in policy.buffers()):
        raise ValueError("T20.44 SmolVLA buffer CPU fallback detected")
    return [parameter for _, parameter in rows]


def _seed_all(seed: int, torch: Any) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _scheduled_update(value: Any) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value not in CHECKPOINT_SCHEDULE
    ):
        raise ValueError("T20.44 update is outside the fixed schedule")
    return value


def _variant_id(n_action_steps: Any) -> str:
    if n_action_steps == 50:
        return "chunk_50"
    if n_action_steps == 10:
        return "receding_10"
    raise ValueError("T20.44 unsupported action-consumption variant")


def _finite_series(values: Any, *, expected: int, label: str) -> None:
    if (
        not isinstance(values, list)
        or len(values) != expected
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in values
        )
    ):
        raise ValueError(f"T20.44 {label} series drifted")


def _vector(value: Any) -> list[float]:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (6,) or not np.isfinite(array).all():
        raise ValueError("T20.44 expected a finite six-joint vector")
    return array.astype(float).tolist()


def _position(value: Any) -> list[float]:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,) or not np.isfinite(array).all():
        raise ValueError("T20.44 expected a finite xyz position")
    return array.astype(float).tolist()


def _sequence_sha(rows: list[dict[str, Any]], field: str) -> str:
    return hashlib.sha256(
        json.dumps(
            [row[field] for row in rows],
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _false_terminal_fields() -> dict[str, bool]:
    return {field: False for field in FALSE_TERMINAL_FIELDS}


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("T20.44 expected a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("T20.44 expected a SHA-256 digest") from error
    return value


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


__all__ = [
    "TRACE_SCHEMA_VERSION",
    "build_comparison_rows",
    "build_result",
    "build_run_summary",
    "build_scorecard",
    "build_trace",
    "run_authorized_attempt",
    "verify_all_outputs",
    "verify_result",
    "verify_run_summary",
    "verify_trace",
]
