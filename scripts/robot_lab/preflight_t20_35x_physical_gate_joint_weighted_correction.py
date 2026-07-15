#!/usr/bin/env python3
"""Write or verify T20.35x's dependency preflight and one-use permit."""

from __future__ import annotations

import argparse
import importlib.metadata
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    RESULT_PATH,
    RUNTIME_PREFLIGHT_PATH,
    SPEC_PATH,
    TRAINING_PERMIT_PATH,
    EXPECTED_RUNTIME_PREFLIGHT_IDENTITY,
    EXPECTED_TRAINING_PERMIT_IDENTITY,
    build_runtime_preflight,
    build_training_permit,
    load_source_artifacts,
    verify_runtime_preflight,
    verify_training_permit,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_35x_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)
from scripts.robot_lab.run_t20_35d_residual_localization import (  # noqa: E402
    _file_tree,
)
from scripts.robot_lab.run_t20_35t_time_normalized_standard_replay_correction import (  # noqa: E402
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
)
from scripts.robot_lab.run_t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    ATTEMPT_PATH,
    RUN_ROOT,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    sources = load_source_artifacts(repo_root=REPO_ROOT)
    spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    verify_training_spec(
        spec,
        source_spec=sources["source_spec"],
        source_run=sources["source_run"],
        source_result=sources["source_result"],
        trajectory_spec=sources["trajectory_spec"],
        trajectory_result=sources["trajectory_result"],
        target_result=sources["target_result"],
        outlier_audit=sources["outlier_audit"],
        dataset_manifest=sources["dataset_manifest"],
        dataset_stats=sources["dataset_stats"],
        dataset_stats_file_sha256=sources["dataset_stats_file_sha256"],
    )
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
        if (
            runtime["identity_sha256"] != EXPECTED_RUNTIME_PREFLIGHT_IDENTITY
            or permit["identity_sha256"] != EXPECTED_TRAINING_PERMIT_IDENTITY
        ):
            raise ValueError("T20.35x archived preflight or permit identity drifted")
        print(runtime["identity_sha256"], permit["identity_sha256"])
        return 0

    if runtime_path.exists() or permit_path.exists():
        raise FileExistsError("T20.35x immutable preflight or permit already exists")
    if RUN_ROOT.exists() or ATTEMPT_PATH.exists() or (REPO_ROOT / RESULT_PATH).exists():
        raise FileExistsError("T20.35x attempt or result exists before preflight")

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
        for package in (
            "datasets",
            "lerobot",
            "pyarrow",
            "safetensors",
            "torch",
            "transformers",
        )
    }
    checkpoint_tree_verified = (
        _file_tree(REPO_ROOT / SOURCE_CHECKPOINT_ROOT) == spec["source_checkpoint_tree"]
    )
    runtime = build_runtime_preflight(
        spec=spec,
        authority_identity=authority_identity,
        python_major_minor=list(sys.version_info[:2]),
        dependency_versions=versions,
        mps_available=torch.backends.mps.is_available(),
        lerobot_stack_identity_sha256=stack["identity_sha256"],
        checkpoint_tree_verified=checkpoint_tree_verified,
        attempt_exists=False,
        result_exists=False,
    )
    permit = build_training_permit(
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime,
    )
    if (
        runtime["identity_sha256"] != EXPECTED_RUNTIME_PREFLIGHT_IDENTITY
        or permit["identity_sha256"] != EXPECTED_TRAINING_PERMIT_IDENTITY
    ):
        raise ValueError("T20.35x derived preflight or permit identity drifted")
    dump_canonical_json(runtime_path, runtime)
    dump_canonical_json(permit_path, permit)
    print(runtime["identity_sha256"], permit["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
