#!/usr/bin/env python3
"""Verify Brief 053 production sources without capturing a live runtime."""

from __future__ import annotations

import hashlib
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scenesmith.robot_lab.census_runtime_binding import (
    verify_census_runtime_source_bindings,
)
from scenesmith.robot_lab.hardware_execution_profile import (
    verify_codex_execution_profile_files,
)
from scenesmith.robot_lab.static_pose_live_execution import (
    verify_pinned_ffmpeg_executable,
)

def main() -> int:
    profiles = verify_codex_execution_profile_files(repo_root=REPO_ROOT)
    profile_paths = {
        "project_default": Path(".codex/config.toml"),
        "hardware_supervised": Path(
            ".codex/profiles/hardware-supervised.toml"
        ),
        "offline_autonomous": Path(".codex/profiles/offline-autonomous.toml"),
    }
    profile_evidence = {
        name: {
            "path": path.as_posix(),
            "sha256": hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest(),
            "sandbox_mode": profiles[name]["sandbox_mode"],
            "approval_policy": profiles[name]["approval_policy"],
        }
        for name, path in profile_paths.items()
    }
    census = verify_census_runtime_source_bindings(repo_root=REPO_ROOT)
    ffmpeg = verify_pinned_ffmpeg_executable()
    print(
        json.dumps(
            {
                "brief_id": "053",
                "profile_evidence": profile_evidence,
                "feetech_source_bindings": census["source_bindings"],
                "ffmpeg": ffmpeg,
                "active_runtime_capture_attempted": False,
                "hardware_enumerated": False,
                "hardware_opened": False,
                "physical_follower_commanded": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
