#!/usr/bin/env python3
"""Compose or verify the offline T20.27 paired source-action gate."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (  # noqa: E402
    default_store_root,
    verify_episode_store,
)
from scenesmith.robot_lab.t20_17_clean_base_preflight import SOURCE_MANIFEST_PATH  # noqa: E402
from scenesmith.robot_lab.t20_25_frozen_candidate_localization import CANDIDATE_IDS  # noqa: E402
from scenesmith.robot_lab.t20_26_frame_zero_variability import (  # noqa: E402
    BATCH_IDS,
    build_paired_source_gate,
    verify_paired_source_gate,
)
from scripts.robot_lab.run_t20_25_frozen_candidate_localization import OUTPUT_ROOT  # noqa: E402


T20_26_GATE = REPO_ROOT / "configurations/robot_lab/t20_26_frame_zero_variability_gate.json"
OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t20_27_paired_source_action_gate.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    batches = [
        load_strict_json(OUTPUT_ROOT / f"{candidate}_frame_zero_batch_{batch}.json")
        for candidate in CANDIDATE_IDS
        for batch in BATCH_IDS
    ]
    manifest = load_strict_json(REPO_ROOT / SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    entry = next(row for row in manifest["episodes"] if row["seed"] == 6)
    episode = load_strict_json(default_store_root() / entry["relative_path"])
    source_action = episode["frames"][0]["actions"]["requested"]["values"]
    t20_26 = load_strict_json(T20_26_GATE)
    verify_signed_payload(t20_26, label="T20.26 variability gate")
    if args.verify:
        verify_paired_source_gate(load_strict_json(OUTPUT_PATH), batches)
        print("T20.27 paired source-action gate verified")
        return 0
    if OUTPUT_PATH.exists():
        raise FileExistsError("T20.27 gate already exists; use --verify")
    gate = build_paired_source_gate(
        batches=batches,
        source_action_rad=source_action,
        source_episode_file_sha256=entry["episode_file_sha256"],
        source_episode_identity_sha256=entry["raw_rollout_record_identity_sha256"],
        t20_26_gate_identity_sha256=t20_26["identity_sha256"],
    )
    dump_canonical_json(OUTPUT_PATH, gate)
    print(gate["identity_sha256"], gate["aggregate"], gate["distribution_result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
