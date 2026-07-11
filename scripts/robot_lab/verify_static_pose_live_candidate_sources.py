#!/usr/bin/env python3
"""Verify accepted private discovery resolves the static-pose candidate sources."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
)
from scenesmith.robot_lab.live_readonly_observation import resolve_follower_identity
from scenesmith.robot_lab.static_pose_live_candidate import (
    resolve_static_pose_candidate_cameras,
)


DEFAULT_DISCOVERY = Path(
    "outputs/robot_lab/live_readonly/private/"
    "t16-5b-20260711-1124-cdt/discovery.json"
)
DEFAULT_MANIFEST = Path(
    "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
DEFAULT_CONTRACT = Path(
    "configurations/robot_lab/pi05_static_pose_bracket_contract.json"
)
EXPECTED_DISCOVERY_IDENTITY = (
    "b57fbec85db582fd29978d0fae227a5daee98ef74f80f50b8658cb1024b044b3"
)
EXPECTED_DISCOVERY_FILE_SHA256 = (
    "3372b817e7e39844130daa0b6fd46843df98dca17abf82ed791e661d4d3caba5"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discovery", type=Path, default=DEFAULT_DISCOVERY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    discovery_path = _resolve_exact(args.discovery, expected=DEFAULT_DISCOVERY)
    manifest_path = _resolve_exact(args.manifest, expected=DEFAULT_MANIFEST)
    contract_path = _resolve_exact(args.contract, expected=DEFAULT_CONTRACT)
    discovery = load_strict_json(discovery_path)
    manifest = load_strict_json(manifest_path)
    contract = load_strict_json(contract_path)
    if (
        discovery.get("identity_sha256") != EXPECTED_DISCOVERY_IDENTITY
        or hashlib.sha256(discovery_path.read_bytes()).hexdigest()
        != EXPECTED_DISCOVERY_FILE_SHA256
    ):
        raise ValueError("Accepted private discovery identity drifted")

    follower = resolve_follower_identity(discovery)
    follower_usb_hash = hashlib.sha256(
        canonical_json_bytes(follower["usb"])
    ).hexdigest()
    if follower_usb_hash != manifest.get("usb_identity_sha256"):
        raise ValueError("Accepted discovery follower USB identity drifted")

    resolved = resolve_static_pose_candidate_cameras(
        discovery=discovery,
        static_pose_contract=contract,
    )
    churned = copy.deepcopy(discovery)
    for offset, device in enumerate(churned["avfoundation_devices"], start=1):
        device["index"] += offset * 10
    churned = sign_payload(churned)
    churned_resolved = resolve_static_pose_candidate_cameras(
        discovery=churned,
        static_pose_contract=contract,
    )
    stable = [item["stable_camera_identity_sha256"] for item in resolved]
    churned_stable = [
        item["stable_camera_identity_sha256"] for item in churned_resolved
    ]
    capture = [item["capture_camera_identity_sha256"] for item in resolved]
    churned_capture = [
        item["capture_camera_identity_sha256"] for item in churned_resolved
    ]
    if stable != churned_stable or capture == churned_capture:
        raise ValueError("Numeric index churn camera identity separation failed")

    print(
        json.dumps(
            {
                "status": "verified",
                "discovery_identity_sha256": discovery["identity_sha256"],
                "follower_usb_identity_sha256": follower_usb_hash,
                "stable_camera_identity_sha256": stable,
                "resolved_numeric_indexes": [
                    item["resolved_camera"]["index"] for item in resolved
                ],
                "churned_numeric_indexes": [
                    item["resolved_camera"]["index"]
                    for item in churned_resolved
                ],
                "hardware_enumerated": False,
                "hardware_opened": False,
                "physical_follower_commanded": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve_exact(path: Path, *, expected: Path) -> Path:
    resolved = (path if path.is_absolute() else REPO_ROOT / path).resolve()
    if resolved != (REPO_ROOT / expected).resolve():
        raise ValueError(f"Path is not canonical: {expected}")
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())
