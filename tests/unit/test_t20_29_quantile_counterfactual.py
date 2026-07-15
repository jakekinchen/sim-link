from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_26_frame_zero_variability import SAMPLE_SCHEDULE
from scenesmith.robot_lab.t20_29_quantile_counterfactual import (
    build_counterfactual,
    verify_counterfactual,
)


class T2029QuantileCounterfactualTests(unittest.TestCase):
    def test_counterfactual_accounts_for_shift_without_training_claim(self) -> None:
        payload = self._payload()
        self.assertTrue(
            payload["result"].startswith("postprocessor_quantile_shift_accounts")
        )
        self.assertFalse(payload["full_training_effect_isolated"])
        self.assertFalse(payload["optimizer_training"])

    def test_rejects_zero_span_reorder_and_signed_mutation(self) -> None:
        stats = self._stats(0.0, 1.0)
        stats["q99"][0] = 0.0
        with self.assertRaisesRegex(ValueError, "span"):
            self._payload(clean_stats=stats)
        batches = self._batches()
        batches["clean_base"]["samples"].reverse()
        with self.assertRaisesRegex(ValueError, "order"):
            self._payload(batches=batches)
        payload = self._payload()
        mutation = copy.deepcopy(payload)
        mutation["optimizer_training"] = True
        mutation = sign_payload(mutation)
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_counterfactual(
                mutation,
                batches=self._batches(),
                source_action_rad=[0.0] * 6,
                clean_stats=self._stats(0.0, 1.0),
                recovery_stats=self._stats(0.2, 1.2),
                **self._evidence(),
            )

    def test_rejects_evidence_candidate_and_joint_substitution(self) -> None:
        payload = self._payload()
        mutation = copy.deepcopy(payload)
        mutation["formula_source_sha256"] = "9" * 64
        mutation = sign_payload(mutation)
        with self.assertRaisesRegex(ValueError, "drifted"):
            self._verify(mutation)

        batches = self._batches()
        batches["clean_base"]["samples"][0]["requested_action_rad"] = [0.0] * 5
        with self.assertRaisesRegex(ValueError, "six-vector"):
            self._payload(batches=batches)

        batches = self._batches()
        batches["substituted_candidate"] = batches.pop("clean_base")
        with self.assertRaisesRegex(ValueError, "candidate coverage"):
            self._payload(batches=batches)

    def _verify(self, payload):
        verify_counterfactual(
            payload,
            batches=self._batches(),
            source_action_rad=[0.0] * 6,
            clean_stats=self._stats(0.0, 1.0),
            recovery_stats=self._stats(0.2, 1.2),
            **self._evidence(),
        )

    def _payload(self, *, batches=None, clean_stats=None):
        return build_counterfactual(
            batches=batches or self._batches(),
            source_action_rad=[0.0] * 6,
            clean_stats=clean_stats or self._stats(0.0, 1.0),
            recovery_stats=self._stats(0.2, 1.2),
            **self._evidence(),
        )

    @staticmethod
    def _evidence():
        return {
            "clean_stats_sha256": "a" * 64,
            "recovery_stats_sha256": "b" * 64,
            "clean_postprocessor_config_sha256": "c" * 64,
            "recovery_postprocessor_config_sha256": "d" * 64,
            "clean_postprocessor_state_sha256": "e" * 64,
            "recovery_postprocessor_state_sha256": "f" * 64,
            "formula_source_sha256": "1" * 64,
            "t20_27_gate_identity_sha256": "2" * 64,
            "observed_recovery_minus_clean_mae_rad": 0.0035,
        }

    @staticmethod
    def _batches():
        return {
            candidate: {
                "samples": [
                    {
                        "sample_id": sample_id,
                        "mode": mode,
                        "inference_seed": seed,
                        "requested_action_rad": [0.0] * 6,
                    }
                    for sample_id, mode, seed in SAMPLE_SCHEDULE
                ]
            }
            for candidate in ("clean_base", "recovery_augmented")
        }

    @staticmethod
    def _stats(low: float, high: float):
        return {"q01": [low] * 6, "q99": [high] * 6}


if __name__ == "__main__":
    unittest.main()
