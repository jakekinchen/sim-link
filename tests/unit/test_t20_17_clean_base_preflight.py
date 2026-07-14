from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.t20_17_clean_base_preflight import (
    CAMERAS,
    HELD_OUT_SEEDS,
    JOINT_NAMES,
    TRAINING_SEEDS,
    build_training_spec,
    select_source_episodes,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_17_simulation_training_authority import (
    AUTHORIZED_ACTIONS,
    build_owner_training_grant,
    verify_owner_training_grant,
)


class T2017CleanBasePreflightTests(unittest.TestCase):
    def test_fixed_split_and_source_native_features(self) -> None:
        manifest = {
            "episodes": [
                {
                    "seed": seed,
                    "frame_count": 244,
                    "episode_file_sha256": f"{seed + 1:064x}",
                    "raw_rollout_record_identity_sha256": f"{seed + 9:064x}",
                    "relative_path": f"{seed + 1:064x}.json",
                    "outcome": {"strict_success": True},
                }
                for seed in range(8)
            ]
        }
        selected = select_source_episodes(manifest)
        self.assertEqual([row["seed"] for row in selected["training"]], list(TRAINING_SEEDS))
        self.assertEqual([row["seed"] for row in selected["held_out"]], list(HELD_OUT_SEEDS))
        self.assertEqual(sum(row["frame_count"] for row in selected["training"]), 1464)
        self.assertEqual(CAMERAS, ("top", "wrist"))
        self.assertEqual(len(JOINT_NAMES), 6)

    def test_split_rejects_non_strict_or_duplicate_source(self) -> None:
        manifest = {
            "episodes": [
                {
                    "seed": seed,
                    "frame_count": 244,
                    "episode_file_sha256": f"{seed + 1:064x}",
                    "raw_rollout_record_identity_sha256": f"{seed + 9:064x}",
                    "relative_path": f"{seed + 1:064x}.json",
                    "outcome": {"strict_success": seed != 4},
                }
                for seed in range(8)
            ]
        }
        with self.assertRaisesRegex(ValueError, "strict-success"):
            select_source_episodes(manifest)
        manifest["episodes"][4]["outcome"]["strict_success"] = True
        manifest["episodes"][7]["seed"] = 6
        with self.assertRaisesRegex(ValueError, "duplicate"):
            select_source_episodes(manifest)

    def test_training_spec_fails_closed_on_campaign_or_stats_drift(self) -> None:
        manifest_ref = {
            "path": "configurations/robot_lab/t20_17_lerobot_dataset_manifest.json",
            "schema_version": "scenesmith.lerobot_native_episode_manifest.v1",
            "identity_sha256": "1" * 64,
            "file_sha256": "2" * 64,
        }
        source_ref = {
            "path": "configurations/robot_lab/t17_5b_episode_generation_manifest.json",
            "schema_version": "scenesmith.scripted_grasp_episode_store.v1",
            "identity_sha256": "3" * 64,
            "file_sha256": "4" * 64,
        }
        snapshot = {
            "repo_id": "lerobot/pi05_base",
            "revision": "7de663972b7817d2c4cf2d84c821153dfea772e9",
            "files": [{"path": "model.safetensors", "size_bytes": 14467165872, "sha256": "5" * 64}],
        }
        stats = {"identity_sha256": "6" * 64, "normalization": "QUANTILES"}
        spec = build_training_spec(
            dataset_manifest_ref=manifest_ref,
            source_manifest_ref=source_ref,
            model_snapshot=snapshot,
            dataset_statistics=stats,
            held_out_episodes=[{"seed": 6}, {"seed": 7}],
        )
        verify_training_spec(spec)
        for field, value in (("optimizer_update_count", 251), ("training_seed", 1)):
            drift = copy.deepcopy(spec)
            drift["campaign"][field] = value
            with self.assertRaises(ValueError):
                verify_training_spec(drift)
        drift = copy.deepcopy(spec)
        drift["dataset_statistics"]["normalization"] = "MEAN_STD"
        with self.assertRaises(ValueError):
            verify_training_spec(drift)

    def test_owner_grant_is_simulation_only_and_spec_bound(self) -> None:
        spec = {"schema_version": "example.v1", "identity_sha256": "a" * 64}
        grant = build_owner_training_grant(training_spec=spec)
        verify_owner_training_grant(grant, training_spec=spec)
        self.assertEqual(grant["authorized_actions"], list(AUTHORIZED_ACTIONS))
        self.assertTrue(grant["simulation_only"])
        self.assertFalse(grant["physical_transfer_authorized"])
        self.assertFalse(grant["promotion_authorized"])
        drift = copy.deepcopy(grant)
        drift["authorized_actions"].append("physical_actuation")
        with self.assertRaises(ValueError):
            verify_owner_training_grant(drift, training_spec=spec)


if __name__ == "__main__":
    unittest.main()
