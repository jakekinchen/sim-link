#!/usr/bin/env python3
"""Write or verify T20.36e's model-free runtime preflight and permit."""

from __future__ import annotations

import argparse
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
from scenesmith.robot_lab.t20_36e_act_batch import load_exact_batch  # noqa: E402
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (  # noqa: E402
    ATTEMPT_PATH,
    EXPECTED_DEPENDENCY_VERSIONS,
    RESULT_PATH,
    RUN_ROOT,
    RUNTIME_PREFLIGHT_PATH,
    TRAINING_PERMIT_PATH,
    build_runtime_preflight,
    build_training_permit,
    load_verified_spec,
    verify_runtime_preflight,
    verify_training_permit,
)
from scenesmith.robot_lab.t20_36e_simulation_training_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
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
        raise FileExistsError("T20.36e immutable preflight or permit already exists")
    if (
        (REPO_ROOT / RUN_ROOT).exists()
        or (REPO_ROOT / ATTEMPT_PATH).exists()
        or (REPO_ROOT / RESULT_PATH).exists()
    ):
        raise FileExistsError("T20.36e attempt or result exists before preflight")
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    import datasets  # noqa: F401
    import lerobot  # noqa: F401
    import numpy  # noqa: F401
    import pyarrow  # noqa: F401
    import torch
    import torchvision  # noqa: F401

    versions = {
        package: importlib.metadata.version(package)
        for package in EXPECTED_DEPENDENCY_VERSIONS
    }
    batch = load_exact_batch(repo_root=REPO_ROOT, spec=spec)
    source_commit = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    if branch != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36e preflight is on the wrong branch")
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
        source_commit=source_commit,
        remote_source_commit=remote_source_commit,
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
