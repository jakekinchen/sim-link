#!/usr/bin/env python3
"""Write or verify the blocked PI0.5 preprocessing source contract."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.pi05_preprocessing_contract import (
    build_pi05_preprocessing_source_contract,
    verify_pi05_preprocessing_source_contract,
)


DEFAULT_CALIBRATION = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
DEFAULT_HF_CACHE = Path.home() / ".cache/huggingface/hub"
DEFAULT_OUTPUT = Path(
    "configurations/robot_lab/"
    "pi05_policy_input_preprocessing.blocked_missing_inputs.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    parser.add_argument("--hf-cache", type=Path, default=DEFAULT_HF_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    calibration_path = _resolve_pinned_file(
        args.calibration,
        expected=DEFAULT_CALIBRATION,
        label="follower calibration",
    )
    hf_cache_root = _resolve_pinned_directory(
        args.hf_cache,
        expected=DEFAULT_HF_CACHE,
        label="Hugging Face cache",
    )
    output_path = _resolve_repo_output(args.output)

    if args.verify:
        payload = load_strict_json(output_path)
        verify_pi05_preprocessing_source_contract(
            payload,
            repo_root=REPO_ROOT,
            hf_cache_root=hf_cache_root,
            calibration_path=calibration_path,
        )
        status = "verified"
    else:
        if output_path.exists() or output_path.is_symlink():
            raise ValueError("PI0.5 preprocessing contract already exists; use --verify")
        payload = build_pi05_preprocessing_source_contract(
            repo_root=REPO_ROOT,
            hf_cache_root=hf_cache_root,
            calibration_path=calibration_path,
        )
        dump_canonical_json(output_path, payload)
        stored = load_strict_json(output_path)
        if stored != payload:
            raise ValueError("Stored PI0.5 preprocessing contract bytes drifted")
        verify_pi05_preprocessing_source_contract(
            stored,
            repo_root=REPO_ROOT,
            hf_cache_root=hf_cache_root,
            calibration_path=calibration_path,
        )
        status = "written"

    print(
        json.dumps(
            {
                "status": status,
                "schema_version": payload["schema_version"],
                "contract_status": payload["status"],
                "identity_sha256": payload["identity_sha256"],
                "missing_inputs": payload["missing_inputs"],
                "production_preprocessing_allowed": payload[
                    "production_preprocessing_allowed"
                ],
                "model_instantiated": payload["model_instantiated"],
                "model_weights_read": payload["model_weights_read"],
                "hardware_accessed": payload["hardware_accessed"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve_pinned_file(path: Path, *, expected: Path, label: str) -> Path:
    unresolved = path.expanduser()
    resolved = unresolved.resolve()
    if resolved != expected.resolve():
        raise ValueError(f"{label} path is not pinned")
    if not resolved.is_file():
        raise ValueError(f"Pinned {label} is missing")
    return resolved


def _resolve_pinned_directory(
    path: Path,
    *,
    expected: Path,
    label: str,
) -> Path:
    unresolved = path.expanduser()
    resolved = unresolved.resolve()
    if resolved != expected.resolve():
        raise ValueError(f"{label} path is not pinned")
    if not resolved.is_dir():
        raise ValueError(f"Pinned {label} is missing")
    return resolved


def _resolve_repo_output(path: Path) -> Path:
    unresolved = path if path.is_absolute() else REPO_ROOT / path
    expected = REPO_ROOT / DEFAULT_OUTPUT
    if unresolved.absolute() != expected.absolute():
        raise ValueError(f"Output path is not canonical: {DEFAULT_OUTPUT}")
    _reject_alias_components(
        unresolved.parent,
        root=REPO_ROOT,
        label="PI0.5 preprocessing output parent",
    )
    if not unresolved.parent.is_dir():
        raise ValueError("PI0.5 preprocessing output parent is missing")
    return unresolved


def _reject_alias_components(path: Path, *, root: Path, label: str) -> None:
    canonical_root = root.resolve()
    candidate = path if path.is_absolute() else canonical_root / path
    try:
        relative = candidate.relative_to(canonical_root)
    except ValueError as exc:
        raise ValueError(f"{label} escaped its root") from exc
    if any(part in {".", ".."} for part in relative.parts):
        raise ValueError(f"{label} path is not canonical")
    current = canonical_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} path is aliased")


if __name__ == "__main__":
    raise SystemExit(main())
