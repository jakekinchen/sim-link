#!/usr/bin/env python3
"""Write or verify the tracked offline SO-101 calibration profile."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.calibration_profile import (
    build_calibration_profile,
    verify_calibration_profile,
)


DEFAULT_CALIBRATION = (
    Path.home()
    / ".cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json"
)
DEFAULT_MANIFEST = Path(
    "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
DEFAULT_OUTPUT = Path("configurations/robot_lab/pi05_calibration_profile.json")
EXPECTED_PREDECESSOR_IDENTITY = (
    "b360b4f60077846c62128fe4d4cc33d1ee4e6e72aa7831fcb7c6706e6b6599b4"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--verify", action="store_true")
    action.add_argument("--refresh-derived", action="store_true")
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    calibration_path = _resolve_calibration(args.calibration)
    manifest_path = _resolve_repo_file(args.manifest, expected=DEFAULT_MANIFEST)
    output_path = _resolve_repo_file(args.output, expected=DEFAULT_OUTPUT)
    if args.verify:
        profile = load_strict_json(output_path)
        verify_calibration_profile(
            profile,
            calibration_path=calibration_path,
            manifest_path=manifest_path,
        )
        status = "verified"
    elif args.refresh_derived:
        predecessor = load_strict_json(output_path)
        if predecessor.get("identity_sha256") != EXPECTED_PREDECESSOR_IDENTITY:
            raise ValueError("Tracked calibration profile is not the exact predecessor")
        profile = build_calibration_profile(
            calibration_path=calibration_path,
            manifest_path=manifest_path,
        )
        dump_canonical_json(output_path, profile)
        verify_calibration_profile(
            profile,
            calibration_path=calibration_path,
            manifest_path=manifest_path,
        )
        status = "refreshed"
    else:
        if output_path.exists():
            raise ValueError("Tracked calibration profile already exists; use --verify")
        profile = build_calibration_profile(
            calibration_path=calibration_path,
            manifest_path=manifest_path,
        )
        dump_canonical_json(output_path, profile)
        status = "written"
    print(
        json.dumps(
            {
                "status": status,
                "schema_version": profile["schema_version"],
                "identity_sha256": profile["identity_sha256"],
                "joint_count": profile["joint_count"],
                "physical_follower_commanded": profile[
                    "physical_follower_commanded"
                ],
                "motion_authority_granted": profile["motion_authority_granted"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve_calibration(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved != DEFAULT_CALIBRATION.resolve():
        raise ValueError("Calibration path is not the pinned follower calibration")
    if not resolved.is_file():
        raise ValueError("Pinned follower calibration file is missing")
    return resolved


def _resolve_repo_file(path: Path, *, expected: Path) -> Path:
    resolved = (path if path.is_absolute() else REPO_ROOT / path).resolve()
    if resolved != (REPO_ROOT / expected).resolve():
        raise ValueError(f"Path is not canonical: {expected}")
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())
