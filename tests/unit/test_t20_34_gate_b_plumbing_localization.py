from __future__ import annotations

import copy
import hashlib
import unittest

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, sign_payload
from scenesmith.robot_lab.t20_33_one_batch_memorization import INFERENCE_SEEDS
from scenesmith.robot_lab.t20_34_gate_b_plumbing_localization import build_report, verify_report
from tests.unit.test_t20_33_one_batch_memorization import T2033OneBatchMemorizationTests


class T2034GateBPlumbingLocalizationTests(unittest.TestCase):
    def test_active_but_inconsistent_movement_routes_alignment(self) -> None:
        spec, run, evidence = self._fixtures(adapter_delta=-0.1)
        report = build_report(spec=spec, prior_run=run, evidence=evidence)
        self.assertTrue(report["adapter_active"])
        self.assertEqual(report["selected_next_hypothesis"], "objective_to_inference_alignment")
        verify_report(report, spec=spec, prior_run=run)

    def test_inactive_adapter_routes_checkpoint_plumbing(self) -> None:
        spec, run, evidence = self._fixtures(adapter_delta=0.0)
        evidence["adapter_tensors"][0]["nonzero_count"] = 0
        evidence["adapter_tensors"][0]["l2_norm"] = 0.0
        evidence["adapter_tensors"][0]["maximum_absolute_value"] = 0.0
        report = build_report(spec=spec, prior_run=run, evidence=evidence)
        self.assertFalse(report["adapter_active"])
        self.assertEqual(report["selected_next_hypothesis"], "adapter_checkpoint_plumbing")

    def test_consistent_target_movement_routes_capacity(self) -> None:
        spec, run, evidence = self._fixtures(adapter_delta=0.1)
        report = build_report(spec=spec, prior_run=run, evidence=evidence)
        self.assertTrue(report["every_seed_decoded_error_improved_and_aligned"])
        self.assertEqual(report["selected_next_hypothesis"], "insufficient_gate_b_optimization_or_capacity")

    def test_rejects_seed_hash_source_nonfinite_and_authority_drift(self) -> None:
        spec, run, evidence = self._fixtures(adapter_delta=0.1)
        report = build_report(spec=spec, prior_run=run, evidence=evidence)
        mutations = (
            lambda value: value["evidence"]["adapter_decoded_chunks_rad"].reverse(),
            lambda value: value["evidence"]["adapter_decoded_chunks_rad"][0]["actions"][0].__setitem__(0, 9.0),
            lambda value: value["evidence"]["source_target_action_rad"][0].__setitem__(0, 9.0),
            lambda value: value.update(physical_actuation=True),
        )
        for mutation in mutations:
            drift = copy.deepcopy(report)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_report(sign_payload(drift), spec=spec, prior_run=run)

    @staticmethod
    def _fixtures(adapter_delta: float):
        spec = T2033OneBatchMemorizationTests._spec()
        target = [[1.0] * 6 for _ in range(50)]
        base_actions = [[0.0] * 6 for _ in range(50)]
        adapter_actions = [[adapter_delta] * 6 for _ in range(50)]
        spec["source_batch"]["measured_action_chunk_sha256"] = hashlib.sha256(
            canonical_json_bytes(target)
        ).hexdigest()
        spec = sign_payload(spec)
        run = T2033OneBatchMemorizationTests._run(max_error=abs(1.0 - adapter_delta), final=0.5)
        prior_rows = []
        for seed in INFERENCE_SEEDS:
            digest = hashlib.sha256(canonical_json_bytes(adapter_actions)).hexdigest()
            prior_rows.append({
                "inference_seed": seed,
                "decoded_action_chunk_sha256": digest,
                "mean_absolute_error_rad": abs(1.0 - adapter_delta),
                "maximum_absolute_error_rad": abs(1.0 - adapter_delta),
            })
        run["decoded_action_chunks"] = prior_rows
        run["training_spec_identity_sha256"] = spec["identity_sha256"]
        run["baseline_objective_mean"] = 1.0
        run["final_objective_mean"] = 0.5
        run = sign_payload(run)
        evidence = {
            "source_target_action_rad": target,
            "base_decoded_chunks_rad": [
                {"inference_seed": seed, "actions": base_actions}
                for seed in INFERENCE_SEEDS
            ],
            "adapter_decoded_chunks_rad": [
                {"inference_seed": seed, "actions": adapter_actions}
                for seed in INFERENCE_SEEDS
            ],
            "adapter_tensors": [{
                "name": "lora_B",
                "value_count": 10,
                "nonzero_count": 10,
                "l2_norm": 1.0,
                "maximum_absolute_value": 0.5,
            }],
            "base_objective_mean": 1.0,
            "adapter_objective_mean": 0.5,
        }
        return spec, run, evidence


if __name__ == "__main__":
    unittest.main()
