from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36d_exact_act_gate_b_control_design import (
    build_spec,
    load_design_sources,
    verify_spec,
)


class T2036dExactActGateBControlDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_design_sources()

    def test_exact_design_binds_fresh_act_and_unchanged_gate_b(self) -> None:
        spec = build_spec(sources=self.sources)
        self.assertEqual(spec["execution_task_id"], "T20.36e")
        self.assertEqual(spec["act_config"]["policy_type"], "act")
        self.assertEqual(spec["act_config"]["chunk_size"], 50)
        self.assertEqual(spec["act_config"]["n_action_steps"], 50)
        self.assertEqual(spec["act_config"]["n_obs_steps"], 1)
        self.assertIsNone(spec["act_config"]["pretrained_backbone_weights"])
        self.assertFalse(spec["model_initialization"]["cached_checkpoint_used"])
        self.assertEqual(
            spec["campaign"]["evaluation_update_schedule"],
            [0, 100, 250, 500, 1000, 2000],
        )
        self.assertTrue(spec["attempt_contract"]["immutable_create_once"])
        self.assertTrue(spec["attempt_contract"]["must_precede_model_construction"])
        self.assertEqual(spec["gate"]["maximum_physical_action_error_rad"], 0.05)
        self.assertEqual(
            spec["gate"]["maximum_final_to_baseline_supervised_objective_ratio"],
            0.10,
        )
        self.assertTrue(spec["gate"]["unchanged_t20_33_conjunction"])
        self.assertFalse(spec["act_control_run_authorized"])

    def test_batch_dataset_and_normalizer_are_exact(self) -> None:
        spec = build_spec(sources=self.sources)
        batch = spec["source_batch"]
        dataset = spec["canonical_dataset"]
        self.assertEqual(batch["source_seed"], 0)
        self.assertEqual(batch["frame_index"], 0)
        self.assertEqual(batch["action_horizon"], 50)
        self.assertEqual(
            batch["source_episode_identity_sha256"],
            dataset["episode_zero_raw_rollout_identity_sha256"],
        )
        self.assertEqual(dataset["state_dimension"], 6)
        self.assertEqual(dataset["action_dimension"], 6)
        self.assertEqual(
            dataset["image_feature_keys"],
            [
                "observation.images.base_0_rgb",
                "observation.images.left_wrist_0_rgb",
            ],
        )
        self.assertEqual(
            spec["normalization"]["mapping"],
            {"ACTION": "MEAN_STD", "STATE": "MEAN_STD", "VISUAL": "IDENTITY"},
        )
        self.assertEqual(spec["normalization"]["statistics_frame_count"], 2330)
        for key in ("action", "observation.state"):
            self.assertEqual(len(spec["normalization"]["statistics"][key]["mean"]), 6)
            self.assertTrue(
                all(value > 0 for value in spec["normalization"]["statistics"][key]["std"])
            )

    def test_source_or_feature_drift_fails_closed(self) -> None:
        stale = copy.deepcopy(self.sources)
        stale["local_preflight"]["identity_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build_spec(sources=stale)
        feature_drift = copy.deepcopy(self.sources)
        feature_drift["dataset_info"]["features"]["action"]["shape"] = [7]
        with self.assertRaises(ValueError):
            build_spec(sources=feature_drift)
        stats_drift = copy.deepcopy(self.sources)
        stats_drift["dataset_stats"]["action"]["std"][0] = 0.0
        with self.assertRaises(ValueError):
            build_spec(sources=stats_drift)

    def test_signed_spec_rejects_schedule_gate_and_authority_tamper(self) -> None:
        spec = build_spec(sources=self.sources)
        verify_spec(spec, sources=self.sources)
        for mutate in (
            lambda row: row["campaign"].__setitem__("maximum_optimizer_updates", 2001),
            lambda row: row["gate"].__setitem__("maximum_physical_action_error_rad", 0.051),
            lambda row: row.__setitem__("act_control_run_authorized", True),
        ):
            drift = copy.deepcopy(spec)
            mutate(drift)
            with self.assertRaises(ValueError):
                verify_spec(sign_payload(drift), sources=self.sources)

    def test_result_routes_are_diagnostic_and_all_execution_authority_is_false(self) -> None:
        spec = build_spec(sources=self.sources)
        self.assertEqual(
            spec["result_routing"]["pass"],
            "shared_batch_and_normalization_control_pass_then_design_smolvla_entry",
        )
        self.assertEqual(
            spec["result_routing"]["fail"],
            "shared_pipeline_not_exonerated_diagnose_before_smolvla_entry",
        )
        self.assertFalse(spec["result_routing"]["act_is_product_policy"])
        for field in (
            "network_accessed",
            "weights_downloaded",
            "checkpoint_tensor_read",
            "model_constructed",
            "model_loaded",
            "model_inference",
            "optimizer_created",
            "optimizer_training",
            "attempt_marker_created",
            "act_control_run_authorized",
            "act_control_run_executed",
            "policy_track_selected",
            "smolvla_entry_authorized",
            "gate_b_threshold_changed",
            "gate_c_authorized",
            "closed_loop_rollout",
            "simulation_policy_accepted",
            "physical_actuation",
            "external_compute_started",
            "brev_compute_started",
            "physical_transfer_ready",
            "promotion_eligible",
        ):
            self.assertFalse(spec[field])


if __name__ == "__main__":
    unittest.main()
