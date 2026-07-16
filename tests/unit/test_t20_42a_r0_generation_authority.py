from __future__ import annotations

import copy
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_42a_r0_generation_authority import (
    ATTEMPT_PATH,
    AUTHORIZED_ACTIONS,
    MINIMUM_FREE_DISK_BYTES,
    build_attempt_marker,
    build_central_authority,
    build_owner_grant,
    build_permit,
    build_runtime_preflight,
    fixture_runtime_snapshot,
    load_verified_sources,
    verify_attempt_marker,
    verify_owner_grant,
    verify_permit,
    verify_runtime_preflight,
    write_attempt_marker,
)


class T2042aR0GenerationAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_verified_sources()
        cls.source_commit = "a" * 40
        cls.valid_from = "2026-07-16T10:30:00-05:00"
        cls.valid_until = "2026-07-16T18:30:00-05:00"
        cls.owner = build_owner_grant(
            sources=cls.sources,
            required_source_commit=cls.source_commit,
            valid_from=cls.valid_from,
            valid_until=cls.valid_until,
        )
        cls.request, cls.decision = build_central_authority(
            sources=cls.sources, owner_grant=cls.owner
        )
        cls.runtime = fixture_runtime_snapshot(source_commit=cls.source_commit)
        cls.preflight = build_runtime_preflight(
            sources=cls.sources,
            owner_grant=cls.owner,
            request=cls.request,
            decision=cls.decision,
            runtime_snapshot=cls.runtime,
        )
        cls.permit = build_permit(
            sources=cls.sources,
            owner_grant=cls.owner,
            request=cls.request,
            decision=cls.decision,
            runtime_preflight=cls.preflight,
        )

    def test_sources_bind_exact_reviewed_construction_boundary(self) -> None:
        self.assertEqual(
            self.sources["construction_spec"]["identity_sha256"],
            "b58a6b31d0a3d892cfce8e319c4736d2da9aab2864663a5b2fc89c752e221458",
        )
        self.assertEqual(
            self.sources["admission_fixture"]["identity_sha256"],
            "b7b1eb7746cf3736a12ae7f0fa3e7bffdf58a92cf702d8d7648366e7350553ba",
        )
        self.assertEqual(
            self.sources["construction_preflight"]["identity_sha256"],
            "5ff8c5cca2abfe3ceb2b15296fb065c66ff416b98888eb3dba0a1a9074136250",
        )

    def test_owner_grant_is_one_fixed_manifest_and_simulation_only(self) -> None:
        verify_owner_grant(self.owner, sources=self.sources)
        self.assertEqual(self.owner["authorized_actions"], list(AUTHORIZED_ACTIONS))
        self.assertEqual(self.owner["authorized_attempt_count"], 1)
        self.assertEqual(self.owner["training_candidate_count"], 119)
        self.assertEqual(self.owner["fresh_held_out_candidate_count"], 9)
        self.assertEqual(self.owner["existing_held_out_seeds"], [6, 7])
        self.assertFalse(self.owner["retry_authorized"])
        self.assertFalse(self.owner["network_access_authorized"])
        self.assertFalse(self.owner["model_or_optimizer_authorized"])
        self.assertFalse(self.owner["hardware_authorized"])
        drifted_sources = copy.deepcopy(self.sources)
        drifted_sources["construction_spec_ref"]["file_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build_owner_grant(
                sources=drifted_sources,
                required_source_commit=self.source_commit,
                valid_from=self.valid_from,
                valid_until=self.valid_until,
            )
        with self.assertRaises(ValueError):
            build_owner_grant(
                sources=self.sources,
                required_source_commit=self.source_commit,
                valid_from=self.valid_from,
                valid_until="2026-07-16T18:30:01-05:00",
            )

    def test_central_composer_grants_only_simulation_training_readiness(self) -> None:
        self.assertEqual(
            self.decision["authority_granted"], ["simulation_training_ready"]
        )
        self.assertEqual(
            self.decision["request_identity_sha256"], self.request["identity_sha256"]
        )
        self.assertNotIn("physical_transfer_ready", self.decision["authority_granted"])
        self.assertNotIn("promotion_eligible", self.decision["authority_granted"])

    def test_runtime_preflight_binds_commit_dependencies_disk_and_absent_outputs(
        self,
    ) -> None:
        verify_runtime_preflight(
            self.preflight,
            sources=self.sources,
            owner_grant=self.owner,
            request=self.request,
            decision=self.decision,
            runtime_snapshot=self.runtime,
        )
        self.assertEqual(self.preflight["source_commit"], self.source_commit)
        self.assertGreaterEqual(
            self.preflight["free_disk_bytes"], MINIMUM_FREE_DISK_BYTES
        )
        self.assertTrue(self.preflight["all_output_paths_absent"])
        self.assertFalse(self.preflight["authority_artifacts_materialized"])
        self.assertFalse(self.preflight["attempt_marker_exists"])
        self.assertFalse(self.preflight["r0_episode_generation_executed"])

    def test_runtime_drift_fails_closed(self) -> None:
        mutations = []
        wrong_commit = copy.deepcopy(self.runtime)
        wrong_commit["source_commit"] = "b" * 40
        mutations.append(wrong_commit)
        wrong_branch = copy.deepcopy(self.runtime)
        wrong_branch["branch"] = "main"
        mutations.append(wrong_branch)
        not_origin = copy.deepcopy(self.runtime)
        not_origin["origin_contains_source_commit"] = False
        mutations.append(not_origin)
        dirty = copy.deepcopy(self.runtime)
        dirty["scoped_dirty_paths"] = ["scenesmith/robot_lab/t20_42.py"]
        mutations.append(dirty)
        network = copy.deepcopy(self.runtime)
        network["network_enabled"] = True
        mutations.append(network)
        fallback = copy.deepcopy(self.runtime)
        fallback["dependency_fallback_enabled"] = True
        mutations.append(fallback)
        low_disk = copy.deepcopy(self.runtime)
        low_disk["free_disk_bytes"] = MINIMUM_FREE_DISK_BYTES - 1
        mutations.append(low_disk)
        present = copy.deepcopy(self.runtime)
        first_path = next(iter(present["output_path_state"]))
        present["output_path_state"][first_path]["exists"] = True
        mutations.append(present)
        aliased = copy.deepcopy(self.runtime)
        first_path = next(iter(aliased["output_path_state"]))
        aliased["output_path_state"][first_path]["is_symlink"] = True
        mutations.append(aliased)
        missing_dependency = copy.deepcopy(self.runtime)
        missing_dependency["dependencies"].pop("mujoco")
        mutations.append(missing_dependency)
        non_finite = copy.deepcopy(self.runtime)
        non_finite["free_disk_bytes"] = float("nan")
        mutations.append(non_finite)
        for runtime in mutations:
            with self.subTest(runtime=runtime):
                with self.assertRaises(ValueError):
                    build_runtime_preflight(
                        sources=self.sources,
                        owner_grant=self.owner,
                        request=self.request,
                        decision=self.decision,
                        runtime_snapshot=runtime,
                    )

    def test_permit_binds_exact_ids_order_outputs_and_no_retry(self) -> None:
        verify_permit(
            self.permit,
            sources=self.sources,
            owner_grant=self.owner,
            request=self.request,
            decision=self.decision,
            runtime_preflight=self.preflight,
        )
        expected_training = self.sources["construction_spec"]["generation_plan"][
            "training_candidate_ids"
        ]
        expected_fresh = self.sources["construction_spec"]["generation_plan"][
            "fresh_held_out_candidate_ids"
        ]
        self.assertEqual(self.permit["training_candidate_ids"], expected_training)
        self.assertEqual(self.permit["fresh_held_out_candidate_ids"], expected_fresh)
        self.assertEqual(self.permit["attempt_marker_path"], str(ATTEMPT_PATH))
        self.assertEqual(self.permit["authorized_attempt_count"], 1)
        self.assertFalse(self.permit["retry_authorized"])
        self.assertFalse(self.permit["adaptive_manifest_extension_authorized"])

    def test_permit_rejects_duplicate_unknown_and_seed_regeneration(self) -> None:
        duplicate = copy.deepcopy(self.permit)
        duplicate["training_candidate_ids"][1] = duplicate["training_candidate_ids"][0]
        with self.assertRaises(ValueError):
            verify_permit(
                sign_payload(duplicate),
                sources=self.sources,
                owner_grant=self.owner,
                request=self.request,
                decision=self.decision,
                runtime_preflight=self.preflight,
            )
        unknown = copy.deepcopy(self.permit)
        unknown["fresh_held_out_candidate_ids"][0] = "f" * 64
        with self.assertRaises(ValueError):
            verify_permit(
                sign_payload(unknown),
                sources=self.sources,
                owner_grant=self.owner,
                request=self.request,
                decision=self.decision,
                runtime_preflight=self.preflight,
            )
        regenerate = copy.deepcopy(self.permit)
        regenerate["existing_held_out_seeds_referenced_without_regeneration"] = []
        with self.assertRaises(ValueError):
            verify_permit(
                sign_payload(regenerate),
                sources=self.sources,
                owner_grant=self.owner,
                request=self.request,
                decision=self.decision,
                runtime_preflight=self.preflight,
            )

    def test_marker_is_deterministic_consumes_once_and_rejects_drift(self) -> None:
        marker = build_attempt_marker(
            permit=self.permit,
            source_commit=self.source_commit,
            started_at="2026-07-16T10:45:00-05:00",
        )
        verify_attempt_marker(marker, permit=self.permit)
        drift = copy.deepcopy(marker)
        drift["source_commit"] = "b" * 40
        with self.assertRaises(ValueError):
            verify_attempt_marker(sign_payload(drift), permit=self.permit)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            written = write_attempt_marker(marker, permit=self.permit, repo_root=root)
            self.assertEqual(written, root / ATTEMPT_PATH)
            with self.assertRaises(FileExistsError):
                write_attempt_marker(marker, permit=self.permit, repo_root=root)

    def test_all_prohibited_authority_fields_remain_false(self) -> None:
        for payload in (self.owner, self.preflight, self.permit):
            for field in (
                "network_access_authorized",
                "model_or_optimizer_authorized",
                "hardware_authorized",
                "external_compute_authorized",
                "brev_compute_authorized",
                "physical_transfer_authorized",
                "promotion_authorized",
                "r1_authorized",
            ):
                self.assertFalse(payload[field])


if __name__ == "__main__":
    unittest.main()
