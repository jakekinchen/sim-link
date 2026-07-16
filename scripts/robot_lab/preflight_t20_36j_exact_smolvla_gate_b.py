#!/usr/bin/env python3
"""Write or verify T20.36j's corrected live preflight and one-use permit."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_36h_smolvla_batch import (  # noqa: E402
    load_smolvla_batch,
)
from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (  # noqa: E402
    ATTEMPT_PATH,
    CORRECTED_PREFLIGHT_PATH,
    OFFLINE_ENVIRONMENT,
    RUN_RESULT_PATH,
    RUN_SUMMARY_PATH,
    TRAINING_PERMIT_PATH,
    build_corrected_preflight,
    verify_contract_file,
    verify_corrected_preflight,
)
from scenesmith.robot_lab.t20_36j_exact_smolvla_gate_b import (  # noqa: E402
    FAILURE_PATH,
    FAILURE_RESULT_PATH,
    INSTALLED_CLOSURE_PATH,
    PROCESSOR_SMOKE_PATH,
    RUN_ROOT,
    build_training_permit,
    collect_installed_closure,
    construct_offline_processor_smoke,
    load_verified_spec,
    verify_training_permit,
)
from scenesmith.robot_lab.t20_36j_simulation_training_authority import (  # noqa: E402
    OWNER_GRANT_PATH,
    require_active_authority,
    verify_authority,
)


SCOPED_PATHS = (
    "scenesmith/robot_lab/t20_36j_simulation_training_authority.py",
    "scenesmith/robot_lab/t20_36j_exact_smolvla_gate_b.py",
    "scripts/robot_lab/compose_t20_36j_simulation_training_authority.py",
    "scripts/robot_lab/preflight_t20_36j_exact_smolvla_gate_b.py",
    "scripts/robot_lab/run_t20_36j_exact_smolvla_gate_b.py",
    "tests/unit/test_t20_36j_simulation_training_authority.py",
    "tests/unit/test_t20_36j_exact_smolvla_gate_b.py",
    "configurations/robot_lab/t20_36j_owner_replacement_authorization.json",
    "configurations/robot_lab/t20_36j_simulation_training_authority_request.json",
    "configurations/robot_lab/t20_36j_simulation_training_authority_decision.json",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    contract = verify_contract_file(repo_root=REPO_ROOT)
    authority = (
        verify_authority(repo_root=REPO_ROOT)
        if args.verify
        else require_active_authority(repo_root=REPO_ROOT)
    )
    authority_identity = authority["decision"]["identity_sha256"]
    spec = load_verified_spec(repo_root=REPO_ROOT)
    if args.verify:
        closure = load_strict_json(REPO_ROOT / INSTALLED_CLOSURE_PATH)
        processor = load_strict_json(REPO_ROOT / PROCESSOR_SMOKE_PATH)
        preflight = load_strict_json(REPO_ROOT / CORRECTED_PREFLIGHT_PATH)
        permit = load_strict_json(REPO_ROOT / TRAINING_PERMIT_PATH)
        if preflight.get("installed_closure") != closure:
            raise ValueError("T20.36j standalone installed closure drifted")
        if preflight.get("processor_smoke") != processor:
            raise ValueError("T20.36j standalone processor smoke drifted")
        verify_corrected_preflight(preflight, contract=contract)
        verify_training_permit(
            permit,
            spec=spec,
            authority_identity=authority_identity,
            corrected_preflight=preflight,
        )
        print(preflight["identity_sha256"], permit["identity_sha256"])
        return 0
    output_paths = (
        INSTALLED_CLOSURE_PATH,
        PROCESSOR_SMOKE_PATH,
        CORRECTED_PREFLIGHT_PATH,
        TRAINING_PERMIT_PATH,
        ATTEMPT_PATH,
        RUN_SUMMARY_PATH,
        FAILURE_PATH,
        RUN_RESULT_PATH,
        FAILURE_RESULT_PATH,
    )
    if (REPO_ROOT / RUN_ROOT).exists() or any(
        (REPO_ROOT / path).exists() for path in output_paths
    ):
        raise FileExistsError("T20.36j immutable preflight or attempt artifact exists")
    os.environ.update(
        {
            **OFFLINE_ENVIRONMENT,
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "0",
        }
    )
    closure = collect_installed_closure()
    processor = construct_offline_processor_smoke(
        expected_vlm_snapshot=contract["processor_smoke"]["exact_vlm_snapshot"]
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    import torch

    batch = load_smolvla_batch(repo_root=REPO_ROOT, spec=spec)
    checkpoints = _checkpoint_tree(spec)
    source_commit = _git("rev-parse", "HEAD")
    remote_source_commit = _git(
        "rev-parse", "origin/codex/pi05-autolearn-loop"
    )
    owner = load_strict_json(REPO_ROOT / OWNER_GRANT_PATH)
    preflight = build_corrected_preflight(
        contract=contract,
        owner_authorization_identity_sha256=owner["identity_sha256"],
        authority_decision_identity_sha256=authority_identity,
        installed_closure=closure,
        processor_smoke=processor,
        python_major_minor=list(sys.version_info[:2]),
        mps_available=torch.backends.mps.is_available(),
        free_disk_bytes=shutil.disk_usage(REPO_ROOT).free,
        lerobot_stack_identity_sha256=stack["identity_sha256"],
        batch_evidence_identity_sha256=hashlib.sha256(
            canonical_json_bytes(batch["evidence"])
        ).hexdigest(),
        checkpoint_tree_identity_sha256=hashlib.sha256(
            canonical_json_bytes(checkpoints)
        ).hexdigest(),
        source_commit=source_commit,
        remote_source_commit=remote_source_commit,
        branch=_git("branch", "--show-current"),
        scoped_dirty_paths=_scoped_dirty_paths(),
        attempt_exists=False,
        run_exists=False,
        result_exists=False,
    )
    permit = build_training_permit(
        spec=spec,
        authority_identity=authority_identity,
        corrected_preflight=preflight,
    )
    dump_canonical_json(REPO_ROOT / INSTALLED_CLOSURE_PATH, closure)
    dump_canonical_json(REPO_ROOT / PROCESSOR_SMOKE_PATH, processor)
    dump_canonical_json(REPO_ROOT / CORRECTED_PREFLIGHT_PATH, preflight)
    dump_canonical_json(REPO_ROOT / TRAINING_PERMIT_PATH, permit)
    print(preflight["identity_sha256"], permit["identity_sha256"])
    return 0


def _checkpoint_tree(spec: dict) -> list[dict]:
    rows = []
    for group in ("policy", "vlm"):
        root = Path(spec["local_cache"][f"{group}_snapshot"])
        for source in spec["local_cache"][f"{group}_files"]:
            if not source["is_weight_or_tensor_file"]:
                continue
            path = root / source["name"]
            if not path.is_file() or path.stat().st_size != source["size_bytes"]:
                raise ValueError(f"T20.36j checkpoint file drifted: {path}")
            rows.append(
                {
                    "path": f"{group}/{source['name']}",
                    "size_bytes": path.stat().st_size,
                    "sha256": _file_sha256(path),
                }
            )
    rows.sort(key=lambda row: row["path"])
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
