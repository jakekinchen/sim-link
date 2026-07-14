"""T20.7 fixed-semantics four-model bake-off plan tests."""

from __future__ import annotations

import copy
import unittest

from pathlib import Path

from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.model_bakeoff import (
    MODEL_ORDER,
    build_model_bakeoff_plan,
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


if __name__ == "__main__":
    unittest.main()
