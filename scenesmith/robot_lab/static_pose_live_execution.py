"""Pinned factories and immutable private evidence for static-pose live candidates."""

from __future__ import annotations

import base64
import copy
import hashlib
import inspect
import json
import os
import re
import sys

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.census_runtime_binding import (
    EXPECTED_RUNTIME_SEMANTICS,
    verify_census_runtime_source_bindings,
)
from scenesmith.robot_lab.hardware_execution_profile import (
    verify_hardware_execution_profile_evidence,
)
from scenesmith.robot_lab.leader_arm_bridge import KNOWN_PHYSICAL_FOLLOWER_PORT
from scenesmith.robot_lab.live_readonly_observation import (
    AuditedReadOnlyBusBackend,
    FFMPEG_EXECUTABLE,
    FFmpegNamedFiniteCamera,
    _parse_exact_png_stream,
    stable_camera_identity_sha256,
)
from scenesmith.robot_lab.static_pose_bracket_runtime import (
    InjectedStaticPoseBusAdapter,
    MAX_FIXTURE_FRAME_BYTES,
)
from scenesmith.robot_lab.static_pose_live_candidate import (
    STATIC_POSE_LIVE_CANDIDATE_CONTRACT_SCHEMA_VERSION,
    STATIC_POSE_LIVE_CANDIDATE_RESULT_SCHEMA_VERSION,
    verify_static_pose_live_candidate_contract,
)


PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSION = (
    "scenesmith.static_pose_live_candidate_private_success.v1"
)
PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSION_V2 = (
    "scenesmith.static_pose_live_candidate_private_success.v2"
)
PRIVATE_STATIC_POSE_FRAME_BUNDLE_SCHEMA_VERSION = (
    "scenesmith.static_pose_live_candidate_private_frame_bundle.v1"
)
_PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSIONS = {
    PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSION,
    PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSION_V2,
}
PRIVATE_STATIC_POSE_FAILURE_SCHEMA_VERSION = (
    "scenesmith.static_pose_live_candidate_private_failure.v1"
)
PINNED_FFMPEG_VERSION = "8.0.1"
PINNED_FFMPEG_RESOLVED_PATH = Path(
    "/opt/homebrew/Cellar/ffmpeg/8.0.1_4/bin/ffmpeg"
)
PINNED_FFMPEG_SHA256 = (
    "0a96da2735695308d964e25fa6f4a0db2e9d24031390360f4c5ff96a4f8938e5"
)
REPO_ROOT = Path(__file__).resolve().parents[2]

_SESSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
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
_EXPECTED_JOINTS = copy.deepcopy(EXPECTED_RUNTIME_SEMANTICS["follower_joint_map"])


class PinnedFFmpegStaticPoseCamera(FFmpegNamedFiniteCamera):
    """Exact finite FFmpeg camera with the live static-pose evidence class."""

    _SEMANTIC_FRAME_FIELDS = (
        "frame_bytes",
        "encoding",
        "width",
        "height",
        "channels",
    )
    _RECEIVE_TIME_FIELDS = (
        "receive_started_monotonic_ns",
        "receive_finished_monotonic_ns",
    )

    @property
    def evidence_mode(self) -> str:
        return "live_injected_camera"

    def bind_private_frame_sink(self, sink: list[dict[str, Any]]) -> None:
        """Bind one empty session-private sink before the first frame read."""

        if hasattr(self, "_private_frame_sink"):
            raise RuntimeError("Pinned static-pose camera frame sink already bound")
        if not isinstance(sink, list) or sink:
            raise ValueError("Pinned static-pose camera frame sink must be empty")
        self._private_frame_sink = sink

    def read(self) -> dict[str, Any]:
        """Validate pinned receive metadata and return the strict frame view."""

        frame = super().read()
        expected_fields = set(self._SEMANTIC_FRAME_FIELDS) | set(
            self._RECEIVE_TIME_FIELDS
        )
        if not isinstance(frame, dict) or set(frame) != expected_fields:
            raise ValueError("Pinned static-pose camera frame fields drifted")
        started = frame["receive_started_monotonic_ns"]
        finished = frame["receive_finished_monotonic_ns"]
        if (
            type(started) is not int
            or type(finished) is not int
            or started < 0
            or finished <= started
        ):
            raise ValueError("Pinned static-pose camera receive interval is invalid")
        semantic = {
            field: frame[field] for field in self._SEMANTIC_FRAME_FIELDS
        }
        sink = getattr(self, "_private_frame_sink", None)
        if sink is not None:
            sink.append(copy.deepcopy(semantic))
        return semantic

    def audit(self) -> dict[str, Any]:
        """Validate the finite FFmpeg lifecycle and return its strict audit view."""

        backend_audit = super().audit()
        expected_backend_audit = {
            "backend": "ffmpeg_named_avfoundation",
            "camera_identity_sha256": hashlib.sha256(
                canonical_json_bytes(self._camera)
            ).hexdigest(),
            "requested_framerate_fps": self._framerate_fps,
            "requested_input_mode": copy.deepcopy(self._input_mode),
            "subprocess_start_attempts": 1,
            "subprocess_start_successes": 1,
            "subprocess_communicate_attempts": 1,
            "subprocess_communicate_successes": 1,
            "subprocess_wait_attempts": 1,
            "subprocess_wait_successes": 1,
            "subprocess_terminate_attempts": 0,
            "subprocess_terminate_successes": 0,
            "subprocess_kill_attempts": 0,
            "subprocess_kill_successes": 0,
            "release_attempts": 1,
            "release_successes": 1,
            "frames_delivered": self._expected_frame_count,
            "capture_property_writes": 0,
            "continuous_recording_sessions": 0,
        }
        if (
            not isinstance(backend_audit, dict)
            or set(backend_audit) != set(expected_backend_audit)
            or canonical_json_bytes(backend_audit)
            != canonical_json_bytes(expected_backend_audit)
        ):
            raise ValueError("Pinned static-pose camera backend audit drifted")
        return {
            "open_attempts": 1,
            "open_successes": 1,
            "read_attempts": self._expected_frame_count,
            "read_successes": self._expected_frame_count,
            "release_attempts": 1,
            "release_successes": 1,
            "capture_property_writes": 0,
            "continuous_recording_sessions": 0,
            "unexpected_operations": 0,
        }


def build_pinned_static_pose_bus_spec(
    candidate_contract: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the exact source-bound raw-bus construction specification."""

    _verify_candidate_contract_core(candidate_contract)
    root = Path(repo_root).resolve()
    source_evidence = verify_census_runtime_source_bindings(repo_root=root)
    follower = candidate_contract["follower_identity"]
    usb = follower["usb"]
    bus = follower["bus"]
    if usb.get("canonical_path") != KNOWN_PHYSICAL_FOLLOWER_PORT:
        raise ValueError("Pinned static-pose follower path drifted")
    paired_alias = KNOWN_PHYSICAL_FOLLOWER_PORT.replace("/dev/cu.", "/dev/tty.", 1)
    if usb.get("observed_aliases") != [paired_alias] or candidate_contract.get(
        "serial_identity_paths"
    ) != [KNOWN_PHYSICAL_FOLLOWER_PORT, paired_alias]:
        raise ValueError("Pinned static-pose follower alias identity drifted")
    if bus != {
        "protocol_family": "feetech",
        "protocol_version": EXPECTED_RUNTIME_SEMANTICS["sts3215_protocol_version"],
        "baudrate": EXPECTED_RUNTIME_SEMANTICS["default_baudrate"],
    }:
        raise ValueError("Pinned static-pose Feetech bus semantics drifted")
    motors = [
        {
            **joint,
            "normalization_mode": (
                "range_0_100" if joint["joint_name"] == "gripper" else "degrees"
            ),
        }
        for joint in _EXPECTED_JOINTS
    ]
    return {
        "source_bindings": copy.deepcopy(source_evidence["source_bindings"]),
        "port": usb["canonical_path"],
        "protocol_version": bus["protocol_version"],
        "baudrate": bus["baudrate"],
        "motors": motors,
        "allowed_registers": ["Present_Position"],
        "normalize": False,
        "num_retry": 0,
        "connect_handshake": False,
        "disconnect_disable_torque": False,
        "calibration": None,
        "candidate_contract_identity_sha256": candidate_contract["identity_sha256"],
    }


def make_pinned_static_pose_transport_factory(
    candidate_contract: dict[str, Any],
    *,
    hardware_execution_profile: dict[str, Any],
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
    repo_root: Path,
    monotonic_ns: Callable[[], int],
) -> Callable[[dict[str, Any]], InjectedStaticPoseBusAdapter]:
    """Return a one-shot factory; creating it does not instantiate hardware."""

    bound_contract = copy.deepcopy(candidate_contract)
    verify_static_pose_live_candidate_contract(
        bound_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
    )
    hardware_profile_identity = _verify_active_hardware_profile(
        hardware_execution_profile,
        now=now,
        repo_root=Path(repo_root),
    )
    spec = build_pinned_static_pose_bus_spec(bound_contract, repo_root=repo_root)
    spec["hardware_execution_profile_identity_sha256"] = hardware_profile_identity
    consumed = False

    def factory(contract: dict[str, Any]) -> InjectedStaticPoseBusAdapter:
        nonlocal consumed
        if consumed:
            raise RuntimeError("Pinned static-pose transport factory is one-shot")
        if canonical_json_bytes(contract) != canonical_json_bytes(bound_contract):
            raise ValueError("Pinned static-pose transport contract drifted")
        consumed = True
        raw_bus = _construct_pinned_feetech_bus(spec, repo_root=Path(repo_root))
        audited = AuditedReadOnlyBusBackend(bus=raw_bus, monotonic_ns=monotonic_ns)
        return InjectedStaticPoseBusAdapter(
            backend=audited,
            servo_names={
                motor["servo_id"]: motor["joint_name"] for motor in spec["motors"]
            },
        )

    return factory


def _construct_pinned_feetech_bus(
    spec: dict[str, Any],
    *,
    repo_root: Path,
) -> Any:
    """Instantiate but do not connect the exact code-pinned Feetech bus."""

    _require_sha256(
        spec.get("hardware_execution_profile_identity_sha256"),
        label="pinned bus hardware profile identity",
    )
    root = Path(repo_root).resolve()
    verify_census_runtime_source_bindings(repo_root=root)
    source_root = (root / "external/lerobot/src").resolve()
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    from lerobot.motors import Motor, MotorNormMode
    from lerobot.motors.feetech import FeetechMotorsBus

    for imported in (Motor, MotorNormMode, FeetechMotorsBus):
        implementation_path = Path(inspect.getfile(imported)).resolve()
        try:
            implementation_path.relative_to(source_root)
        except ValueError as exc:
            raise ValueError("Pinned static-pose bus imported an unpinned LeRobot") from exc
    motors = {
        motor["joint_name"]: Motor(
            motor["servo_id"],
            motor["model"],
            (
                MotorNormMode.RANGE_0_100
                if motor["normalization_mode"] == "range_0_100"
                else MotorNormMode.DEGREES
            ),
        )
        for motor in spec["motors"]
    }
    return FeetechMotorsBus(
        port=spec["port"],
        motors=motors,
        calibration=None,
        protocol_version=spec["protocol_version"],
    )


def verify_pinned_ffmpeg_executable() -> dict[str, Any]:
    """Verify the exact finite-capture executable without running it."""

    path = Path(FFMPEG_EXECUTABLE)
    if path != Path("/opt/homebrew/bin/ffmpeg") or path.is_dir() or not path.exists():
        raise ValueError("Pinned FFmpeg executable path drifted")
    resolved = path.resolve()
    if resolved != PINNED_FFMPEG_RESOLVED_PATH:
        raise ValueError("Pinned FFmpeg resolved path drifted")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != PINNED_FFMPEG_SHA256:
        raise ValueError("Pinned FFmpeg executable hash drifted")
    return {
        "path": str(path),
        "resolved_path": str(resolved),
        "version": PINNED_FFMPEG_VERSION,
        "sha256": digest,
        "size_bytes": resolved.stat().st_size,
    }


def make_pinned_static_pose_camera_factory(
    candidate_contract: dict[str, Any],
    *,
    hardware_execution_profile: dict[str, Any],
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
    monotonic_ns: Callable[[], int],
    private_frame_batches: list[dict[str, Any]] | None = None,
) -> Callable[[dict[str, Any], dict[str, Any]], PinnedFFmpegStaticPoseCamera]:
    """Return a factory that consumes each of the two exact cameras once."""

    if private_frame_batches is not None and (
        not isinstance(private_frame_batches, list) or private_frame_batches
    ):
        raise ValueError("Pinned static-pose private frame batches must start empty")
    verify_static_pose_live_candidate_contract(
        candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
    )
    _verify_candidate_contract_core(candidate_contract)
    hardware_profile_identity = _verify_active_hardware_profile(
        hardware_execution_profile,
        now=now,
        repo_root=REPO_ROOT,
    )
    ffmpeg = verify_pinned_ffmpeg_executable()
    expected: dict[str, dict[str, Any]] = {}
    for camera in candidate_contract["cameras"]:
        spec = _pinned_camera_spec(camera, ffmpeg=ffmpeg)
        spec["hardware_execution_profile_identity_sha256"] = (
            hardware_profile_identity
        )
        stable = spec["stable_camera_identity_sha256"]
        if stable in expected:
            raise ValueError("Pinned static-pose camera identity is duplicated")
        expected[stable] = spec
    consumed: set[str] = set()

    def factory(
        resolved_camera: dict[str, Any],
        static_camera: dict[str, Any],
    ) -> PinnedFFmpegStaticPoseCamera:
        stable = static_camera.get("stable_camera_identity_sha256")
        spec = expected.get(stable)
        if spec is None:
            raise ValueError("Pinned static-pose camera is not in the candidate")
        if stable in consumed:
            raise RuntimeError("Pinned static-pose camera factory entry already consumed")
        if (
            resolved_camera != spec["resolved_camera"]
            or static_camera != spec["static_camera_contract"]
        ):
            raise ValueError("Pinned static-pose camera source or mode drifted")
        consumed.add(stable)
        instance = _construct_pinned_ffmpeg_camera(
            spec,
            monotonic_ns=monotonic_ns,
        )
        if instance.evidence_mode != "live_injected_camera":
            raise ValueError("Pinned static-pose camera evidence class drifted")
        if private_frame_batches is not None:
            frames: list[dict[str, Any]] = []
            instance.bind_private_frame_sink(frames)
            private_frame_batches.append(
                {
                    "stable_camera_identity_sha256": stable,
                    "frames": frames,
                }
            )
        return instance

    return factory


def _pinned_camera_spec(
    camera: dict[str, Any],
    *,
    ffmpeg: dict[str, Any],
) -> dict[str, Any]:
    resolved = camera.get("resolved_camera")
    static = camera.get("static_camera_contract")
    if not isinstance(resolved, dict) or not isinstance(static, dict):
        raise ValueError("Pinned static-pose camera binding is malformed")
    stable = _require_sha256(
        camera.get("stable_camera_identity_sha256"),
        label="stable camera identity",
    )
    _require_sha256(
        camera.get("capture_camera_identity_sha256"),
        label="capture camera identity",
    )
    if (
        stable_camera_identity_sha256(resolved) != stable
        or _sha256_payload(resolved)
        != camera.get("capture_camera_identity_sha256")
    ):
        raise ValueError("Pinned static-pose camera identity digest drifted")
    if static.get("stable_camera_identity_sha256") != stable:
        raise ValueError("Pinned static-pose camera stable identity drifted")
    mode = static.get("input_mode")
    if (
        not isinstance(mode, dict)
        or resolved.get("input_mode") != mode
        or mode.get("framerate_fps") != 30
        or type(mode.get("width")) is not int
        or type(mode.get("height")) is not int
        or mode["width"] < 640
        or mode["height"] < 480
        or static.get("required_frame_count") != 2
        or static.get("required_encoding") != "png"
        or static.get("required_channels") != 3
    ):
        raise ValueError("Pinned static-pose camera mode or frame contract drifted")
    if set(resolved) != {"index", "name", "unique_id", "model_id", "input_mode"}:
        raise ValueError("Pinned static-pose resolved camera fields drifted")
    return {
        "stable_camera_identity_sha256": stable,
        "resolved_camera": copy.deepcopy(resolved),
        "static_camera_contract": copy.deepcopy(static),
        "expected_frame_count": 2,
        "framerate_fps": 30,
        "ffmpeg": copy.deepcopy(ffmpeg),
    }


def _construct_pinned_ffmpeg_camera(
    spec: dict[str, Any],
    *,
    monotonic_ns: Callable[[], int],
) -> PinnedFFmpegStaticPoseCamera:
    _require_sha256(
        spec.get("hardware_execution_profile_identity_sha256"),
        label="pinned camera hardware profile identity",
    )
    if spec.get("ffmpeg") != verify_pinned_ffmpeg_executable():
        raise ValueError("Pinned FFmpeg source drifted before construction")
    return PinnedFFmpegStaticPoseCamera(
        copy.deepcopy(spec["resolved_camera"]),
        expected_frame_count=spec["expected_frame_count"],
        framerate_fps=spec["framerate_fps"],
        monotonic_ns=monotonic_ns,
    )


def build_private_static_pose_candidate_success_evidence(
    *,
    candidate_contract: dict[str, Any],
    hardware_execution_profile: dict[str, Any],
    candidate_result: dict[str, Any],
    private_frame_batches: list[dict[str, Any]] | None = None,
    completed_at: str,
) -> dict[str, Any]:
    """Build a label-free private success record for later acceptance review."""

    completed = _parse_time(completed_at, label="candidate completed_at")
    _verify_candidate_contract_core(candidate_contract)
    _verify_candidate_result_core(candidate_result, contract=candidate_contract)
    verify_hardware_execution_profile_evidence(
        hardware_execution_profile,
        repo_root=REPO_ROOT,
        now=completed.isoformat(),
        expected_thread_id=hardware_execution_profile.get("thread_id"),
        require_active_runtime=False,
    )
    if candidate_result.get(
        "hardware_execution_profile_identity_sha256"
    ) != hardware_execution_profile.get("identity_sha256"):
        raise ValueError("Candidate result hardware profile linkage drifted")
    schema_version = PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSION
    private_frame_bundle = None
    if private_frame_batches is not None:
        schema_version = PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSION_V2
        private_frame_bundle = _build_private_static_pose_frame_bundle(
            private_frame_batches,
            candidate_contract=candidate_contract,
            candidate_result=candidate_result,
        )
    payload = {
        "schema_version": schema_version,
        "evidence_name": "pi05_static_pose_live_candidate_private_success",
        "qualification_scope": "local_static_pose_live_candidate_runtime",
        "evidence_mode": "local_private_live_candidate_success",
        "status": "candidate_observed",
        "session_id": candidate_contract["session_id"],
        "candidate_only": True,
        "candidate_contract": copy.deepcopy(candidate_contract),
        "candidate_contract_identity_sha256": candidate_contract["identity_sha256"],
        "hardware_execution_profile": copy.deepcopy(hardware_execution_profile),
        "hardware_execution_profile_identity_sha256": hardware_execution_profile[
            "identity_sha256"
        ],
        "candidate_result": copy.deepcopy(candidate_result),
        "candidate_result_identity_sha256": candidate_result["identity_sha256"],
        "completed_at": completed.isoformat(),
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "hardware_opened": True,
        "physical_follower_commanded": False,
        "policy_inference_run": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
        "tracked_redacted_manifest_written": False,
    }
    if private_frame_bundle is not None:
        payload["private_frame_bundle"] = private_frame_bundle
    signed = sign_payload(payload)
    verify_private_static_pose_candidate_success_evidence(
        signed,
        repo_root=REPO_ROOT,
        now=completed.isoformat(),
        expected_thread_id=hardware_execution_profile["thread_id"],
    )
    return signed


def _build_private_static_pose_frame_bundle(
    private_frame_batches: list[dict[str, Any]],
    *,
    candidate_contract: dict[str, Any],
    candidate_result: dict[str, Any],
) -> dict[str, Any]:
    expected_cameras = _candidate_camera_frame_records(
        candidate_contract,
        candidate_result=candidate_result,
    )
    if (
        not isinstance(private_frame_batches, list)
        or len(private_frame_batches) != len(expected_cameras)
    ):
        raise ValueError("Private static-pose frame batch count drifted")
    cameras = []
    total_png_bytes = 0
    for batch, expected_camera in zip(
        private_frame_batches,
        expected_cameras,
        strict=True,
    ):
        if not isinstance(batch, dict) or set(batch) != {
            "stable_camera_identity_sha256",
            "frames",
        }:
            raise ValueError("Private static-pose frame batch fields drifted")
        stable = batch.get("stable_camera_identity_sha256")
        if stable != expected_camera["stable_camera_identity_sha256"]:
            raise ValueError("Private static-pose frame source identity drifted")
        raw_frames = batch.get("frames")
        expected_frames = expected_camera["frames"]
        if not isinstance(raw_frames, list) or len(raw_frames) != len(
            expected_frames
        ):
            raise ValueError("Private static-pose frame count drifted")
        frames = []
        for frame_index, (frame, expected_frame) in enumerate(
            zip(raw_frames, expected_frames, strict=True)
        ):
            if not isinstance(frame, dict) or set(frame) != {
                "frame_bytes",
                "encoding",
                "width",
                "height",
                "channels",
            }:
                raise ValueError("Private static-pose raw frame fields drifted")
            frame_bytes = _validated_private_png_bytes(
                frame.get("frame_bytes"),
                expected_frame=expected_frame,
                observed_semantics=frame,
            )
            total_png_bytes += len(frame_bytes)
            frames.append(
                {
                    "frame_index": frame_index,
                    "frame_sha256": expected_frame["frame_sha256"],
                    "encoding": expected_frame["encoding"],
                    "width": expected_frame["width"],
                    "height": expected_frame["height"],
                    "channels": expected_frame["channels"],
                    "png_base64": base64.b64encode(frame_bytes).decode("ascii"),
                }
            )
        cameras.append(
            {
                "stable_camera_identity_sha256": stable,
                "frames": frames,
            }
        )
    bundle = {
        "schema_version": PRIVATE_STATIC_POSE_FRAME_BUNDLE_SCHEMA_VERSION,
        "camera_count": len(cameras),
        "frame_count": sum(len(camera["frames"]) for camera in cameras),
        "total_png_bytes": total_png_bytes,
        "cameras": cameras,
    }
    _verify_private_static_pose_frame_bundle(
        bundle,
        candidate_contract=candidate_contract,
        candidate_result=candidate_result,
    )
    return bundle


def _verify_private_static_pose_frame_bundle(
    bundle: Any,
    *,
    candidate_contract: dict[str, Any],
    candidate_result: dict[str, Any],
) -> None:
    if not isinstance(bundle, dict) or set(bundle) != {
        "schema_version",
        "camera_count",
        "frame_count",
        "total_png_bytes",
        "cameras",
    }:
        raise ValueError("Private static-pose frame bundle fields drifted")
    expected_cameras = _candidate_camera_frame_records(
        candidate_contract,
        candidate_result=candidate_result,
    )
    cameras = bundle.get("cameras")
    if (
        bundle.get("schema_version")
        != PRIVATE_STATIC_POSE_FRAME_BUNDLE_SCHEMA_VERSION
        or bundle.get("camera_count") != 2
        or bundle.get("frame_count") != 4
        or not isinstance(cameras, list)
        or len(cameras) != 2
    ):
        raise ValueError("Private static-pose frame bundle classification drifted")
    total_png_bytes = 0
    for camera, expected_camera in zip(cameras, expected_cameras, strict=True):
        if not isinstance(camera, dict) or set(camera) != {
            "stable_camera_identity_sha256",
            "frames",
        }:
            raise ValueError("Private static-pose frame camera fields drifted")
        if (
            camera.get("stable_camera_identity_sha256")
            != expected_camera["stable_camera_identity_sha256"]
        ):
            raise ValueError("Private static-pose frame source identity drifted")
        frames = camera.get("frames")
        expected_frames = expected_camera["frames"]
        if not isinstance(frames, list) or len(frames) != 2:
            raise ValueError("Private static-pose retained frame count drifted")
        for frame_index, (frame, expected_frame) in enumerate(
            zip(frames, expected_frames, strict=True)
        ):
            if not isinstance(frame, dict) or set(frame) != {
                "frame_index",
                "frame_sha256",
                "encoding",
                "width",
                "height",
                "channels",
                "png_base64",
            }:
                raise ValueError("Private static-pose retained frame fields drifted")
            if frame.get("frame_index") != frame_index:
                raise ValueError("Private static-pose retained frame order drifted")
            encoded = frame.get("png_base64")
            if not isinstance(encoded, str) or not encoded:
                raise ValueError("Private static-pose retained frame bytes are missing")
            try:
                frame_bytes = base64.b64decode(encoded, validate=True)
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    "Private static-pose retained frame base64 is invalid"
                ) from exc
            if base64.b64encode(frame_bytes).decode("ascii") != encoded:
                raise ValueError(
                    "Private static-pose retained frame base64 is noncanonical"
                )
            _validated_private_png_bytes(
                frame_bytes,
                expected_frame=expected_frame,
                observed_semantics=frame,
            )
            total_png_bytes += len(frame_bytes)
    if (
        type(bundle.get("total_png_bytes")) is not int
        or bundle.get("total_png_bytes") != total_png_bytes
    ):
        raise ValueError("Private static-pose retained byte total drifted")


def _candidate_camera_frame_records(
    candidate_contract: dict[str, Any],
    *,
    candidate_result: dict[str, Any],
) -> list[dict[str, Any]]:
    contract_cameras = candidate_contract.get("cameras")
    capture = candidate_result.get("capture")
    result_cameras = capture.get("cameras") if isinstance(capture, dict) else None
    if (
        not isinstance(contract_cameras, list)
        or len(contract_cameras) != 2
        or not isinstance(result_cameras, list)
        or len(result_cameras) != 2
    ):
        raise ValueError("Private static-pose source camera evidence is missing")
    expected = []
    for contract_camera, result_camera in zip(
        contract_cameras,
        result_cameras,
        strict=True,
    ):
        stable = contract_camera.get("stable_camera_identity_sha256")
        _require_sha256(stable, label="private frame stable camera identity")
        if (
            not isinstance(result_camera, dict)
            or result_camera.get("stable_camera_identity_sha256") != stable
        ):
            raise ValueError("Private static-pose result camera identity drifted")
        frames = result_camera.get("frames")
        if not isinstance(frames, list) or len(frames) != 2:
            raise ValueError("Private static-pose result frame evidence drifted")
        validated_frames = []
        for frame_index, frame in enumerate(frames):
            if not isinstance(frame, dict) or set(frame) != {
                "frame_index",
                "frame_sha256",
                "width",
                "height",
                "channels",
                "encoding",
            }:
                raise ValueError("Private static-pose result frame fields drifted")
            _require_sha256(
                frame.get("frame_sha256"),
                label="private frame result digest",
            )
            static_camera = contract_camera.get("static_camera_contract")
            input_mode = (
                static_camera.get("input_mode")
                if isinstance(static_camera, dict)
                else None
            )
            if (
                frame.get("frame_index") != frame_index
                or frame.get("encoding") != "png"
                or not isinstance(input_mode, dict)
                or frame.get("width") != input_mode.get("width")
                or frame.get("height") != input_mode.get("height")
                or frame.get("channels") != 3
            ):
                raise ValueError("Private static-pose result frame semantics drifted")
            validated_frames.append(copy.deepcopy(frame))
        expected.append(
            {
                "stable_camera_identity_sha256": stable,
                "frames": validated_frames,
            }
        )
    return expected


def _validated_private_png_bytes(
    value: Any,
    *,
    expected_frame: dict[str, Any],
    observed_semantics: dict[str, Any],
) -> bytes:
    if (
        not isinstance(value, bytes)
        or not value
        or len(value) > MAX_FIXTURE_FRAME_BYTES
    ):
        raise ValueError("Private static-pose PNG bytes exceed their finite bound")
    if hashlib.sha256(value).hexdigest() != expected_frame["frame_sha256"]:
        raise ValueError("Private static-pose PNG digest drifted")
    parsed = _parse_exact_png_stream(value, expected_frame_count=1)[0]
    for field in ("encoding", "width", "height", "channels"):
        if (
            observed_semantics.get(field) != expected_frame[field]
            or parsed[field] != expected_frame[field]
        ):
            raise ValueError("Private static-pose PNG semantics drifted")
    if parsed["frame_bytes"] != value:
        raise ValueError("Private static-pose PNG parser did not consume exact bytes")
    return value


def build_private_static_pose_candidate_failure_evidence(
    *,
    candidate_contract: dict[str, Any],
    hardware_execution_profile: dict[str, Any],
    error: BaseException,
    failed_at: str,
) -> dict[str, Any]:
    """Build a conservative private rejection record after profile validation."""

    failed = _parse_time(failed_at, label="candidate failed_at")
    _verify_candidate_contract_core(candidate_contract)
    verify_hardware_execution_profile_evidence(
        hardware_execution_profile,
        repo_root=REPO_ROOT,
        now=failed.isoformat(),
        expected_thread_id=hardware_execution_profile.get("thread_id"),
        require_active_runtime=False,
    )
    error_types, error_messages = _flatten_errors(error)
    payload = {
        "schema_version": PRIVATE_STATIC_POSE_FAILURE_SCHEMA_VERSION,
        "evidence_name": "pi05_static_pose_live_candidate_private_failure",
        "qualification_scope": "local_static_pose_live_candidate_runtime",
        "evidence_mode": "local_private_rejected_live_candidate_attempt",
        "status": "rejected",
        "session_id": candidate_contract["session_id"],
        "candidate_only": True,
        "candidate_contract": copy.deepcopy(candidate_contract),
        "candidate_contract_identity_sha256": candidate_contract["identity_sha256"],
        "hardware_execution_profile": copy.deepcopy(hardware_execution_profile),
        "hardware_execution_profile_identity_sha256": hardware_execution_profile[
            "identity_sha256"
        ],
        "error_types": error_types,
        "error_leaf_count": len(error_messages),
        "error_messages_sha256": _sha256_payload(error_messages),
        "failed_at": failed.isoformat(),
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "hardware_opened_may_have_occurred": True,
        "physical_follower_commanded": False,
        "policy_inference_run": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
        "private_success_written": False,
        "tracked_redacted_manifest_written": False,
    }
    signed = sign_payload(payload)
    verify_private_static_pose_candidate_failure_evidence(
        signed,
        repo_root=REPO_ROOT,
        now=failed.isoformat(),
        expected_thread_id=hardware_execution_profile["thread_id"],
    )
    return signed


def verify_private_static_pose_candidate_success_evidence(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    now: str,
    expected_thread_id: str,
) -> None:
    completed = _parse_time(payload.get("completed_at"), label="candidate completed_at")
    verified = _parse_time(now, label="candidate success verification time")
    if verified < completed:
        raise ValueError("Private static-pose success is future-dated")
    schema_version = payload.get("schema_version")
    if schema_version not in _PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSIONS:
        raise ValueError("Private static-pose success schema is unsupported")
    expected_fields = {
        "candidate_result",
        "candidate_result_identity_sha256",
        "completed_at",
        "hardware_opened",
    }
    if schema_version == PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSION_V2:
        expected_fields.add("private_frame_bundle")
    _verify_private_candidate_common(
        payload,
        repo_root=repo_root,
        profile_time=completed.isoformat(),
        expected_thread_id=expected_thread_id,
        expected_schema=schema_version,
        expected_fields=expected_fields,
    )
    if (
        payload.get("evidence_name")
        != "pi05_static_pose_live_candidate_private_success"
        or payload.get("evidence_mode") != "local_private_live_candidate_success"
        or payload.get("status") != "candidate_observed"
        or payload.get("hardware_opened") is not True
    ):
        raise ValueError("Private static-pose success classification drifted")
    result = payload.get("candidate_result")
    _verify_candidate_result_core(result, contract=payload["candidate_contract"])
    if (
        payload.get("candidate_result_identity_sha256") != result["identity_sha256"]
        or result.get("hardware_execution_profile_identity_sha256")
        != payload["hardware_execution_profile_identity_sha256"]
    ):
        raise ValueError("Private static-pose success result identity drifted")
    if schema_version == PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSION_V2:
        _verify_private_static_pose_frame_bundle(
            payload.get("private_frame_bundle"),
            candidate_contract=payload["candidate_contract"],
            candidate_result=result,
        )


def verify_private_static_pose_candidate_failure_evidence(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    now: str,
    expected_thread_id: str,
) -> None:
    failed = _parse_time(payload.get("failed_at"), label="candidate failed_at")
    verified = _parse_time(now, label="candidate failure verification time")
    if verified < failed:
        raise ValueError("Private static-pose failure is future-dated")
    _verify_private_candidate_common(
        payload,
        repo_root=repo_root,
        profile_time=failed.isoformat(),
        expected_thread_id=expected_thread_id,
        expected_schema=PRIVATE_STATIC_POSE_FAILURE_SCHEMA_VERSION,
        expected_fields={
            "error_types",
            "error_leaf_count",
            "error_messages_sha256",
            "failed_at",
            "hardware_opened_may_have_occurred",
            "private_success_written",
        },
    )
    if (
        payload.get("evidence_name")
        != "pi05_static_pose_live_candidate_private_failure"
        or payload.get("evidence_mode")
        != "local_private_rejected_live_candidate_attempt"
        or payload.get("status") != "rejected"
        or payload.get("hardware_opened_may_have_occurred") is not True
        or payload.get("private_success_written") is not False
    ):
        raise ValueError("Private static-pose failure classification drifted")
    error_types = payload.get("error_types")
    if (
        not isinstance(error_types, list)
        or not error_types
        or error_types != sorted(set(error_types))
        or any(not isinstance(value, str) or not value for value in error_types)
    ):
        raise ValueError("Private static-pose failure error types drifted")
    if type(payload.get("error_leaf_count")) is not int or payload.get(
        "error_leaf_count"
    ) < len(error_types):
        raise ValueError("Private static-pose failure error count drifted")
    _require_sha256(
        payload.get("error_messages_sha256"),
        label="private failure message digest",
    )


def _verify_private_candidate_common(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    profile_time: str,
    expected_thread_id: str,
    expected_schema: str,
    expected_fields: set[str],
) -> None:
    common_fields = {
        "schema_version",
        "evidence_name",
        "qualification_scope",
        "evidence_mode",
        "status",
        "session_id",
        "candidate_only",
        "candidate_contract",
        "candidate_contract_identity_sha256",
        "hardware_execution_profile",
        "hardware_execution_profile_identity_sha256",
        "proof_labels",
        "authority_not_granted",
        "physical_follower_commanded",
        "policy_inference_run",
        "motion_authority_granted",
        "training_authority_granted",
        "tracked_redacted_manifest_written",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != common_fields | expected_fields:
        raise ValueError("Private static-pose candidate evidence fields are malformed")
    if (
        payload.get("schema_version") != expected_schema
        or payload.get("qualification_scope")
        != "local_static_pose_live_candidate_runtime"
        or payload.get("candidate_only") is not True
    ):
        raise ValueError("Private static-pose candidate classification drifted")
    verify_signed_payload(payload, label="Private static-pose candidate evidence")
    contract = payload.get("candidate_contract")
    _verify_candidate_contract_core(contract)
    if (
        payload.get("session_id") != contract["session_id"]
        or payload.get("candidate_contract_identity_sha256")
        != contract["identity_sha256"]
        or payload.get("hardware_execution_profile_identity_sha256") is None
    ):
        raise ValueError("Private static-pose candidate contract identity drifted")
    profile = payload.get("hardware_execution_profile")
    verify_hardware_execution_profile_evidence(
        profile,
        repo_root=repo_root,
        now=profile_time,
        expected_thread_id=expected_thread_id,
        require_active_runtime=False,
    )
    if payload.get("hardware_execution_profile_identity_sha256") != profile.get(
        "identity_sha256"
    ):
        raise ValueError("Private static-pose hardware profile identity drifted")
    if (
        payload.get("proof_labels") != []
        or payload.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
        or payload.get("physical_follower_commanded") is not False
        or payload.get("policy_inference_run") is not False
        or payload.get("motion_authority_granted") is not False
        or payload.get("training_authority_granted") is not False
        or payload.get("tracked_redacted_manifest_written") is not False
    ):
        raise ValueError("Private static-pose candidate authority fields drifted")


def write_private_static_pose_candidate_evidence(
    *,
    private_root: Path,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Write one content-addressed artifact with no replacement path."""

    if evidence.get("schema_version") in _PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSIONS:
        verify_private_static_pose_candidate_success_evidence(
            evidence,
            repo_root=REPO_ROOT,
            now=evidence.get("completed_at"),
            expected_thread_id=evidence["hardware_execution_profile"]["thread_id"],
        )
        filename = "private_success.json"
    elif evidence.get("schema_version") == PRIVATE_STATIC_POSE_FAILURE_SCHEMA_VERSION:
        verify_private_static_pose_candidate_failure_evidence(
            evidence,
            repo_root=REPO_ROOT,
            now=evidence.get("failed_at"),
            expected_thread_id=evidence["hardware_execution_profile"]["thread_id"],
        )
        filename = "private_failure.json"
    else:
        raise ValueError("Private static-pose evidence schema is unsupported")
    session_id = _validated_session_id(evidence.get("session_id"))
    verify_private_static_pose_candidate_evidence_destination(
        private_root=private_root,
        session_id=session_id,
    )
    root = Path(private_root).resolve()
    session_directory = root / session_id
    try:
        session_directory.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(
            "Private static-pose session already has immutable evidence"
        ) from exc
    if not session_directory.is_dir() or session_directory.resolve().parent != root:
        raise ValueError("Private static-pose session directory escaped its root")
    output_directory = session_directory / evidence["identity_sha256"]
    try:
        output_directory.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError("Private static-pose evidence path must be new and immutable") from exc
    output_path = output_directory / filename
    encoded = (
        json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    try:
        with output_path.open("xb") as stream:
            stream.write(encoded)
    except BaseException:
        raise
    relative = output_path.relative_to(root).as_posix()
    return {
        "relative_path": relative,
        "schema_version": evidence["schema_version"],
        "identity_sha256": evidence["identity_sha256"],
        "file_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "size_bytes": output_path.stat().st_size,
    }


def verify_private_static_pose_candidate_evidence_destination(
    *,
    private_root: Path,
    session_id: str,
) -> None:
    """Verify a new immutable session destination without creating it."""

    root_path = Path(private_root)
    if _path_has_symlink_component(root_path):
        raise ValueError(
            "Private static-pose evidence root cannot contain a symlink"
        )
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError("Private static-pose evidence root must already exist")
    session_directory = root_path.resolve() / _validated_session_id(session_id)
    if session_directory.exists() or session_directory.is_symlink():
        raise ValueError(
            "Private static-pose session already has immutable evidence"
        )


def verify_private_static_pose_candidate_evidence_reference(
    reference: dict[str, Any],
    *,
    private_root: Path,
    evidence: dict[str, Any],
) -> None:
    expected_fields = {
        "relative_path",
        "schema_version",
        "identity_sha256",
        "file_sha256",
        "size_bytes",
    }
    if not isinstance(reference, dict) or set(reference) != expected_fields:
        raise ValueError("Private static-pose evidence reference fields are malformed")
    root_path = Path(private_root)
    if _path_has_symlink_component(root_path) or not root_path.is_dir():
        raise ValueError("Private static-pose evidence reference root is invalid")
    root = root_path.resolve()
    relative = Path(require_nonblank(reference.get("relative_path"), label="private path"))
    if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 3:
        raise ValueError("Private static-pose evidence reference path is unsafe")
    filename = (
        "private_success.json"
        if evidence.get("schema_version")
        in _PRIVATE_STATIC_POSE_SUCCESS_SCHEMA_VERSIONS
        else "private_failure.json"
    )
    expected_relative = Path(
        _validated_session_id(evidence.get("session_id")),
        evidence.get("identity_sha256"),
        filename,
    )
    if relative != expected_relative:
        raise ValueError("Private static-pose evidence reference path drifted")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise ValueError("Private static-pose evidence reference is missing or aliased")
    if any(parent.is_symlink() for parent in path.parents if parent != root.parent):
        raise ValueError("Private static-pose evidence reference parent is aliased")
    file_bytes = path.read_bytes()
    if (
        reference.get("schema_version") != evidence.get("schema_version")
        or reference.get("identity_sha256") != evidence.get("identity_sha256")
        or reference.get("file_sha256") != hashlib.sha256(file_bytes).hexdigest()
        or reference.get("size_bytes") != len(file_bytes)
        or load_strict_json(path) != evidence
    ):
        raise ValueError("Private static-pose evidence reference hash, size, or content drifted")


def _verify_candidate_contract_core(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Static-pose live candidate contract is missing")
    verify_signed_payload(payload, label="Static-pose live candidate contract")
    if (
        payload.get("schema_version")
        != STATIC_POSE_LIVE_CANDIDATE_CONTRACT_SCHEMA_VERSION
        or payload.get("contract_name") != "pi05_static_pose_live_candidate"
        or payload.get("qualification_scope")
        != "local_static_pose_live_candidate_contract"
        or payload.get("execution_class") != "live_candidate"
        or payload.get("evidence_mode")
        != "private_source_bound_live_candidate_contract"
        or payload.get("hardware_access_authorized") is not True
        or payload.get("proof_labels") != []
        or payload.get("local_capabilities")
        != ["static_pose_live_candidate_contract_valid"]
        or payload.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
        or payload.get("physical_follower_commanded") is not False
        or payload.get("motion_authority_granted") is not False
        or payload.get("training_authority_granted") is not False
        or payload.get("private_output_required") is not True
        or payload.get("hardware_accessed") is not False
    ):
        raise ValueError("Static-pose live candidate contract authority drifted")
    _validated_session_id(payload.get("session_id"))
    cameras = payload.get("cameras")
    if not isinstance(cameras, list) or len(cameras) != 2:
        raise ValueError("Static-pose live candidate requires two cameras")


def _verify_active_hardware_profile(
    payload: dict[str, Any],
    *,
    now: str,
    repo_root: Path,
) -> str:
    thread_id = require_nonblank(
        os.environ.get("CODEX_THREAD_ID"),
        label="active Codex hardware thread ID",
    )
    verify_hardware_execution_profile_evidence(
        payload,
        repo_root=Path(repo_root).resolve(),
        now=now,
        expected_thread_id=thread_id,
    )
    return _require_sha256(
        payload.get("identity_sha256"),
        label="hardware execution profile identity",
    )


def _verify_candidate_result_core(
    payload: Any,
    *,
    contract: dict[str, Any],
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Static-pose live candidate result is missing")
    verify_signed_payload(payload, label="Static-pose live candidate result")
    _require_sha256(
        payload.get("hardware_execution_profile_identity_sha256"),
        label="candidate result hardware profile identity",
    )
    if (
        payload.get("schema_version")
        != STATIC_POSE_LIVE_CANDIDATE_RESULT_SCHEMA_VERSION
        or payload.get("result_name")
        != "pi05_static_pose_live_candidate_runtime"
        or payload.get("qualification_scope")
        != "local_static_pose_live_candidate_runtime"
        or payload.get("execution_class") != "live_candidate"
        or payload.get("evidence_mode")
        != "private_source_bound_live_candidate_runtime"
        or payload.get("candidate_only") is not True
        or payload.get("candidate_contract_identity_sha256")
        != contract["identity_sha256"]
        or payload.get("proof_labels") != []
        or payload.get("local_capabilities")
        != ["source_bound_static_pose_live_candidate_runtime_observed"]
        or payload.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
        or payload.get("hardware_opened") is not True
        or payload.get("physical_follower_commanded") is not False
        or payload.get("policy_inference_run") is not False
        or payload.get("motion_authority_granted") is not False
        or payload.get("training_authority_granted") is not False
        or payload.get("private_output_required") is not True
        or payload.get("tracked_redacted_manifest_written") is not False
    ):
        raise ValueError("Static-pose live candidate result authority drifted")


def _flatten_errors(error: BaseException) -> tuple[list[str], list[str]]:
    if not isinstance(error, BaseException):
        raise ValueError("Private static-pose failure requires an exception")
    leaves: list[BaseException] = []

    def visit(value: BaseException) -> None:
        if isinstance(value, BaseExceptionGroup):
            for child in value.exceptions:
                visit(child)
        else:
            leaves.append(value)

    visit(error)
    return (
        sorted({type(value).__name__ for value in leaves}),
        sorted(str(value) for value in leaves),
    )


def _validated_session_id(value: Any) -> str:
    session_id = require_nonblank(value, label="private static-pose session ID")
    if not _SESSION_PATTERN.fullmatch(session_id):
        raise ValueError("Private static-pose session ID is unsafe")
    return session_id


def _path_has_symlink_component(path: Path) -> bool:
    absolute = Path(path).absolute()
    return any(
        candidate.is_symlink() for candidate in (absolute, *absolute.parents)
    )


def _require_sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest


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
