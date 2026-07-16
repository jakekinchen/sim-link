#!/usr/bin/env python3
"""Write or verify T20.36f's model-free inference preflight and permit."""

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
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (  # noqa: E402
    EXPECTED_DEPENDENCY_VERSIONS,
)
from scenesmith.robot_lab.t20_36f_act_decode_localization import (  # noqa: E402
    ATTEMPT_PATH,
    INFERENCE_PERMIT_PATH,
    RESULT_PATH,
    RUNTIME_PREFLIGHT_PATH,
    SOURCE_CHECKPOINT_ROOT,
    build_inference_permit,
    build_runtime_preflight,
    checkpoint_tree,
    load_verified_sources,
    verify_inference_permit,
    verify_runtime_preflight,
)
from scenesmith.robot_lab.t20_36f_simulation_inference_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_verified_sources(repo_root=REPO_ROOT)
    authority = (
        verify_authority(repo_root=REPO_ROOT)
        if args.verify
        else require_active_authority(repo_root=REPO_ROOT)
    )
    authority_identity = authority["decision"]["identity_sha256"]
    runtime_path = REPO_ROOT / RUNTIME_PREFLIGHT_PATH
    permit_path = REPO_ROOT / INFERENCE_PERMIT_PATH
    if args.verify:
        runtime = load_strict_json(runtime_path)
        verify_runtime_preflight(
            runtime,
            sources=sources,
            authority_identity=authority_identity,
        )
        permit = load_strict_json(permit_path)
        verify_inference_permit(
            permit,
            sources=sources,
            authority_identity=authority_identity,
            runtime_preflight=runtime,
        )
        print(runtime["identity_sha256"], permit["identity_sha256"])
        return 0
    if runtime_path.exists() or permit_path.exists():
        raise FileExistsError("T20.36f immutable preflight or permit exists")
    if (REPO_ROOT / ATTEMPT_PATH).exists() or (REPO_ROOT / RESULT_PATH).exists():
        raise FileExistsError("T20.36f attempt or result exists before preflight")
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
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
    source_commit = _git("rev-parse", "HEAD")
    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36f preflight is on the wrong branch")
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
        sources=sources,
        authority_identity=authority_identity,
        python_major_minor=list(sys.version_info[:2]),
        dependency_versions=versions,
        mps_available=torch.backends.mps.is_available(),
        lerobot_stack_identity_sha256=stack["identity_sha256"],
        checkpoint_tree=checkpoint_tree(REPO_ROOT / SOURCE_CHECKPOINT_ROOT),
        free_disk_bytes=shutil.disk_usage(REPO_ROOT).free,
        source_commit=source_commit,
        remote_source_commit=remote_source_commit,
        attempt_exists=False,
        result_exists=False,
    )
    permit = build_inference_permit(
        sources=sources,
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
