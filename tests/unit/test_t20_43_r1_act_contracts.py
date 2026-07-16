import copy
import unittest

from scenesmith.robot_lab.t20_43_r1_act_contracts import (
    CHECKPOINT_SCHEDULE,
    OUTPUT_PATHS,
    SAMPLE_INDICES,
    build_attempt_marker,
    build_central_authority,
    build_gate_a,
    build_owner_grant,
    build_permit,
    build_runtime_preflight,
    build_spec,
    load_verified_sources,
    verify_attempt_marker,
    verify_gate_a,
    verify_owner_grant,
    verify_permit,
    verify_spec,
)


class T2043R1ACTContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_verified_sources()
        cls.spec = build_spec(sources=cls.sources)

    def test_exact_spec_binds_full_standard_recipe(self) -> None:
        verify_spec(self.spec, sources=self.sources)
        self.assertEqual(self.spec["campaign"]["maximum_optimizer_updates"], 10000)
        self.assertEqual(self.spec["campaign"]["batch_size"], 8)
        self.assertEqual(
            self.spec["campaign"]["checkpoint_schedule"],
            list(CHECKPOINT_SCHEDULE),
        )
        self.assertEqual(self.spec["act_config"]["dim_model"], 512)
        self.assertTrue(self.spec["act_config"]["use_vae"])
        self.assertEqual(
            [row["n_action_steps"] for row in self.spec["evaluation"]["variants"]],
            [50, 10],
        )

    def test_spec_rejects_tiny_act_or_retry(self) -> None:
        for path, value in (
            (("act_config", "dim_model"), 64),
            (("campaign", "retry_or_sweep_allowed"), True),
            (("campaign", "maximum_optimizer_updates"), 2000),
        ):
            mutated = copy.deepcopy(self.spec)
            mutated[path[0]][path[1]] = value
            with self.assertRaises(ValueError):
                verify_spec(mutated, sources=self.sources)

    def test_gate_a_rejects_held_out_leakage_and_inverse_error(self) -> None:
        evidence = self._gate_a_evidence()
        gate = build_gate_a(spec=self.spec, evidence=evidence)
        verify_gate_a(gate, spec=self.spec)
        for key, value in (
            ("fresh_held_out_training_rows", 1),
            ("maximum_postprocessor_inverse_error", 1e-3),
            ("sample_indices", list(SAMPLE_INDICES[:-1])),
        ):
            mutated = copy.deepcopy(evidence)
            mutated[key] = value
            with self.assertRaises(ValueError):
                build_gate_a(spec=self.spec, evidence=mutated)

    def test_authority_permit_and_marker_are_one_use_and_fail_closed(self) -> None:
        gate = build_gate_a(spec=self.spec, evidence=self._gate_a_evidence())
        owner = build_owner_grant(
            spec=self.spec,
            required_source_commit="a" * 40,
            valid_from="2026-07-16T12:35:56-05:00",
            valid_until="2026-07-16T20:35:56-05:00",
        )
        verify_owner_grant(owner, spec=self.spec)
        request, decision = build_central_authority(
            sources=self.sources,
            spec=self.spec,
            gate_a=gate,
            owner_grant=owner,
        )
        runtime = build_runtime_preflight(
            spec=self.spec,
            gate_a=gate,
            owner_grant=owner,
            request=request,
            decision=decision,
            runtime_snapshot=self._runtime_snapshot(),
        )
        permit = build_permit(
            spec=self.spec,
            gate_a=gate,
            owner_grant=owner,
            request=request,
            decision=decision,
            runtime_preflight=runtime,
        )
        verify_permit(
            permit,
            spec=self.spec,
            gate_a=gate,
            owner_grant=owner,
            request=request,
            decision=decision,
            runtime_preflight=runtime,
        )
        self.assertFalse(permit["retry_or_sweep_authorized"])
        marker = build_attempt_marker(
            permit=permit,
            source_commit="b" * 40,
            started_at="2026-07-16T15:00:00-05:00",
        )
        verify_attempt_marker(marker, permit=permit)
        self.assertTrue(marker["created_before_model_construction"])
        self.assertTrue(marker["permit_consumed"])

    def test_runtime_snapshot_rejects_output_collision(self) -> None:
        gate = build_gate_a(spec=self.spec, evidence=self._gate_a_evidence())
        owner = build_owner_grant(
            spec=self.spec,
            required_source_commit="a" * 40,
            valid_from="2026-07-16T12:35:56-05:00",
            valid_until="2026-07-16T20:35:56-05:00",
        )
        request, decision = build_central_authority(
            sources=self.sources,
            spec=self.spec,
            gate_a=gate,
            owner_grant=owner,
        )
        runtime = self._runtime_snapshot()
        runtime["output_path_state"][OUTPUT_PATHS[0].as_posix()]["exists"] = True
        with self.assertRaises(ValueError):
            build_runtime_preflight(
                spec=self.spec,
                gate_a=gate,
                owner_grant=owner,
                request=request,
                decision=decision,
                runtime_snapshot=runtime,
            )

    @staticmethod
    def _gate_a_evidence() -> dict:
        return {
            "dataset_episode_count": 129,
            "dataset_frame_count": 31366,
            "sample_indices": list(SAMPLE_INDICES),
            "sample_count": len(SAMPLE_INDICES),
            "action_shape": [50, 6],
            "state_shape": [6],
            "image_shapes": {
                "observation.images.base_0_rgb": [3, 256, 256],
                "observation.images.left_wrist_0_rgb": [3, 256, 256],
            },
            "fresh_held_out_training_rows": 0,
            "existing_held_out_training_rows": 0,
            "all_values_finite": True,
            "dataset_stats_match_compact_statistics": True,
            "processor_matches_manual_mean_std": True,
            "postprocessor_inverse_matches_actions": True,
            "coordinate_round_trip_passed": True,
            "maximum_processor_manual_error": 0.0,
            "maximum_postprocessor_inverse_error": 3e-6,
            "maximum_coordinate_round_trip_error_rad": 1e-14,
            "dataset_tree_identity_sha256": "1" * 64,
            "dataset_manifest_identity_sha256": "2" * 64,
            "dataset_info_file_sha256": "3" * 64,
            "dataset_stats_file_sha256": "4" * 64,
            "sample_tensor_identity_sha256": "5" * 64,
            "normalized_tensor_identity_sha256": "6" * 64,
            "postprocessed_action_identity_sha256": "7" * 64,
        }

    @staticmethod
    def _runtime_snapshot() -> dict:
        return {
            "source_commit": "a" * 40,
            "branch": "codex/pi05-autolearn-loop",
            "origin_contains_source_commit": True,
            "scoped_dirty_paths": [],
            "dependencies": {
                "python": "3.12.12",
                "torch": "2.11.0",
                "torchvision": "0.26.0",
                "datasets": "4.8.5",
                "mujoco": "3.3.5",
                "numpy": "2.2.6",
                "pillow": "12.3.0",
                "pyarrow": "25.0.0",
                "lerobot": "0.6.1",
            },
            "mps_available": True,
            "free_disk_bytes": 20 * 1024**3,
            "network_enabled": False,
            "dependency_fallback_enabled": False,
            "cached_backbone_file_sha256": (
                "f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec"
            ),
            "cached_backbone_size_bytes": 46830571,
            "output_path_state": {
                path.as_posix(): {"exists": False, "is_symlink": False}
                for path in OUTPUT_PATHS
            },
            "authority_artifacts_materialized": False,
            "attempt_marker_exists": False,
        }


if __name__ == "__main__":
    unittest.main()
