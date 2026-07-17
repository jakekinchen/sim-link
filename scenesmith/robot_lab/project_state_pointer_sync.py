"""Derive and reconcile top-level project-state pointer fields.

The autonomous loop appends per-task entries under ``tasks`` and keeps the
active ledger front matter current, but the top-level ``current_task``,
``next_eligible_task``, and ``latest_verified_task_implementation_boundary``
pointers only move when something rewrites them explicitly. This module
derives those pointers mechanically from the ledger front matter and the
per-task entries so a verification boundary cannot leave them stale.
"""

from __future__ import annotations

import copy
import json
import re

from typing import Any

LEDGER_CURRENT_TASK_PATTERN = re.compile(r"^current_task:\s*(\S+)", re.MULTILINE)
LEDGER_NEXT_TASK_PATTERN = re.compile(r"^next_task:\s*(\S+)", re.MULTILINE)
TASK_ID_PATTERN = re.compile(
    r"^(?:T\d+(?:\.\d+)?[a-z]?(?:-[A-Z][A-Za-z0-9]*)?|[FK]\d+[a-z]?)$"
)
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SUMMARY_WORD_LIMIT = 8

POINTER_FIELDS = (
    "current_task",
    "next_eligible_task",
    "latest_verified_task_implementation_boundary",
)


def parse_ledger_current_task(ledger_text: str) -> str:
    """Extract the current task ID from the ledger front matter.

    The active ledger keeps exactly one machine-oriented ``current_task:``
    line whose first token is the task ID, for example
    ``current_task: T17.4 pending after verified T17.3; ...``.
    """
    matches = LEDGER_CURRENT_TASK_PATTERN.findall(ledger_text)
    if not matches:
        raise ValueError("Ledger has no 'current_task:' front-matter line")
    if len(matches) > 1:
        raise ValueError(
            f"Ledger has {len(matches)} 'current_task:' lines; expected exactly one"
        )
    token = matches[0].rstrip(";,.")
    if not TASK_ID_PATTERN.match(token):
        raise ValueError(
            f"Ledger current_task token {token!r} is not a recognizable task ID"
        )
    return token


def parse_ledger_next_task(ledger_text: str) -> str:
    """Extract an explicit next task, falling back to the current task.

    A closeout may truthfully keep the completed task as ``current_task`` while
    routing a distinct dependency-ready task through ``next_task``. Older
    ledgers without that line retain their historical current-equals-next
    behavior.
    """
    matches = LEDGER_NEXT_TASK_PATTERN.findall(ledger_text)
    if len(matches) > 1:
        raise ValueError(
            f"Ledger has {len(matches)} 'next_task:' lines; expected at most one"
        )
    if not matches:
        return parse_ledger_current_task(ledger_text)
    token = matches[0].rstrip(";,")
    if not TASK_ID_PATTERN.match(token):
        raise ValueError(
            f"Ledger next_task token {token!r} is not a recognizable task ID"
        )
    return token


def derive_latest_verified_boundary(tasks: dict[str, Any]) -> dict[str, Any]:
    """Select the verified task with the highest numeric verified brief ID."""
    best: dict[str, Any] | None = None
    best_brief = -1
    for task_id, entry in tasks.items():
        if not isinstance(entry, dict) or entry.get("state") != "verified":
            continue
        raw_brief = entry.get("latest_verified_brief_id")
        if raw_brief is None:
            continue
        try:
            brief_number = int(str(raw_brief))
        except ValueError as error:
            raise ValueError(
                f"Task {task_id} has non-numeric latest_verified_brief_id"
                f" {raw_brief!r}"
            ) from error
        if brief_number > best_brief:
            best_brief = brief_number
            artifact = entry.get("artifact")
            best = {
                "task_id": task_id,
                "brief_id": str(raw_brief),
                "reviewer_decision_id": entry.get("review_decision_id"),
                "result": entry.get("result", ""),
                "artifact_path": (
                    artifact.get("path") if isinstance(artifact, dict) else None
                ),
            }
    if best is None:
        raise ValueError("No verified task with a latest_verified_brief_id found")
    if not best["reviewer_decision_id"]:
        raise ValueError(
            f"Verified task {best['task_id']} (brief {best['brief_id']})"
            " has no review_decision_id"
        )
    return best


def _summary_slug(result: str) -> str:
    words = re.sub(r"[^0-9A-Za-z]+", " ", result.lower()).split()
    if not words:
        raise ValueError("Cannot derive a boundary summary from an empty result")
    return "_".join(words[:SUMMARY_WORD_LIMIT])


def derive_pointer_targets(
    project_state: dict[str, Any],
    ledger_text: str,
    boundary_commit: str,
) -> dict[str, Any]:
    """Compute the truthful values for the top-level pointer fields."""
    if not COMMIT_PATTERN.match(boundary_commit):
        raise ValueError(
            f"Boundary commit {boundary_commit!r} is not a full 40-hex SHA"
        )
    tasks = project_state.get("tasks")
    if not isinstance(tasks, dict):
        raise ValueError("project_state has no 'tasks' object")
    current_task = parse_ledger_current_task(ledger_text)
    next_task = parse_ledger_next_task(ledger_text)
    boundary = derive_latest_verified_boundary(tasks)
    return {
        "current_task": current_task,
        "next_eligible_task": next_task,
        "latest_verified_task_implementation_boundary": {
            "brief_id": boundary["brief_id"],
            "commit": boundary_commit,
            "reviewer_decision_id": boundary["reviewer_decision_id"],
            "summary": _summary_slug(boundary["result"]),
        },
    }


def find_pointer_drift(
    project_state: dict[str, Any], targets: dict[str, Any]
) -> list[str]:
    """Return one line per top-level pointer value that disagrees with targets."""
    drift: list[str] = []
    for field in ("current_task", "next_eligible_task"):
        recorded = project_state.get(field)
        expected = targets[field]
        if recorded != expected:
            drift.append(f"{field}: recorded {recorded!r} expected {expected!r}")
    recorded_boundary = project_state.get(
        "latest_verified_task_implementation_boundary"
    )
    expected_boundary = targets["latest_verified_task_implementation_boundary"]
    if not isinstance(recorded_boundary, dict):
        drift.append(
            "latest_verified_task_implementation_boundary: recorded value"
            " is not an object"
        )
        return drift
    for key in ("brief_id", "commit", "reviewer_decision_id"):
        recorded = recorded_boundary.get(key)
        expected = expected_boundary[key]
        if recorded != expected:
            drift.append(
                "latest_verified_task_implementation_boundary."
                f"{key}: recorded {recorded!r} expected {expected!r}"
            )
    return drift


def apply_pointer_targets(
    project_state: dict[str, Any],
    targets: dict[str, Any],
    updated: str | None = None,
) -> dict[str, Any]:
    """Write the derived pointer values onto the project state in place."""
    for field in POINTER_FIELDS:
        project_state[field] = targets[field]
    if updated is not None:
        project_state["updated"] = updated
    return project_state


def _replace_string_line(text: str, indent: str, key: str, value: str) -> str:
    if re.search(r'["\\]', value):
        raise ValueError(f"Refusing to write value with quote or backslash: {value!r}")
    pattern = re.compile(
        rf'^({indent}"{re.escape(key)}": )"[^"]*"(,?)$', re.MULTILINE
    )
    replaced, count = pattern.subn(rf'\g<1>"{value}"\g<2>', text)
    if count != 1:
        raise ValueError(
            f"Expected exactly one {key!r} line at indent {len(indent)};"
            f" found {count}"
        )
    return replaced


def rewrite_pointer_fields(
    text: str, targets: dict[str, Any], updated: str | None = None
) -> str:
    """Rewrite only the top-level pointer lines, preserving all other formatting.

    The project state is hand-formatted by the loop agents, so a full JSON
    dump would produce a large cosmetic diff. This edits the exact pointer
    lines instead and then proves the result parses to the same object that
    :func:`apply_pointer_targets` produces.
    """
    original = json.loads(text)
    result = text
    if updated is not None:
        result = _replace_string_line(result, "  ", "updated", updated)
    for field in ("current_task", "next_eligible_task"):
        result = _replace_string_line(result, "  ", field, targets[field])

    block_pattern = re.compile(
        r'^  "latest_verified_task_implementation_boundary": \{\n(.*?)^  \}',
        re.MULTILINE | re.DOTALL,
    )
    block_matches = block_pattern.findall(result)
    if len(block_matches) != 1:
        raise ValueError(
            "Expected exactly one latest_verified_task_implementation_boundary"
            f" block; found {len(block_matches)}"
        )
    block = block_matches[0]
    boundary = targets["latest_verified_task_implementation_boundary"]
    for key in ("brief_id", "commit", "reviewer_decision_id", "summary"):
        block = _replace_string_line(block, "    ", key, boundary[key])
    result = block_pattern.sub(
        lambda _match: (
            '  "latest_verified_task_implementation_boundary": {\n' + block + "  }"
        ),
        result,
        count=1,
    )

    expected = apply_pointer_targets(copy.deepcopy(original), targets, updated)
    if json.loads(result) != expected:
        raise ValueError(
            "Surgical pointer rewrite did not produce the expected project state"
        )
    return result
