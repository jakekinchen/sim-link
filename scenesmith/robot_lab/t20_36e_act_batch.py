"""Model-free loading and verification of the exact T20.36e batch."""

from __future__ import annotations

import hashlib

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import canonical_json_bytes
from scenesmith.robot_lab.so101_coordinates import (
    lerobot_to_mujoco,
    mujoco_to_lerobot,
)
from scenesmith.robot_lab.t20_33_one_batch_memorization import verify_preflight
from scenesmith.robot_lab.t20_36e_exact_act_gate_b_control import (
    EXPECTED_BATCH_EVIDENCE,
)


def load_exact_batch(
    *, repo_root: Path, spec: dict[str, Any]
) -> dict[str, Any]:
    """Load the canonical batch without importing or constructing a policy."""

    import numpy as np

    from lerobot.datasets import LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata

    root = Path(repo_root)
    dataset_contract = spec["canonical_dataset"]
    repo_id = dataset_contract["repo_id"]
    dataset_root = root / dataset_contract["root"]
    metadata = LeRobotDatasetMetadata(repo_id, root=dataset_root)
    delta_timestamps = {
        "action": [index / metadata.fps for index in range(50)]
    }
    dataset = LeRobotDataset(
        repo_id,
        root=dataset_root,
        episodes=[spec["source_batch"]["canonical_dataset_episode_index"]],
        delta_timestamps=delta_timestamps,
        return_uint8=False,
    )
    item = dataset[spec["source_batch"]["frame_index"]]
    action = item["action"].detach().cpu().numpy()
    state = item["observation.state"].detach().cpu().numpy()
    physical_action = np.asarray(
        [lerobot_to_mujoco(row.tolist()) for row in action], dtype=np.float64
    )
    physical_state = np.asarray(
        lerobot_to_mujoco(state.tolist()), dtype=np.float64
    )
    source_episode = verify_preflight(repo_root=root)["source_episode"]
    frames = source_episode["frames"][:50]
    source_action = np.asarray(
        [row["actions"]["measured"]["values"] for row in frames],
        dtype=np.float64,
    )
    source_state = np.asarray(
        frames[0]["observations"]["joint_position_mujoco_rad"],
        dtype=np.float64,
    )
    round_trip = np.asarray(
        [
            lerobot_to_mujoco(mujoco_to_lerobot(row.tolist()))
            for row in source_action
        ],
        dtype=np.float64,
    )
    image_shapes = {}
    image_hashes = {}
    for key in dataset_contract["image_feature_keys"]:
        tensor = item[key].detach().cpu().contiguous()
        image_shapes[key] = list(tensor.shape)
        image_hashes[key] = hashlib.sha256(
            tensor.numpy().tobytes()
        ).hexdigest()
    evidence = {
        "dataset_episode_index": int(item["episode_index"]),
        "dataset_frame_index": int(item["frame_index"]),
        "action_shape": list(action.shape),
        "action_pad_count": int(item["action_is_pad"].sum().item()),
        "state_shape": list(state.shape),
        "image_shapes": image_shapes,
        "image_tensor_sha256": image_hashes,
        "physical_action_chunk_sha256": hashlib.sha256(
            canonical_json_bytes(physical_action.astype(float).tolist())
        ).hexdigest(),
        "physical_state_sha256": hashlib.sha256(
            canonical_json_bytes(physical_state.astype(float).tolist())
        ).hexdigest(),
        "maximum_source_action_error_rad": float(
            np.max(np.abs(physical_action - source_action))
        ),
        "maximum_source_state_error_rad": float(
            np.max(np.abs(physical_state - source_state))
        ),
        "maximum_coordinate_round_trip_error_rad": float(
            np.max(np.abs(round_trip - source_action))
        ),
        "task": item["task"],
    }
    if evidence != EXPECTED_BATCH_EVIDENCE:
        raise ValueError("T20.36e exact canonical batch evidence drifted")
    return {
        "dataset": dataset,
        "item": item,
        "physical_action": physical_action,
        "evidence": evidence,
    }
