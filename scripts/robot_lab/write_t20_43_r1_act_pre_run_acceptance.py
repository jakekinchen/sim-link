#!/usr/bin/env python3
"""Write or verify signed Reviewer acceptance for the sole T20.43 attempt."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.t20_43_r1_act_contracts import (  # noqa: E402
    PERMIT_PATH,
    PRE_RUN_ACCEPTANCE_PATH,
    build_pre_run_acceptance,
    verify_pre_run_acceptance,
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
        payload = load_strict_json(REPO_ROOT / PRE_RUN_ACCEPTANCE_PATH)
        verify_pre_run_acceptance(payload, permit=permit)
    else:
        if not all(
            (
                args.authority_commit,
                args.reviewer_decision_id,
                args.reviewer_path,
            )
        ):
            parser.error(
                "acceptance requires authority commit, reviewer id, and reviewer path"
            )
        reviewer = REPO_ROOT / args.reviewer_path
        if not reviewer.is_file() or reviewer.is_symlink():
            raise FileNotFoundError("T20.43 reviewer decision is absent or aliased")
        payload = build_pre_run_acceptance(
            authority_commit=args.authority_commit,
            reviewer_decision_id=args.reviewer_decision_id,
            reviewer_path=args.reviewer_path.as_posix(),
            reviewer_file_sha256=hashlib.sha256(reviewer.read_bytes()).hexdigest(),
            permit=permit,
        )
        if (REPO_ROOT / PRE_RUN_ACCEPTANCE_PATH).exists():
            raise FileExistsError("T20.43 pre-run acceptance already exists")
        dump_canonical_json(REPO_ROOT / PRE_RUN_ACCEPTANCE_PATH, payload)
        payload = load_strict_json(REPO_ROOT / PRE_RUN_ACCEPTANCE_PATH)
        verify_pre_run_acceptance(payload, permit=permit)
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
