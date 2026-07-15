from __future__ import annotations

import copy
import unittest

from pathlib import Path
from unittest.mock import patch

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_36c_local_policy_track_preflight import (
    build_audit,
    load_local_snapshot,
    verify_audit,
)


class T2036cLocalPolicyTrackPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = load_local_snapshot()

    def test_exact_local_snapshot_routes_act_control_before_smolvla(self) -> None:
        audit = build_audit(snapshot=self.snapshot)
        self.assertTrue(audit["act"]["source_entrypoints_complete"])
        self.assertTrue(audit["act"]["mps_runtime_previously_observed"])
        self.assertTrue(audit["act"]["local_checkpoint_metadata_complete"])
        self.assertFalse(audit["act"]["cached_checkpoint_drop_in_compatible"])
        self.assertFalse(audit["act"]["exact_gate_b_control_already_run"])
        self.assertTrue(audit["smolvla"]["source_entrypoints_complete"])
        self.assertTrue(audit["smolvla"]["base_cache_metadata_complete"])
        self.assertTrue(audit["smolvla"]["vlm_cache_metadata_complete"])
        self.assertTrue(audit["smolvla"]["action_state_horizon_match"])
        self.assertFalse(audit["smolvla"]["camera_feature_match"])
        self.assertTrue(audit["smolvla"]["two_camera_override_required"])
        self.assertFalse(audit["smolvla"]["mps_runtime_verified"])
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "design_exact_act_gate_b_control_before_smolvla_entry",
        )

    def test_dataset_and_cache_evidence_are_metadata_only(self) -> None:
        audit = build_audit(snapshot=self.snapshot)
        self.assertEqual(audit["dataset"]["state_dimension"], 6)
        self.assertEqual(audit["dataset"]["action_dimension"], 6)
        self.assertEqual(audit["dataset"]["image_feature_count"], 2)
        self.assertEqual(audit["dataset"]["image_shape"], [3, 256, 256])
        self.assertEqual(audit["dataset"]["total_frames"], 2330)
        self.assertTrue(audit["dataset"]["language_task_available"])
        for cache in audit["cache_inventory"].values():
            for row in cache["files"]:
                if row["is_weight_or_tensor_file"]:
                    self.assertFalse(row["content_read"])
                    self.assertNotIn("sha256", row)

    def test_snapshot_loader_never_reads_weight_or_tensor_content(self) -> None:
        original_read_bytes = Path.read_bytes

        def guarded_read_bytes(path: Path) -> bytes:
            if path.suffix.lower() in {".bin", ".pt", ".pth", ".safetensors"}:
                raise AssertionError(f"tensor content read attempted: {path}")
            return original_read_bytes(path)

        with patch.object(Path, "read_bytes", guarded_read_bytes):
            snapshot = load_local_snapshot()
        self.assertEqual(snapshot["lerobot_head"], self.snapshot["lerobot_head"])

    def test_stale_source_fails_and_missing_cache_fails_closed(self) -> None:
        stale = copy.deepcopy(self.snapshot)
        stale["source_files"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build_audit(snapshot=stale)
        missing = copy.deepcopy(self.snapshot)
        missing["cache_inventory"]["smolvla_base"]["files"] = []
        audit = build_audit(snapshot=missing)
        self.assertFalse(audit["smolvla"]["base_cache_metadata_complete"])
        self.assertFalse(audit["smolvla"]["local_entry_design_ready"])
        self.assertFalse(audit["policy_track_selected"])
        aliased = copy.deepcopy(self.snapshot)
        aliased["cache_inventory"]["smolvla_base"]["path"] = "/tmp/alias"
        audit = build_audit(snapshot=aliased)
        self.assertFalse(audit["smolvla"]["base_cache_metadata_complete"])
        self.assertFalse(audit["smolvla"]["local_entry_design_ready"])

    def test_config_or_dataset_drift_fails_closed(self) -> None:
        config = copy.deepcopy(self.snapshot)
        config["smolvla_base_config"]["chunk_size"] = 49
        audit = build_audit(snapshot=config)
        self.assertFalse(audit["smolvla"]["action_state_horizon_match"])
        self.assertFalse(audit["smolvla"]["local_entry_design_ready"])
        dataset = copy.deepcopy(self.snapshot)
        dataset["dataset_info"]["features"]["action"]["shape"] = [7]
        audit = build_audit(snapshot=dataset)
        self.assertFalse(audit["act"]["canonical_dataset_shape_compatible"])
        self.assertFalse(audit["smolvla"]["action_state_horizon_match"])

    def test_signed_tamper_and_all_authority_escalation_fail(self) -> None:
        audit = build_audit(snapshot=self.snapshot)
        drift = copy.deepcopy(audit)
        drift["policy_track_selected"] = True
        with self.assertRaises(ValueError):
            verify_audit(sign_payload(drift), snapshot=self.snapshot)
        for field in (
            "network_accessed",
            "weights_downloaded",
            "checkpoint_tensor_read",
            "model_loaded",
            "model_inference",
            "optimizer_created",
            "optimizer_training",
            "policy_track_selected",
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
            self.assertFalse(audit[field])


if __name__ == "__main__":
    unittest.main()
