from __future__ import annotations

import copy
import hashlib
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_42_r0_dataset_construction import (
    ADMISSION_FIXTURE_PATH,
    CONSTRUCTION_SPEC_PATH,
    build_admission_fixture,
    build_construction_spec,
    build_preflight,
    load_source_snapshot,
    verify_admission_fixture,
    verify_artifacts,
    verify_construction_spec,
    verify_preflight,
    write_artifacts,
)


class T2042R0DatasetConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_source_snapshot()
        cls.spec = build_construction_spec(source_snapshot=cls.sources)
        cls.fixture = build_admission_fixture(construction_spec=cls.spec)
        cls.spec_ref = cls._ref(CONSTRUCTION_SPEC_PATH, cls.spec)
        cls.fixture_ref = cls._ref(ADMISSION_FIXTURE_PATH, cls.fixture)
        cls.preflight = build_preflight(
            construction_spec_ref=cls.spec_ref,
            admission_fixture_ref=cls.fixture_ref,
        )

    def test_exact_route_sources_and_candidate_split_are_frozen(self) -> None:
        verify_construction_spec(self.spec, source_snapshot=self.sources)
        construction = self.spec["construction"]
        self.assertEqual(construction["training_candidate_count"], 119)
        self.assertEqual(len(construction["training_candidates"]), 119)
        self.assertEqual(construction["fresh_held_out_candidate_count"], 9)
        self.assertEqual(len(construction["fresh_held_out_candidates"]), 9)
        self.assertEqual(
            construction["required_new_nominal_successes"],
            {"minimum": 64, "maximum": 119, "owner_ceiling": 128},
        )
        self.assertEqual(construction["optional_new_recovery_count"], 0)
        self.assertEqual(
            [row["seed"] for row in self.spec["existing_held_out_episodes"]],
            [6, 7],
        )
        self.assertEqual(len(self.spec["verified_base_membership"]), 10)
        self.assertEqual(
            [row["source_class"] for row in self.spec["verified_base_membership"]],
            ["nominal_strict_success"] * 6 + ["policy_visited_recovery"] * 4,
        )
        for row in construction["training_candidates"]:
            self.assertEqual(row["initial_joint_delta_rad"], [0.0] * 6)
            self.assertEqual(row["split_role"], "training_candidate")
            self.assertFalse(row["physics_parameter_randomization"])
        for row in construction["fresh_held_out_candidates"]:
            self.assertEqual(row["initial_joint_delta_rad"], [0.0] * 6)
            self.assertEqual(row["split_role"], "evaluation_only_fresh_pose_band")
            self.assertFalse(row["physics_parameter_randomization"])

    def test_candidate_order_is_deterministic_unique_and_disjoint(self) -> None:
        rebuilt = build_construction_spec(source_snapshot=self.sources)
        self.assertEqual(canonical_json_bytes(rebuilt), canonical_json_bytes(self.spec))
        construction = self.spec["construction"]
        training = construction["training_candidates"]
        fresh = construction["fresh_held_out_candidates"]
        self.assertEqual(
            [row["candidate_id"] for row in training],
            sorted(row["candidate_id"] for row in training),
        )
        self.assertEqual(len({row["candidate_id"] for row in training}), len(training))
        self.assertEqual(len({row["seed"] for row in training}), len(training))
        self.assertFalse(
            {self._pose_key(row) for row in training}
            & {self._pose_key(row) for row in fresh}
        )
        historical = {
            (
                round(spec["planar_offset_m"][0], 9),
                round(spec["planar_offset_m"][1], 9),
                round(spec["yaw_offset_rad"], 9),
            )
            for spec in self.sources["t17_manifest"]["episode_specs"]
        }
        self.assertFalse({self._pose_key(row) for row in training} & historical)

    def test_semantic_drift_and_authority_escalation_fail_closed(self) -> None:
        duplicate = copy.deepcopy(self.spec)
        duplicate["construction"]["training_candidates"][1]["candidate_id"] = duplicate[
            "construction"
        ]["training_candidates"][0]["candidate_id"]
        with self.assertRaises(ValueError):
            verify_construction_spec(
                sign_payload(duplicate), source_snapshot=self.sources
            )

        out_of_range = copy.deepcopy(self.spec)
        out_of_range["construction"]["training_candidates"][0]["planar_offset_m"][0] = (
            0.002
        )
        with self.assertRaises(ValueError):
            verify_construction_spec(
                sign_payload(out_of_range), source_snapshot=self.sources
            )

        physics = copy.deepcopy(self.spec)
        physics["construction"]["training_candidates"][0][
            "physics_parameter_randomization"
        ] = True
        with self.assertRaises(ValueError):
            verify_construction_spec(
                sign_payload(physics), source_snapshot=self.sources
            )

        execution = copy.deepcopy(self.spec)
        execution["execution_state"]["r0_episode_generation_executed"] = True
        with self.assertRaises(ValueError):
            verify_construction_spec(
                sign_payload(execution), source_snapshot=self.sources
            )

    def test_source_identity_drift_fails_before_spec_acceptance(self) -> None:
        drift = copy.deepcopy(self.sources)
        drift["route_decision_file_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build_construction_spec(source_snapshot=drift)
        drift = copy.deepcopy(self.sources)
        drift["t20_23_training_spec"]["identity_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build_construction_spec(source_snapshot=drift)

    def test_fixture_admits_exact_base_plus_64_and_statistics_only_training(
        self,
    ) -> None:
        verify_admission_fixture(self.fixture, construction_spec=self.spec)
        membership = self.fixture["training_membership"]
        self.assertEqual(len(membership["verified_base_episodes"]), 10)
        self.assertEqual(len(membership["new_nominal_successes"]), 64)
        self.assertEqual(len(membership["optional_new_recoveries"]), 0)
        self.assertEqual(self.fixture["counts"]["training_episode_count"], 74)
        expected_statistics = [
            *[row["membership_id"] for row in membership["verified_base_episodes"]],
            *[row["candidate_id"] for row in membership["new_nominal_successes"]],
        ]
        self.assertEqual(
            self.fixture["statistics_contract"]["training_episode_ids"],
            expected_statistics,
        )
        self.assertEqual(
            self.fixture["statistics_contract"]["normalization"], "MEAN_STD"
        )
        self.assertFalse(self.fixture["r0_dataset_materialized"])

    def test_fixture_rejects_base_omission_failure_and_held_out_leakage(self) -> None:
        omitted = copy.deepcopy(self.fixture)
        omitted["training_membership"]["verified_base_episodes"].pop()
        with self.assertRaises(ValueError):
            verify_admission_fixture(sign_payload(omitted), construction_spec=self.spec)

        failed = copy.deepcopy(self.fixture)
        failed_id = failed["excluded_evidence"]["failed_candidate_ids"][0]
        failed["statistics_contract"]["training_episode_ids"].append(failed_id)
        with self.assertRaises(ValueError):
            verify_admission_fixture(sign_payload(failed), construction_spec=self.spec)

        held_out = copy.deepcopy(self.fixture)
        held_out_id = held_out["excluded_evidence"]["fresh_held_out_candidate_ids"][0]
        held_out["statistics_contract"]["training_episode_ids"].append(held_out_id)
        with self.assertRaises(ValueError):
            verify_admission_fixture(
                sign_payload(held_out), construction_spec=self.spec
            )

    def test_preflight_binds_artifacts_and_withholds_generation(self) -> None:
        verify_preflight(
            self.preflight,
            construction_spec_ref=self.spec_ref,
            admission_fixture_ref=self.fixture_ref,
        )
        self.assertEqual(
            self.preflight["required_before_generation"],
            [
                "implementation_committed_and_origin_confirmed",
                "same_agent_adversarial_review_accepted",
                "fresh_central_generation_decision_granted",
                "fresh_runtime_preflight_valid",
                "one_use_generation_permit_valid",
            ],
        )
        for field in (
            "r0_episode_generation_executed",
            "dataset_materialized",
            "model_loaded",
            "model_inference",
            "optimizer_created",
            "optimizer_training",
            "learned_policy_rollout",
            "hardware_accessed",
            "network_accessed",
            "external_compute_started",
            "brev_compute_started",
            "r1_activated",
        ):
            self.assertFalse(self.preflight[field])

    def test_tracked_product_path_verifies_and_refuses_overwrite(self) -> None:
        result = verify_artifacts()
        self.assertEqual(
            result["construction_spec"]["identity_sha256"],
            self.spec["identity_sha256"],
        )
        self.assertFalse(result["preflight"]["generation_ready"])
        with self.assertRaises(FileExistsError):
            write_artifacts()

    @staticmethod
    def _pose_key(row: dict) -> tuple[float, float, float]:
        return (
            round(row["planar_offset_m"][0], 9),
            round(row["planar_offset_m"][1], 9),
            round(row["yaw_offset_rad"], 9),
        )

    @staticmethod
    def _ref(path: Path, payload: dict) -> dict:
        return {
            "path": str(path),
            "schema_version": payload["schema_version"],
            "identity_sha256": payload["identity_sha256"],
            "file_sha256": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
        }


if __name__ == "__main__":
    unittest.main()
