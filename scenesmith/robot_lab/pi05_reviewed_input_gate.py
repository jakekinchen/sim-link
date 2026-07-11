"""Fail-closed reviewed-input issuance gate for PI0.5 preprocessing."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.pi05_preprocessing_contract import (
    PI05_PREPROCESSING_SOURCE_CONTRACT_SCHEMA_VERSION,
    verify_pi05_preprocessing_source_contract,
)


PI05_REVIEWED_INPUT_GATE_SCHEMA_VERSION = (
    "scenesmith.pi05_reviewed_input_gate.v1"
)
PI05_LIVE_SESSION_ACCEPTANCE_SCHEMA_VERSION = (
    "scenesmith.pi05_live_session_acceptance.v1"
)
PI05_CAMERA_ROLE_BINDING_SCHEMA_VERSION = (
    "scenesmith.pi05_camera_role_binding.v1"
)
PI05_REVIEWED_TASK_PROMPT_SCHEMA_VERSION = (
    "scenesmith.pi05_reviewed_task_prompt.v1"
)

_SOURCE_CONTRACT_PATH = Path(
    "configurations/robot_lab/"
    "pi05_policy_input_preprocessing.blocked_missing_inputs.json"
)
_EXPECTED_SOURCE_CONTRACT_IDENTITY = (
    "f6b216684f6bb3f895b3d1761d72e80b5e93a5ec7be8f44b04cc277e7a871afa"
)
_INPUT_KINDS = [
    "accepted_live_session_review_decision",
    "reviewed_stable_camera_role_binding",
    "reviewed_task_prompt",
]
_AUTHORITY_NOT_GRANTED = [
    "accepted_live_policy_input",
    "policy_shadow_input_valid",
    "policy_shadow",
    "model_weight_load",
    "policy_inference",
    "physical_follower_command",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]
_SOURCE_REVIEW_AUTHORITY_NOT_GRANTED = [
    "live_candidate_session_accepted",
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]
_NO_EXECUTION_FACTS = {
    "accepted_live_policy_input": False,
    "policy_input_built": False,
    "model_instantiated": False,
    "model_weights_read": False,
    "preprocessing_run": False,
    "policy_shadow_run": False,
    "policy_inference_run": False,
    "mujoco_replay_run": False,
    "hardware_accessed": False,
    "physical_follower_commanded": False,
    "motion_authority_granted": False,
    "training_authority_granted": False,
}
_INPUT_SPECS = {
    "accepted_live_session_review_decision": {
        "schema_version": PI05_LIVE_SESSION_ACCEPTANCE_SCHEMA_VERSION,
        "scope": "local_pi05_live_session_acceptance",
        "fixture_capability": (
            "fixture_pi05_live_session_acceptance_conformant"
        ),
        "production_capability": "pi05_live_session_acceptance_valid",
        "filename": re.compile(
            r"pi05_static_pose_live_session_([A-Za-z0-9][A-Za-z0-9._-]{0,127})"
            r"\.acceptance\.json"
        ),
    },
    "reviewed_stable_camera_role_binding": {
        "schema_version": PI05_CAMERA_ROLE_BINDING_SCHEMA_VERSION,
        "scope": "local_pi05_stable_camera_role_binding",
        "fixture_capability": "fixture_pi05_camera_role_binding_conformant",
        "production_capability": "pi05_stable_camera_role_binding_valid",
        "filename": re.compile(
            r"pi05_camera_role_binding_"
            r"([A-Za-z0-9][A-Za-z0-9._-]{0,127})\.json"
        ),
    },
    "reviewed_task_prompt": {
        "schema_version": PI05_REVIEWED_TASK_PROMPT_SCHEMA_VERSION,
        "scope": "local_pi05_task_prompt_review",
        "fixture_capability": "fixture_pi05_task_prompt_review_conformant",
        "production_capability": "pi05_task_prompt_review_valid",
        "filename": re.compile(
            r"pi05_task_prompt_"
            r"([A-Za-z0-9][A-Za-z0-9._-]{0,127})\.json"
        ),
    },
}
_CAMERA_ROLE_MAP = {
    "observation.images.top": "observation.images.base_0_rgb",
    "observation.images.wrist": "observation.images.left_wrist_0_rgb",
}
_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_REVIEW_DECISION_PATTERN = re.compile(r"[0-9]{3}")
_REVIEW_RECORD_PATTERN = re.compile(
    r"docs/reviewer-messages/([0-9]{3})-[a-z0-9][a-z0-9-]*\.md"
)
_REVIEW_MANIFEST_PATTERN = re.compile(
    r"configurations/robot_lab/pi05_static_pose_live_session_"
    r"([A-Za-z0-9][A-Za-z0-9._-]{0,127})\.redacted\.json"
)
_MAX_VALIDITY_INTERVAL_NS = 24 * 60 * 60 * 1_000_000_000
_MAX_REVIEW_RECORD_BYTES = 1_000_000
_COMMON_INPUT_FIELDS = {
    "schema_version",
    "input_kind",
    "qualification_scope",
    "evidence_class",
    "status",
    "issuer_id",
    "review_decision_id",
    "source_contract_identity_sha256",
    "session_id",
    "issued_at_unix_ns",
    "valid_from_unix_ns",
    "valid_until_unix_ns",
    "production_eligible",
    "review_subject_sha256",
    "review_record",
    "local_capabilities",
    "proof_labels",
    "authority_not_granted",
    "identity_sha256",
    *_NO_EXECUTION_FACTS,
}
_SPECIFIC_INPUT_FIELDS = {
    "accepted_live_session_review_decision": {
        "review_manifest",
        "review_outcome",
        "accepted_live_session_review",
        "accepted_as_static_pose_bracketed_observation",
    },
    "reviewed_stable_camera_role_binding": {
        "review_manifest",
        "assignments",
        "private_review_evidence_sha256",
        "binding_reviewed",
        "numeric_camera_index_used",
        "raw_camera_identity_included",
    },
    "reviewed_task_prompt": {
        "task_key",
        "task_text",
        "task_text_sha256",
        "prompt_template_sha256",
        "prompt_prefix_sha256",
        "task_prompt_reviewed",
    },
}


def build_pi05_reviewed_input_gate(
    *,
    repo_root: Path,
    hf_cache_root: Path,
    calibration_path: Path,
    evaluation_time_unix_ns: int | None = None,
    acceptance_decision_path: Path | None = None,
    camera_role_binding_path: Path | None = None,
    task_prompt_path: Path | None = None,
) -> dict[str, Any]:
    """Build a source-bound reviewed-input decision without preprocessing."""

    root = Path(repo_root).resolve()
    source_path = root / _SOURCE_CONTRACT_PATH
    source_contract = _load_nonaliased_json(
        source_path,
        repo_root=root,
        label="PI0.5 preprocessing source contract",
    )
    verify_pi05_preprocessing_source_contract(
        source_contract,
        repo_root=root,
        hf_cache_root=hf_cache_root,
        calibration_path=calibration_path,
    )
    _verify_source_contract_classification(source_contract)

    paths = {
        "accepted_live_session_review_decision": acceptance_decision_path,
        "reviewed_stable_camera_role_binding": camera_role_binding_path,
        "reviewed_task_prompt": task_prompt_path,
    }
    if any(path is not None for path in paths.values()):
        evaluation_time = _positive_integer(
            evaluation_time_unix_ns,
            label="PI0.5 reviewed-input evaluation time",
        )
    elif evaluation_time_unix_ns is not None:
        raise ValueError("PI0.5 reviewed-input evaluation time has no inputs")
    else:
        evaluation_time = None

    reviewed_inputs: dict[str, dict[str, Any]] = {}
    verified_payloads: dict[str, dict[str, Any]] = {}
    missing_inputs: list[str] = []
    for input_kind in _INPUT_KINDS:
        path = paths[input_kind]
        if path is None:
            missing_inputs.append(input_kind)
            reviewed_inputs[input_kind] = {"present": False}
            continue
        payload, evidence = _load_reviewed_input(
            path,
            input_kind=input_kind,
            repo_root=root,
        )
        summary = _verify_reviewed_input(
            payload,
            input_kind=input_kind,
            source_contract=source_contract,
            evaluation_time_unix_ns=evaluation_time,
            repo_root=root,
        )
        reviewed_inputs[input_kind] = {
            "present": True,
            **evidence,
            **summary,
        }
        verified_payloads[input_kind] = payload

    production_allowed = False
    local_capabilities = ["pi05_reviewed_input_issuance_gate_conformant"]
    if missing_inputs:
        status = "blocked_missing_reviewed_inputs"
        qualification_scope = "fixture_pi05_reviewed_input_issuance_gate"
        evidence_mode = "deterministic_fixture_blocked_missing_reviewed_inputs"
        _verify_partial_consistency(verified_payloads)
    else:
        production_allowed = _verify_complete_consistency(verified_payloads)
        if production_allowed:
            status = "reviewed_input_bundle_valid"
            qualification_scope = "local_pi05_reviewed_input_bundle"
            evidence_mode = "tracked_production_reviewed_inputs"
            local_capabilities.append("pi05_reviewed_input_bundle_valid")
        else:
            status = "fixture_inputs_conformant"
            qualification_scope = "fixture_pi05_reviewed_input_issuance_gate"
            evidence_mode = "deterministic_fixture_reviewed_inputs"

    payload = {
        "schema_version": PI05_REVIEWED_INPUT_GATE_SCHEMA_VERSION,
        "gate_name": "pi05_reviewed_input_issuance_gate",
        "qualification_scope": qualification_scope,
        "evidence_mode": evidence_mode,
        "status": status,
        "source_contract": _tracked_artifact_evidence(
            source_path,
            repo_root=root,
            payload=source_contract,
        ),
        "requirements": _requirements_summary(source_contract),
        "evaluation_time_unix_ns": evaluation_time,
        "reviewed_inputs": reviewed_inputs,
        "missing_inputs": missing_inputs,
        "production_input_issuance_allowed": production_allowed,
        **_NO_EXECUTION_FACTS,
        "local_capabilities": local_capabilities,
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
    }
    return sign_payload(payload)


def verify_pi05_reviewed_input_gate(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    hf_cache_root: Path,
    calibration_path: Path,
    evaluation_time_unix_ns: int | None = None,
    acceptance_decision_path: Path | None = None,
    camera_role_binding_path: Path | None = None,
    task_prompt_path: Path | None = None,
) -> None:
    """Rebuild the gate from its exact sources and reject re-signed drift."""

    if not isinstance(payload, dict):
        raise ValueError("PI0.5 reviewed-input gate must be an object")
    if payload.get("schema_version") != PI05_REVIEWED_INPUT_GATE_SCHEMA_VERSION:
        raise ValueError("PI0.5 reviewed-input gate schema is unsupported")
    verify_signed_payload(payload, label="PI0.5 reviewed-input gate")
    expected = build_pi05_reviewed_input_gate(
        repo_root=repo_root,
        hf_cache_root=hf_cache_root,
        calibration_path=calibration_path,
        evaluation_time_unix_ns=evaluation_time_unix_ns,
        acceptance_decision_path=acceptance_decision_path,
        camera_role_binding_path=camera_role_binding_path,
        task_prompt_path=task_prompt_path,
    )
    if payload != expected:
        raise ValueError("PI0.5 reviewed-input gate drifted from sources")


def review_subject_sha256(payload: dict[str, Any]) -> str:
    """Hash only the reviewed semantic subject, excluding its record linkage."""

    if not isinstance(payload, dict):
        raise ValueError("PI0.5 review subject must be an object")
    subject = {
        key: value
        for key, value in payload.items()
        if key not in {"identity_sha256", "review_record", "review_subject_sha256"}
    }
    return hashlib.sha256(canonical_json_bytes(subject)).hexdigest()


def _verify_source_contract_classification(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="PI0.5 preprocessing source contract")
    if (
        payload.get("schema_version")
        != PI05_PREPROCESSING_SOURCE_CONTRACT_SCHEMA_VERSION
        or payload.get("identity_sha256") != _EXPECTED_SOURCE_CONTRACT_IDENTITY
        or payload.get("status") != "blocked_missing_inputs"
        or payload.get("missing_inputs") != _INPUT_KINDS
        or payload.get("local_capabilities")
        != ["pi05_policy_input_preprocessing_source_contract_conformant"]
        or payload.get("proof_labels") != []
        or payload.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
        or payload.get("production_preprocessing_allowed") is not False
    ):
        raise ValueError("PI0.5 preprocessing source classification drifted")
    for key, expected in _NO_EXECUTION_FACTS.items():
        source_key = key
        if key == "accepted_live_policy_input":
            continue
        if key == "motion_authority_granted":
            source_key = "motion_authority_granted"
        if key == "training_authority_granted":
            source_key = "training_authority_granted"
        if payload.get(source_key) is not expected:
            raise ValueError(f"PI0.5 preprocessing source fact drifted: {source_key}")
    cameras = payload.get("camera_contract", {}).get(
        "stable_camera_identity_sha256"
    )
    if (
        not isinstance(cameras, list)
        or len(cameras) != 2
        or len(set(cameras)) != 2
    ):
        raise ValueError("PI0.5 source camera identities are ambiguous")
    for digest in cameras:
        _require_sha256(digest, label="PI0.5 source stable camera identity")
    task_contract = payload.get("task_contract")
    if (
        not isinstance(task_contract, dict)
        or task_contract.get("task_key") != "task"
        or task_contract.get("prompt_template")
        != "Task: {cleaned_task}, State: {discretized_state};\nAction: "
        or task_contract.get("reviewed_task_prompt") is not None
        or task_contract.get("task_prompt_reviewed") is not False
    ):
        raise ValueError("PI0.5 source task contract drifted")
    observation = payload.get("observation_acceptance_contract")
    if (
        not isinstance(observation, dict)
        or observation.get("accepted_live_review_artifact_present") is not False
        or observation.get("accepted_live_review_decision_present") is not False
        or observation.get("accepted_live_review_manifest_identity_sha256")
        is not None
        or observation.get("acceptance_decision_identity_sha256") is not None
    ):
        raise ValueError("PI0.5 source acceptance contract drifted")


def _load_reviewed_input(
    path: Path,
    *,
    input_kind: str,
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = _INPUT_SPECS[input_kind]
    resolved, relative = _require_nonaliased_file(
        path,
        root=repo_root,
        label=f"PI0.5 {input_kind}",
    )
    if relative.parent.as_posix() != "configurations/robot_lab":
        raise ValueError(f"PI0.5 {input_kind} is outside robot-lab configuration")
    match = spec["filename"].fullmatch(relative.name)
    if match is None:
        raise ValueError(f"PI0.5 {input_kind} filename is invalid")
    payload = load_strict_json(resolved)
    evidence = _tracked_artifact_evidence(
        resolved,
        repo_root=repo_root,
        payload=payload,
    )
    if load_strict_json(resolved) != payload:
        raise ValueError(f"PI0.5 {input_kind} changed while loading")
    if payload.get("session_id") != match.group(1):
        raise ValueError(f"PI0.5 {input_kind} filename/session drifted")
    return payload, evidence


def _verify_reviewed_input(
    payload: dict[str, Any],
    *,
    input_kind: str,
    source_contract: dict[str, Any],
    evaluation_time_unix_ns: int,
    repo_root: Path,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"PI0.5 {input_kind} must be an object")
    verify_signed_payload(payload, label=f"PI0.5 {input_kind}")
    if set(payload) != _COMMON_INPUT_FIELDS | _SPECIFIC_INPUT_FIELDS[input_kind]:
        raise ValueError(f"PI0.5 {input_kind} fields drifted")
    spec = _INPUT_SPECS[input_kind]
    evidence_class = payload.get("evidence_class")
    if evidence_class not in {
        "deterministic_fixture",
        "tracked_production_review",
    }:
        raise ValueError(f"PI0.5 {input_kind} evidence class is unsupported")
    production = evidence_class == "tracked_production_review"
    expected_status = "reviewed" if production else "fixture_conformant"
    expected_capability = (
        spec["production_capability"]
        if production
        else spec["fixture_capability"]
    )
    if (
        payload.get("schema_version") != spec["schema_version"]
        or payload.get("input_kind") != input_kind
        or payload.get("qualification_scope") != spec["scope"]
        or payload.get("status") != expected_status
        or payload.get("issuer_id") != "scenesmith_same_agent_reviewer_v1"
        or payload.get("source_contract_identity_sha256")
        != source_contract.get("identity_sha256")
        or payload.get("production_eligible") is not production
        or payload.get("local_capabilities") != [expected_capability]
        or payload.get("proof_labels") != []
        or payload.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
    ):
        raise ValueError(f"PI0.5 {input_kind} classification drifted")
    for key, expected in _NO_EXECUTION_FACTS.items():
        if payload.get(key) is not expected:
            raise ValueError(f"PI0.5 {input_kind} authority fact drifted: {key}")

    session_id = _session_id(payload.get("session_id"))
    decision_id = _review_decision_id(payload.get("review_decision_id"))
    issued_at = _positive_integer(
        payload.get("issued_at_unix_ns"),
        label=f"PI0.5 {input_kind} issued at",
    )
    valid_from = _positive_integer(
        payload.get("valid_from_unix_ns"),
        label=f"PI0.5 {input_kind} valid from",
    )
    valid_until = _positive_integer(
        payload.get("valid_until_unix_ns"),
        label=f"PI0.5 {input_kind} valid until",
    )
    if (
        issued_at > valid_from
        or valid_from > evaluation_time_unix_ns
        or evaluation_time_unix_ns > valid_until
        or valid_until <= valid_from
        or valid_until - valid_from > _MAX_VALIDITY_INTERVAL_NS
    ):
        raise ValueError(f"PI0.5 {input_kind} validity window is invalid")

    if input_kind == "accepted_live_session_review_decision":
        specific = _verify_acceptance(
            payload,
            production=production,
            source_contract=source_contract,
            repo_root=repo_root,
        )
    elif input_kind == "reviewed_stable_camera_role_binding":
        specific = _verify_camera_binding(
            payload,
            production=production,
            source_contract=source_contract,
            repo_root=repo_root,
        )
    else:
        specific = _verify_task_prompt(
            payload,
            production=production,
            source_contract=source_contract,
        )
    subject = _require_sha256(
        payload.get("review_subject_sha256"),
        label=f"PI0.5 {input_kind} review subject",
    )
    if subject != review_subject_sha256(payload):
        raise ValueError(f"PI0.5 {input_kind} review subject drifted")
    review_record = _verify_review_record(
        payload.get("review_record"),
        input_kind=input_kind,
        decision_id=decision_id,
        subject_sha256=subject,
        repo_root=repo_root,
    )
    return {
        "evidence_class": evidence_class,
        "issuer_id": payload["issuer_id"],
        "review_decision_id": decision_id,
        "session_id": session_id,
        "issued_at_unix_ns": issued_at,
        "valid_from_unix_ns": valid_from,
        "valid_until_unix_ns": valid_until,
        "review_subject_sha256": subject,
        "review_record_sha256": review_record["sha256"],
        **specific,
    }


def _verify_acceptance(
    payload: dict[str, Any],
    *,
    production: bool,
    source_contract: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    manifest, manifest_evidence = _verify_review_manifest_reference(
        payload.get("review_manifest"),
        session_id=payload.get("session_id"),
        source_contract=source_contract,
        repo_root=repo_root,
    )
    expected_outcome = (
        "accepted_for_pi05_reviewed_input_bundle"
        if production
        else "fixture_acceptance_conformant"
    )
    if (
        payload.get("review_outcome") != expected_outcome
        or payload.get("accepted_live_session_review") is not production
        or payload.get("accepted_as_static_pose_bracketed_observation")
        is not production
    ):
        raise ValueError("PI0.5 live-session acceptance semantics drifted")
    return {
        "review_manifest_identity_sha256": manifest["identity_sha256"],
        "review_manifest_sha256": manifest_evidence["sha256"],
    }


def _verify_camera_binding(
    payload: dict[str, Any],
    *,
    production: bool,
    source_contract: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    manifest, manifest_evidence = _verify_review_manifest_reference(
        payload.get("review_manifest"),
        session_id=payload.get("session_id"),
        source_contract=source_contract,
        repo_root=repo_root,
    )
    assignments = payload.get("assignments")
    if not isinstance(assignments, list) or len(assignments) != 2:
        raise ValueError("PI0.5 camera binding requires exactly two assignments")
    observed: dict[str, str] = {}
    identities: set[str] = set()
    for assignment in assignments:
        if not isinstance(assignment, dict) or set(assignment) != {
            "stable_camera_identity_sha256",
            "source_key",
            "model_key",
        }:
            raise ValueError("PI0.5 camera binding assignment fields drifted")
        identity = _require_sha256(
            assignment.get("stable_camera_identity_sha256"),
            label="PI0.5 bound stable camera identity",
        )
        source_key = assignment.get("source_key")
        model_key = assignment.get("model_key")
        if source_key not in _CAMERA_ROLE_MAP or model_key != _CAMERA_ROLE_MAP[
            source_key
        ]:
            raise ValueError("PI0.5 camera role/model mapping drifted")
        if source_key in observed or identity in identities:
            raise ValueError("PI0.5 camera role binding is not bijective")
        observed[source_key] = model_key
        identities.add(identity)
    expected_identities = set(
        source_contract["camera_contract"]["stable_camera_identity_sha256"]
    )
    if observed != _CAMERA_ROLE_MAP or identities != expected_identities:
        raise ValueError("PI0.5 camera binding does not cover exact sources")
    private_review = _require_sha256(
        payload.get("private_review_evidence_sha256"),
        label="PI0.5 private camera review evidence",
    )
    if (
        payload.get("binding_reviewed") is not production
        or payload.get("numeric_camera_index_used") is not False
        or payload.get("raw_camera_identity_included") is not False
    ):
        raise ValueError("PI0.5 camera binding review semantics drifted")
    return {
        "review_manifest_identity_sha256": manifest["identity_sha256"],
        "review_manifest_sha256": manifest_evidence["sha256"],
        "camera_assignment_sha256": _sha256_payload(assignments),
        "private_review_evidence_sha256": private_review,
    }


def _verify_task_prompt(
    payload: dict[str, Any],
    *,
    production: bool,
    source_contract: dict[str, Any],
) -> dict[str, Any]:
    task = payload.get("task_text")
    if not isinstance(task, str):
        raise ValueError("PI0.5 task text must be a string")
    encoded = task.encode("utf-8")
    if (
        not task
        or len(encoded) > 256
        or task != task.strip()
        or "_" in task
        or "\n" in task
        or "\r" in task
        or "\t" in task
        or " ".join(task.split()) != task
        or unicodedata.normalize("NFC", task) != task
        or any(unicodedata.category(character).startswith("C") for character in task)
    ):
        raise ValueError("PI0.5 task text is ambiguous or unbounded")
    task_sha256 = hashlib.sha256(encoded).hexdigest()
    template = source_contract["task_contract"]["prompt_template"]
    template_sha256 = hashlib.sha256(template.encode("utf-8")).hexdigest()
    prefix_sha256 = hashlib.sha256(
        f"Task: {task}, State: ".encode("utf-8")
    ).hexdigest()
    if (
        payload.get("task_key") != "task"
        or payload.get("task_text_sha256") != task_sha256
        or payload.get("prompt_template_sha256") != template_sha256
        or payload.get("prompt_prefix_sha256") != prefix_sha256
        or payload.get("task_prompt_reviewed") is not production
    ):
        raise ValueError("PI0.5 task review semantics drifted")
    return {
        "task_text_sha256": task_sha256,
        "prompt_template_sha256": template_sha256,
        "prompt_prefix_sha256": prefix_sha256,
        "task_text_included": False,
    }


def _verify_review_manifest_reference(
    reference: Any,
    *,
    session_id: Any,
    source_contract: dict[str, Any],
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(reference, dict) or set(reference) != {
        "path",
        "schema_version",
        "identity_sha256",
        "sha256",
        "size_bytes",
    }:
        raise ValueError("PI0.5 review manifest reference fields drifted")
    relative = reference.get("path")
    if not isinstance(relative, str):
        raise ValueError("PI0.5 review manifest path is missing")
    match = _REVIEW_MANIFEST_PATTERN.fullmatch(relative)
    expected_session = _session_id(session_id)
    if match is None or match.group(1) != expected_session:
        raise ValueError("PI0.5 review manifest path/session drifted")
    resolved, observed_relative = _require_nonaliased_file(
        repo_root / relative,
        root=repo_root,
        label="PI0.5 review manifest",
    )
    if observed_relative.as_posix() != relative:
        raise ValueError("PI0.5 review manifest logical path drifted")
    manifest = load_strict_json(resolved)
    evidence = _tracked_artifact_evidence(
        resolved,
        repo_root=repo_root,
        payload=manifest,
    )
    if load_strict_json(resolved) != manifest:
        raise ValueError("PI0.5 review manifest changed while loading")
    if reference != evidence:
        raise ValueError("PI0.5 review manifest reference drifted")
    _verify_review_manifest_classification(
        manifest,
        session_id=expected_session,
        source_contract=source_contract,
    )
    return manifest, evidence


def _verify_review_manifest_classification(
    payload: dict[str, Any],
    *,
    session_id: str,
    source_contract: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="PI0.5 live-session review manifest")
    if (
        payload.get("schema_version")
        != "scenesmith.static_pose_live_session_review_manifest.v1"
        or payload.get("manifest_name")
        != "pi05_static_pose_live_candidate_session_review"
        or payload.get("qualification_scope")
        != "local_static_pose_live_candidate_session_review"
        or payload.get("evidence_mode")
        != "tracked_redacted_private_candidate_session_review"
        or payload.get("status") != "candidate_observed_pending_review"
        or payload.get("review_decision_required") is not True
        or payload.get("session_id") != session_id
        or payload.get("candidate_only") is not True
        or payload.get("local_capabilities")
        != ["redacted_static_pose_live_candidate_session_review_conformant"]
        or payload.get("proof_labels") != []
        or payload.get("authority_not_granted")
        != _SOURCE_REVIEW_AUTHORITY_NOT_GRANTED
        or payload.get("hardware_opened") is not True
        or payload.get("physical_follower_commanded") is not False
        or payload.get("policy_inference_run") is not False
        or payload.get("motion_authority_granted") is not False
        or payload.get("training_authority_granted") is not False
        or payload.get("accepted_as_static_pose_bracketed_observation") is not False
        or payload.get("accepted_as_policy_shadow_input") is not False
    ):
        raise ValueError("PI0.5 live-session review manifest classification drifted")
    cameras = payload.get("camera_observation_summary")
    if not isinstance(cameras, list) or len(cameras) != 2:
        raise ValueError("PI0.5 review manifest camera evidence is incomplete")
    observed = []
    for camera in cameras:
        if not isinstance(camera, dict):
            raise ValueError("PI0.5 review manifest camera is malformed")
        observed.append(
            _require_sha256(
                camera.get("stable_camera_identity_sha256"),
                label="PI0.5 review manifest stable camera",
            )
        )
    expected = source_contract["camera_contract"][
        "stable_camera_identity_sha256"
    ]
    if len(set(observed)) != 2 or set(observed) != set(expected):
        raise ValueError("PI0.5 review manifest camera identity drifted")


def _verify_review_record(
    reference: Any,
    *,
    input_kind: str,
    decision_id: str,
    subject_sha256: str,
    repo_root: Path,
) -> dict[str, Any]:
    if not isinstance(reference, dict) or set(reference) != {
        "path",
        "sha256",
        "size_bytes",
    }:
        raise ValueError("PI0.5 review record reference fields drifted")
    relative = reference.get("path")
    if not isinstance(relative, str):
        raise ValueError("PI0.5 review record path is missing")
    match = _REVIEW_RECORD_PATTERN.fullmatch(relative)
    if match is None or match.group(1) != decision_id:
        raise ValueError("PI0.5 review record decision/path drifted")
    resolved, observed_relative = _require_nonaliased_file(
        repo_root / relative,
        root=repo_root,
        label="PI0.5 reviewer record",
    )
    if observed_relative.as_posix() != relative:
        raise ValueError("PI0.5 review record logical path drifted")
    evidence = _tracked_file_evidence(resolved, repo_root=repo_root)
    if evidence != reference:
        raise ValueError("PI0.5 review record reference drifted")
    if evidence["size_bytes"] > _MAX_REVIEW_RECORD_BYTES:
        raise ValueError("PI0.5 review record is unbounded")
    before = resolved.stat()
    encoded = resolved.read_bytes()
    after = resolved.stat()
    if (
        _stat_identity(before) != _stat_identity(after)
        or len(encoded) != evidence["size_bytes"]
        or hashlib.sha256(encoded).hexdigest() != evidence["sha256"]
    ):
        raise ValueError("PI0.5 review record changed while loading")
    try:
        lines = encoded.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("PI0.5 review record is not UTF-8") from exc
    kind_line = f"PI05_REVIEW_INPUT_KIND: {input_kind}"
    decision_line = f"PI05_REVIEW_DECISION_ID: {decision_id}"
    subject_line = f"PI05_REVIEW_SUBJECT_SHA256: {subject_sha256}"
    if lines.count(kind_line) != 1 or lines.count(subject_line) != 1:
        raise ValueError("PI0.5 review record markers are missing or ambiguous")
    index = lines.index(kind_line)
    if (
        index + 2 >= len(lines)
        or lines[index + 1] != decision_line
        or lines[index + 2] != subject_line
    ):
        raise ValueError("PI0.5 review record marker block drifted")
    return evidence


def _verify_partial_consistency(
    payloads: dict[str, dict[str, Any]],
) -> None:
    if len(payloads) < 2:
        return
    values = list(payloads.values())
    reference = values[0]
    for payload in values[1:]:
        for field in (
            "source_contract_identity_sha256",
            "session_id",
            "issuer_id",
            "review_decision_id",
            "valid_from_unix_ns",
            "valid_until_unix_ns",
        ):
            if payload.get(field) != reference.get(field):
                raise ValueError(f"PI0.5 partial reviewed inputs disagree on {field}")


def _verify_complete_consistency(
    payloads: dict[str, dict[str, Any]],
) -> bool:
    if set(payloads) != set(_INPUT_KINDS):
        raise ValueError("PI0.5 reviewed-input bundle is incomplete")
    _verify_partial_consistency(payloads)
    acceptance = payloads["accepted_live_session_review_decision"]
    binding = payloads["reviewed_stable_camera_role_binding"]
    if acceptance.get("review_manifest") != binding.get("review_manifest"):
        raise ValueError("PI0.5 acceptance and camera binding manifests disagree")
    classes = {payload.get("evidence_class") for payload in payloads.values()}
    if classes == {"deterministic_fixture"}:
        return False
    if classes == {"tracked_production_review"}:
        return True
    raise ValueError("PI0.5 reviewed-input evidence classes are mixed")


def _requirements_summary(source_contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_contract_identity_sha256": source_contract["identity_sha256"],
        "required_input_order": list(_INPUT_KINDS),
        "allowed_issuer_ids": ["scenesmith_same_agent_reviewer_v1"],
        "fixture_evidence_class": "deterministic_fixture",
        "production_evidence_class": "tracked_production_review",
        "maximum_validity_interval_ns": _MAX_VALIDITY_INTERVAL_NS,
        "required_camera_roles": [
            {
                "source_key": source_key,
                "model_key": model_key,
            }
            for source_key, model_key in _CAMERA_ROLE_MAP.items()
        ],
        "stable_camera_identity_sha256": list(
            source_contract["camera_contract"]["stable_camera_identity_sha256"]
        ),
        "task_key": "task",
        "prompt_template_sha256": hashlib.sha256(
            source_contract["task_contract"]["prompt_template"].encode("utf-8")
        ).hexdigest(),
        "input_artifacts_created_by_gate": False,
    }


def _tracked_artifact_evidence(
    path: Path,
    *,
    repo_root: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    evidence = _tracked_file_evidence(path, repo_root=repo_root)
    evidence.update(
        {
            "schema_version": payload.get("schema_version"),
            "identity_sha256": _require_sha256(
                payload.get("identity_sha256"),
                label="PI0.5 tracked artifact identity",
            ),
        }
    )
    if not isinstance(evidence["schema_version"], str):
        raise ValueError("PI0.5 tracked artifact schema is missing")
    return evidence


def _tracked_file_evidence(path: Path, *, repo_root: Path) -> dict[str, Any]:
    resolved, relative = _require_nonaliased_file(
        path,
        root=repo_root,
        label="PI0.5 tracked source",
    )
    before = resolved.stat()
    encoded = resolved.read_bytes()
    after = resolved.stat()
    if _stat_identity(before) != _stat_identity(after):
        raise ValueError("PI0.5 tracked source changed while reading")
    return {
        "path": relative.as_posix(),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "size_bytes": len(encoded),
    }


def _load_nonaliased_json(
    path: Path,
    *,
    repo_root: Path,
    label: str,
) -> dict[str, Any]:
    resolved, _ = _require_nonaliased_file(path, root=repo_root, label=label)
    return load_strict_json(resolved)


def _require_nonaliased_file(
    path: Path,
    *,
    root: Path,
    label: str,
) -> tuple[Path, Path]:
    canonical_root = Path(root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = canonical_root / candidate
    try:
        relative = candidate.relative_to(canonical_root)
    except ValueError as exc:
        raise ValueError(f"{label} escaped the repository") from exc
    if not relative.parts or any(part in {".", ".."} for part in relative.parts):
        raise ValueError(f"{label} has an invalid relative path")
    current = canonical_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} is aliased")
    if not current.is_file() or current.resolve() != current:
        raise ValueError(f"{label} is missing or escaped")
    return current, relative


def _positive_integer(value: Any, *, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _session_id(value: Any) -> str:
    if not isinstance(value, str) or _SESSION_ID_PATTERN.fullmatch(value) is None:
        raise ValueError("PI0.5 reviewed-input session ID is invalid")
    return value


def _review_decision_id(value: Any) -> str:
    if not isinstance(value, str) or _REVIEW_DECISION_PATTERN.fullmatch(value) is None:
        raise ValueError("PI0.5 review decision ID is invalid")
    return value


def _require_sha256(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return value


def _sha256_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _stat_identity(value: Any) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
