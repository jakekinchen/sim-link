#!/usr/bin/env python3
"""Write or verify the model-free T20.36o bounded optimizer specification."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_spec import (  # noqa: E402
    SPEC_PATH,
    build_optimizer_spec,
    load_verified_sources,
    verify_optimizer_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_verified_sources(repo_root=REPO_ROOT)
    expected = build_optimizer_spec(sources=sources)
    if args.verify:
        archived = load_strict_json(REPO_ROOT / SPEC_PATH)
        verify_optimizer_spec(archived, sources=sources)
        print(archived["identity_sha256"])
        return 0
    if (REPO_ROOT / SPEC_PATH).exists():
        raise FileExistsError("T20.36o optimizer spec already exists")
    dump_canonical_json(REPO_ROOT / SPEC_PATH, expected)
    verify_optimizer_spec(expected, sources=sources)
    print(expected["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
