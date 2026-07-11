#!/usr/bin/env python3
"""Write or verify the blocked PI0.5 reviewed-input issuance gate."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.pi05_reviewed_input_gate import (
    build_pi05_reviewed_input_gate,
    verify_pi05_reviewed_input_gate,
)


DEFAULT_CALIBRATION = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
DEFAULT_HF_CACHE = Path.home() / ".cache/huggingface/hub"
DEFAULT_OUTPUT = Path(
    "configurations/robot_lab/"
    "pi05_reviewed_inputs.blocked_missing_reviewed_inputs.json"
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
    arguments = {
        "repo_root": REPO_ROOT,
        "hf_cache_root": hf_cache_root,
        "calibration_path": calibration_path,
    }

    if args.verify:
        payload = load_strict_json(output_path)
        verify_pi05_reviewed_input_gate(payload, **arguments)
        status = "verified"
    else:
        if output_path.exists() or output_path.is_symlink():
            raise ValueError("PI0.5 reviewed-input gate already exists; use --verify")
        payload = build_pi05_reviewed_input_gate(**arguments)
        dump_canonical_json(output_path, payload)
        stored = load_strict_json(output_path)
        if stored != payload:
            raise ValueError("Stored PI0.5 reviewed-input gate bytes drifted")
        verify_pi05_reviewed_input_gate(stored, **arguments)
        status = "written"

    print(
        json.dumps(
            {
                "status": status,
                "schema_version": payload["schema_version"],
                "gate_status": payload["status"],
                "identity_sha256": payload["identity_sha256"],
                "missing_inputs": payload["missing_inputs"],
                "production_input_issuance_allowed": payload[
                    "production_input_issuance_allowed"
                ],
                "accepted_live_policy_input": payload[
                    "accepted_live_policy_input"
                ],
                "hardware_accessed": payload["hardware_accessed"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve_pinned_file(path: Path, *, expected: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved != expected.resolve() or not resolved.is_file():
        raise ValueError(f"Pinned {label} is missing or changed")
    return resolved


def _resolve_pinned_directory(
    path: Path,
    *,
    expected: Path,
    label: str,
) -> Path:
    resolved = path.expanduser().resolve()
    if resolved != expected.resolve() or not resolved.is_dir():
        raise ValueError(f"Pinned {label} is missing or changed")
    return resolved


def _resolve_repo_output(path: Path) -> Path:
    unresolved = path if path.is_absolute() else REPO_ROOT / path
    expected = REPO_ROOT / DEFAULT_OUTPUT
    if unresolved.absolute() != expected.absolute():
        raise ValueError(f"Output path is not canonical: {DEFAULT_OUTPUT}")
    current = REPO_ROOT
    for part in DEFAULT_OUTPUT.parent.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("PI0.5 reviewed-input output parent is aliased")
    if not unresolved.parent.is_dir():
        raise ValueError("PI0.5 reviewed-input output parent is missing")
    return unresolved


if __name__ == "__main__":
    raise SystemExit(main())
