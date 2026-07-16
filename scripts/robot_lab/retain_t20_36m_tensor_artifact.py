#!/usr/bin/env python3
"""Write or verify the tracked T20.36m tensor-retention receipt."""

from __future__ import annotations

import argparse
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.t20_36h_smolvla_batch import load_smolvla_batch  # noqa: E402
from scenesmith.robot_lab.t20_36m_tensor_reproduction import (  # noqa: E402
    load_verified_sources,
)
from scenesmith.robot_lab.t20_36m_tensor_retention import (  # noqa: E402
    verify_retention_receipt,
    write_retention_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        receipt = verify_retention_receipt(repo_root=REPO_ROOT)
    else:
        sources = load_verified_sources(repo_root=REPO_ROOT)
        batch = load_smolvla_batch(repo_root=REPO_ROOT, spec=sources["smolvla_spec"])
        receipt = write_retention_receipt(
            target=batch["physical_action"].astype(float).tolist(),
            repo_root=REPO_ROOT,
        )
    print(receipt["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
