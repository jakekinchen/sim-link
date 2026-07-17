#!/usr/bin/env python3
"""Preflight, capture, or verify one owner-present RGB-only camera census."""

from __future__ import annotations

import argparse
import hashlib
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
    sign_payload,
)
from scenesmith.robot_lab.authority_composer import (
    compose_rgb_camera_census_authority,
    verify_rgb_camera_census_authority,
)
from scenesmith.robot_lab.hardware_execution_profile import (
    capture_hardware_execution_profile_evidence,
)
from scenesmith.robot_lab.live_readonly_observation import (
    FFmpegNamedFiniteCamera,
    enumerate_camera_metadata,
)
from scenesmith.robot_lab.rgb_camera_census import (
    build_private_rgb_camera_census,
    build_redacted_rgb_camera_manifest,
    build_rgb_camera_discovery,
    execute_rgb_camera_census,
    verify_private_rgb_camera_census,
    verify_redacted_rgb_camera_manifest,
    write_private_rgb_camera_bundle,
)


DEFAULT_PROJECT_STATE = Path("docs/autonomous-workflow/project_state.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-state", type=Path, default=DEFAULT_PROJECT_STATE)
    commands = parser.add_subparsers(dest="command", required=True)

    preflight = commands.add_parser("preflight")
    preflight.add_argument("--session-id", required=True)
    preflight.add_argument("--runtime-profile-output", type=Path, required=True)
    preflight.add_argument("--private-output-dir", type=Path, required=True)
    preflight.add_argument("--manifest-output", type=Path, required=True)
    preflight.add_argument("--request-output", type=Path, required=True)
    preflight.add_argument("--decision-output", type=Path, required=True)
    preflight.add_argument("--permit-output", type=Path, required=True)

    capture = commands.add_parser("capture")
    capture.add_argument("--runtime-profile", type=Path, required=True)
    capture.add_argument("--request", type=Path, required=True)
    capture.add_argument("--decision", type=Path, required=True)
    capture.add_argument("--permit", type=Path, required=True)

    verify = commands.add_parser("verify")
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
    output_paths = [
        args.runtime_profile_output,
        args.private_output_dir,
        args.manifest_output,
        args.request_output,
        args.decision_output,
        args.permit_output,
    ]
    for value in output_paths:
        path = _resolve_repo(value)
        if path.exists() or path.is_symlink():
            raise ValueError(f"Refusing to overwrite RGB camera artifact: {path}")
    now = datetime.now().astimezone()
    owner_end = datetime.fromisoformat(
        state["owner_authority"]["current_rgb_camera_census_window"][
            "valid_through"
        ]
    )
    expires = min(now + timedelta(minutes=10), owner_end)
    runtime = capture_hardware_execution_profile_evidence(
        repo_root=REPO_ROOT,
        captured_at=now.isoformat(timespec="seconds"),
    )
    request, decision, permit = compose_rgb_camera_census_authority(
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
        raise RuntimeError("RGB camera central authority denied; no permit written")
    for path, payload in (
        (_resolve_private_authority(args.runtime_profile_output), runtime),
        (_resolve_configuration(args.request_output), request),
        (_resolve_configuration(args.decision_output), decision),
        (_resolve_configuration(args.permit_output), permit),
    ):
        if path.exists() or path.is_symlink():
            raise ValueError(f"Refusing to overwrite RGB camera artifact: {path}")
        dump_canonical_json(path, payload)
    print(
        json.dumps(
            {
                "status": "rgb_camera_census_preflight_granted",
                "hardware_enumerated": False,
                "hardware_opened": False,
                "session_id": permit["session_id"],
                "runtime_profile_identity_sha256": runtime["identity_sha256"],
                "decision_identity_sha256": decision["identity_sha256"],
                "permit_identity_sha256": permit["identity_sha256"],
                "remote_boundary_commit": permit["remote_boundary_commit"],
                "expires_at": permit["expires_at"],
                "depth_stream_authorized": False,
                "serial_access_authorized": False,
                "motion_authorized": False,
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
    verify_rgb_camera_census_authority(
        request=request,
        decision=decision,
        permit=permit,
        project_state=state,
        runtime_profile=runtime,
        repo_root=REPO_ROOT,
        now=_now(),
    )
    private_output = _resolve_private_directory(Path(permit["private_output_dir"]))
    manifest_output = _resolve_configuration(Path(permit["manifest_output"]))
    if private_output.exists() or private_output.is_symlink() or manifest_output.exists():
        raise ValueError("RGB camera census one-use output already exists")
    hardware_enumeration_attempted = False
    camera_open_attempted = False
    try:
        hardware_enumeration_attempted = True
        avfoundation, system_cameras = enumerate_camera_metadata()
        discovery = build_rgb_camera_discovery(
            session_id=permit["session_id"],
            captured_at=_now(),
            avfoundation_devices=avfoundation,
            system_cameras=system_cameras,
        )
        camera_open_attempted = True
        frames, result = execute_rgb_camera_census(
            permit=permit,
            discovery=discovery,
            camera_factory=lambda camera: FFmpegNamedFiniteCamera(
                camera,
                expected_frame_count=1,
                framerate_fps=30,
                read_timeout_seconds=30,
                monotonic_ns=time.monotonic_ns,
            ),
            monotonic_ns=time.monotonic_ns,
            wall_time=_now,
        )
        private = build_private_rgb_camera_census(
            runtime_profile_identity_sha256=runtime["identity_sha256"],
            request=request,
            decision=decision,
            permit=permit,
            discovery=discovery,
            result=result,
            frames=frames,
            completed_at=_now(),
        )
        refs = write_private_rgb_camera_bundle(
            output_directory=private_output,
            private_evidence=private,
            frames=frames,
        )
        manifest = build_redacted_rgb_camera_manifest(
            private_evidence=private,
            private_bundle_refs=refs,
        )
        verify_redacted_rgb_camera_manifest(
            manifest,
            private_evidence=private,
            private_bundle_refs=refs,
        )
        dump_canonical_json(manifest_output, manifest)
    except BaseException as error:
        _write_failure(
            output_directory=private_output,
            runtime=runtime,
            request=request,
            decision=decision,
            permit=permit,
            hardware_enumeration_attempted=hardware_enumeration_attempted,
            camera_open_attempted=camera_open_attempted,
            error=error,
        )
        raise
    print(
        json.dumps(
            {
                "status": "rgb_camera_census_complete",
                "session_id": manifest["session_id"],
                "manifest_output": str(manifest_output),
                "manifest_identity_sha256": manifest["identity_sha256"],
                "camera_roles": [
                    camera["camera_role"] for camera in manifest["cameras"]
                ],
                "selected_input_modes": [
                    camera["selected_input_mode"] for camera in manifest["cameras"]
                ],
                "coarse_observation_receive_latency_ns": [
                    camera["coarse_observation_receive_latency_ns"]
                    for camera in manifest["cameras"]
                ],
                "rgb_streams_opened": 2,
                "depth_streams_opened": 0,
                "serial_devices_enumerated": 0,
                "motion_commands": 0,
                "physical_follower_commanded": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _verify(args: argparse.Namespace) -> int:
    output = _resolve_private_directory(args.private_output_dir)
    manifest = load_strict_json(_resolve_configuration(args.manifest))
    private = load_strict_json(output / "private_evidence.json")
    refs = load_strict_json(output / "private_bundle_refs.json")
    private_path = output / "private_evidence.json"
    if (
        refs["private_evidence_relative_path"] != private_path.name
        or refs["private_evidence_file_sha256"]
        != hashlib.sha256(private_path.read_bytes()).hexdigest()
        or refs["private_evidence_size_bytes"] != private_path.stat().st_size
    ):
        raise ValueError("RGB camera private evidence file reference drifted")
    frames = []
    signed_by_role = {
        frame["camera_role"]: frame for frame in private["signed_frames"]
    }
    for ref in refs["frames"]:
        role = ref["camera_role"]
        frame_path = (output / ref["relative_path"]).resolve()
        if (
            frame_path.parent != output.resolve()
            or frame_path.is_symlink()
            or not frame_path.is_file()
            or hashlib.sha256(frame_path.read_bytes()).hexdigest()
            != ref["file_sha256"]
            or frame_path.stat().st_size != ref["size_bytes"]
            or ref["signed_frame_identity_sha256"]
            != signed_by_role[role]["identity_sha256"]
        ):
            raise ValueError("RGB camera private frame file reference drifted")
        frames.append(
            {
                "camera_role": role,
                "frame_bytes": frame_path.read_bytes(),
                "signed_frame": signed_by_role[role],
            }
        )
    verify_private_rgb_camera_census(private, frames=frames)
    verify_redacted_rgb_camera_manifest(
        manifest,
        private_evidence=private,
        private_bundle_refs=refs,
    )
    print(
        json.dumps(
            {
                "status": "rgb_camera_census_verified",
                "manifest_identity_sha256": manifest["identity_sha256"],
                "private_identity_sha256": private["identity_sha256"],
                "frame_count": len(frames),
                "depth_streams_opened": manifest["depth_streams_opened"],
                "motion_commands": manifest["motion_commands"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _write_failure(
    *,
    output_directory: Path,
    runtime: dict,
    request: dict,
    decision: dict,
    permit: dict,
    hardware_enumeration_attempted: bool,
    camera_open_attempted: bool,
    error: BaseException,
) -> None:
    if output_directory.is_symlink():
        return
    if not output_directory.exists():
        output_directory.mkdir(parents=True, exist_ok=False)
    elif not output_directory.is_dir():
        return
    failure_path = output_directory / "failure.json"
    if failure_path.exists() or failure_path.is_symlink():
        return
    failure = sign_payload(
        {
            "schema_version": "scenesmith.rgb_camera_census_failure.v1",
            "status": "rejected",
            "failed_at": _now(),
            "runtime_profile_identity_sha256": runtime["identity_sha256"],
            "request_identity_sha256": request["identity_sha256"],
            "decision_identity_sha256": decision["identity_sha256"],
            "permit_identity_sha256": permit["identity_sha256"],
            "hardware_enumeration_attempted": hardware_enumeration_attempted,
            "camera_open_attempted": camera_open_attempted,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "proof_labels": [],
            "depth_stream_authorized": False,
            "serial_access_authorized": False,
            "motion_authorized": False,
            "physical_follower_commanded": False,
        }
    )
    dump_canonical_json(failure_path, failure)


def _resolve_repo(path: Path) -> Path:
    resolved = path if path.is_absolute() else REPO_ROOT / path
    resolved = resolved.resolve()
    if not resolved.is_relative_to(REPO_ROOT.resolve()):
        raise ValueError("RGB camera path escapes repository")
    return resolved


def _resolve_configuration(path: Path) -> Path:
    resolved = _resolve_repo(path)
    root = (REPO_ROOT / "configurations/robot_lab").resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError("RGB camera configuration path escapes required root")
    return resolved


def _resolve_private_directory(path: Path) -> Path:
    resolved = _resolve_repo(path)
    root = (REPO_ROOT / "outputs/robot_lab/rgb_camera_census/private").resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError("RGB camera private path escapes required root")
    return resolved


def _resolve_private_authority(path: Path) -> Path:
    resolved = _resolve_repo(path)
    root = (REPO_ROOT / "outputs/robot_lab/rgb_camera_census/authority").resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError("RGB camera authority path escapes required root")
    return resolved


def _relative(path: Path) -> str:
    return _resolve_repo(path).relative_to(REPO_ROOT.resolve()).as_posix()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
