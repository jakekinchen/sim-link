#!/usr/bin/env python3
"""Capture T20.25 source-relative traces for one frozen candidate on seeds 6-7."""

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
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.scripted_grasp_episode_generation import (  # noqa: E402
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.so101_coordinates import (  # noqa: E402
    lerobot_to_mujoco,
    mujoco_to_lerobot,
)
from scenesmith.robot_lab.t20_17_clean_base_campaign import (  # noqa: E402
    verify_run_summary as verify_clean_summary,
)
from scenesmith.robot_lab.t20_17_clean_base_preflight import (  # noqa: E402
    EXPECTED_MODEL_REVISION,
    SOURCE_MANIFEST_PATH,
    TASK,
)
from scenesmith.robot_lab.t20_17_simulation_training_authority import (  # noqa: E402
    require_active_t20_17_authority,
)
from scenesmith.robot_lab.t20_23_simulation_training_authority import (  # noqa: E402
    require_active_t20_23_authority,
)
from scenesmith.robot_lab.t20_24_recovery_augmented_campaign import (  # noqa: E402
    verify_run_summary as verify_recovery_summary,
)
from scenesmith.robot_lab.t20_25_frozen_candidate_localization import (  # noqa: E402
    CANDIDATE_IDS,
    HELD_OUT_SEEDS,
    build_comparison_rows,
    build_trace_payload,
)


OUTPUT_ROOT = REPO_ROOT / "outputs/robot_lab/t20_25_frozen_candidate_localization"
INFERENCE_SEEDS = {6: 20260714, 7: 20260715}
ACTION_HORIZON = 5
CANDIDATE_CONFIG = {
    "clean_base": {
        "run_root": REPO_ROOT / "outputs/robot_lab/t20_17_clean_base_run_002",
        "summary_verifier": verify_clean_summary,
        "authority": require_active_t20_17_authority,
        "policy_label": "pi05_clean_base_lora_rank4",
        "prior_evaluations": {
            6: REPO_ROOT
            / "outputs/robot_lab/t20_17_clean_base_run_002/held_out_seed_6_closed_loop.json",
        },
    },
    "recovery_augmented": {
        "run_root": REPO_ROOT / "outputs/robot_lab/t20_24_recovery_augmented_run_002",
        "summary_verifier": verify_recovery_summary,
        "authority": require_active_t20_23_authority,
        "policy_label": "pi05_recovery_augmented_lora_rank4",
        "prior_evaluations": {
            seed: REPO_ROOT
            / "outputs/robot_lab/t20_24_recovery_augmented_run_002"
            / f"held_out_seed_{seed}_closed_loop.json"
            for seed in HELD_OUT_SEEDS
        },
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATE_IDS)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    config = CANDIDATE_CONFIG[args.candidate]
    outputs = {
        seed: OUTPUT_ROOT / f"{args.candidate}_seed_{seed}.json" for seed in HELD_OUT_SEEDS
    }
    if args.verify:
        from scenesmith.robot_lab.t20_25_frozen_candidate_localization import verify_trace_payload
        for path in outputs.values():
            verify_trace_payload(load_strict_json(path))
        print(args.candidate, "verified", flush=True)
        return 0
    if any(path.exists() for path in outputs.values()):
        raise FileExistsError("T20.25 candidate trace output already exists")

    activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    config["authority"](repo_root=REPO_ROOT)
    run_root: Path = config["run_root"]
    summary_path = run_root / "run_summary.json"
    summary = load_strict_json(summary_path)
    verify_signed_payload(summary, label=f"T20.25 {args.candidate} training summary")
    config["summary_verifier"](summary)
    checkpoint = run_root / "training/checkpoints/last/pretrained_model"
    _verify_checkpoint(checkpoint, summary)

    manifest = load_strict_json(REPO_ROOT / SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    sources = {
        seed: next(row for row in manifest["episodes"] if row["seed"] == seed)
        for seed in HELD_OUT_SEEDS
    }
    if any(row["outcome"]["strict_success"] is not True for row in sources.values()):
        raise ValueError("T20.25 held-out source episode is not strict-success evidence")

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
        raise RuntimeError("T20.25 frozen-candidate localization requires local MPS")
    policy_config = PreTrainedConfig.from_pretrained(checkpoint, local_files_only=True)
    snapshot = Path(policy_config.pretrained_path).resolve()
    if snapshot.name != EXPECTED_MODEL_REVISION or not (snapshot / "model.safetensors").is_file():
        raise ValueError("T20.25 base snapshot binding drifted")
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
        raise ValueError("T20.25 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base, checkpoint, config=peft_config, is_trainable=False, local_files_only=True
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

    for seed in HELD_OUT_SEEDS:
        source_entry = sources[seed]
        source_path = default_store_root() / source_entry["relative_path"]
        source_episode = load_strict_json(source_path)
        torch.manual_seed(INFERENCE_SEEDS[seed])
        policy.reset()
        observed: list[dict[str, Any]] = []

        def policy_action(images: dict[str, np.ndarray], state: np.ndarray) -> np.ndarray:
            raw = {
                "observation.images.base_0_rgb": images["top"].copy(),
                "observation.images.left_wrist_0_rgb": images["wrist"].copy(),
                "observation.state": np.asarray(mujoco_to_lerobot(state[:6]), dtype=np.float32),
            }
            prepared = prepare_observation_for_inference(
                raw, torch.device("mps"), task=TASK, robot_type="so101_follower"
            )
            with torch.inference_mode():
                canonical = postprocessor(policy.select_action(preprocessor(prepared)))
            values = canonical.detach().cpu().float().numpy().reshape(-1)
            if values.shape != (6,) or not np.isfinite(values).all():
                raise ValueError("T20.25 candidate emitted an invalid action")
            return np.asarray(lerobot_to_mujoco(values.tolist()), dtype=np.float64)

        rollout = run_policy_grasp_closed_loop(
            policy_action,
            checkpoint_sha256=adapter_sha,
            training_run_summary_sha256=_sha(summary_path),
            seed=seed,
            schema_version="scenesmith.t20_25_frozen_candidate_closed_loop.v1",
            task_id="T20.25",
            evidence_mode=f"{args.candidate}_held_out_seed_{seed}_action_state_localization",
            policy_label=config["policy_label"],
            frame_observer=observed.append,
            release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        )
        if (
            rollout["projected_action_frame_count"] != 0
            or rollout["active_assist_frame_count"] != 0
        ):
            raise ValueError("T20.25 candidate used projection or assistance")
        prior_path = config["prior_evaluations"].get(seed)
        if prior_path is not None:
            prior = load_strict_json(prior_path)
            verify_signed_payload(prior, label="T20.25 prior frozen evaluation")
            if (
                prior["closed_loop"]["policy_action_sequence_sha256"]
                != rollout["policy_action_sequence_sha256"]
            ):
                raise ValueError("T20.25 frozen candidate did not reproduce prior action sequence")
        rows = build_comparison_rows(source_episode["frames"], observed)
        trace = build_trace_payload(
            candidate_id=args.candidate,
            seed=seed,
            source_episode_file_sha256=source_entry["episode_file_sha256"],
            source_episode_identity_sha256=source_entry["raw_rollout_record_identity_sha256"],
            training_identity_sha256=summary["identity_sha256"],
            checkpoint_sha256=adapter_sha,
            rows=rows,
            closed_loop=rollout,
        )
        dump_canonical_json(outputs[seed], trace)
        d = trace["diagnostics"]
        print(
            args.candidate,
            seed,
            trace["identity_sha256"],
            d["frame_zero_action_mean_absolute_error_rad"],
            d["precontact_action_mean_absolute_error_rad"],
            flush=True,
        )
    return 0


def _verify_checkpoint(checkpoint: Path, summary: dict[str, Any]) -> None:
    for row in summary["checkpoint_tree"]:
        path = checkpoint / row["path"]
        if (
            not path.is_file()
            or path.stat().st_size != row["size_bytes"]
            or _sha(path) != row["sha256"]
        ):
            raise ValueError(f"T20.25 checkpoint file drifted: {row['path']}")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
