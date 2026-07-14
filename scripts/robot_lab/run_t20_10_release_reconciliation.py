#!/usr/bin/env python3
"""Run or verify the T20.10 release-semantics source oracle."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.act_grasp_closed_loop import (  # noqa: E402
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
)
from scenesmith.robot_lab.artifact_contract import (  # noqa: E402
    dump_canonical_json,
    load_strict_json,
)
from scenesmith.robot_lab.release_semantics_reconciliation import (  # noqa: E402
    EVIDENCE_MODE,
    ROLLOUT_SCHEMA_VERSION,
    build_release_semantics_reconciliation,
    verify_release_semantics_reconciliation,
)
from scenesmith.robot_lab.source_expert_oracle import (  # noqa: E402
    verify_source_oracle_artifact,
)
from scripts.robot_lab.run_t20_9_source_expert_oracle import (  # noqa: E402
    build_oracle_evidence,
)


SOURCE_T20_9_PATH = REPO_ROOT / "outputs/robot_lab/t20_9_source_expert_oracle_run_001.json"
OUTPUT_PATH = REPO_ROOT / "outputs/robot_lab/t20_10_release_reconciliation_run_001.json"


def build() -> dict:
    source_t20_9 = load_strict_json(SOURCE_T20_9_PATH)
    verify_source_oracle_artifact(source_t20_9)
    evidence = build_oracle_evidence(
        release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
        schema_version=ROLLOUT_SCHEMA_VERSION,
        task_id="T20.10",
        evidence_mode=EVIDENCE_MODE,
    )
    return build_release_semantics_reconciliation(
        source_t20_9_ref={
            "path": str(SOURCE_T20_9_PATH.relative_to(REPO_ROOT)),
            "identity_sha256": source_t20_9["identity_sha256"],
            "file_sha256": _sha(SOURCE_T20_9_PATH),
        },
        **evidence,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    payload = build()
    verify_release_semantics_reconciliation(payload)
    if args.check:
        stored = load_strict_json(output)
        verify_release_semantics_reconciliation(stored)
        if stored != payload:
            raise ValueError("T20.10 release-semantics output drifted")
        print("verified", output.relative_to(REPO_ROOT), payload["identity_sha256"])
        return 0
    if output.exists():
        raise ValueError("T20.10 release-semantics output exists; use --check")
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(output, payload)
    print("wrote", output.relative_to(REPO_ROOT), payload["identity_sha256"])
    return 0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
