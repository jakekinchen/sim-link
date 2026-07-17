from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path

from scenesmith.robot_lab.project_state_pointer_sync import (
    apply_pointer_targets,
    derive_latest_verified_boundary,
    derive_pointer_targets,
    find_pointer_drift,
    parse_ledger_current_task,
    parse_ledger_next_task,
    rewrite_pointer_fields,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC_CLI = REPO_ROOT / "scripts/robot_lab/sync_project_state_pointers.py"
FAKE_COMMIT = "76cb16ddbc46967a1c558216dad9780c701d42e6"

LEDGER_TEXT = """# Ledger

Updated: 2026-07-13

```text
training_lock: closed
current_task: T17.4 pending after verified T17.3; compile source-bound frames
next_task: T18.1
next_step: compile deterministic frame/segment tables
```
"""

PROJECT_STATE = {
    "schema_version": "scenesmith.project_state.v1",
    "updated": "2026-07-13",
    "current_task": "T19.0e",
    "next_eligible_task": "T19.0e",
    "latest_verified_task_implementation_boundary": {
        "brief_id": "093",
        "commit": "0ff508c70c7ad3d165088baf26f170cb4dca9b5b",
        "reviewer_decision_id": "119",
        "summary": "analytic_antipodal_contact_gate_with_actual_grasp_withheld",
    },
    "training_lock": "closed",
    "tasks": {
        "T16.6": {
            "state": "pending",
            "latest_verified_brief_id": None,
            "review_decision_id": None,
        },
        "T19.0e": {
            "state": "verified",
            "latest_verified_brief_id": "099",
            "review_decision_id": "125",
            "result": "bilateral explicit-pad contact in two candidates",
            "artifact": {"path": "configurations/robot_lab/old_artifact.json"},
        },
        "T17.3": {
            "state": "verified",
            "latest_verified_brief_id": "109",
            "review_decision_id": "135",
            "result": (
                "immutable fixture-scoped normalization/preprocessing bundle"
                " binds canonical processor"
            ),
            "artifact": {"path": "configurations/robot_lab/normalization_bundle.json"},
        },
    },
}


class LedgerCurrentTaskParseTest(unittest.TestCase):
    def test_parses_front_matter_current_task(self) -> None:
        self.assertEqual(parse_ledger_current_task(LEDGER_TEXT), "T17.4")

    def test_rejects_missing_current_task_line(self) -> None:
        with self.assertRaises(ValueError):
            parse_ledger_current_task("# Ledger\n\nno front matter here\n")

    def test_rejects_non_task_token(self) -> None:
        with self.assertRaises(ValueError):
            parse_ledger_current_task("current_task: unknown pending\n")

    def test_accepts_suffixed_task_ids(self) -> None:
        self.assertEqual(
            parse_ledger_current_task("current_task: T16.2b-A in_progress\n"),
            "T16.2b-A",
        )

    def test_accepts_fork_and_support_task_ids(self) -> None:
        for task_id in ("F0b", "F3", "K2", "T20.43c-R2"):
            with self.subTest(task_id=task_id):
                self.assertEqual(
                    parse_ledger_current_task(f"current_task: {task_id} active\n"),
                    task_id,
                )

    def test_parses_distinct_next_task_and_falls_back_to_current(self) -> None:
        self.assertEqual(parse_ledger_next_task(LEDGER_TEXT), "T18.1")
        self.assertEqual(
            parse_ledger_next_task("current_task: F3 in_progress\n"),
            "F3",
        )

    def test_rejects_duplicate_or_invalid_next_task(self) -> None:
        with self.assertRaises(ValueError):
            parse_ledger_next_task(
                "current_task: F3 active\nnext_task: F3\nnext_task: K2\n"
            )
        with self.assertRaises(ValueError):
            parse_ledger_next_task(
                "current_task: F3 active\nnext_task: unknown\n"
            )


class LatestVerifiedBoundaryTest(unittest.TestCase):
    def test_selects_highest_verified_brief(self) -> None:
        boundary = derive_latest_verified_boundary(PROJECT_STATE["tasks"])
        self.assertEqual(boundary["task_id"], "T17.3")
        self.assertEqual(boundary["brief_id"], "109")
        self.assertEqual(boundary["reviewer_decision_id"], "135")
        self.assertEqual(
            boundary["artifact_path"],
            "configurations/robot_lab/normalization_bundle.json",
        )

    def test_rejects_tasks_without_verified_briefs(self) -> None:
        with self.assertRaises(ValueError):
            derive_latest_verified_boundary(
                {"T1": {"state": "pending", "latest_verified_brief_id": None}}
            )


class PointerTargetsAndDriftTest(unittest.TestCase):
    def build_targets(self) -> dict:
        return derive_pointer_targets(
            PROJECT_STATE, LEDGER_TEXT, boundary_commit=FAKE_COMMIT
        )

    def test_targets_follow_ledger_and_tasks(self) -> None:
        targets = self.build_targets()
        self.assertEqual(targets["current_task"], "T17.4")
        self.assertEqual(targets["next_eligible_task"], "T18.1")
        boundary = targets["latest_verified_task_implementation_boundary"]
        self.assertEqual(boundary["brief_id"], "109")
        self.assertEqual(boundary["commit"], FAKE_COMMIT)
        self.assertEqual(boundary["reviewer_decision_id"], "135")
        self.assertTrue(boundary["summary"].startswith("immutable_fixture_scoped"))

    def test_stale_pointers_report_drift(self) -> None:
        drift = find_pointer_drift(PROJECT_STATE, self.build_targets())
        self.assertGreaterEqual(len(drift), 3)
        self.assertTrue(any("current_task" in line for line in drift))
        self.assertTrue(any("brief_id" in line for line in drift))

    def test_apply_then_check_is_clean(self) -> None:
        targets = self.build_targets()
        state = apply_pointer_targets(copy.deepcopy(PROJECT_STATE), targets)
        self.assertEqual(state["current_task"], "T17.4")
        self.assertEqual(state["next_eligible_task"], "T18.1")
        self.assertEqual(
            state["latest_verified_task_implementation_boundary"]["commit"],
            FAKE_COMMIT,
        )
        self.assertEqual(state["training_lock"], "closed")
        self.assertEqual(find_pointer_drift(state, targets), [])


class RewritePreservesFormattingTest(unittest.TestCase):
    STATE_TEXT = (
        "{\n"
        '  "schema_version": "scenesmith.project_state.v1",\n'
        '  "updated": "2026-07-10",\n'
        '  "latest_verified_task_implementation_boundary": {\n'
        '    "brief_id": "093",\n'
        '    "commit": "0ff508c70c7ad3d165088baf26f170cb4dca9b5b",\n'
        '    "reviewer_decision_id": "119",\n'
        '    "summary": "analytic_antipodal_contact_gate"\n'
        "  },\n"
        '  "permit": {"body": {"role": "follower"}, "counts": [0, 0]},\n'
        '  "current_task": "T19.0e",\n'
        '  "next_eligible_task": "T19.0e",\n'
        '  "tasks": {\n'
        '    "T17.3": {\n'
        '      "state": "verified",\n'
        '      "latest_verified_brief_id": "109",\n'
        '      "review_decision_id": "135",\n'
        '      "result": "immutable fixture-scoped bundle",\n'
        '      "commit": "should_not_change",\n'
        '      "artifact": {"path": "configurations/x.json"}\n'
        "    }\n"
        "  }\n"
        "}\n"
    )

    def test_rewrites_only_pointer_lines(self) -> None:
        state = json.loads(self.STATE_TEXT)
        targets = derive_pointer_targets(
            state,
            "current_task: T17.4 pending\n",
            boundary_commit=FAKE_COMMIT,
        )
        rewritten = rewrite_pointer_fields(
            self.STATE_TEXT, targets, updated="2026-07-13"
        )
        # Compact formatting outside the pointer fields must be untouched.
        self.assertIn(
            '"permit": {"body": {"role": "follower"}, "counts": [0, 0]},', rewritten
        )
        self.assertIn('"commit": "should_not_change",', rewritten)
        self.assertIn('"updated": "2026-07-13",', rewritten)
        self.assertIn('"current_task": "T17.4",', rewritten)
        reloaded = json.loads(rewritten)
        expected = apply_pointer_targets(
            json.loads(self.STATE_TEXT), targets, updated="2026-07-13"
        )
        self.assertEqual(reloaded, expected)
        self.assertEqual(find_pointer_drift(reloaded, targets), [])

    def test_rejects_missing_anchor(self) -> None:
        state = json.loads(self.STATE_TEXT)
        targets = derive_pointer_targets(
            state, "current_task: T17.4 pending\n", boundary_commit=FAKE_COMMIT
        )
        without_pointer = self.STATE_TEXT.replace(
            '  "current_task": "T19.0e",\n', ""
        )
        with self.assertRaises(ValueError):
            rewrite_pointer_fields(without_pointer, targets, updated="2026-07-13")


class SyncCliTest(unittest.TestCase):
    def run_cli(self, *args: str, cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SYNC_CLI),
                "--project-state",
                str(cwd / "project_state.json"),
                "--ledger",
                str(cwd / "ledger.md"),
                "--boundary-commit",
                FAKE_COMMIT,
                *args,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_check_fails_then_apply_reconciles(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            (work / "project_state.json").write_text(
                json.dumps(PROJECT_STATE, indent=2) + "\n", encoding="utf-8"
            )
            (work / "ledger.md").write_text(LEDGER_TEXT, encoding="utf-8")

            stale = self.run_cli("--check", cwd=work)
            self.assertEqual(stale.returncode, 1, stale.stdout + stale.stderr)
            self.assertIn("current_task", stale.stdout)

            applied = self.run_cli("--apply", cwd=work)
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)

            reloaded = json.loads((work / "project_state.json").read_text())
            self.assertEqual(reloaded["current_task"], "T17.4")
            self.assertEqual(
                reloaded["latest_verified_task_implementation_boundary"]["brief_id"],
                "109",
            )

            clean = self.run_cli("--check", cwd=work)
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)


if __name__ == "__main__":
    unittest.main()
