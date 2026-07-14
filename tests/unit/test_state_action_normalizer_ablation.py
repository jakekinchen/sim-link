import hashlib
import unittest

import numpy as np

from scenesmith.robot_lab.state_action_normalizer_ablation import (
    CELL_ORDER,
    build_state_action_normalizer_ablation,
)


class StateActionNormalizerAblationTest(unittest.TestCase):
    def test_state_effect_can_be_isolated(self) -> None:
        cells = self._cells()
        payload = build_state_action_normalizer_ablation(
            sources={},
            cells=cells,
            oracle_action_rad=[0.0] * 6,
            processor_evidence=self._processor_evidence(),
            runtime=self._runtime(),
        )
        self.assertEqual(payload["finding"]["dominant_effect"], "state_preprocessor")
        self.assertTrue(payload["finding"]["single_effect_isolated"])
        self.assertEqual(
            payload["finding"]["selected_next_hypothesis"],
            "dataset_state_token_distribution_shift_dominates",
        )
        self.assertEqual(
            payload["effect_decomposition_rad"]["closure_residual_max_abs"], 0.0
        )

    def test_common_state_output_drift_rejects(self) -> None:
        cells = self._cells()
        cells[1]["normalized_model_output"][0] = 0.5
        cells[1]["normalized_output_sha256"] = self._output_sha(
            cells[1]["normalized_model_output"]
        )
        with self.assertRaisesRegex(ValueError, "not identical"):
            build_state_action_normalizer_ablation(
                sources={},
                cells=cells,
                oracle_action_rad=[0.0] * 6,
                processor_evidence=self._processor_evidence(),
                runtime=self._runtime(),
            )

    @staticmethod
    def _cells():
        outputs = [[0.0] * 6, [0.0] * 6, [1.0] * 6, [1.0] * 6]
        actions = [[0.0] * 6, [0.01] * 6, [1.0] * 6, [1.01] * 6]
        hashes = [
            StateActionNormalizerAblationTest._output_sha(output)
            for output in outputs
        ]
        return [
            {
                "cell_id": cell_id,
                "normalized_model_output": normalized,
                "normalized_output_sha256": hash_value,
                "canonical_action_mujoco_rad": action,
                "oracle_absolute_error_rad": [abs(value) for value in action],
            }
            for cell_id, normalized, hash_value, action in zip(
                CELL_ORDER, outputs, hashes, actions, strict=True
            )
        ]

    @staticmethod
    def _output_sha(values):
        return hashlib.sha256(np.asarray(values, dtype=np.float32).tobytes()).hexdigest()

    @staticmethod
    def _processor_evidence():
        return {
            "checkpoint_pipeline_loaded_from_pinned_snapshot": True,
            "only_state_statistics_replaced_in_dataset_state_preprocessor": True,
            "only_action_statistics_replaced_in_dataset_action_postprocessor": True,
            "all_other_preprocessor_statistics_identical": True,
            "all_other_postprocessor_statistics_identical": True,
            "checkpoint_state_statistics_sha256": "1" * 64,
            "dataset_state_statistics_sha256": "2" * 64,
            "checkpoint_action_statistics_sha256": "3" * 64,
            "dataset_action_statistics_sha256": "4" * 64,
        }

    @staticmethod
    def _runtime():
        return {
            "device": "mps",
            "offline": True,
            "inference_seed": 2027,
            "model_inference_call_count": 4,
            "optimizer_step_count": 0,
            "simulation_step_count": 0,
        }


if __name__ == "__main__":
    unittest.main()
