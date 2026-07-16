import unittest

from datetime import datetime

from scenesmith.robot_lab.t20_36o_baseline_inference_authority import (
    AUTHORIZED_ACTIONS,
    VALID_FROM,
    VALID_UNTIL,
    build_owner_grant,
    build_production_authority,
    load_verified_sources,
    verify_owner_grant,
)


class T2036oBaselineInferenceAuthorityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_verified_sources()

    def test_owner_grant_is_one_load_baseline_inference_only(self) -> None:
        grant = build_owner_grant(sources=self.sources)
        verify_owner_grant(grant, sources=self.sources)
        self.assertEqual(grant["authorized_actions"], list(AUTHORIZED_ACTIONS))
        self.assertEqual(grant["authorized_attempt_count"], 1)
        self.assertEqual(grant["chunk_start_count"], 5)
        self.assertEqual(grant["inference_seed_count_per_start"], 5)
        self.assertEqual(grant["repeats_per_start_seed"], 2)
        self.assertEqual(grant["decoded_chunk_count"], 50)
        self.assertEqual(grant["denoise_step_record_count"], 500)
        self.assertFalse(grant["optimizer_authorized"])
        self.assertFalse(grant["gate_c_authorized"])

    def test_authority_window_is_exactly_eight_hours(self) -> None:
        start = datetime.fromisoformat(VALID_FROM)
        stop = datetime.fromisoformat(VALID_UNTIL)
        self.assertEqual((stop - start).total_seconds(), 8 * 60 * 60)

    def test_central_composer_grants_only_generic_simulation_readiness(self) -> None:
        request, decision = build_production_authority(
            sources=self.sources,
            owner=build_owner_grant(sources=self.sources),
        )
        self.assertEqual(decision["authority_granted"], ["simulation_training_ready"])
        self.assertNotIn("physical_transfer_ready", decision["authority_granted"])
        self.assertNotIn("promotion_eligible", decision["authority_granted"])
        self.assertEqual(decision["request_identity_sha256"], request["identity_sha256"])


if __name__ == "__main__":
    unittest.main()
