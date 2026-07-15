#!/usr/bin/env python3
"""Run or verify the one T20.35d deterministic checkpoint replay."""

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
from scenesmith.robot_lab.t20_35c_expert_only_capacity_ceiling import (  # noqa: E402
    ADAPTATION_MODE,
    PALIGEMMA_PREFIX,
    TRAINABLE_PREFIXES,
    verify_parameter_boundary,
    verify_tensor_manifest,
)
from scenesmith.robot_lab.t20_35c_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (  # noqa: E402
    ATTEMPT_PATH,
    CHECKPOINT_ROOT,
    INFERENCE_SEEDS,
    REPORT_PATH,
    build_report,
    verify_evaluation_files,
    verify_report,
)


CHECKPOINT_CONFIG_PATH = CHECKPOINT_ROOT / "expert_only_config.json"
CHECKPOINT_MODEL_PATH = CHECKPOINT_ROOT / "expert_only_model.safetensors"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = verify_evaluation_files(repo_root=REPO_ROOT)
    spec = sources["evaluation_spec"]
    permit = sources["evaluation_permit"]
    authority = require_active_authority(repo_root=REPO_ROOT)
    if (
        authority["decision"]["identity_sha256"]
        != permit["inherited_authority_decision_identity_sha256"]
    ):
        raise ValueError("T20.35d inherited authority identity drifted")
    checkpoint_tree = _file_tree(REPO_ROOT / CHECKPOINT_ROOT)
    if checkpoint_tree != spec["checkpoint_tree"]:
        raise ValueError("T20.35d checkpoint tree drifted before replay")
    if args.verify:
        attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
        _verify_attempt(
            attempt,
            spec_identity=spec["identity_sha256"],
            permit_identity=permit["identity_sha256"],
        )
        report = load_strict_json(REPO_ROOT / REPORT_PATH)
        verify_report(report, spec=spec, permit=permit)
        if report["replay_attempt_identity_sha256"] != attempt["identity_sha256"]:
            raise ValueError("T20.35d report drifted from replay attempt")
        print(report["identity_sha256"])
        return 0
    if (REPO_ROOT / ATTEMPT_PATH).exists() or (REPO_ROOT / REPORT_PATH).exists():
        raise FileExistsError("T20.35d replay attempt already exists; use --verify")

    attempt = sign_payload(
        {
            "schema_version": "scenesmith.t20_35d_replay_attempt.v1",
            "task_id": "T20.35d",
            "evaluation_spec_identity_sha256": spec["identity_sha256"],
            "evaluation_permit_identity_sha256": permit["identity_sha256"],
            "started_at": datetime.now().astimezone().isoformat(),
            "one_replay_permit_consumed": True,
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
    if stack["identity_sha256"] != sources["t20_35c_spec"]["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.35d live LeRobot stack drifted")
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
        raise RuntimeError("T20.35d requires the authorized local MPS runtime")
    checkpoint_config = _verify_checkpoint_config(
        load_strict_json(REPO_ROOT / CHECKPOINT_CONFIG_PATH),
        source_run=sources["source_run"],
    )
    checkpoint = load_file(REPO_ROOT / CHECKPOINT_MODEL_PATH, device="cpu")
    if sorted(checkpoint) != sorted(checkpoint_config["trainable_parameter_names"]):
        raise ValueError("T20.35d checkpoint key set drifted")
    manifest = checkpoint_config["trainable_tensor_manifest"]
    for row in manifest:
        tensor = checkpoint[row["name"]]
        if (
            list(tensor.shape) != row["shape"]
            or str(tensor.dtype) != row["dtype"]
            or tensor.numel() != row["numel"]
            or not torch.isfinite(tensor).all().item()
        ):
            raise ValueError("T20.35d checkpoint tensor drifted or is non-finite")

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
    target = np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in target_lerobot],
        dtype=np.float64,
    )
    if hashlib.sha256(canonical_json_bytes(target.astype(float).tolist())).hexdigest() != spec[
        "dataset_action_chunk_sha256"
    ]:
        raise ValueError("T20.35d dataset target drifted")

    torch.manual_seed(20260717)
    np.random.seed(20260717)
    random.seed(20260717)
    policy = make_policy(config, ds_meta=dataset.meta).to("mps")
    if hasattr(policy, "peft_config") or "Peft" in type(policy).__name__:
        raise ValueError("T20.35d unexpectedly constructed a PEFT policy")
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
    if all_names != sources["source_run"]["all_parameter_names"]:
        raise ValueError("T20.35d model parameter names drifted")
    if trainable_names != checkpoint_config["trainable_parameter_names"]:
        raise ValueError("T20.35d model trainable names drifted")
    if any(
        parameter.requires_grad
        for name, parameter in all_named
        if name.startswith(PALIGEMMA_PREFIX)
    ):
        raise ValueError("T20.35d PaliGemma freeze drifted")
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
    replay_chunks = _decoded_chunks(
        policy, preprocessor, postprocessor, raw_batch, torch
    )
    report = build_report(
        spec=spec,
        permit=permit,
        replay_attempt_identity=attempt["identity_sha256"],
        target_chunk=target.astype(float).tolist(),
        replay_chunks=replay_chunks,
    )
    dump_canonical_json(REPO_ROOT / REPORT_PATH, report)
    verify_report(report, spec=spec, permit=permit)
    print(report["identity_sha256"], report["residual_classification"], flush=True)
    return 0


def _decoded_chunks(policy, preprocessor, postprocessor, raw_batch, torch):
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
    return rows


def _verify_checkpoint_config(payload: dict, *, source_run: dict) -> dict:
    verify_signed_payload(payload, label="T20.35d source checkpoint config")
    if (
        payload.get("schema_version")
        != "scenesmith.t20_35c_expert_only_checkpoint.v1"
        or payload.get("task_id") != "T20.35c"
        or payload.get("training_spec_identity_sha256")
        != source_run["training_spec_identity_sha256"]
        or payload.get("authority_decision_identity_sha256")
        != source_run["authority_decision_identity_sha256"]
        or payload.get("base_model_revision") != EXPECTED_MODEL_REVISION
        or payload.get("adaptation_mode") != ADAPTATION_MODE
        or payload.get("peft_wrapper_used") is not False
        or payload.get("train_expert_only") is not True
        or payload.get("freeze_vision_encoder") is not True
        or payload.get("trainable_prefixes") != list(TRAINABLE_PREFIXES)
        or payload.get("trainable_parameter_names")
        != source_run["trainable_parameter_names"]
        or payload.get("trainable_parameter_names_sha256")
        != source_run["trainable_parameter_names_sha256"]
        or payload.get("trainable_tensor_manifest")
        != source_run["trainable_tensor_manifest"]
        or payload.get("trainable_parameter_count")
        != source_run["trainable_parameter_count"]
        or payload.get("paligemma_trainable_parameter_count") != 0
    ):
        raise ValueError("T20.35d checkpoint config drifted")
    if verify_tensor_manifest(
        payload["trainable_tensor_manifest"],
        trainable_parameter_names=payload["trainable_parameter_names"],
    ) != payload["trainable_parameter_count"]:
        raise ValueError("T20.35d checkpoint tensor manifest accounting drifted")
    return payload


def _verify_attempt(
    payload: dict, *, spec_identity: str, permit_identity: str
) -> None:
    verify_signed_payload(payload, label="T20.35d replay attempt")
    if (
        payload.get("schema_version") != "scenesmith.t20_35d_replay_attempt.v1"
        or payload.get("task_id") != "T20.35d"
        or payload.get("evaluation_spec_identity_sha256") != spec_identity
        or payload.get("evaluation_permit_identity_sha256") != permit_identity
        or payload.get("one_replay_permit_consumed") is not True
        or payload.get("checkpoint_tree_verified") is not True
        or payload.get("model_loaded_at_marker") is not False
        or payload.get("model_inference_at_marker") is not False
        or payload.get("optimizer_created_at_marker") is not False
        or any(
            payload.get(field) is not False
            for field in (
                "optimizer_training",
                "checkpoint_mutated",
                "closed_loop_rollout",
                "physical_actuation",
                "external_compute_started",
                "brev_compute_started",
            )
        )
    ):
        raise ValueError("T20.35d replay attempt drifted")
    try:
        datetime.fromisoformat(payload["started_at"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("T20.35d replay attempt timestamp is invalid") from error


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _file_tree(root: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
                "sha256": _sha_file(path),
            }
        )
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
