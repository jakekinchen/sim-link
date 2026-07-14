#!/usr/bin/env python3
"""Write or verify the source-bound T20.12 PI0.5 gripper-channel audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.learned_action_localization import (
    verify_model_action_localization,
)
from scenesmith.robot_lab.lerobot_stack import build_stack_identity
from scenesmith.robot_lab.model_bakeoff import verify_model_training_result
from scenesmith.robot_lab.pi05_gripper_channel_audit import (
    build_pi05_gripper_channel_audit,
    load_action_statistics,
    verify_pi05_gripper_channel_audit,
)


PLAN = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
T20_11 = REPO_ROOT / "outputs/robot_lab/t20_11_action_localization/pi05.json"
TRAINING = REPO_ROOT / "outputs/robot_lab/t20_7_four_model_training_run_001/pi05/run_summary.json"
OUTPUT = REPO_ROOT / "outputs/robot_lab/t20_12_pi05_gripper_channel_audit.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    inputs = _inputs()
    payload = build_pi05_gripper_channel_audit(**inputs)
    if args.check:
        stored = load_strict_json(OUTPUT)
        verify_pi05_gripper_channel_audit(stored, **inputs)
        print("verified", OUTPUT.relative_to(REPO_ROOT), stored["identity_sha256"])
        return 0
    if OUTPUT.exists():
        raise ValueError("T20.12 audit exists; use --check")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(OUTPUT, payload)
    print("wrote", OUTPUT.relative_to(REPO_ROOT), payload["identity_sha256"])
    return 0


def _inputs() -> dict:
    plan = load_strict_json(PLAN)
    verify_signed_payload(plan, label="T20.12 source T20.7 bake-off plan")
    model = next(item for item in plan["models"] if item["model_id"] == "pi05")
    initialization = model["initialization"]
    snapshot = _snapshot(initialization["repository_id"], initialization["revision"])
    dependency = next(
        item
        for item in initialization["source_dependencies"]
        if item["repository_id"] == initialization["repository_id"]
    )
    tensor = REPO_ROOT / plan["source_tensor_view"]["path"]
    if _sha(tensor) != plan["source_tensor_view"]["file_sha256"]:
        raise ValueError("T20.12 source tensor view hash drifted")
    arrays = np.load(tensor)

    preprocessor_path = snapshot / "policy_preprocessor.json"
    postprocessor_path = snapshot / "policy_postprocessor.json"
    preprocessor = load_strict_json(preprocessor_path)
    postprocessor = load_strict_json(postprocessor_path)
    _verify_processor_configs(preprocessor, postprocessor)
    pre_stats_path = snapshot / "policy_preprocessor_step_2_normalizer_processor.safetensors"
    post_stats_path = snapshot / "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
    pre_stats = load_action_statistics(
        pre_stats_path,
        expected_sha256=dependency["files"][pre_stats_path.name],
    )
    post_stats = load_action_statistics(post_stats_path, expected_sha256=_sha(post_stats_path))
    if pre_stats != post_stats:
        raise ValueError("T20.12 pre/postprocessor action statistics disagree")

    stack = build_stack_identity(repo_root=REPO_ROOT)
    normalizer_source = REPO_ROOT / "external/lerobot/src/lerobot/processor/normalize_processor.py"
    model_source = REPO_ROOT / "external/lerobot/src/lerobot/policies/pi05/modeling_pi05.py"
    coordinate_source = REPO_ROOT / "scenesmith/robot_lab/so101_coordinates.py"
    training_source = REPO_ROOT / "scripts/robot_lab/run_t20_7_model_training.py"
    _verify_source_semantics(normalizer_source, model_source)
    t20_11 = load_strict_json(T20_11)
    verify_model_action_localization(t20_11)
    training = load_strict_json(TRAINING)
    verify_model_training_result(training, plan)
    checkpoint = (
        REPO_ROOT
        / "outputs/robot_lab/t20_7_four_model_training_run_001/pi05/checkpoint/"
        "adapter_model.safetensors"
    )
    if _sha(checkpoint) != training["checkpoint_files"][
        "checkpoint/adapter_model.safetensors"
    ]["sha256"]:
        raise ValueError("T20.12 PI0.5 checkpoint hash drifted")

    source_evidence = {
        "coordinate_contract_source": _file_evidence(coordinate_source),
        "lerobot_stack_identity": {
            "path": "composite://scenesmith.lerobot_stack_identity.v1",
            "sha256": stack["identity_sha256"],
            "kind": "composite_identity",
        },
        "loss_source": _file_evidence(model_source),
        "normalizer_source": _file_evidence(normalizer_source),
        "pi05_checkpoint": _file_evidence(checkpoint),
        "pi05_postprocessor_config": _file_evidence(
            postprocessor_path,
            display_path=_snapshot_uri(initialization, postprocessor_path.name),
        ),
        "pi05_postprocessor_statistics": _file_evidence(
            post_stats_path,
            display_path=_snapshot_uri(initialization, post_stats_path.name),
        ),
        "pi05_preprocessor_config": _file_evidence(
            preprocessor_path,
            display_path=_snapshot_uri(initialization, preprocessor_path.name),
        ),
        "pi05_preprocessor_statistics": _file_evidence(
            pre_stats_path,
            display_path=_snapshot_uri(initialization, pre_stats_path.name),
        ),
        "t20_11_pi05_localization": _file_evidence(T20_11),
        "t20_7_bakeoff_plan": _file_evidence(PLAN),
        "t20_7_pi05_training_result": _file_evidence(TRAINING),
        "t20_7_training_source": _file_evidence(training_source),
        "training_tensor_view": _file_evidence(tensor),
    }
    source_evidence["t20_11_pi05_localization"]["identity_sha256"] = t20_11[
        "identity_sha256"
    ]
    source_evidence["t20_7_bakeoff_plan"]["identity_sha256"] = plan[
        "identity_sha256"
    ]
    source_evidence["t20_7_pi05_training_result"]["identity_sha256"] = training[
        "identity_sha256"
    ]
    loss_contract = {
        "action_dimension_count": 6,
        "action_dimension_weights": [1.0] * 6,
        "gripper_dimension_weight": 1.0,
        "gripper_only_loss": False,
        "reduction": "mean_over_batch_time_and_six_action_dimensions",
        "per_dimension_aggregation_share": 1.0 / 6.0,
        "observed_loss_per_dimension_recomputed": False,
        "target_scale_proxy_is_not_observed_loss": True,
    }
    return {
        "train_action_mujoco": arrays["train_action"],
        "evaluation_action_mujoco": arrays["evaluation_action"],
        "checkpoint_action_statistics": pre_stats,
        "source_evidence": source_evidence,
        "t20_11_pi05": t20_11,
        "loss_contract": loss_contract,
    }


def _verify_processor_configs(preprocessor: dict, postprocessor: dict) -> None:
    pre_steps = preprocessor.get("steps", [])
    post_steps = postprocessor.get("steps", [])
    if (
        len(pre_steps) != 6
        or pre_steps[2].get("registry_name") != "normalizer_processor"
        or pre_steps[2].get("config", {}).get("norm_map", {}).get("ACTION")
        != "MEAN_STD"
        or pre_steps[2].get("config", {}).get("eps") != 1e-8
        or len(post_steps) != 2
        or post_steps[0].get("registry_name") != "unnormalizer_processor"
        or post_steps[0].get("config", {}).get("norm_map", {}).get("ACTION")
        != "MEAN_STD"
        or post_steps[0].get("config", {}).get("eps") != 1e-8
    ):
        raise ValueError("T20.12 PI0.5 pre/postprocessor semantics drifted")


def _verify_source_semantics(normalizer: Path, model: Path) -> None:
    normalizer_text = normalizer.read_text(encoding="utf-8")
    model_text = model.read_text(encoding="utf-8")
    required_normalizer = (
        "return (tensor - mean) / denom",
        "return tensor * std + mean",
    )
    required_model = (
        'os.environ.get("SCENESMITH_GRIPPER_LOSS_WEIGHT", "1")',
        'os.environ.get("SCENESMITH_GRIPPER_ONLY_LOSS", "0") == "1"',
        "loss = losses.mean()",
    )
    if any(item not in normalizer_text for item in required_normalizer) or any(
        item not in model_text for item in required_model
    ):
        raise ValueError("T20.12 processor or loss source semantics drifted")


def _snapshot(repository_id: str, revision: str) -> Path:
    return (
        Path.home()
        / ".cache/huggingface/hub"
        / ("models--" + repository_id.replace("/", "--"))
        / "snapshots"
        / revision
    )


def _snapshot_uri(initialization: dict, filename: str) -> str:
    return (
        f"hf://{initialization['repository_id']}@{initialization['revision']}/{filename}"
    )


def _file_evidence(path: Path, *, display_path: str | None = None) -> dict[str, str]:
    if display_path is None:
        relative = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        display_path = str(relative)
    return {"path": display_path, "sha256": _sha(path)}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
