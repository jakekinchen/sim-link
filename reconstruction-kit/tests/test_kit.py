from __future__ import annotations

import copy
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "reconstruction-kit/scripts/kit.py"
SPEC = importlib.util.spec_from_file_location("reconstruction_kit", SCRIPT_PATH)
assert SPEC and SPEC.loader
kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)

ASSET_SCRIPT_PATH = REPO_ROOT / "reconstruction-kit/scripts/portable_assets.py"
ASSET_SPEC = importlib.util.spec_from_file_location(
    "reconstruction_assets", ASSET_SCRIPT_PATH
)
assert ASSET_SPEC and ASSET_SPEC.loader
assets = importlib.util.module_from_spec(ASSET_SPEC)
ASSET_SPEC.loader.exec_module(assets)

BOOTSTRAP_SCRIPT_PATH = REPO_ROOT / "reconstruction-kit/scripts/bootstrap.py"
BOOTSTRAP_SPEC = importlib.util.spec_from_file_location(
    "reconstruction_bootstrap", BOOTSTRAP_SCRIPT_PATH
)
assert BOOTSTRAP_SPEC and BOOTSTRAP_SPEC.loader
bootstrap = importlib.util.module_from_spec(BOOTSTRAP_SPEC)
BOOTSTRAP_SPEC.loader.exec_module(bootstrap)

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def local_markdown_targets(path: Path) -> list[Path]:
    targets: list[Path] = []
    for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
        target = raw_target.strip().strip("<>").split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        targets.append((path.parent / target).resolve())
    return targets


class ReconstructionKitTest(unittest.TestCase):
    def test_bootstrap_contract_is_non_authorizing(self) -> None:
        signed = bootstrap._sign(
            {
                "schema_version": bootstrap.SCHEMA_VERSION,
                "authority_transferred": False,
            }
        )
        self.assertEqual(
            signed["identity_sha256"], bootstrap._sign(signed)["identity_sha256"]
        )

    def test_minimal_portable_assets_verify_without_full_r0_or_authority(self) -> None:
        manifest = assets.verify_asset_pack()
        base = manifest["base_dataset"]
        self.assertEqual(base["episode_count"], 10)
        self.assertEqual(base["frame_count"], 2330)
        self.assertEqual(len(base["files"]), 5)
        self.assertEqual(len(manifest["trace_fixtures"]), 3)
        self.assertFalse(manifest["full_r0_dataset_included"])
        self.assertFalse(manifest["model_checkpoint_included"])
        self.assertFalse(manifest["private_observation_included"])
        self.assertFalse(manifest["authority_transferred"])
        for row in base["files"]:
            for chunk in row["chunks"]:
                self.assertLessEqual(chunk["size_bytes"], manifest["chunk_size_bytes"])

    def test_source_selection_retains_r2_result_but_excludes_live_authority(
        self,
    ) -> None:
        selection = kit.load_strict_json(kit.SELECTION_PATH)
        explicit = set(selection["explicit_paths"])
        patterns = selection["path_globs"]
        terminal_paths = {
            "configurations/robot_lab/t20_43c_r2_act_equivalence_receipt.json",
            "configurations/robot_lab/t20_43c_r2_act_final_receipt.json",
            "configurations/robot_lab/t20_43c_r2_act_replacement_marker.json",
            "configurations/robot_lab/t20_43c_r2_act_retention_receipt.json",
            "configurations/robot_lab/t20_43c_r2_act_scorecard.json",
            "configurations/robot_lab/t20_43c_r2_act_standard_result.json",
        }
        self.assertTrue(terminal_paths.issubset(explicit))
        live_paths = (
            "configurations/robot_lab/t20_43c_r2_act_authority_decision.json",
            "configurations/robot_lab/t20_43c_r2_act_authority_request.json",
            "configurations/robot_lab/t20_43c_r2_act_owner_authorization.json",
            "configurations/robot_lab/t20_43c_r2_act_permit.json",
            "configurations/robot_lab/t20_43c_r2_act_pre_run_acceptance.json",
            "configurations/robot_lab/t20_43c_r2_act_runtime_preflight.json",
        )
        for path in live_paths:
            with self.subTest(path=path):
                self.assertNotIn(path, explicit)
                self.assertFalse(
                    any(kit.fnmatch.fnmatchcase(path, pattern) for pattern in patterns)
                )
        self.assertNotIn(
            "scripts/robot_lab/run_t20_43c_manual_replacement.py",
            selection["python_seeds"],
        )

    def test_generated_manifest_is_current_and_verifies(self) -> None:
        expected = kit.build_manifest(REPO_ROOT)
        actual = kit.load_strict_json(kit.MANIFEST_PATH)
        self.assertEqual(expected, actual)
        kit.verify_manifest(actual, REPO_ROOT)
        self.assertFalse(actual["authority_transferred"])
        self.assertFalse(actual["learned_policy_success_claimed"])
        self.assertGreater(len(actual["files"]), 50)
        paths = [row["path"] for row in actual["files"]]
        self.assertIn(
            "scripts/robot_lab/render_rollout_mirror_v2.py",
            paths,
        )
        self.assertIn(
            "configurations/robot_lab/t20_43b_r1_act_attempt.json",
            paths,
        )
        self.assertIn(
            "configurations/robot_lab/t20_43b_r1_act_terminal_failure.json",
            paths,
        )
        self.assertIn(
            "docs/autonomous-workflow/hackathon-fork-annex-2026-07-16.md",
            paths,
        )
        self.assertIn(
            "docs/briefs/227-t20-43c-zero-update-act-continuation.md",
            paths,
        )
        self.assertIn(
            "docs/autonomous-workflow/owner-direction-2026-07-16-overnight-foundation.md",
            paths,
        )
        self.assertIn(
            "scenesmith/robot_lab/t20_43c_act_continuation.py",
            paths,
        )
        self.assertIn(
            "configurations/robot_lab/t20_43c_act_terminal_failure.json",
            paths,
        )
        for path in (
            "configurations/robot_lab/t20_43c_r2_act_equivalence_receipt.json",
            "configurations/robot_lab/t20_43c_r2_act_final_receipt.json",
            "configurations/robot_lab/t20_43c_r2_act_replacement_marker.json",
            "configurations/robot_lab/t20_43c_r2_act_retention_receipt.json",
            "configurations/robot_lab/t20_43c_r2_act_scorecard.json",
            "configurations/robot_lab/t20_43c_r2_act_standard_result.json",
        ):
            self.assertIn(path, paths)
        self.assertIn(
            "docs/reviewer-messages/318-verify-t20-43c-r2-terminal-negative.md",
            paths,
        )
        self.assertIn(
            "docs/session-logs/323-t20-43c-r2-terminal-negative.md",
            paths,
        )
        self.assertNotIn(
            "scripts/robot_lab/run_t20_43c_manual_replacement.py",
            paths,
        )
        self.assertIn(
            "docs/reviewer-messages/314-close-t20-43c-terminal-interruption.md",
            paths,
        )
        self.assertIn(
            "reconstruction-kit/assets/ASSET_MANIFEST.json",
            paths,
        )
        self.assertNotIn(
            "docs/autonomous-workflow/project_state.json",
            paths,
        )
        self.assertEqual(
            [row["path"] for row in actual["omitted_source_artifacts"]],
            [
                "configurations/robot_lab/t17_7_compiler_window_replay_audit.json",
                "configurations/robot_lab/t20_35o_flow_trajectory_consistency_result.json",
                "configurations/robot_lab/t20_35q_post_training_trajectory_result.json",
                "configurations/robot_lab/t20_35v_post_training_trajectory_result.json",
                "docs/autonomous-workflow/project_state.json",
            ],
        )
        state = kit.load_strict_json(kit.KIT_ROOT / "CURRENT_STATE.json")
        act = state["act_replacement"]
        self.assertEqual(
            act["status"],
            "verified_terminal_runtime_failure_capability_unresolved",
        )
        self.assertTrue(act["replacement_consumed"])
        self.assertEqual(act["optimizer_update_count"], 0)
        self.assertFalse(act["retry_authorized"])
        route = state["current_route"]
        self.assertEqual(route["task_id"], "K2")
        self.assertFalse(route["model_action_currently_authorized"])
        self.assertFalse(route["t20_43c_retry_authorized"])
        continuation = state["act_continuation"]
        self.assertEqual(
            continuation["status"], "inconclusive_owner_directive_interruption"
        )
        self.assertEqual(continuation["optimizer_update_count"], 728)
        self.assertTrue(continuation["marker_consumed"])
        self.assertFalse(continuation["infrastructure_failure"])
        self.assertFalse(continuation["trained_negative"])
        replacement = state["act_manual_replacement"]
        self.assertEqual(replacement["status"], "verified_terminal_negative")
        self.assertEqual(replacement["optimizer_update_count"], 10000)
        self.assertEqual(replacement["checkpoint_count"], 7)
        self.assertEqual(replacement["rollout_count"], 14)
        self.assertFalse(replacement["gate_c_passed"])
        self.assertFalse(replacement["infrastructure_failure"])
        self.assertFalse(replacement["retry_authorized"])
        self.assertEqual(
            replacement["final_chunk_50_only_failed_gate"],
            "release_final_contact_clear",
        )
        self.assertEqual(replacement["final_chunk_50_lift_m"], 0.037655304225193253)
        self.assertEqual(replacement["maximum_chunk_50_lift_m"], 0.04567430422519325)
        self.assertFalse(replacement["final_receding_10_grasp_hold"])
        self.assertEqual(replacement["final_receding_10_lift_m"], 0.000502)

    def test_fork_spine_keeps_current_and_future_contracts_distinct(self) -> None:
        required = [
            REPO_ROOT / "docs/README.md",
            REPO_ROOT / "docs/architecture.md",
            REPO_ROOT / "docs/sim-link-mvp-execution-plan.md",
            REPO_ROOT / "reconstruction-kit/README.md",
            REPO_ROOT / "reconstruction-kit/ARCHITECTURE.md",
            REPO_ROOT / "reconstruction-kit/FORWARD_PLAN.md",
            REPO_ROOT / "reconstruction-kit/QUICKSTART.md",
            REPO_ROOT / "reconstruction-kit/RESULTS_AND_LESSONS.md",
            REPO_ROOT / "reconstruction-kit/templates/README.md",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in required)
        for phrase in (
            "pinned LeRobot",
            "joint state",
            "object pose",
            "60-frame",
            "CPU/fp32",
            "RUN_RECEIPT.json",
            "ACT",
            "state-based RL",
            "task registry",
            "gateway",
            "frozen held-out",
            "replayable",
            "separate evaluation",
        ):
            self.assertIn(phrase, combined)
        self.assertIn("dual-runtime", combined)
        self.assertIn("current-repo authority", combined)

    def test_current_and_reconstruction_document_links_resolve(self) -> None:
        documents = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "docs/README.md",
            REPO_ROOT / "docs/architecture.md",
            REPO_ROOT / "docs/current-and-historical.md",
            REPO_ROOT / "docs/requirements-and-contracts.md",
            REPO_ROOT / "docs/sim-link-mvp-execution-plan.md",
            *sorted((REPO_ROOT / "reconstruction-kit").glob("*.md")),
        ]
        missing = []
        for document in documents:
            for target in local_markdown_targets(document):
                if not target.exists():
                    missing.append(f"{document.relative_to(REPO_ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_manifest_rejects_traversal_and_authority_escalation(self) -> None:
        manifest = kit.load_strict_json(kit.MANIFEST_PATH)
        traversal = copy.deepcopy(manifest)
        traversal["files"][0]["path"] = "../escape"
        traversal["identity_sha256"] = kit.payload_identity(traversal)
        with self.assertRaises(kit.KitError):
            kit.verify_manifest(traversal, REPO_ROOT)
        escalated = copy.deepcopy(manifest)
        escalated["authority_transferred"] = True
        escalated["identity_sha256"] = kit.payload_identity(escalated)
        with self.assertRaises(kit.KitError):
            kit.verify_manifest(escalated, REPO_ROOT)
        incomplete = copy.deepcopy(manifest)
        incomplete["files"].pop()
        incomplete["identity_sha256"] = kit.payload_identity(incomplete)
        with self.assertRaises(kit.KitError):
            kit.verify_manifest(incomplete, REPO_ROOT)

    def test_export_is_receipted_and_excludes_forbidden_classes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "new-repo"
            receipt = kit.export_kit(REPO_ROOT, destination)
            verified = kit.verify_export(destination)
            self.assertEqual(receipt, verified)
            self.assertTrue((destination / "README.md").is_file())
            self.assertTrue((destination / "tools/reconstruction_kit.py").is_file())
            self.assertTrue((destination / "tools/portable_assets.py").is_file())
            self.assertTrue((destination / "tools/bootstrap.py").is_file())
            self.assertTrue((destination / "tools/bootstrap_runtime.py").is_file())
            self.assertTrue(
                (
                    destination
                    / "docs/reconstruction/HARDWARE_READINESS_RGB_CAMERAS.md"
                ).is_file()
            )
            self.assertTrue(
                (
                    destination / "reconstruction-kit/assets/ASSET_MANIFEST.json"
                ).is_file()
            )
            self.assertTrue((destination / "tests/__init__.py").is_file())
            self.assertTrue((destination / "tests/unit/__init__.py").is_file())
            self.assertTrue(
                (
                    destination / "tests/fixtures/robot_lab/lerobot_stack/sample.json"
                ).is_file()
            )
            imported = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    "import scenesmith.robot_lab.artifact_contract; "
                    "import tests.unit.test_artifact_contract",
                ],
                cwd=destination,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(imported.returncode, 0, msg=imported.stderr)
            exported_documents = sorted(
                (destination / "docs/reconstruction").glob("*.md")
            )
            missing_links = []
            for document in exported_documents:
                for target in local_markdown_targets(document):
                    if not target.exists():
                        missing_links.append(
                            f"{document.relative_to(destination)} -> {target}"
                        )
            self.assertEqual(missing_links, [])
            self.assertFalse((destination / "outputs").exists())
            self.assertFalse((destination / "external").exists())
            self.assertFalse(receipt["bulk_outputs_copied"])
            self.assertFalse(receipt["external_checkouts_copied"])

    def test_export_rejects_existing_or_in_repo_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary) / "existing"
            existing.mkdir()
            with self.assertRaises(kit.KitError):
                kit.export_kit(REPO_ROOT, existing)
        with self.assertRaises(kit.KitError):
            kit.export_kit(REPO_ROOT, REPO_ROOT / "tmp/reconstruction-export")

    def test_export_verifier_rejects_unreceipted_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "new-repo"
            kit.export_kit(REPO_ROOT, destination)
            (destination / "unexpected.txt").write_text("drift\n")
            with self.assertRaises(kit.KitError):
                kit.verify_export(destination)


if __name__ == "__main__":
    unittest.main()
