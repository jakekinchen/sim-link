from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_35a_peft_module_coverage import (
    EXPECTED_EXPERT_LAYER_COUNT,
    EXPECTED_TARGET_MODULES,
    REQUIRED_ACTION_STATE_MODULES,
    build_coverage_audit,
    verify_coverage_audit,
)


class T2035aPeftModuleCoverageTests(unittest.TestCase):
    def test_complete_required_and_expert_pairs_pass(self) -> None:
        tensors = self._tensors(include_all_required=True)
        audit = self._audit(tensors)
        verify_coverage_audit(audit)
        self.assertTrue(audit["all_required_action_state_pathways_wrapped"])
        self.assertEqual(audit["missing_required_action_state_modules"], [])
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "gate_b_objective_floor_attainability_audit",
        )

    def test_missing_required_pairs_fail_and_route_capacity_ceiling(self) -> None:
        tensors = self._tensors(include_all_required=False)
        audit = self._audit(tensors)
        self.assertFalse(audit["all_required_action_state_pathways_wrapped"])
        self.assertEqual(
            audit["missing_required_action_state_modules"],
            [
                "model.action_time_mlp_in",
                "model.action_time_mlp_out",
                "model.state_proj",
            ],
        )
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "gate_b_expert_only_unfreeze_capacity_ceiling",
        )

    def test_unpaired_unknown_shape_nonfinite_and_count_drift_fail(self) -> None:
        base = self._tensors(include_all_required=True)
        cases = []
        unpaired = copy.deepcopy(base)
        unpaired.pop()
        cases.append(unpaired)
        unknown = copy.deepcopy(base)
        unknown[0]["key"] = "base_model.model.model.vision_proj.lora_A.weight"
        cases.append(unknown)
        wrong_rank = copy.deepcopy(base)
        wrong_rank[0]["shape"] = [8, 4]
        cases.append(wrong_rank)
        nonfinite = copy.deepcopy(base)
        nonfinite[0]["all_finite"] = False
        cases.append(nonfinite)
        duplicate = copy.deepcopy(base)
        duplicate.append(copy.deepcopy(duplicate[0]))
        cases.append(duplicate)
        for tensors in cases:
            with self.subTest(first=tensors[0]["key"], count=len(tensors)):
                with self.assertRaises(ValueError):
                    self._audit(tensors)

    def test_signed_derived_mutation_fails(self) -> None:
        audit = self._audit(self._tensors(include_all_required=False))
        drift = copy.deepcopy(audit)
        drift["all_required_action_state_pathways_wrapped"] = True
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_coverage_audit(sign_payload(drift))

    @staticmethod
    def _audit(tensors: list[dict]) -> dict:
        return build_coverage_audit(
            t20_35_result_identity="1" * 64,
            t20_35_run_identity="2" * 64,
            checkpoint_identity="3" * 64,
            adapter_config_sha256="4" * 64,
            adapter_model_sha256="5" * 64,
            target_modules=EXPECTED_TARGET_MODULES,
            tensor_descriptors=tensors,
            expected_trainable_parameter_count=sum(
                row["element_count"] for row in tensors
            ),
        )

    @staticmethod
    def _tensors(*, include_all_required: bool) -> list[dict]:
        modules = []
        for layer in range(EXPECTED_EXPERT_LAYER_COUNT):
            for projection in ("q_proj", "v_proj"):
                modules.append(
                    "model.paligemma_with_expert.gemma_expert.model.layers."
                    f"{layer}.self_attn.{projection}"
                )
        required = list(REQUIRED_ACTION_STATE_MODULES)
        if not include_all_required:
            required = ["model.action_in_proj", "model.action_out_proj"]
        modules.extend(required)
        rows = []
        for index, module in enumerate(modules):
            for side, shape in (("A", [16, 4]), ("B", [4, 16])):
                rows.append(
                    {
                        "key": f"base_model.model.{module}.lora_{side}.weight",
                        "shape": shape,
                        "dtype": "float32",
                        "element_count": 64,
                        "nonzero_count": 64,
                        "all_finite": True,
                        "content_sha256": f"{(index % 9) + 1}" * 64,
                    }
                )
        return rows


if __name__ == "__main__":
    unittest.main()
