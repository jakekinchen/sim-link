"""Fail-closed Gate B contract for T20.33 one-batch memorization."""

from __future__ import annotations

import hashlib
import math

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.t20_17_clean_base_preflight import (
    DATASET_MANIFEST_PATH,
    DATASET_ROOT,
    EXPECTED_MODEL_REVISION,
    SOURCE_MANIFEST_PATH,
    TASK,
    verify_preflight_sources,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("configurations/robot_lab/t20_33_one_batch_training_spec.json")
RESULT_PATH = Path("configurations/robot_lab/t20_33_one_batch_result.json")
SCHEMA_VERSION = "scenesmith.t20_33_one_batch_training_spec.v1"
RESULT_SCHEMA_VERSION = "scenesmith.t20_33_one_batch_result.v1"
RUN_SCHEMA_VERSION = "scenesmith.t20_33_one_batch_run.v1"
DATASET_EPISODE_INDEX = 0
SOURCE_SEED = 0
FRAME_INDEX = 0
ACTION_HORIZON = 50
OPTIMIZER_UPDATES = 500
TRAINING_SEED = 20260717
LEARNING_RATE = 2.5e-5
LORA_RANK = 4
LORA_ALPHA = 4
INFERENCE_SEEDS = (20260721, 20260722, 20260723, 20260724, 20260725)
MAX_ACTION_ERROR_RAD = 0.05
MAX_OBJECTIVE_RATIO = 0.10


def build_training_spec(
    *,
    dataset_manifest_ref: dict[str, Any],
    source_manifest_ref: dict[str, Any],
    source_episode: dict[str, Any],
    source_entry: dict[str, Any],
    model_revision: str,
) -> dict[str, Any]:
    frames = source_episode.get("frames")
    if not isinstance(frames, list) or len(frames) < ACTION_HORIZON:
        raise ValueError("T20.33 source episode lacks the fixed horizon-50 batch")
    selected = frames[FRAME_INDEX : FRAME_INDEX + ACTION_HORIZON]
    actions = [_measured_action(frame) for frame in selected]
    first = selected[0]
    observations = first.get("observations", {})
    image_hashes = {
        role: _sha(observations.get(role, {}).get("image_sha256"), f"{role} image")
        for role in ("top", "wrist")
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": "T20.33",
        "scope": "gate_b_one_fixed_source_batch_memorization",
        "dataset_manifest_ref": dict(dataset_manifest_ref),
        "source_manifest_ref": dict(source_manifest_ref),
        "source_batch": {
            "dataset_root": str(DATASET_ROOT),
            "dataset_episode_index": DATASET_EPISODE_INDEX,
            "source_seed": SOURCE_SEED,
            "source_episode_file_sha256": _sha(
                source_entry.get("episode_file_sha256"), "source episode file"
            ),
            "source_episode_identity_sha256": _sha(
                source_entry.get("raw_rollout_record_identity_sha256"),
                "source episode identity",
            ),
            "frame_index": FRAME_INDEX,
            "action_horizon": ACTION_HORIZON,
            "action_variant": "measured",
            "action_units": "mujoco_radian",
            "measured_action_chunk_sha256": hashlib.sha256(
                canonical_json_bytes(actions)
            ).hexdigest(),
            "initial_observation_state_sha256": hashlib.sha256(
                canonical_json_bytes(
                    _six(
                        observations.get("joint_position_mujoco_rad"),
                        "initial state",
                    )
                )
            ).hexdigest(),
            "initial_image_sha256": image_hashes,
            "padding_or_inferred_actions": False,
        },
        "model": {
            "repo_id": "lerobot/pi05_base",
            "revision": model_revision,
            "device": "mps",
            "dtype": "float32",
            "adapter": "lora",
            "lora_rank": LORA_RANK,
            "lora_alpha": LORA_ALPHA,
        },
        "campaign": {
            "optimizer": "AdamW",
            "learning_rate": LEARNING_RATE,
            "weight_decay": 0.0,
            "gradient_clip_norm": 1.0,
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "batch_size": 1,
            "fixed_batch_repeated": True,
            "training_seed": TRAINING_SEED,
            "inference_seeds": list(INFERENCE_SEEDS),
            "network_mode": "offline_local_cache_only",
        },
        "gate": {
            "maximum_decoded_action_error_rad": MAX_ACTION_ERROR_RAD,
            "maximum_final_to_baseline_objective_ratio": MAX_OBJECTIVE_RATIO,
            "all_inference_seeds_must_pass": True,
        },
        "task": TASK,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_training": False,
        "closed_loop_rollout": False,
        "dataset_mutated": False,
        "statistics_changed": False,
        "twin_updated": False,
        "simulation_policy_accepted": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "physical_transfer_ready": False,
        "promotion_eligible": False,
    }
    return sign_payload(payload)


def verify_training_spec(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.33 one-batch training spec")
    expected_campaign = {
        "optimizer": "AdamW",
        "learning_rate": LEARNING_RATE,
        "weight_decay": 0.0,
        "gradient_clip_norm": 1.0,
        "optimizer_update_count": OPTIMIZER_UPDATES,
        "batch_size": 1,
        "fixed_batch_repeated": True,
        "training_seed": TRAINING_SEED,
        "inference_seeds": list(INFERENCE_SEEDS),
        "network_mode": "offline_local_cache_only",
    }
    expected_gate = {
        "maximum_decoded_action_error_rad": MAX_ACTION_ERROR_RAD,
        "maximum_final_to_baseline_objective_ratio": MAX_OBJECTIVE_RATIO,
        "all_inference_seeds_must_pass": True,
    }
    batch = payload.get("source_batch", {})
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != "T20.33"
        or batch.get("dataset_episode_index") != DATASET_EPISODE_INDEX
        or batch.get("source_seed") != SOURCE_SEED
        or batch.get("frame_index") != FRAME_INDEX
        or batch.get("action_horizon") != ACTION_HORIZON
        or batch.get("padding_or_inferred_actions") is not False
        or payload.get("campaign") != expected_campaign
        or payload.get("gate") != expected_gate
        or payload.get("model", {}).get("revision") != EXPECTED_MODEL_REVISION
    ):
        raise ValueError("T20.33 fixed batch, campaign, or gate drifted")
    for field in (
        "source_episode_file_sha256",
        "source_episode_identity_sha256",
        "measured_action_chunk_sha256",
        "initial_observation_state_sha256",
    ):
        _sha(batch.get(field), field)
    if set(batch.get("initial_image_sha256", {})) != {"top", "wrist"}:
        raise ValueError("T20.33 fixed batch image roles drifted")
    for role, value in batch["initial_image_sha256"].items():
        _sha(value, f"{role} image")
    false_fields = (
        "model_loaded",
        "model_inference",
        "optimizer_training",
        "closed_loop_rollout",
        "dataset_mutated",
        "statistics_changed",
        "twin_updated",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if any(payload.get(field) is not False for field in false_fields):
        raise ValueError("T20.33 preflight carries execution or authority drift")


def verify_preflight(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    t20_17 = verify_preflight_sources(repo_root=root)
    source_manifest = load_strict_json(root / SOURCE_MANIFEST_PATH)
    verify_episode_store(source_manifest, default_store_root())
    entries = [row for row in source_manifest["episodes"] if row.get("seed") == SOURCE_SEED]
    if len(entries) != 1:
        raise ValueError("T20.33 fixed source seed is missing or duplicated")
    entry = entries[0]
    relative = entry.get("relative_path")
    if not isinstance(relative, str) or Path(relative).name != relative:
        raise ValueError("T20.33 source path is unsafe")
    episode = load_strict_json(default_store_root() / relative)
    spec = build_training_spec(
        dataset_manifest_ref=artifact_ref(
            path=DATASET_MANIFEST_PATH,
            payload=t20_17["dataset_manifest"],
            repo_root=root,
        ),
        source_manifest_ref=artifact_ref(
            path=SOURCE_MANIFEST_PATH, payload=source_manifest, repo_root=root
        ),
        source_episode=episode,
        source_entry=entry,
        model_revision=t20_17["model_snapshot"]["revision"],
    )
    verify_training_spec(spec)
    return {"training_spec": spec, "source_episode": episode, "source_entry": entry}


def verify_training_spec_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    expected = verify_preflight(repo_root=repo_root)["training_spec"]
    archived = load_strict_json(Path(repo_root) / SPEC_PATH)
    verify_training_spec(archived)
    if archived != expected:
        raise ValueError("T20.33 training spec drifted from live sources")
    return archived


def build_result(*, spec: dict[str, Any], authority_identity: str, run: dict[str, Any]) -> dict[str, Any]:
    verify_training_spec(spec)
    verify_run(run, spec=spec, authority_identity=authority_identity)
    _sha(authority_identity, "authority identity")
    if run.get("optimizer_update_count") != OPTIMIZER_UPDATES:
        raise ValueError("T20.33 optimizer update accounting drifted")
    losses = run.get("per_update_objective")
    gradients = run.get("gradient_norms_before_clip")
    if not isinstance(losses, list) or len(losses) != OPTIMIZER_UPDATES:
        raise ValueError("T20.33 loss trace is incomplete")
    if not isinstance(gradients, list) or len(gradients) != OPTIMIZER_UPDATES:
        raise ValueError("T20.33 gradient trace is incomplete")
    baseline = _finite(run.get("baseline_objective_mean"), "baseline objective")
    final = _finite(run.get("final_objective_mean"), "final objective")
    if baseline <= 0 or any(not math.isfinite(float(value)) for value in losses + gradients):
        raise ValueError("T20.33 objective or gradient evidence is invalid")
    chunks = run.get("decoded_action_chunks")
    if not isinstance(chunks, list) or [row.get("inference_seed") for row in chunks] != list(INFERENCE_SEEDS):
        raise ValueError("T20.33 decoded action seed coverage drifted")
    for row in chunks:
        _sha(row.get("decoded_action_chunk_sha256"), "decoded action chunk")
        _finite(row.get("mean_absolute_error_rad"), "chunk mean error")
        _finite(row.get("maximum_absolute_error_rad"), "chunk maximum error")
    ratio = final / baseline
    action_pass = all(
        float(row["maximum_absolute_error_rad"]) <= MAX_ACTION_ERROR_RAD
        for row in chunks
    )
    objective_pass = ratio <= MAX_OBJECTIVE_RATIO
    passed = action_pass and objective_pass
    return sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": "T20.33",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "run_identity_sha256": _sha(run.get("identity_sha256"), "run identity"),
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "baseline_objective_mean": baseline,
            "final_objective_mean": final,
            "final_to_baseline_objective_ratio": ratio,
            "maximum_allowed_objective_ratio": MAX_OBJECTIVE_RATIO,
            "maximum_allowed_action_error_rad": MAX_ACTION_ERROR_RAD,
            "decoded_action_chunks": chunks,
            "all_decoded_chunks_within_threshold": action_pass,
            "objective_ratio_within_threshold": objective_pass,
            "gate_b_one_batch_memorization_passed": passed,
            "decision": "gate_b_pass" if passed else "gate_b_fail",
            "selected_next_hypothesis": (
                "gate_c_closed_loop_execution_semantics"
                if passed
                else "gate_b_model_or_trainer_plumbing"
            ),
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "twin_updated": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )


def verify_run(
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    verify_training_spec(spec)
    verify_signed_payload(payload, label="T20.33 one-batch run")
    if (
        payload.get("schema_version") != RUN_SCHEMA_VERSION
        or payload.get("task_id") != "T20.33"
        or payload.get("training_spec_identity_sha256") != spec["identity_sha256"]
        or payload.get("authority_decision_identity_sha256") != authority_identity
        or payload.get("optimizer_update_count") != OPTIMIZER_UPDATES
        or payload.get("training_seed") != TRAINING_SEED
        or payload.get("fixed_dataset_index") != FRAME_INDEX
        or payload.get("fixed_source_seed") != SOURCE_SEED
        or payload.get("action_horizon") != ACTION_HORIZON
    ):
        raise ValueError("T20.33 run identity, batch, or update accounting drifted")
    for field in (
        "source_measured_action_chunk_sha256",
        "dataset_action_chunk_sha256",
        "checkpoint_identity_sha256",
    ):
        _sha(payload.get(field), field)
    tree = payload.get("checkpoint_tree")
    if not isinstance(tree, list) or not tree:
        raise ValueError("T20.33 run checkpoint tree is missing")
    required = {"adapter_config.json", "adapter_model.safetensors"}
    if not required.issubset({row.get("path") for row in tree if isinstance(row, dict)}):
        raise ValueError("T20.33 run checkpoint tree is incomplete")
    if hashlib.sha256(canonical_json_bytes(tree)).hexdigest() != payload[
        "checkpoint_identity_sha256"
    ]:
        raise ValueError("T20.33 run checkpoint identity drifted")
    losses = payload.get("per_update_objective")
    gradients = payload.get("gradient_norms_before_clip")
    if not isinstance(losses, list) or len(losses) != OPTIMIZER_UPDATES:
        raise ValueError("T20.33 run loss trace is incomplete")
    if not isinstance(gradients, list) or len(gradients) != OPTIMIZER_UPDATES:
        raise ValueError("T20.33 run gradient trace is incomplete")
    for value in [
        payload.get("baseline_objective_mean"),
        payload.get("final_objective_mean"),
        *losses,
        *gradients,
    ]:
        _finite(value, "run numeric evidence")
    chunks = payload.get("decoded_action_chunks")
    if not isinstance(chunks, list) or [row.get("inference_seed") for row in chunks] != list(INFERENCE_SEEDS):
        raise ValueError("T20.33 run inference seed coverage drifted")
    for row in chunks:
        _sha(row.get("decoded_action_chunk_sha256"), "decoded action chunk")
        _finite(row.get("mean_absolute_error_rad"), "chunk mean error")
        _finite(row.get("maximum_absolute_error_rad"), "chunk maximum error")
    required_false = (
        "closed_loop_rollout",
        "dataset_mutated",
        "statistics_changed",
        "twin_updated",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if payload.get("optimizer_training") is not True or any(
        payload.get(field) is not False for field in required_false
    ):
        raise ValueError("T20.33 run execution or authority fields drifted")


def verify_result(payload: dict[str, Any], *, spec: dict[str, Any], run: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.33 one-batch result")
    expected = build_result(
        spec=spec,
        authority_identity=payload.get("authority_decision_identity_sha256"),
        run=run,
    )
    if payload != expected:
        raise ValueError("T20.33 result drifted from run evidence")


def _measured_action(frame: dict[str, Any]) -> list[float]:
    measured = frame.get("actions", {}).get("measured", {})
    if measured.get("state") != "derived" or measured.get("units") != "radian":
        raise ValueError("T20.33 measured action provenance drifted")
    return _six(measured.get("values"), "measured action")


def _six(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError(f"T20.33 {label} must contain six joints")
    result = [_finite(item, label) for item in value]
    return result


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"T20.33 {label} must be finite")
    return float(value)


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"T20.33 {label} must be lowercase SHA-256")
    return value
