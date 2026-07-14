from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_28_sampler_exposure_audit import build_audit, verify_audit


class T2028SamplerExposureAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clean = [{"source_class": "nominal", "phases": ["approach"] * 250}]
        self.recovery = [
            {"source_class": "nominal", "phases": ["approach"] * 300},
            {"source_class": "recovery", "phases": ["close"] * 300},
        ]

    def test_audit_rejects_lower_exposure_hypothesis_without_authority(self) -> None:
        audit = self._audit()
        self.assertFalse(audit["recovery_early_phase_exposure_lower_than_clean"])
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "audit_recovery_dataset_quantile_and_postprocessor_shift",
        )
        self.assertFalse(audit["optimizer_training"])

    def test_audit_rejects_duplicate_range_mutation_and_authority(self) -> None:
        audit = self._audit()
        duplicate = list(range(249)) + [0]
        with self.assertRaisesRegex(ValueError, "duplicated"):
            build_audit(
                sampler_source_sha256="a" * 64,
                sampler_schema="lerobot.datasets.sampler.EpisodeAwareSampler",
                clean_indices=duplicate,
                recovery_indices=list(range(500)),
                clean_episodes=self.clean,
                recovery_episodes=self.recovery,
                clean_seed=1,
                recovery_seed=1,
            )
        mutation = copy.deepcopy(audit)
        mutation["campaigns"]["clean_base"]["approach_count"] = 0
        mutation = sign_payload(mutation)
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_audit(mutation, clean_episodes=self.clean, recovery_episodes=self.recovery)
        authority = copy.deepcopy(audit)
        authority["optimizer_training"] = True
        authority = sign_payload(authority)
        with self.assertRaisesRegex(ValueError, "drifted|authority"):
            verify_audit(authority, clean_episodes=self.clean, recovery_episodes=self.recovery)

    def _audit(self) -> dict:
        return build_audit(
            sampler_source_sha256="a" * 64,
            sampler_schema="lerobot.datasets.sampler.EpisodeAwareSampler",
            clean_indices=list(range(250)),
            recovery_indices=list(range(500)),
            clean_episodes=self.clean,
            recovery_episodes=self.recovery,
            clean_seed=1,
            recovery_seed=1,
        )


if __name__ == "__main__":
    unittest.main()
