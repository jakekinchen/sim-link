from __future__ import annotations

import copy
import importlib.util
import re
import tempfile
import unittest

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "reconstruction-kit/scripts/kit.py"
SPEC = importlib.util.spec_from_file_location("reconstruction_kit", SCRIPT_PATH)
assert SPEC and SPEC.loader
kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)

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
    def test_generated_manifest_is_current_and_verifies(self) -> None:
        expected = kit.build_manifest(REPO_ROOT)
        actual = kit.load_strict_json(kit.MANIFEST_PATH)
        self.assertEqual(expected, actual)
        kit.verify_manifest(actual, REPO_ROOT)
        self.assertFalse(actual["authority_transferred"])
        self.assertFalse(actual["learned_policy_success_claimed"])
        self.assertGreater(len(actual["files"]), 50)
        self.assertNotIn(
            "docs/autonomous-workflow/project_state.json",
            [row["path"] for row in actual["files"]],
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
