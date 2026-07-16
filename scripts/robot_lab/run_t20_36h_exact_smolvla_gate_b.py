#!/usr/bin/env python3
"""Run or verify the authorized exact T20.36h SmolVLA Gate B attempt."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import random
import subprocess
import sys

from collections import defaultdict
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
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (  # noqa: E402
    ATTEMPT_PATH,
    CHECKPOINT_ROOT,
    EVALUATION_UPDATE_SCHEDULE,
    FAILURE_PATH,
    INFERENCE_SEEDS,
    OBJECTIVE_SEEDS,
    RESULT_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    RUNTIME_PREFLIGHT_PATH,
    SMOKE_SEED,
    TRAINING_PERMIT_PATH,
    build_attempt_marker,
    build_evaluation_row,
    build_failure,
    build_result,
    build_run_summary,
    load_verified_spec,
    verify_attempt_marker,
    verify_failure,
    verify_result,
    verify_run_summary,
    verify_runtime_preflight,
    verify_training_permit,
)
from scenesmith.robot_lab.t20_36h_simulation_training_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
)
from scenesmith.robot_lab.t20_36h_smolvla_batch import (  # noqa: E402
    load_smolvla_batch,
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
        return _verify_outputs(spec, authority_identity, permit)
    if (REPO_ROOT / RUN_ROOT).exists() or (REPO_ROOT / RESULT_PATH).exists():
        raise FileExistsError("T20.36h immutable attempt already exists")
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
    if stack["identity_sha256"] != runtime["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36h LeRobot stack drifted after preflight")
    batch_source = load_smolvla_batch(repo_root=REPO_ROOT, spec=spec)
    if batch_source["evidence"] != runtime["batch_evidence"]:
        raise ValueError("T20.36h canonical batch drifted after preflight")
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
            runtime,
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
        dump_canonical_json(REPO_ROOT / FAILURE_PATH, failure)
        print(failure["identity_sha256"], flush=True)
        raise
    print(identity, flush=True)
    return 0


def _execute(
    spec,
    authority_identity,
    runtime,
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
        raise RuntimeError("T20.36h requires the authorized local MPS runtime")
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
            raise ValueError(f"T20.36h non-finite objective at update {update}")
        loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in trainable
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.36h non-finite gradient at update {update}")
        norm = torch.nn.utils.clip_grad_norm_(
            trainable, spec["campaign"]["gradient_clip_norm"]
        )
        if not torch.isfinite(norm):
            raise ValueError(f"T20.36h non-finite gradient norm at update {update}")
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
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
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
    result_path = REPO_ROOT / RESULT_PATH
    if failure_path.exists():
        if result_path.exists() or (REPO_ROOT / RUN_SUMMARY_PATH).exists():
            raise ValueError("T20.36h failure and successful result coexist")
        failure = load_strict_json(failure_path)
        verify_failure(
            failure,
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
            attempt=attempt,
        )
        print(failure["identity_sha256"])
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
        raise ValueError("T20.36h saved checkpoint files drifted")
    result = load_strict_json(result_path)
    verify_result(result, spec=spec, run=run)
    print(result["identity_sha256"])
    return 0


def _build_config(
    spec, SmolVLAConfig, FeatureType, NormalizationMode, PolicyFeature
):
    source = copy.deepcopy(spec["smolvla_config"])
    source["input_features"] = {
        key: PolicyFeature(
            type=FeatureType[value["type"]], shape=tuple(value["shape"])
        )
        for key, value in source["input_features"].items()
    }
    source["output_features"] = {
        key: PolicyFeature(
            type=FeatureType[value["type"]], shape=tuple(value["shape"])
        )
        for key, value in source["output_features"].items()
    }
    source["normalization_mapping"] = {
        key: NormalizationMode[value]
        for key, value in source["normalization_mapping"].items()
    }
    source["resize_imgs_with_padding"] = tuple(
        source["resize_imgs_with_padding"]
    )
    source.update(
        {
            "optimizer_lr": spec["campaign"]["learning_rate"],
            "optimizer_betas": tuple(spec["campaign"]["betas"]),
            "optimizer_eps": spec["campaign"]["epsilon"],
            "optimizer_weight_decay": spec["campaign"]["weight_decay"],
            "optimizer_grad_clip_norm": spec["campaign"][
                "gradient_clip_norm"
            ],
            "scheduler_warmup_steps": 0,
        }
    )
    return SmolVLAConfig(**source)


def _runtime_smoke(policy, processed, torch):
    parameter_inventory = _aggregate_inventory(policy.parameters())
    buffer_inventory = _aggregate_inventory(policy.buffers())
    trainable_rows = [
        {
            "name": name,
            "device": str(parameter.device),
            "dtype": str(parameter.dtype),
            "numel": parameter.numel(),
        }
        for name, parameter in policy.named_parameters()
        if parameter.requires_grad
    ]
    trainable = [
        parameter for parameter in policy.parameters() if parameter.requires_grad
    ]
    if not trainable:
        raise ValueError("T20.36h SmolVLA has no trainable parameters")
    policy.train()
    policy.zero_grad(set_to_none=True)
    _seed_all(SMOKE_SEED, torch)
    loss, _ = policy(processed)
    if not torch.isfinite(loss):
        raise ValueError("T20.36h runtime smoke loss is non-finite")
    loss.backward()
    gradients = [
        parameter.grad for parameter in trainable if parameter.grad is not None
    ]
    if not gradients or not all(
        torch.isfinite(gradient).all().item() for gradient in gradients
    ):
        raise ValueError("T20.36h runtime smoke gradients are missing or non-finite")
    squared = torch.zeros((), device="mps", dtype=torch.float32)
    for gradient in gradients:
        squared = squared + gradient.detach().float().pow(2).sum()
    gradient_norm = squared.sqrt()
    torch.mps.synchronize()
    smoke = {
        "processed_action_shape": list(processed["action"].shape),
        "processed_state_shape": list(processed["observation.state"].shape),
        "processed_image_keys": sorted(
            key for key in processed if key.startswith("observation.images.")
        ),
        "parameter_inventory": parameter_inventory,
        "buffer_inventory": buffer_inventory,
        "trainable_parameter_inventory": trainable_rows,
        "smoke_loss": float(loss.detach().cpu()),
        "smoke_gradient_norm": float(gradient_norm.detach().cpu()),
        "mps_forward_backward_passed": True,
        "cpu_fallback_observed": False,
    }
    policy.zero_grad(set_to_none=True)
    return smoke, trainable


def _aggregate_inventory(values):
    counts = defaultdict(int)
    for value in values:
        counts[(str(value.device), str(value.dtype))] += value.numel()
    return [
        {"device": device, "dtype": dtype, "numel": numel}
        for (device, dtype), numel in sorted(counts.items())
    ]


def _objective_by_seed(policy, processed, torch):
    policy.eval()
    values = []
    with torch.no_grad():
        for seed in OBJECTIVE_SEEDS:
            generator = torch.Generator(device="cpu").manual_seed(seed)
            noise = torch.randn(
                (1, 50, 32), generator=generator, dtype=torch.float32
            ).to("mps")
            uniform = torch.rand((1,), generator=generator, dtype=torch.float32)
            time = (uniform.pow(2.0 / 3.0) * 0.999 + 0.001).to("mps")
            loss, _ = policy(processed, noise=noise, time=time)
            if not torch.isfinite(loss):
                raise ValueError("T20.36h non-finite scheduled objective")
            values.append(float(loss.detach().cpu()))
    return values


def _evaluation(
    policy,
    preprocessor,
    postprocessor,
    raw_batch,
    target,
    torch,
    *,
    update,
    objective_values,
    baseline,
):
    observation = {
        key: copy.deepcopy(value)
        for key, value in raw_batch.items()
        if key.startswith("observation.") or key == "task"
    }
    processed_observation = preprocessor(observation)
    rows = []
    for index, seed in enumerate(INFERENCE_SEEDS):
        first = _decode(
            policy, postprocessor, processed_observation, torch, seed=seed
        )
        second = _decode(
            policy, postprocessor, processed_observation, torch, seed=seed
        )
        first_physical = np.asarray(
            [lerobot_to_mujoco(row.tolist()) for row in first],
            dtype=np.float64,
        )
        second_physical = np.asarray(
            [lerobot_to_mujoco(row.tolist()) for row in second],
            dtype=np.float64,
        )
        error = np.abs(first_physical - target)
        rows.append(
            {
                "seed_index": index,
                "inference_seed": seed,
                "first_action_chunk_sha256": hashlib.sha256(
                    canonical_json_bytes(first_physical.astype(float).tolist())
                ).hexdigest(),
                "second_action_chunk_sha256": hashlib.sha256(
                    canonical_json_bytes(second_physical.astype(float).tolist())
                ).hexdigest(),
                "repeat_maximum_absolute_difference_rad": float(
                    np.max(np.abs(first_physical - second_physical))
                ),
                "mean_absolute_error_rad": float(np.mean(error)),
                "maximum_absolute_error_rad": float(np.max(error)),
            }
        )
    return build_evaluation_row(
        optimizer_update_count=update,
        supervised_objective_by_seed=objective_values,
        baseline_objective_mean=baseline,
        inference_rows=rows,
    )


def _decode(policy, postprocessor, observation, torch, *, seed):
    generator = torch.Generator(device="cpu").manual_seed(seed)
    noise = torch.randn(
        (1, 50, 32), generator=generator, dtype=torch.float32
    ).to("mps")
    policy.reset()
    with torch.no_grad():
        chunk = policy.predict_action_chunk(observation, noise=noise)
        canonical = postprocessor(chunk)
    values = canonical.detach().cpu().float().numpy()
    if values.shape != (1, 50, 6):
        raise ValueError(f"T20.36h decoded action shape drifted: {values.shape}")
    return values[0].astype(np.float64)


def _require_remote_preservation(permit) -> None:
    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36h run is on the wrong branch")
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
        raise ValueError("T20.36h current source is not remotely preserved")
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


def _file_tree(root: Path):
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    return rows


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


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
