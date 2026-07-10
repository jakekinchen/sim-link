#!/usr/bin/env python3
"""Write or verify the tracked structural twin diff artifact."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.structural_twin_diff import (
    DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
    verify_structural_twin_diff,
    write_structural_twin_diff,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
        help="Artifact path to write or verify.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the tracked artifact instead of rewriting it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output

    if args.verify:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        verify_structural_twin_diff(payload, repo_root=REPO_ROOT)
        print(
            json.dumps(
                {
                    "status": "verified",
                    "artifact": str(args.output),
                    "identity_sha256": payload["identity_sha256"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    payload = write_structural_twin_diff(repo_root=REPO_ROOT, output_path=args.output)
    print(
        json.dumps(
            {
                "status": "written",
                "artifact": str(args.output),
                "identity_sha256": payload["identity_sha256"],
                "summary": payload["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
