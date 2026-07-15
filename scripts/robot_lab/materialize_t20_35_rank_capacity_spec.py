#!/usr/bin/env python3
"""Materialize or verify the T20.35 rank-capacity specification."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json  # noqa: E402
from scenesmith.robot_lab.t20_35_rank_capacity_discriminator import (  # noqa: E402
    SPEC_PATH,
    verify_preflight,
    verify_training_spec_file,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        payload = verify_training_spec_file(repo_root=REPO_ROOT)
    else:
        payload = verify_preflight(repo_root=REPO_ROOT)["training_spec"]
        dump_canonical_json(REPO_ROOT / SPEC_PATH, payload)
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
