"""Live collection and exclusive materialization for T20.42/R0 authority.

The functions here create no simulation output and execute no candidate. They
only collect local runtime facts, build the already-reviewed T20.42a payloads,
and exclusively persist the five compact authority artifacts.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import load_strict_json
from scenesmith.robot_lab.t20_42a_r0_generation_authority import (
    BRANCH,
    DECISION_PATH,
    OUTPUT_PATHS,
    OWNER_GRANT_PATH,
    PERMIT_PATH,
    REQUEST_PATH,
    REQUIRED_DEPENDENCIES,
    RUNTIME_PREFLIGHT_PATH,
    build_central_authority,
    build_owner_grant,
    build_permit,
    build_runtime_preflight,
    load_verified_sources,
    verify_owner_grant,
    verify_permit,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_PATHS = (
    OWNER_GRANT_PATH,
    REQUEST_PATH,
    DECISION_PATH,
    RUNTIME_PREFLIGHT_PATH,
    PERMIT_PATH,
)
IMPLEMENTATION_SCOPED_PATHS = (
    Path("scenesmith/robot_lab/scripted_grasp_episode_generation.py"),
    Path("scenesmith/robot_lab/t20_42a_r0_generation_authority.py"),
    Path("scenesmith/robot_lab/t20_42b_r0_materialization.py"),
    Path("scenesmith/robot_lab/t20_42b_r0_runner.py"),
    Path("scripts/robot_lab/materialize_t20_42b_r0_authority.py"),
    Path("scripts/robot_lab/run_t20_42_r0_generation.py"),
    Path("scripts/robot_lab/write_t20_42b_r0_pre_run_acceptance.py"),
    Path("tests/unit/test_t20_42a_r0_generation_authority.py"),
    Path("tests/unit/test_t20_42b_r0_materialization.py"),
    Path("tests/unit/test_t20_42b_r0_runner.py"),
)


def build_materialization_bundle(
    *,
    sources: dict[str, Any],
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    runtime_snapshot: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    owner = build_owner_grant(
        sources=sources,
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    request, decision = build_central_authority(
        sources=sources,
        owner_grant=owner,
    )
    preflight = build_runtime_preflight(
        sources=sources,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_snapshot=runtime_snapshot,
    )
    permit = build_permit(
        sources=sources,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_preflight=preflight,
    )
    bundle = {
        OWNER_GRANT_PATH.as_posix(): owner,
        REQUEST_PATH.as_posix(): request,
        DECISION_PATH.as_posix(): decision,
        RUNTIME_PREFLIGHT_PATH.as_posix(): preflight,
        PERMIT_PATH.as_posix(): permit,
    }
    verify_materialization_bundle(bundle, sources=sources)
    return bundle


def verify_materialization_bundle(
    bundle: dict[str, dict[str, Any]], *, sources: dict[str, Any]
) -> None:
    if not isinstance(bundle, dict) or list(bundle) != [
        path.as_posix() for path in AUTHORITY_PATHS
    ]:
        raise ValueError("T20.42b authority bundle path/order drifted")
    owner = bundle[OWNER_GRANT_PATH.as_posix()]
    request = bundle[REQUEST_PATH.as_posix()]
    decision = bundle[DECISION_PATH.as_posix()]
    preflight = bundle[RUNTIME_PREFLIGHT_PATH.as_posix()]
    permit = bundle[PERMIT_PATH.as_posix()]
    verify_owner_grant(owner, sources=sources)
    expected_request, expected_decision = build_central_authority(
        sources=sources,
        owner_grant=owner,
    )
    if request != expected_request or decision != expected_decision:
        raise ValueError("T20.42b central authority bundle drifted")
    verify_permit(
        permit,
        sources=sources,
        owner_grant=owner,
        request=request,
        decision=decision,
        runtime_preflight=preflight,
    )


def write_authority_bundle(
    bundle: dict[str, dict[str, Any]],
    *,
    sources: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> dict[str, dict[str, Any]]:
    """Write all authority files exclusively; partial writes never authorize."""

    verify_materialization_bundle(bundle, sources=sources)
    root = Path(repo_root)
    resolved_root = root.resolve()
    targets = []
    for path in AUTHORITY_PATHS:
        _safe_relative(path)
        target = root / path
        _reject_aliases(root, path.parent)
        if os.path.lexists(target):
            raise FileExistsError(f"T20.42b authority target already exists: {path}")
        if not target.parent.resolve().is_relative_to(resolved_root):
            raise ValueError(f"T20.42b authority target escapes checkout: {path}")
        targets.append((path, target))
    for _path, target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
    written: dict[str, dict[str, Any]] = {}
    for path, target in targets:
        _reject_aliases(root, path.parent)
        _exclusive_json_write(target, bundle[path.as_posix()])
        persisted = load_strict_json(target)
        if persisted != bundle[path.as_posix()]:
            raise ValueError(f"T20.42b persisted authority bytes drifted: {path}")
        written[path.as_posix()] = persisted
    verify_materialization_bundle(written, sources=sources)
    return written


def verify_materialized_authority(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    sources = load_verified_sources(repo_root=root)
    bundle = {
        path.as_posix(): load_strict_json(root / path) for path in AUTHORITY_PATHS
    }
    verify_materialization_bundle(bundle, sources=sources)
    return bundle


def collect_live_runtime_snapshot(
    *,
    required_source_commit: str,
    repo_root: Path = REPO_ROOT,
    scoped_paths: tuple[Path, ...] = IMPLEMENTATION_SCOPED_PATHS,
) -> dict[str, Any]:
    """Collect no-write local facts for the reviewed T20.42a preflight."""

    root = Path(repo_root).resolve()
    head = _git(root, "rev-parse", "HEAD")
    if head != required_source_commit:
        raise ValueError("T20.42b HEAD drifted from required source commit")
    branch = _git(root, "branch", "--show-current")
    if branch != BRANCH:
        raise ValueError("T20.42b branch drifted")
    ancestor = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "merge-base",
            "--is-ancestor",
            required_source_commit,
            f"refs/remotes/origin/{BRANCH}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError("T20.42b source commit is absent from origin tracking ref")
    for path in scoped_paths:
        _safe_relative(path)
    dirty_output = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *[path.as_posix() for path in scoped_paths],
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    scoped_dirty = sorted(
        line[3:] for line in dirty_output.splitlines() if len(line) >= 4
    )
    dependencies = _dependency_versions()
    free_disk = shutil.disk_usage(root).free
    output_state = {
        path.as_posix(): {
            "exists": os.path.lexists(root / path),
            "is_symlink": _path_or_parent_is_symlink(root, path),
        }
        for path in OUTPUT_PATHS
    }
    if any(os.path.lexists(root / path) for path in AUTHORITY_PATHS):
        raise FileExistsError("T20.42b authority artifact already exists")
    return {
        "source_commit": head,
        "branch": branch,
        "origin_contains_source_commit": True,
        "scoped_dirty_paths": scoped_dirty,
        "dependencies": dependencies,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
        },
        "minimum_free_disk_bytes": 10 * 1024**3,
        "free_disk_bytes": free_disk,
        "network_enabled": False,
        "dependency_fallback_enabled": False,
        "authority_artifacts_materialized": False,
        "attempt_marker_exists": False,
        "r0_episode_generation_executed": False,
        "output_path_state": output_state,
    }


def materialize_live_authority(
    *,
    required_source_commit: str,
    valid_from: str,
    valid_until: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root).resolve()
    sources = load_verified_sources(repo_root=root)
    runtime = collect_live_runtime_snapshot(
        required_source_commit=required_source_commit,
        repo_root=root,
    )
    bundle = build_materialization_bundle(
        sources=sources,
        required_source_commit=required_source_commit,
        valid_from=valid_from,
        valid_until=valid_until,
        runtime_snapshot=runtime,
    )
    return write_authority_bundle(bundle, sources=sources, repo_root=root)


def _dependency_versions() -> dict[str, str]:
    import mujoco
    import numpy
    import pyarrow

    from PIL import __version__ as pillow_version

    import lerobot

    versions = {
        "python": platform.python_version(),
        "mujoco": str(mujoco.__version__),
        "numpy": str(numpy.__version__),
        "pillow": str(pillow_version),
        "pyarrow": str(pyarrow.__version__),
        "lerobot": str(lerobot.__version__),
    }
    if set(versions) != set(REQUIRED_DEPENDENCIES) or any(
        not value for value in versions.values()
    ):
        raise ValueError("T20.42b dependency versions are incomplete")
    return versions


def _exclusive_json_write(path: Path, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _safe_relative(path: Path) -> None:
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"T20.42b unsafe path: {path}")


def _reject_aliases(root: Path, relative: Path) -> None:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"T20.42b path is aliased: {relative}")


def _path_or_parent_is_symlink(root: Path, relative: Path) -> bool:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False
