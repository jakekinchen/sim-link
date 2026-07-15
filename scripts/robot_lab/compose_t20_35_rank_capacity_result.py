#!/usr/bin/env python3
"""Compose or verify the T20.35 Gate B rank-capacity result."""

from __future__ import annotations

import argparse
import sys

from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.authority_composer import (  # noqa: E402
    require_global_decision,
    verify_authority_decision,
)
from scenesmith.robot_lab.t20_35_rank_capacity_discriminator import (  # noqa: E402
    RESULT_PATH,
    SPEC_PATH,
    T20_33_SPEC_PATH,
    build_result,
    load_t20_33_result,
    verify_result,
    verify_training_spec,
)
from scenesmith.robot_lab.t20_35_simulation_training_authority import (  # noqa: E402
    DECISION_PATH,
    REQUEST_PATH,
    VALID_FROM,
    VALID_UNTIL,
)
from scripts.robot_lab.run_t20_35_rank_capacity_discriminator import (  # noqa: E402
    SUMMARY_PATH,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    t20_33_spec = load_strict_json(REPO_ROOT / T20_33_SPEC_PATH)
    spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    verify_training_spec(spec, t20_33_spec=t20_33_spec)
    request = load_strict_json(REPO_ROOT / REQUEST_PATH)
    authority = load_strict_json(REPO_ROOT / DECISION_PATH)
    verify_authority_decision(authority, request=request)
    require_global_decision(
        authority, request=request, decision_id="simulation_training_ready"
    )
    if authority.get("authority_granted") != ["simulation_training_ready"]:
        raise ValueError("T20.35 result authority exceeded training-only scope")
    now = datetime.now().astimezone()
    if not datetime.fromisoformat(VALID_FROM) <= now <= datetime.fromisoformat(
        VALID_UNTIL
    ):
        raise ValueError("T20.35 result composition is outside its active window")
    run = load_strict_json(SUMMARY_PATH)
    t20_33_result = load_t20_33_result(repo_root=REPO_ROOT)
    if args.verify:
        result = load_strict_json(REPO_ROOT / RESULT_PATH)
        verify_result(
            result,
            spec=spec,
            run=run,
            t20_33_result=t20_33_result,
        )
    else:
        result = build_result(
            spec=spec,
            authority_identity=authority["identity_sha256"],
            run=run,
            t20_33_result=t20_33_result,
        )
        dump_canonical_json(REPO_ROOT / RESULT_PATH, result)
    print(result["identity_sha256"], result["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
