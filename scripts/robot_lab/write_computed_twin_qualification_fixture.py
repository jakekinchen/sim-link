#!/usr/bin/env python3
"""Write or verify the deterministic computed twin-qualification fixture."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.computed_twin_qualification import (
    verify_qualification_fixture_artifacts,
    write_qualification_fixture_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        bundle = verify_qualification_fixture_artifacts(repo_root=REPO_ROOT)
        status = "verified"
    else:
        bundle = write_qualification_fixture_artifacts(repo_root=REPO_ROOT)
        status = "written"
    print(
        json.dumps(
            {
                "status": status,
                "spec_identity_sha256": bundle["spec"]["identity_sha256"],
                "input_identity_sha256": bundle["input"]["identity_sha256"],
                "report_identity_sha256": bundle["report"]["identity_sha256"],
                "capabilities": bundle["report"]["capabilities"],
                "authority_granted": bundle["decision"]["authority_granted"],
                "authority_withheld": bundle["decision"]["authority_withheld"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
