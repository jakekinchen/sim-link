from __future__ import annotations

import copy
import json
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.calibration_profile import (
    ACCEPTED_LIVE_MANIFEST_IDENTITY,
    CALIBRATION_PROFILE_SCHEMA_VERSION,
    EXPECTED_JOINT_IDS,
    build_calibration_profile,
    verify_calibration_profile,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_PATH = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
MANIFEST_PATH = (
    REPO_ROOT
    / "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
PROFILE_PATH = REPO_ROOT / "configurations/robot_lab/pi05_calibration_profile.json"


class CalibrationProfileTests(unittest.TestCase):
    def _build(self) -> dict:
        return build_calibration_profile(
            calibration_path=CALIBRATION_PATH,
            manifest_path=MANIFEST_PATH,
        )

    def _mutated_calibration(self, mutate) -> Path:
        payload = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
        mutate(payload)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "follower_arm.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _mutated_manifest(self, mutate) -> Path:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        mutate(payload)
        payload = sign_payload(payload)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "manifest.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_builds_signed_profile_bound_to_live_servo_identity(self):
        profile = self._build()
        verify_calibration_profile(
            profile,
            calibration_path=CALIBRATION_PATH,
            manifest_path=MANIFEST_PATH,
        )

        self.assertEqual(profile["schema_version"], CALIBRATION_PROFILE_SCHEMA_VERSION)
        self.assertEqual(
            profile["accepted_live_manifest"]["identity_sha256"],
            ACCEPTED_LIVE_MANIFEST_IDENTITY,
        )
        self.assertEqual(
            [(joint["joint_name"], joint["servo_id"]) for joint in profile["joints"]],
            list(EXPECTED_JOINT_IDS.items()),
        )
        self.assertEqual(
            profile["joints"][0]["normalization"]["mode"], "degrees"
        )
        gripper = profile["joints"][-1]["normalization"]
        self.assertEqual(gripper["mode"], "range_0_100")
        self.assertEqual(gripper["normalized_0_physical_meaning"], "closed")
        self.assertEqual(gripper["normalized_100_physical_meaning"], "open")
        self.assertEqual(
            profile["local_capabilities"], ["calibration_profile_semantically_valid"]
        )
        self.assertFalse(profile["physical_follower_commanded"])
        self.assertFalse(profile["hardware_accessed"])
        self.assertNotIn("/dev/", str(profile))
        self.assertNotIn(str(Path.home()), str(profile))

    def test_checked_in_profile_rebuilds_exactly_from_pinned_sources(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        verify_calibration_profile(
            profile,
            calibration_path=CALIBRATION_PATH,
            manifest_path=MANIFEST_PATH,
        )
        self.assertEqual(profile, self._build())

    def test_rejects_missing_extra_and_duplicate_joint_identity(self):
        cases = (
            (
                "missing",
                lambda payload: payload.pop("wrist_roll"),
                "exactly the expected six joints",
            ),
            (
                "extra",
                lambda payload: payload.__setitem__("extra", copy.deepcopy(payload["gripper"])),
                "exactly the expected six joints",
            ),
            (
                "duplicate",
                lambda payload: payload["gripper"].__setitem__("id", 5),
                "duplicate servo id",
            ),
            (
                "wrong id",
                lambda payload: payload["gripper"].__setitem__("id", 7),
                "servo id mismatch",
            ),
        )
        for label, mutate, message in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, message):
                    build_calibration_profile(
                        calibration_path=self._mutated_calibration(mutate),
                        manifest_path=MANIFEST_PATH,
                    )

    def test_rejects_invalid_integer_ranges_offsets_and_drive_modes(self):
        cases = (
            (
                "boolean",
                lambda payload: payload["shoulder_pan"].__setitem__("homing_offset", True),
                "homing_offset must be an integer",
            ),
            (
                "float",
                lambda payload: payload["shoulder_pan"].__setitem__("range_min", 755.5),
                "range_min must be an integer",
            ),
            (
                "inverted",
                lambda payload: payload["shoulder_pan"].update(
                    {"range_min": 1000, "range_max": 1000}
                ),
                "range_min must be less than range_max",
            ),
            (
                "range domain",
                lambda payload: payload["shoulder_pan"].__setitem__("range_max", 4096),
                "range_max is outside",
            ),
            (
                "offset domain",
                lambda payload: payload["shoulder_pan"].__setitem__("homing_offset", 2048),
                "homing_offset is outside",
            ),
            (
                "drive mode",
                lambda payload: payload["shoulder_pan"].__setitem__("drive_mode", 1),
                "drive_mode must be zero",
            ),
        )
        for label, mutate, message in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, message):
                    build_calibration_profile(
                        calibration_path=self._mutated_calibration(mutate),
                        manifest_path=MANIFEST_PATH,
                    )

    def test_rejects_calibration_and_manifest_substitution(self):
        calibration = self._mutated_calibration(
            lambda payload: payload["shoulder_pan"].__setitem__("homing_offset", 1067)
        )
        with self.assertRaisesRegex(ValueError, "calibration source identity"):
            build_calibration_profile(
                calibration_path=calibration,
                manifest_path=MANIFEST_PATH,
            )

        manifest = self._mutated_manifest(
            lambda payload: payload.__setitem__("session_id", "substituted")
        )
        with self.assertRaisesRegex(ValueError, "[Aa]ccepted live manifest identity"):
            build_calibration_profile(
                calibration_path=CALIBRATION_PATH,
                manifest_path=manifest,
            )

    def test_rejects_resigned_semantic_drift_and_extra_fields(self):
        for label, mutate in (
            (
                "formula",
                lambda payload: payload["joints"][0]["normalization"].__setitem__(
                    "formula", "raw_value"
                ),
            ),
            (
                "gripper polarity",
                lambda payload: payload["joints"][-1]["normalization"].update(
                    {
                        "normalized_0_physical_meaning": "open",
                        "normalized_100_physical_meaning": "closed",
                    }
                ),
            ),
            (
                "global authority",
                lambda payload: payload.__setitem__("physical_transfer_ready", True),
            ),
        ):
            with self.subTest(label=label):
                profile = self._build()
                mutate(profile)
                profile = sign_payload(profile)
                with self.assertRaisesRegex(ValueError, "semantic or source drift"):
                    verify_calibration_profile(
                        profile,
                        calibration_path=CALIBRATION_PATH,
                        manifest_path=MANIFEST_PATH,
                    )


if __name__ == "__main__":
    unittest.main()
