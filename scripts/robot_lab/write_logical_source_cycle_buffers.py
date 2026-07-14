#!/usr/bin/env python3
"""Write or verify the immutable initial T18.2 logical buffer registry."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from scenesmith.robot_lab.artifact_contract import canonical_json_bytes, dump_canonical_json, load_strict_json  # noqa: E402
from scenesmith.robot_lab.logical_source_cycle_buffers import build_initial_buffer_registry, verify_initial_buffer_registry  # noqa: E402
OUTPUT_PATH = REPO_ROOT / "configurations/robot_lab/t18_2_logical_source_cycle_buffers.json"
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--rewrite", action="store_true")
    args = parser.parse_args()
    if args.rewrite:
        raise ValueError("T18.2 source windows are immutable; write a new reviewed cycle")
    if args.verify:
        if not OUTPUT_PATH.is_file(): raise ValueError("T18.2 logical registry is absent")
        registry = load_strict_json(OUTPUT_PATH)
        verify_initial_buffer_registry(registry)
        if canonical_json_bytes(registry) != canonical_json_bytes(build_initial_buffer_registry()): raise ValueError("T18.2 logical registry bytes drifted")
        status = "verified"
    else:
        if OUTPUT_PATH.exists(): raise ValueError("T18.2 logical registry exists; use --verify")
        registry = build_initial_buffer_registry()
        verify_initial_buffer_registry(registry)
        dump_canonical_json(OUTPUT_PATH, registry)
        status = "written"
    print(json.dumps({"status":status,"cycle_count":registry["realized_cycle_count"],"window_count":registry["realized_window_count"],"buffer_materialized":registry["buffer_materialized"],"training_eligible":registry["training_eligible"]}, indent=2, sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())
