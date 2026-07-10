#!/usr/bin/env python3
"""Write or verify the tracked simulation-only twin contract examples."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.twin_contract import (
    DEFAULT_DEPENDENCY_LOCK_PATH,
    DEFAULT_TWIN_PROFILE_PATH,
    DEFAULT_TWIN_QUALIFICATION_REPORT_PATH,
    DEFAULT_TWIN_QUALIFICATION_SPEC_PATH,
    verify_twin_contract_examples,
    write_twin_contract_examples,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--dependency-lock", type=Path, default=DEFAULT_DEPENDENCY_LOCK_PATH)
    parser.add_argument("--profile-output", type=Path, default=DEFAULT_TWIN_PROFILE_PATH)
    parser.add_argument("--spec-output", type=Path, default=DEFAULT_TWIN_QUALIFICATION_SPEC_PATH)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_TWIN_QUALIFICATION_REPORT_PATH)
    args = parser.parse_args()
    profile_path = _resolve(args.profile_output)
    spec_path = _resolve(args.spec_output)
    report_path = _resolve(args.report_output)
    dependency_lock_path = _resolve(args.dependency_lock)
    if args.verify:
        payload = verify_twin_contract_examples(
            repo_root=REPO_ROOT,
            profile_path=profile_path.relative_to(REPO_ROOT),
            spec_path=spec_path.relative_to(REPO_ROOT),
            report_path=report_path.relative_to(REPO_ROOT),
            dependency_lock_path=dependency_lock_path.relative_to(REPO_ROOT),
        )
    else:
        payload = write_twin_contract_examples(
            repo_root=REPO_ROOT,
            profile_path=profile_path.relative_to(REPO_ROOT),
            spec_path=spec_path.relative_to(REPO_ROOT),
            report_path=report_path.relative_to(REPO_ROOT),
            dependency_lock_path=dependency_lock_path.relative_to(REPO_ROOT),
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
