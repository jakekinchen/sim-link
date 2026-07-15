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
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (
    ADAPTATION_MODE,
    EXPECTED_DATASET_ACTION_CHUNK_SHA256,
    INFERENCE_SEEDS,
    OPTIMIZER_UPDATES,
    PALIGEMMA_PREFIX,
    SPEC_PATH,
    TRAINABLE_PREFIXES,
    build_result,
    build_training_spec,
    verify_parameter_boundary,
    verify_result,
    verify_run,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_35c_simulation_training_authority import (
    AUTHORIZED_ACTIONS,
    build_owner_grant,
    verify_owner_grant,
)
from scripts.robot_lab.run_t20_35c_expert_only_capacity_ceiling import (
    _verify_attempt,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
T20_33_SPEC = load_strict_json(
    REPO_ROOT / "configurations/robot_lab/t20_33_one_batch_training_spec.json"
)
CORRECTION = load_strict_json(
    REPO_ROOT / "configurations/robot_lab/t20_35b_pi05_coverage_correction.json"
)
T20_35_RESULT = load_strict_json(
    REPO_ROOT / "configurations/robot_lab/t20_35_rank_capacity_result.json"
)


class T2035CExpertOnlyCapacityCeilingTests(unittest.TestCase):
    def test_spec_changes_only_identity_and_expert_adaptation_boundary(self) -> None:
        spec = self._spec()
        verify_training_spec(
            spec, t20_33_spec=T20_33_SPEC, correction=CORRECTION
        )
        self.assertEqual(spec["campaign"], T20_33_SPEC["campaign"])
        self.assertEqual(spec["source_batch"], T20_33_SPEC["source_batch"])
        self.assertEqual(spec["gate"], T20_33_SPEC["gate"])
        self.assertEqual(spec["model"]["adapter"], "none")
        self.assertNotIn("lora_rank", spec["model"])
        self.assertNotIn("lora_alpha", spec["model"])
        self.assertTrue(spec["model"]["train_expert_only"])
        self.assertEqual(
            spec["t20_35b_coverage_correction_identity_sha256"],
            CORRECTION["identity_sha256"],
        )

    def test_spec_rejects_peft_campaign_source_gate_and_boundary_drift(self) -> None:
        spec = self._spec()
        for mutation in (
            lambda value: value["model"].update(adapter="lora"),
            lambda value: value["model"].update(train_expert_only=False),
            lambda value: value["model"]["trainable_prefixes"].pop(),
            lambda value: value["campaign"].update(learning_rate=2.5e-4),
            lambda value: value["campaign"].update(optimizer_update_count=5000),
            lambda value: value["source_batch"].update(frame_index=1),
            lambda value: value["gate"].update(maximum_decoded_action_error_rad=0.1),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaisesRegex(ValueError, "drift"):
                verify_training_spec(
                    sign_payload(drift),
                    t20_33_spec=T20_33_SPEC,
                    correction=CORRECTION,
                )

    def test_parameter_boundary_rejects_lora_pali_and_missing_time_mlp(self) -> None:
        all_names, trainable_names = self._names()
        counts = verify_parameter_boundary(
            all_parameter_names=all_names,
            trainable_parameter_names=trainable_names,
        )
        self.assertEqual(set(counts), set(TRAINABLE_PREFIXES))
        mutations = (
            (all_names + ["model.lora_A.weight"], trainable_names),
            (all_names, trainable_names + [PALIGEMMA_PREFIX + "weight"]),
            (
                all_names,
                [name for name in trainable_names if not name.startswith("model.time_mlp_out.")],
            ),
        )
        for all_drift, trainable_drift in mutations:
            with self.assertRaises(ValueError):
                verify_parameter_boundary(
                    all_parameter_names=all_drift,
                    trainable_parameter_names=trainable_drift,
                )

    def test_run_rejects_peft_trainability_rate_seed_retry_and_authority_drift(self) -> None:
        spec = self._spec()
        run = self._run(spec=spec, max_error=0.04, final=0.09)
        self._verify_run(run, spec)
        for mutation in (
            lambda value: value.update(peft_wrapper_used=True),
            lambda value: value.update(paligemma_trainable_parameter_count=1),
            lambda value: value.update(learning_rate=2.5e-4),
            lambda value: value.update(training_seed=1),
            lambda value: value.update(optimizer_update_count=501),
            lambda value: value["decoded_action_chunks"].reverse(),
            lambda value: value.update(simulation_policy_accepted=True),
        ):
            drift = copy.deepcopy(run)
            mutation(drift)
            with self.assertRaises(ValueError):
                self._verify_run(sign_payload(drift), spec)

    def test_result_routes_each_gate_combination(self) -> None:
        spec = self._spec()
        passing_run = self._run(spec=spec, max_error=0.04, final=0.09)
        passing = self._result(spec, passing_run)
        self.assertTrue(passing["gate_b_one_batch_memorization_passed"])
        self.assertEqual(
            passing["selected_next_hypothesis"],
            "gate_b_expert_only_capacity_ceiling_pass_route_t20_36",
        )
        verify_result(
            passing,
            spec=spec,
            run=passing_run,
            t20_35_result=T20_35_RESULT,
            t20_33_spec=T20_33_SPEC,
            correction=CORRECTION,
        )
        action_only_failure = self._result(
            spec, self._run(spec=spec, max_error=0.051, final=0.09)
        )
        self.assertEqual(
            action_only_failure["selected_next_hypothesis"],
            "gate_b_objective_pass_action_fail_route_decoded_action_residual_localization",
        )
        objective_only_failure = self._result(
            spec, self._run(spec=spec, max_error=0.04, final=0.11)
        )
        self.assertEqual(
            objective_only_failure["selected_next_hypothesis"],
            "gate_b_action_pass_objective_fail_route_objective_floor_audit",
        )
        both_fail = self._result(
            spec, self._run(spec=spec, max_error=0.051, final=0.11)
        )
        self.assertFalse(both_fail["gate_b_one_batch_memorization_passed"])
        self.assertEqual(
            both_fail["selected_next_hypothesis"],
            "gate_b_expert_only_both_fail_route_loss_action_attainability_audit",
        )

    def test_nonfinite_and_checkpoint_mutation_fail_closed(self) -> None:
        spec = self._spec()
        run = self._run(spec=spec, max_error=0.04, final=0.09)
        run["gradient_norms_before_clip"][0] = "nan"
        with self.assertRaisesRegex(ValueError, "finite"):
            self._verify_run(sign_payload(run), spec)
        run = self._run(spec=spec, max_error=0.04, final=0.09)
        run["checkpoint_tree"][0]["size_bytes"] = 9
        with self.assertRaisesRegex(ValueError, "checkpoint identity"):
            self._verify_run(sign_payload(run), spec)

    def test_owner_grant_is_spec_bound_and_simulation_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / SPEC_PATH
            path.parent.mkdir(parents=True)
            spec = self._spec()
            path.write_text(json.dumps(spec), encoding="utf-8")
            grant = build_owner_grant(training_spec=spec, repo_root=root)
            verify_owner_grant(grant, training_spec=spec, repo_root=root)
            self.assertEqual(grant["authorized_actions"], list(AUTHORIZED_ACTIONS))
            self.assertFalse(grant["external_compute_authorized"])
            drift = copy.deepcopy(grant)
            drift["authorized_actions"].append("physical_actuation")
            with self.assertRaisesRegex(ValueError, "drifted"):
                verify_owner_grant(
                    sign_payload(drift), training_spec=spec, repo_root=root
                )

    def test_attempt_marker_consumes_exactly_one_pre_model_permit(self) -> None:
        spec = self._spec()
        marker = sign_payload(
            {
                "schema_version": "scenesmith.t20_35c_expert_only_attempt.v1",
                "task_id": "T20.35c",
                "training_spec_identity_sha256": spec["identity_sha256"],
                "authority_decision_identity_sha256": "f" * 64,
                "started_at": "2026-07-15T09:00:00-05:00",
                "one_run_permit_consumed": True,
                "model_loaded_at_marker": False,
                "optimizer_created_at_marker": False,
                "closed_loop_rollout": False,
                "physical_actuation": False,
                "external_compute_started": False,
                "brev_compute_started": False,
            }
        )
        _verify_attempt(
            marker,
            spec_identity=spec["identity_sha256"],
            authority_identity="f" * 64,
        )
        drift = copy.deepcopy(marker)
        drift["one_run_permit_consumed"] = False
        with self.assertRaisesRegex(ValueError, "attempt marker"):
            _verify_attempt(
                sign_payload(drift),
                spec_identity=spec["identity_sha256"],
                authority_identity="f" * 64,
            )

    @staticmethod
    def _spec() -> dict:
        return build_training_spec(
            t20_33_spec=T20_33_SPEC, correction=CORRECTION
        )

    @staticmethod
    def _names() -> tuple[list[str], list[str]]:
        trainable = [prefix + "weight" for prefix in TRAINABLE_PREFIXES]
        all_names = [PALIGEMMA_PREFIX + "weight", *trainable]
        return all_names, trainable

    @classmethod
    def _run(cls, *, spec: dict, max_error: float, final: float) -> dict:
        all_names, trainable_names = cls._names()
        counts = verify_parameter_boundary(
            all_parameter_names=all_names,
            trainable_parameter_names=trainable_names,
        )
        tree = [
            {"path": "expert_only_config.json", "size_bytes": 1, "sha256": "d" * 64},
            {"path": "expert_only_model.safetensors", "size_bytes": 2, "sha256": "e" * 64},
        ]
        tensor_manifest = [
            {"name": name, "shape": [1], "dtype": "torch.float32", "numel": 1}
            for name in trainable_names
        ]
        return sign_payload(
            {
                "schema_version": "scenesmith.t20_35c_expert_only_run.v1",
                "task_id": "T20.35c",
                "training_spec_identity_sha256": spec["identity_sha256"],
                "authority_decision_identity_sha256": "f" * 64,
                "attempt_identity_sha256": "8" * 64,
                "lerobot_stack_identity_sha256": CORRECTION["lerobot_stack_identity_sha256"],
                "fixed_dataset_index": 0,
                "fixed_source_seed": 0,
                "action_horizon": 50,
                "source_measured_action_chunk_sha256": spec["source_batch"][
                    "measured_action_chunk_sha256"
                ],
                "dataset_action_chunk_sha256": EXPECTED_DATASET_ACTION_CHUNK_SHA256,
                "optimizer_update_count": OPTIMIZER_UPDATES,
                "training_seed": 20260717,
                "learning_rate": 2.5e-5,
                "adaptation_mode": ADAPTATION_MODE,
                "peft_wrapper_used": False,
                "train_expert_only": True,
                "freeze_vision_encoder": True,
                "trainable_prefixes": list(TRAINABLE_PREFIXES),
                "trainable_boundary_complete": True,
                "all_parameter_names": all_names,
                "all_parameter_names_sha256": hashlib.sha256(canonical_json_bytes(all_names)).hexdigest(),
                "trainable_parameter_names": trainable_names,
                "trainable_parameter_names_sha256": hashlib.sha256(canonical_json_bytes(trainable_names)).hexdigest(),
                "trainable_tensor_manifest": tensor_manifest,
                "required_prefix_parameter_counts": counts,
                "all_parameter_count": 6,
                "trainable_parameter_count": 5,
                "paligemma_parameter_count": 1,
                "paligemma_trainable_parameter_count": 0,
                "baseline_objective_mean": 1.0,
                "final_objective_mean": final,
                "per_update_objective": [1.0] * OPTIMIZER_UPDATES,
                "gradient_norms_before_clip": [1.0] * OPTIMIZER_UPDATES,
                "decoded_action_chunks": [
                    {
                        "inference_seed": seed,
                        "decoded_action_chunk_sha256": f"{index + 1}" * 64,
                        "mean_absolute_error_rad": max_error / 2,
                        "maximum_absolute_error_rad": max_error,
                    }
                    for index, seed in enumerate(INFERENCE_SEEDS)
                ],
                "checkpoint_tree": tree,
                "checkpoint_identity_sha256": hashlib.sha256(canonical_json_bytes(tree)).hexdigest(),
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

    @staticmethod
    def _verify_run(run: dict, spec: dict) -> None:
        verify_run(
            run,
            spec=spec,
            authority_identity="f" * 64,
            t20_33_spec=T20_33_SPEC,
            correction=CORRECTION,
        )

    @staticmethod
    def _result(spec: dict, run: dict) -> dict:
        return build_result(
            spec=spec,
            authority_identity="f" * 64,
            run=run,
            t20_35_result=T20_35_RESULT,
            t20_33_spec=T20_33_SPEC,
            correction=CORRECTION,
        )


if __name__ == "__main__":
    unittest.main()
