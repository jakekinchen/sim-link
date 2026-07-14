from __future__ import annotations

import copy
import hashlib
import math
import tempfile
import unittest

from pathlib import Path

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.pi05_gripper_channel_audit import (
    build_pi05_gripper_channel_audit,
    load_action_statistics,
    verify_pi05_gripper_channel_audit,
)


class Pi05GripperChannelAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        frame = np.array([0.05, -1.67, 1.54, 1.04, -0.03, 1.6], dtype=np.float64)
        close = frame.copy()
        close[1] = -0.01
        close[3] = -0.12
        close[4] = 1.55
        close[-1] = 0.2492469645219354
        self.train = np.stack([frame if index % 2 == 0 else close for index in range(488)])
        self.evaluation = np.stack(
            [frame if index % 2 == 0 else close for index in range(244)]
        )
        self.stats = {
            "count": 94568,
            "min": [-70.0, -100.0, -100.0, 17.0, -29.0, 0.2],
            "q01": [-40.0, -98.0, -72.0, 39.0, -12.0, 1.0],
            "q99": [45.0, 54.0, 99.0, 88.0, 1.2, 60.0],
            "max": [72.0, 77.0, 100.0, 100.0, 8.0, 81.0],
            "mean": [1.8, -7.1, 5.2, 61.9, -3.9, 22.8],
            "std": [26.7, 46.8, 47.9, 14.3, 4.6, 24.9],
        }
        requested = frame.copy()
        requested[-1] = 0.8456789783607485
        error = float(frame[-1] - requested[-1])
        self.t20_11 = {
            "model_id": "pi05",
            "action_error_diagnostics": {
                "first_action_divergence": {
                    "frame_index": 0,
                    "joint_name": "gripper",
                    "source_action_rad": float(frame[-1]),
                    "model_action_rad": float(requested[-1]),
                    "absolute_error_rad": error,
                }
            },
            "corrected_closed_loop": {"policy_requested_action_first": requested.tolist()},
        }
        self.evidence = {
            "source": {"path": "source", "sha256": "a" * 64},
            "checkpoint": {"path": "checkpoint", "sha256": "b" * 64},
        }
        self.loss = {
            "action_dimension_count": 6,
            "action_dimension_weights": [1.0] * 6,
            "gripper_dimension_weight": 1.0,
            "gripper_only_loss": False,
            "reduction": "mean_over_batch_time_and_six_action_dimensions",
            "per_dimension_aggregation_share": 1.0 / 6.0,
            "observed_loss_per_dimension_recomputed": False,
            "target_scale_proxy_is_not_observed_loss": True,
        }

    def build(self):
        return build_pi05_gripper_channel_audit(
            train_action_mujoco=self.train,
            evaluation_action_mujoco=self.evaluation,
            checkpoint_action_statistics=self.stats,
            source_evidence=self.evidence,
            t20_11_pi05=self.t20_11,
            loss_contract=self.loss,
        )

    def verify(self, payload):
        verify_pi05_gripper_channel_audit(
            payload,
            train_action_mujoco=self.train,
            evaluation_action_mujoco=self.evaluation,
            checkpoint_action_statistics=self.stats,
            source_evidence=self.evidence,
            t20_11_pi05=self.t20_11,
            loss_contract=self.loss,
        )

    def test_build_reports_roundtrip_support_margins_and_broad_mismatch(self) -> None:
        payload = self.build()
        self.verify(payload)
        self.assertTrue(
            payload["coordinate_contract"]["all_732_actions_roundtrip_within_threshold"]
        )
        self.assertFalse(
            payload["gate_margins"]["frame_zero_open_gripper_within_checkpoint_max"][
                "pass"
            ]
        )
        self.assertEqual(payload["loss_accounting"]["gripper_dimension_weight"], 1.0)
        self.assertFalse(payload["finding"]["single_gripper_fault_supported"])
        self.assertEqual(
            payload["finding"]["selected_next_hypothesis"],
            "derive_dataset_bound_pi05_normalizer_then_retest_without_loss_reweighting",
        )

    def test_source_substitution_is_rejected(self) -> None:
        payload = self.build()
        evidence = copy.deepcopy(self.evidence)
        evidence["source"]["sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "drifted from sources"):
            verify_pi05_gripper_channel_audit(
                payload,
                train_action_mujoco=self.train,
                evaluation_action_mujoco=self.evaluation,
                checkpoint_action_statistics=self.stats,
                source_evidence=evidence,
                t20_11_pi05=self.t20_11,
                loss_contract=self.loss,
            )

    def test_action_reordering_is_rejected(self) -> None:
        payload = self.build()
        changed = self.evaluation.copy()
        changed[:, [0, 5]] = changed[:, [5, 0]]
        with self.assertRaises(ValueError):
            verify_pi05_gripper_channel_audit(
                payload,
                train_action_mujoco=self.train,
                evaluation_action_mujoco=changed,
                checkpoint_action_statistics=self.stats,
                source_evidence=self.evidence,
                t20_11_pi05=self.t20_11,
                loss_contract=self.loss,
            )

    def test_nonfinite_and_missing_gripper_metadata_are_rejected(self) -> None:
        changed = self.train.copy()
        changed[0, 5] = math.nan
        with self.assertRaisesRegex(ValueError, "malformed"):
            build_pi05_gripper_channel_audit(
                train_action_mujoco=changed,
                evaluation_action_mujoco=self.evaluation,
                checkpoint_action_statistics=self.stats,
                source_evidence=self.evidence,
                t20_11_pi05=self.t20_11,
                loss_contract=self.loss,
            )
        t20_11 = copy.deepcopy(self.t20_11)
        t20_11["action_error_diagnostics"]["first_action_divergence"].pop(
            "model_action_rad"
        )
        with self.assertRaisesRegex(ValueError, "linkage"):
            build_pi05_gripper_channel_audit(
                train_action_mujoco=self.train,
                evaluation_action_mujoco=self.evaluation,
                checkpoint_action_statistics=self.stats,
                source_evidence=self.evidence,
                t20_11_pi05=t20_11,
                loss_contract=self.loss,
            )

    def test_false_roundtrip_loss_and_authority_claims_are_rejected(self) -> None:
        for mutate in (
            lambda value: value["coordinate_contract"].__setitem__(
                "maximum_inverse_roundtrip_error_rad", 0.0
            ),
            lambda value: value["loss_accounting"].__setitem__(
                "gripper_dimension_weight", 0.1
            ),
            lambda value: value.__setitem__("simulation_policy_accepted", True),
        ):
            with self.subTest(mutate=mutate):
                changed = copy.deepcopy(self.build())
                mutate(changed)
                changed.pop("identity_sha256")
                changed = sign_payload(changed)
                with self.assertRaisesRegex(ValueError, "drifted from sources"):
                    self.verify(changed)

    def test_safetensors_hash_and_nonfinite_statistics_fail_closed(self) -> None:
        def encoded(std_value: float) -> bytes:
            names = {
                "action.count": [94568.0],
                "action.min": [-1.0] * 6,
                "action.q01": [-0.5] * 6,
                "action.q99": [0.5] * 6,
                "action.max": [1.0] * 6,
                "action.mean": [0.0] * 6,
                "action.std": [std_value] * 6,
            }
            offset = 0
            header = {}
            chunks = []
            import json
            import struct

            for name, values in names.items():
                chunk = struct.pack(f"<{len(values)}f", *values)
                header[name] = {
                    "dtype": "F32",
                    "shape": [len(values)],
                    "data_offsets": [offset, offset + len(chunk)],
                }
                chunks.append(chunk)
                offset += len(chunk)
            header_bytes = json.dumps(header, separators=(",", ":")).encode()
            return struct.pack("<Q", len(header_bytes)) + header_bytes + b"".join(chunks)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.safetensors"
            value = encoded(1.0)
            path.write_bytes(value)
            stats = load_action_statistics(
                path, expected_sha256=hashlib.sha256(value).hexdigest()
            )
            self.assertEqual(stats["count"], 94568.0)
            with self.assertRaisesRegex(ValueError, "hash drifted"):
                load_action_statistics(path, expected_sha256="0" * 64)
            invalid = encoded(math.nan)
            path.write_bytes(invalid)
            with self.assertRaisesRegex(ValueError, "non-finite"):
                load_action_statistics(
                    path, expected_sha256=hashlib.sha256(invalid).hexdigest()
                )


if __name__ == "__main__":
    unittest.main()
