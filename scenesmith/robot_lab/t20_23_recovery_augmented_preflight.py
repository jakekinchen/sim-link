"""T20.23 source-bound nominal plus successful-recovery dataset preflight.

This module may materialize and verify an actual package-owned LeRobotDataset.
It never loads a model, runs inference, starts an optimizer, or executes a
simulation or physical rollout.
"""

from __future__ import annotations

import hashlib
import math

from collections import Counter
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_native_episode_manifest import (
    build_lerobot_episode_manifest,
    verify_lerobot_episode_manifest,
)
from scenesmith.robot_lab.so101_coordinates import coordinate_contract, mujoco_to_lerobot
from scenesmith.robot_lab.t20_17_clean_base_preflight import (
    CAMERAS,
    HELD_OUT_SEEDS,
    IMAGE_KEYS,
    JOINT_NAMES,
    MODEL_REPO_ID,
    REPO_ROOT,
    SOURCE_MANIFEST_PATH as NOMINAL_SOURCE_MANIFEST_PATH,
    TASK,
    TRAINING_SEEDS,
    _dataset_frame as nominal_dataset_frame,
    _dataset_statistics,
    _features,
    _held_out_ref,
    _load_source_episode,
    resolve_model_snapshot,
    select_source_episodes,
    verify_preflight_sources as verify_nominal_preflight_sources,
)
from scenesmith.robot_lab.t20_18_state_fork_recovery import (
    verify_recovery_episode_package_gate,
)


RECOVERY_PACKAGE_GATE_PATH = Path(
    "configurations/robot_lab/t20_18_recovery_episode_package_gate.json"
)
DATASET_ROOT = Path("outputs/robot_lab/t20_23_recovery_augmented_dataset")
DATASET_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_23_recovery_augmented_dataset_manifest.json"
)
TRAINING_SPEC_PATH = Path(
    "configurations/robot_lab/t20_23_recovery_augmented_training_spec.json"
)
DATASET_REPO_ID = "scenesmith/t20-23-anchor-grasp-recovery-train"
DATASET_LABEL = "t20_23/nominal_plus_policy_visited_recovery_train"
SCHEMA_VERSION = "scenesmith.t20_23_recovery_augmented_training_spec.v1"
EXPECTED_NOMINAL_EPISODES = 6
EXPECTED_NOMINAL_FRAMES = 1464
EXPECTED_RECOVERY_EPISODES = 4
EXPECTED_RECOVERY_FRAMES = 866
EXPECTED_DIAGNOSTIC_EPISODES = 4
EXPECTED_DIAGNOSTIC_FRAMES = 424
EXPECTED_TOTAL_EPISODES = 10
EXPECTED_TOTAL_FRAMES = 2330
_FALSE_EXECUTION_FIELDS = (
    "model_loaded",
    "model_inference",
    "optimizer_training",
    "simulation_rollout_executed",
    "simulation_training_ready",
    "simulation_policy_accepted",
    "physical_transfer_ready",
    "promotion_eligible",
    "physical_actuation",
    "external_compute_started",
    "brev_compute_started",
)


def select_recovery_episodes(package: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Freeze successful recovery rows for training and retain all negatives."""

    if package.get("schema_version") != "scenesmith.t20_18_recovery_episode_package.v1":
        raise ValueError("T20.23 recovery package schema drifted")
    if package.get("actions_padded") is not False or package.get("actions_inferred") is not False:
        raise ValueError("T20.23 recovery package contains padded or inferred actions")
    if package.get("recovery_training_candidate") is not True:
        raise ValueError("T20.23 recovery package is not a training candidate")
    rows = package.get("episodes")
    if not isinstance(rows, list) or len(rows) != EXPECTED_RECOVERY_EPISODES + EXPECTED_DIAGNOSTIC_EPISODES:
        raise ValueError("T20.23 recovery episode count drifted")
    seen: set[str] = set()
    training: list[dict[str, Any]] = []
    diagnostic: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    frame_count = image_count = 0
    for value in rows:
        if not isinstance(value, dict):
            raise ValueError("T20.23 recovery episode row is invalid")
        row = _recovery_ref(value)
        branch_id = row["branch_id"]
        if branch_id in seen:
            raise ValueError("T20.23 recovery package contains a duplicate branch")
        seen.add(branch_id)
        counts[row["outcome_class"]] += 1
        frame_count += row["frame_count"]
        image_count += row["image_count"]
        if row["outcome_class"] == "recovery":
            training.append(row)
        else:
            diagnostic.append(row)
    if counts != Counter({"recovery": 4, "near_failure": 2, "failure": 2}):
        raise ValueError("T20.23 recovery outcome counts drifted")
    if frame_count != 1290 or package.get("frame_count") != frame_count:
        raise ValueError("T20.23 recovery package frame count drifted")
    if image_count != 2580 or package.get("image_count") != image_count:
        raise ValueError("T20.23 recovery package image count drifted")
    if sum(row["frame_count"] for row in training) != EXPECTED_RECOVERY_FRAMES:
        raise ValueError("T20.23 successful recovery frame count drifted")
    if sum(row["frame_count"] for row in diagnostic) != EXPECTED_DIAGNOSTIC_FRAMES:
        raise ValueError("T20.23 diagnostic frame count drifted")
    return {"training": training, "diagnostic": diagnostic}


def build_training_spec(
    *,
    nominal_episode_refs: list[dict[str, Any]],
    recovery_episode_refs: list[dict[str, Any]],
    diagnostic_episode_refs: list[dict[str, Any]],
    held_out_episode_refs: list[dict[str, Any]],
    dataset_manifest_ref: dict[str, Any],
    nominal_source_manifest_ref: dict[str, Any],
    recovery_package_manifest_ref: dict[str, Any],
    dataset_statistics: dict[str, Any],
    model_snapshot: dict[str, Any],
) -> dict[str, Any]:
    nominal = [_nominal_ref(row) for row in nominal_episode_refs]
    recovery = [_recovery_ref(row) for row in recovery_episode_refs]
    diagnostic = [_recovery_ref(row) for row in diagnostic_episode_refs]
    held_out = [_held_out_training_ref(row) for row in held_out_episode_refs]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "scope": "t20_23_source_bound_nominal_plus_successful_recovery_simulation_training_preflight",
        "dataset_manifest_ref": dict(dataset_manifest_ref),
        "nominal_source_manifest_ref": dict(nominal_source_manifest_ref),
        "recovery_package_manifest_ref": dict(recovery_package_manifest_ref),
        "nominal_training_episodes": nominal,
        "recovery_training_episodes": recovery,
        "diagnostic_episodes": diagnostic,
        "held_out_episodes": held_out,
        "dataset_statistics": dict(dataset_statistics),
        "model_snapshot": dict(model_snapshot),
        "coordinate_contract": coordinate_contract(),
        "dataset_contract": {
            "dataset_repo_id": DATASET_REPO_ID,
            "episode_count": EXPECTED_TOTAL_EPISODES,
            "frame_count": EXPECTED_TOTAL_FRAMES,
            "source_episode_counts": {
                "nominal_strict_success": EXPECTED_NOMINAL_EPISODES,
                "policy_visited_recovery": EXPECTED_RECOVERY_EPISODES,
            },
            "source_frame_counts": {
                "nominal_strict_success": EXPECTED_NOMINAL_FRAMES,
                "policy_visited_recovery": EXPECTED_RECOVERY_FRAMES,
            },
            "diagnostic_episode_count": EXPECTED_DIAGNOSTIC_EPISODES,
            "diagnostic_frame_count": EXPECTED_DIAGNOSTIC_FRAMES,
            "training_seeds": list(TRAINING_SEEDS),
            "held_out_seeds": list(HELD_OUT_SEEDS),
            "camera_source_roles": list(CAMERAS),
            "image_feature_keys": [IMAGE_KEYS[name] for name in CAMERAS],
            "joint_names": list(JOINT_NAMES),
            "state_dimension": 6,
            "action_dimension": 6,
            "action_variant": "measured",
            "padding_or_inferred_actions": False,
            "implicit_resampling_or_duplication": False,
            "diagnostics_in_training": False,
            "held_out_in_training": False,
            "diagnostics_or_held_out_in_statistics": False,
        },
        "campaign": {
            "official_training_entrypoint": "lerobot.scripts.lerobot_train",
            "policy_type": "pi05",
            "adapter": "lora",
            "lora_rank": 4,
            "device": "mps",
            "batch_size": 1,
            "optimizer_update_count": 500,
            "training_seed": 20260714,
            "processor_statistics_source": "lerobot_dataset_meta_stats",
            "normalization": "QUANTILES",
            "network_mode": "offline_local_cache_only",
            "strict_closed_loop_evaluation_seeds": [6, 7],
        },
        "dataset_mixture_frozen": True,
        "task": TASK,
        "simulation_only": True,
        **{field: False for field in _FALSE_EXECUTION_FIELDS},
        "authority_not_granted": [
            "simulation_training_ready",
            "simulation_optimizer_training",
            "simulation_policy_accepted",
            "physical_transfer_ready",
            "promotion_eligible",
            "physical_actuation",
            "external_compute",
            "brev_compute",
        ],
    }
    return sign_payload(payload)


def verify_training_spec(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.23 recovery-augmented training specification")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("T20.23 training specification schema drifted")
    if payload.get("dataset_mixture_frozen") is not True or payload.get("simulation_only") is not True:
        raise ValueError("T20.23 dataset mixture or simulation scope drifted")
    for field in _FALSE_EXECUTION_FIELDS:
        if payload.get(field) is not False:
            raise ValueError(f"T20.23 execution or authority field drifted: {field}")
    nominal = payload.get("nominal_training_episodes")
    recovery = payload.get("recovery_training_episodes")
    diagnostic = payload.get("diagnostic_episodes")
    held_out = payload.get("held_out_episodes")
    if not isinstance(nominal, list) or [row.get("seed") for row in nominal] != list(TRAINING_SEEDS):
        raise ValueError("T20.23 nominal training membership drifted")
    if nominal != [_nominal_ref(row) for row in nominal]:
        raise ValueError("T20.23 nominal training references drifted")
    if len(nominal) != EXPECTED_NOMINAL_EPISODES or sum(row.get("frame_count", 0) for row in nominal) != EXPECTED_NOMINAL_FRAMES:
        raise ValueError("T20.23 nominal training counts drifted")
    if not isinstance(recovery, list) or len(recovery) != EXPECTED_RECOVERY_EPISODES:
        raise ValueError("T20.23 recovery training membership drifted")
    if any(row.get("outcome_class") != "recovery" for row in recovery):
        raise ValueError("T20.23 non-recovery outcome entered training")
    if recovery != [_recovery_ref(row) for row in recovery]:
        raise ValueError("T20.23 recovery training references drifted")
    if sum(row.get("frame_count", 0) for row in recovery) != EXPECTED_RECOVERY_FRAMES:
        raise ValueError("T20.23 recovery training counts drifted")
    if not isinstance(diagnostic, list) or len(diagnostic) != EXPECTED_DIAGNOSTIC_EPISODES:
        raise ValueError("T20.23 diagnostic membership drifted")
    if Counter(row.get("outcome_class") for row in diagnostic) != Counter({"near_failure": 2, "failure": 2}):
        raise ValueError("T20.23 diagnostic outcomes drifted")
    if diagnostic != [_recovery_ref(row) for row in diagnostic]:
        raise ValueError("T20.23 diagnostic references drifted")
    if sum(row.get("frame_count", 0) for row in diagnostic) != EXPECTED_DIAGNOSTIC_FRAMES:
        raise ValueError("T20.23 diagnostic counts drifted")
    training_ids = {row.get("branch_id") for row in recovery}
    diagnostic_ids = {row.get("branch_id") for row in diagnostic}
    if len(training_ids) != len(recovery) or len(diagnostic_ids) != len(diagnostic) or training_ids & diagnostic_ids:
        raise ValueError("T20.23 recovery membership aliases or duplicates")
    if not isinstance(held_out, list) or [row.get("seed") for row in held_out] != list(HELD_OUT_SEEDS):
        raise ValueError("T20.23 held-out membership drifted")
    if held_out != [_held_out_training_ref(row) for row in held_out]:
        raise ValueError("T20.23 held-out references or exclusion flags drifted")
    expected_contract = {
        "dataset_repo_id": DATASET_REPO_ID,
        "episode_count": EXPECTED_TOTAL_EPISODES,
        "frame_count": EXPECTED_TOTAL_FRAMES,
        "source_episode_counts": {"nominal_strict_success": 6, "policy_visited_recovery": 4},
        "source_frame_counts": {"nominal_strict_success": 1464, "policy_visited_recovery": 866},
        "diagnostic_episode_count": 4,
        "diagnostic_frame_count": 424,
        "training_seeds": list(TRAINING_SEEDS),
        "held_out_seeds": list(HELD_OUT_SEEDS),
        "camera_source_roles": list(CAMERAS),
        "image_feature_keys": [IMAGE_KEYS[name] for name in CAMERAS],
        "joint_names": list(JOINT_NAMES),
        "state_dimension": 6,
        "action_dimension": 6,
        "action_variant": "measured",
        "padding_or_inferred_actions": False,
        "implicit_resampling_or_duplication": False,
        "diagnostics_in_training": False,
        "held_out_in_training": False,
        "diagnostics_or_held_out_in_statistics": False,
    }
    if payload.get("dataset_contract") != expected_contract:
        raise ValueError("T20.23 dataset contract drifted")
    expected_campaign = {
        "official_training_entrypoint": "lerobot.scripts.lerobot_train",
        "policy_type": "pi05",
        "adapter": "lora",
        "lora_rank": 4,
        "device": "mps",
        "batch_size": 1,
        "optimizer_update_count": 500,
        "training_seed": 20260714,
        "processor_statistics_source": "lerobot_dataset_meta_stats",
        "normalization": "QUANTILES",
        "network_mode": "offline_local_cache_only",
        "strict_closed_loop_evaluation_seeds": [6, 7],
    }
    if payload.get("campaign") != expected_campaign:
        raise ValueError("T20.23 campaign bounds drifted")
    stats = payload.get("dataset_statistics", {})
    if stats.get("source") != "lerobot_dataset_meta_stats" or stats.get("normalization") != "QUANTILES":
        raise ValueError("T20.23 dataset statistics contract drifted")
    if payload.get("model_snapshot", {}).get("repo_id") != MODEL_REPO_ID:
        raise ValueError("T20.23 model repository drifted")
    if payload.get("model_snapshot", {}).get("revision") != "7de663972b7817d2c4cf2d84c821153dfea772e9":
        raise ValueError("T20.23 model revision drifted")


def recovery_dataset_frame(
    repo_root: Path,
    episode: dict[str, Any],
    frame: dict[str, Any],
    *,
    frame_index: int,
) -> dict[str, Any]:
    """Convert one verified T20.18 actor-facing frame into LeRobot features."""

    import numpy as np
    from PIL import Image

    if episode.get("outcome_class") != "recovery":
        raise ValueError("T20.23 only recovery outcomes may enter training")
    if episode.get("actions_padded") is not False or episode.get("actions_inferred") is not False:
        raise ValueError("T20.23 recovery episode contains padded or inferred actions")
    actions = episode.get("measured_actions")
    if not isinstance(actions, list) or frame_index < 0 or frame_index >= len(actions):
        raise ValueError("T20.23 measured action binding is absent")
    rendered_state = _finite_six(frame.get("state"), "recovery state")
    rendered_action = _finite_six(frame.get("action"), "recovery action")
    state = mujoco_to_lerobot(_finite_six(frame.get("mujoco_qpos"), "MuJoCo state"))
    measured = mujoco_to_lerobot(
        _finite_six(actions[frame_index], "measured action radians")
    )
    if max(abs(left - right) for left, right in zip(rendered_state, state, strict=True)) > 5e-7:
        raise ValueError("T20.23 rendered state drifted from its MuJoCo source")
    if max(abs(left - right) for left, right in zip(rendered_action, measured, strict=True)) > 5e-7:
        raise ValueError("T20.23 frame action drifted from its measured action")
    images = frame.get("actor_observation_images")
    if not isinstance(images, dict) or set(images) != set(CAMERAS):
        raise ValueError("T20.23 recovery image roles drifted")
    result: dict[str, Any] = {
        "task": TASK,
        "observation.state": np.asarray(state, dtype=np.float32),
        "action": np.asarray(measured, dtype=np.float32),
    }
    root = Path(repo_root).resolve()
    for role in CAMERAS:
        ref = images[role]
        if not isinstance(ref, dict):
            raise ValueError(f"T20.23 {role} image reference is invalid")
        relative = ref.get("path")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"T20.23 {role} image path is invalid")
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ValueError(f"T20.23 {role} image path escapes checkout") from error
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"T20.23 {role} image is absent or aliased")
        if _sha_file(path) != ref.get("file_sha256"):
            raise ValueError(f"T20.23 {role} image hash drifted")
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            if rgb.size != (256, 256) or ref.get("width") != 256 or ref.get("height") != 256 or ref.get("channels") != 3:
                raise ValueError(f"T20.23 {role} image dimensions drifted")
            result[IMAGE_KEYS[role]] = np.asarray(rgb, dtype=np.uint8)
    return result


def materialize_dataset(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = _verified_sources(root)
    dataset_root = root / DATASET_ROOT
    if dataset_root.exists():
        raise FileExistsError(f"Persistent T20.23 LeRobotDataset already exists: {dataset_root}")
    from lerobot.datasets import LeRobotDataset

    dataset = LeRobotDataset.create(
        repo_id=DATASET_REPO_ID,
        fps=30,
        root=dataset_root,
        robot_type="so101_follower",
        features=_features(),
        use_videos=False,
        image_writer_processes=0,
        image_writer_threads=0,
    )
    annotations: list[dict[str, Any]] = []
    for output_index, row in enumerate(sources["nominal"]["training"]):
        episode = _load_source_episode(root, row)
        for frame in episode["frames"]:
            dataset.add_frame(nominal_dataset_frame(frame))
        dataset.save_episode(parallel_encoding=False)
        annotations.append(_annotation(output_index, row["raw_rollout_record_identity_sha256"]))
    for row in sources["recovery"]["training"]:
        episode = load_strict_json(root / row["path"])
        verify_signed_payload(episode, label="T20.23 selected recovery episode")
        frames = episode.get("frames")
        if not isinstance(frames, list) or len(frames) != row["frame_count"]:
            raise ValueError("T20.23 selected recovery episode frame count drifted")
        output_index = len(annotations)
        for frame_index, frame in enumerate(frames):
            dataset.add_frame(
                recovery_dataset_frame(root, episode, frame, frame_index=frame_index)
            )
        dataset.save_episode(parallel_encoding=False)
        annotations.append(_annotation(output_index, row["identity_sha256"]))
    dataset.finalize()
    loaded = LeRobotDataset(DATASET_REPO_ID, root=dataset_root, return_uint8=True)
    manifest = build_lerobot_episode_manifest(
        loaded, dataset_label=DATASET_LABEL, episode_annotations=annotations
    )
    dump_canonical_json(root / DATASET_MANIFEST_PATH, manifest)
    return verify_preflight_sources(repo_root=root)


def verify_preflight_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    sources = _verified_sources(root)
    from lerobot.datasets import LeRobotDataset

    dataset = LeRobotDataset(DATASET_REPO_ID, root=root / DATASET_ROOT, return_uint8=True)
    annotations = [
        *[
            _annotation(index, row["raw_rollout_record_identity_sha256"])
            for index, row in enumerate(sources["nominal"]["training"])
        ],
        *[
            _annotation(index + EXPECTED_NOMINAL_EPISODES, row["identity_sha256"])
            for index, row in enumerate(sources["recovery"]["training"])
        ],
    ]
    manifest = load_strict_json(root / DATASET_MANIFEST_PATH)
    verify_lerobot_episode_manifest(
        manifest, dataset, dataset_label=DATASET_LABEL, episode_annotations=annotations
    )
    if dataset.meta.total_episodes != EXPECTED_TOTAL_EPISODES or dataset.meta.total_frames != EXPECTED_TOTAL_FRAMES:
        raise ValueError("Persistent T20.23 dataset cardinality drifted")
    stats = _dataset_statistics(dataset)
    snapshot = resolve_model_snapshot()
    nominal_manifest = load_strict_json(root / NOMINAL_SOURCE_MANIFEST_PATH)
    package_path = Path(sources["recovery_gate"]["package_manifest_path"])
    package = load_strict_json(root / package_path)
    spec = build_training_spec(
        nominal_episode_refs=sources["nominal"]["training"],
        recovery_episode_refs=sources["recovery"]["training"],
        diagnostic_episode_refs=sources["recovery"]["diagnostic"],
        held_out_episode_refs=[_held_out_ref(row) for row in sources["nominal"]["held_out"]],
        dataset_manifest_ref=artifact_ref(path=DATASET_MANIFEST_PATH, payload=manifest, repo_root=root),
        nominal_source_manifest_ref=artifact_ref(path=NOMINAL_SOURCE_MANIFEST_PATH, payload=nominal_manifest, repo_root=root),
        recovery_package_manifest_ref=artifact_ref(path=package_path, payload=package, repo_root=root),
        dataset_statistics=stats,
        model_snapshot=snapshot,
    )
    verify_training_spec(spec)
    return {
        "dataset_manifest": manifest,
        "training_spec": spec,
        "dataset_statistics": stats,
        "model_snapshot": snapshot,
    }


def write_training_spec(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = verify_preflight_sources(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / TRAINING_SPEC_PATH, result["training_spec"])
    return result


def verify_training_spec_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = verify_preflight_sources(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / TRAINING_SPEC_PATH)
    verify_training_spec(archived)
    if archived != result["training_spec"]:
        raise ValueError("T20.23 training specification drifted from live sources")
    return archived


def _verified_sources(root: Path) -> dict[str, Any]:
    verify_nominal_preflight_sources(repo_root=root)
    nominal_manifest = load_strict_json(root / NOMINAL_SOURCE_MANIFEST_PATH)
    nominal = select_source_episodes(nominal_manifest)
    gate = load_strict_json(root / RECOVERY_PACKAGE_GATE_PATH)
    package = verify_recovery_episode_package_gate(gate, repo_root=root)
    recovery = select_recovery_episodes(package)
    return {"nominal": nominal, "recovery": recovery, "recovery_gate": gate}


def _nominal_ref(row: dict[str, Any]) -> dict[str, Any]:
    seed = row.get("seed")
    frames = row.get("frame_count")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("T20.23 nominal seed is invalid")
    if isinstance(frames, bool) or not isinstance(frames, int) or frames <= 0:
        raise ValueError("T20.23 nominal frame count is invalid")
    return {
        "seed": seed,
        "frame_count": frames,
        "raw_rollout_record_identity_sha256": _sha(
            row.get("raw_rollout_record_identity_sha256"), "nominal rollout identity"
        ),
    }


def _recovery_ref(row: dict[str, Any]) -> dict[str, Any]:
    outcome = row.get("outcome_class")
    if outcome not in {"recovery", "near_failure", "failure"}:
        raise ValueError("T20.23 recovery outcome class is invalid")
    frames = row.get("frame_count")
    images = row.get("image_count")
    if isinstance(frames, bool) or not isinstance(frames, int) or frames <= 0:
        raise ValueError("T20.23 recovery frame count is invalid")
    if isinstance(images, bool) or not isinstance(images, int) or images != frames * len(CAMERAS):
        raise ValueError("T20.23 recovery image count is invalid")
    path = row.get("path")
    if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("T20.23 recovery episode path is invalid")
    return {
        "branch_id": _sha(row.get("branch_id"), "recovery branch ID"),
        "identity_sha256": _sha(row.get("identity_sha256"), "recovery episode identity"),
        "file_sha256": _sha(row.get("file_sha256"), "recovery episode file hash"),
        "path": path,
        "outcome_class": outcome,
        "frame_count": frames,
        "image_count": images,
        "included_in_training_dataset": outcome == "recovery",
        "included_in_dataset_statistics": outcome == "recovery",
    }


def _held_out_training_ref(row: dict[str, Any]) -> dict[str, Any]:
    seed = row.get("seed")
    frames = row.get("frame_count")
    relative = row.get("relative_path")
    if seed not in HELD_OUT_SEEDS:
        raise ValueError("T20.23 held-out seed is invalid")
    if isinstance(frames, bool) or not isinstance(frames, int) or frames <= 0:
        raise ValueError("T20.23 held-out frame count is invalid")
    if not isinstance(relative, str) or Path(relative).name != relative:
        raise ValueError("T20.23 held-out episode path is invalid")
    result = {
        "seed": seed,
        "frame_count": frames,
        "relative_path": relative,
        "episode_file_sha256": _sha(
            row.get("episode_file_sha256"), "held-out episode file hash"
        ),
        "raw_rollout_record_identity_sha256": _sha(
            row.get("raw_rollout_record_identity_sha256"),
            "held-out rollout identity",
        ),
        "included_in_training_dataset": False,
        "included_in_dataset_statistics": False,
    }
    if row.get("included_in_training_dataset") is not False:
        raise ValueError("T20.23 held-out episode entered training")
    if row.get("included_in_dataset_statistics") is not False:
        raise ValueError("T20.23 held-out episode entered dataset statistics")
    return result


def _annotation(index: int, identity: str) -> dict[str, Any]:
    return {
        "episode_index": index,
        "raw_rollout_identity_sha256": identity,
        "eligible": True,
        "quarantine_reason": None,
    }


def _finite_six(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError(f"T20.23 {label} must contain exactly six values")
    result = [float(item) for item in value]
    if not all(math.isfinite(item) for item in result):
        raise ValueError(f"T20.23 {label} contains a non-finite value")
    return result


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"T20.23 {label} must be lowercase SHA-256")
    return value


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
