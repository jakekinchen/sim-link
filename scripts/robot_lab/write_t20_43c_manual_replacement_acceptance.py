#!/usr/bin/env python3
"""Write the one-use T20.43c-R2 acceptance after reviewer preservation."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_43c_manual_replacement import write_acceptance  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-commit", required=True)
    parser.add_argument("--reviewer-decision-id", required=True)
    parser.add_argument("--reviewer-path", required=True)
    args = parser.parse_args()
    acceptance = write_acceptance(
        authority_commit=args.authority_commit,
        reviewer_decision_id=args.reviewer_decision_id,
        reviewer_path=args.reviewer_path,
        repo_root=REPO_ROOT,
    )
    print(json.dumps(acceptance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
