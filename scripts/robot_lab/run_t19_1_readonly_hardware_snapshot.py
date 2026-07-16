#!/usr/bin/env python3
"""Preflight, execute, or verify one centrally authorized T19.1 census."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time

from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.authority_composer import (
    compose_t19_1_readonly_session_authority,
    verify_t19_1_readonly_session_authority,
)
from scenesmith.robot_lab.census_runtime_binding import (
    verify_census_runtime_source_bindings,
)
from scenesmith.robot_lab.hardware_execution_profile import (
    capture_hardware_execution_profile_evidence,
)
from scenesmith.robot_lab.live_readonly_observation import (
    DEFAULT_FOLLOWER_CALIBRATION_PATH,
    enumerate_serial_identity_holders,
    require_no_serial_identity_holders,
    resolve_follower_identity,
    verify_serial_identity_holder_stability,
)
from scenesmith.robot_lab.t19_1_readonly_hardware_snapshot import (
    build_t19_1_private_snapshot,
    build_t19_1_redacted_manifest,
    capture_t19_1_serial_discovery,
    default_t19_1_bus_factory,
    execute_t19_1_readonly_servo_census,
    verify_t19_1_private_snapshot,
    verify_t19_1_redacted_manifest,
    write_t19_1_private_snapshot,
)


DEFAULT_PROJECT_STATE = Path("docs/autonomous-workflow/project_state.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-state", type=Path, default=DEFAULT_PROJECT_STATE)
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--session-id", required=True)
    preflight.add_argument("--runtime-profile-output", type=Path, required=True)
    preflight.add_argument("--private-output-dir", type=Path, required=True)
    preflight.add_argument("--manifest-output", type=Path, required=True)
    preflight.add_argument("--request-output", type=Path, required=True)
    preflight.add_argument("--decision-output", type=Path, required=True)
    preflight.add_argument("--permit-output", type=Path, required=True)

    capture = subparsers.add_parser("capture")
    capture.add_argument("--runtime-profile", type=Path, required=True)
    capture.add_argument("--request", type=Path, required=True)
    capture.add_argument("--decision", type=Path, required=True)
    capture.add_argument("--permit", type=Path, required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--private-output-dir", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state = load_strict_json(_resolve_repo(args.project_state))
    if args.command == "preflight":
        return _preflight(args, state)
    if args.command == "capture":
        return _capture(args, state)
    return _verify(args)


def _preflight(args: argparse.Namespace, state: dict) -> int:
    outputs = [
        args.runtime_profile_output,
        args.request_output,
        args.decision_output,
        args.permit_output,
        args.private_output_dir,
        args.manifest_output,
    ]
    for value in outputs:
        path = _resolve_repo(value)
        if path.exists():
            raise ValueError(f"Refusing to overwrite T19.1 artifact: {path}")
    now = datetime.now().astimezone()
    effective_end = min(
        datetime.fromisoformat(state["run_window"]["hard_closeout"]),
        datetime.fromisoformat(
            state["owner_authority"]["current_hardware_access_window"][
                "valid_through_approximate"
            ]
        ),
    )
    expires = min(now + timedelta(minutes=5), effective_end)
    runtime = capture_hardware_execution_profile_evidence(
        repo_root=REPO_ROOT,
        captured_at=now.isoformat(timespec="seconds"),
    )
    request, decision, permit = compose_t19_1_readonly_session_authority(
        project_state=state,
        runtime_profile=runtime,
        repo_root=REPO_ROOT,
        session_id=args.session_id,
        issued_at=now.isoformat(timespec="seconds"),
        expires_at=expires.isoformat(timespec="seconds"),
        private_output_dir=_relative(args.private_output_dir),
        manifest_output=_relative(args.manifest_output),
    )
    if decision["granted"] is not True or permit is None:
        print(json.dumps(decision, indent=2, sort_keys=True))
        raise RuntimeError("T19.1 central authority denied; no permit was written")
    runtime_output = _resolve_private_authority(args.runtime_profile_output)
    for path, payload in (
        (runtime_output, runtime),
        (_resolve_configuration(args.request_output), request),
        (_resolve_configuration(args.decision_output), decision),
        (_resolve_configuration(args.permit_output), permit),
    ):
        if path.exists():
            raise ValueError(f"Refusing to overwrite T19.1 artifact: {path}")
        dump_canonical_json(path, payload)
    print(
        json.dumps(
            {
                "status": "t19_1_preflight_granted",
                "hardware_accessed": False,
                "session_id": permit["session_id"],
                "runtime_profile_identity_sha256": runtime["identity_sha256"],
                "decision_identity_sha256": decision["identity_sha256"],
                "permit_identity_sha256": permit["identity_sha256"],
                "remote_boundary_commit": permit["remote_boundary_commit"],
                "expires_at": permit["expires_at"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _capture(args: argparse.Namespace, state: dict) -> int:
    runtime = load_strict_json(_resolve_private_authority(args.runtime_profile))
    request = load_strict_json(_resolve_configuration(args.request))
    decision = load_strict_json(_resolve_configuration(args.decision))
    permit = load_strict_json(_resolve_configuration(args.permit))
    now = _now()
    verify_t19_1_readonly_session_authority(
        request=request,
        decision=decision,
        permit=permit,
        project_state=state,
        runtime_profile=runtime,
        repo_root=REPO_ROOT,
        now=now,
    )
    verify_census_runtime_source_bindings(repo_root=REPO_ROOT)
    private_output = _resolve_repo(Path(permit["private_output_dir"]))
    manifest_output = _resolve_configuration(Path(permit["manifest_output"]))
    if private_output.exists() or manifest_output.exists():
        raise ValueError("T19.1 one-use output already exists; permit is consumed")
    calibration = DEFAULT_FOLLOWER_CALIBRATION_PATH.resolve()
    if not calibration.is_file():
        raise ValueError("Pinned follower calibration is missing")

    discovery = None
    pre_holders = None
    post_holders = None
    hardware_open_attempted = False
    try:
        discovery = capture_t19_1_serial_discovery(
            session_id=permit["session_id"],
            captured_at=_now(),
        )
        identity = resolve_follower_identity(discovery)
        serial = identity["usb"]
        pre_holders = enumerate_serial_identity_holders(
            serial["canonical_path"],
            serial["observed_aliases"],
        )
        require_no_serial_identity_holders(pre_holders)
        hardware_open_attempted = True
        contract, result = execute_t19_1_readonly_servo_census(
            permit=permit,
            discovery=discovery,
            calibration_file_sha256=hashlib.sha256(calibration.read_bytes()).hexdigest(),
            bus_factory=default_t19_1_bus_factory(repo_root=REPO_ROOT),
            monotonic_ns=time.monotonic_ns,
        )
        post_holders = enumerate_serial_identity_holders(
            serial["canonical_path"],
            serial["observed_aliases"],
        )
        require_no_serial_identity_holders(post_holders)
        verify_serial_identity_holder_stability(pre_holders, post_holders)
        private = build_t19_1_private_snapshot(
            runtime_profile_identity_sha256=runtime["identity_sha256"],
            request=request,
            decision=decision,
            permit=permit,
            discovery=discovery,
            census_contract=contract,
            servo_result=result,
            pre_open_holders=pre_holders,
            post_close_holders=post_holders,
            completed_at=_now(),
        )
        reference = write_t19_1_private_snapshot(
            output_directory=private_output,
            private_snapshot=private,
        )
        manifest = build_t19_1_redacted_manifest(
            private_snapshot=private,
            private_reference=reference,
        )
        verify_t19_1_redacted_manifest(
            manifest,
            private_snapshot=private,
            private_reference=reference,
        )
        dump_canonical_json(manifest_output, manifest)
    except BaseException as error:
        if discovery is not None:
            try:
                identity = resolve_follower_identity(discovery)
                serial = identity["usb"]
                post_holders = enumerate_serial_identity_holders(
                    serial["canonical_path"],
                    serial["observed_aliases"],
                )
            except BaseException:
                post_holders = None
        _write_private_failure(
            output_directory=private_output,
            runtime=runtime,
            request=request,
            decision=decision,
            permit=permit,
            discovery=discovery,
            pre_holders=pre_holders,
            post_holders=post_holders,
            hardware_open_attempted=hardware_open_attempted,
            error=error,
        )
        raise
    print(
        json.dumps(
            {
                "status": "t19_1_readonly_hardware_snapshot_complete",
                "session_id": manifest["session_id"],
                "manifest_output": str(manifest_output),
                "manifest_identity_sha256": manifest["identity_sha256"],
                "servo_result_identity_sha256": manifest[
                    "servo_result_identity_sha256"
                ],
                "operation_counts": manifest["operation_counts"],
                "proof_labels": manifest["proof_labels"],
                "physical_follower_commanded": False,
                "register_write_count": 0,
                "torque_change_count": 0,
                "motion_command_count": 0,
                "camera_accessed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _verify(args: argparse.Namespace) -> int:
    output = _resolve_repo(args.private_output_dir)
    private_path = output / "private_readonly_hardware_snapshot.json"
    private = load_strict_json(private_path)
    reference = {
        "filename": private_path.name,
        "sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
        "size_bytes": private_path.stat().st_size,
        "identity_sha256": private["identity_sha256"],
    }
    manifest = load_strict_json(_resolve_configuration(args.manifest))
    verify_t19_1_private_snapshot(private)
    verify_t19_1_redacted_manifest(
        manifest,
        private_snapshot=private,
        private_reference=reference,
    )
    print(
        json.dumps(
            {
                "status": "t19_1_snapshot_verified",
                "private_identity_sha256": private["identity_sha256"],
                "manifest_identity_sha256": manifest["identity_sha256"],
                "read_successes": manifest["operation_counts"]["read_successes"],
                "unsafe_counts": {
                    "register_writes": manifest["register_write_count"],
                    "torque_changes": manifest["torque_change_count"],
                    "motion_commands": manifest["motion_command_count"],
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _write_private_failure(
    *,
    output_directory: Path,
    runtime: dict,
    request: dict,
    decision: dict,
    permit: dict,
    discovery: dict | None,
    pre_holders: dict | None,
    post_holders: dict | None,
    hardware_open_attempted: bool,
    error: BaseException,
) -> None:
    if output_directory.exists():
        return
    payload = sign_payload(
        {
            "schema_version": "scenesmith.t19_1_readonly_hardware_failure_private.v1",
            "evidence_name": "pi05_t19_1_private_readonly_hardware_failure",
            "status": "rejected",
            "session_id": permit["session_id"],
            "failed_at": _now(),
            "runtime_profile_identity_sha256": runtime["identity_sha256"],
            "request_identity_sha256": request["identity_sha256"],
            "decision_identity_sha256": decision["identity_sha256"],
            "permit_identity_sha256": permit["identity_sha256"],
            "discovery_identity_sha256": (
                discovery.get("identity_sha256") if discovery else None
            ),
            "pre_open_holder_snapshot_identity_sha256": (
                pre_holders.get("identity_sha256") if pre_holders else None
            ),
            "post_close_holder_snapshot_identity_sha256": (
                post_holders.get("identity_sha256") if post_holders else None
            ),
            "error_type": type(error).__name__,
            "hardware_opened": hardware_open_attempted,
            "proof_labels": [],
            "physical_follower_commanded": False,
            "tracked_manifest_written": False,
        }
    )
    temporary = output_directory.with_name(output_directory.name + ".tmp")
    try:
        temporary.mkdir(parents=True, exist_ok=False)
        dump_canonical_json(temporary / "private_failure.json", payload)
        temporary.replace(output_directory)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        raise


def _resolve_repo(path: Path) -> Path:
    resolved = path if path.is_absolute() else REPO_ROOT / path
    resolved = resolved.resolve()
    if not resolved.is_relative_to(REPO_ROOT.resolve()):
        raise ValueError("T19.1 path escapes the repository")
    return resolved


def _resolve_configuration(path: Path) -> Path:
    resolved = _resolve_repo(path)
    if not resolved.is_relative_to((REPO_ROOT / "configurations/robot_lab").resolve()):
        raise ValueError("T19.1 tracked artifact must stay under configurations/robot_lab")
    return resolved


def _resolve_private_authority(path: Path) -> Path:
    resolved = _resolve_repo(path)
    if not resolved.is_relative_to(
        (REPO_ROOT / "outputs/robot_lab/t19_1/authority").resolve()
    ):
        raise ValueError("T19.1 runtime profile must stay under private authority output")
    return resolved


def _relative(path: Path) -> str:
    return _resolve_repo(path).relative_to(REPO_ROOT.resolve()).as_posix()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
