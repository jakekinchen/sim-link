#!/usr/bin/env python3
"""Run or verify the one authorized T20.35t time-normalized standard-replay correction."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import os
import random
import sys

from datetime import datetime
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco  # noqa: E402
from scenesmith.robot_lab.t20_17_clean_base_preflight import (  # noqa: E402
    DATASET_REPO_ID,
    DATASET_ROOT,
    EXPECTED_MODEL_REVISION,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (  # noqa: E402
    ACTION_HORIZON,
    FRAME_INDEX,
    INFERENCE_SEEDS,
)
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    ADAPTATION_MODE,
    PALIGEMMA_PREFIX,
    TRAINABLE_PREFIXES,
    verify_parameter_boundary,
    verify_tensor_manifest,
)
from scenesmith.robot_lab.t20_35j_initial_noise_scale_discriminator import (  # noqa: E402
    SAMPLER_SOURCE_PATH,
)
from scenesmith.robot_lab.t20_35t_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)
from scenesmith.robot_lab.t20_35t_time_normalized_standard_replay_correction import (  # noqa: E402
    ACTIVE_ACTION_DIMENSIONS,
    CORRECTION_EXAMPLE_COUNT,
    GRADIENT_CLIP_NORM,
    LEARNING_RATE,
    MAXIMUM_ACTION_DIMENSIONS,
    OPTIMIZER_UPDATES,
    RUN_SCHEMA_VERSION,
    SPEC_PATH,
    TRAINING_SEED,
    load_source_artifacts,
    materialize_correction_tensors,
    verify_run,
    verify_training_spec,
)
from scripts.robot_lab.run_t20_35p_terminal_time_flow_consistency_correction import (  # noqa: E402
    CHECKPOINT_CONFIG_PATH as SOURCE_CHECKPOINT_CONFIG_PATH,
    CHECKPOINT_MODEL_PATH as SOURCE_CHECKPOINT_MODEL_PATH,
    CHECKPOINT_ROOT as SOURCE_CHECKPOINT_ROOT,
    _verify_output_checkpoint_config as _verify_source_checkpoint_config,
)
from scripts.robot_lab.run_t20_35d_residual_localization import (  # noqa: E402
    _file_tree,
)


RUN_ROOT = REPO_ROOT / "outputs/robot_lab/t20_35t_time_normalized_standard_replay_run_001"
SUMMARY_PATH = RUN_ROOT / "run_summary.json"
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
CHECKPOINT_ROOT = RUN_ROOT / "checkpoint"
CHECKPOINT_CONFIG_PATH = CHECKPOINT_ROOT / "time_normalized_standard_replay_config.json"
CHECKPOINT_MODEL_PATH = CHECKPOINT_ROOT / "time_normalized_standard_replay_model.safetensors"
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_35t_time_normalized_standard_replay_attempt.v1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.verify and args.preflight:
        raise ValueError("T20.35t choose either --verify or --preflight")
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
        objective_mass_audit=sources["objective_mass_audit"],
    )
    if spec.get("required_python_major_minor") != [3, 12] or list(
        sys.version_info[:2]
    ) != [3, 12]:
        raise RuntimeError("T20.35t requires the reviewed Python 3.12 runtime")
    authority = require_active_authority(repo_root=REPO_ROOT)
    authority_identity = authority["decision"]["identity_sha256"]
    source_root = REPO_ROOT / SOURCE_CHECKPOINT_ROOT
    if _file_tree(source_root) != spec["source_checkpoint_tree"]:
        raise ValueError("T20.35t source checkpoint tree drifted")
    if hashlib.sha256(
        (REPO_ROOT / SAMPLER_SOURCE_PATH).read_bytes()
    ).hexdigest() != spec["sampler_source_sha256"]:
        raise ValueError("T20.35t sampler source drifted")
    if args.preflight:
        if RUN_ROOT.exists():
            raise FileExistsError("T20.35t run root already exists")
        print(spec["identity_sha256"], authority_identity)
        return 0
    if args.verify:
        attempt = load_strict_json(ATTEMPT_PATH)
        _verify_attempt(
            attempt,
            spec_identity=spec["identity_sha256"],
            authority_identity=authority_identity,
        )
        summary = load_strict_json(SUMMARY_PATH)
        verify_run(summary, spec=spec, authority_identity=authority_identity)
        if summary["attempt_identity_sha256"] != attempt["identity_sha256"]:
            raise ValueError("T20.35t summary drifted from consumed attempt")
        if _file_tree(CHECKPOINT_ROOT) != summary["checkpoint_tree"]:
            raise ValueError("T20.35t output checkpoint tree drifted")
        config = _verify_output_checkpoint_config(
            load_strict_json(CHECKPOINT_CONFIG_PATH), summary=summary
        )
        from safetensors import safe_open

        with safe_open(CHECKPOINT_MODEL_PATH, framework="pt", device="cpu") as handle:
            if sorted(handle.keys()) != sorted(config["trainable_parameter_names"]):
                raise ValueError("T20.35t output checkpoint tensor names drifted")
        print(summary["identity_sha256"])
        return 0
    if RUN_ROOT.exists():
        raise FileExistsError("T20.35t immutable run root already exists; use --verify")

    correction_tensors = materialize_correction_tensors(
        sources["trajectory_result"], sources["target_result"]
    )
    RUN_ROOT.mkdir(parents=True, exist_ok=False)
    attempt = sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": "T20.35t",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "started_at": datetime.now().astimezone().isoformat(),
            "one_run_permit_consumed": True,
            "source_checkpoint_tree_verified": True,
            "correction_examples_verified": True,
            "model_loaded_at_marker": False,
            "model_inference_at_marker": False,
            "optimizer_created_at_marker": False,
            "closed_loop_rollout": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )
    dump_canonical_json(ATTEMPT_PATH, attempt)

    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    if stack["identity_sha256"] != spec["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.35t live LeRobot stack drifted")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.utils.constants import (
        OBS_LANGUAGE_ATTENTION_MASK,
        OBS_LANGUAGE_TOKENS,
    )
    from lerobot.datasets import LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.datasets.factory import resolve_delta_timestamps
    from lerobot.policies import make_policy, make_pre_post_processors
    from safetensors.torch import load_file, save_file
    from torch.utils.data import default_collate

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.35t requires the authorized local MPS runtime")
    source_checkpoint_config = _verify_source_checkpoint_config(
        load_strict_json(REPO_ROOT / SOURCE_CHECKPOINT_CONFIG_PATH),
        summary=sources["source_run"],
    )
    checkpoint = load_file(REPO_ROOT / SOURCE_CHECKPOINT_MODEL_PATH, device="cpu")
    if sorted(checkpoint) != sorted(
        source_checkpoint_config["trainable_parameter_names"]
    ):
        raise ValueError("T20.35t source checkpoint key set drifted")
    for row in source_checkpoint_config["trainable_tensor_manifest"]:
        tensor = checkpoint[row["name"]]
        if (
            list(tensor.shape) != row["shape"]
            or str(tensor.dtype) != row["dtype"]
            or tensor.numel() != row["numel"]
            or not torch.isfinite(tensor).all().item()
        ):
            raise ValueError("T20.35t source checkpoint tensor drifted")

    snapshot = (
        Path.home()
        / ".cache/huggingface/hub/models--lerobot--pi05_base/snapshots"
        / EXPECTED_MODEL_REVISION
    ).resolve()
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.pretrained_path = str(snapshot)
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.gradient_checkpointing = True
    config.compile_model = False
    config.n_action_steps = ACTION_HORIZON
    config.num_inference_steps = spec["evaluation"]["num_inference_steps"]
    config.train_expert_only = True
    config.freeze_vision_encoder = True
    metadata = LeRobotDatasetMetadata(DATASET_REPO_ID, root=REPO_ROOT / DATASET_ROOT)
    dataset = LeRobotDataset(
        DATASET_REPO_ID,
        root=REPO_ROOT / DATASET_ROOT,
        episodes=[0],
        delta_timestamps=resolve_delta_timestamps(config, metadata),
        return_uint8=True,
    )
    raw_batch = default_collate([dataset[FRAME_INDEX]])
    target_lerobot = raw_batch["action"].detach().cpu().numpy()[0]
    if target_lerobot.shape != (ACTION_HORIZON, ACTIVE_ACTION_DIMENSIONS):
        raise ValueError("T20.35t fixed dataset target shape drifted")
    target_mujoco = np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in target_lerobot],
        dtype=np.float64,
    )
    if hashlib.sha256(
        canonical_json_bytes(target_mujoco.astype(float).tolist())
    ).hexdigest() != spec["dataset_action_chunk_sha256"]:
        raise ValueError("T20.35t fixed dataset target drifted")

    torch.manual_seed(TRAINING_SEED)
    np.random.seed(TRAINING_SEED)
    random.seed(TRAINING_SEED)
    policy = make_policy(config, ds_meta=dataset.meta).to("mps")
    if hasattr(policy, "peft_config") or "Peft" in type(policy).__name__:
        raise ValueError("T20.35t unexpectedly constructed a PEFT policy")
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
        all_names != sources["base_source_run"]["all_parameter_names"]
        or trainable_names != source_checkpoint_config["trainable_parameter_names"]
        or any(
            parameter.requires_grad
            for name, parameter in all_named
            if name.startswith(PALIGEMMA_PREFIX)
        )
    ):
        raise ValueError("T20.35t model parameter boundary drifted")
    for name, parameter in trainable_named:
        parameter.data.copy_(checkpoint[name].to(device="mps"))
    del checkpoint
    gc.collect()
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
        trainable_manifest, trainable_parameter_names=trainable_names
    )
    paligemma_count = sum(
        parameter.numel()
        for name, parameter in all_named
        if name.startswith(PALIGEMMA_PREFIX)
    )

    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=snapshot,
        dataset_stats=dataset.meta.stats,
        preprocessor_overrides={
            "device_processor": {"device": "mps"},
            "normalizer_processor": {
                "stats": dataset.meta.stats,
                "features": {
                    **policy.config.input_features,
                    **policy.config.output_features,
                },
                "norm_map": policy.config.normalization_mapping,
            },
        },
        postprocessor_overrides={
            "unnormalizer_processor": {
                "stats": dataset.meta.stats,
                "features": policy.config.output_features,
                "norm_map": policy.config.normalization_mapping,
            }
        },
    )
    for key in dataset.meta.camera_keys:
        if raw_batch[key].dtype == torch.uint8:
            raw_batch[key] = raw_batch[key].float().div(255.0)
    batch = preprocessor(copy.deepcopy(raw_batch))
    actions = policy.prepare_action(batch)
    normalized_target = (
        actions[0].detach().cpu().float().numpy().astype(float).tolist()
    )
    if hashlib.sha256(
        canonical_json_bytes(normalized_target)
    ).hexdigest() != spec["normalized_padded_target_sha256"]:
        raise ValueError("T20.35t live normalized target drifted")
    images, img_masks = policy._preprocess_images(batch)  # noqa: SLF001
    tokens = batch[OBS_LANGUAGE_TOKENS]
    masks = batch[OBS_LANGUAGE_ATTENTION_MASK]
    examples = [
        {
            "noise": torch.tensor(
                row["derived_noise"], dtype=torch.float32, device="mps"
            ).unsqueeze(0),
            "time": torch.tensor([row["time"]], dtype=torch.float32, device="mps"),
        }
        for row in correction_tensors
    ]
    if len(examples) != CORRECTION_EXAMPLE_COUNT:
        raise ValueError("T20.35t live correction example count drifted")

    baseline_by_example = _correction_objectives(
        policy, images, img_masks, tokens, masks, actions, examples, torch
    )
    baseline_standard_by_seed = _standard_objectives(policy, batch, torch)
    weights = spec["time_normalization"]["weight_by_step"]
    baseline_weighted_by_example = [
        value * weights[index % 10]
        for index, value in enumerate(baseline_by_example)
    ]
    optimizer = torch.optim.AdamW(
        trainable,
        lr=LEARNING_RATE,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
        amsgrad=False,
    )
    losses: list[float] = []
    raw_correction_losses: list[float] = []
    weighted_correction_losses: list[float] = []
    standard_replay_losses: list[float] = []
    gradients: list[float] = []
    sample_order = spec["campaign"]["sample_index_by_update"]
    policy.train()
    for update, example_index in enumerate(sample_order):
        optimizer.zero_grad(set_to_none=True)
        raw_loss = _correction_loss(
            policy,
            images,
            img_masks,
            tokens,
            masks,
            actions,
            examples[example_index],
            torch,
        )
        if not torch.isfinite(raw_loss):
            raise ValueError(f"T20.35t non-finite correction objective at update {update + 1}")
        weighted_loss = raw_loss * weights[example_index % 10]
        weighted_loss.backward()
        standard_seed = spec["campaign"]["standard_replay_seed_by_update"][update]
        torch.manual_seed(standard_seed)
        standard_loss, _ = policy(batch)
        if not torch.isfinite(standard_loss):
            raise ValueError(f"T20.35t non-finite standard replay at update {update + 1}")
        standard_loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in trainable
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.35t non-finite gradient at update {update + 1}")
        norm = torch.nn.utils.clip_grad_norm_(trainable, GRADIENT_CLIP_NORM)
        if not torch.isfinite(norm):
            raise ValueError(f"T20.35t non-finite gradient norm at update {update + 1}")
        optimizer.step()
        torch.mps.synchronize()
        raw_value = float(raw_loss.detach().cpu())
        weighted_value = float(weighted_loss.detach().cpu())
        standard_value = float(standard_loss.detach().cpu())
        raw_correction_losses.append(raw_value)
        weighted_correction_losses.append(weighted_value)
        standard_replay_losses.append(standard_value)
        losses.append(weighted_value + standard_value)
        gradients.append(float(norm.detach().cpu()))
        if (update + 1) % 25 == 0:
            print(update + 1, losses[-1], flush=True)
    final_by_example = _correction_objectives(
        policy, images, img_masks, tokens, masks, actions, examples, torch
    )
    final_standard_by_seed = _standard_objectives(policy, batch, torch)
    final_weighted_by_example = [
        value * weights[index % 10]
        for index, value in enumerate(final_by_example)
    ]
    decoded_chunks = _decoded_chunks(
        policy, preprocessor, postprocessor, raw_batch, target_mujoco, torch, spec
    )

    CHECKPOINT_ROOT.mkdir(parents=True, exist_ok=False)
    checkpoint_config = sign_payload(
        {
            "schema_version": "scenesmith.t20_35t_time_normalized_standard_replay_checkpoint.v1",
            "task_id": "T20.35t",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "source_checkpoint_identity_sha256": spec[
                "source_checkpoint_identity_sha256"
            ],
            "base_model_revision": EXPECTED_MODEL_REVISION,
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
        }
    )
    dump_canonical_json(CHECKPOINT_CONFIG_PATH, checkpoint_config)
    save_file(
        {
            name: parameter.detach().cpu().contiguous()
            for name, parameter in trainable_named
        },
        CHECKPOINT_MODEL_PATH,
    )
    output_tree = _file_tree(CHECKPOINT_ROOT)
    source_unchanged = _file_tree(source_root) == spec["source_checkpoint_tree"]
    summary = sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": "T20.35t",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "attempt_identity_sha256": attempt["identity_sha256"],
            "source_checkpoint_identity_sha256": spec[
                "source_checkpoint_identity_sha256"
            ],
            "source_checkpoint_tree_unchanged": source_unchanged,
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "learning_rate": LEARNING_RATE,
            "optimizer_config": {
                "optimizer": "AdamW",
                "betas": [0.9, 0.999],
                "epsilon": 1e-8,
                "weight_decay": 0.0,
                "amsgrad": False,
                "gradient_clip_norm": GRADIENT_CLIP_NORM,
            },
            "correction_example_count": CORRECTION_EXAMPLE_COUNT,
            "sample_index_by_update": sample_order,
            "example_use_count": [
                sample_order.count(index) for index in range(CORRECTION_EXAMPLE_COUNT)
            ],
            "time_normalization_weight_by_step": weights,
            "standard_replay_seed_by_update": spec["campaign"][
                "standard_replay_seed_by_update"
            ],
            "standard_replay_update_count": OPTIMIZER_UPDATES,
            "adaptation_mode": ADAPTATION_MODE,
            "trainable_prefixes": list(TRAINABLE_PREFIXES),
            "trainable_parameter_names_sha256": checkpoint_config[
                "trainable_parameter_names_sha256"
            ],
            "trainable_parameter_count": trainable_count,
            "paligemma_parameter_count": paligemma_count,
            "paligemma_trainable_parameter_count": 0,
            "baseline_correction_objective_mean": sum(baseline_by_example)
            / CORRECTION_EXAMPLE_COUNT,
            "final_correction_objective_mean": sum(final_by_example)
            / CORRECTION_EXAMPLE_COUNT,
            "baseline_objective_by_example": baseline_by_example,
            "final_objective_by_example": final_by_example,
            "baseline_weighted_correction_objective_mean": sum(
                baseline_weighted_by_example
            )
            / CORRECTION_EXAMPLE_COUNT,
            "final_weighted_correction_objective_mean": sum(
                final_weighted_by_example
            )
            / CORRECTION_EXAMPLE_COUNT,
            "baseline_weighted_objective_by_example": baseline_weighted_by_example,
            "final_weighted_objective_by_example": final_weighted_by_example,
            "baseline_standard_objective_mean": sum(baseline_standard_by_seed)
            / len(INFERENCE_SEEDS),
            "final_standard_objective_mean": sum(final_standard_by_seed)
            / len(INFERENCE_SEEDS),
            "baseline_standard_objective_by_seed": baseline_standard_by_seed,
            "final_standard_objective_by_seed": final_standard_by_seed,
            "per_update_objective": losses,
            "per_update_raw_correction_objective": raw_correction_losses,
            "per_update_weighted_correction_objective": weighted_correction_losses,
            "per_update_standard_replay_objective": standard_replay_losses,
            "gradient_norms_before_clip": gradients,
            "decoded_action_chunks": decoded_chunks,
            "checkpoint_tree": output_tree,
            "checkpoint_identity_sha256": hashlib.sha256(
                canonical_json_bytes(output_tree)
            ).hexdigest(),
            "optimizer_training": True,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "sampler_mutated": False,
            "closed_loop_rollout": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    dump_canonical_json(SUMMARY_PATH, summary)
    verify_run(summary, spec=spec, authority_identity=authority_identity)
    print(summary["identity_sha256"], flush=True)
    return 0


def _correction_loss(
    policy, images, img_masks, tokens, masks, actions, example, torch
):
    losses = policy.model.forward(
        images,
        img_masks,
        tokens,
        masks,
        actions,
        example["noise"],
        example["time"],
    )
    if list(losses.shape) != [1, ACTION_HORIZON, MAXIMUM_ACTION_DIMENSIONS]:
        raise ValueError("T20.35t live correction loss shape drifted")
    loss = losses[:, :, :ACTIVE_ACTION_DIMENSIONS].mean()
    if not torch.isfinite(loss):
        raise ValueError("T20.35t live correction loss is non-finite")
    return loss


def _correction_objectives(
    policy, images, img_masks, tokens, masks, actions, examples, torch
):
    values = []
    policy.eval()
    with torch.no_grad():
        for example in examples:
            values.append(
                float(
                    _correction_loss(
                        policy,
                        images,
                        img_masks,
                        tokens,
                        masks,
                        actions,
                        example,
                        torch,
                    )
                    .detach()
                    .cpu()
                )
            )
    return values


def _standard_objectives(policy, batch, torch):
    values = []
    policy.eval()
    with torch.no_grad():
        for seed in INFERENCE_SEEDS:
            torch.manual_seed(seed)
            loss, _ = policy(batch)
            if not torch.isfinite(loss):
                raise ValueError("T20.35t standard objective is non-finite")
            values.append(float(loss.detach().cpu()))
    return values


def _decoded_chunks(policy, preprocessor, postprocessor, raw_batch, target, torch, spec):
    observation = {
        key: copy.deepcopy(value)
        for key, value in raw_batch.items()
        if key != "action" and not key.startswith("action_")
    }
    processed = preprocessor(observation)
    mask = torch.tensor(
        [0.0] * ACTIVE_ACTION_DIMENSIONS
        + [1.0] * (MAXIMUM_ACTION_DIMENSIONS - ACTIVE_ACTION_DIMENSIONS),
        dtype=torch.float32,
        device="mps",
    ).view(1, 1, MAXIMUM_ACTION_DIMENSIONS)
    rows = []
    policy.eval()
    with torch.no_grad():
        for seed_index, seed in enumerate(INFERENCE_SEEDS):
            torch.manual_seed(seed)
            policy.reset()
            noise_shape = (
                1,
                policy.model.config.chunk_size,
                policy.model.config.max_action_dim,
            )
            base_noise = policy.model.sample_noise(noise_shape, "mps")
            base_noise_values = (
                base_noise.detach().cpu().float().numpy().astype(float).tolist()
            )
            if hashlib.sha256(
                canonical_json_bytes(base_noise_values)
            ).hexdigest() != spec["evaluation"]["base_noise_sha256_by_seed"][seed_index]:
                raise ValueError("T20.35t base noise failed exact reproduction")
            actions = policy.predict_action_chunk(processed, noise=base_noise * mask)
            decoded = []
            for action in actions[0]:
                canonical = postprocessor(action.unsqueeze(0))
                values = canonical.detach().cpu().float().numpy().reshape(-1)
                decoded.append(lerobot_to_mujoco(values.tolist()))
            matrix = np.asarray(decoded, dtype=np.float64)
            error = np.abs(matrix - target)
            rows.append(
                {
                    "inference_seed": seed,
                    "decoded_action_chunk_sha256": hashlib.sha256(
                        canonical_json_bytes(matrix.astype(float).tolist())
                    ).hexdigest(),
                    "mean_absolute_error_rad": float(np.mean(error)),
                    "maximum_absolute_error_rad": float(np.max(error)),
                }
            )
    return rows


def _verify_attempt(
    payload: dict, *, spec_identity: str, authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35t attempt")
    if (
        payload.get("schema_version") != ATTEMPT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.35t"
        or payload.get("training_spec_identity_sha256") != spec_identity
        or payload.get("authority_decision_identity_sha256") != authority_identity
        or payload.get("one_run_permit_consumed") is not True
        or payload.get("source_checkpoint_tree_verified") is not True
        or payload.get("correction_examples_verified") is not True
        or payload.get("model_loaded_at_marker") is not False
        or payload.get("model_inference_at_marker") is not False
        or payload.get("optimizer_created_at_marker") is not False
        or any(
            payload.get(field) is not False
            for field in (
                "closed_loop_rollout",
                "physical_actuation",
                "external_compute_started",
                "brev_compute_started",
            )
        )
    ):
        raise ValueError("T20.35t attempt marker drifted")
    try:
        datetime.fromisoformat(payload["started_at"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("T20.35t attempt timestamp is invalid") from error


def _verify_output_checkpoint_config(payload: dict, *, summary: dict) -> dict:
    verify_signed_payload(payload, label="T20.35t output checkpoint")
    if (
        payload.get("schema_version")
        != "scenesmith.t20_35t_time_normalized_standard_replay_checkpoint.v1"
        or payload.get("task_id") != "T20.35t"
        or payload.get("training_spec_identity_sha256")
        != summary["training_spec_identity_sha256"]
        or payload.get("authority_decision_identity_sha256")
        != summary["authority_decision_identity_sha256"]
        or payload.get("source_checkpoint_identity_sha256")
        != summary["source_checkpoint_identity_sha256"]
        or payload.get("base_model_revision") != EXPECTED_MODEL_REVISION
        or payload.get("adaptation_mode") != ADAPTATION_MODE
        or payload.get("peft_wrapper_used") is not False
        or payload.get("train_expert_only") is not True
        or payload.get("freeze_vision_encoder") is not True
        or payload.get("trainable_prefixes") != list(TRAINABLE_PREFIXES)
        or payload.get("trainable_parameter_names_sha256")
        != summary["trainable_parameter_names_sha256"]
        or payload.get("trainable_parameter_count")
        != summary["trainable_parameter_count"]
        or payload.get("paligemma_trainable_parameter_count") != 0
    ):
        raise ValueError("T20.35t output checkpoint config drifted")
    names = payload.get("trainable_parameter_names")
    if hashlib.sha256(canonical_json_bytes(names)).hexdigest() != payload.get(
        "trainable_parameter_names_sha256"
    ):
        raise ValueError("T20.35t output checkpoint trainable-name hash drifted")
    if verify_tensor_manifest(
        payload.get("trainable_tensor_manifest"),
        trainable_parameter_names=names,
    ) != payload.get("trainable_parameter_count"):
        raise ValueError("T20.35t output checkpoint tensor manifest drifted")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
