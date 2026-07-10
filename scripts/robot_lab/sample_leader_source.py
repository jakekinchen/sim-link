#!/usr/bin/env python3
"""Capture a bounded read-only SceneSmith leader-source proof."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.leader_arm_bridge import make_correction_source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=("studio_leader", "physical_leader"),
        default="studio_leader",
    )
    parser.add_argument("--studio-url", default="http://127.0.0.1:8790")
    parser.add_argument("--leader-port")
    parser.add_argument("--leader-config")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--hz", type=float, default=10.0)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.samples <= 100:
        parser.error("--samples must be between 1 and 100")
    if args.hz <= 0:
        parser.error("--hz must be positive")

    source = make_correction_source(
        args.source,
        studio_url=args.studio_url,
        leader_port=args.leader_port,
        leader_config=args.leader_config,
        repo_root=REPO_ROOT,
    )
    rows = []
    try:
        for index in range(args.samples):
            action = source.get_action("read_only_sample", index)
            rows.append(
                {
                    "sample_index": index,
                    "captured_at": time.time(),
                    "action_radians": action,
                    "action_degrees_or_percent": [
                        *[round(math.degrees(value), 6) for value in action[:5]],
                        round(100 * (action[5] + 0.17453) / (1.74533 + 0.17453), 6),
                    ],
                }
            )
            if index + 1 < args.samples:
                time.sleep(1.0 / args.hz)
        payload = {
            "schema_version": "scenesmith.leader_readonly_sample.v1",
            "status": "pass",
            "source": args.source,
            "samples": rows,
            "safety_report": source.safety_report(),
            "physical_follower_commanded": False,
        }
    finally:
        source.close()

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
