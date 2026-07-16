import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.t20_36o_bounded_optimizer_authority import (
    build_attempt_marker,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_run import (
    build_failure_result,
    build_probe_artifact,
    build_result,
    verify_probe_artifact,
    verify_result,
)


class T2036oBoundedOptimizerRunTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("configurations/robot_lab")
        self.permit = load_strict_json(root / "t20_36o_optimizer_training_permit.json")
        self.spec = load_strict_json(root / "t20_36o_bounded_optimizer_spec.json")
        self.bridge = load_strict_json(root / "t20_36o_episode_bridge_design.json")
        self.attempt = build_attempt_marker(
            permit=self.permit,
            source_commit="a" * 40,
        )
        self.baseline = 0.9590791046619416

    def _rows(self, *, offset: float = 0.0):
        rows = []
        for start_index, window in enumerate(self.bridge["source_windows"]):
            tensor = [
                [float(value + offset) for value in target]
                for target in window["padded_target_action_mujoco_rad"]
            ]
            for seed_index, inference_seed in enumerate(
                self.permit["probe_inference_seeds"]
            ):
                for repeat_index in range(2):
                    rows.append(
                        {
                            "start_index": start_index,
                            "start_frame": window["start_frame"],
                            "executed_length": window["executed_length"],
                            "seed_index": seed_index,
                            "inference_seed": inference_seed,
                            "repeat_index": repeat_index,
                            "decoded_action_chunk": tensor,
                        }
                    )
        return rows

    def _probe(self, update_count: int, *, offset: float = 0.0, ratio: float = 0.05):
        return {
            "update_count": update_count,
            "source_objective_mean": self.baseline * ratio,
            "source_objective_ratio": ratio,
            "rows": self._rows(offset=offset),
        }

    def test_first_complete_pass_stops_and_round_trips(self) -> None:
        artifact = build_probe_artifact(
            attempt=self.attempt,
            permit=self.permit,
            optimizer_spec=self.spec,
            bridge_spec=self.bridge,
            source_gate_baseline_objective_mean=self.baseline,
            probes=[self._probe(500)],
        )
        self.assertEqual(artifact["first_passing_update"], 500)
        self.assertEqual(artifact["decoded_tensor_count"], 50)
        self.assertTrue(artifact["all_repeats_bit_identical"])
        verify_probe_artifact(
            artifact,
            attempt=self.attempt,
            permit=self.permit,
            optimizer_spec=self.spec,
            bridge_spec=self.bridge,
            source_gate_baseline_objective_mean=self.baseline,
        )
        metrics = {
            "optimizer_update_count": 500,
            "per_update_objective": [1.0] * 500,
            "per_update_correction_objective": [0.5] * 500,
            "per_update_standard_replay_objective": [0.5] * 500,
            "gradient_norms_before_clip": [0.25] * 500,
        }
        result = build_result(
            attempt=self.attempt,
            permit=self.permit,
            optimizer_spec=self.spec,
            probe_artifact=artifact,
            training_metrics=metrics,
            checkpoint_tree=[
                {"path": "config.json", "sha256": "b" * 64, "size_bytes": 1},
                {"path": "model.safetensors", "sha256": "c" * 64, "size_bytes": 2},
            ],
            source_checkpoint_tree_unchanged=True,
        )
        self.assertTrue(result["bridge_gate_passed"])
        self.assertTrue(result["gate_c_request_eligible"])
        verify_result(
            result,
            attempt=self.attempt,
            permit=self.permit,
            optimizer_spec=self.spec,
            probe_artifact=artifact,
        )

    def test_negative_must_reach_ceiling_and_repeat_drift_fails(self) -> None:
        probes = [
            self._probe(update, offset=1.0)
            for update in self.permit["probe_update_counts"]
        ]
        artifact = build_probe_artifact(
            attempt=self.attempt,
            permit=self.permit,
            optimizer_spec=self.spec,
            bridge_spec=self.bridge,
            source_gate_baseline_objective_mean=self.baseline,
            probes=probes,
        )
        self.assertIsNone(artifact["first_passing_update"])
        self.assertFalse(artifact["probes"][-1]["passed"])
        with self.assertRaises(ValueError):
            build_probe_artifact(
                attempt=self.attempt,
                permit=self.permit,
                optimizer_spec=self.spec,
                bridge_spec=self.bridge,
                source_gate_baseline_objective_mean=self.baseline,
                probes=probes[:-1],
            )
        drift = copy.deepcopy(probes)
        drift[0]["rows"][1]["decoded_action_chunk"] = copy.deepcopy(
            drift[0]["rows"][1]["decoded_action_chunk"]
        )
        drift[0]["rows"][1]["decoded_action_chunk"][0][0] += 0.1
        with self.assertRaises(ValueError):
            build_probe_artifact(
                attempt=self.attempt,
                permit=self.permit,
                optimizer_spec=self.spec,
                bridge_spec=self.bridge,
                source_gate_baseline_objective_mean=self.baseline,
                probes=drift,
            )

    def test_lineage_objective_and_metric_drift_fail_closed(self) -> None:
        drift_spec = copy.deepcopy(self.spec)
        drift_spec["bridge_spec_identity_sha256"] = "d" * 64
        drift_spec = sign_payload(drift_spec)
        with self.assertRaises(ValueError):
            build_probe_artifact(
                attempt=self.attempt,
                permit=self.permit,
                optimizer_spec=drift_spec,
                bridge_spec=self.bridge,
                source_gate_baseline_objective_mean=self.baseline,
                probes=[self._probe(500)],
            )
        with self.assertRaises(ValueError):
            build_probe_artifact(
                attempt=self.attempt,
                permit=self.permit,
                optimizer_spec=self.spec,
                bridge_spec=self.bridge,
                source_gate_baseline_objective_mean=self.baseline,
                probes=[self._probe(500, ratio=0.2)],
            )
        artifact = build_probe_artifact(
            attempt=self.attempt,
            permit=self.permit,
            optimizer_spec=self.spec,
            bridge_spec=self.bridge,
            source_gate_baseline_objective_mean=self.baseline,
            probes=[self._probe(500)],
        )
        metrics = {
            "optimizer_update_count": 500,
            "per_update_objective": [True] * 500,
            "per_update_correction_objective": [0.5] * 500,
            "per_update_standard_replay_objective": [0.5] * 500,
            "gradient_norms_before_clip": [0.25] * 500,
        }
        with self.assertRaises(ValueError):
            build_result(
                attempt=self.attempt,
                permit=self.permit,
                optimizer_spec=self.spec,
                probe_artifact=artifact,
                training_metrics=metrics,
                checkpoint_tree=[
                    {"path": "model.safetensors", "sha256": "c" * 64, "size_bytes": 2}
                ],
                source_checkpoint_tree_unchanged=True,
            )
        drift_attempt = copy.deepcopy(self.attempt)
        drift_attempt["training_permit_identity_sha256"] = "e" * 64
        drift_attempt = sign_payload(drift_attempt)
        with self.assertRaises(ValueError):
            build_failure_result(
                permit=self.permit,
                attempt=drift_attempt,
                failure_stage="optimizer_training",
                error_type="RuntimeError",
                error_message="test",
                checkpoint_tensor_read=True,
                model_constructed=True,
                model_loaded=True,
                optimizer_created=True,
                optimizer_update_count=1,
            )


if __name__ == "__main__":
    unittest.main()
