from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.f0_release_gap_diagnosis import (
    PHASE_PLAN,
    analyze_normalization,
    analyze_sampler,
    build_release_gap_diagnosis,
    derive_physical_l1_weights,
    reconstruct_sampler_batches,
    verify_release_gap_diagnosis,
)


class F0ReleaseGapDiagnosisTests(unittest.TestCase):
    def test_sampler_reconstruction_is_deterministic_and_tail_padded(self) -> None:
        batches_a, epochs_a = reconstruct_sampler_batches(
            [244], seed=17, batch_size=8, update_count=31
        )
        batches_b, epochs_b = reconstruct_sampler_batches(
            [244], seed=17, batch_size=8, update_count=31
        )
        self.assertEqual(batches_a, batches_b)
        self.assertEqual(epochs_a, epochs_b)
        analysis = analyze_sampler([244], batches_a)
        self.assertEqual(analysis["sampled_start_count"], 244)
        self.assertEqual(analysis["target_exposure_by_frame"][243], 50)
        self.assertEqual(analysis["median_target_exposure_frames_50_199"], 50)
        self.assertEqual(analysis["frame_200_valid_length_histogram"], {"44": 1})
        self.assertFalse(analysis["tail_coverage_defect"])

    def test_r0_normalization_falsifies_old_envelope_hypothesis(self) -> None:
        rows = self._late_rows()
        stats = self._action_stats()
        result = analyze_normalization(stats, rows)
        self.assertTrue(result["required_open_inside_r0_envelope"])
        self.assertLess(result["required_open_z_score"], 1.5)
        self.assertFalse(result["normalization_defect"])
        old = copy.deepcopy(stats)
        old["max"][5] = 81.0264
        self.assertTrue(analyze_normalization(old, rows)["normalization_defect"])

    def test_physical_l1_weight_exposes_gripper_underweight(self) -> None:
        weighting = derive_physical_l1_weights(self._action_stats()["std"])
        self.assertAlmostEqual(weighting["active_joint_coefficient_mean"], 1.0)
        self.assertAlmostEqual(weighting["gripper_coefficient"], 2.6963081473868007)
        self.assertTrue(weighting["gripper_weighting_mechanism_eligible"])

    def test_signed_result_routes_delay_to_fresh_model_free_audit(self) -> None:
        result = self._result()
        verify_release_gap_diagnosis(result)
        self.assertFalse(result["findings"]["tail_coverage_defect"])
        self.assertFalse(result["findings"]["normalization_defect"])
        self.assertFalse(result["findings"]["release_mixture_underweight_defect"])
        self.assertTrue(result["findings"]["gripper_physical_l1_underweight_supported"])
        self.assertTrue(
            result["findings"]["twenty_frame_release_sequence_delay_counterexample"]
        )
        self.assertEqual(
            result["selected_route"],
            "open_fresh_model_free_chunk_timing_and_phase_observability_audit",
        )
        self.assertFalse(result["corrective_training_selected"])
        self.assertEqual(result["training_lock"], "closed")

    def test_drift_and_authority_mutations_fail(self) -> None:
        result = self._result()
        for field, value in (
            ("selected_route", "propose_training"),
            ("optimizer_created", True),
            ("corrective_training_selected", True),
            ("training_lock", "open"),
        ):
            drift = copy.deepcopy(result)
            drift[field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    verify_release_gap_diagnosis(sign_payload(drift))
        bad_lengths = copy.deepcopy(result)
        bad_lengths["input_evidence"]["episode_lengths"][0] = 245
        with self.assertRaises(ValueError):
            verify_release_gap_diagnosis(sign_payload(bad_lengths))

    def _result(self):
        return build_release_gap_diagnosis(
            source_refs=[
                {
                    "label": "fixture",
                    "path": "fixture.json",
                    "file_sha256": "1" * 64,
                    "size_bytes": 1,
                }
            ],
            source_semantics={
                "act_loss_masks_action_is_pad": True,
                "dataset_reader_clamps_and_marks_tail_padding": True,
                "episode_aware_sampler_covers_all_episode_frames": True,
                "phase_plan_matches_frozen_244_frames": True,
                "r2_runner_uses_delta_timestamps_0_through_49": True,
                "r2_runner_uses_episode_aware_sampler": True,
                "r2_spec_has_no_sample_weighting": True,
                "standalone_unpadded_index_not_consumed_by_runner": True,
            },
            episode_lengths=[244],
            unpadded_horizon_50_start_histogram={str(index): 1 for index in range(112, 127)},
            action_statistics=self._action_stats(),
            late_rollout_evidence=self._late_rows(),
            failed_gate_names=["release_final_contact_clear"],
        )

    @staticmethod
    def _action_stats():
        return {
            "min": [2.328871488571167, 9.688922882080078, -31.66107177734375, -11.638205528259277, -1.708101749420166, 22.073326110839844],
            "max": [2.889882802963257, 105.75819396972656, -1.0937222242355347, 59.728057861328125, 91.67324829101562, 92.43017578125],
            "mean": [2.6095025491510775, 92.26261373591771, -24.800576567277382, -7.0730842961452005, 87.82986620218483, 47.30410281220679],
            "std": [0.17685739363531575, 14.975893115165848, 5.558689790400484, 9.57219818572664, 12.626469272630263, 31.837386095890416],
        }

    @staticmethod
    def _late_rows():
        phases = [phase for phase, count in PHASE_PLAN for _ in range(count)][200:244]
        source_release = [
            0.2758242811922214,
            0.349303,
            0.460302,
            0.599442,
            0.757343,
            0.924623,
            1.091904,
            1.249805,
            1.388945,
            1.499944,
            1.573423,
            1.6,
        ]
        source = source_release + [1.6] * 32
        candidate = [0.24] * 20 + source_release + [1.6] * 12
        return [
            {
                "frame_index": 200 + offset,
                "phase": phase,
                "source_gripper_rad": source[offset],
                "candidate_gripper_rad": candidate[offset],
                "candidate_strict_contact": offset < 20,
            }
            for offset, phase in enumerate(phases)
        ]


if __name__ == "__main__":
    unittest.main()
