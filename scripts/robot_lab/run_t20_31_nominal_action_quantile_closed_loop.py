#!/usr/bin/env python3
"""Evaluate the frozen T20.31 adapter on held-out seeds 6 and 7."""

from __future__ import annotations

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
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.grasp_evidence import (  # noqa: E402
    validate_rendered_keyframes,
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
from scenesmith.robot_lab.t20_17_clean_base_preflight import (  # noqa: E402
    EXPECTED_MODEL_REVISION,
    SOURCE_MANIFEST_PATH,
    TASK,
)
from scenesmith.robot_lab.t20_30_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)
from scenesmith.robot_lab.t20_31_nominal_action_quantile_campaign import (  # noqa: E402
    HELD_OUT_SEEDS,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    verify_run_summary,
)


INFERENCE_SEEDS = {6: 20260714, 7: 20260715}
ACTION_HORIZON = 5
SCHEMA_VERSION = "scenesmith.t20_31_nominal_action_quantile_closed_loop.v1"


def main() -> int:
    outputs = {
        seed: REPO_ROOT / RUN_ROOT / f"held_out_seed_{seed}_closed_loop.json"
        for seed in HELD_OUT_SEEDS
    }
    if any(path.exists() for path in outputs.values()):
        raise FileExistsError("T20.31 held-out evaluation output already exists")
    stack = activate_lerobot_stack(repo_root=REPO_ROOT, stage="inference")
    require_active_authority(repo_root=REPO_ROOT)
    run_root = REPO_ROOT / RUN_ROOT
    summary_path = run_root / RUN_SUMMARY_PATH
    summary = load_strict_json(summary_path)
    verify_signed_payload(summary, label="T20.31 training run")
    verify_run_summary(summary)
    checkpoint = run_root / "training/checkpoints/last/pretrained_model"
    _verify_checkpoint(checkpoint, summary)
    manifest = load_strict_json(REPO_ROOT / SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    source_entries = {
        seed: next(row for row in manifest["episodes"] if row["seed"] == seed)
        for seed in HELD_OUT_SEEDS
    }
    if any(
        row["outcome"]["strict_success"] is not True
        for row in source_entries.values()
    ):
        raise ValueError("T20.31 held-out source is not strict-success evidence")

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
        raise RuntimeError("T20.31 evaluation requires local MPS")
    config = PreTrainedConfig.from_pretrained(checkpoint, local_files_only=True)
    snapshot = Path(config.pretrained_path).resolve()
    if snapshot.name != EXPECTED_MODEL_REVISION or not (
        snapshot / "model.safetensors"
    ).is_file():
        raise ValueError("T20.31 evaluation base snapshot drifted")
    config.device = "mps"
    config.dtype = "float32"
    config.use_amp = False
    config.compile_model = False
    config.n_action_steps = ACTION_HORIZON
    policy_class = get_policy_class(config.type)
    base = policy_class.from_pretrained(
        snapshot, config=config, local_files_only=True, strict=True
    )
    peft_config = PeftConfig.from_pretrained(checkpoint, local_files_only=True)
    if Path(peft_config.base_model_name_or_path).resolve() != snapshot:
        raise ValueError("T20.31 adapter base-model binding drifted")
    policy = PeftModel.from_pretrained(
        base,
        checkpoint,
        config=peft_config,
        is_trainable=False,
        local_files_only=True,
    ).to("mps").eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=config,
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
        torch.manual_seed(INFERENCE_SEEDS[seed])
        policy.reset()

        def policy_action(
            images: dict[str, np.ndarray], state: np.ndarray
        ) -> np.ndarray:
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
                normalized = policy.select_action(preprocessor(prepared))
                canonical = postprocessor(normalized)
            values = canonical.detach().cpu().float().numpy().reshape(-1)
            if values.shape != (6,) or not np.isfinite(values).all():
                raise ValueError("T20.31 candidate emitted an invalid action")
            return np.asarray(
                lerobot_to_mujoco(values.tolist()), dtype=np.float64
            )

        rollout = run_policy_grasp_closed_loop(
            policy_action,
            checkpoint_sha256=adapter_sha,
            training_run_summary_sha256=_sha(summary_path),
            seed=seed,
            schema_version=SCHEMA_VERSION,
            task_id="T20.31",
            evidence_mode=f"nominal_action_quantile_seed_{seed}_unassisted",
            policy_label="pi05_nominal_action_quantile_lora_rank4",
            release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        )
        if rollout.get("seed") != seed:
            raise ValueError("T20.31 rollout seed binding drifted")
        if any(
            rollout.get(key) != 0
            for key in ("projected_action_frame_count", "active_assist_frame_count")
        ):
            raise ValueError("T20.31 rollout used projection or assistance")
        validate_rendered_keyframes(rollout["rendered_keyframes"])
        source = source_entries[seed]
        payload = sign_payload(
            {
                "schema_version": SCHEMA_VERSION,
                "task_id": "T20.31",
                "held_out_seed": seed,
                "source_training_identity_sha256": summary["identity_sha256"],
                "source_training_file_sha256": _sha(summary_path),
                "source_episode_file_sha256": source["episode_file_sha256"],
                "source_episode_raw_rollout_identity_sha256": source[
                    "raw_rollout_record_identity_sha256"
                ],
                "closed_loop": rollout,
                "policy_runtime": {
                    "device": "mps",
                    "dtype": "float32",
                    "offline": True,
                    "inference_seed": INFERENCE_SEEDS[seed],
                    "action_horizon": ACTION_HORIZON,
                    "base_revision": EXPECTED_MODEL_REVISION,
                    "lerobot_stack_identity_sha256": stack["identity_sha256"],
                },
                "model_inference_executed": True,
                "optimizer_training": False,
                "simulation_policy_accepted": False,
                "physical_actuation": False,
                "external_compute_started": False,
                "brev_compute_started": False,
                "physical_transfer_ready": False,
                "promotion_eligible": False,
            }
        )
        dump_canonical_json(outputs[seed], payload)
        print(
            payload["identity_sha256"],
            seed,
            rollout["simulation_semantic_strict_success"],
            rollout["maximum_anchor_lift_m"],
            rollout["terminal_outcome"],
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
            raise ValueError(f"T20.31 checkpoint file drifted: {row['path']}")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
