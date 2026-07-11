#!/usr/bin/env python3
"""Verify the unified SceneSmith LeRobot stack and saved-sample parity."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.lerobot_stack import build_stack_identity, process_saved_sample


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample",
        type=Path,
        default=REPO_ROOT / "tests/fixtures/robot_lab/lerobot_stack/sample.json",
    )
    args = parser.parse_args()
    sample_path = args.sample if args.sample.is_absolute() else REPO_ROOT / args.sample
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    identity = build_stack_identity(repo_root=REPO_ROOT)
    processed = {
        stage: process_saved_sample(sample, repo_root=REPO_ROOT, stage=stage)
        for stage in ("collection", "training", "inference")
    }
    comparable = [
        {key: value for key, value in result.items() if key != "stage"}
        for result in processed.values()
    ]
    if not all(result == comparable[0] for result in comparable[1:]):
        raise ValueError("Collection, training, and inference processor outputs diverged")
    report = {
        "status": "pass",
        "stack_identity_sha256": identity["identity_sha256"],
        "base_revision": identity["base_revision"],
        "patch_set_sha256": identity["patch_set_sha256"],
        "environment_lock_sha256": identity["environment_lock"]["sha256"],
        "sample": str(sample_path),
        "processor_stages": list(processed),
        "observation_state_tensor": processed["collection"]["observation_state_tensor"],
        "action_tensor": processed["collection"]["action_tensor"],
    }
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
