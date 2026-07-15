from __future__ import annotations

import copy
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_35b_pi05_coverage_correction import (
    ACTUAL_PI05_MODULES,
    DECLARED_DEFAULT_PEFT_MODULES,
    build_correction,
    verify_correction,
)


class T2035bPi05CoverageCorrectionTests(unittest.TestCase):
    def test_current_saved_modules_fail_only_real_time_mlp_coverage(self) -> None:
        result = self._build(
            saved_modules=["model.action_in_proj", "model.action_out_proj"]
        )
        verify_correction(result)
        self.assertFalse(result["all_real_pi05_action_time_pathways_wrapped"])
        self.assertEqual(
            result["missing_real_pi05_action_time_modules"],
            ["model.time_mlp_in", "model.time_mlp_out"],
        )
        self.assertTrue(result["state_proj_intentionally_absent"])
        self.assertEqual(
            result["stale_or_nonexistent_declared_peft_modules"],
            [
                "model.action_time_mlp_in",
                "model.action_time_mlp_out",
                "model.state_proj",
            ],
        )

    def test_complete_real_module_coverage_passes(self) -> None:
        result = self._build(saved_modules=list(ACTUAL_PI05_MODULES))
        self.assertTrue(result["all_real_pi05_action_time_pathways_wrapped"])
        self.assertEqual(result["missing_real_pi05_action_time_modules"], [])
        self.assertEqual(
            result["selected_next_hypothesis"],
            "gate_b_objective_floor_attainability_audit",
        )

    def test_source_module_and_default_name_drift_fail(self) -> None:
        kwargs = self._kwargs(
            saved_modules=["model.action_in_proj", "model.action_out_proj"]
        )
        kwargs["actual_pi05_modules"] = [*ACTUAL_PI05_MODULES, "model.state_proj"]
        with self.assertRaises(ValueError):
            build_correction(**kwargs)
        kwargs = self._kwargs(
            saved_modules=["model.action_in_proj", "model.action_out_proj"]
        )
        kwargs["declared_default_peft_modules"] = ["model.time_mlp_in"]
        with self.assertRaises(ValueError):
            build_correction(**kwargs)

    def test_signed_derived_mutation_fails(self) -> None:
        result = self._build(
            saved_modules=["model.action_in_proj", "model.action_out_proj"]
        )
        drift = copy.deepcopy(result)
        drift["state_proj_intentionally_absent"] = False
        with self.assertRaisesRegex(ValueError, "drifted"):
            verify_correction(sign_payload(drift))

    @classmethod
    def _build(cls, *, saved_modules: list[str]) -> dict:
        return build_correction(**cls._kwargs(saved_modules=saved_modules))

    @staticmethod
    def _kwargs(*, saved_modules: list[str]) -> dict:
        return {
            "t20_35a_audit_identity": "1" * 64,
            "lerobot_stack_identity": "2" * 64,
            "lerobot_revision": "3" * 40,
            "patch_set_sha256": "4" * 64,
            "pi05_source_sha256": "5" * 64,
            "actual_pi05_modules": list(ACTUAL_PI05_MODULES),
            "declared_default_peft_modules": list(
                DECLARED_DEFAULT_PEFT_MODULES
            ),
            "saved_lora_module_paths": saved_modules,
        }


if __name__ == "__main__":
    unittest.main()
