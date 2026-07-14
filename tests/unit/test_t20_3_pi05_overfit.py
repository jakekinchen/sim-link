import importlib.util
import unittest

from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/robot_lab/run_t20_3_pi05_overfit.py"
SPEC = importlib.util.spec_from_file_location("run_t20_3_pi05_overfit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class T20_3PI05OverfitTest(unittest.TestCase):
    def test_training_starts_never_cross_episode_boundary(self) -> None:
        self.assertEqual(len(MODULE.VALID_TRAIN_STARTS), 390)
        self.assertIn(194, MODULE.VALID_TRAIN_STARTS)
        self.assertNotIn(195, MODULE.VALID_TRAIN_STARTS)
        self.assertIn(244, MODULE.VALID_TRAIN_STARTS)
        self.assertIn(438, MODULE.VALID_TRAIN_STARTS)
        self.assertNotIn(439, MODULE.VALID_TRAIN_STARTS)

    def test_array_validation_rejects_nonfinite_values(self) -> None:
        arrays = {
            "train_state": np.zeros((488, 12), dtype=np.float32),
            "train_action": np.zeros((488, 6), dtype=np.float32),
            "evaluation_state": np.zeros((244, 12), dtype=np.float32),
            "evaluation_action": np.zeros((244, 6), dtype=np.float32),
        }
        MODULE._validate_arrays(arrays)
        arrays["evaluation_action"][0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "evaluation_action"):
            MODULE._validate_arrays(arrays)

    def test_snapshot_root_is_content_addressed(self) -> None:
        path = MODULE._snapshot_root("org/model", "abc123")
        self.assertTrue(str(path).endswith("models--org--model/snapshots/abc123"))

    def test_t20_4_training_plan_distinguishes_updates_and_microbatches(self) -> None:
        plan = MODULE._training_plan(250, 2)
        self.assertEqual(len(plan), 250)
        self.assertTrue(all(len(update) == 2 for update in plan))
        starts = [start for update in plan for start in update]
        self.assertEqual(len(starts), 500)
        self.assertTrue(all(start in MODULE.VALID_TRAIN_STARTS for start in starts))

    def test_training_plan_rejects_nonpositive_dimensions(self) -> None:
        for updates, accumulation in ((0, 1), (1, 0), (-1, 2)):
            with self.assertRaises(ValueError):
                MODULE._training_plan(updates, accumulation)


if __name__ == "__main__":
    unittest.main()
