#!/usr/bin/env python3
"""Write or verify the T20.35l active-versus-padded noise-mask spec."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_35l_active_padded_noise_mask_discriminator import (  # noqa: E402
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
    spec = files["noise_mask_spec"]
    permit = files["noise_mask_permit"]
    print(spec["identity_sha256"], permit["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
