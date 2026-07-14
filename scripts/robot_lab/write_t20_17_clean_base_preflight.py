#!/usr/bin/env python3
"""Materialize or verify the T20.17 source-native clean-base preflight."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    activate_lerobot_stack(repo_root=repo_root, stage="training")
    from scenesmith.robot_lab.t20_17_clean_base_preflight import (
        DATASET_ROOT,
        REPO_ROOT,
        materialize_dataset,
        verify_training_spec_file,
        write_training_spec,
    )
    if args.write:
        if (REPO_ROOT / DATASET_ROOT).exists():
            result = write_training_spec()
        else:
            result = materialize_dataset()
            result = write_training_spec()
    else:
        spec = verify_training_spec_file()
        result = {"training_spec": spec}
    print(json.dumps({
        "status": "pass",
        "dataset_root": str(DATASET_ROOT),
        "training_spec_identity_sha256": result["training_spec"]["identity_sha256"],
        "model_loaded": False,
        "optimizer_training": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
