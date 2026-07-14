"""Exact official-sampler exposure audit for T20.28."""

from __future__ import annotations

import hashlib
import json

from collections import Counter
from typing import Any

from scenesmith.robot_lab.artifact_contract import sign_payload, verify_signed_payload


SCHEMA_VERSION = "scenesmith.t20_28_sampler_exposure_audit.v1"


def build_audit(
    *,
    sampler_source_sha256: str,
    sampler_schema: str,
    clean_indices: list[int],
    recovery_indices: list[int],
    clean_episodes: list[dict[str, Any]],
    recovery_episodes: list[dict[str, Any]],
    clean_seed: int,
    recovery_seed: int,
    _skip_verify: bool = False,
) -> dict[str, Any]:
    _sha(sampler_source_sha256, "sampler source")
    if sampler_schema != "lerobot.datasets.sampler.EpisodeAwareSampler":
        raise ValueError("T20.28 sampler implementation drifted")
    clean = _campaign(
        label="clean_base",
        indices=clean_indices,
        episodes=clean_episodes,
        expected_updates=250,
        seed=clean_seed,
    )
    recovery = _campaign(
        label="recovery_augmented",
        indices=recovery_indices,
        episodes=recovery_episodes,
        expected_updates=500,
        seed=recovery_seed,
    )
    early_phase_lower = (
        recovery["phase_counts"].get("approach", 0)
        < clean["phase_counts"].get("approach", 0)
        or recovery["frame_zero_count"] < clean["frame_zero_count"]
    )
    audit = sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "task_id": "T20.28",
            "sampler_schema": sampler_schema,
            "sampler_source_sha256": sampler_source_sha256,
            "sampler_contract": {
                "shuffle": True,
                "resume": False,
                "batch_size": 1,
                "num_processes": 1,
                "epoch": 0,
                "order_is_pure_function_of_seed_and_epoch": True,
            },
            "campaigns": {"clean_base": clean, "recovery_augmented": recovery},
            "recovery_early_phase_exposure_lower_than_clean": early_phase_lower,
            "exposure_hypothesis": (
                "supported"
                if early_phase_lower
                else "rejected_recovery_campaign_had_at_least_clean_early_phase_exposure"
            ),
            "selected_next_hypothesis": (
                "audit_recovery_dataset_quantile_and_postprocessor_shift"
                if not early_phase_lower
                else "increase_declared_early_phase_sampling_before_optimizer"
            ),
            "counts_alone_claim_optimizer_causality": False,
            "model_inference_executed": False,
            "action_applied": False,
            "closed_loop_rollout_executed": False,
            "optimizer_training": False,
            "simulation_policy_accepted": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
            "physical_transfer_ready": False,
            "promotion_eligible": False,
        }
    )
    if not _skip_verify:
        verify_audit(
            audit,
            clean_episodes=clean_episodes,
            recovery_episodes=recovery_episodes,
        )
    return audit


def verify_audit(
    audit: dict[str, Any],
    *,
    clean_episodes: list[dict[str, Any]],
    recovery_episodes: list[dict[str, Any]],
) -> None:
    verify_signed_payload(audit, label="T20.28 sampler exposure audit")
    if audit.get("schema_version") != SCHEMA_VERSION or audit.get("task_id") != "T20.28":
        raise ValueError("T20.28 audit identity drifted")
    expected = build_audit(
        sampler_source_sha256=audit["sampler_source_sha256"],
        sampler_schema=audit["sampler_schema"],
        clean_indices=audit["campaigns"]["clean_base"]["sampled_indices"],
        recovery_indices=audit["campaigns"]["recovery_augmented"]["sampled_indices"],
        clean_episodes=clean_episodes,
        recovery_episodes=recovery_episodes,
        clean_seed=audit["campaigns"]["clean_base"]["seed"],
        recovery_seed=audit["campaigns"]["recovery_augmented"]["seed"],
        _skip_verify=True,
    )
    if audit != expected:
        raise ValueError("T20.28 audit drifted from exact sampled indices")
    required_false = (
        "counts_alone_claim_optimizer_causality",
        "model_inference_executed",
        "action_applied",
        "closed_loop_rollout_executed",
        "optimizer_training",
        "simulation_policy_accepted",
        "physical_actuation",
        "external_compute_started",
        "brev_compute_started",
        "physical_transfer_ready",
        "promotion_eligible",
    )
    if any(audit.get(field) is not False for field in required_false):
        raise ValueError("T20.28 authority fields drifted")


def _campaign(
    *,
    label: str,
    indices: list[int],
    episodes: list[dict[str, Any]],
    expected_updates: int,
    seed: int,
) -> dict[str, Any]:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("T20.28 sampler seed is invalid")
    if len(indices) != expected_updates or len(set(indices)) != expected_updates:
        raise ValueError("T20.28 sampled indices are missing or duplicated")
    boundaries = []
    cursor = 0
    for episode_index, episode in enumerate(episodes):
        phases = episode.get("phases")
        source_class = episode.get("source_class")
        if not isinstance(phases, list) or not phases or source_class not in {
            "nominal",
            "recovery",
        }:
            raise ValueError("T20.28 episode phase/source descriptor is malformed")
        boundaries.append((cursor, cursor + len(phases), episode_index, source_class, phases))
        cursor += len(phases)
    rows = []
    for position, index in enumerate(indices):
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < cursor:
            raise ValueError("T20.28 sampled index is out of range")
        start, _, episode_index, source_class, phases = next(
            boundary for boundary in boundaries if boundary[0] <= index < boundary[1]
        )
        frame_index = index - start
        phase = phases[frame_index]
        if not isinstance(phase, str) or not phase:
            raise ValueError("T20.28 phase label is invalid")
        rows.append((position, index, episode_index, frame_index, source_class, phase))
    source_counts = Counter(row[4] for row in rows)
    phase_counts = Counter(row[5] for row in rows)
    episode_counts = Counter(str(row[2]) for row in rows)
    frame_zero_by_source = Counter(row[4] for row in rows if row[3] == 0)
    approach_by_source = Counter(row[4] for row in rows if row[5] == "approach")
    encoded = json.dumps(indices, separators=(",", ":")).encode()
    return {
        "label": label,
        "seed": seed,
        "optimizer_update_count": expected_updates,
        "dataset_frame_count": cursor,
        "sampled_index_count": len(indices),
        "unique_sampled_index_count": len(set(indices)),
        "sampled_indices_sha256": hashlib.sha256(encoded).hexdigest(),
        "sampled_indices": indices,
        "episode_counts": dict(sorted(episode_counts.items())),
        "source_class_counts": dict(sorted(source_counts.items())),
        "phase_counts": dict(sorted(phase_counts.items())),
        "frame_zero_count": sum(frame_zero_by_source.values()),
        "frame_zero_by_source_class": dict(sorted(frame_zero_by_source.items())),
        "approach_count": phase_counts.get("approach", 0),
        "approach_by_source_class": dict(sorted(approach_by_source.items())),
        "dataset_fraction_sampled": len(indices) / cursor,
        "all_positions_source_and_phase_bound": True,
    }


def _sha(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError(f"T20.28 {label} must be lowercase SHA-256")
    return value
