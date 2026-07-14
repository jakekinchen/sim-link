#!/usr/bin/env python3
"""Compose or verify the exact T20.28 official-sampler exposure audit."""

from __future__ import annotations

import argparse
import hashlib
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
from scenesmith.robot_lab.t20_28_sampler_exposure_audit import (  # noqa: E402
    build_audit,
    verify_audit,
)


SAMPLER_PATH = REPO_ROOT / "external/lerobot/src/lerobot/datasets/sampler.py"
SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "configurations/robot_lab/t17_5b_episode_generation_manifest.json"
)
CLEAN_SPEC_PATH = REPO_ROOT / "configurations/robot_lab/t20_17_clean_base_training_spec.json"
RECOVERY_SPEC_PATH = (
    REPO_ROOT / "configurations/robot_lab/t20_23_recovery_augmented_training_spec.json"
)
CLEAN_RUN_PATH = REPO_ROOT / "outputs/robot_lab/t20_17_clean_base_run_002/run_summary.json"
RECOVERY_RUN_PATH = (
    REPO_ROOT / "outputs/robot_lab/t20_24_recovery_augmented_run_002/run_summary.json"
)
OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t20_28_sampler_exposure_audit.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    expected, clean_episodes, recovery_episodes = _compose()
    if args.verify:
        recorded = load_strict_json(OUTPUT_PATH)
        verify_audit(
            recorded,
            clean_episodes=clean_episodes,
            recovery_episodes=recovery_episodes,
        )
        if recorded != expected:
            raise ValueError("T20.28 recorded audit drifted from actual pinned sampler")
        print("T20.28 sampler exposure audit verified")
        return 0
    if OUTPUT_PATH.exists():
        raise FileExistsError("T20.28 audit already exists; use --verify")
    dump_canonical_json(OUTPUT_PATH, expected)
    print(
        expected["identity_sha256"],
        {
            label: {
                "sources": row["source_class_counts"],
                "approach": row["approach_by_source_class"],
                "frame_zero": row["frame_zero_by_source_class"],
            }
            for label, row in expected["campaigns"].items()
        },
        expected["selected_next_hypothesis"],
    )
    return 0


def _compose() -> tuple[dict, list[dict], list[dict]]:
    from lerobot.datasets import EpisodeAwareSampler

    manifest = load_strict_json(SOURCE_MANIFEST_PATH)
    verify_episode_store(manifest, default_store_root())
    clean_spec = load_strict_json(CLEAN_SPEC_PATH)
    recovery_spec = load_strict_json(RECOVERY_SPEC_PATH)
    verify_signed_payload(clean_spec, label="T20.17 clean training spec")
    verify_signed_payload(recovery_spec, label="T20.23 recovery training spec")
    clean_run = load_strict_json(CLEAN_RUN_PATH)
    recovery_run = load_strict_json(RECOVERY_RUN_PATH)
    verify_signed_payload(clean_run, label="T20.17 clean run")
    verify_signed_payload(recovery_run, label="T20.24 recovery run")

    nominal = []
    for seed in range(6):
        entry = next(row for row in manifest["episodes"] if row["seed"] == seed)
        episode = load_strict_json(default_store_root() / entry["relative_path"])
        nominal.append(
            {
                "source_class": "nominal",
                "phases": [frame["source_phase"] for frame in episode["frames"]],
            }
        )
    recovery = []
    for entry in recovery_spec["recovery_training_episodes"]:
        episode = load_strict_json(REPO_ROOT / entry["path"])
        verify_signed_payload(episode, label="T20.28 recovery episode")
        recovery.append(
            {
                "source_class": "recovery",
                "phases": [frame["phase"] for frame in episode["frames"]],
            }
        )
    recovery_episodes = nominal + recovery
    clean_seed = clean_spec["campaign"]["training_seed"]
    recovery_seed = recovery_spec["campaign"]["training_seed"]
    clean_updates = clean_run["optimizer_update_count"]
    recovery_updates = recovery_run["optimizer_update_count"]
    if clean_updates != 250 or recovery_updates != 500:
        raise ValueError("T20.28 campaign update count drifted")
    clean_indices = _sample(EpisodeAwareSampler, nominal, clean_seed, clean_updates)
    recovery_indices = _sample(
        EpisodeAwareSampler, recovery_episodes, recovery_seed, recovery_updates
    )
    audit = build_audit(
        sampler_source_sha256=hashlib.sha256(SAMPLER_PATH.read_bytes()).hexdigest(),
        sampler_schema="lerobot.datasets.sampler.EpisodeAwareSampler",
        clean_indices=clean_indices,
        recovery_indices=recovery_indices,
        clean_episodes=nominal,
        recovery_episodes=recovery_episodes,
        clean_seed=clean_seed,
        recovery_seed=recovery_seed,
    )
    return audit, nominal, recovery_episodes


def _sample(sampler_class, episodes: list[dict], seed: int, count: int) -> list[int]:
    starts = []
    ends = []
    cursor = 0
    for episode in episodes:
        starts.append(cursor)
        cursor += len(episode["phases"])
        ends.append(cursor)
    sampler = sampler_class(starts, ends, shuffle=True, seed=seed)
    iterator = iter(sampler)
    return [next(iterator) for _ in range(count)]


if __name__ == "__main__":
    raise SystemExit(main())
