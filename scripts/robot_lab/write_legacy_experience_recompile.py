#!/usr/bin/env python3
"""Write or verify the immutable T17.6 legacy-canary audit and empty view."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.experience_compiler import OUTPUT_NAMES, verify_compilation  # noqa: E402
from scenesmith.robot_lab.legacy_experience_recompile import (  # noqa: E402
    DEFAULT_LEGACY_ROOT,
    build_legacy_inventory_manifest,
    compile_legacy_inventory,
    verify_legacy_inventory_manifest,
)


MANIFEST_PATH = REPO_ROOT / "configurations/robot_lab/t17_6_legacy_inventory_manifest.json"
OUTPUT_DIR = REPO_ROOT / "configurations/robot_lab/t17_6_legacy_compile"


def _all_outputs_exist() -> bool:
    return all((OUTPUT_DIR / name).is_file() for name in OUTPUT_NAMES)


def _manifest_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_outputs(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_NAMES:
        os.replace(source / name, destination / name)


def _write() -> dict:
    if MANIFEST_PATH.exists() or _all_outputs_exist():
        raise ValueError("T17.6 legacy artifacts already exist; use --verify")
    if any((OUTPUT_DIR / name).exists() for name in OUTPUT_NAMES):
        raise ValueError("T17.6 legacy compiler output is incomplete; refuse to overwrite")
    manifest = build_legacy_inventory_manifest(DEFAULT_LEGACY_ROOT)
    verify_legacy_inventory_manifest(manifest, DEFAULT_LEGACY_ROOT)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="scenesmith-t17-6-", dir=MANIFEST_PATH.parent) as directory:
        temporary = Path(directory)
        temporary_manifest = temporary / MANIFEST_PATH.name
        temporary_output = temporary / "compile"
        dump_canonical_json(temporary_manifest, manifest)
        compile_legacy_inventory(
            manifest,
            temporary_output,
            inventory_manifest_sha256=_manifest_sha256(temporary_manifest),
        )
        os.replace(temporary_manifest, MANIFEST_PATH)
        _copy_outputs(temporary_output, OUTPUT_DIR)
    verify_compilation(OUTPUT_DIR)
    return manifest


def _verify() -> dict:
    if not MANIFEST_PATH.is_file() or not _all_outputs_exist():
        raise ValueError("T17.6 legacy artifacts are incomplete")
    stored = load_strict_json(MANIFEST_PATH)
    verify_legacy_inventory_manifest(stored, DEFAULT_LEGACY_ROOT)
    with tempfile.TemporaryDirectory(prefix="scenesmith-t17-6-verify-") as directory:
        temporary = Path(directory)
        regenerated = build_legacy_inventory_manifest(DEFAULT_LEGACY_ROOT)
        if canonical_json_bytes(regenerated) != canonical_json_bytes(stored):
            raise ValueError("T17.6 legacy inventory manifest drifted")
        temporary_manifest = temporary / MANIFEST_PATH.name
        dump_canonical_json(temporary_manifest, regenerated)
        temporary_output = temporary / "compile"
        compile_legacy_inventory(
            regenerated,
            temporary_output,
            inventory_manifest_sha256=_manifest_sha256(temporary_manifest),
        )
        for name in OUTPUT_NAMES:
            if (temporary_output / name).read_bytes() != (OUTPUT_DIR / name).read_bytes():
                raise ValueError(f"T17.6 compiler output drifted: {name}")
    verify_compilation(OUTPUT_DIR)
    return stored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument(
        "--rewrite",
        action="store_true",
        help="Rejected: legacy raw bytes are immutable; write a new reviewed task view.",
    )
    args = parser.parse_args()
    if args.rewrite:
        raise ValueError("T17.6 legacy raw bytes are immutable; write a new reviewed task view")
    manifest = _verify() if args.verify else _write()
    print(
        json.dumps(
            {
                "status": "verified" if args.verify else "written",
                "configured_candidate_count": manifest["configured_candidate_count"],
                "accepted_candidate_count": manifest["accepted_candidate_count"],
                "quarantined_candidate_count": manifest["quarantined_candidate_count"],
                "decision": manifest["decision"],
                "training_eligible": manifest["training_eligible"],
                "raw_bytes_rewritten": manifest["raw_bytes_rewritten"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
