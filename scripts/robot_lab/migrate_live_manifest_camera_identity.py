#!/usr/bin/env python3
"""Migrate or verify the accepted live manifest's stable camera binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.live_readonly_observation import (
    LEGACY_REDACTED_MANIFEST_SCHEMA_VERSION,
    REDACTED_MANIFEST_SCHEMA_VERSION,
    build_redacted_observation_manifest,
    verify_redacted_observation_manifest,
)


DEFAULT_PRIVATE_BUNDLE = Path(
    "outputs/robot_lab/live_readonly/private/"
    "t16-5b-20260711-1124-cdt/capture"
)
DEFAULT_MANIFEST = Path(
    "configurations/robot_lab/pi05_live_readonly_observation.redacted.json"
)
EXPECTED_LEGACY_MANIFEST_IDENTITY = (
    "eff3c82444efd38b6a2e240b1137846ad835222fd86ed330cf274343e1e28c5f"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--migrate", action="store_true")
    action.add_argument("--verify", action="store_true")
    parser.add_argument("--private-bundle", type=Path, default=DEFAULT_PRIVATE_BUNDLE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    private_bundle = _resolve_exact_repo_path(
        args.private_bundle,
        expected=DEFAULT_PRIVATE_BUNDLE,
    )
    manifest_path = _resolve_exact_repo_path(args.manifest, expected=DEFAULT_MANIFEST)
    manifest = load_strict_json(manifest_path)
    private_evidence_path = private_bundle / "private_observation.json"
    private_evidence = load_strict_json(private_evidence_path)
    private_bundle_refs = manifest.get("private_bundle_refs")
    _verify_private_bundle_files(
        private_bundle,
        private_evidence=private_evidence,
        private_bundle_refs=private_bundle_refs,
    )

    if args.migrate:
        if (
            manifest.get("schema_version")
            != LEGACY_REDACTED_MANIFEST_SCHEMA_VERSION
            or manifest.get("identity_sha256") != EXPECTED_LEGACY_MANIFEST_IDENTITY
        ):
            raise ValueError("Manifest is not the exact accepted v4 migration source")
        verify_redacted_observation_manifest(
            manifest,
            private_evidence=private_evidence,
            private_bundle_refs=private_bundle_refs,
        )
        manifest = build_redacted_observation_manifest(
            private_evidence=private_evidence,
            private_bundle_refs=private_bundle_refs,
        )
        dump_canonical_json(manifest_path, manifest)
        status = "migrated"
    else:
        if manifest.get("schema_version") != REDACTED_MANIFEST_SCHEMA_VERSION:
            raise ValueError("Tracked manifest is not the current stable-binding schema")
        status = "verified"

    verify_redacted_observation_manifest(
        manifest,
        private_evidence=private_evidence,
        private_bundle_refs=private_bundle_refs,
    )
    print(
        json.dumps(
            {
                "status": status,
                "schema_version": manifest["schema_version"],
                "identity_sha256": manifest["identity_sha256"],
                "camera_count": len(manifest["cameras"]),
                "stable_camera_identity_binding": manifest[
                    "camera_identity_binding"
                ]["local_capability"],
                "physical_follower_commanded": manifest[
                    "physical_follower_commanded"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _resolve_exact_repo_path(path: Path, *, expected: Path) -> Path:
    resolved = (path if path.is_absolute() else REPO_ROOT / path).resolve()
    expected_resolved = (REPO_ROOT / expected).resolve()
    if resolved != expected_resolved:
        raise ValueError(f"Path is not canonical: {expected}")
    return resolved


def _verify_private_bundle_files(
    bundle: Path,
    *,
    private_evidence: dict[str, Any],
    private_bundle_refs: dict[str, Any],
) -> None:
    if not isinstance(private_bundle_refs, dict) or set(private_bundle_refs) != {
        "evidence",
        "frames",
    }:
        raise ValueError("Private bundle refs are malformed")
    evidence_ref = private_bundle_refs["evidence"]
    evidence_path = _resolve_bundle_file(bundle, evidence_ref)
    if load_strict_json(evidence_path) != private_evidence:
        raise ValueError("Private evidence file content drifted")
    for frame_ref in private_bundle_refs["frames"]:
        _resolve_bundle_file(bundle, frame_ref)


def _resolve_bundle_file(bundle: Path, reference: dict[str, Any]) -> Path:
    if not isinstance(reference, dict) or set(reference) != {
        "filename",
        "sha256",
        "size_bytes",
    }:
        raise ValueError("Private bundle file ref is malformed")
    filename = reference.get("filename")
    if not isinstance(filename, str) or Path(filename).name != filename:
        raise ValueError("Private bundle filename must be a basename")
    path = bundle / filename
    content = path.read_bytes()
    if (
        len(content) != reference.get("size_bytes")
        or hashlib.sha256(content).hexdigest() != reference.get("sha256")
    ):
        raise ValueError(f"Private bundle file identity drifted: {filename}")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
