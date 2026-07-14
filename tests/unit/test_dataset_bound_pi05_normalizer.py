from __future__ import annotations

import copy
import unittest

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.dataset_bound_pi05_normalizer import (
    build_dataset_bound_pi05_normalizer,
    verify_dataset_bound_pi05_normalizer,
)


class DatasetBoundPi05NormalizerTest(unittest.TestCase):
    def setUp(self) -> None:
        base = np.array([0.05, -1.0, 1.2, 0.1, 0.4, 0.8], dtype=np.float64)
        train = np.stack([base + (index % 17) * 0.001 for index in range(488)])
        evaluation = np.stack(
            [base + 0.01 + (index % 13) * 0.001 for index in range(244)]
        )
        self.train_action = train
        self.evaluation_action = evaluation
        self.train_state = np.concatenate([train, np.zeros_like(train)], axis=1)
        self.evaluation_state = np.concatenate(
            [evaluation, np.zeros_like(evaluation)], axis=1
        )
        self.evidence = {
            "tensor": {"path": "tensor", "sha256": "a" * 64},
            "processor": {"path": "processor", "sha256": "b" * 64},
        }
        joints = {}
        for name in (
            "shoulder_pan",
            "shoulder_lift",
            "elbow_flex",
            "wrist_flex",
            "wrist_roll",
            "gripper",
        ):
            joints[name] = {"normalized_target_mean_square": 10.0}
        self.t20_12 = {
            "schema_version": "scenesmith.t20_12_pi05_gripper_channel_audit.v1",
            "finding": {
                "selected_next_hypothesis": (
                    "derive_dataset_bound_pi05_normalizer_then_retest_without_loss_reweighting"
                )
            },
            "dataset_action_audit": {"train": {"joints": joints}},
            "t20_11_gripper_reconciliation": {"source_gripper_normalized": 2.8},
        }

    def build(self, **overrides):
        values = {
            "train_state_mujoco": self.train_state,
            "train_action_mujoco": self.train_action,
            "evaluation_state_mujoco": self.evaluation_state,
            "evaluation_action_mujoco": self.evaluation_action,
            "source_evidence": self.evidence,
            "t20_12_audit": self.t20_12,
        }
        values.update(overrides)
        return build_dataset_bound_pi05_normalizer(**values)

    def verify(self, payload, **overrides):
        values = {
            "train_state_mujoco": self.train_state,
            "train_action_mujoco": self.train_action,
            "evaluation_state_mujoco": self.evaluation_state,
            "evaluation_action_mujoco": self.evaluation_action,
            "source_evidence": self.evidence,
            "t20_12_audit": self.t20_12,
        }
        values.update(overrides)
        verify_dataset_bound_pi05_normalizer(payload, **values)

    def test_train_only_fit_and_inverse_gates_pass(self) -> None:
        payload = self.build()
        self.verify(payload)
        self.assertFalse(payload["fit_contract"]["held_out_values_contributed_to_fit"])
        self.assertEqual(
            payload["fit_contract"]["standard_deviation_estimator"],
            "population_ddof_0",
        )
        self.assertIn(
            "velocity_columns_excluded",
            payload["fit_contract"]["state_projection"],
        )
        self.assertTrue(
            payload["gate_summary"][
                "all_train_means_zero_and_stds_one_within_tolerance"
            ]
        )
        self.assertTrue(
            payload["gate_summary"][
                "all_state_and_action_inverse_transforms_within_tolerance"
            ]
        )

    def test_held_out_change_does_not_change_fitted_statistics(self) -> None:
        original = self.build()
        changed_evaluation = self.evaluation_action.copy()
        changed_evaluation[:, 5] += 0.1
        changed = self.build(evaluation_action_mujoco=changed_evaluation)
        self.assertEqual(original["fitted_statistics"], changed["fitted_statistics"])
        self.assertNotEqual(
            original["feature_audits"]["action"]["joints"]["gripper"],
            changed["feature_audits"]["action"]["joints"]["gripper"],
        )

    def test_source_substitution_and_joint_reordering_are_rejected(self) -> None:
        payload = self.build()
        evidence = copy.deepcopy(self.evidence)
        evidence["tensor"]["sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "drifted from sources"):
            self.verify(payload, source_evidence=evidence)
        reordered = self.train_action[:, ::-1].copy()
        with self.assertRaisesRegex(ValueError, "drifted from sources"):
            self.verify(payload, train_action_mujoco=reordered)

    def test_nonfinite_and_near_zero_statistics_fail_closed(self) -> None:
        nonfinite = self.train_action.copy()
        nonfinite[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "malformed"):
            self.build(train_action_mujoco=nonfinite)
        constant = self.train_action.copy()
        constant[:, 0] = constant[0, 0]
        with self.assertRaisesRegex(ValueError, "near-zero"):
            self.build(train_action_mujoco=constant)

    def test_false_inverse_loss_or_authority_claims_are_rejected(self) -> None:
        for mutate in (
            lambda value: value["feature_audits"]["action"]["inverse_gate"].__setitem__(
                "measured_maximum_error_rad", 0.0
            ),
            lambda value: value["target_scale_comparison"].__setitem__(
                "same_equal_six_way_loss_weights_required_for_next_test", False
            ),
            lambda value: value.__setitem__("optimizer_training", True),
        ):
            changed = copy.deepcopy(self.build())
            mutate(changed)
            changed.pop("identity_sha256")
            changed = sign_payload(changed)
            with self.assertRaisesRegex(ValueError, "drifted from sources"):
                self.verify(changed)


if __name__ == "__main__":
    unittest.main()
