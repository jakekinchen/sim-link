#!/usr/bin/env python3
"""Run or verify the one-use T20.36m SmolVLA tensor reproduction."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import subprocess
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco  # noqa: E402
from scenesmith.robot_lab.t20_36h_smolvla_batch import load_smolvla_batch  # noqa: E402
from scenesmith.robot_lab.t20_36j_exact_smolvla_gate_b import (  # noqa: E402
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
)
from scenesmith.robot_lab.t20_36m_tensor_reproduction import (  # noqa: E402
    ATTEMPT_PATH,
    FAILURE_PATH,
    FAILURE_RESULT_PATH,
    RESULT_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    TENSOR_PATH,
    build_attempt_marker,
    build_failure,
    build_failure_result,
    build_result,
    build_run_summary,
    build_tensor_artifact,
    load_live_contracts,
    verify_attempt_marker,
    verify_result,
    verify_run_summary,
    verify_tensor_artifact,
)
from scenesmith.robot_lab.t20_36m_tensor_reproduction_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
)
from scripts.robot_lab.run_t20_36h_exact_smolvla_gate_b import _decode  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    authority = (
        verify_authority(repo_root=REPO_ROOT)
        if args.verify
        else require_active_authority(repo_root=REPO_ROOT)
    )
    authority_identity = authority["decision"]["identity_sha256"]
    sources, preflight, permit = load_live_contracts(
        authority_identity=authority_identity, repo_root=REPO_ROOT
    )
    if args.verify:
        return _verify_outputs(sources, authority_identity, permit)
    if (REPO_ROOT / RUN_ROOT).exists() or any(
        (REPO_ROOT / path).exists() for path in (RESULT_PATH, FAILURE_RESULT_PATH)
    ):
        raise FileExistsError("T20.36m immutable tensor reproduction already exists")
    _require_remote_preservation(permit)
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "0",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    if stack["identity_sha256"] != preflight["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36m LeRobot stack drifted after preflight")
    batch_source = load_smolvla_batch(
        repo_root=REPO_ROOT, spec=sources["smolvla_spec"]
    )
    batch_identity = hashlib.sha256(
        canonical_json_bytes(batch_source["evidence"])
    ).hexdigest()
    if batch_identity != preflight["batch_evidence_identity_sha256"]:
        raise ValueError("T20.36m canonical batch drifted after preflight")
    current_commit = _git("rev-parse", "HEAD")
    attempt = build_attempt_marker(
        permit=permit,
        authority_identity=authority_identity,
        source_commit=current_commit,
    )
    (REPO_ROOT / RUN_ROOT).mkdir(parents=True, exist_ok=False)
    dump_canonical_json(REPO_ROOT / ATTEMPT_PATH, attempt)
    verify_attempt_marker(
        attempt, permit=permit, authority_identity=authority_identity
    )
    state = {
        "stage": "model_construction",
        "checkpoint_tensor_read": False,
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "tensor_artifact_written": False,
    }
    try:
        result = _execute(
            sources=sources,
            authority_identity=authority_identity,
            permit=permit,
            attempt=attempt,
            batch_source=batch_source,
            state=state,
        )
    except Exception as error:
        failure = build_failure(
            permit=permit,
            attempt=attempt,
            failure_stage=state["stage"],
            error_type=type(error).__name__,
            error_message=(str(error) or repr(error))[:2000],
            checkpoint_tensor_read=state["checkpoint_tensor_read"],
            model_constructed=state["model_constructed"],
            model_loaded=state["model_loaded"],
            model_inference=state["model_inference"],
            tensor_artifact_written=state["tensor_artifact_written"],
        )
        failure_result = build_failure_result(sources=sources, failure=failure)
        dump_canonical_json(REPO_ROOT / FAILURE_PATH, failure)
        dump_canonical_json(REPO_ROOT / FAILURE_RESULT_PATH, failure_result)
        print(failure_result["identity_sha256"], flush=True)
        raise
    print(result["identity_sha256"], result["decision"], flush=True)
    return 0


def _execute(
    *,
    sources,
    authority_identity,
    permit,
    attempt,
    batch_source,
    state,
):
    import torch

    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    from lerobot.policies.smolvla.processor_smolvla import (
        make_smolvla_pre_post_processors,
    )
    from torch.utils.data import default_collate

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36m requires the authorized local MPS runtime")
    state["model_constructed"] = True
    state["checkpoint_tensor_read"] = True
    policy = SmolVLAPolicy.from_pretrained(
        REPO_ROOT / SOURCE_CHECKPOINT_ROOT,
        local_files_only=True,
        strict=True,
    )
    state["model_loaded"] = True
    policy.eval()
    preprocessor, postprocessor = make_smolvla_pre_post_processors(
        policy.config, dataset_stats=batch_source["dataset"].meta.stats
    )
    raw_batch = default_collate([batch_source["item"]])
    observation = {
        key: copy.deepcopy(value)
        for key, value in raw_batch.items()
        if key.startswith("observation.") or key == "task"
    }
    processed_observation = preprocessor(observation)
    state["stage"] = "tensor_reproduction"
    rows = []
    for index, seed in enumerate(permit["inference_seeds"]):
        first = _decode(
            policy, postprocessor, processed_observation, torch, seed=seed
        )
        second = _decode(
            policy, postprocessor, processed_observation, torch, seed=seed
        )
        first_physical = np.asarray(
            [lerobot_to_mujoco(row.tolist()) for row in first], dtype=np.float64
        )
        second_physical = np.asarray(
            [lerobot_to_mujoco(row.tolist()) for row in second], dtype=np.float64
        )
        rows.append(
            {
                "seed_index": index,
                "inference_seed": seed,
                "first": first_physical.astype(float).tolist(),
                "second": second_physical.astype(float).tolist(),
            }
        )
    state["model_inference"] = True
    target = batch_source["physical_action"].astype(float).tolist()
    tensor_artifact = build_tensor_artifact(
        attempt=attempt, rows=rows, target=target
    )
    dump_canonical_json(REPO_ROOT / TENSOR_PATH, tensor_artifact)
    state["tensor_artifact_written"] = True
    verify_tensor_artifact(tensor_artifact, attempt=attempt, target=target)
    state["stage"] = "frozen_gate_scoring"
    run = build_run_summary(
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        target=target,
    )
    result = build_result(sources=sources, run=run)
    dump_canonical_json(REPO_ROOT / RUN_SUMMARY_PATH, run)
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    verify_run_summary(
        run,
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        target=target,
    )
    verify_result(result, sources=sources, run=run)
    return result


def _verify_outputs(sources, authority_identity, permit) -> int:
    attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
    verify_attempt_marker(
        attempt, permit=permit, authority_identity=authority_identity
    )
    if (REPO_ROOT / FAILURE_RESULT_PATH).exists():
        failure = load_strict_json(REPO_ROOT / FAILURE_PATH)
        failure_result = load_strict_json(REPO_ROOT / FAILURE_RESULT_PATH)
        verify_signed_payload(failure, label="T20.36m failure")
        verify_signed_payload(failure_result, label="T20.36m failure result")
        print(failure_result["identity_sha256"], failure_result["decision"])
        return 0
    batch_source = load_smolvla_batch(
        repo_root=REPO_ROOT, spec=sources["smolvla_spec"]
    )
    target = batch_source["physical_action"].astype(float).tolist()
    tensor_artifact = load_strict_json(REPO_ROOT / TENSOR_PATH)
    run = load_strict_json(REPO_ROOT / RUN_SUMMARY_PATH)
    result = load_strict_json(REPO_ROOT / RESULT_PATH)
    verify_tensor_artifact(tensor_artifact, attempt=attempt, target=target)
    verify_run_summary(
        run,
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        target=target,
    )
    verify_result(result, sources=sources, run=run)
    print(result["identity_sha256"], result["decision"])
    return 0


def _require_remote_preservation(permit) -> None:
    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36m run is on the wrong branch")
    head = _git("rev-parse", "HEAD")
    remote = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "codex/pi05-autolearn-loop"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    if head != remote:
        raise ValueError("T20.36m current source is not remotely preserved")
    subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            permit["required_source_commit"],
            head,
        ],
        cwd=REPO_ROOT,
        check=True,
    )


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
