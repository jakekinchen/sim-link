"""Source-bound, unpadded T17.5 action-window index compilation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.experience_compiler import (
    FRAME_SCHEMA,
    SCHEMA_VERSION as EXPERIENCE_COMPILER_SCHEMA_VERSION,
    SEGMENT_SCHEMA,
    verify_compilation,
)
from scenesmith.robot_lab.experience_records import ACTION_VARIANTS, JOINT_NAMES


SCHEMA_VERSION = "scenesmith.experience_window_index.v1"
HORIZONS = (5, 10, 15, 50)
OUTPUT_NAMES = ("window_index.parquet", "window_manifest.json")

WINDOW_SCHEMA = pa.schema(
    [
        ("window_id", pa.string()),
        ("segment_id", pa.string()),
        ("rollout_id", pa.string()),
        ("horizon", pa.int64()),
        ("window_frame_count", pa.int64()),
        ("start_frame_id", pa.string()),
        ("end_frame_id", pa.string()),
        ("start_frame_index", pa.int64()),
        ("end_frame_index", pa.int64()),
        ("start_timestamp_ns", pa.int64()),
        ("end_timestamp_ns", pa.int64()),
        ("frame_ids_json", pa.string()),
        ("action_frame_ids_json", pa.string()),
        ("action_variants_json", pa.string()),
        ("raw_rollout_record_identity_sha256", pa.string()),
        ("source_experience_identity_sha256", pa.string()),
        ("source_normalization_identity_sha256", pa.string()),
        ("source_compiler_manifest_sha256", pa.string()),
    ]
)


def compile_window_index(source_dir: Path) -> dict[str, Any]:
    """Build valid windows from one verified T17.4 compiler output directory."""

    source_dir = Path(source_dir)
    verify_compilation(source_dir)
    source_manifest_path = source_dir / "compiler_manifest.json"
    source_manifest = load_strict_json(source_manifest_path)
    if source_manifest.get("schema_version") != EXPERIENCE_COMPILER_SCHEMA_VERSION:
        raise ValueError("Source compiler schema version drifted")
    _require_closed_authority(source_manifest, label="Source compiler manifest")

    frame_table = pq.read_table(source_dir / "frames.parquet")
    segment_table = pq.read_table(source_dir / "segments.parquet")
    if frame_table.schema != FRAME_SCHEMA or segment_table.schema != SEGMENT_SCHEMA:
        raise ValueError("Source compiler parquet schema drifted")
    frame_rows = frame_table.to_pylist()
    segment_rows = segment_table.to_pylist()
    if len(frame_rows) != source_manifest.get("frame_count"):
        raise ValueError("Source compiler frame count drifted")
    if len(segment_rows) != source_manifest.get("segment_count"):
        raise ValueError("Source compiler segment count drifted")

    source_manifest_sha256 = _sha256_file(source_manifest_path)
    return _compile_rows(
        frame_rows,
        segment_rows,
        source_manifest=source_manifest,
        source_manifest_sha256=source_manifest_sha256,
    )


def write_window_index(result: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Write a deterministic Parquet index and canonical manifest."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    window_path = output_dir / "window_index.parquet"
    manifest_path = output_dir / "window_manifest.json"
    pq.write_table(
        pa.Table.from_pylist(result["window_rows"], schema=WINDOW_SCHEMA),
        window_path,
        compression="NONE",
        use_dictionary=False,
        write_statistics=False,
        version="2.6",
    )
    manifest = dict(result["manifest"])
    manifest["output_sha256"] = {"window_index.parquet": _sha256_file(window_path)}
    dump_canonical_json(manifest_path, manifest)
    return {"manifest": manifest, "window_rows": result["window_rows"]}


def verify_window_index(output_dir: Path, source_dir: Path) -> None:
    """Replay the compiler and reject output or source-binding drift."""

    output_dir = Path(output_dir)
    source_dir = Path(source_dir)
    manifest_path = output_dir / "window_manifest.json"
    window_path = output_dir / "window_index.parquet"
    if not manifest_path.is_file() or not window_path.is_file():
        raise ValueError("Window-index outputs are incomplete")

    actual_manifest = load_strict_json(manifest_path)
    if actual_manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Window-index schema version drifted")
    _require_closed_authority(actual_manifest, label="Window-index manifest")
    if actual_manifest.get("output_sha256", {}).get("window_index.parquet") != _sha256_file(window_path):
        raise ValueError("Window-index output hash drifted")
    window_table = pq.read_table(window_path)
    if window_table.schema != WINDOW_SCHEMA:
        raise ValueError("Window-index parquet schema drifted")

    expected = compile_window_index(source_dir)
    expected_manifest = expected["manifest"]
    actual_without_output = dict(actual_manifest)
    actual_without_output.pop("output_sha256", None)
    if actual_without_output != expected_manifest:
        raise ValueError("Window-index manifest drifted from source compiler output")
    rows = window_table.to_pylist()
    if rows != expected["window_rows"]:
        raise ValueError("Window-index rows drifted from source compiler output")
    if len(rows) != actual_manifest.get("window_count"):
        raise ValueError("Window-index count drifted")


def _compile_rows(
    frame_rows: list[dict[str, Any]],
    segment_rows: list[dict[str, Any]],
    *,
    source_manifest: dict[str, Any],
    source_manifest_sha256: str,
) -> dict[str, Any]:
    source_experience_identity = _require_sha256(
        source_manifest.get("source_experience_identity_sha256"),
        label="Source experience identity",
    )
    source_normalization_identity = _require_sha256(
        source_manifest.get("source_normalization_identity_sha256"),
        label="Source normalization identity",
    )
    max_timestamp_gap_ns = _require_positive_int(
        source_manifest.get("max_timestamp_gap_ns"), label="Source maximum timestamp gap"
    )
    _validate_frame_uniqueness(frame_rows)

    ordered_segments = sorted(
        segment_rows,
        key=lambda row: (
            _require_text(row.get("rollout_id"), label="Segment rollout ID"),
            _require_int(row.get("start_frame_index"), label="Segment start frame index"),
            _require_text(row.get("segment_id"), label="Segment ID"),
        ),
    )
    seen_segment_ids: set[str] = set()
    window_rows: list[dict[str, Any]] = []
    window_count_by_horizon = {str(horizon): 0 for horizon in HORIZONS}
    short_count_by_horizon = {str(horizon): 0 for horizon in HORIZONS}

    for segment in ordered_segments:
        segment_id = _require_text(segment.get("segment_id"), label="Segment ID")
        if segment_id in seen_segment_ids:
            raise ValueError(f"Duplicate source segment ID: {segment_id}")
        seen_segment_ids.add(segment_id)
        frames = _frames_for_segment(
            frame_rows,
            segment,
            source_experience_identity=source_experience_identity,
            source_normalization_identity=source_normalization_identity,
            max_timestamp_gap_ns=max_timestamp_gap_ns,
        )
        for horizon in HORIZONS:
            if len(frames) < horizon:
                short_count_by_horizon[str(horizon)] += 1
                continue
            for start in range(len(frames) - horizon + 1):
                sequence = frames[start : start + horizon]
                row = _window_row(
                    sequence,
                    segment=segment,
                    source_experience_identity=source_experience_identity,
                    source_normalization_identity=source_normalization_identity,
                    source_manifest_sha256=source_manifest_sha256,
                )
                window_rows.append(row)
                window_count_by_horizon[str(horizon)] += 1

    window_ids = [row["window_id"] for row in window_rows]
    if len(window_ids) != len(set(window_ids)):
        raise ValueError("Duplicate compiled window ID")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source_compiler_schema_version": EXPERIENCE_COMPILER_SCHEMA_VERSION,
        "source_compiler_manifest_sha256": source_manifest_sha256,
        "source_experience_identity_sha256": source_experience_identity,
        "source_normalization_identity_sha256": source_normalization_identity,
        "source_frames_sha256": _require_sha256(
            source_manifest.get("output_sha256", {}).get("frames.parquet"),
            label="Source frames hash",
        ),
        "source_segments_sha256": _require_sha256(
            source_manifest.get("output_sha256", {}).get("segments.parquet"),
            label="Source segments hash",
        ),
        "source_frame_count": len(frame_rows),
        "source_eligible_frame_count": source_manifest.get("eligible_frame_count"),
        "source_segment_count": len(segment_rows),
        "horizons": list(HORIZONS),
        "window_count": len(window_rows),
        "window_count_by_horizon": window_count_by_horizon,
        "segments_shorter_than_horizon_count_by_horizon": short_count_by_horizon,
        "padding_applied": False,
        "inferred_actions": False,
        "raw_bytes_rewritten": False,
        "training_eligible": False,
        "simulation_training_ready": False,
        "optimizer_training": False,
        "physical_actuation": False,
    }
    return {"manifest": manifest, "window_rows": window_rows}


def _validate_frame_uniqueness(frame_rows: list[dict[str, Any]]) -> None:
    seen_frame_ids: set[str] = set()
    seen_rollout_indices: set[tuple[str, int]] = set()
    for row in frame_rows:
        frame_id = _require_text(row.get("frame_id"), label="Source frame ID")
        rollout_id = _require_text(row.get("rollout_id"), label="Source frame rollout ID")
        frame_index = _require_int(row.get("frame_index"), label="Source frame index")
        if frame_id in seen_frame_ids:
            raise ValueError(f"Duplicate source frame ID: {frame_id}")
        if (rollout_id, frame_index) in seen_rollout_indices:
            raise ValueError(f"Duplicate source rollout frame index: {rollout_id}/{frame_index}")
        seen_frame_ids.add(frame_id)
        seen_rollout_indices.add((rollout_id, frame_index))


def _frames_for_segment(
    frame_rows: list[dict[str, Any]],
    segment: dict[str, Any],
    *,
    source_experience_identity: str,
    source_normalization_identity: str,
    max_timestamp_gap_ns: int,
) -> list[dict[str, Any]]:
    rollout_id = _require_text(segment.get("rollout_id"), label="Segment rollout ID")
    start_index = _require_int(segment.get("start_frame_index"), label="Segment start frame index")
    end_index = _require_int(segment.get("end_frame_index"), label="Segment end frame index")
    if end_index < start_index:
        raise ValueError("Segment frame indices are reversed")
    expected_count = _require_positive_int(segment.get("frame_count"), label="Segment frame count")
    if segment.get("source_experience_identity_sha256") != source_experience_identity:
        raise ValueError("Segment source experience identity drifted")
    if segment.get("source_normalization_identity_sha256") != source_normalization_identity:
        raise ValueError("Segment source normalization identity drifted")
    raw_identity = _require_sha256(
        segment.get("raw_rollout_record_identity_sha256"),
        label="Segment raw rollout identity",
    )
    frames = sorted(
        [
            row
            for row in frame_rows
            if row.get("rollout_id") == rollout_id
            and start_index <= _require_int(row.get("frame_index"), label="Source frame index") <= end_index
        ],
        key=lambda row: _require_int(row.get("frame_index"), label="Source frame index"),
    )
    if len(frames) != expected_count:
        raise ValueError("Segment frame count does not match source frames")
    if not frames:
        raise ValueError("Source segment has no frames")
    if frames[0].get("frame_id") != segment.get("start_frame_id"):
        raise ValueError("Segment start frame identity drifted")
    if frames[-1].get("frame_id") != segment.get("end_frame_id"):
        raise ValueError("Segment end frame identity drifted")
    if frames[0].get("timestamp_ns") != segment.get("start_timestamp_ns"):
        raise ValueError("Segment start timestamp drifted")
    if frames[-1].get("timestamp_ns") != segment.get("end_timestamp_ns"):
        raise ValueError("Segment end timestamp drifted")

    prior_index: int | None = None
    prior_timestamp: int | None = None
    for position, frame in enumerate(frames):
        frame_index = _require_int(frame.get("frame_index"), label="Source frame index")
        timestamp = _require_int(frame.get("timestamp_ns"), label="Source frame timestamp")
        if frame.get("frame_eligible") is not True:
            raise ValueError("Source segment contains an ineligible frame")
        if frame.get("action_variants_complete") is not True:
            raise ValueError("Source segment contains action-incomplete frame")
        if frame.get("raw_rollout_record_identity_sha256") != raw_identity:
            raise ValueError("Source frame raw-rollout identity drifted")
        quarantine_reasons = _parse_json(
            frame.get("quarantine_reason_codes_json"), label="Source frame quarantine reasons"
        )
        if quarantine_reasons != []:
            raise ValueError("Source segment contains quarantined frame")
        _validate_actions(frame.get("actions_json"))
        events = _parse_json(frame.get("boundary_events_json"), label="Source frame boundary events")
        if not isinstance(events, list) or any(not isinstance(event, str) for event in events):
            raise ValueError("Source frame boundary events are invalid")
        if 0 < position < len(frames) - 1 and events:
            raise ValueError("Source segment contains an internal hard boundary")
        if prior_index is not None and frame_index != prior_index + 1:
            raise ValueError("Source segment frame indices are not contiguous")
        if prior_timestamp is not None:
            if timestamp <= prior_timestamp:
                raise ValueError("Source segment timestamps are not strictly increasing")
            if timestamp - prior_timestamp > max_timestamp_gap_ns:
                raise ValueError("Source segment contains a timestamp gap")
        prior_index = frame_index
        prior_timestamp = timestamp
    return frames


def _window_row(
    frames: list[dict[str, Any]],
    *,
    segment: dict[str, Any],
    source_experience_identity: str,
    source_normalization_identity: str,
    source_manifest_sha256: str,
) -> dict[str, Any]:
    frame_ids = [frame["frame_id"] for frame in frames]
    unsigned = {
        "segment_id": segment["segment_id"],
        "horizon": len(frames),
        "frame_ids": frame_ids,
        "source_compiler_manifest_sha256": source_manifest_sha256,
    }
    return {
        "window_id": hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest(),
        "segment_id": segment["segment_id"],
        "rollout_id": segment["rollout_id"],
        "horizon": len(frames),
        "window_frame_count": len(frames),
        "start_frame_id": frames[0]["frame_id"],
        "end_frame_id": frames[-1]["frame_id"],
        "start_frame_index": frames[0]["frame_index"],
        "end_frame_index": frames[-1]["frame_index"],
        "start_timestamp_ns": frames[0]["timestamp_ns"],
        "end_timestamp_ns": frames[-1]["timestamp_ns"],
        "frame_ids_json": _json(frame_ids),
        "action_frame_ids_json": _json(frame_ids),
        "action_variants_json": _json(list(ACTION_VARIANTS)),
        "raw_rollout_record_identity_sha256": segment["raw_rollout_record_identity_sha256"],
        "source_experience_identity_sha256": source_experience_identity,
        "source_normalization_identity_sha256": source_normalization_identity,
        "source_compiler_manifest_sha256": source_manifest_sha256,
    }


def _validate_actions(value: Any) -> None:
    actions = _parse_json(value, label="Source frame actions")
    if not isinstance(actions, dict):
        raise ValueError("Source frame actions are invalid")
    for variant in ACTION_VARIANTS:
        action = actions.get(variant)
        if not isinstance(action, dict) or action.get("state") not in {"observed", "derived"}:
            raise ValueError(f"Source frame action variant is unavailable: {variant}")
        if action["state"] == "derived":
            provenance = action.get("provenance")
            derived_values = action.get("values")
            if (
                not isinstance(provenance, dict)
                or provenance.get("state") != "derived"
                or not isinstance(provenance.get("derivation"), str)
                or not provenance["derivation"].strip()
                or action.get("ordered_joint_names") != list(JOINT_NAMES)
                or not isinstance(derived_values, list)
                or len(derived_values) != len(JOINT_NAMES)
                or any(
                    isinstance(item, bool)
                    or not isinstance(item, (int, float))
                    or not math.isfinite(item)
                    for item in derived_values
                )
            ):
                raise ValueError(
                    "Source frame derived action is incomplete or lacks a named "
                    f"derivation: {variant}"
                )
        values = action.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError(f"Source frame action values are invalid: {variant}")
        for item in values:
            if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item):
                raise ValueError(f"Source frame action values are non-finite: {variant}")


def _require_closed_authority(payload: dict[str, Any], *, label: str) -> None:
    for field in (
        "training_eligible",
        "simulation_training_ready",
        "optimizer_training",
        "physical_actuation",
        "raw_bytes_rewritten",
    ):
        if payload.get(field) is not False:
            raise ValueError(f"{label} authority flag drifted: {field}")


def _parse_json(value: Any, *, label: str) -> Any:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be canonical JSON text")
    try:
        parsed = json.loads(value, parse_constant=_reject_constant)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} must be valid finite JSON") from exc
    _reject_non_finite(parsed, label=label)
    return parsed


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")


def _reject_non_finite(value: Any, *, label: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{label} contains non-finite values")
    if isinstance(value, dict):
        for child in value.values():
            _reject_non_finite(child, label=label)
    elif isinstance(value, list):
        for child in value:
            _reject_non_finite(child, label=label)


def _require_text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be nonblank")
    return value


def _require_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _require_positive_int(value: Any, *, label: str) -> int:
    number = _require_int(value, label=label)
    if number <= 0:
        raise ValueError(f"{label} must be positive")
    return number


def _require_sha256(value: Any, *, label: str) -> str:
    text = _require_text(value, label=label)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return text


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
