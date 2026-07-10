#!/usr/bin/env python3
"""Protect pre-existing out-of-scope work during a bounded goal loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys

from pathlib import Path
from typing import Any


SCHEMA_VERSION = "scenesmith.scoped_worktree_baseline.v1"
DEFAULT_SCOPE = Path("configurations/robot_lab/pi05_goal_loop_scope.json")


class GuardError(RuntimeError):
    """Raised when the protected worktree contract is violated."""


def load_scope(repo_root: Path, scope_path: Path) -> dict[str, Any]:
    path = _resolve(repo_root, scope_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "scenesmith.scoped_worktree.v1":
        raise GuardError(f"Unsupported scoped-worktree config: {path}")
    prefixes = payload.get("governed_path_prefixes")
    if not isinstance(prefixes, list) or not prefixes:
        raise GuardError("governed_path_prefixes must be a non-empty list")
    payload["governed_path_prefixes"] = [_normal_path(value) for value in prefixes]
    payload["explicitly_protected_paths"] = [
        _normal_path(value) for value in payload.get("explicitly_protected_paths", [])
    ]
    payload["path"] = str(path.relative_to(repo_root))
    payload["sha256"] = _sha256(path)
    return payload


def snapshot_baseline(
    repo_root: Path,
    scope_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    scope = load_scope(repo_root, scope_path)
    branch = _git(repo_root, "branch", "--show-current").strip()
    expected = scope.get("expected_branch")
    if expected and branch != expected:
        raise GuardError(f"Expected branch {expected!r}, found {branch!r}")
    status = worktree_status(repo_root)
    governed = sorted(path for path in status if is_governed(path, scope))
    if governed:
        raise GuardError(
            "Governed paths must be clean before recording a baseline: "
            + ", ".join(governed)
        )
    protected = {
        path: {
            "status": status[path],
            "fingerprint": fingerprint_path(repo_root, path, status[path]),
        }
        for path in sorted(status)
    }
    explicit_missing = [
        path for path in scope["explicitly_protected_paths"] if path not in protected
    ]
    if explicit_missing:
        raise GuardError(
            "Explicitly protected paths are not currently dirty: "
            + ", ".join(explicit_missing)
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "repo_root": str(repo_root),
        "branch": branch,
        "scope_config": scope["path"],
        "scope_config_sha256": scope["sha256"],
        "protected_entries": protected,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(output_path)
    return payload


def verify_baseline(
    repo_root: Path,
    scope_path: Path,
    baseline_path: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    scope = load_scope(repo_root, scope_path)
    if not baseline_path.is_file():
        raise GuardError(f"Missing protected-worktree baseline: {baseline_path}")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if baseline.get("schema_version") != SCHEMA_VERSION:
        raise GuardError(f"Unsupported protected-worktree baseline: {baseline_path}")
    if baseline.get("repo_root") != str(repo_root):
        raise GuardError("Protected-worktree baseline belongs to a different repository")
    if baseline.get("scope_config_sha256") != scope["sha256"]:
        raise GuardError("Scoped-worktree configuration changed after baseline creation")
    branch = _git(repo_root, "branch", "--show-current").strip()
    if branch != baseline.get("branch"):
        raise GuardError(
            f"Worktree branch changed from {baseline.get('branch')!r} to {branch!r}"
        )

    current_status = worktree_status(repo_root)
    governed = sorted(path for path in current_status if is_governed(path, scope))
    if governed:
        raise GuardError(
            "Goal-loop governed paths are dirty at the verification boundary: "
            + ", ".join(governed)
        )
    current_protected = {path: value for path, value in current_status.items()}
    expected = baseline.get("protected_entries", {})
    if set(current_protected) != set(expected):
        added = sorted(set(current_protected) - set(expected))
        removed = sorted(set(expected) - set(current_protected))
        raise GuardError(
            f"Protected dirty-path set changed; added={added}, removed={removed}"
        )

    drift: list[str] = []
    for path in sorted(expected):
        current_entry = {
            "status": current_protected[path],
            "fingerprint": fingerprint_path(repo_root, path, current_protected[path]),
        }
        if current_entry != expected[path]:
            drift.append(path)
    if drift:
        raise GuardError("Protected path content/status drifted: " + ", ".join(drift))
    return {
        "status": "pass",
        "branch": branch,
        "protected_paths": len(expected),
        "governed_dirty_paths": 0,
        "baseline": str(baseline_path),
    }


def worktree_status(repo_root: Path) -> dict[str, str]:
    raw = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=normal",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout
    items = raw.split(b"\0")
    result: dict[str, str] = {}
    index = 0
    while index < len(items):
        item = items[index]
        index += 1
        if not item:
            continue
        text = os.fsdecode(item)
        if len(text) < 4 or text[2] != " ":
            raise GuardError(f"Unrecognized git status record: {text!r}")
        code = text[:2]
        path = _normal_path(text[3:])
        if "R" in code or "C" in code:
            if index >= len(items) or not items[index]:
                raise GuardError(f"Rename/copy status lacks source path: {text!r}")
            source_path = _normal_path(os.fsdecode(items[index]))
            index += 1
            result[source_path] = code + ":source"
        result[path] = code
    return result


def is_governed(path: str, scope: dict[str, Any]) -> bool:
    if path in scope["explicitly_protected_paths"]:
        return False
    return any(
        path == prefix.rstrip("/") or path.startswith(prefix)
        for prefix in scope["governed_path_prefixes"]
    )


def fingerprint_path(repo_root: Path, relative: str, status_code: str) -> dict[str, Any]:
    path = _resolve(repo_root, Path(relative))
    if not path.exists() and not path.is_symlink():
        return {"kind": "missing"}
    if path.is_symlink():
        metadata = path.lstat()
        return {
            "kind": "symlink",
            "target": os.readlink(path),
            "mtime_ns": metadata.st_mtime_ns,
        }
    if path.is_file():
        metadata = path.stat()
        payload: dict[str, Any] = {
            "kind": "file",
            "size": metadata.st_size,
            "mtime_ns": metadata.st_mtime_ns,
        }
        if status_code != "??" or metadata.st_size <= 1_048_576:
            payload["sha256"] = _sha256(path)
        return payload
    if path.is_dir():
        digest = hashlib.sha256()
        count = 0
        for child in sorted(path.rglob("*")):
            if ".git" in child.relative_to(path).parts:
                continue
            metadata = child.lstat()
            relative_child = child.relative_to(path).as_posix()
            kind = (
                "symlink"
                if stat.S_ISLNK(metadata.st_mode)
                else "dir"
                if stat.S_ISDIR(metadata.st_mode)
                else "file"
            )
            record = (
                relative_child,
                kind,
                metadata.st_size,
                metadata.st_mtime_ns,
                os.readlink(child) if child.is_symlink() else None,
            )
            digest.update(json.dumps(record, separators=(",", ":")).encode())
            digest.update(b"\n")
            count += 1
        return {"kind": "directory", "entries": count, "metadata_sha256": digest.hexdigest()}
    metadata = path.lstat()
    return {"kind": "other", "mode": metadata.st_mode, "mtime_ns": metadata.st_mtime_ns}


def _normal_path(value: Any) -> str:
    path = Path(str(value)).as_posix()
    if path.startswith("/") or path == ".." or path.startswith("../"):
        raise GuardError(f"Worktree paths must be relative: {value!r}")
    return path


def _resolve(repo_root: Path, path: Path) -> Path:
    candidate = path if path.is_absolute() else repo_root / path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as error:
        raise GuardError(f"Path escapes repository: {path}") from error
    return resolved


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("snapshot", "verify"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            result = snapshot_baseline(args.repo_root, args.scope, args.baseline)
            printable = {
                "status": "recorded",
                "branch": result["branch"],
                "protected_paths": len(result["protected_entries"]),
                "baseline": str(args.baseline),
            }
        else:
            result = verify_baseline(args.repo_root, args.scope, args.baseline)
            printable = result
    except (GuardError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
