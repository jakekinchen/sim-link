"""Compile source-bound T18.3 exact-state component records.

This module projects only the phase, progress, and reward fields already
present in verified compiler rows.  It deliberately does not materialize a
training buffer or expose privileged outcome fields to an actor.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    require_finite_number,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.episode_first_window_sampling import (
    COMPILER_DIR,
    WINDOW_DIR,
    verify_episode_first_window_sample,
)
from scenesmith.robot_lab.experience_compiler import verify_compilation
from scenesmith.robot_lab.experience_records import REPO_ROOT
from scenesmith.robot_lab.experience_window_index import verify_window_index
from scenesmith.robot_lab.logical_source_cycle_buffers import (
    INITIAL_CYCLE_ID,
    verify_initial_buffer_registry,
)


SCHEMA_VERSION = "scenesmith.exact_state_components.v1"
TASK_ID = "T18.3"
CYCLE_REGISTRY_PATH = REPO_ROOT / "configurations/robot_lab/t18_2_logical_source_cycle_buffers.json"
SELECTION_PATH = REPO_ROOT / "configurations/robot_lab/t18_1_episode_first_window_sample.json"
COMPILER_MANIFEST_PATH = COMPILER_DIR / "compiler_manifest.json"
WINDOW_INDEX_PATH = WINDOW_DIR / "window_index.parquet"
ACTOR_INPUT_SCHEMA = (
    "observation.top_rgb",
    "observation.wrist_rgb",
    "observation.joint_position",
    "observation.joint_velocity",
)
PRIVILEGED_FIELD_NAMES = (
    "reward",
    "progress",
    "contact_geometry_witness",
    "strict_evaluator_result",
    "requested_gripper_pose",
    "achieved_gripper_pose",
    "aperture",
    "effort",
    "actions",
    "boundary_events",
)
_FALSE_AUTHORITY_FIELDS = (
    "buffer_materialized",
    "buffer_mutated",
    "dataset_mixture_frozen",
    "model_loaded",
    "model_inference_executed",
    "optimizer_training",
    "training_eligible",
    "simulation_training_ready",
    "physical_actuation",
    "raw_bytes_rewritten",
    "external_compute_started",
    "brev_compute_started",
)


def build_exact_state_components() -> dict[str, Any]:
    """Build the deterministic, source-bound T18.3 component manifest."""

    registry = load_strict_json(CYCLE_REGISTRY_PATH)
    selection = load_strict_json(SELECTION_PATH)
    verify_initial_buffer_registry(registry)
    verify_episode_first_window_sample(selection)
    verify_compilation(COMPILER_DIR)
    verify_window_index(WINDOW_DIR, COMPILER_DIR)

    compiler_manifest = load_strict_json(COMPILER_MANIFEST_PATH)
    compiler_manifest_identity = _sha256(compiler_manifest)
    cycle = _initial_cycle(registry, selection)
    selection_by_window = _selection_by_window(selection)
    window_rows = _unique_map(
        pq.read_table(WINDOW_INDEX_PATH).to_pylist(), "window_id", label="source window"
    )
    frame_rows = _unique_map(
        pq.read_table(COMPILER_DIR / "frames.parquet").to_pylist(),
        "frame_id",
        label="compiler frame",
    )

    bindings: list[dict[str, Any]] = []
    component_records: list[dict[str, Any]] = []
    records_by_frame: dict[str, dict[str, Any]] = {}
    for cycle_position, window_id in enumerate(cycle["window_ids"], start=1):
        selection_row = selection_by_window[window_id]
        window = window_rows.get(window_id)
        if window is None:
            raise ValueError("Logical cycle references an absent source window")
        frame_ids = _validated_window_frame_ids(window, selection_row)
        records: list[dict[str, str]] = []
        for frame_id in frame_ids:
            frame = frame_rows.get(frame_id)
            if frame is None:
                raise ValueError("Source window references an absent compiler frame")
            _validate_window_frame(frame, window=window, selection=selection_row)
            record = records_by_frame.get(frame_id)
            if record is None:
                record = _component_record(
                    frame, compiler_manifest_identity=compiler_manifest_identity
                )
                records_by_frame[frame_id] = record
                component_records.append(record)
            records.append(
                {
                    "frame_id": frame_id,
                    "frame_record_identity_sha256": record["frame_record_identity_sha256"],
                    "component_record_id": record["component_record_id"],
                }
            )
        bindings.append(
            {
                "cycle_id": cycle["cycle_id"],
                "cycle_position": cycle_position,
                "window_id": window_id,
                "rollout_id": selection_row["rollout_id"],
                "segment_id": selection_row["segment_id"],
                "task_phase": selection_row["task_phase"],
                "horizon": selection_row["horizon"],
                "frame_ids_sha256": _sha256(frame_ids),
                "frames": records,
            }
        )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "component_scope": "exact_source_phase_progress_reward_projection_for_immutable_logical_cycle",
        "source_cycle_registry_path": _repo_relative(CYCLE_REGISTRY_PATH),
        "source_cycle_registry_file_sha256": _sha256_file(CYCLE_REGISTRY_PATH),
        "source_cycle_registry_identity_sha256": registry["identity_sha256"],
        "source_selection_path": _repo_relative(SELECTION_PATH),
        "source_selection_file_sha256": _sha256_file(SELECTION_PATH),
        "source_selection_identity_sha256": selection["identity_sha256"],
        "source_compiler_manifest_path": _repo_relative(COMPILER_MANIFEST_PATH),
        "source_compiler_manifest_file_sha256": _sha256_file(COMPILER_MANIFEST_PATH),
        "source_compiler_manifest_identity_sha256": compiler_manifest_identity,
        "source_window_index_path": _repo_relative(WINDOW_INDEX_PATH),
        "source_window_index_file_sha256": _sha256_file(WINDOW_INDEX_PATH),
        "logical_cycle_id": cycle["cycle_id"],
        "logical_cycle_window_ids_sha256": cycle["window_ids_sha256"],
        "logical_cycle_window_count": len(cycle["window_ids"]),
        "unique_frame_count": len(component_records),
        "component_record_ids_sha256": _sha256(
            [record["component_record_id"] for record in component_records]
        ),
        "actor_input_schema": list(ACTOR_INPUT_SCHEMA),
        "actor_input_schema_sha256": _sha256(list(ACTOR_INPUT_SCHEMA)),
        "privileged_field_names": list(PRIVILEGED_FIELD_NAMES),
        "privileged_fields_available_to_actor": False,
        "window_frame_bindings": bindings,
        "component_records": component_records,
        **{field: False for field in _FALSE_AUTHORITY_FIELDS},
    }
    return sign_payload(payload)


def verify_exact_state_components(manifest: dict[str, Any]) -> None:
    """Fail closed on source, exact-state, privilege, or authority drift."""

    _verify_manifest_structure(manifest)
    expected = build_exact_state_components()
    if canonical_json_bytes(manifest) != canonical_json_bytes(expected):
        raise ValueError("Exact-state component manifest drifted from verified sources")


def _initial_cycle(registry: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    cycles = registry.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != 1:
        raise ValueError("T18.3 requires exactly one immutable logical source cycle")
    cycle = cycles[0]
    if not isinstance(cycle, dict) or cycle.get("cycle_id") != INITIAL_CYCLE_ID:
        raise ValueError("T18.3 source logical cycle identity drifted")
    ids = _require_sha_list(cycle.get("window_ids"), label="logical cycle window IDs")
    if cycle.get("window_ids_sha256") != _sha256(ids):
        raise ValueError("T18.3 source logical cycle digest drifted")
    selected_ids = _require_sha_list(
        [row.get("window_id") for row in selection.get("selected_windows", []) if isinstance(row, dict)],
        label="T18.1 selected window IDs",
    )
    if ids != selected_ids:
        raise ValueError("T18.3 logical cycle does not exactly bind the T18.1 selection")
    return cycle


def _selection_by_window(selection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = selection.get("selected_windows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("T18.3 selected windows are absent")
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("T18.3 selected window is invalid")
        window_id = _require_sha256(row.get("window_id"), label="selected window ID")
        if window_id in selected:
            raise ValueError("T18.3 selected windows contain a duplicate ID")
        for field in ("rollout_id", "segment_id", "source_class", "task_phase", "control_mode"):
            _require_text(row.get(field), label=f"selected window {field}")
        if not isinstance(row.get("horizon"), int) or isinstance(row["horizon"], bool):
            raise ValueError("Selected window horizon is invalid")
        _require_sha256(row.get("frame_ids_sha256"), label="selected window frame digest")
        selected[window_id] = row
    return selected


def _validated_window_frame_ids(window: dict[str, Any], selection: dict[str, Any]) -> list[str]:
    if window.get("rollout_id") != selection["rollout_id"] or window.get("segment_id") != selection["segment_id"]:
        raise ValueError("Logical cycle window identity drifted from selection")
    if window.get("horizon") != selection["horizon"] or window.get("window_frame_count") != selection["horizon"]:
        raise ValueError("Logical cycle window horizon drifted from selection")
    frame_ids = _parse_json_list(window.get("frame_ids_json"), label="source window frame IDs")
    if len(frame_ids) != selection["horizon"] or len(frame_ids) != len(set(frame_ids)):
        raise ValueError("Logical cycle window frame membership is invalid")
    if _sha256(frame_ids) != selection["frame_ids_sha256"]:
        raise ValueError("Logical cycle window frame digest drifted from selection")
    return frame_ids


def _validate_window_frame(
    frame: dict[str, Any], *, window: dict[str, Any], selection: dict[str, Any]
) -> None:
    if frame.get("frame_eligible") is not True or frame.get("action_variants_complete") is not True:
        raise ValueError("Exact-state component source frame is ineligible")
    if _parse_json(frame.get("quarantine_reason_codes_json"), label="frame quarantine") != []:
        raise ValueError("Exact-state component source frame is quarantined")
    if frame.get("rollout_id") != window.get("rollout_id"):
        raise ValueError("Exact-state component frame rollout identity drifted")
    if _require_text(frame.get("task_phase"), label="frame task phase") != selection["task_phase"]:
        raise ValueError("Exact-state component frame phase drifted from selected window")
    _require_text(frame.get("source_phase"), label="frame source phase")
    _require_sha256(frame.get("record_identity_sha256"), label="frame record identity")
    _require_sha256(frame.get("raw_rollout_record_identity_sha256"), label="raw rollout identity")


def _component_record(frame: dict[str, Any], *, compiler_manifest_identity: str) -> dict[str, Any]:
    actor_inputs = _parse_json_list(
        frame.get("actor_input_field_names_json"), label="frame actor input schema"
    )
    if actor_inputs != list(ACTOR_INPUT_SCHEMA):
        raise ValueError("Exact-state component actor input schema privilege drifted")
    reward = _validated_value_component(
        _parse_json(frame.get("reward_json"), label="frame reward"),
        label="reward",
        units="binary",
    )
    progress = _validated_value_component(
        _parse_json(frame.get("progress_json"), label="frame progress"),
        label="progress",
        units="unit_interval",
    )
    strict = _parse_json(frame.get("strict_evaluator_result_json"), label="strict evaluator result")
    _validate_strict_evaluator(strict)
    reward_value = reward["source_value"]["value"]
    expected_reward = 1.0 if strict["valid"] else 0.0
    if reward_value != expected_reward:
        raise ValueError("Exact-state reward does not equal the strict evaluator result")
    progress_value = progress["source_value"]["value"]
    if not 0.0 <= progress_value <= 1.0:
        raise ValueError("Exact-state progress is outside the source ordinal interval")

    frame_id = _require_text(frame.get("frame_id"), label="frame ID")
    source = {
        "frame_id": frame_id,
        "frame_record_identity_sha256": frame["record_identity_sha256"],
        "raw_rollout_record_identity_sha256": frame["raw_rollout_record_identity_sha256"],
        "compiler_frame_pointer": f"/compiler_frames/{frame_id}",
        "compiler_manifest_identity_sha256": compiler_manifest_identity,
    }
    record = {
        "frame_id": frame_id,
        "frame_record_identity_sha256": frame["record_identity_sha256"],
        "rollout_id": _require_text(frame.get("rollout_id"), label="frame rollout ID"),
        "frame_index": _require_nonnegative_int(frame.get("frame_index"), label="frame index"),
        "timestamp_ns": _require_nonnegative_int(frame.get("timestamp_ns"), label="frame timestamp"),
        "source": source,
        "phase": {
            "task_phase": _phase_component(
                _require_text(frame.get("task_phase"), label="frame task phase"),
                source=source,
                source_pointer=f"{source['compiler_frame_pointer']}/task_phase",
            ),
            "source_phase": _phase_component(
                _require_text(frame.get("source_phase"), label="frame source phase"),
                source=source,
                source_pointer=f"{source['compiler_frame_pointer']}/source_phase",
            ),
        },
        "progress": {
            **progress,
            "exact_state_predicate": {
                "name": "sourced_derived_progress_unit_interval_v1",
                "components": ["source_phase_ordinal"],
                "value_in_unit_interval": True,
                "satisfied": True,
            },
        },
        "reward": {
            **reward,
            "exact_state_predicate": {
                "name": "strict_evaluator_binary_reward_projection_v1",
                "strict_evaluator": strict["evaluator"],
                "strict_evaluator_valid": strict["valid"],
                "expected_value": expected_reward,
                "satisfied": True,
            },
        },
        "actor_input_schema": actor_inputs,
        "actor_input_schema_sha256": _sha256(actor_inputs),
        "privileged_field_names": list(PRIVILEGED_FIELD_NAMES),
        "privileged_fields_available_to_actor": False,
    }
    record["component_record_id"] = _sha256(record)
    return record


def _phase_component(value: str, *, source: dict[str, Any], source_pointer: str) -> dict[str, Any]:
    return {
        "value": value,
        "availability_state": "observed",
        "units": "categorical",
        "source": deepcopy(source),
        "source_pointer": source_pointer,
        "exact_state_predicate": {
            "name": "compiler_phase_exact_projection_v1",
            "source_pointer_nonblank": True,
            "satisfied": True,
        },
    }


def _validated_value_component(value: Any, *, label: str, units: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Exact-state {label} value is invalid")
    availability = value.get("state")
    if availability not in {"observed", "derived"}:
        raise ValueError(f"Exact-state {label} availability state is invalid")
    number = require_finite_number(value.get("value"), label=f"exact-state {label} value")
    components = value.get("components")
    if not isinstance(components, list) or not components or any(
        not isinstance(component, str) or not component for component in components
    ):
        raise ValueError(f"Exact-state {label} components are invalid")
    provenance = value.get("provenance")
    _validate_provenance(provenance, label=label)
    return {
        "source_value": deepcopy(value),
        "availability_state": availability,
        "units": units,
        "source_pointer": provenance["source_pointer"],
        "source_provenance": deepcopy(provenance),
        "source_value_sha256": _sha256(value),
    }


def _validate_strict_evaluator(value: Any) -> None:
    if not isinstance(value, dict) or not isinstance(value.get("valid"), bool):
        raise ValueError("Exact-state strict evaluator result is invalid")
    _require_text(value.get("evaluator"), label="strict evaluator name")
    _validate_provenance(value.get("provenance"), label="strict evaluator")


def _validate_provenance(value: Any, *, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"Exact-state {label} provenance is absent")
    if value.get("state") not in {"observed", "derived"}:
        raise ValueError(f"Exact-state {label} provenance state is invalid")
    _require_text(value.get("source_pointer"), label=f"exact-state {label} source pointer")
    source_ref = value.get("source_ref")
    if not isinstance(source_ref, dict):
        raise ValueError(f"Exact-state {label} provenance source ref is absent")
    _require_text(source_ref.get("path"), label=f"exact-state {label} source ref path")
    _require_text(source_ref.get("schema_version"), label=f"exact-state {label} source ref schema")
    _require_sha256(source_ref.get("identity_sha256"), label=f"exact-state {label} source ref identity")
    _require_sha256(source_ref.get("file_sha256"), label=f"exact-state {label} source ref file hash")


def _verify_manifest_structure(manifest: dict[str, Any]) -> None:
    verify_signed_payload(manifest, label="exact-state component manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("task_id") != TASK_ID:
        raise ValueError("Exact-state component manifest schema or task identity drifted")
    for field in _FALSE_AUTHORITY_FIELDS:
        if manifest.get(field) is not False:
            raise ValueError(f"Exact-state component authority flag drifted: {field}")
    if manifest.get("actor_input_schema") != list(ACTOR_INPUT_SCHEMA):
        raise ValueError("Exact-state manifest actor input schema privilege drifted")
    if manifest.get("privileged_fields_available_to_actor") is not False:
        raise ValueError("Exact-state manifest exposes privileged fields to an actor")
    if manifest.get("privileged_field_names") != list(PRIVILEGED_FIELD_NAMES):
        raise ValueError("Exact-state manifest privileged field list drifted")
    for path_field, hash_field in (
        ("source_cycle_registry_path", "source_cycle_registry_file_sha256"),
        ("source_selection_path", "source_selection_file_sha256"),
        ("source_compiler_manifest_path", "source_compiler_manifest_file_sha256"),
        ("source_window_index_path", "source_window_index_file_sha256"),
    ):
        path = _absolute_repo_path(manifest.get(path_field), label=path_field)
        if manifest.get(hash_field) != _sha256_file(path):
            raise ValueError(f"Exact-state manifest source hash drifted: {hash_field}")
    records = manifest.get("component_records")
    if not isinstance(records, list) or not records:
        raise ValueError("Exact-state component records are absent")
    frame_ids: set[str] = set()
    record_ids: set[str] = set()
    by_frame: dict[str, dict[str, Any]] = {}
    for record in records:
        _validate_component_record(record)
        frame_id = record["frame_id"]
        record_id = record["component_record_id"]
        if frame_id in frame_ids or record_id in record_ids:
            raise ValueError("Exact-state component records contain a duplicate frame")
        frame_ids.add(frame_id)
        record_ids.add(record_id)
        by_frame[frame_id] = record
    if manifest.get("unique_frame_count") != len(records):
        raise ValueError("Exact-state unique frame count drifted")
    if manifest.get("component_record_ids_sha256") != _sha256(
        [record["component_record_id"] for record in records]
    ):
        raise ValueError("Exact-state component record digest drifted")
    _validate_bindings(manifest, by_frame=by_frame)


def _validate_component_record(record: Any) -> None:
    if not isinstance(record, dict):
        raise ValueError("Exact-state component record is invalid")
    component_id = _require_sha256(record.get("component_record_id"), label="component record ID")
    unsigned = {key: value for key, value in record.items() if key != "component_record_id"}
    if component_id != _sha256(unsigned):
        raise ValueError("Exact-state component record identity drifted")
    frame_id = _require_text(record.get("frame_id"), label="component frame ID")
    _require_sha256(record.get("frame_record_identity_sha256"), label="component frame identity")
    source = record.get("source")
    if not isinstance(source, dict) or source.get("frame_id") != frame_id:
        raise ValueError("Exact-state component source frame binding drifted")
    if source.get("frame_record_identity_sha256") != record.get("frame_record_identity_sha256"):
        raise ValueError("Exact-state component source identity drifted")
    _require_sha256(source.get("raw_rollout_record_identity_sha256"), label="component raw rollout identity")
    _require_sha256(source.get("compiler_manifest_identity_sha256"), label="component compiler identity")
    _require_text(source.get("compiler_frame_pointer"), label="component compiler frame pointer")
    for phase_name in ("task_phase", "source_phase"):
        phase = record.get("phase", {}).get(phase_name) if isinstance(record.get("phase"), dict) else None
        if not isinstance(phase, dict) or _require_text(phase.get("value"), label=f"component {phase_name}") is None:
            raise ValueError("Exact-state phase component is invalid")
        if phase.get("availability_state") != "observed" or phase.get("units") != "categorical":
            raise ValueError("Exact-state phase component availability or units drifted")
        if phase.get("source") != source or not isinstance(phase.get("exact_state_predicate"), dict):
            raise ValueError("Exact-state phase component provenance drifted")
    for name in ("progress", "reward"):
        component = record.get(name)
        if not isinstance(component, dict):
            raise ValueError(f"Exact-state {name} component is absent")
        _validated_value_component(component.get("source_value"), label=name, units=component.get("units"))
        if component.get("availability_state") != component["source_value"].get("state"):
            raise ValueError(f"Exact-state {name} availability drifted")
        if component.get("source_value_sha256") != _sha256(component["source_value"]):
            raise ValueError(f"Exact-state {name} source value digest drifted")
        if component.get("source_pointer") != component["source_value"].get("provenance", {}).get("source_pointer"):
            raise ValueError(f"Exact-state {name} source pointer drifted")
        if component.get("source_provenance") != component["source_value"].get("provenance"):
            raise ValueError(f"Exact-state {name} source provenance drifted")
        if not isinstance(component.get("exact_state_predicate"), dict) or component["exact_state_predicate"].get("satisfied") is not True:
            raise ValueError(f"Exact-state {name} predicate drifted")
    reward_predicate = record["reward"]["exact_state_predicate"]
    if record["reward"]["source_value"]["value"] != reward_predicate.get("expected_value"):
        raise ValueError("Exact-state reward predicate drifted")
    if record.get("actor_input_schema") != list(ACTOR_INPUT_SCHEMA):
        raise ValueError("Exact-state component actor input privilege drifted")
    if record.get("actor_input_schema_sha256") != _sha256(list(ACTOR_INPUT_SCHEMA)):
        raise ValueError("Exact-state component actor input digest drifted")
    if record.get("privileged_field_names") != list(PRIVILEGED_FIELD_NAMES):
        raise ValueError("Exact-state component privileged field list drifted")
    if record.get("privileged_fields_available_to_actor") is not False:
        raise ValueError("Exact-state component exposes privileged fields to an actor")


def _validate_bindings(manifest: dict[str, Any], *, by_frame: dict[str, dict[str, Any]]) -> None:
    bindings = manifest.get("window_frame_bindings")
    if not isinstance(bindings, list) or not bindings:
        raise ValueError("Exact-state window-frame bindings are absent")
    window_ids: list[str] = []
    for position, binding in enumerate(bindings, start=1):
        if not isinstance(binding, dict) or binding.get("cycle_id") != INITIAL_CYCLE_ID:
            raise ValueError("Exact-state window-frame binding cycle drifted")
        if binding.get("cycle_position") != position:
            raise ValueError("Exact-state window-frame binding order drifted")
        window_id = _require_sha256(binding.get("window_id"), label="binding window ID")
        if window_id in window_ids:
            raise ValueError("Exact-state window-frame bindings contain a duplicate window")
        window_ids.append(window_id)
        frames = binding.get("frames")
        if not isinstance(frames, list) or len(frames) != binding.get("horizon"):
            raise ValueError("Exact-state window-frame binding count drifted")
        frame_ids = []
        for frame in frames:
            if not isinstance(frame, dict):
                raise ValueError("Exact-state bound frame is invalid")
            frame_id = _require_text(frame.get("frame_id"), label="bound frame ID")
            component = by_frame.get(frame_id)
            if component is None or frame.get("component_record_id") != component.get("component_record_id"):
                raise ValueError("Exact-state bound frame component reference drifted")
            if frame.get("frame_record_identity_sha256") != component.get("frame_record_identity_sha256"):
                raise ValueError("Exact-state bound frame identity drifted")
            frame_ids.append(frame_id)
        if len(frame_ids) != len(set(frame_ids)) or binding.get("frame_ids_sha256") != _sha256(frame_ids):
            raise ValueError("Exact-state bound frame digest drifted")
    if manifest.get("logical_cycle_window_count") != len(bindings):
        raise ValueError("Exact-state logical cycle window count drifted")
    if manifest.get("logical_cycle_window_ids_sha256") != _sha256(window_ids):
        raise ValueError("Exact-state logical cycle window digest drifted")


def _unique_map(rows: list[dict[str, Any]], field: str, *, label: str) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{label} is invalid")
        identifier = _require_text(row.get(field), label=f"{label} {field}")
        if identifier in values:
            raise ValueError(f"Duplicate {label} {field}")
        values[identifier] = row
    return values


def _parse_json(value: Any, *, label: str) -> Any:
    if not isinstance(value, str):
        raise ValueError(f"{label} JSON is invalid")
    try:
        return json.loads(value, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} JSON is invalid") from error


def _parse_json_list(value: Any, *, label: str) -> list[str]:
    parsed = _parse_json(value, label=label)
    if not isinstance(parsed, list):
        raise ValueError(f"{label} must be a JSON list")
    return [_require_text(item, label=label) for item in parsed]


def _require_sha_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} are required")
    ids = [_require_sha256(item, label=label) for item in value]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} contain duplicates")
    return ids


def _require_text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank")
    return value.strip()


def _require_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        char not in "0123456789abcdef" for char in value
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return value


def _require_nonnegative_int(value: Any, *, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError as error:
        raise ValueError("Exact-state source must remain inside this checkout") from error


def _absolute_repo_path(value: Any, *, label: str) -> Path:
    relative = _require_text(value, label=label)
    path = (REPO_ROOT / relative).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError as error:
        raise ValueError(f"Exact-state source escapes checkout: {label}") from error
    if not path.is_file():
        raise ValueError(f"Exact-state source is absent: {label}")
    return path


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
