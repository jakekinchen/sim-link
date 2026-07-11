#!/usr/bin/env python3
"""Verify, discover, prepare, or execute one bounded live read-only observation."""

from __future__ import annotations

import argparse
import json
import sys
import time

from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.census_runtime_binding import (
    verify_census_runtime_source_bindings,
)
from scenesmith.robot_lab.live_readonly_observation import (
    DEFAULT_FOLLOWER_CALIBRATION_PATH,
    FFmpegNamedFiniteCamera,
    build_live_execution_contract,
    build_operator_presence_lease,
    build_private_capture_failure_evidence,
    build_private_observation_evidence,
    build_redacted_observation_manifest,
    capture_finite_camera_frames,
    capture_live_discovery,
    construct_pinned_feetech_bus,
    execute_live_servo_census,
    enumerate_serial_device_holders,
    verify_discovery_stability,
    verify_live_execution_contract,
    verify_redacted_observation_manifest,
    require_no_serial_device_holders,
    write_private_capture_failure_record,
    write_private_observation_bundle,
)


DEFAULT_PROJECT_STATE_PATH = Path("docs/autonomous-workflow/project_state.json")
DEFAULT_PRIVATE_ROOT = Path("outputs/robot_lab/live_readonly/private")
DEFAULT_MANIFEST_PATH = Path(
    "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-state",
        type=Path,
        default=DEFAULT_PROJECT_STATE_PATH,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "verify-offline",
        help="Verify pinned source/calibration/state without enumerating or opening devices.",
    )

    discover = subparsers.add_parser(
        "discover",
        help="Enumerate USB/serial/camera metadata without opening a port or camera.",
    )
    discover.add_argument("--session-id", required=True)
    discover.add_argument("--output", type=Path, required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Create a short private lease and exact execution contract from discovery.",
    )
    prepare.add_argument("--discovery", type=Path, required=True)
    prepare.add_argument("--camera-index", type=int, action="append", required=True)
    prepare.add_argument("--output", type=Path, required=True)

    capture = subparsers.add_parser(
        "capture",
        help="Execute the exact unexpired contract once and write private plus redacted evidence.",
    )
    capture.add_argument("--contract", type=Path, required=True)
    capture.add_argument("--private-output-dir", type=Path, required=True)
    capture.add_argument(
        "--manifest-output",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state = load_strict_json(_resolve_repo_path(args.project_state))
    if args.command == "verify-offline":
        source_binding = verify_census_runtime_source_bindings(repo_root=REPO_ROOT)
        calibration = DEFAULT_FOLLOWER_CALIBRATION_PATH.resolve()
        if not calibration.is_file():
            raise ValueError("Pinned follower calibration file is missing")
        print(
            json.dumps(
                {
                    "status": "offline_verified",
                    "hardware_enumerated": False,
                    "hardware_opened": False,
                    "source_bindings": source_binding["source_bindings"],
                    "protocol_version": source_binding["semantics"][
                        "sts3215_protocol_version"
                    ],
                    "t16_5a_state": state["tasks"]["T16.5a"]["state"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "discover":
        _require_t16_5a_verified(state)
        output = _resolve_private_path(args.output)
        now = _now_iso()
        discovery = capture_live_discovery(
            session_id=args.session_id,
            captured_at=now,
        )
        _require_new_path(output)
        dump_canonical_json(output, discovery)
        print(
            json.dumps(
                {
                    "status": "metadata_discovered",
                    "output": str(output),
                    "identity_sha256": discovery["identity_sha256"],
                    "serial_candidate_count": len(discovery["serial_candidates"]),
                    "camera_candidate_count": len(discovery["avfoundation_devices"]),
                    "serial_ports_opened": 0,
                    "cameras_opened": 0,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "prepare":
        _require_t16_5a_verified(state)
        discovery = load_strict_json(_resolve_private_path(args.discovery))
        issued = datetime.now().astimezone()
        hard_closeout = datetime.fromisoformat(state["run_window"]["hard_closeout"])
        expires = min(issued + timedelta(minutes=5), hard_closeout)
        issued_at = issued.isoformat(timespec="seconds")
        expires_at = expires.isoformat(timespec="seconds")
        lease = build_operator_presence_lease(
            project_state=state,
            session_id=discovery["session_id"],
            issued_at=issued_at,
            valid_until=expires_at,
        )
        contract = build_live_execution_contract(
            project_state=state,
            presence_lease=lease,
            discovery=discovery,
            camera_indexes=args.camera_index,
            calibration_path=DEFAULT_FOLLOWER_CALIBRATION_PATH,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        output = _resolve_private_path(args.output)
        _require_new_path(output)
        dump_canonical_json(output, contract)
        print(
            json.dumps(
                {
                    "status": "execution_contract_prepared",
                    "output": str(output),
                    "identity_sha256": contract["identity_sha256"],
                    "session_id": contract["session_id"],
                    "valid_until": contract["expires_at"],
                    "camera_indexes": [
                        camera["index"] for camera in contract["cameras"]
                    ],
                    "physical_follower_commanded": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    contract = load_strict_json(_resolve_private_path(args.contract))
    started_ns = time.monotonic_ns()
    verify_live_execution_contract(contract, project_state=state, now=_now_iso())
    before = capture_live_discovery(
        session_id=contract["session_id"],
        captured_at=_now_iso(),
    )
    verify_discovery_stability(contract["discovery"], before)
    serial_path = contract["live_census_contract"]["target_device_identity"]["usb"][
        "canonical_path"
    ]
    pre_open_serial_holders = enumerate_serial_device_holders(serial_path)
    require_no_serial_device_holders(pre_open_serial_holders)
    servo_result = execute_live_servo_census(
        contract,
        project_state=state,
        now=_now_iso(),
        bus_factory=lambda census_contract: construct_pinned_feetech_bus(
            repo_root=REPO_ROOT,
            census_contract=census_contract,
        ),
        monotonic_ns=time.monotonic_ns,
    )
    post_close_serial_holders = enumerate_serial_device_holders(serial_path)
    require_no_serial_device_holders(post_close_serial_holders)
    private_output = _resolve_private_directory(args.private_output_dir)
    try:
        frames = capture_finite_camera_frames(
            contract,
            project_state=state,
            now=_now_iso(),
            camera_factory=lambda camera: FFmpegNamedFiniteCamera(
                camera,
                expected_frame_count=contract["frame_count_per_camera"],
                read_timeout_seconds=contract["camera_read_timeout_seconds"],
                monotonic_ns=time.monotonic_ns,
            ),
            monotonic_ns=time.monotonic_ns,
            wall_time=_now_iso,
        )
    except BaseException as capture_error:
        elapsed_seconds = (time.monotonic_ns() - started_ns) / 1_000_000_000
        try:
            failure = build_private_capture_failure_evidence(
                execution_contract=contract,
                servo_result=servo_result,
                error=capture_error,
                pre_open_discovery=before,
                pre_open_serial_holders=pre_open_serial_holders,
                post_close_serial_holders=post_close_serial_holders,
                failed_at=_now_iso(),
                elapsed_seconds=elapsed_seconds,
            )
            failure_reference = write_private_capture_failure_record(
                output_directory=private_output,
                failure_evidence=failure,
            )
        except BaseException as evidence_error:
            raise BaseExceptionGroup(
                "Live camera capture failed and failure evidence also failed",
                [capture_error, evidence_error],
            )
        print(
            json.dumps(
                {
                    "status": "live_read_only_observation_rejected",
                    "private_failure_output": str(private_output),
                    "failure_reference": failure_reference,
                    "tracked_manifest_written": False,
                    "proof_labels": [],
                    "physical_follower_commanded": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        raise
    after = capture_live_discovery(
        session_id=contract["session_id"],
        captured_at=_now_iso(),
    )
    verify_discovery_stability(contract["discovery"], after)
    elapsed_seconds = (time.monotonic_ns() - started_ns) / 1_000_000_000
    if elapsed_seconds > contract["max_duration_seconds"]:
        raise RuntimeError(
            "Live read-only execution exceeded its finite duration bound"
        )
    private = build_private_observation_evidence(
        execution_contract=contract,
        servo_result=servo_result,
        frames=frames,
        pre_open_discovery=before,
        post_close_discovery=after,
        pre_open_serial_holders=pre_open_serial_holders,
        post_close_serial_holders=post_close_serial_holders,
    )
    refs = write_private_observation_bundle(
        output_directory=private_output,
        private_evidence=private,
        frames=frames,
    )
    manifest = build_redacted_observation_manifest(
        private_evidence=private,
        private_bundle_refs=refs,
    )
    verify_redacted_observation_manifest(
        manifest,
        private_evidence=private,
        private_bundle_refs=refs,
    )
    manifest_output = _resolve_manifest_path(args.manifest_output)
    _require_new_path(manifest_output)
    dump_canonical_json(manifest_output, manifest)
    print(
        json.dumps(
            {
                "status": "live_read_only_observation_complete",
                "private_output": str(private_output),
                "manifest_output": str(manifest_output),
                "manifest_identity_sha256": manifest["identity_sha256"],
                "proof_labels": manifest["proof_labels"],
                "operation_counts": manifest["operation_counts"],
                "physical_follower_commanded": False,
                "elapsed_seconds": elapsed_seconds,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve_repo_path(path: Path) -> Path:
    resolved = path if path.is_absolute() else REPO_ROOT / path
    try:
        resolved.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Repository path escapes the repository") from exc
    return resolved


def _resolve_private_path(path: Path) -> Path:
    resolved = _resolve_repo_path(path)
    private_root = (REPO_ROOT / DEFAULT_PRIVATE_ROOT).resolve()
    try:
        resolved.resolve().relative_to(private_root)
    except ValueError as exc:
        raise ValueError(
            "Private live evidence path must remain under the private output root"
        ) from exc
    return resolved


def _resolve_private_directory(path: Path) -> Path:
    return _resolve_private_path(path)


def _resolve_manifest_path(path: Path) -> Path:
    resolved = _resolve_repo_path(path)
    manifest_root = (REPO_ROOT / "configurations" / "robot_lab").resolve()
    try:
        resolved.resolve().relative_to(manifest_root)
    except ValueError as exc:
        raise ValueError(
            "Redacted manifest must remain under configurations/robot_lab"
        ) from exc
    return resolved


def _require_t16_5a_verified(state: dict) -> None:
    if state.get("tasks", {}).get("T16.5a", {}).get("state") != "verified":
        raise ValueError("T16.5a is not verified")


def _require_new_path(path: Path) -> None:
    if path.exists():
        raise ValueError(f"Refusing to overwrite immutable live evidence: {path}")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
