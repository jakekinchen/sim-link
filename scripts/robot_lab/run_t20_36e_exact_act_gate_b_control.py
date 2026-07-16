#!/usr/bin/env python3
"""Run or verify the authorized exact T20.36e ACT Gate B control."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import random
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
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco  # noqa: E402
from scenesmith.robot_lab.t20_36e_act_batch import load_exact_batch  # noqa: E402
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (  # noqa: E402
    ATTEMPT_PATH,
    CHECKPOINT_ROOT,
    EVALUATION_UPDATE_SCHEDULE,
    EXPECTED_BATCH_EVIDENCE,
    RESULT_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    RUNTIME_PREFLIGHT_PATH,
    TRAINING_PERMIT_PATH,
    build_attempt_marker,
    build_evaluation_row,
    build_result,
    build_run_summary,
    load_verified_spec,
    verify_attempt_marker,
    verify_result,
    verify_run_summary,
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
    runtime = load_strict_json(REPO_ROOT / RUNTIME_PREFLIGHT_PATH)
    verify_runtime_preflight(
        runtime, spec=spec, authority_identity=authority_identity
    )
    permit = load_strict_json(REPO_ROOT / TRAINING_PERMIT_PATH)
    verify_training_permit(
        permit,
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime,
    )
    if args.verify:
        attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
        verify_attempt_marker(
            attempt,
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
        )
        run = load_strict_json(REPO_ROOT / RUN_SUMMARY_PATH)
        verify_run_summary(
            run,
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
            attempt=attempt,
        )
        if _file_tree(REPO_ROOT / CHECKPOINT_ROOT) != run["checkpoint_tree"]:
            raise ValueError("T20.36e checkpoint files drifted")
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_result(result, spec=spec, run=run)
        print(result["identity_sha256"])
        return 0
    if (REPO_ROOT / RUN_ROOT).exists() or (REPO_ROOT / RESULT_PATH).exists():
        raise FileExistsError("T20.36e immutable attempt already exists")
    _require_remote_preservation(permit)
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    if stack["identity_sha256"] != runtime["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36e LeRobot stack drifted after preflight")
    batch_source = load_exact_batch(repo_root=REPO_ROOT, spec=spec)
    if batch_source["evidence"] != EXPECTED_BATCH_EVIDENCE:
        raise ValueError("T20.36e batch drifted after preflight")
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

    import torch

    from lerobot.configs.types import (
        FeatureType,
        NormalizationMode,
        PolicyFeature,
    )
    from lerobot.policies.act.configuration_act import ACTConfig
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.act.processor_act import make_act_pre_post_processors
    from torch.utils.data import default_collate

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36e requires the authorized local MPS runtime")
    _seed_all(spec["campaign"]["training_seed"], torch)
    config = _build_config(
        spec, ACTConfig, FeatureType, NormalizationMode, PolicyFeature
    )
    policy = ACTPolicy(config).to("mps")
    if {parameter.dtype for parameter in policy.parameters()} != {torch.float32}:
        raise ValueError("T20.36e ACT parameters are not uniformly float32")
    preprocessor, postprocessor = make_act_pre_post_processors(
        config, dataset_stats=batch_source["dataset"].meta.stats
    )
    raw_batch = default_collate([batch_source["item"]])
    processed = preprocessor(copy.deepcopy(raw_batch))
    trainable = [
        parameter for parameter in policy.parameters() if parameter.requires_grad
    ]
    if not trainable:
        raise ValueError("T20.36e ACT has no trainable parameters")
    optimizer = torch.optim.AdamW(
        trainable,
        lr=spec["campaign"]["learning_rate"],
        betas=tuple(spec["campaign"]["betas"]),
        eps=spec["campaign"]["epsilon"],
        weight_decay=spec["campaign"]["weight_decay"],
    )
    baseline = _objective(policy, processed, torch)
    evaluations = [
        _evaluation(
            policy,
            preprocessor,
            postprocessor,
            raw_batch,
            batch_source["physical_action"],
            torch,
            update=0,
            objective=baseline,
            baseline=baseline,
        )
    ]
    losses: list[float] = []
    gradients: list[float] = []
    selected_update = None
    for update in range(1, spec["campaign"]["maximum_optimizer_updates"] + 1):
        policy.train()
        optimizer.zero_grad(set_to_none=True)
        _seed_all(spec["campaign"]["training_seed"] + update - 1, torch)
        loss, _ = policy(processed)
        if not torch.isfinite(loss):
            raise ValueError(f"T20.36e non-finite objective at update {update}")
        loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in trainable
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.36e non-finite gradient at update {update}")
        norm = torch.nn.utils.clip_grad_norm_(
            trainable, spec["campaign"]["gradient_clip_norm"]
        )
        if not torch.isfinite(norm):
            raise ValueError(f"T20.36e non-finite gradient norm at update {update}")
        optimizer.step()
        torch.mps.synchronize()
        losses.append(float(loss.detach().cpu()))
        gradients.append(float(norm.detach().cpu()))
        if update % 25 == 0:
            print(update, losses[-1], flush=True)
        if update in EVALUATION_UPDATE_SCHEDULE[1:]:
            objective = _objective(policy, processed, torch)
            row = _evaluation(
                policy,
                preprocessor,
                postprocessor,
                raw_batch,
                batch_source["physical_action"],
                torch,
                update=update,
                objective=objective,
                baseline=baseline,
            )
            evaluations.append(row)
            print(
                "evaluation",
                update,
                row["final_to_baseline_supervised_objective_ratio"],
                row["maximum_absolute_error_rad"],
                row["gate_b_control_passed"],
                flush=True,
            )
            if row["gate_b_control_passed"]:
                selected_update = update
                break
    if selected_update is None:
        selected_update = spec["campaign"]["maximum_optimizer_updates"]
    policy.save_pretrained(REPO_ROOT / CHECKPOINT_ROOT, safe_serialization=True)
    checkpoint_tree = _file_tree(REPO_ROOT / CHECKPOINT_ROOT)
    checkpoint_identity = hashlib.sha256(
        canonical_json_bytes(checkpoint_tree)
    ).hexdigest()
    run = build_run_summary(
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
        attempt=attempt,
        optimizer_update_count=selected_update,
        per_update_objective=losses,
        gradient_norms_before_clip=gradients,
        evaluations=evaluations,
        checkpoint_tree=checkpoint_tree,
        checkpoint_identity_sha256=checkpoint_identity,
    )
    dump_canonical_json(REPO_ROOT / RUN_SUMMARY_PATH, run)
    result = build_result(spec=spec, run=run)
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    verify_run_summary(
        run,
        spec=spec,
        authority_identity=authority_identity,
        training_permit=permit,
        attempt=attempt,
    )
    verify_result(result, spec=spec, run=run)
    print(result["identity_sha256"], flush=True)
    return 0


def _build_config(spec, ACTConfig, FeatureType, NormalizationMode, PolicyFeature):
    source = spec["act_config"]
    features = {
        key: PolicyFeature(
            type=FeatureType[value["type"]], shape=tuple(value["shape"])
        )
        for key, value in source["input_features"].items()
    }
    outputs = {
        key: PolicyFeature(
            type=FeatureType[value["type"]], shape=tuple(value["shape"])
        )
        for key, value in source["output_features"].items()
    }
    normalization = {
        key: NormalizationMode[value]
        for key, value in source["normalization_mapping"].items()
    }
    return ACTConfig(
        input_features=features,
        output_features=outputs,
        normalization_mapping=normalization,
        n_obs_steps=source["n_obs_steps"],
        chunk_size=source["chunk_size"],
        n_action_steps=source["n_action_steps"],
        vision_backbone=source["vision_backbone"],
        pretrained_backbone_weights=source["pretrained_backbone_weights"],
        replace_final_stride_with_dilation=source[
            "replace_final_stride_with_dilation"
        ],
        pre_norm=source["pre_norm"],
        dim_model=source["dim_model"],
        n_heads=source["n_heads"],
        dim_feedforward=source["dim_feedforward"],
        feedforward_activation=source["feedforward_activation"],
        n_encoder_layers=source["n_encoder_layers"],
        n_decoder_layers=source["n_decoder_layers"],
        use_vae=source["use_vae"],
        temporal_ensemble_coeff=source["temporal_ensemble_coeff"],
        dropout=source["dropout"],
        device=source["device"],
        use_amp=source["use_amp"],
        optimizer_lr=spec["campaign"]["learning_rate"],
        optimizer_lr_backbone=spec["campaign"]["learning_rate"],
        optimizer_weight_decay=spec["campaign"]["weight_decay"],
    )


def _objective(policy, batch, torch) -> float:
    policy.eval()
    with torch.no_grad():
        loss, _ = policy(batch)
    if not torch.isfinite(loss):
        raise ValueError("T20.36e non-finite evaluation objective")
    return float(loss.detach().cpu())


def _evaluation(
    policy,
    preprocessor,
    postprocessor,
    raw_batch,
    target,
    torch,
    *,
    update,
    objective,
    baseline,
):
    observation = {
        key: copy.deepcopy(value)
        for key, value in raw_batch.items()
        if key.startswith("observation.")
    }
    processed_observation = preprocessor(observation)
    repetitions = []
    policy.eval()
    with torch.no_grad():
        for index in range(5):
            policy.reset()
            decoded = []
            for _ in range(50):
                canonical = postprocessor(policy.select_action(processed_observation))
                values = canonical.detach().cpu().float().numpy().reshape(-1)
                decoded.append(lerobot_to_mujoco(values.tolist()))
            matrix = np.asarray(decoded, dtype=np.float64)
            error = np.abs(matrix - target)
            repetitions.append(
                {
                    "repetition_index": index,
                    "action_chunk_sha256": hashlib.sha256(
                        canonical_json_bytes(matrix.astype(float).tolist())
                    ).hexdigest(),
                    "mean_absolute_error_rad": float(np.mean(error)),
                    "maximum_absolute_error_rad": float(np.max(error)),
                }
            )
    return build_evaluation_row(
        optimizer_update_count=update,
        supervised_objective_mean=objective,
        baseline_objective_mean=baseline,
        repetition_rows=repetitions,
    )


def _require_remote_preservation(permit) -> None:
    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36e run is on the wrong branch")
    head = _git("rev-parse", "HEAD")
    remote = subprocess.run(
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
    if head != remote:
        raise ValueError("T20.36e current source is not remotely preserved")
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


def _seed_all(seed: int, torch) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _file_tree(root: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
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


if __name__ == "__main__":
    raise SystemExit(main())
