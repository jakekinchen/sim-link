import copy
import unittest

import numpy as np

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.grasp_evidence import KEYFRAME_PHASES, encode_png_image
from scenesmith.robot_lab.model_bakeoff_evaluation import GATE_NAMES
from scenesmith.robot_lab.release_semantics_reconciliation import (
    EVIDENCE_MODE,
    ROLLOUT_SCHEMA_VERSION,
    build_release_semantics_reconciliation,
    verify_release_semantics_reconciliation,
)


class ReleaseSemanticsReconciliationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.artifact = self._artifact()

    def test_valid_force_bearing_release_and_geometry_retreat_pass(self) -> None:
        verify_release_semantics_reconciliation(self.artifact)

    def test_resigned_mode_confusion_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.artifact)
        mutated.pop("identity_sha256")
        mutated["release_semantics"]["release_clearance_basis"] = (
            "geometry_contact_pair"
        )
        with self.assertRaisesRegex(ValueError, "release/retreat"):
            verify_release_semantics_reconciliation(sign_payload(mutated))

    def test_resigned_nested_rollout_or_authority_escalation_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.artifact)
        mutated.pop("identity_sha256")
        nested = mutated["corrected_oracle_rollout"]
        nested.pop("identity_sha256")
        nested["release_clearance_basis"] = "geometry_contact_pair"
        mutated["corrected_oracle_rollout"] = sign_payload(nested)
        with self.assertRaisesRegex(ValueError, "rollout"):
            verify_release_semantics_reconciliation(sign_payload(mutated))

        escalated = copy.deepcopy(self.artifact)
        escalated.pop("identity_sha256")
        escalated["simulation_policy_accepted"] = True
        with self.assertRaisesRegex(ValueError, "authority"):
            verify_release_semantics_reconciliation(sign_payload(escalated))

    @staticmethod
    def _artifact():
        exact = {
            "measured": 1,
            "threshold": 1,
            "comparison": "==",
            "margin": 0.0,
            "passed": True,
        }
        margins = {
            name: copy.deepcopy(exact)
            for name in GATE_NAMES
        }
        image = encode_png_image(
            np.zeros((256, 256, 3), dtype=np.uint8), image_size=256
        )
        rollout = sign_payload(
            {
                "schema_version": ROLLOUT_SCHEMA_VERSION,
                "task_id": "T20.10",
                "evidence_mode": EVIDENCE_MODE,
                "policy_label": "source_expert_oracle",
                "seed": 2,
                "frame_count": 244,
                "release_clearance_basis": "force_bearing_pad_or_nonpad_contact",
                "terminal_outcome": "strict_success",
                "simulation_semantic_strict_success": True,
                "policy_controls_owned_all_frames": True,
                "projected_action_frame_count": 0,
                "active_assist_frame_count": 0,
                "maximum_anchor_lift_m": 0.036,
                "policy_action_sequence_sha256": "a" * 64,
                "gate_margins": margins,
                "failed_gate_margins": [],
                "rendered_keyframes": [
                    {
                        "phase": phase,
                        "frame_index": index,
                        "images": {"top": image, "wrist": image},
                    }
                    for index, phase in enumerate(KEYFRAME_PHASES)
                ],
            }
        )
        diagnostics = {
            "frame_count": 244,
            "first_execution_divergence": None,
            "execution_adapter_reproduced_source_trajectory": True,
            "source_declared_strict_success": True,
            "oracle_strict_success": True,
            "source_vs_acceptance_semantic_mismatch": False,
            "release_clearance_basis": "force_bearing_pad_or_nonpad_contact",
            "release_settle_final_geometry_clear": False,
            "release_settle_final_force_bearing_contact_clear": True,
            "retreat_final_contact_clear": True,
        }
        return build_release_semantics_reconciliation(
            source_t20_9_ref={
                "identity_sha256": "b" * 64,
                "file_sha256": "c" * 64,
            },
            source_refs={
                "episode": {"source_action_sequence_sha256": "a" * 64}
            },
            t20_7_evaluation_ref={"strict_success_count": 0},
            oracle_rollout=rollout,
            diagnostics=diagnostics,
        )


if __name__ == "__main__":
    unittest.main()
