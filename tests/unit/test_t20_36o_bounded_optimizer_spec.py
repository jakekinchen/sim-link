import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36o_bounded_optimizer_spec import (
    build_normalized_targets,
)


class T2036oBoundedOptimizerSpecTest(unittest.TestCase):
    def _bridge(self):
        return sign_payload(
            {
                "schema_version": "test.bridge.v1",
                "source_windows": [
                    {
                        "start_frame": start,
                        "executed_length": length,
                        "padded_target_action_lerobot_deg": [
                            [1.0] * 6 for _ in range(50)
                        ],
                    }
                    for start, length in zip(
                        (0, 50, 100, 150, 200),
                        (50, 50, 50, 50, 44),
                        strict=True,
                    )
                ],
            }
        )

    def test_quantile_targets_are_float32_normalized_and_zero_padded(self) -> None:
        rows = build_normalized_targets(
            bridge_spec=self._bridge(),
            dataset_stats={"action": {"q01": [0.0] * 6, "q99": [2.0] * 6}},
        )
        self.assertEqual([row["start_frame"] for row in rows], [0, 50, 100, 150, 200])
        self.assertEqual([row["executed_length"] for row in rows], [50, 50, 50, 50, 44])
        self.assertEqual(rows[0]["normalized_padded_target"][0], [0.0] * 32)
        self.assertEqual(len(rows[0]["normalized_padded_target"]), 50)

    def test_target_shape_and_quantile_range_fail_closed(self) -> None:
        bridge = self._bridge()
        drift = copy.deepcopy(bridge)
        drift["source_windows"][0]["padded_target_action_lerobot_deg"] = [[1.0] * 6]
        drift = sign_payload(drift)
        with self.assertRaises(ValueError):
            build_normalized_targets(
                bridge_spec=drift,
                dataset_stats={"action": {"q01": [0.0] * 6, "q99": [2.0] * 6}},
            )
        with self.assertRaises(ValueError):
            build_normalized_targets(
                bridge_spec=self._bridge(),
                dataset_stats={"action": {"q01": [1.0] * 6, "q99": [1.0] * 6}},
            )


if __name__ == "__main__":
    unittest.main()
