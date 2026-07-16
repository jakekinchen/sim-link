from __future__ import annotations

import copy
import hashlib
import math
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (
    EVALUATION_UPDATE_SCHEDULE,
    EXPECTED_BATCH_EVIDENCE,
    EXPECTED_DEPENDENCY_VERSIONS,
    build_attempt_marker,
    build_evaluation_row,
    build_result,
    build_run_summary,
    build_runtime_preflight,
    build_training_permit,
    load_verified_spec,
    verify_result,
    verify_run_summary,
    verify_runtime_preflight,
    verify_training_permit,
)


class T2036eExactActGateBControlTests(unittest.TestCase):
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
            batch_evidence=EXPECTED_BATCH_EVIDENCE,
            source_commit="c" * 40,
            remote_source_commit="c" * 40,
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

    def test_runtime_and_permit_bind_exact_local_boundary(self) -> None:
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
        self.assertEqual(self.permit["authorized_attempt_count"], 1)
        self.assertTrue(self.permit["attempt_marker_must_precede_model_construction"])
        self.assertEqual(
            self.runtime["batch_evidence"]["physical_action_chunk_sha256"],
            EXPECTED_BATCH_EVIDENCE["physical_action_chunk_sha256"],
        )
        self.assertFalse(self.runtime["model_constructed"])

    def test_runtime_fails_closed_on_target_mps_attempt_or_remote_drift(self) -> None:
        variants = []
        for field, value in (
            ("mps_available", False),
            ("attempt_exists", True),
            ("run_exists", True),
        ):
            values = self._runtime_kwargs()
            values[field] = value
            variants.append(values)
        target = self._runtime_kwargs()
        target["batch_evidence"]["physical_action_chunk_sha256"] = "0" * 64
        variants.append(target)
        remote = self._runtime_kwargs()
        remote["remote_source_commit"] = "e" * 40
        variants.append(remote)
        for values in variants:
            with self.assertRaises(ValueError):
                build_runtime_preflight(
                    spec=self.spec,
                    authority_identity=self.authority,
                    **values,
                )

    def test_pass_run_stops_at_first_passing_checkpoint(self) -> None:
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
        self.assertEqual(result["decision"], "act_control_gate_b_pass")
        self.assertTrue(result["shared_batch_and_normalization_control_passed"])
        self.assertTrue(result["smolvla_entry_design_routed"])
        self.assertFalse(result["policy_track_selected"])

    def test_fail_run_requires_full_schedule_and_no_nondeterminism(self) -> None:
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
        self.assertEqual(result["decision"], "act_control_gate_b_fail")
        self.assertFalse(result["smolvla_entry_design_routed"])
        truncated = copy.deepcopy(evaluations[:-1])
        with self.assertRaises(ValueError):
            self._run(1000, truncated)
        nondeterministic = copy.deepcopy(evaluations)
        nondeterministic[-1]["repetitions"][1]["action_chunk_sha256"] = "f" * 64
        nondeterministic[-1] = sign_payload(nondeterministic[-1])
        with self.assertRaises(ValueError):
            self._run(2000, nondeterministic)

    def test_nonfinite_gate_or_authority_tamper_rejects(self) -> None:
        evaluations = [
            self._evaluation(0, objective=1.0, maximum_error=0.8),
            self._evaluation(100, objective=0.05, maximum_error=0.01),
        ]
        with self.assertRaises(ValueError):
            build_evaluation_row(
                optimizer_update_count=100,
                supervised_objective_mean=math.nan,
                baseline_objective_mean=1.0,
                repetition_rows=self._repetitions(0.01),
            )
        run = self._run(100, evaluations)
        result = build_result(spec=self.spec, run=run)
        drift = copy.deepcopy(result)
        drift["gate_c_authorized"] = True
        with self.assertRaises(ValueError):
            verify_result(sign_payload(drift), spec=self.spec, run=run)

    def _runtime_kwargs(self):
        return {
            "python_major_minor": [3, 12],
            "dependency_versions": copy.deepcopy(EXPECTED_DEPENDENCY_VERSIONS),
            "mps_available": True,
            "lerobot_stack_identity_sha256": "b" * 64,
            "free_disk_bytes": 8 * 1024 * 1024 * 1024,
            "batch_evidence": copy.deepcopy(EXPECTED_BATCH_EVIDENCE),
            "source_commit": "c" * 40,
            "remote_source_commit": "c" * 40,
            "attempt_exists": False,
            "run_exists": False,
            "result_exists": False,
        }

    def _repetitions(self, maximum_error: float):
        return [
            {
                "repetition_index": index,
                "action_chunk_sha256": "e" * 64,
                "mean_absolute_error_rad": maximum_error / 2,
                "maximum_absolute_error_rad": maximum_error,
            }
            for index in range(5)
        ]

    def _evaluation(self, update: int, *, objective: float, maximum_error: float):
        return build_evaluation_row(
            optimizer_update_count=update,
            supervised_objective_mean=objective,
            baseline_objective_mean=1.0,
            repetition_rows=self._repetitions(maximum_error),
        )

    def _run(self, updates: int, evaluations):
        checkpoint_tree = [
            {"path": "config.json", "size_bytes": 100, "sha256": "1" * 64},
            {
                "path": "model.safetensors",
                "size_bytes": 1000,
                "sha256": "2" * 64,
            },
        ]
        return build_run_summary(
            spec=self.spec,
            authority_identity=self.authority,
            training_permit=self.permit,
            attempt=self.attempt,
            optimizer_update_count=updates,
            per_update_objective=[0.5] * updates,
            gradient_norms_before_clip=[1.0] * updates,
            evaluations=evaluations,
            checkpoint_tree=checkpoint_tree,
            checkpoint_identity_sha256=hashlib.sha256(
                canonical_json_bytes(checkpoint_tree)
            ).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
