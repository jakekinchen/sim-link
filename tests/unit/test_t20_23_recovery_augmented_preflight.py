from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest

from pathlib import Path

import numpy as np
from PIL import Image

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.so101_coordinates import mujoco_to_lerobot
from scenesmith.robot_lab.t20_23_recovery_augmented_preflight import (
    build_training_spec,
    recovery_dataset_frame,
    select_recovery_episodes,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_23_simulation_training_authority import (
    AUTHORIZED_ACTIONS,
    build_owner_training_grant,
    verify_owner_training_grant,
)


class T2023RecoveryAugmentedPreflightTests(unittest.TestCase):
    def test_selects_only_strict_recoveries_and_freezes_diagnostics(self) -> None:
        selected = select_recovery_episodes(self._package())
        self.assertEqual(len(selected["training"]), 4)
        self.assertEqual(sum(row["frame_count"] for row in selected["training"]), 866)
        self.assertEqual(len(selected["diagnostic"]), 4)
        self.assertEqual(sum(row["frame_count"] for row in selected["diagnostic"]), 424)
        self.assertEqual(
            {row["outcome_class"] for row in selected["training"]}, {"recovery"}
        )
        self.assertEqual(
            {row["outcome_class"] for row in selected["diagnostic"]},
            {"near_failure", "failure"},
        )

    def test_selection_rejects_duplicates_unknown_outcomes_and_count_drift(self) -> None:
        package = self._package()
        package["episodes"][1]["branch_id"] = package["episodes"][0]["branch_id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            select_recovery_episodes(package)
        package = self._package()
        package["episodes"][0]["outcome_class"] = "claimed_success"
        with self.assertRaisesRegex(ValueError, "outcome"):
            select_recovery_episodes(package)
        package = self._package()
        package["episodes"][0]["frame_count"] += 1
        package["episodes"][0]["image_count"] += 2
        with self.assertRaisesRegex(ValueError, "frame count"):
            select_recovery_episodes(package)

    def test_spec_binds_exact_membership_counts_and_false_execution(self) -> None:
        selected = select_recovery_episodes(self._package())
        spec = build_training_spec(
            nominal_episode_refs=[
                {
                    "seed": seed,
                    "frame_count": 244,
                    "raw_rollout_record_identity_sha256": f"{seed + 20:064x}",
                }
                for seed in range(6)
            ],
            recovery_episode_refs=selected["training"],
            diagnostic_episode_refs=selected["diagnostic"],
            held_out_episode_refs=[
                {
                    "seed": seed,
                    "frame_count": 244,
                    "relative_path": f"{seed:064x}.json",
                    "episode_file_sha256": f"{seed + 60:064x}",
                    "raw_rollout_record_identity_sha256": f"{seed + 70:064x}",
                    "included_in_training_dataset": False,
                    "included_in_dataset_statistics": False,
                }
                for seed in (6, 7)
            ],
            dataset_manifest_ref=self._ref("dataset", "1"),
            nominal_source_manifest_ref=self._ref("nominal", "2"),
            recovery_package_manifest_ref=self._ref("recovery", "3"),
            dataset_statistics={
                "source": "lerobot_dataset_meta_stats",
                "normalization": "QUANTILES",
                "identity_sha256": "4" * 64,
                "statistics_sha256": "5" * 64,
            },
            model_snapshot={
                "repo_id": "lerobot/pi05_base",
                "revision": "7de663972b7817d2c4cf2d84c821153dfea772e9",
                "files": [{"path": "model.safetensors", "sha256": "6" * 64}],
            },
        )
        verify_training_spec(spec)
        self.assertEqual(spec["dataset_contract"]["episode_count"], 10)
        self.assertEqual(spec["dataset_contract"]["frame_count"], 2330)
        self.assertEqual(spec["dataset_contract"]["source_frame_counts"], {
            "nominal_strict_success": 1464,
            "policy_visited_recovery": 866,
        })
        self.assertFalse(spec["optimizer_training"])
        self.assertFalse(spec["simulation_training_ready"])
        drift = copy.deepcopy(spec)
        drift["dataset_contract"]["frame_count"] = 2331
        with self.assertRaises(ValueError):
            verify_training_spec(sign_payload(drift))
        drift = copy.deepcopy(spec)
        drift["optimizer_training"] = True
        with self.assertRaisesRegex(ValueError, "execution|authority"):
            verify_training_spec(sign_payload(drift))
        drift = copy.deepcopy(spec)
        drift["held_out_episodes"][0]["included_in_dataset_statistics"] = True
        with self.assertRaisesRegex(ValueError, "held-out"):
            verify_training_spec(sign_payload(drift))

    def test_recovery_frame_requires_bound_images_and_measured_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            images = {}
            for index, role in enumerate(("top", "wrist")):
                path = root / f"{role}.png"
                Image.fromarray(
                    np.full((256, 256, 3), 20 + index, dtype=np.uint8), mode="RGB"
                ).save(path)
                images[role] = {
                    "path": path.relative_to(root).as_posix(),
                    "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "width": 256,
                    "height": 256,
                    "channels": 3,
                }
            qpos = [0.01, -0.02, 0.03, -0.04, 0.05, 0.6]
            measured_radians = [0.02, -0.03, 0.04, -0.05, 0.06, 0.7]
            state = [round(value, 6) for value in mujoco_to_lerobot(qpos)]
            action = [round(value, 6) for value in mujoco_to_lerobot(measured_radians)]
            frame = {
                "state": state,
                "action": action,
                "mujoco_qpos": qpos,
                "actor_observation_images": images,
            }
            episode = {
                "outcome_class": "recovery",
                "actions_padded": False,
                "actions_inferred": False,
                "measured_actions": [measured_radians],
                "frames": [frame],
            }
            result = recovery_dataset_frame(root, episode, frame, frame_index=0)
            self.assertEqual(result["observation.state"].dtype, np.float32)
            np.testing.assert_allclose(result["action"], mujoco_to_lerobot(measured_radians))
            self.assertEqual(result["observation.images.base_0_rgb"].shape, (256, 256, 3))
            bad = copy.deepcopy(frame)
            bad["actor_observation_images"]["top"]["file_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "image hash"):
                recovery_dataset_frame(root, episode, bad, frame_index=0)
            bad = copy.deepcopy(frame)
            bad["action"][0] = 9.0
            with self.assertRaisesRegex(ValueError, "measured action"):
                recovery_dataset_frame(root, episode, bad, frame_index=0)
            bad = copy.deepcopy(frame)
            bad["state"][0] = 9.0
            with self.assertRaisesRegex(ValueError, "rendered state"):
                recovery_dataset_frame(root, episode, bad, frame_index=0)
            bad = copy.deepcopy(frame)
            bad["mujoco_qpos"][0] = float("nan")
            with self.assertRaisesRegex(ValueError, "non-finite"):
                recovery_dataset_frame(root, episode, bad, frame_index=0)

    def test_owner_grant_is_spec_bound_and_simulation_only(self) -> None:
        spec = {"schema_version": "example.v1", "identity_sha256": "a" * 64}
        grant = build_owner_training_grant(training_spec=spec)
        verify_owner_training_grant(grant, training_spec=spec)
        self.assertEqual(grant["authorized_actions"], list(AUTHORIZED_ACTIONS))
        self.assertTrue(grant["simulation_only"])
        self.assertFalse(grant["physical_transfer_authorized"])
        self.assertFalse(grant["promotion_authorized"])
        drift = copy.deepcopy(grant)
        drift["authorized_actions"].append("physical_actuation")
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_owner_training_grant(sign_payload(drift), training_spec=spec)

    @staticmethod
    def _ref(name: str, digit: str) -> dict:
        return {
            "path": f"configurations/robot_lab/{name}.json",
            "schema_version": f"scenesmith.{name}.v1",
            "identity_sha256": digit * 64,
            "file_sha256": str((int(digit) + 6) % 10) * 64,
        }

    @staticmethod
    def _package() -> dict:
        outcomes = [
            ("recovery", 238),
            ("recovery", 238),
            ("recovery", 195),
            ("recovery", 195),
            ("near_failure", 173),
            ("near_failure", 173),
            ("failure", 39),
            ("failure", 39),
        ]
        episodes = [
            {
                "branch_id": f"{index + 1:064x}",
                "identity_sha256": f"{index + 20:064x}",
                "file_sha256": f"{index + 40:064x}",
                "path": f"outputs/episode-{index}.json",
                "outcome_class": outcome,
                "frame_count": frames,
                "image_count": frames * 2,
            }
            for index, (outcome, frames) in enumerate(outcomes)
        ]
        return {
            "schema_version": "scenesmith.t20_18_recovery_episode_package.v1",
            "identity_sha256": "f" * 64,
            "episodes": episodes,
            "episode_count": 8,
            "frame_count": 1290,
            "image_count": 2580,
            "outcome_class_counts": {
                "failure": 2,
                "near_failure": 2,
                "recovery": 4,
            },
            "actions_padded": False,
            "actions_inferred": False,
            "recovery_training_candidate": True,
        }


if __name__ == "__main__":
    unittest.main()
