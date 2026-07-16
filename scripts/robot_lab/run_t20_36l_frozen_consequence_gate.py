#!/usr/bin/env python3
"""Materialize or verify the frozen T20.36l consequence Gate B artifacts."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json  # noqa: E402
from scenesmith.robot_lab.t20_36l_frozen_consequence_gate import (  # noqa: E402
    OWNER_DECISION_PATH,
    RESULT_PATH,
    SPEC_PATH,
    build_artifacts,
    verify_owner_decision,
    verify_result,
    verify_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        owner = load_strict_json(REPO_ROOT / OWNER_DECISION_PATH)
        spec = load_strict_json(REPO_ROOT / SPEC_PATH)
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_owner_decision(owner)
        verify_spec(spec)
        verify_result(result, spec=spec)
        print(result["identity_sha256"], result["decision"])
        return 0
    owner, spec, result = build_artifacts(repo_root=REPO_ROOT)
    dump_canonical_json(REPO_ROOT / OWNER_DECISION_PATH, owner)
    dump_canonical_json(REPO_ROOT / SPEC_PATH, spec)
    dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    verify_owner_decision(owner)
    verify_spec(spec)
    verify_result(result, spec=spec)
    print(result["identity_sha256"], result["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
