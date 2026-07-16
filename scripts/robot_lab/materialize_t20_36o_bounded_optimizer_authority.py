#!/usr/bin/env python3
"""Materialize or verify the T20.36o bounded optimizer authority boundary."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys

from importlib.metadata import version
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_17_clean_base_preflight import (  # noqa: E402
    EXPECTED_MODEL_REVISION,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_authority import (  # noqa: E402
    ATTEMPT_PATH,
    CHECKPOINT_ROOT,
    DECISION_PATH,
    FAILURE_RESULT_PATH,
    OWNER_GRANT_PATH,
    REQUEST_PATH,
    RESULT_PATH,
    RUN_ROOT,
    RUNTIME_PREFLIGHT_PATH,
    TRACKED_ATTEMPT_PATH,
    TRAINING_PERMIT_PATH,
    build_owner_grant,
    build_production_authority,
    build_runtime_preflight,
    build_training_permit,
    load_verified_sources,
    verify_owner_grant,
    verify_runtime_preflight,
    verify_training_permit,
)
from scripts.robot_lab.run_t20_35d_residual_localization import (  # noqa: E402
    _file_tree,
)
from scripts.robot_lab.run_t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
)
from scripts.robot_lab.run_t20_36o_baseline_capture import (  # noqa: E402
    snapshot_file_tree,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_verified_sources(repo_root=REPO_ROOT)
    if args.verify:
        artifacts = _load_and_verify(sources)
        print(artifacts["permit"]["identity_sha256"])
        return 0
    paths = (
        OWNER_GRANT_PATH,
        REQUEST_PATH,
        DECISION_PATH,
        RUNTIME_PREFLIGHT_PATH,
        TRAINING_PERMIT_PATH,
    )
    if any((REPO_ROOT / path).exists() for path in paths):
        raise FileExistsError("T20.36o optimizer authority already exists")
    owner = build_owner_grant(sources=sources, repo_root=REPO_ROOT)
    request, decision = build_production_authority(
        sources=sources,
        owner=owner,
        repo_root=REPO_ROOT,
    )
    runtime = _runtime_surface(sources)
    preflight = build_runtime_preflight(
        sources=sources,
        authority_identity=decision["identity_sha256"],
        **runtime,
    )
    permit = build_training_permit(
        sources=sources,
        authority_identity=decision["identity_sha256"],
        runtime_preflight=preflight,
    )
    for path, payload in (
        (OWNER_GRANT_PATH, owner),
        (REQUEST_PATH, request),
        (DECISION_PATH, decision),
        (RUNTIME_PREFLIGHT_PATH, preflight),
        (TRAINING_PERMIT_PATH, permit),
    ):
        dump_canonical_json(REPO_ROOT / path, payload)
    _load_and_verify(sources)
    print(permit["identity_sha256"])
    return 0


def _load_and_verify(sources):
    owner = load_strict_json(REPO_ROOT / OWNER_GRANT_PATH)
    verify_owner_grant(owner, sources=sources, repo_root=REPO_ROOT)
    expected_request, expected_decision = build_production_authority(
        sources=sources,
        owner=owner,
        repo_root=REPO_ROOT,
    )
    request = load_strict_json(REPO_ROOT / REQUEST_PATH)
    decision = load_strict_json(REPO_ROOT / DECISION_PATH)
    if request != expected_request or decision != expected_decision:
        raise ValueError("T20.36o optimizer central authority drifted")
    preflight = load_strict_json(REPO_ROOT / RUNTIME_PREFLIGHT_PATH)
    verify_runtime_preflight(
        preflight,
        sources=sources,
        authority_identity=decision["identity_sha256"],
    )
    permit = load_strict_json(REPO_ROOT / TRAINING_PERMIT_PATH)
    verify_training_permit(
        permit,
        sources=sources,
        authority_identity=decision["identity_sha256"],
        runtime_preflight=preflight,
    )
    return {
        "owner": owner,
        "request": request,
        "decision": decision,
        "preflight": preflight,
        "permit": permit,
    }


def _runtime_surface(sources):
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    if stack["identity_sha256"] != sources["x_runtime"][
        "lerobot_stack_identity_sha256"
    ]:
        raise ValueError("T20.36o optimizer live stack drifted")
    import torch

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36o optimizer preflight requires local MPS")
    checkpoint_tree = _file_tree(SOURCE_CHECKPOINT_ROOT)
    if checkpoint_tree != sources["x_runtime"]["checkpoint_tree"]:
        raise ValueError("T20.36o optimizer source checkpoint drifted")
    snapshot = (
        Path.home()
        / ".cache/huggingface/hub/models--lerobot--pi05_base/snapshots"
        / EXPECTED_MODEL_REVISION
    ).resolve()
    snapshot_tree = snapshot_file_tree(snapshot)
    snapshot_identity = hashlib.sha256(
        canonical_json_bytes(snapshot_tree)
    ).hexdigest()
    if (
        snapshot.name != sources["x_runtime"]["snapshot_revision"]
        or snapshot_tree != sources["x_runtime"]["snapshot_tree"]
        or snapshot_identity
        != sources["x_runtime"]["snapshot_tree_identity_sha256"]
    ):
        raise ValueError("T20.36o optimizer base snapshot drifted")
    head = _git("rev-parse", "HEAD")
    remote = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "codex/pi05-autolearn-loop"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    dependency_versions = {
        name: version(name)
        for name in (
            "datasets",
            "lerobot",
            "pyarrow",
            "safetensors",
            "torch",
            "transformers",
        )
    }
    return {
        "python_major_minor": list(sys.version_info[:2]),
        "mps_available": True,
        "checkpoint_tree": checkpoint_tree,
        "dependency_versions": dependency_versions,
        "snapshot_revision": snapshot.name,
        "snapshot_tree": snapshot_tree,
        "free_disk_bytes": shutil.disk_usage(REPO_ROOT).free,
        "source_commit": head,
        "remote_source_commit": remote,
        "attempt_exists": any(
            (REPO_ROOT / path).exists()
            for path in (ATTEMPT_PATH, TRACKED_ATTEMPT_PATH)
        ),
        "result_exists": any(
            (REPO_ROOT / path).exists()
            for path in (RESULT_PATH, FAILURE_RESULT_PATH)
        ),
        "output_checkpoint_exists": (REPO_ROOT / CHECKPOINT_ROOT).exists()
        or (REPO_ROOT / RUN_ROOT).exists(),
    }


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
