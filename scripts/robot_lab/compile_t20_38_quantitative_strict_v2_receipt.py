#!/usr/bin/env python3
"""Write or verify the T20.38 quantitative strict-v2 receipt."""

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
from scenesmith.robot_lab.quantitative_strict_v2_receipt import (  # noqa: E402
    RECEIPT_PATH,
    build_quantitative_receipt,
    load_verified_sources,
    verify_quantitative_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--rewrite-derived",
        action="store_true",
        help="Rewrite only the checked-in derived receipt after a reviewed schema change.",
    )
    args = parser.parse_args()
    sources = load_verified_sources(repo_root=REPO_ROOT)
    expected = build_quantitative_receipt(sources=sources)
    if args.verify:
        payload = load_strict_json(REPO_ROOT / RECEIPT_PATH)
        verify_quantitative_receipt(payload, sources=sources)
    else:
        if (REPO_ROOT / RECEIPT_PATH).exists() and not args.rewrite_derived:
            raise FileExistsError("T20.38 quantitative receipt already exists")
        dump_canonical_json(REPO_ROOT / RECEIPT_PATH, expected)
    print(expected["identity_sha256"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
