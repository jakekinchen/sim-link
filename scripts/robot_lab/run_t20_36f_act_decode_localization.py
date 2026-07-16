#!/usr/bin/env python3
"""Run or verify the authorized T20.36f ACT decode localization."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import subprocess
import sys

from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack  # noqa: E402
from scenesmith.robot_lab.so101_coordinates import lerobot_to_mujoco  # noqa: E402
from scenesmith.robot_lab.t20_36e_act_batch import load_exact_batch  # noqa: E402
from scenesmith.robot_lab.t20_36f_act_decode_localization import (  # noqa: E402
    ATTEMPT_PATH,
    DIRECT_QUEUE_TOLERANCE,
    EXPECTED_CHECKPOINT_TREE,
    EXPECTED_FINAL_ACTION_HASH,
    EXPECTED_FINAL_OBJECTIVE,
    INFERENCE_PERMIT_PATH,
    JOINT_NAMES,
    PHYSICAL_THRESHOLD_RAD,
    RESULT_PATH,
    RUN_ROOT,
    RUNTIME_PREFLIGHT_PATH,
    SOURCE_CHECKPOINT_ROOT,
    TIME_REGIONS,
    build_attempt_marker,
    build_result,
    checkpoint_tree,
    load_verified_sources,
    verify_attempt_marker,
    verify_inference_permit,
    verify_result,
    verify_runtime_preflight,
)
from scenesmith.robot_lab.t20_36f_simulation_inference_authority import (  # noqa: E402
    require_active_authority,
    verify_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_verified_sources(repo_root=REPO_ROOT)
    authority = (
        verify_authority(repo_root=REPO_ROOT)
        if args.verify
        else require_active_authority(repo_root=REPO_ROOT)
    )
    authority_identity = authority["decision"]["identity_sha256"]
    runtime = load_strict_json(REPO_ROOT / RUNTIME_PREFLIGHT_PATH)
    verify_runtime_preflight(
        runtime,
        sources=sources,
        authority_identity=authority_identity,
    )
    permit = load_strict_json(REPO_ROOT / INFERENCE_PERMIT_PATH)
    verify_inference_permit(
        permit,
        sources=sources,
        authority_identity=authority_identity,
        runtime_preflight=runtime,
    )
    if args.verify:
        attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
        verify_attempt_marker(
            attempt, permit=permit, authority_identity=authority_identity
        )
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_result(result, permit=permit, attempt=attempt)
        if (
            checkpoint_tree(REPO_ROOT / SOURCE_CHECKPOINT_ROOT)
            != EXPECTED_CHECKPOINT_TREE
        ):
            raise ValueError("T20.36f source checkpoint drifted")
        print(result["identity_sha256"])
        return 0
    if (REPO_ROOT / RUN_ROOT).exists() or (REPO_ROOT / RESULT_PATH).exists():
        raise FileExistsError("T20.36f immutable attempt already exists")
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
    if stack["identity_sha256"] != runtime["lerobot_stack_identity_sha256"]:
        raise ValueError("T20.36f LeRobot stack drifted")
    batch_source = load_exact_batch(repo_root=REPO_ROOT, spec=sources["spec"])
    current_commit = _git("rev-parse", "HEAD")
    attempt = build_attempt_marker(
        permit=permit,
        authority_identity=authority_identity,
        source_commit=current_commit,
    )
    (REPO_ROOT / RUN_ROOT).mkdir(parents=True, exist_ok=False)
    dump_canonical_json(REPO_ROOT / ATTEMPT_PATH, attempt)

    import torch

    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.act.processor_act import make_act_pre_post_processors
    from torch.utils.data import default_collate

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.36f requires the authorized local MPS runtime")
    policy = ACTPolicy.from_pretrained(
        REPO_ROOT / SOURCE_CHECKPOINT_ROOT,
        local_files_only=True,
    ).to("mps")
    policy.eval()
    preprocessor, postprocessor = make_act_pre_post_processors(
        policy.config, dataset_stats=batch_source["dataset"].meta.stats
    )
    raw_batch = default_collate([batch_source["item"]])
    processed = preprocessor(copy.deepcopy(raw_batch))
    observation = {
        key: copy.deepcopy(value)
        for key, value in raw_batch.items()
        if key.startswith("observation.")
    }
    processed_observation = preprocessor(observation)
    with torch.no_grad():
        objective, _ = policy(processed)
        direct_normalized = policy.predict_action_chunk(processed_observation)
    reproduced_objective = float(objective.detach().cpu())
    if abs(reproduced_objective - EXPECTED_FINAL_OBJECTIVE) > 1e-7:
        raise ValueError("T20.36f final objective did not reproduce")
    direct_lerobot = postprocessor(direct_normalized).numpy()[0]
    direct_physical = _physical(direct_lerobot)
    direct_hash = _hash_matrix(direct_physical)
    repetitions = []
    queue_normalized = None
    queue_physical = None
    with torch.no_grad():
        for _ in range(5):
            policy.reset()
            actions = [
                policy.select_action(processed_observation) for _ in range(50)
            ]
            current_queue = torch.stack(actions, dim=1)
            current_lerobot = postprocessor(current_queue).numpy()[0]
            current_physical = _physical(current_lerobot)
            repetitions.append(_hash_matrix(current_physical))
            if queue_normalized is None:
                queue_normalized = current_queue.detach().cpu().numpy()[0]
                queue_physical = current_physical
    if set(repetitions) != {EXPECTED_FINAL_ACTION_HASH}:
        raise ValueError("T20.36f queued action hash did not reproduce")
    if direct_hash != EXPECTED_FINAL_ACTION_HASH:
        raise ValueError("T20.36f direct action hash differs from source queue")
    direct_queue_error = float(np.max(np.abs(direct_physical - queue_physical)))
    if direct_queue_error > DIRECT_QUEUE_TOLERANCE:
        raise ValueError("T20.36f direct and queued decodes differ")
    target_normalized = processed["action"].detach().cpu().numpy()[0]
    normalized_error = np.abs(queue_normalized - target_normalized)
    physical_error = np.abs(queue_physical - batch_source["physical_action"])
    maximum_index = np.unravel_index(np.argmax(physical_error), physical_error.shape)
    result = build_result(
        permit=permit,
        attempt=attempt,
        reproduced_objective=reproduced_objective,
        repetition_action_hashes=repetitions,
        direct_action_hash=direct_hash,
        direct_queue_maximum_error_rad=direct_queue_error,
        normalized_per_joint=_joint_rows(normalized_error, physical=False),
        physical_per_joint=_joint_rows(physical_error, physical=True),
        time_regions=_time_rows(physical_error),
        maximum_error={
            "joint_name": JOINT_NAMES[maximum_index[1]],
            "timestep": int(maximum_index[0]),
            "predicted_action": float(queue_physical[maximum_index]),
            "target_action": float(batch_source["physical_action"][maximum_index]),
            "absolute_error_rad": float(physical_error[maximum_index]),
        },
    )
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    verify_result(result, permit=permit, attempt=attempt)
    print(result["identity_sha256"])
    return 0


def _physical(lerobot_matrix):
    return np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in lerobot_matrix],
        dtype=np.float64,
    )


def _hash_matrix(matrix) -> str:
    return hashlib.sha256(
        canonical_json_bytes(matrix.astype(float).tolist())
    ).hexdigest()


def _joint_rows(error, *, physical: bool):
    rows = []
    for index, name in enumerate(JOINT_NAMES):
        values = error[:, index]
        row = {
            "joint_name": name,
            "mean_absolute_error": float(np.mean(values)),
            "maximum_absolute_error": float(np.max(values)),
            "maximum_error_timestep": int(np.argmax(values)),
        }
        if physical:
            row["threshold_exceedance_count"] = int(
                np.count_nonzero(values > PHYSICAL_THRESHOLD_RAD)
            )
        rows.append(row)
    return rows


def _time_rows(error):
    rows = []
    for region in TIME_REGIONS:
        values = error[region["start"] : region["stop"]]
        rows.append(
            {
                "label": region["label"],
                "mean_absolute_error_rad": float(np.mean(values)),
                "maximum_absolute_error_rad": float(np.max(values)),
                "threshold_exceedance_count": int(
                    np.count_nonzero(values > PHYSICAL_THRESHOLD_RAD)
                ),
            }
        )
    return rows


def _require_remote_preservation(permit) -> None:
    if _git("branch", "--show-current") != "codex/pi05-autolearn-loop":
        raise ValueError("T20.36f run is on the wrong branch")
    head = _git("rev-parse", "HEAD")
    remote = subprocess.run(
        [
            "git",
            "ls-remote",
            "--heads",
            "origin",
            "codex/pi05-autolearn-loop",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    if head != remote:
        raise ValueError("T20.36f current source is not remotely preserved")
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
