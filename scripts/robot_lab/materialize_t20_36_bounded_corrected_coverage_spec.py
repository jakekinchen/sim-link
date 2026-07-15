#!/usr/bin/env python3
"""Materialize or verify the T20.36 bounded corrected-coverage spec."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.t20_36_bounded_corrected_coverage import (  # noqa: E402
    SPEC_PATH,
    build_training_spec,
    load_source_artifacts,
    verify_training_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_source_artifacts(repo_root=REPO_ROOT)
    if args.verify:
        payload = load_strict_json(REPO_ROOT / SPEC_PATH)
        verify_training_spec(payload, **sources)
    else:
        if (REPO_ROOT / SPEC_PATH).exists():
            raise FileExistsError("T20.36 immutable training spec already exists")
        payload = build_training_spec(**sources)
        dump_canonical_json(REPO_ROOT / SPEC_PATH, payload)
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
