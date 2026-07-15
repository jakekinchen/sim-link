#!/usr/bin/env python3
"""Run or verify the one T20.35u post-training trajectory audit."""

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
from scenesmith.robot_lab.t20_33_one_batch_memorization import INFERENCE_SEEDS  # noqa: E402
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    PALIGEMMA_PREFIX,
    verify_parameter_boundary,
)
from scenesmith.robot_lab.t20_35j_initial_noise_scale_discriminator import (  # noqa: E402
    SAMPLER_SOURCE_PATH,
)
from scenesmith.robot_lab.t20_35t_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)
from scenesmith.robot_lab.t20_35u_post_training_trajectory_audit import (  # noqa: E402
    ACTIVE_ACTION_DIMENSIONS,
    ATTEMPT_PATH,
    MAXIMUM_ACTION_DIMENSIONS,
    NUM_INFERENCE_STEPS,
    RESULT_PATH,
    build_result,
    load_and_verify_evaluation_files,
    verify_attempt_marker,
    verify_result,
)
from scripts.robot_lab.run_t20_35d_residual_localization import _file_tree  # noqa: E402
from scripts.robot_lab.run_t20_35t_time_normalized_standard_replay_correction import (  # noqa: E402
    CHECKPOINT_CONFIG_PATH,
    CHECKPOINT_MODEL_PATH,
    CHECKPOINT_ROOT,
    _verify_output_checkpoint_config,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.verify and args.preflight:
        raise ValueError("T20.35u choose either --verify or --preflight")
    sources = load_and_verify_evaluation_files(repo_root=REPO_ROOT)
    spec = sources["trajectory_spec"]
    permit = sources["trajectory_permit"]
    if spec.get("required_python_major_minor") != [3, 12] or list(
        sys.version_info[:2]
    ) != [3, 12]:
        raise RuntimeError("T20.35u requires the reviewed Python 3.12 runtime")
    authority = require_active_authority(repo_root=REPO_ROOT)
    if (
        authority["decision"]["identity_sha256"]
        != permit["inherited_authority_decision_identity_sha256"]
    ):
        raise ValueError("T20.35u inherited authority identity drifted")
    if _file_tree(CHECKPOINT_ROOT) != spec["checkpoint_tree"]:
        raise ValueError("T20.35u checkpoint tree drifted")
    if hashlib.sha256(
        (REPO_ROOT / SAMPLER_SOURCE_PATH).read_bytes()
    ).hexdigest() != spec["sampler_source_sha256"]:
        raise ValueError("T20.35u sampler source drifted")
    target = sources["residual_report"]["target_action_chunk"]
    if args.preflight:
        if (REPO_ROOT / ATTEMPT_PATH).exists() or (REPO_ROOT / RESULT_PATH).exists():
            raise FileExistsError("T20.35u evaluation already exists")
        print(spec["identity_sha256"], permit["identity_sha256"])
        return 0
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
            source_trajectory_result=sources["source_result"],
            training_result=sources["training_result"],
            target_chunk=target,
            normalized_target=sources["target_result"]["normalized_padded_target"],
        )
        print(result["identity_sha256"], result["selected_next_hypothesis"])
        return 0
    if (REPO_ROOT / ATTEMPT_PATH).exists() or (REPO_ROOT / RESULT_PATH).exists():
        raise FileExistsError("T20.35u evaluation already exists; use --verify")

    attempt = sign_payload(
        {
            "schema_version": "scenesmith.t20_35u_evaluation_attempt.v1",
            "task_id": "T20.35u",
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
    (REPO_ROOT / ATTEMPT_PATH).parent.mkdir(parents=True, exist_ok=True)
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
    if stack["identity_sha256"] != spec["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.35u live LeRobot stack drifted")
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
        raise RuntimeError("T20.35u requires the authorized local MPS runtime")
    checkpoint_config = _verify_output_checkpoint_config(
        load_strict_json(CHECKPOINT_CONFIG_PATH),
        summary=sources["training_run"],
    )
    checkpoint = load_file(CHECKPOINT_MODEL_PATH, device="cpu")
    if sorted(checkpoint) != sorted(checkpoint_config["trainable_parameter_names"]):
        raise ValueError("T20.35u checkpoint key set drifted")
    for row in checkpoint_config["trainable_tensor_manifest"]:
        tensor = checkpoint[row["name"]]
        if (
            list(tensor.shape) != row["shape"]
            or str(tensor.dtype) != row["dtype"]
            or tensor.numel() != row["numel"]
            or not torch.isfinite(tensor).all().item()
        ):
            raise ValueError("T20.35u checkpoint tensor drifted")

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
    config.num_inference_steps = NUM_INFERENCE_STEPS
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
    raw_batch = default_collate([dataset[0]])
    target_lerobot = raw_batch["action"].detach().cpu().numpy()[0]
    target_array = np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in target_lerobot],
        dtype=np.float64,
    )
    if hashlib.sha256(
        canonical_json_bytes(target_array.astype(float).tolist())
    ).hexdigest() != spec["dataset_action_chunk_sha256"]:
        raise ValueError("T20.35u dataset target drifted")

    torch.manual_seed(20260717)
    np.random.seed(20260717)
    random.seed(20260717)
    policy = make_policy(config, ds_meta=dataset.meta).to("mps")
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
        raise ValueError("T20.35u model parameter boundary drifted")
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
    evaluations = _trajectory_evaluations(
        policy, preprocessor, postprocessor, raw_batch, torch, spec
    )
    result = build_result(
        spec=spec,
        permit=permit,
        attempt=attempt,
        source_trajectory_result=sources["source_result"],
        training_result=sources["training_result"],
        target_chunk=target_array.astype(float).tolist(),
        normalized_target=sources["target_result"]["normalized_padded_target"],
        new_trajectory_evaluations=evaluations,
    )
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    verify_result(
        result,
        spec=spec,
        permit=permit,
        attempt=attempt,
        source_trajectory_result=sources["source_result"],
        training_result=sources["training_result"],
        target_chunk=target_array.astype(float).tolist(),
        normalized_target=sources["target_result"]["normalized_padded_target"],
    )
    print(result["identity_sha256"], result["selected_next_hypothesis"], flush=True)
    return 0


def _trajectory_evaluations(policy, preprocessor, postprocessor, raw_batch, torch, spec):
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
            shape = (1, policy.model.config.chunk_size, MAXIMUM_ACTION_DIMENSIONS)
            base_noise = policy.model.sample_noise(shape, "mps")
            base_values = base_noise.detach().cpu().float().numpy().astype(float).tolist()
            base_sha = hashlib.sha256(canonical_json_bytes(base_values)).hexdigest()
            if base_sha != spec["base_noise_sha256_by_seed"][seed_index]:
                raise ValueError("T20.35u base noise failed exact reproduction")
            captured = []
            original = policy.model.denoise_step

            def capture(*args, **kwargs):
                state = kwargs.get("x_t")
                timestep = kwargs.get("timestep")
                if state is None or timestep is None:
                    raise ValueError("T20.35u denoise call signature drifted")
                expected_time = 1.0 - len(captured) / NUM_INFERENCE_STEPS
                observed_time = float(timestep[0].detach().cpu().item())
                if abs(observed_time - expected_time) > 1e-6:
                    raise ValueError("T20.35u live time grid drifted")
                velocity = original(*args, **kwargs)
                captured.append(
                    {
                        "step_index": len(captured),
                        "time": expected_time,
                        "state": state[0].detach().cpu().float().numpy().astype(float).tolist(),
                        "learned_velocity": velocity[0]
                        .detach()
                        .cpu()
                        .float()
                        .numpy()
                        .astype(float)
                        .tolist(),
                    }
                )
                return velocity

            policy.model.denoise_step = capture
            try:
                actions = policy.predict_action_chunk(processed, noise=base_noise * mask)
            finally:
                policy.model.denoise_step = original
            if len(captured) != NUM_INFERENCE_STEPS:
                raise ValueError("T20.35u did not capture exactly ten steps")
            decoded = []
            for action in actions[0]:
                canonical = postprocessor(action.unsqueeze(0))
                values = canonical.detach().cpu().float().numpy().reshape(-1)
                decoded.append(lerobot_to_mujoco(values.tolist()))
            rows.append(
                {
                    "inference_seed": seed,
                    "base_noise_sha256": base_sha,
                    "decoded_action_chunk": np.asarray(decoded, dtype=np.float64)
                    .astype(float)
                    .tolist(),
                    "steps": captured,
                }
            )
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
