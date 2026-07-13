#!/usr/bin/env python3
"""Check or reconcile the top-level project-state pointer fields.

At every verification boundary the loop must run ``--apply`` so
``current_task``, ``next_eligible_task``, and
``latest_verified_task_implementation_boundary`` advance with the per-task
entries and the active ledger. ``--check`` fails closed when any pointer
disagrees with the derived truth.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.project_state_pointer_sync import (
    derive_latest_verified_boundary,
    derive_pointer_targets,
    find_pointer_drift,
    rewrite_pointer_fields,
)

DEFAULT_PROJECT_STATE = REPO_ROOT / "docs/autonomous-workflow/project_state.json"
DEFAULT_LEDGER = (
    REPO_ROOT / "docs/autonomous-workflow/experience-compiler-twin-task-ledger.md"
)


def resolve_boundary_commit(repo_root: Path, artifact_path: str | None) -> str:
    if artifact_path is None:
        raise SystemExit(
            "Latest verified task has no artifact path; pass --boundary-commit"
            " with the reviewed implementation commit."
        )
    result = subprocess.run(
        ["git", "-C", str(repo_root), "log", "-1", "--format=%H", "--", artifact_path],
        capture_output=True,
        text=True,
        check=True,
    )
    commit = result.stdout.strip()
    if not commit:
        raise SystemExit(
            f"No commit touches {artifact_path!r}; pass --boundary-commit"
            " with the reviewed implementation commit."
        )
    return commit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Fail with exit 1 when any top-level pointer is stale.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite the top-level pointers from the ledger and per-task entries.",
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--project-state", type=Path, default=DEFAULT_PROJECT_STATE)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument(
        "--boundary-commit",
        help="Full 40-hex reviewed implementation commit; overrides git derivation"
        " from the latest verified task's artifact path.",
    )
    args = parser.parse_args()

    state = load_strict_json(args.project_state)
    ledger_text = args.ledger.read_text(encoding="utf-8")

    if args.boundary_commit:
        boundary_commit = args.boundary_commit
    else:
        boundary = derive_latest_verified_boundary(state["tasks"])
        boundary_commit = resolve_boundary_commit(
            args.repo_root, boundary["artifact_path"]
        )

    targets = derive_pointer_targets(state, ledger_text, boundary_commit)
    drift = find_pointer_drift(state, targets)

    if args.check:
        if drift:
            print(f"project-state pointer drift in {args.project_state}:")
            for line in drift:
                print(f"  {line}")
            return 1
        print("project-state pointers consistent")
        return 0

    if not drift:
        print("project-state pointers already consistent; nothing to apply")
        return 0

    state_text = args.project_state.read_text(encoding="utf-8")
    rewritten = rewrite_pointer_fields(
        state_text, targets, updated=datetime.now().date().isoformat()
    )
    args.project_state.write_text(rewritten, encoding="utf-8")
    remaining = find_pointer_drift(load_strict_json(args.project_state), targets)
    if remaining:
        print("pointer drift remains after apply:")
        for line in remaining:
            print(f"  {line}")
        return 1
    print(f"reconciled project-state pointers in {args.project_state}:")
    for line in drift:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
