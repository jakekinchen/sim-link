#!/usr/bin/env python3
"""Run a LeLab command with the unified SceneSmith LeRobot source first."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.lerobot_stack import activate_lerobot_stack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        parser.error("pass a command after --")
    identity = activate_lerobot_stack(repo_root=REPO_ROOT, stage="lelab")
    source = str((REPO_ROOT / identity["source_root"]).resolve())
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [source, *[item for item in env.get("PYTHONPATH", "").split(os.pathsep) if item]]
    )
    env["SCENESMITH_LEROBOT_STACK_IDENTITY"] = identity["identity_sha256"]
    return subprocess.run(command, cwd=REPO_ROOT / "external/leLab", env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
