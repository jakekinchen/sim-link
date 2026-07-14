"""Deterministic T17.7 raw-to-window replay audit for the T17.5b grasp source.

The audit deliberately materializes only input/action *descriptors*.  It never
loads a policy, invokes model inference, or rewrites the append-only raw store.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import struct
import zlib
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
from scenesmith.robot_lab.experience_records import ACTION_VARIANTS, JOINT_NAMES, REPO_ROOT
from scenesmith.robot_lab.experience_window_index import HORIZONS, verify_window_index
from scenesmith.robot_lab.scripted_grasp_episode_generation import (
    default_store_root,
    verify_episode_store,
)


SCHEMA_VERSION = "scenesmith.compiler_window_replay_audit.v1"
TASK_ID = "T17.7"
SELECTION_PER_HORIZON = 25
EPISODE_MANIFEST_PATH = REPO_ROOT / "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
COMPILER_DIR = REPO_ROOT / "configurations/robot_lab/t17_5b_compile"
WINDOW_DIR = REPO_ROOT / "configurations/robot_lab/t17_5b_window_index"
EXPECTED_ACTOR_INPUT_FIELDS = (
    "observation.top_rgb",
    "observation.wrist_rgb",
    "observation.joint_position",
    "observation.joint_velocity",
)
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def build_replay_audit() -> dict[str, Any]:
    """Audit exactly 100 source-bound windows and return a signed manifest."""

    episode_manifest = load_strict_json(EPISODE_MANIFEST_PATH)
    store_root = default_store_root()
    verify_episode_store(episode_manifest, store_root)
    verify_compilation(COMPILER_DIR)
    verify_window_index(WINDOW_DIR, COMPILER_DIR)

    compiler_manifest_path = COMPILER_DIR / "compiler_manifest.json"
    window_manifest_path = WINDOW_DIR / "window_manifest.json"
    compiler_manifest = load_strict_json(compiler_manifest_path)
    window_manifest = load_strict_json(window_manifest_path)
    if window_manifest.get("source_compiler_manifest_sha256") != _sha256_file(
        compiler_manifest_path
    ):
        raise ValueError("T17.5b window source compiler binding drifted")
    if episode_manifest.get("identity_sha256") is None:
        raise ValueError("T17.5b episode manifest identity is absent")

    frame_rows = pq.read_table(COMPILER_DIR / "frames.parquet").to_pylist()
    segment_rows = pq.read_table(COMPILER_DIR / "segments.parquet").to_pylist()
    window_rows = pq.read_table(WINDOW_DIR / "window_index.parquet").to_pylist()
    raw_frames = _load_raw_frames(episode_manifest, store_root)
    compiler_frames = _unique_map(frame_rows, "frame_id", label="compiler frame")
    segments = _unique_map(segment_rows, "segment_id", label="compiler segment")
    _validate_source_cardinality(
        compiler_manifest=compiler_manifest,
        window_manifest=window_manifest,
        raw_frames=raw_frames,
        compiler_frames=compiler_frames,
        segments=segments,
        window_rows=window_rows,
    )

    selected = select_replay_windows(window_rows)
    audit_windows = [
        _audit_window(
            window,
            selection_rank=rank,
            raw_frames=raw_frames,
            compiler_frames=compiler_frames,
            segments=segments,
            compiler_manifest=compiler_manifest,
        )
        for rank, window in selected
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "audit_scope": "t17_5b_raw_compiler_window_identity_and_input_descriptor_parity",
        "source_episode_store_manifest_path": _repo_relative(EPISODE_MANIFEST_PATH),
        "source_episode_store_manifest_file_sha256": _sha256_file(EPISODE_MANIFEST_PATH),
        "source_episode_store_manifest_identity_sha256": episode_manifest["identity_sha256"],
        "source_compiler_manifest_path": _repo_relative(compiler_manifest_path),
        "source_compiler_manifest_file_sha256": _sha256_file(compiler_manifest_path),
        "source_window_manifest_path": _repo_relative(window_manifest_path),
        "source_window_manifest_file_sha256": _sha256_file(window_manifest_path),
        "source_frames_file_sha256": _sha256_file(COMPILER_DIR / "frames.parquet"),
        "source_segments_file_sha256": _sha256_file(COMPILER_DIR / "segments.parquet"),
        "source_window_index_file_sha256": _sha256_file(WINDOW_DIR / "window_index.parquet"),
        "selection_algorithm": {
            "name": "per_horizon_rollout_cover_then_sha256_rank_v1",
            "per_horizon_count": SELECTION_PER_HORIZON,
            "horizons": list(HORIZONS),
            "sha256_domain": "t17.7/window-selection/v1",
        },
        "source_counts": {
            "raw_frame_count": len(raw_frames),
            "compiler_frame_count": len(compiler_frames),
            "compiler_segment_count": len(segments),
            "window_count": len(window_rows),
        },
        "selected_window_count": len(audit_windows),
        "selected_window_count_by_horizon": {
            str(horizon): sum(window["horizon"] == horizon for window in audit_windows)
            for horizon in HORIZONS
        },
        "selected_windows": audit_windows,
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


def verify_replay_audit(manifest: dict[str, Any]) -> None:
    """Regenerate and compare the complete signed audit without writes."""

    verify_signed_payload(manifest, label="compiler window replay audit")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("task_id") != TASK_ID:
        raise ValueError("Replay audit schema or task identity drifted")
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
        if manifest.get(field) is not False:
            raise ValueError(f"Replay audit authority flag drifted: {field}")
    if manifest.get("selected_window_count") != len(HORIZONS) * SELECTION_PER_HORIZON:
        raise ValueError("Replay audit selected-window count drifted")
    expected_counts = {str(horizon): SELECTION_PER_HORIZON for horizon in HORIZONS}
    if manifest.get("selected_window_count_by_horizon") != expected_counts:
        raise ValueError("Replay audit horizon selection count drifted")
    windows = manifest.get("selected_windows")
    if not isinstance(windows, list):
        raise ValueError("Replay audit selected windows are absent")
    if len({window.get("window_id") for window in windows if isinstance(window, dict)}) != len(windows):
        raise ValueError("Replay audit selected a duplicate window")
    expected = build_replay_audit()
    if canonical_json_bytes(manifest) != canonical_json_bytes(expected):
        raise ValueError("Replay audit drifted from its verified sources")


def select_replay_windows(window_rows: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    """Return 25 stable selections per horizon with full rollout coverage first."""

    if not isinstance(window_rows, list):
        raise ValueError("Window rows must be a list")
    by_horizon: dict[int, list[dict[str, Any]]] = {horizon: [] for horizon in HORIZONS}
    seen_ids: set[str] = set()
    for row in window_rows:
        if not isinstance(row, dict):
            raise ValueError("Window row must be an object")
        window_id = _require_sha256(row.get("window_id"), label="window ID")
        if window_id in seen_ids:
            raise ValueError("Window index has a duplicate window ID")
        seen_ids.add(window_id)
        horizon = _require_int(row.get("horizon"), label="window horizon")
        if horizon not in by_horizon:
            raise ValueError("Window index has an unsupported horizon")
        by_horizon[horizon].append(row)

    selected: list[tuple[int, dict[str, Any]]] = []
    for horizon in HORIZONS:
        rows = by_horizon[horizon]
        if len(rows) < SELECTION_PER_HORIZON:
            raise ValueError(f"Horizon {horizon} cannot supply {SELECTION_PER_HORIZON} windows")
        by_rollout: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            rollout_id = _require_text(row.get("rollout_id"), label="window rollout ID")
            by_rollout.setdefault(rollout_id, []).append(row)
        if len(by_rollout) > SELECTION_PER_HORIZON:
            raise ValueError("Rollout coverage exceeds the fixed per-horizon selection budget")
        chosen: list[dict[str, Any]] = []
        for rollout_id in sorted(by_rollout):
            chosen.append(min(by_rollout[rollout_id], key=lambda row: _selection_key(row, horizon)))
        chosen_ids = {row["window_id"] for row in chosen}
        remainder = sorted(
            (row for row in rows if row["window_id"] not in chosen_ids),
            key=lambda row: _selection_key(row, horizon),
        )
        chosen.extend(remainder[: SELECTION_PER_HORIZON - len(chosen)])
        if len(chosen) != SELECTION_PER_HORIZON:
            raise ValueError("Replay selection did not meet the fixed per-horizon budget")
        for rank, row in enumerate(chosen, start=1):
            selected.append((rank, row))
    if len({row["window_id"] for _, row in selected}) != len(selected):
        raise ValueError("Replay selection contains duplicate windows")
    return selected


def _audit_window(
    window: dict[str, Any],
    *,
    selection_rank: int,
    raw_frames: dict[str, dict[str, Any]],
    compiler_frames: dict[str, dict[str, Any]],
    segments: dict[str, dict[str, Any]],
    compiler_manifest: dict[str, Any],
) -> dict[str, Any]:
    horizon = _require_int(window.get("horizon"), label="window horizon")
    if horizon not in HORIZONS or window.get("window_frame_count") != horizon:
        raise ValueError("Window horizon and frame count drifted")
    frame_ids = _parse_string_list(window.get("frame_ids_json"), label="window frame IDs")
    action_frame_ids = _parse_string_list(
        window.get("action_frame_ids_json"), label="window action frame IDs"
    )
    if len(frame_ids) != horizon or action_frame_ids != frame_ids:
        raise ValueError("Window frame/action sequence drifted")
    if window.get("action_variants_json") != _canonical_json(list(ACTION_VARIANTS)):
        raise ValueError("Window action variant declaration drifted")
    segment_id = _require_text(window.get("segment_id"), label="window segment ID")
    segment = segments.get(segment_id)
    if segment is None:
        raise ValueError("Window references an absent source segment")
    raw_rollout_identity = _require_sha256(
        window.get("raw_rollout_record_identity_sha256"), label="window raw rollout identity"
    )
    if segment.get("raw_rollout_record_identity_sha256") != raw_rollout_identity:
        raise ValueError("Window raw rollout identity drifted from source segment")
    if window.get("source_compiler_manifest_sha256") != _sha256_file(
        COMPILER_DIR / "compiler_manifest.json"
    ):
        raise ValueError("Window compiler manifest binding drifted")
    source_identity = compiler_manifest.get("source_experience_identity_sha256")
    normalization_identity = compiler_manifest.get("source_normalization_identity_sha256")
    if (
        window.get("source_experience_identity_sha256") != source_identity
        or window.get("source_normalization_identity_sha256") != normalization_identity
    ):
        raise ValueError("Window source identity binding drifted")

    audited_frames: list[dict[str, Any]] = []
    prior_index: int | None = None
    prior_timestamp: int | None = None
    for position, frame_id in enumerate(frame_ids):
        raw = raw_frames.get(frame_id)
        compiler = compiler_frames.get(frame_id)
        if raw is None or compiler is None:
            raise ValueError("Window frame cannot be traced to raw and compiler sources")
        _validate_raw_compiler_frame(raw, compiler)
        if compiler.get("raw_rollout_record_identity_sha256") != raw_rollout_identity:
            raise ValueError("Window raw rollout identity drifted from compiler frame")
        frame_index = _require_int(compiler.get("frame_index"), label="compiler frame index")
        timestamp = _require_int(compiler.get("timestamp_ns"), label="compiler timestamp")
        if prior_index is not None and frame_index != prior_index + 1:
            raise ValueError("Selected window frame indices are not contiguous")
        if prior_timestamp is not None:
            if timestamp <= prior_timestamp:
                raise ValueError("Selected window timestamps are not strictly increasing")
            if timestamp - prior_timestamp > compiler_manifest.get("max_timestamp_gap_ns"):
                raise ValueError("Selected window contains a timestamp gap")
        boundary_events = _parse_string_list(
            compiler.get("boundary_events_json"), label="compiler frame boundary events"
        )
        if 0 < position < len(frame_ids) - 1 and boundary_events:
            raise ValueError("Selected window crosses an internal hard boundary")
        collection_descriptor = _collection_input_descriptor(raw)
        training_descriptor = _training_input_descriptor(raw, compiler)
        inference_descriptor = _inference_input_descriptor(raw, compiler)
        collection_sha = _sha256(collection_descriptor)
        if collection_sha != _sha256(training_descriptor) or collection_sha != _sha256(
            inference_descriptor
        ):
            raise ValueError("Collection/training/inference actor-input descriptor drifted")
        requested_action = _requested_action_descriptor(raw.get("actions"), compiler.get("actions_json"))
        audited_frames.append(
            {
                "frame_id": frame_id,
                "frame_index": frame_index,
                "timestamp_ns": timestamp,
                "raw_frame_record_identity_sha256": raw["record_identity_sha256"],
                "compiler_frame_record_identity_sha256": compiler["record_identity_sha256"],
                "actor_input_descriptor_sha256": collection_sha,
                "actor_input_tensor_fields": collection_descriptor["fields"],
                "requested_action_descriptor_sha256": _sha256(requested_action),
                "requested_action_tensor": requested_action,
            }
        )
        prior_index = frame_index
        prior_timestamp = timestamp
    if audited_frames[0]["frame_id"] != window.get("start_frame_id") or audited_frames[-1][
        "frame_id"
    ] != window.get("end_frame_id"):
        raise ValueError("Window endpoint frame identity drifted")
    if audited_frames[0]["frame_index"] != window.get("start_frame_index") or audited_frames[-1][
        "frame_index"
    ] != window.get("end_frame_index"):
        raise ValueError("Window endpoint frame index drifted")
    if audited_frames[0]["timestamp_ns"] != window.get("start_timestamp_ns") or audited_frames[-1][
        "timestamp_ns"
    ] != window.get("end_timestamp_ns"):
        raise ValueError("Window endpoint timestamp drifted")
    if window.get("rollout_id") != segment.get("rollout_id"):
        raise ValueError("Window rollout identity drifted from source segment")
    if (
        audited_frames[0]["frame_index"] < segment.get("start_frame_index")
        or audited_frames[-1]["frame_index"] > segment.get("end_frame_index")
    ):
        raise ValueError("Window lies outside its source segment")
    return {
        "window_id": window["window_id"],
        "horizon": horizon,
        "selection_rank": selection_rank,
        "segment_id": segment_id,
        "rollout_id": window["rollout_id"],
        "raw_rollout_record_identity_sha256": raw_rollout_identity,
        "frame_ids_sha256": _sha256(frame_ids),
        "frame_count": len(audited_frames),
        "frames": audited_frames,
    }


def _validate_source_cardinality(
    *,
    compiler_manifest: dict[str, Any],
    window_manifest: dict[str, Any],
    raw_frames: dict[str, dict[str, Any]],
    compiler_frames: dict[str, dict[str, Any]],
    segments: dict[str, dict[str, Any]],
    window_rows: list[dict[str, Any]],
) -> None:
    if len(raw_frames) != compiler_manifest.get("frame_count"):
        raise ValueError("Raw frame count does not match source compiler manifest")
    if len(compiler_frames) != compiler_manifest.get("frame_count"):
        raise ValueError("Compiler frame count does not match source compiler manifest")
    if len(segments) != compiler_manifest.get("segment_count"):
        raise ValueError("Compiler segment count does not match source compiler manifest")
    if len(window_rows) != window_manifest.get("window_count"):
        raise ValueError("Window row count does not match source window manifest")


def _load_raw_frames(manifest: dict[str, Any], store_root: Path) -> dict[str, dict[str, Any]]:
    root = Path(store_root).resolve()
    if not root.is_dir():
        raise ValueError("T17.5b raw episode store is absent")
    frames: dict[str, dict[str, Any]] = {}
    for entry in manifest.get("episodes", []):
        relative_path = entry.get("relative_path")
        if not isinstance(relative_path, str) or not relative_path or ".." in Path(relative_path).parts:
            raise ValueError("T17.5b episode relative path is invalid")
        configured_path = root / relative_path
        if configured_path.is_symlink():
            raise ValueError("T17.5b episode source may not be a symlink")
        path = configured_path.resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ValueError("T17.5b episode source escapes its store root") from error
        payload = load_strict_json(path)
        for frame in payload.get("frames", []):
            frame_id = _require_text(frame.get("frame_id"), label="raw frame ID")
            if frame_id in frames:
                raise ValueError("T17.5b raw store has a duplicate frame ID")
            frames[frame_id] = frame
    if not frames:
        raise ValueError("T17.5b raw store has no frames")
    return frames


def _validate_raw_compiler_frame(raw: dict[str, Any], compiler: dict[str, Any]) -> None:
    if raw.get("record_identity_sha256") != compiler.get("record_identity_sha256"):
        raise ValueError("Raw/compiler frame record identity drifted")
    for field in (
        "frame_id",
        "rollout_id",
        "frame_index",
        "timestamp_ns",
        "task_phase",
        "source_phase",
        "source_class",
        "proof_mode",
        "controller_owner",
        "control_mode",
    ):
        if raw.get(field) != compiler.get(field):
            raise ValueError(f"Raw/compiler frame field drifted: {field}")
    if compiler.get("frame_eligible") is not True or compiler.get("action_variants_complete") is not True:
        raise ValueError("Selected compiler frame is not fully eligible")
    if _parse_string_list(compiler.get("quarantine_reason_codes_json"), label="compiler quarantine"):
        raise ValueError("Selected compiler frame is quarantined")
    if _parse_string_list(compiler.get("actor_input_field_names_json"), label="compiler actor inputs") != raw.get(
        "actor_input_field_names"
    ):
        raise ValueError("Raw/compiler actor input declaration drifted")
    if _parse_json(compiler.get("actions_json"), label="compiler actions") != raw.get("actions"):
        raise ValueError("Raw/compiler action record drifted")


def _collection_input_descriptor(raw: dict[str, Any]) -> dict[str, Any]:
    return _actor_input_descriptor(raw, raw.get("actor_input_field_names"), label="collection")


def _training_input_descriptor(raw: dict[str, Any], compiler: dict[str, Any]) -> dict[str, Any]:
    fields = _parse_string_list(compiler.get("actor_input_field_names_json"), label="training actor inputs")
    return _actor_input_descriptor(raw, fields, label="training")


def _inference_input_descriptor(raw: dict[str, Any], compiler: dict[str, Any]) -> dict[str, Any]:
    fields = _parse_string_list(compiler.get("actor_input_field_names_json"), label="inference actor inputs")
    return _actor_input_descriptor(raw, fields, label="inference")


def _actor_input_descriptor(raw: dict[str, Any], fields: Any, *, label: str) -> dict[str, Any]:
    if fields != list(EXPECTED_ACTOR_INPUT_FIELDS):
        raise ValueError(f"{label} actor input fields drifted or leak privileged data")
    observations = raw.get("observations")
    if not isinstance(observations, dict):
        raise ValueError(f"{label} observations are absent")
    descriptors = [
        _image_tensor_descriptor("observation.top_rgb", observations.get("top")),
        _image_tensor_descriptor("observation.wrist_rgb", observations.get("wrist")),
        _numeric_tensor_descriptor(
            "observation.joint_position", observations.get("joint_position_mujoco_rad")
        ),
        _numeric_tensor_descriptor(
            "observation.joint_velocity", observations.get("joint_velocity_mujoco_rad_s")
        ),
    ]
    return {
        "serialization": "scenesmith.actor_input_tensor_descriptor.v1",
        "fields": descriptors,
    }


def _image_tensor_descriptor(name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} image descriptor is absent")
    if value.get("encoding") != "png" or value.get("width") != 256 or value.get("height") != 256:
        raise ValueError(f"{name} image encoding or dimensions drifted")
    if value.get("channels") != 3:
        raise ValueError(f"{name} image channel count drifted")
    encoded = value.get("png_base64")
    if not isinstance(encoded, str):
        raise ValueError(f"{name} image bytes are absent")
    try:
        png = base64.b64decode(encoded, validate=True)
    except Exception as error:  # pragma: no cover - decoder details vary
        raise ValueError(f"{name} image bytes are not canonical base64") from error
    if value.get("image_sha256") != hashlib.sha256(png).hexdigest():
        raise ValueError(f"{name} image byte hash drifted")
    pixels = _decode_unfiltered_rgb_png(png)
    return {
        "name": name,
        "dtype": "uint8",
        "shape": [256, 256, 3],
        "layout": "HWC",
        "tensor_sha256": hashlib.sha256(pixels).hexdigest(),
    }


def _numeric_tensor_descriptor(name: str, values: Any) -> dict[str, Any]:
    if not isinstance(values, list) or len(values) != len(JOINT_NAMES):
        raise ValueError(f"{name} numeric tensor shape drifted")
    numbers: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name} numeric tensor contains a non-finite value")
        numbers.append(float(value))
    encoded = struct.pack("<" + "d" * len(numbers), *numbers)
    return {
        "name": name,
        "dtype": "float64_le",
        "shape": [len(numbers)],
        "tensor_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _requested_action_descriptor(raw_actions: Any, compiler_actions_json: Any) -> dict[str, Any]:
    compiler_actions = _parse_json(compiler_actions_json, label="compiler requested actions")
    if raw_actions != compiler_actions or not isinstance(raw_actions, dict):
        raise ValueError("Raw/compiler requested action record drifted")
    requested = raw_actions.get("requested")
    if not isinstance(requested, dict) or requested.get("state") != "observed":
        raise ValueError("Requested action is not observed")
    if requested.get("ordered_joint_names") != list(JOINT_NAMES):
        raise ValueError("Requested action joint order drifted")
    values = requested.get("values")
    if not isinstance(values, list) or len(values) != len(JOINT_NAMES):
        raise ValueError("Requested action value shape drifted")
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Requested action contains a non-finite value")
    return {
        "dtype": "float64_le",
        "shape": [len(values)],
        "ordered_joint_names": list(JOINT_NAMES),
        "representation": requested.get("representation"),
        "units": requested.get("units"),
        "tensor_sha256": hashlib.sha256(
            struct.pack("<" + "d" * len(values), *(float(value) for value in values))
        ).hexdigest(),
    }


def _decode_unfiltered_rgb_png(png: bytes) -> bytes:
    if not png.startswith(_PNG_SIGNATURE):
        raise ValueError("Actor input image is not a PNG")
    cursor = len(_PNG_SIGNATURE)
    width = height = channels = None
    idat: list[bytes] = []
    ended = False
    while cursor < len(png):
        if cursor + 12 > len(png):
            raise ValueError("Actor input PNG is truncated")
        length = struct.unpack(">I", png[cursor : cursor + 4])[0]
        kind = png[cursor + 4 : cursor + 8]
        end = cursor + 12 + length
        if end > len(png):
            raise ValueError("Actor input PNG chunk is truncated")
        payload = png[cursor + 8 : cursor + 8 + length]
        expected_crc = struct.unpack(">I", png[cursor + 8 + length : end])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != expected_crc:
            raise ValueError("Actor input PNG chunk checksum drifted")
        if kind == b"IHDR":
            if len(payload) != 13:
                raise ValueError("Actor input PNG header is invalid")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if (width, height, bit_depth, color_type, compression, filtering, interlace) != (
                256,
                256,
                8,
                2,
                0,
                0,
                0,
            ):
                raise ValueError("Actor input PNG format drifted")
            channels = 3
        elif kind == b"IDAT":
            idat.append(payload)
        elif kind == b"IEND":
            if payload or end != len(png):
                raise ValueError("Actor input PNG end chunk is invalid")
            ended = True
            break
        cursor = end
    if not ended or width != 256 or height != 256 or channels != 3 or not idat:
        raise ValueError("Actor input PNG is incomplete")
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as error:
        raise ValueError("Actor input PNG pixel stream is invalid") from error
    row_bytes = width * channels
    expected_length = height * (row_bytes + 1)
    if len(raw) != expected_length:
        raise ValueError("Actor input PNG pixel length drifted")
    pixels = bytearray()
    for offset in range(0, len(raw), row_bytes + 1):
        if raw[offset] != 0:
            raise ValueError("Actor input PNG row filtering is unsupported")
        pixels.extend(raw[offset + 1 : offset + 1 + row_bytes])
    return bytes(pixels)


def _selection_key(row: dict[str, Any], horizon: int) -> tuple[str, str]:
    window_id = _require_sha256(row.get("window_id"), label="window ID")
    digest = _sha256(
        {
            "domain": "t17.7/window-selection/v1",
            "horizon": horizon,
            "window_id": window_id,
        }
    )
    return digest, window_id


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
    if _canonical_json(parsed) != value:
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
        raise ValueError("T17.7 source must remain inside this checkout") from error


def _canonical_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


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
