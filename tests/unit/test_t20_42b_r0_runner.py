from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.t20_42a_r0_generation_authority import (
    build_central_authority,
    build_owner_grant,
    build_permit,
    build_runtime_preflight,
    fixture_runtime_snapshot,
    load_verified_sources,
)
from scenesmith.robot_lab.t20_42b_r0_runner import (
    PROHIBITED_RESULT_FIELDS,
    build_statistics_artifact,
    build_store_manifest,
    candidate_sequence,
)


class T2042bR0RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_verified_sources()
        commit = "d" * 40
        owner = build_owner_grant(
            sources=cls.sources,
            required_source_commit=commit,
            valid_from="2026-07-16T12:35:56-05:00",
            valid_until="2026-07-16T20:35:56-05:00",
        )
        request, decision = build_central_authority(
            sources=cls.sources, owner_grant=owner
        )
        preflight = build_runtime_preflight(
            sources=cls.sources,
            owner_grant=owner,
            request=request,
            decision=decision,
            runtime_snapshot=fixture_runtime_snapshot(source_commit=commit),
        )
        cls.permit = build_permit(
            sources=cls.sources,
            owner_grant=owner,
            request=request,
            decision=decision,
            runtime_preflight=preflight,
        )
        cls.candidates = candidate_sequence(
            construction_spec=cls.sources["construction_spec"],
            permit=cls.permit,
        )

    def _outcomes(self, *, training_success_count: int) -> list[dict]:
        rows = []
        for index, candidate in enumerate(self.candidates):
            strict = index < training_success_count or index >= 119
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "split_role": candidate["split_role"],
                    "generation_spec": {
                        "seed": candidate["seed"],
                        "planar_offset_m": candidate["planar_offset_m"],
                        "yaw_offset_rad": candidate["yaw_offset_rad"],
                    },
                    "runtime_status": "completed",
                    "strict_success": strict,
                }
            )
        return rows

    def test_candidate_sequence_is_exact_ordered_disjoint_119_plus_9(self) -> None:
        self.assertEqual(len(self.candidates), 128)
        self.assertEqual(
            [row["candidate_id"] for row in self.candidates[:119]],
            self.permit["training_candidate_ids"],
        )
        self.assertEqual(
            [row["candidate_id"] for row in self.candidates[119:]],
            self.permit["fresh_held_out_candidate_ids"],
        )
        self.assertFalse(
            set(self.permit["training_candidate_ids"])
            & set(self.permit["fresh_held_out_candidate_ids"])
        )

    def test_candidate_sequence_rejects_duplicate_unknown_and_order_drift(self) -> None:
        for mutation in ("duplicate", "unknown", "order"):
            permit = copy.deepcopy(self.permit)
            if mutation == "duplicate":
                permit["training_candidate_ids"][1] = permit["training_candidate_ids"][
                    0
                ]
            elif mutation == "unknown":
                permit["fresh_held_out_candidate_ids"][0] = "f" * 64
            else:
                permit["training_candidate_ids"].reverse()
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    candidate_sequence(
                        construction_spec=self.sources["construction_spec"],
                        permit=permit,
                    )

    def test_store_manifest_admits_only_training_strict_successes(self) -> None:
        outcomes = self._outcomes(training_success_count=70)
        store = build_store_manifest(
            outcomes=outcomes,
            construction_spec=self.sources["construction_spec"],
            permit=self.permit,
        )
        self.assertEqual(store["new_training_strict_success_count"], 70)
        self.assertEqual(len(store["admitted_training_candidate_ids"]), 70)
        self.assertEqual(
            store["fresh_held_out_strict_success_candidate_ids"],
            self.permit["fresh_held_out_candidate_ids"],
        )
        self.assertEqual(store["fresh_held_out_training_rows"], 0)
        self.assertEqual(
            store["existing_held_out_seeds_referenced_without_regeneration"], [6, 7]
        )
        for field in PROHIBITED_RESULT_FIELDS:
            self.assertFalse(store[field])

    def test_store_manifest_preserves_insufficient_success_terminal_fact(self) -> None:
        store = build_store_manifest(
            outcomes=self._outcomes(training_success_count=63),
            construction_spec=self.sources["construction_spec"],
            permit=self.permit,
        )
        self.assertEqual(store["new_training_strict_success_count"], 63)
        self.assertEqual(len(store["admitted_training_candidate_ids"]), 63)
        self.assertFalse(store["retry_authorized"])

    def test_store_manifest_rejects_held_out_relabel_and_runtime_failure_pass(
        self,
    ) -> None:
        relabel = self._outcomes(training_success_count=70)
        relabel[119]["split_role"] = "training_candidate"
        with self.assertRaises(ValueError):
            build_store_manifest(
                outcomes=relabel,
                construction_spec=self.sources["construction_spec"],
                permit=self.permit,
            )
        failure = self._outcomes(training_success_count=70)
        failure[0]["runtime_status"] = "runtime_failure"
        failure[0]["error"] = "fixture"
        with self.assertRaises(ValueError):
            build_store_manifest(
                outcomes=failure,
                construction_spec=self.sources["construction_spec"],
                permit=self.permit,
            )

    def test_mean_std_artifact_is_training_only_finite_and_six_dimensional(
        self,
    ) -> None:
        stats = {
            "observation.state": {
                "mean": [0.0] * 6,
                "std": [1.0] * 6,
                "count": [18000],
            },
            "action": {
                "mean": [0.1] * 6,
                "std": [0.5] * 6,
                "count": [18000],
            },
        }
        artifact = build_statistics_artifact(
            dataset_stats=stats,
            dataset_manifest_ref={
                "path": "outputs/fixture.json",
                "schema_version": "fixture.v1",
                "identity_sha256": "a" * 64,
                "file_sha256": "b" * 64,
            },
            training_episode_count=80,
            training_frame_count=18000,
            excluded_candidate_ids=self.permit["fresh_held_out_candidate_ids"],
        )
        self.assertEqual(artifact["normalization"], "MEAN_STD")
        self.assertFalse(artifact["held_out_values_contributed_to_fit"])
        self.assertEqual(
            artifact["excluded_fresh_held_out_candidate_ids"],
            self.permit["fresh_held_out_candidate_ids"],
        )
        for field in PROHIBITED_RESULT_FIELDS:
            self.assertFalse(artifact[field])
        bad = copy.deepcopy(stats)
        bad["action"]["std"][0] = 0.0
        with self.assertRaises(ValueError):
            build_statistics_artifact(
                dataset_stats=bad,
                dataset_manifest_ref=artifact["dataset_manifest_ref"],
                training_episode_count=80,
                training_frame_count=18000,
                excluded_candidate_ids=self.permit["fresh_held_out_candidate_ids"],
            )


if __name__ == "__main__":
    unittest.main()
