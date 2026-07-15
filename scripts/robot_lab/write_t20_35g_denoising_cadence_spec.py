#!/usr/bin/env python3
"""Write or verify the T20.35g denoising-cadence spec and permit."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_35g_denoising_cadence_discriminator import (  # noqa: E402
    load_and_verify_evaluation_files,
    write_evaluation_files,
    write_runtime_correction_files,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verify", action="store_true")
    group.add_argument("--runtime-correction", action="store_true")
    args = parser.parse_args()
    if args.verify:
        result = load_and_verify_evaluation_files(repo_root=REPO_ROOT)
        spec = result["cadence_spec"]
        permit = result["cadence_permit"]
    elif args.runtime_correction:
        result = write_runtime_correction_files(repo_root=REPO_ROOT)
        spec = result["spec"]
        permit = result["permit"]
    else:
        result = write_evaluation_files(repo_root=REPO_ROOT)
        spec = result["spec"]
        permit = result["permit"]
    print(spec["identity_sha256"], permit["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
