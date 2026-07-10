"""Machine-readable PI0.5 dataset contracts for safe incremental training."""

from __future__ import annotations

import hashlib
import json

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.so101_coordinates import coordinate_contract


DATASET_CONTRACT_FILENAME = "scenesmith_pi05_dataset_contract.json"
DATASET_CONTRACT_SCHEMA_VERSION = "scenesmith.pi05_dataset_contract.v1"
EXACT_TASK_CONDITIONING = {
    "frame_exact_task_mixture",
    "frame_policy_task",
    "frame_stage_task",
}


def build_dataset_contract(
    dataset_root: Path,
    *,
    task_conditioning: str,
    temporal_segmentation: str = "contiguous_source_frames",
) -> dict[str, Any]:
    info_path = dataset_root / "meta" / "info.json"
    stats_path = dataset_root / "meta" / "stats.json"
    info = _read_json(info_path)
    if not stats_path.is_file():
        raise FileNotFoundError(f"Missing LeRobot statistics: {stats_path}")
    if task_conditioning not in EXACT_TASK_CONDITIONING | {"episode_task"}:
        raise ValueError(f"Unsupported PI0.5 task conditioning: {task_conditioning}")
    if temporal_segmentation != "contiguous_source_frames":
        raise ValueError("PI0.5 datasets must preserve contiguous source frames")
    return {
        "schema_version": DATASET_CONTRACT_SCHEMA_VERSION,
        "dataset_root": str(dataset_root),
        "fps": int(info["fps"]),
        "total_episodes": int(info["total_episodes"]),
        "total_frames": int(info["total_frames"]),
        "coordinate_contract": coordinate_contract(),
        "action_representation": "absolute_joint_degrees_plus_gripper_percent",
        "task_conditioning": task_conditioning,
        "temporal_segmentation": temporal_segmentation,
        "info_sha256": _sha256(info_path),
        "native_stats_sha256": _sha256(stats_path),
    }


def write_dataset_contract(
    dataset_root: Path,
    *,
    task_conditioning: str,
    temporal_segmentation: str = "contiguous_source_frames",
) -> dict[str, Any]:
    contract = build_dataset_contract(
        dataset_root,
        task_conditioning=task_conditioning,
        temporal_segmentation=temporal_segmentation,
    )
    path = dataset_root / DATASET_CONTRACT_FILENAME
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
    return contract


def load_dataset_contract(dataset_root: Path) -> dict[str, Any]:
    path = dataset_root / DATASET_CONTRACT_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"Missing PI0.5 dataset contract: {path}")
    contract = _read_json(path)
    if contract.get("schema_version") != DATASET_CONTRACT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported PI0.5 dataset contract: {path}")
    return contract


def validate_merge_contracts(base: dict[str, Any], corrections: dict[str, Any]) -> None:
    for label, contract in (("base", base), ("correction", corrections)):
        if contract.get("task_conditioning") not in EXACT_TASK_CONDITIONING:
            raise ValueError(f"{label} dataset lacks exact frame-level task conditioning")
        if contract.get("temporal_segmentation") != "contiguous_source_frames":
            raise ValueError(f"{label} dataset lacks contiguous temporal segmentation")
    for key in ("coordinate_contract", "action_representation", "fps"):
        if base.get(key) != corrections.get(key):
            raise ValueError(f"Base and correction dataset contracts differ for {key}")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
