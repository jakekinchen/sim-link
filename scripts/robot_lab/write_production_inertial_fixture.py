#!/usr/bin/env python3
"""Write or verify the deterministic production-schema inertial fixture."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.production_inertial_compiler import (
    DEFAULT_PRODUCTION_FIXTURE_PATH,
    DEFAULT_PRODUCTION_OUTPUT_FIXTURE_PATH,
    verify_production_fixture_artifacts,
    write_production_fixture_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--intake", type=Path, default=DEFAULT_PRODUCTION_FIXTURE_PATH)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PRODUCTION_OUTPUT_FIXTURE_PATH,
    )
    args = parser.parse_args()
    if args.verify:
        artifacts = verify_production_fixture_artifacts(
            repo_root=REPO_ROOT,
            intake_path=args.intake,
            output_path=args.output,
        )
        status = "verified"
    else:
        artifacts = write_production_fixture_artifacts(
            repo_root=REPO_ROOT,
            intake_path=args.intake,
            output_path=args.output,
        )
        status = "written"
    print(
        json.dumps(
            {
                "status": status,
                "intake": str(args.intake),
                "output": str(args.output),
                "intake_identity_sha256": artifacts["intake"]["identity_sha256"],
                "output_identity_sha256": artifacts["output"]["identity_sha256"],
                "qualification_scope": artifacts["output"]["qualification_scope"],
                "capabilities": artifacts["output"]["capabilities"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
