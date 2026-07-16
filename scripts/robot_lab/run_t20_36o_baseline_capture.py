#!/usr/bin/env python3
"""Run or verify the one-use T20.36o X bridge baseline capture."""

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
from typing import Any

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
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    PALIGEMMA_PREFIX,
    verify_parameter_boundary,
)
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    ACTIVE_ACTION_DIMENSIONS,
    MAXIMUM_ACTION_DIMENSIONS,
    RESULT_PATH as SOURCE_RESULT_PATH,
)
from scenesmith.robot_lab.t20_36o_baseline_capture import (  # noqa: E402
    ATTEMPT_PATH,
    CHUNK_START_FRAMES,
    CONSTRUCTION_SEED,
    DENOISE_STEP_COUNT,
    EXECUTED_LENGTHS,
    FAILURE_PATH,
    FAILURE_RESULT_PATH,
    INFERENCE_SEEDS,
    RESULT_PATH,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    TENSOR_PATH,
    TRACKED_ATTEMPT_PATH,
    TRAJECTORY_PATH,
    build_attempt_marker,
    build_failure,
    build_failure_result,
    build_result,
    build_run_summary,
    build_tensor_artifact,
    build_trajectory_artifact,
    load_live_contracts,
    verify_attempt_marker,
    verify_result,
    verify_run_summary,
    verify_tensor_artifact,
    verify_tracked_result,
    verify_trajectory_artifact,
)
from scenesmith.robot_lab.t20_36o_baseline_inference_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
)
from scenesmith.robot_lab.t20_36o_episode_bridge_design import (  # noqa: E402
    SPEC_PATH as BRIDGE_SPEC_PATH,
)
from scripts.robot_lab.run_t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    CHECKPOINT_CONFIG_PATH as SOURCE_CHECKPOINT_CONFIG_PATH,
    CHECKPOINT_MODEL_PATH as SOURCE_CHECKPOINT_MODEL_PATH,
    _verify_output_checkpoint_config,
)


def load_t20_36o_batches(*, sources: dict[str, Any]) -> dict[str, Any]:
    """Load and hash-check all five bound episode-0 observations and targets."""
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
    config.n_action_steps = 50
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
    windows = sources["bridge_spec"]["source_windows"]
    batches = []
    for start_index, (start, executed_length, window) in enumerate(
        zip(CHUNK_START_FRAMES, EXECUTED_LENGTHS, windows, strict=True)
    ):
        if (
            window["start_frame"] != start
            or window["executed_length"] != executed_length
        ):
            raise ValueError("T20.36o source window order drifted")
        raw_batch = default_collate([dataset[start]])
        target_lerobot = raw_batch["action"].detach().cpu().numpy()[0]
        if target_lerobot.shape != (50, ACTIVE_ACTION_DIMENSIONS):
            raise ValueError("T20.36o dataset target shape drifted")
        target_physical = np.asarray(
            [lerobot_to_mujoco(row.tolist()) for row in target_lerobot],
            dtype=np.float64,
        )
        signed_target = np.asarray(
            window["padded_target_action_mujoco_rad"], dtype=np.float64
        )
        pad_mask = raw_batch["action_is_pad"][0].detach().cpu().tolist()
        expected_pad_mask = [not value for value in window["executed_mask"]]
        if (
            not np.allclose(target_physical, signed_target, atol=1e-4, rtol=0.0)
            or hashlib.sha256(
                canonical_json_bytes(signed_target.astype(float).tolist())
            ).hexdigest()
            != window["padded_target_action_sha256"]
            or pad_mask != expected_pad_mask
        ):
            raise ValueError("T20.36o padded target or tail mask drifted")
        _verify_live_observation(raw_batch, window=window, dataset=dataset)
        batches.append(
            {
                "start_index": start_index,
                "start_frame": start,
                "executed_length": executed_length,
                "raw_batch": raw_batch,
                "target_physical": target_physical,
            }
        )
    return {
        "snapshot": snapshot,
        "config": config,
        "dataset": dataset,
        "batches": batches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-retained", action="store_true")
    args = parser.parse_args()
    if args.verify and args.verify_retained:
        raise ValueError("T20.36o choose one verification mode")
    if args.verify_retained:
        return _verify_retained_outputs()
    authority = (
        verify_authority(repo_root=REPO_ROOT)
        if args.verify
        else require_active_authority(repo_root=REPO_ROOT)
    )
    authority_identity = authority["decision"]["identity_sha256"]
    sources, preflight, permit = load_live_contracts(
        authority_identity=authority_identity,
        repo_root=REPO_ROOT,
    )
    if args.verify:
        return _verify_outputs(
            sources=sources,
            authority_identity=authority_identity,
            permit=permit,
        )
    immutable_paths = (
        RESULT_PATH,
        FAILURE_RESULT_PATH,
        TENSOR_PATH,
        TRAJECTORY_PATH,
        TRACKED_ATTEMPT_PATH,
    )
    if (REPO_ROOT / RUN_ROOT).exists() or any(
        (REPO_ROOT / path).exists() for path in immutable_paths
    ):
        raise FileExistsError("T20.36o immutable baseline capture already exists")
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
        raise ValueError("T20.36o LeRobot stack drifted after preflight")
    batch_source = load_t20_36o_batches(sources=sources)
    snapshot_tree = snapshot_file_tree(batch_source["snapshot"])
    snapshot_identity = hashlib.sha256(
        canonical_json_bytes(snapshot_tree)
    ).hexdigest()
    if (
        snapshot_tree != preflight["snapshot_tree"]
        or snapshot_identity != preflight["snapshot_tree_identity_sha256"]
        or batch_source["snapshot"].name != preflight["snapshot_revision"]
    ):
        raise ValueError("T20.36o base-model snapshot drifted after preflight")
    current_commit = _git("rev-parse", "HEAD")
    attempt = build_attempt_marker(
        permit=permit,
        authority_identity=authority_identity,
        source_commit=current_commit,
    )
    (REPO_ROOT / RUN_ROOT).mkdir(parents=True, exist_ok=False)
    dump_canonical_json(REPO_ROOT / ATTEMPT_PATH, attempt)
    dump_canonical_json(REPO_ROOT / TRACKED_ATTEMPT_PATH, attempt)
    verify_attempt_marker(
        attempt,
        permit=permit,
        authority_identity=authority_identity,
    )
    state = {
        "stage": "checkpoint_tensor_read",
        "checkpoint_tensor_read": False,
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "tensor_artifact_written": False,
        "trajectory_artifact_written": False,
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
            trajectory_artifact_written=state["trajectory_artifact_written"],
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
    sources: dict[str, Any],
    authority_identity: str,
    permit: dict[str, Any],
    attempt: dict[str, Any],
    batch_source: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    import torch

    from lerobot.policies import make_policy, make_pre_post_processors
    from safetensors.torch import load_file

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36o requires the authorized local MPS runtime")
    source_run = sources["x_runtime"]["source_run"]
    checkpoint_config = _verify_output_checkpoint_config(
        load_strict_json(Path(SOURCE_CHECKPOINT_CONFIG_PATH)),
        summary=source_run,
    )
    state["checkpoint_tensor_read"] = True
    checkpoint = load_file(Path(SOURCE_CHECKPOINT_MODEL_PATH), device="cpu")
    if sorted(checkpoint) != sorted(checkpoint_config["trainable_parameter_names"]):
        raise ValueError("T20.36o source checkpoint key set drifted")
    for row in checkpoint_config["trainable_tensor_manifest"]:
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
    config.num_inference_steps = DENOISE_STEP_COUNT
    config.train_expert_only = True
    config.freeze_vision_encoder = True
    torch.manual_seed(CONSTRUCTION_SEED)
    np.random.seed(CONSTRUCTION_SEED)
    random.seed(CONSTRUCTION_SEED)
    state["stage"] = "model_construction"
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
        trainable_names != checkpoint_config["trainable_parameter_names"]
        or any(
            parameter.requires_grad
            for name, parameter in all_named
            if name.startswith(PALIGEMMA_PREFIX)
        )
    ):
        raise ValueError("T20.36o model parameter boundary drifted")
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
    processed_by_start = []
    for batch in batch_source["batches"]:
        raw_batch = batch["raw_batch"]
        for key in batch_source["dataset"].meta.camera_keys:
            if raw_batch[key].dtype == torch.uint8:
                raw_batch[key] = raw_batch[key].float().div(255.0)
        observation = {
            key: copy.deepcopy(value)
            for key, value in raw_batch.items()
            if key != "action" and not key.startswith("action_")
        }
        processed_by_start.append(preprocessor(observation))

    state["stage"] = "baseline_capture"
    tensor_rows = []
    trajectory_rows = []
    for start_index, batch in enumerate(batch_source["batches"]):
        processed = processed_by_start[start_index]
        for seed_index, seed in enumerate(INFERENCE_SEEDS):
            pair = []
            for repeat_index in range(2):
                decoded, steps, base_noise_sha256 = _decode_pi05(
                    policy,
                    postprocessor,
                    processed,
                    torch,
                    seed=seed,
                    expected_noise_hash=permit["base_noise_sha256_by_seed"][
                        seed_index
                    ],
                )
                decoded_values = decoded.astype(float).tolist()
                decoded_sha256 = hashlib.sha256(
                    canonical_json_bytes(decoded_values)
                ).hexdigest()
                denoise_path_sha256 = hashlib.sha256(
                    canonical_json_bytes(steps)
                ).hexdigest()
                common = {
                    "start_index": start_index,
                    "start_frame": batch["start_frame"],
                    "executed_length": batch["executed_length"],
                    "seed_index": seed_index,
                    "inference_seed": seed,
                    "repeat_index": repeat_index,
                }
                tensor_rows.append(
                    {**common, "decoded_action_chunk": decoded_values}
                )
                trajectory_rows.append(
                    {
                        **common,
                        "base_noise_sha256": base_noise_sha256,
                        "decoded_action_chunk_sha256": decoded_sha256,
                        "steps": steps,
                    }
                )
                pair.append((decoded_sha256, denoise_path_sha256))
            if pair[0] != pair[1]:
                raise ValueError("T20.36o decoded or denoise repeat drifted")
            if (
                batch["start_frame"] == 0
                and pair[0][0] != permit["expected_start_zero_hashes"][seed_index]
            ):
                raise ValueError("T20.36o start-zero action hash failed reproduction")
        if batch["start_frame"] == 0 and len(tensor_rows) != 10:
            raise ValueError("T20.36o start-zero gate did not complete first")
    state["model_inference"] = True

    tensor_artifact = build_tensor_artifact(
        attempt=attempt,
        permit=permit,
        rows=tensor_rows,
    )
    dump_canonical_json(REPO_ROOT / TENSOR_PATH, tensor_artifact)
    state["tensor_artifact_written"] = True
    verify_tensor_artifact(
        tensor_artifact,
        attempt=attempt,
        permit=permit,
    )
    trajectory_artifact = build_trajectory_artifact(
        attempt=attempt,
        permit=permit,
        tensor_artifact=tensor_artifact,
        rows=trajectory_rows,
    )
    del trajectory_rows
    gc.collect()
    dump_canonical_json(REPO_ROOT / TRAJECTORY_PATH, trajectory_artifact)
    state["trajectory_artifact_written"] = True
    verify_trajectory_artifact(
        trajectory_artifact,
        attempt=attempt,
        permit=permit,
        tensor_artifact=tensor_artifact,
    )
    state["stage"] = "frozen_bridge_scoring"
    run = build_run_summary(
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        trajectory_artifact=trajectory_artifact,
    )
    result = build_result(run=run)
    dump_canonical_json(REPO_ROOT / RUN_SUMMARY_PATH, run)
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    verify_run_summary(
        run,
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        trajectory_artifact=trajectory_artifact,
    )
    verify_result(result, run=run)
    return result


def _decode_pi05(
    policy,
    postprocessor,
    processed_observation,
    torch,
    *,
    seed: int,
    expected_noise_hash: str,
) -> tuple[np.ndarray, list[dict[str, Any]], str]:
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
    base_noise_sha256 = hashlib.sha256(
        canonical_json_bytes(base_values)
    ).hexdigest()
    if base_noise_sha256 != expected_noise_hash:
        raise ValueError("T20.36o base noise failed exact reproduction")
    captured = []
    original = policy.model.denoise_step

    def capture(*args, **kwargs):
        state = kwargs.get("x_t")
        timestep = kwargs.get("timestep")
        if state is None or timestep is None:
            raise ValueError("T20.36o denoise call signature drifted")
        expected_time = 1.0 - len(captured) / DENOISE_STEP_COUNT
        observed_time = float(timestep[0].detach().cpu().item())
        if abs(observed_time - expected_time) > 1e-6:
            raise ValueError("T20.36o live denoise time grid drifted")
        velocity = original(*args, **kwargs)
        captured.append(
            {
                "step_index": len(captured),
                "time": expected_time,
                "state": state[0]
                .detach()
                .cpu()
                .float()
                .numpy()
                .astype(float)
                .tolist(),
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
        with torch.no_grad():
            actions = policy.predict_action_chunk(
                processed_observation,
                noise=base_noise * mask,
            )
    finally:
        policy.model.denoise_step = original
    if len(captured) != DENOISE_STEP_COUNT:
        raise ValueError("T20.36o did not capture exactly ten denoise steps")
    decoded = []
    for action in actions[0]:
        canonical = postprocessor(action.unsqueeze(0))
        values = canonical.detach().cpu().float().numpy().reshape(-1)
        decoded.append(lerobot_to_mujoco(values.tolist()))
    result = np.asarray(decoded, dtype=np.float64)
    if result.shape != (50, ACTIVE_ACTION_DIMENSIONS):
        raise ValueError("T20.36o decoded action shape drifted")
    return result, captured, base_noise_sha256


def _verify_outputs(
    *,
    sources: dict[str, Any],
    authority_identity: str,
    permit: dict[str, Any],
) -> int:
    attempt = load_strict_json(REPO_ROOT / TRACKED_ATTEMPT_PATH)
    verify_attempt_marker(
        attempt,
        permit=permit,
        authority_identity=authority_identity,
    )
    if (REPO_ROOT / FAILURE_RESULT_PATH).exists():
        failure = load_strict_json(REPO_ROOT / FAILURE_PATH)
        failure_result = load_strict_json(REPO_ROOT / FAILURE_RESULT_PATH)
        verify_signed_payload(failure, label="T20.36o baseline failure")
        verify_signed_payload(failure_result, label="T20.36o failure result")
        print(failure_result["identity_sha256"], failure_result["decision"])
        return 0
    tensor_artifact = load_strict_json(REPO_ROOT / TENSOR_PATH)
    trajectory_artifact = load_strict_json(REPO_ROOT / TRAJECTORY_PATH)
    run = load_strict_json(REPO_ROOT / RUN_SUMMARY_PATH)
    result = load_strict_json(REPO_ROOT / RESULT_PATH)
    verify_tensor_artifact(
        tensor_artifact,
        attempt=attempt,
        permit=permit,
    )
    verify_trajectory_artifact(
        trajectory_artifact,
        attempt=attempt,
        permit=permit,
        tensor_artifact=tensor_artifact,
    )
    verify_run_summary(
        run,
        sources=sources,
        authority_identity=authority_identity,
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        trajectory_artifact=trajectory_artifact,
    )
    verify_result(result, run=run)
    print(result["identity_sha256"], result["decision"])
    return 0


def _verify_retained_outputs() -> int:
    permit = load_strict_json(
        REPO_ROOT
        / "configurations/robot_lab/t20_36o_baseline_capture_permit.json"
    )
    attempt = load_strict_json(REPO_ROOT / TRACKED_ATTEMPT_PATH)
    tensor_artifact = load_strict_json(REPO_ROOT / TENSOR_PATH)
    trajectory_artifact = load_strict_json(REPO_ROOT / TRAJECTORY_PATH)
    result = load_strict_json(REPO_ROOT / RESULT_PATH)
    bridge_spec = load_strict_json(REPO_ROOT / BRIDGE_SPEC_PATH)
    source_result = load_strict_json(REPO_ROOT / SOURCE_RESULT_PATH)
    verify_tracked_result(
        permit=permit,
        attempt=attempt,
        tensor_artifact=tensor_artifact,
        trajectory_artifact=trajectory_artifact,
        result=result,
        bridge_spec=bridge_spec,
        source_result=source_result,
    )
    print(result["identity_sha256"], result["decision"])
    return 0


def _verify_live_observation(raw_batch, *, window, dataset) -> None:
    import torch

    expected = window["dataset_observation"]
    scalar_fields = {
        "episode_index": int(raw_batch["episode_index"][0].item()),
        "frame_index": int(raw_batch["frame_index"][0].item()),
        "dataset_index": int(raw_batch["index"][0].item()),
        "task_index": int(raw_batch["task_index"][0].item()),
        "timestamp": float(raw_batch["timestamp"][0].item()),
    }
    if any(scalar_fields[key] != expected[key] for key in scalar_fields):
        raise ValueError("T20.36o live dataset scalar observation drifted")
    state = raw_batch["observation.state"][0].detach().cpu().float().tolist()
    if state != expected["state_lerobot_deg"]:
        raise ValueError("T20.36o live dataset state observation drifted")
    roles = {
        "top": "observation.images.base_0_rgb",
        "wrist": "observation.images.left_wrist_0_rgb",
    }
    for role, key in roles.items():
        image = raw_batch[key][0].detach().cpu()
        if image.ndim != 3 or image.shape[0] != 3:
            raise ValueError("T20.36o live image shape drifted")
        if str(image.dtype) == "torch.uint8":
            pixels = image
        else:
            pixels = image.mul(255.0).round().clamp(0, 255).to(dtype=torch.uint8)
        height, width = int(pixels.shape[1]), int(pixels.shape[2])
        digest = hashlib.sha256()
        digest.update(
            canonical_json_bytes({"mode": "RGB", "size": [width, height]})
        )
        digest.update(pixels.permute(1, 2, 0).contiguous().numpy().tobytes())
        if digest.hexdigest() != expected["image_pixel_sha256"][role]:
            raise ValueError(f"T20.36o live {role} image pixels drifted")
    if dataset.meta.camera_keys != list(roles.values()):
        raise ValueError("T20.36o live camera key order drifted")


def snapshot_file_tree(snapshot: Path) -> list[dict[str, Any]]:
    """Hash the exact frozen base files without tensor deserialization."""
    rows = []
    for path in sorted(item for item in snapshot.rglob("*") if item.is_file()):
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


def _require_remote_preservation(permit: dict[str, Any]) -> None:
    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36o run is on the wrong branch")
    head = _git("rev-parse", "HEAD")
    remote = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "codex/pi05-autolearn-loop"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    if head != remote:
        raise ValueError("T20.36o current source is not remotely preserved")
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
