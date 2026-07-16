#!/usr/bin/env python3
"""Write or verify the model-free T20.43b ACT standard-rung specification."""

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
from scenesmith.robot_lab.t20_43b_r1_act_contracts import (  # noqa: E402
    SPEC_PATH,
    build_spec,
    load_verified_sources,
    verify_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_verified_sources(repo_root=REPO_ROOT)
    expected = build_spec(sources=sources)
    if args.verify:
        payload = load_strict_json(REPO_ROOT / SPEC_PATH)
        verify_spec(payload, sources=sources)
    else:
        if (REPO_ROOT / SPEC_PATH).exists():
            raise FileExistsError("T20.43b spec already exists")
        dump_canonical_json(REPO_ROOT / SPEC_PATH, expected)
        payload = load_strict_json(REPO_ROOT / SPEC_PATH)
        verify_spec(payload, sources=sources)
    print(payload["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
