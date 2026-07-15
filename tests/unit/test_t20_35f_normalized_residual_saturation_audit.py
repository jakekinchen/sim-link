from __future__ import annotations

import copy
import math
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco
from scenesmith.robot_lab.t20_35f_normalized_residual_saturation_audit import (
    build_audit,
    verify_audit,
)


class T2035FNormalizedResidualSaturationAuditTests(unittest.TestCase):
    def test_systematic_normalized_bias_routes_denoising_cadence(self) -> None:
        correction, report, stats, sources = self._sources(
            wrist_errors=[0.08] * 5,
            gripper_errors=[0.07] * 5,
        )
        audit = build_audit(
            correction=correction,
            report=report,
            action_stats=stats,
            source_contract=sources,
        )
        self.assertFalse(audit["hard_saturation_detected"])
        self.assertTrue(audit["all_selected_channels_systematic_bias_dominant"])
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "gate_b_inference_denoising_cadence_discriminator",
        )
        self.assertEqual(
            [row["physical_threshold_exceedance_count"] for row in audit["channel_audits"]],
            [250, 250],
        )
        verify_audit(
            audit,
            correction=correction,
            report=report,
            action_stats=stats,
            source_contract=sources,
        )

    def test_seed_variance_and_bound_hit_routes_remain_distinct(self) -> None:
        correction, report, stats, sources = self._sources(
            wrist_errors=[-0.08, 0.08, -0.08, 0.08, 0.0],
            gripper_errors=[-0.07, 0.07, -0.07, 0.07, 0.0],
        )
        noisy = build_audit(
            correction=correction,
            report=report,
            action_stats=stats,
            source_contract=sources,
        )
        self.assertEqual(
            noisy["selected_next_hypothesis"],
            "gate_b_seed_noise_stability_discriminator",
        )

        clipped_report = copy.deepcopy(report)
        bound = lerobot_to_mujoco([0.0, 0.0, 0.0, 0.0, 0.0, 100.0])[5]
        clipped_report["replayed_chunks"][0]["decoded_action_chunk"][0][5] = bound
        clipped_report = sign_payload(clipped_report)
        clipped_correction = copy.deepcopy(correction)
        clipped_correction["source_t20_35d_report_identity_sha256"] = clipped_report[
            "identity_sha256"
        ]
        clipped_correction = sign_payload(clipped_correction)
        clipped_sources = copy.deepcopy(sources)
        clipped_sources["t20_35d_report_identity_sha256"] = clipped_report[
            "identity_sha256"
        ]
        clipped_sources["t20_35e_correction_identity_sha256"] = clipped_correction[
            "identity_sha256"
        ]
        clipped = build_audit(
            correction=clipped_correction,
            report=clipped_report,
            action_stats=stats,
            source_contract=clipped_sources,
        )
        self.assertTrue(clipped["hard_saturation_detected"])
        self.assertEqual(
            clipped["selected_next_hypothesis"],
            "audit_coordinate_output_clipping_before_decoder_change",
        )

    def test_signed_source_statistic_metric_route_and_flag_drift_fail_closed(self) -> None:
        correction, report, stats, sources = self._sources(
            wrist_errors=[0.08] * 5,
            gripper_errors=[0.07] * 5,
        )
        audit = build_audit(
            correction=correction,
            report=report,
            action_stats=stats,
            source_contract=sources,
        )
        for mutation in (
            lambda value: value["source_contract"].update(
                dataset_stats_file_sha256="f" * 64
            ),
            lambda value: value["channel_audits"][0].update(q01=math.nan),
            lambda value: value["channel_audits"][0].update(
                physical_threshold_exceedance_count=0
            ),
            lambda value: value.update(
                selected_next_hypothesis="model_free_action_quantile_coverage_counterfactual"
            ),
            lambda value: value.update(model_loaded=True),
        ):
            drift = copy.deepcopy(audit)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_audit(
                    sign_payload(drift),
                    correction=correction,
                    report=report,
                    action_stats=stats,
                    source_contract=sources,
                )

        wrong_channel = copy.deepcopy(correction)
        wrong_channel["top_two_channels"][0]["joint_index"] = 3
        wrong_channel = sign_payload(wrong_channel)
        wrong_channel_sources = copy.deepcopy(sources)
        wrong_channel_sources["t20_35e_correction_identity_sha256"] = wrong_channel[
            "identity_sha256"
        ]
        with self.assertRaisesRegex(ValueError, "selected channel drifted"):
            build_audit(
                correction=wrong_channel,
                report=report,
                action_stats=stats,
                source_contract=wrong_channel_sources,
            )

        malformed_report = copy.deepcopy(report)
        malformed_report["target_action_chunk"][0][0] = math.inf
        with self.assertRaises(ValueError):
            build_audit(
                correction=correction,
                report=malformed_report,
                action_stats=stats,
                source_contract=sources,
            )

        collapsed_stats = copy.deepcopy(stats)
        collapsed_stats["q99"][4] = collapsed_stats["q01"][4]
        with self.assertRaisesRegex(ValueError, "quantile statistics drifted"):
            build_audit(
                correction=correction,
                report=report,
                action_stats=collapsed_stats,
                source_contract=sources,
            )

    @staticmethod
    def _sources(*, wrist_errors: list[float], gripper_errors: list[float]):
        target_lerobot = [0.0, 0.0, 0.0, 0.0, 95.0, 95.0]
        target_row = lerobot_to_mujoco(target_lerobot)
        target = [list(target_row) for _ in range(50)]
        replayed = []
        for seed, wrist_error, gripper_error in zip(
            (20260721, 20260722, 20260723, 20260724, 20260725),
            wrist_errors,
            gripper_errors,
            strict=True,
        ):
            decoded = []
            for row in target:
                changed = list(row)
                changed[4] += wrist_error
                changed[5] += gripper_error
                decoded.append(changed)
            replayed.append(
                {"inference_seed": seed, "decoded_action_chunk": decoded}
            )
        report = sign_payload(
            {
                "schema_version": "fixture.t20_35d.v1",
                "target_action_chunk": target,
                "replayed_chunks": replayed,
            }
        )
        correction = sign_payload(
            {
                "schema_version": "fixture.t20_35e.v1",
                "source_t20_35d_report_identity_sha256": report["identity_sha256"],
                "top_two_channels": [
                    {
                        "joint_index": 4,
                        "joint_name": "wrist_roll",
                        "threshold_exceedance_count": 50
                        * sum(abs(value) > 0.05 for value in wrist_errors),
                    },
                    {
                        "joint_index": 5,
                        "joint_name": "gripper",
                        "threshold_exceedance_count": 50
                        * sum(abs(value) > 0.05 for value in gripper_errors),
                    },
                ],
            }
        )
        stats = {
            "q01": [0.0, 0.0, 0.0, 0.0, 10.0, 20.0],
            "q99": [1.0, 1.0, 1.0, 1.0, 90.0, 90.0],
            "count": [1464],
        }
        sources = {
            "t20_35e_correction_identity_sha256": correction["identity_sha256"],
            "t20_35d_report_identity_sha256": report["identity_sha256"],
            "t20_35d_spec_identity_sha256": "a" * 64,
            "t20_35c_training_spec_identity_sha256": "b" * 64,
            "t20_33_training_spec_identity_sha256": "c" * 64,
            "dataset_manifest_identity_sha256": "d" * 64,
            "dataset_stats_file_sha256": "e" * 64,
            "pi05_configuration_source_sha256": "1" * 64,
            "pi05_normalizer_source_sha256": "2" * 64,
            "pi05_model_source_sha256": "3" * 64,
            "coordinate_source_sha256": "4" * 64,
            "action_normalization_mode": "QUANTILES",
            "normalizer_clips_normalized_values": False,
            "pi05_default_num_inference_steps": 10,
        }
        return correction, report, stats, sources


if __name__ == "__main__":
    unittest.main()
