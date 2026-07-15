#!/usr/bin/env python3
"""Run or verify the one authorized T20.35c expert-only Gate B probe."""

from __future__ import annotations

import argparse
import copy
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
from scenesmith.robot_lab.t20_35b_pi05_coverage_correction import CORRECTION_PATH  # noqa: E402
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    ACTION_HORIZON,
    ADAPTATION_MODE,
    EXPECTED_DATASET_ACTION_CHUNK_SHA256,
    FRAME_INDEX,
    INFERENCE_SEEDS,
    LEARNING_RATE,
    OPTIMIZER_UPDATES,
    PALIGEMMA_PREFIX,
    RUN_SCHEMA_VERSION,
    SOURCE_SEED,
    T20_33_SPEC_PATH,
    TRAINABLE_PREFIXES,
    TRAINING_SEED,
    verify_parameter_boundary,
    verify_preflight,
    verify_run,
    verify_tensor_manifest,
    verify_training_spec_file,
)
from scenesmith.robot_lab.t20_35c_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)


RUN_ROOT = REPO_ROOT / "outputs/robot_lab/t20_35c_expert_only_run_001"
SUMMARY_PATH = RUN_ROOT / "run_summary.json"
ATTEMPT_PATH = RUN_ROOT / "attempt.json"
CHECKPOINT_ROOT = RUN_ROOT / "checkpoint"
CHECKPOINT_CONFIG_PATH = CHECKPOINT_ROOT / "expert_only_config.json"
CHECKPOINT_MODEL_PATH = CHECKPOINT_ROOT / "expert_only_model.safetensors"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    spec = verify_training_spec_file(repo_root=REPO_ROOT)
    authority = require_active_authority(repo_root=REPO_ROOT)
    authority_identity = authority["decision"]["identity_sha256"]
    t20_33_spec = load_strict_json(REPO_ROOT / T20_33_SPEC_PATH)
    correction = load_strict_json(REPO_ROOT / CORRECTION_PATH)
    if args.verify:
        attempt = load_strict_json(ATTEMPT_PATH)
        _verify_attempt(
            attempt,
            spec_identity=spec["identity_sha256"],
            authority_identity=authority_identity,
        )
        summary = load_strict_json(SUMMARY_PATH)
        verify_run(
            summary,
            spec=spec,
            authority_identity=authority_identity,
            t20_33_spec=t20_33_spec,
            correction=correction,
        )
        if summary["attempt_identity_sha256"] != attempt["identity_sha256"]:
            raise ValueError("T20.35c summary drifted from consumed attempt")
        if _file_tree(CHECKPOINT_ROOT) != summary["checkpoint_tree"]:
            raise ValueError("T20.35c checkpoint files drifted from run summary")
        config = _verify_checkpoint_config(
            load_strict_json(CHECKPOINT_CONFIG_PATH), summary=summary
        )
        from safetensors import safe_open

        with safe_open(CHECKPOINT_MODEL_PATH, framework="pt", device="cpu") as handle:
            if sorted(handle.keys()) != sorted(config["trainable_parameter_names"]):
                raise ValueError("T20.35c checkpoint tensor names drifted")
        print(summary["identity_sha256"])
        return 0
    if RUN_ROOT.exists():
        raise FileExistsError("T20.35c immutable run root already exists; use --verify")

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
        raise ValueError("T20.35c live LeRobot stack drifted before attempt")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.datasets import LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.datasets.factory import resolve_delta_timestamps
    from lerobot.policies import make_policy, make_pre_post_processors
    from safetensors.torch import save_file
    from torch.utils.data import default_collate

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.35c requires the authorized local MPS runtime")
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
    config.train_expert_only = True
    config.freeze_vision_encoder = True
    if config.train_expert_only is not True or config.freeze_vision_encoder is not True:
        raise ValueError("T20.35c expert-only config flags did not bind")
    metadata = LeRobotDatasetMetadata(
        DATASET_REPO_ID, root=REPO_ROOT / DATASET_ROOT
    )
    dataset = LeRobotDataset(
        DATASET_REPO_ID,
        root=REPO_ROOT / DATASET_ROOT,
        episodes=[0],
        delta_timestamps=resolve_delta_timestamps(config, metadata),
        return_uint8=True,
    )
    item = dataset[FRAME_INDEX]
    raw_batch = default_collate([item])
    target_lerobot = raw_batch["action"].detach().cpu().numpy()[0]
    if target_lerobot.shape != (ACTION_HORIZON, 6):
        raise ValueError("T20.35c fixed dataset batch lacks the horizon-50 target")
    target_mujoco = np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in target_lerobot],
        dtype=np.float64,
    )
    source_episode = verify_preflight(repo_root=REPO_ROOT)["source_episode"]
    source_target = np.asarray(
        [
            row["actions"]["measured"]["values"]
            for row in source_episode["frames"][FRAME_INDEX : FRAME_INDEX + ACTION_HORIZON]
        ],
        dtype=np.float64,
    )
    source_hash = hashlib.sha256(
        canonical_json_bytes(source_target.astype(float).tolist())
    ).hexdigest()
    dataset_hash = hashlib.sha256(
        canonical_json_bytes(target_mujoco.astype(float).tolist())
    ).hexdigest()
    if (
        source_hash != spec["source_batch"]["measured_action_chunk_sha256"]
        or dataset_hash != EXPECTED_DATASET_ACTION_CHUNK_SHA256
        or not np.allclose(target_mujoco, source_target, rtol=0.0, atol=1e-5)
    ):
        raise ValueError("T20.35c dataset batch substituted the source target")

    RUN_ROOT.mkdir(parents=True, exist_ok=False)
    attempt = sign_payload(
        {
            "schema_version": "scenesmith.t20_35c_expert_only_attempt.v1",
            "task_id": "T20.35c",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "started_at": datetime.now().astimezone().isoformat(),
            "one_run_permit_consumed": True,
            "model_loaded_at_marker": False,
            "optimizer_created_at_marker": False,
            "closed_loop_rollout": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )
    dump_canonical_json(ATTEMPT_PATH, attempt)

    torch.manual_seed(TRAINING_SEED)
    np.random.seed(TRAINING_SEED)
    random.seed(TRAINING_SEED)
    policy = make_policy(config, ds_meta=dataset.meta).to("mps")
    if hasattr(policy, "peft_config") or "Peft" in type(policy).__name__:
        raise ValueError("T20.35c unexpectedly constructed a PEFT policy")
    all_named = list(policy.named_parameters())
    all_names = [name for name, _ in all_named]
    trainable_named = [
        (name, parameter) for name, parameter in all_named if parameter.requires_grad
    ]
    trainable_names = [name for name, _ in trainable_named]
    prefix_counts = verify_parameter_boundary(
        all_parameter_names=all_names,
        trainable_parameter_names=trainable_names,
    )
    paligemma_named = [
        (name, parameter)
        for name, parameter in all_named
        if name.startswith(PALIGEMMA_PREFIX)
    ]
    if not paligemma_named or any(parameter.requires_grad for _, parameter in paligemma_named):
        raise ValueError("T20.35c PaliGemma freeze failed")
    trainable = [parameter for _, parameter in trainable_named]
    trainable_tensor_manifest = [
        {
            "name": name,
            "shape": list(parameter.shape),
            "dtype": str(parameter.dtype),
            "numel": parameter.numel(),
        }
        for name, parameter in trainable_named
    ]
    trainable_parameter_count = sum(parameter.numel() for parameter in trainable)
    if verify_tensor_manifest(
        trainable_tensor_manifest,
        trainable_parameter_names=trainable_names,
    ) != trainable_parameter_count:
        raise ValueError("T20.35c trainable tensor manifest accounting failed")
    all_parameter_count = sum(parameter.numel() for _, parameter in all_named)
    paligemma_parameter_count = sum(parameter.numel() for _, parameter in paligemma_named)
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
    optimizer = torch.optim.AdamW(trainable, lr=LEARNING_RATE, weight_decay=0.0)

    baseline = _objective_mean(policy, batch, torch)
    losses: list[float] = []
    gradients: list[float] = []
    policy.train()
    for update in range(OPTIMIZER_UPDATES):
        optimizer.zero_grad(set_to_none=True)
        torch.manual_seed(TRAINING_SEED + update)
        loss, _ = policy(batch)
        if not torch.isfinite(loss):
            raise ValueError(f"T20.35c non-finite objective at update {update + 1}")
        loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in trainable
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.35c non-finite gradient at update {update + 1}")
        norm = torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        if not torch.isfinite(norm):
            raise ValueError(f"T20.35c non-finite gradient norm at update {update + 1}")
        optimizer.step()
        torch.mps.synchronize()
        losses.append(float(loss.detach().cpu()))
        gradients.append(float(norm.detach().cpu()))
        if (update + 1) % 25 == 0:
            print(update + 1, losses[-1], flush=True)
    final = _objective_mean(policy, batch, torch)
    chunks = _decoded_chunks(
        policy, preprocessor, postprocessor, raw_batch, target_mujoco, torch
    )

    CHECKPOINT_ROOT.mkdir(parents=True, exist_ok=False)
    checkpoint_config = sign_payload(
        {
            "schema_version": "scenesmith.t20_35c_expert_only_checkpoint.v1",
            "task_id": "T20.35c",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
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
            "trainable_tensor_manifest": trainable_tensor_manifest,
            "trainable_parameter_count": trainable_parameter_count,
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
    tree = _file_tree(CHECKPOINT_ROOT)
    summary = sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": "T20.35c",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "attempt_identity_sha256": attempt["identity_sha256"],
            "lerobot_stack_identity_sha256": stack["identity_sha256"],
            "fixed_dataset_index": FRAME_INDEX,
            "fixed_source_seed": SOURCE_SEED,
            "action_horizon": ACTION_HORIZON,
            "source_measured_action_chunk_sha256": source_hash,
            "dataset_action_chunk_sha256": dataset_hash,
            "optimizer_update_count": OPTIMIZER_UPDATES,
            "training_seed": TRAINING_SEED,
            "learning_rate": LEARNING_RATE,
            "adaptation_mode": ADAPTATION_MODE,
            "peft_wrapper_used": False,
            "train_expert_only": True,
            "freeze_vision_encoder": True,
            "trainable_prefixes": list(TRAINABLE_PREFIXES),
            "trainable_boundary_complete": True,
            "all_parameter_names": all_names,
            "all_parameter_names_sha256": hashlib.sha256(
                canonical_json_bytes(all_names)
            ).hexdigest(),
            "trainable_parameter_names": trainable_names,
            "trainable_parameter_names_sha256": checkpoint_config[
                "trainable_parameter_names_sha256"
            ],
            "trainable_tensor_manifest": trainable_tensor_manifest,
            "required_prefix_parameter_counts": prefix_counts,
            "all_parameter_count": all_parameter_count,
            "trainable_parameter_count": trainable_parameter_count,
            "paligemma_parameter_count": paligemma_parameter_count,
            "paligemma_trainable_parameter_count": 0,
            "baseline_objective_mean": baseline,
            "final_objective_mean": final,
            "per_update_objective": losses,
            "gradient_norms_before_clip": gradients,
            "decoded_action_chunks": chunks,
            "checkpoint_tree": tree,
            "checkpoint_identity_sha256": hashlib.sha256(
                canonical_json_bytes(tree)
            ).hexdigest(),
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "twin_updated": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    dump_canonical_json(SUMMARY_PATH, summary)
    verify_run(
        summary,
        spec=spec,
        authority_identity=authority_identity,
        t20_33_spec=t20_33_spec,
        correction=correction,
    )
    print(summary["identity_sha256"], flush=True)
    return 0


def _objective_mean(policy, batch, torch) -> float:
    values = []
    policy.eval()
    with torch.no_grad():
        for seed in INFERENCE_SEEDS:
            torch.manual_seed(seed)
            loss, _ = policy(batch)
            if not torch.isfinite(loss):
                raise ValueError("T20.35c non-finite objective evaluation")
            values.append(float(loss.detach().cpu()))
    return float(sum(values) / len(values))


def _decoded_chunks(policy, preprocessor, postprocessor, raw_batch, target, torch):
    observation = {
        key: copy.deepcopy(value)
        for key, value in raw_batch.items()
        if key != "action" and not key.startswith("action_")
    }
    processed = preprocessor(observation)
    rows = []
    policy.eval()
    with torch.no_grad():
        for seed in INFERENCE_SEEDS:
            torch.manual_seed(seed)
            policy.reset()
            decoded = []
            for _ in range(ACTION_HORIZON):
                canonical = postprocessor(policy.select_action(processed))
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


def _verify_checkpoint_config(payload: dict, *, summary: dict) -> dict:
    verify_signed_payload(payload, label="T20.35c expert-only checkpoint")
    if (
        payload.get("schema_version")
        != "scenesmith.t20_35c_expert_only_checkpoint.v1"
        or payload.get("task_id") != "T20.35c"
        or payload.get("training_spec_identity_sha256")
        != summary["training_spec_identity_sha256"]
        or payload.get("authority_decision_identity_sha256")
        != summary["authority_decision_identity_sha256"]
        or payload.get("base_model_revision") != EXPECTED_MODEL_REVISION
        or payload.get("adaptation_mode") != ADAPTATION_MODE
        or payload.get("peft_wrapper_used") is not False
        or payload.get("train_expert_only") is not True
        or payload.get("freeze_vision_encoder") is not True
        or payload.get("trainable_prefixes") != list(TRAINABLE_PREFIXES)
        or payload.get("trainable_parameter_names")
        != summary["trainable_parameter_names"]
        or payload.get("trainable_parameter_names_sha256")
        != summary["trainable_parameter_names_sha256"]
        or payload.get("trainable_tensor_manifest")
        != summary["trainable_tensor_manifest"]
        or payload.get("trainable_parameter_count")
        != summary["trainable_parameter_count"]
        or payload.get("paligemma_trainable_parameter_count") != 0
    ):
        raise ValueError("T20.35c checkpoint config drifted")
    return payload


def _verify_attempt(
    payload: dict, *, spec_identity: str, authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35c expert-only attempt")
    if (
        payload.get("schema_version")
        != "scenesmith.t20_35c_expert_only_attempt.v1"
        or payload.get("task_id") != "T20.35c"
        or payload.get("training_spec_identity_sha256") != spec_identity
        or payload.get("authority_decision_identity_sha256") != authority_identity
        or payload.get("one_run_permit_consumed") is not True
        or payload.get("model_loaded_at_marker") is not False
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
        raise ValueError("T20.35c attempt marker drifted")
    try:
        datetime.fromisoformat(payload["started_at"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("T20.35c attempt timestamp is invalid") from error


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


if __name__ == "__main__":
    raise SystemExit(main())
