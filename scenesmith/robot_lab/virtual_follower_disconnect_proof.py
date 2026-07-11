"""Machine-verifiable proof for the one-call virtual follower disconnect."""

from __future__ import annotations

import copy
import hashlib

from datetime import datetime
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.leader_arm_bridge import KNOWN_PHYSICAL_FOLLOWER_PORT
from scenesmith.robot_lab.live_readonly_observation import (
    require_no_serial_identity_holders,
    verify_serial_identity_holder_snapshot,
)


PRIVATE_DISCONNECT_EVIDENCE_SCHEMA_VERSION = (
    "scenesmith.virtual_follower_disconnect_private.v1"
)
VIRTUAL_DISCONNECT_PROOF_SCHEMA_VERSION = (
    "scenesmith.virtual_follower_disconnect_proof.v1"
)
DISCONNECT_PERMIT_SCHEMA_VERSION = (
    "scenesmith.virtual_follower_disconnect_permit.v1"
)
PERMIT_SOURCE_COMMIT = "59f09d1576d777ee8e186ff885b58ac69c2a253d"
PERMIT_SOURCE_PATH = "docs/autonomous-workflow/project_state.json"


def build_private_virtual_disconnect_evidence(
    *,
    project_state: dict[str, Any],
    observation: dict[str, Any],
    post_holder_snapshot: dict[str, Any],
    post_holder_revalidated_at: str,
) -> dict[str, Any]:
    permit = _build_consumed_permit(project_state)
    _verify_observation_input(observation)
    verify_serial_identity_holder_snapshot(post_holder_snapshot)
    require_no_serial_identity_holders(post_holder_snapshot)
    payload = {
        "schema_version": PRIVATE_DISCONNECT_EVIDENCE_SCHEMA_VERSION,
        "evidence_name": "pi05_virtual_follower_disconnect_private",
        "qualification_scope": "physical_observation",
        "evidence_mode": "local_private_reconstructed_operation_evidence",
        "provenance_class": observation["provenance_class"],
        "reconstructed_at": observation["reconstructed_at"],
        "source_session_log": observation["source_session_log"],
        "source_reviewer_decision": observation["source_reviewer_decision"],
        "permit_source_commit": observation["permit_source_commit"],
        "permit_source_path": observation["permit_source_path"],
        "permit_source_file_sha256": observation["permit_source_file_sha256"],
        "authority_id": project_state["owner_authority"]["authority_id"],
        "permit": permit,
        "request": copy.deepcopy(observation["request"]),
        "maximum_call_count": permit["maximum_call_count"],
        "observed_call_count": observation["observed_call_count"],
        "started_at": observation["started_at"],
        "finished_at": observation["finished_at"],
        "timestamp_resolution_seconds": observation[
            "timestamp_resolution_seconds"
        ],
        "response": copy.deepcopy(observation["response"]),
        "pre_hardware": copy.deepcopy(observation["pre_hardware"]),
        "post_hardware": copy.deepcopy(observation["post_hardware"]),
        "safety_before": copy.deepcopy(observation["safety_before"]),
        "safety_after": copy.deepcopy(observation["safety_after"]),
        "routing_before": copy.deepcopy(observation["routing_before"]),
        "routing_after": copy.deepcopy(observation["routing_after"]),
        "jobs_before": copy.deepcopy(observation["jobs_before"]),
        "jobs_after": copy.deepcopy(observation["jobs_after"]),
        "canonical_path_holder_snapshot_before": copy.deepcopy(
            observation["canonical_path_holder_snapshot_before"]
        ),
        "post_holder_snapshot": copy.deepcopy(post_holder_snapshot),
        "post_holder_revalidated_at": _require_time(
            post_holder_revalidated_at,
            label="post-holder revalidated_at",
        ),
        "forbidden_effects_observed": copy.deepcopy(
            observation["forbidden_effects_observed"]
        ),
        "physical_motion_commanded": observation["physical_motion_commanded"],
        "physical_follower_commanded": observation[
            "physical_follower_commanded"
        ],
        "permit_consumed": True,
        "additional_calls_allowed": 0,
        "proof_label": "virtual_follower_disconnect_observed",
    }
    signed = sign_payload(payload)
    verify_private_virtual_disconnect_evidence(
        signed,
        project_state=project_state,
    )
    return signed


def verify_private_virtual_disconnect_evidence(
    payload: dict[str, Any],
    *,
    project_state: dict[str, Any],
) -> None:
    allowed_fields = {
        "schema_version",
        "evidence_name",
        "qualification_scope",
        "evidence_mode",
        "provenance_class",
        "reconstructed_at",
        "source_session_log",
        "source_reviewer_decision",
        "permit_source_commit",
        "permit_source_path",
        "permit_source_file_sha256",
        "authority_id",
        "permit",
        "request",
        "maximum_call_count",
        "observed_call_count",
        "started_at",
        "finished_at",
        "timestamp_resolution_seconds",
        "response",
        "pre_hardware",
        "post_hardware",
        "safety_before",
        "safety_after",
        "routing_before",
        "routing_after",
        "jobs_before",
        "jobs_after",
        "canonical_path_holder_snapshot_before",
        "post_holder_snapshot",
        "post_holder_revalidated_at",
        "forbidden_effects_observed",
        "physical_motion_commanded",
        "physical_follower_commanded",
        "permit_consumed",
        "additional_calls_allowed",
        "proof_label",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Private virtual disconnect evidence fields are malformed")
    if (
        payload.get("schema_version")
        != PRIVATE_DISCONNECT_EVIDENCE_SCHEMA_VERSION
        or payload.get("evidence_name")
        != "pi05_virtual_follower_disconnect_private"
        or payload.get("qualification_scope") != "physical_observation"
        or payload.get("evidence_mode")
        != "local_private_reconstructed_operation_evidence"
        or payload.get("provenance_class")
        != "reconstructed_from_executor_operation_output"
        or payload.get("proof_label")
        != "virtual_follower_disconnect_observed"
    ):
        raise ValueError("Private virtual disconnect classification drifted")
    verify_signed_payload(payload, label="Private virtual disconnect evidence")
    expected_permit = _build_consumed_permit(project_state)
    permit = payload.get("permit")
    if permit != expected_permit:
        raise ValueError("Virtual disconnect permit identity or content drifted")
    if payload.get("authority_id") != project_state["owner_authority"][
        "authority_id"
    ]:
        raise ValueError("Virtual disconnect authority identity drifted")
    if (
        payload.get("permit_source_commit") != PERMIT_SOURCE_COMMIT
        or payload.get("permit_source_path") != PERMIT_SOURCE_PATH
    ):
        raise ValueError("Virtual disconnect permit source drifted")
    _require_sha256(
        payload.get("permit_source_file_sha256"),
        label="permit source file SHA-256",
    )
    for field in ("source_session_log", "source_reviewer_decision"):
        source = require_nonblank(payload.get(field), label=field)
        if not source.startswith("docs/") or ".." in Path(source).parts:
            raise ValueError("Virtual disconnect source reference is invalid")
    reconstructed = _parse_time(
        payload.get("reconstructed_at"),
        label="reconstructed_at",
    )
    started = _parse_time(payload.get("started_at"), label="started_at")
    finished = _parse_time(payload.get("finished_at"), label="finished_at")
    if (
        finished < started
        or reconstructed < finished
        or payload.get("timestamp_resolution_seconds") != 1
    ):
        raise ValueError("Virtual disconnect operation interval is invalid")
    holder_revalidated = _parse_time(
        payload.get("post_holder_revalidated_at"),
        label="post-holder revalidated_at",
    )
    if holder_revalidated < finished:
        raise ValueError("Virtual disconnect holder proof predates the operation")
    if payload.get("request") != permit["request"]:
        raise ValueError("Virtual disconnect request drifted from the permit")
    if (
        payload.get("maximum_call_count") != 1
        or payload.get("observed_call_count") != 1
        or payload.get("permit_consumed") is not True
        or payload.get("additional_calls_allowed") != 0
    ):
        raise ValueError("Virtual disconnect call count or consumption is invalid")
    response = payload.get("response")
    if response != {"http_status": 200, "body": {"connected": False}}:
        raise ValueError("Virtual disconnect response is invalid")
    pre = payload.get("pre_hardware")
    post = payload.get("post_hardware")
    if not isinstance(pre, dict) or not isinstance(post, dict):
        raise ValueError("Virtual disconnect hardware snapshots are missing")
    if pre.get("follower") != {
        "connected": True,
        "port": KNOWN_PHYSICAL_FOLLOWER_PORT,
        "torque": True,
    }:
        raise ValueError("Virtual disconnect precondition follower state is invalid")
    if post.get("follower") != {
        "connected": False,
        "port": None,
        "torque": False,
    }:
        raise ValueError("Virtual disconnect postcondition follower state is invalid")
    if (
        pre.get("leader", {}).get("connected") is not True
        or post.get("leader", {}).get("connected") is not True
        or pre.get("leader", {}).get("port")
        != post.get("leader", {}).get("port")
    ):
        raise ValueError("Virtual disconnect changed or lost the leader identity")
    if payload.get("safety_before") != payload.get("safety_after"):
        raise ValueError("Virtual disconnect safety state changed")
    if payload.get("routing_before") != payload.get("routing_after"):
        raise ValueError("Virtual disconnect routing state changed")
    for field in ("jobs_before", "jobs_after"):
        jobs = payload.get(field)
        if (
            not isinstance(jobs, dict)
            or not isinstance(jobs.get("job_count"), int)
            or jobs.get("job_count") < 0
            or jobs.get("running_jobs") != []
        ):
            raise ValueError("Virtual disconnect observed a running job")
    pre_holders = payload.get("canonical_path_holder_snapshot_before")
    if (
        not isinstance(pre_holders, list)
        or len(pre_holders) != 1
        or pre_holders[0].get("pid") != 62234
    ):
        raise ValueError("Virtual disconnect pre-holder evidence is invalid")
    holder_snapshot = payload.get("post_holder_snapshot")
    verify_serial_identity_holder_snapshot(holder_snapshot)
    require_no_serial_identity_holders(holder_snapshot)
    if (
        payload.get("forbidden_effects_observed") != []
        or payload.get("physical_motion_commanded") is not False
        or payload.get("physical_follower_commanded") is not False
    ):
        raise ValueError("Virtual disconnect observed a forbidden effect")


def write_private_virtual_disconnect_evidence(
    *,
    path: Path,
    evidence: dict[str, Any],
    reference_path: str,
) -> dict[str, Any]:
    verify_signed_payload(evidence, label="Private virtual disconnect evidence")
    if path.exists():
        raise ValueError("Private virtual disconnect path must be new and immutable")
    reference = require_nonblank(reference_path, label="private reference path")
    reference_parts = Path(reference)
    expected_prefix = Path("outputs/robot_lab/virtual_disconnect/private")
    if (
        reference_parts.is_absolute()
        or ".." in reference_parts.parts
        or reference_parts == expected_prefix
        or not reference_parts.is_relative_to(expected_prefix)
    ):
        raise ValueError("Private virtual disconnect reference path is invalid")
    dump_canonical_json(path, evidence)
    return {
        "path": reference,
        "schema_version": evidence["schema_version"],
        "identity_sha256": evidence["identity_sha256"],
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }


def build_redacted_virtual_disconnect_proof(
    *,
    private_evidence: dict[str, Any],
    private_evidence_reference: dict[str, Any],
) -> dict[str, Any]:
    _verify_private_reference(
        private_evidence_reference,
        private_evidence=private_evidence,
    )
    holder = private_evidence["post_holder_snapshot"]
    payload = {
        "schema_version": VIRTUAL_DISCONNECT_PROOF_SCHEMA_VERSION,
        "proof_name": "pi05_virtual_follower_disconnect_redacted",
        "qualification_scope": "physical_observation",
        "evidence_mode": "tracked_redacted_reconstructed_operation_proof",
        "proof_label": private_evidence["proof_label"],
        "authority_id": private_evidence["authority_id"],
        "permit_identity_sha256": private_evidence["permit"]["identity_sha256"],
        "permit_source_commit": private_evidence["permit_source_commit"],
        "permit_source_file_sha256": private_evidence[
            "permit_source_file_sha256"
        ],
        "private_evidence_reference": copy.deepcopy(private_evidence_reference),
        "request": copy.deepcopy(private_evidence["request"]),
        "maximum_call_count": private_evidence["maximum_call_count"],
        "observed_call_count": private_evidence["observed_call_count"],
        "started_at": private_evidence["started_at"],
        "finished_at": private_evidence["finished_at"],
        "timestamp_resolution_seconds": private_evidence[
            "timestamp_resolution_seconds"
        ],
        "response": {
            "http_status": private_evidence["response"]["http_status"],
            "body_sha256": _sha256_payload(private_evidence["response"]["body"]),
        },
        "preconditions": {
            "follower_connected": private_evidence["pre_hardware"]["follower"]
            ["connected"],
            "follower_torque_reported": private_evidence["pre_hardware"]
            ["follower"]["torque"],
            "leader_connected": private_evidence["pre_hardware"]["leader"]
            ["connected"],
        },
        "postconditions": {
            "follower_connected": private_evidence["post_hardware"]["follower"]
            ["connected"],
            "follower_torque_reported": private_evidence["post_hardware"]
            ["follower"]["torque"],
            "leader_connected": private_evidence["post_hardware"]["leader"]
            ["connected"],
            "follower_holder_count": holder["deduplicated_holder_count"],
        },
        "invariants": {
            "safety_state_unchanged": (
                private_evidence["safety_before"] == private_evidence["safety_after"]
            ),
            "routing_state_unchanged": (
                private_evidence["routing_before"]
                == private_evidence["routing_after"]
            ),
            "running_job_count_before": len(
                private_evidence["jobs_before"]["running_jobs"]
            ),
            "running_job_count_after": len(
                private_evidence["jobs_after"]["running_jobs"]
            ),
        },
        "serial_holder_evidence": {
            "paths_checked_count": len(holder["paths_checked"]),
            "path_identity_sha256": [
                _sha256_payload(path) for path in holder["paths_checked"]
            ],
            "per_path_holder_counts": copy.deepcopy(
                holder["per_path_holder_counts"]
            ),
            "deduplicated_holder_count": holder["deduplicated_holder_count"],
            "normalized_holder_snapshot_sha256": holder["identity_sha256"],
            "revalidated_at": private_evidence["post_holder_revalidated_at"],
        },
        "forbidden_effects_observed": copy.deepcopy(
            private_evidence["forbidden_effects_observed"]
        ),
        "physical_motion_commanded": private_evidence[
            "physical_motion_commanded"
        ],
        "physical_follower_commanded": private_evidence[
            "physical_follower_commanded"
        ],
        "permit_consumed": private_evidence["permit_consumed"],
        "additional_calls_allowed": private_evidence[
            "additional_calls_allowed"
        ],
        "privacy": {
            "raw_usb_serial_included": False,
            "raw_device_paths_included": False,
            "raw_response_body_included": False,
            "private_evidence_required": True,
        },
    }
    return sign_payload(payload)


def verify_redacted_virtual_disconnect_proof(
    payload: dict[str, Any],
    *,
    private_evidence: dict[str, Any],
    private_evidence_reference: dict[str, Any],
    project_state: dict[str, Any],
) -> None:
    if payload.get("schema_version") != VIRTUAL_DISCONNECT_PROOF_SCHEMA_VERSION:
        raise ValueError("Unsupported virtual disconnect proof schema")
    verify_private_virtual_disconnect_evidence(
        private_evidence,
        project_state=project_state,
    )
    _verify_private_reference(
        private_evidence_reference,
        private_evidence=private_evidence,
    )
    verify_signed_payload(payload, label="Redacted virtual disconnect proof")
    expected = build_redacted_virtual_disconnect_proof(
        private_evidence=private_evidence,
        private_evidence_reference=private_evidence_reference,
    )
    if payload != expected:
        raise ValueError("Redacted virtual disconnect proof drifted from raw evidence")


def _build_consumed_permit(project_state: dict[str, Any]) -> dict[str, Any]:
    owner = project_state.get("owner_authority")
    task = project_state.get("tasks", {}).get("T16.5b")
    if not isinstance(owner, dict) or not isinstance(task, dict):
        raise ValueError("Project state disconnect authority is missing")
    virtual = owner.get("virtual_connection_authority")
    decision = task.get("owner_decision_required")
    plan = decision.get("disconnect_plan") if isinstance(decision, dict) else None
    if not isinstance(virtual, dict) or not isinstance(plan, dict):
        raise ValueError("Project state disconnect permit is missing")
    if (
        virtual.get("permit_consumed") is not True
        or virtual.get("observed_call_count") != 1
        or virtual.get("additional_calls_allowed") != 0
        or plan.get("maximum_call_count") != 1
        or plan.get("observed_call_count") != 1
        or plan.get("permit_consumed") is not True
        or plan.get("additional_calls_allowed") != 0
    ):
        raise ValueError("Project state disconnect permit is not consumed exactly once")
    payload = {
        "schema_version": DISCONNECT_PERMIT_SCHEMA_VERSION,
        "permit_name": "pi05_one_call_virtual_follower_disconnect",
        "authority_id": owner.get("authority_id"),
        "granted_at": decision.get("granted_at"),
        "request": {
            "method": plan.get("method"),
            "path": plan.get("path"),
            "body": copy.deepcopy(plan.get("body")),
        },
        "maximum_call_count": plan.get("maximum_call_count"),
        "expected_effect": plan.get("expected_effect"),
        "forbidden_effects": copy.deepcopy(plan.get("forbidden_effects")),
        "required_postconditions": copy.deepcopy(
            plan.get("required_postconditions")
        ),
        "permit_consumed": True,
        "observed_call_count": 1,
        "additional_calls_allowed": 0,
    }
    signed = sign_payload(payload)
    if signed["request"] != {
        "method": "POST",
        "path": "/api/hardware/disconnect",
        "body": {"role": "follower"},
    }:
        raise ValueError("Project state disconnect permit request is invalid")
    return signed


def _verify_observation_input(payload: dict[str, Any]) -> None:
    allowed_fields = {
        "schema_version",
        "provenance_class",
        "reconstructed_at",
        "source_session_log",
        "source_reviewer_decision",
        "permit_source_commit",
        "permit_source_path",
        "permit_source_file_sha256",
        "started_at",
        "finished_at",
        "timestamp_resolution_seconds",
        "request",
        "observed_call_count",
        "response",
        "pre_hardware",
        "post_hardware",
        "safety_before",
        "safety_after",
        "routing_before",
        "routing_after",
        "jobs_before",
        "jobs_after",
        "canonical_path_holder_snapshot_before",
        "forbidden_effects_observed",
        "physical_motion_commanded",
        "physical_follower_commanded",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Virtual disconnect observation input fields are malformed")
    if (
        payload.get("schema_version")
        != "scenesmith.virtual_follower_disconnect_observation.v1"
        or payload.get("provenance_class")
        != "reconstructed_from_executor_operation_output"
        or payload.get("permit_source_commit") != PERMIT_SOURCE_COMMIT
        or payload.get("permit_source_path") != PERMIT_SOURCE_PATH
    ):
        raise ValueError("Virtual disconnect observation provenance drifted")
    _require_sha256(
        payload.get("permit_source_file_sha256"),
        label="observation permit source file SHA-256",
    )


def _verify_private_reference(
    payload: dict[str, Any],
    *,
    private_evidence: dict[str, Any],
) -> None:
    if not isinstance(payload, dict) or set(payload) != {
        "path",
        "schema_version",
        "identity_sha256",
        "file_sha256",
        "size_bytes",
    }:
        raise ValueError("Private virtual disconnect reference is malformed")
    reference_path = Path(require_nonblank(payload.get("path"), label="private path"))
    expected_prefix = Path("outputs/robot_lab/virtual_disconnect/private")
    if (
        reference_path.is_absolute()
        or ".." in reference_path.parts
        or reference_path == expected_prefix
        or not reference_path.is_relative_to(expected_prefix)
        or payload.get("schema_version") != private_evidence["schema_version"]
        or payload.get("identity_sha256") != private_evidence["identity_sha256"]
    ):
        raise ValueError("Private virtual disconnect reference linkage drifted")
    _require_sha256(payload.get("file_sha256"), label="private evidence file SHA-256")
    size = payload.get("size_bytes")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("Private virtual disconnect reference size is invalid")


def _parse_time(value: Any, *, label: str) -> datetime:
    text = require_nonblank(value, label=label)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a UTC offset")
    return parsed


def _require_time(value: Any, *, label: str) -> str:
    text = require_nonblank(value, label=label)
    _parse_time(text, label=label)
    return text


def _require_sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
