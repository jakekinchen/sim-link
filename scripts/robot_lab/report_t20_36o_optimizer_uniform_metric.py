#!/usr/bin/env python3
"""Write or verify the T20.36o strict-uniform report-only supplement."""

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
from scenesmith.robot_lab.t20_36o_bounded_optimizer_authority import (  # noqa: E402
    TRACKED_ATTEMPT_PATH,
    TRAINING_PERMIT_PATH,
    load_verified_sources,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_run import (  # noqa: E402
    PROBE_TENSOR_PATH,
)
from scenesmith.robot_lab.t20_36o_bounded_optimizer_spec import (  # noqa: E402
    SPEC_PATH,
)
from scenesmith.robot_lab.t20_36o_episode_bridge_design import (  # noqa: E402
    SPEC_PATH as BRIDGE_SPEC_PATH,
)
from scenesmith.robot_lab.t20_36o_optimizer_uniform_report import (  # noqa: E402
    REPORT_PATH,
    build_uniform_report,
    verify_uniform_report,
)


RESULT_PATH = Path("configurations/robot_lab/t20_36o_optimizer_result.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    sources = load_verified_sources(repo_root=REPO_ROOT)
    attempt = load_strict_json(REPO_ROOT / TRACKED_ATTEMPT_PATH)
    permit = load_strict_json(REPO_ROOT / TRAINING_PERMIT_PATH)
    optimizer_spec = load_strict_json(REPO_ROOT / SPEC_PATH)
    bridge_spec = load_strict_json(REPO_ROOT / BRIDGE_SPEC_PATH)
    probe_artifact = load_strict_json(REPO_ROOT / PROBE_TENSOR_PATH)
    result = load_strict_json(REPO_ROOT / RESULT_PATH)
    baseline = sources["optimizer_sources"]["source_spec"][
        "source_gate_baseline_objective_mean"
    ]
    expected = build_uniform_report(
        attempt=attempt,
        permit=permit,
        optimizer_spec=optimizer_spec,
        bridge_spec=bridge_spec,
        probe_artifact=probe_artifact,
        result=result,
        source_gate_baseline_objective_mean=baseline,
    )
    if args.verify:
        payload = load_strict_json(REPO_ROOT / REPORT_PATH)
        verify_uniform_report(
            payload,
            attempt=attempt,
            permit=permit,
            optimizer_spec=optimizer_spec,
            bridge_spec=bridge_spec,
            probe_artifact=probe_artifact,
            result=result,
            source_gate_baseline_objective_mean=baseline,
        )
    else:
        if (REPO_ROOT / REPORT_PATH).exists():
            raise FileExistsError("T20.36o strict uniform report already exists")
        dump_canonical_json(REPO_ROOT / REPORT_PATH, expected)
    print(expected["identity_sha256"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
