from __future__ import annotations

import copy
import json
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.static_pose_bracket import (
    STATIC_POSE_BRACKET_CONTRACT_SCHEMA_VERSION,
    STATIC_POSE_BRACKET_RESULT_SCHEMA_VERSION,
    build_fixture_static_pose_observation,
    build_static_pose_bracket_contract,
    evaluate_static_pose_bracket,
    verify_static_pose_bracket_contract,
    verify_static_pose_bracket_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_PATH = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
PROFILE_PATH = REPO_ROOT / "configurations/robot_lab/pi05_calibration_profile.json"
MANIFEST_PATH = (
    REPO_ROOT
    / "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
CONTRACT_PATH = (
    REPO_ROOT / "configurations/robot_lab/pi05_static_pose_bracket_contract.json"
)
FIXTURE_ROOT = REPO_ROOT / "tests/fixtures/robot_lab/static_pose_bracket"
OBSERVATION_PATH = FIXTURE_ROOT / "observation.fixture.json"
RESULT_PATH = FIXTURE_ROOT / "result.fixture.json"


class StaticPoseBracketTests(unittest.TestCase):
    def _contract(self) -> dict:
        return build_static_pose_bracket_contract(
            calibration_path=CALIBRATION_PATH,
            calibration_profile_path=PROFILE_PATH,
            manifest_path=MANIFEST_PATH,
        )

    def _observation(self, contract: dict | None = None) -> dict:
        return build_fixture_static_pose_observation(contract or self._contract())

    def _resign(self, payload: dict) -> dict:
        return sign_payload(payload)

    def test_contract_binds_profile_manifest_joints_cameras_and_authority(self):
        contract = self._contract()
        verify_static_pose_bracket_contract(
            contract,
            calibration_path=CALIBRATION_PATH,
            calibration_profile_path=PROFILE_PATH,
            manifest_path=MANIFEST_PATH,
        )
        self.assertEqual(
            contract["schema_version"], STATIC_POSE_BRACKET_CONTRACT_SCHEMA_VERSION
        )
        self.assertEqual(contract["joint_count"], 6)
        self.assertEqual(contract["camera_count"], 2)
        self.assertEqual(
            [joint["tolerance"] for joint in contract["joints"][:-1]],
            [0.5] * 5,
        )
        self.assertEqual(contract["joints"][-1]["tolerance"], 0.5)
        self.assertEqual(
            contract["local_capabilities"], ["static_pose_bracket_contract_valid"]
        )
        self.assertFalse(contract["lifecycle_constraints"]["handshake"])
        self.assertFalse(
            contract["lifecycle_constraints"]["disconnect_disable_torque"]
        )
        self.assertEqual(
            contract["serial_holder_contract"][
                "pre_open_deduplicated_holder_count"
            ],
            0,
        )
        self.assertEqual(
            contract["serial_holder_contract"][
                "post_close_deduplicated_holder_count"
            ],
            0,
        )
        self.assertFalse(contract["hardware_accessed"])
        self.assertFalse(contract["physical_follower_commanded"])
        self.assertNotIn("/dev/", str(contract))
        self.assertNotIn(str(Path.home()), str(contract))

    def test_fixture_result_converts_coordinates_and_accepts_static_pose(self):
        contract = self._contract()
        observation = self._observation(contract)
        result = evaluate_static_pose_bracket(
            contract=contract,
            observation=observation,
        )
        verify_static_pose_bracket_result(
            result,
            contract=contract,
            observation=observation,
        )
        self.assertEqual(
            result["schema_version"], STATIC_POSE_BRACKET_RESULT_SCHEMA_VERSION
        )
        self.assertTrue(result["static_pose_within_tolerance"])
        self.assertEqual(
            result["local_capabilities"], ["fixture_static_pose_bracket_conformant"]
        )
        self.assertEqual(result["joint_drift"][-1]["coordinate_units"], "percent")
        self.assertGreater(
            result["joint_drift"][-1]["coordinate_after"],
            result["joint_drift"][-1]["coordinate_before"],
        )
        self.assertFalse(result["physical_follower_commanded"])

    def test_rejects_missing_extra_duplicate_and_wrong_position_identity(self):
        cases = (
            (
                "missing",
                lambda payload: payload["q_before"].pop(),
                "q_before must contain exactly six positions",
            ),
            (
                "extra",
                lambda payload: payload["q_before"].append(
                    copy.deepcopy(payload["q_before"][-1])
                ),
                "q_before must contain exactly six positions",
            ),
            (
                "duplicate",
                lambda payload: payload["q_after"][-1].update(
                    {"joint_name": "wrist_roll", "servo_id": 5}
                ),
                "q_after has duplicate joint identity",
            ),
            (
                "wrong id",
                lambda payload: payload["q_after"][-1].__setitem__("servo_id", 7),
                "q_after servo identity mismatch",
            ),
        )
        for label, mutate, message in cases:
            with self.subTest(label=label):
                contract = self._contract()
                observation = self._observation(contract)
                mutate(observation)
                observation = self._resign(observation)
                with self.assertRaisesRegex(ValueError, message):
                    evaluate_static_pose_bracket(
                        contract=contract,
                        observation=observation,
                    )

    def test_rejects_boolean_noninteger_and_out_of_range_positions(self):
        cases = (
            (
                "boolean",
                lambda payload: payload["q_before"][0].__setitem__(
                    "raw_position", True
                ),
                "raw_position must be an integer",
            ),
            (
                "float",
                lambda payload: payload["q_before"][0].__setitem__(
                    "raw_position", 2000.5
                ),
                "raw_position must be an integer",
            ),
            (
                "below range",
                lambda payload: payload["q_before"][0].__setitem__(
                    "raw_position", 754
                ),
                "raw_position is outside calibrated range",
            ),
            (
                "above range",
                lambda payload: payload["q_after"][-1].__setitem__(
                    "raw_position", 2325
                ),
                "raw_position is outside calibrated range",
            ),
        )
        for label, mutate, message in cases:
            with self.subTest(label=label):
                contract = self._contract()
                observation = self._observation(contract)
                mutate(observation)
                observation = self._resign(observation)
                with self.assertRaisesRegex(ValueError, message):
                    evaluate_static_pose_bracket(
                        contract=contract,
                        observation=observation,
                    )

    def test_rejects_body_and_gripper_drift_beyond_signed_tolerance(self):
        for label, index, delta, message in (
            ("body", 0, 6, "shoulder_pan drift exceeds tolerance"),
            ("gripper", 5, 5, "gripper drift exceeds tolerance"),
        ):
            with self.subTest(label=label):
                contract = self._contract()
                observation = self._observation(contract)
                observation["q_after"][index]["raw_position"] = (
                    observation["q_before"][index]["raw_position"] + delta
                )
                observation = self._resign(observation)
                with self.assertRaisesRegex(ValueError, message):
                    evaluate_static_pose_bracket(
                        contract=contract,
                        observation=observation,
                    )

    def test_rejects_timestamp_order_and_duration_drift(self):
        cases = (
            (
                "camera before q",
                lambda payload: payload["timing"].__setitem__(
                    "camera_receive_started_monotonic_ns",
                    payload["timing"]["q_before_finished_monotonic_ns"] - 1,
                ),
                "camera interval is not enclosed by position reads",
            ),
            (
                "after before camera",
                lambda payload: payload["timing"].__setitem__(
                    "q_after_started_monotonic_ns",
                    payload["timing"]["camera_receive_finished_monotonic_ns"] - 1,
                ),
                "camera interval is not enclosed by position reads",
            ),
            (
                "too long",
                lambda payload: payload["timing"].__setitem__(
                    "q_after_finished_monotonic_ns",
                    payload["timing"]["q_before_started_monotonic_ns"]
                    + 5_000_000_001,
                ),
                "bracket duration exceeds contract",
            ),
        )
        for label, mutate, message in cases:
            with self.subTest(label=label):
                contract = self._contract()
                observation = self._observation(contract)
                mutate(observation)
                observation = self._resign(observation)
                with self.assertRaisesRegex(ValueError, message):
                    evaluate_static_pose_bracket(
                        contract=contract,
                        observation=observation,
                    )

    def test_rejects_camera_identity_mode_dimensions_and_duplicate_frames(self):
        cases = (
            (
                "identity",
                lambda payload: payload["cameras"][0].__setitem__(
                    "camera_identity_sha256", "f" * 64
                ),
                "camera identity mismatch",
            ),
            (
                "mode",
                lambda payload: payload["cameras"][0]["input_mode"].__setitem__(
                    "width", 800
                ),
                "camera input mode mismatch",
            ),
            (
                "dimensions",
                lambda payload: payload["cameras"][0]["frames"][0].__setitem__(
                    "height", 479
                ),
                "frame dimensions mismatch",
            ),
            (
                "duplicate frame",
                lambda payload: payload["cameras"][1]["frames"][0].__setitem__(
                    "frame_sha256",
                    payload["cameras"][0]["frames"][0]["frame_sha256"],
                ),
                "frame hashes must be unique",
            ),
        )
        for label, mutate, message in cases:
            with self.subTest(label=label):
                contract = self._contract()
                observation = self._observation(contract)
                mutate(observation)
                observation = self._resign(observation)
                with self.assertRaisesRegex(ValueError, message):
                    evaluate_static_pose_bracket(
                        contract=contract,
                        observation=observation,
                    )

    def test_rejects_operation_count_write_torque_motion_and_command_drift(self):
        cases = (
            (
                "reads",
                lambda payload: payload["operation_counts"].__setitem__(
                    "position_read_successes", 11
                ),
                "operation counts drifted",
            ),
            (
                "write",
                lambda payload: payload["operation_counts"].__setitem__(
                    "motor_register_writes", 1
                ),
                "operation counts drifted",
            ),
            (
                "torque",
                lambda payload: payload["operation_counts"].__setitem__(
                    "torque_changes", 1
                ),
                "operation counts drifted",
            ),
            (
                "motion",
                lambda payload: payload["operation_counts"].__setitem__(
                    "motion_commands", 1
                ),
                "operation counts drifted",
            ),
            (
                "command flag",
                lambda payload: payload.__setitem__(
                    "physical_follower_commanded", True
                ),
                "physical_follower_commanded must be false",
            ),
        )
        for label, mutate, message in cases:
            with self.subTest(label=label):
                contract = self._contract()
                observation = self._observation(contract)
                mutate(observation)
                observation = self._resign(observation)
                with self.assertRaisesRegex(ValueError, message):
                    evaluate_static_pose_bracket(
                        contract=contract,
                        observation=observation,
                    )

    def test_rejects_resigned_contract_and_result_semantic_drift(self):
        contract = self._contract()
        drifted_contract = copy.deepcopy(contract)
        drifted_contract["joints"][0]["tolerance"] = 1.0
        drifted_contract = self._resign(drifted_contract)
        with self.assertRaisesRegex(ValueError, "semantic or source drift"):
            verify_static_pose_bracket_contract(
                drifted_contract,
                calibration_path=CALIBRATION_PATH,
                calibration_profile_path=PROFILE_PATH,
                manifest_path=MANIFEST_PATH,
            )
        with self.assertRaisesRegex(ValueError, "semantic or source drift"):
            evaluate_static_pose_bracket(
                contract=drifted_contract,
                observation=self._observation(contract),
            )

        observation = self._observation(contract)
        result = evaluate_static_pose_bracket(
            contract=contract,
            observation=observation,
        )
        result["authority_not_granted"].remove("physical_twin_qualified")
        result["physical_twin_qualified"] = True
        result = self._resign(result)
        with self.assertRaisesRegex(ValueError, "semantic drift"):
            verify_static_pose_bracket_result(
                result,
                contract=contract,
                observation=observation,
            )

    def test_rejects_resigned_observation_extra_authority_or_nested_fields(self):
        for label, mutate, message in (
            (
                "top-level authority",
                lambda payload: payload.__setitem__("physical_transfer_ready", True),
                "observation fields are invalid",
            ),
            (
                "position field",
                lambda payload: payload["q_before"][0].__setitem__(
                    "normalized_position", 0.0
                ),
                "q_before position fields are invalid",
            ),
            (
                "camera field",
                lambda payload: payload["cameras"][0].__setitem__(
                    "raw_device_path", "/forbidden"
                ),
                "camera fields are invalid",
            ),
            (
                "frame field",
                lambda payload: payload["cameras"][0]["frames"][0].__setitem__(
                    "accepted", True
                ),
                "frame fields are invalid",
            ),
        ):
            with self.subTest(label=label):
                contract = self._contract()
                observation = self._observation(contract)
                mutate(observation)
                observation = self._resign(observation)
                with self.assertRaisesRegex(ValueError, message):
                    evaluate_static_pose_bracket(
                        contract=contract,
                        observation=observation,
                    )

    def test_checked_in_contract_observation_and_result_verify(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        observation = json.loads(OBSERVATION_PATH.read_text(encoding="utf-8"))
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        verify_static_pose_bracket_contract(
            contract,
            calibration_path=CALIBRATION_PATH,
            calibration_profile_path=PROFILE_PATH,
            manifest_path=MANIFEST_PATH,
        )
        verify_static_pose_bracket_result(
            result,
            contract=contract,
            observation=observation,
        )
        self.assertEqual(contract, self._contract())
        self.assertEqual(observation, self._observation(contract))


if __name__ == "__main__":
    unittest.main()
