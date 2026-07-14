"""T20.17 source-native dataset and clean PI0.5-base preflight.

This module may materialize and verify a package-owned LeRobotDataset, but it
does not load a policy, run inference, start an optimizer, or execute a
simulation rollout.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_native_episode_manifest import (
    build_lerobot_episode_manifest,
    verify_lerobot_episode_manifest,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import verify_episode_store
from scenesmith.robot_lab.so101_coordinates import coordinate_contract, mujoco_to_lerobot


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST_PATH = Path("configurations/robot_lab/t17_5b_episode_generation_manifest.json")
SOURCE_STORE_ROOT = Path("outputs/robot_lab/t17_5b_raw_store")
DATASET_ROOT = Path("outputs/robot_lab/t20_17_lerobot_training_dataset")
DATASET_MANIFEST_PATH = Path("configurations/robot_lab/t20_17_lerobot_dataset_manifest.json")
TRAINING_SPEC_PATH = Path("configurations/robot_lab/t20_17_clean_base_training_spec.json")
DATASET_REPO_ID = "scenesmith/t20-17-anchor-grasp-train"
DATASET_LABEL = "t20_17/source_native_anchor_grasp_train"
TRAINING_SEEDS = (0, 1, 2, 3, 4, 5)
HELD_OUT_SEEDS = (6, 7)
CAMERAS = ("top", "wrist")
IMAGE_KEYS = {
    "top": "observation.images.base_0_rgb",
    "wrist": "observation.images.left_wrist_0_rgb",
}
JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)
TASK = "Grasp the lightweight anchor, lift 40 mm, hold, lower, release, and retreat."
MODEL_REPO_ID = "lerobot/pi05_base"
EXPECTED_MODEL_REVISION = "7de663972b7817d2c4cf2d84c821153dfea772e9"
MODEL_FILES = ("config.json", "model.safetensors", "policy_postprocessor.json", "policy_preprocessor.json")
SCHEMA_VERSION = "scenesmith.t20_17_clean_base_training_spec.v1"


def select_source_episodes(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    episodes = manifest.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError("Source episode manifest lacks episodes")
    by_seed: dict[int, dict[str, Any]] = {}
    for row in episodes:
        if not isinstance(row, dict) or isinstance(row.get("seed"), bool) or not isinstance(row.get("seed"), int):
            raise ValueError("Source episode seed is invalid")
        seed = row["seed"]
        if seed in by_seed:
            raise ValueError("Source episode manifest contains a duplicate seed")
        if row.get("outcome", {}).get("strict_success") is not True:
            raise ValueError(f"Source seed {seed} is not strict-success evidence")
        frame_count = row.get("frame_count")
        if isinstance(frame_count, bool) or not isinstance(frame_count, int) or frame_count <= 0:
            raise ValueError("Source episode frame count is invalid")
        for key in ("episode_file_sha256", "raw_rollout_record_identity_sha256"):
            _require_sha(row.get(key), label=f"source {key}")
        by_seed[seed] = dict(row)
    required = set(TRAINING_SEEDS + HELD_OUT_SEEDS)
    if set(by_seed) != required:
        raise ValueError("Source episode seed coverage drifted from the fixed split")
    return {
        "training": [by_seed[seed] for seed in TRAINING_SEEDS],
        "held_out": [by_seed[seed] for seed in HELD_OUT_SEEDS],
    }


def build_training_spec(
    *,
    dataset_manifest_ref: dict[str, Any],
    source_manifest_ref: dict[str, Any],
    model_snapshot: dict[str, Any],
    dataset_statistics: dict[str, Any],
    held_out_episodes: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "scope": "t20_17_clean_pi05_base_dataset_native_simulation_training",
        "source_dataset_manifest_ref": dict(dataset_manifest_ref),
        "source_episode_store_manifest_ref": dict(source_manifest_ref),
        "dataset_statistics": dict(dataset_statistics),
        "model_snapshot": dict(model_snapshot),
        "held_out_episodes": list(held_out_episodes),
        "coordinate_contract": coordinate_contract(),
        "dataset_contract": {
            "training_seeds": list(TRAINING_SEEDS),
            "held_out_seeds": list(HELD_OUT_SEEDS),
            "camera_source_roles": list(CAMERAS),
            "image_feature_keys": [IMAGE_KEYS[name] for name in CAMERAS],
            "joint_names": list(JOINT_NAMES),
            "state_dimension": 6,
            "action_dimension": 6,
            "action_variant": "measured",
            "padding_or_inferred_actions": False,
            "statistics_include_held_out": False,
        },
        "campaign": {
            "official_training_entrypoint": "lerobot.scripts.lerobot_train",
            "policy_type": "pi05",
            "adapter": "lora",
            "lora_rank": 4,
            "device": "mps",
            "batch_size": 1,
            "optimizer_update_count": 250,
            "training_seed": 20260714,
            "processor_statistics_source": "lerobot_dataset_meta_stats",
            "normalization": "QUANTILES",
            "network_mode": "offline_local_cache_only",
            "strict_closed_loop_evaluation_seed": 6,
        },
        "task": TASK,
        "simulation_only": True,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_training": False,
        "simulation_rollout_executed": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
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
    verify_signed_payload(payload, label="T20.17 clean-base training specification")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("T20.17 training specification schema drifted")
    dataset = payload.get("dataset_contract", {})
    expected_dataset = {
        "training_seeds": list(TRAINING_SEEDS),
        "held_out_seeds": list(HELD_OUT_SEEDS),
        "camera_source_roles": list(CAMERAS),
        "image_feature_keys": [IMAGE_KEYS[name] for name in CAMERAS],
        "joint_names": list(JOINT_NAMES),
        "state_dimension": 6,
        "action_dimension": 6,
        "action_variant": "measured",
        "padding_or_inferred_actions": False,
        "statistics_include_held_out": False,
    }
    if dataset != expected_dataset:
        raise ValueError("T20.17 dataset contract drifted")
    expected_campaign = {
        "official_training_entrypoint": "lerobot.scripts.lerobot_train",
        "policy_type": "pi05",
        "adapter": "lora",
        "lora_rank": 4,
        "device": "mps",
        "batch_size": 1,
        "optimizer_update_count": 250,
        "training_seed": 20260714,
        "processor_statistics_source": "lerobot_dataset_meta_stats",
        "normalization": "QUANTILES",
        "network_mode": "offline_local_cache_only",
        "strict_closed_loop_evaluation_seed": 6,
    }
    if payload.get("campaign") != expected_campaign:
        raise ValueError("T20.17 campaign bounds drifted")
    stats = payload.get("dataset_statistics", {})
    if stats.get("normalization") != "QUANTILES":
        raise ValueError("T20.17 requires package dataset quantile statistics")
    if [row.get("seed") for row in payload.get("held_out_episodes", [])] != list(HELD_OUT_SEEDS):
        raise ValueError("T20.17 held-out episode binding drifted")
    if payload.get("model_snapshot", {}).get("repo_id") != MODEL_REPO_ID:
        raise ValueError("T20.17 model repository drifted")
    if payload.get("model_snapshot", {}).get("revision") != EXPECTED_MODEL_REVISION:
        raise ValueError("T20.17 model revision drifted")
    if any(payload.get(name) is not False for name in (
        "model_loaded", "model_inference", "optimizer_training", "simulation_rollout_executed",
        "physical_actuation", "external_compute_started", "brev_compute_started",
    )):
        raise ValueError("T20.17 preflight carries unauthorized execution state")


def materialize_dataset(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    source_manifest = load_strict_json(root / SOURCE_MANIFEST_PATH)
    verify_episode_store(source_manifest, root / SOURCE_STORE_ROOT)
    selected = select_source_episodes(source_manifest)
    dataset_root = root / DATASET_ROOT
    if dataset_root.exists():
        raise FileExistsError(f"Persistent LeRobot dataset already exists: {dataset_root}")
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
    annotations = []
    for output_index, row in enumerate(selected["training"]):
        episode = _load_source_episode(root, row)
        for frame in episode["frames"]:
            dataset.add_frame(_dataset_frame(frame))
        dataset.save_episode(parallel_encoding=False)
        annotations.append({
            "episode_index": output_index,
            "raw_rollout_identity_sha256": row["raw_rollout_record_identity_sha256"],
            "eligible": True,
            "quarantine_reason": None,
        })
    dataset.finalize()
    loaded = LeRobotDataset(DATASET_REPO_ID, root=dataset_root, return_uint8=True)
    manifest = build_lerobot_episode_manifest(
        loaded, dataset_label=DATASET_LABEL, episode_annotations=annotations
    )
    dump_canonical_json(root / DATASET_MANIFEST_PATH, manifest)
    return verify_preflight_sources(repo_root=root)


def verify_preflight_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    source_manifest = load_strict_json(root / SOURCE_MANIFEST_PATH)
    verify_episode_store(source_manifest, root / SOURCE_STORE_ROOT)
    selected = select_source_episodes(source_manifest)
    from lerobot.datasets import LeRobotDataset
    dataset = LeRobotDataset(DATASET_REPO_ID, root=root / DATASET_ROOT, return_uint8=True)
    annotations = [
        {"episode_index": index, "raw_rollout_identity_sha256": row["raw_rollout_record_identity_sha256"], "eligible": True, "quarantine_reason": None}
        for index, row in enumerate(selected["training"])
    ]
    manifest = load_strict_json(root / DATASET_MANIFEST_PATH)
    verify_lerobot_episode_manifest(
        manifest, dataset, dataset_label=DATASET_LABEL, episode_annotations=annotations
    )
    if dataset.meta.total_episodes != 6 or dataset.meta.total_frames != 1464:
        raise ValueError("Persistent T20.17 dataset cardinality drifted")
    stats = _dataset_statistics(dataset)
    snapshot = resolve_model_snapshot()
    held_out = [_held_out_ref(row) for row in selected["held_out"]]
    spec = build_training_spec(
        dataset_manifest_ref=artifact_ref(path=DATASET_MANIFEST_PATH, payload=manifest, repo_root=root),
        source_manifest_ref=artifact_ref(path=SOURCE_MANIFEST_PATH, payload=source_manifest, repo_root=root),
        model_snapshot=snapshot,
        dataset_statistics=stats,
        held_out_episodes=held_out,
    )
    verify_training_spec(spec)
    return {"dataset_manifest": manifest, "training_spec": spec, "dataset_statistics": stats, "model_snapshot": snapshot}


def write_training_spec(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = verify_preflight_sources(repo_root=repo_root)
    dump_canonical_json(Path(repo_root) / TRAINING_SPEC_PATH, result["training_spec"])
    return result


def verify_training_spec_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = verify_preflight_sources(repo_root=repo_root)
    archived = load_strict_json(Path(repo_root) / TRAINING_SPEC_PATH)
    verify_training_spec(archived)
    if archived != result["training_spec"]:
        raise ValueError("T20.17 training specification drifted from live sources")
    return archived


def resolve_model_snapshot(*, cache_root: Path | None = None) -> dict[str, Any]:
    base = cache_root or (Path.home() / ".cache/huggingface/hub/models--lerobot--pi05_base")
    ref = base / "refs/main"
    if not ref.is_file():
        raise FileNotFoundError("Local pi05_base main revision is unavailable")
    revision = ref.read_text(encoding="utf-8").strip()
    if revision != EXPECTED_MODEL_REVISION:
        raise ValueError("Local pi05_base revision drifted")
    snapshot_root = base / "snapshots" / revision
    files = []
    for name in MODEL_FILES:
        alias = snapshot_root / name
        if not alias.is_symlink():
            raise ValueError(f"pi05_base snapshot file is missing or not cache-addressed: {name}")
        target = alias.resolve(strict=True)
        files.append({"path": name, "size_bytes": target.stat().st_size, "sha256": _sha256_file(target)})
    if next(row for row in files if row["path"] == "model.safetensors")["size_bytes"] != 14467165872:
        raise ValueError("pi05_base model byte size drifted")
    return {
        "repo_id": MODEL_REPO_ID,
        "revision": revision,
        "snapshot_mode": "complete_local_content_addressed_cache",
        "files": files,
    }


def _features() -> dict[str, dict[str, Any]]:
    features = {
        key: {"dtype": "image", "shape": (3, 256, 256), "names": ["channel", "height", "width"]}
        for key in IMAGE_KEYS.values()
    }
    features["observation.state"] = {"dtype": "float32", "shape": (6,), "names": list(JOINT_NAMES)}
    features["action"] = {"dtype": "float32", "shape": (6,), "names": list(JOINT_NAMES)}
    return features


def _load_source_episode(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    relative = row.get("relative_path")
    if not isinstance(relative, str) or Path(relative).name != relative:
        raise ValueError("Source episode relative path is unsafe")
    path = root / SOURCE_STORE_ROOT / relative
    if _sha256_file(path) != row["episode_file_sha256"]:
        raise ValueError("Source episode byte hash drifted during dataset conversion")
    return load_strict_json(path)


def _dataset_frame(frame: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    result: dict[str, Any] = {"task": TASK}
    observations = frame.get("observations", {})
    for role in CAMERAS:
        result[IMAGE_KEYS[role]] = _decode_png(observations.get(role), role=role)
    state = observations.get("joint_position_mujoco_rad")
    measured = frame.get("actions", {}).get("measured", {})
    if measured.get("state") != "derived" or measured.get("units") != "radian":
        raise ValueError("Source measured action provenance drifted")
    if measured.get("ordered_joint_names") != list(JOINT_NAMES):
        raise ValueError("Source measured action joint order drifted")
    result["observation.state"] = np.asarray(mujoco_to_lerobot(_finite_six(state, "state")), dtype=np.float32)
    result["action"] = np.asarray(mujoco_to_lerobot(_finite_six(measured.get("values"), "measured action")), dtype=np.float32)
    return result


def _decode_png(value: Any, *, role: str) -> Any:
    import numpy as np
    from PIL import Image
    if not isinstance(value, dict) or value.get("encoding") != "png":
        raise ValueError(f"Source {role} image encoding drifted")
    encoded = value.get("png_base64")
    if not isinstance(encoded, str):
        raise ValueError(f"Source {role} image bytes are missing")
    raw = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(raw).hexdigest() != value.get("image_sha256"):
        raise ValueError(f"Source {role} image hash drifted")
    with Image.open(io.BytesIO(raw)) as image:
        rgb = image.convert("RGB")
        if rgb.size != (256, 256) or value.get("width") != 256 or value.get("height") != 256:
            raise ValueError(f"Source {role} image dimensions drifted")
        return np.asarray(rgb, dtype=np.uint8)


def _dataset_statistics(dataset: Any) -> dict[str, Any]:
    stats = _json_value(dataset.meta.stats)
    required = {"observation.state", "action"}
    if not required.issubset(stats):
        raise ValueError("LeRobot dataset metadata lacks state/action statistics")
    encoded = canonical_json_bytes(stats)
    return {
        "source": "lerobot_dataset_meta_stats",
        "normalization": "QUANTILES",
        "feature_keys": sorted(stats),
        "statistics_sha256": hashlib.sha256(encoded).hexdigest(),
        "identity_sha256": hashlib.sha256(canonical_json_bytes({"stats": stats})).hexdigest(),
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    if hasattr(value, "tolist"):
        return _json_value(value.tolist())
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("LeRobot dataset statistics contain a non-finite value")
        return value
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise ValueError(f"Unsupported LeRobot statistics value: {type(value).__name__}")


def _held_out_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": row["seed"],
        "frame_count": row["frame_count"],
        "relative_path": row["relative_path"],
        "episode_file_sha256": row["episode_file_sha256"],
        "raw_rollout_record_identity_sha256": row["raw_rollout_record_identity_sha256"],
        "included_in_training_dataset": False,
        "included_in_dataset_statistics": False,
    }


def _finite_six(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError(f"Source {label} must contain exactly six values")
    result = [float(item) for item in value]
    if not all(math.isfinite(item) for item in result):
        raise ValueError(f"Source {label} contains a non-finite value")
    return result


def _require_sha(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{label} must be lowercase sha256")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
