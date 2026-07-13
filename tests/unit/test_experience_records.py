"""Tests for immutable M17 raw-rollout and frame-record contracts."""

from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.experience_records import (
    CONTRACT_PATH,
    REPO_ROOT,
    build_experience_record_contract,
    sign_record,
    validate_frame_records,
    validate_raw_rollout_record,
    verify_experience_record_contract,
)


class ExperienceRecordContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = load_strict_json(REPO_ROOT / CONTRACT_PATH)

    def test_checked_contract_is_deterministic_and_source_bound(self) -> None:
        verify_experience_record_contract(self.payload, repo_root=REPO_ROOT)
        self.assertEqual(self.payload, build_experience_record_contract(repo_root=REPO_ROOT))
        fixture = self.payload["fixture_projection"]
        self.assertFalse(fixture["training_eligible"])
        self.assertTrue(fixture["quarantine_reasons"])
        self.assertFalse(self.payload["simulation_training_ready"])

    def test_raw_payload_hash_drift_is_rejected(self) -> None:
        raw = copy.deepcopy(self.payload["fixture_projection"]["raw_rollout"])
        raw["raw_payload"]["source_artifact_identity_sha256"] = "0" * 64
        raw = sign_record(raw)
        with self.assertRaisesRegex(ValueError, "raw payload hash drifted"):
            validate_raw_rollout_record(raw, self.payload["source_grasp_artifact_ref"])

    def test_source_artifact_link_drift_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["source_grasp_artifact_ref"]["identity_sha256"] = "0" * 64
        payload = sign_payload(payload)
        with self.assertRaisesRegex(ValueError, "source grasp artifact linkage drifted"):
            verify_experience_record_contract(payload, repo_root=REPO_ROOT)

    def test_duplicate_frame_index_is_rejected(self) -> None:
        fixture = copy.deepcopy(self.payload["fixture_projection"])
        fixture["frames"][1]["frame_index"] = fixture["frames"][0]["frame_index"]
        fixture["frames"][1] = sign_record(fixture["frames"][1])
        with self.assertRaisesRegex(ValueError, "Duplicate frame frame_index"):
            validate_frame_records(fixture["frames"], fixture["raw_rollout"])

    def test_non_monotonic_frame_time_is_rejected(self) -> None:
        fixture = copy.deepcopy(self.payload["fixture_projection"])
        fixture["frames"][1]["timestamp_ns"] = fixture["frames"][0]["timestamp_ns"]
        fixture["frames"][1] = sign_record(fixture["frames"][1])
        with self.assertRaisesRegex(ValueError, "timestamps must increase"):
            validate_frame_records(fixture["frames"], fixture["raw_rollout"])

    def test_unknown_orthogonal_semantics_are_rejected(self) -> None:
        for field, bad_value in (
            ("source_class", "opaque_mixture"),
            ("task_phase", "recovery"),
            ("control_mode", "unknown"),
            ("controller_owner", "anonymous"),
        ):
            with self.subTest(field=field):
                fixture = copy.deepcopy(self.payload["fixture_projection"])
                fixture["frames"][0][field] = bad_value
                fixture["frames"][0] = sign_record(fixture["frames"][0])
                with self.assertRaisesRegex(ValueError, f"{field} is invalid"):
                    validate_frame_records(fixture["frames"], fixture["raw_rollout"])

    def test_unavailable_action_cannot_carry_values(self) -> None:
        fixture = copy.deepcopy(self.payload["fixture_projection"])
        fixture["frames"][0]["actions"]["measured"]["values"] = [0.0] * 6
        fixture["frames"][0] = sign_record(fixture["frames"][0])
        with self.assertRaisesRegex(ValueError, "unavailable action must not carry values"):
            validate_frame_records(fixture["frames"], fixture["raw_rollout"])

    def test_observed_action_requires_provenance(self) -> None:
        fixture = copy.deepcopy(self.payload["fixture_projection"])
        fixture["frames"][0]["actions"]["sent"] = {
            "state": "observed",
            "representation": "absolute_joint_radians_plus_gripper_radians",
            "units": "radian",
            "ordered_joint_names": [
                "shoulder_pan",
                "shoulder_lift",
                "elbow_flex",
                "wrist_flex",
                "wrist_roll",
                "gripper",
            ],
            "values": [0.0] * 6,
            "provenance": None,
            "reason": None,
        }
        fixture["frames"][0] = sign_record(fixture["frames"][0])
        with self.assertRaisesRegex(ValueError, "action provenance is required"):
            validate_frame_records(fixture["frames"], fixture["raw_rollout"])

    def test_actor_input_leakage_is_rejected(self) -> None:
        fixture = copy.deepcopy(self.payload["fixture_projection"])
        fixture["frames"][0]["actor_input_field_names"].append("progress.future_value")
        fixture["frames"][0] = sign_record(fixture["frames"][0])
        with self.assertRaisesRegex(ValueError, "actor input leaks privileged field"):
            validate_frame_records(fixture["frames"], fixture["raw_rollout"])

    def test_frame_id_drift_is_rejected(self) -> None:
        fixture = copy.deepcopy(self.payload["fixture_projection"])
        fixture["frames"][0]["frame_id"] = "unstable-frame-id"
        fixture["frames"][0] = sign_record(fixture["frames"][0])
        with self.assertRaisesRegex(ValueError, "Frame_id is not stable"):
            validate_frame_records(fixture["frames"], fixture["raw_rollout"])

    def test_rollout_id_drift_is_rejected(self) -> None:
        raw = copy.deepcopy(self.payload["fixture_projection"]["raw_rollout"])
        raw["rollout_id"] = "rollout-not-content-bound"
        raw = sign_record(raw)
        with self.assertRaisesRegex(ValueError, "rollout_id is not bound"):
            validate_raw_rollout_record(raw, self.payload["source_grasp_artifact_ref"])

    def test_fixture_keeps_action_variants_distinct_and_uninvented(self) -> None:
        fixture = self.payload["fixture_projection"]
        dictionaries = self.payload["provenance_dictionaries"]
        self.assertIn("recovery", dictionaries["control_modes"])
        self.assertNotIn("recovery", dictionaries["task_phases"])
        for frame in fixture["frames"]:
            self.assertEqual(
                set(frame["actions"]),
                {"requested", "proposed", "projected", "sent", "measured"},
            )
            self.assertTrue(all(action["state"] == "not_observed" for action in frame["actions"].values()))
            self.assertTrue(frame["strict_evaluator_result"]["valid"])
        self.assertEqual(
            [frame["task_phase"] for frame in fixture["frames"]],
            ["grasp_confirmed", "stable_hold"],
        )
        self.assertEqual(
            [frame["source_phase"] for frame in fixture["frames"]],
            ["grasp_hold", "unsupported_lift_hold"],
        )


if __name__ == "__main__":
    unittest.main()
