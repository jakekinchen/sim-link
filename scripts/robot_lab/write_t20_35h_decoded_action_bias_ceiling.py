#!/usr/bin/env python3
"""Write or verify the model-free T20.35h decoded-action bias ceiling."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_35h_decoded_action_bias_ceiling import (  # noqa: E402
    verify_bias_ceiling_file,
    write_bias_ceiling,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = (
        verify_bias_ceiling_file(repo_root=REPO_ROOT)
        if args.verify
        else write_bias_ceiling(repo_root=REPO_ROOT)
    )
    print(result["identity_sha256"], result["selected_next_hypothesis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
