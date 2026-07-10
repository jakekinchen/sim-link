from __future__ import annotations

import unittest

import json
import tempfile

from pathlib import Path

from scenesmith.robot_lab.autolearn import (
    PromotionGate,
    decide_promotion,
    is_dagger_correction_frame,
    policy_expert_delta_l2,
    select_training_frames,
    summarize_evaluation,
    validate_dagger_episode_scope,
)
from scenesmith.robot_lab.autolearn_cycle import (
    CycleConfig,
    CycleRunner,
    StageResult,
)
from scripts.robot_lab.export_intervention_dataset import _features
from scripts.robot_lab.finalize_pi05_checkpoint import _compare_normalization
from scripts.robot_lab.merge_pi05_training_datasets import (
    _pin_normalization_stats,
    _validate_compatible,
)


def _frame(source: str, *, intervention: bool = False, motion: str = "contact_physics"):
    return {
        "action_source": source,
        "is_intervention": intervention,
        "human_action": [0.2] * 6 if intervention else None,
        "policy_action": [0.0] * 6,
        "executed_action": [0.1] * 6,
        "object_motion_mode": motion,
    }


def _episode(
    seed: int,
    *,
    success: bool,
    sorted_count: int,
    controller_frames: int = 0,
    grasp_activations: int = 0,
    scripted: bool = False,
    physical: bool = False,
):
    return {
        "seed": seed,
        "status": "pass" if success else "fail",
        "final_score": {"success": success, "sorted_count": sorted_count},
        "intervention": {
            "frames": 0,
            "physical_follower_commanded": physical,
            "safety_report": {"physical_follower_commanded": physical},
        },
        "policy_runtime": {"physical_follower_commanded": physical},
        "proof_scope": {
            "scripted_object_motion": scripted,
            "object_motion_modes": ["contact_physics_neural_policy"],
            "grasp_assist": {
                "activation_count": grasp_activations,
                "post_place_controller": {
                    "executed_frames": controller_frames,
                    "tray_transfer_executed_frames": 0,
                    "recovery_pick_executed_frames": 0,
                },
            },
        },
    }


class DaggerFrameTests(unittest.TestCase):
    def test_selects_controller_and_human_corrections_only(self):
        policy = _frame("policy")
        transfer = _frame("contact_gated_tray_transfer")
        human = _frame("physical_leader", intervention=True)
        selected = select_training_frames([policy, transfer, human], "dagger_corrections")
        self.assertEqual(selected, [transfer, human])
        self.assertTrue(is_dagger_correction_frame(transfer))
        self.assertAlmostEqual(policy_expert_delta_l2(transfer), 6**0.5 * 0.1)

    def test_rejects_scripted_motion(self):
        frame = _frame("contact_gated_recovery_pick", motion="scripted_cube_teleport")
        self.assertFalse(is_dagger_correction_frame(frame))

    def test_scope_requires_neural_non_scripted_episode(self):
        summary = {
            "proof_scope": {
                "scripted_object_motion": False,
                "neural_policy_actions_applied_to_simulation": True,
            },
            "intervention": {"physical_follower_commanded": False},
            "policy_runtime": {"physical_follower_commanded": False},
        }
        validate_dagger_episode_scope(summary, [_frame("contact_reflex_post_place")])
        summary["proof_scope"]["scripted_object_motion"] = True
        with self.assertRaisesRegex(ValueError, "scripted_object_motion"):
            validate_dagger_episode_scope(summary, [_frame("contact_reflex_post_place")])

    def test_causal_export_schema_matches_six_axis_training_contract(self):
        features = _features(224, "pi05_causal")
        self.assertEqual(
            set(features),
            {
                "observation.images.top",
                "observation.images.wrist",
                "observation.state",
                "action",
            },
        )
        self.assertEqual(features["action"]["shape"], (6,))
        _validate_compatible(
            {"features": features},
            {"features": json.loads(json.dumps(features))},
        )

    def test_merge_rejects_incompatible_correction_schema(self):
        base = _features(224, "pi05_causal")
        corrections = _features(224, "pi05_causal")
        corrections["action"]["shape"] = (32,)
        with self.assertRaisesRegex(ValueError, "definitions differ"):
            _validate_compatible({"features": base}, {"features": corrections})

    def test_merge_pins_normalization_stats_from_accepted_base(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source" / "meta"
            output = root / "output" / "meta"
            source.mkdir(parents=True)
            output.mkdir(parents=True)
            expected = {
                "action": {"mean": [1.0], "std": [2.0]},
                "observation.state": {"mean": [3.0], "std": [4.0]},
            }
            (source / "stats.json").write_text(json.dumps(expected), encoding="utf-8")
            (output / "stats.json").write_text(json.dumps({"action": {}}), encoding="utf-8")

            contract = _pin_normalization_stats(root / "source", root / "output")

            self.assertEqual(contract["mode"], "pinned")
            self.assertEqual(
                json.loads((output / "stats.json").read_text(encoding="utf-8")), expected
            )
            self.assertEqual(
                contract["source_stats_sha256"], contract["output_stats_sha256"]
            )

    def test_checkpoint_normalization_comparison_rejects_drift(self):
        expected = {
            "action": {"mean": [1.0, 2.0], "std": [3.0, 4.0]},
            "observation.state": {"mean": [5.0], "std": [6.0]},
        }
        actual = {
            "action.mean": [1.0, 2.0],
            "action.std": [3.0, 4.0],
            "observation.state.mean": [5.0],
            "observation.state.std": [6.0],
        }
        _compare_normalization(expected, actual, ("action", "observation.state"))
        actual["action.mean"][1] = 20.0
        with self.assertRaisesRegex(ValueError, "differs for action.mean"):
            _compare_normalization(expected, actual, ("action",))


class PromotionTests(unittest.TestCase):
    def test_accepts_complete_unassisted_improvement(self):
        seeds = (7100, 7101, 7102, 7103)
        baseline = summarize_evaluation(
            {"results": [_episode(seed, success=False, sorted_count=1) for seed in seeds]}
        )
        candidate = summarize_evaluation(
            {"results": [_episode(seed, success=True, sorted_count=4) for seed in seeds]}
        )
        decision = decide_promotion(
            baseline,
            candidate,
            PromotionGate(expected_seeds=seeds, min_pure_success_rate=0.75),
        )
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reasons, ())

    def test_rejects_assisted_success(self):
        seeds = (7100, 7101)
        baseline = summarize_evaluation(
            {"results": [_episode(seed, success=False, sorted_count=0) for seed in seeds]}
        )
        candidate = summarize_evaluation(
            {
                "results": [
                    _episode(seed, success=True, sorted_count=4, controller_frames=50)
                    for seed in seeds
                ]
            }
        )
        decision = decide_promotion(
            baseline,
            candidate,
            PromotionGate(expected_seeds=seeds, min_pure_success_rate=0.5),
        )
        self.assertFalse(decision.accepted)
        self.assertIn("candidate_contains_controller_or_human_assistance", decision.reasons)

    def test_rejects_incomplete_seed_set_and_physical_command(self):
        baseline = summarize_evaluation(
            {"results": [_episode(7100, success=False, sorted_count=0)]}
        )
        candidate = summarize_evaluation(
            {"results": [_episode(7100, success=True, sorted_count=4, physical=True)]}
        )
        decision = decide_promotion(
            baseline,
            candidate,
            PromotionGate(expected_seeds=(7100, 7101), min_pure_success_rate=0.5),
        )
        self.assertFalse(decision.accepted)
        self.assertIn("candidate_seed_set_incomplete", decision.reasons)
        self.assertIn("candidate_commanded_physical_follower", decision.reasons)


class _FakeStageRunner:
    def __init__(self, exit_codes=None, raises=None):
        self.exit_codes = exit_codes or {}
        self.raises = raises or {}
        self.calls = []

    def run(self, stage, *, repo_root):
        self.calls.append(stage.name)
        if stage.name in self.raises:
            raise self.raises[stage.name]
        return StageResult(
            exit_code=self.exit_codes.get(stage.name, 0),
            duration_s=0.01,
            log_path=f"outputs/{stage.name}.log",
            log_sha256="0" * 64,
        )


def _cycle_payload(*, external=False):
    payload = {
        "schema_version": "scenesmith.pi05_autolearn.v1",
        "cycle_id": "test-cycle",
        "train_seeds": [7000, 7001],
        "eval_seeds": [7100, 7101],
        "accepted_model": "models/accepted",
        "candidate_model": "models/candidate",
        "manifest_path": "experiments/pi05_autolearn/cycles/test-cycle.json",
        "accepted_pointer_path": "experiments/pi05_autolearn/accepted.json",
        "baseline_evaluation": "outputs/baseline.json",
        "candidate_evaluation": "outputs/candidate.json",
        "stages": [
            {
                "name": "train",
                "argv": ["trainer", "--steps={max_steps}"],
                "timeout_s": 30,
            }
        ],
        "training": {"stage": "train", "max_steps": 25},
        "git": {"auto_commit": False, "clean_paths": ["scenesmith/robot_lab"]},
        "promotion": {"min_pure_success_rate": 0.5},
    }
    if external:
        payload["external_compute"] = {
            "provider": "brev",
            "cleanup": {
                "name": "brev_cleanup",
                "argv": ["brev", "stop", "test-gpu"],
                "timeout_s": 30,
            },
            "inventory": {
                "name": "brev_inventory",
                "argv": ["brev", "ls", "--json"],
                "timeout_s": 30,
            },
        }
    return payload


class CycleConfigTests(unittest.TestCase):
    def test_rejects_seed_overlap(self):
        payload = _cycle_payload()
        payload["eval_seeds"] = [7001, 7100]
        with self.assertRaisesRegex(ValueError, "overlap"):
            CycleConfig.from_dict(payload)

    def test_rejects_noncontiguous_seed_lists(self):
        payload = _cycle_payload()
        payload["train_seeds"] = [7000, 7002]
        with self.assertRaisesRegex(ValueError, "contiguous"):
            CycleConfig.from_dict(payload)

    def test_rejects_shell_command_and_unbounded_training(self):
        payload = _cycle_payload()
        payload["stages"][0]["argv"] = ["bash", "-c", "train forever"]
        with self.assertRaisesRegex(ValueError, "shell -c"):
            CycleConfig.from_dict(payload)

        payload = _cycle_payload()
        payload["stages"][0]["argv"] = ["trainer"]
        with self.assertRaisesRegex(ValueError, "finite max_steps"):
            CycleConfig.from_dict(payload)

    def test_allows_tokenizer_setting_but_rejects_credential_env(self):
        payload = _cycle_payload()
        payload["stages"][0]["env"] = {"TOKENIZERS_PARALLELISM": "false"}
        CycleConfig.from_dict(payload)
        payload["stages"][0]["env"] = {"HF_TOKEN": "do-not-store-this"}
        with self.assertRaisesRegex(ValueError, "credentials"):
            CycleConfig.from_dict(payload)

    def test_dry_run_writes_manifest_without_running_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "cycle.json"
            config_path.write_text(json.dumps(_cycle_payload()), encoding="utf-8")
            config = CycleConfig.from_dict(_cycle_payload())
            fake = _FakeStageRunner()
            manifest = CycleRunner(
                config,
                repo_root=root,
                config_path=config_path,
                stage_runner=fake,
                enforce_git=False,
            ).run(dry_run=True)
            self.assertEqual(manifest["status"], "dry_run")
            self.assertEqual(fake.calls, [])
            self.assertTrue(
                (root / "experiments/pi05_autolearn/cycles/test-cycle.json").is_file()
            )

    def test_brev_cleanup_runs_after_training_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = _cycle_payload(external=True)
            config_path = root / "cycle.json"
            config_path.write_text(json.dumps(payload), encoding="utf-8")
            fake = _FakeStageRunner(exit_codes={"train": 2})
            runner = CycleRunner(
                CycleConfig.from_dict(payload),
                repo_root=root,
                config_path=config_path,
                stage_runner=fake,
                enforce_git=False,
            )
            with self.assertRaisesRegex(Exception, "Stage train exited 2"):
                runner.run()
            self.assertEqual(fake.calls, ["train", "brev_cleanup", "brev_inventory"])

    def test_keyboard_interrupt_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = _cycle_payload()
            config_path = root / "cycle.json"
            config_path.write_text(json.dumps(payload), encoding="utf-8")
            fake = _FakeStageRunner(raises={"train": KeyboardInterrupt()})
            runner = CycleRunner(
                CycleConfig.from_dict(payload),
                repo_root=root,
                config_path=config_path,
                stage_runner=fake,
                enforce_git=False,
            )
            with self.assertRaises(KeyboardInterrupt):
                runner.run()
            manifest = json.loads(
                (root / "experiments/pi05_autolearn/cycles/test-cycle.json").read_text()
            )
            self.assertEqual(manifest["status"], "interrupted")
            self.assertEqual(manifest["error"]["type"], "KeyboardInterrupt")

    def test_resume_skips_matching_successful_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = _cycle_payload()
            config_path = root / "cycle.json"
            config_path.write_text(json.dumps(payload), encoding="utf-8")
            (root / "outputs").mkdir()
            evaluation = {"results": [_episode(7100, success=False, sorted_count=0), _episode(7101, success=False, sorted_count=0)]}
            (root / "outputs/baseline.json").write_text(json.dumps(evaluation))
            (root / "outputs/candidate.json").write_text(json.dumps(evaluation))
            manifest_path = root / "experiments/pi05_autolearn/cycles/test-cycle.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "cycle_id": "test-cycle",
                        "status": "failed",
                        "source_commit": "old",
                        "config_sha256": "old",
                        "stages": [
                            {
                                "name": "train",
                                "argv": ["trainer", "--steps=25"],
                                "result": {
                                    "exit_code": 0,
                                    "duration_s": 1.0,
                                    "log_path": "outputs/train.log",
                                    "log_sha256": "0" * 64,
                                },
                            }
                        ],
                    }
                )
            )
            fake = _FakeStageRunner()
            manifest = CycleRunner(
                CycleConfig.from_dict(payload),
                repo_root=root,
                config_path=config_path,
                stage_runner=fake,
                enforce_git=False,
            ).run(resume=True)
            self.assertEqual(fake.calls, [])
            self.assertEqual(manifest["status"], "complete")
            self.assertTrue(manifest["stages"][0]["resumed"])


if __name__ == "__main__":
    unittest.main()
