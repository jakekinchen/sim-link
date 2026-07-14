"""Regression checks for the human-facing documentation front door."""

from __future__ import annotations

import unittest

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
REQUIRED_GUIDES = {
    "README.md": ("# SceneSmith SO-101 Program Documentation", "## Current State"),
    "architecture.md": (
        "# SceneSmith SO-101 Program Architecture",
        "## Technology Stack",
        "## Authority Flow",
    ),
    "requirements-and-contracts.md": ("# Requirements And Contract Index", "## Requirement Families"),
    "current-and-historical.md": ("# Current Versus Historical Documentation", "## The Current Truth Surface"),
    "decisions-and-adjuncts.md": ("# Decisions And Adjuncts", "## Evaluation Rule"),
    "robo-scan-integration.md": (
        "# Robo Scan Integration Boundary",
        "## Authority-Preserving Handoff",
        "## Required Future Export Receipt",
    ),
    "robo-scan-sim-link-integration-roadmap.md": (
        "# Robo Scan And Sim-Link Integration Roadmap",
        "## Final Repository Ownership",
        "## Integration Phases",
        "## Definition Of Integrated",
    ),
}


class DocumentationInformationArchitectureTests(unittest.TestCase):
    def test_required_guides_exist_with_stable_entry_headings(self) -> None:
        for relative, headings in REQUIRED_GUIDES.items():
            with self.subTest(relative=relative):
                content = (DOCS / relative).read_text(encoding="utf-8")
                for heading in headings:
                    self.assertIn(heading, content)

    def test_root_and_workflow_entry_points_link_to_hub(self) -> None:
        root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        workflow_readme = (
            DOCS / "autonomous-workflow" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertIn("docs/README.md", root_readme)
        self.assertIn("../README.md", workflow_readme)

    def test_hub_routes_to_canonical_state_and_explainers(self) -> None:
        content = (DOCS / "README.md").read_text(encoding="utf-8")
        for target in (
            "../GOAL.md",
            "autonomous-workflow/project_state.json",
            "architecture.md",
            "requirements-and-contracts.md",
            "current-and-historical.md",
            "decisions-and-adjuncts.md",
            "robo-scan-integration.md",
            "robo-scan-sim-link-integration-roadmap.md",
        ):
            with self.subTest(target=target):
                self.assertIn(target, content)

    def test_document_map_owns_the_new_system_guides(self) -> None:
        content = (
            DOCS / "autonomous-workflow" / "07-document-and-artifact-map.md"
        ).read_text(encoding="utf-8")
        for target in (
            "docs/README.md",
            "docs/architecture.md",
            "docs/requirements-and-contracts.md",
            "docs/current-and-historical.md",
            "docs/robo-scan-integration.md",
            "docs/robo-scan-sim-link-integration-roadmap.md",
        ):
            with self.subTest(target=target):
                self.assertIn(target, content)

    def test_new_reader_path_has_no_broken_local_markdown_links(self) -> None:
        documents = (
            REPO_ROOT / "README.md",
            DOCS / "README.md",
            DOCS / "architecture.md",
            DOCS / "requirements-and-contracts.md",
            DOCS / "current-and-historical.md",
            DOCS / "decisions-and-adjuncts.md",
            DOCS / "robo-scan-integration.md",
            DOCS / "robo-scan-sim-link-integration-roadmap.md",
            DOCS / "autonomous-workflow" / "README.md",
        )
        for document in documents:
            content = document.read_text(encoding="utf-8")
            for target in re.findall(r"(?<!!)(?:!?)\[[^]]+\]\(([^)]+)\)", content):
                target = target.split("#", maxsplit=1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                with self.subTest(document=document, target=target):
                    self.assertTrue(
                        (document.parent / target).resolve().exists(),
                        f"broken local documentation link: {target}",
                    )

    def test_robo_scan_is_an_explicit_handoff_not_a_runtime_dependency(self) -> None:
        handoff = (DOCS / "robo-scan-integration.md").read_text(encoding="utf-8")
        architecture = (DOCS / "architecture.md").read_text(encoding="utf-8")
        requirements = (DOCS / "requirements-and-contracts.md").read_text(encoding="utf-8")
        roadmap = (DOCS / "robo-scan-sim-link-integration-roadmap.md").read_text(encoding="utf-8")

        for content, expected in (
            (handoff, "explicit artifact handoff"),
            (handoff, "automatic filesystem, package, Git, or runtime import"),
            (handoff, "reference-only"),
            (architecture, "Robo Scan Boundary"),
            (requirements, "R11: Scan/calibration handoff"),
            (roadmap, "Do not merge the Git repositories"),
            (roadmap, "### I2 - Independent Sim-Link Receipt Conformance"),
            (roadmap, "### I7 - Deduplicate Active Paths"),
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, content)

        forbidden_import = re.compile(
            r"^\\s*(?:from\\s+(?:environment_scanner|so101_scan)\\b|"
            r"import\\s+(?:environment_scanner|so101_scan)\\b)",
            re.MULTILINE,
        )
        for source in (REPO_ROOT / "scenesmith" / "robot_lab").rglob("*.py"):
            with self.subTest(source=source):
                self.assertIsNone(
                    forbidden_import.search(source.read_text(encoding="utf-8")),
                    f"Robo Scan runtime dependency requires a reviewed handoff implementation: {source}",
                )


if __name__ == "__main__":
    unittest.main()
