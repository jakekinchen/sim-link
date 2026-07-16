#!/usr/bin/env python3
"""Run or verify the one-use T20.36n T20.35x tensor reproduction."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import os
import random
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
from scenesmith.robot_lab.t20_17_clean_base_preflight import (  # noqa: E402
    DATASET_REPO_ID,
    DATASET_ROOT,
    EXPECTED_MODEL_REVISION,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (  # noqa: E402
    ACTION_HORIZON,
    FRAME_INDEX,
)
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    PALIGEMMA_PREFIX,
    verify_parameter_boundary,
)
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    ACTIVE_ACTION_DIMENSIONS,
    MAXIMUM_ACTION_DIMENSIONS,
    TRAINING_SEED,
)
from scenesmith.robot_lab.t20_36n_tensor_reproduction import (  # noqa: E402
    ATTEMPT_PATH,
    FAILURE_PATH,
    FAILURE_RESULT_PATH,
    RESULT_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    SOURCE_CHECKPOINT_ROOT,
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
    verify_tracked_result,
)
from scenesmith.robot_lab.t20_36n_tensor_reproduction_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
)
from scripts.robot_lab.run_t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    CHECKPOINT_CONFIG_PATH as SOURCE_CHECKPOINT_CONFIG_PATH,
    CHECKPOINT_MODEL_PATH as SOURCE_CHECKPOINT_MODEL_PATH,
    _verify_output_checkpoint_config,
)


def load_t20_35x_batch(*, sources):
    """Load and hash-check the source one-batch target without a model."""
    import lerobot.policies.pi05.processor_pi05  # noqa: F401

    from lerobot.configs import PreTrainedConfig
    from lerobot.datasets import LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.datasets.factory import resolve_delta_timestamps
    from torch.utils.data import default_collate

    snapshot = (
        Path.home()
        / ".cache/huggingface/hub/models--lerobot--pi05_base/snapshots"
        / EXPECTED_MODEL_REVISION
    ).resolve()
    config = PreTrainedConfig.from_pretrained(snapshot, local_files_only=True)
    config.pretrained_path = str(snapshot)
    config.n_action_steps = ACTION_HORIZON
    metadata = LeRobotDatasetMetadata(
        DATASET_REPO_ID,
        root=REPO_ROOT / DATASET_ROOT,
    )
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
        raise ValueError("T20.36n fixed dataset target shape drifted")
    target_physical = np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in target_lerobot],
        dtype=np.float64,
    )
    target_sha256 = hashlib.sha256(
        canonical_json_bytes(target_physical.astype(float).tolist())
    ).hexdigest()
    if target_sha256 != sources["batch_evidence_identity_sha256"]:
        raise ValueError("T20.36n fixed dataset target drifted")
    return {
        "snapshot": snapshot,
        "config": config,
        "dataset": dataset,
        "raw_batch": raw_batch,
        "physical_action": target_physical,
    }


def snapshot_file_tree(snapshot: Path) -> list[dict[str, object]]:
    """Hash the exact frozen base files without tensor deserialization."""
    rows = []
    for path in sorted(item for item in Path(snapshot).rglob("*") if item.is_file()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024 * 1024), b""):
                digest.update(chunk)
        rows.append(
            {
                "path": path.relative_to(snapshot).as_posix(),
                "sha256": digest.hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-retained", action="store_true")
    args = parser.parse_args()
    if args.verify and args.verify_retained:
        raise ValueError("T20.36n choose one verification mode")
    if args.verify_retained:
        verify_authority(repo_root=REPO_ROOT)
        sources = load_verified_sources(repo_root=REPO_ROOT)
        tensor = load_strict_json(REPO_ROOT / TENSOR_PATH)
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_tracked_result(
            tensor_artifact=tensor,
            result=result,
            sources=sources,
        )
        print(result["identity_sha256"], result["decision"])
        return 0
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
        (REPO_ROOT / path).exists()
        for path in (RESULT_PATH, FAILURE_RESULT_PATH, TENSOR_PATH)
    ):
        raise FileExistsError("T20.36n immutable tensor reproduction already exists")
    _require_remote_preservation(permit)
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    if stack["identity_sha256"] != preflight["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36n LeRobot stack drifted after preflight")
    batch_source = load_t20_35x_batch(sources=sources)
    snapshot_tree = snapshot_file_tree(batch_source["snapshot"])
    snapshot_identity = hashlib.sha256(
        canonical_json_bytes(snapshot_tree)
    ).hexdigest()
    if (
        snapshot_tree != preflight["snapshot_tree"]
        or snapshot_identity != preflight["snapshot_tree_identity_sha256"]
        or batch_source["snapshot"].name != preflight["snapshot_revision"]
    ):
        raise ValueError("T20.36n base-model snapshot drifted after preflight")
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

    from lerobot.policies import make_policy, make_pre_post_processors
    from safetensors.torch import load_file

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36n requires the authorized local MPS runtime")
    spec = sources["t20_35x_spec"]
    source_checkpoint_config = _verify_output_checkpoint_config(
        load_strict_json(Path(SOURCE_CHECKPOINT_CONFIG_PATH)),
        summary=sources["source_run"],
    )
    state["checkpoint_tensor_read"] = True
    checkpoint = load_file(Path(SOURCE_CHECKPOINT_MODEL_PATH), device="cpu")
    if sorted(checkpoint) != sorted(
        source_checkpoint_config["trainable_parameter_names"]
    ):
        raise ValueError("T20.36n source checkpoint key set drifted")
    for row in source_checkpoint_config["trainable_tensor_manifest"]:
        tensor = checkpoint[row["name"]]
        if (
            list(tensor.shape) != row["shape"]
            or str(tensor.dtype) != row["dtype"]
            or tensor.numel() != row["numel"]
            or not torch.isfinite(tensor).all().item()
        ):
            raise ValueError("T20.36n source checkpoint tensor drifted")
    config = batch_source["config"]
    config.pretrained_path = str(batch_source["snapshot"])
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.gradient_checkpointing = True
    config.compile_model = False
    config.n_action_steps = ACTION_HORIZON
    config.num_inference_steps = spec["evaluation"]["num_inference_steps"]
    config.train_expert_only = True
    config.freeze_vision_encoder = True
    torch.manual_seed(TRAINING_SEED)
    np.random.seed(TRAINING_SEED)
    random.seed(TRAINING_SEED)
    state["model_constructed"] = True
    policy = make_policy(config, ds_meta=batch_source["dataset"].meta).to("mps")
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
        raise ValueError("T20.36n model parameter boundary drifted")
    for name, parameter in trainable_named:
        parameter.data.copy_(checkpoint[name].to(device="mps"))
    del checkpoint
    gc.collect()
    state["model_loaded"] = True
    policy.eval()
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
    raw_batch = batch_source["raw_batch"]
    for key in batch_source["dataset"].meta.camera_keys:
        if raw_batch[key].dtype == torch.uint8:
            raw_batch[key] = raw_batch[key].float().div(255.0)
    observation = {
        key: copy.deepcopy(value)
        for key, value in raw_batch.items()
        if key != "action" and not key.startswith("action_")
    }
    processed_observation = preprocessor(observation)
    state["stage"] = "tensor_reproduction"
    rows = []
    for index, seed in enumerate(permit["inference_seeds"]):
        expected_noise_hash = spec["evaluation"][
            "base_noise_sha256_by_seed"
        ][index]
        first_physical = _decode_pi05(
            policy,
            postprocessor,
            processed_observation,
            torch,
            seed=seed,
            expected_noise_hash=expected_noise_hash,
        )
        second_physical = _decode_pi05(
            policy,
            postprocessor,
            processed_observation,
            torch,
            seed=seed,
            expected_noise_hash=expected_noise_hash,
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


def _decode_pi05(
    policy,
    postprocessor,
    processed_observation,
    torch,
    *,
    seed,
    expected_noise_hash,
):
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
    base_noise_values = (
        base_noise.detach().cpu().float().numpy().astype(float).tolist()
    )
    if (
        hashlib.sha256(canonical_json_bytes(base_noise_values)).hexdigest()
        != expected_noise_hash
    ):
        raise ValueError("T20.36n base noise failed exact reproduction")
    actions = policy.predict_action_chunk(
        processed_observation,
        noise=base_noise * mask,
    )
    decoded = []
    for action in actions[0]:
        canonical = postprocessor(action.unsqueeze(0))
        values = canonical.detach().cpu().float().numpy().reshape(-1)
        decoded.append(lerobot_to_mujoco(values.tolist()))
    return np.asarray(decoded, dtype=np.float64)


def _verify_outputs(sources, authority_identity, permit) -> int:
    attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
    verify_attempt_marker(
        attempt, permit=permit, authority_identity=authority_identity
    )
    if (REPO_ROOT / FAILURE_RESULT_PATH).exists():
        failure = load_strict_json(REPO_ROOT / FAILURE_PATH)
        failure_result = load_strict_json(REPO_ROOT / FAILURE_RESULT_PATH)
        verify_signed_payload(failure, label="T20.36n failure")
        verify_signed_payload(failure_result, label="T20.36n failure result")
        print(failure_result["identity_sha256"], failure_result["decision"])
        return 0
    batch_source = load_t20_35x_batch(sources=sources)
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
        raise ValueError("T20.36n run is on the wrong branch")
    head = _git("rev-parse", "HEAD")
    remote = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "codex/pi05-autolearn-loop"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    if head != remote:
        raise ValueError("T20.36n current source is not remotely preserved")
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
