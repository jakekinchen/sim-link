"""T20.7 fixed-semantics four-model bake-off plan tests."""

from __future__ import annotations

import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.model_bakeoff import (
    MODEL_ORDER,
    build_model_canary_gate,
    build_model_canary_result,
    build_model_bakeoff_plan,
    verify_model_canary_gate,
    verify_model_canary_result,
    verify_model_bakeoff_plan,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
TRAINING_SPEC_PATH = (
    REPO_ROOT / "configurations/robot_lab/t20_1_simulation_training_spec.json"
)
SEMANTIC_PATH = REPO_ROOT / "configurations/robot_lab/t20_6_phase_outcome_evaluation.json"
STRICT_V2_PATH = (
    REPO_ROOT / "configurations/robot_lab/strict_anchor_grasp_evaluator_v2.fixture.json"
)


class ModelBakeoffPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = load_strict_json(PLAN_PATH)
        cls.training_spec = load_strict_json(TRAINING_SPEC_PATH)
        cls.semantic = load_strict_json(SEMANTIC_PATH)
        cls.strict_v2 = load_strict_json(STRICT_V2_PATH)

    def test_checked_plan_is_deterministic_and_source_bound(self) -> None:
        verify_model_bakeoff_plan(
            self.plan,
            self.training_spec,
            self.semantic,
            self.strict_v2,
            repo_root=REPO_ROOT,
        )
        self.assertEqual(
            self.plan,
            build_model_bakeoff_plan(
                self.training_spec,
                self.semantic,
                self.strict_v2,
                repo_root=REPO_ROOT,
            ),
        )

    def test_all_models_share_exact_sample_plan_and_behavior_contract(self) -> None:
        self.assertEqual([model["model_id"] for model in self.plan["models"]], list(MODEL_ORDER))
        starts = self.plan["common_sample_plan"]["ordered_train_starts"]
        self.assertEqual(len(starts), 20)
        self.assertEqual(len(set(starts)), 20)
        self.assertTrue(all(model["sample_plan_sha256"] == self.plan["common_sample_plan"]["ordered_train_starts_sha256"] for model in self.plan["models"]))
        self.assertEqual(self.plan["common_sample_plan"]["action_chunk_size"], 50)
        self.assertEqual(self.plan["evaluation_contract"]["held_out_episode_seed"], 2)
        self.assertEqual(self.plan["evaluation_contract"]["inference_seed"], 1703)
        smolvla = next(model for model in self.plan["models"] if model["model_id"] == "smolvla")
        self.assertEqual(smolvla["input_adapter"]["empty_camera_count"], 1)
        self.assertEqual(smolvla["input_adapter"]["empty_camera_value"], 0.0)

    def test_plan_records_initialization_asymmetry_and_denies_results(self) -> None:
        initializations = {model["model_id"]: model["initialization"] for model in self.plan["models"]}
        self.assertEqual(initializations["pi05"]["kind"], "pinned_pretrained_plus_rank4_lora")
        self.assertEqual(initializations["smolvla"]["kind"], "pinned_pretrained_plus_rank4_lora")
        self.assertEqual(initializations["act"]["kind"], "deterministic_compact_random_init")
        self.assertEqual(initializations["diffusion_policy"]["kind"], "deterministic_compact_random_init")
        self.assertFalse(self.plan["canary_executed"])
        self.assertFalse(self.plan["optimizer_training"])
        self.assertFalse(self.plan["simulation_policy_accepted"])

    def test_resigned_sample_or_authority_drift_is_rejected(self) -> None:
        for mutation in ("sample", "authority"):
            changed = copy.deepcopy(self.plan)
            if mutation == "sample":
                changed["common_sample_plan"]["ordered_train_starts"][0] = 1
            else:
                changed["simulation_policy_accepted"] = True
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(ValueError, "drifted"):
                    verify_model_bakeoff_plan(
                        sign_payload(changed),
                        self.training_spec,
                        self.semantic,
                        self.strict_v2,
                        repo_root=REPO_ROOT,
                    )

    def test_observed_canary_requires_finite_same_sample_and_denies_authority(self) -> None:
        observed = {
            "loss": 1.25,
            "gradient_norm": 0.75,
            "trainable_parameter_count": 10,
            "total_parameter_count": 20,
            "runtime": {"device": "mps", "torch": "test"},
            "source_weight_check": {"kind": "fixture"},
        }
        result = build_model_canary_result(self.plan, "act", observed)
        verify_model_canary_result(result, self.plan)
        self.assertFalse(result["optimizer_step_completed"])
        self.assertFalse(result["simulation_policy_accepted"])

        changed = copy.deepcopy(result)
        changed["sample_start"] = 1
        with self.assertRaisesRegex(ValueError, "linkage drifted"):
            verify_model_canary_result(sign_payload(changed), self.plan)

    def test_four_model_gate_requires_exact_model_order(self) -> None:
        observed = {
            "loss": 1.25,
            "gradient_norm": 0.75,
            "trainable_parameter_count": 10,
            "total_parameter_count": 20,
            "runtime": {"device": "mps", "torch": "test"},
            "source_weight_check": {"kind": "fixture"},
        }
        results = [
            (f"outputs/{model_id}.json", build_model_canary_result(self.plan, model_id, observed), "0" * 64)
            for model_id in MODEL_ORDER
        ]
        gate = build_model_canary_gate(self.plan, results)
        verify_model_canary_gate(gate, self.plan, results)
        self.assertTrue(gate["continuation_rung_authorized"])
        self.assertFalse(gate["optimizer_training"])
        with self.assertRaisesRegex(ValueError, "incomplete or out of order"):
            build_model_canary_gate(self.plan, list(reversed(results)))


if __name__ == "__main__":
    unittest.main()
