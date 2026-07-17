"""Bounded owner-present D405/C922 RGB-only camera census evidence."""

from __future__ import annotations

import copy
import hashlib

from pathlib import Path
from typing import Any, Callable, Protocol

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.authority_composer import (
    RGB_CAMERA_CENSUS_ALLOWED_OPERATIONS,
    RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED,
    RGB_CAMERA_CENSUS_DECISION_SCHEMA_VERSION,
    RGB_CAMERA_CENSUS_MAX_SESSION_SECONDS,
    RGB_CAMERA_CENSUS_PERMIT_SCHEMA_VERSION,
    RGB_CAMERA_CENSUS_REQUEST_SCHEMA_VERSION,
    RGB_CAMERA_CENSUS_TARGETS,
)
from scenesmith.robot_lab.live_readonly_observation import (
    build_live_discovery_snapshot,
    select_camera_input_mode,
)


DISCOVERY_SCHEMA_VERSION = "scenesmith.rgb_camera_discovery.v1"
RESULT_SCHEMA_VERSION = "scenesmith.rgb_camera_census_result.v1"
FRAME_SCHEMA_VERSION = "scenesmith.rgb_camera_signed_frame.v1"
PRIVATE_SCHEMA_VERSION = "scenesmith.rgb_camera_census_private.v1"
PRIVATE_REFS_SCHEMA_VERSION = "scenesmith.rgb_camera_census_private_refs.v1"
MANIFEST_SCHEMA_VERSION = "scenesmith.rgb_camera_census_manifest.v1"
FAILURE_SCHEMA_VERSION = "scenesmith.rgb_camera_census_failure.v1"
FAILURE_MANIFEST_SCHEMA_VERSION = (
    "scenesmith.rgb_camera_census_failure_manifest.v1"
)
PROOF_LABEL = "owner_present_rgb_camera_census_observed"


class FiniteCamera(Protocol):
    def open(self) -> None: ...
    def read(self) -> dict[str, Any]: ...
    def release(self) -> None: ...
    def audit(self) -> dict[str, Any]: ...


def build_rgb_camera_discovery(
    *,
    session_id: str,
    captured_at: str,
    avfoundation_devices: list[dict[str, Any]],
    system_cameras: list[dict[str, Any]],
) -> dict[str, Any]:
    """Normalize and sign camera-only metadata without serial candidates."""

    live = build_live_discovery_snapshot(
        session_id=session_id,
        captured_at=captured_at,
        serial_candidates=[],
        avfoundation_devices=avfoundation_devices,
        system_cameras=system_cameras,
    )
    return sign_payload(
        {
            "schema_version": DISCOVERY_SCHEMA_VERSION,
            "discovery_name": "owner_present_rgb_camera_only_metadata",
            "session_id": live["session_id"],
            "captured_at": live["captured_at"],
            "avfoundation_devices": copy.deepcopy(live["avfoundation_devices"]),
            "system_cameras": copy.deepcopy(live["system_cameras"]),
            "serial_candidates": [],
            "camera_metadata_enumerated": True,
            "serial_devices_enumerated": 0,
            "cameras_opened": 0,
            "depth_streams_opened": 0,
            "physical_follower_commanded": False,
        }
    )


def verify_rgb_camera_discovery(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="RGB camera discovery")
    expected_fields = {
        "schema_version",
        "discovery_name",
        "session_id",
        "captured_at",
        "avfoundation_devices",
        "system_cameras",
        "serial_candidates",
        "camera_metadata_enumerated",
        "serial_devices_enumerated",
        "cameras_opened",
        "depth_streams_opened",
        "physical_follower_commanded",
        "identity_sha256",
    }
    if set(payload) != expected_fields:
        raise ValueError("RGB camera discovery fields are malformed")
    if (
        payload.get("schema_version") != DISCOVERY_SCHEMA_VERSION
        or payload.get("discovery_name")
        != "owner_present_rgb_camera_only_metadata"
        or payload.get("serial_candidates") != []
        or payload.get("camera_metadata_enumerated") is not True
        or payload.get("serial_devices_enumerated") != 0
        or payload.get("cameras_opened") != 0
        or payload.get("depth_streams_opened") != 0
        or payload.get("physical_follower_commanded") is not False
    ):
        raise ValueError("RGB camera discovery classification drifted")
    rebuilt = build_rgb_camera_discovery(
        session_id=payload.get("session_id"),
        captured_at=payload.get("captured_at"),
        avfoundation_devices=payload.get("avfoundation_devices"),
        system_cameras=payload.get("system_cameras"),
    )
    if payload != rebuilt:
        raise ValueError("RGB camera discovery normalization drifted")


def execute_rgb_camera_census(
    *,
    permit: dict[str, Any],
    discovery: dict[str, Any],
    camera_factory: Callable[[dict[str, Any]], FiniteCamera],
    monotonic_ns: Callable[[], int],
    wall_time: Callable[[], str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Capture exactly one RGB PNG from each exact target, sequentially."""

    _verify_permit_safety(permit)
    verify_rgb_camera_discovery(discovery)
    if discovery.get("session_id") != permit.get("session_id"):
        raise ValueError("RGB camera discovery session drifted from permit")
    selected = _resolve_target_cameras(discovery)
    frames: list[dict[str, Any]] = []
    result_cameras: list[dict[str, Any]] = []
    capture_started = monotonic_ns()
    previous_finished: int | None = None
    for target, camera in selected:
        input_mode = select_camera_input_mode(camera)
        avfoundation = _resolve_avfoundation_device(discovery, camera["name"])
        execution_camera = {
            "index": avfoundation["index"],
            "name": camera["name"],
            "unique_id": camera["unique_id"],
            "model_id": camera["model_id"],
            "input_mode": input_mode,
        }
        instance: FiniteCamera | None = None
        primary_error: BaseException | None = None
        release_error: BaseException | None = None
        frame: dict[str, Any] | None = None
        try:
            instance = camera_factory(copy.deepcopy(execution_camera))
            instance.open()
            call_started = monotonic_ns()
            frame = instance.read()
            call_finished = monotonic_ns()
        except BaseException as exc:
            primary_error = exc
        finally:
            if instance is not None:
                try:
                    instance.release()
                except BaseException as exc:
                    release_error = exc
        if primary_error is not None and release_error is not None:
            raise BaseExceptionGroup(
                "RGB camera capture and release both failed",
                [primary_error, release_error],
            )
        if primary_error is not None:
            raise primary_error
        if release_error is not None:
            raise release_error
        if instance is None or frame is None:
            raise RuntimeError("RGB camera capture returned no frame")
        audit = instance.audit()
        _verify_camera_audit(audit)
        normalized = _normalize_frame(
            frame,
            input_mode=input_mode,
            call_started=call_started,
            call_finished=call_finished,
        )
        if (
            previous_finished is not None
            and normalized["receive_started_monotonic_ns"] < previous_finished
        ):
            raise ValueError("RGB camera receive intervals overlap or regress")
        previous_finished = normalized["receive_finished_monotonic_ns"]
        frame_sha = hashlib.sha256(normalized["frame_bytes"]).hexdigest()
        signed_frame = sign_payload(
            {
                "schema_version": FRAME_SCHEMA_VERSION,
                "camera_role": target["camera_role"],
                "camera_name": camera["name"],
                "camera_model_id": camera["model_id"],
                "selected_input_mode": copy.deepcopy(input_mode),
                "host_wall_time": require_nonblank(
                    wall_time(), label="RGB frame host wall time"
                ),
                "clock_source": "host_monotonic_ns",
                "receive_started_monotonic_ns": normalized[
                    "receive_started_monotonic_ns"
                ],
                "receive_finished_monotonic_ns": normalized[
                    "receive_finished_monotonic_ns"
                ],
                "coarse_observation_receive_latency_ns": (
                    normalized["receive_finished_monotonic_ns"]
                    - normalized["receive_started_monotonic_ns"]
                ),
                "t20_22_timing_fields": {
                    "frame_age_ns": None,
                    "observation_assembly_ns": None,
                    "inference_latency_ns": None,
                    "action_hold_ns": None,
                },
                "clock_synchronization_proven": False,
                "encoding": normalized["encoding"],
                "width": normalized["width"],
                "height": normalized["height"],
                "channels": normalized["channels"],
                "frame_sha256": frame_sha,
                "frame_size_bytes": len(normalized["frame_bytes"]),
            }
        )
        frames.append(
            {
                "camera_role": target["camera_role"],
                "frame_bytes": normalized["frame_bytes"],
                "signed_frame": signed_frame,
            }
        )
        result_cameras.append(
            {
                "camera_role": target["camera_role"],
                "name": camera["name"],
                "model_id": camera["model_id"],
                "camera_identity_sha256": hashlib.sha256(
                    canonical_json_bytes(
                        {
                            "name": camera["name"],
                            "unique_id": camera["unique_id"],
                            "model_id": camera["model_id"],
                        }
                    )
                ).hexdigest(),
                "achievable_stream_configs": copy.deepcopy(
                    camera["supported_modes"]
                ),
                "selected_input_mode": copy.deepcopy(input_mode),
                "frame_count": 1,
                "signed_frame": signed_frame,
                "capture_audit": copy.deepcopy(audit),
            }
        )
    capture_finished = monotonic_ns()
    duration = capture_finished - capture_started
    if duration <= 0 or duration > permit["maximum_capture_duration_seconds"] * 1_000_000_000:
        raise RuntimeError("RGB camera census exceeded its finite duration")
    result = sign_payload(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "result_name": "owner_present_d405_c922_rgb_camera_census",
            "qualification_scope": "physical_hardware_readiness_observation",
            "evidence_mode": "live_physical_rgb_only",
            "proof_label": PROOF_LABEL,
            "permit_identity_sha256": permit["identity_sha256"],
            "discovery_identity_sha256": discovery["identity_sha256"],
            "capture_started_monotonic_ns": capture_started,
            "capture_finished_monotonic_ns": capture_finished,
            "capture_duration_ns": duration,
            "cameras": result_cameras,
            "camera_metadata_enumerations": 1,
            "rgb_streams_opened": 2,
            "rgb_streams_closed": 2,
            "frames_captured": 2,
            "depth_streams_opened": 0,
            "serial_devices_enumerated": 0,
            "serial_devices_opened": 0,
            "register_reads": 0,
            "register_writes": 0,
            "torque_changes": 0,
            "motion_commands": 0,
            "audio_streams_opened": 0,
            "physical_follower_commanded": False,
            "clock_synchronization_proven": False,
            "calibration_result_granted": False,
            "authority_not_granted": list(
                RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED
            ),
        }
    )
    _verify_result(result, permit=permit, discovery=discovery)
    return frames, result


def build_private_rgb_camera_census(
    *,
    runtime_profile_identity_sha256: str,
    request: dict[str, Any],
    decision: dict[str, Any],
    permit: dict[str, Any],
    discovery: dict[str, Any],
    result: dict[str, Any],
    frames: list[dict[str, Any]],
    completed_at: str,
) -> dict[str, Any]:
    _verify_authority_linkage(request=request, decision=decision, permit=permit)
    _verify_result(result, permit=permit, discovery=discovery)
    _verify_frame_set(frames, result=result)
    payload = sign_payload(
        {
            "schema_version": PRIVATE_SCHEMA_VERSION,
            "evidence_name": "private_owner_present_rgb_camera_census",
            "status": "accepted",
            "proof_labels": [PROOF_LABEL],
            "session_id": permit["session_id"],
            "completed_at": require_nonblank(
                completed_at, label="RGB camera census completed_at"
            ),
            "runtime_profile_identity_sha256": runtime_profile_identity_sha256,
            "request": copy.deepcopy(request),
            "decision": copy.deepcopy(decision),
            "permit": copy.deepcopy(permit),
            "discovery": copy.deepcopy(discovery),
            "result": copy.deepcopy(result),
            "signed_frames": [
                copy.deepcopy(frame["signed_frame"]) for frame in frames
            ],
            "hardware_accessed": True,
            "camera_accessed": True,
            "depth_streams_opened": 0,
            "serial_accessed": False,
            "physical_follower_commanded": False,
            "motion_commands": 0,
            "authority_not_granted": list(
                RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED
            ),
        }
    )
    verify_private_rgb_camera_census(payload, frames=frames)
    return payload


def verify_private_rgb_camera_census(
    payload: dict[str, Any], *, frames: list[dict[str, Any]]
) -> None:
    verify_signed_payload(payload, label="private RGB camera census")
    if (
        payload.get("schema_version") != PRIVATE_SCHEMA_VERSION
        or payload.get("evidence_name")
        != "private_owner_present_rgb_camera_census"
        or payload.get("status") != "accepted"
        or payload.get("proof_labels") != [PROOF_LABEL]
        or payload.get("hardware_accessed") is not True
        or payload.get("camera_accessed") is not True
        or payload.get("depth_streams_opened") != 0
        or payload.get("serial_accessed") is not False
        or payload.get("physical_follower_commanded") is not False
        or payload.get("motion_commands") != 0
        or payload.get("authority_not_granted")
        != list(RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED)
    ):
        raise ValueError("Private RGB camera evidence classification drifted")
    permit = payload.get("permit")
    request = payload.get("request")
    decision = payload.get("decision")
    discovery = payload.get("discovery")
    result = payload.get("result")
    _verify_authority_linkage(request=request, decision=decision, permit=permit)
    _verify_permit_safety(permit)
    verify_rgb_camera_discovery(discovery)
    _verify_result(result, permit=permit, discovery=discovery)
    _verify_frame_set(frames, result=result)
    if payload.get("signed_frames") != [frame["signed_frame"] for frame in frames]:
        raise ValueError("Private RGB camera signed frame set drifted")


def write_private_rgb_camera_bundle(
    *,
    output_directory: Path,
    private_evidence: dict[str, Any],
    frames: list[dict[str, Any]],
) -> dict[str, Any]:
    verify_private_rgb_camera_census(private_evidence, frames=frames)
    output = Path(output_directory)
    if output.exists() or output.is_symlink():
        raise ValueError("Refusing to overwrite immutable RGB camera evidence")
    output.mkdir(parents=True, exist_ok=False)
    frame_refs = []
    for frame in frames:
        role = require_nonblank(frame.get("camera_role"), label="camera role")
        path = output / f"{role}.png"
        path.write_bytes(frame["frame_bytes"])
        frame_refs.append(
            {
                "camera_role": role,
                "relative_path": path.name,
                "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
                "signed_frame_identity_sha256": frame["signed_frame"][
                    "identity_sha256"
                ],
            }
        )
    evidence_path = output / "private_evidence.json"
    dump_canonical_json(evidence_path, private_evidence)
    refs = sign_payload(
        {
            "schema_version": PRIVATE_REFS_SCHEMA_VERSION,
            "private_evidence_relative_path": evidence_path.name,
            "private_evidence_file_sha256": hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest(),
            "private_evidence_size_bytes": evidence_path.stat().st_size,
            "private_evidence_identity_sha256": private_evidence[
                "identity_sha256"
            ],
            "frames": frame_refs,
        }
    )
    dump_canonical_json(output / "private_bundle_refs.json", refs)
    return refs


def build_redacted_rgb_camera_manifest(
    *, private_evidence: dict[str, Any], private_bundle_refs: dict[str, Any]
) -> dict[str, Any]:
    _verify_private_refs(private_bundle_refs, private_evidence=private_evidence)
    result = private_evidence["result"]
    return sign_payload(
        {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "manifest_name": "owner_present_rgb_camera_hardware_readiness",
            "status": "accepted",
            "proof_labels": [PROOF_LABEL],
            "session_id": private_evidence["session_id"],
            "completed_at": private_evidence["completed_at"],
            "runtime_profile_identity_sha256": private_evidence[
                "runtime_profile_identity_sha256"
            ],
            "request_identity_sha256": private_evidence["request"][
                "identity_sha256"
            ],
            "decision_identity_sha256": private_evidence["decision"][
                "identity_sha256"
            ],
            "permit_identity_sha256": private_evidence["permit"][
                "identity_sha256"
            ],
            "private_evidence_identity_sha256": private_evidence[
                "identity_sha256"
            ],
            "private_evidence_file_sha256": private_bundle_refs[
                "private_evidence_file_sha256"
            ],
            "cameras": [
                {
                    "camera_role": camera["camera_role"],
                    "name": camera["name"],
                    "model_id": camera["model_id"],
                    "camera_identity_sha256": camera[
                        "camera_identity_sha256"
                    ],
                    "achievable_stream_configs": copy.deepcopy(
                        camera["achievable_stream_configs"]
                    ),
                    "selected_input_mode": copy.deepcopy(
                        camera["selected_input_mode"]
                    ),
                    "frame_count": camera["frame_count"],
                    "frame_sha256": camera["signed_frame"]["frame_sha256"],
                    "frame_size_bytes": camera["signed_frame"][
                        "frame_size_bytes"
                    ],
                    "signed_frame_identity_sha256": camera["signed_frame"][
                        "identity_sha256"
                    ],
                    "coarse_observation_receive_latency_ns": camera[
                        "signed_frame"
                    ]["coarse_observation_receive_latency_ns"],
                    "t20_22_timing_fields": copy.deepcopy(
                        camera["signed_frame"]["t20_22_timing_fields"]
                    ),
                }
                for camera in result["cameras"]
            ],
            "capture_duration_ns": result["capture_duration_ns"],
            "camera_metadata_enumerations": 1,
            "rgb_streams_opened": 2,
            "rgb_streams_closed": 2,
            "frames_captured": 2,
            "depth_streams_opened": 0,
            "serial_devices_enumerated": 0,
            "serial_devices_opened": 0,
            "register_reads": 0,
            "register_writes": 0,
            "torque_changes": 0,
            "motion_commands": 0,
            "audio_streams_opened": 0,
            "physical_follower_commanded": False,
            "clock_synchronization_proven": False,
            "calibration_result_granted": False,
            "depth_out_of_scope_on_macos": True,
            "authority_not_granted": list(
                RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED
            ),
        }
    )


def verify_redacted_rgb_camera_manifest(
    payload: dict[str, Any],
    *,
    private_evidence: dict[str, Any],
    private_bundle_refs: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="RGB camera census manifest")
    expected = build_redacted_rgb_camera_manifest(
        private_evidence=private_evidence,
        private_bundle_refs=private_bundle_refs,
    )
    if payload != expected:
        raise ValueError("RGB camera census manifest drifted")
    private_unique_ids = [
        camera["unique_id"] for camera in private_evidence["discovery"]["system_cameras"]
    ]
    if any(value in str(payload) for value in private_unique_ids):
        raise ValueError("RGB camera manifest leaked a private unique ID")


def build_redacted_rgb_camera_failure_manifest(
    *,
    failure: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    permit: dict[str, Any],
    private_failure_file_sha256: str,
    private_failure_size_bytes: int,
) -> dict[str, Any]:
    """Build a tracked terminal receipt for a consumed failed camera session."""

    verify_signed_payload(failure, label="private RGB camera census failure")
    _verify_authority_linkage(request=request, decision=decision, permit=permit)
    if (
        failure.get("schema_version") != FAILURE_SCHEMA_VERSION
        or failure.get("status") != "rejected"
        or failure.get("runtime_profile_identity_sha256")
        != permit.get("runtime_profile_identity_sha256")
        or failure.get("request_identity_sha256")
        != request.get("identity_sha256")
        or failure.get("decision_identity_sha256")
        != decision.get("identity_sha256")
        or failure.get("permit_identity_sha256")
        != permit.get("identity_sha256")
        or failure.get("hardware_enumeration_attempted") is not True
        or failure.get("camera_open_attempted") is not True
        or failure.get("error_type") != "ValueError"
        or failure.get("error_message")
        != "Captured camera frame dimensions drifted from the signed input mode"
        or failure.get("proof_labels") != []
        or failure.get("depth_stream_authorized") is not False
        or failure.get("serial_access_authorized") is not False
        or failure.get("motion_authorized") is not False
        or failure.get("physical_follower_commanded") is not False
    ):
        raise ValueError("Private RGB camera failure classification drifted")
    if (
        not isinstance(private_failure_file_sha256, str)
        or len(private_failure_file_sha256) != 64
        or any(c not in "0123456789abcdef" for c in private_failure_file_sha256)
        or isinstance(private_failure_size_bytes, bool)
        or not isinstance(private_failure_size_bytes, int)
        or private_failure_size_bytes <= 0
    ):
        raise ValueError("Private RGB camera failure file reference is malformed")
    return sign_payload(
        {
            "schema_version": FAILURE_MANIFEST_SCHEMA_VERSION,
            "manifest_name": "owner_present_rgb_camera_census_terminal_failure",
            "status": "rejected",
            "proof_labels": [],
            "session_id": permit["session_id"],
            "failed_at": failure["failed_at"],
            "remote_boundary_commit": permit["remote_boundary_commit"],
            "runtime_profile_identity_sha256": permit[
                "runtime_profile_identity_sha256"
            ],
            "request_identity_sha256": request["identity_sha256"],
            "decision_identity_sha256": decision["identity_sha256"],
            "permit_identity_sha256": permit["identity_sha256"],
            "private_failure_identity_sha256": failure["identity_sha256"],
            "private_failure_file_sha256": private_failure_file_sha256,
            "private_failure_size_bytes": private_failure_size_bytes,
            "permit_consumed": True,
            "failure_stage": "first_d405_decoded_frame_dimension_validation",
            "failure_reason": "decoded_png_dimensions_differed_from_signed_input_mode",
            "d405_rgb_open_attempts": 1,
            "d405_decoded_pngs_received": 1,
            "d405_accepted_signed_frames": 0,
            "c922_rgb_open_attempts": 0,
            "c922_accepted_signed_frames": 0,
            "advertised_stream_configs_preserved": False,
            "accepted_signed_frame_count": 0,
            "rgb_stream_cleanup_complete": True,
            "live_ffmpeg_processes_after_failure": 0,
            "depth_streams_opened": 0,
            "serial_devices_enumerated": 0,
            "serial_devices_opened": 0,
            "register_reads": 0,
            "register_writes": 0,
            "torque_changes": 0,
            "motion_commands": 0,
            "audio_streams_opened": 0,
            "physical_follower_commanded": False,
            "hardware_readiness_granted": False,
            "additional_camera_session_authorized": False,
            "authority_not_granted": list(
                RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED
            ),
        }
    )


def verify_redacted_rgb_camera_failure_manifest(
    payload: dict[str, Any],
    *,
    failure: dict[str, Any],
    request: dict[str, Any],
    decision: dict[str, Any],
    permit: dict[str, Any],
    private_failure_file_sha256: str,
    private_failure_size_bytes: int,
) -> None:
    verify_signed_payload(payload, label="RGB camera failure manifest")
    expected = build_redacted_rgb_camera_failure_manifest(
        failure=failure,
        request=request,
        decision=decision,
        permit=permit,
        private_failure_file_sha256=private_failure_file_sha256,
        private_failure_size_bytes=private_failure_size_bytes,
    )
    if payload != expected:
        raise ValueError("RGB camera failure manifest drifted")


def _resolve_target_cameras(
    discovery: dict[str, Any]
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    selected = []
    for target in RGB_CAMERA_CENSUS_TARGETS:
        matches = [
            camera
            for camera in discovery["system_cameras"]
            if target["required_name_substring"].casefold()
            in camera["name"].casefold()
            and all(
                value.casefold() in camera["model_id"].casefold()
                for value in target["required_model_substrings"]
            )
        ]
        if len(matches) != 1:
            label = "D405" if target["camera_role"] == "d405_uvc_rgb" else "C922"
            raise ValueError(f"RGB camera census requires exactly one {label}")
        selected.append((copy.deepcopy(target), copy.deepcopy(matches[0])))
    return selected


def _resolve_avfoundation_device(
    discovery: dict[str, Any], name: str
) -> dict[str, Any]:
    matches = [
        device
        for device in discovery["avfoundation_devices"]
        if device["name"] == name
    ]
    if len(matches) != 1:
        raise ValueError("RGB camera AVFoundation identity is missing or ambiguous")
    return copy.deepcopy(matches[0])


def _normalize_frame(
    frame: Any,
    *,
    input_mode: dict[str, Any],
    call_started: int,
    call_finished: int,
) -> dict[str, Any]:
    if not isinstance(frame, dict):
        raise ValueError("RGB camera frame is malformed")
    frame_bytes = frame.get("frame_bytes")
    if not isinstance(frame_bytes, bytes) or not frame_bytes:
        raise ValueError("RGB camera frame bytes are missing")
    started = frame.get("receive_started_monotonic_ns", call_started)
    finished = frame.get("receive_finished_monotonic_ns", call_finished)
    if (
        isinstance(started, bool)
        or not isinstance(started, int)
        or isinstance(finished, bool)
        or not isinstance(finished, int)
        or finished <= started
    ):
        raise ValueError("RGB camera frame timestamps are malformed")
    if (
        frame.get("encoding") != "png"
        or frame.get("width") != input_mode["width"]
        or frame.get("height") != input_mode["height"]
        or frame.get("channels") != 3
    ):
        raise ValueError("RGB camera frame encoding or dimensions drifted")
    return {
        "frame_bytes": frame_bytes,
        "encoding": "png",
        "width": input_mode["width"],
        "height": input_mode["height"],
        "channels": 3,
        "receive_started_monotonic_ns": started,
        "receive_finished_monotonic_ns": finished,
    }


def _verify_camera_audit(audit: Any) -> None:
    if (
        not isinstance(audit, dict)
        or audit.get("backend") != "ffmpeg_named_avfoundation"
        or audit.get("subprocess_start_attempts") != 1
        or audit.get("subprocess_start_successes") != 1
        or audit.get("release_attempts") != 1
        or audit.get("release_successes") != 1
        or audit.get("frames_delivered") != 1
        or audit.get("capture_property_writes") != 0
        or audit.get("continuous_recording_sessions") != 0
    ):
        raise ValueError("RGB camera capture audit is unsafe or malformed")


def _verify_permit_safety(permit: Any) -> None:
    verify_signed_payload(permit, label="RGB camera census permit")
    if (
        permit.get("schema_version") != RGB_CAMERA_CENSUS_PERMIT_SCHEMA_VERSION
        or permit.get("permit_name") != "one_use_d405_c922_rgb_camera_census"
        or permit.get("task_id") != "K3"
        or permit.get("use_limit") != 1
        or permit.get("target_cameras") != list(RGB_CAMERA_CENSUS_TARGETS)
        or permit.get("maximum_camera_open_count") != 2
        or permit.get("frame_count_per_camera") != 1
        or permit.get("maximum_capture_duration_seconds")
        != RGB_CAMERA_CENSUS_MAX_SESSION_SECONDS
        or permit.get("allowed_operations")
        != list(RGB_CAMERA_CENSUS_ALLOWED_OPERATIONS)
        or permit.get("rgb_stream_authorized") is not True
        or permit.get("depth_stream_authorized") is not False
        or permit.get("serial_access_authorized") is not False
        or permit.get("motion_authorized") is not False
        or permit.get("audio_capture_authorized") is not False
        or permit.get("authority_not_granted")
        != list(RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED)
    ):
        raise ValueError("RGB camera census permit safety contract drifted")


def _verify_authority_linkage(
    *, request: Any, decision: Any, permit: Any
) -> None:
    verify_signed_payload(request, label="RGB camera census request")
    verify_signed_payload(decision, label="RGB camera census decision")
    _verify_permit_safety(permit)
    if (
        request.get("schema_version") != RGB_CAMERA_CENSUS_REQUEST_SCHEMA_VERSION
        or request.get("request_name")
        != "owner_present_d405_c922_rgb_camera_census"
        or request.get("task_id") != "K3"
        or decision.get("schema_version")
        != RGB_CAMERA_CENSUS_DECISION_SCHEMA_VERSION
        or decision.get("decision_id")
        != "owner_present_d405_c922_rgb_camera_census"
        or decision.get("task_id") != "K3"
        or decision.get("granted") is not True
        or decision.get("request_identity_sha256")
        != request.get("identity_sha256")
        or permit.get("request_identity_sha256")
        != request.get("identity_sha256")
        or permit.get("decision_identity_sha256")
        != decision.get("identity_sha256")
        or permit.get("session_id") != request.get("session_id")
        or permit.get("runtime_profile_identity_sha256")
        != request.get("runtime_profile_identity_sha256")
        or permit.get("remote_boundary_commit")
        != request.get("remote_boundary_commit")
    ):
        raise ValueError("RGB camera census authority linkage drifted")


def _verify_result(
    payload: dict[str, Any], *, permit: dict[str, Any], discovery: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="RGB camera census result")
    if (
        payload.get("schema_version") != RESULT_SCHEMA_VERSION
        or payload.get("result_name")
        != "owner_present_d405_c922_rgb_camera_census"
        or payload.get("proof_label") != PROOF_LABEL
        or payload.get("permit_identity_sha256") != permit.get("identity_sha256")
        or payload.get("discovery_identity_sha256")
        != discovery.get("identity_sha256")
        or len(payload.get("cameras", [])) != 2
        or [camera.get("camera_role") for camera in payload["cameras"]]
        != ["d405_uvc_rgb", "c922_rgb"]
        or any(camera.get("frame_count") != 1 for camera in payload["cameras"])
        or payload.get("rgb_streams_opened") != 2
        or payload.get("rgb_streams_closed") != 2
        or payload.get("frames_captured") != 2
        or payload.get("depth_streams_opened") != 0
        or payload.get("serial_devices_enumerated") != 0
        or payload.get("serial_devices_opened") != 0
        or payload.get("register_reads") != 0
        or payload.get("register_writes") != 0
        or payload.get("torque_changes") != 0
        or payload.get("motion_commands") != 0
        or payload.get("audio_streams_opened") != 0
        or payload.get("physical_follower_commanded") is not False
        or payload.get("clock_synchronization_proven") is not False
        or payload.get("calibration_result_granted") is not False
        or isinstance(payload.get("capture_duration_ns"), bool)
        or not isinstance(payload.get("capture_duration_ns"), int)
        or not 0
        < payload.get("capture_duration_ns")
        <= permit.get("maximum_capture_duration_seconds") * 1_000_000_000
        or payload.get("authority_not_granted")
        != list(RGB_CAMERA_CENSUS_AUTHORITY_NOT_GRANTED)
    ):
        raise ValueError("RGB camera census result classification drifted")
    for camera in payload["cameras"]:
        signed = camera.get("signed_frame")
        verify_signed_payload(signed, label="RGB signed frame")
        if (
            signed.get("schema_version") != FRAME_SCHEMA_VERSION
            or signed.get("camera_role") != camera.get("camera_role")
            or signed.get("clock_source") != "host_monotonic_ns"
            or signed.get("clock_synchronization_proven") is not False
            or signed.get("coarse_observation_receive_latency_ns", 0) <= 0
            or signed.get("t20_22_timing_fields")
            != {
                "frame_age_ns": None,
                "observation_assembly_ns": None,
                "inference_latency_ns": None,
                "action_hold_ns": None,
            }
        ):
            raise ValueError("RGB signed frame timing classification drifted")


def _verify_frame_set(
    frames: list[dict[str, Any]], *, result: dict[str, Any]
) -> None:
    if (
        not isinstance(frames, list)
        or len(frames) != 2
        or [frame.get("camera_role") for frame in frames]
        != ["d405_uvc_rgb", "c922_rgb"]
    ):
        raise ValueError("RGB private frame set is malformed")
    for frame, camera in zip(frames, result["cameras"]):
        frame_bytes = frame.get("frame_bytes")
        if (
            not isinstance(frame_bytes, bytes)
            or hashlib.sha256(frame_bytes).hexdigest()
            != camera["signed_frame"]["frame_sha256"]
            or len(frame_bytes) != camera["signed_frame"]["frame_size_bytes"]
            or frame.get("signed_frame") != camera.get("signed_frame")
        ):
            raise ValueError("RGB private frame bytes drifted from signed frame")


def _verify_private_refs(
    payload: dict[str, Any], *, private_evidence: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="RGB camera private bundle refs")
    if (
        payload.get("schema_version") != PRIVATE_REFS_SCHEMA_VERSION
        or payload.get("private_evidence_identity_sha256")
        != private_evidence.get("identity_sha256")
        or len(payload.get("frames", [])) != 2
        or [frame.get("camera_role") for frame in payload["frames"]]
        != ["d405_uvc_rgb", "c922_rgb"]
        or any(frame.get("size_bytes", 0) <= 0 for frame in payload["frames"])
    ):
        raise ValueError("RGB camera private bundle references drifted")
