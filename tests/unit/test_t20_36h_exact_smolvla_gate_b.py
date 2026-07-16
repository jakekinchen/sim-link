from __future__ import annotations

import copy
import math
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (
    EXPECTED_BATCH_EVIDENCE,
)
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (
    EVALUATION_UPDATE_SCHEDULE,
    EXPECTED_DEPENDENCY_VERSIONS,
    INFERENCE_SEEDS,
    OBJECTIVE_SEEDS,
    build_attempt_marker,
    build_evaluation_row,
    build_failure,
    build_failure_result,
    build_result,
    build_run_summary,
    build_runtime_preflight,
    build_training_permit,
    load_verified_spec,
    verify_result,
    verify_run_summary,
    verify_runtime_preflight,
    verify_training_permit,
    verify_failure,
    verify_failure_result,
)
from scripts.robot_lab.run_t20_36h_exact_smolvla_gate_b import _build_config


class T2036hExactSmolVLAGateBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = load_verified_spec()
        cls.authority = "a" * 64
        cls.runtime = build_runtime_preflight(
            spec=cls.spec,
            authority_identity=cls.authority,
            python_major_minor=[3, 12],
            dependency_versions=EXPECTED_DEPENDENCY_VERSIONS,
            mps_available=True,
            lerobot_stack_identity_sha256="b" * 64,
            free_disk_bytes=8 * 1024 * 1024 * 1024,
            batch_evidence=copy.deepcopy(EXPECTED_BATCH_EVIDENCE),
            checkpoint_tree=cls._source_checkpoints(cls.spec),
            source_commit="c" * 40,
            remote_source_commit="c" * 40,
            branch="codex/pi05-autolearn-loop",
            scoped_dirty_paths=[],
            attempt_exists=False,
            run_exists=False,
            result_exists=False,
        )
        cls.permit = build_training_permit(
            spec=cls.spec,
            authority_identity=cls.authority,
            runtime_preflight=cls.runtime,
        )
        cls.attempt = build_attempt_marker(
            spec=cls.spec,
            authority_identity=cls.authority,
            training_permit=cls.permit,
            source_commit="d" * 40,
        )

    def test_preflight_binds_exact_checkpoints_batch_mps_and_remote(self) -> None:
        verify_runtime_preflight(
            self.runtime,
            spec=self.spec,
            authority_identity=self.authority,
        )
        verify_training_permit(
            self.permit,
            spec=self.spec,
            authority_identity=self.authority,
            runtime_preflight=self.runtime,
        )
        self.assertEqual(len(self.runtime["checkpoint_tree"]), 4)
        self.assertTrue(self.runtime["checkpoint_content_read_as_raw_bytes"])
        self.assertFalse(self.runtime["checkpoint_tensor_deserialized"])
        self.assertTrue(self.permit["smoke_failure_consumes_attempt"])

    def test_preflight_rejects_checkpoint_camera_remote_or_dirty_drift(self) -> None:
        for mutation in ("checkpoint", "camera", "remote", "dirty"):
            values = self._runtime_kwargs()
            if mutation == "checkpoint":
                values["checkpoint_tree"][0]["size_bytes"] += 1
            elif mutation == "camera":
                values["batch_evidence"]["image_tensor_sha256"][
                    "observation.images.base_0_rgb"
                ] = "0" * 64
            elif mutation == "remote":
                values["remote_source_commit"] = "e" * 40
            else:
                values["scoped_dirty_paths"] = ["runner.py"]
            with self.assertRaises(ValueError):
                build_runtime_preflight(
                    spec=self.spec,
                    authority_identity=self.authority,
                    **values,
                )

    def test_passing_run_stops_at_first_passing_checkpoint(self) -> None:
        evaluations = [
            self._evaluation(0, objective=1.0, maximum_error=0.8),
            self._evaluation(100, objective=0.05, maximum_error=0.01),
        ]
        run = self._run(100, evaluations)
        verify_run_summary(
            run,
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
        )
        result = build_result(spec=self.spec, run=run)
        verify_result(result, spec=self.spec, run=run)
        self.assertEqual(result["decision"], "smolvla_gate_b_pass")
        self.assertTrue(result["gate_c_design_routed"])
        self.assertFalse(result["policy_track_selected"])

    def test_failed_run_requires_full_schedule_and_deterministic_seeds(self) -> None:
        evaluations = [
            self._evaluation(
                update,
                objective=1.0 if update == 0 else 0.2,
                maximum_error=0.1,
            )
            for update in EVALUATION_UPDATE_SCHEDULE
        ]
        run = self._run(2000, evaluations)
        result = build_result(spec=self.spec, run=run)
        self.assertEqual(result["decision"], "smolvla_gate_b_fail")
        with self.assertRaises(ValueError):
            self._run(1000, evaluations[:-1])
        nondeterministic = copy.deepcopy(evaluations[:-1])
        rows = self._inference_rows(0.1)
        rows[0]["second_action_chunk_sha256"] = "f" * 64
        nondeterministic.append(
            build_evaluation_row(
                optimizer_update_count=2000,
                supervised_objective_by_seed=[0.2] * len(OBJECTIVE_SEEDS),
                baseline_objective_mean=1.0,
                inference_rows=rows,
            )
        )
        failed = self._run(2000, nondeterministic)
        self.assertFalse(failed["gate_b_passed"])

    def test_nonfinite_or_authority_escalation_rejects(self) -> None:
        with self.assertRaises(ValueError):
            build_evaluation_row(
                optimizer_update_count=100,
                supervised_objective_by_seed=[math.nan] * len(OBJECTIVE_SEEDS),
                baseline_objective_mean=1.0,
                inference_rows=self._inference_rows(0.01),
            )
        run = self._run(
            100,
            [
                self._evaluation(0, objective=1.0, maximum_error=0.8),
                self._evaluation(100, objective=0.05, maximum_error=0.01),
            ],
        )
        drift = copy.deepcopy(run)
        drift["gate_c_authorized"] = True
        drift = sign_payload(drift)
        with self.assertRaises(ValueError):
            build_result(spec=self.spec, run=drift)

    def test_runtime_config_has_only_two_real_cameras_and_exact_vlm_path(self) -> None:
        from lerobot.configs.types import (
            FeatureType,
            NormalizationMode,
            PolicyFeature,
        )
        from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig

        config = _build_config(
            self.spec,
            SmolVLAConfig,
            FeatureType,
            NormalizationMode,
            PolicyFeature,
        )
        self.assertEqual(config.empty_cameras, 0)
        self.assertEqual(
            list(config.image_features),
            [
                "observation.images.base_0_rgb",
                "observation.images.left_wrist_0_rgb",
            ],
        )
        self.assertEqual(
            config.vlm_model_name,
            self.spec["local_cache"]["vlm_snapshot"],
        )

    def test_counted_runtime_failure_is_signed_and_cannot_grant_retry(self) -> None:
        failure = build_failure(
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
            failure_stage="runtime_smoke",
            error_type="RuntimeError",
            error_message="bounded smoke failure",
            optimizer_update_count=0,
            model_constructed=True,
            model_loaded=True,
            model_inference=False,
            optimizer_created=False,
            optimizer_training=False,
        )
        verify_failure(
            failure,
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
        )
        self.assertTrue(failure["attempt_consumed"])
        self.assertFalse(failure["retry_or_sweep_allowed"])
        result = build_failure_result(
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
            failure=failure,
        )
        verify_failure_result(
            result,
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
            failure=failure,
        )
        self.assertFalse(result["smolvla_gate_b_evaluated"])
        self.assertFalse(result["retry_or_sweep_allowed"])

    def _runtime_kwargs(self):
        return {
            "python_major_minor": [3, 12],
            "dependency_versions": copy.deepcopy(EXPECTED_DEPENDENCY_VERSIONS),
            "mps_available": True,
            "lerobot_stack_identity_sha256": "b" * 64,
            "free_disk_bytes": 8 * 1024 * 1024 * 1024,
            "batch_evidence": copy.deepcopy(EXPECTED_BATCH_EVIDENCE),
            "checkpoint_tree": self._source_checkpoints(self.spec),
            "source_commit": "c" * 40,
            "remote_source_commit": "c" * 40,
            "branch": "codex/pi05-autolearn-loop",
            "scoped_dirty_paths": [],
            "attempt_exists": False,
            "run_exists": False,
            "result_exists": False,
        }

    @staticmethod
    def _source_checkpoints(spec):
        rows = []
        for group in ("policy", "vlm"):
            for row in spec["local_cache"][f"{group}_files"]:
                if row["is_weight_or_tensor_file"]:
                    rows.append(
                        {
                            "path": f"{group}/{row['name']}",
                            "size_bytes": row["size_bytes"],
                            "sha256": "1" * 64,
                        }
                    )
        return rows

    @staticmethod
    def _runtime_smoke():
        return {
            "processed_action_shape": [1, 50, 6],
            "processed_state_shape": [1, 6],
            "processed_image_keys": [
                "observation.images.base_0_rgb",
                "observation.images.left_wrist_0_rgb",
            ],
            "parameter_inventory": [
                {"device": "mps:0", "dtype": "torch.float32", "numel": 1000}
            ],
            "buffer_inventory": [],
            "trainable_parameter_inventory": [
                {
                    "name": "model.vlm_with_expert.lm_expert.layer.weight",
                    "device": "mps:0",
                    "dtype": "torch.float32",
                    "numel": 100,
                },
                {
                    "name": "model.state_proj.weight",
                    "device": "mps:0",
                    "dtype": "torch.float32",
                    "numel": 100,
                },
                *[
                    {
                        "name": f"model.{name}.weight",
                        "device": "mps:0",
                        "dtype": "torch.float32",
                        "numel": 100,
                    }
                    for name in (
                        "action_in_proj",
                        "action_out_proj",
                        "action_time_mlp_in",
                        "action_time_mlp_out",
                    )
                ],
            ],
            "smoke_loss": 1.0,
            "smoke_gradient_norm": 2.0,
            "mps_forward_backward_passed": True,
            "cpu_fallback_observed": False,
        }

    @staticmethod
    def _inference_rows(maximum_error):
        return [
            {
                "seed_index": index,
                "inference_seed": seed,
                "first_action_chunk_sha256": f"{index + 2}" * 64,
                "second_action_chunk_sha256": f"{index + 2}" * 64,
                "repeat_maximum_absolute_difference_rad": 0.0,
                "mean_absolute_error_rad": maximum_error / 2,
                "maximum_absolute_error_rad": maximum_error,
            }
            for index, seed in enumerate(INFERENCE_SEEDS)
        ]

    def _evaluation(self, update, *, objective, maximum_error):
        return build_evaluation_row(
            optimizer_update_count=update,
            supervised_objective_by_seed=[objective] * len(OBJECTIVE_SEEDS),
            baseline_objective_mean=1.0,
            inference_rows=self._inference_rows(maximum_error),
        )

    def _run(self, updates, evaluations):
        checkpoint_tree = [
            {"path": "config.json", "size_bytes": 100, "sha256": "1" * 64},
            {
                "path": "model.safetensors",
                "size_bytes": 1000,
                "sha256": "2" * 64,
            },
            {
                "path": "policy_preprocessor.json",
                "size_bytes": 100,
                "sha256": "3" * 64,
            },
            {
                "path": "policy_postprocessor.json",
                "size_bytes": 100,
                "sha256": "4" * 64,
            },
        ]
        return build_run_summary(
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
            runtime_smoke=self._runtime_smoke(),
            optimizer_update_count=updates,
            per_update_objective=[0.5] * updates,
            gradient_norms_before_clip=[1.0] * updates,
            evaluations=evaluations,
            checkpoint_tree=checkpoint_tree,
        )


if __name__ == "__main__":
    unittest.main()
