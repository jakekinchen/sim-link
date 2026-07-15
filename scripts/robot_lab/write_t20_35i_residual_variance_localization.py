#!/usr/bin/env python3
"""Write or verify the model-free T20.35i variance localization."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_35i_residual_variance_localization import (  # noqa: E402
    verify_variance_localization_file,
    write_variance_localization,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = (
        verify_variance_localization_file(repo_root=REPO_ROOT)
        if args.verify
        else write_variance_localization(repo_root=REPO_ROOT)
    )
    print(result["identity_sha256"], result["selected_next_hypothesis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
