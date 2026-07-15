from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36b_gate_b_retention_contract import (
    build_checkpoint_evidence,
    build_fixture_artifacts,
    build_retention_decision,
    build_retention_spec,
    verify_retention_decision,
)


class T2036bGateBRetentionContractTests(unittest.TestCase):
    def _evidence(
        self,
        label: str,
        update: int,
        maximum: float,
        *,
        standard_ratio: float = 0.02,
        proxy: float = 0.001,
    ) -> dict:
        return build_checkpoint_evidence(
            checkpoint_label=label,
            optimizer_update_count=update,
            checkpoint_identity_sha256=("a" if update == 0 else "b") * 64,
            standard_objective_ratio=standard_ratio,
            decoded_action_maximum_by_seed=[
                {"inference_seed": seed, "maximum_absolute_error_rad": maximum}
                for seed in range(20260721, 20260726)
            ],
            tracked_proxy_metrics={"weighted_correction_objective": proxy},
        )

    def test_exact_historical_fixture_keeps_only_source_as_rollback(self) -> None:
        spec, evidence, decision = build_fixture_artifacts()
        self.assertTrue(spec["historical_fixture_only"])
        self.assertEqual(len(evidence), 2)
        self.assertEqual(decision["retained_checkpoint_labels"], ["t20_35x_source"])
        self.assertEqual(decision["post_source_retained_checkpoint_labels"], [])
        self.assertEqual(decision["rollback_checkpoint_label"], "t20_35x_source")
        self.assertIsNone(decision["selected_coverage_checkpoint_label"])
        self.assertEqual(
            decision["decision"],
            "only_source_checkpoint_retains_gate_b_no_coverage_candidate",
        )

    def test_post_source_pass_is_candidate_but_does_not_open_gate_c(self) -> None:
        source = self._evidence("source", 0, 0.04)
        candidate = self._evidence("candidate", 100, 0.049)
        spec = build_retention_spec(
            evidence_rows=[source, candidate],
            source_checkpoint_label="source",
            historical_fixture_only=False,
            schedule_registration_boundary_sha256="c" * 64,
        )
        decision = build_retention_decision(spec=spec, evidence_rows=[source, candidate])
        self.assertEqual(decision["selected_coverage_checkpoint_label"], "candidate")
        self.assertEqual(
            decision["decision"],
            "post_source_checkpoint_retains_gate_b_candidate_available",
        )
        self.assertFalse(decision["gate_c_authorized"])
        self.assertFalse(decision["optimizer_training_authorized"])

    def test_no_pass_and_proxy_only_candidate_fail_closed(self) -> None:
        source = self._evidence("source", 0, 0.06, standard_ratio=0.2)
        candidate = self._evidence("candidate", 100, 0.06, proxy=0.0)
        spec = build_retention_spec(
            evidence_rows=[source, candidate],
            source_checkpoint_label="source",
            historical_fixture_only=False,
            schedule_registration_boundary_sha256="c" * 64,
        )
        decision = build_retention_decision(spec=spec, evidence_rows=[source, candidate])
        self.assertEqual(decision["retained_checkpoint_labels"], [])
        self.assertEqual(decision["decision"], "no_checkpoint_retains_gate_b")
        self.assertTrue(decision["proxy_metrics_ignored_for_gate_b"])

    def test_missing_duplicate_reordered_changed_stale_and_nonfinite_fail(self) -> None:
        with self.assertRaises(ValueError):
            build_checkpoint_evidence(
                checkpoint_label="missing",
                optimizer_update_count=0,
                checkpoint_identity_sha256="a" * 64,
                standard_objective_ratio=0.02,
                decoded_action_maximum_by_seed=[
                    {"inference_seed": seed, "maximum_absolute_error_rad": 0.04}
                    for seed in range(20260721, 20260725)
                ],
                tracked_proxy_metrics={},
            )
        source = self._evidence("source", 0, 0.04)
        candidate = self._evidence("candidate", 100, 0.06)
        with self.assertRaises(ValueError):
            build_retention_spec(
                evidence_rows=[source, source],
                source_checkpoint_label="source",
                historical_fixture_only=False,
                schedule_registration_boundary_sha256="c" * 64,
            )
        spec = build_retention_spec(
            evidence_rows=[source, candidate],
            source_checkpoint_label="source",
            historical_fixture_only=False,
            schedule_registration_boundary_sha256="c" * 64,
        )
        with self.assertRaises(ValueError):
            build_retention_decision(spec=spec, evidence_rows=[candidate, source])
        changed = copy.deepcopy(spec)
        changed["maximum_action_error_rad"] = 0.06
        with self.assertRaises(ValueError):
            build_retention_decision(
                spec=sign_payload(changed), evidence_rows=[source, candidate]
            )
        stale = copy.deepcopy(candidate)
        stale["standard_objective_ratio"] = 0.01
        with self.assertRaises(ValueError):
            build_retention_decision(
                spec=spec, evidence_rows=[source, sign_payload(stale)]
            )
        with self.assertRaises(ValueError):
            self._evidence("bad", 100, float("nan"))

    def test_signed_decision_tamper_and_all_authority_escalation_fail(self) -> None:
        spec, evidence, decision = build_fixture_artifacts()
        drift = copy.deepcopy(decision)
        drift["selected_coverage_checkpoint_label"] = "t20_35x_source"
        with self.assertRaises(ValueError):
            verify_retention_decision(
                sign_payload(drift), spec=spec, evidence_rows=evidence
            )
        for field in (
            "checkpoint_read",
            "model_loaded",
            "model_inference",
            "optimizer_created",
            "optimizer_training",
            "optimizer_training_authorized",
            "campaign_authorized",
            "gate_b_threshold_changed",
            "gate_c_authorized",
            "closed_loop_rollout",
            "simulation_policy_accepted",
            "physical_actuation",
            "external_compute_started",
            "brev_compute_started",
            "physical_transfer_ready",
            "promotion_eligible",
        ):
            self.assertFalse(decision[field])


if __name__ == "__main__":
    unittest.main()
