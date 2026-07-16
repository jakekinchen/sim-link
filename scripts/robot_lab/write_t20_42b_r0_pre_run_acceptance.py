#!/usr/bin/env python3
"""Write or verify the signed T20.42b pre-run reviewer acceptance."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import load_strict_json  # noqa: E402
from scenesmith.robot_lab.t20_42b_r0_runner import (  # noqa: E402
    PRE_RUN_ACCEPTANCE_PATH,
    verify_pre_run_acceptance,
    write_pre_run_acceptance,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--authority-commit")
    args = parser.parse_args()
    if args.write:
        if not args.authority_commit:
            parser.error("--write requires --authority-commit")
        payload = write_pre_run_acceptance(
            authority_commit=args.authority_commit, repo_root=REPO_ROOT
        )
    else:
        payload = load_strict_json(REPO_ROOT / PRE_RUN_ACCEPTANCE_PATH)
        verify_pre_run_acceptance(
            payload, repo_root=REPO_ROOT, require_head_preserved=True
        )
    print(
        json.dumps(
            {
                "status": "verified",
                "decision": payload["decision"],
                "identity_sha256": payload["identity_sha256"],
                "authority_commit": payload["authority_commit"],
                "attempt_marker_exists_at_review": payload[
                    "attempt_marker_exists_at_review"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
