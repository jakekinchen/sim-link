"""Source-bound, candidate-only runner for a future static-pose live gate."""

from __future__ import annotations

import copy
import hashlib
import os

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
from scenesmith.robot_lab.live_readonly_observation import (
    DEFAULT_FOLLOWER_CALIBRATION_PATH,
    LIVE_DISCOVERY_SCHEMA_VERSION,
    MAX_EXECUTION_DURATION_SECONDS,
    resolve_camera_selection,
    resolve_follower_identity,
    stable_camera_identity_sha256,
    verify_operator_presence_lease,
)
from scenesmith.robot_lab.hardware_execution_profile import (
    verify_hardware_execution_profile_evidence,
)
from scenesmith.robot_lab.static_pose_bracket import (
    ACCEPTED_CALIBRATION_PROFILE_IDENTITY,
    ACCEPTED_STATIC_POSE_BRACKET_CONTRACT_IDENTITY,
    EXPECTED_OPERATION_COUNTS,
    evaluate_static_pose_bracket_measurements,
    verify_static_pose_bracket_contract,
)
from scenesmith.robot_lab.static_pose_bracket_runtime import (
    FiniteStaticPoseCamera,
    StaticPoseTransport,
    _capture_static_pose_bracket_runtime,
    verify_static_pose_runtime_capture,
)


STATIC_POSE_LIVE_CANDIDATE_CONTRACT_SCHEMA_VERSION = (
    "scenesmith.static_pose_live_candidate_contract.v1"
)
STATIC_POSE_LIVE_CANDIDATE_RESULT_SCHEMA_VERSION = (
    "scenesmith.static_pose_live_candidate_result.v2"
)
EXPECTED_ACCEPTED_MANIFEST_IDENTITY = (
    "5218c3bd0ee0b34aca9aa32e5e1912c284a2dfffcdbc86ba7fa34f08f4433ed4"
)
LIVE_GATE_SCOPE = "one_static_pose_bracket_candidate_session"
HARDWARE_EXECUTION_PROFILE = "hardware_supervised_on_request"
HARDWARE_APPROVAL_POLICY = "on-request"
REPO_ROOT = Path(__file__).resolve().parents[2]

_ALLOWED_OPERATIONS = [
    "serial_identity_holder_snapshot",
    "serial_connect_without_handshake",
    "scalar_present_position_read",
    "finite_named_camera_open_read_release",
    "serial_disconnect_without_torque_change",
]
_FORBIDDEN_OPERATIONS = [
    "calibrate",
    "configure",
    "disable_torque",
    "enable_torque",
    "goal_position",
    "motion",
    "scan",
    "send_action",
    "setup_motor",
    "sync_write",
    "write",
    "write_register",
]
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


def build_static_pose_live_candidate_contract(
    *,
    project_state: dict[str, Any],
    presence_lease: dict[str, Any],
    discovery: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    issued_at: str,
    expires_at: str,
) -> dict[str, Any]:
    """Build a live-marked contract from already supplied source evidence."""

    return _build_static_pose_candidate_contract(
        project_state=project_state,
        presence_lease=presence_lease,
        discovery=discovery,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        issued_at=issued_at,
        expires_at=expires_at,
        execution_class="live_candidate",
    )


def build_static_pose_live_candidate_fixture_contract(
    *,
    project_state: dict[str, Any],
    presence_lease: dict[str, Any],
    discovery: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    issued_at: str,
    expires_at: str,
) -> dict[str, Any]:
    """Build the explicit no-hardware fixture form of the candidate contract."""

    return _build_static_pose_candidate_contract(
        project_state=project_state,
        presence_lease=presence_lease,
        discovery=discovery,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        issued_at=issued_at,
        expires_at=expires_at,
        execution_class="deterministic_candidate_fixture",
    )


def _build_static_pose_candidate_contract(
    *,
    project_state: dict[str, Any],
    presence_lease: dict[str, Any],
    discovery: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    issued_at: str,
    expires_at: str,
    execution_class: str,
) -> dict[str, Any]:
    """Build one fixed-class candidate contract."""

    classification = _candidate_execution_classification(execution_class)
    (
        pinned_calibration_path,
        profile_path,
        accepted_manifest_path,
        static_contract_path,
    ) = _validated_source_paths(
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
    )
    if load_strict_json(static_contract_path) != static_pose_contract:
        raise ValueError("Canonical static pose contract content drifted")
    if project_state.get("training_lock") != "closed":
        raise ValueError("Static pose candidate requires the training lock closed")
    t16_5c = project_state.get("tasks", {}).get("T16.5c", {})
    if (
        "051" not in t16_5c.get("completed_brief_ids", [])
        or "stable_camera_identity_binding_valid"
        not in t16_5c.get("authority_granted", [])
    ):
        raise ValueError("Brief 051 stable camera binding is not verified")
    verify_static_pose_bracket_contract(
        static_pose_contract,
        calibration_path=pinned_calibration_path,
        calibration_profile_path=profile_path,
        manifest_path=accepted_manifest_path,
    )
    if (
        static_pose_contract.get("identity_sha256")
        != ACCEPTED_STATIC_POSE_BRACKET_CONTRACT_IDENTITY
    ):
        raise ValueError("Static pose candidate contract source identity drifted")
    verify_operator_presence_lease(
        presence_lease,
        project_state=project_state,
        now=issued_at,
    )
    if (
        presence_lease.get("issued_at") != issued_at
        or presence_lease.get("valid_until") != expires_at
    ):
        raise ValueError("Static pose candidate lease times drifted")
    if discovery.get("schema_version") != LIVE_DISCOVERY_SCHEMA_VERSION:
        raise ValueError("Static pose candidate requires signed discovery v2")
    if discovery.get("session_id") != presence_lease.get("session_id"):
        raise ValueError("Static pose candidate discovery/lease session drifted")

    live_gate_snapshot = _validated_live_gate_snapshot(
        project_state,
        now=issued_at,
        expires_at=expires_at,
    )
    manifest = load_strict_json(accepted_manifest_path)
    profile = load_strict_json(profile_path)
    if manifest.get("identity_sha256") != EXPECTED_ACCEPTED_MANIFEST_IDENTITY:
        raise ValueError("Static pose candidate accepted manifest identity drifted")
    if profile.get("identity_sha256") != ACCEPTED_CALIBRATION_PROFILE_IDENTITY:
        raise ValueError("Static pose candidate CalibrationProfile identity drifted")

    follower_identity = resolve_follower_identity(discovery)
    follower_usb_identity = _sha256_payload(follower_identity["usb"])
    if follower_usb_identity != manifest.get("usb_identity_sha256"):
        raise ValueError("Fresh follower USB identity differs from accepted evidence")
    serial_identity_paths = [
        follower_identity["usb"]["canonical_path"],
        *follower_identity["usb"]["observed_aliases"],
    ]
    if len(serial_identity_paths) != len(set(serial_identity_paths)):
        raise ValueError("Fresh follower serial identity paths are ambiguous")
    cameras = resolve_static_pose_candidate_cameras(
        discovery=discovery,
        static_pose_contract=static_pose_contract,
    )
    maximum_execution_duration = min(
        MAX_EXECUTION_DURATION_SECONDS,
        presence_lease["validity_seconds"],
        int(
            (
                _parse_time(
                    live_gate_snapshot["valid_until"],
                    label="gate valid_until",
                )
                - _parse_time(issued_at, label="candidate issued_at")
            ).total_seconds()
        ),
    )
    if maximum_execution_duration <= 0:
        raise ValueError("Static pose candidate execution duration is invalid")
    payload = {
        "schema_version": STATIC_POSE_LIVE_CANDIDATE_CONTRACT_SCHEMA_VERSION,
        "contract_name": "pi05_static_pose_live_candidate",
        "qualification_scope": "local_static_pose_live_candidate_contract",
        "evidence_mode": classification["contract_evidence_mode"],
        "execution_class": execution_class,
        "hardware_access_authorized": classification[
            "hardware_access_authorized"
        ],
        "session_id": presence_lease["session_id"],
        "project_state": copy.deepcopy(project_state),
        "project_state_identity_sha256": _sha256_payload(project_state),
        "live_gate_snapshot": live_gate_snapshot,
        "presence_lease": copy.deepcopy(presence_lease),
        "presence_lease_identity_sha256": presence_lease["identity_sha256"],
        "discovery": copy.deepcopy(discovery),
        "discovery_identity_sha256": discovery["identity_sha256"],
        "source_artifacts": {
            "accepted_manifest": _artifact_reference(
                accepted_manifest_path,
                logical_path=(
                    "configurations/robot_lab/"
                    "pi05_live_readonly_observation.redacted.json"
                ),
                payload=manifest,
            ),
            "calibration_profile": _artifact_reference(
                profile_path,
                logical_path="configurations/robot_lab/pi05_calibration_profile.json",
                payload=profile,
            ),
            "static_pose_contract": _artifact_reference(
                static_contract_path,
                logical_path=(
                    "configurations/robot_lab/pi05_static_pose_bracket_contract.json"
                ),
                payload=static_pose_contract,
            ),
        },
        "follower_identity": follower_identity,
        "follower_usb_identity_sha256": follower_usb_identity,
        "serial_identity_paths": serial_identity_paths,
        "cameras": cameras,
        "operation_counts": dict(EXPECTED_OPERATION_COUNTS),
        "maximum_bracket_duration_ns": static_pose_contract["timing_contract"][
            "maximum_bracket_duration_ns"
        ],
        "maximum_execution_duration_seconds": maximum_execution_duration,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "allowed_operations": list(_ALLOWED_OPERATIONS),
        "forbidden_operations": list(_FORBIDDEN_OPERATIONS),
        "local_capabilities": [classification["contract_local_capability"]],
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
        "hardware_accessed": False,
        "physical_follower_commanded": False,
        "motion_authority_granted": False,
        "training_authority_granted": False,
        "private_output_required": True,
    }
    return sign_payload(payload)


def verify_static_pose_live_candidate_contract(
    payload: dict[str, Any],
    *,
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
) -> None:
    """Verify the fixed live-marked candidate contract."""

    _verify_static_pose_candidate_contract(
        payload,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
        expected_execution_class="live_candidate",
    )


def verify_static_pose_live_candidate_fixture_contract(
    payload: dict[str, Any],
    *,
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
) -> None:
    """Verify the fixed no-hardware fixture candidate contract."""

    _verify_static_pose_candidate_contract(
        payload,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
        expected_execution_class="deterministic_candidate_fixture",
    )


def _verify_static_pose_candidate_contract(
    payload: dict[str, Any],
    *,
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
    expected_execution_class: str,
) -> None:
    """Rebuild a fixed-class contract and require its gate to remain active."""

    expected_fields = {
        "schema_version",
        "contract_name",
        "qualification_scope",
        "evidence_mode",
        "execution_class",
        "hardware_access_authorized",
        "session_id",
        "project_state",
        "project_state_identity_sha256",
        "live_gate_snapshot",
        "presence_lease",
        "presence_lease_identity_sha256",
        "discovery",
        "discovery_identity_sha256",
        "source_artifacts",
        "follower_identity",
        "follower_usb_identity_sha256",
        "serial_identity_paths",
        "cameras",
        "operation_counts",
        "maximum_bracket_duration_ns",
        "maximum_execution_duration_seconds",
        "issued_at",
        "expires_at",
        "allowed_operations",
        "forbidden_operations",
        "local_capabilities",
        "proof_labels",
        "authority_not_granted",
        "hardware_accessed",
        "physical_follower_commanded",
        "motion_authority_granted",
        "training_authority_granted",
        "private_output_required",
        "identity_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != expected_fields:
        raise ValueError("Static pose live candidate contract fields are malformed")
    if (
        payload.get("schema_version")
        != STATIC_POSE_LIVE_CANDIDATE_CONTRACT_SCHEMA_VERSION
    ):
        raise ValueError("Static pose live candidate contract schema is unsupported")
    verify_signed_payload(payload, label="Static pose live candidate contract")
    if payload.get("execution_class") != expected_execution_class:
        raise ValueError("Static pose live candidate execution class drifted")
    if (
        payload.get("project_state") != project_state
        or payload.get("project_state_identity_sha256")
        != _sha256_payload(project_state)
    ):
        raise ValueError("Static pose live candidate project state drifted")
    verify_operator_presence_lease(
        payload.get("presence_lease"),
        project_state=project_state,
        now=now,
    )
    _validated_live_gate_snapshot(
        project_state,
        now=now,
        expires_at=payload.get("expires_at"),
    )
    expected = _build_static_pose_candidate_contract(
        project_state=project_state,
        presence_lease=payload["presence_lease"],
        discovery=payload["discovery"],
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        issued_at=payload["issued_at"],
        expires_at=payload["expires_at"],
        execution_class=expected_execution_class,
    )
    if payload != expected:
        raise ValueError("Static pose live candidate contract source or semantics drifted")


def resolve_static_pose_candidate_cameras(
    *,
    discovery: dict[str, Any],
    static_pose_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Resolve fresh numeric indexes from ordered stable camera identities."""

    verify_signed_payload(static_pose_contract, label="Static pose bracket contract")
    if (
        static_pose_contract.get("identity_sha256")
        != ACCEPTED_STATIC_POSE_BRACKET_CONTRACT_IDENTITY
    ):
        raise ValueError("Static pose camera resolution contract identity drifted")
    avfoundation = discovery.get("avfoundation_devices")
    if not isinstance(avfoundation, list) or not avfoundation:
        raise ValueError("Fresh camera discovery has no AVFoundation devices")
    selections = [
        resolve_camera_selection(discovery, [device.get("index")])[0]
        for device in avfoundation
    ]
    resolved = []
    selected_indexes = []
    for expected in static_pose_contract.get("cameras", []):
        stable_identity = expected.get("stable_camera_identity_sha256")
        matches = [
            camera
            for camera in selections
            if stable_camera_identity_sha256(camera) == stable_identity
        ]
        if len(matches) != 1:
            raise ValueError(
                "Fresh discovery must resolve exactly one stable target camera"
            )
        camera = matches[0]
        if camera.get("input_mode") != expected.get("input_mode"):
            raise ValueError("Fresh target camera input mode drifted")
        selected_indexes.append(camera["index"])
        resolved.append(
            {
                "stable_camera_identity_sha256": stable_identity,
                "capture_camera_identity_sha256": _sha256_payload(camera),
                "resolved_camera": copy.deepcopy(camera),
                "static_camera_contract": copy.deepcopy(expected),
            }
        )
    if len(resolved) != 2 or len(set(selected_indexes)) != len(selected_indexes):
        raise ValueError("Fresh target camera resolution is ambiguous")
    return resolved


def run_static_pose_live_candidate(
    candidate_contract: dict[str, Any],
    *,
    hardware_execution_profile: dict[str, Any],
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
    transport_factory: Callable[[dict[str, Any]], StaticPoseTransport],
    camera_factory: Callable[
        [dict[str, Any], dict[str, Any]], FiniteStaticPoseCamera
    ],
    pre_open_holder_snapshot: dict[str, Any],
    post_close_holder_snapshot_factory: Callable[[], dict[str, Any]],
    monotonic_ns: Callable[[], int],
) -> dict[str, Any]:
    """Run one live-marked candidate lifecycle with no physical proof label."""

    current_thread_id = require_nonblank(
        os.environ.get("CODEX_THREAD_ID"),
        label="active Codex hardware thread ID",
    )
    verify_hardware_execution_profile_evidence(
        hardware_execution_profile,
        repo_root=REPO_ROOT,
        now=now,
        expected_thread_id=current_thread_id,
    )
    hardware_profile_identity = _require_sha256(
        hardware_execution_profile.get("identity_sha256"),
        label="hardware execution profile identity",
    )

    return _run_static_pose_candidate(
        candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
        transport_factory=transport_factory,
        camera_factory=camera_factory,
        pre_open_holder_snapshot=pre_open_holder_snapshot,
        post_close_holder_snapshot_factory=post_close_holder_snapshot_factory,
        monotonic_ns=monotonic_ns,
        execution_class="live_candidate",
        hardware_execution_profile_identity_sha256=hardware_profile_identity,
    )


def run_static_pose_live_candidate_fixture(
    candidate_contract: dict[str, Any],
    *,
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
    transport_factory: Callable[[dict[str, Any]], StaticPoseTransport],
    camera_factory: Callable[
        [dict[str, Any], dict[str, Any]], FiniteStaticPoseCamera
    ],
    pre_open_holder_snapshot: dict[str, Any],
    post_close_holder_snapshot_factory: Callable[[], dict[str, Any]],
    monotonic_ns: Callable[[], int],
) -> dict[str, Any]:
    """Exercise the candidate runner with explicit fixture-only backends."""

    return _run_static_pose_candidate(
        candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
        transport_factory=transport_factory,
        camera_factory=camera_factory,
        pre_open_holder_snapshot=pre_open_holder_snapshot,
        post_close_holder_snapshot_factory=post_close_holder_snapshot_factory,
        monotonic_ns=monotonic_ns,
        execution_class="deterministic_candidate_fixture",
        hardware_execution_profile_identity_sha256=None,
    )


def _run_static_pose_candidate(
    candidate_contract: dict[str, Any],
    *,
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
    transport_factory: Callable[[dict[str, Any]], StaticPoseTransport],
    camera_factory: Callable[
        [dict[str, Any], dict[str, Any]], FiniteStaticPoseCamera
    ],
    pre_open_holder_snapshot: dict[str, Any],
    post_close_holder_snapshot_factory: Callable[[], dict[str, Any]],
    monotonic_ns: Callable[[], int],
    execution_class: str,
    hardware_execution_profile_identity_sha256: str | None,
) -> dict[str, Any]:
    """Run one candidate lifecycle after every source and gate check passes."""

    classification = _candidate_execution_classification(execution_class)
    contract_verifier = (
        verify_static_pose_live_candidate_contract
        if execution_class == "live_candidate"
        else verify_static_pose_live_candidate_fixture_contract
    )
    contract_verifier(
        candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
    )
    _require_candidate_holder_paths(
        pre_open_holder_snapshot,
        expected_paths=candidate_contract["serial_identity_paths"],
    )
    camera_by_stable_identity = {
        camera["stable_camera_identity_sha256"]: camera
        for camera in candidate_contract["cameras"]
    }

    def bound_camera_factory(
        static_camera: dict[str, Any],
    ) -> FiniteStaticPoseCamera:
        resolved = camera_by_stable_identity.get(
            static_camera.get("stable_camera_identity_sha256")
        )
        if resolved is None:
            raise ValueError("Static pose candidate camera binding is missing")
        return camera_factory(
            copy.deepcopy(resolved["resolved_camera"]),
            copy.deepcopy(static_camera),
        )

    capture = _capture_static_pose_bracket_runtime(
        static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        transport_factory=lambda: transport_factory(copy.deepcopy(candidate_contract)),
        camera_factory=bound_camera_factory,
        pre_open_holder_snapshot=pre_open_holder_snapshot,
        post_close_holder_snapshot_factory=post_close_holder_snapshot_factory,
        monotonic_ns=monotonic_ns,
        expected_transport_evidence_mode=classification[
            "transport_evidence_mode"
        ],
        expected_camera_evidence_mode=classification["camera_evidence_mode"],
        expected_hardware_opened=classification["hardware_opened"],
    )
    _require_candidate_holder_paths(
        capture["post_close_holder_snapshot"],
        expected_paths=candidate_contract["serial_identity_paths"],
    )
    measurements = evaluate_static_pose_bracket_measurements(
        contract=static_pose_contract,
        timing=capture["timing"],
        q_before=capture["q_before"],
        cameras=capture["cameras"],
        q_after=capture["q_after"],
        operation_counts=capture["operation_counts"],
    )
    _require_candidate_duration(capture, candidate_contract=candidate_contract)
    result = sign_payload(
        {
            "schema_version": STATIC_POSE_LIVE_CANDIDATE_RESULT_SCHEMA_VERSION,
            "result_name": "pi05_static_pose_live_candidate_runtime",
            "qualification_scope": "local_static_pose_live_candidate_runtime",
            "evidence_mode": classification["result_evidence_mode"],
            "execution_class": execution_class,
            "candidate_only": True,
            "verified_at": now,
            "candidate_contract_identity_sha256": candidate_contract[
                "identity_sha256"
            ],
            "static_pose_contract_identity_sha256": static_pose_contract[
                "identity_sha256"
            ],
            "project_state_identity_sha256": candidate_contract[
                "project_state_identity_sha256"
            ],
            "presence_lease_identity_sha256": candidate_contract[
                "presence_lease_identity_sha256"
            ],
            "discovery_identity_sha256": candidate_contract[
                "discovery_identity_sha256"
            ],
            "hardware_execution_profile_identity_sha256": (
                hardware_execution_profile_identity_sha256
            ),
            "capture": copy.deepcopy(capture),
            "measurements": measurements,
            "resolved_camera_binding": [
                {
                    "stable_camera_identity_sha256": camera[
                        "stable_camera_identity_sha256"
                    ],
                    "capture_camera_identity_sha256": camera[
                        "capture_camera_identity_sha256"
                    ],
                    "numeric_index": camera["resolved_camera"]["index"],
                }
                for camera in candidate_contract["cameras"]
            ],
            "local_capabilities": [classification["local_capability"]],
            "proof_labels": [],
            "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
            "hardware_opened": classification["hardware_opened"],
            "physical_follower_commanded": False,
            "policy_inference_run": False,
            "motion_authority_granted": False,
            "training_authority_granted": False,
            "private_output_required": True,
            "tracked_redacted_manifest_written": False,
        }
    )
    result_verifier = (
        verify_static_pose_live_candidate_result
        if execution_class == "live_candidate"
        else verify_static_pose_live_candidate_fixture_result
    )
    result_verifier(
        result,
        candidate_contract=candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
    )
    return result


def verify_static_pose_live_candidate_result(
    result: dict[str, Any],
    *,
    candidate_contract: dict[str, Any],
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
) -> None:
    """Verify a fixed live-marked candidate-only runtime result."""

    _verify_static_pose_candidate_result(
        result,
        candidate_contract=candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
        expected_execution_class="live_candidate",
    )


def verify_static_pose_live_candidate_fixture_result(
    result: dict[str, Any],
    *,
    candidate_contract: dict[str, Any],
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
) -> None:
    """Verify a fixed no-hardware candidate fixture result."""

    _verify_static_pose_candidate_result(
        result,
        candidate_contract=candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
        expected_execution_class="deterministic_candidate_fixture",
    )


def _verify_static_pose_candidate_result(
    result: dict[str, Any],
    *,
    candidate_contract: dict[str, Any],
    project_state: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
    now: str,
    expected_execution_class: str,
) -> None:
    """Independently verify fixed-class runtime evidence and authority fields."""

    allowed_fields = {
        "schema_version",
        "result_name",
        "qualification_scope",
        "evidence_mode",
        "execution_class",
        "candidate_only",
        "verified_at",
        "candidate_contract_identity_sha256",
        "static_pose_contract_identity_sha256",
        "project_state_identity_sha256",
        "presence_lease_identity_sha256",
        "discovery_identity_sha256",
        "hardware_execution_profile_identity_sha256",
        "capture",
        "measurements",
        "resolved_camera_binding",
        "local_capabilities",
        "proof_labels",
        "authority_not_granted",
        "hardware_opened",
        "physical_follower_commanded",
        "policy_inference_run",
        "motion_authority_granted",
        "training_authority_granted",
        "private_output_required",
        "tracked_redacted_manifest_written",
        "identity_sha256",
    }
    if not isinstance(result, dict) or set(result) != allowed_fields:
        raise ValueError("Static pose live candidate result fields are malformed")
    if (
        result.get("schema_version")
        != STATIC_POSE_LIVE_CANDIDATE_RESULT_SCHEMA_VERSION
    ):
        raise ValueError("Static pose live candidate result schema is unsupported")
    verify_signed_payload(result, label="Static pose live candidate result")
    if result.get("execution_class") != expected_execution_class:
        raise ValueError("Static pose live candidate result execution class drifted")
    classification = _candidate_execution_classification(expected_execution_class)
    profile_identity = result.get("hardware_execution_profile_identity_sha256")
    if expected_execution_class == "live_candidate":
        _require_sha256(profile_identity, label="hardware execution profile identity")
    elif profile_identity is not None:
        raise ValueError("Fixture candidate cannot bind a hardware execution profile")
    if result.get("verified_at") != now:
        raise ValueError("Static pose live candidate verification time drifted")
    contract_verifier = (
        verify_static_pose_live_candidate_contract
        if expected_execution_class == "live_candidate"
        else verify_static_pose_live_candidate_fixture_contract
    )
    contract_verifier(
        candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
    )
    if (
        result.get("candidate_contract_identity_sha256")
        != candidate_contract.get("identity_sha256")
        or result.get("static_pose_contract_identity_sha256")
        != static_pose_contract.get("identity_sha256")
        or result.get("project_state_identity_sha256")
        != candidate_contract.get("project_state_identity_sha256")
        or result.get("presence_lease_identity_sha256")
        != candidate_contract.get("presence_lease_identity_sha256")
        or result.get("discovery_identity_sha256")
        != candidate_contract.get("discovery_identity_sha256")
    ):
        raise ValueError("Static pose live candidate result source linkage drifted")
    capture = result.get("capture")
    verify_static_pose_runtime_capture(
        capture,
        contract=static_pose_contract,
        expected_transport_evidence_mode=classification[
            "transport_evidence_mode"
        ],
        expected_camera_evidence_mode=classification["camera_evidence_mode"],
        expected_hardware_opened=classification["hardware_opened"],
    )
    _require_candidate_duration(capture, candidate_contract=candidate_contract)
    for snapshot in (
        capture["pre_open_holder_snapshot"],
        capture["post_close_holder_snapshot"],
    ):
        _require_candidate_holder_paths(
            snapshot,
            expected_paths=candidate_contract["serial_identity_paths"],
        )
    expected_measurements = evaluate_static_pose_bracket_measurements(
        contract=static_pose_contract,
        timing=capture["timing"],
        q_before=capture["q_before"],
        cameras=capture["cameras"],
        q_after=capture["q_after"],
        operation_counts=capture["operation_counts"],
    )
    if result.get("measurements") != expected_measurements:
        raise ValueError("Static pose live candidate measurements drifted")
    expected_camera_binding = [
        {
            "stable_camera_identity_sha256": camera[
                "stable_camera_identity_sha256"
            ],
            "capture_camera_identity_sha256": camera[
                "capture_camera_identity_sha256"
            ],
            "numeric_index": camera["resolved_camera"]["index"],
        }
        for camera in candidate_contract["cameras"]
    ]
    if result.get("resolved_camera_binding") != expected_camera_binding:
        raise ValueError("Static pose live candidate camera binding drifted")
    if (
        result.get("result_name") != "pi05_static_pose_live_candidate_runtime"
        or result.get("qualification_scope")
        != "local_static_pose_live_candidate_runtime"
        or result.get("evidence_mode")
        != classification["result_evidence_mode"]
        or result.get("candidate_only") is not True
        or result.get("local_capabilities")
        != [classification["local_capability"]]
        or result.get("proof_labels") != []
        or result.get("authority_not_granted") != _AUTHORITY_NOT_GRANTED
        or result.get("hardware_opened") is not classification["hardware_opened"]
        or result.get("physical_follower_commanded") is not False
        or result.get("policy_inference_run") is not False
        or result.get("motion_authority_granted") is not False
        or result.get("training_authority_granted") is not False
        or result.get("private_output_required") is not True
        or result.get("tracked_redacted_manifest_written") is not False
    ):
        raise ValueError("Static pose live candidate result authority fields drifted")


def verify_static_pose_live_candidate_result_from_embedded_authority(
    result: dict[str, Any],
    *,
    candidate_contract: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
) -> None:
    """Verify retained private evidence after canonical state has reclosed."""

    project_state = candidate_contract.get("project_state")
    if not isinstance(project_state, dict):
        raise ValueError("Candidate contract embedded project state is missing")
    now = result.get("verified_at")
    verify_static_pose_live_candidate_result(
        result,
        candidate_contract=candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=now,
    )


def verify_static_pose_live_candidate_fixture_result_from_embedded_authority(
    result: dict[str, Any],
    *,
    candidate_contract: dict[str, Any],
    static_pose_contract: dict[str, Any],
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
) -> None:
    """Verify retained fixture evidence from its embedded authority snapshot."""

    project_state = candidate_contract.get("project_state")
    if not isinstance(project_state, dict):
        raise ValueError("Candidate contract embedded project state is missing")
    verify_static_pose_live_candidate_fixture_result(
        result,
        candidate_contract=candidate_contract,
        project_state=project_state,
        static_pose_contract=static_pose_contract,
        calibration_path=calibration_path,
        calibration_profile_path=calibration_profile_path,
        manifest_path=manifest_path,
        now=result.get("verified_at"),
    )


def _validated_live_gate_snapshot(
    project_state: dict[str, Any],
    *,
    now: str,
    expires_at: str,
) -> dict[str, Any]:
    task = project_state.get("tasks", {}).get("T16.5b")
    if not isinstance(task, dict) or task.get("state") != "verified":
        raise ValueError("T16.5b is not verified for a static pose candidate")
    if task.get("live_gate") != "open":
        raise ValueError("Static pose candidate live gate is not open")
    opened_at = _parse_time(task.get("live_gate_opened_at"), label="gate opened_at")
    valid_until = _parse_time(
        task.get("live_gate_valid_until"), label="gate valid_until"
    )
    observed = _parse_time(now, label="gate verification time")
    expires = _parse_time(expires_at, label="candidate expires_at")
    if observed < opened_at or observed > valid_until:
        raise ValueError("Static pose candidate live gate is not active")
    if expires > valid_until:
        raise ValueError("Static pose candidate outlives its live gate")
    session_limit = task.get("live_gate_session_limit")
    sessions_started = task.get("live_gate_sessions_started")
    if session_limit != 1 or sessions_started != 0:
        raise ValueError("Static pose candidate requires one unconsumed gate session")
    if task.get("live_gate_scope") != LIVE_GATE_SCOPE:
        raise ValueError("Static pose candidate live gate scope drifted")
    if (
        task.get("live_gate_execution_profile") != HARDWARE_EXECUTION_PROFILE
        or task.get("live_gate_approval_policy") != HARDWARE_APPROVAL_POLICY
    ):
        raise ValueError("Static pose candidate supervised execution profile drifted")
    review_decision_id = require_nonblank(
        task.get("live_gate_review_decision_id"),
        label="static pose live gate review decision",
    )
    return {
        "state": "open",
        "opened_at": task["live_gate_opened_at"],
        "valid_until": task["live_gate_valid_until"],
        "session_limit": 1,
        "sessions_started": 0,
        "scope": LIVE_GATE_SCOPE,
        "execution_profile": HARDWARE_EXECUTION_PROFILE,
        "approval_policy": HARDWARE_APPROVAL_POLICY,
        "review_decision_id": review_decision_id,
    }


def _require_candidate_holder_paths(
    snapshot: dict[str, Any],
    *,
    expected_paths: list[str],
) -> None:
    if snapshot.get("paths_checked") != expected_paths:
        raise ValueError("Static pose candidate holder path identity drifted")


def _require_candidate_duration(
    capture: dict[str, Any],
    *,
    candidate_contract: dict[str, Any],
) -> None:
    maximum_seconds = candidate_contract.get("maximum_execution_duration_seconds")
    if (
        type(maximum_seconds) is not int
        or maximum_seconds <= 0
        or capture.get("runtime_duration_ns") > maximum_seconds * 1_000_000_000
    ):
        raise ValueError("Static pose candidate execution duration exceeded")


def _candidate_execution_classification(execution_class: Any) -> dict[str, Any]:
    classifications = {
        "deterministic_candidate_fixture": {
            "contract_evidence_mode": (
                "deterministic_source_bound_live_candidate_fixture_contract"
            ),
            "contract_local_capability": (
                "fixture_static_pose_live_candidate_contract_conformant"
            ),
            "hardware_access_authorized": False,
            "transport_evidence_mode": (
                "source_bound_candidate_fixture_transport"
            ),
            "camera_evidence_mode": "source_bound_candidate_fixture_camera",
            "result_evidence_mode": (
                "deterministic_source_bound_live_candidate_fixture"
            ),
            "local_capability": (
                "source_bound_static_pose_live_candidate_runtime_conformant"
            ),
            "hardware_opened": False,
        },
        "live_candidate": {
            "contract_evidence_mode": (
                "private_source_bound_live_candidate_contract"
            ),
            "contract_local_capability": (
                "static_pose_live_candidate_contract_valid"
            ),
            "hardware_access_authorized": True,
            "transport_evidence_mode": "live_injected_transport",
            "camera_evidence_mode": "live_injected_camera",
            "result_evidence_mode": "private_source_bound_live_candidate_runtime",
            "local_capability": (
                "source_bound_static_pose_live_candidate_runtime_observed"
            ),
            "hardware_opened": True,
        },
    }
    classification = classifications.get(execution_class)
    if classification is None:
        raise ValueError("Static pose candidate execution class is unsupported")
    return classification


def _artifact_reference(
    path: Path,
    *,
    logical_path: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if load_strict_json(path) != payload:
        raise ValueError(f"Source artifact content drifted: {logical_path}")
    return {
        "logical_path": logical_path,
        "schema_version": payload["schema_version"],
        "identity_sha256": payload["identity_sha256"],
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }


def _validated_source_paths(
    *,
    calibration_path: Path,
    calibration_profile_path: Path,
    manifest_path: Path,
) -> tuple[Path, Path, Path, Path]:
    calibration = Path(calibration_path).expanduser().resolve()
    profile = Path(calibration_profile_path).resolve()
    manifest = Path(manifest_path).resolve()
    expected_profile = (
        REPO_ROOT / "configurations/robot_lab/pi05_calibration_profile.json"
    ).resolve()
    expected_manifest = (
        REPO_ROOT
        / "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
    ).resolve()
    static_contract = (
        REPO_ROOT / "configurations/robot_lab/pi05_static_pose_bracket_contract.json"
    ).resolve()
    if calibration != DEFAULT_FOLLOWER_CALIBRATION_PATH.resolve():
        raise ValueError("Static pose candidate calibration path is not canonical")
    if profile != expected_profile or manifest != expected_manifest:
        raise ValueError("Static pose candidate source artifact path is not canonical")
    if not all(
        path.is_file()
        for path in (calibration, profile, manifest, static_contract)
    ):
        raise ValueError("Static pose candidate source artifact is missing")
    return calibration, profile, manifest, static_contract


def _parse_time(value: Any, *, label: str) -> datetime:
    text = require_nonblank(value, label=label)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a UTC offset")
    return parsed


def _require_sha256(value: Any, *, label: str) -> str:
    digest = require_nonblank(value, label=label)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return digest


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
