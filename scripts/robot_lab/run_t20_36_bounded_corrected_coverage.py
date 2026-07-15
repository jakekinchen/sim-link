#!/usr/bin/env python3
"""Run or verify the one authorized T20.36 corrected-coverage campaign."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import importlib.metadata
import os
import random
import shutil
import subprocess
import sys

from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.act_grasp_closed_loop import (  # noqa: E402
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    run_policy_grasp_closed_loop,
)
from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.geometry_derived_grasp_primitives import (  # noqa: E402
    has_valid_antipodal_contact,
)
from scenesmith.robot_lab.grasp_evidence import validate_rendered_keyframes  # noqa: E402
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.scripted_grasp_episode_generation import (  # noqa: E402
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.so101_coordinates import (  # noqa: E402
    lerobot_to_mujoco,
    mujoco_to_lerobot,
)
from scenesmith.robot_lab.strict_grasp import strict_grasp_spec_v2  # noqa: E402
from scenesmith.robot_lab.t20_17_clean_base_preflight import (  # noqa: E402
    DATASET_REPO_ID as CLEAN_DATASET_REPO_ID,
    DATASET_ROOT as CLEAN_DATASET_ROOT,
    EXPECTED_MODEL_REVISION,
    SOURCE_MANIFEST_PATH,
    TASK,
)
from scenesmith.robot_lab.t20_23_recovery_augmented_preflight import (  # noqa: E402
    DATASET_REPO_ID as RECOVERY_DATASET_REPO_ID,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import (  # noqa: E402
    ACTION_HORIZON as GATE_B_ACTION_HORIZON,
    FRAME_INDEX,
)
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    PALIGEMMA_PREFIX,
    verify_parameter_boundary,
    verify_tensor_manifest,
)
from scenesmith.robot_lab.t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    ACTIVE_ACTION_DIMENSIONS,
    CORRECTION_EXAMPLE_COUNT,
    MAXIMUM_ACTION_DIMENSIONS,
    load_source_artifacts as load_x_correction_sources,
    materialize_correction_tensors,
)
from scenesmith.robot_lab.t20_36_bounded_corrected_coverage import (  # noqa: E402
    ATTEMPT_PATH,
    CHECKPOINT_ROOT,
    EVALUATION_SEEDS,
    INFERENCE_SEEDS,
    RECOVERY_DATASET_ROOT,
    RESULT_PATH,
    RUN_ROOT,
    RUN_SCHEMA_VERSION,
    RUN_SUMMARY_PATH,
    RUNTIME_PREFLIGHT_PATH,
    SPEC_PATH,
    TRAINING_PERMIT_PATH,
    X_CHECKPOINT_CONFIG_PATH,
    X_CHECKPOINT_MODEL_PATH,
    X_CHECKPOINT_ROOT,
    build_mirror_ref,
    build_result,
    build_trace,
    file_tree,
    load_source_artifacts,
    verify_result,
    verify_run,
    verify_runtime_preflight,
    verify_training_permit,
    verify_training_spec,
    verify_trace,
)
from scenesmith.robot_lab.t20_36_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)
from scenesmith.robot_lab.t20_32_closed_loop_divergence import (  # noqa: E402
    build_comparison_rows,
)
from scripts.robot_lab.run_t20_35x_physical_gate_joint_weighted_correction import (  # noqa: E402
    _correction_losses,
    _correction_objectives,
    _decoded_chunks,
    _standard_objectives,
)


RUN_ROOT_ABS = REPO_ROOT / RUN_ROOT
ATTEMPT_PATH_ABS = REPO_ROOT / ATTEMPT_PATH
SUMMARY_PATH_ABS = REPO_ROOT / RUN_SUMMARY_PATH
CHECKPOINT_ROOT_ABS = REPO_ROOT / CHECKPOINT_ROOT
CHECKPOINT_CONFIG_PATH = CHECKPOINT_ROOT_ABS / "corrected_coverage_config.json"
CHECKPOINT_MODEL_PATH = CHECKPOINT_ROOT_ABS / "corrected_coverage_model.safetensors"
TRACE_PATHS = {
    seed: RUN_ROOT_ABS / f"seed_{seed}_closed_loop_trace.json"
    for seed in EVALUATION_SEEDS
}
ATTEMPT_SCHEMA_VERSION = "scenesmith.t20_36_bounded_corrected_coverage_attempt.v1"
CHECKPOINT_SCHEMA_VERSION = "scenesmith.t20_36_bounded_corrected_coverage_checkpoint.v1"
CLOSED_LOOP_SCHEMA_VERSION = "scenesmith.t20_36_closed_loop_probe.v1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.verify and args.preflight:
        raise ValueError("T20.36 choose either --verify or --preflight")
    sources = load_source_artifacts(repo_root=REPO_ROOT)
    spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    verify_training_spec(spec, **sources)
    if list(sys.version_info[:2]) != spec["required_python_major_minor"]:
        raise RuntimeError("T20.36 requires the reviewed Python 3.12 runtime")
    authority = require_active_authority(repo_root=REPO_ROOT)
    authority_identity = authority["decision"]["identity_sha256"]
    runtime = load_strict_json(REPO_ROOT / RUNTIME_PREFLIGHT_PATH)
    verify_runtime_preflight(runtime, spec=spec, authority_identity=authority_identity)
    permit = load_strict_json(REPO_ROOT / TRAINING_PERMIT_PATH)
    verify_training_permit(
        permit,
        spec=spec,
        authority_identity=authority_identity,
        runtime_preflight=runtime,
    )
    _verify_immutable_inputs(spec)
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="training")
    import datasets  # noqa: F401
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    import pyarrow  # noqa: F401
    import safetensors  # noqa: F401
    import torch
    import transformers  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.datasets import LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.datasets.factory import resolve_delta_timestamps
    from lerobot.policies import make_policy, make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from lerobot.utils.constants import (
        OBS_LANGUAGE_ATTENTION_MASK,
        OBS_LANGUAGE_TOKENS,
    )
    from safetensors.torch import load_file, save_file
    from torch.utils.data import default_collate

    versions = {
        package: importlib.metadata.version(package)
        for package in spec["required_dependency_versions"]
    }
    if versions != spec["required_dependency_versions"]:
        raise RuntimeError("T20.36 live dependency versions drifted before attempt")
    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36 requires the authorized local MPS runtime")
    if (
        not args.verify
        and shutil.disk_usage(REPO_ROOT).free
        < spec["minimum_free_disk_bytes_before_attempt"]
    ):
        raise RuntimeError("T20.36 free disk fell below the pre-attempt minimum")
    if args.preflight:
        if RUN_ROOT_ABS.exists() or (REPO_ROOT / RESULT_PATH).exists():
            raise FileExistsError("T20.36 run or result already exists")
        print(spec["identity_sha256"], authority_identity, stack["identity_sha256"])
        return 0
    if args.verify:
        _verify_outputs(
            spec=spec,
            authority_identity=authority_identity,
            threshold=sources["threshold"],
        )
        return 0
    if RUN_ROOT_ABS.exists() or (REPO_ROOT / RESULT_PATH).exists():
        raise FileExistsError("T20.36 immutable run or result already exists; use --verify")

    correction_sources = load_x_correction_sources(repo_root=REPO_ROOT)
    correction_tensors = materialize_correction_tensors(
        correction_sources["trajectory_result"],
        correction_sources["target_result"],
        spec["processor_contract"]["physical_joint_weighting"][
            "coefficient_by_dimension"
        ],
    )
    RUN_ROOT_ABS.mkdir(parents=True, exist_ok=False)
    attempt = sign_payload(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "task_id": "T20.36",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime["identity_sha256"],
            "training_permit_identity_sha256": permit["identity_sha256"],
            "started_at": datetime.now().astimezone().isoformat(),
            "one_run_permit_consumed": True,
            "source_checkpoint_tree_verified": True,
            "coverage_dataset_tree_verified": True,
            "correction_examples_verified": True,
            "model_loaded_at_marker": False,
            "model_inference_at_marker": False,
            "optimizer_created_at_marker": False,
            "closed_loop_rollout_at_marker": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )
    dump_canonical_json(ATTEMPT_PATH_ABS, attempt)

    source_config = load_strict_json(REPO_ROOT / X_CHECKPOINT_CONFIG_PATH)
    verify_signed_payload(source_config, label="T20.36 X checkpoint config")
    checkpoint = load_file(REPO_ROOT / X_CHECKPOINT_MODEL_PATH, device="cpu")
    if sorted(checkpoint) != sorted(source_config["trainable_parameter_names"]):
        raise ValueError("T20.36 source checkpoint key set drifted")
    for row in source_config["trainable_tensor_manifest"]:
        tensor = checkpoint[row["name"]]
        if (
            list(tensor.shape) != row["shape"]
            or str(tensor.dtype) != row["dtype"]
            or tensor.numel() != row["numel"]
            or not torch.isfinite(tensor).all().item()
        ):
            raise ValueError("T20.36 source checkpoint tensor drifted")

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
    config.n_action_steps = 5
    config.num_inference_steps = 10
    config.train_expert_only = True
    config.freeze_vision_encoder = True
    clean_metadata = LeRobotDatasetMetadata(
        CLEAN_DATASET_REPO_ID, root=REPO_ROOT / CLEAN_DATASET_ROOT
    )
    clean_dataset = LeRobotDataset(
        CLEAN_DATASET_REPO_ID,
        root=REPO_ROOT / CLEAN_DATASET_ROOT,
        episodes=[0],
        delta_timestamps=resolve_delta_timestamps(config, clean_metadata),
        return_uint8=True,
    )
    recovery_metadata = LeRobotDatasetMetadata(
        RECOVERY_DATASET_REPO_ID, root=REPO_ROOT / RECOVERY_DATASET_ROOT
    )
    recovery_dataset = LeRobotDataset(
        RECOVERY_DATASET_REPO_ID,
        root=REPO_ROOT / RECOVERY_DATASET_ROOT,
        delta_timestamps=resolve_delta_timestamps(config, recovery_metadata),
        return_uint8=True,
    )
    if len(recovery_dataset) != spec["coverage_dataset"]["frame_count"]:
        raise ValueError("T20.36 recovery dataset frame coverage drifted")
    raw_gate_batch = default_collate([clean_dataset[FRAME_INDEX]])
    target_lerobot = raw_gate_batch["action"].detach().cpu().numpy()[0]
    if target_lerobot.shape != (GATE_B_ACTION_HORIZON, ACTIVE_ACTION_DIMENSIONS):
        raise ValueError("T20.36 Gate B target shape drifted")
    target_mujoco = np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in target_lerobot],
        dtype=np.float64,
    )

    seed = spec["campaign"]["training_seed"]
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    policy = make_policy(config, ds_meta=clean_dataset.meta).to("mps")
    if hasattr(policy, "peft_config") or "Peft" in type(policy).__name__:
        raise ValueError("T20.36 unexpectedly constructed a PEFT policy")
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
        trainable_names != source_config["trainable_parameter_names"]
        or any(
            parameter.requires_grad
            for name, parameter in all_named
            if name.startswith(PALIGEMMA_PREFIX)
        )
    ):
        raise ValueError("T20.36 expert-only parameter boundary drifted")
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
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=snapshot,
        dataset_stats=clean_dataset.meta.stats,
        preprocessor_overrides={
            "device_processor": {"device": "mps"},
            "normalizer_processor": {
                "stats": clean_dataset.meta.stats,
                "features": {
                    **policy.config.input_features,
                    **policy.config.output_features,
                },
                "norm_map": policy.config.normalization_mapping,
            },
        },
        postprocessor_overrides={
            "unnormalizer_processor": {
                "stats": clean_dataset.meta.stats,
                "features": policy.config.output_features,
                "norm_map": policy.config.normalization_mapping,
            }
        },
    )
    gate_batch = preprocessor(_float_images(raw_gate_batch, clean_dataset, torch))
    gate_actions = policy.prepare_action(gate_batch)
    images, image_masks = policy._preprocess_images(gate_batch)  # noqa: SLF001
    tokens = gate_batch[OBS_LANGUAGE_TOKENS]
    masks = gate_batch[OBS_LANGUAGE_ATTENTION_MASK]
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
        raise ValueError("T20.36 correction example coverage drifted")
    joint_coefficients = torch.tensor(
        spec["processor_contract"]["physical_joint_weighting"][
            "coefficient_by_dimension"
        ],
        dtype=torch.float32,
        device="mps",
    ).view(1, 1, MAXIMUM_ACTION_DIMENSIONS)
    weights = spec["processor_contract"]["time_normalization"]["weight_by_step"]
    baseline_raw, baseline_joint = _correction_objectives(
        policy,
        images,
        image_masks,
        tokens,
        masks,
        gate_actions,
        examples,
        joint_coefficients,
        torch,
    )
    optimizer = torch.optim.AdamW(
        trainable,
        lr=spec["campaign"]["learning_rate"],
        betas=tuple(spec["campaign"]["betas"]),
        eps=spec["campaign"]["epsilon"],
        weight_decay=spec["campaign"]["weight_decay"],
        amsgrad=spec["campaign"]["amsgrad"],
    )
    standard_losses: list[float] = []
    correction_losses: list[float] = []
    total_losses: list[float] = []
    gradients: list[float] = []
    policy.train()
    for update, (dataset_index, example_index, flow_seed) in enumerate(
        zip(
            spec["campaign"]["coverage_sample_index_by_update"],
            spec["campaign"]["correction_example_index_by_update"],
            spec["campaign"]["standard_flow_seed_by_update"],
            strict=True,
        )
    ):
        optimizer.zero_grad(set_to_none=True)
        _, joint_loss = _correction_losses(
            policy,
            images,
            image_masks,
            tokens,
            masks,
            gate_actions,
            examples[example_index],
            joint_coefficients,
            torch,
        )
        correction_loss = joint_loss * weights[example_index % 10]
        if not torch.isfinite(correction_loss):
            raise ValueError(f"T20.36 non-finite correction at update {update + 1}")
        correction_loss.backward()
        raw_coverage = default_collate([recovery_dataset[dataset_index]])
        coverage_batch = preprocessor(
            _float_images(raw_coverage, recovery_dataset, torch)
        )
        torch.manual_seed(flow_seed)
        standard_loss, _ = policy(coverage_batch)
        if not torch.isfinite(standard_loss):
            raise ValueError(f"T20.36 non-finite coverage loss at update {update + 1}")
        standard_loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in trainable
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.36 non-finite gradient at update {update + 1}")
        norm = torch.nn.utils.clip_grad_norm_(
            trainable, spec["campaign"]["gradient_clip_norm"]
        )
        if not torch.isfinite(norm):
            raise ValueError(f"T20.36 non-finite gradient norm at update {update + 1}")
        optimizer.step()
        torch.mps.synchronize()
        standard_value = float(standard_loss.detach().cpu())
        correction_value = float(correction_loss.detach().cpu())
        standard_losses.append(standard_value)
        correction_losses.append(correction_value)
        total_losses.append(standard_value + correction_value)
        gradients.append(float(norm.detach().cpu()))
        if (update + 1) % 25 == 0:
            print(update + 1, total_losses[-1], flush=True)
        del raw_coverage, coverage_batch, standard_loss, correction_loss, joint_loss

    final_raw, final_joint = _correction_objectives(
        policy,
        images,
        image_masks,
        tokens,
        masks,
        gate_actions,
        examples,
        joint_coefficients,
        torch,
    )
    final_standard_by_seed = _standard_objectives(policy, gate_batch, torch)
    decoded_chunks = _decoded_chunks(
        policy,
        preprocessor,
        postprocessor,
        raw_gate_batch,
        target_mujoco,
        torch,
        sources["x_spec"],
    )
    final_standard_mean = sum(final_standard_by_seed) / len(final_standard_by_seed)
    objective_ratio = final_standard_mean / spec["gate_b"][
        "source_gate_baseline_objective_mean"
    ]
    objective_pass = objective_ratio <= spec["gate_b"]["maximum_objective_ratio"]
    action_pass = all(
        row["maximum_absolute_error_rad"]
        <= spec["gate_b"]["maximum_action_error_rad"]
        for row in decoded_chunks
    )
    gate_b_passed = objective_pass and action_pass
    CHECKPOINT_ROOT_ABS.mkdir(parents=True, exist_ok=False)
    checkpoint_config = sign_payload(
        {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "task_id": "T20.36",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime["identity_sha256"],
            "training_permit_identity_sha256": permit["identity_sha256"],
            "source_checkpoint_identity_sha256": spec["source_gate_b"][
                "checkpoint_identity_sha256"
            ],
            "base_model_revision": EXPECTED_MODEL_REVISION,
            "peft_wrapper_used": False,
            "train_expert_only": True,
            "freeze_vision_encoder": True,
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
    output_tree = file_tree(CHECKPOINT_ROOT_ABS)
    checkpoint_identity = hashlib.sha256(
        canonical_json_bytes(output_tree)
    ).hexdigest()
    summary = sign_payload(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "task_id": "T20.36",
            "training_spec_identity_sha256": spec["identity_sha256"],
            "authority_decision_identity_sha256": authority_identity,
            "runtime_preflight_identity_sha256": runtime["identity_sha256"],
            "training_permit_identity_sha256": permit["identity_sha256"],
            "attempt_identity_sha256": attempt["identity_sha256"],
            "source_checkpoint_identity_sha256": spec["source_gate_b"][
                "checkpoint_identity_sha256"
            ],
            "optimizer_update_count": len(total_losses),
            "optimizer_config": copy.deepcopy(spec["campaign"]),
            "coverage_sample_index_by_update": spec["campaign"][
                "coverage_sample_index_by_update"
            ],
            "correction_example_index_by_update": spec["campaign"][
                "correction_example_index_by_update"
            ],
            "standard_flow_seed_by_update": spec["campaign"][
                "standard_flow_seed_by_update"
            ],
            "per_update_standard_coverage_objective": standard_losses,
            "per_update_time_joint_weighted_correction_objective": correction_losses,
            "per_update_total_objective": total_losses,
            "gradient_norms_before_clip": gradients,
            "baseline_raw_correction_objective_mean": sum(baseline_raw)
            / CORRECTION_EXAMPLE_COUNT,
            "final_raw_correction_objective_mean": sum(final_raw)
            / CORRECTION_EXAMPLE_COUNT,
            "baseline_joint_weighted_correction_objective_mean": sum(baseline_joint)
            / CORRECTION_EXAMPLE_COUNT,
            "final_joint_weighted_correction_objective_mean": sum(final_joint)
            / CORRECTION_EXAMPLE_COUNT,
            "final_standard_objective_by_seed": final_standard_by_seed,
            "final_standard_objective_mean": final_standard_mean,
            "final_to_source_gate_baseline_objective_ratio": objective_ratio,
            "decoded_action_chunks": decoded_chunks,
            "objective_ratio_within_threshold": objective_pass,
            "all_decoded_chunks_within_threshold": action_pass,
            "gate_b_passed": gate_b_passed,
            "checkpoint_tree": output_tree,
            "checkpoint_identity_sha256": checkpoint_identity,
            "optimizer_training": True,
            "closed_loop_rollout": False,
            "checkpoint_mutated": False,
            "dataset_mutated": False,
            "statistics_changed": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    dump_canonical_json(SUMMARY_PATH_ABS, summary)
    verify_run(summary, spec=spec, authority_identity=authority_identity)
    del optimizer
    gc.collect()

    traces: list[dict[str, Any]] = []
    mirror_refs: list[dict[str, Any]] = []
    if gate_b_passed:
        traces, mirror_refs = _run_ordered_evaluations(
            policy=policy,
            preprocessor=preprocessor,
            postprocessor=postprocessor,
            torch=torch,
            prepare_observation_for_inference=prepare_observation_for_inference,
            summary=summary,
            checkpoint_identity=checkpoint_identity,
            threshold=sources["threshold"],
        )
    result = build_result(
        spec=spec,
        run=summary,
        authority_identity=authority_identity,
        traces=traces,
        mirror_refs=mirror_refs,
        threshold=sources["threshold"],
    )
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    print(
        result["identity_sha256"],
        result["decision"],
        result["evaluation_seeds_reached"],
        flush=True,
    )
    return 0


def _run_ordered_evaluations(
    *,
    policy,
    preprocessor,
    postprocessor,
    torch,
    prepare_observation_for_inference,
    summary: dict[str, Any],
    checkpoint_identity: str,
    threshold: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest = load_strict_json(REPO_ROOT / SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    sources = {
        seed: next(row for row in manifest["episodes"] if row["seed"] == seed)
        for seed in EVALUATION_SEEDS
    }
    if any(row["outcome"]["strict_success"] is not True for row in sources.values()):
        raise ValueError("T20.36 source episode is not strict-success evidence")
    contact_requirement = strict_grasp_spec_v2()["antipodal_contact_requirement"]
    model_sha = _sha(CHECKPOINT_MODEL_PATH)
    traces = []
    mirror_refs = []

    def select_action(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
        raw = {
            "observation.images.base_0_rgb": images["top"].copy(),
            "observation.images.left_wrist_0_rgb": images["wrist"].copy(),
            "observation.state": np.asarray(
                mujoco_to_lerobot(state[:6]), dtype=np.float32
            ),
        }
        prepared = prepare_observation_for_inference(
            raw,
            torch.device("mps"),
            task=TASK,
            robot_type="so101_follower",
        )
        with torch.inference_mode():
            canonical = postprocessor(policy.select_action(preprocessor(prepared)))
        values = canonical.detach().cpu().float().numpy().reshape(-1)
        if values.shape != (6,) or not np.isfinite(values).all():
            raise ValueError("T20.36 candidate emitted an invalid action")
        return np.asarray(lerobot_to_mujoco(values.tolist()), dtype=np.float64)

    policy.eval()
    for seed in EVALUATION_SEEDS:
        torch.manual_seed(INFERENCE_SEEDS[seed])
        policy.reset()
        observed: list[dict[str, Any]] = []
        rollout = run_policy_grasp_closed_loop(
            select_action,
            checkpoint_sha256=model_sha,
            training_run_summary_sha256=_sha(SUMMARY_PATH_ABS),
            seed=seed,
            schema_version=CLOSED_LOOP_SCHEMA_VERSION,
            task_id="T20.36",
            evidence_mode=f"t20_36_seed_{seed}_unassisted_complete_trace",
            policy_label="pi05_expert_only_corrected_coverage",
            frame_observer=observed.append,
            release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        )
        if any(
            rollout.get(key) != 0
            for key in ("projected_action_frame_count", "active_assist_frame_count")
        ):
            raise ValueError("T20.36 rollout used projection or assistance")
        validate_rendered_keyframes(rollout["rendered_keyframes"])
        for row in observed:
            row["t20_32_strict_contact"] = has_valid_antipodal_contact(
                row, contact_requirement
            )
        source_entry = sources[seed]
        source_episode = load_strict_json(
            default_store_root() / source_entry["relative_path"]
        )
        trace = build_trace(
            threshold=threshold,
            seed=seed,
            inference_seed=INFERENCE_SEEDS[seed],
            source_episode_file_sha256=source_entry["episode_file_sha256"],
            source_episode_identity_sha256=source_entry[
                "raw_rollout_record_identity_sha256"
            ],
            run_identity_sha256=summary["identity_sha256"],
            checkpoint_identity_sha256=checkpoint_identity,
            rows=build_comparison_rows(source_episode["frames"], observed),
            closed_loop=rollout,
        )
        dump_canonical_json(TRACE_PATHS[seed], trace)
        output = RUN_ROOT_ABS / "mirrors" / f"{trace['identity_sha256']}.mp4"
        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/robot_lab/render_rollout_mirror.py"),
                "--trace",
                str(TRACE_PATHS[seed]),
                "--output-mp4",
                str(output),
            ],
            cwd=REPO_ROOT,
            check=True,
        )
        mirror_manifest = load_strict_json(output.with_suffix(".manifest.json"))
        mirror_ref = build_mirror_ref(trace=trace, manifest=mirror_manifest)
        traces.append(trace)
        mirror_refs.append(mirror_ref)
        print(
            "evaluation",
            seed,
            trace["identity_sha256"],
            rollout["simulation_semantic_strict_success"],
            rollout["terminal_outcome"],
            flush=True,
        )
        if seed == 0 and rollout["simulation_semantic_strict_success"] is not True:
            break
    return traces, mirror_refs


def _float_images(batch: dict[str, Any], dataset, torch):
    batch = copy.deepcopy(batch)
    for key in dataset.meta.camera_keys:
        if batch[key].dtype == torch.uint8:
            batch[key] = batch[key].float().div(255.0)
    return batch


def _verify_immutable_inputs(spec: dict[str, Any]) -> None:
    if file_tree(REPO_ROOT / X_CHECKPOINT_ROOT) != spec["source_gate_b"][
        "checkpoint_tree"
    ]:
        raise ValueError("T20.36 X checkpoint tree drifted")
    if file_tree(REPO_ROOT / RECOVERY_DATASET_ROOT) != spec["coverage_dataset"][
        "file_tree"
    ]:
        raise ValueError("T20.36 coverage dataset tree drifted")


def _verify_outputs(
    *, spec: dict[str, Any], authority_identity: str, threshold: dict[str, Any]
) -> None:
    attempt = load_strict_json(ATTEMPT_PATH_ABS)
    _verify_attempt(attempt, spec=spec, authority_identity=authority_identity)
    summary = load_strict_json(SUMMARY_PATH_ABS)
    verify_run(summary, spec=spec, authority_identity=authority_identity)
    if summary["attempt_identity_sha256"] != attempt["identity_sha256"]:
        raise ValueError("T20.36 summary drifted from attempt")
    if file_tree(CHECKPOINT_ROOT_ABS) != summary["checkpoint_tree"]:
        raise ValueError("T20.36 output checkpoint tree drifted")
    config = load_strict_json(CHECKPOINT_CONFIG_PATH)
    _verify_checkpoint_config(config, summary=summary)
    from safetensors import safe_open

    with safe_open(CHECKPOINT_MODEL_PATH, framework="pt", device="cpu") as handle:
        if sorted(handle.keys()) != sorted(config["trainable_parameter_names"]):
            raise ValueError("T20.36 checkpoint tensor names drifted")
    traces = []
    mirror_refs = []
    for seed in EVALUATION_SEEDS:
        path = TRACE_PATHS[seed]
        if not path.exists():
            continue
        trace = load_strict_json(path)
        verify_trace(trace, threshold=threshold)
        manifest_path = (
            RUN_ROOT_ABS / "mirrors" / f"{trace['identity_sha256']}.manifest.json"
        )
        manifest = load_strict_json(manifest_path)
        output = Path(manifest["output_mp4"])
        if (
            not output.is_file()
            or output.stat().st_size != manifest["output_bytes"]
            or _sha(output) != manifest["output_sha256"]
        ):
            raise ValueError("T20.36 mirror MP4 drifted")
        traces.append(trace)
        mirror_refs.append(build_mirror_ref(trace=trace, manifest=manifest))
    result = load_strict_json(REPO_ROOT / RESULT_PATH)
    verify_result(
        result,
        spec=spec,
        run=summary,
        authority_identity=authority_identity,
        traces=traces,
        mirror_refs=mirror_refs,
        threshold=threshold,
    )
    print(result["identity_sha256"], result["decision"])


def _verify_attempt(
    payload: dict[str, Any], *, spec: dict[str, Any], authority_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.36 attempt")
    if (
        payload.get("schema_version") != ATTEMPT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.36"
        or payload.get("training_spec_identity_sha256") != spec["identity_sha256"]
        or payload.get("authority_decision_identity_sha256") != authority_identity
        or payload.get("one_run_permit_consumed") is not True
        or payload.get("source_checkpoint_tree_verified") is not True
        or payload.get("coverage_dataset_tree_verified") is not True
        or payload.get("correction_examples_verified") is not True
        or payload.get("model_loaded_at_marker") is not False
        or payload.get("model_inference_at_marker") is not False
        or payload.get("optimizer_created_at_marker") is not False
        or payload.get("closed_loop_rollout_at_marker") is not False
        or any(
            payload.get(field) is not False
            for field in (
                "physical_actuation",
                "external_compute_started",
                "brev_compute_started",
            )
        )
    ):
        raise ValueError("T20.36 attempt marker drifted")
    datetime.fromisoformat(payload["started_at"])


def _verify_checkpoint_config(
    payload: dict[str, Any], *, summary: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36 output checkpoint config")
    if (
        payload.get("schema_version") != CHECKPOINT_SCHEMA_VERSION
        or payload.get("task_id") != "T20.36"
        or payload.get("training_spec_identity_sha256")
        != summary["training_spec_identity_sha256"]
        or payload.get("source_checkpoint_identity_sha256")
        != summary["source_checkpoint_identity_sha256"]
        or payload.get("base_model_revision") != EXPECTED_MODEL_REVISION
        or payload.get("peft_wrapper_used") is not False
        or payload.get("train_expert_only") is not True
        or payload.get("freeze_vision_encoder") is not True
        or payload.get("paligemma_trainable_parameter_count") != 0
    ):
        raise ValueError("T20.36 output checkpoint config drifted")
    names = payload.get("trainable_parameter_names")
    if hashlib.sha256(canonical_json_bytes(names)).hexdigest() != payload.get(
        "trainable_parameter_names_sha256"
    ):
        raise ValueError("T20.36 checkpoint trainable-name hash drifted")
    if verify_tensor_manifest(
        payload.get("trainable_tensor_manifest"),
        trainable_parameter_names=names,
    ) != payload.get("trainable_parameter_count"):
        raise ValueError("T20.36 checkpoint tensor manifest drifted")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
