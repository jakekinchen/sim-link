#!/usr/bin/env python3
"""Verify or materialize a local candidate from one copied Robo Scan export."""

import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.robo_scan_export_receipt import main


if __name__ == "__main__":
    raise SystemExit(main())
