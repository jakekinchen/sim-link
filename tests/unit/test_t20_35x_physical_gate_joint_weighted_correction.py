from __future__ import annotations

import copy
import hashlib
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (
    CORRECTION_EXAMPLE_COUNT,
    EXPECTED_DEPENDENCY_VERSIONS,
    EXPECTED_RUNTIME_PREFLIGHT_IDENTITY,
    EXPECTED_TRAINING_PERMIT_IDENTITY,
    OPTIMIZER_UPDATES,
    RECONSTRUCTION_TOLERANCE,
    RUN_SCHEMA_VERSION,
    build_correction_examples,
    build_result,
    build_runtime_preflight,
    build_training_permit,
    build_training_spec,
    derive_joint_weighting,
    load_source_artifacts,
    verify_result,
    verify_runtime_preflight,
    verify_training_permit,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_35x_simulation_training_authority import (
    build_owner_grant,
    verify_authority,
    verify_owner_grant,
)
from scripts.robot_lab.run_t20_35x_physical_gate_joint_weighted_correction import (
    _correction_losses,
)


class T2035xPhysicalGateJointWeightedCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sources = load_source_artifacts()
        cls.sources = sources
        cls.weighting = derive_joint_weighting(sources["dataset_stats"])

    def test_exact_current_path_fifty_example_reconstruction(self) -> None:
        examples = build_correction_examples(
            self.sources["trajectory_result"],
            self.sources["target_result"],
            self.weighting["coefficient_by_dimension"],
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
        self.assertTrue(
            all(
                row["baseline_joint_weighted_correction_objective"] > 0
                for row in examples
            )
        )

    def test_physical_joint_weights_bind_exact_stats_and_padded_dimensions(
        self,
    ) -> None:
        weighting = self.weighting
        self.assertEqual(len(weighting["active_joint_coefficient"]), 6)
        self.assertEqual(len(weighting["coefficient_by_dimension"]), 32)
        self.assertAlmostEqual(
            sum(weighting["active_joint_coefficient"]) / 6, 1.0, places=15
        )
        self.assertEqual(weighting["coefficient_by_dimension"][6:], [1.0] * 26)
        self.assertEqual(
            weighting["dataset_action_standard_deviation_lerobot_units"],
            self.sources["dataset_stats"]["action"]["std"],
        )
        drift = copy.deepcopy(self.sources["dataset_stats"])
        drift["action"]["std"][1] = float("nan")
        with self.assertRaises(ValueError):
            derive_joint_weighting(drift)

    def test_spec_binds_balanced_schedule_joint_and_time_weights(self) -> None:
        spec = self._spec()
        self._verify_spec(spec)
        self.assertEqual(spec["campaign"]["optimizer_update_count"], 500)
        self.assertEqual(spec["campaign"]["correction_example_count"], 50)
        self.assertEqual(
            spec["campaign"]["sample_index_by_update"][:51],
            list(range(50)) + [0],
        )
        step_means = spec["time_normalization"][
            "initial_joint_weighted_objective_by_step"
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
        self.assertEqual(len(spec["campaign"]["standard_replay_seed_by_update"]), 500)
        self.assertEqual(
            len(set(spec["campaign"]["standard_replay_seed_by_update"])), 500
        )
        self.assertTrue(spec["runtime_dependency_preflight_required"])
        self.assertTrue(spec["one_run_permit_required"])
        self.assertFalse(spec["closed_loop_rollout"])

    def test_live_loss_surface_weights_all_dimensions_but_raw_is_active_only(
        self,
    ) -> None:
        import torch

        losses = torch.arange(1, 33, dtype=torch.float32).view(1, 1, 32)
        losses = losses.expand(1, 50, 32)

        class Model:
            @staticmethod
            def forward(*_args):
                return losses

        class Policy:
            model = Model()

        coefficients = torch.tensor(
            self.weighting["coefficient_by_dimension"], dtype=torch.float32
        ).view(1, 1, 32)
        raw, joint = _correction_losses(
            Policy(),
            None,
            None,
            None,
            None,
            None,
            {"noise": None, "time": None},
            coefficients,
            torch,
        )
        self.assertAlmostEqual(float(raw), float(losses[:, :, :6].mean()))
        self.assertAlmostEqual(float(joint), float((losses * coefficients).mean()))

    def test_spec_and_route_drift_fail_closed(self) -> None:
        spec = self._spec()
        for mutation in (
            lambda value: value["campaign"].update(optimizer_update_count=501),
            lambda value: value["campaign"].update(learning_rate=2.5e-4),
            lambda value: value["physical_joint_weighting"].update(
                coefficient_by_dimension=[1.0] * 32
            ),
            lambda value: value["time_normalization"].update(weight_by_step=[1.0] * 10),
            lambda value: value.update(closed_loop_rollout=True),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaises(ValueError):
                self._verify_spec(sign_payload(drift))
        route_drift = copy.deepcopy(self.sources["outlier_audit"])
        route_drift["gate_b_passed"] = True
        with self.assertRaises(ValueError):
            self._build_spec(outlier_audit=sign_payload(route_drift))

    def test_runtime_preflight_and_one_use_permit_fail_closed(self) -> None:
        spec = self._spec()
        runtime = build_runtime_preflight(
            spec=spec,
            authority_identity="a" * 64,
            python_major_minor=[3, 12],
            dependency_versions=copy.deepcopy(EXPECTED_DEPENDENCY_VERSIONS),
            mps_available=True,
            lerobot_stack_identity_sha256=spec["lerobot_stack_identity_sha256"],
            checkpoint_tree_verified=True,
            attempt_exists=False,
            result_exists=False,
        )
        verify_runtime_preflight(runtime, spec=spec, authority_identity="a" * 64)
        permit = build_training_permit(
            spec=spec,
            authority_identity="a" * 64,
            runtime_preflight=runtime,
        )
        verify_training_permit(
            permit,
            spec=spec,
            authority_identity="a" * 64,
            runtime_preflight=runtime,
        )
        with self.assertRaises(ValueError):
            build_runtime_preflight(
                spec=spec,
                authority_identity="a" * 64,
                python_major_minor=[3, 12],
                dependency_versions={**EXPECTED_DEPENDENCY_VERSIONS, "datasets": "0"},
                mps_available=True,
                lerobot_stack_identity_sha256=spec["lerobot_stack_identity_sha256"],
                checkpoint_tree_verified=True,
                attempt_exists=False,
                result_exists=False,
            )

    def test_central_authority_is_training_only(self) -> None:
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

    def test_result_requires_unchanged_objective_and_action_gates(self) -> None:
        spec = self._spec()
        passing_run = self._run(spec, correction_ratio=0.05, maximum_error=0.04)
        result = build_result(spec=spec, authority_identity="a" * 64, run=passing_run)
        verify_result(result, spec=spec, run=passing_run)
        self.assertTrue(result["gate_b_passed"])
        self.assertEqual(
            result["selected_next_hypothesis"],
            "gate_b_pass_route_separately_reviewed_gate_c_closed_loop_reproduction",
        )
        action_fail_run = self._run(spec, correction_ratio=0.05, maximum_error=0.06)
        action_fail = build_result(
            spec=spec, authority_identity="a" * 64, run=action_fail_run
        )
        self.assertFalse(action_fail["gate_b_passed"])
        self.assertEqual(
            action_fail["selected_next_hypothesis"],
            "joint_weighted_objectives_pass_action_fail_route_post_training_path_audit",
        )
        objective_fail_run = self._run(
            spec,
            correction_ratio=0.05,
            maximum_error=0.04,
            final_standard_objective=0.2,
        )
        objective_fail = build_result(
            spec=spec, authority_identity="a" * 64, run=objective_fail_run
        )
        self.assertFalse(objective_fail["gate_b_passed"])
        self.assertEqual(
            objective_fail["selected_next_hypothesis"],
            "action_pass_standard_objective_fail_route_objective_floor_audit",
        )
        result_drift = copy.deepcopy(result)
        result_drift["gate_b_passed"] = False
        with self.assertRaises(ValueError):
            verify_result(sign_payload(result_drift), spec=spec, run=passing_run)
        nonfinite_run = copy.deepcopy(passing_run)
        nonfinite_run["per_update_objective"][0] = float("nan")
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                authority_identity="a" * 64,
                run=sign_payload(nonfinite_run),
            )
        lineage_drift = copy.deepcopy(passing_run)
        lineage_drift["training_permit_identity_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build_result(
                spec=spec,
                authority_identity="a" * 64,
                run=sign_payload(lineage_drift),
            )

    def _build_spec(self, **overrides):
        values = {
            "source_spec": self.sources["source_spec"],
            "source_run": self.sources["source_run"],
            "source_result": self.sources["source_result"],
            "trajectory_spec": self.sources["trajectory_spec"],
            "trajectory_result": self.sources["trajectory_result"],
            "target_result": self.sources["target_result"],
            "outlier_audit": self.sources["outlier_audit"],
            "dataset_manifest": self.sources["dataset_manifest"],
            "dataset_stats": self.sources["dataset_stats"],
            "dataset_stats_file_sha256": self.sources["dataset_stats_file_sha256"],
        }
        values.update(overrides)
        return build_training_spec(**values)

    def _spec(self):
        return self._build_spec()

    def _verify_spec(self, spec):
        return verify_training_spec(
            spec,
            source_spec=self.sources["source_spec"],
            source_run=self.sources["source_run"],
            source_result=self.sources["source_result"],
            trajectory_spec=self.sources["trajectory_spec"],
            trajectory_result=self.sources["trajectory_result"],
            target_result=self.sources["target_result"],
            outlier_audit=self.sources["outlier_audit"],
            dataset_manifest=self.sources["dataset_manifest"],
            dataset_stats=self.sources["dataset_stats"],
            dataset_stats_file_sha256=self.sources["dataset_stats_file_sha256"],
        )

    @staticmethod
    def _run(
        spec,
        *,
        correction_ratio: float,
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
        baseline_raw = [
            row["baseline_raw_correction_objective"]
            for row in spec["correction_examples"]
        ]
        baseline_joint = [
            row["baseline_joint_weighted_correction_objective"]
            for row in spec["correction_examples"]
        ]
        final_raw = [value * correction_ratio for value in baseline_raw]
        final_joint = [value * correction_ratio for value in baseline_joint]
        baseline_time_joint = [
            value * weights[index % 10] for index, value in enumerate(baseline_joint)
        ]
        final_time_joint = [
            value * weights[index % 10] for index, value in enumerate(final_joint)
        ]
        raw_updates = [final_raw[index] for index in sample_order]
        joint_updates = [final_joint[index] for index in sample_order]
        time_joint_updates = [
            value * weights[index % 10]
            for value, index in zip(joint_updates, sample_order, strict=True)
        ]
        standard_updates = [0.01] * OPTIMIZER_UPDATES
        return sign_payload(
            {
                "schema_version": RUN_SCHEMA_VERSION,
                "task_id": "T20.35x",
                "training_spec_identity_sha256": spec["identity_sha256"],
                "authority_decision_identity_sha256": "a" * 64,
                "runtime_preflight_identity_sha256": EXPECTED_RUNTIME_PREFLIGHT_IDENTITY,
                "training_permit_identity_sha256": EXPECTED_TRAINING_PERMIT_IDENTITY,
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
                "sample_index_by_update": sample_order,
                "example_use_count": [10] * CORRECTION_EXAMPLE_COUNT,
                "joint_weight_coefficient_by_dimension": spec[
                    "physical_joint_weighting"
                ]["coefficient_by_dimension"],
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
                "baseline_raw_correction_objective_mean": sum(baseline_raw) / 50,
                "final_raw_correction_objective_mean": sum(final_raw) / 50,
                "baseline_joint_weighted_correction_objective_mean": sum(baseline_joint)
                / 50,
                "final_joint_weighted_correction_objective_mean": sum(final_joint) / 50,
                "baseline_time_joint_weighted_correction_objective_mean": sum(
                    baseline_time_joint
                )
                / 50,
                "final_time_joint_weighted_correction_objective_mean": sum(
                    final_time_joint
                )
                / 50,
                "baseline_raw_objective_by_example": baseline_raw,
                "final_raw_objective_by_example": final_raw,
                "baseline_joint_weighted_objective_by_example": baseline_joint,
                "final_joint_weighted_objective_by_example": final_joint,
                "baseline_time_joint_weighted_objective_by_example": baseline_time_joint,
                "final_time_joint_weighted_objective_by_example": final_time_joint,
                "baseline_standard_objective_mean": spec[
                    "source_checkpoint_standard_objective_mean"
                ],
                "final_standard_objective_mean": final_standard_objective,
                "baseline_standard_objective_by_seed": [
                    spec["source_checkpoint_standard_objective_mean"]
                ]
                * 5,
                "final_standard_objective_by_seed": [final_standard_objective] * 5,
                "per_update_objective": [
                    correction + standard
                    for correction, standard in zip(
                        time_joint_updates, standard_updates, strict=True
                    )
                ],
                "per_update_raw_correction_objective": raw_updates,
                "per_update_joint_weighted_correction_objective": joint_updates,
                "per_update_time_joint_weighted_correction_objective": time_joint_updates,
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
