#!/usr/bin/env python3
"""Write or verify the T20.35n near-zero active-noise scale spec."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_35n_near_zero_active_noise_scale_discriminator import (  # noqa: E402
    load_and_verify_evaluation_files,
    write_evaluation_files,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    files = (
        load_and_verify_evaluation_files(repo_root=REPO_ROOT)
        if args.verify
        else write_evaluation_files(repo_root=REPO_ROOT)
    )
    spec = files["active_scale_spec"]
    permit = files["active_scale_permit"]
    print(spec["identity_sha256"], permit["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
