#!/usr/bin/env python3
"""Run or verify the bounded model-free T20.36k consequence calibration."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json  # noqa: E402
from scenesmith.robot_lab.t20_36k_consequence_gate_design import (  # noqa: E402
    RESULT_PATH,
    run_design,
    verify_design,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    output = REPO_ROOT / RESULT_PATH
    if args.verify:
        payload = load_strict_json(output)
        verify_design(payload, repo_root=REPO_ROOT)
        print(payload["identity_sha256"], payload["decision"])
        return 0
    payload = run_design(repo_root=REPO_ROOT)
    dump_canonical_json(output, payload)
    print(payload["identity_sha256"], payload["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
