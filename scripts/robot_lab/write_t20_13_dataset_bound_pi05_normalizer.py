#!/usr/bin/env python3
"""Write or verify the T20.13 train-only dataset-bound normalizer."""

from __future__ import annotations

import argparse
import hashlib
import sys

from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.dataset_bound_pi05_normalizer import (
    build_dataset_bound_pi05_normalizer,
    verify_dataset_bound_pi05_normalizer,
)


PLAN = REPO_ROOT / "configurations/robot_lab/t20_7_model_bakeoff_plan.json"
T20_12 = REPO_ROOT / "outputs/robot_lab/t20_12_pi05_gripper_channel_audit.json"
OUTPUT = REPO_ROOT / "outputs/robot_lab/t20_13_dataset_bound_pi05_normalizer.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    inputs = _inputs()
    payload = build_dataset_bound_pi05_normalizer(**inputs)
    if args.check:
        stored = load_strict_json(OUTPUT)
        verify_dataset_bound_pi05_normalizer(stored, **inputs)
        print("verified", OUTPUT.relative_to(REPO_ROOT), stored["identity_sha256"])
        return 0
    if OUTPUT.exists():
        raise ValueError("T20.13 normalizer exists; use --check")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    dump_canonical_json(OUTPUT, payload)
    print("wrote", OUTPUT.relative_to(REPO_ROOT), payload["identity_sha256"])
    return 0


def _inputs() -> dict:
    plan = load_strict_json(PLAN)
    verify_signed_payload(plan, label="T20.13 source T20.7 plan")
    tensor = REPO_ROOT / plan["source_tensor_view"]["path"]
    if _sha(tensor) != plan["source_tensor_view"]["file_sha256"]:
        raise ValueError("T20.13 tensor view hash drifted")
    arrays = np.load(tensor)
    t20_12 = load_strict_json(T20_12)
    verify_signed_payload(t20_12, label="T20.13 source T20.12 audit")
    processor_source = (
        REPO_ROOT / "external/lerobot/src/lerobot/policies/pi05/processor_pi05.py"
    )
    training_source = REPO_ROOT / "scripts/robot_lab/run_t20_7_model_training.py"
    processor_text = processor_source.read_text(encoding="utf-8")
    required = (
        "stats=dataset_stats",
        "NormalizerProcessorStep(",
        "UnnormalizerProcessorStep(",
    )
    if any(value not in processor_text for value in required):
        raise ValueError("T20.13 PI0.5 dataset-stat processor path drifted")
    evidence = {
        "pi05_processor_construction_source": _file_evidence(processor_source),
        "t20_12_audit": {
            **_file_evidence(T20_12),
            "identity_sha256": t20_12["identity_sha256"],
        },
        "t20_7_bakeoff_plan": {
            **_file_evidence(PLAN),
            "identity_sha256": plan["identity_sha256"],
        },
        "training_tensor_view": _file_evidence(tensor),
        "t20_7_vla_batch_source": _file_evidence(training_source),
    }
    return {
        "train_state_mujoco": arrays["train_state"],
        "train_action_mujoco": arrays["train_action"],
        "evaluation_state_mujoco": arrays["evaluation_state"],
        "evaluation_action_mujoco": arrays["evaluation_action"],
        "source_evidence": evidence,
        "t20_12_audit": t20_12,
    }


def _file_evidence(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(REPO_ROOT)), "sha256": _sha(path)}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
