#!/usr/bin/env python3
"""Write or verify the T19.2 physical calibration readiness matrix."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json
from scenesmith.robot_lab.t19_2_calibration_readiness import (
    build_t19_2_calibration_readiness,
    verify_t19_2_calibration_readiness,
)


DEFAULT_STATE = Path("docs/autonomous-workflow/project_state.json")
DEFAULT_OUTPUT = Path("configurations/robot_lab/t19_2_calibration_readiness.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--project-state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    state = load_strict_json(REPO_ROOT / args.project_state)
    output = (REPO_ROOT / args.output).resolve()
    if not output.is_relative_to((REPO_ROOT / "configurations/robot_lab").resolve()):
        raise ValueError("T19.2 readiness output escaped configurations/robot_lab")
    if args.verify:
        payload = load_strict_json(output)
        verify_t19_2_calibration_readiness(
            payload, repo_root=REPO_ROOT, project_state=state
        )
        status = "verified"
    else:
        if output.exists():
            raise ValueError("T19.2 readiness output exists; use --verify")
        payload = build_t19_2_calibration_readiness(
            repo_root=REPO_ROOT, project_state=state
        )
        dump_canonical_json(output, payload)
        status = "written"
    print(json.dumps({"status": status, "identity_sha256": payload["identity_sha256"], "calibration_session_ready": payload["calibration_session_ready"], "missing_prerequisite_ids": payload["missing_prerequisite_ids"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
