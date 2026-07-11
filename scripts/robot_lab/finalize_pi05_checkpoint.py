#!/usr/bin/env python3
"""Finalize a LeRobot PEFT checkpoint for standalone PI0.5 inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys

from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "adapter_config.json",
    "adapter_model.safetensors",
    "policy_preprocessor.json",
    "policy_postprocessor.json",
    "policy_preprocessor_step_2_normalizer_processor.safetensors",
    "policy_postprocessor_step_0_unnormalizer_processor.safetensors",
    "train_config.json",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--source-config", type=Path, required=True)
    parser.add_argument("--normalization-stats", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack

    stack_identity = activate_lerobot_stack(
        repo_root=Path(__file__).resolve().parents[2], stage="finalization"
    )

    missing = [name for name in REQUIRED_FILES if not (args.checkpoint_root / name).is_file()]
    if missing:
        parser.error(f"Checkpoint is incomplete: {missing}")
    if not args.source_config.is_file():
        parser.error(f"Missing source policy config: {args.source_config}")
    normalization = _validate_normalization(args.checkpoint_root, args.normalization_stats)

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
        "normalization_contract": normalization,
        "policy_type": finalized.get("type"),
        "device": finalized.get("device"),
        "dtype": finalized.get("dtype"),
        "input_features": sorted((finalized.get("input_features") or {}).keys()),
        "output_features": finalized.get("output_features"),
        "lerobot_stack_identity_sha256": stack_identity["identity_sha256"],
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


def _validate_normalization(checkpoint_root: Path, expected_path: Path) -> dict[str, Any]:
    if not expected_path.is_file():
        raise FileNotFoundError(f"Missing expected normalization statistics: {expected_path}")
    expected = _read_json(expected_path)
    try:
        from safetensors.numpy import load_file
    except ModuleNotFoundError as exc:
        raise RuntimeError("safetensors is required to validate PI0.5 normalization") from exc

    preprocessor_path = (
        checkpoint_root / "policy_preprocessor_step_2_normalizer_processor.safetensors"
    )
    postprocessor_path = (
        checkpoint_root / "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
    )
    preprocessor = {key: value.reshape(-1).tolist() for key, value in load_file(preprocessor_path).items()}
    postprocessor = {
        key: value.reshape(-1).tolist() for key, value in load_file(postprocessor_path).items()
    }
    _compare_normalization(expected, preprocessor, ("action", "observation.state"))
    _compare_normalization(expected, postprocessor, ("action",))
    return {
        "mode": "pinned",
        "expected_stats": str(expected_path),
        "expected_stats_sha256": _sha256(expected_path),
        "preprocessor_state_sha256": _sha256(preprocessor_path),
        "postprocessor_state_sha256": _sha256(postprocessor_path),
    }


def _compare_normalization(
    expected: dict[str, Any], actual: dict[str, list[float]], features: tuple[str, ...]
) -> None:
    for feature in features:
        feature_stats = expected.get(feature)
        if not isinstance(feature_stats, dict):
            raise ValueError(f"Expected normalization lacks feature {feature}")
        for statistic, expected_values in feature_stats.items():
            key = f"{feature}.{statistic}"
            actual_values = actual.get(key)
            if actual_values is None:
                raise ValueError(f"Checkpoint normalization lacks {key}")
            normalized_expected = [float(value) for value in expected_values]
            if len(normalized_expected) != len(actual_values) or any(
                not math.isclose(left, right, rel_tol=1e-5, abs_tol=1e-5)
                for left, right in zip(normalized_expected, actual_values, strict=True)
            ):
                raise ValueError(f"Checkpoint normalization differs for {key}")


if __name__ == "__main__":
    raise SystemExit(main())
