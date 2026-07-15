from __future__ import annotations

import copy
import hashlib
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35t_time_normalized_standard_replay_correction import (
    CORRECTION_EXAMPLE_COUNT,
    OPTIMIZER_UPDATES,
    RECONSTRUCTION_TOLERANCE,
    RUN_SCHEMA_VERSION,
    build_correction_examples,
    build_result,
    build_training_spec,
    load_source_artifacts,
    verify_result,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_35t_simulation_training_authority import (
    build_owner_grant,
    verify_authority,
    verify_owner_grant,
)


class T2035tTimeNormalizedStandardReplayCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sources = load_source_artifacts()
        cls.source_spec = sources["source_spec"]
        cls.source_run = sources["source_run"]
        cls.source_result = sources["source_result"]
        cls.trajectory_spec = sources["trajectory_spec"]
        cls.trajectory_result = sources["trajectory_result"]
        cls.target_result = sources["target_result"]
        cls.objective_mass_audit = sources["objective_mass_audit"]

    def test_exact_fifty_example_reconstruction(self) -> None:
        examples = build_correction_examples(
            self.trajectory_result, self.target_result
        )
        self.assertEqual(len(examples), CORRECTION_EXAMPLE_COUNT)
        self.assertEqual(
            [(row["inference_seed"], row["step_index"]) for row in examples],
            [
                (seed, step)
                for seed in (20260721, 20260722, 20260723, 20260724, 20260725)
                for step in range(10)
            ],
        )
        self.assertLessEqual(
            max(row["state_reconstruction_maximum_error"] for row in examples),
            RECONSTRUCTION_TOLERANCE,
        )
        self.assertLessEqual(
            max(row["velocity_reconstruction_maximum_error"] for row in examples),
            RECONSTRUCTION_TOLERANCE,
        )

    def test_spec_binds_source_checkpoint_schedule_and_closed_authority(self) -> None:
        spec = self._spec()
        verify_training_spec(
            spec,
            source_spec=self.source_spec,
            source_run=self.source_run,
            source_result=self.source_result,
            trajectory_spec=self.trajectory_spec,
            trajectory_result=self.trajectory_result,
            target_result=self.target_result,
            objective_mass_audit=self.objective_mass_audit,
        )
        self.assertEqual(spec["campaign"]["optimizer_update_count"], 500)
        self.assertEqual(spec["campaign"]["correction_example_count"], 50)
        self.assertEqual(
            spec["campaign"]["sample_index_by_update"][:51],
            list(range(50)) + [0],
        )
        self.assertEqual(len(spec["time_normalization"]["weight_by_step"]), 10)
        self.assertEqual(
            len(spec["campaign"]["standard_replay_seed_by_update"]), 500
        )
        step_means = [
            row["baseline_objective_mean"]
            for row in self.objective_mass_audit["objective_by_step"]
        ]
        weighted = [
            mean * weight
            for mean, weight in zip(
                step_means,
                spec["time_normalization"]["weight_by_step"],
                strict=True,
            )
        ]
        self.assertLess(max(weighted) - min(weighted), 1e-12)
        self.assertFalse(spec["closed_loop_rollout"])
        self.assertFalse(spec["external_compute_started"])

    def test_spec_and_source_route_drift_fail_closed(self) -> None:
        spec = self._spec()
        for mutation in (
            lambda value: value["campaign"].update(optimizer_update_count=501),
            lambda value: value["campaign"].update(learning_rate=2.5e-4),
            lambda value: value["campaign"].update(sample_index_by_update=[0] * 500),
            lambda value: value["time_normalization"].update(weight_by_step=[1.0] * 10),
            lambda value: value["campaign"].update(standard_replay_seed_by_update=[1] * 500),
            lambda value: value.update(closed_loop_rollout=True),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_training_spec(
                    sign_payload(drift),
                    source_spec=self.source_spec,
                    source_run=self.source_run,
                    source_result=self.source_result,
                    trajectory_spec=self.trajectory_spec,
                    trajectory_result=self.trajectory_result,
                    target_result=self.target_result,
                    objective_mass_audit=self.objective_mass_audit,
                )
        route_drift = copy.deepcopy(self.trajectory_result)
        route_drift["gate_b_passed"] = True
        with self.assertRaises(ValueError):
            build_training_spec(
                source_spec=self.source_spec,
                source_run=self.source_run,
                source_result=self.source_result,
                trajectory_spec=self.trajectory_spec,
                trajectory_result=sign_payload(route_drift),
                target_result=self.target_result,
                objective_mass_audit=self.objective_mass_audit,
            )

    def test_central_authority_is_training_only_and_owner_grant_fails_closed(self) -> None:
        spec = self._spec()
        owner = build_owner_grant(training_spec=spec)
        verify_owner_grant(owner, training_spec=spec)
        self.assertFalse(owner["physical_transfer_authorized"])
        self.assertFalse(owner["external_compute_authorized"])
        self.assertFalse(owner["brev_compute_authorized"])
        authority = verify_authority()
        self.assertEqual(
            authority["decision"]["authority_granted"],
            ["simulation_training_ready"],
        )
        drift = copy.deepcopy(owner)
        drift["brev_compute_authorized"] = True
        with self.assertRaises(ValueError):
            verify_owner_grant(sign_payload(drift), training_spec=spec)

    def test_result_requires_both_objective_and_action_gate(self) -> None:
        spec = self._spec()
        result = build_result(
            spec=spec,
            authority_identity="a" * 64,
            run=self._run(spec, final_objective=0.05, maximum_error=0.04),
        )
        verify_result(result, spec=spec, run=self._run(spec, final_objective=0.05, maximum_error=0.04))
        self.assertTrue(result["gate_b_passed"])
        self.assertEqual(
            result["selected_next_hypothesis"],
            "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction",
        )
        action_fail = build_result(
            spec=spec,
            authority_identity="a" * 64,
            run=self._run(spec, final_objective=0.05, maximum_error=0.06),
        )
        self.assertFalse(action_fail["gate_b_passed"])
        self.assertEqual(
            action_fail["selected_next_hypothesis"],
            "balanced_objectives_pass_action_fail_route_post_training_path_audit",
        )
        objective_fail = build_result(
            spec=spec,
            authority_identity="a" * 64,
            run=self._run(
                spec,
                final_objective=0.05,
                maximum_error=0.04,
                final_standard_objective=0.2,
            ),
        )
        self.assertFalse(objective_fail["gate_b_passed"])
        self.assertEqual(
            objective_fail["selected_next_hypothesis"],
            "action_pass_balanced_objective_fail_route_objective_floor_audit",
        )

    def test_result_tamper_nonfinite_and_incomplete_coverage_fail_closed(self) -> None:
        spec = self._spec()
        run = self._run(spec, final_objective=0.05, maximum_error=0.04)
        result = build_result(spec=spec, authority_identity="a" * 64, run=run)
        drift = copy.deepcopy(result)
        drift["gate_b_passed"] = False
        with self.assertRaises(ValueError):
            verify_result(sign_payload(drift), spec=spec, run=run)
        bad = copy.deepcopy(run)
        bad["per_update_objective"][0] = float("nan")
        with self.assertRaises(ValueError):
            build_result(spec=spec, authority_identity="a" * 64, run=sign_payload(bad))
        bad = copy.deepcopy(run)
        bad["sample_index_by_update"] = [0] * OPTIMIZER_UPDATES
        with self.assertRaises(ValueError):
            build_result(spec=spec, authority_identity="a" * 64, run=sign_payload(bad))

    def _spec(self):
        return build_training_spec(
            source_spec=self.source_spec,
            source_run=self.source_run,
            source_result=self.source_result,
            trajectory_spec=self.trajectory_spec,
            trajectory_result=self.trajectory_result,
            target_result=self.target_result,
            objective_mass_audit=self.objective_mass_audit,
        )

    @staticmethod
    def _run(
        spec,
        *,
        final_objective: float,
        maximum_error: float,
        final_standard_objective: float = 0.05,
    ):
        chunks = [
            {
                "inference_seed": seed,
                "decoded_action_chunk_sha256": f"{index + 1:064x}",
                "mean_absolute_error_rad": maximum_error / 2,
                "maximum_absolute_error_rad": maximum_error,
            }
            for index, seed in enumerate(
                (20260721, 20260722, 20260723, 20260724, 20260725)
            )
        ]
        checkpoint_tree = [
            {"path": "config.json", "size_bytes": 1, "sha256": "c" * 64},
            {"path": "model.safetensors", "size_bytes": 1, "sha256": "d" * 64},
        ]
        weights = spec["time_normalization"]["weight_by_step"]
        sample_order = spec["campaign"]["sample_index_by_update"]
        raw_updates = [final_objective] * OPTIMIZER_UPDATES
        weighted_updates = [
            final_objective * weights[index % 10] for index in sample_order
        ]
        standard_updates = [0.01] * OPTIMIZER_UPDATES
        baseline_raw = [1.0] * CORRECTION_EXAMPLE_COUNT
        final_raw = [final_objective] * CORRECTION_EXAMPLE_COUNT
        baseline_weighted = [
            value * weights[index % 10]
            for index, value in enumerate(baseline_raw)
        ]
        final_weighted = [
            value * weights[index % 10]
            for index, value in enumerate(final_raw)
        ]
        return sign_payload(
            {
                "schema_version": RUN_SCHEMA_VERSION,
                "task_id": "T20.35t",
                "training_spec_identity_sha256": spec["identity_sha256"],
                "authority_decision_identity_sha256": "a" * 64,
                "attempt_identity_sha256": "b" * 64,
                "source_checkpoint_identity_sha256": spec[
                    "source_checkpoint_identity_sha256"
                ],
                "optimizer_update_count": OPTIMIZER_UPDATES,
                "learning_rate": 2.5e-5,
                "optimizer_config": {
                    "optimizer": "AdamW",
                    "betas": [0.9, 0.999],
                    "epsilon": 1e-8,
                    "weight_decay": 0.0,
                    "amsgrad": False,
                    "gradient_clip_norm": 1.0,
                },
                "correction_example_count": CORRECTION_EXAMPLE_COUNT,
                "sample_index_by_update": spec["campaign"]["sample_index_by_update"],
                "example_use_count": [10] * CORRECTION_EXAMPLE_COUNT,
                "time_normalization_weight_by_step": weights,
                "standard_replay_seed_by_update": spec["campaign"][
                    "standard_replay_seed_by_update"
                ],
                "standard_replay_update_count": OPTIMIZER_UPDATES,
                "adaptation_mode": "expert_only_no_peft",
                "trainable_prefixes": spec["model"]["trainable_prefixes"],
                "trainable_parameter_names_sha256": "f" * 64,
                "trainable_parameter_count": 100,
                "paligemma_parameter_count": 200,
                "paligemma_trainable_parameter_count": 0,
                "source_checkpoint_tree_unchanged": True,
                "baseline_correction_objective_mean": 1.0,
                "final_correction_objective_mean": final_objective,
                "baseline_standard_objective_mean": spec[
                    "source_checkpoint_standard_objective_mean"
                ],
                "final_standard_objective_mean": final_standard_objective,
                "baseline_objective_by_example": baseline_raw,
                "final_objective_by_example": final_raw,
                "baseline_weighted_correction_objective_mean": sum(
                    baseline_weighted
                )
                / CORRECTION_EXAMPLE_COUNT,
                "final_weighted_correction_objective_mean": sum(final_weighted)
                / CORRECTION_EXAMPLE_COUNT,
                "baseline_weighted_objective_by_example": baseline_weighted,
                "final_weighted_objective_by_example": final_weighted,
                "baseline_standard_objective_by_seed": [
                    spec["source_checkpoint_standard_objective_mean"]
                ]
                * 5,
                "final_standard_objective_by_seed": [final_standard_objective] * 5,
                "per_update_objective": [
                    weighted + standard
                    for weighted, standard in zip(
                        weighted_updates, standard_updates, strict=True
                    )
                ],
                "per_update_raw_correction_objective": raw_updates,
                "per_update_weighted_correction_objective": weighted_updates,
                "per_update_standard_replay_objective": standard_updates,
                "gradient_norms_before_clip": [0.1] * OPTIMIZER_UPDATES,
                "decoded_action_chunks": chunks,
                "checkpoint_tree": checkpoint_tree,
                "checkpoint_identity_sha256": hashlib.sha256(
                    canonical_json_bytes(checkpoint_tree)
                ).hexdigest(),
                "optimizer_training": True,
                "checkpoint_mutated": False,
                "dataset_mutated": False,
                "statistics_changed": False,
                "sampler_mutated": False,
                "closed_loop_rollout": False,
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
