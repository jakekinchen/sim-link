"""Deterministic source- and phase-balanced replay plans for PI0.5."""

from __future__ import annotations

import hashlib
import json
import random

from collections import Counter
from pathlib import Path
from typing import Any, Iterator


REPLAY_PLAN_SCHEMA_VERSION = "scenesmith.pi05_replay_plan.v1"


def build_replay_plan(
    dataset_root: Path,
    correction_sidecar: Path,
    *,
    draws: int,
    correction_fraction: float,
    seed: int,
) -> dict[str, Any]:
    if draws <= 0:
        raise ValueError("Replay plan draws must be positive")
    if not 0.0 < correction_fraction < 1.0:
        raise ValueError("Correction fraction must be between zero and one")
    merge_summary_path = dataset_root / "scenesmith_merge_summary.json"
    contract_path = dataset_root / "scenesmith_pi05_dataset_contract.json"
    merge = _read_json(merge_summary_path)
    sources = merge.get("sources") or []
    if len(sources) != 2:
        raise ValueError("Balanced PI0.5 replay requires exactly base and correction sources")
    base_frames = int(sources[0]["total_frames"])
    correction_frames = int(sources[1]["total_frames"])
    if base_frames + correction_frames != int(merge["total_frames"]):
        raise ValueError("Merge source counts do not match merged frame count")

    phase_indices: dict[str, list[int]] = {}
    sidecar_rows = _read_jsonl(correction_sidecar)
    if len(sidecar_rows) != correction_frames:
        raise ValueError("Correction sidecar count does not match merged correction frames")
    for offset, row in enumerate(sidecar_rows):
        phase = _correction_phase(row)
        phase_indices.setdefault(phase, []).append(base_frames + offset)

    correction_draws = round(draws * correction_fraction)
    correction_draws = min(max(correction_draws, 1), draws - 1)
    base_draws = draws - correction_draws
    rng = random.Random(seed)
    base_schedule = _cycle_shuffled(range(base_frames), base_draws, rng)
    correction_schedule = _balanced_phase_schedule(phase_indices, correction_draws, rng)
    source_slots = _even_slots(draws, correction_draws)
    base_iter = iter(base_schedule)
    correction_iter = iter(correction_schedule)
    sample_indices = [next(correction_iter) if slot else next(base_iter) for slot in source_slots]
    phase_by_index = {index: phase for phase, indices in phase_indices.items() for index in indices}
    phase_counts = Counter(phase_by_index[index] for index in correction_schedule)
    sample_labels = [
        {
            "source": "base" if index < base_frames else "correction",
            "phase": None if index < base_frames else phase_by_index[index],
        }
        for index in sample_indices
    ]
    return {
        "schema_version": REPLAY_PLAN_SCHEMA_VERSION,
        "dataset_root": str(dataset_root),
        "dataset_contract_sha256": _sha256(contract_path),
        "merge_summary_sha256": _sha256(merge_summary_path),
        "correction_sidecar_sha256": _sha256(correction_sidecar),
        "seed": seed,
        "draws": draws,
        "dataset_total_frames": base_frames + correction_frames,
        "correction_fraction": correction_fraction,
        "source_counts": {"base": base_draws, "correction": correction_draws},
        "correction_phase_counts": dict(sorted(phase_counts.items())),
        "sample_indices": sample_indices,
        "sample_labels": sample_labels,
    }


def write_replay_plan(path: Path, plan: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


class AuditedReplaySampler:
    """Yield a finite replay plan and atomically record every requested sample."""

    def __init__(self, plan: dict[str, Any], audit_path: Path) -> None:
        if plan.get("schema_version") != REPLAY_PLAN_SCHEMA_VERSION:
            raise ValueError("Unsupported replay plan")
        self.indices = [int(index) for index in plan["sample_indices"]]
        self.labels = list(plan.get("sample_labels") or [{} for _ in self.indices])
        if len(self.labels) != len(self.indices):
            raise ValueError("Replay sample labels do not match indices")
        self.audit_path = audit_path
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_path.write_text("", encoding="utf-8")

    def __iter__(self) -> Iterator[int]:
        for draw, (index, label) in enumerate(zip(self.indices, self.labels, strict=True)):
            with self.audit_path.open("a", encoding="utf-8") as stream:
                stream.write(
                    json.dumps({"draw": draw, "sample_index": index, **label}) + "\n"
                )
            yield index

    def __len__(self) -> int:
        return len(self.indices)


def _balanced_phase_schedule(
    groups: dict[str, list[int]],
    count: int,
    rng: random.Random,
) -> list[int]:
    if not groups:
        raise ValueError("Correction replay has no phase groups")
    names = sorted(groups)
    slots = [names[index % len(names)] for index in range(count)]
    schedules = {
        name: iter(_cycle_shuffled(groups[name], slots.count(name), rng)) for name in names
    }
    return [next(schedules[name]) for name in slots]


def _cycle_shuffled(values: Any, count: int, rng: random.Random) -> list[int]:
    pool = list(values)
    if not pool and count:
        raise ValueError("Cannot draw from an empty replay group")
    result: list[int] = []
    while len(result) < count:
        epoch = pool.copy()
        rng.shuffle(epoch)
        result.extend(epoch[: count - len(result)])
    return result


def _even_slots(total: int, selected: int) -> list[bool]:
    return [((index + 1) * selected // total) > (index * selected // total) for index in range(total)]


def _correction_phase(row: dict[str, Any]) -> str:
    replay_role = str(row.get("replay_role") or "")
    if replay_role in {"pre_context", "post_context"}:
        return replay_role
    source = str(row.get("action_source") or "unknown")
    if "recovery_pick" in source:
        return "recovery_pick"
    if "tray_transfer" in source:
        return "tray_transfer"
    if "post_place" in source:
        return "post_place"
    return source


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()
