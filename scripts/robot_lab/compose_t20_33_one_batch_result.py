#!/usr/bin/env python3
"""Compose or verify the T20.33 Gate B result."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json  # noqa: E402
from scenesmith.robot_lab.t20_33_one_batch_memorization import (  # noqa: E402
    RESULT_PATH,
    build_result,
    verify_result,
    verify_training_spec_file,
)
from scenesmith.robot_lab.t20_33_simulation_training_authority import (  # noqa: E402
    require_active_authority,
)
from scripts.robot_lab.run_t20_33_one_batch_memorization import SUMMARY_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    spec = verify_training_spec_file(repo_root=REPO_ROOT)
    authority = require_active_authority(repo_root=REPO_ROOT)["decision"]
    run = load_strict_json(SUMMARY_PATH)
    if args.verify:
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_result(result, spec=spec, run=run)
    else:
        result = build_result(
            spec=spec,
            authority_identity=authority["identity_sha256"],
            run=run,
        )
        dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    print(result["identity_sha256"], result["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
