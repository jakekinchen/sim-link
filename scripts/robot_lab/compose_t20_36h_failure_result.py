#!/usr/bin/env python3
"""Write or verify T20.36h's tracked consumed-attempt failure result."""

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
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (  # noqa: E402
    ATTEMPT_PATH,
    FAILURE_PATH,
    FAILURE_RESULT_PATH,
    TRAINING_PERMIT_PATH,
    build_failure_result,
    load_verified_spec,
    verify_failure_result,
)
from scenesmith.robot_lab.t20_36h_simulation_training_authority import (  # noqa: E402
    verify_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    spec = load_verified_spec(repo_root=REPO_ROOT)
    authority = verify_authority(repo_root=REPO_ROOT)
    authority_identity = authority["decision"]["identity_sha256"]
    permit = load_strict_json(REPO_ROOT / TRAINING_PERMIT_PATH)
    attempt = load_strict_json(REPO_ROOT / ATTEMPT_PATH)
    failure = load_strict_json(REPO_ROOT / FAILURE_PATH)
    path = REPO_ROOT / FAILURE_RESULT_PATH
    if args.verify:
        result = load_strict_json(path)
        verify_failure_result(
            result,
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
            attempt=attempt,
            failure=failure,
        )
    else:
        if path.exists():
            raise FileExistsError("T20.36h tracked failure result already exists")
        result = build_failure_result(
            spec=spec,
            authority_identity=authority_identity,
            training_permit=permit,
            attempt=attempt,
            failure=failure,
        )
        dump_canonical_json(path, result)
    print(result["identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
