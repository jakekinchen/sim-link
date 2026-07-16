#!/usr/bin/env python3
"""Materialize or verify T20.36n central authority, preflight, and permit."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import os
import shutil
import subprocess
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json  # noqa: E402
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_36n_tensor_reproduction import (  # noqa: E402
    ATTEMPT_PATH,
    FAILURE_RESULT_PATH,
    INFERENCE_PERMIT_PATH,
    RESULT_PATH,
    RUN_ROOT,
    RUNTIME_PREFLIGHT_PATH,
    SOURCE_CHECKPOINT_ROOT,
    TENSOR_PATH,
    build_inference_permit,
    build_runtime_preflight,
    load_verified_sources,
    verify_inference_permit,
    verify_runtime_preflight,
)
from scenesmith.robot_lab.t20_36n_tensor_reproduction_authority import (  # noqa: E402
    verify_authority,
    write_authority,
)
from scripts.robot_lab.run_t20_36n_tensor_reproduction import (  # noqa: E402
    load_t20_35x_batch,
    snapshot_file_tree,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        authority = verify_authority(repo_root=REPO_ROOT)
        sources = load_verified_sources(repo_root=REPO_ROOT)
        from scenesmith.robot_lab.artifact_contract import load_strict_json

        preflight = load_strict_json(REPO_ROOT / RUNTIME_PREFLIGHT_PATH)
        permit = load_strict_json(REPO_ROOT / INFERENCE_PERMIT_PATH)
        authority_identity = authority["decision"]["identity_sha256"]
        verify_runtime_preflight(
            preflight, sources=sources, authority_identity=authority_identity
        )
        verify_inference_permit(
            permit,
            sources=sources,
            authority_identity=authority_identity,
            runtime_preflight=preflight,
        )
        print(permit["identity_sha256"])
        return 0

    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36n authority materialization is on the wrong branch")
    authority = write_authority(repo_root=REPO_ROOT)
    authority_identity = authority["decision"]["identity_sha256"]
    sources = load_verified_sources(repo_root=REPO_ROOT)

    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    if stack["identity_sha256"] != sources["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36n LeRobot stack identity drifted")
    dependencies = _ensure_exact_dependency_versions(
        sources["required_dependency_versions"]
    )
    batch = load_t20_35x_batch(sources=sources)
    snapshot_tree = snapshot_file_tree(batch["snapshot"])

    import torch

    source_commit = _git("rev-parse", "HEAD")
    remote_commit = _remote_head()
    attempt_exists = (REPO_ROOT / RUN_ROOT).exists() or (REPO_ROOT / ATTEMPT_PATH).exists()
    result_exists = any(
        (REPO_ROOT / path).exists()
        for path in (RESULT_PATH, FAILURE_RESULT_PATH, TENSOR_PATH)
    )
    preflight = build_runtime_preflight(
        sources=sources,
        authority_identity=authority_identity,
        python_major_minor=[sys.version_info.major, sys.version_info.minor],
        mps_available=torch.backends.mps.is_available(),
        checkpoint_tree=_file_tree(Path(SOURCE_CHECKPOINT_ROOT)),
        dependency_versions=dependencies,
        snapshot_revision=batch["snapshot"].name,
        snapshot_tree=snapshot_tree,
        free_disk_bytes=shutil.disk_usage(REPO_ROOT).free,
        source_commit=source_commit,
        remote_source_commit=remote_commit,
        attempt_exists=attempt_exists,
        result_exists=result_exists,
    )
    permit = build_inference_permit(
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=preflight,
    )
    dump_canonical_json(REPO_ROOT / RUNTIME_PREFLIGHT_PATH, preflight)
    dump_canonical_json(REPO_ROOT / INFERENCE_PERMIT_PATH, permit)
    print(permit["identity_sha256"])
    return 0


def _file_tree(root: Path) -> list[dict[str, object]]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": digest.hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def _ensure_exact_dependency_versions(expected: dict[str, str]) -> dict[str, str]:
    actual = {package: importlib.metadata.version(package) for package in expected}
    if actual == expected:
        return actual
    differences = {
        package: (actual.get(package), expected[package])
        for package in expected
        if actual.get(package) != expected[package]
    }
    if differences != {"pyarrow": ("24.0.0", "25.0.0")}:
        raise ValueError("T20.36n installed dependency versions drifted")
    uv = shutil.which("uv")
    if uv is None:
        raise ValueError("T20.36n offline uv executable is unavailable")
    environment = os.environ.copy()
    environment.update(
        {
            "UV_OFFLINE": "1",
            "UV_PYTHON_DOWNLOADS": "never",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        }
    )
    subprocess.run(
        [
            uv,
            "pip",
            "install",
            "--offline",
            "--python",
            str(REPO_ROOT / "external/lerobot/.venv/bin/python"),
            "pyarrow==25.0.0",
        ],
        cwd=REPO_ROOT,
        env=environment,
        check=True,
    )
    restored = {
        package: importlib.metadata.version(package) for package in expected
    }
    if restored != expected:
        raise ValueError("T20.36n offline dependency restore failed closed")
    return restored


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
        raise ValueError("T20.36n remote branch is missing")
    return output[0]


if __name__ == "__main__":
    raise SystemExit(main())
