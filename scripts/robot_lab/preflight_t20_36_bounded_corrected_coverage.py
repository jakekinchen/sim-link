#!/usr/bin/env python3
"""Write or verify T20.36's dependency preflight and one-use permit."""

from __future__ import annotations

import argparse
import importlib.metadata
import subprocess
import sys
import tempfile
import shutil

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_36_bounded_corrected_coverage import (  # noqa: E402
    ATTEMPT_PATH,
    RECOVERY_DATASET_ROOT,
    RESULT_PATH,
    RUN_ROOT,
    RUNTIME_PREFLIGHT_PATH,
    SPEC_PATH,
    TRAINING_PERMIT_PATH,
    X_CHECKPOINT_ROOT,
    build_runtime_preflight,
    build_training_permit,
    file_tree,
    load_source_artifacts,
    verify_runtime_preflight,
    verify_training_permit,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_36_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_source_artifacts(repo_root=REPO_ROOT)
    spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    verify_training_spec(spec, **sources)
    authority = require_active_authority(repo_root=REPO_ROOT)
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
        raise FileExistsError("T20.36 immutable preflight or permit already exists")
    if (
        (REPO_ROOT / RUN_ROOT).exists()
        or (REPO_ROOT / ATTEMPT_PATH).exists()
        or (REPO_ROOT / RESULT_PATH).exists()
    ):
        raise FileExistsError("T20.36 attempt or result exists before preflight")
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    import datasets  # noqa: F401
    import lerobot  # noqa: F401
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    import pyarrow  # noqa: F401
    import safetensors  # noqa: F401
    import torch
    import transformers  # noqa: F401

    versions = {
        package: importlib.metadata.version(package)
        for package in spec["required_dependency_versions"]
    }
    ffmpeg = subprocess.run(
        ["ffmpeg", "-version"], capture_output=True, text=True, check=True
    ).stdout.splitlines()[0].split()[2]
    with tempfile.TemporaryDirectory(prefix="scenesmith-t20-36-render-preflight-") as directory:
        output = Path(directory) / "smoke.mp4"
        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/robot_lab/render_rollout_mirror.py"),
                "--trace",
                str(
                    REPO_ROOT
                    / "outputs/robot_lab/t20_32_closed_loop_divergence/t20_24_recovery_augmented_seed_0.json"
                ),
                "--output-mp4",
                str(output),
                "--max-frames",
                "1",
            ],
            cwd=REPO_ROOT,
            check=True,
        )
        manifest = load_strict_json(output.with_suffix(".manifest.json"))
        verify_signed_payload(manifest, label="T20.36 render smoke manifest")
        render_smoke_verified = (
            output.is_file()
            and output.stat().st_size == manifest["output_bytes"]
            and manifest["frame_count"] == 1
        )
    runtime = build_runtime_preflight(
        spec=spec,
        authority_identity=authority_identity,
        python_major_minor=list(sys.version_info[:2]),
        dependency_versions=versions,
        mps_available=torch.backends.mps.is_available(),
        lerobot_stack_identity_sha256=stack["identity_sha256"],
        ffmpeg_version=ffmpeg,
        render_smoke_verified=render_smoke_verified,
        free_disk_bytes=shutil.disk_usage(REPO_ROOT).free,
        source_checkpoint_tree_verified=(
            file_tree(REPO_ROOT / X_CHECKPOINT_ROOT)
            == spec["source_gate_b"]["checkpoint_tree"]
        ),
        coverage_dataset_tree_verified=(
            file_tree(REPO_ROOT / RECOVERY_DATASET_ROOT)
            == spec["coverage_dataset"]["file_tree"]
        ),
        attempt_exists=False,
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


if __name__ == "__main__":
    raise SystemExit(main())
