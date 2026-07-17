"""Machine-check the active Codex runtime before any robot hardware access."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tomllib

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)


HARDWARE_EXECUTION_PROFILE_SCHEMA_VERSION = (
    "scenesmith.hardware_execution_profile_evidence.v1"
)
HARDWARE_APPROVAL_POLICY = "never"
HARDWARE_SANDBOX_MODE = "danger-full-access"
HARDWARE_EXECUTION_PROFILE_NAME = "hardware_supervised_no_prompt"
CODEX_EXECUTABLE = Path("/opt/homebrew/bin/codex")
DOCTOR_COMMAND = [
    str(CODEX_EXECUTABLE),
    "--ask-for-approval",
    HARDWARE_APPROVAL_POLICY,
    "--sandbox",
    HARDWARE_SANDBOX_MODE,
    "doctor",
    "--json",
    "--summary",
    "--no-color",
]
MAX_PROFILE_AGE_SECONDS = 300
DOCTOR_TIMEOUT_SECONDS = 60

_PROJECT_DEFAULT_PATH = Path(".codex/config.toml")
_HARDWARE_PROFILE_PATH = Path(".codex/profiles/hardware-supervised.toml")
_OFFLINE_PROFILE_PATH = Path(".codex/profiles/offline-autonomous.toml")
_AUTHORITY_NOT_GRANTED = [
    "static_pose_bracketed_observation",
    "policy_shadow_input_valid",
    "policy_shadow",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "supervised_micro_motion",
]
_SESSION_META_RESUME_ADDITIVE_FIELDS = {"memory_mode"}
_HARDWARE_PROFILE_INSTRUCTIONS = (
    "Hardware-supervised permissions do not grant robot authority. Require the "
    "repository live gate, owner-presence lease, and exact session permit before "
    "physical hardware access."
)
_OFFLINE_PROFILE_INSTRUCTIONS = (
    "Offline-autonomous permissions do not grant robot authority. Keep every "
    "physical-hardware gate closed."
)


def verify_codex_execution_profile_files(*, repo_root: Path) -> dict[str, Any]:
    """Verify the safe project default and the two explicit profile fragments."""

    root = Path(repo_root).resolve()
    paths = {
        "project_default": _PROJECT_DEFAULT_PATH,
        "hardware_supervised": _HARDWARE_PROFILE_PATH,
        "offline_autonomous": _OFFLINE_PROFILE_PATH,
    }
    profiles: dict[str, Any] = {}
    for name, relative in paths.items():
        unresolved = root / relative
        if unresolved.is_symlink() or unresolved.parent.is_symlink():
            raise ValueError(f"Codex execution profile is aliased: {relative}")
        path = unresolved.resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Codex execution profile path escapes the repository") from exc
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Codex execution profile is missing or aliased: {relative}")
        try:
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(f"Codex execution profile is malformed: {relative}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Codex execution profile is malformed: {relative}")
        profiles[name] = payload

    default = profiles["project_default"]
    if (
        default.get("sandbox_mode") != HARDWARE_SANDBOX_MODE
        or default.get("approval_policy") != HARDWARE_APPROVAL_POLICY
        or default.get("features", {}).get("multi_agent") is not False
    ):
        raise ValueError("Committed Codex project default is not full-access no-prompt")
    _verify_profile_fragment(
        profiles["hardware_supervised"],
        expected_sandbox=HARDWARE_SANDBOX_MODE,
        expected_approval=HARDWARE_APPROVAL_POLICY,
        expected_instructions=_HARDWARE_PROFILE_INSTRUCTIONS,
        label="hardware-supervised",
    )
    _verify_profile_fragment(
        profiles["offline_autonomous"],
        expected_sandbox="danger-full-access",
        expected_approval="never",
        expected_instructions=_OFFLINE_PROFILE_INSTRUCTIONS,
        label="offline-autonomous",
    )
    if profiles["hardware_supervised"] == profiles["offline_autonomous"]:
        raise ValueError("Codex hardware and offline profiles collapsed")
    return copy.deepcopy(profiles)


def capture_hardware_execution_profile_evidence(
    *,
    repo_root: Path,
    captured_at: str,
    environment: Mapping[str, str] | None = None,
    run_command: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    runtime_context_loader: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Capture one fresh, private, active-runtime report without hardware access."""

    root = Path(repo_root).resolve()
    profiles = verify_codex_execution_profile_files(repo_root=root)
    runtime_environment = environment or os.environ
    thread_id = require_nonblank(
        runtime_environment.get("CODEX_THREAD_ID"),
        label="Codex hardware profile thread ID",
    )
    captured = _parse_time(captured_at, label="hardware profile captured_at")
    loader = runtime_context_loader or _capture_active_thread_runtime
    active_before = loader(
        thread_id=thread_id,
        repo_root=root,
        environment=runtime_environment,
    )
    _validate_active_runtime_capture(active_before, thread_id=thread_id, repo_root=root)
    active_context = active_before["active_runtime_context"]
    if active_context["approval_policy"] != HARDWARE_APPROVAL_POLICY:
        raise ValueError("Active Codex thread is not using no-prompt approval")
    if active_context["sandbox_policy"] != {"type": HARDWARE_SANDBOX_MODE}:
        raise ValueError("Active Codex thread is not using the hardware sandbox")
    completed = run_command(
        list(DOCTOR_COMMAND),
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
        timeout=DOCTOR_TIMEOUT_SECONDS,
        shell=False,
    )
    if type(completed.returncode) is not int or completed.returncode not in {0, 1}:
        raise ValueError("Codex doctor returned an unsupported status")
    if not isinstance(completed.stdout, str) or not completed.stdout.strip():
        raise ValueError("Codex doctor did not return a JSON report")
    try:
        report = json.loads(completed.stdout, parse_constant=_reject_json_constant)
    except (TypeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("Codex doctor report is not strict JSON") from exc
    runtime = _validated_doctor_runtime(report, repo_root=root)
    active_after = loader(
        thread_id=thread_id,
        repo_root=root,
        environment=runtime_environment,
    )
    _validate_active_runtime_capture(active_after, thread_id=thread_id, repo_root=root)
    if active_after != active_before:
        raise ValueError("Active Codex runtime context changed during profile capture")
    if runtime["approval_policy"] != HARDWARE_APPROVAL_POLICY:
        raise ValueError("Hardware execution requires active no-prompt approval")
    if runtime["sandbox_mode"] != HARDWARE_SANDBOX_MODE:
        raise ValueError("Hardware execution requires the supervised device-access sandbox")
    payload = {
        "schema_version": HARDWARE_EXECUTION_PROFILE_SCHEMA_VERSION,
        "evidence_name": "pi05_hardware_supervised_codex_runtime",
        "qualification_scope": "local_hardware_execution_profile",
        "source_mode": "live_codex_doctor_and_active_rollout_runtime_capture",
        "synthetic": False,
        "thread_id": thread_id,
        "captured_at": captured.isoformat(),
        "doctor_command": list(DOCTOR_COMMAND),
        "doctor_exit_code": completed.returncode,
        "doctor_report": report,
        "doctor_report_sha256": _sha256_payload(report),
        "rollout_reference": copy.deepcopy(active_before["rollout_reference"]),
        "active_runtime_context": copy.deepcopy(active_context),
        "active_runtime_context_sha256": active_before[
            "active_runtime_context_sha256"
        ],
        "codex_version": runtime["codex_version"],
        "codex_executable": runtime["codex_executable"],
        "approval_policy": runtime["approval_policy"],
        "sandbox_mode": runtime["sandbox_mode"],
        "project_profile_references": _profile_references(
            root=root,
            profiles=profiles,
        ),
        "local_capabilities": ["hardware_supervised_runtime_profile_observed"],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
    }
    signed = sign_payload(payload)
    verify_hardware_execution_profile_evidence(
        signed,
        repo_root=root,
        now=captured.isoformat(),
        expected_thread_id=thread_id,
        runtime_context_loader=loader,
        runtime_environment=runtime_environment,
    )
    return signed


def verify_hardware_execution_profile_evidence(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    now: str,
    expected_thread_id: str,
    require_active_runtime: bool = True,
    runtime_context_loader: Callable[..., dict[str, Any]] | None = None,
    runtime_environment: Mapping[str, str] | None = None,
) -> None:
    """Independently verify a fresh active-runtime profile and tracked configs."""

    allowed_fields = {
        "schema_version",
        "evidence_name",
        "qualification_scope",
        "source_mode",
        "synthetic",
        "thread_id",
        "captured_at",
        "doctor_command",
        "doctor_exit_code",
        "doctor_report",
        "doctor_report_sha256",
        "rollout_reference",
        "active_runtime_context",
        "active_runtime_context_sha256",
        "codex_version",
        "codex_executable",
        "approval_policy",
        "sandbox_mode",
        "project_profile_references",
        "local_capabilities",
        "authority_not_granted",
        "hardware_accessed",
        "physical_follower_commanded",
        "motion_authority_granted",
        "training_authority_granted",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != allowed_fields:
        raise ValueError("Hardware execution profile evidence fields are malformed")
    if (
        payload.get("schema_version")
        != HARDWARE_EXECUTION_PROFILE_SCHEMA_VERSION
        or payload.get("evidence_name")
        != "pi05_hardware_supervised_codex_runtime"
        or payload.get("qualification_scope")
        != "local_hardware_execution_profile"
        or payload.get("source_mode")
        != "live_codex_doctor_and_active_rollout_runtime_capture"
        or payload.get("synthetic") is not False
    ):
        raise ValueError("Hardware execution profile source classification drifted")
    verify_signed_payload(payload, label="Hardware execution profile evidence")
    thread_id = require_nonblank(
        payload.get("thread_id"),
        label="hardware execution profile thread ID",
    )
    if thread_id != require_nonblank(
        expected_thread_id,
        label="expected Codex thread ID",
    ):
        raise ValueError("Hardware execution profile thread identity drifted")
    embedded_runtime = {
        "rollout_reference": payload.get("rollout_reference"),
        "active_runtime_context": payload.get("active_runtime_context"),
        "active_runtime_context_sha256": payload.get(
            "active_runtime_context_sha256"
        ),
    }
    root = Path(repo_root).resolve()
    _validate_active_runtime_capture(
        embedded_runtime,
        thread_id=thread_id,
        repo_root=root,
    )
    active_context = embedded_runtime["active_runtime_context"]
    if (
        active_context["approval_policy"] != HARDWARE_APPROVAL_POLICY
        or active_context["sandbox_policy"] != {"type": HARDWARE_SANDBOX_MODE}
    ):
        raise ValueError("Hardware execution profile active runtime is not supervised")
    if require_active_runtime:
        loader = runtime_context_loader or _capture_active_thread_runtime
        observed_runtime = loader(
            thread_id=thread_id,
            repo_root=root,
            environment=runtime_environment or os.environ,
        )
        _validate_active_runtime_capture(
            observed_runtime,
            thread_id=thread_id,
            repo_root=root,
        )
        if observed_runtime != embedded_runtime:
            raise ValueError("Hardware execution profile active runtime context drifted")
    captured = _parse_time(payload.get("captured_at"), label="profile captured_at")
    verified = _parse_time(now, label="profile verification time")
    age = (verified - captured).total_seconds()
    if age < 0 or age > MAX_PROFILE_AGE_SECONDS:
        raise ValueError("Hardware execution profile is stale or future-dated")
    if payload.get("doctor_command") != DOCTOR_COMMAND:
        raise ValueError("Hardware execution profile doctor command drifted")
    if type(payload.get("doctor_exit_code")) is not int or payload.get(
        "doctor_exit_code"
    ) not in {0, 1}:
        raise ValueError("Hardware execution profile doctor status drifted")
    report = payload.get("doctor_report")
    if not isinstance(report, dict) or payload.get(
        "doctor_report_sha256"
    ) != _sha256_payload(report):
        raise ValueError("Hardware execution profile doctor report identity drifted")
    runtime = _validated_doctor_runtime(report, repo_root=root)
    if (
        payload.get("codex_version") != runtime["codex_version"]
        or payload.get("codex_executable") != runtime["codex_executable"]
        or payload.get("approval_policy") != HARDWARE_APPROVAL_POLICY
        or payload.get("approval_policy") != runtime["approval_policy"]
        or payload.get("sandbox_mode") != HARDWARE_SANDBOX_MODE
        or payload.get("sandbox_mode") != runtime["sandbox_mode"]
        or payload.get("approval_policy") != active_context["approval_policy"]
        or payload.get("sandbox_mode")
        != active_context["sandbox_policy"]["type"]
    ):
        raise ValueError("Hardware execution profile runtime semantics drifted")
    profiles = verify_codex_execution_profile_files(repo_root=root)
    if payload.get("project_profile_references") != _profile_references(
        root=root,
        profiles=profiles,
    ):
        raise ValueError("Hardware execution profile tracked profile identity drifted")
    if (
        payload.get("local_capabilities")
        != ["hardware_supervised_runtime_profile_observed"]
        or payload.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
        or payload.get("hardware_accessed") is not False
        or payload.get("physical_follower_commanded") is not False
        or payload.get("motion_authority_granted") is not False
        or payload.get("training_authority_granted") is not False
    ):
        raise ValueError("Hardware execution profile authority fields drifted")


def _capture_active_thread_runtime(
    *,
    thread_id: str,
    repo_root: Path,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    """Read the latest persisted turn context for the active Codex thread."""

    codex_home = Path(environment.get("CODEX_HOME", Path.home() / ".codex")).resolve()
    sessions = codex_home / "sessions"
    if not sessions.is_dir() or sessions.is_symlink():
        raise ValueError("Codex active-session directory is missing or aliased")
    matches = sorted(sessions.rglob(f"*{thread_id}.jsonl"))
    if len(matches) != 1:
        raise ValueError("Codex active thread must resolve to exactly one rollout")
    rollout = matches[0]
    if rollout.is_symlink() or not rollout.is_file():
        raise ValueError("Codex active rollout is missing or aliased")
    try:
        relative = rollout.resolve().relative_to(codex_home)
    except ValueError as exc:
        raise ValueError("Codex active rollout escaped CODEX_HOME") from exc
    session_meta_records: list[dict[str, Any]] = []
    contexts: list[tuple[int, dict[str, Any]]] = []
    with rollout.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                record = json.loads(line, parse_constant=_reject_json_constant)
            except (TypeError, json.JSONDecodeError, ValueError) as exc:
                raise ValueError("Codex active rollout contains malformed JSON") from exc
            if not isinstance(record, dict):
                raise ValueError("Codex active rollout record is malformed")
            if record.get("type") == "session_meta":
                metadata = record.get("payload")
                if not isinstance(metadata, dict):
                    raise ValueError("Codex active session metadata is malformed")
                session_meta_records.append(metadata)
            elif record.get("type") == "turn_context":
                context = record.get("payload")
                if not isinstance(context, dict):
                    raise ValueError("Codex active turn context is malformed")
                contexts.append((line_number, context))
    if (
        not session_meta_records
        or any(metadata.get("id") != thread_id for metadata in session_meta_records)
        or not contexts
    ):
        raise ValueError("Codex active rollout identity or turn context is missing")
    session_meta = _resolve_resumed_session_metadata(session_meta_records)
    line_number, full_context = contexts[-1]
    selected = {
        "turn_id": require_nonblank(
            full_context.get("turn_id"), label="Codex active turn ID"
        ),
        "cwd": require_nonblank(full_context.get("cwd"), label="Codex active cwd"),
        "approval_policy": _normalize_approval_policy(
            full_context.get("approval_policy")
        ),
        "sandbox_policy": copy.deepcopy(full_context.get("sandbox_policy")),
        "model": require_nonblank(
            full_context.get("model"), label="Codex active model"
        ),
        "effort": require_nonblank(
            full_context.get("effort"), label="Codex active effort"
        ),
        "multi_agent_mode": require_nonblank(
            full_context.get("multi_agent_mode"),
            label="Codex active multi-agent mode",
        ),
    }
    return {
        "rollout_reference": {
            "relative_path": relative.as_posix(),
            "session_meta_identity_sha256": _sha256_payload(session_meta),
            "turn_context_line_number": line_number,
        },
        "active_runtime_context": selected,
        "active_runtime_context_sha256": _sha256_payload(full_context),
    }


def _resolve_resumed_session_metadata(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Accept only monotonic, identity-stable Codex Desktop resume metadata."""

    selected = copy.deepcopy(records[0])
    for record in records[1:]:
        added = set(record) - set(selected)
        if not added.issubset(_SESSION_META_RESUME_ADDITIVE_FIELDS) or any(
            field not in record or record[field] != value
            for field, value in selected.items()
        ):
            raise ValueError("Codex active session metadata identity drifted")
        selected = copy.deepcopy(record)
    return selected


def _validate_active_runtime_capture(
    payload: Any,
    *,
    thread_id: str,
    repo_root: Path,
) -> None:
    if not isinstance(payload, dict) or set(payload) != {
        "rollout_reference",
        "active_runtime_context",
        "active_runtime_context_sha256",
    }:
        raise ValueError("Codex active runtime capture fields are malformed")
    reference = payload.get("rollout_reference")
    if not isinstance(reference, dict) or set(reference) != {
        "relative_path",
        "session_meta_identity_sha256",
        "turn_context_line_number",
    }:
        raise ValueError("Codex active rollout reference fields are malformed")
    relative = Path(
        require_nonblank(reference.get("relative_path"), label="active rollout path")
    )
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.as_posix().startswith("sessions/")
        or not relative.name.endswith(f"{thread_id}.jsonl")
    ):
        raise ValueError("Codex active rollout reference path drifted")
    _require_sha256(
        reference.get("session_meta_identity_sha256"),
        label="active rollout session metadata identity",
    )
    if (
        type(reference.get("turn_context_line_number")) is not int
        or reference["turn_context_line_number"] <= 0
    ):
        raise ValueError("Codex active turn-context line number is invalid")
    context = payload.get("active_runtime_context")
    if not isinstance(context, dict) or set(context) != {
        "turn_id",
        "cwd",
        "approval_policy",
        "sandbox_policy",
        "model",
        "effort",
        "multi_agent_mode",
    }:
        raise ValueError("Codex active runtime context fields are malformed")
    for field in ("turn_id", "model", "effort", "multi_agent_mode"):
        require_nonblank(context.get(field), label=f"active runtime {field}")
    if Path(require_nonblank(context.get("cwd"), label="active runtime cwd")).resolve() != Path(
        repo_root
    ).resolve():
        raise ValueError("Codex active runtime repository cwd drifted")
    if context.get("approval_policy") not in {"on-request", "never"}:
        raise ValueError("Codex active runtime approval policy is unsupported")
    sandbox = context.get("sandbox_policy")
    if not isinstance(sandbox, dict) or set(sandbox) != {"type"} or sandbox.get(
        "type"
    ) not in {"danger-full-access", "workspace-write", "read-only"}:
        raise ValueError("Codex active runtime sandbox policy is unsupported")
    _require_sha256(
        payload.get("active_runtime_context_sha256"),
        label="active runtime context identity",
    )


def _validated_doctor_runtime(
    report: Any,
    *,
    repo_root: Path,
) -> dict[str, str]:
    if not isinstance(report, dict) or report.get("schemaVersion") != 1:
        raise ValueError("Codex doctor report schema is unsupported")
    checks = report.get("checks")
    if not isinstance(checks, dict):
        raise ValueError("Codex doctor report checks are missing")
    config = _required_doctor_check(checks, "config.load")
    provenance = _required_doctor_check(checks, "runtime.provenance")
    sandbox = _required_doctor_check(checks, "sandbox.helpers")
    cwd = Path(require_nonblank(config["details"].get("cwd"), label="doctor cwd"))
    if cwd.resolve() != repo_root.resolve():
        raise ValueError("Codex doctor report repository cwd drifted")
    version = require_nonblank(report.get("codexVersion"), label="Codex version")
    if provenance["details"].get("version") != version:
        raise ValueError("Codex doctor runtime version drifted")
    executable = Path(
        require_nonblank(
            provenance["details"].get("current executable"),
            label="Codex runtime executable",
        )
    )
    if not executable.is_absolute() or executable.name != "codex":
        raise ValueError("Codex doctor runtime executable is invalid")
    approval = _normalize_approval_policy(
        sandbox["details"].get("approval policy")
    )
    filesystem = require_nonblank(
        sandbox["details"].get("filesystem sandbox"),
        label="Codex filesystem sandbox",
    )
    sandbox_mode = (
        "danger-full-access" if filesystem == "unrestricted" else filesystem
    )
    return {
        "codex_version": version,
        "codex_executable": str(executable),
        "approval_policy": approval,
        "sandbox_mode": sandbox_mode,
    }


def _required_doctor_check(checks: dict[str, Any], name: str) -> dict[str, Any]:
    check = checks.get(name)
    if (
        not isinstance(check, dict)
        or check.get("status") != "ok"
        or not isinstance(check.get("details"), dict)
    ):
        raise ValueError(f"Codex doctor required check failed: {name}")
    return check


def _normalize_approval_policy(value: Any) -> str:
    text = require_nonblank(value, label="Codex approval policy")
    normalized = text.lower().replace("-", "").replace("_", "").replace(" ", "")
    mapping = {"onrequest": "on-request", "never": "never"}
    result = mapping.get(normalized)
    if result is None:
        raise ValueError("Codex approval policy is unsupported")
    return result


def _verify_profile_fragment(
    payload: dict[str, Any],
    *,
    expected_sandbox: str,
    expected_approval: str,
    expected_instructions: str,
    label: str,
) -> None:
    if set(payload) != {
        "sandbox_mode",
        "approval_policy",
        "developer_instructions",
        "features",
    }:
        raise ValueError(f"Codex {label} profile fields drifted")
    if (
        payload.get("sandbox_mode") != expected_sandbox
        or payload.get("approval_policy") != expected_approval
        or payload.get("developer_instructions") != expected_instructions
        or payload.get("features") != {"multi_agent": False}
    ):
        raise ValueError(f"Codex {label} profile semantics drifted")


def _profile_references(
    *,
    root: Path,
    profiles: dict[str, Any],
) -> dict[str, Any]:
    relative_paths = {
        "project_default": _PROJECT_DEFAULT_PATH,
        "hardware_supervised": _HARDWARE_PROFILE_PATH,
        "offline_autonomous": _OFFLINE_PROFILE_PATH,
    }
    return {
        name: {
            "relative_path": relative.as_posix(),
            "sha256": hashlib.sha256((root / relative).read_bytes()).hexdigest(),
            "size_bytes": (root / relative).stat().st_size,
            "sandbox_mode": profiles[name]["sandbox_mode"],
            "approval_policy": profiles[name]["approval_policy"],
        }
        for name, relative in relative_paths.items()
    }


def _parse_time(value: Any, *, label: str) -> datetime:
    text = require_nonblank(value, label=label)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a UTC offset")
    return parsed


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _require_sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")
