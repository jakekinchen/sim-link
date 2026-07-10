#!/usr/bin/env python3
"""Finalize a LeRobot PEFT checkpoint for standalone PI0.5 inference."""

from __future__ import annotations

import argparse
import hashlib
import json

from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "adapter_config.json",
    "adapter_model.safetensors",
    "policy_preprocessor.json",
    "policy_postprocessor.json",
    "train_config.json",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--source-config", type=Path, required=True)
    args = parser.parse_args()

    missing = [name for name in REQUIRED_FILES if not (args.checkpoint_root / name).is_file()]
    if missing:
        parser.error(f"Checkpoint is incomplete: {missing}")
    if not args.source_config.is_file():
        parser.error(f"Missing source policy config: {args.source_config}")

    source = _read_json(args.source_config)
    train = _read_json(args.checkpoint_root / "train_config.json")
    trained_policy = train.get("policy") or {}
    for key in ("type", "input_features", "output_features"):
        if source.get(key) != trained_policy.get(key):
            raise ValueError(f"Source and trained policy {key} do not match")

    finalized = dict(source)
    finalized.update(
        {
            "device": trained_policy.get("device", source.get("device")),
            "dtype": trained_policy.get("dtype", source.get("dtype")),
            "push_to_hub": False,
            "pretrained_path": _read_json(args.checkpoint_root / "adapter_config.json").get(
                "base_model_name_or_path"
            ),
        }
    )
    config_path = args.checkpoint_root / "config.json"
    _write_json(config_path, finalized)
    summary = {
        "schema_version": "scenesmith.pi05_checkpoint_finalize.v1",
        "status": "pass",
        "checkpoint_root": str(args.checkpoint_root),
        "source_config": str(args.source_config),
        "config_sha256": _sha256(config_path),
        "adapter_sha256": _sha256(args.checkpoint_root / "adapter_model.safetensors"),
        "policy_type": finalized.get("type"),
        "device": finalized.get("device"),
        "dtype": finalized.get("dtype"),
        "input_features": sorted((finalized.get("input_features") or {}).keys()),
        "output_features": finalized.get("output_features"),
    }
    _write_json(args.checkpoint_root / "scenesmith_finalize_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
