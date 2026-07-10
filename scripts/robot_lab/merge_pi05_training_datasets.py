#!/usr/bin/env python3
"""Safely merge compatible base and DAgger datasets for PI0.5 training."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys

from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
LEROBOT_SRC = REPO_ROOT / "external" / "lerobot" / "src"
REQUIRED_FEATURES = {
    "observation.images.top",
    "observation.images.wrist",
    "observation.state",
    "action",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--corrections-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument(
        "--normalization-root",
        type=Path,
        help=(
            "Dataset whose meta/stats.json remains the fixed normalization contract. "
            "Defaults to --base-root for incremental same-embodiment training."
        ),
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    base_info = _load_info(args.base_root)
    correction_info = _load_info(args.corrections_root)
    _validate_compatible(base_info, correction_info)
    if args.output_root.exists():
        if not args.overwrite:
            parser.error(f"{args.output_root} exists; pass --overwrite to replace it")
        shutil.rmtree(args.output_root)

    sys.path.insert(0, str(LEROBOT_SRC))
    from lerobot.datasets import LeRobotDataset, merge_datasets

    base_repo = "local/pi05-base"
    correction_repo = "local/pi05-dagger-corrections"
    base = LeRobotDataset(base_repo, root=args.base_root, return_uint8=True)
    corrections = LeRobotDataset(correction_repo, root=args.corrections_root, return_uint8=True)
    merged = merge_datasets(
        [base, corrections],
        output_repo_id=args.repo_id,
        output_dir=args.output_root,
        concatenate_videos=False,
        concatenate_data=False,
    )
    output_info = _load_info(args.output_root)
    expected_episodes = int(base_info["total_episodes"]) + int(correction_info["total_episodes"])
    expected_frames = int(base_info["total_frames"]) + int(correction_info["total_frames"])
    if merged.num_episodes != expected_episodes or merged.num_frames != expected_frames:
        raise RuntimeError(
            "Merged dataset count mismatch: "
            f"got {merged.num_episodes} episodes/{merged.num_frames} frames, "
            f"expected {expected_episodes}/{expected_frames}"
        )
    normalization = _pin_normalization_stats(
        args.normalization_root or args.base_root,
        args.output_root,
    )

    summary = {
        "schema_version": "scenesmith.pi05_training_merge.v1",
        "status": "pass",
        "repo_id": args.repo_id,
        "output_root": str(args.output_root),
        "sources": [
            _source_evidence(args.base_root, base_info),
            _source_evidence(args.corrections_root, correction_info),
        ],
        "total_episodes": int(output_info["total_episodes"]),
        "total_frames": int(output_info["total_frames"]),
        "features": sorted(output_info["features"]),
        "normalization_contract": normalization,
    }
    summary_path = args.output_root / "scenesmith_merge_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _load_info(root: Path) -> dict[str, Any]:
    path = root / "meta" / "info.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing LeRobot metadata: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _validate_compatible(base: dict[str, Any], corrections: dict[str, Any]) -> None:
    base_features = base.get("features") or {}
    correction_features = corrections.get("features") or {}
    if set(base_features) != set(correction_features):
        raise ValueError("Base and correction dataset feature keys do not match")
    if not REQUIRED_FEATURES.issubset(base_features):
        raise ValueError("PI0.5 training datasets are missing required causal features")
    mismatches = [
        key
        for key in sorted(base_features)
        if _feature_signature(base_features[key]) != _feature_signature(correction_features[key])
    ]
    if mismatches:
        raise ValueError(f"Base and correction feature definitions differ: {mismatches}")


def _feature_signature(feature: dict[str, Any]) -> tuple[Any, ...]:
    return (
        feature.get("dtype"),
        tuple(feature.get("shape") or ()),
        tuple(feature.get("names") or ()),
    )


def _source_evidence(root: Path, info: dict[str, Any]) -> dict[str, Any]:
    info_path = root / "meta" / "info.json"
    return {
        "root": str(root),
        "info_sha256": hashlib.sha256(info_path.read_bytes()).hexdigest(),
        "total_episodes": int(info["total_episodes"]),
        "total_frames": int(info["total_frames"]),
    }


def _pin_normalization_stats(source_root: Path, output_root: Path) -> dict[str, Any]:
    source = source_root / "meta" / "stats.json"
    destination = output_root / "meta" / "stats.json"
    if not source.is_file():
        raise FileNotFoundError(f"Missing normalization statistics: {source}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not {"action", "observation.state"}.issubset(payload):
        raise ValueError(f"Normalization statistics lack action/state entries: {source}")
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(source.read_bytes())
    temporary.replace(destination)
    return {
        "mode": "pinned",
        "source_root": str(source_root),
        "source_stats_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "output_stats_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
