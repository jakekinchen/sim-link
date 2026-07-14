"""Append-only logical T18.2 source/cycle buffer registry.

The registry stores immutable window IDs and source bindings only. It neither
materializes a dataset nor grants any training authority.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.experience_records import REPO_ROOT


SCHEMA_VERSION = "scenesmith.logical_source_cycle_buffers.v1"
TASK_ID = "T18.2"
INITIAL_CYCLE_ID = "0001"
SELECTION_PATH = REPO_ROOT / "configurations/robot_lab/t18_1_episode_first_window_sample.json"
WINDOW_INDEX_PATH = REPO_ROOT / "configurations/robot_lab/t17_5b_window_index/window_index.parquet"


def build_initial_buffer_registry() -> dict[str, Any]:
    """Freeze the exact T18.1 ordered selection as immutable logical cycle 0001."""

    selection = load_strict_json(SELECTION_PATH)
    selected_ids = _validate_selection(selection)
    source_ids = _source_window_ids()
    if not set(selected_ids).issubset(source_ids):
        raise ValueError("T18.1 selection includes an absent source window ID")
    cycle = _cycle_record(INITIAL_CYCLE_ID, selected_ids, selection)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "registry_scope": "logical_window_id_cycles_not_materialized_dataset_buffers",
        "source_selection_path": _repo_relative(SELECTION_PATH),
        "source_selection_file_sha256": _sha256_file(SELECTION_PATH),
        "source_selection_identity_sha256": selection["identity_sha256"],
        "source_window_index_path": _repo_relative(WINDOW_INDEX_PATH),
        "source_window_index_file_sha256": _sha256_file(WINDOW_INDEX_PATH),
        "cycles": [cycle],
        "configured_cycle_count": 1,
        "realized_cycle_count": 1,
        "configured_window_count": len(selected_ids),
        "realized_window_count": len(selected_ids),
        "cumulative_unique_window_count": len(selected_ids),
        "cumulative_unique_window_ratio": 1.0,
        "buffer_materialized": False,
        "buffer_mutated": False,
        "model_loaded": False,
        "model_inference_executed": False,
        "optimizer_training": False,
        "training_eligible": False,
        "simulation_training_ready": False,
        "physical_actuation": False,
        "raw_bytes_rewritten": False,
        "external_compute_started": False,
    }
    return sign_payload(payload)


def verify_initial_buffer_registry(registry: dict[str, Any]) -> None:
    """Verify the signed initial registry against the exact current T18.1 source."""

    _verify_registry_structure(registry)
    expected = build_initial_buffer_registry()
    if canonical_json_bytes(registry) != canonical_json_bytes(expected):
        raise ValueError("Initial logical buffer registry drifted from T18.1 selection")


def append_logical_cycle(registry: dict[str, Any], cycle_id: str, window_ids: list[str]) -> dict[str, Any]:
    """Return a signed additive registry, rejecting prior mutation and ID reuse."""

    _verify_registry_structure(registry)
    expected_initial = build_initial_buffer_registry()["cycles"][0]
    cycles = registry["cycles"]
    if cycles[0] != expected_initial:
        raise ValueError("Existing initial cycle was mutated")
    cycle_id = _require_cycle_id(cycle_id)
    existing_ids = {cycle["cycle_id"] for cycle in cycles}
    if cycle_id in existing_ids or cycle_id <= cycles[-1]["cycle_id"]:
        raise ValueError("New logical cycle ID is not strictly append-only")
    ids = _validate_ids(window_ids, label="new logical cycle window IDs")
    if not set(ids).issubset(_source_window_ids()):
        raise ValueError("New logical cycle includes an absent source window ID")
    used = {item for cycle in cycles for item in cycle["window_ids"]}
    if used.intersection(ids):
        raise ValueError("New logical cycle reuses an existing window ID")
    selection = load_strict_json(SELECTION_PATH)
    new_cycle = _cycle_record(cycle_id, ids, selection)
    payload = {key: value for key, value in registry.items() if key != "identity_sha256"}
    payload["cycles"] = [*deepcopy(cycles), new_cycle]
    all_ids = [item for cycle in payload["cycles"] for item in cycle["window_ids"]]
    payload["configured_cycle_count"] = len(payload["cycles"])
    payload["realized_cycle_count"] = len(payload["cycles"])
    payload["configured_window_count"] = len(all_ids)
    payload["realized_window_count"] = len(all_ids)
    payload["cumulative_unique_window_count"] = len(set(all_ids))
    payload["cumulative_unique_window_ratio"] = len(set(all_ids)) / len(all_ids)
    return sign_payload(payload)


def _verify_registry_structure(registry: dict[str, Any]) -> None:
    verify_signed_payload(registry, label="logical source-cycle registry")
    if registry.get("schema_version") != SCHEMA_VERSION or registry.get("task_id") != TASK_ID:
        raise ValueError("Logical registry schema or task identity drifted")
    for field in (
        "buffer_materialized",
        "buffer_mutated",
        "model_loaded",
        "model_inference_executed",
        "optimizer_training",
        "training_eligible",
        "simulation_training_ready",
        "physical_actuation",
        "raw_bytes_rewritten",
        "external_compute_started",
    ):
        if registry.get(field) is not False:
            raise ValueError(f"Logical registry authority flag drifted: {field}")
    cycles = registry.get("cycles")
    if not isinstance(cycles, list) or not cycles:
        raise ValueError("Logical registry cycles are absent")
    prior = ""
    ids: list[str] = []
    for cycle in cycles:
        if not isinstance(cycle, dict):
            raise ValueError("Logical registry cycle is invalid")
        cycle_id = _require_cycle_id(cycle.get("cycle_id"))
        if cycle_id <= prior:
            raise ValueError("Logical registry cycles are not strictly ordered")
        prior = cycle_id
        cycle_ids = _validate_ids(cycle.get("window_ids"), label=f"cycle {cycle_id} window IDs")
        if cycle.get("window_ids_sha256") != _sha256(cycle_ids):
            raise ValueError("Logical registry cycle ID digest drifted")
        if cycle.get("immutable") is not True:
            raise ValueError("Logical registry cycle immutability drifted")
        ids.extend(cycle_ids)
    if len(ids) != len(set(ids)):
        raise ValueError("Logical registry reuses a window ID across cycles")
    if registry.get("realized_window_count") != len(ids):
        raise ValueError("Logical registry window count drifted")
    if registry.get("cumulative_unique_window_ratio") != 1.0:
        raise ValueError("Logical registry is not unique")


def _validate_selection(selection: dict[str, Any]) -> list[str]:
    verify_signed_payload(selection, label="T18.1 selection")
    if selection.get("schema_version") != "scenesmith.episode_first_window_sampling.v1":
        raise ValueError("T18.1 selection schema drifted")
    for field in (
        "model_loaded",
        "model_inference_executed",
        "optimizer_training",
        "training_eligible",
        "simulation_training_ready",
        "physical_actuation",
        "raw_bytes_rewritten",
        "buffer_mutated",
        "external_compute_started",
    ):
        if selection.get(field) is not False:
            raise ValueError(f"T18.1 selection authority flag drifted: {field}")
    if selection.get("source_window_index_file_sha256") != _sha256_file(WINDOW_INDEX_PATH):
        raise ValueError("T18.1 selection window-index binding drifted")
    rows = selection.get("selected_windows")
    if not isinstance(rows, list):
        raise ValueError("T18.1 selected windows are absent")
    ids = _validate_ids([row.get("window_id") if isinstance(row, dict) else None for row in rows], label="T18.1 selected window IDs")
    if selection.get("selected_window_ids_sha256") != _sha256(ids):
        raise ValueError("T18.1 selected-window digest drifted")
    return ids


def _cycle_record(cycle_id: str, window_ids: list[str], selection: dict[str, Any]) -> dict[str, Any]:
    return {
        "cycle_id": _require_cycle_id(cycle_id),
        "immutable": True,
        "source_selection_identity_sha256": selection["identity_sha256"],
        "source_selection_window_ids_sha256": selection["selected_window_ids_sha256"],
        "window_count": len(window_ids),
        "window_ids_sha256": _sha256(window_ids),
        "window_ids": window_ids,
    }


def _source_window_ids() -> set[str]:
    rows = pq.read_table(WINDOW_INDEX_PATH, columns=["window_id"]).to_pylist()
    return set(_validate_ids([row.get("window_id") for row in rows], label="source window IDs"))


def _validate_ids(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} are required")
    ids = [_require_sha256(item, label=label) for item in value]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} contain duplicates")
    return ids


def _require_cycle_id(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 4 or not value.isdigit():
        raise ValueError("Logical cycle ID must be four decimal digits")
    return value


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError as error:
        raise ValueError("Logical registry source must remain inside this checkout") from error


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return value
