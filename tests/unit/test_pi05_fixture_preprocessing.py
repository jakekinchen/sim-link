from __future__ import annotations

import copy
import hashlib
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import (
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.pi05_fixture_preprocessing import (
    EXPECTED_RUNTIME_RESULT_IDENTITY,
    PI05_FIXTURE_MODEL_READY_PARITY_SCHEMA_VERSION,
    build_fixture_input_spec,
    canonical_fixture_frame,
    verify_pi05_fixture_model_ready_parity,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
HF_CACHE_ROOT = Path.home() / ".cache/huggingface/hub"
CALIBRATION_PATH = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
ARTIFACT_PATH = (
    REPO_ROOT
    / "configurations/robot_lab/pi05_fixture_model_ready_tensor_parity.json"
)


class Pi05FixturePreprocessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = load_strict_json(ARTIFACT_PATH)

    def verify(self, payload: dict) -> None:
        verify_pi05_fixture_model_ready_parity(
            payload,
            repo_root=REPO_ROOT,
            hf_cache_root=HF_CACHE_ROOT,
            calibration_path=CALIBRATION_PATH,
        )

    def assert_resigned_rejected(self, mutation) -> None:
        altered = copy.deepcopy(self.payload)
        mutation(altered)
        with self.assertRaises(ValueError):
            self.verify(sign_payload(altered))

    def test_checked_artifact_verifies(self) -> None:
        self.verify(self.payload)
        self.assertEqual(
            self.payload["schema_version"],
            PI05_FIXTURE_MODEL_READY_PARITY_SCHEMA_VERSION,
        )
        self.assertEqual(
            self.payload["runtime_result"]["identity_sha256"],
            EXPECTED_RUNTIME_RESULT_IDENTITY,
        )

    def test_fixture_input_spec_is_deterministic(self) -> None:
        first = build_fixture_input_spec(repo_root=REPO_ROOT)
        second = build_fixture_input_spec(repo_root=REPO_ROOT)
        self.assertEqual(first, second)
        self.assertEqual(first["state_selection"], "q_after")
        self.assertEqual(first["selected_frame_rule"], "highest_complete_frame_index")
        self.assertEqual([item["frame_index"] for item in first["selected_frames"]], [1, 1])
        self.assertEqual([item["source_key"] for item in first["selected_frames"]], [
            "observation.images.top",
            "observation.images.wrist",
        ])

    def test_canonical_png_and_decoded_rgb_are_stable_and_distinct(self) -> None:
        frames = [
            canonical_fixture_frame(role=role, frame_index=index)
            for role in ("top", "wrist")
            for index in (0, 1)
        ]
        self.assertEqual(len({item["png_sha256"] for item in frames}), 4)
        self.assertEqual(len({item["decoded_rgb_sha256"] for item in frames}), 4)
        for item in frames:
            self.assertTrue(item["png_bytes"].startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(item["png_sha256"], hashlib.sha256(item["png_bytes"]).hexdigest())
            self.assertEqual(
                item["decoded_rgb_sha256"],
                hashlib.sha256(item["decoded_rgb_bytes"]).hexdigest(),
            )
            self.assertEqual(len(item["decoded_rgb_bytes"]), 640 * 480 * 3)

    def test_fixture_classification_withholds_live_authority(self) -> None:
        self.assertEqual(self.payload["evidence_mode"], "deterministic_fixture_preprocessing")
        self.assertEqual(self.payload["qualification_scope"], "fixture_pi05_model_input_parity")
        self.assertEqual(
            self.payload["local_capabilities"],
            [
                "fixture_pi05_model_ready_tensor_parity_conformant",
                "fixture_pi05_training_support_audit_conformant",
            ],
        )
        self.assertEqual(self.payload["proof_labels"], [])
        self.assertFalse(self.payload["production_eligible"])

    def test_runtime_used_real_processor_without_model_or_weights(self) -> None:
        runtime = self.payload["runtime_result"]
        self.assertTrue(runtime["processor_instantiated"])
        self.assertTrue(runtime["tokenizer_instantiated"])
        self.assertTrue(runtime["preprocessing_run"])
        self.assertFalse(runtime["model_instantiated"])
        self.assertFalse(runtime["model_weights_named"])
        self.assertFalse(runtime["model_weights_read"])
        self.assertFalse(runtime["policy_inference_run"])
        self.assertFalse(runtime["network_accessed"])
        self.assertFalse(runtime["hardware_accessed"])

    def test_model_input_camera_order_and_missing_mask_are_exact(self) -> None:
        image_inputs = self.payload["runtime_result"]["model_image_inputs"]
        self.assertEqual(image_inputs["ordered_keys"], [
            "observation.images.base_0_rgb",
            "observation.images.left_wrist_0_rgb",
            "observation.images.right_wrist_0_rgb",
        ])
        self.assertEqual(image_inputs["image_resolution"], [224, 224])
        self.assertEqual([item["mask_value"] for item in image_inputs["entries"]], [True, True, False])
        self.assertEqual(image_inputs["entries"][-1]["fill_value"], -1.0)

    def test_action_and_queue_contract_is_declarative_only(self) -> None:
        action = self.payload["runtime_result"]["action_contract"]
        self.assertEqual(action["representation"], "absolute_joint_positions")
        self.assertEqual(action["chunk_size"], 50)
        self.assertEqual(action["n_action_steps"], 50)
        self.assertTrue(action["reset_required_before_first_sample"])
        self.assertFalse(action["queue_created"])
        self.assertFalse(action["queue_reset_executed"])
        self.assertFalse(action["action_proposal_created"])

    def test_state_support_audit_corrects_mean_std_semantics(self) -> None:
        audit = self.payload["runtime_result"]["state_support_audit"]
        self.assertEqual(audit["normalization_mode"], "MEAN_STD")
        self.assertFalse(audit["normalization_mode_mutated"])
        self.assertFalse(audit["clipping_applied"])
        self.assertEqual(audit["discretizer"]["reference_interval"], [-1.0, 1.0])
        self.assertFalse(
            audit["discretizer"]["reference_interval_is_hard_validity_domain"]
        )
        summary = audit["summary"]
        self.assertEqual(
            summary["outside_mean_plus_minus_std_joints"],
            ["wrist_flex", "gripper"],
        )
        self.assertEqual(summary["outside_q01_q99_joints"], ["wrist_flex"])
        self.assertEqual(summary["outside_observed_min_max_joints"], ["wrist_flex"])
        self.assertIn("gripper", summary["within_observed_support_joints"])
        self.assertFalse(summary["policy_shadow_input_valid_granted"])

    def test_wrist_is_outside_support_but_gripper_is_not(self) -> None:
        joints = {
            item["joint_name"]: item
            for item in self.payload["runtime_result"]["state_support_audit"]["joints"]
        }
        self.assertEqual(
            joints["wrist_flex"]["support_class"],
            "outside_observed_training_min_max",
        )
        self.assertFalse(joints["wrist_flex"]["within_observed_min_max"])
        self.assertEqual(joints["gripper"]["support_class"], "within_q01_q99")
        self.assertTrue(joints["gripper"]["within_observed_min_max"])
        self.assertTrue(joints["gripper"]["within_q01_q99"])

    def test_corrected_metadata_preserves_all_model_facing_tensor_hashes(self) -> None:
        runtime = self.payload["runtime_result"]
        outputs = runtime["preprocessor_outputs"]
        self.assertEqual(
            outputs["observation.state"]["sha256"],
            "586d37596d287f396c09f4adb072506daeddbee574196c6338825fc55830c3fd",
        )
        self.assertEqual(
            outputs["observation.language.tokens"]["sha256"],
            "29f09d673f6c1ee8e3e7e00453e609af118ca9d33d6ccd7d22d8f19d91b104df",
        )
        self.assertEqual(
            [entry["tensor"]["sha256"] for entry in runtime["model_image_inputs"]["entries"]],
            [
                "763cfd8b6e6137318f45be30231daf37d577deb54f7c5ce4ca04161cd16c0b66",
                "b45244549a2fda21698707efabd79659d5a92527c1787199c36082cb4029cfee",
                "811b0abfb7b806545700b3a1b9513d4ff52fd7da3ac337ae9ca69772f74e8415",
            ],
        )

    def test_model_call_contract_has_no_separate_state_or_execution(self) -> None:
        contract = self.payload["runtime_result"]["model_call_contract"]
        self.assertEqual(
            contract["positional_argument_order"],
            ["images", "img_masks", "tokens", "masks"],
        )
        self.assertFalse(contract["separate_state_tensor_passed_to_model"])
        self.assertTrue(contract["state_semantics_embedded_in_prompt_tokens"])
        self.assertFalse(contract["model_call_executed"])

    def test_schema_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(lambda item: item.__setitem__("schema_version", "wrong"))

    def test_source_reference_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["source_contract"].__setitem__("sha256", "0" * 64)
        )

    def test_reviewed_gate_reference_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["reviewed_input_gate"].__setitem__("identity_sha256", "0" * 64)
        )

    def test_fixture_to_live_relabeling_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item.__setitem__("evidence_mode", "tracked_production_review")
        )

    def test_review_shape_production_escalation_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["fixture_review_shape"].__setitem__("production_eligible", True)
        )

    def test_camera_role_ambiguity_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["fixture_input_spec"]["camera_role_assignments"][1].__setitem__(
                "source_key", "observation.images.top"
            )
        )

    def test_frame_selection_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["fixture_input_spec"]["selected_frames"][0].__setitem__(
                "frame_index", 0
            )
        )

    def test_png_hash_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["fixture_input_spec"]["frames"][0].__setitem__("png_sha256", "0" * 64)
        )

    def test_state_selection_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["fixture_input_spec"].__setitem__("state_selection", "q_before")
        )

    def test_joint_order_drift_is_rejected(self) -> None:
        def mutate(item: dict) -> None:
            item["fixture_input_spec"]["joint_order"][0:2] = reversed(
                item["fixture_input_spec"]["joint_order"][0:2]
            )

        self.assert_resigned_rejected(mutate)

    def test_state_units_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["fixture_input_spec"]["state_units"].__setitem__("gripper", "degrees")
        )

    def test_prompt_or_token_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"].__setitem__("prompt_text", "different")
        )

    def test_tensor_digest_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["preprocessor_outputs"]["observation.state"].__setitem__(
                "sha256", "0" * 64
            )
        )

    def test_missing_camera_mask_escalation_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["model_image_inputs"]["entries"][-1].__setitem__(
                "mask_value", True
            )
        )

    def test_action_horizon_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["action_contract"].__setitem__("n_action_steps", 49)
        )

    def test_state_support_audit_escalation_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["state_support_audit"]["summary"].__setitem__(
                "policy_shadow_input_valid_granted", True
            )
        )

    def test_silent_normalization_mode_change_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["state_support_audit"].__setitem__(
                "normalization_mode", "QUANTILES"
            )
        )

    def test_silent_clipping_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["state_support_audit"].__setitem__(
                "clipping_applied", True
            )
        )

    def test_discretizer_reference_interval_hard_domain_relabel_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["state_support_audit"]["discretizer"].__setitem__(
                "reference_interval_is_hard_validity_domain", True
            )
        )

    def test_gripper_false_rejection_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["state_support_audit"]["summary"][
                "outside_observed_min_max_joints"
            ].append("gripper")
        )

    def test_wrist_false_acceptance_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["state_support_audit"]["summary"][
                "outside_observed_min_max_joints"
            ].remove("wrist_flex")
        )

    def test_model_call_execution_claim_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["model_call_contract"].__setitem__(
                "model_call_executed", True
            )
        )

    def test_queue_reset_requirement_drift_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["runtime_result"]["action_contract"].__setitem__(
                "reset_required_before_first_sample", False
            )
        )

    def test_false_execution_claims_are_rejected(self) -> None:
        for field in (
            "model_instantiated",
            "model_weights_named",
            "model_weights_read",
            "policy_inference_run",
            "policy_shadow_run",
            "mujoco_replay_run",
            "network_accessed",
            "hardware_accessed",
            "physical_follower_commanded",
        ):
            with self.subTest(field=field):
                self.assert_resigned_rejected(
                    lambda item, field=field: item["runtime_result"].__setitem__(field, True)
                )

    def test_proof_label_or_capability_escalation_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["proof_labels"].append("policy_shadow_input_valid")
        )
        self.assert_resigned_rejected(
            lambda item: item["local_capabilities"].append("policy_shadow_input_valid")
        )

    def test_authority_denial_removal_is_rejected(self) -> None:
        self.assert_resigned_rejected(
            lambda item: item["authority_not_granted"].remove("policy_shadow_input_valid")
        )


if __name__ == "__main__":
    unittest.main()
