#!/usr/bin/env python3
"""Write or verify the T20.43c same-agent pre-run acceptance."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json  # noqa: E402
from scenesmith.robot_lab.t20_43c_act_continuation import (  # noqa: E402
    ACCEPTANCE_PATH,
    PERMIT_PATH,
    build_acceptance,
    verify_acceptance,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--authority-commit")
    parser.add_argument("--reviewer-decision-id")
    parser.add_argument("--reviewer-path", type=Path)
    args = parser.parse_args()
    permit = load_strict_json(REPO_ROOT / PERMIT_PATH)
    if args.verify:
        payload = load_strict_json(REPO_ROOT / ACCEPTANCE_PATH)
        verify_acceptance(payload, permit=permit)
    else:
        if not all(
            (args.authority_commit, args.reviewer_decision_id, args.reviewer_path)
        ):
            parser.error(
                "acceptance requires authority commit, reviewer id, and reviewer path"
            )
        reviewer = REPO_ROOT / args.reviewer_path
        if not reviewer.is_file() or reviewer.is_symlink():
            raise FileNotFoundError("T20.43c reviewer decision is absent or aliased")
        if os.path.lexists(REPO_ROOT / ACCEPTANCE_PATH):
            raise FileExistsError("T20.43c pre-run acceptance already exists")
        payload = build_acceptance(
            authority_commit=args.authority_commit,
            reviewer_decision_id=args.reviewer_decision_id,
            reviewer_path=args.reviewer_path.as_posix(),
            reviewer_file_sha256=hashlib.sha256(reviewer.read_bytes()).hexdigest(),
            permit=permit,
        )
        dump_canonical_json(REPO_ROOT / ACCEPTANCE_PATH, payload)
        verify_acceptance(load_strict_json(REPO_ROOT / ACCEPTANCE_PATH), permit=permit)
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
