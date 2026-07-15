from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_35e_top_two_channel_correction import (
    build_correction,
    verify_correction,
)


class T2035ETopTwoChannelCorrectionTests(unittest.TestCase):
    def test_top_two_concentration_corrects_distributed_label(self) -> None:
        correction = self._build([0, 29, 0, 52, 164, 121], boundary=34 / 366)
        self.assertEqual(
            correction["corrected_residual_classification"],
            "multi_joint_output_channel_concentrated",
        )
        self.assertEqual(
            [row["joint_name"] for row in correction["top_two_channels"]],
            ["joint_4", "joint_5"],
        )
        self.assertAlmostEqual(
            correction["top_two_channel_exceedance_fraction"], 285 / 366
        )
        verify_correction(correction)

    def test_single_joint_and_boundary_precedence_remain_distinct(self) -> None:
        joint = self._build([0, 0, 0, 0, 80, 20], boundary=0.1)
        self.assertEqual(
            joint["corrected_residual_classification"], "joint_specific_residual"
        )
        boundary = self._build([20, 20, 20, 20, 10, 10], boundary=0.7)
        self.assertEqual(
            boundary["corrected_residual_classification"], "chunk_boundary_residual"
        )

    def test_below_top_two_threshold_remains_distributed(self) -> None:
        correction = self._build([18, 18, 17, 17, 15, 15], boundary=0.1)
        self.assertEqual(
            correction["corrected_residual_classification"],
            "distributed_decoding_residual",
        )

    def test_count_sort_fraction_and_signed_mutation_fail_closed(self) -> None:
        correction = self._build([0, 29, 0, 52, 164, 121], boundary=34 / 366)
        for mutation in (
            lambda value: value["per_joint_exceedance_counts"][0].update(
                threshold_exceedance_count=1
            ),
            lambda value: value["ranked_joint_exceedance_counts"].reverse(),
            lambda value: value.update(top_two_channel_exceedance_fraction=0.1),
            lambda value: value.update(model_loaded=True),
        ):
            drift = copy.deepcopy(correction)
            mutation(drift)
            with self.assertRaises(ValueError):
                verify_correction(sign_payload(drift))

    @staticmethod
    def _build(counts: list[int], *, boundary: float) -> dict:
        return build_correction(
            source_report_identity="a" * 64,
            threshold_exceedance_count=sum(counts),
            per_joint_summary=[
                {
                    "joint_index": index,
                    "joint_name": f"joint_{index}",
                    "threshold_exceedance_count": count,
                }
                for index, count in enumerate(counts)
            ],
            boundary_exceedance_fraction=boundary,
            original_classification="distributed_decoding_residual",
            original_selected_next_hypothesis="inspect_decoder_sampling_or_action_gate_calibration",
        )


if __name__ == "__main__":
    unittest.main()
