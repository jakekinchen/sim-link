from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (
    EVALUATION_UPDATE_SCHEDULE,
    IMAGE_FEATURE_KEYS,
    VLM_SNAPSHOT,
    build_spec,
    load_sources,
    verify_spec,
)


class T2036gExactSmolVLAEntryDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_sources()
        cls.spec = build_spec(sources=cls.sources)

    def test_exact_two_camera_pretrained_expert_only_design(self) -> None:
        verify_spec(self.spec, sources=self.sources)
        config = self.spec["smolvla_config"]
        self.assertEqual(
            list(config["input_features"]),
            [*IMAGE_FEATURE_KEYS, "observation.state"],
        )
        self.assertEqual(config["empty_cameras"], 0)
        self.assertTrue(config["load_vlm_weights"])
        self.assertTrue(config["train_expert_only"])
        self.assertTrue(config["train_state_proj"])
        self.assertFalse(config["compile_model"])
        self.assertEqual(config["vlm_model_name"], str(VLM_SNAPSHOT))

    def test_processor_batching_and_offline_runtime_are_exact(self) -> None:
        normalization = self.spec["normalization"]
        self.assertIn(
            "processor_smolvla",
            normalization["policy_specific_processor_implementation"],
        )
        self.assertEqual(
            self.spec["batch_construction"]["processed_action_shape"],
            [1, 50, 6],
        )
        runtime = self.spec["runtime_contract"]
        self.assertTrue(runtime["local_files_only"])
        self.assertTrue(runtime["huggingface_hub_offline"])
        self.assertFalse(runtime["network_access_allowed"])
        self.assertFalse(runtime["cpu_fallback_allowed"])

    def test_finite_evidence_and_selected_checkpoint_are_required(self) -> None:
        self.assertTrue(
            self.spec["finite_evidence"]["non_finite_value_fails_closed"]
        )
        checkpoint = self.spec["checkpoint_contract"]
        self.assertTrue(checkpoint["scheduled_evaluations_are_in_memory"])
        self.assertTrue(checkpoint["save_only_selected_pass_or_terminal_checkpoint"])
        self.assertEqual(checkpoint["model_file"], "model.safetensors")

    def test_schedule_and_gate_are_frozen_without_authority(self) -> None:
        self.assertEqual(
            self.spec["campaign"]["evaluation_update_schedule"],
            EVALUATION_UPDATE_SCHEDULE,
        )
        self.assertIsNone(self.spec["campaign"]["scheduler"])
        self.assertEqual(
            self.spec["gate"]["maximum_physical_action_error_rad"], 0.05
        )
        self.assertFalse(self.spec["gate_b_threshold_changed"])
        self.assertFalse(self.spec["smolvla_entry_authorized"])
        self.assertFalse(self.spec["model_loaded"])

    def test_source_or_camera_alias_drift_rejects(self) -> None:
        source_drift = copy.deepcopy(self.sources)
        source_drift["base_config_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build_spec(sources=source_drift)
        camera_drift = copy.deepcopy(self.spec)
        camera_drift["camera_override"]["duplicate_camera_allowed"] = True
        with self.assertRaises(ValueError):
            verify_spec(sign_payload(camera_drift), sources=self.sources)

    def test_design_cannot_select_policy_or_gate_c(self) -> None:
        for field in (
            "policy_track_selected",
            "smolvla_entry_authorized",
            "gate_c_authorized",
            "optimizer_training",
        ):
            drift = copy.deepcopy(self.spec)
            drift[field] = True
            with self.assertRaises(ValueError):
                verify_spec(sign_payload(drift), sources=self.sources)


if __name__ == "__main__":
    unittest.main()
