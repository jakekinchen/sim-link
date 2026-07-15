#!/usr/bin/env python3
"""Run or verify optimizer-free T20.34 Gate B plumbing localization."""

from __future__ import annotations

import argparse
import copy
import math
import os
import sys

from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
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
    RESULT_PATH,
    verify_preflight,
    verify_result,
    verify_run,
    verify_training_spec_file,
)
from scenesmith.robot_lab.t20_34_gate_b_plumbing_localization import (  # noqa: E402
    OUTPUT_PATH,
    build_report,
    verify_report,
)
from scripts.robot_lab.run_t20_33_one_batch_memorization import (  # noqa: E402
    RUN_ROOT,
    SUMMARY_PATH,
)


OUTPUT = REPO_ROOT / OUTPUT_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    spec = verify_training_spec_file(repo_root=REPO_ROOT)
    prior_run = load_strict_json(SUMMARY_PATH)
    verify_run(
        prior_run,
        spec=spec,
        authority_identity=prior_run["authority_decision_identity_sha256"],
    )
    prior_result = load_strict_json(REPO_ROOT / RESULT_PATH)
    verify_result(prior_result, spec=spec, run=prior_run)
    if args.verify:
        report = load_strict_json(OUTPUT)
        verify_report(report, spec=spec, prior_run=prior_run)
        print(report["identity_sha256"], report["selected_next_hypothesis"])
        return 0
    if OUTPUT.exists():
        raise FileExistsError("T20.34 report already exists; use --verify")

    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.datasets import LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.datasets.factory import resolve_delta_timestamps
    from lerobot.policies import make_policy, make_pre_post_processors
    from peft import PeftConfig, PeftModel
    from safetensors import safe_open
    from torch.utils.data import default_collate

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.34 requires local MPS for exact frozen replay")
    adapter_root = RUN_ROOT / "adapter"
    adapter_path = adapter_root / "adapter_model.safetensors"
    adapter_tensors = _adapter_tensor_evidence(adapter_path, safe_open)
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
    dataset_target = np.asarray(
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
    if not np.allclose(dataset_target, source_target, rtol=0.0, atol=1e-5):
        raise ValueError("T20.34 dataset batch substituted the T20.33 source target")
    base = make_policy(config, ds_meta=dataset.meta).eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=snapshot,
        dataset_stats=dataset.meta.stats,
        preprocessor_overrides={
            "device_processor": {"device": "mps"},
            "normalizer_processor": {
                "stats": dataset.meta.stats,
                "features": {**base.config.input_features, **base.config.output_features},
                "norm_map": base.config.normalization_mapping,
            },
        },
        postprocessor_overrides={
            "unnormalizer_processor": {
                "stats": dataset.meta.stats,
                "features": base.config.output_features,
                "norm_map": base.config.normalization_mapping,
            }
        },
    )
    for key in dataset.meta.camera_keys:
        if raw_batch[key].dtype == torch.uint8:
            raw_batch[key] = raw_batch[key].float().div(255.0)
    batch = preprocessor(copy.deepcopy(raw_batch))
    observation = preprocessor(
        {
            key: copy.deepcopy(value)
            for key, value in raw_batch.items()
            if key != "action" and not key.startswith("action_")
        }
    )
    base_objective = _objective_mean(base, batch, torch)
    base_chunks = _decode(base, observation, postprocessor, torch)
    peft_config = PeftConfig.from_pretrained(adapter_root, local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot:
        raise ValueError("T20.34 adapter base-model binding drifted")
    adapter = PeftModel.from_pretrained(
        base,
        adapter_root,
        config=peft_config,
        is_trainable=False,
        local_files_only=True,
    ).to("mps").eval()
    adapter_objective = _objective_mean(adapter, batch, torch)
    adapter_chunks = _decode(adapter, observation, postprocessor, torch)
    evidence = {
        "source_target_action_rad": source_target.astype(float).tolist(),
        "base_decoded_chunks_rad": base_chunks,
        "adapter_decoded_chunks_rad": adapter_chunks,
        "adapter_tensors": adapter_tensors,
        "base_objective_mean": base_objective,
        "adapter_objective_mean": adapter_objective,
    }
    report = build_report(spec=spec, prior_run=prior_run, evidence=evidence)
    dump_canonical_json(OUTPUT, report)
    print(report["identity_sha256"], report["selected_next_hypothesis"])
    return 0


def _objective_mean(policy, batch, torch) -> float:
    values = []
    policy.eval()
    with torch.no_grad():
        for seed in INFERENCE_SEEDS:
            torch.manual_seed(seed)
            loss, _ = policy(batch)
            if not torch.isfinite(loss):
                raise ValueError("T20.34 observed a non-finite objective")
            values.append(float(loss.detach().cpu()))
    return float(sum(values) / len(values))


def _decode(policy, observation, postprocessor, torch):
    result = []
    policy.eval()
    with torch.no_grad():
        for seed in INFERENCE_SEEDS:
            torch.manual_seed(seed)
            policy.reset()
            actions = []
            for _ in range(ACTION_HORIZON):
                canonical = postprocessor(policy.select_action(observation))
                values = canonical.detach().cpu().float().numpy().reshape(-1)
                converted = lerobot_to_mujoco(values.tolist())
                if len(converted) != 6 or not all(math.isfinite(value) for value in converted):
                    raise ValueError("T20.34 decoded a non-finite or wrong-shaped action")
                actions.append(converted)
            result.append({"inference_seed": seed, "actions": actions})
    return result


def _adapter_tensor_evidence(path: Path, safe_open) -> list[dict[str, object]]:
    rows = []
    with safe_open(path, framework="pt", device="cpu") as handle:
        for name in handle.keys():
            tensor = handle.get_tensor(name).float()
            if not tensor.isfinite().all().item():
                raise ValueError("T20.34 adapter contains a non-finite tensor")
            rows.append(
                {
                    "name": name,
                    "value_count": tensor.numel(),
                    "nonzero_count": int(torch_count_nonzero(tensor)),
                    "l2_norm": float(tensor.norm()),
                    "maximum_absolute_value": float(tensor.abs().max()),
                }
            )
    if not rows:
        raise ValueError("T20.34 adapter tensor file is empty")
    return rows


def torch_count_nonzero(tensor) -> int:
    return int((tensor != 0).sum().item())


if __name__ == "__main__":
    raise SystemExit(main())
