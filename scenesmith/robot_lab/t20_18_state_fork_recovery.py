"""Fail-closed T20.18 policy-visited MuJoCo state-fork evidence contract."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)


SCHEMA_VERSION = "scenesmith.t20_18_state_fork_recovery.v1"
TASK_ID = "T20.18"
INTEGRATION_STATE_SPEC = 8191
PHASE_ROLES = ("approach", "grasp", "hold", "release")
_ROLE_PHASE = {
    "approach": "approach",
    "grasp": "close",
    "hold": "grasp_hold",
    "release": "release",
}
_FALSE_AUTHORITY_FIELDS = (
    "optimizer_training",
    "dataset_mixture_frozen",
    "simulation_training_ready",
    "simulation_policy_accepted",
    "physical_transfer_ready",
    "promotion_eligible",
    "physical_actuation",
    "external_compute_started",
    "brev_compute_started",
)


def capture_integration_state(
    mujoco: Any,
    model: Any,
    data: Any,
    *,
    frame_index: int,
    phase: str,
    observation_state: list[float],
    requested_action: list[float],
    applied_action: list[float],
    object_pose: list[float],
    source_evaluation_identity_sha256: str,
) -> dict[str, Any]:
    """Capture the complete MuJoCo integration state before an applied action."""

    spec = int(mujoco.mjtState.mjSTATE_INTEGRATION)
    if spec != INTEGRATION_STATE_SPEC:
        raise ValueError("Pinned MuJoCo integration-state specification drifted")
    size = int(mujoco.mj_stateSize(model, spec))
    values = np.empty(size, dtype=np.float64)
    mujoco.mj_getState(model, data, values, spec)
    return build_parent_snapshot(
        frame_index=frame_index,
        phase=phase,
        integration_state_spec=spec,
        integration_state=values.astype(float).tolist(),
        observation_state=observation_state,
        requested_action=requested_action,
        applied_action=applied_action,
        object_pose=object_pose,
        source_evaluation_identity_sha256=source_evaluation_identity_sha256,
    )


def restore_integration_state(
    mujoco: Any, model: Any, data: Any, snapshot: dict[str, Any]
) -> list[float]:
    """Restore and immediately read back one exact integration-state snapshot."""

    _validate_parent(snapshot)
    spec = int(mujoco.mjtState.mjSTATE_INTEGRATION)
    if spec != snapshot["integration_state_spec"]:
        raise ValueError("MuJoCo integration-state specification does not match snapshot")
    if int(mujoco.mj_stateSize(model, spec)) != snapshot["integration_state_size"]:
        raise ValueError("MuJoCo integration-state size does not match snapshot")
    source = np.asarray(snapshot["integration_state"], dtype=np.float64)
    mujoco.mj_setState(model, data, source, spec)
    restored = np.empty_like(source)
    mujoco.mj_getState(model, data, restored, spec)
    if not np.array_equal(source, restored):
        raise ValueError("MuJoCo integration-state round trip drifted")
    mujoco.mj_forward(model, data)
    return restored.astype(float).tolist()


def build_parent_snapshot(
    *,
    frame_index: int,
    phase: str,
    integration_state_spec: int,
    integration_state: list[float],
    observation_state: list[float],
    requested_action: list[float],
    applied_action: list[float],
    object_pose: list[float],
    source_evaluation_identity_sha256: str,
) -> dict[str, Any]:
    if not isinstance(frame_index, int) or isinstance(frame_index, bool) or frame_index < 0:
        raise ValueError("Parent frame index is invalid")
    phase = _text(phase, "parent phase")
    if integration_state_spec != INTEGRATION_STATE_SPEC:
        raise ValueError("Parent integration-state specification drifted")
    state = _finite_vector(integration_state, None, "integration state")
    observation = _finite_vector(observation_state, None, "observation state")
    requested = _finite_vector(requested_action, None, "requested action")
    applied = _finite_vector(applied_action, len(requested), "applied action")
    pose = _finite_vector(object_pose, 7, "object pose")
    payload = {
        "frame_index": frame_index,
        "phase": phase,
        "integration_state_spec": integration_state_spec,
        "integration_state_size": len(state),
        "integration_state": state,
        "integration_state_sha256": _sha(state),
        "observation_state": observation,
        "requested_action": requested,
        "applied_action": applied,
        "object_pose": pose,
        "source_evaluation_identity_sha256": _sha_value(
            source_evaluation_identity_sha256, "source evaluation identity"
        ),
    }
    payload["parent_snapshot_id"] = _sha(payload)
    _validate_parent(payload)
    return payload


def select_parent_snapshots(captures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select the deterministic midpoint of four semantic phase groups."""

    if not isinstance(captures, list) or not captures:
        raise ValueError("Policy-visited captures are absent")
    indices: list[int] = []
    for capture in captures:
        _validate_parent(capture)
        indices.append(capture["frame_index"])
    if indices != list(range(len(captures))):
        raise ValueError("Policy-visited frame indices are not contiguous or contain a duplicate")
    selected: list[dict[str, Any]] = []
    for role in PHASE_ROLES:
        rows = [row for row in captures if row["phase"] == _ROLE_PHASE[role]]
        if not rows:
            raise ValueError(f"Policy-visited captures lack the {role} phase")
        row = dict(rows[(len(rows) - 1) // 2])
        row["phase_role"] = role
        selected.append(row)
    return selected


def build_branch_record(
    parent: dict[str, Any],
    *,
    generation_reason: str,
    perturbation: dict[str, Any],
    measured_actions: list[list[float]],
    action_source_record_ids: list[str],
    observed_result: dict[str, Any],
    replay_evidence: dict[str, Any],
    trace_summary: dict[str, Any],
) -> dict[str, Any]:
    _validate_parent(parent)
    reason = _text(generation_reason, "generation reason")
    clean_perturbation = _validate_perturbation(perturbation)
    if not isinstance(measured_actions, list) or not measured_actions:
        raise ValueError("Measured correction actions are absent")
    actions = [_finite_vector(row, 6, "measured correction action") for row in measured_actions]
    if not isinstance(action_source_record_ids, list) or len(action_source_record_ids) != len(actions):
        raise ValueError("Measured action source records do not match actions")
    source_ids = [_sha_value(value, "action source record ID") for value in action_source_record_ids]
    result = _validate_observed_result(observed_result)
    replay = _validate_replay_evidence(replay_evidence)
    payload = {
        "parent_snapshot_id": parent["parent_snapshot_id"],
        "parent_frame_index": parent["frame_index"],
        "phase_role": _text(parent.get("phase_role"), "branch phase role"),
        "generation_reason": reason,
        "perturbation": clean_perturbation,
        "action_provenance": "measured_source",
        "action_source_record_ids": source_ids,
        "measured_actions": actions,
        "measured_action_sequence_sha256": _sha(actions),
        "actions_padded": False,
        "actions_inferred": False,
        "observed_result": result,
        "replay_evidence": replay,
        "trace_summary": trace_summary,
        "outcome_class": _outcome_class(result),
    }
    payload["branch_id"] = _sha(payload)
    _validate_branch(payload, parents={parent["parent_snapshot_id"]: parent})
    return payload


def build_recovery_manifest(
    *,
    source_refs: dict[str, Any],
    t18_4_identity_sha256: str,
    t20_17_evaluation_identity_sha256: str,
    t20_17_action_sequence_sha256: str,
    reproduced_action_sequence_sha256: str,
    reproduced_terminal_outcome: str,
    parents: list[dict[str, Any]],
    branches: list[dict[str, Any]],
) -> dict[str, Any]:
    parent_map = _validate_parents(parents)
    _validate_branches(branches, parents=parent_map)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "source_refs": _validate_source_refs(source_refs),
        "t18_4_identity_sha256": _sha_value(t18_4_identity_sha256, "T18.4 identity"),
        "t20_17_evaluation_identity_sha256": _sha_value(
            t20_17_evaluation_identity_sha256, "T20.17 evaluation identity"
        ),
        "t20_17_action_sequence_sha256": _sha_value(
            t20_17_action_sequence_sha256, "T20.17 action sequence"
        ),
        "reproduced_action_sequence_sha256": _sha_value(
            reproduced_action_sequence_sha256, "reproduced action sequence"
        ),
        "reproduced_terminal_outcome": _text(
            reproduced_terminal_outcome, "reproduced terminal outcome"
        ),
        "parent_count": len(parents),
        "parent_snapshot_ids_sha256": _sha([row["parent_snapshot_id"] for row in parents]),
        "branch_count": len(branches),
        "branch_ids_sha256": _sha([row["branch_id"] for row in branches]),
        "parents": parents,
        "branches": branches,
        **{field: False for field in _FALSE_AUTHORITY_FIELDS},
    }
    manifest = sign_payload(payload)
    verify_recovery_manifest(manifest)
    return manifest


def verify_recovery_manifest(manifest: dict[str, Any]) -> None:
    verify_signed_payload(manifest, label="T20.18 recovery manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("task_id") != TASK_ID:
        raise ValueError("T20.18 recovery manifest schema or task drifted")
    for field in _FALSE_AUTHORITY_FIELDS:
        if manifest.get(field) is not False:
            raise ValueError(f"T20.18 recovery authority flag drifted: {field}")
    if manifest.get("t20_17_action_sequence_sha256") != manifest.get(
        "reproduced_action_sequence_sha256"
    ):
        raise ValueError("T20.18 candidate replay did not reproduce the T20.17 action sequence")
    for field in (
        "t18_4_identity_sha256",
        "t20_17_evaluation_identity_sha256",
        "t20_17_action_sequence_sha256",
        "reproduced_action_sequence_sha256",
    ):
        _sha_value(manifest.get(field), field)
    _validate_source_refs(manifest.get("source_refs"))
    _text(manifest.get("reproduced_terminal_outcome"), "reproduced terminal outcome")
    parents = manifest.get("parents")
    parent_map = _validate_parents(parents)
    if manifest.get("parent_count") != len(parents):
        raise ValueError("T20.18 parent count drifted")
    if manifest.get("parent_snapshot_ids_sha256") != _sha(
        [row["parent_snapshot_id"] for row in parents]
    ):
        raise ValueError("T20.18 parent digest drifted")
    branches = manifest.get("branches")
    _validate_branches(branches, parents=parent_map)
    if manifest.get("branch_count") != len(branches):
        raise ValueError("T20.18 branch count drifted")
    if manifest.get("branch_ids_sha256") != _sha([row["branch_id"] for row in branches]):
        raise ValueError("T20.18 branch digest drifted")


def verify_source_files(manifest: dict[str, Any], *, repo_root: Path) -> None:
    """Reverify every source-reference byte hash inside the named checkout."""

    verify_recovery_manifest(manifest)
    root = Path(repo_root).resolve()
    for label, row in manifest["source_refs"].items():
        path = (root / row["path"]).resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ValueError(f"T20.18 source path escapes checkout: {label}") from error
        if not path.is_file() or _sha_file(path) != row["file_sha256"]:
            raise ValueError(f"T20.18 source file drifted: {label}")


def verify_recovery_gate(gate: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    """Verify the tracked gate and its complete immutable recovery artifact."""

    verify_signed_payload(gate, label="T20.18 recovery gate")
    if gate.get("schema_version") != "scenesmith.t20_18_state_fork_recovery_gate.v1" or gate.get("task_id") != TASK_ID:
        raise ValueError("T20.18 recovery gate schema or task drifted")
    for field in _FALSE_AUTHORITY_FIELDS:
        if gate.get(field) is not False:
            raise ValueError(f"T20.18 gate authority flag drifted: {field}")
    for field in ("exact_candidate_reproduced", "deterministic_replay_verified"):
        if gate.get(field) is not True:
            raise ValueError(f"T20.18 gate verification flag drifted: {field}")
    if gate.get("actions_padded") is not False or gate.get("actions_inferred") is not False:
        raise ValueError("T20.18 gate admits padded or inferred actions")
    root = Path(repo_root).resolve()
    relative = _text(gate.get("artifact_path"), "T20.18 artifact path")
    artifact = (root / relative).resolve()
    try:
        artifact.relative_to(root)
    except ValueError as error:
        raise ValueError("T20.18 artifact path escapes checkout") from error
    if not artifact.is_file() or _sha_file(artifact) != gate.get("artifact_file_sha256"):
        raise ValueError("T20.18 recovery artifact bytes drifted")
    manifest = load_strict_json(artifact)
    verify_recovery_manifest(manifest)
    verify_source_files(manifest, repo_root=root)
    if gate.get("artifact_identity_sha256") != manifest["identity_sha256"]:
        raise ValueError("T20.18 gate artifact identity drifted")
    if gate.get("parent_count") != manifest["parent_count"] or gate.get("branch_count") != manifest["branch_count"]:
        raise ValueError("T20.18 gate artifact counts drifted")
    expected_counts = dict(sorted(Counter(row["outcome_class"] for row in manifest["branches"]).items()))
    if gate.get("outcome_class_counts") != expected_counts:
        raise ValueError("T20.18 gate outcome counts drifted")
    return manifest


def _validate_parent(parent: Any) -> None:
    if not isinstance(parent, dict):
        raise ValueError("Parent snapshot is invalid")
    if not isinstance(parent.get("frame_index"), int) or isinstance(parent["frame_index"], bool) or parent["frame_index"] < 0:
        raise ValueError("Parent frame index is invalid")
    _text(parent.get("phase"), "parent phase")
    if parent.get("integration_state_spec") != INTEGRATION_STATE_SPEC:
        raise ValueError("Parent integration-state specification drifted")
    state = _finite_vector(parent.get("integration_state"), None, "integration state")
    if parent.get("integration_state_size") != len(state):
        raise ValueError("Parent integration-state size drifted")
    if parent.get("integration_state_sha256") != _sha(state):
        raise ValueError("Parent integration-state digest drifted")
    _finite_vector(parent.get("observation_state"), None, "observation state")
    requested = _finite_vector(parent.get("requested_action"), None, "requested action")
    _finite_vector(parent.get("applied_action"), len(requested), "applied action")
    _finite_vector(parent.get("object_pose"), 7, "object pose")
    _sha_value(parent.get("source_evaluation_identity_sha256"), "source evaluation identity")
    parent_id = _sha_value(parent.get("parent_snapshot_id"), "parent snapshot ID")
    unsigned = {key: value for key, value in parent.items() if key not in {"parent_snapshot_id", "phase_role"}}
    if parent_id != _sha(unsigned):
        raise ValueError("Parent snapshot identity drifted")


def _validate_parents(parents: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(parents, list) or len(parents) != len(PHASE_ROLES):
        raise ValueError("T20.18 requires exactly four parent snapshots")
    result: dict[str, dict[str, Any]] = {}
    roles: list[str] = []
    for parent in parents:
        _validate_parent(parent)
        role = _text(parent.get("phase_role"), "parent phase role")
        roles.append(role)
        parent_id = parent["parent_snapshot_id"]
        if parent_id in result:
            raise ValueError("T20.18 parent snapshots contain a duplicate")
        result[parent_id] = parent
    if roles != list(PHASE_ROLES):
        raise ValueError("T20.18 parent phase-role order drifted")
    return result


def _validate_branch(branch: Any, *, parents: dict[str, dict[str, Any]]) -> None:
    if not isinstance(branch, dict):
        raise ValueError("T20.18 branch is invalid")
    parent_id = _sha_value(branch.get("parent_snapshot_id"), "branch parent ID")
    parent = parents.get(parent_id)
    if parent is None or branch.get("parent_frame_index") != parent.get("frame_index"):
        raise ValueError("T20.18 branch parent binding drifted")
    role = _text(branch.get("phase_role"), "branch phase role")
    if role not in PHASE_ROLES or role != parent.get("phase_role"):
        raise ValueError("T20.18 branch phase-role binding drifted")
    _text(branch.get("generation_reason"), "generation reason")
    _validate_perturbation(branch.get("perturbation"))
    if branch.get("action_provenance") != "measured_source":
        raise ValueError("T20.18 branch action provenance drifted")
    if branch.get("actions_padded") is not False or branch.get("actions_inferred") is not False:
        raise ValueError("T20.18 branch contains padded or inferred actions")
    actions = branch.get("measured_actions")
    if not isinstance(actions, list) or not actions:
        raise ValueError("T20.18 branch measured actions are absent")
    clean = [_finite_vector(row, 6, "measured correction action") for row in actions]
    sources = branch.get("action_source_record_ids")
    if not isinstance(sources, list) or len(sources) != len(clean):
        raise ValueError("T20.18 branch action source binding drifted")
    for value in sources:
        _sha_value(value, "action source record ID")
    if branch.get("measured_action_sequence_sha256") != _sha(clean):
        raise ValueError("T20.18 branch measured-action digest drifted")
    result = _validate_observed_result(branch.get("observed_result"))
    replay = _validate_replay_evidence(branch.get("replay_evidence"))
    trace = branch.get("trace_summary")
    if not isinstance(trace, dict):
        raise ValueError("T20.18 branch trace summary is invalid")
    if _sha(trace) != replay["first_trace_sha256"]:
        raise ValueError("T20.18 branch trace summary is not bound to deterministic replay")
    if trace.get("frame_count") != replay["frame_count"]:
        raise ValueError("T20.18 branch trace frame count drifted")
    if trace.get("observed_result") != result:
        raise ValueError("T20.18 branch trace observed result drifted")
    if branch.get("outcome_class") != _outcome_class(result):
        raise ValueError("T20.18 branch outcome label is not observed-result derived")
    branch_id = _sha_value(branch.get("branch_id"), "branch ID")
    unsigned = {key: value for key, value in branch.items() if key != "branch_id"}
    if branch_id != _sha(unsigned):
        raise ValueError("T20.18 branch identity drifted")


def _validate_branches(branches: Any, *, parents: dict[str, dict[str, Any]]) -> None:
    if not isinstance(branches, list) or not branches:
        raise ValueError("T20.18 branches are absent")
    seen: set[str] = set()
    for branch in branches:
        _validate_branch(branch, parents=parents)
        if branch["branch_id"] in seen:
            raise ValueError("T20.18 branches contain a duplicate")
        seen.add(branch["branch_id"])


def _validate_perturbation(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise ValueError("T20.18 perturbation is absent")
    allowed = {"joint_delta_rad", "object_position_delta_m", "object_yaw_delta_rad"}
    if set(value) - allowed:
        raise ValueError("T20.18 perturbation contains an unsupported field")
    clean: dict[str, Any] = {}
    if "joint_delta_rad" in value:
        delta = _finite_vector(value["joint_delta_rad"], 6, "joint perturbation")
        if max(map(abs, delta)) > 0.05:
            raise ValueError("T20.18 joint perturbation exceeds its bound")
        clean["joint_delta_rad"] = delta
    if "object_position_delta_m" in value:
        delta = _finite_vector(value["object_position_delta_m"], 3, "object perturbation")
        if max(map(abs, delta)) > 0.005:
            raise ValueError("T20.18 object-position perturbation exceeds its bound")
        clean["object_position_delta_m"] = delta
    if "object_yaw_delta_rad" in value:
        yaw = _finite_number(value["object_yaw_delta_rad"], "object-yaw perturbation")
        if abs(yaw) > 0.05:
            raise ValueError("T20.18 object-yaw perturbation exceeds its bound")
        clean["object_yaw_delta_rad"] = yaw
    return clean


def _validate_observed_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("T20.18 observed result is invalid")
    success = value.get("simulation_semantic_strict_success")
    contacts = value.get("strict_contact_frame_count")
    if not isinstance(success, bool):
        raise ValueError("T20.18 strict-success result is invalid")
    if not isinstance(contacts, int) or isinstance(contacts, bool) or contacts < 0:
        raise ValueError("T20.18 strict-contact count is invalid")
    lift = _finite_number(value.get("maximum_anchor_lift_m"), "maximum anchor lift")
    return {
        "simulation_semantic_strict_success": success,
        "strict_contact_frame_count": contacts,
        "maximum_anchor_lift_m": lift,
    }


def _validate_replay_evidence(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("T20.18 replay evidence is invalid")
    first = _sha_value(value.get("first_trace_sha256"), "first replay trace")
    second = _sha_value(value.get("second_trace_sha256"), "second replay trace")
    if first != second:
        raise ValueError("T20.18 branch deterministic replay drifted")
    frame_count = value.get("frame_count")
    if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count <= 0:
        raise ValueError("T20.18 replay frame count is invalid")
    tolerance = _finite_number(value.get("absolute_tolerance"), "replay tolerance")
    if tolerance != 0.0:
        raise ValueError("T20.18 exact replay tolerance drifted")
    return {
        "first_trace_sha256": first,
        "second_trace_sha256": second,
        "frame_count": frame_count,
        "absolute_tolerance": tolerance,
    }


def _validate_source_refs(value: Any) -> dict[str, Any]:
    required = {
        "t18_4_manifest",
        "t20_17_result_gate",
        "t20_17_evaluation",
        "t20_17_training_summary",
        "t20_17_adapter",
        "held_out_source_episode",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("T20.18 source references are incomplete")
    clean: dict[str, Any] = {}
    paths: set[str] = set()
    for label in sorted(required):
        row = value[label]
        if not isinstance(row, dict):
            raise ValueError("T20.18 source reference is invalid")
        path = _text(row.get("path"), f"{label} path")
        if path.startswith("/") or ".." in path.split("/") or path in paths:
            raise ValueError("T20.18 source reference path aliases or escapes the checkout")
        paths.add(path)
        fields = {"path": path, "file_sha256": _sha_value(row.get("file_sha256"), f"{label} file hash")}
        if "identity_sha256" in row:
            fields["identity_sha256"] = _sha_value(row["identity_sha256"], f"{label} identity")
        clean[label] = fields
    return clean


def _outcome_class(result: dict[str, Any]) -> str:
    if result["simulation_semantic_strict_success"]:
        return "recovery"
    if result["strict_contact_frame_count"] > 0 or result["maximum_anchor_lift_m"] >= 0.005:
        return "near_failure"
    return "failure"


def _finite_vector(value: Any, length: int | None, label: str) -> list[float]:
    if not isinstance(value, list) or not value or (length is not None and len(value) != length):
        raise ValueError(f"{label} has an invalid shape")
    return [_finite_number(item, label) for item in value]


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must contain only finite numbers")
    return float(value)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank")
    return value.strip()


def _sha_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return value


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
