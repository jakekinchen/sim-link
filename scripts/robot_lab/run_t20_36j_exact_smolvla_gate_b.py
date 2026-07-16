#!/usr/bin/env python3
"""Run or verify the sole corrected T20.36j SmolVLA Gate B replacement."""

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
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (  # noqa: E402
    EVALUATION_UPDATE_SCHEDULE,
)
from scenesmith.robot_lab.t20_36h_smolvla_batch import (  # noqa: E402
    load_smolvla_batch,
)
from scenesmith.robot_lab.t20_36j_b_corrected_preflight_contract import (  # noqa: E402
    RUN_RESULT_PATH,
)
from scenesmith.robot_lab.t20_36j_exact_smolvla_gate_b import (  # noqa: E402
    ATTEMPT_PATH,
    CHECKPOINT_ROOT,
    FAILURE_PATH,
    FAILURE_RESULT_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    build_attempt_marker,
    build_failure,
    build_failure_result,
    build_result,
    build_run_summary,
    load_live_contracts,
    verify_attempt_marker,
    verify_failure,
    verify_failure_result,
    verify_result,
    verify_run_summary,
)
from scenesmith.robot_lab.t20_36j_simulation_training_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
)
from scripts.robot_lab.run_t20_36h_exact_smolvla_gate_b import (  # noqa: E402
    _build_config,
    _evaluation,
    _file_tree,
    _objective_by_seed,
    _runtime_smoke,
    _seed_all,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    authority = (
        verify_authority(repo_root=REPO_ROOT)
        if args.verify
        else require_active_authority(repo_root=REPO_ROOT)
    )
    authority_identity = authority["decision"]["identity_sha256"]
    spec, preflight, permit = load_live_contracts(
        authority_identity=authority_identity
    )
    if args.verify:
        return _verify_outputs(spec, authority_identity, permit)
    if (REPO_ROOT / RUN_ROOT).exists() or any(
        (REPO_ROOT / path).exists()
        for path in (RUN_RESULT_PATH, FAILURE_RESULT_PATH)
    ):
        raise FileExistsError("T20.36j immutable replacement attempt already exists")
    _require_remote_preservation(permit)
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "0",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    if stack["identity_sha256"] != preflight["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36j LeRobot stack drifted after preflight")
    batch_source = load_smolvla_batch(repo_root=REPO_ROOT, spec=spec)
    batch_identity = hashlib.sha256(
        canonical_json_bytes(batch_source["evidence"])
    ).hexdigest()
    if batch_identity != preflight["batch_evidence_identity_sha256"]:
        raise ValueError("T20.36j canonical batch drifted after preflight")
    current_commit = _git("rev-parse", "HEAD")
    attempt = build_attempt_marker(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
        source_commit=current_commit,
    )
    (REPO_ROOT / RUN_ROOT).mkdir(parents=True, exist_ok=False)
    dump_canonical_json(REPO_ROOT / ATTEMPT_PATH, attempt)
    verify_attempt_marker(
        attempt,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
    )
    state = {
        "stage": "model_construction",
        "optimizer_update_count": 0,
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
    }
    try:
        identity = _execute(
            spec,
            authority_identity,
            permit,
            attempt,
            batch_source,
            state,
        )
    except Exception as error:
        message = str(error) or repr(error)
        failure = build_failure(
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
            attempt=attempt,
            failure_stage=state["stage"],
            error_type=type(error).__name__,
            error_message=message[:2000],
            optimizer_update_count=state["optimizer_update_count"],
            model_constructed=state["model_constructed"],
            model_loaded=state["model_loaded"],
            model_inference=state["model_inference"],
            optimizer_created=state["optimizer_created"],
            optimizer_training=state["optimizer_training"],
        )
        result = build_failure_result(
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
            attempt=attempt,
            failure=failure,
        )
        dump_canonical_json(REPO_ROOT / FAILURE_PATH, failure)
        dump_canonical_json(REPO_ROOT / FAILURE_RESULT_PATH, result)
        print(result["identity_sha256"], flush=True)
        raise
    print(identity, flush=True)
    return 0


def _execute(
    spec,
    authority_identity,
    permit,
    attempt,
    batch_source,
    state,
):
    import torch

    from lerobot.configs.types import FeatureType, NormalizationMode, PolicyFeature
    from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    from lerobot.policies.smolvla.processor_smolvla import (
        make_smolvla_pre_post_processors,
    )
    from torch.utils.data import default_collate

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36j requires the authorized local MPS runtime")
    _seed_all(spec["campaign"]["training_seed"], torch)
    config = _build_config(
        spec, SmolVLAConfig, FeatureType, NormalizationMode, PolicyFeature
    )
    state["model_constructed"] = True
    policy = SmolVLAPolicy.from_pretrained(
        spec["runtime_contract"]["policy_checkpoint_path"],
        config=config,
        local_files_only=True,
        strict=True,
    )
    state["model_loaded"] = True
    preprocessor, postprocessor = make_smolvla_pre_post_processors(
        config, dataset_stats=batch_source["dataset"].meta.stats
    )
    raw_batch = default_collate([batch_source["item"]])
    processed = preprocessor(copy.deepcopy(raw_batch))
    state["stage"] = "runtime_smoke"
    smoke, trainable = _runtime_smoke(policy, processed, torch)
    state["stage"] = "evaluation"
    baseline_values = _objective_by_seed(policy, processed, torch)
    baseline = float(np.mean(baseline_values))
    state["model_inference"] = True
    baseline_evaluation = _evaluation(
        policy,
        preprocessor,
        postprocessor,
        raw_batch,
        batch_source["physical_action"],
        torch,
        update=0,
        objective_values=baseline_values,
        baseline=baseline,
    )
    optimizer = torch.optim.AdamW(
        trainable,
        lr=spec["campaign"]["learning_rate"],
        betas=tuple(spec["campaign"]["betas"]),
        eps=spec["campaign"]["epsilon"],
        weight_decay=spec["campaign"]["weight_decay"],
    )
    state["optimizer_created"] = True
    evaluations = [baseline_evaluation]
    losses = []
    gradients = []
    selected_update = None
    state["stage"] = "optimizer_training"
    state["optimizer_training"] = True
    for update in range(1, spec["campaign"]["maximum_optimizer_updates"] + 1):
        policy.train()
        optimizer.zero_grad(set_to_none=True)
        _seed_all(spec["campaign"]["training_seed"] + update - 1, torch)
        loss, _ = policy(processed)
        if not torch.isfinite(loss):
            raise ValueError(f"T20.36j non-finite objective at update {update}")
        loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in trainable
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.36j non-finite gradient at update {update}")
        norm = torch.nn.utils.clip_grad_norm_(
            trainable, spec["campaign"]["gradient_clip_norm"]
        )
        if not torch.isfinite(norm):
            raise ValueError(f"T20.36j non-finite gradient norm at update {update}")
        optimizer.step()
        torch.mps.synchronize()
        state["optimizer_update_count"] = update
        losses.append(float(loss.detach().cpu()))
        gradients.append(float(norm.detach().cpu()))
        if update % 25 == 0:
            print(update, losses[-1], flush=True)
        if update in EVALUATION_UPDATE_SCHEDULE[1:]:
            state["stage"] = "evaluation"
            objective_values = _objective_by_seed(policy, processed, torch)
            row = _evaluation(
                policy,
                preprocessor,
                postprocessor,
                raw_batch,
                batch_source["physical_action"],
                torch,
                update=update,
                objective_values=objective_values,
                baseline=baseline,
            )
            evaluations.append(row)
            print(
                "evaluation",
                update,
                row["final_to_baseline_supervised_objective_ratio"],
                row["maximum_absolute_error_rad"],
                row["gate_b_passed"],
                flush=True,
            )
            if row["gate_b_passed"]:
                selected_update = update
                break
            state["stage"] = "optimizer_training"
    if selected_update is None:
        selected_update = spec["campaign"]["maximum_optimizer_updates"]
    state["stage"] = "checkpoint_write"
    policy.save_pretrained(REPO_ROOT / CHECKPOINT_ROOT)
    preprocessor.save_pretrained(REPO_ROOT / CHECKPOINT_ROOT)
    postprocessor.save_pretrained(REPO_ROOT / CHECKPOINT_ROOT)
    checkpoint_tree = _file_tree(REPO_ROOT / CHECKPOINT_ROOT)
    run = build_run_summary(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
        attempt=attempt,
        runtime_smoke=smoke,
        optimizer_update_count=selected_update,
        per_update_objective=losses,
        gradient_norms_before_clip=gradients,
        evaluations=evaluations,
        checkpoint_tree=checkpoint_tree,
    )
    dump_canonical_json(REPO_ROOT / RUN_SUMMARY_PATH, run)
    result = build_result(spec=spec, run=run)
    dump_canonical_json(REPO_ROOT / RUN_RESULT_PATH, result)
    verify_run_summary(
        run,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
        attempt=attempt,
    )
    verify_result(result, spec=spec, run=run)
    return result["identity_sha256"]


def _verify_outputs(spec, authority_identity, permit) -> int:
    attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
    verify_attempt_marker(
        attempt,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
    )
    failure_path = REPO_ROOT / FAILURE_PATH
    if failure_path.exists():
        if (REPO_ROOT / RUN_RESULT_PATH).exists() or (
            REPO_ROOT / RUN_SUMMARY_PATH
        ).exists():
            raise ValueError("T20.36j failure and successful result coexist")
        failure = load_strict_json(failure_path)
        verify_failure(
            failure,
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
            attempt=attempt,
        )
        result = load_strict_json(REPO_ROOT / FAILURE_RESULT_PATH)
        verify_failure_result(
            result,
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
            attempt=attempt,
            failure=failure,
        )
        print(result["identity_sha256"])
        return 0
    run = load_strict_json(REPO_ROOT / RUN_SUMMARY_PATH)
    verify_run_summary(
        run,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
        attempt=attempt,
    )
    if _file_tree(REPO_ROOT / CHECKPOINT_ROOT) != run["checkpoint_tree"]:
        raise ValueError("T20.36j saved checkpoint files drifted")
    result = load_strict_json(REPO_ROOT / RUN_RESULT_PATH)
    verify_result(result, spec=spec, run=run)
    print(result["identity_sha256"])
    return 0


def _require_remote_preservation(permit) -> None:
    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36j run is on the wrong branch")
    head = _git("rev-parse", "HEAD")
    remote = _git("rev-parse", "origin/codex/pi05-autolearn-loop")
    if head != remote:
        raise ValueError("T20.36j current source is not remotely preserved")
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
