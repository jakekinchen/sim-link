#!/usr/bin/env python3
"""Run dependency-backed expert and renderer smoke stages for bootstrap."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = (
    SCRIPT_PATH.parents[1]
    if SCRIPT_PATH.parent.name == "tools"
    else SCRIPT_PATH.parents[2]
)
ASSET_ROOT = REPO_ROOT / "reconstruction-kit/assets"
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.scripted_grasp_episode_generation import (  # noqa: E402
    EPISODE_SPECS,
    default_store_root,
    generate_episode_payload,
)


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_expert(output_root: Path) -> dict[str, Any]:
    store = default_store_root(repo_root=REPO_ROOT)
    if store.exists() or store.is_symlink():
        raise FileExistsError(f"bootstrap expert store already exists: {store}")
    store.mkdir(parents=True, exist_ok=False)
    payload = generate_episode_payload(dict(EPISODE_SPECS[0]))
    temporary = store / ".seed0.tmp.json"
    dump_canonical_json(temporary, payload)
    digest = _sha_file(temporary)
    destination = store / f"{digest}.json"
    os.replace(temporary, destination)
    outcome = payload["outcome"]
    if outcome.get("strict_success") is not True:
        raise ValueError("bootstrap expert seed 0 did not pass strict-v2")
    receipt = sign_payload(
        {
            "schema_version": "scenesmith.reconstruction_bootstrap_expert.v1",
            "seed": 0,
            "episode_path": destination.relative_to(REPO_ROOT).as_posix(),
            "episode_file_sha256": digest,
            "raw_rollout_record_identity_sha256": payload["raw_rollout"][
                "record_identity_sha256"
            ],
            "frame_count": len(payload["frames"]),
            "terminal_outcome": outcome["terminal_outcome"],
            "strict_success": True,
            "training_eligible": False,
            "simulation_training_ready": False,
            "optimizer_training": False,
            "physical_actuation": False,
        }
    )
    receipt_path = output_root / "expert_seed0_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(receipt_path, receipt)
    return {
        "receipt_path": receipt_path.relative_to(REPO_ROOT).as_posix(),
        "receipt_identity_sha256": receipt["identity_sha256"],
        "episode_file_sha256": digest,
        "frame_count": len(payload["frames"]),
        "strict_success": True,
    }


def _renderer_smokes(output_root: Path) -> list[dict[str, Any]]:
    asset_manifest = load_strict_json(ASSET_ROOT / "ASSET_MANIFEST.json")
    rows = []
    for fixture in asset_manifest["trace_fixtures"]:
        trace = ASSET_ROOT / fixture["asset_path"]
        output = output_root / "renderer_smokes" / f"{fixture['name']}.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                sys.executable,
                "scripts/robot_lab/render_rollout_mirror_v2.py",
                "--trace",
                str(trace),
                "--output-mp4",
                str(output),
                "--max-frames",
                "1",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        render_manifest_path = output.with_suffix(".manifest.json")
        render_manifest = load_strict_json(render_manifest_path)
        verify_signed_payload(render_manifest, label="bootstrap renderer smoke")
        if (
            render_manifest.get("trace_identity_sha256") != fixture["identity_sha256"]
            or render_manifest.get("frame_count") != 1
            or render_manifest.get("output_sha256") != _sha_file(output)
            or render_manifest.get("output_bytes") != output.stat().st_size
        ):
            raise ValueError(f"renderer smoke evidence drifted: {fixture['name']}")
        rows.append(
            {
                "name": fixture["name"],
                "trace_schema_version": fixture["schema_version"],
                "trace_identity_sha256": fixture["identity_sha256"],
                "render_manifest_identity_sha256": render_manifest["identity_sha256"],
                "output_sha256": render_manifest["output_sha256"],
                "output_bytes": render_manifest["output_bytes"],
                "frame_count": 1,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    rehearse = subparsers.add_parser("rehearse")
    rehearse.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    try:
        output_root.relative_to(REPO_ROOT.resolve())
    except ValueError as error:
        raise ValueError("bootstrap output root escapes the repository") from error
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"bootstrap output already exists: {output_root}")
    expert = _write_expert(output_root)
    smokes = _renderer_smokes(output_root)
    asset_manifest = load_strict_json(ASSET_ROOT / "ASSET_MANIFEST.json")
    print(
        json.dumps(
            {
                "portable_asset_manifest_identity_sha256": asset_manifest[
                    "identity_sha256"
                ],
                "expert_episode": expert,
                "renderer_smokes": smokes,
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
