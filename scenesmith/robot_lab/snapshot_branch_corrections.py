"""Immutable T18.4 snapshots and branch-and-correct event mechanics.

The current source cycle contains scripted expert rollouts, not correction
episodes. Its tracked manifest therefore contains only source snapshots and
zero correction events. Event construction is a fail-closed mechanism that is
exercised only with explicitly fixture-only records until source evidence exists.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.exact_state_components import (
    CYCLE_REGISTRY_PATH,
    REPO_ROOT,
    _sha256_file,
    verify_exact_state_components,
)
from scenesmith.robot_lab.logical_source_cycle_buffers import verify_initial_buffer_registry


SCHEMA_VERSION = "scenesmith.snapshot_branch_corrections.v1"
TASK_ID = "T18.4"
EXACT_STATE_PATH = REPO_ROOT / "configurations/robot_lab/t18_3_exact_state_components.json"
ALLOWED_EVENT_EVIDENCE_CLASSES = {"fixture_only"}
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


def build_snapshot_branch_manifest() -> dict[str, Any]:
    """Build a source-bound, correction-free snapshot manifest for cycle 0001."""

    exact_state = load_strict_json(EXACT_STATE_PATH)
    registry = load_strict_json(CYCLE_REGISTRY_PATH)
    verify_exact_state_components(exact_state)
    verify_initial_buffer_registry(registry)
    _verify_exact_cycle_binding(exact_state, registry)

    components = _component_map(exact_state)
    snapshots: list[dict[str, Any]] = []
    base_branches: list[dict[str, Any]] = []
    for binding in exact_state["window_frame_bindings"]:
        snapshot = _snapshot_from_binding(binding, components=components)
        snapshots.append(snapshot)
        base_branches.append(_base_branch(snapshot))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "manifest_scope": "immutable_source_snapshots_and_branch_contract_without_correction_evidence",
        "source_exact_state_path": _repo_relative(EXACT_STATE_PATH),
        "source_exact_state_file_sha256": _sha256_file(EXACT_STATE_PATH),
        "source_exact_state_identity_sha256": exact_state["identity_sha256"],
        "source_cycle_registry_path": _repo_relative(CYCLE_REGISTRY_PATH),
        "source_cycle_registry_file_sha256": _sha256_file(CYCLE_REGISTRY_PATH),
        "source_cycle_registry_identity_sha256": registry["identity_sha256"],
        "logical_cycle_id": exact_state["logical_cycle_id"],
        "logical_cycle_window_ids_sha256": exact_state["logical_cycle_window_ids_sha256"],
        "logical_cycle_window_count": exact_state["logical_cycle_window_count"],
        "snapshot_count": len(snapshots),
        "snapshot_ids_sha256": _sha256([snapshot["snapshot_id"] for snapshot in snapshots]),
        "base_branch_count": len(base_branches),
        "base_branch_ids_sha256": _sha256([branch["branch_id"] for branch in base_branches]),
        "source_correction_evidence_present": False,
        "fixture_events_included": False,
        "correction_event_count": 0,
        "correction_event_ids_sha256": _sha256([]),
        "snapshots": snapshots,
        "base_branches": base_branches,
        "correction_events": [],
        **{field: False for field in _FALSE_AUTHORITY_FIELDS},
    }
    return sign_payload(payload)


def verify_snapshot_branch_manifest(manifest: dict[str, Any]) -> None:
    """Fail closed on source, snapshot, branch, correction, or authority drift."""

    _verify_manifest_structure(manifest)
    expected = build_snapshot_branch_manifest()
    if canonical_json_bytes(manifest) != canonical_json_bytes(expected):
        raise ValueError("Snapshot branch manifest drifted from verified sources")


def restore_snapshot(manifest: dict[str, Any], snapshot_id: str) -> dict[str, Any]:
    """Return the exact immutable identity sequence captured for one snapshot."""

    _verify_manifest_structure(manifest)
    snapshot_id = _require_sha256(snapshot_id, label="snapshot ID")
    snapshots = {snapshot["snapshot_id"]: snapshot for snapshot in manifest["snapshots"]}
    snapshot = snapshots.get(snapshot_id)
    if snapshot is None:
        raise ValueError("Snapshot is absent from the immutable manifest")
    return {
        "logical_cycle_id": snapshot["logical_cycle_id"],
        "window_id": snapshot["window_id"],
        "cycle_position": snapshot["cycle_position"],
        "frame_ids": [frame["frame_id"] for frame in snapshot["frames"]],
        "component_record_ids": [frame["component_record_id"] for frame in snapshot["frames"]],
        "frame_record_identity_sha256s": [
            frame["frame_record_identity_sha256"] for frame in snapshot["frames"]
        ],
    }


def build_correction_event(
    snapshots: list[dict[str, Any]],
    *,
    failure_snapshot_id: str,
    correction_snapshot_id: str,
    evidence_class: str,
) -> dict[str, Any]:
    """Build one immutable event linking distinct failure/correction branches.

    This function does not modify a manifest. T18.4 permits only fixture-only
    event construction; a later reviewed task must add a source-specific
    correction-evidence contract before any source-bound event is possible.
    """

    snapshots_by_id = _validate_snapshots(snapshots)
    evidence_class = _require_event_evidence_class(evidence_class)
    failure_snapshot = snapshots_by_id.get(_require_sha256(failure_snapshot_id, label="failure snapshot ID"))
    correction_snapshot = snapshots_by_id.get(
        _require_sha256(correction_snapshot_id, label="correction snapshot ID")
    )
    if failure_snapshot is None or correction_snapshot is None:
        raise ValueError("Correction event references an absent snapshot")
    if failure_snapshot["snapshot_id"] == correction_snapshot["snapshot_id"]:
        raise ValueError("Correction event must use distinct failure and correction snapshots")
    event = {
        "evidence_class": evidence_class,
        "failure_branch": _event_branch("failure", failure_snapshot, evidence_class=evidence_class),
        "correction_branch": _event_branch(
            "correction", correction_snapshot, evidence_class=evidence_class
        ),
    }
    event["correction_event_id"] = _sha256(event)
    validate_correction_event(event, snapshots=snapshots)
    return event


def validate_correction_event(event: dict[str, Any], *, snapshots: list[dict[str, Any]]) -> None:
    """Validate one immutable correction event against registered snapshots."""

    if not isinstance(event, dict):
        raise ValueError("Correction event is invalid")
    evidence_class = _require_event_evidence_class(event.get("evidence_class"))
    snapshots_by_id = _validate_snapshots(snapshots)
    event_id = _require_sha256(event.get("correction_event_id"), label="correction event ID")
    unsigned = {key: value for key, value in event.items() if key != "correction_event_id"}
    if event_id != _sha256(unsigned):
        raise ValueError("Correction event identity drifted")
    failure = _validate_event_branch(event.get("failure_branch"), role="failure", snapshots=snapshots_by_id)
    correction = _validate_event_branch(
        event.get("correction_branch"), role="correction", snapshots=snapshots_by_id
    )
    if failure["branch_id"] == correction["branch_id"]:
        raise ValueError("Correction event reuses one branch for failure and correction")
    if failure["snapshot_id"] == correction["snapshot_id"]:
        raise ValueError("Correction event reuses one snapshot for failure and correction")
    for branch in (failure, correction):
        if branch["outcome_class"].startswith("fixture_") is not True:
            raise ValueError("Fixture correction event outcome class drifted")


def validate_correction_events(events: list[dict[str, Any]], *, snapshots: list[dict[str, Any]]) -> None:
    """Reject duplicate event IDs or reuse of an immutable branch across events."""

    if not isinstance(events, list):
        raise ValueError("Correction event list is invalid")
    event_ids: set[str] = set()
    branch_ids: set[str] = set()
    for event in events:
        validate_correction_event(event, snapshots=snapshots)
        event_id = event["correction_event_id"]
        if event_id in event_ids:
            raise ValueError("Correction event list contains a reused event ID")
        event_ids.add(event_id)
        for branch_name in ("failure_branch", "correction_branch"):
            branch_id = event[branch_name]["branch_id"]
            if branch_id in branch_ids:
                raise ValueError("Correction event list reuses an immutable branch")
            branch_ids.add(branch_id)


def _verify_exact_cycle_binding(exact_state: dict[str, Any], registry: dict[str, Any]) -> None:
    cycles = registry.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != 1 or not isinstance(cycles[0], dict):
        raise ValueError("Snapshot source registry must contain exactly one logical cycle")
    cycle = cycles[0]
    if cycle.get("cycle_id") != exact_state.get("logical_cycle_id"):
        raise ValueError("Snapshot source cycle identity drifted")
    if cycle.get("window_ids_sha256") != exact_state.get("logical_cycle_window_ids_sha256"):
        raise ValueError("Snapshot source cycle window digest drifted")
    if cycle.get("window_count") != exact_state.get("logical_cycle_window_count"):
        raise ValueError("Snapshot source cycle window count drifted")


def _component_map(exact_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = exact_state.get("component_records")
    if not isinstance(records, list) or not records:
        raise ValueError("Exact-state component records are absent")
    values: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Exact-state component record is invalid")
        record_id = _require_sha256(record.get("component_record_id"), label="component record ID")
        if record_id in values:
            raise ValueError("Exact-state component record IDs are duplicated")
        values[record_id] = record
    return values


def _snapshot_from_binding(
    binding: dict[str, Any], *, components: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    if not isinstance(binding, dict):
        raise ValueError("Exact-state window-frame binding is invalid")
    cycle_id = _require_text(binding.get("cycle_id"), label="binding cycle ID")
    window_id = _require_sha256(binding.get("window_id"), label="binding window ID")
    position = _require_positive_int(binding.get("cycle_position"), label="binding cycle position")
    frames = binding.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("Exact-state binding frames are absent")
    snapshot_frames: list[dict[str, str]] = []
    frame_ids: list[str] = []
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError("Exact-state bound frame is invalid")
        frame_id = _require_text(frame.get("frame_id"), label="bound frame ID")
        component_id = _require_sha256(frame.get("component_record_id"), label="bound component ID")
        component = components.get(component_id)
        if component is None or component.get("frame_id") != frame_id:
            raise ValueError("Snapshot binding component does not match frame")
        frame_identity = _require_sha256(
            frame.get("frame_record_identity_sha256"), label="bound frame identity"
        )
        if component.get("frame_record_identity_sha256") != frame_identity:
            raise ValueError("Snapshot binding frame identity drifted")
        frame_ids.append(frame_id)
        snapshot_frames.append(
            {
                "frame_id": frame_id,
                "component_record_id": component_id,
                "frame_record_identity_sha256": frame_identity,
            }
        )
    if len(frame_ids) != len(set(frame_ids)):
        raise ValueError("Snapshot binding repeats a frame")
    if binding.get("frame_ids_sha256") != _sha256(frame_ids):
        raise ValueError("Snapshot binding frame digest drifted")
    snapshot = {
        "logical_cycle_id": cycle_id,
        "cycle_position": position,
        "window_id": window_id,
        "frame_ids_sha256": _sha256(frame_ids),
        "component_record_ids_sha256": _sha256(
            [frame["component_record_id"] for frame in snapshot_frames]
        ),
        "frame_record_identity_sha256s": [
            frame["frame_record_identity_sha256"] for frame in snapshot_frames
        ],
        "immutable": True,
        "frames": snapshot_frames,
    }
    snapshot["snapshot_id"] = _sha256(snapshot)
    return snapshot


def _base_branch(snapshot: dict[str, Any]) -> dict[str, Any]:
    branch = {
        "branch_role": "source_base",
        "snapshot_id": snapshot["snapshot_id"],
        "window_id": snapshot["window_id"],
        "immutable": True,
    }
    branch["branch_id"] = _sha256(branch)
    return branch


def _event_branch(
    role: str, snapshot: dict[str, Any], *, evidence_class: str
) -> dict[str, Any]:
    if role not in {"failure", "correction"}:
        raise ValueError("Correction event branch role is invalid")
    branch = {
        "branch_role": role,
        "snapshot_id": snapshot["snapshot_id"],
        "window_id": snapshot["window_id"],
        "immutable": True,
        "outcome_class": f"{evidence_class}_{role}",
    }
    branch["branch_id"] = _sha256(branch)
    return branch


def _verify_manifest_structure(manifest: dict[str, Any]) -> None:
    verify_signed_payload(manifest, label="snapshot branch manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("task_id") != TASK_ID:
        raise ValueError("Snapshot branch manifest schema or task identity drifted")
    for field in _FALSE_AUTHORITY_FIELDS:
        if manifest.get(field) is not False:
            raise ValueError(f"Snapshot branch authority flag drifted: {field}")
    if manifest.get("source_correction_evidence_present") is not False:
        raise ValueError("Snapshot branch manifest invents correction evidence")
    if manifest.get("fixture_events_included") is not False:
        raise ValueError("Snapshot branch manifest mixes fixture events into source evidence")
    if manifest.get("correction_events") != [] or manifest.get("correction_event_count") != 0:
        raise ValueError("Snapshot branch source manifest must contain zero correction events")
    if manifest.get("correction_event_ids_sha256") != _sha256([]):
        raise ValueError("Snapshot branch correction event digest drifted")
    for path_field, hash_field in (
        ("source_exact_state_path", "source_exact_state_file_sha256"),
        ("source_cycle_registry_path", "source_cycle_registry_file_sha256"),
    ):
        path = _absolute_repo_path(manifest.get(path_field), label=path_field)
        if manifest.get(hash_field) != _sha256_file(path):
            raise ValueError(f"Snapshot branch source hash drifted: {hash_field}")
    snapshots = _validate_snapshots(manifest.get("snapshots"))
    if manifest.get("snapshot_count") != len(snapshots):
        raise ValueError("Snapshot branch snapshot count drifted")
    snapshot_ids = [snapshot["snapshot_id"] for snapshot in manifest["snapshots"]]
    if manifest.get("snapshot_ids_sha256") != _sha256(snapshot_ids):
        raise ValueError("Snapshot branch snapshot digest drifted")
    branches = manifest.get("base_branches")
    if not isinstance(branches, list) or len(branches) != len(snapshots):
        raise ValueError("Snapshot branch base branches are incomplete")
    branch_ids: list[str] = []
    seen_snapshot_ids: set[str] = set()
    for branch in branches:
        if not isinstance(branch, dict):
            raise ValueError("Snapshot base branch is invalid")
        if branch.get("branch_role") != "source_base" or branch.get("immutable") is not True:
            raise ValueError("Snapshot base branch semantics drifted")
        snapshot_id = _require_sha256(branch.get("snapshot_id"), label="base branch snapshot ID")
        snapshot = snapshots.get(snapshot_id)
        if snapshot is None or branch.get("window_id") != snapshot.get("window_id"):
            raise ValueError("Snapshot base branch source binding drifted")
        branch_id = _require_sha256(branch.get("branch_id"), label="base branch ID")
        unsigned = {key: value for key, value in branch.items() if key != "branch_id"}
        if branch_id != _sha256(unsigned):
            raise ValueError("Snapshot base branch identity drifted")
        if branch_id in branch_ids or snapshot_id in seen_snapshot_ids:
            raise ValueError("Snapshot base branch is duplicated")
        branch_ids.append(branch_id)
        seen_snapshot_ids.add(snapshot_id)
    if manifest.get("base_branch_count") != len(branches):
        raise ValueError("Snapshot branch base branch count drifted")
    if manifest.get("base_branch_ids_sha256") != _sha256(branch_ids):
        raise ValueError("Snapshot branch base branch digest drifted")


def _validate_snapshots(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("Snapshots are absent")
    snapshots: dict[str, dict[str, Any]] = {}
    prior_position = 0
    for snapshot in value:
        if not isinstance(snapshot, dict):
            raise ValueError("Snapshot is invalid")
        snapshot_id = _require_sha256(snapshot.get("snapshot_id"), label="snapshot ID")
        unsigned = {key: item for key, item in snapshot.items() if key != "snapshot_id"}
        if snapshot_id != _sha256(unsigned):
            raise ValueError("Snapshot identity drifted")
        if snapshot_id in snapshots:
            raise ValueError("Snapshots contain a duplicate ID")
        position = _require_positive_int(snapshot.get("cycle_position"), label="snapshot cycle position")
        if position != prior_position + 1:
            raise ValueError("Snapshots are not in immutable logical-cycle order")
        prior_position = position
        _require_text(snapshot.get("logical_cycle_id"), label="snapshot logical cycle ID")
        _require_sha256(snapshot.get("window_id"), label="snapshot window ID")
        if snapshot.get("immutable") is not True:
            raise ValueError("Snapshot immutability drifted")
        frames = snapshot.get("frames")
        if not isinstance(frames, list) or not frames:
            raise ValueError("Snapshot frames are absent")
        frame_ids: list[str] = []
        component_ids: list[str] = []
        identities: list[str] = []
        for frame in frames:
            if not isinstance(frame, dict):
                raise ValueError("Snapshot frame is invalid")
            frame_ids.append(_require_text(frame.get("frame_id"), label="snapshot frame ID"))
            component_ids.append(
                _require_sha256(frame.get("component_record_id"), label="snapshot component ID")
            )
            identities.append(
                _require_sha256(
                    frame.get("frame_record_identity_sha256"), label="snapshot frame identity"
                )
            )
        if len(frame_ids) != len(set(frame_ids)):
            raise ValueError("Snapshot repeats a frame")
        if snapshot.get("frame_ids_sha256") != _sha256(frame_ids):
            raise ValueError("Snapshot frame digest drifted")
        if snapshot.get("component_record_ids_sha256") != _sha256(component_ids):
            raise ValueError("Snapshot component digest drifted")
        if snapshot.get("frame_record_identity_sha256s") != identities:
            raise ValueError("Snapshot frame identity sequence drifted")
        snapshots[snapshot_id] = snapshot
    return snapshots


def _validate_event_branch(
    branch: Any, *, role: str, snapshots: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    if not isinstance(branch, dict) or branch.get("branch_role") != role:
        raise ValueError("Correction event branch role drifted")
    if branch.get("immutable") is not True:
        raise ValueError("Correction event branch immutability drifted")
    snapshot_id = _require_sha256(branch.get("snapshot_id"), label="event branch snapshot ID")
    snapshot = snapshots.get(snapshot_id)
    if snapshot is None or branch.get("window_id") != snapshot.get("window_id"):
        raise ValueError("Correction event branch snapshot binding drifted")
    _require_text(branch.get("outcome_class"), label="event branch outcome class")
    branch_id = _require_sha256(branch.get("branch_id"), label="event branch ID")
    unsigned = {key: value for key, value in branch.items() if key != "branch_id"}
    if branch_id != _sha256(unsigned):
        raise ValueError("Correction event branch identity drifted")
    return branch


def _require_event_evidence_class(value: Any) -> str:
    if value not in ALLOWED_EVENT_EVIDENCE_CLASSES:
        raise ValueError("Correction event evidence class is invalid")
    return value


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


def _require_positive_int(value: Any, *, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError as error:
        raise ValueError("Snapshot source must remain inside this checkout") from error


def _absolute_repo_path(value: Any, *, label: str) -> Path:
    relative = _require_text(value, label=label)
    path = (REPO_ROOT / relative).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError as error:
        raise ValueError(f"Snapshot source escapes checkout: {label}") from error
    if not path.is_file():
        raise ValueError(f"Snapshot source is absent: {label}")
    return path


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
