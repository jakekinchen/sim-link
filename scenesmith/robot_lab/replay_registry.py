"""Content-addressed bounded registry of accepted PI0.5 correction datasets."""

from __future__ import annotations

import hashlib
import json

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.pi05_dataset_contract import (
    DATASET_CONTRACT_FILENAME,
    load_dataset_contract,
)


REGISTRY_SCHEMA_VERSION = "scenesmith.pi05_replay_registry.v1"
SIDECAR_FILENAME = "scenesmith_intervention_sidecar.jsonl"


def register_correction_dataset(
    registry_path: Path,
    dataset_root: Path,
    *,
    cycle_id: str,
    max_sources: int,
    max_frames: int,
) -> dict[str, Any]:
    if max_sources <= 0 or max_frames <= 0:
        raise ValueError("Replay registry bounds must be positive")
    registry = load_replay_registry(registry_path) if registry_path.is_file() else {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "revision": 0,
        "entries": [],
    }
    validate_replay_registry(registry)
    entry = _dataset_entry(dataset_root, cycle_id=cycle_id, sequence=int(registry["revision"]) + 1)
    entries = [item for item in registry["entries"] if item["root"] != entry["root"]]
    entries.append(entry)
    entries.sort(key=lambda item: int(item["sequence"]), reverse=True)
    retained: list[dict[str, Any]] = []
    retained_frames = 0
    for item in entries:
        frames = int(item["total_frames"])
        if retained and (len(retained) >= max_sources or retained_frames + frames > max_frames):
            continue
        if not retained and frames > max_frames:
            raise ValueError("Newest correction dataset exceeds replay frame budget")
        retained.append(item)
        retained_frames += frames
    retained.sort(key=lambda item: int(item["sequence"]))
    updated = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "revision": int(registry["revision"]) + 1,
        "bounds": {"max_sources": max_sources, "max_frames": max_frames},
        "retained_frames": retained_frames,
        "entries": retained,
    }
    validate_replay_registry(updated, verify_files=True)
    return updated


def load_replay_registry(path: Path, *, verify_files: bool = True) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected replay registry object: {path}")
    validate_replay_registry(payload, verify_files=verify_files)
    return payload


def write_replay_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_replay_registry(registry: dict[str, Any], *, verify_files: bool = False) -> None:
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError("Unsupported PI0.5 replay registry")
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Replay registry entries must be a list")
    roots = [str(entry.get("root")) for entry in entries]
    if len(roots) != len(set(roots)):
        raise ValueError("Replay registry contains duplicate roots")
    bounds = registry.get("bounds")
    if bounds:
        if len(entries) > int(bounds["max_sources"]):
            raise ValueError("Replay registry exceeds source bound")
        if sum(int(entry["total_frames"]) for entry in entries) > int(bounds["max_frames"]):
            raise ValueError("Replay registry exceeds frame bound")
    if verify_files:
        seen_frame_keys: set[tuple[str, int, int]] = set()
        for entry in entries:
            root = Path(entry["root"])
            expected = _dataset_entry(
                root,
                cycle_id=str(entry["cycle_id"]),
                sequence=int(entry["sequence"]),
            )
            for key in ("contract_sha256", "sidecar_sha256", "info_sha256", "total_frames"):
                if entry.get(key) != expected.get(key):
                    raise ValueError(f"Registered correction dataset mutated for {key}: {root}")
            frame_keys = _sidecar_frame_keys(root / SIDECAR_FILENAME)
            overlap = seen_frame_keys.intersection(frame_keys)
            if overlap:
                raise ValueError(f"Replay registry contains overlapping correction frames: {root}")
            seen_frame_keys.update(frame_keys)


def _dataset_entry(dataset_root: Path, *, cycle_id: str, sequence: int) -> dict[str, Any]:
    contract = load_dataset_contract(dataset_root)
    sidecar = dataset_root / SIDECAR_FILENAME
    info = dataset_root / "meta" / "info.json"
    if not sidecar.is_file() or not info.is_file():
        raise FileNotFoundError(f"Correction dataset lacks sidecar or info: {dataset_root}")
    return {
        "root": str(dataset_root),
        "cycle_id": cycle_id,
        "sequence": sequence,
        "total_frames": int(contract["total_frames"]),
        "contract_sha256": _sha256(dataset_root / DATASET_CONTRACT_FILENAME),
        "sidecar_sha256": _sha256(sidecar),
        "info_sha256": _sha256(info),
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sidecar_frame_keys(path: Path) -> set[tuple[str, int, int]]:
    keys: set[tuple[str, int, int]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if {"scene_id", "seed", "frame_index"}.issubset(row):
            keys.add((str(row["scene_id"]), int(row["seed"]), int(row["frame_index"])))
    return keys
