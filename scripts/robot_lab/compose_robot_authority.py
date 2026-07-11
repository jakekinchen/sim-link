#!/usr/bin/env python3
"""Compose or verify fail-closed SceneSmith robot-lab authority decisions."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.authority_composer import (
    DEFAULT_AUTHORITY_CONTRACT_PATH,
    DEFAULT_AUTHORITY_DECISION_PATH,
    DEFAULT_EVALUATION_TIME,
    build_current_authority_decision,
    verify_authority_artifacts,
    write_authority_artifacts,
)
from scenesmith.robot_lab.measured_inertial_intake import (
    DEFAULT_ASSEMBLY_INERTIALS_PATH,
    DEFAULT_MEASURED_MASS_INTAKE_PATH,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--verify", action="store_true")
    action.add_argument("--write", action="store_true")
    parser.add_argument("--contract", type=Path, default=DEFAULT_AUTHORITY_CONTRACT_PATH)
    parser.add_argument("--decision", type=Path, default=DEFAULT_AUTHORITY_DECISION_PATH)
    parser.add_argument("--intake", type=Path, default=DEFAULT_MEASURED_MASS_INTAKE_PATH)
    parser.add_argument(
        "--inertial-artifact",
        type=Path,
        default=DEFAULT_ASSEMBLY_INERTIALS_PATH,
    )
    parser.add_argument("--evaluation-time", default=DEFAULT_EVALUATION_TIME)
    parser.add_argument(
        "--decision-output",
        type=Path,
        help="Optional output for a custom composed decision; never rewrites component evidence.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify:
        payload = verify_authority_artifacts(
            repo_root=REPO_ROOT,
            contract_path=args.contract,
            decision_path=args.decision,
        )["decision"]
    elif args.write:
        payload = write_authority_artifacts(
            repo_root=REPO_ROOT,
            contract_path=args.contract,
            decision_path=args.decision,
        )["decision"]
    else:
        _, payload = build_current_authority_decision(
            repo_root=REPO_ROOT,
            inertial_artifact_path=args.inertial_artifact,
            intake_path=args.intake,
            evaluation_time=args.evaluation_time,
        )
        if args.decision_output is not None:
            from scenesmith.robot_lab.artifact_contract import dump_canonical_json

            dump_canonical_json(_resolve(args.decision_output), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
