#!/usr/bin/env python3
"""Run or verify the one T20.35g inference-only cadence evaluation."""

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
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco  # noqa: E402
from scenesmith.robot_lab.t20_17_clean_base_preflight import (  # noqa: E402
    DATASET_REPO_ID,
    DATASET_ROOT,
    EXPECTED_MODEL_REVISION,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (  # noqa: E402
    INFERENCE_SEEDS,
)
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    PALIGEMMA_PREFIX,
    verify_parameter_boundary,
)
from scenesmith.robot_lab.t20_35c_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (  # noqa: E402
    CHECKPOINT_ROOT,
)
from scenesmith.robot_lab.t20_35g_denoising_cadence_discriminator import (  # noqa: E402
    ATTEMPT_PATH,
    CADENCE_NUM_INFERENCE_STEPS,
    RESULT_PATH,
    build_result,
    load_and_verify_evaluation_files,
    verify_attempt_marker,
    verify_result,
)
from scripts.robot_lab.run_t20_35d_residual_localization import (  # noqa: E402
    CHECKPOINT_CONFIG_PATH,
    CHECKPOINT_MODEL_PATH,
    _file_tree,
    _verify_checkpoint_config,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_and_verify_evaluation_files(repo_root=REPO_ROOT)
    spec = sources["cadence_spec"]
    permit = sources["cadence_permit"]
    authority = require_active_authority(repo_root=REPO_ROOT)
    if (
        authority["decision"]["identity_sha256"]
        != permit["inherited_authority_decision_identity_sha256"]
    ):
        raise ValueError("T20.35g inherited authority identity drifted")
    checkpoint_tree = _file_tree(REPO_ROOT / CHECKPOINT_ROOT)
    if checkpoint_tree != spec["checkpoint_tree"]:
        raise ValueError("T20.35g checkpoint tree drifted before evaluation")
    target = sources["residual_report"]["target_action_chunk"]

    if args.verify:
        attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
        verify_attempt_marker(
            attempt,
            spec_identity=spec["identity_sha256"],
            permit_identity=permit["identity_sha256"],
        )
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_result(
            result,
            spec=spec,
            permit=permit,
            attempt=attempt,
            target_chunk=target,
        )
        print(result["identity_sha256"], result["selected_next_hypothesis"])
        return 0
    if (REPO_ROOT / ATTEMPT_PATH).exists() or (REPO_ROOT / RESULT_PATH).exists():
        raise FileExistsError("T20.35g cadence attempt already exists; use --verify")

    attempt = sign_payload(
        {
            "schema_version": "scenesmith.t20_35g_evaluation_attempt.v1",
            "task_id": "T20.35g",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "started_at": datetime.now().astimezone().isoformat(),
            "one_evaluation_permit_consumed": True,
            "checkpoint_tree_verified": True,
            "model_loaded_at_marker": False,
            "model_inference_at_marker": False,
            "optimizer_created_at_marker": False,
            "optimizer_training": False,
            "checkpoint_mutated": False,
            "closed_loop_rollout": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )
    (REPO_ROOT / ATTEMPT_PATH).parent.mkdir(parents=True, exist_ok=False)
    dump_canonical_json(REPO_ROOT / ATTEMPT_PATH, attempt)

    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    if (
        stack["identity_sha256"]
        != sources["t20_35c_spec"]["lerobot_stack_identity_sha256"]
    ):
        raise ValueError("T20.35g live LeRobot stack drifted")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.datasets import LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.datasets.factory import resolve_delta_timestamps
    from lerobot.policies import make_policy, make_pre_post_processors
    from safetensors.torch import load_file
    from torch.utils.data import default_collate

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.35g requires the authorized local MPS runtime")
    checkpoint_config = _verify_checkpoint_config(
        load_strict_json(REPO_ROOT / CHECKPOINT_CONFIG_PATH),
        source_run=sources["source_run"],
    )
    checkpoint = load_file(REPO_ROOT / CHECKPOINT_MODEL_PATH, device="cpu")
    if sorted(checkpoint) != sorted(checkpoint_config["trainable_parameter_names"]):
        raise ValueError("T20.35g checkpoint key set drifted")
    for row in checkpoint_config["trainable_tensor_manifest"]:
        tensor = checkpoint[row["name"]]
        if (
            list(tensor.shape) != row["shape"]
            or str(tensor.dtype) != row["dtype"]
            or tensor.numel() != row["numel"]
            or not torch.isfinite(tensor).all().item()
        ):
            raise ValueError("T20.35g checkpoint tensor drifted or is non-finite")

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
    config.n_action_steps = 50
    config.train_expert_only = True
    config.freeze_vision_encoder = True
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
    item = dataset[0]
    raw_batch = default_collate([item])
    target_lerobot = raw_batch["action"].detach().cpu().numpy()[0]
    target_array = np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in target_lerobot],
        dtype=np.float64,
    )
    if hashlib.sha256(
        canonical_json_bytes(target_array.astype(float).tolist())
    ).hexdigest() != spec["dataset_action_chunk_sha256"]:
        raise ValueError("T20.35g dataset target drifted")

    torch.manual_seed(20260717)
    np.random.seed(20260717)
    random.seed(20260717)
    policy = make_policy(config, ds_meta=dataset.meta).to("mps")
    if hasattr(policy, "peft_config") or "Peft" in type(policy).__name__:
        raise ValueError("T20.35g unexpectedly constructed a PEFT policy")
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
        all_names != sources["source_run"]["all_parameter_names"]
        or trainable_names != checkpoint_config["trainable_parameter_names"]
        or any(
            parameter.requires_grad
            for name, parameter in all_named
            if name.startswith(PALIGEMMA_PREFIX)
        )
    ):
        raise ValueError("T20.35g model parameter boundary drifted")
    for name, parameter in trainable_named:
        parameter.data.copy_(checkpoint[name].to(device="mps"))
    del checkpoint
    gc.collect()

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
    evaluations = _decoded_cadences(
        policy, preprocessor, postprocessor, raw_batch, torch
    )
    result = build_result(
        spec=spec,
        permit=permit,
        attempt=attempt,
        target_chunk=target_array.astype(float).tolist(),
        cadence_evaluations=evaluations,
    )
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    verify_result(
        result,
        spec=spec,
        permit=permit,
        attempt=attempt,
        target_chunk=target_array.astype(float).tolist(),
    )
    print(result["identity_sha256"], result["selected_next_hypothesis"], flush=True)
    return 0


def _decoded_cadences(policy, preprocessor, postprocessor, raw_batch, torch):
    observation = {
        key: copy.deepcopy(value)
        for key, value in raw_batch.items()
        if key != "action" and not key.startswith("action_")
    }
    processed = preprocessor(observation)
    evaluations = []
    policy.eval()
    with torch.no_grad():
        for step_count in CADENCE_NUM_INFERENCE_STEPS:
            policy.model.config.num_inference_steps = step_count
            if policy.model.config.num_inference_steps != step_count:
                raise ValueError("T20.35g cadence assignment failed")
            rows = []
            for seed in INFERENCE_SEEDS:
                torch.manual_seed(seed)
                policy.reset()
                decoded = []
                for _ in range(50):
                    canonical = postprocessor(policy.select_action(processed))
                    values = canonical.detach().cpu().float().numpy().reshape(-1)
                    decoded.append(lerobot_to_mujoco(values.tolist()))
                rows.append(
                    {
                        "inference_seed": seed,
                        "decoded_action_chunk": np.asarray(
                            decoded, dtype=np.float64
                        ).astype(float).tolist(),
                    }
                )
            evaluations.append(
                {
                    "num_inference_steps": step_count,
                    "decoded_action_chunks": rows,
                }
            )
    return evaluations
if __name__ == "__main__":
    raise SystemExit(main())
