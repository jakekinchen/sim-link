from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_33_one_batch_memorization import (
    INFERENCE_SEEDS,
    OPTIMIZER_UPDATES,
    build_result,
    build_training_spec,
    verify_result,
    verify_run,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_33_simulation_training_authority import (
    AUTHORIZED_ACTIONS,
    build_owner_grant,
    verify_owner_grant,
)


class T2033OneBatchMemorizationTests(unittest.TestCase):
    def test_spec_freezes_one_batch_campaign_gate_and_authority(self) -> None:
        spec = self._spec()
        verify_training_spec(spec)
        self.assertEqual(spec["source_batch"]["frame_index"], 0)
        self.assertEqual(spec["source_batch"]["action_horizon"], 50)
        self.assertEqual(spec["campaign"]["optimizer_update_count"], 500)
        self.assertFalse(spec["optimizer_training"])
        for mutation in (
            lambda value: value["source_batch"].update(frame_index=1),
            lambda value: value["campaign"].update(optimizer_update_count=501),
            lambda value: value["gate"].update(maximum_decoded_action_error_rad=0.1),
            lambda value: value.update(physical_actuation=True),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaisesRegex(ValueError, "drift"):
                verify_training_spec(sign_payload(drift))

    def test_result_passes_only_when_objective_and_every_chunk_pass(self) -> None:
        spec = self._spec()
        run = self._run(max_error=0.04, final=0.09)
        result = build_result(spec=spec, authority_identity="f" * 64, run=run)
        self.assertTrue(result["gate_b_one_batch_memorization_passed"])
        self.assertEqual(result["selected_next_hypothesis"], "gate_c_closed_loop_execution_semantics")
        verify_result(result, spec=spec, run=run)

        for run in (self._run(max_error=0.051, final=0.09), self._run(max_error=0.04, final=0.11)):
            result = build_result(spec=spec, authority_identity="f" * 64, run=run)
            self.assertFalse(result["gate_b_one_batch_memorization_passed"])
            self.assertEqual(result["selected_next_hypothesis"], "gate_b_model_or_trainer_plumbing")

    def test_result_rejects_update_seed_nonfinite_and_signed_mutation(self) -> None:
        spec = self._spec()
        for mutation, message in (
            (lambda value: value.update(optimizer_update_count=499), "update"),
            (lambda value: value["decoded_action_chunks"].reverse(), "seed"),
            (lambda value: value["per_update_objective"].__setitem__(0, "nan"), "finite"),
        ):
            run = self._run(max_error=0.04, final=0.09)
            mutation(run)
            run = sign_payload(run)
            with self.assertRaisesRegex(ValueError, message):
                build_result(spec=spec, authority_identity="f" * 64, run=run)
        run = self._run(max_error=0.04, final=0.09)
        result = build_result(spec=spec, authority_identity="f" * 64, run=run)
        drift = copy.deepcopy(result)
        drift["simulation_policy_accepted"] = True
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_result(sign_payload(drift), spec=spec, run=run)

    def test_owner_grant_is_spec_bound_and_simulation_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "configurations/robot_lab/t20_33_one_batch_training_spec.json"
            path.parent.mkdir(parents=True)
            spec = self._spec()
            path.write_text(json.dumps(spec), encoding="utf-8")
            grant = build_owner_grant(training_spec=spec, repo_root=root)
            verify_owner_grant(grant, training_spec=spec, repo_root=root)
            self.assertEqual(grant["authorized_actions"], list(AUTHORIZED_ACTIONS))
            self.assertFalse(grant["physical_transfer_authorized"])
            drift = copy.deepcopy(grant)
            drift["authorized_actions"].append("physical_actuation")
            with self.assertRaisesRegex(ValueError, "drifted"):
                verify_owner_grant(
                    sign_payload(drift), training_spec=spec, repo_root=root
                )

    def test_run_rejects_batch_update_seed_and_authority_drift(self) -> None:
        spec = self._spec()
        base = self._run(max_error=0.04, final=0.09)
        verify_run(base, spec=spec, authority_identity="f" * 64)
        for mutation in (
            lambda value: value.update(fixed_dataset_index=1),
            lambda value: value.update(optimizer_update_count=499),
            lambda value: value["decoded_action_chunks"].reverse(),
            lambda value: value.update(simulation_policy_accepted=True),
        ):
            drift = copy.deepcopy(base)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_run(sign_payload(drift), spec=spec, authority_identity="f" * 64)

    @staticmethod
    def _spec() -> dict:
        frames = []
        for index in range(50):
            frames.append({
                "observations": {
                    "joint_position_mujoco_rad": [0.0] * 6,
                    "top": {"image_sha256": "a" * 64},
                    "wrist": {"image_sha256": "b" * 64},
                },
                "actions": {"measured": {"state": "derived", "units": "radian", "values": [index / 1000] * 6}},
            })
        return build_training_spec(
            dataset_manifest_ref={"path": "dataset.json", "schema_version": "dataset.v1", "identity_sha256": "1" * 64, "file_sha256": "2" * 64},
            source_manifest_ref={"path": "source.json", "schema_version": "source.v1", "identity_sha256": "3" * 64, "file_sha256": "4" * 64},
            source_episode={"frames": frames},
            source_entry={"episode_file_sha256": "5" * 64, "raw_rollout_record_identity_sha256": "6" * 64},
            model_revision="7de663972b7817d2c4cf2d84c821153dfea772e9",
        )

    @staticmethod
    def _run(*, max_error: float, final: float) -> dict:
        spec = T2033OneBatchMemorizationTests._spec()
        tree = [
            {"path": "adapter_config.json", "size_bytes": 1, "sha256": "d" * 64},
            {"path": "adapter_model.safetensors", "size_bytes": 2, "sha256": "e" * 64},
        ]
        return sign_payload({
            "schema_version": "scenesmith.t20_33_one_batch_run.v1",
            "task_id": "T20.33",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": "f" * 64,
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "training_seed": 20260717,
            "fixed_dataset_index": 0,
            "fixed_source_seed": 0,
            "action_horizon": 50,
            "source_measured_action_chunk_sha256": "a" * 64,
            "dataset_action_chunk_sha256": "b" * 64,
            "checkpoint_identity_sha256": hashlib.sha256(
                canonical_json_bytes(tree)
            ).hexdigest(),
            "checkpoint_tree": tree,
            "per_update_objective": [1.0] * OPTIMIZER_UPDATES,
            "gradient_norms_before_clip": [1.0] * OPTIMIZER_UPDATES,
            "baseline_objective_mean": 1.0,
            "final_objective_mean": final,
            "decoded_action_chunks": [
                {
                    "inference_seed": seed,
                    "decoded_action_chunk_sha256": str(index + 1) * 64,
                    "mean_absolute_error_rad": max_error / 2,
                    "maximum_absolute_error_rad": max_error,
                }
                for index, seed in enumerate(INFERENCE_SEEDS)
            ],
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "twin_updated": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        })


if __name__ == "__main__":
    unittest.main()
