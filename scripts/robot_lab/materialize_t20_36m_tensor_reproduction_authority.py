#!/usr/bin/env python3
"""Materialize or verify T20.36m central authority, preflight, and permit."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_36h_smolvla_batch import load_smolvla_batch  # noqa: E402
from scenesmith.robot_lab.t20_36j_exact_smolvla_gate_b import (  # noqa: E402
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
    collect_installed_closure,
)
from scenesmith.robot_lab.t20_36m_tensor_reproduction import (  # noqa: E402
    ATTEMPT_PATH,
    FAILURE_RESULT_PATH,
    INFERENCE_PERMIT_PATH,
    RESULT_PATH,
    RUN_ROOT,
    RUNTIME_PREFLIGHT_PATH,
    build_inference_permit,
    build_runtime_preflight,
    load_verified_sources,
    verify_inference_permit,
    verify_runtime_preflight,
)
from scenesmith.robot_lab.t20_36m_tensor_reproduction_authority import (  # noqa: E402
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
        raise ValueError("T20.36m authority materialization is on the wrong branch")
    authority = write_authority(repo_root=REPO_ROOT)
    authority_identity = authority["decision"]["identity_sha256"]
    sources = load_verified_sources(repo_root=REPO_ROOT)

    live_closure = collect_installed_closure()
    if live_closure != sources["installed_closure"]:
        raise ValueError("T20.36m installed dependency closure drifted")
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    if stack["identity_sha256"] != sources["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36m LeRobot stack identity drifted")
    batch = load_smolvla_batch(repo_root=REPO_ROOT, spec=sources["smolvla_spec"])
    batch_identity = hashlib.sha256(canonical_json_bytes(batch["evidence"])).hexdigest()
    if batch_identity != sources["batch_evidence_identity_sha256"]:
        raise ValueError("T20.36m canonical batch identity drifted")

    import torch

    source_commit = _git("rev-parse", "HEAD")
    remote_commit = _remote_head()
    attempt_exists = (REPO_ROOT / RUN_ROOT).exists() or (REPO_ROOT / ATTEMPT_PATH).exists()
    result_exists = any(
        (REPO_ROOT / path).exists()
        for path in (RESULT_PATH, FAILURE_RESULT_PATH)
    )
    preflight = build_runtime_preflight(
        sources=sources,
        authority_identity=authority_identity,
        python_major_minor=[sys.version_info.major, sys.version_info.minor],
        mps_available=torch.backends.mps.is_available(),
        checkpoint_tree=_file_tree(REPO_ROOT / SOURCE_CHECKPOINT_ROOT),
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
        raise ValueError("T20.36m remote branch is missing")
    return output[0]


if __name__ == "__main__":
    raise SystemExit(main())
