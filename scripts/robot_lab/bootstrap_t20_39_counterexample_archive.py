#!/usr/bin/env python3
"""Write or verify the T20.39 counterexample archive bootstrap."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import dump_canonical_json, load_strict_json  # noqa: E402
from scenesmith.robot_lab.counterexample_archive import (  # noqa: E402
    INDEX_PATH,
    RECEIPT_PATH,
    build_archive_index,
    build_receipt_ref,
    build_seed_receipt,
    load_verified_sources,
    verify_archive_index,
    verify_seed_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_verified_sources(repo_root=REPO_ROOT)
    expected_receipt = build_seed_receipt(sources=sources)
    receipt_ref = build_receipt_ref(path=RECEIPT_PATH, payload=expected_receipt)
    expected_index = build_archive_index(
        receipt_refs=[receipt_ref],
        receipts=[expected_receipt],
    )
    if args.verify:
        receipt = load_strict_json(REPO_ROOT / RECEIPT_PATH)
        index = load_strict_json(REPO_ROOT / INDEX_PATH)
        verify_seed_receipt(receipt, sources=sources)
        verify_archive_index(
            index,
            receipt_refs=[build_receipt_ref(path=RECEIPT_PATH, payload=receipt)],
            receipts=[receipt],
        )
    else:
        if (REPO_ROOT / RECEIPT_PATH).exists() or (REPO_ROOT / INDEX_PATH).exists():
            raise FileExistsError("T20.39 counterexample archive output already exists")
        dump_canonical_json(REPO_ROOT / RECEIPT_PATH, expected_receipt)
        dump_canonical_json(REPO_ROOT / INDEX_PATH, expected_index)
    print(expected_receipt["identity_sha256"], expected_index["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
