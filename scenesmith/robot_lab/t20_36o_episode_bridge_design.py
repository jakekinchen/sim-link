"""Model-free execution and correction design for the bounded X episode bridge."""

from __future__ import annotations

import ast
import base64
import copy
import hashlib
import io
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.so101_coordinates import mujoco_to_lerobot
from scenesmith.robot_lab.so101_processor import JOINT_NAMES


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_36o_episode_bridge_design.json")
SCHEMA_VERSION = "scenesmith.t20_36o_episode_bridge_design.v1"

DEPENDENCY_LOCK_PATH = Path("configurations/robot_lab/pi05_robotics_dependency_lock.json")
T20_1_SPEC_PATH = Path("configurations/robot_lab/t20_1_simulation_training_spec.json")
DATASET_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_17_lerobot_dataset_manifest.json"
)
SOURCE_MANIFEST_PATH = Path(
    "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
)
T20_35X_SPEC_PATH = Path(
    "configurations/robot_lab/t20_35x_physical_gate_joint_weighted_training_spec.json"
)
T20_36N_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36n_tensor_reproduction_result.json"
)
FROZEN_GATE_PATH = Path(
    "configurations/robot_lab/t20_36l_frozen_consequence_gate.json"
)
DATA_PARQUET_PATH = Path(
    "outputs/robot_lab/t20_17_lerobot_training_dataset/data/chunk-000/file-000.parquet"
)
PI05_SOURCE_PATH = Path(
    "external/lerobot/src/lerobot/policies/pi05/modeling_pi05.py"
)
OWNER_DIRECTION_PATH = Path(
    "docs/autonomous-workflow/owner-direction-2026-07-16-overnight.md"
)
REVIEWER_PATH = Path(
    "docs/reviewer-messages/266-verify-t20-36n-x-mixed-negative-route-bridge.md"
)

EXPECTED_DEPENDENCY_LOCK_IDENTITY = (
    "adf09cc324a6f1fbe7d086d16c454dcf6785bd9fd136c1e3442cb319598c8262"
)
EXPECTED_T20_1_SPEC_IDENTITY = (
    "099ed4250a7e47e8afd7bf956446cdabb656400eaf7adebe5c1d7bbc18384d94"
)
EXPECTED_DATASET_MANIFEST_IDENTITY = (
    "689516af0ee418b600d51a5ae7cda8a5c49709a6f4e1c3356e18c9d5c708ab29"
)
EXPECTED_SOURCE_MANIFEST_IDENTITY = (
    "3860158e201e457146a167cfa778da14f210d88fa223cb075a1ec6d422ecfd1a"
)
EXPECTED_T20_35X_SPEC_IDENTITY = (
    "96efc6d35115126268684c91346b7388077342c573e458b7e708e98714113cfd"
)
EXPECTED_T20_36N_RESULT_IDENTITY = (
    "f8d7866e852a9b9a288b724016abe104dc94bf631251023faa8d26dbf5b86eb7"
)
EXPECTED_FROZEN_GATE_IDENTITY = (
    "463477dc91e3fb36b0550b88d461a788709a7258f9825ad6644f98bf0c77e48f"
)
EXPECTED_LEROBOT_REVISION = "e40b58a8dfa9e7b86918c374791599d070518d11"
EXPECTED_PI05_SOURCE_SHA256 = (
    "b05b6afe70a4a09f2eb610827b9ae09e8b08e43cd748d435e47879344e3fa619"
)
EXPECTED_DATA_PARQUET_SHA256 = (
    "7843e5310bed9ddf9f4bbae6136079f3743dc51783edabcd0994b631a105c910"
)
EXPECTED_SOURCE_EPISODE_SHA256 = (
    "586a3e67034a577bf046381837aebe68d3d5febdce6b1c51dbcb6f0be4968b54"
)
EXPECTED_SOURCE_EPISODE_IDENTITY = (
    "9e186088c9ca82fa9c58cb6e3870f322a9c2a84405d5ea23152b822fb9d4abdb"
)
EXPECTED_X_CHECKPOINT_IDENTITY = (
    "40c94f66e24f0e949c1b48c057de7643b868468cc3ee0025e15778c25b8cad50"
)

ROLLOUT_FRAME_COUNT = 244
N_ACTION_STEPS = 50
CHUNK_START_FRAMES = (0, 50, 100, 150, 200)
EXECUTED_LENGTHS = (50, 50, 50, 50, 44)
PROBE_SEEDS = (20260721, 20260722, 20260723, 20260724, 20260725)
DENOISE_STEP_COUNT = 10
CORRECTION_EXAMPLE_COUNT = (
    len(CHUNK_START_FRAMES) * len(PROBE_SEEDS) * DENOISE_STEP_COUNT
)
EXAMPLE_USE_COUNT = 10
OPTIMIZER_UPDATE_COUNT = CORRECTION_EXAMPLE_COUNT * EXAMPLE_USE_COUNT
TRAINING_SEED = 20260719
STANDARD_REPLAY_SEED_BASE = 20265719
LEARNING_RATE = 2.5e-5
PROBE_UPDATE_COUNTS = (0, 500, 1000, 1500, 2000, 2500)


def derive_chunk_windows(
    *, frame_count: int = ROLLOUT_FRAME_COUNT, n_action_steps: int = N_ACTION_STEPS
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if frame_count <= 0 or n_action_steps <= 0:
        raise ValueError("T20.36o frame count and action steps must be positive")
    starts = tuple(range(0, frame_count, n_action_steps))
    lengths = tuple(min(n_action_steps, frame_count - start) for start in starts)
    return starts, lengths


def load_verified_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    payload_paths = {
        "dependency_lock": DEPENDENCY_LOCK_PATH,
        "t20_1_spec": T20_1_SPEC_PATH,
        "dataset_manifest": DATASET_MANIFEST_PATH,
        "source_manifest": SOURCE_MANIFEST_PATH,
        "t20_35x_spec": T20_35X_SPEC_PATH,
        "t20_36n_result": T20_36N_RESULT_PATH,
        "frozen_gate": FROZEN_GATE_PATH,
    }
    sources = {
        name: load_strict_json(root / path) for name, path in payload_paths.items()
    }
    for name, payload in sources.items():
        verify_signed_payload(payload, label=f"T20.36o {name}")
    expected_identities = {
        "dependency_lock": EXPECTED_DEPENDENCY_LOCK_IDENTITY,
        "t20_1_spec": EXPECTED_T20_1_SPEC_IDENTITY,
        "dataset_manifest": EXPECTED_DATASET_MANIFEST_IDENTITY,
        "source_manifest": EXPECTED_SOURCE_MANIFEST_IDENTITY,
        "t20_35x_spec": EXPECTED_T20_35X_SPEC_IDENTITY,
        "t20_36n_result": EXPECTED_T20_36N_RESULT_IDENTITY,
        "frozen_gate": EXPECTED_FROZEN_GATE_IDENTITY,
    }
    for name, identity in expected_identities.items():
        if sources[name].get("identity_sha256") != identity:
            raise ValueError(f"T20.36o {name} identity drifted")

    source_entries = [
        row
        for row in sources["source_manifest"].get("episodes", [])
        if row.get("seed") == 0
    ]
    if len(source_entries) != 1:
        raise ValueError("T20.36o source seed 0 is missing or duplicated")
    source_entry = source_entries[0]
    if (
        source_entry.get("episode_file_sha256") != EXPECTED_SOURCE_EPISODE_SHA256
        or source_entry.get("raw_rollout_record_identity_sha256")
        != EXPECTED_SOURCE_EPISODE_IDENTITY
        or source_entry.get("frame_count") != ROLLOUT_FRAME_COUNT
    ):
        raise ValueError("T20.36o source episode entry drifted")
    relative_path = source_entry.get("relative_path")
    if not isinstance(relative_path, str) or Path(relative_path).name != relative_path:
        raise ValueError("T20.36o source episode path is unsafe")
    source_episode_path = root / "outputs/robot_lab/t17_5b_raw_store" / relative_path
    if _file_sha256(source_episode_path) != EXPECTED_SOURCE_EPISODE_SHA256:
        raise ValueError("T20.36o source episode bytes drifted")
    source_episode = load_strict_json(source_episode_path)
    frames = source_episode.get("frames")
    if not isinstance(frames, list) or len(frames) != ROLLOUT_FRAME_COUNT:
        raise ValueError("T20.36o source episode frame coverage drifted")
    if (
        source_episode.get("raw_rollout", {}).get("record_identity_sha256")
        != EXPECTED_SOURCE_EPISODE_IDENTITY
        or source_episode.get("outcome", {}).get("strict_success") is not True
    ):
        raise ValueError("T20.36o source episode eligibility drifted")

    data_path = root / DATA_PARQUET_PATH
    if _file_sha256(data_path) != EXPECTED_DATA_PARQUET_SHA256:
        raise ValueError("T20.36o dataset parquet drifted")
    dataset_rows = _load_episode_zero_rows(data_path)
    if len(dataset_rows) != ROLLOUT_FRAME_COUNT:
        raise ValueError("T20.36o dataset episode 0 frame coverage drifted")

    policy_source_path = root / PI05_SOURCE_PATH
    if _file_sha256(policy_source_path) != EXPECTED_PI05_SOURCE_SHA256:
        raise ValueError("T20.36o PI0.5 policy source drifted")
    policy_semantics = _policy_semantics(policy_source_path)
    dependency = sources["dependency_lock"]["dependencies"]["local_lerobot_checkout"]
    if (
        dependency.get("git", {}).get("revision") != EXPECTED_LEROBOT_REVISION
        or dependency.get("executable_stack", {}).get("identity_sha256")
        != sources["t20_35x_spec"].get("lerobot_stack_identity_sha256")
    ):
        raise ValueError("T20.36o LeRobot stack binding drifted")
    relevant = dependency.get("relevant_sources", {}).get("files", [])
    matches = [row for row in relevant if row.get("path") == PI05_SOURCE_PATH.as_posix()]
    if len(matches) != 1 or matches[0].get("sha256") != EXPECTED_PI05_SOURCE_SHA256:
        raise ValueError("T20.36o dependency lock omits the PI0.5 source")

    t20_1_rows = [
        row
        for row in sources["t20_1_spec"].get("selected_episodes", [])
        if row.get("seed") == 0
    ]
    dataset_rows_meta = [
        row
        for row in sources["dataset_manifest"].get("episodes", [])
        if row.get("episode_index") == 0
    ]
    if (
        len(t20_1_rows) != 1
        or t20_1_rows[0].get("episode_file_sha256")
        != EXPECTED_SOURCE_EPISODE_SHA256
        or len(dataset_rows_meta) != 1
        or dataset_rows_meta[0].get("raw_rollout_identity_sha256")
        != EXPECTED_SOURCE_EPISODE_IDENTITY
    ):
        raise ValueError("T20.36o episode-0 dataset lineage drifted")

    x_result = sources["t20_36n_result"]
    if (
        x_result.get("source_checkpoint_identity_sha256")
        != EXPECTED_X_CHECKPOINT_IDENTITY
        or x_result.get("all_expected_hashes_reproduced") is not True
        or x_result.get("all_repeats_bit_identical") is not True
        or x_result.get("uniform_gate_b_passed") is not True
        or x_result.get("amended_gate_b_passed") is not False
        or x_result.get("total_violation_count") != 5
    ):
        raise ValueError("T20.36o X bridge route evidence drifted")

    return {
        **sources,
        "payload_paths": payload_paths,
        "source_entry": source_entry,
        "source_episode": source_episode,
        "source_episode_path": source_episode_path,
        "dataset_rows": dataset_rows,
        "policy_semantics": policy_semantics,
    }


def build_bridge_spec(*, sources: dict[str, Any]) -> dict[str, Any]:
    starts, lengths = derive_chunk_windows()
    if starts != CHUNK_START_FRAMES or lengths != EXECUTED_LENGTHS:
        raise ValueError("T20.36o queue-derived windows drifted")
    windows = [
        _source_window(
            frames=sources["source_episode"]["frames"],
            dataset_rows=sources["dataset_rows"],
            start=start,
            executed_length=executed_length,
        )
        for start, executed_length in zip(starts, lengths, strict=True)
    ]
    correction_examples = [
        {
            "example_index": index,
            "chunk_start_frame": start,
            "inference_seed": seed,
            "denoise_step_index": step,
            "time": 1.0 - step / DENOISE_STEP_COUNT,
        }
        for index, (start, seed, step) in enumerate(
            (start, seed, step)
            for start in starts
            for seed in PROBE_SEEDS
            for step in range(DENOISE_STEP_COUNT)
        )
    ]
    if len(correction_examples) != CORRECTION_EXAMPLE_COUNT:
        raise ValueError("T20.36o correction example coverage drifted")
    sample_order = [
        update % CORRECTION_EXAMPLE_COUNT for update in range(OPTIMIZER_UPDATE_COUNT)
    ]
    if [sample_order.count(index) for index in range(CORRECTION_EXAMPLE_COUNT)] != [
        EXAMPLE_USE_COUNT
    ] * CORRECTION_EXAMPLE_COUNT:
        raise ValueError("T20.36o correction schedule is not balanced")
    standard_replay_seeds = [
        STANDARD_REPLAY_SEED_BASE + update
        for update in range(OPTIMIZER_UPDATE_COUNT)
    ]
    frozen_thresholds = copy.deepcopy(
        sources["frozen_gate"]["amended_gate_b_conjunction"][
            "phase_joint_maximum_error_rad"
        ]
    )
    frozen_timestep_mapping = copy.deepcopy(
        sources["frozen_gate"]["timestep_phase_mapping"]
    )
    x_spec = sources["t20_35x_spec"]
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.36o",
            "scope": "model_free_bounded_x_episode_0_bridge_design",
            "source_refs": {
                name: _payload_ref(
                    path=sources["payload_paths"][name], payload=sources[name]
                )
                for name in sources["payload_paths"]
            },
            "authority_refs": {
                "owner_direction": _file_ref(OWNER_DIRECTION_PATH),
                "reviewer_266": _file_ref(REVIEWER_PATH),
            },
            "source_checkpoint_identity_sha256": EXPECTED_X_CHECKPOINT_IDENTITY,
            "source_episode": {
                "seed": 0,
                "episode_index": 0,
                "file_ref": _file_ref(sources["source_episode_path"]),
                "raw_rollout_identity_sha256": EXPECTED_SOURCE_EPISODE_IDENTITY,
                "frame_count": ROLLOUT_FRAME_COUNT,
                "strict_success": True,
            },
            "dataset_parquet_ref": _file_ref(DATA_PARQUET_PATH),
            "policy_queue_semantics": {
                "lerobot_revision": EXPECTED_LEROBOT_REVISION,
                "lerobot_stack_identity_sha256": x_spec[
                    "lerobot_stack_identity_sha256"
                ],
                "source_path": PI05_SOURCE_PATH.as_posix(),
                "source_sha256": EXPECTED_PI05_SOURCE_SHA256,
                **sources["policy_semantics"],
            },
            "execution_contract": {
                "rollout_frame_count": ROLLOUT_FRAME_COUNT,
                "n_action_steps": N_ACTION_STEPS,
                "queue_reset_count": 1,
                "queue_reset_timing": "once_immediately_before_rollout_frame_0",
                "sample_only_when_queue_empty": True,
                "one_queued_action_popped_per_environment_frame": True,
                "chunk_start_frames": list(starts),
                "executed_lengths": list(lengths),
                "prediction_count": len(starts) * N_ACTION_STEPS,
                "executed_action_count": sum(lengths),
                "unexecuted_tail_count": len(starts) * N_ACTION_STEPS - sum(lengths),
                "legacy_action_horizon_5_allowed": False,
            },
            "source_windows": windows,
            "probe_contract": {
                "probe_seed_by_start": [
                    {"start_frame": start, "inference_seeds": list(PROBE_SEEDS)}
                    for start in starts
                ],
                "base_noise_sha256_by_seed": copy.deepcopy(
                    x_spec["evaluation"]["base_noise_sha256_by_seed"]
                ),
                "num_inference_steps": DENOISE_STEP_COUNT,
                "repeats_per_probe": 2,
                "decoded_and_denoise_path_hashes_must_repeat": True,
                "baseline_probe_precedes_optimizer_creation": True,
                "baseline_pass_skips_optimizer_entirely": True,
            },
            "correction_schedule": {
                "source_recipe": "t20_35x_physical_gate_joint_and_time_weighted_correction_plus_paired_standard_replay",
                "training_seed": TRAINING_SEED,
                "optimizer": "AdamW",
                "learning_rate": LEARNING_RATE,
                "weight_decay": 0.0,
                "betas": [0.9, 0.999],
                "epsilon": 1e-8,
                "amsgrad": False,
                "gradient_clip_norm": 1.0,
                "correction_example_count": CORRECTION_EXAMPLE_COUNT,
                "example_order": correction_examples,
                "example_order_sha256": _canonical_sha(correction_examples),
                "uses_per_example_ceiling": EXAMPLE_USE_COUNT,
                "optimizer_update_count_ceiling": OPTIMIZER_UPDATE_COUNT,
                "sample_index_by_update": sample_order,
                "standard_replay_ratio": "one_unique_source_batch_replay_per_correction_example",
                "standard_replay_update_count": OPTIMIZER_UPDATE_COUNT,
                "standard_replay_seed_by_update": standard_replay_seeds,
                "physical_joint_weighting": copy.deepcopy(
                    x_spec["physical_joint_weighting"]
                ),
                "time_normalization": {
                    "origin": "frozen_t20_35x_step_weights",
                    "weight_by_step": copy.deepcopy(
                        x_spec["time_normalization"]["weight_by_step"]
                    ),
                    "joint_weighted_correction_loss_coefficient": 1.0,
                    "standard_replay_loss_coefficient": 1.0,
                    "recomputed_from_bridge_candidate": False,
                },
                "masked_correction_loss": True,
                "probe_update_counts": list(PROBE_UPDATE_COUNTS),
                "selection_rule": "first_complete_confirmed_pass",
                "provisional_pass_requires_immediate_second_identical_repeat": True,
                "stop_after_first_complete_confirmed_pass": True,
                "stop_negative_after_update_ceiling": True,
                "retry_authorized": False,
            },
            "acceptance": {
                "frozen_gate_identity_sha256": EXPECTED_FROZEN_GATE_IDENTITY,
                "threshold_rule": "exact_frozen_relative_timestep_phase_mapping_per_chunk",
                "timestep_phase_mapping": frozen_timestep_mapping,
                "phase_joint_maximum_error_rad": frozen_thresholds,
                "all_executed_actions_must_pass": True,
                "all_starts_and_probe_seeds_must_pass": True,
                "all_confirming_repeats_must_be_hash_identical": True,
                "unexecuted_tail_is_scored": False,
                "strict_uniform_maximum_absolute_error_rad_report_only": 0.05,
                "maximum_source_batch_objective_ratio": sources["frozen_gate"][
                    "amended_gate_b_conjunction"
                ]["maximum_objective_ratio"],
                "gate_c_execution_authorized_by_pass": False,
            },
            "next_route": {
                "baseline_pass": "separate_gate_c_episode_0_authority_request",
                "baseline_fail": "retain_complete_correction_trajectory_then_compose_separate_training_authority",
                "training_pass": "separate_gate_c_episode_0_authority_request",
                "training_fail": "close_x_bridge_without_retry",
            },
            "model_constructed": False,
            "model_loaded": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "gate_c_executed": False,
            "threshold_changed": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "network_accessed": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_bridge_spec(payload: dict[str, Any], *, sources: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36o bridge design")
    expected = build_bridge_spec(sources=sources)
    if payload != expected:
        raise ValueError("T20.36o bridge design drifted")


def verify_bridge_spec_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = load_verified_sources(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / SPEC_PATH)
    verify_bridge_spec(archived, sources=sources)
    return archived


def _source_window(
    *,
    frames: list[dict[str, Any]],
    dataset_rows: list[dict[str, Any]],
    start: int,
    executed_length: int,
) -> dict[str, Any]:
    selected = frames[start : start + executed_length]
    rows = dataset_rows[start : start + executed_length]
    if len(selected) != executed_length or len(rows) != executed_length:
        raise ValueError("T20.36o source window is incomplete")
    frame_indices = [frame.get("frame_index") for frame in selected]
    if frame_indices != list(range(start, start + executed_length)):
        raise ValueError("T20.36o source frame order drifted")
    phases = [frame.get("task_phase") for frame in selected]
    if not all(isinstance(phase, str) and phase for phase in phases):
        raise ValueError("T20.36o source phase coverage drifted")
    physical_actions = [
        _six(frame.get("actions", {}).get("measured", {}).get("values"), "action")
        for frame in selected
    ]
    lerobot_actions = [mujoco_to_lerobot(action) for action in physical_actions]
    for row, expected_index, converted in zip(
        rows, frame_indices, lerobot_actions, strict=True
    ):
        if (
            row.get("frame_index") != expected_index
            or row.get("episode_index") != 0
            or not _vectors_close(row.get("action"), converted, tolerance=1e-4)
        ):
            raise ValueError("T20.36o dataset action lineage drifted")
    start_frame = selected[0]
    start_row = rows[0]
    observations = start_frame.get("observations", {})
    expected_state = mujoco_to_lerobot(
        _six(observations.get("joint_position_mujoco_rad"), "state")
    )
    if not _vectors_close(start_row.get("observation.state"), expected_state, tolerance=1e-4):
        raise ValueError("T20.36o dataset observation-state lineage drifted")
    image_roles = {
        "top": "observation.images.base_0_rgb",
        "wrist": "observation.images.left_wrist_0_rgb",
    }
    dataset_image_hashes = {}
    image_pixel_hashes = {}
    for role, key in image_roles.items():
        cell = start_row.get(key)
        if not isinstance(cell, dict) or not isinstance(cell.get("bytes"), bytes):
            raise ValueError(f"T20.36o {role} dataset image is missing")
        source_image = observations.get(role, {})
        encoded = source_image.get("png_base64")
        if not isinstance(encoded, str):
            raise ValueError(f"T20.36o {role} source image bytes are missing")
        source_bytes = base64.b64decode(encoded, validate=True)
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        if source_digest != source_image.get("image_sha256"):
            raise ValueError(f"T20.36o {role} source image hash drifted")
        dataset_digest = hashlib.sha256(cell["bytes"]).hexdigest()
        source_pixels = _image_pixel_sha256(source_bytes)
        dataset_pixels = _image_pixel_sha256(cell["bytes"])
        if source_pixels != dataset_pixels:
            raise ValueError(f"T20.36o {role} dataset image pixels drifted")
        dataset_image_hashes[role] = {
            "source_png_sha256": source_digest,
            "dataset_png_sha256": dataset_digest,
        }
        image_pixel_hashes[role] = source_pixels
    pad_count = N_ACTION_STEPS - executed_length
    padded_physical = [*physical_actions, *([physical_actions[-1]] * pad_count)]
    padded_lerobot = [*lerobot_actions, *([lerobot_actions[-1]] * pad_count)]
    mask = [True] * executed_length + [False] * pad_count
    frame_ids = [frame.get("frame_id") for frame in selected]
    record_ids = [frame.get("record_identity_sha256") for frame in selected]
    if not all(isinstance(value, str) and value for value in frame_ids):
        raise ValueError("T20.36o source frame IDs drifted")
    if not all(_is_sha(value) for value in record_ids):
        raise ValueError("T20.36o source record identities drifted")
    return {
        "start_frame": start,
        "executed_length": executed_length,
        "start_frame_id": frame_ids[0],
        "start_frame_record_identity_sha256": record_ids[0],
        "start_task_phase": phases[0],
        "source_frame_indices": frame_indices,
        "source_frame_ids": frame_ids,
        "source_frame_record_identity_sha256s": record_ids,
        "source_task_phase_by_offset": phases,
        "source_phase_runs": _phase_runs(phases),
        "source_window_identity_sha256": _canonical_sha(
            {
                "frame_ids": frame_ids,
                "record_ids": record_ids,
                "phases": phases,
                "actions": physical_actions,
            }
        ),
        "start_observation": {
            "joint_position_mujoco_rad": _six(
                observations.get("joint_position_mujoco_rad"), "state"
            ),
            "joint_velocity_mujoco_rad_s": _six(
                observations.get("joint_velocity_mujoco_rad_s"), "velocity"
            ),
            "top_image_sha256": observations["top"]["image_sha256"],
            "wrist_image_sha256": observations["wrist"]["image_sha256"],
            "identity_sha256": _canonical_sha(
                {
                    "state": observations.get("joint_position_mujoco_rad"),
                    "velocity": observations.get("joint_velocity_mujoco_rad_s"),
                    "top": observations["top"]["image_sha256"],
                    "wrist": observations["wrist"]["image_sha256"],
                }
            ),
        },
        "dataset_observation": {
            "dataset_index": start,
            "episode_index": start_row["episode_index"],
            "frame_index": start_row["frame_index"],
            "timestamp": start_row["timestamp"],
            "task_index": start_row["task_index"],
            "state_lerobot_deg": start_row["observation.state"],
            "image_sha256": dataset_image_hashes,
            "image_pixel_sha256": image_pixel_hashes,
            "identity_sha256": _canonical_sha(
                {
                    "dataset_index": start,
                    "episode_index": start_row["episode_index"],
                    "frame_index": start_row["frame_index"],
                    "timestamp": start_row["timestamp"],
                    "task_index": start_row["task_index"],
                    "state": start_row["observation.state"],
                    "images": dataset_image_hashes,
                    "image_pixels": image_pixel_hashes,
                }
            ),
        },
        "padded_target_action_mujoco_rad": padded_physical,
        "padded_target_action_lerobot_deg": padded_lerobot,
        "executed_target_action_sha256": _canonical_sha(physical_actions),
        "padded_target_action_sha256": _canonical_sha(padded_physical),
        "executed_mask": mask,
        "executed_mask_sha256": _canonical_sha(mask),
        "padding_rule": "repeat_last_episode_action_for_tensor_shape_only",
        "unexecuted_tail_actor_valid": False,
        "unexecuted_tail_gate_valid": False,
        "unexecuted_tail_loss_valid": False,
    }


def _policy_semantics(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PI05Policy"
    ]
    if len(classes) != 1:
        raise ValueError("T20.36o PI05Policy source class drifted")
    functions = {
        node.name: node
        for node in classes[0].body
        if isinstance(node, ast.FunctionDef) and node.name in {"reset", "select_action"}
    }
    if set(functions) != {"reset", "select_action"}:
        raise ValueError("T20.36o queue function coverage drifted")
    reset = ast.unparse(functions["reset"])
    select = ast.unparse(functions["select_action"])
    required_reset = "self._action_queue = deque(maxlen=self.config.n_action_steps)"
    required_select = (
        "if len(self._action_queue) == 0:",
        "self.predict_action_chunk(batch)[:, :self.config.n_action_steps]",
        "self._action_queue.extend(actions.transpose(0, 1))",
        "return self._action_queue.popleft()",
    )
    if required_reset not in reset or any(token not in select for token in required_select):
        raise ValueError("T20.36o PI0.5 queue semantics drifted")
    return {
        "reset_function_sha256": hashlib.sha256(reset.encode()).hexdigest(),
        "select_action_function_sha256": hashlib.sha256(select.encode()).hexdigest(),
        "reset_reinitializes_queue_to_n_action_steps": True,
        "select_action_samples_only_when_queue_empty": True,
        "select_action_slices_n_action_steps": True,
        "select_action_pops_one_action": True,
        "rtc_select_action_supported": False,
    }


def _load_episode_zero_rows(path: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    table = pq.read_table(path)
    rows = [row for row in table.to_pylist() if row.get("episode_index") == 0]
    if [row.get("frame_index") for row in rows] != list(range(ROLLOUT_FRAME_COUNT)):
        raise ValueError("T20.36o dataset episode-0 row order drifted")
    return rows


def _image_pixel_sha256(encoded: bytes) -> str:
    from PIL import Image

    with Image.open(io.BytesIO(encoded)) as image:
        rgb = image.convert("RGB")
        digest = hashlib.sha256()
        digest.update(canonical_json_bytes({"mode": rgb.mode, "size": list(rgb.size)}))
        digest.update(rgb.tobytes())
        return digest.hexdigest()


def _phase_runs(phases: list[str]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for offset, phase in enumerate(phases):
        if not runs or runs[-1]["task_phase"] != phase:
            runs.append(
                {
                    "task_phase": phase,
                    "start_offset": offset,
                    "end_offset_exclusive": offset + 1,
                }
            )
        else:
            runs[-1]["end_offset_exclusive"] = offset + 1
    return runs


def _payload_ref(*, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    ref = _file_ref(path)
    ref.update(
        {
            "schema_version": payload.get("schema_version"),
            "identity_sha256": payload.get("identity_sha256"),
        }
    )
    return ref


def _file_ref(path: Path) -> dict[str, Any]:
    absolute = path if path.is_absolute() else REPO_ROOT / path
    return {
        "path": path.as_posix() if not path.is_absolute() else str(path.relative_to(REPO_ROOT)),
        "sha256": _file_sha256(absolute),
        "size_bytes": absolute.stat().st_size,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _six(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError(f"T20.36o {label} must have six values")
    output = [float(item) for item in value]
    if not all(math.isfinite(item) for item in output):
        raise ValueError(f"T20.36o {label} must be finite")
    return output


def _vectors_close(left: Any, right: Any, *, tolerance: float) -> bool:
    if not isinstance(left, list) or len(left) != len(right):
        return False
    return all(
        math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tolerance)
        for a, b in zip(left, right, strict=True)
    )


def _is_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
