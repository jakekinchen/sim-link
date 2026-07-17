from __future__ import annotations

import copy
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.authority_composer import (
    compose_rgb_camera_census_authority,
    verify_rgb_camera_census_authority,
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


NOW = "2026-07-16T22:40:00-05:00"
EXPIRES = "2026-07-16T22:50:00-05:00"
BRANCH = "codex/pi05-autolearn-loop"
HEAD = "a" * 40


def _state() -> dict:
    return {
        "schema_version": "scenesmith.project_state.v1",
        "branch": BRANCH,
        "owner_authority": {
            "current_rgb_camera_census_window": {
                "state": (
                    "owner_presence_and_rgb_camera_access_granted_pending_"
                    "central_and_session_permits"
                ),
                "recorded_at": "2026-07-16T22:25:00-05:00",
                "valid_through": "2026-07-16T23:25:00-05:00",
                "owner_present": True,
                "camera_access_authorized": True,
                "scope": [
                    "d405_uvc_rgb_metadata_and_one_frame",
                    "c922_rgb_metadata_and_one_frame",
                    "coarse_host_observation_latency",
                ],
                "required_before_any_access": [
                    "same_thread_danger_full_access_verified",
                    "same_thread_approval_policy_never_verified",
                    "fresh_central_camera_session_decision",
                    "finite_content_addressed_one_use_camera_permit",
                    "remote_preservation_and_review",
                ],
                "not_authorized": [
                    "depth_stream",
                    "librealsense",
                    "serial_access",
                    "register_read",
                    "register_write",
                    "torque_change",
                    "motion",
                    "audio_capture",
                    "inference",
                    "training",
                    "network_access",
                    "external_compute",
                    "brev_compute",
                    "physical_qualification",
                    "physical_transfer",
                    "promotion",
                ],
                "physical_access_performed_in_window": False,
            }
        },
        "support_tasks": {
            "K3": {
                "state": "in_progress",
                "active_brief_id": "228",
                "live_gate": "open",
                "session_limit": 1,
                "sessions_started": 0,
            }
        },
    }


def _runtime() -> dict:
    return sign_payload(
        {
            "schema_version": "test.hardware_profile.v1",
            "thread_id": "thread-1",
            "approval_policy": "never",
            "sandbox_mode": "danger-full-access",
        }
    )


def _repo() -> dict:
    return {
        "branch": BRANCH,
        "head": HEAD,
        "upstream_head": HEAD,
        "remote_head": HEAD,
        "scoped_source_diff_clean": True,
        "gate_state_diff_clean": True,
    }


def _verify_runtime(payload: dict, **_: object) -> None:
    if payload != _runtime():
        raise ValueError("runtime drift")


def _mode(pixel: str = "uyvy422") -> dict:
    return {
        "pixel_format": pixel,
        "width": 640,
        "height": 480,
        "min_framerate_fps": 30.0,
        "max_framerate_fps": 30.0,
    }


def _discovery() -> dict:
    d405 = "Intel(R) RealSense(TM) Depth Camera 405 with RGB Module"
    c922 = "Logitech C922 Pro Stream Webcam"
    return build_rgb_camera_discovery(
        session_id="rgb-census-20260716-2240-cdt",
        captured_at=NOW,
        avfoundation_devices=[
            {"index": 0, "name": d405},
            {"index": 1, "name": c922},
        ],
        system_cameras=[
            {
                "name": d405,
                "unique_id": "private-d405-location",
                "model_id": "UVC Camera VendorID_32902 ProductID_2907",
                "supported_modes": [_mode()],
            },
            {
                "name": c922,
                "unique_id": "private-c922-location",
                "model_id": "UVC Camera VendorID_1133 ProductID_2140",
                "supported_modes": [_mode("nv12")],
            },
        ],
    )


class _Clock:
    def __init__(self) -> None:
        self.value = 1_000_000_000

    def __call__(self) -> int:
        value = self.value
        self.value += 5_000_000
        return value


class _FakeCamera:
    def __init__(self, camera: dict, clock: _Clock) -> None:
        self.camera = camera
        self.clock = clock
        self.opened = False
        self.released = False

    def open(self) -> None:
        self.opened = True

    def read(self) -> dict:
        if not self.opened or self.released:
            raise RuntimeError("camera lifecycle")
        started = self.clock()
        finished = self.clock()
        return {
            "frame_bytes": b"\x89PNG\r\n\x1a\nfixture",
            "encoding": "png",
            "width": 640,
            "height": 480,
            "channels": 3,
            "receive_started_monotonic_ns": started,
            "receive_finished_monotonic_ns": finished,
        }

    def release(self) -> None:
        self.released = True

    def audit(self) -> dict:
        return {
            "backend": "ffmpeg_named_avfoundation",
            "subprocess_start_attempts": 1,
            "subprocess_start_successes": 1,
            "release_attempts": 1,
            "release_successes": 1,
            "frames_delivered": 1,
            "capture_property_writes": 0,
            "continuous_recording_sessions": 0,
        }


class RgbCameraCensusAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "outputs/robot_lab/rgb_camera_census/private").mkdir(
            parents=True
        )
        (self.root / "configurations/robot_lab").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def compose(self, *, state: dict | None = None, repo: dict | None = None):
        return compose_rgb_camera_census_authority(
            project_state=state or _state(),
            runtime_profile=_runtime(),
            repo_root=self.root,
            session_id="rgb-census-20260716-2240-cdt",
            issued_at=NOW,
            expires_at=EXPIRES,
            private_output_dir=(
                "outputs/robot_lab/rgb_camera_census/private/"
                "rgb-census-20260716-2240-cdt"
            ),
            manifest_output=(
                "configurations/robot_lab/"
                "rgb_camera_census_20260716_2240.json"
            ),
            repository_state_loader=lambda **_: repo or _repo(),
            runtime_profile_verifier=_verify_runtime,
        )

    def test_central_grant_is_two_rgb_streams_one_frame_each(self) -> None:
        request, decision, permit = self.compose()
        self.assertTrue(decision["granted"])
        self.assertEqual(permit["maximum_camera_open_count"], 2)
        self.assertEqual(permit["frame_count_per_camera"], 1)
        self.assertEqual(permit["maximum_capture_duration_seconds"], 600)
        self.assertFalse(permit["depth_stream_authorized"])
        self.assertFalse(permit["serial_access_authorized"])
        self.assertFalse(permit["motion_authorized"])
        verify_rgb_camera_census_authority(
            request=request,
            decision=decision,
            permit=permit,
            project_state=_state(),
            runtime_profile=_runtime(),
            repo_root=self.root,
            now=NOW,
            repository_state_loader=lambda **_: _repo(),
            runtime_profile_verifier=_verify_runtime,
        )

    def test_closed_gate_and_remote_drift_deny_without_permit(self) -> None:
        state = _state()
        state["support_tasks"]["K3"]["live_gate"] = "closed"
        _, decision, permit = self.compose(state=state)
        self.assertFalse(decision["granted"])
        self.assertIsNone(permit)

    def test_expired_owner_window_and_bad_runtime_deny(self) -> None:
        state = _state()
        state["owner_authority"]["current_rgb_camera_census_window"][
            "valid_through"
        ] = "2026-07-16T22:30:00-05:00"
        _, decision, permit = self.compose(state=state)
        self.assertFalse(decision["granted"])
        self.assertIsNone(permit)
        _, decision, permit = compose_rgb_camera_census_authority(
            project_state=_state(),
            runtime_profile=_runtime(),
            repo_root=self.root,
            session_id="rgb-census-20260716-2240-cdt",
            issued_at=NOW,
            expires_at=EXPIRES,
            private_output_dir=(
                "outputs/robot_lab/rgb_camera_census/private/"
                "rgb-census-20260716-2240-cdt"
            ),
            manifest_output=(
                "configurations/robot_lab/rgb_camera_census_20260716_2240.json"
            ),
            repository_state_loader=lambda **_: _repo(),
            runtime_profile_verifier=lambda *args, **kwargs: (_ for _ in ()).throw(
                ValueError("wrong thread")
            ),
        )
        self.assertFalse(decision["granted"])
        self.assertIsNone(permit)
        repo = _repo()
        repo["remote_head"] = "b" * 40
        _, decision, permit = self.compose(repo=repo)
        self.assertFalse(decision["granted"])
        self.assertIsNone(permit)

    def test_path_escape_and_resigned_depth_escalation_reject(self) -> None:
        with self.assertRaisesRegex(ValueError, "private output"):
            compose_rgb_camera_census_authority(
                project_state=_state(),
                runtime_profile=_runtime(),
                repo_root=self.root,
                session_id="rgb-census-20260716-2240-cdt",
                issued_at=NOW,
                expires_at=EXPIRES,
                private_output_dir="../escape",
                manifest_output="configurations/robot_lab/result.json",
                repository_state_loader=lambda **_: _repo(),
                runtime_profile_verifier=_verify_runtime,
            )
        request, decision, permit = self.compose()
        forged = copy.deepcopy(permit)
        forged["depth_stream_authorized"] = True
        forged = sign_payload(
            {key: value for key, value in forged.items() if key != "identity_sha256"}
        )
        with self.assertRaises(ValueError):
            verify_rgb_camera_census_authority(
                request=request,
                decision=decision,
                permit=forged,
                project_state=_state(),
                runtime_profile=_runtime(),
                repo_root=self.root,
                now=NOW,
                repository_state_loader=lambda **_: _repo(),
                runtime_profile_verifier=_verify_runtime,
            )

    def test_fixture_capture_writes_two_signed_frames_and_redacted_manifest(self) -> None:
        request, decision, permit = self.compose()
        clock = _Clock()
        frames, result = execute_rgb_camera_census(
            permit=permit,
            discovery=_discovery(),
            camera_factory=lambda camera: _FakeCamera(camera, clock),
            monotonic_ns=clock,
            wall_time=lambda: NOW,
        )
        self.assertEqual(len(frames), 2)
        self.assertEqual(len(result["cameras"]), 2)
        self.assertEqual(result["rgb_streams_opened"], 2)
        self.assertEqual(result["depth_streams_opened"], 0)
        self.assertEqual(result["serial_devices_enumerated"], 0)
        private = build_private_rgb_camera_census(
            runtime_profile_identity_sha256=_runtime()["identity_sha256"],
            request=request,
            decision=decision,
            permit=permit,
            discovery=_discovery(),
            result=result,
            frames=frames,
            completed_at=NOW,
        )
        verify_private_rgb_camera_census(private, frames=frames)
        refs = write_private_rgb_camera_bundle(
            output_directory=self.root / permit["private_output_dir"],
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
        self.assertNotIn("private-d405-location", str(manifest))
        self.assertNotIn("private-c922-location", str(manifest))
        self.assertEqual(len(manifest["cameras"]), 2)
        self.assertEqual(
            [camera["frame_count"] for camera in manifest["cameras"]], [1, 1]
        )
        self.assertTrue(all(camera["signed_frame_identity_sha256"] for camera in manifest["cameras"]))

        tampered = copy.deepcopy(frames)
        tampered[0]["frame_bytes"] += b"tampered"
        with self.assertRaisesRegex(ValueError, "frame bytes"):
            verify_private_rgb_camera_census(private, frames=tampered)

    def test_missing_or_ambiguous_d405_rejects_before_open(self) -> None:
        _, _, permit = self.compose()
        discovery = _discovery()
        discovery = copy.deepcopy(discovery)
        discovery["system_cameras"] = discovery["system_cameras"][1:]
        discovery = sign_payload(
            {key: value for key, value in discovery.items() if key != "identity_sha256"}
        )
        opened = []
        with self.assertRaisesRegex(ValueError, "D405"):
            execute_rgb_camera_census(
                permit=permit,
                discovery=discovery,
                camera_factory=lambda camera: opened.append(camera),
                monotonic_ns=_Clock(),
                wall_time=lambda: NOW,
            )
        self.assertEqual(opened, [])

    def test_unsupported_mode_and_camera_property_write_reject(self) -> None:
        _, _, permit = self.compose()
        discovery = _discovery()
        unsupported = copy.deepcopy(discovery)
        unsupported["system_cameras"][0]["supported_modes"] = [
            {
                "pixel_format": "uyvy422",
                "width": 320,
                "height": 240,
                "min_framerate_fps": 30.0,
                "max_framerate_fps": 30.0,
            }
        ]
        unsupported = sign_payload(
            {key: value for key, value in unsupported.items() if key != "identity_sha256"}
        )
        with self.assertRaisesRegex(ValueError, "supported mode"):
            execute_rgb_camera_census(
                permit=permit,
                discovery=unsupported,
                camera_factory=lambda camera: self.fail("camera should not open"),
                monotonic_ns=_Clock(),
                wall_time=lambda: NOW,
            )

        clock = _Clock()

        class UnsafeCamera(_FakeCamera):
            def audit(self) -> dict:
                audit = super().audit()
                audit["capture_property_writes"] = 1
                return audit

        with self.assertRaisesRegex(ValueError, "audit"):
            execute_rgb_camera_census(
                permit=permit,
                discovery=_discovery(),
                camera_factory=lambda camera: UnsafeCamera(camera, clock),
                monotonic_ns=clock,
                wall_time=lambda: NOW,
            )


if __name__ == "__main__":
    unittest.main()
