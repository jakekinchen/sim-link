from __future__ import annotations

import copy
import subprocess
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.leader_arm_bridge import KNOWN_PHYSICAL_FOLLOWER_PORT
from scenesmith.robot_lab.live_readonly_observation import (
    enumerate_serial_identity_holders,
)
from scenesmith.robot_lab.virtual_follower_disconnect_proof import (
    build_private_virtual_disconnect_evidence,
    build_redacted_virtual_disconnect_proof,
    verify_private_virtual_disconnect_evidence,
    verify_redacted_virtual_disconnect_proof,
    write_private_virtual_disconnect_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_STATE = load_strict_json(
    REPO_ROOT / "docs/autonomous-workflow/project_state.json"
)
FOLLOWER_TTY_ALIAS = KNOWN_PHYSICAL_FOLLOWER_PORT.replace(
    "/dev/cu.", "/dev/tty.", 1
)


def _zero_holder_snapshot() -> dict:
    return enumerate_serial_identity_holders(
        KNOWN_PHYSICAL_FOLLOWER_PORT,
        [FOLLOWER_TTY_ALIAS],
        run_command=lambda command, **kwargs: subprocess.CompletedProcess(
            command, 1, "", ""
        ),
        path_exists=lambda path: True,
    )


def _held_holder_snapshot() -> dict:
    outputs = {
        KNOWN_PHYSICAL_FOLLOWER_PORT: (1, ""),
        FOLLOWER_TTY_ALIAS: (0, "p77\nctest-holder\nf4\ntCHR\n"),
    }

    def runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
        returncode, stdout = outputs[command[-1]]
        return subprocess.CompletedProcess(command, returncode, stdout, "")

    return enumerate_serial_identity_holders(
        KNOWN_PHYSICAL_FOLLOWER_PORT,
        [FOLLOWER_TTY_ALIAS],
        run_command=runner,
        path_exists=lambda path: True,
    )


def _observation() -> dict:
    return {
        "schema_version": "scenesmith.virtual_follower_disconnect_observation.v1",
        "provenance_class": "reconstructed_from_executor_operation_output",
        "reconstructed_at": "2026-07-11T09:30:00-05:00",
        "source_session_log": "docs/session-logs/060-virtual-follower-disconnect-and-zero-holder-proof.md",
        "source_reviewer_decision": "docs/reviewer-messages/056-virtual-follower-disconnect-verified.md",
        "permit_source_commit": "59f09d1576d777ee8e186ff885b58ac69c2a253d",
        "permit_source_path": "docs/autonomous-workflow/project_state.json",
        "permit_source_file_sha256": "a" * 64,
        "started_at": "2026-07-11T08:57:17-05:00",
        "finished_at": "2026-07-11T08:57:17-05:00",
        "timestamp_resolution_seconds": 1,
        "request": {
            "method": "POST",
            "path": "/api/hardware/disconnect",
            "body": {"role": "follower"},
        },
        "observed_call_count": 1,
        "response": {"http_status": 200, "body": {"connected": False}},
        "pre_hardware": {
            "leader": {
                "connected": True,
                "port": "/dev/cu.usbmodem5B3D0448141",
            },
            "follower": {
                "connected": True,
                "port": KNOWN_PHYSICAL_FOLLOWER_PORT,
                "torque": True,
            },
        },
        "post_hardware": {
            "leader": {
                "connected": True,
                "port": "/dev/cu.usbmodem5B3D0448141",
            },
            "follower": {"connected": False, "port": None, "torque": False},
        },
        "safety_before": {
            "armed": True,
            "deadmanRequired": True,
            "lastEstopAt": None,
            "limits": {"fixture": True},
            "simLockout": True,
        },
        "safety_after": {
            "armed": True,
            "deadmanRequired": True,
            "lastEstopAt": None,
            "limits": {"fixture": True},
            "simLockout": True,
        },
        "routing_before": {
            "follower": {"source": "none"},
            "linked": True,
            "twin": {"source": "sliders"},
        },
        "routing_after": {
            "follower": {"source": "none"},
            "linked": True,
            "twin": {"source": "sliders"},
        },
        "jobs_before": {"job_count": 50, "running_jobs": []},
        "jobs_after": {"job_count": 50, "running_jobs": []},
        "canonical_path_holder_snapshot_before": [
            {
                "pid": 62234,
                "command": "python3.13",
                "file_descriptors": ["15"],
                "file_types": ["CHR"],
            }
        ],
        "forbidden_effects_observed": [],
        "physical_motion_commanded": False,
        "physical_follower_commanded": False,
    }


class VirtualFollowerDisconnectProofTests(unittest.TestCase):
    def _private(self) -> dict:
        return build_private_virtual_disconnect_evidence(
            project_state=PROJECT_STATE,
            observation=_observation(),
            post_holder_snapshot=_zero_holder_snapshot(),
            post_holder_revalidated_at="2026-07-11T09:30:00-05:00",
        )

    def test_private_and_redacted_proof_bind_consumed_one_call_permit(self):
        private = self._private()
        verify_private_virtual_disconnect_evidence(
            private,
            project_state=PROJECT_STATE,
        )
        self.assertEqual(private["permit"]["maximum_call_count"], 1)
        self.assertEqual(private["observed_call_count"], 1)
        self.assertTrue(private["permit_consumed"])
        self.assertEqual(private["additional_calls_allowed"], 0)
        self.assertEqual(
            private["post_holder_snapshot"]["deduplicated_holder_count"], 0
        )
        self.assertFalse(private["physical_motion_commanded"])

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "private.json"
            reference = write_private_virtual_disconnect_evidence(
                path=path,
                evidence=private,
                reference_path=(
                    "outputs/robot_lab/virtual_disconnect/private/test/private.json"
                ),
            )
            redacted = build_redacted_virtual_disconnect_proof(
                private_evidence=private,
                private_evidence_reference=reference,
            )
            verify_redacted_virtual_disconnect_proof(
                redacted,
                private_evidence=private,
                private_evidence_reference=reference,
                project_state=PROJECT_STATE,
            )
            self.assertEqual(load_strict_json(path), private)
            self.assertNotIn(KNOWN_PHYSICAL_FOLLOWER_PORT, str(redacted))
            self.assertFalse(redacted["physical_motion_commanded"])
            self.assertEqual(redacted["forbidden_effects_observed"], [])

    def test_private_proof_rejects_resigned_authority_and_effect_mutations(self):
        base = self._private()
        mutations = (
            ("method", lambda p: p["request"].__setitem__("method", "GET")),
            ("path", lambda p: p["request"].__setitem__("path", "/wrong")),
            ("body", lambda p: p["request"].__setitem__("body", {"role": "leader"})),
            ("calls", lambda p: p.__setitem__("observed_call_count", 2)),
            ("response", lambda p: p["response"].__setitem__("http_status", 500)),
            (
                "leader",
                lambda p: p["post_hardware"]["leader"].__setitem__(
                    "connected", False
                ),
            ),
            ("safety", lambda p: p["safety_after"].__setitem__("armed", False)),
            (
                "routing",
                lambda p: p["routing_after"]["follower"].__setitem__(
                    "source", "leader"
                ),
            ),
            (
                "jobs",
                lambda p: p["jobs_after"]["running_jobs"].append(
                    {"id": "unexpected"}
                ),
            ),
            ("consumed", lambda p: p.__setitem__("permit_consumed", False)),
            ("reusable", lambda p: p.__setitem__("additional_calls_allowed", 1)),
            (
                "forbidden",
                lambda p: p["forbidden_effects_observed"].append("motion"),
            ),
            ("motion", lambda p: p.__setitem__("physical_motion_commanded", True)),
            (
                "follower_command",
                lambda p: p.__setitem__("physical_follower_commanded", True),
            ),
            (
                "holder",
                lambda p: p.__setitem__(
                    "post_holder_snapshot",
                    _held_holder_snapshot(),
                ),
            ),
            (
                "reconstruction_time",
                lambda p: p.__setitem__(
                    "reconstructed_at",
                    "2026-07-11T08:57:16-05:00",
                ),
            ),
            (
                "holder_time",
                lambda p: p.__setitem__(
                    "post_holder_revalidated_at",
                    "2026-07-11T08:57:16-05:00",
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(base)
                mutate(changed)
                changed = sign_payload(changed)
                with self.assertRaises(ValueError):
                    verify_private_virtual_disconnect_evidence(
                        changed,
                        project_state=PROJECT_STATE,
                    )

    def test_redacted_proof_rejects_missing_or_substituted_private_reference(self):
        private = self._private()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "private.json"
            reference = write_private_virtual_disconnect_evidence(
                path=path,
                evidence=private,
                reference_path=(
                    "outputs/robot_lab/virtual_disconnect/private/test/private.json"
                ),
            )
            redacted = build_redacted_virtual_disconnect_proof(
                private_evidence=private,
                private_evidence_reference=reference,
            )
            substituted = copy.deepcopy(reference)
            substituted["file_sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                verify_redacted_virtual_disconnect_proof(
                    redacted,
                    private_evidence=private,
                    private_evidence_reference=substituted,
                    project_state=PROJECT_STATE,
                )
            for unsafe_path in (
                "outputs/../private.json",
                "outputs/unrelated/private.json",
            ):
                with self.subTest(unsafe_path=unsafe_path):
                    aliased = copy.deepcopy(reference)
                    aliased["path"] = unsafe_path
                    with self.assertRaises(ValueError):
                        verify_redacted_virtual_disconnect_proof(
                            redacted,
                            private_evidence=private,
                            private_evidence_reference=aliased,
                            project_state=PROJECT_STATE,
                        )
            with self.assertRaisesRegex(ValueError, "new and immutable"):
                write_private_virtual_disconnect_evidence(
                    path=path,
                    evidence=private,
                    reference_path=reference["path"],
                )


if __name__ == "__main__":
    unittest.main()
