#!/usr/bin/env python3
"""Run or verify the T20.9 immutable source-action oracle diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.act_grasp_closed_loop import (  # noqa: E402
    run_policy_grasp_closed_loop,
)
from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (  # noqa: E402
    default_store_root,
    generate_episode_payload,
    verify_episode_store,
)
from scenesmith.robot_lab.source_expert_oracle import (  # noqa: E402
    SCHEMA_VERSION,
    analyze_source_oracle,
    build_source_oracle_artifact,
    verify_source_oracle_artifact,
)


MANIFEST_PATH = REPO_ROOT / "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
T20_7_EVALUATION_PATH = (
    REPO_ROOT
    / "outputs/robot_lab/t20_7_four_model_training_run_001/evaluation_summary.json"
)
OUTPUT_PATH = REPO_ROOT / "outputs/robot_lab/t20_9_source_expert_oracle_run_001.json"
SEED = 2


def build() -> dict:
    manifest = load_strict_json(MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    entry = next((item for item in manifest["episodes"] if item["seed"] == SEED), None)
    if entry is None:
        raise ValueError("T20.9 seed-2 source episode is absent")
    episode_path = default_store_root() / entry["relative_path"]
    stored_episode = load_strict_json(episode_path)
    if _sha(episode_path) != entry["episode_file_sha256"]:
        raise ValueError("T20.9 source episode bytes drifted")

    regenerated_trace: list[dict] = []
    regenerated_episode = generate_episode_payload(
        dict(entry["spec"]), raw_trace_sink=regenerated_trace.append
    )
    if canonical_json_bytes(regenerated_episode) != canonical_json_bytes(stored_episode):
        raise ValueError("T20.9 deterministic source episode regeneration drifted")
    source_actions = [
        frame["actions"]["requested"]["values"] for frame in stored_episode["frames"]
    ]
    source_action_sha256 = hashlib.sha256(
        json.dumps(source_actions, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    cursor = 0
    oracle_trace: list[dict] = []

    def oracle(_images: dict[str, np.ndarray], _state: np.ndarray) -> np.ndarray:
        nonlocal cursor
        if cursor >= len(source_actions):
            raise ValueError("T20.9 oracle requested more actions than the source contains")
        action = np.asarray(source_actions[cursor], dtype=np.float64)
        cursor += 1
        return action

    rollout = run_policy_grasp_closed_loop(
        oracle,
        checkpoint_sha256=entry["episode_file_sha256"],
        training_run_summary_sha256=_sha(MANIFEST_PATH),
        seed=SEED,
        schema_version=SCHEMA_VERSION,
        task_id="T20.9",
        evidence_mode="source_expert_action_oracle_through_policy_closed_loop_adapter",
        policy_label="source_expert_oracle",
        frame_observer=oracle_trace.append,
    )
    if cursor != len(source_actions) or rollout["policy_action_sequence_sha256"] != source_action_sha256:
        raise ValueError("T20.9 oracle did not consume the exact source action sequence")
    diagnostics = analyze_source_oracle(
        stored_episode["frames"],
        regenerated_trace,
        oracle_trace,
        source_outcome=stored_episode["outcome"],
        oracle_rollout=rollout,
    )
    evaluation = load_strict_json(T20_7_EVALUATION_PATH)
    verify_signed_payload(evaluation, label="T20.7 evaluation gate")
    if evaluation.get("strict_success_count") != 0 or evaluation.get("winner_model_id") is not None:
        raise ValueError("T20.9 source T20.7 negative gate drifted")
    return build_source_oracle_artifact(
        source_refs={
            "episode_store_manifest": {
                "path": str(MANIFEST_PATH.relative_to(REPO_ROOT)),
                "identity_sha256": manifest["identity_sha256"],
                "file_sha256": _sha(MANIFEST_PATH),
            },
            "episode": {
                "path": str(episode_path.relative_to(REPO_ROOT)),
                "seed": SEED,
                "file_sha256": entry["episode_file_sha256"],
                "raw_rollout_record_identity_sha256": entry[
                    "raw_rollout_record_identity_sha256"
                ],
                "frame_count": entry["frame_count"],
                "source_action_sequence_sha256": source_action_sha256,
            },
            "source_grasp_identity_sha256": stored_episode[
                "source_grasp_identity_sha256"
            ],
            "source_episode_regenerated_byte_identically": True,
        },
        t20_7_evaluation_ref={
            "path": str(T20_7_EVALUATION_PATH.relative_to(REPO_ROOT)),
            "identity_sha256": evaluation["identity_sha256"],
            "file_sha256": _sha(T20_7_EVALUATION_PATH),
            "strict_success_count": evaluation["strict_success_count"],
            "winner_model_id": evaluation["winner_model_id"],
        },
        oracle_rollout=rollout,
        diagnostics=diagnostics,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    payload = build()
    verify_source_oracle_artifact(payload)
    if args.check:
        stored = load_strict_json(output)
        verify_source_oracle_artifact(stored)
        if stored != payload:
            raise ValueError("T20.9 oracle output drifted from source recomposition")
        print("verified", output.relative_to(REPO_ROOT), payload["identity_sha256"])
        return 0
    if output.exists():
        raise ValueError("T20.9 oracle output exists; use --check")
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print("wrote", output.relative_to(REPO_ROOT), payload["identity_sha256"])
    return 0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
