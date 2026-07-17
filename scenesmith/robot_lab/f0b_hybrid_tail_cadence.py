"""One-use, no-training ACT hybrid-tail cadence evaluation for F0b."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import subprocess

from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np

from scenesmith.robot_lab.act_grasp_closed_loop import (
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    ROLLOUT_FRAMES,
    _evaluate,
    phase_for_frame,
    run_policy_grasp_closed_loop,
)
from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.authority_composer import (
    DEFAULT_AUTHORITY_SCOPE_ID,
    DEFAULT_AUTHORITY_SUBJECT_ID,
    build_authority_contract,
    build_capability_claim,
    build_composition_request,
    build_evidence_ref,
    compose_authority,
    require_global_decision,
    verify_authority_decision,
)
from scenesmith.robot_lab.geometry_derived_grasp_primitives import (
    has_valid_antipodal_contact,
)
from scenesmith.robot_lab.mujoco_anchor_grasp import OBJECT_ID
from scenesmith.robot_lab.scripted_grasp_episode_generation import default_store_root
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco, mujoco_to_lerobot
from scenesmith.robot_lab.strict_grasp import strict_grasp_spec_v2
from scenesmith.robot_lab.t20_43b_r1_act_contracts import (
    MUJOCO_SUPPORT_SITE_PACKAGES,
    R0_DATASET_REPO_ID,
    R0_DATASET_ROOT,
    STABLE_RUNNER_INTERPRETER,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
BRANCH = "codex/pi05-autolearn-loop"
TASK_ID = "F0b"
OWNER_AUTHORIZATION_SOURCE = (
    "owner_direct_chat_eight_hour_continue_authorization_2026_07_17"
)
OWNER_STATEMENT_RECORD = "Okay. I authorize all of this for the next eight hours."
TRAINING_SEED = 20260801
SIMULATION_SEED = 0
CHUNK_SIZE = 50
DECODE_STARTS = (0, 50, 100, 150, 176, 186, 196, 206, 216, 226, 236)
EXECUTED_LENGTHS = (50, 50, 50, 26, 10, 10, 10, 10, 10, 10, 8)
SELECTED_PREFIX_LENGTHS = (50, 50, 50, 50, 10, 10, 10, 10, 10, 10, 10)
TAIL_TRANSITION_FRAME = 176
MANUAL_DISCARD_COUNT = 24
TERMINAL_UNEXECUTED_COUNT = 2

SOURCE_BOUNDARY_COMMIT = "951c5254950b734677a6d185c227c56724182b58"
BRIEF_ACTIVATION_COMMIT = "fe552f02ffe59e133924a79d53df9806b4a92139"
F0A_IDENTITY = "278e8bc772dc879622a226abe22665d320421925045ad9b3cb1f88b1c31153a4"
R2_RUN_IDENTITY = "82a0608386375f029a56be8ca9f972bc0e83939d30ad286164db828aa22dc851"
R2_RESULT_IDENTITY = "bf2c8b466597ac23ff76ad88e8697b7b5d70a09b9016bc11442010243c984327"
R2_RETENTION_IDENTITY = (
    "e565e17a5d4f8a52c4d894d3d61f03cf4b38beaf1df0bec3b83ade7f05afc023"
)
R2_FINAL_IDENTITY = "be11a258b6662baa10341acac13fe09055cd4ded7c2eaba4236d466977dfac5e"
COMPARATOR_TRACE_IDENTITY = (
    "77bf82ce917c2a30cc3bfc915b887f0e6af98c8c8a397f022b633ccf23c7d19c"
)
CHECKPOINT_IDENTITY = "c77ee36250f921dbdfc7b19802ab8705c9795b298fa14d4a2b1825acf68451ab"
CHECKPOINT_CONFIG_SHA256 = (
    "1b2ba89880e421180962a0c862b37bfc854d16e5f8811e82210a64ecf6d09aaf"
)
CHECKPOINT_MODEL_SHA256 = (
    "673c87a5c411997e5a0e146702df95a0e301ba8585ec1cba64dca25b6d55170c"
)
CHECKPOINT_CONFIG_BYTES = 1714
CHECKPOINT_MODEL_BYTES = 206494928
SOURCE_EPISODE_FILE_SHA256 = (
    "586a3e67034a577bf046381837aebe68d3d5febdce6b1c51dbcb6f0be4968b54"
)
SOURCE_ROLLOUT_IDENTITY = (
    "9e186088c9ca82fa9c58cb6e3870f322a9c2a84405d5ea23152b822fb9d4abdb"
)
R0_STATISTICS_IDENTITY = (
    "02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae"
)
R0_RETENTION_IDENTITY = (
    "19d19fbaa315511fa0e7df736d3895089827da8f0b8a2aecd15a2a75885bd495"
)
LEROBOT_CHECKOUT_HEAD = "e40b58a8dfa9e7b86918c374791599d070518d11"
LEROBOT_CHECKOUT_TREE = "2fcde03d7b9920a4db01d12e0fe20704698ba5cf"
SO_ARM_CHECKOUT_HEAD = "fda892cba81032c46c40976a48c9ceadbf40a9ca"
SO_ARM_CHECKOUT_TREE = "3694b619d148dfeec39b4ee239a176db864ce424"
SO101_ASSET_TREE_IDENTITY = (
    "2cf012477d630936efe7045e52e83644d447ec7dd6762438beeb16fed14b5eb4"
)
EXPECTED_PYTHON_VERSION = "3.12.12"
EXPECTED_TORCH_VERSION = "2.11.0"
EXPECTED_MUJOCO_VERSION = "3.3.5"
EXPECTED_LEROBOT_VERSION = "0.6.1"

F0A_PATH = Path("configurations/robot_lab/f0a_chunk_phase_observability.json")
R2_RESULT_PATH = Path("configurations/robot_lab/t20_43c_r2_act_standard_result.json")
R2_RETENTION_PATH = Path(
    "configurations/robot_lab/t20_43c_r2_act_retention_receipt.json"
)
R2_FINAL_PATH = Path("configurations/robot_lab/t20_43c_r2_act_final_receipt.json")
R0_STATISTICS_PATH = Path("configurations/robot_lab/t20_42_r0_dataset_statistics.json")
R0_RETENTION_PATH = Path("configurations/robot_lab/t20_42_r0_retention_receipt.json")
R2_RUN_PATH = Path(
    "outputs/robot_lab/t20_43c_r2_act_replacement_run_001/run_summary.json"
)
COMPARATOR_TRACE_PATH = Path(
    "outputs/robot_lab/t20_43c_r2_act_replacement_run_001/rollouts/step_10000_chunk_50.json"
)
COMPARATOR_TRACE_FILE_SHA256 = (
    "c357f4e10d57c8cffde4a96ca3ac2dd1a9ce86e7e21210b85f0cbd0f8ff9bfb3"
)
SOURCE_EPISODE_PATH = Path(
    "outputs/robot_lab/t17_5b_raw_store/"
    "586a3e67034a577bf046381837aebe68d3d5febdce6b1c51dbcb6f0be4968b54.json"
)
CHECKPOINT_PATH = Path(
    "outputs/robot_lab/t20_43c_r2_act_replacement_run_001/checkpoints/step_10000"
)
OWNER_DIRECTION_PATH = Path(
    "docs/autonomous-workflow/owner-direction-2026-07-17-final-overnight.md"
)
BRIEF_PATH = Path("docs/briefs/232-f0b-hybrid-tail-cadence-evaluation.md")
RENDERER_PATH = Path("scripts/robot_lab/render_rollout_mirror_v2.py")
LEGACY_RENDERER_PATH = Path("scripts/robot_lab/render_rollout_mirror.py")
SO101_ASSET_PATH = Path("external/SO-ARM100/Simulation/SO101")

SPEC_PATH = Path("configurations/robot_lab/f0b_hybrid_tail_cadence_spec.json")
SMOKE_PATH = Path(
    "configurations/robot_lab/f0b_hybrid_tail_cadence_renderer_smoke.json"
)
OWNER_PATH = Path("configurations/robot_lab/f0b_hybrid_tail_cadence_owner_grant.json")
REQUEST_PATH = Path(
    "configurations/robot_lab/f0b_hybrid_tail_cadence_authority_request.json"
)
DECISION_PATH = Path(
    "configurations/robot_lab/f0b_hybrid_tail_cadence_authority_decision.json"
)
RUNTIME_PATH = Path(
    "configurations/robot_lab/f0b_hybrid_tail_cadence_runtime_preflight.json"
)
PERMIT_PATH = Path("configurations/robot_lab/f0b_hybrid_tail_cadence_permit.json")
ACCEPTANCE_PATH = Path(
    "configurations/robot_lab/f0b_hybrid_tail_cadence_pre_run_acceptance.json"
)
MARKER_PATH = Path("configurations/robot_lab/f0b_hybrid_tail_cadence_attempt.json")
TRACE_PATH = Path("configurations/robot_lab/f0b_hybrid_tail_cadence_trace.json")
RESULT_PATH = Path("configurations/robot_lab/f0b_hybrid_tail_cadence_result.json")
SCORECARD_PATH = Path("configurations/robot_lab/f0b_hybrid_tail_cadence_scorecard.json")
RETENTION_PATH = Path(
    "configurations/robot_lab/f0b_hybrid_tail_cadence_retention_receipt.json"
)
FINAL_PATH = Path("configurations/robot_lab/f0b_hybrid_tail_cadence_final_receipt.json")
FAILURE_PATH = Path(
    "configurations/robot_lab/f0b_hybrid_tail_cadence_terminal_failure.json"
)

RUN_ROOT = Path("outputs/robot_lab/f0b_hybrid_tail_cadence_run_001")
OUTPUT_TRACE_PATH = RUN_ROOT / "trace.json"
MIRROR_PATH = RUN_ROOT / "mirror.mp4"
MIRROR_MANIFEST_PATH = MIRROR_PATH.with_suffix(".manifest.json")
PROGRESS_PATH = RUN_ROOT / "progress.json"
SMOKE_ROOT = Path("outputs/robot_lab/f0b_hybrid_tail_cadence_renderer_smoke_001")
SMOKE_VIDEO_PATH = SMOKE_ROOT / "retained_chunk_50.mp4"
SMOKE_MANIFEST_PATH = SMOKE_VIDEO_PATH.with_suffix(".manifest.json")

SPEC_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_spec.v1"
SMOKE_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_renderer_smoke.v1"
OWNER_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_owner_grant.v1"
RUNTIME_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_runtime_preflight.v1"
PERMIT_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_permit.v1"
ACCEPTANCE_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_pre_run_acceptance.v1"
MARKER_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_attempt.v1"
TRACE_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_trace.v1"
RESULT_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_result.v1"
SCORECARD_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_scorecard.v1"
RETENTION_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_retention_receipt.v1"
FINAL_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_final_receipt.v1"
FAILURE_SCHEMA = "scenesmith.f0b_hybrid_tail_cadence_terminal_failure.v1"

IMPLEMENTATION_PATHS = (
    Path("scenesmith/robot_lab/f0b_hybrid_tail_cadence.py"),
    Path("tests/unit/test_f0b_hybrid_tail_cadence.py"),
    RENDERER_PATH,
    BRIEF_PATH,
    SPEC_PATH,
)
AUTHORITY_PATHS = (OWNER_PATH, REQUEST_PATH, DECISION_PATH, RUNTIME_PATH, PERMIT_PATH)
TERMINAL_PATHS = (
    TRACE_PATH,
    RESULT_PATH,
    SCORECARD_PATH,
    RETENTION_PATH,
    FINAL_PATH,
    FAILURE_PATH,
)
FALSE_AUTHORITY_FIELDS = (
    "optimizer_created",
    "optimizer_training",
    "dataset_mutated",
    "statistics_changed",
    "network_accessed",
    "external_compute_started",
    "brev_compute_started",
    "hardware_accessed",
    "camera_accessed",
    "serial_accessed",
    "physical_motion",
    "physical_actuation",
    "physical_transfer_ready",
    "promotion_eligible",
    "freeze_tag_authorized",
)
SIMULATION_PREREQUISITES = (
    "required_training_authority_present",
    "structural_contract_valid",
    "executable_stack_valid",
    "coordinate_contract_valid",
    "normalization_contract_valid",
    "experience_compiler_valid",
    "required_simulation_properties_available",
)


class HybridTailQueueAdapter:
    """Pure queue consumer implementing the exact F0b decode schedule."""

    def __init__(
        self, decode_chunk: Callable[[dict[str, np.ndarray], np.ndarray], Any]
    ):
        self.decode_chunk = decode_chunk
        self.queue: deque[np.ndarray] = deque()
        self.frame_index = 0
        self.decode_rows: list[dict[str, Any]] = []
        self.discard_events: list[dict[str, Any]] = []

    def __call__(self, images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        if self.frame_index >= ROLLOUT_FRAMES:
            raise ValueError("F0b adapter called beyond the frozen rollout")
        if self.frame_index == TAIL_TRANSITION_FRAME:
            self._discard_tail_transition()
        if not self.queue:
            self._decode(images, state)
        action = self.queue.popleft()
        self.frame_index += 1
        return action.copy()

    def _decode(self, images: dict[str, np.ndarray], state: np.ndarray) -> None:
        ordinal = len(self.decode_rows)
        if ordinal >= len(DECODE_STARTS) or self.frame_index != DECODE_STARTS[ordinal]:
            raise ValueError("F0b decode start drifted")
        chunk = np.asarray(self.decode_chunk(images, state), dtype=np.float64)
        if chunk.shape != (CHUNK_SIZE, 6) or not np.isfinite(chunk).all():
            raise ValueError("F0b decoder emitted an invalid 50x6 action chunk")
        selected = SELECTED_PREFIX_LENGTHS[ordinal]
        executed = EXECUTED_LENGTHS[ordinal]
        self.queue.extend(row.copy() for row in chunk[:selected])
        self.decode_rows.append(
            {
                "decode_ordinal": ordinal,
                "decode_start_frame": self.frame_index,
                "predicted_chunk_length": CHUNK_SIZE,
                "selected_prefix_length": selected,
                "executed_length": executed,
                "nonselected_prediction_count": CHUNK_SIZE - selected,
                "physical_action_chunk_rad": chunk.astype(float).tolist(),
                "physical_action_chunk_sha256": _rows_sha(chunk),
                "selected_prefix_sha256": _rows_sha(chunk[:selected]),
            }
        )

    def _discard_tail_transition(self) -> None:
        if self.discard_events or len(self.queue) != MANUAL_DISCARD_COUNT:
            raise ValueError("F0b frame-176 queued-tail coverage drifted")
        rows = np.asarray(list(self.queue), dtype=np.float64)
        self.queue.clear()
        self.discard_events.append(
            {
                "frame_index": TAIL_TRANSITION_FRAME,
                "source_decode_start_frame": 150,
                "discarded_action_count": MANUAL_DISCARD_COUNT,
                "discarded_action_rows_rad": rows.astype(float).tolist(),
                "discarded_action_sha256": _rows_sha(rows),
                "manual_queue_reset": True,
            }
        )

    def finalize(self) -> dict[str, Any]:
        if self.frame_index != ROLLOUT_FRAMES:
            raise ValueError("F0b adapter did not execute 244 frames")
        if len(self.decode_rows) != len(DECODE_STARTS) or len(self.discard_events) != 1:
            raise ValueError("F0b adapter evidence coverage drifted")
        if len(self.queue) != TERMINAL_UNEXECUTED_COUNT:
            raise ValueError("F0b terminal selected-tail coverage drifted")
        rows = np.asarray(list(self.queue), dtype=np.float64)
        evidence = {
            "frame_index_after_rollout": ROLLOUT_FRAMES,
            "source_decode_start_frame": DECODE_STARTS[-1],
            "unexecuted_selected_action_count": TERMINAL_UNEXECUTED_COUNT,
            "unexecuted_selected_action_rows_rad": rows.astype(float).tolist(),
            "unexecuted_selected_action_sha256": _rows_sha(rows),
        }
        verify_adapter_evidence(
            decode_rows=self.decode_rows,
            discard_events=self.discard_events,
            terminal_unexecuted=evidence,
        )
        return evidence


class ACTChunkDecoder:
    """Observation-only ACT decoder; no phase, progress, or source actions."""

    def __init__(
        self, *, policy: Any, preprocessor: Any, postprocessor: Any, torch: Any
    ):
        self.policy = policy
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor
        self.torch = torch

    def __call__(self, images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
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
        }
        processed = self.preprocessor(observation)
        with torch.no_grad():
            normalized = self.policy.predict_action_chunk(processed).squeeze(0)
            canonical = self.postprocessor(normalized)
        values = canonical.detach().cpu().float().numpy()
        if values.shape != (CHUNK_SIZE, 6) or not np.isfinite(values).all():
            raise ValueError("F0b ACT emitted an invalid normalized action chunk")
        return np.asarray(
            [lerobot_to_mujoco(row.tolist()) for row in values], dtype=np.float64
        )


def verify_schedule(
    *, decode_starts: Any, executed_lengths: Any, selected_prefix_lengths: Any
) -> None:
    if (
        decode_starts != list(DECODE_STARTS)
        or executed_lengths != list(EXECUTED_LENGTHS)
        or selected_prefix_lengths != list(SELECTED_PREFIX_LENGTHS)
        or sum(executed_lengths) != ROLLOUT_FRAMES
        or selected_prefix_lengths[3] - executed_lengths[3] != MANUAL_DISCARD_COUNT
        or selected_prefix_lengths[-1] - executed_lengths[-1]
        != TERMINAL_UNEXECUTED_COUNT
    ):
        raise ValueError("F0b frozen hybrid schedule drifted")


def verify_adapter_evidence(
    *, decode_rows: Any, discard_events: Any, terminal_unexecuted: Any
) -> None:
    if not isinstance(decode_rows, list) or len(decode_rows) != len(DECODE_STARTS):
        raise ValueError("F0b decode evidence coverage drifted")
    for ordinal, row in enumerate(decode_rows):
        expected_keys = {
            "decode_ordinal",
            "decode_start_frame",
            "predicted_chunk_length",
            "selected_prefix_length",
            "executed_length",
            "nonselected_prediction_count",
            "physical_action_chunk_rad",
            "physical_action_chunk_sha256",
            "selected_prefix_sha256",
        }
        if not isinstance(row, dict) or set(row) != expected_keys:
            raise ValueError("F0b decode row schema drifted")
        chunk = _matrix(row["physical_action_chunk_rad"], rows=CHUNK_SIZE)
        selected = SELECTED_PREFIX_LENGTHS[ordinal]
        if (
            row["decode_ordinal"] != ordinal
            or row["decode_start_frame"] != DECODE_STARTS[ordinal]
            or row["predicted_chunk_length"] != CHUNK_SIZE
            or row["selected_prefix_length"] != selected
            or row["executed_length"] != EXECUTED_LENGTHS[ordinal]
            or row["nonselected_prediction_count"] != CHUNK_SIZE - selected
            or row["physical_action_chunk_sha256"] != _rows_sha(chunk)
            or row["selected_prefix_sha256"] != _rows_sha(chunk[:selected])
        ):
            raise ValueError("F0b decode row derivation drifted")
    if not isinstance(discard_events, list) or len(discard_events) != 1:
        raise ValueError("F0b discard evidence coverage drifted")
    discard = discard_events[0]
    discarded = _matrix(
        discard.get("discarded_action_rows_rad"), rows=MANUAL_DISCARD_COUNT
    )
    source_chunk = _matrix(decode_rows[3]["physical_action_chunk_rad"], rows=CHUNK_SIZE)
    expected_discard = source_chunk[EXECUTED_LENGTHS[3] : SELECTED_PREFIX_LENGTHS[3]]
    if (
        discard.get("frame_index") != TAIL_TRANSITION_FRAME
        or discard.get("source_decode_start_frame") != 150
        or discard.get("discarded_action_count") != MANUAL_DISCARD_COUNT
        or discard.get("manual_queue_reset") is not True
        or not np.array_equal(discarded, expected_discard)
        or discard.get("discarded_action_sha256") != _rows_sha(discarded)
    ):
        raise ValueError("F0b discard evidence drifted")
    if not isinstance(terminal_unexecuted, dict):
        raise ValueError("F0b terminal unexecuted evidence is absent")
    terminal = _matrix(
        terminal_unexecuted.get("unexecuted_selected_action_rows_rad"),
        rows=TERMINAL_UNEXECUTED_COUNT,
    )
    final_chunk = _matrix(decode_rows[-1]["physical_action_chunk_rad"], rows=CHUNK_SIZE)
    expected_terminal = final_chunk[EXECUTED_LENGTHS[-1] : SELECTED_PREFIX_LENGTHS[-1]]
    if (
        terminal_unexecuted.get("frame_index_after_rollout") != ROLLOUT_FRAMES
        or terminal_unexecuted.get("source_decode_start_frame") != DECODE_STARTS[-1]
        or terminal_unexecuted.get("unexecuted_selected_action_count")
        != TERMINAL_UNEXECUTED_COUNT
        or not np.array_equal(terminal, expected_terminal)
        or terminal_unexecuted.get("unexecuted_selected_action_sha256")
        != _rows_sha(terminal)
    ):
        raise ValueError("F0b terminal unexecuted evidence drifted")


def build_spec(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = _load_verified_sources(root)
    source_refs = []
    for label, relative, identity in (
        ("f0a_result", F0A_PATH, F0A_IDENTITY),
        ("r2_result", R2_RESULT_PATH, R2_RESULT_IDENTITY),
        ("r2_retention", R2_RETENTION_PATH, R2_RETENTION_IDENTITY),
        ("r2_final", R2_FINAL_PATH, R2_FINAL_IDENTITY),
        ("r2_run", R2_RUN_PATH, R2_RUN_IDENTITY),
        ("comparator_trace", COMPARATOR_TRACE_PATH, COMPARATOR_TRACE_IDENTITY),
        ("r0_statistics", R0_STATISTICS_PATH, R0_STATISTICS_IDENTITY),
        ("r0_retention", R0_RETENTION_PATH, R0_RETENTION_IDENTITY),
    ):
        source_refs.append(_file_ref(root, label, root / relative, identity))
    source_path = root / sources["comparator"]["source_episode_ref"]["path"]
    source_refs.append(
        _file_ref(root, "source_episode", source_path, SOURCE_ROLLOUT_IDENTITY)
    )
    for label, relative in (
        (
            "act_model_source",
            Path("external/lerobot/src/lerobot/policies/act/modeling_act.py"),
        ),
        (
            "act_processor_source",
            Path("external/lerobot/src/lerobot/policies/act/processor_act.py"),
        ),
        (
            "act_configuration_source",
            Path("external/lerobot/src/lerobot/policies/act/configuration_act.py"),
        ),
        (
            "lerobot_pretrained_source",
            Path("external/lerobot/src/lerobot/policies/pretrained.py"),
        ),
        ("closed_loop_source", Path("scenesmith/robot_lab/act_grasp_closed_loop.py")),
        ("coordinate_source", Path("scenesmith/robot_lab/so101_coordinates.py")),
        (
            "geometry_source",
            Path("scenesmith/robot_lab/geometry_derived_grasp_primitives.py"),
        ),
        ("mujoco_anchor_source", Path("scenesmith/robot_lab/mujoco_anchor_grasp.py")),
        ("mujoco_export_source", Path("scenesmith/robot_lab/mujoco_export.py")),
        ("scene_spec_source", Path("scenesmith/robot_lab/spec.py")),
        (
            "source_episode_generator",
            Path("scenesmith/robot_lab/scripted_grasp_episode_generation.py"),
        ),
        ("strict_v2_source", Path("scenesmith/robot_lab/strict_grasp.py")),
        ("renderer_source", RENDERER_PATH),
        ("legacy_renderer_source", LEGACY_RENDERER_PATH),
        ("artifact_contract_source", Path("scenesmith/robot_lab/artifact_contract.py")),
        (
            "authority_composer_source",
            Path("scenesmith/robot_lab/authority_composer.py"),
        ),
        (
            "f0b_implementation_source",
            Path("scenesmith/robot_lab/f0b_hybrid_tail_cadence.py"),
        ),
        ("f0b_test_source", Path("tests/unit/test_f0b_hybrid_tail_cadence.py")),
        ("brief_source", BRIEF_PATH),
        ("task_ordering_source", OWNER_DIRECTION_PATH),
    ):
        source_refs.append(_file_ref(root, label, root / relative))
    checkpoint_tree = _file_tree(root / CHECKPOINT_PATH)
    if _tree_identity(checkpoint_tree) != CHECKPOINT_IDENTITY:
        raise ValueError("F0b checkpoint tree identity drifted")
    if checkpoint_tree != [
        {
            "path": "config.json",
            "sha256": CHECKPOINT_CONFIG_SHA256,
            "size_bytes": CHECKPOINT_CONFIG_BYTES,
        },
        {
            "path": "model.safetensors",
            "sha256": CHECKPOINT_MODEL_SHA256,
            "size_bytes": CHECKPOINT_MODEL_BYTES,
        },
    ]:
        raise ValueError("F0b checkpoint file inventory drifted")
    asset_tree = _file_tree(root / SO101_ASSET_PATH)
    if _tree_identity(asset_tree) != SO101_ASSET_TREE_IDENTITY:
        raise ValueError("F0b SO-101 scene-asset tree identity drifted")
    dependency_revisions = {
        "lerobot": _dependency_revision(
            root / "external/lerobot",
            expected_head=LEROBOT_CHECKOUT_HEAD,
            expected_tree=LEROBOT_CHECKOUT_TREE,
        ),
        "so_arm_100": _dependency_revision(
            root / "external/SO-ARM100",
            expected_head=SO_ARM_CHECKOUT_HEAD,
            expected_tree=SO_ARM_CHECKOUT_TREE,
        ),
    }
    payload = {
        "schema_version": SPEC_SCHEMA,
        "task_id": TASK_ID,
        "source_boundary_commit": SOURCE_BOUNDARY_COMMIT,
        "brief_activation_commit": BRIEF_ACTIVATION_COMMIT,
        "source_refs": sorted(source_refs, key=lambda row: row["label"]),
        "checkpoint": {
            "path": CHECKPOINT_PATH.as_posix(),
            "identity_sha256": CHECKPOINT_IDENTITY,
            "tree": checkpoint_tree,
            "optimizer_update_count": 10000,
            "load_count": 1,
        },
        "dependency_revisions": dependency_revisions,
        "scene_asset_tree": {
            "path": SO101_ASSET_PATH.as_posix(),
            "identity_sha256": SO101_ASSET_TREE_IDENTITY,
            "files": asset_tree,
        },
        "source_episode_ref": sources["comparator"]["source_episode_ref"],
        "runtime": {
            "interpreter": STABLE_RUNNER_INTERPRETER.as_posix(),
            "mujoco_support_site_packages": str(MUJOCO_SUPPORT_SITE_PACKAGES),
            "device": "mps",
            "dtype": "float32",
            "offline_only": True,
        },
        "evaluation": {
            "training_seed_before_policy_construction": TRAINING_SEED,
            "simulation_seed": SIMULATION_SEED,
            "episode_count": 1,
            "frame_count": ROLLOUT_FRAMES,
            "decode_starts": list(DECODE_STARTS),
            "executed_lengths": list(EXECUTED_LENGTHS),
            "selected_prefix_lengths": list(SELECTED_PREFIX_LENGTHS),
            "manual_queue_reset_count": 1,
            "manual_discard_frame": TAIL_TRANSITION_FRAME,
            "manual_discard_count": MANUAL_DISCARD_COUNT,
            "terminal_unexecuted_selected_count": TERMINAL_UNEXECUTED_COUNT,
            "strict_v2_oracle_unchanged": True,
            "release_clearance_basis": FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
            "baseline_rerun": False,
            "full_decoded_chunks_retained": True,
            "full_observed_frames_retained": True,
            "signed_mp4_required": True,
        },
        "decision": {
            "pass_requires_strict_v2_conjunction": True,
            "pass_routes_to_separate_kit_fold_f2_decision": True,
            "failure_is_terminal_for_f0b": True,
            "infrastructure_failure_is_not_policy_negative": True,
            "retry_authorized": False,
            "corrective_training_selected": False,
            "single_corrective_rung_consumed": False,
        },
        "training_lock": "closed",
        "checkpoint_tensor_read": False,
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "simulation_rollout": False,
        "live_rendering": False,
        **_false_fields(),
    }
    verify_schedule(
        decode_starts=payload["evaluation"]["decode_starts"],
        executed_lengths=payload["evaluation"]["executed_lengths"],
        selected_prefix_lengths=payload["evaluation"]["selected_prefix_lengths"],
    )
    return sign_payload(payload)


def verify_spec(payload: dict[str, Any], *, repo_root: Path = REPO_ROOT) -> None:
    verify_signed_payload(payload, label="F0b spec")
    if payload != build_spec(repo_root=repo_root):
        raise ValueError("F0b spec drifted from frozen sources")


def write_spec(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = build_spec(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / SPEC_PATH, result)
    return result


def build_owner_grant(
    *,
    spec: dict[str, Any],
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
) -> dict[str, Any]:
    verify_signed_payload(spec, label="F0b owner source spec")
    start, stop = _window(valid_from, valid_until)
    return sign_payload(
        {
            "schema_version": OWNER_SCHEMA,
            "task_id": TASK_ID,
            "authorization_id": "f0b_one_retained_act_hybrid_tail_cadence_evaluation",
            "authorization_source": OWNER_AUTHORIZATION_SOURCE,
            "owner_statement_record": OWNER_STATEMENT_RECORD,
            "task_ordering_source": OWNER_DIRECTION_PATH.as_posix(),
            "subject_id": DEFAULT_AUTHORITY_SUBJECT_ID,
            "scope_id": DEFAULT_AUTHORITY_SCOPE_ID,
            "required_source_commit": _commit(required_source_commit),
            "spec_identity_sha256": spec["identity_sha256"],
            "authorized_actions": [
                "create_one_attempt_marker",
                "read_one_hash_bound_act_checkpoint",
                "construct_and_load_one_act_policy",
                "execute_one_seed_0_hybrid_tail_cadence_simulation_rollout",
                "render_one_signed_mirror",
                "preserve_one_terminal_evidence_bundle",
            ],
            "authorized_attempt_count": 1,
            "optimizer_authorized": False,
            "training_authorized": False,
            "retry_authorized": False,
            "simulation_only": True,
            "issued_at": start.isoformat(),
            "valid_from": start.isoformat(),
            "valid_until": stop.isoformat(),
            **_false_fields(),
        }
    )


def verify_owner_grant(payload: dict[str, Any], *, spec: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="F0b owner grant")
    expected = build_owner_grant(
        spec=spec,
        required_source_commit=payload.get("required_source_commit"),
        valid_from=payload.get("valid_from"),
        valid_until=payload.get("valid_until"),
    )
    if payload != expected:
        raise ValueError("F0b owner grant drifted")


def build_central_authority(
    *, spec: dict[str, Any], owner: dict[str, Any], smoke: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    verify_owner_grant(owner, spec=spec)
    verify_signed_payload(smoke, label="F0b central renderer smoke")
    if (
        smoke.get("schema_version") != SMOKE_SCHEMA
        or smoke.get("task_id") != TASK_ID
        or smoke.get("new_rendering_executed") is not True
        or any(
            smoke.get(field) is not False
            for field in (
                "checkpoint_tensor_read",
                "model_constructed",
                "model_inference",
                "simulation_rollout",
                "optimizer_created",
                "optimizer_training",
            )
        )
    ):
        raise ValueError("F0b central renderer-smoke evidence drifted")
    requirements = {
        row["prerequisite_id"]: row
        for row in build_authority_contract()["prerequisites"]
    }
    claims = []
    duration = int(
        (
            datetime.fromisoformat(owner["valid_until"])
            - datetime.fromisoformat(owner["valid_from"])
        ).total_seconds()
    )
    evidence = {
        "required_training_authority_present": (
            "f0b_owner_grant",
            owner["schema_version"],
            owner["identity_sha256"],
        ),
        "structural_contract_valid": (
            "f0b_hybrid_tail_cadence_spec",
            spec["schema_version"],
            spec["identity_sha256"],
        ),
        "executable_stack_valid": (
            "f0b_renderer_smoke",
            smoke["schema_version"],
            smoke["identity_sha256"],
        ),
        "coordinate_contract_valid": (
            "f0b_source_bound_coordinate_contract",
            spec["schema_version"],
            spec["identity_sha256"],
        ),
        "normalization_contract_valid": (
            "t20_42_r0_mean_std_statistics",
            "scenesmith.t20_42_r0_mean_std_statistics.v1",
            R0_STATISTICS_IDENTITY,
        ),
        "experience_compiler_valid": (
            "t20_42_r0_retention_receipt",
            "scenesmith.t20_42_r0_retention_receipt.v1",
            R0_RETENTION_IDENTITY,
        ),
        "required_simulation_properties_available": (
            "t20_43c_r2_act_result",
            "scenesmith.t20_43b_r1_act_result.v1",
            R2_RESULT_IDENTITY,
        ),
    }
    if set(evidence) != set(SIMULATION_PREREQUISITES):
        raise ValueError("F0b central evidence coverage drifted")
    for prerequisite_id in SIMULATION_PREREQUISITES:
        requirement = requirements[prerequisite_id]
        provenance = requirement["allowed_provenance_classes"][0]
        artifact_kind, schema_version, identity = evidence[prerequisite_id]
        claims.append(
            build_capability_claim(
                claim_id=f"f0b_{prerequisite_id}",
                capability_id=prerequisite_id,
                value=True,
                subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                provenance_class=provenance,
                issuer=requirement["authorized_issuers"][0],
                validity={
                    "observed_at": owner["valid_from"],
                    "valid_from": owner["valid_from"],
                    "valid_until": owner["valid_until"],
                    "max_age_seconds": duration,
                },
                evidence_refs=[
                    build_evidence_ref(
                        artifact_kind=artifact_kind,
                        artifact_schema_version=schema_version,
                        artifact_identity_sha256=identity,
                        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
                        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
                        provenance_class=provenance,
                    )
                ],
            )
        )
    request = build_composition_request(
        subject_id=DEFAULT_AUTHORITY_SUBJECT_ID,
        scope_id=DEFAULT_AUTHORITY_SCOPE_ID,
        evaluation_time=owner["valid_from"],
        claims=claims,
        composition_mode="production",
    )
    decision = compose_authority(request)
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    if decision.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("F0b central authority exceeded its prerequisite")
    return request, decision


def build_renderer_smoke_receipt(
    *, manifest: dict[str, Any], video_file_sha256: str
) -> dict[str, Any]:
    verify_signed_payload(manifest, label="F0b smoke mirror manifest")
    video_sha256 = _sha(video_file_sha256)
    _verify_mirror_manifest(
        manifest,
        trace_path=COMPARATOR_TRACE_PATH,
        trace_identity_sha256=COMPARATOR_TRACE_IDENTITY,
        output_path=SMOKE_VIDEO_PATH,
        output_sha256=video_sha256,
    )
    return sign_payload(
        {
            "schema_version": SMOKE_SCHEMA,
            "task_id": TASK_ID,
            "source_trace_path": COMPARATOR_TRACE_PATH.as_posix(),
            "source_trace_identity_sha256": COMPARATOR_TRACE_IDENTITY,
            "renderer_path": RENDERER_PATH.as_posix(),
            "runner_interpreter": STABLE_RUNNER_INTERPRETER.as_posix(),
            "video_path": SMOKE_VIDEO_PATH.as_posix(),
            "video_file_sha256": video_sha256,
            "manifest_path": SMOKE_MANIFEST_PATH.as_posix(),
            "manifest_identity_sha256": manifest["identity_sha256"],
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_inference": False,
            "simulation_rollout": False,
            "new_rendering_executed": True,
            **_false_fields(),
        }
    )


def build_runtime_preflight(
    *,
    spec: dict[str, Any],
    owner: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    smoke: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    verify_owner_grant(owner, spec=spec)
    verify_authority_decision(decision, request=request)
    require_global_decision(
        decision, request=request, decision_id="simulation_training_ready"
    )
    verify_signed_payload(smoke, label="F0b renderer smoke")
    _verify_snapshot(snapshot, owner=owner, smoke=smoke)
    return sign_payload(
        {
            "schema_version": RUNTIME_SCHEMA,
            "task_id": TASK_ID,
            "spec_identity_sha256": spec["identity_sha256"],
            "owner_identity_sha256": owner["identity_sha256"],
            "authority_request_identity_sha256": request["identity_sha256"],
            "authority_decision_identity_sha256": decision["identity_sha256"],
            "renderer_smoke_identity_sha256": smoke["identity_sha256"],
            "snapshot": snapshot,
            "checkpoint_hash_verified_without_tensor_deserialization": True,
            "outputs_absent_and_unaliased": True,
            "optimizer_authorized": False,
            "training_authorized": False,
            **_false_fields(),
        }
    )


def build_permit(
    *,
    spec: dict[str, Any],
    owner: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    smoke: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    expected_runtime = build_runtime_preflight(
        spec=spec,
        owner=owner,
        request=request,
        decision=decision,
        smoke=smoke,
        snapshot=runtime.get("snapshot"),
    )
    if runtime != expected_runtime:
        raise ValueError("F0b runtime preflight drifted")
    return sign_payload(
        {
            "schema_version": PERMIT_SCHEMA,
            "task_id": TASK_ID,
            "required_source_commit": owner["required_source_commit"],
            "spec_identity_sha256": spec["identity_sha256"],
            "owner_identity_sha256": owner["identity_sha256"],
            "authority_decision_identity_sha256": decision["identity_sha256"],
            "runtime_preflight_identity_sha256": runtime["identity_sha256"],
            "authorized_attempt_count": 1,
            "checkpoint_identity_sha256": CHECKPOINT_IDENTITY,
            "decode_starts": list(DECODE_STARTS),
            "executed_lengths": list(EXECUTED_LENGTHS),
            "attempt_marker_path": MARKER_PATH.as_posix(),
            "marker_precedes_checkpoint_tensor_read": True,
            "one_model_load": True,
            "one_seed_0_rollout": True,
            "optimizer_authorized": False,
            "training_authorized": False,
            "retry_authorized": False,
            **_false_fields(),
        }
    )


def build_acceptance(
    *,
    permit: dict[str, Any],
    authority_commit: str,
    reviewer_decision_id: str,
    reviewer_path: str,
    reviewer_file_sha256: str,
) -> dict[str, Any]:
    verify_signed_payload(permit, label="F0b acceptance permit")
    return sign_payload(
        {
            "schema_version": ACCEPTANCE_SCHEMA,
            "task_id": TASK_ID,
            "decision": "ACCEPT_ONE_F0B_HYBRID_TAIL_CADENCE_EVALUATION",
            "permit_identity_sha256": permit["identity_sha256"],
            "authority_commit": _commit(authority_commit),
            "reviewer_decision_id": str(reviewer_decision_id),
            "reviewer_path": _safe_relative(reviewer_path),
            "reviewer_file_sha256": _sha(reviewer_file_sha256),
            "attempt_marker_exists": False,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_inference": False,
            "simulation_rollout": False,
            "retry_authorized": False,
            **_false_fields(),
        }
    )


def build_marker(
    *, permit: dict[str, Any], source_commit: str, started_at: str
) -> dict[str, Any]:
    started = _aware_time(started_at, "attempt start")
    return sign_payload(
        {
            "schema_version": MARKER_SCHEMA,
            "task_id": TASK_ID,
            "permit_identity_sha256": permit["identity_sha256"],
            "source_commit": _commit(source_commit),
            "started_at": started.isoformat(),
            "attempt_ordinal": 1,
            "permit_consumed": True,
            "created_before_checkpoint_tensor_read": True,
            "created_before_model_construction": True,
            "created_before_model_inference": True,
            "created_before_simulation_rollout": True,
            "retry_authorized": False,
            "checkpoint_tensor_read": False,
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "simulation_rollout": False,
            **_false_fields(),
        }
    )


def build_comparison_rows(
    *, source_frames: list[dict[str, Any]], candidate_frames: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if len(source_frames) != ROLLOUT_FRAMES or len(candidate_frames) != ROLLOUT_FRAMES:
        raise ValueError("F0b comparison frame coverage drifted")
    requirement = strict_grasp_spec_v2()["antipodal_contact_requirement"]
    rows = []
    for index, (source, candidate) in enumerate(
        zip(source_frames, candidate_frames, strict=True)
    ):
        ordinal, start, offset = _chunk_location(index)
        if source.get("source_phase") != phase_for_frame(index) or candidate.get(
            "phase"
        ) != phase_for_frame(index):
            raise ValueError("F0b comparison phase drifted")
        rows.append(
            {
                "frame_index": index,
                "phase": phase_for_frame(index),
                "decode_ordinal": ordinal,
                "decode_start_frame": start,
                "chunk_offset": offset,
                "source_requested_action_rad": _vector6(
                    source["actions"]["requested"]["values"]
                ),
                "source_applied_action_rad": _vector6(
                    source["actions"]["sent"]["values"]
                ),
                "candidate_requested_action_rad": _vector6(
                    candidate["policy_requested_action"]
                ),
                "candidate_applied_action_rad": _vector6(
                    candidate["policy_applied_action"]
                ),
                "source_qpos_rad": _vector6(
                    source["observations"]["joint_position_mujoco_rad"]
                ),
                "candidate_qpos_rad": _vector6(candidate["mujoco_qpos"]),
                "source_qvel_rad_s": _vector6(
                    source["observations"]["joint_velocity_mujoco_rad_s"]
                ),
                "candidate_qvel_rad_s": _vector6(candidate["mujoco_qvel"]),
                "candidate_anchor_position_m": _vector3(
                    candidate["cube_positions_m"][OBJECT_ID]
                ),
                "candidate_strict_contact": bool(
                    has_valid_antipodal_contact(candidate, requirement)
                ),
            }
        )
    _verify_comparison_rows(rows)
    return rows


def build_trace(
    *,
    spec_identity_sha256: str,
    checkpoint_ref: dict[str, Any],
    source_episode_ref: dict[str, Any],
    comparator_trace_ref: dict[str, Any],
    comparisons: list[dict[str, Any]],
    observed_frames: list[dict[str, Any]],
    decode_rows: list[dict[str, Any]],
    discard_events: list[dict[str, Any]],
    terminal_unexecuted: dict[str, Any],
    closed_loop: dict[str, Any],
) -> dict[str, Any]:
    verify_adapter_evidence(
        decode_rows=decode_rows,
        discard_events=discard_events,
        terminal_unexecuted=terminal_unexecuted,
    )
    _verify_comparison_rows(comparisons)
    replay = replay_strict_v2(observed_frames=observed_frames, closed_loop=closed_loop)
    requested_sha = _sequence_sha(comparisons, "candidate_requested_action_rad")
    applied_sha = _sequence_sha(comparisons, "candidate_applied_action_rad")
    source_ref = _source_ref(source_episode_ref)
    expected_source_ref = {
        "path": SOURCE_EPISODE_PATH.as_posix(),
        "file_sha256": SOURCE_EPISODE_FILE_SHA256,
        "raw_rollout_identity_sha256": SOURCE_ROLLOUT_IDENTITY,
    }
    comparator_ref = _source_ref(comparator_trace_ref)
    expected_comparator_ref = {
        "path": COMPARATOR_TRACE_PATH.as_posix(),
        "file_sha256": COMPARATOR_TRACE_FILE_SHA256,
        "identity_sha256": COMPARATOR_TRACE_IDENTITY,
    }
    if source_ref != expected_source_ref or comparator_ref != expected_comparator_ref:
        raise ValueError("F0b source/comparator linkage drifted")
    if closed_loop.get("policy_action_sequence_sha256") != requested_sha:
        raise ValueError("F0b closed-loop action linkage drifted")
    payload = sign_payload(
        {
            "schema_version": TRACE_SCHEMA,
            "task_id": TASK_ID,
            "adapter_id": "hybrid_tail_chunk_50_to_10",
            "seed": SIMULATION_SEED,
            "spec_identity_sha256": _sha(spec_identity_sha256),
            "checkpoint_ref": _checkpoint_ref(checkpoint_ref),
            "source_episode_ref": source_ref,
            "comparator_trace_ref": comparator_ref,
            "decode_starts": list(DECODE_STARTS),
            "executed_lengths": list(EXECUTED_LENGTHS),
            "selected_prefix_lengths": list(SELECTED_PREFIX_LENGTHS),
            "decode_rows": decode_rows,
            "discard_events": discard_events,
            "terminal_unexecuted": terminal_unexecuted,
            "comparisons": comparisons,
            "observed_frames": observed_frames,
            "requested_action_sequence_sha256": requested_sha,
            "applied_action_sequence_sha256": applied_sha,
            "closed_loop": closed_loop,
            "strict_v2_replay": replay,
            "strict_v2_oracle_unchanged": True,
            "policy_controls_owned_all_frames": True,
            "phase_or_progress_policy_input": False,
            "source_action_fallback": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            **_false_fields(),
        }
    )
    return payload


def verify_trace(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="F0b trace")
    if (
        payload.get("schema_version") != TRACE_SCHEMA
        or payload.get("task_id") != TASK_ID
    ):
        raise ValueError("F0b trace header drifted")
    expected = build_trace(
        spec_identity_sha256=payload.get("spec_identity_sha256"),
        checkpoint_ref=payload.get("checkpoint_ref"),
        source_episode_ref=payload.get("source_episode_ref"),
        comparator_trace_ref=payload.get("comparator_trace_ref"),
        comparisons=payload.get("comparisons"),
        observed_frames=payload.get("observed_frames"),
        decode_rows=payload.get("decode_rows"),
        discard_events=payload.get("discard_events"),
        terminal_unexecuted=payload.get("terminal_unexecuted"),
        closed_loop=payload.get("closed_loop"),
    )
    if payload != expected:
        raise ValueError("F0b trace drifted")


def replay_strict_v2(
    *, observed_frames: Any, closed_loop: dict[str, Any]
) -> dict[str, Any]:
    verify_signed_payload(closed_loop, label="F0b embedded closed loop")
    if not isinstance(observed_frames, list) or len(observed_frames) != ROLLOUT_FRAMES:
        raise ValueError("F0b observed-frame coverage drifted")
    for index, row in enumerate(observed_frames):
        if (
            not isinstance(row, dict)
            or row.get("frame_index") != index
            or row.get("phase") != phase_for_frame(index)
        ):
            raise ValueError("F0b observed-frame order drifted")
    projected = closed_loop.get("projected_action_frame_indices")
    if not isinstance(projected, list) or not all(
        isinstance(item, int) for item in projected
    ):
        raise ValueError("F0b projected-frame evidence drifted")
    replay = _evaluate(
        observed_frames,
        anchor_start=np.asarray(
            closed_loop.get("anchor_start_position_m"), dtype=np.float64
        ),
        anchor_final=np.asarray(
            closed_loop.get("anchor_final_position_m"), dtype=np.float64
        ),
        projected_frames=projected,
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    )
    for key, value in replay.items():
        if closed_loop.get(key) != value:
            raise ValueError(f"F0b strict-v2 replay drifted at {key}")
    return replay


def build_result(*, trace: dict[str, Any], marker: dict[str, Any]) -> dict[str, Any]:
    verify_trace(trace)
    verify_signed_payload(marker, label="F0b result marker")
    replay = trace["strict_v2_replay"]
    passed = replay["simulation_semantic_strict_success"]
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA,
            "task_id": TASK_ID,
            "status": "verified_gate_c_pass"
            if passed
            else "verified_terminal_negative",
            "attempt_identity_sha256": marker["identity_sha256"],
            "trace_identity_sha256": trace["identity_sha256"],
            "checkpoint_identity_sha256": CHECKPOINT_IDENTITY,
            "comparator_trace_identity_sha256": COMPARATOR_TRACE_IDENTITY,
            "gate_c_executed": True,
            "gate_c_passed": passed,
            "failed_gate_margins": replay["failed_gate_margins"],
            "terminal_outcome": replay["terminal_outcome"],
            "maximum_anchor_lift_m": replay["maximum_anchor_lift_m"],
            "decode_starts": list(DECODE_STARTS),
            "executed_lengths": list(EXECUTED_LENGTHS),
            "manual_discard_count": MANUAL_DISCARD_COUNT,
            "model_load_count": 1,
            "rollout_count": 1,
            "optimizer_created": False,
            "optimizer_training": False,
            "retry_authorized": False,
            "corrective_training_selected": False,
            "single_corrective_rung_consumed": False,
            "simulation_policy_accepted": False,
            **_false_fields(),
        }
    )


def verify_result(
    payload: dict[str, Any], *, trace: dict[str, Any], marker: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="F0b result")
    if payload != build_result(trace=trace, marker=marker):
        raise ValueError("F0b result drifted")


def build_scorecard(*, result: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    verify_signed_payload(result, label="F0b scorecard result")
    verify_trace(trace)
    return sign_payload(
        {
            "schema_version": SCORECARD_SCHEMA,
            "task_id": TASK_ID,
            "result_identity_sha256": result["identity_sha256"],
            "trace_identity_sha256": trace["identity_sha256"],
            "gate_c_passed": result["gate_c_passed"],
            "terminal_outcome": result["terminal_outcome"],
            "failed_gate_margins": result["failed_gate_margins"],
            "comparator_gate_c_passed": False,
            "comparator_failed_gate": "release_final_contact_clear",
            "same_checkpoint_and_seed": True,
            "only_execution_cadence_changed": True,
            "physical_proof": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def build_retention(
    *,
    marker: dict[str, Any],
    result: dict[str, Any],
    trace: dict[str, Any],
    mirror_manifest: dict[str, Any],
    mirror_file_sha256: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    verify_result(result, trace=trace, marker=marker)
    verify_signed_payload(mirror_manifest, label="F0b mirror manifest")
    root = Path(repo_root).resolve()
    mirror_sha256 = _sha(mirror_file_sha256)
    _verify_mirror_manifest(
        mirror_manifest,
        trace_path=OUTPUT_TRACE_PATH,
        trace_identity_sha256=trace["identity_sha256"],
        output_path=MIRROR_PATH,
        output_sha256=mirror_sha256,
    )
    return sign_payload(
        {
            "schema_version": RETENTION_SCHEMA,
            "task_id": TASK_ID,
            "result_identity_sha256": result["identity_sha256"],
            "trace_identity_sha256": trace["identity_sha256"],
            "tracked_trace_path": TRACE_PATH.as_posix(),
            "tracked_trace_file_sha256": _sha_file(root / TRACE_PATH),
            "output_trace_path": OUTPUT_TRACE_PATH.as_posix(),
            "output_trace_file_sha256": _sha_file(root / OUTPUT_TRACE_PATH),
            "mirror_path": MIRROR_PATH.as_posix(),
            "mirror_file_sha256": mirror_sha256,
            "mirror_manifest_path": MIRROR_MANIFEST_PATH.as_posix(),
            "mirror_manifest_identity_sha256": mirror_manifest["identity_sha256"],
            "checkpoint_retained_in_place": True,
            "checkpoint_copied": False,
            "replayable_trace_tracked": True,
            "large_outputs_tracked_in_git": False,
            "retry_authorized": False,
            **_false_fields(),
        }
    )


def build_final(
    *,
    marker: dict[str, Any],
    result: dict[str, Any],
    scorecard: dict[str, Any],
    retention: dict[str, Any],
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": FINAL_SCHEMA,
            "task_id": TASK_ID,
            "status": result["status"],
            "attempt_identity_sha256": marker["identity_sha256"],
            "result_identity_sha256": result["identity_sha256"],
            "scorecard_identity_sha256": scorecard["identity_sha256"],
            "retention_identity_sha256": retention["identity_sha256"],
            "gate_c_passed": result["gate_c_passed"],
            "model_load_count": 1,
            "rollout_count": 1,
            "optimizer_created": False,
            "optimizer_training": False,
            "retry_authorized": False,
            **_false_fields(),
        }
    )


def build_terminal_failure(
    *,
    marker: dict[str, Any],
    progress: dict[str, Any],
    partial_tree: list[dict[str, Any]],
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    verify_signed_payload(marker, label="F0b failure marker")
    _validate_progress(progress)
    _validate_file_tree(partial_tree)
    return sign_payload(
        {
            "schema_version": FAILURE_SCHEMA,
            "task_id": TASK_ID,
            "attempt_identity_sha256": marker["identity_sha256"],
            "progress": progress,
            "partial_tree": partial_tree,
            "partial_tree_identity_sha256": _tree_identity(partial_tree),
            "error_type": str(error_type),
            "error_message": str(error_message)[:2000],
            "policy_verdict": None,
            "gate_c_passed": False,
            "infrastructure_failure": True,
            "retry_authorized": False,
            **_false_fields(),
        }
    )


def materialize_authority(
    *,
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    spec = load_strict_json(root / SPEC_PATH)
    verify_spec(spec, repo_root=root)
    _require_origin_boundary(root, required_source_commit)
    _require_paths_absent(
        root,
        (
            *AUTHORITY_PATHS,
            SMOKE_PATH,
            SMOKE_ROOT,
            ACCEPTANCE_PATH,
            MARKER_PATH,
            *TERMINAL_PATHS,
            RUN_ROOT,
        ),
    )
    _run_renderer(
        root=root,
        trace_path=COMPARATOR_TRACE_PATH,
        video_path=SMOKE_VIDEO_PATH,
    )
    manifest = load_strict_json(root / SMOKE_MANIFEST_PATH)
    smoke = build_renderer_smoke_receipt(
        manifest=manifest, video_file_sha256=_sha_file(root / SMOKE_VIDEO_PATH)
    )
    dump_canonical_json(root / SMOKE_PATH, smoke)
    owner = build_owner_grant(
        spec=spec,
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    request, decision = build_central_authority(spec=spec, owner=owner, smoke=smoke)
    snapshot = _collect_snapshot(root, owner=owner, smoke=smoke)
    runtime = build_runtime_preflight(
        spec=spec,
        owner=owner,
        request=request,
        decision=decision,
        smoke=smoke,
        snapshot=snapshot,
    )
    permit = build_permit(
        spec=spec,
        owner=owner,
        request=request,
        decision=decision,
        smoke=smoke,
        runtime=runtime,
    )
    bundle = {
        OWNER_PATH.as_posix(): owner,
        REQUEST_PATH.as_posix(): request,
        DECISION_PATH.as_posix(): decision,
        RUNTIME_PATH.as_posix(): runtime,
        PERMIT_PATH.as_posix(): permit,
    }
    for relative, payload in bundle.items():
        dump_canonical_json(root / relative, payload)
    return bundle


def verify_authority_bundle(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    spec = load_strict_json(root / SPEC_PATH)
    verify_spec(spec, repo_root=root)
    smoke = load_strict_json(root / SMOKE_PATH)
    manifest = load_strict_json(root / SMOKE_MANIFEST_PATH)
    if smoke != build_renderer_smoke_receipt(
        manifest=manifest, video_file_sha256=_sha_file(root / SMOKE_VIDEO_PATH)
    ):
        raise ValueError("F0b renderer smoke drifted")
    owner, request, decision, runtime, permit = [
        load_strict_json(root / path) for path in AUTHORITY_PATHS
    ]
    verify_owner_grant(owner, spec=spec)
    expected_request, expected_decision = build_central_authority(
        spec=spec, owner=owner, smoke=smoke
    )
    if request != expected_request or decision != expected_decision:
        raise ValueError("F0b central authority drifted")
    expected_runtime = build_runtime_preflight(
        spec=spec,
        owner=owner,
        request=request,
        decision=decision,
        smoke=smoke,
        snapshot=runtime.get("snapshot"),
    )
    if runtime != expected_runtime:
        raise ValueError("F0b runtime drifted")
    if permit != build_permit(
        spec=spec,
        owner=owner,
        request=request,
        decision=decision,
        smoke=smoke,
        runtime=runtime,
    ):
        raise ValueError("F0b permit drifted")
    return {
        "spec": spec,
        "smoke": smoke,
        "owner": owner,
        "request": request,
        "decision": decision,
        "runtime": runtime,
        "permit": permit,
    }


def write_acceptance(
    *,
    authority_commit: str,
    reviewer_decision_id: str,
    reviewer_path: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    if os.path.lexists(root / ACCEPTANCE_PATH):
        raise FileExistsError("F0b acceptance already exists")
    bundle = verify_authority_bundle(repo_root=root)
    reviewer = root / _safe_relative(reviewer_path)
    _reject_symlink_components(reviewer)
    if not reviewer.is_file() or reviewer.is_symlink():
        raise ValueError("F0b reviewer evidence is absent or aliased")
    acceptance = build_acceptance(
        permit=bundle["permit"],
        authority_commit=authority_commit,
        reviewer_decision_id=reviewer_decision_id,
        reviewer_path=reviewer_path,
        reviewer_file_sha256=_sha_file(reviewer),
    )
    dump_canonical_json(root / ACCEPTANCE_PATH, acceptance)
    return acceptance


def run_authorized(*, started_at: str, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    bundle = verify_authority_bundle(repo_root=root)
    owner, permit, spec = bundle["owner"], bundle["permit"], bundle["spec"]
    acceptance = load_strict_json(root / ACCEPTANCE_PATH)
    expected_acceptance = build_acceptance(
        permit=permit,
        authority_commit=acceptance.get("authority_commit"),
        reviewer_decision_id=acceptance.get("reviewer_decision_id"),
        reviewer_path=acceptance.get("reviewer_path"),
        reviewer_file_sha256=acceptance.get("reviewer_file_sha256"),
    )
    if acceptance != expected_acceptance:
        raise ValueError("F0b pre-run acceptance drifted")
    _require_active(owner, started_at, minimum_seconds=1800)
    _require_remote_run_boundary(root, acceptance=acceptance, owner=owner)
    _require_paths_absent(root, (MARKER_PATH, *TERMINAL_PATHS, RUN_ROOT))
    marker = build_marker(
        permit=permit,
        source_commit=_git(root, "rev-parse", "HEAD"),
        started_at=started_at,
    )
    dump_canonical_json(root / MARKER_PATH, marker)
    progress = _progress("marker_written", marker_written=True)
    try:
        (root / RUN_ROOT).mkdir(parents=True, exist_ok=False)
        progress = _progress("checkpoint_load_entered", marker_written=True)
        dump_canonical_json(root / PROGRESS_PATH, progress)
        result = _execute_once(root=root, spec=spec, marker=marker, progress=progress)
    except BaseException as error:
        for relative in (
            TRACE_PATH,
            RESULT_PATH,
            SCORECARD_PATH,
            RETENTION_PATH,
            FINAL_PATH,
        ):
            path = root / relative
            if path.is_file() and not path.is_symlink():
                path.unlink()
        if (root / PROGRESS_PATH).is_file() and not (root / PROGRESS_PATH).is_symlink():
            progress = load_strict_json(root / PROGRESS_PATH)
        failure = build_terminal_failure(
            marker=marker,
            progress=progress,
            partial_tree=_partial_tree(root / RUN_ROOT),
            error_type=type(error).__name__,
            error_message=str(error) or repr(error),
        )
        dump_canonical_json(root / FAILURE_PATH, failure)
        raise
    return result


def verify_outputs(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    bundle = verify_authority_bundle(repo_root=root)
    _verify_terminal_exclusivity(root)
    marker = load_strict_json(root / MARKER_PATH)
    expected_marker = build_marker(
        permit=bundle["permit"],
        source_commit=marker.get("source_commit"),
        started_at=marker.get("started_at"),
    )
    if marker != expected_marker:
        raise ValueError("F0b attempt marker drifted")
    if (root / FAILURE_PATH).exists():
        if any(
            (root / path).exists()
            for path in (
                TRACE_PATH,
                RESULT_PATH,
                SCORECARD_PATH,
                RETENTION_PATH,
                FINAL_PATH,
            )
        ):
            raise ValueError("F0b success and failure evidence coexist")
        failure = load_strict_json(root / FAILURE_PATH)
        expected = build_terminal_failure(
            marker=marker,
            progress=failure.get("progress"),
            partial_tree=_partial_tree(root / RUN_ROOT),
            error_type=failure.get("error_type"),
            error_message=failure.get("error_message"),
        )
        if failure != expected:
            raise ValueError("F0b terminal failure drifted")
        return {"terminal_failure": failure}
    trace = load_strict_json(root / TRACE_PATH)
    output_trace = load_strict_json(root / OUTPUT_TRACE_PATH)
    if trace != output_trace:
        raise ValueError("F0b tracked/output trace copies drifted")
    verify_trace(trace)
    if trace.get("spec_identity_sha256") != bundle["spec"]["identity_sha256"]:
        raise ValueError("F0b trace/spec linkage drifted")
    result = load_strict_json(root / RESULT_PATH)
    verify_result(result, trace=trace, marker=marker)
    scorecard = load_strict_json(root / SCORECARD_PATH)
    if scorecard != build_scorecard(result=result, trace=trace):
        raise ValueError("F0b scorecard drifted")
    manifest = load_strict_json(root / MIRROR_MANIFEST_PATH)
    retention = load_strict_json(root / RETENTION_PATH)
    expected_retention = build_retention(
        marker=marker,
        result=result,
        trace=trace,
        mirror_manifest=manifest,
        mirror_file_sha256=_sha_file(root / MIRROR_PATH),
        repo_root=root,
    )
    if retention != expected_retention:
        raise ValueError("F0b retention drifted")
    final = load_strict_json(root / FINAL_PATH)
    if final != build_final(
        marker=marker, result=result, scorecard=scorecard, retention=retention
    ):
        raise ValueError("F0b final receipt drifted")
    return {
        "trace": trace,
        "result": result,
        "scorecard": scorecard,
        "retention": retention,
        "final": final,
    }


def _execute_once(
    *,
    root: Path,
    spec: dict[str, Any],
    marker: dict[str, Any],
    progress: dict[str, Any],
) -> dict[str, Any]:
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    import torch
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.act.processor_act import make_act_pre_post_processors

    if not torch.backends.mps.is_available():
        raise RuntimeError("F0b requires MPS")
    random.seed(TRAINING_SEED)
    np.random.seed(TRAINING_SEED)
    torch.manual_seed(TRAINING_SEED)
    checkpoint = root / CHECKPOINT_PATH
    policy = ACTPolicy.from_pretrained(checkpoint, local_files_only=True, strict=True)
    policy.reset()
    progress.update(
        _progress(
            "model_loaded",
            marker_written=True,
            checkpoint_tensor_read=True,
            model_constructed=True,
            model_loaded=True,
        )
    )
    dump_canonical_json(root / PROGRESS_PATH, progress)
    metadata = LeRobotDatasetMetadata(R0_DATASET_REPO_ID, root=root / R0_DATASET_ROOT)
    preprocessor, postprocessor = make_act_pre_post_processors(
        policy.config, dataset_stats=metadata.stats
    )
    source_ref, source_frames = _source_episode_zero(root)
    observed: list[dict[str, Any]] = []
    adapter = HybridTailQueueAdapter(
        ACTChunkDecoder(
            policy=policy,
            preprocessor=preprocessor,
            postprocessor=postprocessor,
            torch=torch,
        )
    )
    progress.update(
        _progress(
            "simulation_rollout",
            marker_written=True,
            checkpoint_tensor_read=True,
            model_constructed=True,
            model_loaded=True,
            model_inference=True,
            simulation_rollout=True,
        )
    )
    dump_canonical_json(root / PROGRESS_PATH, progress)
    rollout = run_policy_grasp_closed_loop(
        adapter,
        checkpoint_sha256=CHECKPOINT_IDENTITY,
        training_run_summary_sha256=R2_RUN_IDENTITY,
        seed=SIMULATION_SEED,
        schema_version="scenesmith.f0b_hybrid_tail_cadence_rollout.v1",
        task_id=TASK_ID,
        evidence_mode="retained_update_10000_hybrid_tail_cadence",
        policy_label="ACT_R2_F0B_HYBRID_TAIL",
        frame_observer=observed.append,
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        capture_images=True,
    )
    terminal = adapter.finalize()
    comparisons = build_comparison_rows(
        source_frames=source_frames, candidate_frames=observed
    )
    trace = build_trace(
        spec_identity_sha256=spec["identity_sha256"],
        checkpoint_ref=spec["checkpoint"],
        source_episode_ref=source_ref,
        comparator_trace_ref={
            "path": COMPARATOR_TRACE_PATH.as_posix(),
            "file_sha256": _sha_file(root / COMPARATOR_TRACE_PATH),
            "identity_sha256": COMPARATOR_TRACE_IDENTITY,
        },
        comparisons=comparisons,
        observed_frames=observed,
        decode_rows=adapter.decode_rows,
        discard_events=adapter.discard_events,
        terminal_unexecuted=terminal,
        closed_loop=rollout,
    )
    dump_canonical_json(root / OUTPUT_TRACE_PATH, trace)
    progress.update(
        _progress(
            "rendering",
            marker_written=True,
            checkpoint_tensor_read=True,
            model_constructed=True,
            model_loaded=True,
            model_inference=True,
            simulation_rollout=True,
            live_rendering=True,
        )
    )
    dump_canonical_json(root / PROGRESS_PATH, progress)
    _run_renderer(root=root, trace_path=OUTPUT_TRACE_PATH, video_path=MIRROR_PATH)
    manifest = load_strict_json(root / MIRROR_MANIFEST_PATH)
    dump_canonical_json(root / TRACE_PATH, trace)
    result = build_result(trace=trace, marker=marker)
    dump_canonical_json(root / RESULT_PATH, result)
    scorecard = build_scorecard(result=result, trace=trace)
    dump_canonical_json(root / SCORECARD_PATH, scorecard)
    retention = build_retention(
        marker=marker,
        result=result,
        trace=trace,
        mirror_manifest=manifest,
        mirror_file_sha256=_sha_file(root / MIRROR_PATH),
        repo_root=root,
    )
    dump_canonical_json(root / RETENTION_PATH, retention)
    final = build_final(
        marker=marker, result=result, scorecard=scorecard, retention=retention
    )
    dump_canonical_json(root / FINAL_PATH, final)
    progress.update(
        _progress(
            "complete",
            marker_written=True,
            checkpoint_tensor_read=True,
            model_constructed=True,
            model_loaded=True,
            model_inference=True,
            simulation_rollout=True,
            live_rendering=True,
        )
    )
    dump_canonical_json(root / PROGRESS_PATH, progress)
    return verify_outputs(repo_root=root)


def _load_verified_sources(root: Path) -> dict[str, Any]:
    payloads = {
        "f0a": load_strict_json(root / F0A_PATH),
        "r2_result": load_strict_json(root / R2_RESULT_PATH),
        "r2_retention": load_strict_json(root / R2_RETENTION_PATH),
        "r2_final": load_strict_json(root / R2_FINAL_PATH),
        "r2_run": load_strict_json(root / R2_RUN_PATH),
        "comparator": load_strict_json(root / COMPARATOR_TRACE_PATH),
        "r0_statistics": load_strict_json(root / R0_STATISTICS_PATH),
        "r0_retention": load_strict_json(root / R0_RETENTION_PATH),
    }
    for label, expected in (
        ("f0a", F0A_IDENTITY),
        ("r2_result", R2_RESULT_IDENTITY),
        ("r2_retention", R2_RETENTION_IDENTITY),
        ("r2_final", R2_FINAL_IDENTITY),
        ("r2_run", R2_RUN_IDENTITY),
        ("comparator", COMPARATOR_TRACE_IDENTITY),
        ("r0_statistics", R0_STATISTICS_IDENTITY),
        ("r0_retention", R0_RETENTION_IDENTITY),
    ):
        verify_signed_payload(payloads[label], label=f"F0b {label}")
        if payloads[label].get("identity_sha256") != expected:
            raise ValueError(f"F0b {label} identity drifted")
    source_ref = _source_ref(payloads["comparator"].get("source_episode_ref"))
    if source_ref != {
        "path": SOURCE_EPISODE_PATH.as_posix(),
        "file_sha256": SOURCE_EPISODE_FILE_SHA256,
        "raw_rollout_identity_sha256": SOURCE_ROLLOUT_IDENTITY,
    }:
        raise ValueError("F0b comparator source reference drifted")
    if _sha_file(root / COMPARATOR_TRACE_PATH) != COMPARATOR_TRACE_FILE_SHA256:
        raise ValueError("F0b comparator trace file bytes drifted")
    source_path = root / source_ref["path"]
    if (
        _sha_file(source_path) != SOURCE_EPISODE_FILE_SHA256
        or source_ref.get("raw_rollout_identity_sha256") != SOURCE_ROLLOUT_IDENTITY
    ):
        raise ValueError("F0b source episode drifted")
    return payloads


def _source_episode_zero(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected_store = default_store_root(repo_root=root)
    path = root / SOURCE_EPISODE_PATH
    if path.parent != expected_store:
        raise ValueError("F0b source episode path left the frozen raw store")
    _reject_symlink_components(path)
    payload = load_strict_json(path)
    if (
        payload.get("episode_spec", {}).get("seed") != SIMULATION_SEED
        or _sha_file(path) != SOURCE_EPISODE_FILE_SHA256
        or payload.get("raw_rollout", {}).get("record_identity_sha256")
        != SOURCE_ROLLOUT_IDENTITY
    ):
        raise ValueError("F0b source episode zero identity drifted")
    frames = sorted(payload["frames"], key=lambda row: row["frame_index"])
    if len(frames) != ROLLOUT_FRAMES:
        raise ValueError("F0b source episode zero is incomplete")
    return (
        {
            "path": SOURCE_EPISODE_PATH.as_posix(),
            "file_sha256": SOURCE_EPISODE_FILE_SHA256,
            "raw_rollout_identity_sha256": SOURCE_ROLLOUT_IDENTITY,
        },
        frames,
    )


def _collect_snapshot(
    root: Path, *, owner: dict[str, Any], smoke: dict[str, Any]
) -> dict[str, Any]:
    head = _git(root, "rev-parse", "HEAD")
    upstream = _git(root, "rev-parse", "@{upstream}")
    dirty = _git(
        root,
        "status",
        "--porcelain=v1",
        "--",
        *[path.as_posix() for path in IMPLEMENTATION_PATHS],
    )
    runtime = subprocess.run(
        [
            str(root / STABLE_RUNNER_INTERPRETER),
            "-c",
            "import json,lerobot,mujoco,torch,sys; print(json.dumps({'python':sys.version.split()[0],'torch':torch.__version__,'mujoco':mujoco.__version__,'lerobot':lerobot.__version__,'mps':torch.backends.mps.is_available()}))",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        env={
            **os.environ,
            "PYTHONPATH": f"{root / 'external/lerobot/src'}:{root / 'external/lerobot/.venv/lib/python3.12/site-packages'}:{MUJOCO_SUPPORT_SITE_PACKAGES}",
        },
    )
    runtime_values = json.loads(runtime.stdout.strip().splitlines()[-1])
    outputs = (*TERMINAL_PATHS, ACCEPTANCE_PATH, MARKER_PATH, RUN_ROOT)
    return {
        "branch": _git(root, "branch", "--show-current"),
        "head": head,
        "upstream": upstream,
        "required_source_commit": owner["required_source_commit"],
        "implementation_scoped_paths_clean": not dirty.strip(),
        "checkpoint_tree": _file_tree(root / CHECKPOINT_PATH),
        "checkpoint_tree_identity_sha256": CHECKPOINT_IDENTITY,
        "lerobot_checkout_head": _git(root / "external/lerobot", "rev-parse", "HEAD"),
        "lerobot_checkout_tree": _git(
            root / "external/lerobot", "rev-parse", "HEAD^{tree}"
        ),
        "so_arm_checkout_head": _git(root / "external/SO-ARM100", "rev-parse", "HEAD"),
        "so_arm_checkout_tree": _git(
            root / "external/SO-ARM100", "rev-parse", "HEAD^{tree}"
        ),
        "so101_asset_tree_identity_sha256": _tree_identity(
            _file_tree(root / SO101_ASSET_PATH)
        ),
        "python_version": runtime_values["python"],
        "torch_version": runtime_values["torch"],
        "mujoco_version": runtime_values["mujoco"],
        "lerobot_version": runtime_values["lerobot"],
        "mps_available": runtime_values["mps"],
        "runner_interpreter": STABLE_RUNNER_INTERPRETER.as_posix(),
        "mujoco_support_site_packages": str(MUJOCO_SUPPORT_SITE_PACKAGES),
        "renderer_smoke_identity_sha256": smoke["identity_sha256"],
        "output_paths_absent": all(
            not os.path.lexists(root / path) for path in outputs
        ),
        "disk_free_bytes": shutil.disk_usage(root).free,
        "checkpoint_tensor_deserialized": False,
        "model_constructed": False,
        "model_inference": False,
        "optimizer_created": False,
        "simulation_rollout": False,
    }


def _verify_snapshot(
    snapshot: Any, *, owner: dict[str, Any], smoke: dict[str, Any]
) -> None:
    if not isinstance(snapshot, dict):
        raise ValueError("F0b runtime snapshot is absent")
    checkpoint_tree = snapshot.get("checkpoint_tree")
    _validate_file_tree(checkpoint_tree)
    if (
        snapshot.get("branch") != BRANCH
        or snapshot.get("head") != snapshot.get("upstream")
        or snapshot.get("head") != owner["required_source_commit"]
        or snapshot.get("required_source_commit") != owner["required_source_commit"]
        or snapshot.get("implementation_scoped_paths_clean") is not True
        or snapshot.get("checkpoint_tree_identity_sha256") != CHECKPOINT_IDENTITY
        or _tree_identity(checkpoint_tree) != CHECKPOINT_IDENTITY
        or snapshot.get("lerobot_checkout_head") != LEROBOT_CHECKOUT_HEAD
        or snapshot.get("lerobot_checkout_tree") != LEROBOT_CHECKOUT_TREE
        or snapshot.get("so_arm_checkout_head") != SO_ARM_CHECKOUT_HEAD
        or snapshot.get("so_arm_checkout_tree") != SO_ARM_CHECKOUT_TREE
        or snapshot.get("so101_asset_tree_identity_sha256") != SO101_ASSET_TREE_IDENTITY
        or snapshot.get("runner_interpreter") != STABLE_RUNNER_INTERPRETER.as_posix()
        or snapshot.get("mujoco_support_site_packages")
        != str(MUJOCO_SUPPORT_SITE_PACKAGES)
        or snapshot.get("renderer_smoke_identity_sha256") != smoke["identity_sha256"]
        or snapshot.get("output_paths_absent") is not True
        or snapshot.get("mps_available") is not True
        or snapshot.get("python_version") != EXPECTED_PYTHON_VERSION
        or snapshot.get("torch_version") != EXPECTED_TORCH_VERSION
        or snapshot.get("mujoco_version") != EXPECTED_MUJOCO_VERSION
        or snapshot.get("lerobot_version") != EXPECTED_LEROBOT_VERSION
        or snapshot.get("disk_free_bytes", 0) < 1_000_000_000
        or any(
            snapshot.get(field) is not False
            for field in (
                "checkpoint_tensor_deserialized",
                "model_constructed",
                "model_inference",
                "optimizer_created",
                "simulation_rollout",
            )
        )
    ):
        raise ValueError("F0b runtime snapshot failed closed")


def _run_renderer(*, root: Path, trace_path: Path, video_path: Path) -> None:
    subprocess.run(
        [
            str(root / STABLE_RUNNER_INTERPRETER),
            str(root / RENDERER_PATH),
            "--trace",
            trace_path.as_posix(),
            "--output-mp4",
            video_path.as_posix(),
            "--fps",
            "25",
        ],
        cwd=root,
        check=True,
        env={
            **os.environ,
            "PYTHONPATH": f"{root / 'external/lerobot/src'}:{root / 'external/lerobot/.venv/lib/python3.12/site-packages'}:{MUJOCO_SUPPORT_SITE_PACKAGES}",
        },
    )


def _require_origin_boundary(root: Path, commit: str) -> None:
    if _git(root, "branch", "--show-current") != BRANCH:
        raise ValueError("F0b is on the wrong branch")
    if (
        _git(root, "rev-parse", "HEAD") != _commit(commit)
        or _git(root, "rev-parse", "@{upstream}") != commit
    ):
        raise ValueError("F0b source boundary is not exact on origin")
    dirty = _git(
        root,
        "status",
        "--porcelain=v1",
        "--",
        *[path.as_posix() for path in IMPLEMENTATION_PATHS],
    )
    if dirty.strip():
        raise ValueError("F0b implementation boundary is dirty")


def _require_remote_run_boundary(
    root: Path, *, acceptance: dict[str, Any], owner: dict[str, Any]
) -> None:
    head = _git(root, "rev-parse", "HEAD")
    if _git(root, "branch", "--show-current") != BRANCH or head != _git(
        root, "rev-parse", "@{upstream}"
    ):
        raise ValueError("F0b pre-run HEAD is not exact on origin")
    for commit in (owner["required_source_commit"], acceptance["authority_commit"]):
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, head], cwd=root, check=True
        )
    reviewer = root / acceptance["reviewer_path"]
    _reject_symlink_components(reviewer)
    if (
        not reviewer.is_file()
        or reviewer.is_symlink()
        or _sha_file(reviewer) != acceptance["reviewer_file_sha256"]
    ):
        raise ValueError("F0b pre-run reviewer bytes drifted")
    scoped = (
        *IMPLEMENTATION_PATHS,
        *AUTHORITY_PATHS,
        SMOKE_PATH,
        ACCEPTANCE_PATH,
        Path(acceptance["reviewer_path"]),
    )
    dirty = _git(
        root, "status", "--porcelain=v1", "--", *[path.as_posix() for path in scoped]
    )
    if dirty.strip():
        raise ValueError("F0b pre-run scoped boundary is dirty")


def _require_active(
    owner: dict[str, Any], started_at: str, *, minimum_seconds: int
) -> None:
    started = _aware_time(started_at, "attempt start")
    begin = _aware_time(owner.get("valid_from"), "valid_from")
    end = _aware_time(owner.get("valid_until"), "valid_until")
    if not begin <= started <= end or (end - started).total_seconds() < minimum_seconds:
        raise ValueError("F0b authority window or completion budget is invalid")


def _window(valid_from: str, valid_until: str) -> tuple[datetime, datetime]:
    start = _aware_time(valid_from, "valid_from")
    stop = _aware_time(valid_until, "valid_until")
    if not start < stop or (stop - start).total_seconds() > 8 * 60 * 60:
        raise ValueError("F0b owner window is invalid")
    return start, stop


def _progress(stage: str, **updates: bool) -> dict[str, Any]:
    result = {
        "stage": stage,
        "marker_written": False,
        "checkpoint_tensor_read": False,
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "simulation_rollout": False,
        "live_rendering": False,
        "optimizer_created": False,
        "optimizer_training": False,
    }
    result.update(updates)
    _validate_progress(result)
    return result


def _validate_progress(value: Any) -> None:
    expected_keys = {
        "stage",
        "marker_written",
        "checkpoint_tensor_read",
        "model_constructed",
        "model_loaded",
        "model_inference",
        "simulation_rollout",
        "live_rendering",
        "optimizer_created",
        "optimizer_training",
    }
    if (
        not isinstance(value, dict)
        or set(value) != expected_keys
        or not isinstance(value.get("stage"), str)
        or not value["stage"]
    ):
        raise ValueError("F0b progress is invalid")
    if any(not isinstance(item, bool) for key, item in value.items() if key != "stage"):
        raise ValueError("F0b progress flags are invalid")
    if (
        value.get("optimizer_created") is not False
        or value.get("optimizer_training") is not False
    ):
        raise ValueError("F0b optimizer progress escalated")
    if (
        value["marker_written"] is not True
        or value["model_loaded"]
        and not (value["checkpoint_tensor_read"] and value["model_constructed"])
        or value["model_inference"]
        and not value["model_loaded"]
        or value["simulation_rollout"]
        and not value["model_inference"]
        or value["live_rendering"]
        and not value["simulation_rollout"]
    ):
        raise ValueError("F0b progress ordering drifted")


def _verify_comparison_rows(rows: Any) -> None:
    if not isinstance(rows, list) or len(rows) != ROLLOUT_FRAMES:
        raise ValueError("F0b comparison rows are incomplete")
    for index, row in enumerate(rows):
        ordinal, start, offset = _chunk_location(index)
        if (
            not isinstance(row, dict)
            or row.get("frame_index") != index
            or row.get("phase") != phase_for_frame(index)
            or row.get("decode_ordinal") != ordinal
            or row.get("decode_start_frame") != start
            or row.get("chunk_offset") != offset
        ):
            raise ValueError("F0b comparison row order drifted")
        for key in (
            "source_requested_action_rad",
            "source_applied_action_rad",
            "candidate_requested_action_rad",
            "candidate_applied_action_rad",
            "source_qpos_rad",
            "candidate_qpos_rad",
            "source_qvel_rad_s",
            "candidate_qvel_rad_s",
        ):
            _vector6(row.get(key))
        _vector3(row.get("candidate_anchor_position_m"))
        if not isinstance(row.get("candidate_strict_contact"), bool):
            raise ValueError("F0b comparison contact flag drifted")


def _chunk_location(frame_index: int) -> tuple[int, int, int]:
    if (
        isinstance(frame_index, bool)
        or not isinstance(frame_index, int)
        or not 0 <= frame_index < ROLLOUT_FRAMES
    ):
        raise ValueError("F0b frame index is invalid")
    for ordinal, (start, length) in enumerate(
        zip(DECODE_STARTS, EXECUTED_LENGTHS, strict=True)
    ):
        if start <= frame_index < start + length:
            return ordinal, start, frame_index - start
    raise ValueError("F0b frame is outside the executed schedule")


def _checkpoint_ref(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("F0b checkpoint reference is absent")
    expected = {
        "path": CHECKPOINT_PATH.as_posix(),
        "identity_sha256": CHECKPOINT_IDENTITY,
        "tree": value.get("tree"),
        "optimizer_update_count": 10000,
        "load_count": 1,
    }
    _validate_file_tree(expected["tree"])
    if _tree_identity(expected["tree"]) != CHECKPOINT_IDENTITY or value != expected:
        raise ValueError("F0b checkpoint reference drifted")
    return expected


def _source_ref(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("F0b source reference is absent")
    allowed = {"path", "file_sha256", "identity_sha256", "raw_rollout_identity_sha256"}
    if not set(value).issubset(allowed) or not {"path", "file_sha256"}.issubset(value):
        raise ValueError("F0b source reference schema drifted")
    result = dict(value)
    result["path"] = _safe_relative(result["path"])
    _sha(result["file_sha256"])
    for field in ("identity_sha256", "raw_rollout_identity_sha256"):
        if field in result:
            _sha(result[field])
    return result


def _file_ref(
    root: Path, label: str, path: Path, identity: str | None = None
) -> dict[str, Any]:
    _reject_symlink_components(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"F0b source file is absent or aliased: {path}")
    result = {
        "label": label,
        "path": path.relative_to(root).as_posix(),
        "file_sha256": _sha_file(path),
        "size_bytes": path.stat().st_size,
    }
    if identity is not None:
        result["identity_sha256"] = _sha(identity)
    return result


def _file_tree(root: Path) -> list[dict[str, Any]]:
    _reject_symlink_components(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"F0b tree is absent or aliased: {root}")
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"F0b tree contains a symlink: {path}")
        if path.is_file():
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": _sha_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    _validate_file_tree(rows)
    return rows


def _validate_file_tree(rows: Any) -> None:
    if not isinstance(rows, list) or not rows:
        raise ValueError("F0b file tree is empty")
    paths = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "size_bytes"}:
            raise ValueError("F0b file tree row drifted")
        paths.append(_safe_relative(row["path"]))
        _sha(row["sha256"])
        if (
            isinstance(row["size_bytes"], bool)
            or not isinstance(row["size_bytes"], int)
            or row["size_bytes"] < 0
        ):
            raise ValueError("F0b file tree size drifted")
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError("F0b file tree path order drifted")


def _partial_tree(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return [
            {
                "path": ".absent",
                "sha256": hashlib.sha256(b"").hexdigest(),
                "size_bytes": 0,
            }
        ]
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": _sha_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    return rows or [
        {"path": ".empty", "sha256": hashlib.sha256(b"").hexdigest(), "size_bytes": 0}
    ]


def _require_paths_absent(root: Path, paths: Any) -> None:
    checked = []
    for path in paths:
        relative = Path(_safe_relative(Path(path).as_posix()))
        candidate = root / relative
        _reject_symlink_components(candidate)
        checked.append((relative, candidate))
    collisions = [
        relative.as_posix()
        for relative, candidate in checked
        if os.path.lexists(candidate)
    ]
    if collisions:
        raise FileExistsError(f"F0b immutable output paths already exist: {collisions}")


def _verify_terminal_exclusivity(root: Path) -> None:
    success_paths = (
        TRACE_PATH,
        RESULT_PATH,
        SCORECARD_PATH,
        RETENTION_PATH,
        FINAL_PATH,
    )
    for path in (*success_paths, FAILURE_PATH):
        _reject_symlink_components(root / path)
    if os.path.lexists(root / FAILURE_PATH) and any(
        os.path.lexists(root / path) for path in success_paths
    ):
        raise ValueError("F0b success and failure evidence coexist")


def _verify_mirror_manifest(
    manifest: dict[str, Any],
    *,
    trace_path: Path,
    trace_identity_sha256: str,
    output_path: Path,
    output_sha256: str,
) -> None:
    expected_adapter = (
        "chunk_50"
        if trace_path == COMPARATOR_TRACE_PATH
        else "hybrid_tail_chunk_50_to_10"
    )
    expected_seed_role = "training" if trace_path == COMPARATOR_TRACE_PATH else None
    expected_panels = [
        "policy side cam (re-render)",
        "policy overhead cam (re-render)",
        "expert top cam (recorded)",
    ]
    if (
        manifest.get("schema_version") != "scenesmith.rollout_mirror_render.v1"
        or manifest.get("purpose")
        != "diagnostic visualization of signed trace evidence; no authority"
        or manifest.get("trace_path") != trace_path.as_posix()
        or manifest.get("trace_identity_sha256") != _sha(trace_identity_sha256)
        or manifest.get("adapter_id") != expected_adapter
        or manifest.get("seed") != SIMULATION_SEED
        or manifest.get("seed_role") != expected_seed_role
        or manifest.get("frame_count") != ROLLOUT_FRAMES
        or manifest.get("panels") != expected_panels
        or manifest.get("anchor_orientation")
        != "held at initial value (position-only playback)"
        or manifest.get("output_mp4") != output_path.as_posix()
        or manifest.get("output_sha256") != _sha(output_sha256)
        or isinstance(manifest.get("output_bytes"), bool)
        or not isinstance(manifest.get("output_bytes"), int)
        or manifest["output_bytes"] <= 0
    ):
        raise ValueError("F0b mirror manifest linkage drifted")


def _dependency_revision(
    root: Path, *, expected_head: str, expected_tree: str
) -> dict[str, str]:
    _reject_symlink_components(root)
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    if head != _commit(expected_head) or tree != _commit(expected_tree):
        raise ValueError(f"F0b dependency revision drifted: {root}")
    return {"head": head, "tree": tree}


def _reject_symlink_components(path: Path) -> None:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        if part == "..":
            raise ValueError(f"F0b path contains parent traversal: {candidate}")
        current /= part
        if os.path.lexists(current) and current.is_symlink():
            raise ValueError(f"F0b path contains a symlink component: {current}")


def _rows_sha(value: Any) -> str:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[1:] != (6,) or not np.isfinite(array).all():
        raise ValueError("F0b action rows are invalid")
    return hashlib.sha256(
        canonical_json_bytes(array.astype(float).tolist())
    ).hexdigest()


def _matrix(value: Any, *, rows: int) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (rows, 6) or not np.isfinite(array).all():
        raise ValueError("F0b matrix coverage drifted")
    return array


def _vector6(value: Any) -> list[float]:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (6,) or not np.isfinite(array).all():
        raise ValueError("F0b six-vector drifted")
    return array.astype(float).tolist()


def _vector3(value: Any) -> list[float]:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,) or not np.isfinite(array).all():
        raise ValueError("F0b three-vector drifted")
    return array.astype(float).tolist()


def _sequence_sha(rows: list[dict[str, Any]], key: str) -> str:
    return hashlib.sha256(
        json.dumps(
            [row[key] for row in rows], separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _tree_identity(rows: Any) -> str:
    _validate_file_tree(rows)
    return hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha(value: Any) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("F0b value is not lowercase SHA-256")
    return value


def _commit(value: Any) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("F0b value is not a git commit")
    return value


def _safe_relative(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or Path(value).is_absolute()
        or ".." in Path(value).parts
    ):
        raise ValueError("F0b path is unsafe")
    return Path(value).as_posix()


def _aware_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"F0b {label} is invalid")
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"F0b {label} lacks UTC offset")
    return result


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


def _false_fields() -> dict[str, bool]:
    return {field: False for field in FALSE_AUTHORITY_FIELDS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write-spec", action="store_true")
    action.add_argument("--verify-spec", action="store_true")
    action.add_argument("--materialize-authority", action="store_true")
    action.add_argument("--verify-authority", action="store_true")
    action.add_argument("--write-acceptance", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify-outputs", action="store_true")
    parser.add_argument("--required-source-commit")
    parser.add_argument("--valid-from")
    parser.add_argument("--valid-until")
    parser.add_argument("--authority-commit")
    parser.add_argument("--reviewer-decision-id")
    parser.add_argument("--reviewer-path")
    parser.add_argument("--started-at")
    args = parser.parse_args()
    if args.write_spec:
        payload = write_spec()
    elif args.verify_spec:
        payload = load_strict_json(REPO_ROOT / SPEC_PATH)
        verify_spec(payload)
    elif args.materialize_authority:
        payload = materialize_authority(
            required_source_commit=args.required_source_commit,
            valid_from=args.valid_from,
            valid_until=args.valid_until,
        )
    elif args.verify_authority:
        payload = verify_authority_bundle()
    elif args.write_acceptance:
        payload = write_acceptance(
            authority_commit=args.authority_commit,
            reviewer_decision_id=args.reviewer_decision_id,
            reviewer_path=args.reviewer_path,
        )
    elif args.run:
        payload = run_authorized(started_at=args.started_at)
    else:
        payload = verify_outputs()
    identity = payload.get("identity_sha256") if isinstance(payload, dict) else None
    print(identity or "ok")


if __name__ == "__main__":
    main()
