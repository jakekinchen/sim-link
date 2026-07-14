"""Source-bound T17.4 frame and hard-boundary segment compilation."""

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
from scenesmith.robot_lab.experience_records import (
    ACTION_VARIANTS,
    HARD_BOUNDARY_EVENTS,
    JOINT_NAMES,
    REPO_ROOT,
    verify_experience_record_contract,
)
from scenesmith.robot_lab.normalization_bundle import verify_normalization_bundle


SCHEMA_VERSION = "scenesmith.experience_compiler.v1"
DEFAULT_MAX_TIMESTAMP_GAP_NS = 1_000_000_000
OUTPUT_NAMES = (
    "frames.parquet",
    "segments.parquet",
    "quarantine_manifest.json",
    "compiler_manifest.json",
)
_SPLIT_BEFORE_EVENTS = set(HARD_BOUNDARY_EVENTS) - {"rollout_start", "rollout_end"}

FRAME_SCHEMA = pa.schema(
    [
        ("frame_id", pa.string()),
        ("rollout_id", pa.string()),
        ("frame_index", pa.int64()),
        ("timestamp_ns", pa.int64()),
        ("task_phase", pa.string()),
        ("source_phase", pa.string()),
        ("source_class", pa.string()),
        ("proof_mode", pa.string()),
        ("controller_owner", pa.string()),
        ("control_mode", pa.string()),
        ("boundary_events_json", pa.string()),
        ("actions_json", pa.string()),
        ("action_variants_complete", pa.bool_()),
        ("requested_gripper_pose_json", pa.string()),
        ("achieved_gripper_pose_json", pa.string()),
        ("effort_json", pa.string()),
        ("contact_geometry_witness_json", pa.string()),
        ("actor_input_field_names_json", pa.string()),
        ("reward_json", pa.string()),
        ("progress_json", pa.string()),
        ("strict_evaluator_result_json", pa.string()),
        ("frame_eligible", pa.bool_()),
        ("quarantine_reason_codes_json", pa.string()),
        ("record_identity_sha256", pa.string()),
        ("raw_rollout_record_identity_sha256", pa.string()),
        ("source_artifact_identity_sha256", pa.string()),
        ("prompt_identity_sha256", pa.string()),
        ("coordinate_contract_identity_sha256", pa.string()),
        ("preprocessing_identity", pa.string()),
    ]
)

SEGMENT_SCHEMA = pa.schema(
    [
        ("segment_id", pa.string()),
        ("rollout_id", pa.string()),
        ("start_frame_id", pa.string()),
        ("end_frame_id", pa.string()),
        ("start_frame_index", pa.int64()),
        ("end_frame_index", pa.int64()),
        ("frame_count", pa.int64()),
        ("start_timestamp_ns", pa.int64()),
        ("end_timestamp_ns", pa.int64()),
        ("raw_rollout_record_identity_sha256", pa.string()),
        ("source_experience_identity_sha256", pa.string()),
        ("source_normalization_identity_sha256", pa.string()),
        ("boundary_policy", pa.string()),
    ]
)


def compile_experience_contract(
    contract_path: Path,
    normalization_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Validate source contracts, compile them, and write deterministic outputs."""

    contract = load_strict_json(contract_path)
    verify_experience_record_contract(contract, repo_root=REPO_ROOT)
    normalization = load_strict_json(normalization_path)
    verify_normalization_bundle(normalization, repo_root=REPO_ROOT)
    result = compile_projection(
        contract["fixture_projection"],
        source_experience_identity=contract["identity_sha256"],
        source_normalization_identity=normalization["identity_sha256"],
    )
    return write_compilation(result, output_dir)


def compile_projection(
    projection: dict[str, Any],
    *,
    source_experience_identity: str,
    source_normalization_identity: str,
    max_timestamp_gap_ns: int = DEFAULT_MAX_TIMESTAMP_GAP_NS,
) -> dict[str, Any]:
    """Compile one validated or test-built projection without inferring data."""

    raw = projection.get("raw_rollout")
    frames = projection.get("frames")
    if not isinstance(raw, dict) or not isinstance(frames, list):
        raise ValueError("Experience projection must contain raw_rollout and frames")
    if not isinstance(max_timestamp_gap_ns, int) or max_timestamp_gap_ns <= 0:
        raise ValueError("max_timestamp_gap_ns must be a positive integer")

    frame_rows: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    eligible_frame_ids: set[Any] = set()
    prior_timestamp: int | None = None
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError("Frame projection row must be an object")
        reasons = _frame_quarantine_reasons(frame)
        timestamp = frame.get("timestamp_ns")
        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            reasons.append("invalid_timestamp")
        elif prior_timestamp is not None and timestamp - prior_timestamp > max_timestamp_gap_ns:
            reasons.append("timestamp_gap")
        if isinstance(timestamp, int) and not isinstance(timestamp, bool):
            prior_timestamp = timestamp

        frame_eligible = not reasons
        row = _frame_row(
            frame,
            raw=raw,
            frame_eligible=frame_eligible,
            reasons=reasons,
        )
        frame_rows.append(row)
        if frame_eligible:
            eligible_frame_ids.add(frame.get("frame_id"))
        else:
            quarantine.append(
                _quarantine_row(
                    kind="frame",
                    frame=frame,
                    raw=raw,
                    reason_codes=reasons,
                )
            )

    segment_rows, segment_quarantine = _build_segments(
        frames,
        raw=raw,
        source_experience_identity=source_experience_identity,
        source_normalization_identity=source_normalization_identity,
        max_timestamp_gap_ns=max_timestamp_gap_ns,
        eligible_frame_ids=eligible_frame_ids,
    )
    quarantine.extend(segment_quarantine)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source_experience_identity_sha256": source_experience_identity,
        "source_normalization_identity_sha256": source_normalization_identity,
        "raw_rollout_id": raw.get("rollout_id"),
        "frame_count": len(frame_rows),
        "eligible_frame_count": sum(row["frame_eligible"] for row in frame_rows),
        "segment_count": len(segment_rows),
        "quarantine_count": len(quarantine),
        "max_timestamp_gap_ns": max_timestamp_gap_ns,
        "training_eligible": False,
        "simulation_training_ready": False,
        "optimizer_training": False,
        "physical_actuation": False,
        "raw_bytes_rewritten": False,
        "hard_boundary_events": list(HARD_BOUNDARY_EVENTS),
        "frame_rows": frame_rows,
        "segment_rows": segment_rows,
        "quarantine": quarantine,
    }
    return {"manifest": manifest, "frame_rows": frame_rows, "segment_rows": segment_rows, "quarantine": quarantine}


def compile_projections(
    projections: list[dict[str, Any]],
    *,
    source_experience_identity: str,
    source_normalization_identity: str,
    source_episode_store_manifest_sha256: str | None = None,
    max_timestamp_gap_ns: int = DEFAULT_MAX_TIMESTAMP_GAP_NS,
) -> dict[str, Any]:
    """Compile multiple append-only rollouts into one source-bound view."""

    if not isinstance(projections, list) or not projections:
        raise ValueError("At least one source projection is required")
    compiled = [
        compile_projection(
            projection,
            source_experience_identity=source_experience_identity,
            source_normalization_identity=source_normalization_identity,
            max_timestamp_gap_ns=max_timestamp_gap_ns,
        )
        for projection in projections
    ]
    frame_rows = [row for result in compiled for row in result["frame_rows"]]
    segment_rows = [row for result in compiled for row in result["segment_rows"]]
    quarantine = [row for result in compiled for row in result["quarantine"]]
    frame_ids = [row["frame_id"] for row in frame_rows]
    segment_ids = [row["segment_id"] for row in segment_rows]
    if len(frame_ids) != len(set(frame_ids)):
        raise ValueError("Source projections contain duplicate frame IDs")
    if len(segment_ids) != len(set(segment_ids)):
        raise ValueError("Source projections contain duplicate segment IDs")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source_experience_identity_sha256": source_experience_identity,
        "source_normalization_identity_sha256": source_normalization_identity,
        "raw_rollout_id": "multiple_append_only_rollouts",
        "source_rollout_count": len(projections),
        "frame_count": len(frame_rows),
        "eligible_frame_count": sum(row["frame_eligible"] for row in frame_rows),
        "segment_count": len(segment_rows),
        "quarantine_count": len(quarantine),
        "max_timestamp_gap_ns": max_timestamp_gap_ns,
        "training_eligible": False,
        "simulation_training_ready": False,
        "optimizer_training": False,
        "physical_actuation": False,
        "raw_bytes_rewritten": False,
        "hard_boundary_events": list(HARD_BOUNDARY_EVENTS),
        "frame_rows": frame_rows,
        "segment_rows": segment_rows,
        "quarantine": quarantine,
    }
    if source_episode_store_manifest_sha256 is not None:
        if (
            not isinstance(source_episode_store_manifest_sha256, str)
            or len(source_episode_store_manifest_sha256) != 64
            or any(character not in "0123456789abcdef" for character in source_episode_store_manifest_sha256)
        ):
            raise ValueError("Source episode-store manifest hash is invalid")
        manifest["source_episode_store_manifest_sha256"] = (
            source_episode_store_manifest_sha256
        )
    return {
        "manifest": manifest,
        "frame_rows": frame_rows,
        "segment_rows": segment_rows,
        "quarantine": quarantine,
    }


def write_compilation(result: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Write parquet and JSON outputs, then bind their hashes into the manifest."""

    output_dir.mkdir(parents=True, exist_ok=True)
    frame_path = output_dir / "frames.parquet"
    segment_path = output_dir / "segments.parquet"
    quarantine_path = output_dir / "quarantine_manifest.json"
    manifest_path = output_dir / "compiler_manifest.json"
    pq.write_table(
        pa.Table.from_pylist(result["frame_rows"], schema=FRAME_SCHEMA),
        frame_path,
        compression="NONE",
        use_dictionary=False,
        write_statistics=False,
        version="2.6",
    )
    pq.write_table(
        pa.Table.from_pylist(result["segment_rows"], schema=SEGMENT_SCHEMA),
        segment_path,
        compression="NONE",
        use_dictionary=False,
        write_statistics=False,
        version="2.6",
    )
    quarantine_payload = {
        "schema_version": SCHEMA_VERSION,
        "source_experience_identity_sha256": result["manifest"]["source_experience_identity_sha256"],
        "source_normalization_identity_sha256": result["manifest"]["source_normalization_identity_sha256"],
        "training_eligible": False,
        "simulation_training_ready": False,
        "optimizer_training": False,
        "physical_actuation": False,
        "raw_bytes_rewritten": False,
        "quarantine": result["quarantine"],
    }
    dump_canonical_json(quarantine_path, quarantine_payload)
    manifest = dict(result["manifest"])
    manifest.pop("frame_rows", None)
    manifest.pop("segment_rows", None)
    manifest.pop("quarantine", None)
    manifest["output_sha256"] = {
        "frames.parquet": _sha256_file(frame_path),
        "segments.parquet": _sha256_file(segment_path),
        "quarantine_manifest.json": _sha256_file(quarantine_path),
    }
    dump_canonical_json(manifest_path, manifest)
    return {
        "manifest": manifest,
        "frame_rows": result["frame_rows"],
        "segment_rows": result["segment_rows"],
        "quarantine": result["quarantine"],
    }


def verify_compilation(output_dir: Path) -> None:
    """Verify output hashes, schemas, counts, and fail-closed authority labels."""

    manifest = load_strict_json(output_dir / "compiler_manifest.json")
    quarantine = load_strict_json(output_dir / "quarantine_manifest.json")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Compiler schema version drifted")
    for field in (
        "training_eligible",
        "simulation_training_ready",
        "optimizer_training",
        "physical_actuation",
        "raw_bytes_rewritten",
    ):
        if manifest.get(field) is not False:
            raise ValueError(f"Compiler authority flag drifted: {field}")
        if quarantine.get(field) is not False:
            raise ValueError(f"Quarantine authority flag drifted: {field}")
    for name in ("frames.parquet", "segments.parquet", "quarantine_manifest.json"):
        path = output_dir / name
        if manifest.get("output_sha256", {}).get(name) != _sha256_file(path):
            raise ValueError(f"Compiler output hash drifted: {name}")
    frame_table = pq.read_table(output_dir / "frames.parquet")
    segment_table = pq.read_table(output_dir / "segments.parquet")
    if frame_table.schema != FRAME_SCHEMA or segment_table.schema != SEGMENT_SCHEMA:
        raise ValueError("Compiler parquet schema drifted")
    if frame_table.num_rows != manifest.get("frame_count"):
        raise ValueError("Compiler frame count drifted")
    if segment_table.num_rows != manifest.get("segment_count"):
        raise ValueError("Compiler segment count drifted")
    if len(quarantine.get("quarantine", [])) != manifest.get("quarantine_count"):
        raise ValueError("Compiler quarantine count drifted")


def _frame_quarantine_reasons(frame: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    actions = frame.get("actions")
    if not isinstance(actions, dict):
        reasons.append("missing_action_variants")
    else:
        for variant in ACTION_VARIANTS:
            action = actions.get(variant)
            if not _action_variant_complete(action):
                reasons.append(f"missing_action_{variant}")
    for field in ("requested_gripper_pose", "achieved_gripper_pose", "effort"):
        value = frame.get(field)
        if not isinstance(value, dict) or value.get("state") != "observed" or value.get("value") is None:
            reasons.append(f"missing_{field}")
    events = frame.get("boundary_events")
    if not isinstance(events, list) or any(event not in HARD_BOUNDARY_EVENTS for event in events):
        reasons.append("unknown_boundary_event")
    return reasons


def _frame_row(
    frame: dict[str, Any],
    *,
    raw: dict[str, Any],
    frame_eligible: bool,
    reasons: list[str],
) -> dict[str, Any]:
    actions = frame.get("actions")
    return {
        "frame_id": _string(frame.get("frame_id")),
        "rollout_id": _string(frame.get("rollout_id")),
        "frame_index": _integer(frame.get("frame_index")),
        "timestamp_ns": _integer(frame.get("timestamp_ns")),
        "task_phase": _string(frame.get("task_phase")),
        "source_phase": _string(frame.get("source_phase")),
        "source_class": _string(frame.get("source_class")),
        "proof_mode": _string(frame.get("proof_mode")),
        "controller_owner": _string(frame.get("controller_owner")),
        "control_mode": _string(frame.get("control_mode")),
        "boundary_events_json": _json(frame.get("boundary_events", [])),
        "actions_json": _json(frame.get("actions")),
        "action_variants_complete": _actions_complete(actions),
        "requested_gripper_pose_json": _json(frame.get("requested_gripper_pose")),
        "achieved_gripper_pose_json": _json(frame.get("achieved_gripper_pose")),
        "effort_json": _json(frame.get("effort")),
        "contact_geometry_witness_json": _json(frame.get("contact_geometry_witness")),
        "actor_input_field_names_json": _json(frame.get("actor_input_field_names", [])),
        "reward_json": _json(frame.get("reward")),
        "progress_json": _json(frame.get("progress")),
        "strict_evaluator_result_json": _json(frame.get("strict_evaluator_result")),
        "frame_eligible": frame_eligible,
        "quarantine_reason_codes_json": _json(reasons),
        "record_identity_sha256": _string(frame.get("record_identity_sha256")),
        "raw_rollout_record_identity_sha256": _string(raw.get("record_identity_sha256")),
        "source_artifact_identity_sha256": _nested_string(raw, "source_artifact_ref", "identity_sha256"),
        "prompt_identity_sha256": _nested_string(raw, "prompt", "identity_sha256"),
        "coordinate_contract_identity_sha256": _nested_string(raw, "coordinate_contract_ref", "identity_sha256"),
        "preprocessing_identity": _string(raw.get("preprocessing_identity")),
    }


def _build_segments(
    frames: list[dict[str, Any]],
    *,
    raw: dict[str, Any],
    source_experience_identity: str,
    source_normalization_identity: str,
    max_timestamp_gap_ns: int,
    eligible_frame_ids: set[Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    segments: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    def finish(reason: str) -> None:
        nonlocal current
        if not current:
            return
        if len(current) < 2:
            quarantine.append(
                _quarantine_row(
                    kind="segment",
                    frame=current[0],
                    raw=raw,
                    reason_codes=["segment_too_short_after_hard_boundary"],
                )
            )
        else:
            segments.append(
                _segment_row(
                    current,
                    raw=raw,
                    source_experience_identity=source_experience_identity,
                    source_normalization_identity=source_normalization_identity,
                    boundary_policy=reason,
                )
            )
        current = []

    prior: dict[str, Any] | None = None
    for frame in frames:
        events = set(frame.get("boundary_events", []))
        if frame.get("frame_id") not in eligible_frame_ids:
            finish("quarantined_frame")
            prior = frame
            continue
        prior_timestamp = prior.get("timestamp_ns") if prior else None
        timestamp = frame.get("timestamp_ns")
        timestamp_gap = (
            isinstance(timestamp, int)
            and not isinstance(timestamp, bool)
            and isinstance(prior_timestamp, int)
            and not isinstance(prior_timestamp, bool)
            and timestamp - prior_timestamp > max_timestamp_gap_ns
        )
        if current and (events & _SPLIT_BEFORE_EVENTS or timestamp_gap):
            finish("hard_boundary_or_timestamp_gap")
        current.append(frame)
        if "rollout_end" in events:
            finish("rollout_end")
        prior = frame
    finish("end_of_rollout")
    return segments, quarantine


def _segment_row(
    frames: list[dict[str, Any]],
    *,
    raw: dict[str, Any],
    source_experience_identity: str,
    source_normalization_identity: str,
    boundary_policy: str,
) -> dict[str, Any]:
    unsigned = {
        "rollout_id": raw.get("rollout_id"),
        "start_frame_id": frames[0].get("frame_id"),
        "end_frame_id": frames[-1].get("frame_id"),
        "start_frame_index": frames[0].get("frame_index"),
        "end_frame_index": frames[-1].get("frame_index"),
        "source_experience_identity_sha256": source_experience_identity,
    }
    return {
        "segment_id": hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest(),
        "rollout_id": _string(raw.get("rollout_id")),
        "start_frame_id": _string(frames[0].get("frame_id")),
        "end_frame_id": _string(frames[-1].get("frame_id")),
        "start_frame_index": _integer(frames[0].get("frame_index")),
        "end_frame_index": _integer(frames[-1].get("frame_index")),
        "frame_count": len(frames),
        "start_timestamp_ns": _integer(frames[0].get("timestamp_ns")),
        "end_timestamp_ns": _integer(frames[-1].get("timestamp_ns")),
        "raw_rollout_record_identity_sha256": _string(raw.get("record_identity_sha256")),
        "source_experience_identity_sha256": source_experience_identity,
        "source_normalization_identity_sha256": source_normalization_identity,
        "boundary_policy": boundary_policy,
    }


def _quarantine_row(
    *,
    kind: str,
    frame: dict[str, Any],
    raw: dict[str, Any],
    reason_codes: list[str],
) -> dict[str, Any]:
    return {
        "kind": kind,
        "rollout_id": raw.get("rollout_id"),
        "frame_id": frame.get("frame_id"),
        "frame_index": frame.get("frame_index"),
        "reason_codes": sorted(set(reason_codes)),
        "source_frame_identity_sha256": frame.get("record_identity_sha256"),
        "source_rollout_identity_sha256": raw.get("record_identity_sha256"),
    }


def _actions_complete(actions: Any) -> bool:
    if not isinstance(actions, dict):
        return False
    return all(_action_variant_complete(actions.get(variant)) for variant in ACTION_VARIANTS)


def _action_variant_complete(action: Any) -> bool:
    """Accept observed values or explicitly sourced scripted derivations only."""

    if not isinstance(action, dict) or action.get("values") is None:
        return False
    state = action.get("state")
    if state == "observed":
        return True
    if state != "derived":
        return False
    provenance = action.get("provenance")
    values = action.get("values")
    return (
        isinstance(provenance, dict)
        and provenance.get("state") == "derived"
        and isinstance(provenance.get("derivation"), str)
        and bool(provenance["derivation"].strip())
        and action.get("ordered_joint_names") == list(JOINT_NAMES)
        and isinstance(values, list)
        and len(values) == len(JOINT_NAMES)
        and all(
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
            for value in values
        )
    )


def _nested_string(value: dict[str, Any], outer: str, inner: str) -> str:
    nested = value.get(outer)
    return _string(nested.get(inner) if isinstance(nested, dict) else None)


def _string(value: Any) -> str:
    return "" if value is None else str(value)


def _integer(value: Any) -> int:
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
