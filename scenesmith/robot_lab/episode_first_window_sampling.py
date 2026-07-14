"""Deterministic, model-free T18.1 episode-first sampling of valid M17 windows."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.experience_compiler import verify_compilation
from scenesmith.robot_lab.experience_window_index import HORIZONS, verify_window_index
from scenesmith.robot_lab.experience_records import REPO_ROOT


SCHEMA_VERSION = "scenesmith.episode_first_window_sampling.v1"
TASK_ID = "T18.1"
SAMPLING_SEED = 181001
SAMPLING_CYCLE_ID = "t18.1-initial-episode-first-window-sample"
COMPILER_DIR = REPO_ROOT / "configurations/robot_lab/t17_5b_compile"
WINDOW_DIR = REPO_ROOT / "configurations/robot_lab/t17_5b_window_index"
REPLAY_AUDIT_PATH = REPO_ROOT / "configurations/robot_lab/t17_7_compiler_window_replay_audit.json"


def build_episode_first_window_sample() -> dict[str, Any]:
    """Build a signed, source-bound selection without mutating any data buffer."""

    verify_compilation(COMPILER_DIR)
    verify_window_index(WINDOW_DIR, COMPILER_DIR)
    audit = load_strict_json(REPLAY_AUDIT_PATH)
    _verify_replay_audit_binding(audit)

    compiler_manifest_path = COMPILER_DIR / "compiler_manifest.json"
    window_manifest_path = WINDOW_DIR / "window_manifest.json"
    compiler_manifest = load_strict_json(compiler_manifest_path)
    window_manifest = load_strict_json(window_manifest_path)
    frame_rows = pq.read_table(COMPILER_DIR / "frames.parquet").to_pylist()
    segment_rows = pq.read_table(COMPILER_DIR / "segments.parquet").to_pylist()
    window_rows = pq.read_table(WINDOW_DIR / "window_index.parquet").to_pylist()
    frames = _unique_map(frame_rows, "frame_id", label="compiler frame")
    segments = _unique_map(segment_rows, "segment_id", label="compiler segment")
    descriptors = [
        _describe_window(row, frames=frames, segments=segments, compiler_manifest=compiler_manifest)
        for row in window_rows
    ]
    if len(descriptors) != window_manifest.get("window_count"):
        raise ValueError("Source window count drifted")
    selected, bucket_summary = select_episode_first(descriptors)
    source_rollouts = sorted({descriptor["rollout_id"] for descriptor in descriptors})
    selected_ids = [item["window_id"] for item in selected]
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("Episode-first selection duplicated a window")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "sampling_scope": "verified_m17_window_index_episode_first_selection_only",
        "sampling_seed": SAMPLING_SEED,
        "selection_algorithm": "per_bucket_per_rollout_sha256_rank_v1",
        "sampling_cycle": {
            "cycle_id": SAMPLING_CYCLE_ID,
            "cycle_ordinal": 1,
            "buffer_persisted": False,
            "buffer_owner": "T18.2_not_started",
        },
        "source_compiler_manifest_path": _repo_relative(compiler_manifest_path),
        "source_compiler_manifest_file_sha256": _sha256_file(compiler_manifest_path),
        "source_window_manifest_path": _repo_relative(window_manifest_path),
        "source_window_manifest_file_sha256": _sha256_file(window_manifest_path),
        "source_window_index_path": _repo_relative(WINDOW_DIR / "window_index.parquet"),
        "source_window_index_file_sha256": _sha256_file(WINDOW_DIR / "window_index.parquet"),
        "source_replay_audit_path": _repo_relative(REPLAY_AUDIT_PATH),
        "source_replay_audit_file_sha256": _sha256_file(REPLAY_AUDIT_PATH),
        "source_replay_audit_identity_sha256": audit["identity_sha256"],
        "source_window_count": len(descriptors),
        "source_episode_count": len(source_rollouts),
        "source_rollout_ids_sha256": _sha256(source_rollouts),
        "configured_bucket_count": len(bucket_summary),
        "realized_bucket_count": len(bucket_summary),
        "configured_window_count": len(bucket_summary) * len(source_rollouts),
        "realized_window_count": len(selected),
        "unique_window_count": len(set(selected_ids)),
        "unique_window_ratio": len(set(selected_ids)) / len(selected),
        "bucket_summary": bucket_summary,
        "selected_window_ids_sha256": _sha256(selected_ids),
        "selected_windows": selected,
        "model_loaded": False,
        "model_inference_executed": False,
        "optimizer_training": False,
        "training_eligible": False,
        "simulation_training_ready": False,
        "physical_actuation": False,
        "raw_bytes_rewritten": False,
        "buffer_mutated": False,
        "external_compute_started": False,
    }
    return sign_payload(payload)


def verify_episode_first_window_sample(manifest: dict[str, Any]) -> None:
    """Fail closed on source, selection, authority, or deterministic-output drift."""

    verify_signed_payload(manifest, label="episode-first window sample")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("task_id") != TASK_ID:
        raise ValueError("Episode-first sample schema or task identity drifted")
    if manifest.get("sampling_seed") != SAMPLING_SEED:
        raise ValueError("Episode-first sampling seed drifted")
    if manifest.get("sampling_cycle", {}).get("cycle_id") != SAMPLING_CYCLE_ID:
        raise ValueError("Episode-first sampling cycle drifted")
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
        if manifest.get(field) is not False:
            raise ValueError(f"Episode-first sample authority flag drifted: {field}")
    selected = manifest.get("selected_windows")
    if not isinstance(selected, list) or not selected:
        raise ValueError("Episode-first selected windows are absent")
    selected_ids = [item.get("window_id") for item in selected if isinstance(item, dict)]
    if len(selected_ids) != len(selected) or len(selected_ids) != len(set(selected_ids)):
        raise ValueError("Episode-first selected-window uniqueness drifted")
    if manifest.get("unique_window_ratio") != 1.0:
        raise ValueError("Episode-first sample is not fully unique")
    expected = build_episode_first_window_sample()
    if canonical_json_bytes(manifest) != canonical_json_bytes(expected):
        raise ValueError("Episode-first sample drifted from verified sources")


def select_episode_first(
    descriptors: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select one hash-ranked valid window per source episode in each bucket."""

    if not isinstance(descriptors, list) or not descriptors:
        raise ValueError("Window descriptors are required")
    seen_ids: set[str] = set()
    all_rollouts: set[str] = set()
    buckets: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for descriptor in descriptors:
        if not isinstance(descriptor, dict):
            raise ValueError("Window descriptor must be an object")
        window_id = _require_sha256(descriptor.get("window_id"), label="window ID")
        if window_id in seen_ids:
            raise ValueError("Source descriptors contain a duplicate window ID")
        seen_ids.add(window_id)
        rollout_id = _require_text(descriptor.get("rollout_id"), label="window rollout ID")
        all_rollouts.add(rollout_id)
        bucket = _bucket_key(descriptor)
        buckets[bucket].append(descriptor)
    if not all_rollouts:
        raise ValueError("Source descriptors have no episodes")

    selected: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for bucket in sorted(buckets):
        rows = buckets[bucket]
        per_rollout: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            per_rollout[row["rollout_id"]].append(row)
        missing = sorted(all_rollouts - set(per_rollout))
        if missing:
            raise ValueError(f"Episode-first bucket lacks realized episodes: {missing}")
        chosen: list[dict[str, Any]] = []
        for rollout_id in sorted(all_rollouts):
            candidates = per_rollout[rollout_id]
            if not candidates:
                raise ValueError("Episode-first bucket has an empty episode candidate set")
            chosen.append(min(candidates, key=lambda row: _selection_key(row)))
        if len({row["window_id"] for row in chosen}) != len(chosen):
            raise ValueError("Episode-first bucket duplicated a selected window")
        selected_ids = [row["window_id"] for row in chosen]
        source_class, task_phase, control_mode, horizon = bucket
        summaries.append(
            {
                "source_class": source_class,
                "task_phase": task_phase,
                "control_mode": control_mode,
                "horizon": horizon,
                "available_window_count": len(rows),
                "configured_episode_count": len(all_rollouts),
                "realized_episode_count": len(chosen),
                "selected_window_count": len(chosen),
                "selected_window_ids_sha256": _sha256(selected_ids),
                "rollout_ids_sha256": _sha256(sorted(all_rollouts)),
            }
        )
        for rank, row in enumerate(chosen, start=1):
            selected.append(
                {
                    "window_id": row["window_id"],
                    "selection_rank_within_bucket": rank,
                    "source_class": source_class,
                    "task_phase": task_phase,
                    "control_mode": control_mode,
                    "horizon": horizon,
                    "rollout_id": row["rollout_id"],
                    "segment_id": row["segment_id"],
                    "frame_ids_sha256": row["frame_ids_sha256"],
                    "source_window_index_sha256": row["source_window_index_sha256"],
                }
            )
    if len({row["window_id"] for row in selected}) != len(selected):
        raise ValueError("Episode-first selection duplicated a window across buckets")
    return selected, summaries


def _describe_window(
    window: dict[str, Any],
    *,
    frames: dict[str, dict[str, Any]],
    segments: dict[str, dict[str, Any]],
    compiler_manifest: dict[str, Any],
) -> dict[str, Any]:
    window_id = _require_sha256(window.get("window_id"), label="window ID")
    horizon = _require_int(window.get("horizon"), label="window horizon")
    if horizon not in HORIZONS or window.get("window_frame_count") != horizon:
        raise ValueError("Window horizon or frame count is invalid")
    frame_ids = _parse_string_list(window.get("frame_ids_json"), label="window frame IDs")
    action_ids = _parse_string_list(window.get("action_frame_ids_json"), label="window action frame IDs")
    if len(frame_ids) != horizon or action_ids != frame_ids:
        raise ValueError("Window action sequence drifted")
    if len(frame_ids) != len(set(frame_ids)):
        raise ValueError("Window repeats a source frame")
    segment_id = _require_text(window.get("segment_id"), label="window segment ID")
    segment = segments.get(segment_id)
    if segment is None:
        raise ValueError("Window references an absent source segment")
    if window.get("rollout_id") != segment.get("rollout_id"):
        raise ValueError("Window rollout identity drifted from segment")
    if window.get("raw_rollout_record_identity_sha256") != segment.get(
        "raw_rollout_record_identity_sha256"
    ):
        raise ValueError("Window raw rollout identity drifted from segment")
    if window.get("source_compiler_manifest_sha256") != _sha256_file(
        COMPILER_DIR / "compiler_manifest.json"
    ):
        raise ValueError("Window compiler source hash drifted")

    source_class: str | None = None
    control_mode: str | None = None
    task_phases: set[str] = set()
    prior_index: int | None = None
    prior_timestamp: int | None = None
    for position, frame_id in enumerate(frame_ids):
        frame = frames.get(frame_id)
        if frame is None:
            raise ValueError("Window references an absent compiler frame")
        if frame.get("frame_eligible") is not True or frame.get("action_variants_complete") is not True:
            raise ValueError("Window contains an invalid compiler frame")
        if _parse_json(frame.get("quarantine_reason_codes_json"), label="frame quarantine") != []:
            raise ValueError("Window contains a quarantined compiler frame")
        if frame.get("rollout_id") != window.get("rollout_id"):
            raise ValueError("Window frame rollout identity drifted")
        if frame.get("raw_rollout_record_identity_sha256") != window.get(
            "raw_rollout_record_identity_sha256"
        ):
            raise ValueError("Window frame raw rollout identity drifted")
        current_source_class = _require_text(frame.get("source_class"), label="frame source class")
        current_control_mode = _require_text(frame.get("control_mode"), label="frame control mode")
        source_class = source_class or current_source_class
        control_mode = control_mode or current_control_mode
        if source_class != current_source_class or control_mode != current_control_mode:
            raise ValueError("Window spans source class or control mode")
        task_phases.add(_require_text(frame.get("task_phase"), label="frame task phase"))
        index = _require_int(frame.get("frame_index"), label="frame index")
        timestamp = _require_int(frame.get("timestamp_ns"), label="frame timestamp")
        if prior_index is not None and index != prior_index + 1:
            raise ValueError("Window frame indices are not contiguous")
        if prior_timestamp is not None:
            if timestamp <= prior_timestamp or timestamp - prior_timestamp > compiler_manifest.get(
                "max_timestamp_gap_ns"
            ):
                raise ValueError("Window timestamps are invalid")
        events = _parse_string_list(frame.get("boundary_events_json"), label="frame boundary events")
        if 0 < position < len(frame_ids) - 1 and events:
            raise ValueError("Window crosses an internal hard boundary")
        prior_index = index
        prior_timestamp = timestamp
    if len(task_phases) != 1:
        raise ValueError("Window spans task phases")
    task_phase = next(iter(task_phases))
    return {
        "window_id": window_id,
        "rollout_id": window["rollout_id"],
        "segment_id": segment_id,
        "source_class": source_class,
        "task_phase": task_phase,
        "control_mode": control_mode,
        "horizon": horizon,
        "frame_ids_sha256": _sha256(frame_ids),
        "source_window_index_sha256": _sha256_file(WINDOW_DIR / "window_index.parquet"),
    }


def _verify_replay_audit_binding(audit: dict[str, Any]) -> None:
    verify_signed_payload(audit, label="T17.7 replay audit")
    if audit.get("schema_version") != "scenesmith.compiler_window_replay_audit.v1":
        raise ValueError("T17.7 replay audit schema drifted")
    for field in (
        "model_loaded",
        "model_inference_executed",
        "optimizer_training",
        "training_eligible",
        "simulation_training_ready",
        "physical_actuation",
        "raw_bytes_rewritten",
        "external_compute_started",
    ):
        if audit.get(field) is not False:
            raise ValueError(f"T17.7 replay audit authority flag drifted: {field}")
    if audit.get("source_window_index_file_sha256") != _sha256_file(
        WINDOW_DIR / "window_index.parquet"
    ):
        raise ValueError("T17.7 replay audit window-index binding drifted")
    if audit.get("source_compiler_manifest_file_sha256") != _sha256_file(
        COMPILER_DIR / "compiler_manifest.json"
    ):
        raise ValueError("T17.7 replay audit compiler binding drifted")


def _bucket_key(descriptor: dict[str, Any]) -> tuple[str, str, str, int]:
    return (
        _require_text(descriptor.get("source_class"), label="source class"),
        _require_text(descriptor.get("task_phase"), label="task phase"),
        _require_text(descriptor.get("control_mode"), label="control mode"),
        _require_int(descriptor.get("horizon"), label="horizon"),
    )


def _selection_key(descriptor: dict[str, Any]) -> tuple[str, str]:
    window_id = _require_sha256(descriptor.get("window_id"), label="window ID")
    return (
        _sha256(
            {
                "domain": "t18.1/episode-first-window-selection/v1",
                "sampling_seed": SAMPLING_SEED,
                "source_class": descriptor["source_class"],
                "task_phase": descriptor["task_phase"],
                "control_mode": descriptor["control_mode"],
                "horizon": descriptor["horizon"],
                "rollout_id": descriptor["rollout_id"],
                "window_id": window_id,
            }
        ),
        window_id,
    )


def _unique_map(rows: list[dict[str, Any]], key: str, *, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = _require_text(row.get(key), label=f"{label} {key}")
        if value in result:
            raise ValueError(f"Duplicate {label} {key}")
        result[value] = row
    return result


def _parse_json(value: Any, *, label: str) -> Any:
    if not isinstance(value, str):
        raise ValueError(f"{label} is not canonical JSON text")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} is not valid JSON") from error
    if canonical_json_bytes(parsed).decode("utf-8") != value:
        raise ValueError(f"{label} is not canonical JSON")
    return parsed


def _parse_string_list(value: Any, *, label: str) -> list[str]:
    parsed = _parse_json(value, label=label)
    if not isinstance(parsed, list) or any(not isinstance(item, str) for item in parsed):
        raise ValueError(f"{label} must be a list of strings")
    return parsed


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError as error:
        raise ValueError("T18.1 source must remain inside this checkout") from error


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be nonblank text")
    return value


def _require_sha256(value: Any, *, label: str) -> str:
    text = _require_text(value, label=label)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return text


def _require_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value
