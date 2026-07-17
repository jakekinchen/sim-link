#!/usr/bin/env python3
"""Write or verify the deterministic F0c fork-day-one package."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import load_strict_json  # noqa: E402
from scenesmith.robot_lab.f0c_release_targeted_package import (  # noqa: E402
    SPEC_PATH,
    verify_package,
    write_package,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        payload = load_strict_json(REPO_ROOT / SPEC_PATH)
        verify_package(payload, repo_root=REPO_ROOT)
    else:
        payload = write_package(repo_root=REPO_ROOT)
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
