"""Usage-locked development and audit seed governance for PI0.5 evaluation."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any


SEED_REGISTRY_SCHEMA_VERSION = "scenesmith.pi05_seed_registry.v1"
SEED_TIERS = {"development", "audit"}


def reserve_evaluation_seeds(
    registry_path: Path,
    *,
    cycle_id: str,
    tier: str,
    seeds: tuple[int, ...],
    development_pool: tuple[int, ...],
    audit_pool: tuple[int, ...],
    development_rotation_window: int = 2,
) -> dict[str, Any]:
    if tier not in SEED_TIERS:
        raise ValueError(f"Unknown evaluation seed tier: {tier}")
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("Evaluation reservation seeds must be non-empty and unique")
    if set(development_pool) & set(audit_pool):
        raise ValueError("Development and audit seed pools overlap")
    pool = development_pool if tier == "development" else audit_pool
    if not set(seeds).issubset(pool):
        raise ValueError(f"{tier} reservation contains seeds outside its declared pool")
    registry = load_seed_registry(registry_path) if registry_path.is_file() else {
        "schema_version": SEED_REGISTRY_SCHEMA_VERSION,
        "reservations": [],
    }
    reservations = list(registry["reservations"])
    if any(item["cycle_id"] == cycle_id for item in reservations):
        raise ValueError(f"Cycle already reserved evaluation seeds: {cycle_id}")
    if tier == "audit":
        prior_audit = {
            int(seed)
            for item in reservations
            if item["tier"] == "audit"
            for seed in item["seeds"]
        }
        reused = sorted(set(seeds) & prior_audit)
        if reused:
            raise ValueError(f"Audit seeds are locked after first use: {reused}")
    else:
        if development_rotation_window <= 0:
            raise ValueError("Development rotation window must be positive")
        recent = [item for item in reservations if item["tier"] == "development"]
        recent = recent[-development_rotation_window:]
        recent_seeds = {int(seed) for item in recent for seed in item["seeds"]}
        reused = sorted(set(seeds) & recent_seeds)
        if reused:
            raise ValueError(f"Development seeds violate rotation window: {reused}")
    reservations.append(
        {
            "sequence": len(reservations) + 1,
            "cycle_id": cycle_id,
            "tier": tier,
            "seeds": list(seeds),
            "promotable": tier == "audit",
        }
    )
    return {
        "schema_version": SEED_REGISTRY_SCHEMA_VERSION,
        "development_pool": list(development_pool),
        "audit_pool": list(audit_pool),
        "development_rotation_window": development_rotation_window,
        "reservations": reservations,
    }


def load_seed_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != SEED_REGISTRY_SCHEMA_VERSION:
        raise ValueError(f"Unsupported seed registry: {path}")
    reservations = payload.get("reservations")
    if not isinstance(reservations, list):
        raise ValueError("Seed registry reservations must be a list")
    cycle_ids = [str(item.get("cycle_id")) for item in reservations]
    if len(cycle_ids) != len(set(cycle_ids)):
        raise ValueError("Seed registry contains duplicate cycle reservations")
    return payload


def write_seed_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
