#!/usr/bin/env python3
"""Run or verify the one-use T20.36o bounded X bridge optimizer."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import importlib.metadata
import os
import random
import subprocess
import sys

from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.authority_composer import (  # noqa: E402
    verify_authority_decision,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco  # noqa: E402
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    ADAPTATION_MODE,
    PALIGEMMA_PREFIX,
    TRAINABLE_PREFIXES,
    verify_parameter_boundary,
    verify_tensor_manifest,
)
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    ACTIVE_ACTION_DIMENSIONS,
    MAXIMUM_ACTION_DIMENSIONS,
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
    build_attempt_marker,
    build_production_authority,
    load_verified_sources,
    require_active_authority,
    verify_attempt_marker,
    verify_owner_grant,
    verify_runtime_preflight,
    verify_training_permit,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_run import (  # noqa: E402
    PROBE_TENSOR_PATH,
    build_failure_result,
    build_probe_artifact,
    build_result,
    verify_probe_artifact,
    verify_result,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_spec import (  # noqa: E402
    materialize_correction_examples,
)
from scripts.robot_lab.run_t20_35d_residual_localization import (  # noqa: E402
    _file_tree,
)
from scripts.robot_lab.run_t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    CHECKPOINT_CONFIG_PATH as SOURCE_CHECKPOINT_CONFIG_PATH,
    CHECKPOINT_MODEL_PATH as SOURCE_CHECKPOINT_MODEL_PATH,
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
    _verify_output_checkpoint_config as _verify_source_checkpoint_config,
)
from scripts.robot_lab.run_t20_36o_baseline_capture import (  # noqa: E402
    load_t20_36o_batches,
    snapshot_file_tree,
)


CHECKPOINT_CONFIG_PATH = CHECKPOINT_ROOT / "bounded_optimizer_config.json"
CHECKPOINT_MODEL_PATH = CHECKPOINT_ROOT / "bounded_optimizer_model.safetensors"
CHECKPOINT_SCHEMA_VERSION = "scenesmith.t20_36o_bounded_optimizer_checkpoint.v1"
PROBE_UPDATE_COUNTS = (500, 1000, 1500, 2000, 2500)
INFERENCE_SEEDS = (20260721, 20260722, 20260723, 20260724, 20260725)
CHUNK_START_FRAMES = (0, 50, 100, 150, 200)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-retained", action="store_true")
    args = parser.parse_args()
    if sum((args.preflight, args.verify, args.verify_retained)) > 1:
        raise ValueError("T20.36o choose one runner mode")
    if args.verify_retained:
        return _verify_retained_outputs()

    contracts = _load_archived_contracts()
    if not args.verify:
        active = require_active_authority(repo_root=REPO_ROOT)
        if active["decision"] != contracts["decision"]:
            raise ValueError("T20.36o active optimizer authority drifted")
    _verify_runtime_environment(contracts=contracts)
    if args.verify:
        return _verify_outputs(contracts=contracts)

    _require_clean_output_boundary()
    _require_remote_preservation(contracts["permit"])
    batch_source = load_t20_36o_batches(
        sources=contracts["sources"]["optimizer_sources"]
    )
    _verify_snapshot(batch_source=batch_source, preflight=contracts["preflight"])
    correction_examples = materialize_correction_examples(
        spec=contracts["spec"],
        sources=contracts["sources"]["optimizer_sources"],
    )
    if len(correction_examples) != contracts["permit"]["correction_example_count"]:
        raise ValueError("T20.36o materialized correction coverage drifted")
    if args.preflight:
        print(
            contracts["permit"]["identity_sha256"],
            contracts["spec"]["identity_sha256"],
            flush=True,
        )
        return 0

    current_commit = _git("rev-parse", "HEAD")
    attempt = build_attempt_marker(
        permit=contracts["permit"],
        source_commit=current_commit,
    )
    (REPO_ROOT / RUN_ROOT).mkdir(parents=True, exist_ok=False)
    dump_canonical_json(REPO_ROOT / ATTEMPT_PATH, attempt)
    dump_canonical_json(REPO_ROOT / TRACKED_ATTEMPT_PATH, attempt)
    verify_attempt_marker(attempt, permit=contracts["permit"])
    state = {
        "stage": "checkpoint_tensor_read",
        "checkpoint_tensor_read": False,
        "model_constructed": False,
        "model_loaded": False,
        "optimizer_created": False,
        "optimizer_update_count": 0,
    }
    try:
        result = _execute(
            contracts=contracts,
            attempt=attempt,
            batch_source=batch_source,
            correction_examples=correction_examples,
            state=state,
        )
    except Exception as error:
        failure = build_failure_result(
            permit=contracts["permit"],
            attempt=attempt,
            failure_stage=state["stage"],
            error_type=type(error).__name__,
            error_message=(str(error) or repr(error))[:2000],
            checkpoint_tensor_read=state["checkpoint_tensor_read"],
            model_constructed=state["model_constructed"],
            model_loaded=state["model_loaded"],
            optimizer_created=state["optimizer_created"],
            optimizer_update_count=state["optimizer_update_count"],
        )
        dump_canonical_json(REPO_ROOT / FAILURE_RESULT_PATH, failure)
        print(failure["identity_sha256"], failure["decision"], flush=True)
        raise
    print(result["identity_sha256"], result["decision"], flush=True)
    return 0


def _execute(
    *,
    contracts: dict[str, Any],
    attempt: dict[str, Any],
    batch_source: dict[str, Any],
    correction_examples: list[dict[str, Any]],
    state: dict[str, Any],
) -> dict[str, Any]:
    import torch

    from lerobot.policies import make_policy, make_pre_post_processors
    from lerobot.utils.constants import (
        OBS_LANGUAGE_ATTENTION_MASK,
        OBS_LANGUAGE_TOKENS,
    )
    from safetensors.torch import load_file, save_file

    sources = contracts["sources"]
    spec = contracts["spec"]
    permit = contracts["permit"]
    schedule = spec["correction_schedule"]
    source_run = sources["x_runtime"]["source_run"]
    source_checkpoint_config = _verify_source_checkpoint_config(
        load_strict_json(SOURCE_CHECKPOINT_CONFIG_PATH),
        summary=source_run,
    )
    state["checkpoint_tensor_read"] = True
    checkpoint = load_file(SOURCE_CHECKPOINT_MODEL_PATH, device="cpu")
    if sorted(checkpoint) != sorted(
        source_checkpoint_config["trainable_parameter_names"]
    ):
        raise ValueError("T20.36o source checkpoint key set drifted")
    for row in source_checkpoint_config["trainable_tensor_manifest"]:
        tensor = checkpoint[row["name"]]
        if (
            list(tensor.shape) != row["shape"]
            or str(tensor.dtype) != row["dtype"]
            or tensor.numel() != row["numel"]
            or not torch.isfinite(tensor).all().item()
        ):
            raise ValueError("T20.36o source checkpoint tensor drifted")

    config = batch_source["config"]
    config.pretrained_path = str(batch_source["snapshot"])
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.gradient_checkpointing = True
    config.compile_model = False
    config.n_action_steps = 50
    config.num_inference_steps = 10
    config.train_expert_only = True
    config.freeze_vision_encoder = True
    construction_seed = permit["construction_seed"]
    torch.manual_seed(construction_seed)
    np.random.seed(construction_seed)
    random.seed(construction_seed)
    state["stage"] = "model_construction"
    state["model_constructed"] = True
    policy = make_policy(config, ds_meta=batch_source["dataset"].meta).to("mps")
    if hasattr(policy, "peft_config") or "Peft" in type(policy).__name__:
        raise ValueError("T20.36o unexpectedly constructed a PEFT policy")
    all_named = list(policy.named_parameters())
    all_names = [name for name, _ in all_named]
    trainable_named = [
        (name, parameter) for name, parameter in all_named if parameter.requires_grad
    ]
    trainable_names = [name for name, _ in trainable_named]
    verify_parameter_boundary(
        all_parameter_names=all_names,
        trainable_parameter_names=trainable_names,
    )
    if (
        trainable_names != source_checkpoint_config["trainable_parameter_names"]
        or any(
            parameter.requires_grad
            for name, parameter in all_named
            if name.startswith(PALIGEMMA_PREFIX)
        )
    ):
        raise ValueError("T20.36o trainable parameter boundary drifted")
    for name, parameter in trainable_named:
        parameter.data.copy_(checkpoint[name].to(device="mps"))
    del checkpoint
    gc.collect()
    state["model_loaded"] = True

    trainable = [parameter for _, parameter in trainable_named]
    trainable_manifest = [
        {
            "name": name,
            "shape": list(parameter.shape),
            "dtype": str(parameter.dtype),
            "numel": parameter.numel(),
        }
        for name, parameter in trainable_named
    ]
    trainable_count = verify_tensor_manifest(
        trainable_manifest,
        trainable_parameter_names=trainable_names,
    )
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=batch_source["snapshot"],
        dataset_stats=batch_source["dataset"].meta.stats,
        preprocessor_overrides={
            "device_processor": {"device": "mps"},
            "normalizer_processor": {
                "stats": batch_source["dataset"].meta.stats,
                "features": {
                    **policy.config.input_features,
                    **policy.config.output_features,
                },
                "norm_map": policy.config.normalization_mapping,
            },
        },
        postprocessor_overrides={
            "unnormalizer_processor": {
                "stats": batch_source["dataset"].meta.stats,
                "features": policy.config.output_features,
                "norm_map": policy.config.normalization_mapping,
            }
        },
    )
    contexts = _prepare_contexts(
        policy=policy,
        preprocessor=preprocessor,
        batch_source=batch_source,
        spec=spec,
        torch=torch,
        language_token_key=OBS_LANGUAGE_TOKENS,
        language_mask_key=OBS_LANGUAGE_ATTENTION_MASK,
    )
    prepared_examples = _prepare_examples(
        examples=correction_examples,
        contexts=contexts,
        bridge_spec=sources["optimizer_sources"]["bridge_spec"],
        coefficients=schedule["physical_joint_weighting"][
            "coefficient_by_dimension"
        ],
        torch=torch,
    )

    state["stage"] = "optimizer_creation"
    optimizer = torch.optim.AdamW(
        trainable,
        lr=schedule["learning_rate"],
        betas=tuple(schedule["betas"]),
        eps=schedule["epsilon"],
        weight_decay=schedule["weight_decay"],
        amsgrad=schedule["amsgrad"],
    )
    state["optimizer_created"] = True
    metrics = {
        "per_update_objective": [],
        "per_update_correction_objective": [],
        "per_update_standard_replay_objective": [],
        "gradient_norms_before_clip": [],
    }
    raw_probes = []
    policy.train()
    state["stage"] = "optimizer_training"
    for update_index, example_index in enumerate(
        permit["sample_index_by_update"], start=1
    ):
        optimizer.zero_grad(set_to_none=True)
        correction_loss = _correction_loss(
            policy=policy,
            example=prepared_examples[example_index],
            torch=torch,
        )
        correction_loss.backward()
        torch.manual_seed(permit["standard_replay_seed_by_update"][update_index - 1])
        standard_loss, _ = policy(contexts[0]["training_batch"])
        if not torch.isfinite(standard_loss):
            raise ValueError(
                f"T20.36o non-finite standard replay at update {update_index}"
            )
        standard_loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in trainable
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.36o non-finite gradient at update {update_index}")
        gradient_norm = torch.nn.utils.clip_grad_norm_(
            trainable,
            schedule["gradient_clip_norm"],
        )
        if not torch.isfinite(gradient_norm):
            raise ValueError(
                f"T20.36o non-finite gradient norm at update {update_index}"
            )
        optimizer.step()
        torch.mps.synchronize()
        correction_value = float(correction_loss.detach().cpu())
        standard_value = float(standard_loss.detach().cpu())
        metrics["per_update_correction_objective"].append(correction_value)
        metrics["per_update_standard_replay_objective"].append(standard_value)
        metrics["per_update_objective"].append(correction_value + standard_value)
        metrics["gradient_norms_before_clip"].append(
            float(gradient_norm.detach().cpu())
        )
        state["optimizer_update_count"] = update_index
        if update_index % 25 == 0:
            print(update_index, metrics["per_update_objective"][-1], flush=True)
        if update_index not in PROBE_UPDATE_COUNTS:
            continue
        state["stage"] = f"probe_{update_index}"
        source_mean = _source_objective_mean(
            policy=policy,
            batch=contexts[0]["training_batch"],
            torch=torch,
        )
        probe = {
            "update_count": update_index,
            "source_objective_mean": source_mean,
            "source_objective_ratio": source_mean
            / sources["optimizer_sources"]["source_spec"][
                "source_gate_baseline_objective_mean"
            ],
            "rows": _decoded_probe_rows(
                policy=policy,
                postprocessor=postprocessor,
                contexts=contexts,
                source_spec=sources["optimizer_sources"]["source_spec"],
                torch=torch,
            ),
        }
        raw_probes.append(probe)
        passed = _probe_passed(
            probe=probe,
            bridge_spec=sources["optimizer_sources"]["bridge_spec"],
        )
        print(update_index, "bridge_pass" if passed else "bridge_fail", flush=True)
        if passed:
            break
        policy.train()
        state["stage"] = "optimizer_training"

    update_count = state["optimizer_update_count"]
    metrics["optimizer_update_count"] = update_count
    baseline = sources["optimizer_sources"]["source_spec"][
        "source_gate_baseline_objective_mean"
    ]
    probe_artifact = build_probe_artifact(
        attempt=attempt,
        permit=permit,
        optimizer_spec=spec,
        bridge_spec=sources["optimizer_sources"]["bridge_spec"],
        source_gate_baseline_objective_mean=baseline,
        probes=raw_probes,
    )
    dump_canonical_json(REPO_ROOT / PROBE_TENSOR_PATH, probe_artifact)
    verify_probe_artifact(
        probe_artifact,
        attempt=attempt,
        permit=permit,
        optimizer_spec=spec,
        bridge_spec=sources["optimizer_sources"]["bridge_spec"],
        source_gate_baseline_objective_mean=baseline,
    )

    state["stage"] = "checkpoint_write"
    (REPO_ROOT / CHECKPOINT_ROOT).mkdir(parents=True, exist_ok=False)
    checkpoint_config = _build_checkpoint_config(
        contracts=contracts,
        attempt=attempt,
        probe_artifact=probe_artifact,
        trainable_names=trainable_names,
        trainable_manifest=trainable_manifest,
        trainable_count=trainable_count,
    )
    dump_canonical_json(REPO_ROOT / CHECKPOINT_CONFIG_PATH, checkpoint_config)
    save_file(
        {
            name: parameter.detach().cpu().contiguous()
            for name, parameter in trainable_named
        },
        REPO_ROOT / CHECKPOINT_MODEL_PATH,
    )
    _verify_checkpoint_config(
        checkpoint_config,
        contracts=contracts,
        attempt=attempt,
        probe_artifact=probe_artifact,
    )
    checkpoint_tree = _file_tree(REPO_ROOT / CHECKPOINT_ROOT)
    source_unchanged = (
        _file_tree(SOURCE_CHECKPOINT_ROOT)
        == sources["x_runtime"]["checkpoint_tree"]
    )
    state["stage"] = "result_write"
    result = build_result(
        attempt=attempt,
        permit=permit,
        optimizer_spec=spec,
        probe_artifact=probe_artifact,
        training_metrics=metrics,
        checkpoint_tree=checkpoint_tree,
        source_checkpoint_tree_unchanged=source_unchanged,
    )
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    verify_result(
        result,
        attempt=attempt,
        permit=permit,
        optimizer_spec=spec,
        probe_artifact=probe_artifact,
    )
    return result


def _prepare_contexts(
    *,
    policy,
    preprocessor,
    batch_source: dict[str, Any],
    spec: dict[str, Any],
    torch,
    language_token_key: str,
    language_mask_key: str,
) -> dict[int, dict[str, Any]]:
    expected_targets = {
        row["start_frame"]: row["normalized_padded_target_sha256"]
        for row in spec["target_normalization"]["targets"]
    }
    contexts = {}
    policy.eval()
    for batch_row in batch_source["batches"]:
        raw_batch = batch_row["raw_batch"]
        for key in batch_source["dataset"].meta.camera_keys:
            if raw_batch[key].dtype == torch.uint8:
                raw_batch[key] = raw_batch[key].float().div(255.0)
        training_batch = preprocessor(copy.deepcopy(raw_batch))
        actions = policy.prepare_action(training_batch)
        normalized = actions[0].detach().cpu().float().numpy().astype(float).tolist()
        observed_hash = hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()
        if observed_hash != expected_targets[batch_row["start_frame"]]:
            raise ValueError("T20.36o normalized target parity drifted")
        images, image_masks = policy._preprocess_images(training_batch)  # noqa: SLF001
        observation = {
            key: copy.deepcopy(value)
            for key, value in raw_batch.items()
            if key != "action" and not key.startswith("action_")
        }
        contexts[batch_row["start_frame"]] = {
            "start_frame": batch_row["start_frame"],
            "executed_length": batch_row["executed_length"],
            "training_batch": training_batch,
            "processed_observation": preprocessor(observation),
            "images": images,
            "image_masks": image_masks,
            "tokens": training_batch[language_token_key],
            "token_masks": training_batch[language_mask_key],
            "actions": actions,
        }
    if tuple(contexts) != CHUNK_START_FRAMES:
        raise ValueError("T20.36o prepared context order drifted")
    return contexts


def _prepare_examples(
    *,
    examples: list[dict[str, Any]],
    contexts: dict[int, dict[str, Any]],
    bridge_spec: dict[str, Any],
    coefficients: list[float],
    torch,
) -> list[dict[str, Any]]:
    coefficient_tensor = torch.tensor(
        coefficients,
        dtype=torch.float32,
        device="mps",
    ).view(1, 1, MAXIMUM_ACTION_DIMENSIONS)
    windows = {row["start_frame"]: row for row in bridge_spec["source_windows"]}
    output = []
    for expected_index, example in enumerate(examples):
        if example["correction_example_index"] != expected_index:
            raise ValueError("T20.36o correction example index drifted")
        start = example["start_frame"]
        context = contexts[start]
        window = windows[start]
        mask = torch.tensor(
            window["executed_mask"],
            dtype=torch.float32,
            device="mps",
        ).view(1, 50, 1)
        output.append(
            {
                "context": context,
                "noise": torch.tensor(
                    example["derived_noise"],
                    dtype=torch.float32,
                    device="mps",
                ).unsqueeze(0),
                "time": torch.tensor(
                    [example["time"]],
                    dtype=torch.float32,
                    device="mps",
                ),
                "mask": mask,
                "coefficient_tensor": coefficient_tensor,
                "normalizer": float(
                    window["executed_length"] * MAXIMUM_ACTION_DIMENSIONS
                ),
                "time_weight": float(example["time_normalization_weight"]),
            }
        )
    return output


def _correction_loss(*, policy, example: dict[str, Any], torch):
    context = example["context"]
    losses = policy.model.forward(
        context["images"],
        context["image_masks"],
        context["tokens"],
        context["token_masks"],
        context["actions"],
        example["noise"],
        example["time"],
    )
    if list(losses.shape) != [1, 50, MAXIMUM_ACTION_DIMENSIONS]:
        raise ValueError("T20.36o correction loss shape drifted")
    loss = (
        losses * example["coefficient_tensor"] * example["mask"]
    ).sum() / example["normalizer"]
    loss = loss * example["time_weight"]
    if not torch.isfinite(loss):
        raise ValueError("T20.36o correction objective is non-finite")
    return loss


def _source_objective_mean(*, policy, batch, torch) -> float:
    values = []
    policy.eval()
    with torch.no_grad():
        for seed in INFERENCE_SEEDS:
            torch.manual_seed(seed)
            loss, _ = policy(batch)
            if not torch.isfinite(loss):
                raise ValueError("T20.36o source objective is non-finite")
            values.append(float(loss.detach().cpu()))
    return sum(values) / len(values)


def _decoded_probe_rows(
    *,
    policy,
    postprocessor,
    contexts: dict[int, dict[str, Any]],
    source_spec: dict[str, Any],
    torch,
) -> list[dict[str, Any]]:
    evaluation = source_spec["evaluation"]
    if (
        evaluation["inference_seeds"] != list(INFERENCE_SEEDS)
        or len(evaluation["base_noise_sha256_by_seed"]) != len(INFERENCE_SEEDS)
        or evaluation["num_inference_steps"] != 10
    ):
        raise ValueError("T20.36o probe noise contract drifted")
    rows = []
    policy.eval()
    with torch.no_grad():
        for start_index, start in enumerate(CHUNK_START_FRAMES):
            context = contexts[start]
            for seed_index, seed in enumerate(INFERENCE_SEEDS):
                for repeat_index in range(2):
                    matrix = _decode_action_chunk(
                        policy=policy,
                        postprocessor=postprocessor,
                        processed_observation=context["processed_observation"],
                        seed=seed,
                        expected_noise_hash=evaluation[
                            "base_noise_sha256_by_seed"
                        ][seed_index],
                        torch=torch,
                    )
                    rows.append(
                        {
                            "start_index": start_index,
                            "start_frame": start,
                            "executed_length": context["executed_length"],
                            "seed_index": seed_index,
                            "inference_seed": seed,
                            "repeat_index": repeat_index,
                            "decoded_action_chunk": matrix,
                        }
                    )
    return rows


def _decode_action_chunk(
    *,
    policy,
    postprocessor,
    processed_observation,
    seed: int,
    expected_noise_hash: str,
    torch,
) -> list[list[float]]:
    torch.manual_seed(seed)
    policy.reset()
    noise_shape = (
        1,
        policy.model.config.chunk_size,
        policy.model.config.max_action_dim,
    )
    mask = torch.tensor(
        [0.0] * ACTIVE_ACTION_DIMENSIONS
        + [1.0] * (MAXIMUM_ACTION_DIMENSIONS - ACTIVE_ACTION_DIMENSIONS),
        dtype=torch.float32,
        device="mps",
    ).view(1, 1, MAXIMUM_ACTION_DIMENSIONS)
    base_noise = policy.model.sample_noise(noise_shape, "mps")
    base_values = base_noise.detach().cpu().float().numpy().astype(float).tolist()
    if hashlib.sha256(canonical_json_bytes(base_values)).hexdigest() != (
        expected_noise_hash
    ):
        raise ValueError("T20.36o probe base noise failed exact reproduction")
    actions = policy.predict_action_chunk(
        processed_observation,
        noise=base_noise * mask,
    )
    decoded = []
    for action in actions[0]:
        canonical = postprocessor(action.unsqueeze(0))
        values = canonical.detach().cpu().float().numpy().reshape(-1)
        decoded.append(lerobot_to_mujoco(values.tolist()))
    matrix = np.asarray(decoded, dtype=np.float64)
    if matrix.shape != (50, ACTIVE_ACTION_DIMENSIONS) or not np.isfinite(matrix).all():
        raise ValueError("T20.36o decoded probe tensor drifted")
    return matrix.astype(float).tolist()


def _probe_passed(*, probe: dict[str, Any], bridge_spec: dict[str, Any]) -> bool:
    from scenesmith.robot_lab.t20_36o_baseline_capture import score_action_tensor

    if probe["source_objective_ratio"] > bridge_spec["acceptance"][
        "maximum_source_batch_objective_ratio"
    ]:
        return False
    windows = {row["start_frame"]: row for row in bridge_spec["source_windows"]}
    thresholds = bridge_spec["acceptance"]["phase_joint_maximum_error_rad"]
    for row in probe["rows"]:
        if row["repeat_index"] != 0:
            continue
        window = windows[row["start_frame"]]
        score = score_action_tensor(
            tensor=row["decoded_action_chunk"],
            target=window["padded_target_action_mujoco_rad"],
            executed_mask=window["executed_mask"],
            thresholds=thresholds,
        )
        if not score["passed"]:
            return False
    return True


def _build_checkpoint_config(
    *,
    contracts: dict[str, Any],
    attempt: dict[str, Any],
    probe_artifact: dict[str, Any],
    trainable_names: list[str],
    trainable_manifest: list[dict[str, Any]],
    trainable_count: int,
) -> dict[str, Any]:
    return sign_payload(
        {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "task_id": "T20.36o",
            "optimizer_spec_identity_sha256": contracts["spec"]["identity_sha256"],
            "training_permit_identity_sha256": contracts["permit"][
                "identity_sha256"
            ],
            "authority_decision_identity_sha256": contracts["decision"][
                "identity_sha256"
            ],
            "runtime_preflight_identity_sha256": contracts["preflight"][
                "identity_sha256"
            ],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "probe_artifact_identity_sha256": probe_artifact["identity_sha256"],
            "source_checkpoint_identity_sha256": contracts["permit"][
                "source_checkpoint_identity_sha256"
            ],
            "selected_update_count": (
                probe_artifact["first_passing_update"]
                if probe_artifact["first_passing_update"] is not None
                else 2500
            ),
            "bridge_gate_passed": probe_artifact["first_passing_update"] is not None,
            "base_model_revision": contracts["permit"]["snapshot_revision"],
            "adaptation_mode": ADAPTATION_MODE,
            "peft_wrapper_used": False,
            "train_expert_only": True,
            "freeze_vision_encoder": True,
            "trainable_prefixes": list(TRAINABLE_PREFIXES),
            "trainable_parameter_names": trainable_names,
            "trainable_parameter_names_sha256": hashlib.sha256(
                canonical_json_bytes(trainable_names)
            ).hexdigest(),
            "trainable_tensor_manifest": trainable_manifest,
            "trainable_parameter_count": trainable_count,
            "paligemma_trainable_parameter_count": 0,
            "retry_authorized": False,
            "gate_c_authorized": False,
        }
    )


def _verify_checkpoint_config(
    payload: dict[str, Any],
    *,
    contracts: dict[str, Any],
    attempt: dict[str, Any],
    probe_artifact: dict[str, Any],
) -> None:
    verify_signed_payload(payload, label="T20.36o bounded optimizer checkpoint")
    expected = _build_checkpoint_config(
        contracts=contracts,
        attempt=attempt,
        probe_artifact=probe_artifact,
        trainable_names=payload.get("trainable_parameter_names"),
        trainable_manifest=payload.get("trainable_tensor_manifest"),
        trainable_count=payload.get("trainable_parameter_count"),
    )
    if payload != expected or verify_tensor_manifest(
        payload.get("trainable_tensor_manifest"),
        trainable_parameter_names=payload.get("trainable_parameter_names"),
    ) != payload.get("trainable_parameter_count"):
        raise ValueError("T20.36o bounded optimizer checkpoint config drifted")


def _load_archived_contracts() -> dict[str, Any]:
    sources = load_verified_sources(repo_root=REPO_ROOT)
    owner = load_strict_json(REPO_ROOT / OWNER_GRANT_PATH)
    verify_owner_grant(owner, sources=sources, repo_root=REPO_ROOT)
    expected_request, expected_decision = build_production_authority(
        sources=sources,
        owner=owner,
        repo_root=REPO_ROOT,
    )
    request = load_strict_json(REPO_ROOT / REQUEST_PATH)
    decision = load_strict_json(REPO_ROOT / DECISION_PATH)
    verify_authority_decision(decision, request=request)
    if request != expected_request or decision != expected_decision:
        raise ValueError("T20.36o archived optimizer authority drifted")
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
        "sources": sources,
        "spec": sources["optimizer_spec"],
        "owner": owner,
        "request": request,
        "decision": decision,
        "preflight": preflight,
        "permit": permit,
    }


def _verify_runtime_environment(*, contracts: dict[str, Any]) -> None:
    if list(sys.version_info[:2]) != [3, 12]:
        raise RuntimeError("T20.36o requires the reviewed Python 3.12 runtime")
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    import torch

    dependencies = {
        package: importlib.metadata.version(package)
        for package in contracts["preflight"]["dependency_versions"]
    }
    if dependencies != contracts["preflight"]["dependency_versions"]:
        raise RuntimeError("T20.36o dependency versions drifted")
    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36o requires the authorized local MPS runtime")
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    if stack["identity_sha256"] != contracts["preflight"][
        "lerobot_stack_identity_sha256"
    ]:
        raise ValueError("T20.36o live LeRobot stack drifted")
    if _file_tree(SOURCE_CHECKPOINT_ROOT) != contracts["sources"]["x_runtime"][
        "checkpoint_tree"
    ]:
        raise ValueError("T20.36o source checkpoint tree drifted")


def _verify_snapshot(*, batch_source: dict[str, Any], preflight: dict[str, Any]) -> None:
    tree = snapshot_file_tree(batch_source["snapshot"])
    identity = hashlib.sha256(canonical_json_bytes(tree)).hexdigest()
    if (
        tree != preflight["snapshot_tree"]
        or identity != preflight["snapshot_tree_identity_sha256"]
        or batch_source["snapshot"].name != preflight["snapshot_revision"]
    ):
        raise ValueError("T20.36o base-model snapshot drifted")


def _require_clean_output_boundary() -> None:
    paths = (
        REPO_ROOT / RUN_ROOT,
        REPO_ROOT / TRACKED_ATTEMPT_PATH,
        REPO_ROOT / PROBE_TENSOR_PATH,
        REPO_ROOT / RESULT_PATH,
        REPO_ROOT / FAILURE_RESULT_PATH,
    )
    if any(path.exists() for path in paths):
        raise FileExistsError("T20.36o immutable optimizer output already exists")


def _require_remote_preservation(permit: dict[str, Any]) -> None:
    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36o optimizer is on the wrong branch")
    head = _git("rev-parse", "HEAD")
    remote = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "codex/pi05-autolearn-loop"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    if head != remote:
        raise ValueError("T20.36o optimizer source is not remotely preserved")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", permit["required_source_commit"], head],
        cwd=REPO_ROOT,
        check=True,
    )


def _verify_outputs(*, contracts: dict[str, Any]) -> int:
    result = _verify_retained(contracts=contracts)
    if _file_tree(REPO_ROOT / CHECKPOINT_ROOT) != result["checkpoint_tree"]:
        raise ValueError("T20.36o output checkpoint tree drifted")
    checkpoint_config = load_strict_json(REPO_ROOT / CHECKPOINT_CONFIG_PATH)
    attempt = load_strict_json(REPO_ROOT / TRACKED_ATTEMPT_PATH)
    probe_artifact = load_strict_json(REPO_ROOT / PROBE_TENSOR_PATH)
    _verify_checkpoint_config(
        checkpoint_config,
        contracts=contracts,
        attempt=attempt,
        probe_artifact=probe_artifact,
    )
    from safetensors import safe_open

    with safe_open(REPO_ROOT / CHECKPOINT_MODEL_PATH, framework="pt", device="cpu") as handle:
        if sorted(handle.keys()) != sorted(
            checkpoint_config["trainable_parameter_names"]
        ):
            raise ValueError("T20.36o checkpoint tensor names drifted")
    print(result["identity_sha256"], result["decision"], flush=True)
    return 0


def _verify_retained_outputs() -> int:
    contracts = _load_archived_contracts()
    result = _verify_retained(contracts=contracts)
    print(result["identity_sha256"], result["decision"], flush=True)
    return 0


def _verify_retained(*, contracts: dict[str, Any]) -> dict[str, Any]:
    attempt = load_strict_json(REPO_ROOT / TRACKED_ATTEMPT_PATH)
    verify_attempt_marker(attempt, permit=contracts["permit"])
    if (REPO_ROOT / FAILURE_RESULT_PATH).exists():
        failure = load_strict_json(REPO_ROOT / FAILURE_RESULT_PATH)
        verify_signed_payload(failure, label="T20.36o optimizer failure")
        raise RuntimeError("T20.36o bounded optimizer ended in a retained failure")
    probe_artifact = load_strict_json(REPO_ROOT / PROBE_TENSOR_PATH)
    baseline = contracts["sources"]["optimizer_sources"]["source_spec"][
        "source_gate_baseline_objective_mean"
    ]
    verify_probe_artifact(
        probe_artifact,
        attempt=attempt,
        permit=contracts["permit"],
        optimizer_spec=contracts["spec"],
        bridge_spec=contracts["sources"]["optimizer_sources"]["bridge_spec"],
        source_gate_baseline_objective_mean=baseline,
    )
    result = load_strict_json(REPO_ROOT / RESULT_PATH)
    verify_result(
        result,
        attempt=attempt,
        permit=contracts["permit"],
        optimizer_spec=contracts["spec"],
        probe_artifact=probe_artifact,
    )
    return result


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
