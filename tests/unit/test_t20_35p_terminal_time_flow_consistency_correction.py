from __future__ import annotations

import copy
import hashlib
import unittest

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (
    RESULT_PATH as SOURCE_RESULT_PATH,
    SPEC_PATH as SOURCE_SPEC_PATH,
)
from scenesmith.robot_lab.t20_35o_flow_trajectory_consistency_audit import (
    RESULT_PATH as TRAJECTORY_RESULT_PATH,
    SPEC_PATH as TRAJECTORY_SPEC_PATH,
)
from scenesmith.robot_lab.t20_35p_terminal_time_flow_consistency_correction import (
    CORRECTION_EXAMPLE_COUNT,
    OPTIMIZER_UPDATES,
    RECONSTRUCTION_TOLERANCE,
    build_correction_examples,
    build_result,
    build_training_spec,
    verify_result,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_35p_simulation_training_authority import (
    build_owner_grant,
    verify_authority,
    verify_owner_grant,
)


class T2035pTerminalTimeFlowConsistencyCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = TRAJECTORY_RESULT_PATH.parents[2]
        cls.source_spec = load_strict_json(root / SOURCE_SPEC_PATH)
        cls.source_result = load_strict_json(root / SOURCE_RESULT_PATH)
        cls.trajectory_spec = load_strict_json(root / TRAJECTORY_SPEC_PATH)
        cls.trajectory_result = load_strict_json(root / TRAJECTORY_RESULT_PATH)

    def test_exact_fifteen_example_reconstruction(self) -> None:
        examples = build_correction_examples(self.trajectory_result)
        self.assertEqual(len(examples), CORRECTION_EXAMPLE_COUNT)
        self.assertEqual(
            [(row["inference_seed"], row["step_index"]) for row in examples],
            [
                (seed, step)
                for seed in (20260721, 20260722, 20260723, 20260724, 20260725)
                for step in (7, 8, 9)
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
            source_result=self.source_result,
            trajectory_spec=self.trajectory_spec,
            trajectory_result=self.trajectory_result,
        )
        self.assertEqual(spec["campaign"]["optimizer_update_count"], 450)
        self.assertEqual(spec["campaign"]["correction_example_count"], 15)
        self.assertEqual(spec["campaign"]["sample_index_by_update"][:16], list(range(15)) + [0])
        self.assertFalse(spec["closed_loop_rollout"])
        self.assertFalse(spec["external_compute_started"])

    def test_spec_and_source_route_drift_fail_closed(self) -> None:
        spec = self._spec()
        for mutation in (
            lambda value: value["campaign"].update(optimizer_update_count=451),
            lambda value: value["campaign"].update(learning_rate=2.5e-4),
            lambda value: value["campaign"].update(sample_index_by_update=[0] * 450),
            lambda value: value.update(closed_loop_rollout=True),
        ):
            drift = copy.deepcopy(spec)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_training_spec(
                    sign_payload(drift),
                    source_spec=self.source_spec,
                    source_result=self.source_result,
                    trajectory_spec=self.trajectory_spec,
                    trajectory_result=self.trajectory_result,
                )
        route_drift = copy.deepcopy(self.trajectory_result)
        route_drift["gate_b_passed"] = True
        with self.assertRaises(ValueError):
            build_training_spec(
                source_spec=self.source_spec,
                source_result=self.source_result,
                trajectory_spec=self.trajectory_spec,
                trajectory_result=sign_payload(route_drift),
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
            "terminal_objective_pass_action_fail_route_post_training_trajectory_audit",
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
            "action_pass_terminal_objective_fail_route_objective_floor_audit",
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
            source_result=self.source_result,
            trajectory_spec=self.trajectory_spec,
            trajectory_result=self.trajectory_result,
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
        return sign_payload(
            {
                "schema_version": "scenesmith.t20_35p_terminal_time_flow_consistency_run.v1",
                "task_id": "T20.35p",
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
                "example_use_count": [30] * CORRECTION_EXAMPLE_COUNT,
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
                "baseline_objective_by_example": [1.0] * CORRECTION_EXAMPLE_COUNT,
                "final_objective_by_example": [final_objective]
                * CORRECTION_EXAMPLE_COUNT,
                "baseline_standard_objective_by_seed": [
                    spec["source_checkpoint_standard_objective_mean"]
                ]
                * 5,
                "final_standard_objective_by_seed": [final_standard_objective] * 5,
                "per_update_objective": [final_objective] * OPTIMIZER_UPDATES,
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
