#!/usr/bin/env python3
"""Capture complete T20.32 traces for one frozen adapter on seeds 0, 6, and 7."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys

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
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.geometry_derived_grasp_primitives import (  # noqa: E402
    has_valid_antipodal_contact,
)
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
    EXPECTED_MODEL_REVISION,
    SOURCE_MANIFEST_PATH,
    TASK,
)
from scenesmith.robot_lab.t20_23_simulation_training_authority import (  # noqa: E402
    require_active_t20_23_authority,
)
from scenesmith.robot_lab.t20_24_recovery_augmented_campaign import (  # noqa: E402
    verify_run_summary as verify_t20_24_summary,
)
from scenesmith.robot_lab.t20_30_simulation_training_authority import (  # noqa: E402
    require_active_authority as require_active_t20_30_authority,
)
from scenesmith.robot_lab.t20_31_nominal_action_quantile_campaign import (  # noqa: E402
    verify_run_summary as verify_t20_31_summary,
)
from scenesmith.robot_lab.t20_32_closed_loop_divergence import (  # noqa: E402
    ACTION_HORIZON,
    ADAPTER_IDS,
    ALL_SEEDS,
    build_comparison_rows,
    build_trace_payload,
    verify_threshold_contract,
    verify_trace_payload,
)
from scripts.robot_lab.materialize_t20_32_divergence_thresholds import (  # noqa: E402
    OUTPUT_PATH as THRESHOLD_PATH,
)


OUTPUT_ROOT = REPO_ROOT / "outputs/robot_lab/t20_32_closed_loop_divergence"
INFERENCE_SEEDS = {0: 20260716, 6: 20260714, 7: 20260715}
ADAPTER_CONFIG = {
    "t20_24_recovery_augmented": {
        "run_root": REPO_ROOT / "outputs/robot_lab/t20_24_recovery_augmented_run_002",
        "summary_verifier": verify_t20_24_summary,
        "authority": require_active_t20_23_authority,
        "policy_label": "pi05_recovery_augmented_lora_rank4",
        "prior_evaluations": {
            seed: REPO_ROOT
            / "outputs/robot_lab/t20_24_recovery_augmented_run_002"
            / f"held_out_seed_{seed}_closed_loop.json"
            for seed in (6, 7)
        },
    },
    "t20_31_nominal_action_quantile": {
        "run_root": REPO_ROOT / "outputs/robot_lab/t20_31_nominal_action_quantile_run_001",
        "summary_verifier": verify_t20_31_summary,
        "authority": require_active_t20_30_authority,
        "policy_label": "pi05_nominal_action_quantile_lora_rank4",
        "prior_evaluations": {
            seed: REPO_ROOT
            / "outputs/robot_lab/t20_31_nominal_action_quantile_run_001"
            / f"held_out_seed_{seed}_closed_loop.json"
            for seed in (6, 7)
        },
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", required=True, choices=ADAPTER_IDS)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    config = ADAPTER_CONFIG[args.adapter]
    outputs = {
        seed: OUTPUT_ROOT / f"{args.adapter}_seed_{seed}.json" for seed in ALL_SEEDS
    }
    threshold = load_strict_json(THRESHOLD_PATH)
    verify_threshold_contract(threshold)
    if args.verify:
        for path in outputs.values():
            verify_trace_payload(load_strict_json(path), threshold=threshold)
        print(args.adapter, "T20.32 traces verified")
        return 0
    if any(path.exists() for path in outputs.values()):
        raise FileExistsError("T20.32 adapter trace already exists; use --verify")

    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    config["authority"](repo_root=REPO_ROOT)
    run_root: Path = config["run_root"]
    summary_path = run_root / "run_summary.json"
    summary = load_strict_json(summary_path)
    verify_signed_payload(summary, label=f"T20.32 {args.adapter} training summary")
    config["summary_verifier"](summary)
    checkpoint = run_root / "training/checkpoints/last/pretrained_model"
    _verify_checkpoint(checkpoint, summary)

    manifest = load_strict_json(REPO_ROOT / SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    sources = {
        seed: next(row for row in manifest["episodes"] if row["seed"] == seed)
        for seed in ALL_SEEDS
    }
    if any(row["outcome"]["strict_success"] is not True for row in sources.values()):
        raise ValueError("T20.32 source episode is not strict-success evidence")

    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    import torch
    import lerobot.policies.pi05.processor_pi05  # noqa: F401
    from lerobot.configs import PreTrainedConfig
    from lerobot.policies import get_policy_class, make_pre_post_processors
    from lerobot.policies.utils import prepare_observation_for_inference
    from peft import PeftConfig, PeftModel

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.32 frozen-adapter localization requires local MPS")
    policy_config = PreTrainedConfig.from_pretrained(checkpoint, local_files_only=True)
    snapshot = Path(policy_config.pretrained_path).resolve()
    if snapshot.name != EXPECTED_MODEL_REVISION or not (
        snapshot / "model.safetensors"
    ).is_file():
        raise ValueError("T20.32 base snapshot binding drifted")
    policy_config.device = "mps"
    policy_config.dtype = "float32"
    policy_config.use_amp = False
    policy_config.compile_model = False
    policy_config.n_action_steps = ACTION_HORIZON
    base = get_policy_class(policy_config.type).from_pretrained(
        snapshot, config=policy_config, local_files_only=True, strict=True
    )
    peft_config = PeftConfig.from_pretrained(checkpoint, local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot:
        raise ValueError("T20.32 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base,
        checkpoint,
        config=peft_config,
        is_trainable=False,
        local_files_only=True,
    ).to("mps").eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy_config,
        pretrained_path=checkpoint,
        preprocessor_overrides={"device_processor": {"device": "mps"}},
        postprocessor_overrides={"device_processor": {"device": "cpu"}},
    )
    adapter_sha = next(
        row["sha256"]
        for row in summary["checkpoint_tree"]
        if row["path"] == "adapter_model.safetensors"
    )

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
            raise ValueError("T20.32 frozen adapter emitted an invalid action")
        return np.asarray(lerobot_to_mujoco(values.tolist()), dtype=np.float64)

    contact_requirement = strict_grasp_spec_v2()["antipodal_contact_requirement"]
    for seed in ALL_SEEDS:
        source_entry = sources[seed]
        source_episode = load_strict_json(
            default_store_root() / source_entry["relative_path"]
        )
        torch.manual_seed(INFERENCE_SEEDS[seed])
        policy.reset()
        observed: list[dict[str, Any]] = []
        rollout = run_policy_grasp_closed_loop(
            select_action,
            checkpoint_sha256=adapter_sha,
            training_run_summary_sha256=_sha(summary_path),
            seed=seed,
            schema_version="scenesmith.t20_32_closed_loop_probe.v1",
            task_id="T20.32",
            evidence_mode=f"{args.adapter}_seed_{seed}_complete_trace",
            policy_label=config["policy_label"],
            frame_observer=observed.append,
            release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        )
        for row in observed:
            row["t20_32_strict_contact"] = has_valid_antipodal_contact(
                row, contact_requirement
            )
        prior_identity = None
        prior_action_sha = None
        prior_path = config["prior_evaluations"].get(seed)
        if prior_path is not None:
            prior = load_strict_json(prior_path)
            verify_signed_payload(prior, label="T20.32 prior frozen evaluation")
            prior_identity = prior["identity_sha256"]
            prior_action_sha = prior["closed_loop"]["policy_action_sequence_sha256"]
        trace = build_trace_payload(
            threshold=threshold,
            adapter_id=args.adapter,
            seed=seed,
            inference_seed=INFERENCE_SEEDS[seed],
            source_episode_file_sha256=source_entry["episode_file_sha256"],
            source_episode_identity_sha256=source_entry[
                "raw_rollout_record_identity_sha256"
            ],
            training_identity_sha256=summary["identity_sha256"],
            checkpoint_sha256=adapter_sha,
            rows=build_comparison_rows(source_episode["frames"], observed),
            closed_loop=rollout,
            prior_evaluation_identity_sha256=prior_identity,
            prior_action_sequence_sha256=prior_action_sha,
        )
        dump_canonical_json(outputs[seed], trace)
        print(
            args.adapter,
            seed,
            trace["identity_sha256"],
            trace["diagnostics"]["divergence_class"],
            trace["closed_loop"]["simulation_semantic_strict_success"],
            flush=True,
        )
    print("lerobot_stack", stack["identity_sha256"], flush=True)
    return 0


def _verify_checkpoint(checkpoint: Path, summary: dict[str, Any]) -> None:
    for row in summary["checkpoint_tree"]:
        path = checkpoint / row["path"]
        if (
            not path.is_file()
            or path.stat().st_size != row["size_bytes"]
            or _sha(path) != row["sha256"]
        ):
            raise ValueError(f"T20.32 checkpoint file drifted: {row['path']}")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
