#!/usr/bin/env python3
"""Compose or verify the four-model T20.11 action-localization gate."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.action_localization_gate import (  # noqa: E402
    build_action_localization_gate,
    verify_action_localization_gate,
)
from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.model_bakeoff import MODEL_ORDER  # noqa: E402


ROOT = REPO_ROOT / "outputs/robot_lab/t20_11_action_localization"
OUTPUT = ROOT / "summary.json"


def _results() -> list[tuple[str, dict, str]]:
    rows = []
    for model_id in MODEL_ORDER:
        path = ROOT / f"{model_id}.json"
        rows.append((str(path.relative_to(REPO_ROOT)), load_strict_json(path), _sha(path)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    results = _results()
    payload = build_action_localization_gate(results)
    if args.check:
        stored = load_strict_json(OUTPUT)
        verify_action_localization_gate(stored, results)
        print("verified", OUTPUT.relative_to(REPO_ROOT), stored["identity_sha256"])
        return 0
    if OUTPUT.exists():
        raise ValueError("T20.11 action-localization gate exists; use --check")
    dump_canonical_json(OUTPUT, payload)
    print("wrote", OUTPUT.relative_to(REPO_ROOT), payload["identity_sha256"])
    return 0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
