from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.t20_35_rank_capacity_discriminator import (
    INFERENCE_SEEDS,
    LORA_ALPHA,
    LORA_RANK,
    OPTIMIZER_UPDATES,
    SPEC_PATH,
    build_result,
    build_training_spec,
    verify_result,
    verify_run,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_35_simulation_training_authority import (
    AUTHORIZED_ACTIONS,
    build_owner_grant,
    verify_owner_grant,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
T20_33_SPEC = load_strict_json(
    REPO_ROOT / "configurations/robot_lab/t20_33_one_batch_training_spec.json"
)
T20_33_RESULT = load_strict_json(
    REPO_ROOT / "configurations/robot_lab/t20_33_one_batch_result.json"
)


class T2035RankCapacityDiscriminatorTests(unittest.TestCase):
    def test_spec_changes_only_identity_metadata_and_rank_alpha(self) -> None:
        spec = build_training_spec(t20_33_spec=T20_33_SPEC)
        verify_training_spec(spec, t20_33_spec=T20_33_SPEC)
        self.assertEqual(spec["model"]["lora_rank"], 16)
        self.assertEqual(spec["model"]["lora_alpha"], 16)
        self.assertEqual(spec["campaign"], T20_33_SPEC["campaign"])
        self.assertEqual(spec["source_batch"], T20_33_SPEC["source_batch"])
        self.assertEqual(spec["gate"], T20_33_SPEC["gate"])
        self.assertEqual(
            spec["t20_33_training_spec_identity_sha256"],
            T20_33_SPEC["identity_sha256"],
        )

    def test_spec_rejects_every_material_drift_beyond_rank_alpha(self) -> None:
        spec = build_training_spec(t20_33_spec=T20_33_SPEC)
        for mutation in (
            lambda value: value["campaign"].update(learning_rate=2.5e-4),
            lambda value: value["campaign"].update(optimizer_update_count=501),
            lambda value: value["source_batch"].update(frame_index=1),
            lambda value: value["gate"].update(
                maximum_final_to_baseline_objective_ratio=0.2
            ),
            lambda value: value["model"].update(lora_rank=8),
            lambda value: value.update(external_compute_started=True),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaisesRegex(ValueError, "drift"):
                verify_training_spec(sign_payload(drift), t20_33_spec=T20_33_SPEC)

    def test_run_rejects_rank_rate_batch_seed_and_authority_drift(self) -> None:
        spec = build_training_spec(t20_33_spec=T20_33_SPEC)
        run = self._run(spec=spec, max_error=0.04, final=0.09)
        verify_run(run, spec=spec, authority_identity="f" * 64)
        for mutation in (
            lambda value: value.update(lora_rank=4),
            lambda value: value.update(learning_rate=2.5e-4),
            lambda value: value.update(fixed_dataset_index=1),
            lambda value: value.update(optimizer_update_count=499),
            lambda value: value["decoded_action_chunks"].reverse(),
            lambda value: value.update(simulation_policy_accepted=True),
        ):
            drift = copy.deepcopy(run)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_run(
                    sign_payload(drift),
                    spec=spec,
                    authority_identity="f" * 64,
                )

    def test_result_routes_pass_or_conditional_ladder_once(self) -> None:
        spec = build_training_spec(t20_33_spec=T20_33_SPEC)
        passing_run = self._run(spec=spec, max_error=0.04, final=0.09)
        passing = build_result(
            spec=spec,
            authority_identity="f" * 64,
            run=passing_run,
            t20_33_result=T20_33_RESULT,
        )
        self.assertTrue(passing["gate_b_one_batch_memorization_passed"])
        self.assertEqual(
            passing["selected_next_hypothesis"], "gate_b_corrected_rank_capacity"
        )
        verify_result(
            passing,
            spec=spec,
            run=passing_run,
            t20_33_result=T20_33_RESULT,
        )

        failing_run = self._run(spec=spec, max_error=0.051, final=0.11)
        failing = build_result(
            spec=spec,
            authority_identity="f" * 64,
            run=failing_run,
            t20_33_result=T20_33_RESULT,
        )
        self.assertFalse(failing["gate_b_one_batch_memorization_passed"])
        self.assertEqual(
            failing["selected_next_hypothesis"],
            "gate_b_rank_capacity_insufficient_route_t20_35_x",
        )
        self.assertEqual(
            failing["t20_33_result_identity_sha256"],
            T20_33_RESULT["identity_sha256"],
        )

    def test_result_rejects_nonfinite_and_signed_mutation(self) -> None:
        spec = build_training_spec(t20_33_spec=T20_33_SPEC)
        run = self._run(spec=spec, max_error=0.04, final=0.09)
        run["gradient_norms_before_clip"][0] = "nan"
        with self.assertRaisesRegex(ValueError, "finite"):
            build_result(
                spec=spec,
                authority_identity="f" * 64,
                run=sign_payload(run),
                t20_33_result=T20_33_RESULT,
            )

    def test_owner_grant_is_new_spec_bound_and_simulation_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / SPEC_PATH
            path.parent.mkdir(parents=True)
            spec = build_training_spec(t20_33_spec=T20_33_SPEC)
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

    @staticmethod
    def _run(*, spec: dict, max_error: float, final: float) -> dict:
        tree = [
            {"path": "adapter_config.json", "size_bytes": 1, "sha256": "d" * 64},
            {
                "path": "adapter_model.safetensors",
                "size_bytes": 2,
                "sha256": "e" * 64,
            },
        ]
        return sign_payload(
            {
                "schema_version": "scenesmith.t20_35_rank_capacity_run.v1",
                "task_id": "T20.35",
                "training_spec_identity_sha256": spec["identity_sha256"],
                "authority_decision_identity_sha256": "f" * 64,
                "attempt_identity_sha256": "8" * 64,
                "lerobot_stack_identity_sha256": "c" * 64,
                "optimizer_update_count": OPTIMIZER_UPDATES,
                "training_seed": 20260717,
                "fixed_dataset_index": 0,
                "fixed_source_seed": 0,
                "action_horizon": 50,
                "learning_rate": 2.5e-5,
                "lora_rank": LORA_RANK,
                "lora_alpha": LORA_ALPHA,
                "peft_target_modules": (
                    r"(.*\.gemma_expert\..*\.self_attn\.(q|v)_proj|model\."
                    r"(state_proj|action_in_proj|action_out_proj|action_time_mlp_in|"
                    r"action_time_mlp_out))"
                ),
                "trainable_parameter_count": 1,
                "trainable_parameter_names_sha256": "9" * 64,
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
                        "decoded_action_chunk_sha256": f"{index + 1}" * 64,
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
            }
        )


if __name__ == "__main__":
    unittest.main()
