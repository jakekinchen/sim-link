#!/usr/bin/env python3
"""Write or verify T20.36h's static runtime preflight and one-use permit."""

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
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (  # noqa: E402
    ATTEMPT_PATH,
    EXPECTED_DEPENDENCY_VERSIONS,
    FAILURE_PATH,
    RESULT_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    RUNTIME_PREFLIGHT_PATH,
    TRAINING_PERMIT_PATH,
    build_runtime_preflight,
    build_training_permit,
    load_verified_spec,
    verify_runtime_preflight,
    verify_training_permit,
)
from scenesmith.robot_lab.t20_36h_simulation_training_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
)
from scenesmith.robot_lab.t20_36h_smolvla_batch import (  # noqa: E402
    load_smolvla_batch,
)

SCOPED_PATHS = (
    "scenesmith/robot_lab/t20_36h_exact_smolvla_gate_b.py",
    "scenesmith/robot_lab/t20_36h_simulation_training_authority.py",
    "scenesmith/robot_lab/t20_36h_smolvla_batch.py",
    "scripts/robot_lab/compose_t20_36h_simulation_training_authority.py",
    "scripts/robot_lab/preflight_t20_36h_exact_smolvla_gate_b.py",
    "scripts/robot_lab/run_t20_36h_exact_smolvla_gate_b.py",
    "tests/unit/test_t20_36h_exact_smolvla_gate_b.py",
    "tests/unit/test_t20_36h_simulation_training_authority.py",
    "configurations/robot_lab/t20_36h_owner_training_authorization.json",
    "configurations/robot_lab/t20_36h_simulation_training_authority_request.json",
    "configurations/robot_lab/t20_36h_simulation_training_authority_decision.json",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    spec = load_verified_spec(repo_root=REPO_ROOT)
    authority = (
        verify_authority(repo_root=REPO_ROOT)
        if args.verify
        else require_active_authority(repo_root=REPO_ROOT)
    )
    authority_identity = authority["decision"]["identity_sha256"]
    runtime_path = REPO_ROOT / RUNTIME_PREFLIGHT_PATH
    permit_path = REPO_ROOT / TRAINING_PERMIT_PATH
    if args.verify:
        runtime = load_strict_json(runtime_path)
        verify_runtime_preflight(
            runtime, spec=spec, authority_identity=authority_identity
        )
        permit = load_strict_json(permit_path)
        verify_training_permit(
            permit,
            spec=spec,
            authority_identity=authority_identity,
            runtime_preflight=runtime,
        )
        print(runtime["identity_sha256"], permit["identity_sha256"])
        return 0
    if runtime_path.exists() or permit_path.exists():
        raise FileExistsError("T20.36h immutable preflight or permit already exists")
    if any(
        path.exists()
        for path in (
            REPO_ROOT / RUN_ROOT,
            REPO_ROOT / ATTEMPT_PATH,
            REPO_ROOT / RUN_SUMMARY_PATH,
            REPO_ROOT / FAILURE_PATH,
            REPO_ROOT / RESULT_PATH,
        )
    ):
        raise FileExistsError("T20.36h attempt or result exists before preflight")
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "0",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    import torch

    versions = {
        package: importlib.metadata.version(package)
        for package in EXPECTED_DEPENDENCY_VERSIONS
    }
    batch = load_smolvla_batch(repo_root=REPO_ROOT, spec=spec)
    source_commit = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    remote_source_commit = subprocess.run(
        [
            "git",
            "ls-remote",
            "--heads",
            "origin",
            "codex/pi05-autolearn-loop",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    runtime = build_runtime_preflight(
        spec=spec,
        authority_identity=authority_identity,
        python_major_minor=list(sys.version_info[:2]),
        dependency_versions=versions,
        mps_available=torch.backends.mps.is_available(),
        lerobot_stack_identity_sha256=stack["identity_sha256"],
        free_disk_bytes=shutil.disk_usage(REPO_ROOT).free,
        batch_evidence=batch["evidence"],
        checkpoint_tree=_checkpoint_tree(spec),
        source_commit=source_commit,
        remote_source_commit=remote_source_commit,
        branch=branch,
        scoped_dirty_paths=_scoped_dirty_paths(),
        attempt_exists=False,
        run_exists=False,
        result_exists=False,
    )
    permit = build_training_permit(
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime,
    )
    dump_canonical_json(runtime_path, runtime)
    dump_canonical_json(permit_path, permit)
    print(runtime["identity_sha256"], permit["identity_sha256"])
    return 0


def _checkpoint_tree(spec):
    rows = []
    for group in ("policy", "vlm"):
        root = Path(spec["local_cache"][f"{group}_snapshot"])
        for source in spec["local_cache"][f"{group}_files"]:
            if not source["is_weight_or_tensor_file"]:
                continue
            path = root / source["name"]
            if not path.is_file() or path.stat().st_size != source["size_bytes"]:
                raise ValueError(f"T20.36h checkpoint file drifted: {path}")
            rows.append(
                {
                    "path": f"{group}/{source['name']}",
                    "size_bytes": path.stat().st_size,
                    "sha256": _file_sha256(path),
                }
            )
    return rows


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _scoped_dirty_paths() -> list[str]:
    output = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", *SCOPED_PATHS],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line[3:] for line in output.splitlines() if line]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
