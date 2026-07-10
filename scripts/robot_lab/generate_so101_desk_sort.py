#!/usr/bin/env python3
"""Generate a SceneSmith SO-101 desk sorting lab from a text description."""

from __future__ import annotations

import argparse
import json
import os
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scenesmith.robot_lab import (
    build_so101_desk_sort_scene,
    export_so101_desk_sort_scene,
)

DEFAULT_DESCRIPTION = (
    "Set up an SO-101 arm on a desk in a simulation room with two colored trays, "
    "one red and one blue, plus a set of red and blue cubes. The robot should sort "
    "each cube into the tray with the matching color."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--description",
        default=DEFAULT_DESCRIPTION,
        help="Natural-language room/task description.",
    )
    parser.add_argument(
        "--scene-id",
        default="scenesmith_so101_desk_cube_sort",
        help="Stable scene id to embed in generated artifacts.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/robot_lab/so101_desk_cube_sort"),
        help="Output directory for generated SceneSmith/robot-lab artifacts.",
    )
    parser.add_argument(
        "--action-server-url",
        default=os.environ.get("MOLMOACT2_ACTION_SERVER_URL"),
        help="Optional MolmoAct2/LeRobot action server URL.",
    )
    args = parser.parse_args()

    scene = build_so101_desk_sort_scene(args.description, scene_id=args.scene_id)
    proof = export_so101_desk_sort_scene(
        scene,
        args.output_dir,
        action_server_url=args.action_server_url,
    )
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0 if proof["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
