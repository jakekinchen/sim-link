"""Thin signed provenance manifests over one actual LeRobotDataset.

This module deliberately owns no frame, segment, window, Parquet, normalization,
or processor format.  It reads the package dataset and records only the
provenance and eligibility facts needed to decide whether a later package-owned
training invocation may consume it.
"""

from __future__ import annotations

import hashlib
import math

from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)


LEROBOT_NATIVE_EPISODE_MANIFEST_SCHEMA_VERSION = (
    "scenesmith.lerobot_native_episode_manifest.v1"
)
_SHA256_HEX = set("0123456789abcdef")
_AUTHORITY_NOT_GRANTED = [
    "simulation_training_ready",
    "simulation_model_load",
    "simulation_model_inference",
    "simulation_optimizer_training",
    "simulation_policy_accepted",
    "physical_transfer_ready",
    "promotion_eligible",
    "physical_actuation",
    "external_compute",
    "brev_compute",
]


def build_lerobot_episode_manifest(
    dataset: Any,
    *,
    dataset_label: str,
    episode_annotations: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Return a signed, content-addressed provenance view of one package dataset.

    ``episode_annotations`` are intentionally supplied by the governance layer:
    LeRobot owns frames and metadata, while SceneSmith owns raw-rollout lineage,
    eligibility, and quarantine decisions. Every actual package episode must
    have exactly one annotation.
    """

    _require_actual_lerobot_dataset(dataset)
    label = _normalize_dataset_label(dataset_label)
    annotations = _normalize_annotations(episode_annotations)
    episode_rows = _actual_episode_rows(dataset)
    actual_indices = [row["episode_index"] for row in episode_rows]
    if set(annotations) != set(actual_indices):
        raise ValueError("Annotations must cover every LeRobot episode exactly once")

    episodes = []
    for row in episode_rows:
        annotation = annotations[row["episode_index"]]
        episodes.append({**row, **annotation})
    episodes.sort(key=lambda row: row["episode_index"])

    metadata = _metadata_tree(Path(dataset.root))
    eligible_count = sum(row["eligible"] for row in episodes)
    payload = {
        "schema_version": LEROBOT_NATIVE_EPISODE_MANIFEST_SCHEMA_VERSION,
        "evidence_mode": "signed_lerobot_dataset_provenance_view",
        "qualification_scope": "simulation_dataset_provenance_and_eligibility_only",
        "dataset": {
            "label": label,
            "repo_id": require_nonblank(dataset.repo_id, label="LeRobot repo_id"),
            "revision": require_nonblank(dataset.revision, label="LeRobot revision"),
            "dataset_class": "lerobot.datasets.lerobot_dataset.LeRobotDataset",
            "total_frames": _positive_int(dataset.meta.total_frames, label="LeRobot total_frames"),
            "total_episodes": _positive_int(
                dataset.meta.total_episodes, label="LeRobot total_episodes"
            ),
            "metadata_tree": metadata,
        },
        "episode_count": len(episodes),
        "eligible_episode_count": eligible_count,
        "quarantined_episode_count": len(episodes) - eligible_count,
        "episodes": episodes,
        "storage_owner": "lerobot_dataset",
        "frames_materialized": False,
        "segments_materialized": False,
        "windows_materialized": False,
        "parallel_parquet_written": False,
        "new_storage_rows_created": 0,
        "normalization_reimplemented": False,
        "processor_executed": False,
        "raw_bytes_rewritten": False,
        "simulation_training_ready": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "local_capabilities": [
            "lerobot_dataset_episode_provenance_bound",
            "lerobot_dataset_episode_eligibility_bound",
            "lerobot_dataset_quarantine_bound",
        ],
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
    }
    return sign_payload(payload)


def verify_lerobot_episode_manifest(
    payload: dict[str, Any],
    dataset: Any,
    *,
    dataset_label: str,
    episode_annotations: Iterable[dict[str, Any]],
) -> None:
    """Rebuild the package-owned view and reject any source or policy drift."""

    if not isinstance(payload, dict):
        raise ValueError("LeRobot episode manifest must be an object")
    if payload.get("schema_version") != LEROBOT_NATIVE_EPISODE_MANIFEST_SCHEMA_VERSION:
        raise ValueError("LeRobot episode manifest schema is unsupported")
    verify_signed_payload(payload, label="LeRobot native episode manifest")
    expected = build_lerobot_episode_manifest(
        dataset,
        dataset_label=dataset_label,
        episode_annotations=episode_annotations,
    )
    if payload != expected:
        raise ValueError("LeRobot episode manifest drifted from dataset or annotations")


def _require_actual_lerobot_dataset(dataset: Any) -> None:
    try:
        from lerobot.datasets import LeRobotDataset
    except ModuleNotFoundError as error:
        raise RuntimeError("Pinned LeRobot runtime is required for this manifest") from error
    if not isinstance(dataset, LeRobotDataset):
        raise TypeError("Manifest requires an actual LeRobotDataset instance")
    if not isinstance(getattr(dataset, "root", None), Path):
        raise ValueError("LeRobot dataset root is unavailable")
    if not dataset.root.is_dir() or dataset.root.is_symlink():
        raise ValueError("LeRobot dataset root is missing or aliased")


def _normalize_dataset_label(value: str) -> str:
    label = require_nonblank(value, label="LeRobot dataset label")
    path = PurePosixPath(label)
    if path.is_absolute() or ".." in path.parts or label != path.as_posix():
        raise ValueError("LeRobot dataset label must be a relative logical path")
    return label


def _normalize_annotations(
    annotations: Iterable[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for value in annotations:
        if not isinstance(value, dict):
            raise ValueError("LeRobot episode annotation must be an object")
        index = _nonnegative_int(value.get("episode_index"), label="episode_index")
        if index in result:
            raise ValueError("LeRobot episode annotations contain a duplicate index")
        raw_identity = _sha256(
            value.get("raw_rollout_identity_sha256"), label="raw rollout identity"
        )
        eligible = value.get("eligible")
        if not isinstance(eligible, bool):
            raise ValueError("LeRobot episode eligibility must be boolean")
        quarantine_reason = value.get("quarantine_reason")
        if eligible:
            if quarantine_reason is not None:
                raise ValueError("Eligible LeRobot episode must not have a quarantine reason")
        else:
            if not isinstance(quarantine_reason, str) or not quarantine_reason.strip():
                raise ValueError("Quarantined LeRobot episode requires a quarantine reason")
            quarantine_reason = quarantine_reason.strip()
        result[index] = {
            "raw_rollout_identity_sha256": raw_identity,
            "eligible": eligible,
            "quarantine_reason": quarantine_reason,
        }
    if not result:
        raise ValueError("LeRobot episode manifest requires at least one annotation")
    return result


def _actual_episode_rows(dataset: Any) -> list[dict[str, Any]]:
    frame_hashes: dict[int, list[str]] = {}
    frame_counts: dict[int, int] = {}
    total_frames = _positive_int(dataset.meta.total_frames, label="LeRobot total_frames")
    if len(dataset) != total_frames:
        raise ValueError("LeRobot dataset length disagrees with metadata")
    for index in range(total_frames):
        frame = dataset[index]
        if not isinstance(frame, dict):
            raise ValueError("LeRobot dataset frame is not an object")
        episode_index = _scalar_int(frame.get("episode_index"), label="LeRobot frame episode_index")
        frame_hashes.setdefault(episode_index, []).append(_frame_hash(frame))
        frame_counts[episode_index] = frame_counts.get(episode_index, 0) + 1
    expected_count = _positive_int(dataset.meta.total_episodes, label="LeRobot total_episodes")
    expected_indices = list(range(expected_count))
    if sorted(frame_hashes) != expected_indices:
        raise ValueError("LeRobot frames do not cover the declared episode indices")
    return [
        {
            "episode_index": index,
            "frame_count": frame_counts[index],
            "episode_content_sha256": hashlib.sha256(
                canonical_json_bytes(
                    {
                        "episode_index": index,
                        "frame_hashes": frame_hashes[index],
                    }
                )
            ).hexdigest(),
        }
        for index in expected_indices
    ]


def _frame_hash(frame: dict[str, Any]) -> str:
    normalized = {key: describe_lerobot_value(value) for key, value in sorted(frame.items())}
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def describe_lerobot_value(value: Any) -> dict[str, Any]:
    """Return a finite, deterministic descriptor for a package-returned value."""

    if value is None:
        return {"kind": "none"}
    if isinstance(value, bool):
        return {"kind": "bool", "value": value}
    if isinstance(value, int):
        return {"kind": "int", "value": value}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("LeRobot frame contains a non-finite float")
        return {"kind": "float", "value": value}
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return {"kind": "utf8", "byte_length": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}
    if isinstance(value, dict):
        return {
            "kind": "mapping",
            "entries": {key: describe_lerobot_value(item) for key, item in sorted(value.items())},
        }
    if isinstance(value, (list, tuple)):
        return {"kind": "sequence", "entries": [describe_lerobot_value(item) for item in value]}
    return _tensor_or_array_descriptor(value)


def _tensor_or_array_descriptor(value: Any) -> dict[str, Any]:
    try:
        import numpy as np
    except ModuleNotFoundError as error:
        raise RuntimeError("NumPy is required to hash LeRobot frames") from error
    if hasattr(value, "detach") and hasattr(value, "cpu"):
        value = value.detach().cpu().contiguous().numpy()
    elif hasattr(value, "numpy") and not isinstance(value, np.ndarray):
        value = value.numpy()
    if not isinstance(value, np.ndarray):
        raise TypeError(f"Unsupported LeRobot frame value type: {type(value)!r}")
    if value.dtype.kind not in {"b", "i", "u", "f"}:
        raise TypeError(f"Unsupported LeRobot frame array dtype: {value.dtype}")
    if value.dtype.kind == "f" and not bool(np.isfinite(value).all()):
        raise ValueError("LeRobot frame contains a non-finite tensor value")
    array = np.ascontiguousarray(value.astype(value.dtype.newbyteorder("<"), copy=False))
    encoded = array.tobytes(order="C")
    return {
        "kind": "tensor_or_array",
        "dtype": array.dtype.str,
        "shape": list(array.shape),
        "byte_length": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _metadata_tree(dataset_root: Path) -> dict[str, Any]:
    metadata_root = dataset_root / "meta"
    if not metadata_root.is_dir() or metadata_root.is_symlink():
        raise ValueError("LeRobot metadata root is missing or aliased")
    entries = []
    for path in sorted(metadata_root.rglob("*")):
        if path.is_symlink():
            raise ValueError("LeRobot metadata contains a symlink")
        if not path.is_file():
            continue
        relative = path.relative_to(dataset_root).as_posix()
        data = path.read_bytes()
        entries.append(
            {
                "path": relative,
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    if not entries:
        raise ValueError("LeRobot metadata contains no regular files")
    return {
        "file_count": len(entries),
        "files": entries,
        "identity_sha256": hashlib.sha256(canonical_json_bytes(entries)).hexdigest(),
    }


def _scalar_int(value: Any, *, label: str) -> int:
    if hasattr(value, "item"):
        value = value.item()
    return _nonnegative_int(value, label=label)


def _positive_int(value: Any, *, label: str) -> int:
    result = _nonnegative_int(value, label=label)
    if result <= 0:
        raise ValueError(f"{label} must be positive")
    return result


def _nonnegative_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(character not in _SHA256_HEX for character in digest):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest
