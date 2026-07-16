#!/usr/bin/env python3
"""Materialize or verify T20.36o baseline authority, preflight, and permit."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import shutil
import subprocess
import sys

from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_36n_tensor_reproduction import (  # noqa: E402
    SOURCE_CHECKPOINT_ROOT,
)
from scenesmith.robot_lab.t20_36o_baseline_capture import (  # noqa: E402
    ATTEMPT_PATH,
    BASELINE_PERMIT_PATH,
    FAILURE_RESULT_PATH,
    RESULT_PATH,
    RUN_ROOT,
    RUNTIME_PREFLIGHT_PATH,
    TENSOR_PATH,
    TRACKED_ATTEMPT_PATH,
    TRAJECTORY_PATH,
    build_baseline_permit,
    build_runtime_preflight,
    load_verified_sources,
    verify_baseline_permit,
    verify_runtime_preflight,
)
from scenesmith.robot_lab.t20_36o_baseline_inference_authority import (  # noqa: E402
    verify_authority,
    write_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        authority = verify_authority(repo_root=REPO_ROOT)
        sources = load_verified_sources(repo_root=REPO_ROOT)
        preflight = load_strict_json(REPO_ROOT / RUNTIME_PREFLIGHT_PATH)
        permit = load_strict_json(REPO_ROOT / BASELINE_PERMIT_PATH)
        authority_identity = authority["decision"]["identity_sha256"]
        verify_runtime_preflight(
            preflight,
            sources=sources,
            authority_identity=authority_identity,
        )
        verify_baseline_permit(
            permit,
            sources=sources,
            authority_identity=authority_identity,
            runtime_preflight=preflight,
        )
        print(permit["identity_sha256"])
        return 0

    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36o baseline authority is on the wrong branch")
    source_commit = _git("rev-parse", "HEAD")
    remote_commit = _remote_head()
    if source_commit != remote_commit:
        raise ValueError("T20.36o baseline implementation is not on origin")
    authority = write_authority(repo_root=REPO_ROOT)
    authority_identity = authority["decision"]["identity_sha256"]
    sources = load_verified_sources(repo_root=REPO_ROOT)
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    if stack["identity_sha256"] != sources["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36o baseline LeRobot stack identity drifted")
    dependencies = {
        package: importlib.metadata.version(package)
        for package in sources["required_dependency_versions"]
    }
    if dependencies != sources["required_dependency_versions"]:
        raise ValueError("T20.36o baseline dependency versions drifted")
    import torch

    snapshot = (
        Path.home()
        / ".cache/huggingface/hub/models--lerobot--pi05_base/snapshots"
        / sources["snapshot_revision"]
    ).resolve()
    checkpoint_tree = _file_tree(Path(SOURCE_CHECKPOINT_ROOT))
    snapshot_tree = _file_tree(snapshot, chunk_size=64 * 1024 * 1024)
    attempt_exists = (
        (REPO_ROOT / RUN_ROOT).exists()
        or (REPO_ROOT / ATTEMPT_PATH).exists()
        or (REPO_ROOT / TRACKED_ATTEMPT_PATH).exists()
    )
    result_exists = any(
        (REPO_ROOT / path).exists()
        for path in (
            RESULT_PATH,
            FAILURE_RESULT_PATH,
            TENSOR_PATH,
            TRAJECTORY_PATH,
        )
    )
    preflight = build_runtime_preflight(
        sources=sources,
        authority_identity=authority_identity,
        python_major_minor=[sys.version_info.major, sys.version_info.minor],
        mps_available=torch.backends.mps.is_available(),
        checkpoint_tree=checkpoint_tree,
        dependency_versions=dependencies,
        snapshot_revision=snapshot.name,
        snapshot_tree=snapshot_tree,
        free_disk_bytes=shutil.disk_usage(REPO_ROOT).free,
        source_commit=source_commit,
        remote_source_commit=remote_commit,
        attempt_exists=attempt_exists,
        result_exists=result_exists,
    )
    permit = build_baseline_permit(
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=preflight,
    )
    dump_canonical_json(REPO_ROOT / RUNTIME_PREFLIGHT_PATH, preflight)
    dump_canonical_json(REPO_ROOT / BASELINE_PERMIT_PATH, permit)
    print(permit["identity_sha256"])
    return 0


def _file_tree(root: Path, *, chunk_size: int = 8 * 1024 * 1024) -> list[dict[str, Any]]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": digest.hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _remote_head() -> str:
    output = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "codex/pi05-autolearn-loop"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    if not output:
        raise ValueError("T20.36o remote branch is missing")
    return output[0]


if __name__ == "__main__":
    raise SystemExit(main())
