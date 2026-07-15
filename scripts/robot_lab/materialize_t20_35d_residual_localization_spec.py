#!/usr/bin/env python3
"""Materialize or verify the T20.35d replay specification and permit."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json  # noqa: E402
from scenesmith.robot_lab.t20_35d_decoded_action_residual_localization import (  # noqa: E402
    PERMIT_PATH,
    SPEC_PATH,
    build_evaluation_permit,
    load_and_verify_sources,
    verify_evaluation_files,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        result = verify_evaluation_files(repo_root=REPO_ROOT)
        spec = result["evaluation_spec"]
        permit = result["evaluation_permit"]
    else:
        result = load_and_verify_sources(repo_root=REPO_ROOT)
        spec = result["evaluation_spec"]
        permit = build_evaluation_permit(spec=spec)
        dump_canonical_json(REPO_ROOT / SPEC_PATH, spec)
        dump_canonical_json(REPO_ROOT / PERMIT_PATH, permit)
    print(spec["identity_sha256"], permit["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
